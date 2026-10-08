#!/usr/bin/env python3
"""Lint the symbol libraries against the (Role, Kind) table (FieldUnit ADR 0003 rule 8).

    python3 tools/contract/lint_libraries.py [--table schemas/symbols/role-kind.toml] [--libdir DIR]

Checks, per table row: Role and Kind spelling, unique keys, listed symbols exist, pin types valid.
Per library symbol: it is in exactly one row; its Role and Kind match that row; its pins are the
row's required pins plus optional packaging and membership pins; every BIT pin carries a polarity
attribute named for it and no other pin does (ADR 0003 D6); its attributes are the row's.
Exit status 1 when any error is found. Warnings and notes never fail the run.
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kicad_services.sch_text import library_symbols  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
TABLE = REPO / "schemas/symbols/role-kind.toml"
LIBDIR = Path.home() / "Dropbox/KiCad/InterlockingPlant/symbols"
LIBRARIES = ("Railroad", "RailroadPanel", "RailroadField")

# Naming axiom 4 (ADR 0003) and the machine Roles.
ROLES = {"APPLIANCE", "PANEL", "DEVICE", "IODRIVER", "TRACK", "POLICY", "STRUCTURE",
         "COLUMN", "MACHINE", "CODELINE_TRANSPORT", "CODELINE_ENCODING"}
PIN_TYPES = {"BIT", "LEVEL", "DUTY", "ANGLE", "TRACK", "SIGNAL", "HEAD", "HOUSE", "COLUMN", "CODELINE", "ENCODING"}
KIND = re.compile(r"^[A-Z0-9]+(?:[_-][A-Z0-9]+)*$")
BARRED = re.compile(r"^~\{(.+)\}$")


@dataclass(frozen=True)
class Finding:
    severity: str  # error | warning | note
    subject: str
    message: str


def base(pin: str) -> tuple[str, bool]:
    """(base name, asserted-low) of a pin name."""
    m = BARRED.match(pin)
    return (m.group(1), True) if m else (pin, False)


def lint(table: dict, libs: dict[str, dict]) -> list[Finding]:
    out: list[Finding] = []
    rows = table.get("row", [])
    owner: dict[str, dict] = {}
    seen: set[tuple[str, str]] = set()
    for row in rows:
        key = f'{row["role"]}/{row["kind"]}'
        if row["role"] not in ROLES:
            out.append(Finding("error", key, f'Role {row["role"]!r} is not in naming axiom 4'))
        if not KIND.match(row["kind"]):
            out.append(Finding("error", key, "Kind is not upper case FAMILY_IMPLEMENTATION[_FEEDBACK]"))
        if (row["role"], row["kind"]) in seen:
            out.append(Finding("error", key, "duplicate (Role, Kind) row"))
        seen.add((row["role"], row["kind"]))
        types = {**row.get("pins", {}), **row.get("packaging", {}), **row.get("membership", {})}
        for pin, ty in types.items():
            if not set(ty.split("|")) <= PIN_TYPES:
                out.append(Finding("error", key, f"pin {pin}: unknown type {ty!r}"))
        for sym in row.get("symbols", []):
            if sym in owner:
                out.append(Finding("error", sym, f'in two rows: {owner[sym]["kind"]} and {row["kind"]}'))
            owner[sym] = row
            if sym not in libs:
                out.append(Finding("error", sym, f"listed by {key} but not in the libraries"))
    for sym, s in sorted(libs.items()):
        props = s["properties"]
        row = owner.get(sym)
        if row is None:
            out.append(Finding("error", sym, f'not in the table (library Role {props.get("Role")!r}, '
                                             f'Kind {props.get("Kind")!r})'))
            continue
        key = f'{row["role"]}/{row["kind"]}'
        if props.get("Role", "") != row["role"] or props.get("Kind", "") != row["kind"]:
            out.append(Finding("error", sym, f'library Role/Kind {props.get("Role", "")}/{props.get("Kind", "")} '
                                             f"!= table {key}" + (" (proposed)" if row.get("proposed") else "")))
        required = row.get("pins", {})
        allowed = {**required, **row.get("packaging", {}), **row.get("membership", {})}
        names: dict[str, list[bool]] = {}
        for pin, _num, _etype in s["pins"]:
            b, low = base(pin)
            names.setdefault(b, []).append(low)
        for b in sorted(set(required) - set(names)):
            out.append(Finding("error", sym, f"missing pin {b} ({required[b]}) required by {key}"))
        for b in sorted(set(names) - set(allowed)):
            out.append(Finding("error", sym, f"pin {b} is not in {key}"))
        for b, lows in names.items():
            if len(lows) > 1 and b != "Column":
                ok = row["role"] == "PANEL" and sorted(lows) == [False, True] and allowed.get(b) == "BIT"
                if not ok:
                    out.append(Finding("error", sym, f"pin {b} appears {len(lows)} times; allowed only on a "
                                                     "PANEL symbol as X and ~{X} of a two-state token (D6)"))
        # polarity attributes: one per BIT pin (devices and panels), none on other pins
        polarity = {b for b in names if allowed.get(b) == "BIT" and row["role"] != "IODRIVER"}
        for b in sorted(polarity):
            if b not in props:
                out.append(Finding("error", sym, f"BIT pin {b} has no polarity attribute {b}= (D6)"))
            elif props[b]:
                out.append(Finding("warning", sym, f"polarity attribute {b}={props[b]!r}: the library leaves it blank"))
            if names[b] == [False] and row["role"] in ("DEVICE", "PANEL"):
                out.append(Finding("note", sym, f"BIT pin {b} is asserted-high (the exception to D6)"))
        for b in sorted(names):
            if b in props and b not in polarity and allowed.get(b) in ("LEVEL", "DUTY", "ANGLE"):
                out.append(Finding("error", sym, f"{allowed[b]} pin {b} carries a polarity attribute"))
        attrs = row.get("attributes", {})
        for a in sorted(set(props) - {"Role", "Kind"} - polarity - set(attrs)):
            out.append(Finding("error", sym, f"attribute {a}={props[a]!r} is not in {key}"))
        for a in sorted(set(attrs) - set(props)):
            out.append(Finding("warning", sym, f"attribute {a} of {key} is missing from the library"))
    return out


def load_libraries(libdir: Path) -> dict[str, dict]:
    libs = {}
    for lib in LIBRARIES:
        for name, s in library_symbols((libdir / f"{lib}.kicad_sym").read_text()).items():
            libs[f"{lib}:{name}"] = s
    return libs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--table", type=Path, default=TABLE)
    ap.add_argument("--libdir", type=Path, default=LIBDIR)
    a = ap.parse_args(argv)
    table = tomllib.loads(a.table.read_text())
    findings = lint(table, load_libraries(a.libdir))
    order = {"error": 0, "warning": 1, "note": 2}
    for f in sorted(findings, key=lambda f: (order[f.severity], f.subject)):
        print(f"{f.severity:8} {f.subject:46} {f.message}")
    counts = {s: sum(f.severity == s for f in findings) for s in order}
    print(f"{len(table.get('row', []))} rows; {counts['error']} errors, {counts['warning']} warnings, "
          f"{counts['note']} notes")
    return 1 if counts["error"] else 0


if __name__ == "__main__":
    sys.exit(main())
