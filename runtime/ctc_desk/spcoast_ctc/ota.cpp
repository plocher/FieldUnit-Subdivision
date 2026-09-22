// ota.cpp — non-blocking WiFi + ArduinoOTA lifecycle.

#include "ota.h"

#if defined(ARDUINO) && defined(ESP32)
#include <WiFi.h>
#include <ArduinoOTA.h>

static const char* errorName(ota_error_t err) {
    switch (err) {
        case OTA_AUTH_ERROR:    return "Auth Failed";
        case OTA_BEGIN_ERROR:   return "Begin Failed";
        case OTA_CONNECT_ERROR: return "Connect Failed";
        case OTA_RECEIVE_ERROR: return "Receive Failed";
        case OTA_END_ERROR:     return "End Failed";
        default:                return "Unknown Error";
    }
}

void OtaManager::begin(const char* hostname, const char* ssid,
                       const char* password, uint32_t connectTimeoutMs) {
    _hostname = hostname;
    _connectTimeoutMs = connectTimeoutMs;
    _connectStartedMs = millis();
    _everReady = false;
    _armed = false;

    WiFi.mode(WIFI_STA);
    WiFi.setSleep(false);   // modem power-save stalls OTA TCP transfers on ESP32
    WiFi.setAutoReconnect(false);
    WiFi.begin(ssid, password);

    _state = CONNECTING;
}

void OtaManager::failJoin_(const char* reason) {
    WiFi.disconnect(true /* wifioff */, false /* eraseAP */);
    WiFi.setAutoReconnect(false);
    _state = FAILED;
    if (onError) {
        onError(reason);
    }
}

void OtaManager::arm(void) {
    ArduinoOTA.setHostname(_hostname);

    ArduinoOTA.onStart([this]() {
        _state = UPDATING;
        if (onStart) onStart();
    });
    ArduinoOTA.onProgress([this](unsigned int received, unsigned int total) {
        if (onProgress) onProgress(received, total);
    });
    ArduinoOTA.onEnd([this]() {
        if (onEnd) onEnd();
    });
    ArduinoOTA.onError([this](ota_error_t err) {
        if (onError) onError(errorName(err));
        if (_state == UPDATING) {
            _state = READY;
        }
    });

    ArduinoOTA.begin();
    _armed = true;
}

void OtaManager::poll(void) {
    if (_state == OFF || _state == FAILED) {
        return;
    }

    if (_state == UPDATING) {
        if (_armed) {
            ArduinoOTA.handle();
        }
        return;
    }

    const bool connected = (WiFi.status() == WL_CONNECTED);
    if (connected) {
        if (!_everReady) {
            _everReady = true;
            WiFi.setAutoReconnect(true);
        }
        if (!_armed) {
            arm();
        }
        _state = READY;
        if (_armed) {
            ArduinoOTA.handle();
        }
        return;
    }

    if (_everReady) {
        _state = CONNECTING;
        return;
    }

    _state = CONNECTING;
    if (_connectTimeoutMs != 0 &&
        (millis() - _connectStartedMs) >= _connectTimeoutMs) {
        failJoin_("WiFi: can't connect");
    }
}

IPAddress OtaManager::ip(void) const {
    return WiFi.localIP();
}

#else

void OtaManager::begin(const char*, const char*, const char*, uint32_t) { _state = OFF; }
void OtaManager::poll(void) {}
void OtaManager::arm(void) {}
void OtaManager::failJoin_(const char*) { _state = FAILED; }
IPAddress OtaManager::ip(void) const { return IPAddress(); }

#endif
