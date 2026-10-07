#!/usr/bin/env python3
"""Pass 1: RailroadField.kicad_sym to the ADR 0003 Kind table (FieldUnit docs/adr/0003-field-io-symbols.md).

Renames, re-Kinds and re-pins the field symbols in place (graphics kept), adds the
polarity and tunable attributes, deletes the retired symbols, adds Local-Lamp
packagings cloned from RailroadPanel:PanelLamp-AMBER without its Column pin.
Channel types (BIT/DUTY/ANGLE) are not written to the library: they are a column
of the (Role, Kind) table, keyed by Kind and pin, so they have one source.

Usage: python3 pass1_field_library.py [--dry-run]
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from symlib_edit import (add_prop, del_pin, del_prop, edit_pin, get_prop, join, pin_names, rename,  # noqa: E402
                         set_prop, set_text, split)

LIBDIR = Path.home() / "Dropbox/KiCad/InterlockingPlant/symbols"
FIELD = LIBDIR / "RailroadField.kicad_sym"
PANEL = LIBDIR / "RailroadPanel.kicad_sym"

DELETE = {"Device-Switch-ElectricLock", "Device-Switch-HandThrow", "Device-Signal-1LED_PWM",
          "Local-Lock_No_Lamps"}


def bar(x):
    return "~{" + x + "}"


def make(b, src, new, role, kind, pins=(), drop=(), attrs=(), text=None):
    """pins: (number, name[, new_number[, etype]]); drop: pin numbers; attrs: (key, value)."""
    b = rename(b, src, new) if src != new else b
    b = set_prop(b, "Role", role)
    b = set_prop(b, "Kind", kind)
    b = del_prop(b, "Polarity")
    for n in drop:
        b = del_pin(b, n)
    for p in pins:
        num, name, *rest = p
        b = edit_pin(b, num, name=name, new_number=rest[0] if rest else None,
                     etype=rest[1] if len(rest) > 1 else None)
    # one blank polarity attribute per asserted pin base name, then tunables
    seen = []
    for n in pin_names(b):
        base = re.sub(r"^~\{(.*)\}$", r"\1", n)
        if (n != base or base in ("WLK",)) and base not in seen:
            seen.append(base)
    for base in seen:
        b = add_prop(b, base, "")
    for k, v in attrs:
        b = add_prop(b, k, v) if get_prop(b, k) is None else set_prop(b, k, v)
    if text:
        b = set_text(b, *text)
    return b


def main(dry):
    head, blocks, tail = split(FIELD.read_text())
    src = dict(blocks)
    panel = dict(split(PANEL.read_text())[1])
    D, P, IO = "DEVICE", "PANEL", "IODRIVER"
    servo = (("NormalIs", "LOW_ANGLE"), ("Normal_deg", ""), ("Reverse_deg", ""), ("Speed", ""))
    new = [
        make(src["Device-Switch-Manual"], "Device-Switch-Manual", "Device-Switch-Sense", D, "SWITCH_SENSE",
             pins=[("1", bar("N")), ("2", bar("R"))]),
        make(src["Device-Switch-StallMotor"], "Device-Switch-StallMotor", "Device-Switch-StallMotor-Sim", D,
             "SWITCH_STALL_SIM", drop=["2", "3"], attrs=[("NormalIs", "HIGH"), ("Travel_ms", "2000")]),
        make(src["Device-Switch-StallMotor"], "Device-Switch-StallMotor", "Device-Switch-StallMotor-Sensed", D,
             "SWITCH_STALL_SENSED", pins=[("2", bar("N")), ("3", bar("R"))], attrs=[("NormalIs", "HIGH")]),
        make(src["Device-Switch-Turtle"], "Device-Switch-Turtle", "Device-Switch-StallMotor-Sensed-OS", D,
             "SWITCH_STALL_SENSED", pins=[("2", bar("N")), ("3", bar("R")), ("4", bar("OCC"))],
             attrs=[("NormalIs", "HIGH")]),
        make(src["Device-Servo_PWM"], "Device-Servo_PWM", "Device-Switch-Servo-Sim", D, "SWITCH_SERVO_SIM",
             pins=[("1", "CH")], attrs=servo),
        make(src["Device-Switch-StallMotor"], "Device-Switch-StallMotor", "Device-Switch-Servo-Sensed", D,
             "SWITCH_SERVO_SENSED", pins=[("1", "CH"), ("2", bar("N")), ("3", bar("R"))], attrs=servo,
             text=("SW ${VALUE}", "Servo ${VALUE}")),
        make(src["Device-TrackCircuit"], "Device-TrackCircuit", "Device-Detector-Optical", D, "DETECTOR_OPTICAL",
             pins=[("1", bar("OCC"))], attrs=[("Hold_ms", "1500")]),
        make(src["Device-TrackCircuit"], "Device-TrackCircuit", "Device-Detector-Current", D, "DETECTOR_CURRENT",
             pins=[("1", bar("OCC"))]),
        make(src["Device-Signal-3LED"], "Device-Signal-3LED", "Device-Head-3LED", D, "HEAD_3LED",
             pins=[("1", bar("R")), ("2", bar("Y")), ("3", bar("G"))]),
        make(src["Device-Signal-3LED_2MUX"], "Device-Signal-3LED_2MUX", "Device-Head-3LED-Mux2", D, "HEAD_3LED_MUX2",
             pins=[("1", bar("S0")), ("2", bar("S1"))]),
        make(src["Device-Signal-3LED_PWM"], "Device-Signal-3LED_PWM", "Device-Head-3LED-PWM", D, "HEAD_3LED_PWM",
             attrs=[("Fade_ms", "")]),
        make(src["Device-Signal-Semaphore_2PWM"], "Device-Signal-Semaphore_2PWM", "Device-Head-Semaphore-Servo", D,
             "HEAD_SEMAPHORE_SERVO", attrs=[("Stop_deg", ""), ("Approach_deg", ""), ("Clear_deg", "")]),
        make(src["Device-Digital_Output"], "Device-Digital_Output", "Device-Lamp-Bit", D, "LAMP_BIT",
             pins=[("1", bar("OUT"))]),
        make(src["Device-Lamp-1LED_PWM"], "Device-Lamp-1LED_PWM", "Device-Lamp-PWM", D, "LAMP_PWM"),
        make(src["Device-Signal-1LED_NEO"], "Device-Signal-1LED_NEO", "Device-Lamp-NeoPixel", D, "LAMP_NEOPIXEL",
             attrs=[("Chain", ""), ("Index", "")]),
        make(src["Device-Digital_Input"], "Device-Digital_Input", "Device-Input-Bit", D, "INPUT_BIT",
             pins=[("1", bar("IN"))]),
        make(src["Local-Switch"], "Local-Switch", "Local-Switch", P, "SWITCH_LEVER",
             pins=[("1", bar("NWS")), ("2", bar("RWS")), ("3", bar("RWK")), ("4", bar("NWK"))]),
        make(src["Local-Switch_No_Lamps"], "Local-Switch_No_Lamps", "Local-Switch-NoLamp", P, "SWITCH_LEVER_NOLAMP",
             pins=[("1", bar("NWS")), ("2", bar("RWS"))]),
        # lever (old NWS position) asks to unlock; the R-side lamp shows unlocked
        make(src["Local-Lock"], "Local-Lock", "Local-Lock", P, "LOCK_LEVER", drop=["2", "4"],
             pins=[("1", bar("WLS")), ("3", bar("WLK"), "2")]),
        # second lamp (old NWK position) shows locked: the complement of WLK on its own channel
        make(src["Local-Lock"], "Local-Lock", "Local-Lock-2Lamp", P, "LOCK_LEVER_2LAMP", drop=["2"],
             pins=[("1", bar("WLS")), ("3", bar("WLK"), "2"), ("4", "WLK", "3")]),
        make(src["Device-I2C-IOx4"], "Device-I2C-IOx4", "Driver-I2C-MCP23017", IO, "MCP23017",
             attrs=[("Pullups", "ON")]),
        make(src["Device-I2C-PWMx4"], "Device-I2C-PWMx4", "Driver-I2C-PCA9685", IO, "PCA9685"),
    ]
    lamp = set_prop(set_prop(panel["PanelLamp-AMBER"], "Value", ""), "IndicationToken", "")
    lamp_bit = make(del_pin(lamp, "1"), "PanelLamp-AMBER", "Local-Lamp", P, "LAMP", pins=[("2", bar("LAMP"), "1")])
    lamp_pwm = make(del_pin(lamp, "1"), "PanelLamp-AMBER", "Local-Lamp-PWM", P, "LAMP", pins=[("2", "LAMP", "1")])
    lamp_neo = make(del_pin(del_pin(lamp, "1"), "2"), "PanelLamp-AMBER", "Local-Lamp-NeoPixel", P, "LAMP",
                    attrs=[("Chain", ""), ("Index", "")])
    for b in (lamp_bit, lamp_pwm, lamp_neo):
        assert get_prop(b, "Reference") == "LAMP"
    new += [lamp_bit, lamp_pwm, lamp_neo]

    consumed = {"Device-Switch-Manual", "Device-Switch-StallMotor", "Device-Switch-Turtle", "Device-Servo_PWM",
                "Device-TrackCircuit", "Device-Signal-3LED", "Device-Signal-3LED_2MUX", "Device-Signal-3LED_PWM",
                "Device-Signal-Semaphore_2PWM", "Device-Digital_Output", "Device-Lamp-1LED_PWM",
                "Device-Signal-1LED_NEO", "Device-Digital_Input", "Local-Switch", "Local-Switch_No_Lamps",
                "Local-Lock", "Device-I2C-IOx4", "Device-I2C-PWMx4"}
    left = set(src) - consumed - DELETE
    assert not left, f"unhandled symbols: {left}"
    named = [(re.match(r'\(symbol "([^"]+)"', b).group(1), b) for b in new]
    named.sort(key=lambda nb: nb[0])
    text = join(head, named, tail)
    for name, b in named:
        props = {k: v for k, v in re.findall(r'\n\t\t\(property "([^"]+)" "([^"]*)"', b)
                 if k not in ("Reference", "Value", "Footprint", "Datasheet", "Description")}
        print(f"{name:36} {props}  pins={pin_names(b)}")
    if not dry:
        FIELD.write_text(text)
        print("wrote", FIELD)


if __name__ == "__main__":
    main("--dry-run" in sys.argv)
