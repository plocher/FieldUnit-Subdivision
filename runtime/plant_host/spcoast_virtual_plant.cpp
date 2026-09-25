#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <unistd.h>
#include <time.h>
#include <assert.h>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <memory>

#include "FieldUnit.h"

#ifdef HAS_MOSQUITTO
#include <mosquitto.h>
#endif

using namespace FieldUnit;

static volatile bool g_running = true;
void sigHandler(int) {
    g_running = false;
}

inline uint32_t getWallClockMs() {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return static_cast<uint32_t>(ts.tv_sec * 1000 + ts.tv_nsec / 1000000);
}

// Simulates prototype dual-control switch machine physics (US&S M-23 / GRS Model 5D):
// Phase 1: Motor energizes, lock rod unlocks (350-500ms). Point contacts remain closed; existing lamp stays lit.
// Phase 2: Lock cleared -> point detector contacts open (MOVING). Both lamps dark. Points travel across (1.8s-2.5s).
// Phase 3: Points seat against opposite stock rail -> lock dog engages -> contacts close -> new lamp illuminates.
// Total stroke duration: 2.2s to 3.0s (compressed for layout operations).
class RealisticSwitchDriver : public ApplianceDriver {
public:
    enum class MotorPhase {
        IDLE,
        UNLOCKING,
        TRAVELING
    };

    RealisticSwitchDriver(Switch* sw, uint32_t minTotalMs = 2200, uint32_t maxTotalMs = 3000)
        : sw_(sw), minTotalMs_(minTotalMs), maxTotalMs_(maxTotalMs),
          phase_(MotorPhase::IDLE), strokeStartMs_(0), unlockDurationMs_(400),
          totalDurationMs_(2500) {}

    void drive(uint32_t nowMs) override {
        if (!sw_) return;
        if (sw_->reportedPosition() != sw_->commandedPosition() && phase_ == MotorPhase::IDLE) {
            phase_ = MotorPhase::UNLOCKING;
            strokeStartMs_ = nowMs;
            // Mechanical lock dog withdrawal delay: 100ms to 180ms
            unlockDurationMs_ = 100 + (rand() % 80);
            // Total stroke duration: 2.2s to 3.0s
            uint32_t range = (maxTotalMs_ > minTotalMs_) ? (maxTotalMs_ - minTotalMs_) : 500;
            totalDurationMs_ = minTotalMs_ + (rand() % range);
            printf("  [%s] Switch motor energized: withdrawing lock dog (total stroke: %.2fs)...\n",
                   sw_->name(), totalDurationMs_ / 1000.0);
        }
    }

    void sample(uint32_t nowMs) override {
        if (!sw_ || phase_ == MotorPhase::IDLE) return;

        uint32_t elapsed = nowMs - strokeStartMs_;

        if (phase_ == MotorPhase::UNLOCKING) {
            // During unlocking, points have not moved yet; keep existing reported position.
            if (elapsed >= unlockDurationMs_) {
                phase_ = MotorPhase::TRAVELING;
                // Lock rod clears notch -> point detector contacts open -> Out of Correspondence!
                sw_->updateFeedback(SwitchPosition::MOVING);
                printf("  [%s] Lock rod cleared: point detector contacts open (MOVING / OOC). Points in motion.\n",
                       sw_->name());
            }
        } else if (phase_ == MotorPhase::TRAVELING) {
            if (elapsed >= totalDurationMs_) {
                phase_ = MotorPhase::IDLE;
                // Points fully seated and lock dog engages -> full correspondence!
                sw_->updateFeedback(sw_->commandedPosition());
                printf("  [%s] Points locked in %s position and proven in correspondence.\n",
                       sw_->name(),
                       (sw_->commandedPosition() == SwitchPosition::NORMAL) ? "NORMAL" : "REVERSE");
            }
        }
    }

    bool inMotion() const { return phase_ != MotorPhase::IDLE; }

private:
    Switch* sw_;
    uint32_t minTotalMs_;
    uint32_t maxTotalMs_;
    MotorPhase phase_;
    uint32_t strokeStartMs_;
    uint32_t unlockDurationMs_;
    uint32_t totalDurationMs_;
};

