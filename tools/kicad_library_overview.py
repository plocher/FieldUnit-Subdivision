#!/usr/bin/env python3
"""Write a static HTML overview of KiCad symbol libraries: every field, pin, unit and graphic.

    python3 tools/kicad_library_overview.py LIB.kicad_sym [LIB2.kicad_sym ...] [--out DIR] [--title TEXT] [--no-render]

One row per symbol: library, symbol name, every property (the standard KiCad fields first, then
Role, Appliance, Style, IC, Address, Invert, then Pin.* sorted, then the rest sorted), the pins
(name, number, electrical type and the Pin.<base> value when the symbol has one), the unit
structure, and one SVG per unit from `kicad-cli sym export svg`, written to <out>/svg-<library>/
and referenced by relative path. The page is plain HTML with inline CSS and JavaScript (no server,
no CDN): the table sorts on several columns at once (click a header to add it as the lowest key,
again to reverse it, a third time to drop it; each sorting header shows its priority and direction),
filters by a search box, per-column text boxes and a per-column value picker (a funnel button
listing the distinct values with counts), and shows or hides columns. The Columns control groups
them (Core, KiCad fields, Contract, Pin.*, Settings, Other), each group with a tri-state parent
checkbox, a shown/total count and a fold; shift-click selects a range within a group; a text
filter and All/None act on the filtered entries; "Show only Core" and "Show all" are one click, and
a right-click on a table header offers hide this column, hide its group, show only Core and show
all. Fields that no symbol fills start hidden; hiding a column that is a sort key drops it from the
sort. Column widths can be dragged at the header's right edge (the default width is the larger of a
per-kind minimum and the measured header title at the current text size) and columns reordered by
dragging a header onto another; the graphics have a scale control: S/M/L/XL presets (10, 20, 30
and 45 px per mm of the drawing, L the default) plus a "px/mm" box for any scale from 2 to 100, and
a "max px" box (empty, "none", by default; 200 to 20000 when set, 0 or empty clears it) for an
optional ceiling on an image's longer side. Every symbol SVG kicad-cli writes is at the same scale,
so every image is drawn at that one scale (its size in mm read from the width and height on the
root element and emitted on each img as `--w` and `--h`): pins, text and bodies are the same size
across symbols and a 16-pin chip is simply taller than a 4-pin unit (at 30 px/mm a 111 mm chip is
about 3330 px tall, as intended); there is no floor and, by default, no ceiling. When the user types
a ceiling, an image whose longer side would exceed it is shrunk to it and gets the class `capped`
(a dashed border) and a title suffix naming the ceiling and the scale it actually got; with no
ceiling nothing is marked. An image of unknown size is drawn in a nominal square (24 mm at the
scale, at least 240 px). The CSS clamp() rule does the sizing from `--w` and `--h` on the img and
`--scale`, `--floor` (0) and `--ceil` (a far-off sentinel when there is none) on the table; the
script sets those from the settings, marks the capped images and sets the Graphics column's
default width to the widest row of units (the images' rendered widths with their borders, margins
and the cell padding, at least 240 and at most 2400 px), so the units of a multi-unit symbol sit
side by side unless the user narrows the column; a dragged width wins and the units then wrap;
rows may be tall. The text has an S/M/L size control (10, 11.5 and 13.5 points) with a "pt" box for
any other size; every text rule inherits the one `--fs` variable on the body, so the whole page
scales together. The column set, order, dragged widths, image scale and ceiling, text size, sort
keys and folded groups are remembered in localStorage when available (under a versioned key); the
value filters and the measured default widths are not.

A second tab, Conventions (also reached as #conventions), audits whether the libraries apply their
field conventions consistently. One group of rows per kind: the Role, Appliance, Kind, Style and IC
a symbol carries (fields, never the symbol name), one row per symbol that draws the kind
(library:name). Its columns are the conventions: the raw Name, Control and Indication fields (the
`${...}` macros as written; absent is shown as a dash), the per-pin tokens (every `Control.<pin>` and
`Indication.<pin>` field, and on a PANEL lever each function pin's expected one), the pins as
base=Pin.* drive (seam pins such as Column left out; a Pin.* naming no pin is listed and flagged),
the unit structure (each unit with pins: its drive words and its pin bases, membership pins
included), the other fields, and the symbol-field lint's messages (`lint_symbol`, the same messages
as the lint's command line). A token's value is never checked, only its presence. A cell is
flagged, with its reasons inline and in its tooltip, by these rules.

General (kept from the first audit):
- G1 the symbols of one kind disagree in that column (Pins and Units compare as sets per unit; Other
  fields compares the field names, not their values; Tokens the field names);
- G2 Name is absent while some kind of the same Role carries it;
- G3 an other field is absent while a symbol of the same family carries it (family: Role and
  Appliance, or the kind itself where there is no Appliance); lower_snake_case settings are
  per-device and never compared, and a field the rulings below supersede is never asked for;
- G4 a Pin.* field names no pin.

The owner's token rulings (2026-10-28), which the libraries do not follow yet; the page shows the gap:
- R1 a PANEL lever (Appliance lever) states a token per function pin: `Control.<pin>` on an output
  pin, `Indication.<pin>` on an input pin. A missing one is flagged, unless the pin deliberately has
  none (EXEMPT_PINS: the lock lever's UNUSED, the code lever's CODE, keyed by Appliance and Style);
  one of the wrong direction is flagged; a `Control.X` or `Indication.X` naming no pin is flagged on
  any symbol; the whole-symbol `Control` and `Indication` on a lever are the superseded form.
- R2 a model board lamp (a PANEL lamp whose only function pin is LAMP) states one whole-symbol
  `Indication` (an expression); its LAMP pin is a driver wire, so no `Indication.LAMP` is expected;
  `IndicationToken` is the superseded form.
- R3 an APPLIANCE carries no tokens (it matches its panel appliance by Name): a `Control` or
  `Indication` field on one is unexpected; lacking them is never flagged.
- R4 `Invert` on a PANEL symbol is superseded (the inversion goes into the token, e.g.
  `Indication.WLK=!${Value}WLK`); its absence is never flagged. DEVICE and IODRIVER keep `Invert`.
- R5 a PANEL lamp pin (an input function pin) states `binary`; a level or PWM driver may still drive
  it, which is a binding, not a pin value. Any other Pin.* value is flagged.
- R6 a retiring kind (RETIRING: the PANEL lamp with Style indication, PanelMCall-Lamp) is marked
  "retiring" and its cells are not flagged.
Nothing else is asked of a kind. "Only flagged kinds" hides the clean groups; the search box
matches any text.

The default <out> is <directory of the first library>/production/overview/ (the Railroad repo
gitignores production/). `--no-render` skips kicad-cli and omits the graphics column.
"""

from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kicad_services.sch_text import library_standard_properties, library_symbols  # noqa: E402
from contract.lint_symbol_fields import MEMBERSHIP_PINS, library_bodies, lint_symbol  # noqa: E402

KICAD_CLI_APP = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
PAGE_NAME = "library-overview.html"
LEAD_FIELDS = ("Role", "Appliance", "Style")            # shown first, before the graphics
NAMED_FIELDS = ("Description", "IC", "Address", "Invert", "Reference", "Value", "Footprint", "Datasheet")
FIXED_HEAD = ("Library", "Symbol", "Extends")
ALWAYS_SHOWN = {"Library", "Symbol", "Extends", "Role", "Appliance", "Style", "Graphics", "Description", "Pins", "Units"}
# Column groups of the Columns control, in display order. Core is ALWAYS_SHOWN; Pin.* is every Pin.<base>
# field; Settings is every lower_snake_case field; Other is whatever is left (Kind, ki_* excluded by Settings).
KICAD_FIELDS = ("Reference", "Value", "Footprint", "Datasheet")
CONTRACT_FIELDS = ("IC", "Address", "Invert", "Color", "IndicationToken", "IndicationCeiling", "CP Name", "Control", "Indication", "TC",
                   "Processor", "Display", "Milepost")
GROUPS = ("Core", "KiCad fields", "Contract", "Pin.*", "Settings", "Other")
DEFAULT_CLOSED_GROUPS = ("Pin.*", "Settings")
_SNAKE_CASE = re.compile(r"^[a-z][a-z0-9_]*$")
_SVG_NAME = re.compile(r"^(.*)_unit(\d+)$")
_SVG_ROOT = re.compile(r"<svg\b[^>]*>", re.S)
_SVG_LENGTH = re.compile(r'\b(width|height)\s*=\s*"\s*([0-9.]+)\s*([a-z%]*)\s*"')
_SVG_MM_PER_UNIT = {"": 25.4 / 96, "px": 25.4 / 96, "in": 25.4, "cm": 10.0, "mm": 1.0, "pt": 25.4 / 72, "pc": 25.4 / 6}
IMG_SCALES = {"S": 10, "M": 20, "L": 30, "XL": 45}         # px per mm of drawing: the scale presets
IMG_SCALE_DEFAULT = 30                                      # the L preset
IMG_SCALE_RANGE = (2, 100, 1)                               # the "px/mm" box: min, max, step
IMG_CEILING_DEFAULT = None                                  # px: the ceiling on an image's longer side; None is no ceiling ...
IMG_CEILING_RANGE = (200, 20000, 50)                        # ... the "max px" box when one is typed: min, max, step
IMG_UNLIMITED_PX = 10_000_000                               # what --ceil carries when there is no ceiling: far beyond any image
IMG_FLOOR = 0                                               # px: the least an image's longer side gets (none: one scale throughout)
IMG_NOMINAL_MM = 24                                         # an image of unknown size is a square of this many mm at the scale ...
IMG_COLUMN_MIN = 240                                        # ... or at least this many px; also the Graphics column's least width ...
IMG_COLUMN_MAX = 2400                                       # ... (the widest row of units) and its most, in px


def css_ceiling(ceiling: int | None = IMG_CEILING_DEFAULT) -> int:
    """The --ceil value for a ceiling: the number, or the far-off sentinel for none."""
    return IMG_UNLIMITED_PX if ceiling is None else ceiling


