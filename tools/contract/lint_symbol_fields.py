#!/usr/bin/env python3
"""Lint the step 4 symbol libraries by their fields (checkpoint rev 9: symbol names decide nothing).

    python3 tools/contract/lint_symbol_fields.py [--libdir DIR] [--table]

Per symbol, by Role:
- CAST (2026-10-18): a head cast: no Appliance; a `Head` field (the head letter, written per
  instance); Style allowed (the head style, fixed by the symbol or written per instance); exactly
  one input pin of kind indication and every other pin one output kind; `Pin.*` per pin; settings
  lower_snake_case. The aspect is derived from style and indication, never a pin.
- APPLIANCE: Appliance present; no Kind.
- DEVICE, PANEL: Appliance present; no Kind; one `Pin.<base>` per function pin (Column excepted) and
  no `Pin.*` without a pin; the capability is one primary word from the vocabulary (binary, level,
  position, color, pixel, message); direction is the KiCad electrical type, which must be input,
  output or bidirectional on a function pin (E66); no retired field (a pin's base name as a field,
  ControlToken, Vital, NormalIs, Chain, Index); every other field, the settings, is
  lower_snake_case; `Invert` names only this symbol's pins; one capability per unit, capability
  meaning primary word plus electrical type, so a symbol whose pins mix them is multi-unit, with
  its units not interchangeable and its Value not autoplaced (the units mesh and show one name).
- IODRIVER: IC present; no Kind; `Pin.*` per pin, primary word, electrical type input, output or
  bidirectional; the attachment's address field by bus kind (ADR 0005 S4): `Bit` for CMRI, none for MQTT, `Address` otherwise. Warning (2026-10-18) when a unit's body (its largest
  rectangle) lacks the driver look: stroke 0.3048 solid 128/77/0 with background fill. The looks by
  Role are a convention for readers, never a fact: device = named box with its proxy glyph, cast =
  plain box with direction arrows, driver (chips included) = brown border, background fill.
- PANEL is exactly a device in a CTC machine column: a PANEL symbol has a `Column` pin and a DEVICE
  symbol has none (E72).
- SETTING: one passive pin, no Pin.*.
- TRACK, POLICY, STRUCTURE, COLUMN, MACHINE, CODELINE_*: Kind allowed; nothing else checked.
`--table` prints every symbol as a markdown row. Exit 1 on any error; warnings only print.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kicad_services.sch_text import blocks, library_symbols  # noqa: E402

LIBDIR = Path.home() / "Dropbox/KiCad/Railroad/symbols"
LIBRARIES = ("Railroad-Trackplan", "Railroad-Office", "Railroad-Field", "Railroad-HardwareIO")
VOCABULARY = {"binary", "level", "position", "color", "indication", "message"}
SOURCE_KINDS = {"indication"}  # a cast's one input
FUNCTION_ETYPES = {"input", "output", "bidirectional"}
STRUCTURAL = {"TRACK", "POLICY", "STRUCTURE", "COLUMN", "MACHINE", "CODELINE_TRANSPORT", "CODELINE_ENCODING"}
FUNCTIONAL = {"APPLIANCE", "DEVICE", "PANEL", "IODRIVER", "SETTING", "CAST"}
RETIRED_FIELDS = {"ControlToken", "Vital", "NormalIs", "Chain", "Index", "Kind"}
ATTACHMENT_ADDRESS = {"CMRI": "Bit", "MQTT": None}  # by IC; every other bus device attaches by Address (ADR 0005 S4)
NOT_SETTINGS = {"Role", "Appliance", "Style", "IC", "Address", "UA", "Bit", "Head", "Invert", "IndicationToken", "Color", "CP", "TC",
                "IndicationCeiling", "Display", "Processor", "Milepost", "Reference", "Value", "Footprint",
                "Datasheet", "Description", "ki_keywords", "ki_fp_filters", "ki_description"}
MEMBERSHIP_PINS = {"Column"}
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
    if "Kind" in props:
        err("Kind is retired")
    if role in {"APPLIANCE", "DEVICE", "PANEL"} and not props.get("Appliance"):
        err("Appliance missing")
    if role == "IODRIVER" and not props.get("IC"):
        err("IC missing")
    pin_caps = {k[4:]: v for k, v in props.items() if k.startswith("Pin.")}
    function_pins = [(n, num, ty) for n, num, ty in pins if n not in MEMBERSHIP_PINS]
    bases = {base(n) for n, _, _ in function_pins}
    if role == "CAST":
        sources = [n for n, _, _ in function_pins if pin_caps.get(base(n)) in SOURCE_KINDS]
        if len(sources) != 1:
            err(f"a cast takes exactly one indication input; this has {len(sources)}")
        outs = {pin_caps.get(base(n), "?") for n, _, _ in function_pins if n not in sources}
        if len(outs) != 1:
            err(f"a cast produces one kind; this produces {', '.join(sorted(outs)) or 'nothing'}")
        if "Appliance" in props:
            err("a cast has no Appliance; identity belongs to the anchor device")
        if "Head" not in props:
            err("a cast renders one head; Head field missing (the letter is written per instance)")
        if len([u for u, p in sym["units"].items() if p]) > 1:
            err("a cast is one head; units would hide the head letter")
    if role in {"DEVICE", "PANEL", "IODRIVER", "CAST"}:
        for n, num, ty in function_pins:
            cap = pin_caps.get(base(n))
            if cap is None:
                err(f"pin {n} has no Pin.{base(n)}")
                continue
            if cap not in VOCABULARY:
                err(f"Pin.{base(n)} = {cap!r} is not in the vocabulary (one primary word; direction is the pin type)")
                continue
            if ty not in FUNCTION_ETYPES:
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
        if want and want not in props:
            err(f"{want} missing on a bus device")
    if role == "IODRIVER":
        for unit, rect in sorted((bodies or {}).items()):
            if not all(mark in rect for mark in DRIVER_LOOK):
                warn(f"unit {unit} body lacks the driver look (brown 0.3048 border, background fill)")
    has_column = any(n in MEMBERSHIP_PINS for n, _, _ in pins)
    if role == "PANEL" and not has_column:
        err("Role PANEL without a Column pin; a plate outside the machine is a DEVICE")
    if role == "DEVICE" and has_column:
        err("Role DEVICE with a Column pin; a plate in the machine is PANEL")
    if role in {"DEVICE", "PANEL"}:
        etype = {n: ty for n, _, ty in pins}
        caps = {f"{pin_caps.get(base(n), '?')} {ty}" for n, _, ty in function_pins}
        pin_units = {u: p for u, p in sym["units"].items() if p}
        for u, names in pin_units.items():
            unit_caps = {f"{pin_caps.get(base(n), '?')} {etype.get(n)}" for n in names if n not in MEMBERSHIP_PINS}
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
    for f in props:
        if f in RETIRED_FIELDS:
            err(f"field {f} is retired")
        elif f not in NOT_SETTINGS and not f.startswith("Pin.") and not SNAKE.match(f):
            err(f"setting {f} is not lower_snake_case")
    return out


def row(lib: str, name: str, sym: dict) -> str:
    p = sym["properties"]
    caps = ", ".join(f"{base(n)}: {p.get('Pin.' + base(n), '?')}" for n, _, _ in sym["pins"] if n not in MEMBERSHIP_PINS)
    if len(sym["pins"]) > 8:
        caps = f"{len(sym['pins'])} pins: {p.get('Pin.A1', '?')}"
    settings = ", ".join(f for f in p if f not in NOT_SETTINGS and not f.startswith("Pin.") and f != "Kind")
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