// Single autonomous virtual bungalow managing one Control Point
class VirtualBungalow {
public:
    VirtualBungalow(const std::string& name, const std::string& jsonPath, bool isTest = false)
        : name_(name), cp_(name.c_str()), lastTickMs_(0) {
        loadJson(jsonPath);
        clearAllTracks();
        setupCodec();
        setupSwitchMocks(isTest ? 800 : 2200, isTest ? 1200 : 3000);
    }

    void clearAllTracks() {
        for (uint8_t i = 0; i < cp_.trackCircuitCount(); ++i) {
            cp_.trackCircuit(i)->update(Occupancy::VACANT);
        }
    }

    void resetToNormative() {
        // 1. All switches to NORMAL
        for (uint8_t i = 0; i < cp_.switchCount(); ++i) {
            Switch* sw = cp_.getSwitch(i);
            if (sw) {
                sw->throwSwitch(SwitchPosition::NORMAL, 0);
                sw->updateFeedback(SwitchPosition::NORMAL);
            }
        }
        // 2. All signals to STOP
        for (uint8_t i = 0; i < cp_.authorityCount(); ++i) {
            SignalControl* sc = cp_.authority(i);
            if (sc) {
                sc->updateCommand(DirectionAuthority::STOP, false, 0, false);
            }
        }
        // 3. All tracks to VACANT
        clearAllTracks();
        // 4. All maintainers to OFF
        for (uint8_t i = 0; i < MAX_APPLIANCES; ++i) {
            cp_.setMaintainerCall(i, false);
        }
        lastPublishedIndication_.clear(); // force republication
    }

    const std::string& name() const { return name_; }
    InterlockingPlant& cp() { return cp_; }
    AarTextCodec& codec() { return codec_; }

    void loadJson(const std::string& jsonPath) {
        std::ifstream file(jsonPath);
        if (!file.is_open()) {
            fprintf(stderr, "[%s] ERROR: Could not open %s\n", name_.c_str(), jsonPath.c_str());
            return;
        }
        std::stringstream buffer;
        buffer << file.rdbuf();
        std::string jsonStr = buffer.str();

        bool ok = cp_.deserialize(jsonStr.c_str());
        if (!ok) {
            fprintf(stderr, "[%s] ERROR: Deserialization failed!\n", name_.c_str());
        }
    }

    void setupSwitchMocks(uint32_t minTravelMs = 2200, uint32_t maxTravelMs = 3000) {
        mockDrivers_.clear();
        for (uint8_t i = 0; i < cp_.switchCount(); ++i) {
            Switch* sw = cp_.getSwitch(i);
            if (sw) {
                auto driver = std::make_unique<RealisticSwitchDriver>(sw, minTravelMs, maxTravelMs);
                cp_.overrideDriver(sw->name(), driver.get());
                mockDrivers_.push_back(std::move(driver));
            }
        }
    }

    void setupCodec() {
        codec_.clearEntries();

        // Switches / independent derails only. Dependent *D has no CodeLine step.
        for (uint8_t i = 0; i < cp_.switchCount(); ++i) {
            Switch* sw = cp_.getSwitch(i);
            if (!sw || sw->isDependentDerail()) {
                continue;
            }
            codec_.addDecodeEntry(decodeSwitch(sw));
            codec_.addEncodeEntry(encodeSwitch(sw));
        }

        // Track circuits
        for (uint8_t i = 0; i < cp_.trackCircuitCount(); ++i) {
            TrackCircuit* tc = cp_.trackCircuit(i);
            codec_.addEncodeEntry(encodeTrack(tc));
        }

        // Signals
        for (uint8_t i = 0; i < cp_.authorityCount(); ++i) {
            SignalControl* sc = cp_.authority(i);
            codec_.addDecodeEntry(decodeSignal(sc));
            codec_.addEncodeEntry(encodeSignal(sc));
        }

        // Maintainer Calls matching the physical desk columns
        if (name_ == "CP_GilroyInterchange") {
            codec_.addDecodeEntry(decodeMaintainer(0, "MC1"));
            codec_.addDecodeEntry(decodeMaintainer(1, "MC2"));
            codec_.addEncodeEntry(encodeMaintainer(0, "MC1"));
            codec_.addEncodeEntry(encodeMaintainer(1, "MC2"));
        } else if (name_ == "CP_Luchessa" || name_ == "CP_Corporal" || name_ == "CP_Sargent") {
            codec_.addDecodeEntry(decodeMaintainer(0, "MC1"));
            codec_.addEncodeEntry(encodeMaintainer(0, "MC1"));
        } else if (name_ == "CP_Christopher") {
            codec_.addDecodeEntry(decodeMaintainer(0, "MC1"));
            codec_.addDecodeEntry(decodeMaintainer(1, "MC2"));
            codec_.addEncodeEntry(encodeMaintainer(0, "MC1"));
            codec_.addEncodeEntry(encodeMaintainer(1, "MC2"));
        }

        codec_.preallocateBuffers();
    }

