#ifndef SPCOAST_IO_I2C_H
#define SPCOAST_IO_I2C_H

#include <Wire.h>
#include <I2Cexpander.h>
#include <drivers/I2CexpanderIOBus.h>
#include <cTcMachine.h>

// Physical desk I/O: one MAX7313 (or compatible) expander per Model 503 column.
// FieldUnit I2CexpanderIOBus binds an array of I2Cexpander chips; device index
// in InputBit/OutputBit is the array index (column-1), not the I2C address.
class PanelIO : public FieldUnit::PanelHardware {
public:
    static constexpr uint8_t kColumnCount = 14;
    // Historical SPCoast map: column 1 -> expander address 4 ... column 14 -> 17
    static constexpr uint8_t kBaseI2cAddress = 4;
    // 0xFFFF = all pins as inputs at chip init; direction is set by later use.
    // MAX7313 direction is managed by the I2Cexpander driver from read/write use.
    static constexpr uint16_t kExpanderConfig = 0xFFFF;

    PanelIO() : i2cBus_(expanders_, kColumnCount) {
        for (uint8_t i = 0; i < kColumnCount; ++i) {
            codeButtonLast_[i] = false;
        }
    }

    static uint8_t colToDevice(uint8_t col) {
        // columns are 1..14
        if (col < 1) {
            return 0;
        }
        if (col > kColumnCount) {
            return kColumnCount - 1;
        }
        return static_cast<uint8_t>(col - 1);
    }

    // Map expander pin 0..15 -> IOBus (offset, bitIndex)
    static FieldUnit::InputBit inputPin(uint8_t device, uint8_t pin,
                                        FieldUnit::Polarity pol = FieldUnit::Polarity::NORMAL) {
        return FieldUnit::InputBit(device, pin / 8, pin % 8, pol);
    }

    static FieldUnit::OutputBit outputPin(uint8_t device, uint8_t pin,
                                          FieldUnit::Polarity pol = FieldUnit::Polarity::NORMAL) {
        return FieldUnit::OutputBit(device, pin / 8, pin % 8, pol);
    }

    bool read(uint8_t col, FieldUnit::PanelInput fn) override {
        uint8_t dev = colToDevice(col);
        switch (fn) {
            case FieldUnit::PanelInput::SW_NORMAL:
                return i2cBus_.readBit(inputPin(dev, 6));
            case FieldUnit::PanelInput::SW_REVERSE:
                return i2cBus_.readBit(inputPin(dev, 7));
            case FieldUnit::PanelInput::SIG_LEFT:
                return i2cBus_.readBit(inputPin(dev, 9));
            case FieldUnit::PanelInput::SIG_STOP:
                return i2cBus_.readBit(inputPin(dev, 10));
            case FieldUnit::PanelInput::SIG_RIGHT:
                return i2cBus_.readBit(inputPin(dev, 11));
            case FieldUnit::PanelInput::CODE_BUTTON: {
                // Rising-edge latch (press). Hardware is typically active-high or
                // active-low depending on panel wiring; match prior active-high read.
                bool now = i2cBus_.readBit(inputPin(dev, 12));
                bool rose = now && !codeButtonLast_[dev];
                codeButtonLast_[dev] = now;
                return rose;
            }
            case FieldUnit::PanelInput::MAINTAINER_CALL_SW:
                return i2cBus_.readBit(inputPin(dev, 2));
            default:
                return false;
        }
    }

    void write(uint8_t col, FieldUnit::PanelOutput fn, bool state) override {
        uint8_t dev = colToDevice(col);
        switch (fn) {
            case FieldUnit::PanelOutput::SW_NORMAL_LAMP:
                i2cBus_.writeBit(outputPin(dev, 0), state);
                break;
            case FieldUnit::PanelOutput::SW_REVERSE_LAMP:
                i2cBus_.writeBit(outputPin(dev, 1), state);
                break;
            case FieldUnit::PanelOutput::TRACK_LAMP_1:
                i2cBus_.writeBit(outputPin(dev, 3), state);
                break;
            case FieldUnit::PanelOutput::TRACK_LAMP_2:
                i2cBus_.writeBit(outputPin(dev, 4), state);
                break;
            case FieldUnit::PanelOutput::TRACK_LAMP_3:
                i2cBus_.writeBit(outputPin(dev, 5), state);
                break;
            case FieldUnit::PanelOutput::MAINTAINER_LAMP:
                i2cBus_.writeBit(outputPin(dev, 8), state);
                break;
            case FieldUnit::PanelOutput::SIG_LEFT_LAMP:
                i2cBus_.writeBit(outputPin(dev, 13), state);
                break;
            case FieldUnit::PanelOutput::SIG_RIGHT_LAMP:
                i2cBus_.writeBit(outputPin(dev, 14), state);
                break;
            case FieldUnit::PanelOutput::SIG_STOP_LAMP:
                i2cBus_.writeBit(outputPin(dev, 15), state);
                break;
            default:
                break;
        }
    }

    void begin() override {
        Wire.begin();
        for (uint8_t i = 0; i < kColumnCount; ++i) {
            // Address matches historical colToDev = 3 + col = 4..17
            expanders_[i].init(
                static_cast<size_t>(kBaseI2cAddress + i),
                I2Cexpander::MAX7313,
                kExpanderConfig
            );
        }
    }

    void syncInputs() override {
        // I2Cexpander digitalRead hits the bus per pin; no batch cache required.
    }

    void syncOutputs() override {
        // digitalWrite is immediate on this driver.
    }

private:
    I2Cexpander expanders_[kColumnCount];
    FieldUnit::I2CexpanderIOBus i2cBus_;
    bool codeButtonLast_[kColumnCount];
};

#endif // SPCOAST_IO_I2C_H