def nominal_px(scale: float = IMG_SCALE_DEFAULT, ceiling: int | None = IMG_CEILING_DEFAULT) -> int:
    """The side of the square an image of unknown size is drawn in: IMG_NOMINAL_MM at the scale, at least
    IMG_COLUMN_MIN, and never above the ceiling."""
    return min(max(round(scale * IMG_NOMINAL_MM), IMG_COLUMN_MIN), css_ceiling(ceiling))


@dataclass
class Symbol:
    library: str
    name: str
    fields: dict[str, str]
    pins: list[tuple[str, str, str]]          # (name, number, electrical type)
    units: dict[int, list[str]]               # unit number -> pin names (0 = common to all units)
    extends: str | None = None
    graphics: list[str] = field(default_factory=list)  # SVG paths relative to the page
    sizes: dict[str, tuple[float, float]] = field(default_factory=dict)  # SVG path -> (width, height) mm; absent when unknown
    lint: list[tuple[str, str]] = field(default_factory=list)           # (severity, message) from lint_symbol, no prefix


def find_kicad_cli() -> str | None:
    """kicad-cli from KICAD_CLI, then PATH, then the macOS app bundle; None when absent."""
    for candidate in (os.environ.get("KICAD_CLI"), shutil.which("kicad-cli"), KICAD_CLI_APP):
        if candidate and Path(candidate).is_file():
            return candidate
    return None


def pin_base(name: str) -> str:
    """The Pin.<base> field name for a pin: `~{OCC}` (overbar) has the base `OCC`."""
    m = re.match(r"^~\{(.+)\}$", name)
    return m.group(1) if m else name


def property_columns(names: set[str]) -> list[str]:
    """Stable column order for the union of field names across the symbols: Role, Appliance, Style,
    Description, the other named fields, Pin.* sorted, then everything else sorted."""
    head = [n for n in LEAD_FIELDS + NAMED_FIELDS if n in names]
    pins = sorted(n for n in names if n.startswith("Pin."))
    rest = sorted(names - set(head) - set(pins), key=lambda n: (n.lower(), n))
    return head + pins + rest


def column_group(name: str) -> str:
    """The Columns-control group of a column: one of GROUPS."""
    if name in ALWAYS_SHOWN:
        return "Core"
    if name in KICAD_FIELDS:
        return "KiCad fields"
    if name in CONTRACT_FIELDS:
        return "Contract"
    if name.startswith("Pin."):
        return "Pin.*"
    if _SNAKE_CASE.match(name):
        return "Settings"
    return "Other"


def load_library(lib_file: Path) -> list[Symbol]:
    """The symbols of one library in file order; a derived symbol inherits what it does not restate. Each carries
    the symbol-field lint's messages for it, linted as the lint's command line does (the symbol as written)."""
    text = lib_file.read_text()
    standard = library_standard_properties(text)
    symbols = library_symbols(text)
    bodies = library_bodies(text)
    out: dict[str, Symbol] = {}
    for name, sym in symbols.items():
        fields = {**standard.get(name, {}), **sym["properties"]}
        s = Symbol(lib_file.stem, name, fields, list(sym["pins"]), dict(sym["units"]), sym["extends"])
        prefix = f"{lib_file.stem}:{name}: "
        s.lint = [(sev, msg.removeprefix(prefix)) for sev, msg in lint_symbol(lib_file.stem, name, sym, bodies.get(name))]
        parent = out.get(s.extends) if s.extends else None
        if parent:
            s.fields = {**parent.fields, **s.fields}
            s.pins = s.pins or parent.pins
            s.units = s.units or parent.units
        out[name] = s
    return list(out.values())


def render(kicad_cli: str, lib_file: Path, svg_dir: Path) -> dict[str, list[str]]:
    """{symbol name: [svg file names]} after rendering every unit of lib_file into svg_dir."""
    shutil.rmtree(svg_dir, ignore_errors=True)
    svg_dir.mkdir(parents=True)
    subprocess.run([kicad_cli, "sym", "export", "svg", "-o", str(svg_dir), str(lib_file)],
                   check=True, capture_output=True)
    files: dict[str, list[tuple[int, str]]] = {}
    for f in svg_dir.iterdir():
        m = _SVG_NAME.match(f.stem)
        if m and f.suffix == ".svg":
            files.setdefault(m.group(1), []).append((int(m.group(2)), f.name))
    return {name: [n for _, n in sorted(units)] for name, units in files.items()}


def svg_size_mm(svg_file: Path) -> tuple[float, float] | None:
    """(width, height) in mm from the root <svg> tag's width and height attributes (any CSS length unit,
    unitless counts as px; kicad-cli writes mm), or None when the file, the tag or either attribute is
    unreadable or a side is not positive."""
    try:
        head = svg_file.read_text(errors="replace")[:4096]
    except OSError:
        return None
    root = _SVG_ROOT.search(head)
    if not root:
        return None
    lengths = {attr: (value, unit) for attr, value, unit in _SVG_LENGTH.findall(root.group(0))}
    sides = []
    for attr in ("width", "height"):
        value, unit = lengths.get(attr, ("", ""))
        if unit not in _SVG_MM_PER_UNIT:
            return None
        try:
            sides.append(float(value) * _SVG_MM_PER_UNIT[unit])
        except ValueError:
            return None
    width, height = sides
    return (width, height) if width > 0 and height > 0 else None


# --- conventions: one group per kind, one row per symbol, a cell per convention (the module docstring has the rules) ---

KEY_FIELDS = ("Role", "Appliance", "Kind", "Style", "IC")       # what a kind is, in label order; empty values do not count
TOKEN_FIELDS = ("Name", "Control", "Indication")               # the whole-symbol fields, one column each
PIN_TOKENS = ("Control.", "Indication.")                       # per-pin token fields (R1): Control.<pin>, Indication.<pin>
CONVENTION_COLUMNS = TOKEN_FIELDS + ("Tokens", "Pins", "Units", "Other fields")
NOT_OTHER = set(KICAD_FIELDS) | {"Description"} | set(KEY_FIELDS) | set(TOKEN_FIELDS)   # plus Pin.*, ki_* and the per-pin tokens
ABSENT = "—"                                              # how an absent field shows
# R1: function pins of a PANEL lever that deliberately state no token, by (Appliance, Style) (owner, 2026-10-28).
EXEMPT_PINS = {("lever", "lock"): {"UNUSED"}, ("lever", "code"): {"CODE"}}
# R6: kinds to be retired after the bulk change, by their fields: marked, never flagged (owner, 2026-10-28).
RETIRING = ({"Role": "PANEL", "Appliance": "lamp", "Style": "indication"},)


@dataclass
class Cell:
    text: str                                 # what the cell shows
    key: object                               # what is compared between the symbols of one kind
    flags: list[str] = field(default_factory=list)


@dataclass
class KindRow:
    key: tuple[tuple[str, str], ...]          # ((field, value), ...) in KEY_FIELDS order
    symbols: list[Symbol]
    cells: list[dict[str, Cell]]              # per symbol, one Cell per CONVENTION_COLUMNS entry
    retiring: bool = False                    # R6: marked, its cells never flagged

    @property
    def label(self) -> str:
        return (" · ".join(f"{f}={v}" for f, v in self.key) or "(no Role)") + (" (retiring)" if self.retiring else "")

    @property
    def flagged(self) -> int:
        return sum(1 for row in self.cells for c in row.values() if c.flags)


def kind_key(s: Symbol) -> tuple[tuple[str, str], ...]:
    return tuple((f, s.fields[f]) for f in KEY_FIELDS if s.fields.get(f))


def family_key(s: Symbol) -> tuple:
    """Role and Appliance; the kind itself where the symbol has no Appliance."""
    return (s.fields.get("Role", ""), s.fields["Appliance"]) if s.fields.get("Appliance") else kind_key(s)


def other_fields(s: Symbol) -> list[str]:
    return [f for f in s.fields if f not in NOT_OTHER and not f.startswith(("Pin.", "ki_") + PIN_TOKENS)]


def function_pins(s: Symbol) -> list[tuple[str, str]]:
    """(base, electrical type) of every pin but the seam pins, in drawn order."""
    return [(pin_base(n), ty) for n, _, ty in s.pins if n not in MEMBERSHIP_PINS]


def is_panel_lever(s: Symbol) -> bool:
    return s.fields.get("Role") == "PANEL" and s.fields.get("Appliance") == "lever"


def is_board_lamp(s: Symbol) -> bool:
    """R2: a PANEL lamp whose only function pin is LAMP."""
    return (s.fields.get("Role") == "PANEL" and s.fields.get("Appliance") == "lamp"
            and [b for b, _ in function_pins(s)] == ["LAMP"])


def is_retiring(s: Symbol) -> bool:
    return any(all(s.fields.get(f) == v for f, v in r.items()) for r in RETIRING)


def superseded(s: Symbol) -> dict[str, str]:
    """{field: reason} for the fields the rulings supersede on this symbol, whether it carries them or not."""
    out = {}
    if is_panel_lever(s):
        out["Control"] = out["Indication"] = "R1: superseded by the per-pin Control.<pin> and Indication.<pin>"
    if is_board_lamp(s):
        out["IndicationToken"] = "R2: superseded by the whole-symbol Indication"
    if s.fields.get("Role") == "PANEL":
        out["Invert"] = "R4: superseded; the inversion goes into the token (Indication.X=!...)"
    return out


def expected_token(s: Symbol, base: str, etype: str) -> str | None:
    """R1: the per-pin token field a PANEL lever's function pin states; None when it states none."""
    exempt = EXEMPT_PINS.get((s.fields.get("Appliance"), s.fields.get("Style")), set())
    if not is_panel_lever(s) or base in exempt or etype not in ("output", "input"):
        return None
    return ("Control." if etype == "output" else "Indication.") + base