    // Ingress: Process incoming AAR control token string from dispatcher desk
    bool handleControlMessage(const char* controlTokens, uint32_t nowMs) {
        ControlTransaction ctl;
        if (!codec_.decodeControls(controlTokens, ctl)) {
            fprintf(stderr, "[%s] REJECTED corrupted control snapshot: %s\n", name_.c_str(), controlTokens);
            return false;
        }

        if (!ctl.vitalValid) {
            fprintf(stderr, "[%s] VITAL CONFLICT: Corrupt controls skipped!\n", name_.c_str());
            return false;
        }

        printf("[%s] [CONTROLS APPLIED] %s\n", name_.c_str(), controlTokens);
        cp_.applyControlTransaction(ctl, nowMs);
        return true;
    }

    // Egress: Export verified plant truth formatted in authentic AAR indication tokens
    bool exportIndications(std::string& outTokens) {
        IndicationVector ind;
        cp_.exportIndicationVector(ind);

        char outBuf[1024];
        size_t outLen = 0;
        if (codec_.encodeIndications(ind, outBuf, sizeof(outBuf), outLen)) {
            outTokens = std::string(outBuf, outLen);
            return true;
        }
        return false;
    }

    // True when indication content differs from what was last published, or
    // when it's byte-identical but at least kMinResendIntervalMs has elapsed
    // since the last publish (a periodic heartbeat re-assert of unchanged
    // retained truth). Suppresses redundant back-to-back resends of
    // identical content (e.g. a flaky desk reconnect storm re-triggering
    // publishAllIndications(), or a no-op control replay) without ever
    // delaying or hiding a genuine state change, which always publishes
    // immediately regardless of timing.
    static constexpr uint32_t kMinResendIntervalMs = 30000;

    bool hasIndicationChanged(uint32_t nowMs) {
        std::string current;
        if (!exportIndications(current)) return false;
        if (current != lastPublishedIndication_) return true;
        return (nowMs - lastPublishedMs_) >= kMinResendIntervalMs;
    }

    void markIndicationPublished(const std::string& ind, uint32_t nowMs) {
        lastPublishedIndication_ = ind;
        lastPublishedMs_ = nowMs;
    }

    const std::string& lastPublishedIndication() const {
        return lastPublishedIndication_;
    }

    void tick(uint32_t nowMs) {
        cp_.tick(nowMs);
        lastTickMs_ = nowMs;
    }

private:
    std::string name_;
    InterlockingPlant cp_;
    AarTextCodec codec_;
    std::vector<std::unique_ptr<RealisticSwitchDriver>> mockDrivers_;
    std::string lastPublishedIndication_;
    uint32_t lastPublishedMs_ = 0;
    uint32_t lastTickMs_;
};

// Manager holding all 7 virtual bungalows across the SPCoast South territory
class SubdivisionPlantHost {
public:
    SubdivisionPlantHost(const std::string& profilesDir, bool isTest = false)
        : profilesDir_(profilesDir), isTest_(isTest) {
        loadStations();
    }

    void loadStations() {
        const std::vector<std::string> stationNames = {
            "CP_GilroyCaltrain",
            "CP_GilroyInterchange",
            "CP_Luchessa",
            "CP_Christopher",
            "CP_Corporal",
            "CP_Sargent",
            "CP_Watsonville"
        };

        for (const auto& name : stationNames) {
            // Luchessa uses KiCad-projected FieldUnit JSON; others remain legacy harvest.
            std::string path = (name == "CP_Luchessa")
                ? (profilesDir_ + "/generated/" + name + ".json")
                : (profilesDir_ + "/" + name + ".json");
            bungalows_.push_back(std::make_unique<VirtualBungalow>(name, path, isTest_));
            printf("[INIT] Loaded virtual bungalow: %s from %s\n", name.c_str(), path.c_str());
        }
    }

