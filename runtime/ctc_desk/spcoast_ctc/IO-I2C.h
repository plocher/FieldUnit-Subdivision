#ifndef SPCOAST_IO_I2C_H
#define SPCOAST_IO_I2C_H

#include <Wire.h>
#include <drivers/I2CexpanderIOBus.h>
#include <cTcMachine.h>

class PanelIO : public FieldUnit::PanelHardware {
public:
    PanelIO() : i2cBus_(Wire) {}

    // Maps column 1..14 to its corresponding MAX7313 expander index (4..17)
    static uint8_t colToDev(uint8_t col) { return 3 + col; }

    bool read(uint8_t col, FieldUnit::PanelInput fn) override {
        uint8_t dev = colToDev(col);
        switch (fn) {
            case FieldUnit::PanelInput::SW_NORMAL:          return i2cBus_.input(dev, 6).read();
            case FieldUnit::PanelInput::SW_REVERSE:         return i2cBus_.input(dev, 7).read();
            case FieldUnit::PanelInput::SIG_LEFT:           return i2cBus_.input(dev, 9).read();
            case FieldUnit::PanelInput::SIG_STOP:           return i2cBus_.input(dev, 10).read();
            case FieldUnit::PanelInput::SIG_RIGHT:          return i2cBus_.input(dev, 11).read();
            case FieldUnit::PanelInput::CODE_BUTTON:        return i2cBus_.input(dev, 12).readRisingEdge();
            case FieldUnit::PanelInput::MAINTAINER_CALL_SW: return i2cBus_.input(dev, 2).read();
            default: return false;
        }
    }

    void write(uint8_t col, FieldUnit::PanelOutput fn, bool state) override {
        uint8_t dev = colToDev(col);
        switch (fn) {
            case FieldUnit::PanelOutput::SW_NORMAL_LAMP:  i2cBus_.output(dev, 0).write(state); break;
            case FieldUnit::PanelOutput::SW_REVERSE_LAMP: i2cBus_.output(dev, 1).write(state); break;
            case FieldUnit::PanelOutput::TRACK_LAMP_1:    i2cBus_.output(dev, 3).write(state); break;
            case FieldUnit::PanelOutput::TRACK_LAMP_2:    i2cBus_.output(dev, 4).write(state); break;
            case FieldUnit::PanelOutput::TRACK_LAMP_3:    i2cBus_.output(dev, 5).write(state); break;
            case FieldUnit::PanelOutput::MAINTAINER_LAMP: i2cBus_.output(dev, 8).write(state); break;
            case FieldUnit::PanelOutput::SIG_LEFT_LAMP:   i2cBus_.output(dev, 13).write(state); break;
            case FieldUnit::PanelOutput::SIG_RIGHT_LAMP:  i2cBus_.output(dev, 14).write(state); break;
            case FieldUnit::PanelOutput::SIG_STOP_LAMP:   i2cBus_.output(dev, 15).write(state); break;
            default: break;
        }
    }

    void begin() override { Wire.begin(); i2cBus_.begin(); }
    void syncInputs() override  { i2cBus_.readInputs(); }
    void syncOutputs() override { i2cBus_.writeOutputs(); }

private:
    FieldUnit::I2CexpanderIOBus i2cBus_;
};

#endif // SPCOAST_IO_I2C_H