def tokens_cell(s: Symbol) -> Cell:
    """The per-pin tokens: on a PANEL lever one entry per function pin (R1), elsewhere the token fields it carries."""
    present = [f for f in s.fields if f.startswith(PIN_TOKENS)]
    pins = {b: ty for b, ty in function_pins(s)}
    items, flags = [], []
    if is_panel_lever(s):
        for b, ty in function_pins(s):
            want = expected_token(s, b, ty)
            have = [f for f in present if f.split(".", 1)[1] == b]
            if want is None and not have:
                items.append(f"{b}: none (deliberate)" if ty in ("output", "input") else f"{b}: none")
            for f in have:
                items.append(f"{f}={s.fields[f]}")
                if want and f != want:
                    flags.append(f"R1: {f} on a{'n' if ty[0] in 'aeiou' else ''} {ty} pin; {want} expected")
            if want and want not in have:
                items.append(f"{b}: {ABSENT}")
                flags.append(f"R1: missing {want}")
    for f in present:
        b = f.split(".", 1)[1]
        if b not in pins:
            items.append(f"{f}={s.fields[f]} (no pin)")
            flags.append(f"R1: {f} names no pin")
        elif not is_panel_lever(s):
            items.append(f"{f}={s.fields[f]}")
            if is_board_lamp(s) and b == "LAMP":
                flags.append(f"R2: {f} not expected; LAMP is a driver wire, the lamp states one Indication")
    return Cell(", ".join(items), tuple(sorted(present)), flags)


def symbol_cells(s: Symbol) -> dict[str, Cell]:
    """The convention cells of one symbol, before any comparison: the values as written."""
    cells = {f: Cell(s.fields[f] if f in s.fields else ABSENT, s.fields.get(f)) for f in TOKEN_FIELDS}
    cells["Tokens"] = tokens_cell(s)
    drive = lambda b: s.fields.get("Pin." + b)                 # None: the pin has no Pin.* (a trackplan appliance's pins)
    bases = [b for b, _ in function_pins(s)]
    orphans = sorted(f[4:] for f in s.fields if f.startswith("Pin.") and f[4:] not in {pin_base(n) for n, _, _ in s.pins})
    pins = [f"{b}={drive(b)}" if drive(b) else b for b in bases] + [f"Pin.{b}={s.fields['Pin.' + b]} (no pin)" for b in orphans]
    cells["Pins"] = Cell(", ".join(pins), tuple(sorted(pins)), [f"Pin.{b} names no pin" for b in orphans])
    if s.fields.get("Role") == "PANEL":                         # R5: a lamp pin (an input function pin) states binary
        cells["Pins"].flags += [f"R5: lamp pin {b} is {drive(b)}; lamp pins state binary"
                                for b, ty in function_pins(s) if ty == "input" and drive(b) and drive(b) != "binary"]
    units = []
    for u in sorted(s.units):
        names = [pin_base(n) for n in s.units[u]]
        if names:                                              # drive words of the unit's pins; "seam" when all are seam pins
            words = "seam" if all(n in MEMBERSHIP_PINS for n in names) else "/".join(sorted({d for n in names if (d := drive(n))}))
            units.append((u, words, names))
    cells["Units"] = Cell("; ".join(f"{u}{f' [{w}]' if w else ''}: {' '.join(n)}" for u, w, n in units),
                          tuple((u, w, tuple(sorted(n))) for u, w, n in units))
    other = other_fields(s)
    cells["Other fields"] = Cell(", ".join(f"{f}={s.fields[f]}" if s.fields[f] else f for f in other), frozenset(other))
    return cells


def carriers_text(names: list[str], limit: int = 3) -> str:
    return ", ".join(names[:limit]) + (f" and {len(names) - limit} more" if len(names) > limit else "")


def convention_kinds(symbols: list[Symbol]) -> list[KindRow]:
    """One KindRow per kind (sorted by its key), each cell flagged by the rules in the module docstring."""
    groups: dict[tuple, list[Symbol]] = {}
    for s in symbols:
        groups.setdefault(kind_key(s), []).append(s)
    kinds = [KindRow(k, members, [symbol_cells(s) for s in members], all(is_retiring(s) for s in members))
             for k, members in sorted(groups.items())]
    ref = lambda s: f"{s.library}:{s.name}"
    for kind in kinds:
        # G1: the symbols of one kind disagree in a column.
        for col in CONVENTION_COLUMNS:
            variants = {repr(row[col].key) for row in kind.cells}
            if len(variants) > 1:
                for row in kind.cells:
                    row[col].flags.append(f"the {len(kind.symbols)} symbols of this kind disagree ({len(variants)} variants)")
        for s, row in zip(kind.symbols, kind.cells):
            role = s.fields.get("Role", "")
            gone = superseded(s)
            # G2: Name absent here and carried by a kind of the same Role.
            if "Name" not in s.fields:
                by_role = [ref(o) for o in symbols if "Name" in o.fields and o.fields.get("Role", "") == role]
                if by_role:
                    row["Name"].flags.append(f"missing; Role {role} carries it on {carriers_text(by_role)}")
            for f in ("Control", "Indication"):
                if f in s.fields and f in gone:                # R1: the whole-symbol form on a lever
                    row[f].flags.append(gone[f])
                if f in s.fields and role == "APPLIANCE":      # R3: an appliance matches its panel appliance by Name
                    row[f].flags.append("R3: unexpected; an APPLIANCE carries no tokens (it matches by Name)")
            if is_board_lamp(s) and "Indication" not in s.fields:
                row["Indication"].flags.append("R2: missing; a model board lamp states one Indication expression")
            for f in ("IndicationToken", "Invert"):             # R2, R4: superseded fields carried
                if f in s.fields and f in gone:
                    row["Other fields"].flags.append(f"{f}: {gone[f]}")
            # G3: a non-setting other field absent here, carried in the family, and not superseded here.
            mine = set(other_fields(s))
            family = [o for o in symbols if family_key(o) == family_key(s)]
            wanted = {f for o in family for f in other_fields(o) if not _SNAKE_CASE.match(f)} - mine - set(gone)
            for f in sorted(wanted, key=str.lower):
                row["Other fields"].flags.append(
                    f"missing {f}; carried by {carriers_text([ref(o) for o in family if f in o.fields])}")
        if kind.retiring:                                      # R6: marked, never flagged
            for row in kind.cells:
                for c in row.values():
                    c.flags.clear()
    return kinds



# --- page -----------------------------------------------------------------------------------

STYLE = """
body{--fs:10pt;font-family:system-ui,sans-serif;font-size:var(--fs);line-height:1.4;margin:1em;color:#222;background:#fff}
h1{font-size:1.4em;margin:0 0 .3em}
.meta{color:#666;margin-bottom:.8em}
.controls{display:flex;flex-wrap:wrap;gap:.6em 1.2em;align-items:center;margin-bottom:.8em}
.controls input[type=search]{font:inherit;padding:.3em .5em;width:22em;max-width:100%}
.controls button,.controls select{font:inherit;padding:.25em .7em}
.controls input[type=number]{font:inherit;padding:.25em .3em;width:4.5em}
#count{color:#666}
[hidden]{display:none!important}
details.columns{position:relative}
details.columns summary{cursor:pointer;user-select:none}
#columns{position:absolute;z-index:3;background:#fff;border:1px solid #bbb;box-shadow:0 2px 8px #0003;
  padding:.5em .8em;min-width:40em;max-height:70vh;overflow:auto}
#columns p{margin:.2em 0 .5em}
#columns .colgroup{border-top:1px solid #ddd;padding:.3em 0}
#columns .grouphead{display:flex;align-items:center;gap:.3em;font-weight:600}
#columns .grouphead .fold{font:inherit;width:1.6em;padding:0;border:0;background:none;cursor:pointer;color:#669}
#columns .n{color:#666;font-weight:normal}
#columns .members{columns:3;column-gap:1.4em;padding-left:1.9em}
#columns .colgroup.closed .members{display:none}
#columns label{display:block;white-space:nowrap;break-inside:avoid}
#colmenu{position:absolute;z-index:5;background:#fff;border:1px solid #bbb;box-shadow:0 2px 8px #0003;padding:.3em 0;min-width:14em}
#colmenu button{display:block;width:100%;text-align:left;font:inherit;padding:.3em 1em;border:0;background:none;cursor:pointer}
#colmenu button:hover{background:#eef}
table{border-collapse:collapse;table-layout:fixed}
th,td{border:1px solid #ccc;padding:3px 5px;vertical-align:top;text-align:left;overflow-wrap:anywhere}
thead th{position:sticky;top:0;background:#eef;z-index:2}
thead th.sortable{cursor:pointer;user-select:none;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;padding-right:12px}
thead th.sortable::after{content:" \\2195";color:#99a}
thead th.asc::after{content:" " attr(data-rank) " \\25b2";color:#226}
thead th.desc::after{content:" " attr(data-rank) " \\25bc";color:#226}
thead th.dragging{opacity:.5}
thead th.dragover{outline:2px solid #58c;outline-offset:-2px}
thead th .grip{position:absolute;top:0;right:0;width:7px;height:100%;cursor:col-resize;user-select:none}
thead th .grip:hover{background:#9ab}
thead tr.filters th{top:1.9em;background:#f6f6fb;padding:1px 2px;font-weight:normal}
thead tr.filters .fwrap{display:flex;gap:2px}
thead tr.filters input{font:inherit;flex:1;min-width:0;box-sizing:border-box;padding:2px 3px}
thead tr.filters .funnel{font:inherit;padding:0 4px;border:1px solid #bbb;background:#fff;color:#669;cursor:pointer}
thead tr.filters .funnel.active{background:#cde;color:#126;border-color:#58c}
#valuepanel{position:absolute;z-index:4;background:#fff;border:1px solid #bbb;box-shadow:0 2px 8px #0003;
  padding:.5em .8em;min-width:16em;max-width:32em;max-height:60vh;overflow:auto}
#valuepanel input[type=search]{font:inherit;width:100%;box-sizing:border-box;padding:2px 3px}
#valuepanel p{margin:.4em 0}
#valuepanel button{font:inherit;padding:.15em .6em}
#valuepanel label{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#valuepanel .n{color:#666}
tbody tr:nth-child(even){background:#fafafa}
tbody tr:hover{background:#f0f4ff}
td.empty::after{content:"\\00b7";color:#aaa}
td.symbol{font-weight:600}
ul.pins,ul.units{margin:0;padding-left:1.1em}
ul.pins .num{color:#666}
ul.pins .etype{color:#36a}
ul.pins .cap{color:#262}
td.graphics img{width:var(--nom,NOM_PX);height:var(--nom,NOM_PX);background:#fff;border:1px solid #ddd;box-sizing:content-box;margin:2px;vertical-align:top}
td.graphics img.mm{--f:clamp(calc(var(--floor,FLOOR_PX) / max(var(--w), var(--h))), var(--scale,SCALE_PX), calc(var(--ceil,CEIL_PX) / max(var(--w), var(--h))));
  width:calc(var(--w) * var(--f) * 1px);height:calc(var(--h) * var(--f) * 1px)}
td.graphics img.capped{border-style:dashed;border-color:#c60}
nav.tabs{display:flex;gap:.3em;margin-bottom:.8em;border-bottom:1px solid #bbb}
nav.tabs button{font:inherit;padding:.3em 1em;border:1px solid #bbb;border-bottom:0;background:#f4f4f8;cursor:pointer;margin-bottom:-1px}
nav.tabs button[aria-selected=true]{background:#fff;font-weight:600}
table#conventions{table-layout:auto;width:100%;min-width:72em}
table#conventions th,table#conventions td{overflow-wrap:break-word}
table#conventions td{min-width:6em}
table#conventions thead th{top:0}
table#conventions tbody{border-top:2px solid #889}
table#conventions th.kind{background:#f4f4fb;width:14em;font-weight:600}
table#conventions th.kind .n{display:block;color:#666;font-weight:normal}
table#conventions td.ref{font-weight:600;white-space:nowrap}
table#conventions td.flag{background:#fff2e0}
table#conventions td.flag::before{content:"\\2691 ";color:#c60}
table#conventions .why{display:block;color:#a50;font-size:.85em}
table#conventions ul.lint{margin:0;padding-left:1.1em}
table#conventions .lint-error{color:#b00}
table#conventions .lint-warning{color:#a60}
""".replace("NOM_PX", f"{nominal_px()}px").replace("FLOOR_PX", str(IMG_FLOOR)).replace("SCALE_PX", str(IMG_SCALE_DEFAULT)) \
   .replace("CEIL_PX", str(css_ceiling())) \
   + f"table#symbols{{--scale:{IMG_SCALE_DEFAULT};--floor:{IMG_FLOOR};--ceil:{css_ceiling()};--nom:{nominal_px()}px}}\n"

