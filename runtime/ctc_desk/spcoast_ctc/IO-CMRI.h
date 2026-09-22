#ifndef SPCOAST_IO_CMRI_H
#define SPCOAST_IO_CMRI_H

#include <drivers/CmriIOBus.h>
#include <cTcMachine.h>

// C/MRI backend: each column is one input byte + one output byte in the image.
// Wire the host CMRI stack to fill/drain these buffers before syncInputs/Outputs.
class PanelIO : public FieldUnit::PanelHardware {
public:
    static constexpr uint8_t kColumnCount = 14;

    PanelIO() : cmriBus_(inputImage_, kColumnCount, outputImage_, kColumnCount) {
        for (uint8_t i = 0; i < kColumnCount; ++i) {
            inputImage_[i] = 0;
            outputImage_[i] = 0;
            codeButtonLast_[i] = false;
        }
    }

    static uint8_t colToByteOffset(uint8_t col) {
        return (col > 0) ? static_cast<uint8_t>(col - 1) : 0;
    }

    static FieldUnit::InputBit inputBit(uint8_t byteOffset, uint8_t bitIndex) {
        return FieldUnit::InputBit(/*device=*/0, byteOffset, bitIndex);
    }

    static FieldUnit::OutputBit outputBit(uint8_t byteOffset, uint8_t bitIndex) {
        return FieldUnit::OutputBit(/*device=*/0, byteOffset, bitIndex);
    }

    bool read(uint8_t col, FieldUnit::PanelInput fn) override {
        uint8_t byteOffset = colToByteOffset(col);
        switch (fn) {
            case FieldUnit::PanelInput::SW_NORMAL:
                return cmriBus_.readBit(inputBit(byteOffset, 6));
            case FieldUnit::PanelInput::SW_REVERSE:
                return cmriBus_.readBit(inputBit(byteOffset, 7));
            case FieldUnit::PanelInput::SIG_LEFT:
                return cmriBus_.readBit(inputBit(byteOffset, 1)); // bit 9 -> next byte in old map; keep simple single-byte map
            case FieldUnit::PanelInput::SIG_STOP:
                return cmriBus_.readBit(inputBit(byteOffset, 2));
            case FieldUnit::PanelInput::SIG_RIGHT:
                return cmriBus_.readBit(inputBit(byteOffset, 3));
            case FieldUnit::PanelInput::CODE_BUTTON: {
                bool now = cmriBus_.readBit(inputBit(byteOffset, 4));
                bool rose = now && !codeButtonLast_[byteOffset];
                codeButtonLast_[byteOffset] = now;
                return rose;
            }
            case FieldUnit::PanelInput::MAINTAINER_CALL_SW:
                return cmriBus_.readBit(inputBit(byteOffset, 2));
            default:
                return false;
        }
    }

    void write(uint8_t col, FieldUnit::PanelOutput fn, bool state) override {
        uint8_t byteOffset = colToByteOffset(col);
        switch (fn) {
            case FieldUnit::PanelOutput::SW_NORMAL_LAMP:
                cmriBus_.writeBit(outputBit(byteOffset, 0), state);
                break;
            case FieldUnit::PanelOutput::SW_REVERSE_LAMP:
                cmriBus_.writeBit(outputBit(byteOffset, 1), state);
                break;
            case FieldUnit::PanelOutput::TRACK_LAMP_1:
                cmriBus_.writeBit(outputBit(byteOffset, 3), state);
                break;
            case FieldUnit::PanelOutput::TRACK_LAMP_2:
                cmriBus_.writeBit(outputBit(byteOffset, 4), state);
                break;
            case FieldUnit::PanelOutput::TRACK_LAMP_3:
                cmriBus_.writeBit(outputBit(byteOffset, 5), state);
                break;
            case FieldUnit::PanelOutput::MAINTAINER_LAMP:
                cmriBus_.writeBit(outputBit(byteOffset, 2), state);
                break;
            case FieldUnit::PanelOutput::SIG_LEFT_LAMP:
                cmriBus_.writeBit(outputBit(byteOffset, 5), state);
                break;
            case FieldUnit::PanelOutput::SIG_RIGHT_LAMP:
                cmriBus_.writeBit(outputBit(byteOffset, 6), state);
                break;
            case FieldUnit::PanelOutput::SIG_STOP_LAMP:
                cmriBus_.writeBit(outputBit(byteOffset, 7), state);
                break;
            default:
                break;
        }
    }

    void begin() override {}
    void syncInputs() override {}
    void syncOutputs() override {}

    // Expose images for an external C/MRI poller to fill/drain.
    uint8_t* inputImage() { return inputImage_; }
    uint8_t* outputImage() { return outputImage_; }
    size_t imageLength() const { return kColumnCount; }

private:
    uint8_t inputImage_[kColumnCount];
    uint8_t outputImage_[kColumnCount];
    FieldUnit::CmriIOBus cmriBus_;
    bool codeButtonLast_[kColumnCount];
};

#endif // SPCOAST_IO_CMRI_H