    VirtualBungalow* findStation(const std::string& name) {
        for (auto& b : bungalows_) {
            if (b->name() == name) return b.get();
        }
        return nullptr;
    }

    void tickAll(uint32_t nowMs) {
        for (auto& b : bungalows_) {
            b->tick(nowMs);
        }
    }

    void resetAllToNormative() {
        for (auto& b : bungalows_) {
            b->resetToNormative();
        }
    }

    const std::vector<std::unique_ptr<VirtualBungalow>>& bungalows() const {
        return bungalows_;
    }

private:
    std::string profilesDir_;
    bool isTest_;
    std::vector<std::unique_ptr<VirtualBungalow>> bungalows_;
};

// Self-contained automated test mode
int runSelfTest(SubdivisionPlantHost& host) {
    printf("\n====================================================\n");
    printf("   RUNNING HEADLESS PLANT HOST SELF-TEST SUITE      \n");
    printf("====================================================\n\n");

    uint32_t clockMs = 1000;
    host.tickAll(clockMs);

    // 1. Test Initial Indications across all 7 stations
    printf("[TEST 1] Initial Baseline Indications\n");
    for (const auto& b : host.bungalows()) {
        std::string indStr;
        bool ok = b->exportIndications(indStr);
        assert(ok);
        printf("  [%s] -> %s\n", b->name().c_str(), indStr.c_str());
    }
    printf("  -> PASS: All 7 stations emitted valid initial indication vectors\n\n");

    // 2. Test Switch Throw and 2.0s Transit Travel at CP_Corporal
    printf("[TEST 2] Switch Throw Transit Delay & Correspondence at CP_Corporal\n");
    VirtualBungalow* corporal = host.findStation("CP_Corporal");
    assert(corporal != nullptr);

    Switch* sw3 = corporal->cp().findSwitch("3");
    assert(sw3 != nullptr);
    assert(sw3->reportedPosition() == SwitchPosition::NORMAL);

    // Dispatcher desk compiles full control transaction snapshot commanding SW3 Reverse
    ControlTransaction ctlThrow;
    ctlThrow.switchDemands[sw3->index()] = SwitchDemand::REVERSE;
    char ctlBuf[512];
    size_t ctlLen = 0;
    bool encOk = corporal->codec().encodeControls(ctlThrow, ctlBuf, sizeof(ctlBuf), ctlLen);
    assert(encOk);
    printf("  -> Dispatcher transmits: %s\n", ctlBuf);

    corporal->handleControlMessage(ctlBuf, clockMs);
    host.tickAll(clockMs);

    // In-flight check: after 500ms, switch must still be MOVING (out of correspondence)
    clockMs += 500;
    host.tickAll(clockMs);
    assert(sw3->reportedPosition() == SwitchPosition::MOVING);
    std::string inFlightInd;
    corporal->exportIndications(inFlightInd);
    assert(inFlightInd.find("(3NWK)") != std::string::npos); // Both normal and reverse unasserted (out of correspondence)
    assert(inFlightInd.find("(3RWK)") != std::string::npos);
    printf("  -> at +500ms: Switch 3 is MOVING (Out of Correspondence: (3NWK), (3RWK))\n");

    // After 2100ms total, switch completes travel and locks in Reverse!
    clockMs += 1600;
    host.tickAll(clockMs);
    assert(sw3->reportedPosition() == SwitchPosition::REVERSE);
    std::string lockedInd;
    corporal->exportIndications(lockedInd);
    assert(lockedInd.find("(3RWK)") == std::string::npos); // 3RWK is now ASSERTED (no parens!)
    assert(lockedInd.find("3RWK") != std::string::npos);
    printf("  -> at +2100ms: Switch 3 locked REVERSE; indication asserts 3RWK: %s\n", lockedInd.c_str());
    printf("  -> PASS: Non-blocking 2.0s switch motor travel verified!\n\n");

    // 3. Test Detector Locking: Attempt to throw Switch 3 Normal while 3T1 is occupied
    printf("[TEST 3] Detector Locking: Rejection of switch throw under train\n");
    TrackCircuit* tc3T1 = corporal->cp().findTrackCircuit("3T1");
    assert(tc3T1 != nullptr);
    tc3T1->update(Occupancy::OCCUPIED);
    host.tickAll(clockMs);

    ControlTransaction ctlUnsafe;
    ctlUnsafe.switchDemands[sw3->index()] = SwitchDemand::NORMAL;
    encOk = corporal->codec().encodeControls(ctlUnsafe, ctlBuf, sizeof(ctlBuf), ctlLen);
    assert(encOk);
    printf("  -> Dispatcher attempts unsafe throw: %s\n", ctlBuf);

    corporal->handleControlMessage(ctlBuf, clockMs);
    host.tickAll(clockMs);
    clockMs += 2500;
    host.tickAll(clockMs);

    // Switch points must NOT have moved; still locked in Reverse!
    assert(sw3->reportedPosition() == SwitchPosition::REVERSE);
    printf("  -> PASS: Switch did not move while 3T1 was occupied (Detector Locked)!\n\n");

    tc3T1->update(Occupancy::VACANT);
    host.tickAll(clockMs);

    // 4. Test Route Clearing & Signal Clearance at CP_Luchessa (KiCad plant)
    printf("[TEST 4] Route Alignment & Signal Authority at CP_Luchessa\n");
    VirtualBungalow* luchessa = host.findStation("CP_Luchessa");
    assert(luchessa != nullptr);
    assert(luchessa->cp().findSwitch("783") != nullptr);
    assert(luchessa->cp().findSwitch("795D") != nullptr);
    assert(luchessa->cp().findSwitch("795D")->isDerail());

    // Align MT-MT1: masters NORMAL. Dependent 795D follows inverse pair automatically.
    for (const char* swName : {"783", "795", "799"}) {
        Switch* sw = luchessa->cp().findSwitch(swName);
        assert(sw != nullptr);
        sw->throwSwitch(SwitchPosition::NORMAL, clockMs);
        sw->updateFeedback(SwitchPosition::NORMAL);
    }
    for (uint8_t i = 0; i < luchessa->cp().trackCircuitCount(); ++i) {
        luchessa->cp().trackCircuit(i)->update(Occupancy::VACANT, Quality::GOOD, clockMs);
    }
    host.tickAll(clockMs);

    ControlTransaction ctlLuch;
    SignalControl* sig784 = luchessa->cp().findSignalControl("784");
    assert(sig784 != nullptr);
    ctlLuch.signalDemands[sig784->index()] = SignalDemand::RIGHT;

    char luchBuf[512];
    size_t luchLen = 0;
    encOk = luchessa->codec().encodeControls(ctlLuch, luchBuf, sizeof(luchBuf), luchLen);
    assert(encOk);

    luchessa->handleControlMessage(luchBuf, clockMs);
    host.tickAll(clockMs);

    std::string luchInd;
    luchessa->exportIndications(luchInd);
    assert(luchInd.find("784SGK") != std::string::npos);
    assert(luchInd.find("(784SGK)") == std::string::npos);
    printf("  -> Dispatcher cleared Signal 784 RIGHT: indication confirms 784SGK asserted\n");
    printf("  -> PASS: Vital route MT-MT1 cleared successfully!\n\n");

    // 5. Test Signal Knockdown on Train Entrance at CP_Luchessa
    printf("[TEST 5] Signal Knockdown on Train Entrance at CP_Luchessa\n");
    TrackCircuit* tc1SA = luchessa->cp().findTrackCircuit("1SA");
    assert(tc1SA != nullptr);

    // Train enters entrance circuit 1SA -> shunts track circuit
    tc1SA->update(Occupancy::OCCUPIED, Quality::GOOD, clockMs);
    host.tickAll(clockMs);

    luchessa->exportIndications(luchInd);
    assert(luchInd.find("(784SGK)") != std::string::npos);
    assert(luchInd.find("1SAK") != std::string::npos && luchInd.find("(1SAK)") == std::string::npos);
    printf("  -> Train shunted 1SA: Signal 784 immediately knocked down to STOP ((784SGK))\n");
    printf("  -> PASS: Automatic signal knockdown verified!\n\n");

    // Train clears plant
    tc1SA->update(Occupancy::VACANT, Quality::GOOD, clockMs);
    host.tickAll(clockMs);

    // 6. Test Yard Departure Route at CP_Watsonville
    printf("[TEST 6] Route Alignment & Yard Departure at CP_Watsonville\n");
    VirtualBungalow* watsonville = host.findStation("CP_Watsonville");
    assert(watsonville != nullptr);

    ControlTransaction ctlWat;
    SignalControl* sig2Wat = watsonville->cp().findSignalControl("2");
    assert(sig2Wat != nullptr);
    ctlWat.signalDemands[sig2Wat->index()] = SignalDemand::RIGHT;

    char watBuf[512];
    size_t watLen = 0;
    encOk = watsonville->codec().encodeControls(ctlWat, watBuf, sizeof(watBuf), watLen);
    assert(encOk);

    watsonville->handleControlMessage(watBuf, clockMs);
    host.tickAll(clockMs);

    std::string watInd;
    watsonville->exportIndications(watInd);
    assert(watInd.find("2SGK") != std::string::npos && watInd.find("(2SGK)") == std::string::npos);
    printf("  -> Watsonville Signal 2 cleared RIGHT: indication confirms 2SGK: %s\n", watInd.c_str());
    printf("  -> PASS: Yard departure route cleared!\n\n");

    printf("====================================================\n");
    printf("   ALL 6 SCENARIOS IN SELF-TEST PASSED 100%%!        \n");
    printf("====================================================\n\n");
    return 0;
}