SCRIPT = r"""
(function () {
  'use strict';
  var KEY = 'kicad-library-overview:v3:' + document.title;   // v3: sort is a list of keys; closed column groups
  var SCALES = SCALE_PRESETS;                                 // px per mm of drawing per graphics preset
  var SCALE_MIN = SCALE_RANGE[0], SCALE_MAX = SCALE_RANGE[1], SCALE_DEFAULT = SCALE_DEFAULT_PX;
  var CEIL_MIN = CEIL_RANGE[0], CEIL_MAX = CEIL_RANGE[1], CEIL_DEFAULT = CEIL_DEFAULT_JS;   // null: no ceiling
  var UNLIMITED = UNLIMITED_PX;                                // px: what --ceil carries when there is no ceiling
  var FLOOR = FLOOR_PX;                                        // px: the least an image's longer side gets (0: none)
  var NOMINAL_MM = NOMINAL_MM_VALUE;                           // an image of unknown size: a square of this many mm at the scale
  var COLUMN_MIN = COLUMN_MIN_PX, COLUMN_MAX = COLUMN_MAX_PX;  // the Graphics column's default width: the widest row of units, within these
  var FONTS = { S: 10, M: 11.5, L: 13.5 };                     // text size in points per size setting
  var FONT_MIN = 4, FONT_MAX = 72;
  var SORT_MARK = ' 9 ▼';                                 // the widest "<rank> ▼" a header appends
  var WIDTH_SLACK = 4;                                         // px beyond the measured title
  var table = document.getElementById('symbols');
  var headRow = table.tHead.rows[0], filterRow = table.tHead.rows[1];
  var rows = Array.prototype.slice.call(table.tBodies[0].rows);
  rows.forEach(function (r, i) { r.dataset.index = i; });
  var heads, filterCells, filters;                             // re-read from the DOM after a reorder
  var search = document.getElementById('search');
  var count = document.getElementById('count');
  var columnsBox = document.getElementById('columns');
  var toggles = Array.prototype.slice.call(columnsBox.querySelectorAll('.members input[type=checkbox]'));
  var labels = toggles.map(function (b) { return b.parentNode; });
  var toggleFor = {}, groupOf = {};
  toggles.forEach(function (b) { toggleFor[b.value] = b; groupOf[b.value] = b.closest('.colgroup').dataset.group; });
  var groups = Array.prototype.slice.call(columnsBox.querySelectorAll('.colgroup')).map(function (g) {
    return { name: g.dataset.group, box: g, parent: g.querySelector('.grouptoggle'), fold: g.querySelector('.fold'),
             n: g.querySelector('.grouphead .n'),
             members: toggles.filter(function (b) { return groupOf[b.value] === g.dataset.group; }), last: -1 };
  });
  var colfilter = document.getElementById('colfilter');
  var scaleSelect = document.getElementById('imgsize');
  var scaleInput = document.getElementById('scalepx');
  var ceilInput = document.getElementById('maxpx');
  var fontSelect = document.getElementById('fontsize');
  var fontInput = document.getElementById('fontpt');
  var panel = document.getElementById('valuepanel');
  var valueSearch = document.getElementById('valuesearch');
  var valueList = document.getElementById('valuelist');
  var menu = document.getElementById('colmenu');
  var defaultHidden = toggles.filter(function (b) { return !b.checked; }).map(function (b) { return b.value; });
  var defaultClosed = groups.filter(function (g) { return g.box.classList.contains('closed'); }).map(function (g) { return g.name; });
  var defaultOrder;
  var state, valueFilter = {}, panelCol = null, menuCol = null, resizing = false, dragCol = null;
  var measured = {};                                           // col -> header title width at the current text size; never saved
  var graphicsWidth = COLUMN_MIN;                              // the Graphics column's default width from the images; never saved

  function readHeads() {
    heads = Array.prototype.slice.call(headRow.cells);
    filterCells = Array.prototype.slice.call(filterRow.cells);
    filters = filterCells.map(function (c) { return c.querySelector('input'); });
  }
  readHeads();
  defaultOrder = heads.map(function (th) { return th.dataset.col; });

  function defaults() {
    return { hidden: defaultHidden.slice(), sort: [], widths: {}, order: defaultOrder.slice(),
             scale: SCALE_DEFAULT, ceiling: CEIL_DEFAULT, font: FONTS.S, closed: defaultClosed.slice() };
  }
  state = defaults();

  function isKey(k) { return k && typeof k.col === 'string' && (k.dir === 'asc' || k.dir === 'desc'); }
  function isFont(n) { return typeof n === 'number' && n >= FONT_MIN && n <= FONT_MAX; }
  function isScale(n) { return typeof n === 'number' && n >= SCALE_MIN && n <= SCALE_MAX; }
  function isCeiling(n) { return typeof n === 'number' && n >= CEIL_MIN && n <= CEIL_MAX; }
  function load() {
    try {
      var s = JSON.parse(localStorage.getItem(KEY));
      if (s && Array.isArray(s.hidden)) {
        state = defaults();
        state.hidden = s.hidden;
        if (Array.isArray(s.sort)) { state.sort = s.sort.filter(isKey); } else if (isKey(s.sort)) { state.sort = [s.sort]; }
        if (s.widths && typeof s.widths === 'object') { state.widths = s.widths; }
        if (Array.isArray(s.order)) { state.order = s.order; }
        if (isScale(s.scale)) { state.scale = s.scale; }         // an old `size` letter or `ppp` (px per pin) is ignored ...
        if (s.ppp === undefined && (s.ceiling === null || isCeiling(s.ceiling))) { state.ceiling = s.ceiling; }
        // ... and so is the ceiling a px-per-pin page saved beside it (that page had a default ceiling; this one has none)
        if (isFont(s.font)) { state.font = s.font; }
        if (Array.isArray(s.closed)) { state.closed = s.closed; }
      }
    } catch (e) { /* storage unavailable or corrupt: defaults */ }
  }
  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) { /* ignore */ }
  }
  function elementOf(e) {
    var t = e.target;
    return t && t.nodeType === 1 ? t : (t && t.parentElement) || document.documentElement;
  }
  function cellText(cell) {
    return cell.dataset.sort !== undefined ? cell.dataset.sort : cell.textContent.trim();
  }
  function cellValue(cell) { return cell.textContent.replace(/\s+/g, ' ').trim(); }
  function colIndex(col) {
    for (var i = 0; i < heads.length; i++) { if (heads[i].dataset.col === col) { return i; } }
    return -1;
  }

  // --- text size: one variable on the body, in points; S/M/L presets or any value typed in the pt box ---
  function applyFont() {
    document.body.style.setProperty('--fs', state.font + 'pt');
    var preset = '';
    Object.keys(FONTS).forEach(function (k) { if (FONTS[k] === state.font) { preset = k; } });
    fontSelect.value = preset;                                 // '' selects the hidden "custom" entry
    if (parseFloat(fontInput.value) !== state.font) { fontInput.value = state.font; }
    measureHeaders();                                          // the titles grew or shrank with the text
    applyWidths();
  }

  // --- graphics: one scale (and an optional ceiling) on the table; the CSS clamp() sizes every image from them ---
  function ceilingPx() { return state.ceiling === null ? UNLIMITED : state.ceiling; }   // what --ceil carries
  function nominal() { return Math.min(Math.max(state.scale * NOMINAL_MM, COLUMN_MIN), ceilingPx()); }   // the unknown-size square
  function imageSize(img) {
    // [width, height] in px as the CSS draws the image: both mm sides times one factor, the scale clamped so the
    // longer side stays between the floor and the ceiling (the CSS --f rule); an image of unknown size is a square.
    var w = parseFloat(img.style.getPropertyValue('--w')), h = parseFloat(img.style.getPropertyValue('--h'));
    if (!(w > 0 && h > 0)) { return [nominal(), nominal()]; }
    var f = Math.max(FLOOR / Math.max(w, h), Math.min(state.scale, ceilingPx() / Math.max(w, h)));
    return [w * f, h * f];
  }
  function markCapped() {
    // The CSS cannot say whether its clamp() applied, so mark each image whose longer side at the scale would
    // exceed the ceiling: a class (dashed border) and a title suffix naming the ceiling and the scale it got.
    // With no ceiling nothing is marked.
    Array.prototype.forEach.call(table.querySelectorAll('td.graphics img.mm'), function (img) {
      var longer = Math.max(parseFloat(img.style.getPropertyValue('--w')), parseFloat(img.style.getPropertyValue('--h')));
      if (img.dataset.title === undefined) { img.dataset.title = img.title; }
      var capped = state.ceiling !== null && longer > 0 && longer * state.scale > state.ceiling;
      img.classList.toggle('capped', capped);
      img.title = capped ? img.dataset.title + ' (capped at ' + state.ceiling + ' px, '
                           + (Math.round(state.ceiling / longer * 10) / 10) + ' px/mm)' : img.dataset.title;
    });
  }
  function measureGraphics() {
    // The Graphics column's default width: the widest row of units, each image's rendered width plus its border
    // and margin, plus the cell's padding and border, at least COLUMN_MIN and at most COLUMN_MAX px, so the units
    // of a multi-unit symbol sit side by side; a width the user dragged wins over it in applyWidths. Computed from
    // the sizes the CSS gives the images at the scale, so it follows every scale and ceiling change.
    var cells = Array.prototype.slice.call(table.querySelectorAll('td.graphics'));
    var img = table.querySelector('td.graphics img');
    if (!cells.length || !img) { graphicsWidth = COLUMN_MIN; return; }
    var ic = getComputedStyle(img), cc = getComputedStyle(cells[0]);
    var perImage = parseFloat(ic.borderLeftWidth) + parseFloat(ic.borderRightWidth) + parseFloat(ic.marginLeft) + parseFloat(ic.marginRight);
    var perCell = parseFloat(cc.paddingLeft) + parseFloat(cc.paddingRight) + parseFloat(cc.borderLeftWidth) + parseFloat(cc.borderRightWidth);
    var widest = 0;
    cells.forEach(function (cell) {
      var total = 0;
      Array.prototype.forEach.call(cell.querySelectorAll('img'), function (i) { total += imageSize(i)[0] + perImage; });
      widest = Math.max(widest, total);
    });
    graphicsWidth = Math.min(Math.max(COLUMN_MIN, Math.ceil(widest + perCell + WIDTH_SLACK)), COLUMN_MAX);
  }
  function applyScale() {
    table.style.setProperty('--scale', state.scale);
    table.style.setProperty('--floor', FLOOR);
    table.style.setProperty('--ceil', ceilingPx());
    table.style.setProperty('--nom', nominal() + 'px');
    var preset = '';
    Object.keys(SCALES).forEach(function (k) { if (SCALES[k] === state.scale) { preset = k; } });
    if (scaleSelect) { scaleSelect.value = preset; }           // '' selects the hidden "custom" entry
    if (scaleInput && parseFloat(scaleInput.value) !== state.scale) { scaleInput.value = state.scale; }
    var shown = state.ceiling === null ? '' : String(state.ceiling);   // an empty box is "none"
    if (ceilInput && ceilInput.value !== shown) { ceilInput.value = shown; }
    markCapped();
    measureGraphics();
    applyWidths();
  }

  // --- columns: visibility, order, widths ---
  function measureHeaders() {
    // The width each header title needs at the current text size: the text in the header's own font, plus
    // its padding (the right padding covers the grip), the sort mark and some slack. Measured, never saved,
    // so it follows the text size; a width the user dragged (state.widths) wins over it in applyWidths.
    var ctx = document.createElement('canvas').getContext('2d');
    var cs = getComputedStyle(heads[0]);
    ctx.font = cs.fontStyle + ' ' + cs.fontWeight + ' ' + cs.fontSize + ' ' + cs.fontFamily;
    var extra = parseFloat(cs.paddingLeft) + parseFloat(cs.paddingRight) + ctx.measureText(SORT_MARK).width + WIDTH_SLACK;
    measured = {};
    heads.forEach(function (th) { measured[th.dataset.col] = Math.ceil(ctx.measureText(th.dataset.col).width + extra); });
  }
  function kindWidth(col) {                                    // the per-kind minimum
    if (col === 'Graphics') { return graphicsWidth; }        // the widest row of units (measureGraphics)
    if (col === 'Pins' || col === 'Units') { return 220; }
    if (col === 'Description') { return 320; }
    if (col === 'Symbol') { return 160; }
    return 120;
  }
  function defaultWidth(col) { return Math.max(kindWidth(col), measured[col] || 0); }
  function applyWidths() {
    var total = 0;
    heads.forEach(function (th) {
      var w = +state.widths[th.dataset.col] > 0 ? +state.widths[th.dataset.col] : defaultWidth(th.dataset.col);
      th.style.width = w + 'px';
      if (!th.hidden) { total += w; }
    });
    table.style.width = total + 'px';
  }
  function applyOrder() {
    var current = heads.map(function (th) { return th.dataset.col; });
    var order = state.order.filter(function (c) { return current.indexOf(c) >= 0; });
    current.forEach(function (c) { if (order.indexOf(c) < 0) { order.push(c); } });
    state.order = order;
    if (order.join('\n') === current.join('\n')) { return; }
    [headRow, filterRow].concat(rows).forEach(function (r) {
      var cells = Array.prototype.slice.call(r.cells);
      order.forEach(function (c) { r.appendChild(cells[current.indexOf(c)]); });
    });
    readHeads();
  }
  function moveColumn(from, to) {
    var order = heads.map(function (th) { return th.dataset.col; });
    order.splice(order.indexOf(from), 1);
    order.splice(order.indexOf(to), 0, from);
    state.order = order;
    applyOrder();
    save();
  }
  function applyColumnFilter() {
    // A text filter shows the matching entries of every group, folded or not; groups without a match are hidden.
    var q = colfilter.value.toLowerCase();
    labels.forEach(function (l, i) { l.hidden = !!q && toggles[i].value.toLowerCase().indexOf(q) < 0; });
    groups.forEach(function (g) {
      var any = g.members.some(function (b) { return !b.parentNode.hidden; });
      g.box.hidden = !!q && !any;
      g.box.classList.toggle('closed', !q && state.closed.indexOf(g.name) >= 0);
      g.fold.textContent = g.box.classList.contains('closed') ? '▸' : '▾';
      g.fold.title = g.box.classList.contains('closed') ? 'Expand' : 'Collapse';
    });
  }
  function readToggles() {
    // Every way a column gets hidden ends here: an entry click or shift-click range, a group parent, All/None,
    // Show only Core, Show all, and the header menu's hide actions (through setToggles).
    state.hidden = toggles.filter(function (b) { return !b.checked; }).map(function (b) { return b.value; });
    var resort = pruneSort();
    save();
    applyColumns();
    if (resort) { applySort(); }
  }
  function setVisibleToggles(on) {
    toggles.forEach(function (b, i) { if (!labels[i].hidden) { b.checked = on; } });
    readToggles();
  }
  function setToggles(wanted) {                                // wanted(col) -> true, false or undefined (leave)
    toggles.forEach(function (b) { var on = wanted(b.value); if (on !== undefined) { b.checked = on; } });
    readToggles();
  }
  function showOnlyCore() { setToggles(function (c) { return groupOf[c] === 'Core'; }); }
  function showAll() { setToggles(function () { return true; }); }
  function hideColumn(col) { setToggles(function (c) { return c === col ? false : undefined; }); }
  function hideGroup(name) { setToggles(function (c) { return groupOf[c] === name ? false : undefined; }); }
  function updateGroups() {
    groups.forEach(function (g) {
      var n = g.members.filter(function (b) { return b.checked; }).length;
      g.parent.checked = n === g.members.length;
      g.parent.indeterminate = n > 0 && n < g.members.length;
      g.n.textContent = '(' + n + '/' + g.members.length + ')';
    });
  }
  function applyColumns() {
    var hidden = {};
    state.hidden.forEach(function (n) { hidden[n] = true; });
    heads.forEach(function (th, i) {
      var on = !hidden[th.dataset.col];
      th.hidden = !on;
      filterCells[i].hidden = !on;
      rows.forEach(function (r) { r.cells[i].hidden = !on; });
      toggleFor[th.dataset.col].checked = on;
    });
    updateGroups();
    applyWidths();
  }
  function toggleGroupFold(g) {
    var i = state.closed.indexOf(g.name);
    if (i >= 0) { state.closed.splice(i, 1); } else { state.closed.push(g.name); }
    save();
    applyColumnFilter();
  }

  // --- rows: filter and sort ---
  function applyFilter() {
    var q = search.value.toLowerCase();
    var active = [];
    heads.forEach(function (th, i) {
      var text = filters[i] && filters[i].value ? filters[i].value.toLowerCase() : '';
      var values = valueFilter[th.dataset.col] || null;
      if (text || values) { active.push({ i: i, text: text, values: values }); }
    });
    var shown = 0;
    rows.forEach(function (r) {
      var ok = !q || r.textContent.toLowerCase().indexOf(q) >= 0;
      for (var k = 0; ok && k < active.length; k++) {
        var cell = r.cells[active[k].i];
        if (active[k].text) { ok = cellText(cell).toLowerCase().indexOf(active[k].text) >= 0; }
        if (ok && active[k].values) { ok = !!active[k].values[cellValue(cell)]; }
      }
      r.hidden = !ok;
      if (ok) { shown++; }
    });
    count.textContent = shown + ' of ' + rows.length + ' symbols';
  }
  function pruneSort() {
    // A hidden (or unknown) column is no sort key: drop it, keeping the others' order. Showing the column
    // again does not restore it. True when a key went, so the caller re-sorts and redraws the ranks.
    var kept = state.sort.filter(function (k) { return colIndex(k.col) >= 0 && state.hidden.indexOf(k.col) < 0; });
    var changed = kept.length !== state.sort.length;
    state.sort = kept;
    return changed;
  }
  function applySort() {
    // state.sort lists the keys by priority: [{col, dir}, ...]. Every sorting header shows "<rank> ▲|▼".
    heads.forEach(function (th) { th.classList.remove('asc', 'desc'); th.removeAttribute('data-rank'); });
    pruneSort();
    var keys = state.sort.map(function (k, rank) {
      var i = colIndex(k.col);
      heads[i].classList.add(k.dir);
      heads[i].dataset.rank = rank + 1;
      return { i: i, dir: k.dir === 'desc' ? -1 : 1 };
    });
    var order = rows.slice();
    if (keys.length) {
      order.sort(function (a, b) {
        for (var k = 0; k < keys.length; k++) {
          var x = cellText(a.cells[keys[k].i]), y = cellText(b.cells[keys[k].i]);
          if (x === '' && y !== '') { return 1; }   // empty cells last either way, per key
          if (y === '' && x !== '') { return -1; }
          var c = x.localeCompare(y, undefined, { numeric: true, sensitivity: 'base' });
          if (c !== 0) { return c * keys[k].dir; }
        }
        return a.dataset.index - b.dataset.index;   // stable: original row order
      });
    }
    var body = table.tBodies[0];
    order.forEach(function (r) { body.appendChild(r); });
  }
  function cycleSort(col) {
    // not a key -> appended ascending; ascending -> descending; descending -> removed
    var i = -1;
    state.sort.forEach(function (k, n) { if (k.col === col) { i = n; } });
    if (i < 0) { state.sort.push({ col: col, dir: 'asc' }); }
    else if (state.sort[i].dir === 'asc') { state.sort[i] = { col: col, dir: 'desc' }; }
    else { state.sort.splice(i, 1); }
    save();
    applySort();
  }

  // --- value filter panel (Excel-style; a working filter, never saved) ---
  function markFunnels() {
    filterCells.forEach(function (c, i) {
      var b = c.querySelector('.funnel');
      if (!b) { return; }
      var on = !!valueFilter[heads[i].dataset.col];
      b.classList.toggle('active', on);
      b.textContent = on ? '▼' : '▽';
      b.title = on ? 'Value filter active (click to edit)' : 'Filter by value';
    });
  }
  function openPanel(i) {
    var col = heads[i].dataset.col;
    var counts = {}, keys = [];
    rows.forEach(function (r) {
      var v = cellValue(r.cells[i]);
      if (!Object.prototype.hasOwnProperty.call(counts, v)) { counts[v] = 0; keys.push(v); }
      counts[v]++;
    });
    keys.sort(function (a, b) {
      if (a === '') { return -1; }
      if (b === '') { return 1; }
      return a.localeCompare(b, undefined, { numeric: true, sensitivity: 'base' });
    });
    var selected = valueFilter[col];
    valueList.innerHTML = '';
    keys.forEach(function (k) {
      var label = document.createElement('label');
      var box = document.createElement('input');
      box.type = 'checkbox';
      box.value = k;
      box.checked = !selected || !!selected[k];
      label.title = k === '' ? '(blank)' : k;
      label.appendChild(box);
      label.appendChild(document.createTextNode(' ' + label.title + ' '));
      var n = document.createElement('span');
      n.className = 'n';
      n.textContent = '(' + counts[k] + ')';
      label.appendChild(n);
      valueList.appendChild(label);
    });
    valueSearch.value = '';
    panelCol = col;
    panel.hidden = false;
    var rect = filterCells[i].querySelector('.funnel').getBoundingClientRect();
    var left = rect.left + window.pageXOffset;
    var maxLeft = window.pageXOffset + document.documentElement.clientWidth - panel.offsetWidth - 8;
    panel.style.left = Math.max(0, Math.min(left, maxLeft)) + 'px';
    panel.style.top = (rect.bottom + window.pageYOffset + 2) + 'px';
    valueSearch.focus();
  }
  function closePanel() { panel.hidden = true; panelCol = null; }
  function readPanel() {
    var boxes = Array.prototype.slice.call(valueList.querySelectorAll('input'));
    if (boxes.every(function (b) { return b.checked; })) {
      delete valueFilter[panelCol];
    } else {
      var m = {};
      boxes.forEach(function (b) { if (b.checked) { m[b.value] = true; } });
      valueFilter[panelCol] = m;
    }
    markFunnels();
    applyFilter();
  }
  function applyValueSearch() {
    var q = valueSearch.value.toLowerCase();
    Array.prototype.slice.call(valueList.children).forEach(function (l) {
      l.hidden = !!q && l.title.toLowerCase().indexOf(q) < 0;
    });
  }
  function setPanelBoxes(on) {
    Array.prototype.slice.call(valueList.children).forEach(function (l) {
      if (!l.hidden) { l.querySelector('input').checked = on; }
    });
    readPanel();
  }

  // --- header events: sort, resize, reorder ---
  headRow.addEventListener('click', function (e) {
    var el = elementOf(e), th = el.closest('th');
    if (!th || resizing || el.classList.contains('grip')) { return; }
    cycleSort(th.dataset.col);
  });
  // --- header context menu: hide this column, hide its group, show only Core, show all ---
  function closeMenu() { menu.hidden = true; menuCol = null; }
  headRow.addEventListener('contextmenu', function (e) {
    var th = elementOf(e).closest('th');
    if (!th) { return; }
    e.preventDefault();
    closePanel();
    menuCol = th.dataset.col;
    menu.querySelector('[data-act=hide]').textContent = 'Hide this column (' + menuCol + ')';
    menu.querySelector('[data-act=hidegroup]').textContent = 'Hide all ' + groupOf[menuCol] + ' columns';
    menu.hidden = false;
    var maxLeft = window.pageXOffset + document.documentElement.clientWidth - menu.offsetWidth - 8;
    menu.style.left = Math.max(0, Math.min(e.pageX, maxLeft)) + 'px';
    menu.style.top = e.pageY + 'px';
  });
  menu.addEventListener('click', function (e) {
    var act = elementOf(e).closest('button') ? elementOf(e).closest('button').dataset.act : null;
    var col = menuCol;
    closeMenu();
    if (act === 'hide') { hideColumn(col); }
    else if (act === 'hidegroup') { hideGroup(groupOf[col]); }
    else if (act === 'core') { showOnlyCore(); }
    else if (act === 'all') { showAll(); }
  });
  headRow.addEventListener('mousedown', function (e) {
    var el = elementOf(e);
    if (!el.classList.contains('grip')) { return; }
    e.preventDefault();
    e.stopPropagation();
    var th = el.parentNode, startX = e.clientX, startW = th.getBoundingClientRect().width;
    resizing = true;
    function move(ev) {
      state.widths[th.dataset.col] = Math.max(40, Math.round(startW + ev.clientX - startX));
      applyWidths();
    }
    function up() {
      document.removeEventListener('mousemove', move);
      document.removeEventListener('mouseup', up);
      save();
      setTimeout(function () { resizing = false; }, 0);   // swallow the click that follows the mouseup
    }
    document.addEventListener('mousemove', move);
    document.addEventListener('mouseup', up);
  });
  headRow.addEventListener('dragstart', function (e) {
    var th = elementOf(e).closest('th');
    if (!th || resizing) { e.preventDefault(); return; }
    dragCol = th.dataset.col;
    th.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', dragCol);
  });
  headRow.addEventListener('dragover', function (e) {
    var th = elementOf(e).closest('th');
    if (!th || !dragCol || th.dataset.col === dragCol) { return; }
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    th.classList.add('dragover');
  });
  headRow.addEventListener('dragleave', function (e) {
    var th = elementOf(e).closest('th');
    if (th) { th.classList.remove('dragover'); }
  });
  headRow.addEventListener('drop', function (e) {
    var th = elementOf(e).closest('th');
    if (!th || !dragCol) { return; }
    e.preventDefault();
    th.classList.remove('dragover');
    if (th.dataset.col !== dragCol) { moveColumn(dragCol, th.dataset.col); }
  });
  headRow.addEventListener('dragend', function () {
    heads.forEach(function (th) { th.classList.remove('dragging', 'dragover'); });
    dragCol = null;
  });

  // --- filter row and panel events ---
  filterRow.addEventListener('click', function (e) {
    var el = elementOf(e);
    if (!el.classList.contains('funnel')) { return; }
    var i = filterCells.indexOf(el.closest('th'));
    if (panelCol === heads[i].dataset.col) { closePanel(); } else { openPanel(i); }
  });
  filters.forEach(function (f) { if (f) { f.addEventListener('input', applyFilter); } });
  valueList.addEventListener('change', readPanel);
  valueSearch.addEventListener('input', applyValueSearch);
  document.getElementById('valall').addEventListener('click', function () { setPanelBoxes(true); });
  document.getElementById('valclear').addEventListener('click', function () { setPanelBoxes(false); });
  document.addEventListener('mousedown', function (e) {
    var el = elementOf(e);
    if (!panel.hidden && !panel.contains(el) && !el.classList.contains('funnel')) { closePanel(); }
    if (!menu.hidden && !menu.contains(el)) { closeMenu(); }
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { closePanel(); closeMenu(); }
  });

  // --- Columns control: entries (shift-click selects a range within the group), group parents, folds, bulk ---
  groups.forEach(function (g) {
    g.members.forEach(function (box, n) {
      box.addEventListener('click', function (e) {
        var on = box.checked;                                  // already toggled by the click
        if (e.shiftKey && g.last >= 0 && g.last !== n) {
          var lo = Math.min(g.last, n), hi = Math.max(g.last, n);
          for (var k = lo; k <= hi; k++) { if (!g.members[k].parentNode.hidden) { g.members[k].checked = on; } }
        }
        g.last = n;
        readToggles();
      });
    });
    g.parent.addEventListener('click', function () {
      var on = g.parent.checked;                               // an indeterminate parent becomes checked
      g.members.forEach(function (b) { b.checked = on; });
      readToggles();
    });
    g.fold.addEventListener('click', function () { toggleGroupFold(g); });
  });
  search.addEventListener('input', applyFilter);
  colfilter.addEventListener('input', applyColumnFilter);
  document.getElementById('colall').addEventListener('click', function () { setVisibleToggles(true); });
  document.getElementById('colnone').addEventListener('click', function () { setVisibleToggles(false); });
  document.getElementById('colcore').addEventListener('click', showOnlyCore);
  document.getElementById('colshowall').addEventListener('click', showAll);
  if (scaleSelect) {
    scaleSelect.addEventListener('change', function () {
      if (SCALES[scaleSelect.value]) { state.scale = SCALES[scaleSelect.value]; save(); applyScale(); }
    });
    scaleInput.addEventListener('input', function () {
      var n = parseFloat(scaleInput.value);
      if (isScale(n)) { state.scale = n; save(); applyScale(); }
    });
    ceilInput.addEventListener('input', function () {
      var n = parseFloat(ceilInput.value);
      if (ceilInput.value === '' || n === 0) { state.ceiling = null; save(); applyScale(); }   // empty or 0: no ceiling
      else if (isCeiling(n)) { state.ceiling = n; save(); applyScale(); }
    });
  }
  fontSelect.addEventListener('change', function () {
    if (FONTS[fontSelect.value]) { state.font = FONTS[fontSelect.value]; save(); applyFont(); }
  });
  fontInput.addEventListener('input', function () {
    var n = parseFloat(fontInput.value);
    if (isFont(n)) { state.font = n; save(); applyFont(); }
  });
  document.getElementById('reset').addEventListener('click', function () {
    search.value = '';
    filters.forEach(function (f) { if (f) { f.value = ''; } });
    colfilter.value = '';
    valueFilter = {};
    closePanel();
    closeMenu();
    state = defaults();
    try { localStorage.removeItem(KEY); } catch (e) { /* ignore */ }
    applyAll();
  });

  function applyAll() {
    applyOrder();
    applyFont();                                               // first: it measures the header titles the widths need
    applyColumns();
    applyColumnFilter();
    applyScale();
    applySort();
    markFunnels();
    applyFilter();
  }
  load();
  applyAll();
})();
""".replace("SCALE_PRESETS", "{ " + ", ".join(f"{s}: {n}" for s, n in IMG_SCALES.items()) + " }") \
   .replace("SCALE_RANGE[0]", str(IMG_SCALE_RANGE[0])).replace("SCALE_RANGE[1]", str(IMG_SCALE_RANGE[1])) \
   .replace("SCALE_DEFAULT_PX", str(IMG_SCALE_DEFAULT)) \
   .replace("CEIL_RANGE[0]", str(IMG_CEILING_RANGE[0])).replace("CEIL_RANGE[1]", str(IMG_CEILING_RANGE[1])) \
   .replace("CEIL_DEFAULT_JS", "null" if IMG_CEILING_DEFAULT is None else str(IMG_CEILING_DEFAULT)) \
   .replace("UNLIMITED_PX", str(IMG_UNLIMITED_PX)).replace("FLOOR_PX", str(IMG_FLOOR)) \
   .replace("NOMINAL_MM_VALUE", str(IMG_NOMINAL_MM)) \
   .replace("COLUMN_MIN_PX", str(IMG_COLUMN_MIN)).replace("COLUMN_MAX_PX", str(IMG_COLUMN_MAX))

