#!/usr/bin/env python3
"""Apply the symbol library recipe (checkpoint step 4) to the baseline libraries.

    python3 tools/contract/apply_symbol_recipe.py [--src DIR] [--out DIR] [--table]

Reads the three baseline libraries (Railroad, RailroadField, RailroadPanel, in the InterlockingPlant
repo) and writes the three new ones (RailroadPlant, RailroadDevice, RailroadDesk, in the Railroad
repo) by text-level edits that keep every untouched byte: rename a symbol, rename a pin, change a
pin's electrical type, add, rename or remove a property, copy a symbol. Two geometric edits: a
pin added to a symbol that has none (the RGB head), at the body's right edge; and the unit split,
one unit per capability on a device or plate whose pins mix them (lever contacts and lamps, drive
and sense, arm and lamp), with the body graphics in the shared unit 0 and the Value fixed in place so
that the units mesh on the sheet and show one name. Both are left for the visual pass to tidy.

Regeneration keeps hand work: every symbol named in HAND_FINISHED is carried over from the
existing output library, byte for byte, instead of the generated block. Finish a symbol in the
KiCad editor, add its name to the list, regenerate; the lint is the gate either way.

The recipe is the RECIPE list below, one entry per output symbol. It is the machine form of
docs/review/symbol-library-triage-2026-10-10.md; `--table` prints it as a markdown table so the
two can be compared. Rules it applies (triage §1): Kind removed from APPLIANCE, DEVICE, PANEL and
IODRIVER symbols; Appliance and Style added; IC on I/O symbols; one `Pin.<base>` capability per
function pin (the base name is the pin name without its `~{}`); per-pin override blanks and
ControlToken/Vital removed; settings renamed to lower_snake_case; `Invert` where a lamp shows a
token's complement.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kicad_services.sch_text import blocks, end_of, replace_spans  # noqa: E402

SRC = Path.home() / "Dropbox/KiCad/InterlockingPlant/symbols"
OUT = Path.home() / "Dropbox/KiCad/Railroad/symbols"
SOURCES = {"Railroad": "Railroad.kicad_sym", "RailroadField": "RailroadField.kicad_sym",
           "RailroadPanel": "RailroadPanel.kicad_sym"}
TARGETS = {"RailroadPlant": "Railroad", "RailroadDevice": "RailroadField", "RailroadDesk": "RailroadPanel"}
# Hand-finished in the KiCad editor; carried over from the existing output on every run.
HAND_FINISHED = {"RailroadDesk": ["PanelSwitch", "PanelSignal", "PanelLock"],
                 "RailroadDevice": ["Driver-I2C-PCA9685-PWM", "Driver-I2C-PCA9685-Servo"]}

BI, BO, BB = "binary in", "binary out", "binary bidirectional"
LI, LO = "level in", "level out"
PO, CO, PX = "position out", "color out", "pixel out"
EXPANDER = {f"{bank}{n}": BB for bank in "AB" for n in range(1, 9)}
PCA_PWM = {f"{bank}{n}": LO for bank in "AB" for n in range(1, 9)}
PCA_SERVO = {f"{bank}{n}": PO for bank in "AB" for n in range(1, 9)}

# One entry per output symbol. Keys:
#   src: (library, symbol)   out: library   name: output symbol name (default: source name)
#   role / appliance / style / ic: fields set   drop: fields removed   rename_fields: {old: new}
#   add: {field: value}   pins: {old pin name: new pin name or (new name, electrical type)}
#   caps: {pin base name: capability}   description: new Description text   add_pin: (name, etype, cap)
#   texts: {body text: replacement or None to delete}   (graphic labels that named a Kind or a domain)
#   keep_kind: leave Kind alone (TRACK, POLICY, STRUCTURE, CODELINE, MACHINE, COLUMN)
PLANT_KEEP = ["Bumper", "IRJ", "IRJ-END_CTC", "IRJ-Signal", "IRJ_Diag", "Interlocking", "MAIN HOUSE",
              "NextCP", "Rule105-RestrictedSpeed", "Rule251-DoT-Left", "Rule251-DoT-Right",
              "Rule261-DoT-BiDirectional", "Rule93-Yard Limits"]
DESK_KEEP = ["Codeline-Encoding-AAR", "Codeline-Encoding-Bits", "Codeline-Encoding-US&S-506",
             "Codeline-Transport-CMRInet", "Codeline-Transport-Loconet", "Codeline-Transport-MQTT",
             "Codeline-Transport-TimeCode", "CtcMachine", "PanelColumn"]
SWITCH_FIELDS = {"rename_fields": {"Indications": "IndicationCeiling"}, "drop": ["Kind"]}

RECIPE: list[dict] = []
P = RECIPE.append

# ---- plant --------------------------------------------------------------------------------
for s in PLANT_KEEP:
    P(dict(src=("Railroad", s), out="RailroadPlant", keep_kind=True))
P(dict(src=("Railroad", "Milepost"), out="RailroadPlant", role="TRACK", add={"Kind": "MILEPOST"}, keep_kind=True,
       description="Milepost: a track anchor carrying the milepost of the point it sits on."))
P(dict(src=("Railroad", "AUXILIARY"), out="RailroadPlant", appliance="lamp", style="non_vital", drop=["Kind"]))
P(dict(src=("Railroad", "AUXILIARY"), out="RailroadPlant", name="Contact", appliance="contact", drop=["Kind"],
       description="Contact: the generic non-vital input the office may see as <Value>K. "
                   "Style says who consumes it (lock_request, button, door, ...). Complement of AUXILIARY."))
P(dict(src=("Railroad", "MaintainerCall"), out="RailroadPlant", appliance="lamp", style="maintainer_call", drop=["Kind"]))
for s, st in (("Mast_Single", "single"), ("Mast_Double", "double"), ("Mast_Dwarf", "dwarf")):
    P(dict(src=("Railroad", s), out="RailroadPlant", appliance="mast", style=st, drop=["Kind"]))
P(dict(src=("Railroad", "Signal Head - CL"), out="RailroadPlant", role="APPLIANCE", appliance="head", style="CL", drop=["Kind"]))
P(dict(src=("Railroad", "Signal Head - CL"), out="RailroadPlant", name="Signal Head - Searchlight", role="APPLIANCE", appliance="head",
       style="searchlight", drop=["Kind"], description="Searchlight signal head: one lamp behind a moving coloured roundel; one colour at a time (E47)."))
P(dict(src=("Railroad", "Signal Head - SemaphoreU2"), out="RailroadPlant", name="Signal Head - SemaphoreLQ2",
       role="APPLIANCE", appliance="head", style="semaphore_lq", drop=["Kind"],
       description="Lower-quadrant semaphore head, two positions: STOP (horizontal) and CLEAR (arm dropped). "
                   "The aspect set is an era fact; see FieldUnit's primer section 17."))
P(dict(src=("Railroad", "Signal Head - SemaphoreU3"), out="RailroadPlant", name="Signal Head - SemaphoreUQ3",
       role="APPLIANCE", appliance="head", style="semaphore_uq", drop=["Kind"],
       description="Upper-quadrant semaphore head, three positions: STOP (horizontal), APPROACH (45 degrees), "
                   "CLEAR (vertical). The aspect set is an era fact; see FieldUnit's primer section 17."))
for s in ("Switch_Powered", "Switch_Powered_Diag", "Switch_Powered_NO_TC", "Switch_Powered_Small"):
    P(dict(src=("Railroad", s), out="RailroadPlant", appliance="switch", style="powered", **SWITCH_FIELDS))
P(dict(src=("Railroad", "Switch_Lock"), out="RailroadPlant", appliance="switch", style="lock", **SWITCH_FIELDS))
P(dict(src=("Railroad", "Switch_Manual"), out="RailroadPlant", appliance="switch", style="manual", **SWITCH_FIELDS))
P(dict(src=("Railroad", "Switch_Manual_Sensed"), out="RailroadPlant", appliance="switch", style="manual_sensed", **SWITCH_FIELDS))
P(dict(src=("Railroad", "Switch_Powered_Derail"), out="RailroadPlant", name="Derail", appliance="switch", style="derail", **SWITCH_FIELDS))
P(dict(src=("Railroad", "Switch_Powered_Derail_TC"), out="RailroadPlant", name="Derail_TC", appliance="switch", style="derail", **SWITCH_FIELDS))
for s in ("Track Circuit", "Track Circuit_RED", "Track Circuit_Yellow"):
    P(dict(src=("Railroad", s), out="RailroadPlant", appliance="track_circuit", drop=["Kind"]))
P(dict(src=("Railroad", "Virtual Indication"), out="RailroadPlant", name="Track Circuit_Virtual",
       appliance="track_circuit", style="virtual", drop=["Kind"],
       description="Virtual track circuit: an indication (Value, e.g. 0100T) that aggregates the circuits "
                   "listed in IndicationToken. No hardware; the plant compiler derives it."))

# ---- device -------------------------------------------------------------------------------
F = "RailroadField"
P(dict(src=(F, "Device-Detector-Current"), out="RailroadDevice", name="Device-TrackCircuit-Current",
       appliance="track_circuit", drop=["Kind", "OCC"], caps={"OCC": BI}))
P(dict(src=(F, "Device-Detector-Optical"), out="RailroadDevice", name="Device-TrackCircuit-Optical",
       appliance="track_circuit", drop=["Kind", "OCC"], rename_fields={"Hold_ms": "hold_ms"}, caps={"OCC": BI}))
P(dict(src=(F, "Device-Head-3LED"), out="RailroadDevice", name="Device-Head-CL-3Lamp",
       appliance="head", style="CL", drop=["Kind", "R", "Y", "G"], caps={"R": BO, "Y": BO, "G": BO},
       description="Colour-light head realised as three lamps, one wire each. Brightness and fade are the "
                   "two-point cast's settings when a lamp lands on a level-out pin."))
P(dict(src=(F, "Device-Head-3LED-Mux2"), out="RailroadDevice", name="Device-Head-CL-Mux2",
       appliance="head", style="CL", drop=["Kind"], caps={"S0": BO, "S1": BO},
       description="Colour-light head driven by a two-bit select code; the decoder on the head is field hardware."))
P(dict(src=(F, "Device-Head-1LED-NeoPixel"), out="RailroadDevice", name="Device-Head-CL-RGB",
       appliance="head", style="CL", drop=["Kind", "Chain", "Index"], add={"Address": ""},
       add_pin=("RGB", "input", CO), texts={"NeoPixel ${VALUE}": "RGB ${VALUE}", "Chain": None, "Index": None},
       description="Colour-light head realised as one lamp of dynamic colour (an RGB LED). Its RGB pin lands "
                   "on a pixel bus with an Address, or on any colour-out pin."))
P(dict(src=(F, "Device-Head-1LED-NeoPixel"), out="RailroadDevice", name="Device-Head-Searchlight",
       appliance="head", style="searchlight", drop=["Kind", "Chain", "Index"], add={"Address": "", "transition_ms": ""},
       add_pin=("RGB", "input", CO), texts={"NeoPixel ${VALUE}": "SL ${VALUE}", "Chain": None, "Index": None},
       description="Searchlight head: one RGB LED imitating a vane of coloured glass moving in front of a "
                   "white lamp. The vane is in the rendering (transition_ms), not in a pin."))
P(dict(src=(F, "Device-Head-Semaphore-Servo"), out="RailroadDevice", name="Device-Head-Semaphore",
       appliance="head", style="semaphore_lq, semaphore_uq", drop=["Kind"],
       rename_fields={"Stop_deg": "stop_deg", "Approach_deg": "approach_deg", "Clear_deg": "clear_deg"},
       pins={"LAMP": "~{LAMP}"}, caps={"ARM": PO, "LAMP": BO},
       description="Semaphore head: ARM is a position, ~{LAMP} the arm's lamp. Serves both quadrants; "
                   "the Style on the plant head fixes the aspect set."))
P(dict(src=(F, "Device-Input-Bit"), out="RailroadDevice", name="Device-Contact",
       appliance="contact", drop=["Kind", "IN"], caps={"IN": BI}, texts={"I/O ${VALUE}": "CONTACT ${VALUE}"},
       description="Contact: one binary input, the device of the Contact appliance."))
P(dict(src=(F, "Device-Lamp-Bit"), out="RailroadDevice", name="Device-Lamp",
       appliance="lamp", drop=["Kind", "OUT"], add={"Address": ""}, pins={"~{OUT}": "~{LAMP}"}, caps={"LAMP": BO},
       texts={"I/O ${VALUE}": "LAMP ${VALUE}"},
       description="Lamp: one binary output, lit or dark. On a level-out pin the two-point cast gives brightness "
                   "and fade; on a pixel bus it carries an Address and the one-point cast gives its colour."))
P(dict(src=(F, "Device-Switch-Sense"), out="RailroadDevice", name="Device-Switch-ManualSensed",
       appliance="switch", style="manual_sensed", drop=["Kind", "N", "R"], caps={"N": BI, "R": BI}))
P(dict(src=(F, "Device-Switch-StallMotor-Sensed"), out="RailroadDevice", name="Device-Switch",
       appliance="switch", style="powered, lock", drop=["Kind", "N", "R", "NormalIs"],
       caps={"M": BO, "N": BI, "R": BI},
       description="Switch machine: M is a binary demand (asserted = REVERSE), ~{N} and ~{R} the point contacts. "
                   "One device for a stall motor, a PWM motor and a servo: the cast on M's wire decides."))
P(dict(src=(F, "Device-Switch-StallMotor-Sensed-OS"), out="RailroadDevice", name="Device-Switch-OS",
       appliance="switch", style="powered, lock", drop=["Kind", "N", "R", "OCC", "NormalIs"],
       caps={"M": BO, "N": BI, "R": BI, "OCC": BI},
       description="Switch machine with its OS circuit detector packaged on the same unit: Device-Switch plus ~{OCC}."))
P(dict(src=(F, "Device-Switch-Sense"), out="RailroadDevice", name="Device-Lock",
       appliance="switch", style="lock", drop=["Kind", "N", "R"], add={"settle_ms": ""},
       pins={"~{N}": ("UNLOCK", "input"), "~{R}": "~{LOCKED}"}, caps={"UNLOCK": BO, "LOCKED": BI},
       texts={"SW ${VALUE}": "LOCK ${VALUE}"},
       description="Electric lock mechanism: UNLOCK is the demand, ~{LOCKED} the optional plunger sense. "
                   "Unwired, the driver simulates the sense (quality SIMULATED) after settle_ms. "
                   "Shares its Value with the Device-Switch of the same switch."))
P(dict(src=(F, "Driver-I2C-MCP23017"), out="RailroadDevice", ic="MCP23017", drop=["Kind"], caps=EXPANDER))
P(dict(src=("RailroadPanel", "Driver-I2C-MAX7313"), out="RailroadDevice", ic="MAX7313", drop=["Kind"], caps=EXPANDER))
P(dict(src=(F, "Driver-I2C-PCA9685"), out="RailroadDevice", name="Driver-I2C-PCA9685-PWM", ic="PCA9685",
       drop=["Kind"], add={"frequency_hz": ""}, caps=PCA_PWM,
       description="PCA9685 as a lamp driver: sixteen level-out pins at one frequency_hz. A servo on it is refused."))
P(dict(src=(F, "Driver-I2C-PCA9685"), out="RailroadDevice", name="Driver-I2C-PCA9685-Servo", ic="PCA9685",
       drop=["Kind"], add={"min_us": "", "max_us": ""}, caps=PCA_SERVO, texts={"12-bit PWM": "Servo 50 Hz"},
       description="PCA9685 as a servo driver: sixteen position-out pins at 50 Hz, pulse min_us to max_us. "
                   "A lamp on it is refused."))
P(dict(src=(F, "Device-Lamp-Bit"), out="RailroadDevice", name="Driver-GPIO-Digital", role="IODRIVER", ic="GPIO",
       drop=["Kind", "OUT"], add={"Reference": "GPIO"}, pins={"~{OUT}": ("D", "bidirectional")}, caps={"D": BB},
       texts={"I/O ${VALUE}": "GPIO ${VALUE}"},
       description="Processor pin used as a digital input or output, by what lands on it. Value = the board "
                   "core's pin name (D4, GPIO5); the C++ build is the check."))
P(dict(src=(F, "Device-Lamp-Bit"), out="RailroadDevice", name="Driver-GPIO-Pixel", role="IODRIVER", ic="GPIO",
       drop=["Kind", "OUT"], add={"Reference": "GPIO"}, pins={"~{OUT}": ("D", "output")}, caps={"D": PX},
       texts={"I/O ${VALUE}": "PIXEL ${VALUE}"},
       description="Processor pin driving a pixel chain: a bus, one colour-out slot per Address. "
                   "Value = the board core's pin name."))
P(dict(src=(F, "Device-Lamp-Bit"), out="RailroadDevice", name="Setting", role="SETTING",
       drop=["Kind", "OUT"], add={"Reference": "SET"}, pins={"~{OUT}": ("net", "passive")}, texts={"I/O ${VALUE}": "SET ${VALUE}"},
       description="Setting: attaches settings to a net; everything on the net inherits them. Value is a short "
                   "displayed name, Description the reason, every other field one setting."))

# ---- desk ---------------------------------------------------------------------------------
D = "RailroadPanel"
for s in DESK_KEEP:
    P(dict(src=(D, s), out="RailroadDesk", keep_kind=True))
P(dict(src=(D, "PanelSwitch"), out="RailroadDesk", appliance="lever", style="switch",
       drop=["Kind", "NWS", "RWS", "RWK", "NWK"], caps={"NWS": BI, "RWS": BI, "NWK": BO, "RWK": BO}))
P(dict(src=(D, "PanelSignal"), out="RailroadDesk", appliance="lever", style="signal",
       drop=["Kind", "NGS", "HS", "SGS", "SGK", "NGK", "TEK"],
       caps={"NGS": BI, "HS": BI, "SGS": BI, "NGK": BO, "SGK": BO, "TEK": BO}))
P(dict(src=(D, "PanelLock"), out="RailroadDesk", appliance="lever", style="lock",
       drop=["Kind", "WLS", "WLK"], add={"Invert": "WLK"},
       pins={"WLS": "~{UNUSED}", "~{WLK}": "~{WLQK}", "WLK": "~{WLK}"},
       caps={"WLS": BI, "UNUSED": BI, "WLQK": BO, "WLK": BO},
       description="Lock lever plate. ~{WLS} is the R contact (release control); ~{UNUSED} the N contact, wired "
                   "but consumed by nothing; ~{WLQK} the red request lamp; ~{WLK} the green locked lamp, "
                   "lit while WLK is deasserted (Invert=WLK: WLK asserted means released, fail-safe)."))
P(dict(src=(D, "PanelCode"), out="RailroadDesk", appliance="lever", style="code", drop=["Kind", "CODE"], caps={"CODE": BI}))
P(dict(src=(D, "PanelMCall"), out="RailroadDesk", appliance="lever", style="maintainer_call",
       drop=["Kind", "Vital", "ControlToken", "SW"], pins={"~{SW}": "~{S}"}, caps={"S": BI}))
P(dict(src=(D, "PanelAuxiliary"), out="RailroadDesk", appliance="lever", style="non_vital",
       drop=["Kind", "Vital", "ControlToken", "SW"], pins={"~{SW}": "~{S}"}, caps={"S": BI}))
for c in ("RED", "YELLOW", "GREEN", "AMBER", "BLUE"):
    P(dict(src=(D, f"PanelLamp-{c}"), out="RailroadDesk", appliance="lamp", style="indication",
           drop=["Kind", "LAMP"], caps={"LAMP": BO}))
P(dict(src=(F, "Local-Switch"), out="RailroadDesk", appliance="lever", style="switch",
       drop=["Kind", "NWS", "RWS", "RWK", "NWK"], caps={"NWS": BI, "RWS": BI, "NWK": BO, "RWK": BO}))
P(dict(src=(F, "Local-Switch-NoLamp"), out="RailroadDesk", appliance="lever", style="switch",
       drop=["Kind", "NWS", "RWS"], caps={"NWS": BI, "RWS": BI}))
P(dict(src=(F, "Local-Lock"), out="RailroadDesk", appliance="lever", style="lock",
       drop=["Kind", "WLK", "WLQ", "WLQK"], add={"Invert": "WLK"}, pins={"WLK": "~{WLK}"},
       caps={"WLQ": BI, "WLQK": BO, "WLK": BO},
       description="Fascia lock plate. ~{WLQ} is the crew's key (request); ~{WLQK} the red request lamp; "
                   "~{WLK} the green locked lamp, lit while WLK is deasserted (Invert=WLK)."))
P(dict(src=(F, "Local-Lamp"), out="RailroadDesk", appliance="lamp", style="indication", drop=["Kind", "LAMP"], caps={"LAMP": BO}))

RETIRED = {("Railroad", "AUXILIARY_TRAFFIC"), (F, "Device-Head-1LED-PWM"), (F, "Device-Head-3LED-PWM"),
           (F, "Device-Lamp-NeoPixel"), (F, "Device-Lamp-PWM"), (F, "Device-Switch-Servo-Sensed"),
           (F, "Device-Switch-Servo-Sim"), (F, "Device-Switch-StallMotor-Sim"),
           (F, "Local-Lamp-NeoPixel"), (F, "Local-Lamp-PWM")}


# ---- text edits ---------------------------------------------------------------------------
def base(pin: str) -> str:
    m = re.match(r"^~\{(.+)\}$", pin)
    return m.group(1) if m else pin


def esc(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def prop_spans(b: str) -> list[tuple[str, int, int]]:
    """(name, start of the '\\n\\t\\t(property' line, end) for each depth-2 property of a symbol block."""
    out = []
    for m in re.finditer(r'\n\t\t\(property "((?:[^"\\]|\\.)*)" ', b):
        out.append((m.group(1), m.start(), end_of(b, m.start() + 3)))
    return out


def set_prop(b: str, name: str, value: str) -> str:
    for n, s, e in prop_spans(b):
        if n == name:
            head = re.match(r'\n\t\t\(property "(?:[^"\\]|\\.)*" "(?:[^"\\]|\\.)*"', b[s:e])
            return b[:s] + f'\n\t\t(property "{esc(name)}" "{esc(value)}"' + b[s + head.end():]
    spans = prop_spans(b)
    template = next((b[s:e] for n, s, e in spans if n == "Role"), None) or b[spans[-1][1]:spans[-1][2]]
    head = re.match(r'\n\t\t\(property "(?:[^"\\]|\\.)*" "(?:[^"\\]|\\.)*"', template)
    new = f'\n\t\t(property "{esc(name)}" "{esc(value)}"' + template[head.end():]
    if "(hide yes)" not in new:  # a new field is hidden
        new = new.replace("\n\t\t\t(effects", "\n\t\t\t(hide yes)\n\t\t\t(effects", 1)
    last_e = spans[-1][2]
    return b[:last_e] + new + b[last_e:]


def del_prop(b: str, name: str) -> str:
    edits = [(s, e, "") for n, s, e in prop_spans(b) if n == name]
    return replace_spans(b, edits)


def rename_prop(b: str, old: str, new: str) -> str:
    for n, s, e in prop_spans(b):
        if n == old:
            return b[:s] + f'\n\t\t(property "{esc(new)}" ' + b[s + len(f'\n\t\t(property "{esc(old)}" '):]
    return b


def rename_symbol(b: str, old: str, new: str) -> str:
    return b.replace(f'(symbol "{old}"', f'(symbol "{new}"').replace(f'(symbol "{old}_', f'(symbol "{new}_')


def pin_spans(b: str) -> list[tuple[str, str, int, int]]:
    """(name, electrical type, start, end) of every pin block."""
    out = []
    for m in re.finditer(r"\n\t\t\t\(pin (\w+) \w+\n", b):
        s = m.start() + 4
        e = end_of(b, s)
        name = re.search(r'\(name "((?:[^"\\]|\\.)*)"', b[s:e]).group(1)
        out.append((name, m.group(1), s, e))
    return out


def rename_pins(b: str, pins: dict) -> str:
    edits = []
    for name, etype, s, e in pin_spans(b):
        if name not in pins:
            continue
        new = pins[name]
        new_name, new_type = (new, etype) if isinstance(new, str) else new
        block = b[s:e]
        block = re.sub(r"^\(pin \w+ ", f"(pin {new_type} ", block, count=1)
        block = block.replace(f'(name "{name}"', f'(name "{new_name}"', 1)
        edits.append((s, e, block))
    return replace_spans(b, edits)


def add_pin(b: str, name: str, etype: str, number: str) -> str:
    """Append a pin to the first unit that has graphics, at the body's right edge."""
    xs = [float(x) for x in re.findall(r"\((?:xy|start|end|center|mid) (-?[\d.]+) -?[\d.]+\)", b)]
    x = (max(xs) if xs else 2.54) + 2.54
    pin = (f"\n\t\t\t(pin {etype} line\n\t\t\t\t(at {x:g} 0 180)\n\t\t\t\t(length 2.54)\n"
           f'\t\t\t\t(name "{name}"\n\t\t\t\t\t(effects\n\t\t\t\t\t\t(font\n\t\t\t\t\t\t\t(size 1.016 1.016)\n'
           f"\t\t\t\t\t\t)\n\t\t\t\t\t)\n\t\t\t\t)\n"
           f'\t\t\t\t(number "{number}"\n\t\t\t\t\t(effects\n\t\t\t\t\t\t(font\n\t\t\t\t\t\t\t(size 0.635 0.635)\n'
           f"\t\t\t\t\t\t)\n\t\t\t\t\t)\n\t\t\t\t)\n\t\t\t)")
    units = list(blocks(b, "symbol", 2))
    if not units:
        raise ValueError("no unit to add a pin to")
    s, e = units[-1]  # the last unit; KiCad accepts a pin in any unit
    return b[:e - 1] + pin + b[e - 1:]