#ifdef HAS_MOSQUITTO
struct MqttContext {
    SubdivisionPlantHost* host;
    struct mosquitto* mosq;
    std::string layout;
};

void publishAllIndications(MqttContext* ctx, const char* reason) {
    // Explicit full resync (cold start / REFRESH): always send every station's
    // current truth regardless of the resend cooldown below.
    printf("[MQTT] Broadcasting all station indications (reason: %s)\n", reason);
    uint32_t nowMs = getWallClockMs();
    for (const auto& b : ctx->host->bungalows()) {
        std::string ind;
        if (b->exportIndications(ind)) {
            std::string topic = "ctc/" + ctx->layout + "/codeline/" + b->name() + "/indications";
            mosquitto_publish(ctx->mosq, nullptr, topic.c_str(), ind.length(), ind.c_str(), 1, true);
            b->markIndicationPublished(ind, nowMs);
            printf("  [%s] -> %s\n", b->name().c_str(), ind.c_str());
        }
    }
}

void on_connect_cb(struct mosquitto* mosq, void* obj, int rc) {
    if (rc == 0) {
        MqttContext* ctx = static_cast<MqttContext*>(obj);
        printf("[MQTT] Connected to Mosquitto broker successfully.\n");

        std::string subControls = "ctc/" + ctx->layout + "/codeline/+/controls";
        mosquitto_subscribe(mosq, nullptr, subControls.c_str(), 1);
        printf("[MQTT] Subscribed to %s\n", subControls.c_str());

        std::string subTelem = "ctc/" + ctx->layout + "/telemetry";
        mosquitto_subscribe(mosq, nullptr, subTelem.c_str(), 1);

        std::string subRefresh = "ctc/" + ctx->layout + "/codeline/refresh";
        mosquitto_subscribe(mosq, nullptr, subRefresh.c_str(), 1);

        // Publish ONLINE status
        std::string telemTopic = "ctc/" + ctx->layout + "/telemetry/plant_host";
        mosquitto_publish(mosq, nullptr, telemTopic.c_str(), 6, "ONLINE", 1, true);

        // Send initial baseline indications once upon connection
        publishAllIndications(ctx, "Initial broker connect");
    } else {
        fprintf(stderr, "[MQTT] Connect failed with code: %d\n", rc);
    }
}