# The tabs and the conventions view: a tab is chosen by the URL hash (#conventions; anything else is the symbols
# table), so a link opens either; the conventions filter hides whole kind groups (one tbody each).
TAB_SCRIPT = r"""
(function () {
  'use strict';
  var tabs = Array.prototype.slice.call(document.querySelectorAll('nav.tabs button'));
  function show(name) {
    tabs.forEach(function (b) {
      var on = b.dataset.tab === name;
      b.setAttribute('aria-selected', on ? 'true' : 'false');
      document.getElementById('tab-' + b.dataset.tab).hidden = !on;
    });
  }
  function fromHash() { show(location.hash === '#conventions' ? 'conventions' : 'symbols'); }
  tabs.forEach(function (b) {
    b.addEventListener('click', function () { history.replaceState(null, '', '#' + b.dataset.tab); show(b.dataset.tab); });
  });
  window.addEventListener('hashchange', fromHash);
  fromHash();

  var table = document.getElementById('conventions');
  var groups = Array.prototype.slice.call(table.tBodies);
  var search = document.getElementById('convsearch'), onlyFlagged = document.getElementById('convflagged');
  var count = document.getElementById('convcount');
  function apply() {
    var q = search.value.toLowerCase(), shown = 0;
    groups.forEach(function (g) {
      var ok = (!onlyFlagged.checked || g.dataset.flagged !== '0') && (!q || g.textContent.toLowerCase().indexOf(q) >= 0);
      g.hidden = !ok;
      if (ok) { shown++; }
    });
    count.textContent = shown + ' of ' + groups.length + ' kinds';
  }
  search.addEventListener('input', apply);
  onlyFlagged.addEventListener('change', apply);
  apply();
})();
"""