def edit_texts(b: str, texts: dict) -> str:
    """Rename or delete body (text "...") items; a deleted text takes its whole block."""
    edits = []
    for m in re.finditer(r'\n\t\t\t\(text "((?:[^"\\]|\\.)*)"', b):
        old = m.group(1)
        if old not in texts:
            continue
        s, e = m.start(), end_of(b, m.start() + 4)
        if texts[old] is None:
            edits.append((s, e, ""))
        else:
            edits.append((m.start() + 4, m.end(), f'(text "{esc(texts[old])}"'))
    return replace_spans(b, edits)


def apply(entry: dict, b: str) -> str:
    src_name = entry["src"][1]
    name = entry.get("name", src_name)
    if name != src_name:
        b = rename_symbol(b, src_name, name)
    for old, new in entry.get("rename_fields", {}).items():
        b = rename_prop(b, old, new)
    for f in entry.get("drop", []):
        b = del_prop(b, f)
    if "role" in entry:
        b = set_prop(b, "Role", entry["role"])
    if "appliance" in entry:
        b = set_prop(b, "Appliance", entry["appliance"])
    if "style" in entry:
        b = set_prop(b, "Style", entry["style"])
    if "ic" in entry:
        b = set_prop(b, "IC", entry["ic"])
    for f, v in entry.get("add", {}).items():
        b = set_prop(b, f, v)
    if "description" in entry:
        b = set_prop(b, "Description", entry["description"])
    if "pins" in entry:
        b = rename_pins(b, entry["pins"])
    if "add_pin" in entry:
        pname, etype, cap = entry["add_pin"]
        b = add_pin(b, pname, etype, str(len(pin_spans(b)) + 1))
        b = set_prop(b, f"Pin.{base(pname)}", cap)
    for p, cap in entry.get("caps", {}).items():
        b = set_prop(b, f"Pin.{p}", cap)
    if "texts" in entry:
        b = edit_texts(b, entry["texts"])
    if entry.get("role", "") in {"DEVICE", "PANEL"} or entry.get("appliance"):
        b = split_units(b, name)
    return b


