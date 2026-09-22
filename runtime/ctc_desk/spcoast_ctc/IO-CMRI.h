#ifndef SPCOAST_IO_CMRI_H
#define SPCOAST_IO_CMRI_H

#include <drivers/CmriIOBus.h>
#include <cTcMachine.h>

class PanelIO : public FieldUnit::PanelHardware {
public:
    PanelIO() : cmriBus_(Serial1, /*nodeAddress=*/1) {}

    // In C/MRI, each column corresponds to 1 input byte and 1 output byte in the packet image
    static uint8_t colToByteOffset(uint8_t col) { return (col > 0) ? (col - 1) : 0; }

    bool read(uint8_t col, FieldUnit::PanelInput fn) override {
        uint8_t byteOffset = colToByteOffset(col);
        switch (fn) {
            case FieldUnit::PanelInput::SW_NORMAL:          return cmriBus_.readInputBit(byteOffset, 6);
            case FieldUnit::PanelInput::SW_REVERSE:         return cmriBus_.readInputBit(byteOffset, 7);
            case FieldUnit::PanelInput::SIG_LEFT:           return cmriBus_.readInputBit(byteOffset, 9);
            case FieldUnit::PanelInput::SIG_STOP:           return cmriBus_.readInputBit(byteOffset, 10);
            case FieldUnit::PanelInput::SIG_RIGHT:          return cmriBus_.readInputBit(byteOffset, 11);
            case FieldUnit::PanelInput::CODE_BUTTON:        return cmriBus_.readInputBit(byteOffset, 12);
            case FieldUnit::PanelInput::MAINTAINER_CALL_SW: return cmriBus_.readInputBit(byteOffset, 2);
            default: return false;
        }
    }

    void write(uint8_t col, FieldUnit::PanelOutput fn, bool state) override {
        uint8_t byteOffset = colToByteOffset(col);
        switch (fn) {
            case FieldUnit::PanelOutput::SW_NORMAL_LAMP:  cmriBus_.writeOutputBit(byteOffset, 0, state); break;
            case FieldUnit::PanelOutput::SW_REVERSE_LAMP: cmriBus_.writeOutputBit(byteOffset, 1, state); break;
            case FieldUnit::PanelOutput::TRACK_LAMP_1:    cmriBus_.writeOutputBit(byteOffset, 3, state); break;
            case FieldUnit::PanelOutput::TRACK_LAMP_2:    cmriBus_.writeOutputBit(byteOffset, 4, state); break;
            case FieldUnit::PanelOutput::TRACK_LAMP_3:    cmriBus_.writeOutputBit(byteOffset, 5, state); break;
            case FieldUnit::PanelOutput::MAINTAINER_LAMP: cmriBus_.writeOutputBit(byteOffset, 8, state); break;
            case FieldUnit::PanelOutput::SIG_LEFT_LAMP:   cmriBus_.writeOutputBit(byteOffset, 13, state); break;
            case FieldUnit::PanelOutput::SIG_RIGHT_LAMP:  cmriBus_.writeOutputBit(byteOffset, 14, state); break;
            case FieldUnit::PanelOutput::SIG_STOP_LAMP:   cmriBus_.writeOutputBit(byteOffset, 15, state); break;
            default: break;
        }
    }

    void begin() override { cmriBus_.begin(19200); }
    void syncInputs() override  { cmriBus_.pollNode(); }
    void syncOutputs() override { cmriBus_.transmitNode(); }

private:
    FieldUnit::CmriIOBus cmriBus_;
};

#endif // SPCOAST_IO_CMRI_H