def conventions_html(kinds: list[KindRow]) -> str:
    """The conventions table: one tbody per kind (its th spans the kind's rows), one tr per symbol."""
    def td(c: Cell) -> str:
        if not c.flags:
            return f"<td>{esc(c.text)}</td>"
        why = "".join(f'<span class="why">{esc(f)}</span>' for f in c.flags)
        return f'<td class="flag" title="{esc("; ".join(c.flags))}">{esc(c.text)}{why}</td>'

    def lint(s: Symbol) -> str:
        if not s.lint:
            return "<td></td>"
        return '<td><ul class="lint">' + "".join(f'<li class="lint-{esc(sev)}">{esc(sev)}: {esc(m)}</li>'
                                                for sev, m in s.lint) + "</ul></td>"

    head = "".join(f"<th>{esc(c)}</th>" for c in ("Kind", "Symbol") + CONVENTION_COLUMNS + ("Lint",))
    bodies = []
    for kind in kinds:
        rows = []
        for i, (s, cells) in enumerate(zip(kind.symbols, kind.cells)):
            lead = (f'<th class="kind" rowspan="{len(kind.symbols)}">{esc(kind.label)}'
                    f'<span class="n">{len(kind.symbols)} symbol{"s" if len(kind.symbols) != 1 else ""}, '
                    f'{kind.flagged} flagged</span></th>') if i == 0 else ""
            rows.append(f'<tr>{lead}<td class="ref">{esc(s.library)}:{esc(s.name)}</td>'
                        + "".join(td(cells[c]) for c in CONVENTION_COLUMNS) + lint(s) + "</tr>")
        bodies.append(f'<tbody data-flagged="{kind.flagged}">' + "".join(rows) + "</tbody>")
    return f'<table id="conventions"><thead><tr>{head}</tr></thead>{"".join(bodies)}</table>'


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def pins_cell(sym: Symbol) -> str:
    if not sym.pins:
        return "<td></td>"
    items = []
    for name, number, etype in sym.pins:
        cap = sym.fields.get("Pin." + pin_base(name))
        items.append(f'<li>{esc(name)} <span class="num">({esc(number)})</span> <span class="etype">{esc(etype)}</span>'
                     + (f' <span class="cap">= {esc(cap)}</span>' if cap else "") + "</li>")
    return '<td><ul class="pins">' + "".join(items) + "</ul></td>"