def unit_items(ub: str) -> list[tuple[str, str]]:
    """[(head, text)] of a unit block's children: graphics and pins, in file order."""
    out = []
    for m in re.finditer(r"\n\t\t\t\(([a-z_]+)", ub):
        s = m.start() + 4
        out.append((m.group(1), ub[s:end_of(ub, s)]))
    return out


def split_units(b: str, name: str) -> str:
    """One unit per capability (triage §1). Unit 0 takes every graphic; pins group by their
    Pin.<base> capability in order of first appearance; passive pins (Column) join the first
    group. Only acts on a symbol whose pins mix capabilities and is not yet multi-unit."""
    props = dict(re.findall(r'\n\t\t\(property "([^"]+)" "([^"]*)"', b))
    units = list(blocks(b, "symbol", 2))
    if len(units) > 2 or not units:
        return b
    items = [it for s, e in units for it in unit_items(b[s:e])]
    graphics = [t for h, t in items if h != "pin"]
    pins = [t for h, t in items if h == "pin"]
    groups: dict[str, list[str]] = {}
    for t in pins:
        pname = re.search(r'\(name "([^"]*)"', t).group(1)
        cap = props.get(f"Pin.{base(pname)}")
        groups.setdefault(cap or "_", []).append(t)
    if "_" in groups and len(groups) > 1:  # passive pins join the first capability group
        first = next(w for w in groups if w != "_")
        groups[first] = groups.pop("_") + groups[first]
    if len(groups) < 2:
        return b
    def unit(n: int, body: list[str]) -> str:
        return f'(symbol "{name}_{n}_1"' + "".join("\n\t\t\t" + t for t in body) + "\n\t\t)"
    new = [unit(0, graphics)] + [unit(i + 1, g) for i, g in enumerate(groups.values())]
    b = b[: units[0][0] - 3] + "".join("\n\t\t" + u for u in new) + b[units[-1][1]:]
    v = re.search(r'\n\t\t\(property "Value" ', b)
    vs, ve = v.start() + 3, end_of(b, v.start() + 3)
    vb = b[vs:ve]
    vb = (vb.replace("(do_not_autoplace no)", "(do_not_autoplace yes)") if "(do_not_autoplace" in vb
          else vb.replace("\n\t\t\t(effects", "\n\t\t\t(do_not_autoplace yes)\n\t\t\t(effects", 1))
    b = b[:vs] + vb + b[ve:]
    return set_prop(b, "ki_locked", "")


