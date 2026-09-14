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

// Single autonomous virtual bungalow managing one Control Point
class VirtualBungalow {
public:
    VirtualBungalow(const std::string& name, const std::string& jsonPath)
        : name_(name), cp_(name.c_str()), lastTickMs_(0) {
        loadJson(jsonPath);
        clearAllTracks();
        setupCodec();
        setupSwitchMocks();
    }

    void clearAllTracks() {
        for (uint8_t i = 0; i < cp_.trackCircuitCount(); ++i) {
            cp_.trackCircuit(i)->update(Occupancy::VACANT);
        }
    }

    const std::string& name() const { return name_; }
    ControlPoint& cp() { return cp_; }
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

    void setupSwitchMocks(uint32_t travelTimeMs = 2000) {
        mockDrivers_.clear();
        for (uint8_t i = 0; i < cp_.switchCount(); ++i) {
            Switch* sw = cp_.getSwitch(i);
            if (sw) {
                auto driver = std::make_unique<MockSwitchDriver>(sw, travelTimeMs);
                cp_.overrideDriver(sw->name(), driver.get());
                mockDrivers_.push_back(std::move(driver));
            }
        }
    }

    void setupCodec() {
        codec_.clearEntries();

        // Switches
        for (uint8_t i = 0; i < cp_.switchCount(); ++i) {
            Switch* sw = cp_.getSwitch(i);
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

    bool hasIndicationChanged() {
        std::string current;
        if (exportIndications(current)) {
            return current != lastPublishedIndication_;
        }
        return false;
    }

    void markIndicationPublished(const std::string& ind) {
        lastPublishedIndication_ = ind;
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
    ControlPoint cp_;
    AarTextCodec codec_;
    std::vector<std::unique_ptr<MockSwitchDriver>> mockDrivers_;
    std::string lastPublishedIndication_;
    uint32_t lastTickMs_;
};

// Manager holding all 7 virtual bungalows across the SPCoast South territory
class SubdivisionPlantHost {
public:
    SubdivisionPlantHost(const std::string& profilesDir) : profilesDir_(profilesDir) {
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
            std::string path = profilesDir_ + "/" + name + ".json";
            bungalows_.push_back(std::make_unique<VirtualBungalow>(name, path));
            printf("[INIT] Loaded virtual bungalow: %s\n", name.c_str());
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

    const std::vector<std::unique_ptr<VirtualBungalow>>& bungalows() const {
        return bungalows_;
    }

private:
    std::string profilesDir_;
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

    // 4. Test Route Clearing & Signal Clearance at CP_Luchessa
    printf("[TEST 4] Route Alignment & Signal Authority at CP_Luchessa\n");
    VirtualBungalow* luchessa = host.findStation("CP_Luchessa");
    assert(luchessa != nullptr);

    // Command Signal 2 RIGHT (Southbound MT1 Straight)
    ControlTransaction ctlLuch;
    SignalControl* sig2Luch = luchessa->cp().findSignalControl("2");
    assert(sig2Luch != nullptr);
    ctlLuch.signalDemands[sig2Luch->index()] = SignalDemand::RIGHT;

    char luchBuf[512];
    size_t luchLen = 0;
    encOk = luchessa->codec().encodeControls(ctlLuch, luchBuf, sizeof(luchBuf), luchLen);
    assert(encOk);

    luchessa->handleControlMessage(luchBuf, clockMs);
    host.tickAll(clockMs);

    std::string luchInd;
    luchessa->exportIndications(luchInd);
    assert(luchInd.find("2SGK") != std::string::npos);
    assert(luchInd.find("(2SGK)") == std::string::npos); // 2SGK is asserted!
    printf("  -> Dispatcher cleared Signal 2 RIGHT: indication confirms 2SGK asserted\n");
    printf("  -> PASS: Vital route SB-MT1-STRAIGHT cleared successfully!\n\n");

    // 5. Test Signal Knockdown on Train Entrance at CP_Luchessa
    printf("[TEST 5] Signal Knockdown on Train Entrance at CP_Luchessa\n");
    TrackCircuit* tc1T1Luch = luchessa->cp().findTrackCircuit("1T1");
    assert(tc1T1Luch != nullptr);

    // Train enters OS block 1T1 -> shunts track circuit
    tc1T1Luch->update(Occupancy::OCCUPIED);
    host.tickAll(clockMs);

    luchessa->exportIndications(luchInd);
    assert(luchInd.find("(2SGK)") != std::string::npos); // Knocked down to stop!
    assert(luchInd.find("1T1K") != std::string::npos && luchInd.find("(1T1K)") == std::string::npos); // 1T1K occupied
    printf("  -> Train shunted 1T1: Signal 2 immediately knocked down to STOP ((2SGK))\n");
    printf("  -> PASS: Automatic signal knockdown verified!\n\n");

    // Train clears plant
    tc1T1Luch->update(Occupancy::VACANT);
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
    printf("[MQTT] Broadcasting all station indications (reason: %s)\n", reason);
    for (const auto& b : ctx->host->bungalows()) {
        std::string ind;
        if (b->exportIndications(ind)) {
            std::string topic = "ctc/" + ctx->layout + "/codeline/" + b->name() + "/indications";
            mosquitto_publish(ctx->mosq, nullptr, topic.c_str(), ind.length(), ind.c_str(), 1, true);
            b->markIndicationPublished(ind);
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

    uint32_t nowMs = static_cast<uint32_t>(clock());
    b->handleControlMessage(payload.c_str(), nowMs);
    b->tick(nowMs);

    // Immediate response to incoming controls: publish updated station truth
    std::string ind;
    if (b->exportIndications(ind)) {
        std::string indTopic = "ctc/" + ctx->layout + "/codeline/" + b->name() + "/indications";
        mosquitto_publish(mosq, nullptr, indTopic.c_str(), ind.length(), ind.c_str(), 1, true);
        b->markIndicationPublished(ind);
        printf("[TX IND RESPONSE] %s: %s\n", b->name().c_str(), ind.c_str());
    }
}
#endif

int main(int argc, char* argv[]) {
    signal(SIGINT, sigHandler);
    signal(SIGTERM, sigHandler);

    const std::string profilesDir = "/Users/jplocher/Dropbox/workspace/FieldUnit-Subdivision/profiles/spcoast_south/cps";
    SubdivisionPlantHost host(profilesDir);

    bool testMode = false;
    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--test") == 0) {
            testMode = true;
        }
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

    uint32_t nowMs = 0;
    while (g_running) {
        mosquitto_loop(mosq, 20, 1);
        nowMs += 20;
        host.tickAll(nowMs);

        // Only publish indications on state change!
        for (const auto& b : host.bungalows()) {
            if (b->hasIndicationChanged()) {
                std::string ind;
                if (b->exportIndications(ind)) {
                    std::string topic = "ctc/" + layout + "/codeline/" + b->name() + "/indications";
                    mosquitto_publish(mosq, nullptr, topic.c_str(), ind.length(), ind.c_str(), 1, true);
                    b->markIndicationPublished(ind);
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