def units_cell(sym: Symbol) -> str:
    if not sym.units:
        return "<td></td>"
    items = []
    for unit in sorted(sym.units):
        label = "common" if unit == 0 else f"unit {unit}"
        pins = ", ".join(sym.units[unit]) or "(no pins)"
        items.append(f"<li>{label}: {esc(pins)}</li>")
    n = len([u for u in sym.units if u != 0])
    return f'<td data-sort="{n}"><ul class="units">' + "".join(items) + "</ul></td>"


def graphics_cell(sym: Symbol) -> str:
    """One img per unit, side by side (they wrap only in a narrowed column). An img of known size carries it as
    `--w` and `--h` (mm, 2 decimals) with the class `mm`, which the CSS draws at the scale; an image of unknown
    size has neither and is drawn in the nominal square."""
    def img(p: str) -> str:
        size = sym.sizes.get(p)
        sized = f' class="mm" style="--w:{size[0]:.2f};--h:{size[1]:.2f}"' if size else ""
        return f'<img src="{esc(p)}" alt="{esc(Path(p).stem)}" title="{esc(p)}" loading="lazy"{sized}>'
    return f'<td class="graphics" data-sort="{len(sym.graphics)}">{"".join(img(p) for p in sym.graphics)}</td>'


def field_cell(sym: Symbol, name: str) -> str:
    value = sym.fields.get(name)
    if value is None:
        return "<td></td>"
    cls = "wrap" if name in ("Description", "ki_keywords") or len(value) > 40 else ""
    if not value:
        cls = (cls + " empty").strip()
    return f'<td class="{cls}">{esc(value)}</td>' if cls else f"<td>{esc(value)}</td>"


def column_count(symbols: list[Symbol], column: str) -> int:
    """How many symbols fill the column: a non-empty field value, an image, a pin or a unit."""
    if column in ("Library", "Symbol"):
        return len(symbols)
    filled = {"Extends": lambda s: s.extends, "Graphics": lambda s: s.graphics,
              "Pins": lambda s: s.pins, "Units": lambda s: s.units}.get(column, lambda s: s.fields.get(column))
    return sum(1 for s in symbols if filled(s))


