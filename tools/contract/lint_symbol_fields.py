#!/usr/bin/env python3
"""Lint the step 4 symbol libraries by their fields (checkpoint rev 9: symbol names decide nothing).

    python3 tools/contract/lint_symbol_fields.py [--libdir DIR] [--table]

Per symbol, by Role:
- DEVICE with Appliance head (a head device; Role CAST until 2026-10-23, ADR 0009 §3.6): Style is the
  manufacturer model, fixed by the symbol; exactly one input pin of kind indication. Two shapes
  (worklist 2026-11-04): the Signals-library head presents a head word, so it has exactly one output
  pin of kind indication, no other pin and no setting, and it is anonymous (owner, 2026-11-04): a head
  is a position on its mast, keyed by the mast pin it is wired to, so a `Name` property is an error.
  This is the one exemption from "Name=${Value} on every keyed symbol" (the overview's G2). The older
  head device makes its lamps itself: the head letter is the last letter of its Name (784A), the `Head`
  field is tolerated, not required, every other pin is one output kind and settings are
  lower_snake_case. The shape is told by whether the device has an output of kind indication. The
  aspect is derived from style and indication, never a pin.
- DEVICE with Appliance mast and lettered pins (a field mast device, take 3, 2026-11-04): the binding
  between the trackplan mast (Name) and its heads. Its pins are outputs of kind indication named A, B,
  C in number order from A with no gap, one to three of them, `Pin.<letter>=indication` each; no Style,
  Kind or Indications field: the pin set states the head count. The older Railroad-Field:Mast (one IND
  output) has no lettered pin and keeps the plain DEVICE rules.
- APPLIANCE with Appliance train_order (a trackplan train order board; the owner, 2026-11-08): Style
  single or double, the symbol drawn, as a signal mast's; a Station field; no pins at all (it stands
  beside the track; its faces are its field mast device's pins).
- DEVICE with Appliance train_order_mast (a train order board's field mast; the owner, 2026-11-08): one
  passive pin per face, `Pin.<pin>=indication` each; a double mast's pins are named N, S, E or W, the
  direction each face serves; a single mast has one pin of any name (its direction is the trackplan
  glyph's turn); no Style, Kind or Indications, as a field signal mast.
- DEVICE with Appliance lever and Style train_order (a train order board's fascia lever; the owner,
  2026-11-08, Railroad-Field:Local-TrainOrder): IND, an input, is the face the lever serves, wired to
  the mast's face pin beside the face's head, so it is a membership pin and carries no Pin.IND; the
  function pins are exactly STOP and SLOW, outputs of kind binary (no CALLON: that is the block
  signal's indication); no code line token field (the control is local): no Control, Indication,
  Control.*, Indication.* or IndicationToken.
- ENCODER (the head word -> hardware step; the owner's hand-edited Railroad-Field-Signals of
  2026-11-04 is the truth): no Appliance; anonymous, keyed by the head it serves, so a `Name` is an
  error (Value is informative, never read); Kind required, any word (RYG, RGB, 3MUX2A, LAMP,
  PIXEL_RYG, PIXEL_RGB, SERVO, ...: a reference-data key, not enumerated here); exactly one input pin
  of kind indication (the head word, `APP`); every hardware-side function pin (R/Y/G/B, S0/S1, ARM,
  LAMP) is an INPUT of kind binary or position, driven by a driver's output pin, as Device-Lamp and the
  old CPL-Encoded S0/S1 were, so an output function pin is an error; `Pin.*` per pin and none without
  a pin; a `CHAIN` pin is a bus attachment like a driver's `IOBus`, no `Pin.*`; `Address` and
  `Address.<colour>` are contract fields (the latter names a lamp colour of the served head, not a
  pin); there is no `Code` field (a 3MUX2A truth table is reference data keyed by Kind); settings
  lower_snake_case.
- APPLIANCE: Appliance present; no Kind, except a mast, which states Kind CONTROLLED, ABSOLUTE or PERMISSIVE
  (owner, 2026-10-31; ADR 0009 §3.10, ADR 0013). A switch (Appliance switch, a derail included) states exactly
  one regime word in its Style, from `grammar.REGIMES` (powered, dual, local, lock, manual_sensed, manual,
  spring); `derail` may accompany it; none or two is an error (owner, 2026-11-09: a missing word is a symbol
  contract defect, caught here, never a model finding).
- DEVICE, PANEL: Appliance present; no Kind; one `Pin.<base>` per function pin (Column excepted) and
  no `Pin.*` without a pin; the capability is one primary word from the vocabulary (binary, level,
  position, color, pixel, message); direction is the KiCad electrical type, which must be input,
  output or bidirectional on a function pin (E66); no retired field (a pin's base name as a field,
  ControlToken, Vital, NormalIs, Chain, Index); every other field, the settings, is
  lower_snake_case; `Invert` names only this symbol's pins; one capability per unit, capability
  meaning primary word plus electrical type, so a symbol whose pins mix them is multi-unit, with
  its units not interchangeable and its Value not autoplaced (the units mesh and show one name).
- IODRIVER: IC present; Kind only to name a JMRI driver's object class (TURNOUT, SENSOR, SIGNALMAST, LIGHT) or what a
  CMRInet driver is; IC CMRI requires Kind, one of NODE, IB, OB (owner, 2026-10-30); `Pin.*` per pin, primary word, electrical type input, output or
  bidirectional; the attachment's address field by bus kind (ADR 0005 S4): `Bit` for a CMRI bit, `Address` for a CMRI node, none for MQTT, `Address` otherwise. Warning (2026-10-18) when a unit's body (its largest
  rectangle) lacks the driver look: stroke 0.3048 solid 128/77/0 with background fill. The looks by
  Role are a convention for readers, never a fact: device = named box with its proxy glyph, cast =
  plain box with direction arrows, driver (chips included) = brown border, background fill.
- PANEL is a device of the CTC machine: in a column, with a `Column` pin, or on the model board, Style
  `board`, with none (owner's ruling 2026-10-23: a model board lamp is a singleton; the board's shape
  lives in the driver). A DEVICE symbol has no `Column` pin (E72).
- PANEL tokens (owner's rulings 2026-10-28): `Control.<pin>` and `Indication.<pin>` are contract
  fields like `Pin.*`: each must name a pin of the symbol (empty is a deliberate none); a lamp's
  whole-symbol `Indication` (a boolean expression) is a contract field. Whether every token pin
  states one is the library overview's report, not this lint's.
- SETTING: one passive pin, no Pin.*.
- TRACK, POLICY, STRUCTURE, COLUMN, OFFICE_UNIT, TRANSPORT, CODELINE_ENCODING, IO_ENCODING: Kind allowed; nothing else checked.
`--table` prints every symbol as a markdown row. Exit 1 on any error; warnings only print.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from kicad_services.sch_text import blocks, library_symbols  # noqa: E402
from tools.layout_model.grammar import REGIMES  # noqa: E402  (the switch words: one definition, shared with the derivation)

LIBDIR = Path.home() / "Dropbox/KiCad/Railroad/symbols"
LIBRARIES = ("Railroad-Trackplan", "Railroad-Office", "Railroad-Field", "Railroad-HardwareIO")
VOCABULARY = {"binary", "level", "position", "color", "indication", "message"}
SOURCE_KINDS = {"indication"}  # a cast's one input
FUNCTION_ETYPES = {"input", "output", "bidirectional"}
STRUCTURAL = {"TRACK", "POLICY", "STRUCTURE", "COLUMN", "OFFICE_UNIT", "TRANSPORT", "CODELINE_ENCODING", "IO_ENCODING"}
FUNCTIONAL = {"APPLIANCE", "DEVICE", "PANEL", "IODRIVER", "ENCODER", "SETTING"}
KIND_ROLES = {"IODRIVER", "ENCODER"}               # Roles whose Kind is not retired: a JMRI or CMRInet driver's class, an encoder's hardware
RETIRED_FIELDS = {"ControlToken", "Vital", "NormalIs", "Chain", "Index", "Kind"}
ATTACHMENT_ADDRESS = {"CMRI": "Bit", "MQTT": None}  # by IC; every other bus device attaches by Address (ADR 0005 S4)
MAST_KINDS = ("CONTROLLED", "ABSOLUTE", "PERMISSIVE")    # what a mast is: dispatcher-controlled, or automatic and absolute or permissive (owner, 2026-10-31)
HEAD_POSITIONS = "ABC"                              # a field mast device's pins, top down (830SAB, 784EAB; Glossary head1..head3)
NOT_ON_FIELD_MAST = ("Style", "Kind", "Indications")    # the pin set states the head count; demand lives on the trackplan mast
CMRI_KINDS = ("NODE", "IB", "OB")                   # what a CMRInet driver is: the node or one of its bits (owner, 2026-10-30)
TRAIN_ORDER_FACES = ("N", "S", "E", "W")            # a double train order mast's face pins, the direction each serves (owner, 2026-11-08)
TRAIN_ORDER_INPUTS = ("STOP", "SLOW")               # a train order lever's outputs, binary, to any driver; IND is the face it serves
TRAIN_ORDER_STYLES = ("single", "double")           # a trackplan train order board's Style, the symbol drawn (owner, 2026-11-08)
TRAIN_ORDER_NO_TOKENS = ("Control", "Indication", "IndicationToken")   # the control is local: no code line token on the lever
NOT_SETTINGS = {"Role", "Name", "Kind", "Appliance", "Style", "IC", "Address", "UA", "Bit", "Node", "Head", "Invert", "IndicationToken", "Members", "Color", "CP Name", "Station", "Indications", "Control", "Indication", "TC",
                "Transport", "NodeType", "InputBytes", "OutputBytes",
                "JMRI.SignalSystem",   # a JMRI identity (the xml/signals folder) on Encoding-JMRI and Driver-JMRI-SignalMast (owner, 2026-11-11): a contract field, not a setting
                "IndicationCeiling", "Display", "Processor", "Milepost", "Reference", "Value", "Footprint",
                "Datasheet", "Description", "ki_keywords", "ki_fp_filters", "ki_description"}
PIN_TOKENS = ("Control.", "Indication.")   # PANEL per-pin tokens (owner, 2026-10-28); an empty one is a deliberate none
MEMBERSHIP_PINS = {"Column", "IOBus", "Processor", "Transport", "Codeline", "MC", "CHAIN"}   # seam pins (ADR 0009 §3.1): nets, not device functions; CHAIN = an encoder's pixel-chain attachment (2026-11-04)
ADDRESS_FIELDS = ("Address.",)                     # an encoder's per-colour pixel address (2026-11-04): a contract field, not a setting
ENCODER_FIELDS: set[str] = set()                   # an encoder's other contract fields: none; `Code` went when the 3MUX2A table became reference data keyed by Kind (2026-11-04)
ENCODER_PIN_KINDS = {"binary", "position"}         # what a driver's output pin hands an encoder's hardware-side input
DRIVER_LOOK = ("(width 0.3048)", "(type solid)", "(color 128 77 0 1)", "(type background)")
RECT = re.compile(r"\(start ([-\d.]+) ([-\d.]+)\)\s*\(end ([-\d.]+) ([-\d.]+)\)")


def library_bodies(text: str) -> dict[str, dict[str, str]]:
    """{symbol: {unit: text of the unit's largest rectangle}} for every unit that has one."""
    out: dict[str, dict[str, str]] = {}
    for s, e in blocks(text, "symbol", 1):
        b = text[s:e]
        name = re.match(r'\(symbol "([^"]+)"', b).group(1)
        for us, ue in blocks(b, "symbol", 2):
            u = b[us:ue]
            unit = re.match(r'\(symbol "(?:[^"\\]|\\.)*_(\d+)_\d+"', u).group(1)
            rects = [(abs(float(x2) - float(x1)) * abs(float(y2) - float(y1)), u[rs:re_])
                     for rs, re_ in blocks(u, "rectangle", 3)
                     for x1, y1, x2, y2 in [RECT.search(u[rs:re_]).groups()]]
            if rects:
                out.setdefault(name, {})[unit] = max(rects)[1]
    return out
SNAKE = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")


def base(pin: str) -> str:
    m = re.match(r"^~\{(.+)\}$", pin)
    return m.group(1) if m else pin


def lint_symbol(lib: str, name: str, sym: dict, bodies: dict[str, str] | None = None) -> list[tuple[str, str]]:
    """[(severity, message)] for one symbol; bodies = {unit: largest rectangle text}."""
    out: list[tuple[str, str]] = []
    props, pins = sym["properties"], sym["pins"]
    role = props.get("Role", "")
    err = lambda m: out.append(("error", f"{lib}:{name}: {m}"))
    warn = lambda m: out.append(("warning", f"{lib}:{name}: {m}"))
    if role in STRUCTURAL:
        return out
    if role not in FUNCTIONAL:
        err(f"Role {role!r} is not known")
        return out
    mast = role == "APPLIANCE" and props.get("Appliance") == "mast"
    if mast and props.get("Kind") not in MAST_KINDS:                 # a mast states what it is (owner, 2026-10-31)
        err(f"a mast states Kind, one of {', '.join(MAST_KINDS)}; this has {props.get('Kind') or 'none'}")
    elif "Kind" in props and role not in KIND_ROLES and not mast:    # a JMRI driver's Kind is its object class (owner, 2026-10-24)
        err("Kind is retired")
    if role in {"APPLIANCE", "DEVICE", "PANEL"} and not props.get("Appliance"):
        err("Appliance missing")
    if role == "ENCODER":                                            # worklist 2026-11-04: Kind says what hardware it makes
        if props.get("Appliance"):
            err("an encoder serves a head through the wire; it has no Appliance")
        if not props.get("Kind"):
            err("an encoder states Kind, the hardware it makes (RYG, PIXEL, SERVO, ...)")
        if "Name" in props:                                          # owner, 2026-11-04: anonymous, like the head it serves
            err("an encoder is keyed by the head it serves; it has no name")
    if role == "IODRIVER" and not props.get("IC"):
        err("IC missing")
    pin_caps = {k[4:]: v for k, v in props.items() if k.startswith("Pin.")}
    to_lever = role == "DEVICE" and props.get("Appliance") == "lever" and "train_order" in props.get("Style", "")
    membership = MEMBERSHIP_PINS | ({"IND"} if to_lever else set())   # a train order lever's IND is the face it serves (owner, 2026-11-08)
    function_pins = [(n, num, ty) for n, num, ty in pins if n not in membership]
    if role == "APPLIANCE" and props.get("Appliance") == "train_order":    # a trackplan train order board (owner, 2026-11-08)
        if props.get("Style") not in TRAIN_ORDER_STYLES:
            err(f"a train order board states Style, one of {', '.join(TRAIN_ORDER_STYLES)}; this has {props.get('Style') or 'none'}")
        if "Station" not in props:
            err("a train order board states Station, the timetable station it stands at")
        if pins:
            err(f"a train order board has no pins; its faces are its field mast's; this has {', '.join(n for n, _, _ in pins)}")
    if role == "APPLIANCE" and props.get("Appliance") == "switch":        # a switch or derail states its regime (owner, 2026-11-09)
        words = [w for w in (x.strip() for x in props.get("Style", "").split(",")) if w in REGIMES]
        if len(words) != 1:
            err(f"a switch or derail states exactly one regime word in Style, one of {', '.join(sorted(REGIMES))}, with derail beside "
                f"it on a derail; this has {', '.join(words) or 'none'}")
    bases = {base(n) for n, _, _ in function_pins}
    etype = {n: ty for n, _, ty in pins}
    if role == "DEVICE" and props.get("Appliance") == "head":        # a head device (ADR 0009 §3.6; Role CAST until 2026-10-23)
        sources = [n for n, _, _ in function_pins if pin_caps.get(base(n)) in SOURCE_KINDS and etype[n] != "output"]
        if len(sources) != 1:
            err(f"a head device takes exactly one indication input; this has {len(sources)}")
        words = [n for n, _, _ in function_pins if pin_caps.get(base(n)) in SOURCE_KINDS and etype[n] == "output"]
        if words:
            # The Signals-library shape (worklist 2026-11-04): the head presents a head word on one indication output
            # and nothing else; an encoder makes the hardware. The older Railroad-Field heads have no such output and
            # keep the rule below, so both libraries lint clean until the sheets migrate.
            if len(words) != 1:
                err(f"a head device presents one head word; this has {len(words)} indication outputs")
            others = [n for n, _, _ in function_pins if n not in sources and n not in words]
            if others:
                err(f"a head device presents a head word and nothing else; it has pins {', '.join(others)}")
            settings = [f for f in props if f not in NOT_SETTINGS and not f.startswith("Pin.")]
            if settings:
                err(f"a head device of this shape has no settings; it has {', '.join(settings)}")
            if "Name" in props:                                      # owner, 2026-11-04: a head is a position on its mast
                err("a head has no name; it is keyed by the mast pin it is wired to")
        else:
            outs = {pin_caps.get(base(n), "?") for n, _, _ in function_pins if n not in sources}
            if len(outs) != 1:
                err(f"a head device produces one kind; this produces {', '.join(sorted(outs)) or 'nothing'}")
        if len([u for u, p in sym["units"].items() if p]) > 1:
            err("a head device is one head; units would hide the head letter")
    lettered = [p for p in function_pins if len(p[0]) == 1 and p[0].isupper()]
    mast_positions = []                                               # a field mast's position pins, passive by rule
    to_mast = role == "DEVICE" and props.get("Appliance") == "train_order_mast"    # a train order board's field mast (owner, 2026-11-08)
    if (role == "DEVICE" and props.get("Appliance") == "mast" and lettered) or to_mast:     # a field mast device (take 3, 2026-11-04)
        mast_positions = list(function_pins)
        by_number = sorted(function_pins, key=lambda p: (len(p[1]), p[1]))
        names = "".join(n for n, _, _ in by_number)
        if to_mast:
            faces = [n for n, _, _ in function_pins]
            if not faces:
                err("a train order mast has one passive pin per face; this has none")
            elif len(faces) > 1 and (len(faces) > 2 or any(f not in TRAIN_ORDER_FACES for f in faces)):
                err(f"a double train order mast's pins are two of {', '.join(TRAIN_ORDER_FACES)}, the direction each face serves; this has {', '.join(faces)}")
        elif not (1 <= len(names) <= len(HEAD_POSITIONS) and names == HEAD_POSITIONS[:len(names)]):
            err(f"a field mast's pins are {', '.join(HEAD_POSITIONS)} in order from A, one per head position; this has {', '.join(names) or 'none'}")
        for n, _, ty in function_pins:
            if ty != "passive":                                       # owner, 2026-11-05: what is wired says what it takes
                err(f"pin {n} is {ty}; a field mast's position pin is passive, so a consumer may take one position or several tied together")
            if pin_caps.get(n) is not None and pin_caps.get(n) != "indication":
                err(f"Pin.{n} = {pin_caps[n]!r}; a field mast's pins are kind indication")
        for f in NOT_ON_FIELD_MAST:
            if f in props:
                err(f"a field mast states no {f}; the pin set states the head count")
    if to_lever:                                                      # a train order board's fascia lever (owner, 2026-11-08)
        if "IND" not in etype:
            err("a train order lever has an IND pin, the face it serves, wired to the mast's face pin")
        elif etype["IND"] != "input":
            err(f"pin IND is {etype['IND']}; a train order lever's IND is an input, the face it serves")
        if "IND" in pin_caps:
            err("Pin.IND: a train order lever's IND is the face it serves, not a capability")
        have = sorted(base(n) for n, _, _ in function_pins)
        if have != sorted(TRAIN_ORDER_INPUTS):
            err(f"a train order lever's function pins are {', '.join(TRAIN_ORDER_INPUTS)}; this has {', '.join(have) or 'none'}")
        for n, _, ty in function_pins:
            if base(n) in TRAIN_ORDER_INPUTS and ty != "output":
                err(f"pin {n} is {ty}; a train order lever's {base(n)} is an output")
            if base(n) in TRAIN_ORDER_INPUTS and pin_caps.get(base(n)) not in (None, "binary"):
                err(f"Pin.{base(n)} = {pin_caps[base(n)]!r}; a train order lever's {base(n)} is binary")
        for f in sorted(props):
            if f in TRAIN_ORDER_NO_TOKENS or f.startswith(PIN_TOKENS):
                err(f"field {f}: a train order board's control is local; no code line token")
    if role == "ENCODER":
        sources = [n for n, _, _ in function_pins if pin_caps.get(base(n)) in SOURCE_KINDS and etype[n] == "input"]
        if len(sources) != 1:
            err(f"an encoder takes exactly one indication input, the head word; this has {len(sources)}")
        for n, _, ty in function_pins:
            if n in sources:
                continue
            if pin_caps.get(base(n)) in SOURCE_KINDS:
                err(f"pin {n} is a second indication pin; an encoder's other pins are its hardware")
                continue
            if ty == "output":                                       # the driver's output drives it (owner, 2026-11-04)
                err(f"pin {n} is an output; encoder hardware pins are inputs, driven by the driver")
            cap = pin_caps.get(base(n))
            if cap in VOCABULARY and cap not in ENCODER_PIN_KINDS:
                err(f"Pin.{base(n)} = {cap!r}; an encoder's hardware pin takes {' or '.join(sorted(ENCODER_PIN_KINDS))} from the driver")
    if role in {"DEVICE", "PANEL", "IODRIVER", "ENCODER"}:
        for n, num, ty in function_pins:
            cap = pin_caps.get(base(n))
            if cap is None:
                err(f"pin {n} has no Pin.{base(n)}")
                continue
            if cap not in VOCABULARY:
                err(f"Pin.{base(n)} = {cap!r} is not in the vocabulary (one primary word; direction is the pin type)")
                continue
            if ty not in FUNCTION_ETYPES and (n, num, ty) not in mast_positions:
                err(f"pin {n} is {ty}; a function pin is input, output or bidirectional")
        for p in pin_caps:
            if p not in bases:
                err(f"Pin.{p} names no pin")
        for n, _, _ in function_pins:
            if base(n) in props:
                err(f"field {base(n)} is a retired per-pin override")
        if role != "IODRIVER" and "Invert" in props:
            for p in [x.strip() for x in props["Invert"].split(",") if x.strip()]:
                if p not in bases:
                    err(f"Invert names {p}, not a pin of this symbol")
    if role == "IODRIVER":
        # ADR 0005 S4: an attachment carries only its own address on its bus; the field depends on the bus kind
        want = ATTACHMENT_ADDRESS.get(props.get("IC"), "Address")
        if props.get("IC") == "CMRI":
            if props.get("Kind") not in CMRI_KINDS:
                err(f"a CMRInet driver states what it is in Kind, one of {', '.join(CMRI_KINDS)}; this has {props.get('Kind') or 'none'}")
            if props.get("Kind") == "NODE":
                want = "Address"                  # the node itself attaches by its UA (ADR 0009 §3.5)
        if want and want not in props:
            err(f"{want} missing on a bus device")
    if role == "IODRIVER":
        for unit, rect in sorted((bodies or {}).items()):
            if not all(mark in rect for mark in DRIVER_LOOK):
                warn(f"unit {unit} body lacks the driver look (brown 0.3048 border, background fill)")
    has_column = any(n == "Column" for n, _, _ in pins)
    board = props.get("Style") == "board"                # a model board device: no column (2026-10-23)
    if role == "PANEL" and not has_column and not board:
        err("Role PANEL without a Column pin; a column device has one, a model board device has Style board")
    if role == "PANEL" and has_column and board:
        err("Role PANEL with Style board and a Column pin; a model board device sits in no column")
    if role == "DEVICE" and has_column:
        err("Role DEVICE with a Column pin; a plate in the machine is PANEL")
    head_device = role == "DEVICE" and props.get("Appliance") == "head"     # one unit, one indication input plus one kind: checked above
    if role in {"DEVICE", "PANEL"} and not head_device:
        caps = {f"{pin_caps.get(base(n), '?')} {ty}" for n, _, ty in function_pins}
        pin_units = {u: p for u, p in sym["units"].items() if p}
        for u, names in pin_units.items():
            unit_caps = {f"{pin_caps.get(base(n), '?')} {etype.get(n)}" for n in names if n not in membership}
            if len(unit_caps) > 1:
                err(f"unit {u} mixes {', '.join(sorted(unit_caps))}; one capability (word and pin type) per unit")
            if len(caps) > 1 and len(pin_units) < 2:
                err(f"pins mix {', '.join(sorted(caps))} in one unit; split the symbol into units")
        if len(pin_units) > 1:
            if not sym["locked"]:
                err("units must be marked not interchangeable")
            if sym["value_autoplace"]:
                err("Value must not be autoplaced on a multi-unit symbol")
    if role == "SETTING":
        if len(pins) != 1 or pins[0][2] != "passive":
            err("wants exactly one passive pin")
        if pin_caps:
            err("carries Pin.* but serves no function")
    all_bases = {base(n) for n, _, _ in pins}
    for f in props:
        if f in RETIRED_FIELDS and not (f == "Kind" and (role in KIND_ROLES or mast)):
            err(f"field {f} is retired")
        elif f.startswith(PIN_TOKENS) and role == "PANEL":          # a per-pin token (2026-10-28): its pin must exist
            if f.split(".", 1)[1] not in all_bases:
                err(f"{f} names no pin")
        elif (f.startswith(ADDRESS_FIELDS) or f in ENCODER_FIELDS) and role == "ENCODER":    # contract fields, not settings
            pass
        elif f not in NOT_SETTINGS and not f.startswith("Pin.") and not SNAKE.match(f):
            err(f"setting {f} is not lower_snake_case")
    return out


def row(lib: str, name: str, sym: dict) -> str:
    p = sym["properties"]
    caps = ", ".join(f"{base(n)}: {p.get('Pin.' + base(n), '?')}" for n, _, _ in sym["pins"] if n not in MEMBERSHIP_PINS)
    if len(sym["pins"]) > 8:
        caps = f"{len(sym['pins'])} pins: {p.get('Pin.A1', '?')}"
    contract = NOT_SETTINGS | (ENCODER_FIELDS if p.get("Role") == "ENCODER" else set())
    settings = ", ".join(f for f in p if f not in contract and not f.startswith(("Pin.",) + PIN_TOKENS + ADDRESS_FIELDS) and f != "Kind")
    return (f"| {lib} | `{name}` | {p.get('Role', '')} | {p.get('Appliance', '')} | {p.get('Style', '')} | "
            f"{p.get('IC', '')} | {caps} | {p.get('Invert', '')} | {settings} |")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--libdir", type=Path, default=LIBDIR)
    ap.add_argument("--table", action="store_true")
    a = ap.parse_args(argv)
    findings, rows, count = [], [], 0
    for lib in LIBRARIES:
        text = (a.libdir / f"{lib}.kicad_sym").read_text()
        syms, bodies = library_symbols(text), library_bodies(text)
        for name, sym in syms.items():
            count += 1
            findings += lint_symbol(lib, name, sym, bodies.get(name))
            rows.append(row(lib, name, sym))
    if a.table:
        print("| Library | Symbol | Role | Appliance | Style | IC | Pin.* | Invert | Settings |")
        print("|---|---|---|---|---|---|---|---|---|")
        print("\n".join(rows))
    for sev, msg in findings:
        print(f"{sev}: {msg}")
    errors = sum(1 for s, _ in findings if s == "error")
    warnings = sum(1 for s, _ in findings if s == "warning")
    print(f"{count} symbols, {errors} errors, {warnings} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
