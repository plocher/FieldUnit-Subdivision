#!/usr/bin/env python3
"""Lint the step 4 symbol libraries by their fields (checkpoint rev 9: symbol names decide nothing).

    python3 tools/contract/lint_symbol_fields.py [--libdir DIR] [--table]

Per symbol, by Role:
- APPLIANCE: Appliance present; no Kind.
- DEVICE, PANEL: Appliance present; no Kind; one `Pin.<base>` per function pin (Column excepted) and
  no `Pin.*` without a pin; capability from the vocabulary; electrical type agrees with it (the
  device is driven by an "out" capability, so the pin is input; it drives an "in", so output);
  no retired field (a pin's base name as a field, ControlToken, Vital, NormalIs, Chain, Index);
  every other field, the settings, is lower_snake_case; `Invert` names only this symbol's pins;
  one capability per unit, so a symbol whose pins mix capabilities is multi-unit, with its units
  not interchangeable and its Value not autoplaced (the units mesh and show one name).
- IODRIVER: IC present; no Kind; `Pin.*` per pin; electrical type agrees (output for an "out"
  capability, input for "in", bidirectional for "bidirectional"); Address or a GPIO Value rule.
- SETTING: one passive pin, no Pin.*.
- TRACK, POLICY, STRUCTURE, COLUMN, MACHINE, CODELINE_*: Kind allowed; nothing else checked.
`--table` prints every symbol as a markdown row. Exit 1 on any error.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kicad_services.sch_text import library_symbols  # noqa: E402

LIBDIR = Path.home() / "Dropbox/KiCad/Railroad/symbols"
LIBRARIES = ("RailroadPlant", "RailroadDevice", "RailroadDesk")
VOCABULARY = {"binary in", "binary out", "binary bidirectional", "level in", "level out",
              "level bidirectional", "position out", "color out", "pixel out", "message in", "message out"}
STRUCTURAL = {"TRACK", "POLICY", "STRUCTURE", "COLUMN", "MACHINE", "CODELINE_TRANSPORT", "CODELINE_ENCODING"}
FUNCTIONAL = {"APPLIANCE", "DEVICE", "PANEL", "IODRIVER", "SETTING"}
RETIRED_FIELDS = {"ControlToken", "Vital", "NormalIs", "Chain", "Index", "Kind"}
NOT_SETTINGS = {"Role", "Appliance", "Style", "IC", "Address", "Invert", "IndicationToken", "Color", "CP", "TC",
                "IndicationCeiling", "Display", "Processor", "Milepost", "Reference", "Value", "Footprint",
                "Datasheet", "Description", "ki_keywords", "ki_fp_filters", "ki_description"}
MEMBERSHIP_PINS = {"Column"}
SNAKE = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")


def base(pin: str) -> str:
    m = re.match(r"^~\{(.+)\}$", pin)
    return m.group(1) if m else pin


def expected_etype(role: str, cap: str) -> str | None:
    word = cap.split()[-1]
    if role == "IODRIVER":
        return {"in": "input", "out": "output", "bidirectional": "bidirectional"}.get(word)
    return {"in": "output", "out": "input", "bidirectional": "bidirectional"}.get(word)


def lint_symbol(lib: str, name: str, sym: dict) -> list[tuple[str, str]]:
    """[(severity, message)] for one symbol."""
    out: list[tuple[str, str]] = []
    props, pins = sym["properties"], sym["pins"]
    role = props.get("Role", "")
    err = lambda m: out.append(("error", f"{lib}:{name}: {m}"))
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
    if role in {"DEVICE", "PANEL", "IODRIVER"}:
        for n, num, ty in function_pins:
            cap = pin_caps.get(base(n))
            if cap is None:
                err(f"pin {n} has no Pin.{base(n)}")
                continue
            if cap not in VOCABULARY:
                err(f"Pin.{base(n)} = {cap!r} is not in the vocabulary")
                continue
            want = expected_etype(role, cap)
            if want and ty != want:
                err(f"pin {n} is {ty}; {cap!r} on a {role} pin wants {want}")
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
    if role == "IODRIVER" and "Address" not in props and props.get("IC") != "GPIO":
        err("Address missing on a bus device")
    if role in {"DEVICE", "PANEL"}:
        caps = {pin_caps.get(base(n), "?") for n, _, _ in function_pins}
        pin_units = {u: p for u, p in sym["units"].items() if p}
        for u, names in pin_units.items():
            unit_caps = {pin_caps.get(base(n), "?") for n in names if n not in MEMBERSHIP_PINS}
            if len(unit_caps) > 1:
                err(f"unit {u} mixes {', '.join(sorted(unit_caps))}; one capability per unit")
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
        syms = library_symbols((a.libdir / f"{lib}.kicad_sym").read_text())
        for name, sym in syms.items():
            count += 1
            findings += lint_symbol(lib, name, sym)
            rows.append(row(lib, name, sym))
    if a.table:
        print("| Library | Symbol | Role | Appliance | Style | IC | Pin.* | Invert | Settings |")
        print("|---|---|---|---|---|---|---|---|---|")
        print("\n".join(rows))
    for sev, msg in findings:
        print(f"{sev}: {msg}")
    errors = sum(1 for s, _ in findings if s == "error")
    print(f"{count} symbols, {errors} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