def column_groups_html(columns: list[str], shown: set[str], counts: dict[str, int]) -> list[str]:
    """One .colgroup block per non-empty group in GROUPS order: a fold button, a tri-state parent checkbox
    (the script sets its state), the shown/total count and one checkbox per member column."""
    blocks = []
    for group in GROUPS:
        members = [c for c in columns if column_group(c) == group]
        if not members:
            continue
        closed = " closed" if group in DEFAULT_CLOSED_GROUPS else ""
        fold = "&#9656;" if closed else "&#9662;"
        n = sum(1 for c in members if c in shown)
        labels = "".join(f'<label><input type="checkbox" value="{esc(c)}"{" checked" if c in shown else ""}> '
                         f'{esc(c)} ({counts[c]})</label>' for c in members)
        blocks.append(f'<div class="colgroup{closed}" data-group="{esc(group)}">'
                      f'<div class="grouphead"><button type="button" class="fold" title="{"Expand" if closed else "Collapse"}" '
                      f'aria-label="fold {esc(group)}">{fold}</button>'
                      f'<label><input type="checkbox" class="grouptoggle" aria-label="show all {esc(group)} columns"> '
                      f'{esc(group)} <span class="n">({n}/{len(members)})</span></label></div>'
                      f'<div class="members">{labels}</div></div>')
    return blocks


def build_page(symbols: list[Symbol], title: str, libraries: list[Path], graphics: bool) -> tuple[str, list[str]]:
    """(html, column names)."""
    props = property_columns({n for s in symbols for n in s.fields})
    head = [c for c in FIXED_HEAD if c != "Extends" or any(s.extends for s in symbols)]
    lead = [c for c in LEAD_FIELDS if c in props]
    desc = ["Description"] if "Description" in props else []
    rest = [p for p in props if p not in lead and p != "Description"]
    columns = head + lead + (["Graphics"] if graphics else []) + desc + ["Pins", "Units"] + rest
    unfilterable = {"Graphics"}
    counts = {c: column_count(symbols, c) for c in columns}
    # The rest of the fields start hidden when no symbol fills them; the Columns control shows them.
    shown = {c for c in columns if c in ALWAYS_SHOWN or counts[c] > 0}

    header = "".join(f'<th class="sortable" draggable="true" data-col="{esc(c)}" data-group="{esc(column_group(c))}">{esc(c)}'
                     f'<span class="grip" title="Drag to resize"></span></th>' for c in columns)
    filter_row = "".join("<th></th>" if c in unfilterable else
                         f'<th><div class="fwrap"><input type="search" placeholder="filter" aria-label="filter {esc(c)}">'
                         f'<button type="button" class="funnel" title="Filter by value" aria-label="filter {esc(c)} by value">'
                         f'&#9661;</button></div></th>'
                         for c in columns)
    toggles = "".join(column_groups_html(columns, shown, counts))
    size_control = ('<label>Graphics <select id="imgsize" aria-label="graphics scale preset">'
                    + "".join(f'<option value="{s}"{" selected" if IMG_SCALES[s] == IMG_SCALE_DEFAULT else ""}>'
                              f'{s} ({IMG_SCALES[s]:g} px/mm)</option>' for s in IMG_SCALES)
                    + '<option value="" hidden>custom</option></select></label> '
                    f'<label><input type="number" id="scalepx" min="{IMG_SCALE_RANGE[0]}" max="{IMG_SCALE_RANGE[1]}" '
                    f'step="{IMG_SCALE_RANGE[2]}" value="{IMG_SCALE_DEFAULT}" aria-label="graphics scale in px per mm"> px/mm</label> '
                    f'<label><input type="number" id="maxpx" min="{IMG_CEILING_RANGE[0]}" max="{IMG_CEILING_RANGE[1]}" '
                    f'step="{IMG_CEILING_RANGE[2]}" value="{"" if IMG_CEILING_DEFAULT is None else IMG_CEILING_DEFAULT}" '
                    'placeholder="none" aria-label="ceiling on an image\'s longer side in px (empty for none)"> max px</label>') if graphics else ""
    font_control = ('<label>Text <select id="fontsize" aria-label="text size">'
                    + "".join(f'<option value="{s}"{" selected" if s == "S" else ""}>{s}</option>' for s in ("S", "M", "L"))
                    + '<option value="" hidden>custom</option></select></label> '
                    '<label><input type="number" id="fontpt" min="4" max="72" step="0.5" value="10" '
                    'aria-label="text size in points"> pt</label>')

    def cell(s: Symbol, c: str) -> str:
        if c == "Library":
            return f"<td>{esc(s.library)}</td>"
        if c == "Symbol":
            return f'<td class="symbol">{esc(s.name)}</td>'
        if c == "Extends":
            return f"<td>{esc(s.extends or '')}</td>"
        if c == "Graphics":
            return graphics_cell(s)
        if c == "Pins":
            return pins_cell(s)
        if c == "Units":
            return units_cell(s)
        return field_cell(s, c)

    rows = ["<tr>" + "".join(cell(s, c) for c in columns) + "</tr>" for s in symbols]
    kinds = convention_kinds(symbols)

    sources = ", ".join(esc(p.name) for p in libraries)
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<style>{STYLE}</style>
</head>
<body>
<h1>{esc(title)}</h1>
<nav class="tabs" role="tablist"><button type="button" role="tab" data-tab="symbols" aria-selected="true">Symbols</button>
<button type="button" role="tab" data-tab="conventions" aria-selected="false">Conventions ({sum(1 for k in kinds if k.flagged)} of {len(kinds)} kinds flagged)</button></nav>
<section id="tab-symbols">
<p class="meta">{len(symbols)} symbols from {sources}. Click a header to add it to the sort as the last key (again to reverse
it, a third time to remove it); sorting headers show their priority and direction. Drag a header onto another to reorder,
drag its right edge to resize; right-click a header to hide it or its group. The funnel in a filter cell picks values.
Pins read name (number) electrical type = Pin.&lt;base&gt; value. A middle dot marks a field that is present but empty.</p>
<div class="controls">
<input type="search" id="search" placeholder="search all columns" aria-label="search all columns">
<details class="columns"><summary>Columns</summary><div id="columns">
<p class="colbulk"><button type="button" id="colcore">Show only Core</button> <button type="button" id="colshowall">Show all</button></p>
<p class="colctl"><input type="search" id="colfilter" placeholder="filter columns" aria-label="filter columns">
<button type="button" id="colall">All</button> <button type="button" id="colnone">None</button> <span class="n">(filtered entries)</span></p>
{toggles}</div></details>
{size_control}
{font_control}
<button type="button" id="reset">Reset view</button>
<span id="count"></span>
</div>
<table id="symbols">
<thead>
<tr class="headers">{header}</tr>
<tr class="filters">{filter_row}</tr>
</thead>
<tbody>
{chr(10).join(rows)}
</tbody>
</table>
</section>
<section id="tab-conventions" hidden>
<p class="meta">One group per kind (Role, Appliance, Kind, Style, IC as the symbols carry them), one row per symbol. A flagged
cell (&#9873;) says why. G rules: the symbols of a kind disagree (G1); Name is missing while another kind of the same
Role carries it (G2); another field is missing while its family carries it, settings and superseded fields excepted
(G3); a Pin.* names no pin (G4). Token rulings of 2026-10-28: a PANEL lever states Control.&lt;pin&gt; or
Indication.&lt;pin&gt; per function pin (R1); a model board lamp states one Indication (R2); an APPLIANCE carries no tokens
(R3); Invert on a PANEL symbol is superseded (R4); a PANEL lamp pin states binary (R5); a retiring kind is not flagged
(R6). Pins read base=drive; Units read
unit [drive words]: pin bases. A dash is an absent field.</p>
<div class="controls">
<input type="search" id="convsearch" placeholder="search kinds" aria-label="search kinds">
<label><input type="checkbox" id="convflagged"> Only flagged kinds</label>
<span id="convcount"></span>
</div>
{conventions_html(kinds)}
</section>
<div id="valuepanel" hidden>
<input type="search" id="valuesearch" placeholder="search values" aria-label="search values">
<p><button type="button" id="valall">Select all</button> <button type="button" id="valclear">Clear</button></p>
<div id="valuelist"></div>
</div>
<div id="colmenu" role="menu" hidden>
<button type="button" data-act="hide">Hide this column</button>
<button type="button" data-act="hidegroup">Hide all columns of its group</button>
<button type="button" data-act="core">Show only Core</button>
<button type="button" data-act="all">Show all</button>
</div>
<script>{SCRIPT}</script>
<script>{TAB_SCRIPT}</script>
</body>
</html>
"""
    return page, columns


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("libraries", nargs="+", type=Path, metavar="LIB.kicad_sym")
    ap.add_argument("--out", type=Path, default=None, help="output directory (default: <first library dir>/production/overview)")
    ap.add_argument("--title", default="KiCad symbol library overview")
    ap.add_argument("--no-render", action="store_true", help="skip kicad-cli; omit the graphics column")
    a = ap.parse_args(argv)

    for lib in a.libraries:
        if not lib.is_file():
            ap.error(f"not a file: {lib}")
    out = a.out or a.libraries[0].resolve().parent / "production" / "overview"
    out.mkdir(parents=True, exist_ok=True)

    kicad_cli = None
    if not a.no_render:
        kicad_cli = find_kicad_cli()
        if not kicad_cli:
            ap.error("kicad-cli not found (set KICAD_CLI, add it to PATH, or pass --no-render)")

    symbols: list[Symbol] = []
    for lib in a.libraries:
        loaded = load_library(lib)
        if kicad_cli:
            svg_dir = out / f"svg-{lib.stem}"
            files = render(kicad_cli, lib, svg_dir)
            for s in loaded:
                s.graphics = [f"{svg_dir.name}/{f}" for f in files.get(s.name, [])]
                s.sizes = {p: size for p in s.graphics if (size := svg_size_mm(out / p))}
        symbols += loaded

    page, _ = build_page(symbols, a.title, a.libraries, graphics=kicad_cli is not None)
    page_file = out / PAGE_NAME
    page_file.write_text(page)
    print(f"{page_file}: {len(symbols)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
