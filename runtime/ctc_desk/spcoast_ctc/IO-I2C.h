#ifndef SPCOAST_IO_I2C_H
#define SPCOAST_IO_I2C_H

#include <Wire.h>
#include <I2Cexpander.h>
#include <cTcMachine.h>

// Physical desk I/O: one MAX7313 per Model 503 column (I2C addr 4..17).
// Uses I2Cexpander 16-bit get()/put() once per sync — not per-bit digitalRead/Write.
//
// Pin map (per column expander, historical SPCoast):
//   Out: 0 N-lamp, 1 R-lamp, 3..5 track lamps, 8 MC lamp, 13..15 signal lamps
//   In:  2 MC switch, 6 N-lever, 7 R-lever, 9..11 signal lever, 12 CODE
class PanelIO : public FieldUnit::PanelHardware {
public:
    static constexpr uint8_t kColumnCount = 14;
    static constexpr uint8_t kBaseI2cAddress = 4;
    // 1-bits = inputs on MAX731x-style config word
    static constexpr uint16_t kInputMask =
        (1u << 2) | (1u << 6) | (1u << 7) |
        (1u << 9) | (1u << 10) | (1u << 11) | (1u << 12);
    static constexpr uint16_t kExpanderConfig = kInputMask;
    static constexpr uint32_t kCodeDebounceMs = 40;

    PanelIO() {
        for (uint8_t i = 0; i < kColumnCount; ++i) {
            inputCache_[i] = 0;
            outputCache_[i] = 0;
            codeStable_[i] = false;
            codeLastEmitted_[i] = false;
            codeChangeMs_[i] = 0;
            codeEdge_[i] = false;
        }
    }

    static uint8_t colToDevice(uint8_t col) {
        if (col < 1) return 0;
        if (col > kColumnCount) return static_cast<uint8_t>(kColumnCount - 1);
        return static_cast<uint8_t>(col - 1);
    }

    bool read(uint8_t col, FieldUnit::PanelInput fn) override {
        uint8_t dev = colToDevice(col);
        switch (fn) {
            case FieldUnit::PanelInput::SW_NORMAL:
                return readInputBit(dev, 6);
            case FieldUnit::PanelInput::SW_REVERSE:
                return readInputBit(dev, 7);
            case FieldUnit::PanelInput::SIG_LEFT:
                return readInputBit(dev, 9);
            case FieldUnit::PanelInput::SIG_STOP:
                return readInputBit(dev, 10);
            case FieldUnit::PanelInput::SIG_RIGHT:
                return readInputBit(dev, 11);
            case FieldUnit::PanelInput::CODE_BUTTON: {
                // One-shot edge for cTcMachine::pollCode (level re-fires every loop).
                bool edge = codeEdge_[dev];
                codeEdge_[dev] = false;
                return edge;
            }
            case FieldUnit::PanelInput::MAINTAINER_CALL_SW:
                return readInputBit(dev, 2);
            default:
                return false;
        }
    }

    void write(uint8_t col, FieldUnit::PanelOutput fn, bool state) override {
        uint8_t dev = colToDevice(col);
        switch (fn) {
            case FieldUnit::PanelOutput::SW_NORMAL_LAMP:
                writeOutputBit(dev, 0, state); break;
            case FieldUnit::PanelOutput::SW_REVERSE_LAMP:
                writeOutputBit(dev, 1, state); break;
            case FieldUnit::PanelOutput::TRACK_LAMP_1:
                writeOutputBit(dev, 3, state); break;
            case FieldUnit::PanelOutput::TRACK_LAMP_2:
                writeOutputBit(dev, 4, state); break;
            case FieldUnit::PanelOutput::TRACK_LAMP_3:
                writeOutputBit(dev, 5, state); break;
            case FieldUnit::PanelOutput::MAINTAINER_LAMP:
                writeOutputBit(dev, 8, state); break;
            case FieldUnit::PanelOutput::SIG_LEFT_LAMP:
                writeOutputBit(dev, 13, state); break;
            case FieldUnit::PanelOutput::SIG_RIGHT_LAMP:
                writeOutputBit(dev, 14, state); break;
            case FieldUnit::PanelOutput::SIG_STOP_LAMP:
                writeOutputBit(dev, 15, state); break;
            default: break;
        }
    }

    void begin() override {
        Wire.begin();
        for (uint8_t i = 0; i < kColumnCount; ++i) {
            expanders_[i].init(
                static_cast<size_t>(kBaseI2cAddress + i),
                I2Cexpander::MAX7313,
                kExpanderConfig
            );
            inputCache_[i] = static_cast<uint16_t>(expanders_[i].get());
            outputCache_[i] = 0;
            expanders_[i].put(outputCache_[i]);
        }
        nowMs_ = millis();
        sampleCodeButtons(true);
    }

    void syncInputs() override {
        nowMs_ = millis();
        for (uint8_t i = 0; i < kColumnCount; ++i) {
            inputCache_[i] = static_cast<uint16_t>(expanders_[i].get());
        }
        sampleCodeButtons(false);
    }

    void syncOutputs() override {
        for (uint8_t i = 0; i < kColumnCount; ++i) {
            expanders_[i].put(outputCache_[i]);
        }
    }

    uint16_t inputImage(uint8_t device) const {
        return (device < kColumnCount) ? inputCache_[device] : 0;
    }
    uint16_t outputImage(uint8_t device) const {
        return (device < kColumnCount) ? outputCache_[device] : 0;
    }
    uint8_t columnCount() const { return kColumnCount; }

private:
    // CODE is active-low on the panel (closed = 0).
    static bool codePressedRaw(uint16_t image) {
        return ((image >> 12) & 0x1u) == 0;
    }

    bool readInputBit(uint8_t device, uint8_t pin) const {
        return ((inputCache_[device] >> pin) & 0x1u) != 0;
    }

    void writeOutputBit(uint8_t device, uint8_t pin, bool state) {
        if (state) {
            outputCache_[device] = static_cast<uint16_t>(outputCache_[device] | (1u << pin));
        } else {
            outputCache_[device] = static_cast<uint16_t>(outputCache_[device] & ~(1u << pin));
        }
    }

    void sampleCodeButtons(bool force) {
        for (uint8_t i = 0; i < kColumnCount; ++i) {
            bool rawPressed = codePressedRaw(inputCache_[i]);
            if (force) {
                codeStable_[i] = rawPressed;
                codeLastEmitted_[i] = rawPressed;
                codeChangeMs_[i] = nowMs_;
                codeEdge_[i] = false;
                continue;
            }
            if (rawPressed != codeStable_[i]) {
                if (nowMs_ - codeChangeMs_[i] >= kCodeDebounceMs) {
                    codeStable_[i] = rawPressed;
                    codeChangeMs_[i] = nowMs_;
                    if (codeStable_[i] && !codeLastEmitted_[i]) {
                        codeEdge_[i] = true;
                    }
                    codeLastEmitted_[i] = codeStable_[i];
                }
            } else {
                codeChangeMs_[i] = nowMs_;
            }
        }
    }

    I2Cexpander expanders_[kColumnCount];
    uint16_t inputCache_[kColumnCount];
    uint16_t outputCache_[kColumnCount];
    bool codeStable_[kColumnCount];
    bool codeLastEmitted_[kColumnCount];
    bool codeEdge_[kColumnCount];
    uint32_t codeChangeMs_[kColumnCount];
    uint32_t nowMs_ = 0;
};

#endif // SPCOAST_IO_I2C_H