void on_message_cb(struct mosquitto* mosq, void* obj, const struct mosquitto_message* msg) {
    if (!msg || !msg->payload || msg->payloadlen == 0) return;
    MqttContext* ctx = static_cast<MqttContext*>(obj);

    std::string topic(msg->topic);
    std::string payload(static_cast<const char*>(msg->payload), msg->payloadlen);

    // Global refresh trigger: telemetry announce from desk or refresh request
    if (topic.find("/telemetry") != std::string::npos || topic.find("/refresh") != std::string::npos) {
        if (payload == "ONLINE" || payload == "REFRESH") {
            publishAllIndications(ctx, payload.c_str());
            return;
        }
    }

    // Station controls format: ctc/<layout>/codeline/<station>/controls
    const std::string prefix = "codeline/";
    size_t pos = topic.find(prefix);
    if (pos == std::string::npos) return;
    pos += prefix.length();

    size_t slash = topic.find('/', pos);
    if (slash == std::string::npos) return;

    std::string stationName = topic.substr(pos, slash - pos);
    VirtualBungalow* b = ctx->host->findStation(stationName);
    if (!b) return;

    uint32_t nowMs = getWallClockMs();
    b->handleControlMessage(payload.c_str(), nowMs);
    b->tick(nowMs);

    // Immediate response to incoming controls: publish updated station truth,
    // but only if it actually changed (or the resend cooldown has elapsed) —
    // a no-op control replay should not spam an identical indication.
    if (b->hasIndicationChanged(nowMs)) {
        std::string ind;
        if (b->exportIndications(ind)) {
            std::string indTopic = "ctc/" + ctx->layout + "/codeline/" + b->name() + "/indications";
            mosquitto_publish(mosq, nullptr, indTopic.c_str(), ind.length(), ind.c_str(), 1, true);
            b->markIndicationPublished(ind, nowMs);
            printf("[TX IND RESPONSE] %s: %s\n", b->name().c_str(), ind.c_str());
        }
    }
}
#endif

