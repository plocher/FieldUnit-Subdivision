#ifndef SPCOAST_DESK_OLED_H
#define SPCOAST_DESK_OLED_H

#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Wire.h>

#include "IO-I2C.h"

// Compact 128x64 live view of the 14-column desk.
// Top: name, version, MQTT/I2C spinners, last error
// Body: rows MC | SW | SIG | CODE | MCL — one glyph column per panel column
class DeskOled {
public:
    static constexpr uint8_t kWidth = 128;
    static constexpr uint8_t kHeight = 64;
    static constexpr uint8_t kI2cAddress = 0x3C;
    static constexpr uint8_t kColumns = PanelIO::kColumnCount;

    enum class NetState : uint8_t { Off, Connecting, Ready, Failed };

    explicit DeskOled(PanelIO& io)
        : io_(io),
          display_(kWidth, kHeight, &Wire, /*rst=*/-1),
          ok_(false),
          txCount_(0),
          rxCount_(0),
          net_(NetState::Off),
          lastCodeStation_("-"),
          lastError_("") {}

    bool begin(const char* title) {
        title_ = title ? title : "SPCoast";
        ok_ = display_.begin(SSD1306_SWITCHCAPVCC, kI2cAddress);
        if (!ok_) {
            return false;
        }
        display_.clearDisplay();
        display_.setTextColor(SSD1306_WHITE);
        display_.setTextSize(1);
        display_.setCursor(0, 0);
        display_.println(title_);
        display_.println(F("OLED OK"));
        display_.display();
        return true;
    }

    void noteTx() { ++txCount_; }
    void noteRx() { ++rxCount_; }
    void setNet(NetState net) { net_ = net; }
    void setLastCode(const char* station) {
        lastCodeStation_ = station ? station : "-";
    }
    void setError(const char* err) { lastError_ = err ? err : ""; }

    void show() {
        if (!ok_) {
            return;
        }
        display_.clearDisplay();
        drawHeader();
        drawMatrix();
        drawFooter();
        display_.display();
    }

private:
    void drawHeader() {
        display_.setCursor(0, 0);
        display_.print(title_);
        display_.print(' ');
        display_.print(F("v1"));
        // Spinners from traffic counters
        static const char spin[] = {'|', '/', '-', '\\'};
        display_.setCursor(90, 0);
        display_.write(spin[txCount_ & 3]);
        display_.write(spin[rxCount_ & 3]);
        display_.setCursor(108, 0);
        switch (net_) {
            case NetState::Ready: display_.print(F("Up")); break;
            case NetState::Connecting: display_.print(F("..")); break;
            case NetState::Failed: display_.print(F("!")); break;
            default: display_.print(F("--")); break;
        }
        display_.drawFastHLine(0, 9, kWidth, SSD1306_WHITE);
    }

    void drawMatrix() {
        // Row labels + 14 column cells (6 px wide)
        const char* labels[] = {"MC", "SW", "SG", "CD", "ML"};
        const uint8_t rowY0 = 12;
        const uint8_t rowH = 8;
        const uint8_t gridX0 = 16;
        const uint8_t cellW = 7;

        for (uint8_t r = 0; r < 5; ++r) {
            uint8_t y = static_cast<uint8_t>(rowY0 + r * rowH);
            display_.setCursor(0, y);
            display_.print(labels[r]);
            for (uint8_t c = 0; c < kColumns; ++c) {
                uint16_t in = io_.inputImage(c);
                uint16_t out = io_.outputImage(c);
                bool on = false;
                switch (r) {
                    case 0: // MC switch input pin 2
                        on = ((in >> 2) & 1u) != 0;
                        break;
                    case 1: // Switch lever: N pin6 or R pin7
                        on = (((in >> 6) & 1u) | ((in >> 7) & 1u)) != 0;
                        break;
                    case 2: // Signal lever any of 9..11
                        on = (((in >> 9) & 1u) | ((in >> 10) & 1u) | ((in >> 11) & 1u)) != 0;
                        break;
                    case 3: // CODE pin12 active-low -> lit when pressed (0)
                        on = ((in >> 12) & 1u) == 0;
                        break;
                    case 4: // MC lamp out pin 8
                        on = ((out >> 8) & 1u) != 0;
                        break;
                    default:
                        break;
                }
                uint8_t x = static_cast<uint8_t>(gridX0 + c * cellW);
                if (on) {
                    display_.fillRect(x, y, 5, 6, SSD1306_WHITE);
                } else {
                    display_.drawRect(x, y, 5, 6, SSD1306_WHITE);
                }
            }
        }
    }

    void drawFooter() {
        display_.drawFastHLine(0, 54, kWidth, SSD1306_WHITE);
        display_.setCursor(0, 56);
        if (lastError_ && lastError_[0]) {
            display_.print(lastError_);
        } else {
            display_.print(F("code:"));
            display_.print(lastCodeStation_);
            display_.print(F(" tx"));
            display_.print(txCount_);
            display_.print(F(" rx"));
            display_.print(rxCount_);
        }
    }

    PanelIO& io_;
    Adafruit_SSD1306 display_;
    bool ok_;
    uint32_t txCount_;
    uint32_t rxCount_;
    NetState net_;
    const char* title_;
    const char* lastCodeStation_;
    const char* lastError_;
};

#endif // SPCOAST_DESK_OLED_H
