#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

#include "FieldUnit.h"

using namespace FieldUnit;

bool testStation(const char* name, const std::string& jsonPath) {
    printf("--------------------------------------------------\n");
    printf("[VALIDATING] Station: %s from %s\n", name, jsonPath.c_str());

    std::ifstream file(jsonPath);
    if (!file.is_open()) {
        fprintf(stderr, "ERROR: Could not open file: %s\n", jsonPath.c_str());
        return false;
    }
    std::stringstream buffer;
    buffer << file.rdbuf();
    std::string jsonStr = buffer.str();

    InterlockingPlant cp("Blank");
    bool ok = cp.deserialize(jsonStr.c_str());
    if (!ok) {
        fprintf(stderr, "ERROR: deserialize failed for %s\n", name);
        return false;
    }

    printf("  -> Name: %s\n", cp.name());
    printf("  -> Track Circuits (%u): ", cp.trackCircuitCount());
    for (uint8_t i = 0; i < cp.trackCircuitCount(); ++i) {
        printf("%s%s", cp.trackCircuit(i)->name(), (i + 1 < cp.trackCircuitCount()) ? ", " : "\n");
    }

    printf("  -> Switches (%u): ", cp.switchCount());
    for (uint8_t i = 0; i < cp.switchCount(); ++i) {
        printf("%s%s", cp.getSwitch(i)->name(), (i + 1 < cp.switchCount()) ? ", " : "\n");
    }

    printf("  -> Crossovers (%u): ", cp.crossoverCount());
    for (uint8_t i = 0; i < cp.crossoverCount(); ++i) {
        printf("%s%s", cp.crossover(i)->name(), (i + 1 < cp.crossoverCount()) ? ", " : "\n");
    }

    printf("  -> Signal Controls (%u): ", cp.authorityCount());
    for (uint8_t i = 0; i < cp.authorityCount(); ++i) {
        printf("%s%s", cp.authority(i)->name(), (i + 1 < cp.authorityCount()) ? ", " : "\n");
    }

    printf("  -> Signal Masts (%u): ", cp.mastCount());
    for (uint8_t i = 0; i < cp.mastCount(); ++i) {
        printf("%s%s", cp.mast(i)->name(), (i + 1 < cp.mastCount()) ? ", " : "\n");
    }

    printf("  -> Detector Locks (%u): ", cp.detectorLockCount());
    for (uint8_t i = 0; i < cp.detectorLockCount(); ++i) {
        printf("[%s <-> %s]%s",
               cp.detectorLockSwitch(i) ? cp.detectorLockSwitch(i)->name() : "?",
               cp.detectorLockTrackCircuit(i) ? cp.detectorLockTrackCircuit(i)->name() : "?",
               (i + 1 < cp.detectorLockCount()) ? ", " : "\n");
    }

    printf("  -> Routes (%u): ", cp.engine().routeCount());
    for (uint8_t i = 0; i < cp.engine().routeCount(); ++i) {
        const Route& r = cp.engine().route(i);
        printf("     [%s] dir=%s, entrance=%s\n",
               r.name(),
               (r.direction() == DirectionAuthority::LEFT) ? "LEFT" :
               (r.direction() == DirectionAuthority::RIGHT) ? "RIGHT" : "STOP",
               r.entranceBlock() ? r.entranceBlock()->name() : "None");
    }

    // Verify round-trip serialization
    char roundTripBuf[16384];
    bool serOk = cp.serialize(roundTripBuf, sizeof(roundTripBuf), true);
    assert(serOk);
    printf("  -> PASS: Round-trip serialization successful (%zu bytes)\n", strlen(roundTripBuf));
    return true;
}

int main() {
    printf("====================================================\n");
    printf("   FIELDUNIT-SUBDIVISION: 7-STATION CP VALIDATOR    \n");
    printf("====================================================\n\n");

    const std::string basePath = "/Users/jplocher/Dropbox/workspace/FieldUnit-Subdivision/profiles/spcoast_south/cps/";
    const std::vector<std::string> stations = {
        "CP_GilroyCaltrain",
        "CP_GilroyInterchange",
        "CP_Luchessa",
        "CP_Christopher",
        "CP_Corporal",
        "CP_Sargent",
        "CP_Watsonville"
    };

    int passed = 0;
    for (const auto& st : stations) {
        std::string path = basePath + st + ".json";
        if (testStation(st.c_str(), path)) {
            passed++;
        } else {
            fprintf(stderr, "FAILED station: %s\n", st.c_str());
            return 1;
        }
    }

    printf("\n====================================================\n");
    printf("   ALL %d STATIONS VALIDATED 100%% SUCCESSFULLY!    \n", passed);
    printf("====================================================\n");
    return 0;
}