def symbol_blocks(text: str) -> tuple[str, dict[str, str]]:
    """(header text before the first symbol, {name: block})."""
    out, first = {}, None
    for s, e in blocks(text, "symbol", 1):
        first = s if first is None else first
        out[re.match(r'\(symbol "((?:[^"\\]|\\.)*)"', text[s:e]).group(1)] = text[s:e]
    return text[: first - 2], out


def table(recipe: list[dict]) -> str:
    rows = ["| Source | Output | Library | Role | Appliance | Style | IC | Pins renamed | Pin.* | Fields dropped | Fields added or renamed |",
            "|---|---|---|---|---|---|---|---|---|---|---|"]
    for e in recipe:
        pins = ", ".join(f"{k} to {v if isinstance(v, str) else v[0]}" for k, v in e.get("pins", {}).items())
        caps = ", ".join(f"{k}: {v}" for k, v in e.get("caps", {}).items()) if len(e.get("caps", {})) < 10 else "A1..B8: " + next(iter(e["caps"].values()))
        if "add_pin" in e:
            caps = f"{e['add_pin'][0]}: {e['add_pin'][2]} (pin added)" + (", " + caps if caps else "")
        added = ", ".join(list(e.get("add", {})) + [f"{k} to {v}" for k, v in e.get("rename_fields", {}).items()])
        rows.append(f"| `{e['src'][1]}` | `{e.get('name', e['src'][1])}` | {e['out']} | {e.get('role', '')} | {e.get('appliance', '')} | "
                    f"{e.get('style', '')} | {e.get('ic', '')} | {pins} | {caps} | {', '.join(e.get('drop', []))} | {added} |")
    return "\n".join(rows)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--src", type=Path, default=SRC)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--table", action="store_true", help="print the recipe as a markdown table and exit")
    a = ap.parse_args(argv)
    if a.table:
        print(table(RECIPE))
        return 0
    sources = {}
    for lib, fn in SOURCES.items():
        sources[lib] = symbol_blocks((a.src / fn).read_text())
    outputs: dict[str, list[str]] = {t: [] for t in TARGETS}
    seen: set[tuple[str, str]] = set()
    used: set[tuple[str, str]] = set()
    for e in RECIPE:
        lib, name = e["src"]
        if name not in sources[lib][1]:
            print(f"error: {lib}:{name} not in the baseline", file=sys.stderr)
            return 1
        out_name = e.get("name", name)
        if (e["out"], out_name) in seen:
            print(f"error: {e['out']}:{out_name} produced twice", file=sys.stderr)
            return 1
        seen.add((e["out"], out_name))
        used.add((lib, name))
        outputs[e["out"]].append(apply(e, sources[lib][1][name]))
    for lib, (_, syms) in sources.items():
        for name in syms:
            if (lib, name) not in used and (lib, name) not in RETIRED:
                print(f"error: {lib}:{name} is neither in the recipe nor retired", file=sys.stderr)
                return 1
    for (lib, name) in RETIRED:
        if (lib, name) in used:
            print(f"error: {lib}:{name} is both used and retired", file=sys.stderr)
            return 1
    for target, src_lib in TARGETS.items():
        header = sources[src_lib][0]
        made = {re.match(r'\(symbol "((?:[^"\\]|\\.)*)"', b).group(1): b for b in outputs[target]}
        out_path = a.out / f"{target}.kicad_sym"
        existing = symbol_blocks(out_path.read_text())[1] if out_path.exists() else {}
        kept = 0
        for name in HAND_FINISHED.get(target, []):
            if name not in made:
                print(f"error: hand-finished {target}:{name} is not produced by the recipe", file=sys.stderr)
                return 1
            if name in existing:
                made[name] = existing[name]
                kept += 1
            else:
                print(f"warning: hand-finished {target}:{name} not in the existing output; generated block used")
        text = header + "".join("\n\t" + made[n] for n in sorted(made)) + "\n)\n"
        out_path.write_text(text)
        print(f"{target}.kicad_sym: {len(made)} symbols, {kept} hand-finished carried over")
    return 0


if __name__ == "__main__":
    sys.exit(main())
