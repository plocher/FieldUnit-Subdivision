/*
 * spcoast_ctc - SPCoast South Dispatcher cTc Desk (Subdivision-owned)
 *
 * Controls 7 Control Points (Gilroy through Watsonville staging)
 * US&S Model 503 physical panel across 14 columns.
 *
 * Luchessa uses KiCad-projected FieldUnit plant IDs. Other stations remain
 * on legacy XML-derived bindings until each is cut over.
 * Reference copy: FieldUnit/examples/spcoast_ctc
 *
 * Select physical I/O backend:
 */
#include "IO-I2C.h"
// #include "IO-CMRI.h"

#include <FieldUnit.h>

using namespace FieldUnit;

#if defined(ARDUINO) && defined(ESP32)
#define USE_OTA
#endif

#ifdef USE_OTA
#include "ota.h"

#if __has_include("secrets.h")
#include "secrets.h"
#endif

#ifndef WIFI_SSID
#define WIFI_SSID       "your-wifi-ssid"
#define WIFI_PASSWORD   "your-wifi-password"
#define MQTT_SERVER     "************"
#define MQTT_PORT       1883
#endif

#include <WiFi.h>
#include <PubSubClient.h>

OtaManager ota;
WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);
#endif

PanelIO hardware;
cTcMachine machine(hardware);

void configureDesk() {
    // Column 1..2: CP_GilroyCaltrain
    machine.addStation("CP_GilroyCaltrain")
        .inColumn(1).withSwitch("1").withTrackLamps({ "1T1", "EA1" })
        .inColumn(2).withSwitch("3").withTrackLamps({ "TK1", "TK2", "TK3" }).withCodeButton();

    // Column 3..4: CP_GilroyInterchange
    machine.addStation("CP_GilroyInterchange")
        .inColumn(3).withSwitch("1").withTrackLamps({ "1T1", "3T1", "TK1" })
        .inColumn(4).withSwitch("3").withTrackLamps({ "EA1", "TL", "TR" }).withCodeButton();

    // Column 5..7: CP_Luchessa (KiCad → FieldUnit JSON truth)
    // Dependent derail 795D has no separate lever; master 795 KR is combined.
    machine.addStation("CP_Luchessa")
        .inColumn(5).withSwitch("783").withTrackLamps({ "783T1", "1SA" })
        .inColumn(6).withSwitch("795").withSignal("784").withTrackLamps({ "795T1", "2SA", "2NAA" }).withMaintainerCall("1")
        .inColumn(7).withSwitch("799").withTrackLamps({ "799T1", "1NA", "2NA", "3NA" }).withCodeButton();

    // Column 8..10: CP_Christopher
    machine.addStation("CP_Christopher")
        .inColumn(8).withSwitch("1").withTrackLamps({ "1T1", "1WA", "2WA" })
        .inColumn(9).withSwitch("3").withSignal("2").withTrackLamps({ "3T1", "3BT1", "5T1" })
        .inColumn(10).withSwitch("5").withTrackLamps({ "1EA", "2EA" }).withCodeButton();

    // Column 11..12: CP_Corporal
    machine.addStation("CP_Corporal")
        .inColumn(11).withSwitch("1").withSignal("2").withTrackLamps({ "1EA", "1T1", "3T1" })
        .inColumn(12).withSwitch("3").withTrackLamps({ "SDT", "TL", "TR" }).withCodeButton();

    // Column 13: CP_Sargent
    machine.addStation("CP_Sargent")
        .inColumn(13).withSwitch("1").withTrackLamps({ "1T1", "HBD" }).withCodeButton();

    // Column 14: CP_Watsonville
    machine.addStation("CP_Watsonville")
        .inColumn(14).withSwitch("1").withSignal("2").withTrackLamps({ "ALT", "EAT", "SAT" });
}

#ifdef USE_OTA
void onMqttMessage(char* topic, byte* payload, unsigned int length) {
    // Topic: ctc/SPCoast/codeline/<stationName>/indications
    const char* prefix = "codeline/";
    const char* p = strstr(topic, prefix);
    if (!p) return;
    p += strlen(prefix);
    const char* slash = strchr(p, '/');
    if (!slash) return;

    char stationName[32];
    size_t stLen = slash - p;
    if (stLen >= sizeof(stationName)) return;
    memcpy(stationName, p, stLen);
    stationName[stLen] = '\0';

    char msgBuf[512];
    size_t copyLen = (length < sizeof(msgBuf) - 1) ? length : sizeof(msgBuf) - 1;
    memcpy(msgBuf, payload, copyLen);
    msgBuf[copyLen] = '\0';

    machine.applyIndications(stationName, msgBuf);
}

void reconnectMqtt(uint32_t nowMs) {
    static uint32_t lastReconnectMs = 0;
    if (nowMs - lastReconnectMs < 5000) return;
    lastReconnectMs = nowMs;

    if (mqtt.connect("ctc-desk-south", "ctc/SPCoast/telemetry", 1, true, "OFFLINE")) {
        mqtt.publish("ctc/SPCoast/telemetry", "ONLINE", true);
        mqtt.subscribe("ctc/SPCoast/codeline/+/indications");
        Serial.println("MQTT connected. Subscribed to plant indications.");
    }
}
#endif

#ifdef ARDUINO
void setup() {
    Serial.begin(115200);
    hardware.begin();
    configureDesk();
    machine.begin(); // Preallocates Strategy B exact buffers and builds canonical AAR schemas

#ifdef USE_OTA
    ota.begin("spcoast-ctc", WIFI_SSID, WIFI_PASSWORD);
    mqtt.setServer(MQTT_SERVER, MQTT_PORT);
    mqtt.setCallback(onMqttMessage);
#endif

    Serial.println("SPCoast CTC Machine initialized.");
}

void loop() {
    uint32_t nowMs = millis();

#ifdef USE_OTA
    ota.poll();
    if (WiFi.status() == WL_CONNECTED) {
        if (!mqtt.connected()) {
            reconnectMqtt(nowMs);
        } else {
            mqtt.loop();
        }
    }
#endif

    hardware.syncInputs();

    size_t stIdx = 0;
    char txTokens[256];
    if (machine.pollCode(stIdx, txTokens, sizeof(txTokens))) {
        const char* targetCp = machine.station(stIdx).name();
        Serial.printf("CODED [%s]: %s\n", targetCp, txTokens);

#ifdef USE_OTA
        if (mqtt.connected()) {
            char topic[128];
            snprintf(topic, sizeof(topic), "ctc/SPCoast/codeline/%s/controls", targetCp);
            mqtt.publish(topic, txTokens);
        }
#endif
    }

    hardware.syncOutputs();
}
#endif
