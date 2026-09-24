#ifndef SPCOAST_IO_I2C_H
#define SPCOAST_IO_I2C_H

#include <Wire.h>
#include <I2Cexpander.h>
#include <cTcMachine.h>

// Hardware edge latch for CODE: high-level code must run once per press.
// Debounce belongs in the I2C sample path; OneShot only enforces single-fire.
//
//   WAITING  --press-->  ARMED  --release-->  TRIGGERED  --consume-->  WAITING
//
// TRIGGERED latches until consume(), so a slow pollCode loop cannot miss it.
class CodeOneShot {
public:
    enum class State : uint8_t { Waiting = 0, Armed, Triggered };

    CodeOneShot() : state_(State::Waiting) {}

    void update(bool isPressed) {
        switch (state_) {
            case State::Waiting:
                if (isPressed) {
                    state_ = State::Armed;
                }
                break;
            case State::Armed:
                if (!isPressed) {
                    state_ = State::Triggered;
                }
                break;
            case State::Triggered:
                // Latched until consume().
                break;
        }
    }

    State state() const { return state_; }
    bool isTriggered() const { return state_ == State::Triggered; }

    void reset() { state_ = State::Waiting; }

    // True once per press/release cycle; clears the latch.
    bool consume() {
        if (!isTriggered()) {
            return false;
        }
        reset();
        return true;
    }

private:
    State state_;
};

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
    // I2C-side contact debounce before feeding OneShot (ms of stable level).
    static constexpr uint32_t kCodeDebounceMs = 25;

    PanelIO() {
        for (uint8_t i = 0; i < kColumnCount; ++i) {
            inputCache_[i] = 0;
            outputCache_[i] = 0;
            codeRaw_[i] = false;
            codeStable_[i] = false;
            codeChangeMs_[i] = 0;
        }
    }

    static uint8_t colToDevice(uint8_t col) {
        if (col < 1) return 0;
        if (col > kColumnCount) return static_cast<uint8_t>(kColumnCount - 1);
        return static_cast<uint8_t>(col - 1);
    }

    // Direct access for cTc / tests that want explicit consume semantics.
    CodeOneShot& codeOneShot(uint8_t col) { return codeOneShot_[colToDevice(col)]; }
    const CodeOneShot& codeOneShot(uint8_t col) const {
        return codeOneShot_[colToDevice(col)];
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
            case FieldUnit::PanelInput::CODE_BUTTON:
                // pollCode reads CODE_BUTTON once per column; consume here so
                // high-level code runs exactly once per press/release cycle.
                return codeOneShot_[dev].consume();
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
        sampleCodeContacts(/*force=*/true);
    }

    void syncInputs() override {
        nowMs_ = millis();
        for (uint8_t i = 0; i < kColumnCount; ++i) {
            inputCache_[i] = static_cast<uint16_t>(expanders_[i].get());
        }
        sampleCodeContacts(/*force=*/false);
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
    // CODE is active-low on the panel (closed / pressed = 0 on the pin).
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

    // Debounce CODE contacts in the I2C path, then drive OneShot.
    void sampleCodeContacts(bool force) {
        for (uint8_t i = 0; i < kColumnCount; ++i) {
            bool raw = codePressedRaw(inputCache_[i]);
            if (force) {
                codeRaw_[i] = raw;
                codeStable_[i] = raw;
                codeChangeMs_[i] = nowMs_;
                codeOneShot_[i].reset();
                // If already held at boot, arm so a later release can trigger.
                codeOneShot_[i].update(codeStable_[i]);
                continue;
            }

            if (raw != codeRaw_[i]) {
                codeRaw_[i] = raw;
                codeChangeMs_[i] = nowMs_;
            } else if (raw != codeStable_[i]
                       && (nowMs_ - codeChangeMs_[i]) >= kCodeDebounceMs) {
                codeStable_[i] = raw;
            }

            codeOneShot_[i].update(codeStable_[i]);
        }
    }

    I2Cexpander expanders_[kColumnCount];
    uint16_t inputCache_[kColumnCount];
    uint16_t outputCache_[kColumnCount];

    bool codeRaw_[kColumnCount];
    bool codeStable_[kColumnCount];
    uint32_t codeChangeMs_[kColumnCount];
    CodeOneShot codeOneShot_[kColumnCount];
    uint32_t nowMs_ = 0;
};

#endif // SPCOAST_IO_I2C_H