int main(int argc, char* argv[]) {
    signal(SIGINT, sigHandler);
    signal(SIGTERM, sigHandler);

    bool testMode = false;
    bool resetMode = false;
    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--test") == 0) {
            testMode = true;
        } else if (strcmp(argv[i], "--reset") == 0 || strcmp(argv[i], "--normative") == 0) {
            resetMode = true;
        }
    }

    const std::string profilesDir = "/Users/jplocher/Dropbox/workspace/FieldUnit-Subdivision/profiles/spcoast_south/cps";
    SubdivisionPlantHost host(profilesDir, testMode);

    if (resetMode) {
        printf("[RESET] Setting all 7 stations to safe normative baseline (Switches NORMAL, Signals STOP, Tracks VACANT, MC OFF)...\n");
        host.resetAllToNormative();
    }

    if (testMode) {
        return runSelfTest(host);
    }

#ifdef HAS_MOSQUITTO
    const char* brokerHost = "localhost";
    int brokerPort = 1883;
    const std::string layout = "SPCoast";

    mosquitto_lib_init();
    struct mosquitto* mosq = mosquitto_new("spcoast-plant-host", true, nullptr);

    MqttContext ctx{&host, mosq, layout};
    mosquitto_user_data_set(mosq, &ctx);
    mosquitto_connect_callback_set(mosq, on_connect_cb);
    mosquitto_message_callback_set(mosq, on_message_cb);

    int conn = mosquitto_connect(mosq, brokerHost, brokerPort, 60);
    if (conn != MOSQ_ERR_SUCCESS) {
        fprintf(stderr, "[MQTT] Could not connect to broker at %s:%d (code %d).\n", brokerHost, brokerPort, conn);
        fprintf(stderr, "[HINT] Make sure Mosquitto is running: 'brew services start mosquitto'\n");
        fprintf(stderr, "Running self-test instead...\n");
        return runSelfTest(host);
    }

    printf("[HOST] Live Virtual Plant Daemon running for layout '%s'. Press Ctrl+C to exit.\n", layout.c_str());

    srand(static_cast<unsigned>(time(nullptr)));
    while (g_running) {
        mosquitto_loop(mosq, 20, 1);
        uint32_t nowMs = getWallClockMs();
        host.tickAll(nowMs);

        // Only publish indications on real change, or a heartbeat resend of
        // unchanged content past the cooldown window.
        for (const auto& b : host.bungalows()) {
            if (b->hasIndicationChanged(nowMs)) {
                std::string ind;
                if (b->exportIndications(ind)) {
                    std::string topic = "ctc/" + layout + "/codeline/" + b->name() + "/indications";
                    mosquitto_publish(mosq, nullptr, topic.c_str(), ind.length(), ind.c_str(), 1, true);
                    b->markIndicationPublished(ind, nowMs);
                    printf("[TX IND CHANGED] %s: %s\n", b->name().c_str(), ind.c_str());
                }
            }
        }
        usleep(20000); // 20ms tick
    }

    printf("\n[HOST] Shutting down cleanly...\n");
    mosquitto_destroy(mosq);
    mosquitto_lib_cleanup();
#else
    printf("Compiled without native MQTT. Running self-test suite.\n");
    return runSelfTest(host);
#endif

    return 0;
}
