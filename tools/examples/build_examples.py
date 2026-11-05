#!/usr/bin/env python3
"""Draft the Railroad `Examples` KiCad project: one page per library pattern, written by script for the owner to tidy.

Each page is one A3 sheet in three bands, TRACKPLAN, FIELD and OFFICE, holding its own `Interlocking` declaration
and `House`. The patterns are the ones already drawn on the SPCoast Gilroy Caltrain sheets (the newest hand-drawn
sheets, on the new Signals symbols): a device and its driver meet by coincident pins, the drivers' IOBus pins join a
vertical wire to the CMRInet node, a desk column's lamps and levers meet the MAX7313 driver's pins by position. What
SPCoast keeps on its South-cTc sheet (the Railroad, the OfficeUnit and its processor, the field processor, the
CMRInet transport and encoding, the AAR code line encoding) sits once on the root sheet and reaches the pages through
global labels, as South-cTc's own PanelIO and AAR labels do. Symbols are embedded fresh from the libraries; every
placed property keeps the library's position and visibility, so a page looks like one placed by hand from the
library. UUIDs are derived from names (a rebuild of unchanged sources writes identical files). Every guess, omission
and empty band is a visible `TODO:` text on the page and in the page's sidecar `.md`.

    uv run python tools/examples/build_examples.py            build Examples/, then check (ERC, netlist, nets)
    uv run python tools/examples/build_examples.py --check    check only

Writes only under ~/Dropbox/KiCad/Railroad/Examples/ (override with EXAMPLES_OUT). Derived files go in
Examples/production/ (gitignored). The netlist it checks is exported fresh into a temporary directory
(EXAMPLES_SCRATCH, else the system one) and deleted.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import uuid
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kicad_services.netlist_reader import NetlistReader  # noqa: E402
from kicad_services.sch_text import blocks  # noqa: E402
from kicad_services.symbol_library_reader import SymbolLibraryReader  # noqa: E402

RAILROAD = Path.home() / "Dropbox/KiCad/Railroad"
LIBDIR = RAILROAD / "symbols"
SPCOAST = RAILROAD / "SPCoast"
OUT = Path(os.environ.get("EXAMPLES_OUT", RAILROAD / "Examples"))
PROJECT = "Examples"
KICAD_CLI = os.environ.get("KICAD_CLI", "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli")
NS = uuid.UUID("7e3a9c54-2b1d-4f0e-8a6b-1d2e3f405060")  # Examples namespace
G = 1.27  # the 50 mil grid; every anchor below is in grid units


def uid(key: str) -> str:
    return str(uuid.uuid5(NS, key))


def mm(v: float) -> str:
    s = f"{round(v, 4):.4f}".rstrip("0").rstrip(".")
    return s if s not in ("", "-0") else "0"


# ------------------------------------------------------------------ libraries

_lib_text: dict[str, str] = {}
_lib_model: dict[str, dict] = {}


def lib_text(lib: str) -> str:
    if lib not in _lib_text:
        _lib_text[lib] = (LIBDIR / f"{lib}.kicad_sym").read_text()
    return _lib_text[lib]


def lib_symbol_text(lib: str, name: str) -> str:
    """The `(symbol "name" ...)` block of a library symbol, as the library file holds it (depth 1)."""
    t = lib_text(lib)
    for s, e in blocks(t, "symbol", 1):
        if t[s:e].startswith(f'(symbol "{name}"'):
            return t[s:e]
    raise KeyError(f"{lib}:{name}")


def lib_pins(lib: str, name: str):
    if lib not in _lib_model:
        _lib_model[lib] = SymbolLibraryReader().read(LIBDIR / f"{lib}.kicad_sym").symbols
    return list(_lib_model[lib][name].pins)


def lib_units(lib: str, name: str) -> list[int]:
    """The unit numbers of a library symbol (1..n); a single-unit symbol gives [1]."""
    units = sorted({int(u) for u in re.findall(r'\(symbol "' + re.escape(name) + r'_(\d+)_\d+"', lib_symbol_text(lib, name))} - {0})
    return units or [1]


def embedded(lib: str, name: str) -> str:
    """The library symbol as a sheet's lib_symbols entry: qualified name (units keep their bare names), one tab deeper."""
    t = lib_symbol_text(lib, name).replace(f'(symbol "{name}"', f'(symbol "{lib}:{name}"', 1)
    return "\n".join("\t" + ln if i else ln for i, ln in enumerate(t.split("\n")))


# ------------------------------------------------------------------ page model

@dataclass
class Placed:
    ref: str
    lib: str
    name: str
    x: float          # grid units
    y: float
    rot: int = 0
    mirror: str = ""
    values: dict = field(default_factory=dict)   # property overrides

    @property
    def lib_id(self) -> str:
        return f"{self.lib}:{self.name}"

    def pin(self, number_or_name: str) -> tuple[float, float]:
        """Page position (grid units) of a pin's connection point: lib coords mirrored, rotated, y flipped."""
        for p in lib_pins(self.lib, self.name):
            if number_or_name in (p.number, p.name):
                px, py = p.x / G, p.y / G
                if self.mirror == "x":
                    py = -py
                if self.mirror == "y":
                    px = -px
                a = math.radians(self.rot)
                rx = px * math.cos(a) - py * math.sin(a)
                ry = px * math.sin(a) + py * math.cos(a)
                return round(self.x + rx, 4), round(self.y - ry, 4)
        raise KeyError(f"{self.lib_id} pin {number_or_name}")


@dataclass
class Page:
    file: str
    title: str
    cp_name: str
    number: int
    paper: str = "A3"
    symbols: list[Placed] = field(default_factory=list)
    wires: list[tuple[tuple[float, float], tuple[float, float], float]] = field(default_factory=list)
    junctions: list[tuple[float, float]] = field(default_factory=list)
    no_connects: list[tuple[float, float]] = field(default_factory=list)
    glabels: list[tuple[str, float, float, int]] = field(default_factory=list)      # name, x, y, rotation
    texts: list[tuple[str, float, float, float, bool]] = field(default_factory=list)   # text, x, y, size mm, bold
    todos: list[str] = field(default_factory=list)
    intent: str = ""
    facts: list[tuple[str, str]] = field(default_factory=list)
    expect: list[set[tuple[str, str]]] = field(default_factory=list)   # nets that must exist: {(ref, pin number)}
    _n: dict = field(default_factory=dict)

    @property
    def uuid(self) -> str:
        return uid("root") if self.number == 1 else uid(f"sheet/{self.file}")

    @property
    def path(self) -> str:
        return f"/{uid('root')}" if self.number == 1 else f"/{uid('root')}/{self.uuid}"

    def add(self, lib: str, name: str, x: float, y: float, rot: int = 0, mirror: str = "", **values) -> Placed:
        prefix = re.search(r'\(property "Reference" "([^"]*)"', lib_symbol_text(lib, name)).group(1)
        self._n[prefix] = self._n.get(prefix, 0) + 1
        p = Placed(f"{prefix}{self.number * 100 + self._n[prefix]}", lib, name, x, y, rot, mirror, values)
        self.symbols.append(p)
        return p

    def wire(self, a, b, width: float = 0):
        self.wires.append((a, b, width))

    def track(self, a, b):
        self.wire(a, b, 0.4064)

    def bus(self, points: list[tuple[float, float]], tail: tuple[float, float] | None = None):
        """A vertical wire through pins at one x (sorted by y), then an L to `tail`; junctions at interior pins."""
        pts = sorted(set(points), key=lambda p: p[1])
        for a, b in zip(pts, pts[1:]):
            self.wire(a, b)
        for p in pts[1:-1]:
            self.junctions.append(p)
        if tail:
            top = pts[0]
            if tail[1] != top[1]:
                self.wire(top, (top[0], tail[1]))
                self.wire((top[0], tail[1]), tail)
            else:
                self.wire(top, tail)
            if len(pts) > 1:
                self.junctions.append(top)

    def glabel(self, name: str, at: tuple[float, float], dx: int = 0, rot: int = 0):
        """A global label `dx` units from a pin on a short wire, or at the pin itself (South-cTc joins its sheets so)."""
        end = (at[0] + dx, at[1])
        if dx:
            self.wire(at, end)
        self.glabels.append((name, end[0], end[1], rot))

    def heading(self, text: str, x: float, y: float):
        self.texts.append((text, x, y, 5.08, True))

    def todo(self, text: str, x: float, y: float):
        self.todos.append(text)
        self.texts.append((f"TODO: {text}", x, y, 1.27, False))

    def note(self, text: str, x: float, y: float):
        self.texts.append((text, x, y, 1.27, False))

    def must(self, *pins: tuple[Placed, str]):
        self.expect.append({(p.ref, number_of(p, n)) for p, n in pins})


def number_of(p: Placed, number_or_name: str) -> str:
    for pin in lib_pins(p.lib, p.name):
        if number_or_name in (pin.number, pin.name):
            return pin.number
    raise KeyError(number_or_name)


# ------------------------------------------------------------------ s-expression writers

def title_block(title: str) -> str:
    lines = [f'(title_block\n\t\t(title "{title}")', '(date "2026.11")', '(rev "0.1")', '(company "SPCoast Railroad")',
             '(comment 1 "JPlocher")', '(comment 2 "Railroad symbol library example")', '(comment 3 "Examples")',
             '(comment 4 "drafted by tools/examples/build_examples.py")']
    return "\n\t\t".join(lines) + "\n\t)"


def esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def property_blocks(p: Placed) -> str:
    """Every library property, at its library position relative to the placement, with the overrides applied."""
    t = lib_symbol_text(p.lib, p.name)
    out = []
    seen = set()
    for s, e in blocks(t, "property", 2):
        b = t[s:e]
        m = re.match(r'\(property "((?:[^"\\]|\\.)*)" "((?:[^"\\]|\\.)*)"', b)
        key = m.group(1)
        seen.add(key)
        value = esc(p.values[key]) if key in p.values else (p.ref if key == "Reference" else m.group(2))
        b = b[:m.start(2)] + value + b[m.end(2):]
        b = re.sub(r"\n\t\t\t\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)",
                   lambda a: f"\n\t\t\t(at {mm(p.x * G + float(a.group(1)))} {mm(p.y * G - float(a.group(2)))} {a.group(3)})",
                   b, count=1)
        out.append(b)
    for key, value in p.values.items():
        if key not in seen:   # a field the library lacks: hidden at the anchor
            out.append(f'(property "{key}" "{esc(value)}"\n\t\t\t(at {mm(p.x * G)} {mm(p.y * G)} 0)\n\t\t\t(show_name no)'
                       f'\n\t\t\t(do_not_autoplace no)\n\t\t\t(hide yes)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)'
                       f'\n\t\t\t\t)\n\t\t\t)\n\t\t)')
    return "\n\t\t".join(out)


def symbol_block(p: Placed, page: Page) -> str:
    """One placed block per unit, all at the same anchor (KiCad lists every pin in each unit's block)."""
    return "\n\t".join(unit_block(p, page, u) for u in lib_units(p.lib, p.name))


def unit_block(p: Placed, page: Page, unit: int) -> str:
    pins = "\n\t\t".join(f'(pin "{pin.number}"\n\t\t\t(uuid "{uid(f"pin/{page.file}/{p.ref}/{unit}/{pin.number}")}")\n\t\t)'
                         for pin in lib_pins(p.lib, p.name))
    mirror = f"\n\t\t(mirror {p.mirror})" if p.mirror else ""
    return f"""(symbol
		(lib_id "{p.lib_id}")
		(at {mm(p.x * G)} {mm(p.y * G)} {p.rot}){mirror}
		(unit {unit})
		(body_style 1)
		(exclude_from_sim no)
		(in_bom yes)
		(on_board yes)
		(in_pos_files yes)
		(dnp no)
		(uuid "{uid(f"symbol/{page.file}/{p.ref}/{unit}")}")
		{property_blocks(p)}
		{pins}
		(instances
			(project "{PROJECT}"
				(path "{page.path}"
					(reference "{p.ref}")
					(unit {unit})
				)
			)
		)
	)"""


def wire_block(page: Page, i: int, a, b, width: float) -> str:
    return f"""(wire
		(pts
			(xy {mm(a[0] * G)} {mm(a[1] * G)}) (xy {mm(b[0] * G)} {mm(b[1] * G)})
		)
		(stroke
			(width {mm(width)})
			(type default)
		)
		(uuid "{uid(f"wire/{page.file}/{i}")}")
	)"""


def junction_block(page: Page, at) -> str:
    return f"""(junction
		(at {mm(at[0] * G)} {mm(at[1] * G)})
		(diameter 0)
		(color 0 0 0 0)
		(uuid "{uid(f"junction/{page.file}/{at}")}")
	)"""


def no_connect_block(page: Page, at) -> str:
    return f"""(no_connect
		(at {mm(at[0] * G)} {mm(at[1] * G)})
		(uuid "{uid(f"nc/{page.file}/{at}")}")
	)"""


def glabel_block(page: Page, i: int, name: str, x: float, y: float, rot: int) -> str:
    return f"""(global_label "{name}"
		(shape bidirectional)
		(at {mm(x * G)} {mm(y * G)} {rot})
		(fields_autoplaced yes)
		(effects
			(font
				(size 1.27 1.27)
			)
			(justify left)
		)
		(uuid "{uid(f"glabel/{page.file}/{i}")}")
		(property "Intersheetrefs" "${{INTERSHEET_REFS}}"
			(at {mm(x * G)} {mm(y * G)} {rot})
			(hide yes)
			(show_name no)
			(do_not_autoplace no)
			(effects
				(font
					(size 1.27 1.27)
				)
				(justify left)
			)
		)
	)"""


def text_block(page: Page, i: int, text: str, x: float, y: float, size: float, bold: bool) -> str:
    weight = "\n\t\t\t\t(thickness 1.016)\n\t\t\t\t(bold yes)" if bold else ""
    return f"""(text "{esc(text)}"
		(exclude_from_sim no)
		(at {mm(x * G)} {mm(y * G)} 0)
		(effects
			(font
				(size {mm(size)} {mm(size)}){weight}
			)
			(justify left)
		)
		(uuid "{uid(f"text/{page.file}/{i}")}")
	)"""


def sheet_block(page: Page, at: tuple[float, float]) -> str:
    x, y = at
    return f"""(sheet
		(at {mm(x)} {mm(y)})
		(size 60 10)
		(exclude_from_sim no)
		(in_bom yes)
		(on_board yes)
		(dnp no)
		(fields_autoplaced yes)
		(stroke
			(width 0.1524)
			(type solid)
		)
		(fill
			(color 0 0 0 0)
		)
		(uuid "{page.uuid}")
		(property "Sheetname" "{page.title}"
			(at {mm(x)} {mm(y - 0.7116)} 0)
			(show_name no)
			(do_not_autoplace no)
			(effects
				(font
					(size 1.27 1.27)
				)
				(justify left bottom)
			)
		)
		(property "Sheetfile" "{page.file}"
			(at {mm(x)} {mm(y + 10.5846)} 0)
			(show_name no)
			(do_not_autoplace no)
			(effects
				(font
					(size 1.27 1.27)
				)
				(justify left top)
			)
		)
		(instances
			(project "{PROJECT}"
				(path "/{uid('root')}"
					(page "{page.number}")
				)
			)
		)
	)"""


def embedded_worksheet() -> str:
    """SPCoast's page layout (kicad-embed://SPCoast.kicad_wks) lives in its root file; reuse it."""
    t = (SPCOAST / "SPCoast.kicad_sch").read_text()
    for s, e in blocks(t, "embedded_files", 1):
        return t[s:e]
    return ""


def page_text(page: Page, children: list[Page] = ()) -> str:
    libs = sorted({(p.lib, p.name) for p in page.symbols})
    body = [embedded(lib, name) for lib, name in libs]
    items = [junction_block(page, j) for j in page.junctions]
    items += [no_connect_block(page, nc) for nc in page.no_connects]
    items += [wire_block(page, i, a, b, w) for i, (a, b, w) in enumerate(page.wires)]
    items += [glabel_block(page, i, *g) for i, g in enumerate(page.glabels)]
    items += [text_block(page, i, *t) for i, t in enumerate(page.texts)]
    items += [symbol_block(p, page) for p in page.symbols]
    items += [sheet_block(c, (12.7, 25.4 + 20.32 * i)) for i, c in enumerate(children)]
    if children:   # the root alone carries sheet_instances and the embedded worksheet; its file uuid is the root sheet's
        items += ['(sheet_instances\n\t\t(path "/"\n\t\t\t(page "1")\n\t\t)\n\t)']
    items += ["(embedded_fonts no)"]
    if children:
        items += [embedded_worksheet()]
    nl1, nl2 = "\n\t", "\n\t\t"
    return f"""(kicad_sch
	(version 20260306)
	(generator "eeschema")
	(generator_version "10.0")
	(uuid "{page.uuid if children else uid(f"file/{page.file}")}")
	(paper "{page.paper}")
	{title_block(page.title)}
	(lib_symbols{nl2 + nl2.join(body) if body else ""}
	)
	{nl1.join(items)}
)
"""


# ------------------------------------------------------------------ the pages
#
# Grid-unit layout shared by the pages (A3: 330 x 233 units). Headings at x=10; bands:
#   TRACKPLAN  y 14..48   FIELD  y 62..102   OFFICE  y 142..212   (title block bottom right, x > 180, y > 212)
# TODO texts sit at the left margin under each band's symbols, or right of the desk column in the office band.
# The root sheet's scaffolding reaches the pages through four global labels (one net each across the project).

HX = 10
TRACK_Y = 36        # the main track
FIELD_Y = 74        # the first device row
COL = (50, 200)     # the desk column anchor; the Gilroy Caltrain offsets hang off it
TX = 90             # office-band text x (right of the column and its driver)
L_PROCESSOR, L_CODELINE, L_TRANSPORT, L_PANELIO = "FieldProcessor", "AAR", "CMRInet", "PanelIO"


def common(page: Page):
    """Headings, the interlocking declaration and the house; their seams to the root sheet are global labels."""
    page.heading("TRACKPLAN", HX, 10)
    page.heading("FIELD", HX, 58)
    page.heading("OFFICE", HX, 136)
    plant = page.add("Railroad-Trackplan", "Interlocking", 30, 19, Value="${TITLE}")
    house = page.add("Railroad-Trackplan", "House", 110, 24, **{"CP Name": page.cp_name, "Milepost": "0.0"})
    mid = (70, plant.pin("Codeline")[1])
    page.wire(plant.pin("Codeline"), mid)
    page.wire(mid, house.pin("Codeline"))
    page.glabel(L_CODELINE, mid)
    page.glabel(L_PROCESSOR, plant.pin("Processor"), 6)
    page.no_connects.append(house.pin("MC"))
    page.must((plant, "Codeline"), (house, "Codeline"))
    page.note(f"Global labels {L_PROCESSOR}, {L_CODELINE}, {L_TRANSPORT} and {L_PANELIO} reach the root sheet's processors, "
              "code line encoding, CMRInet transport and desk processor (SPCoast keeps these on South-cTc).", HX, 48)
    page.todo("Milepost 0.0 on the House is a placeholder; no Milepost, NextCP or direction-of-traffic policy is drawn.", HX, 50)
    return plant, house


def office_column(page: Page) -> tuple[Placed, Placed]:
    """A PanelColumn and its MAX7313 driver at the Gilroy Caltrain offsets, so lamps and levers meet its pins."""
    n = page.number - 1   # the pages share one desk: column n, MAX7313 at 0x20 + n - 1
    col = page.add("Railroad-Office", "PanelColumn", COL[0], COL[1], Value=str(n), **{"CP Name": page.cp_name})
    u = page.add("Railroad-HardwareIO", "Driver-I2C-MAX7313-SPCoastcTc", COL[0] + 16, COL[1] - 20, Address=f"0x{0x1f + n:02x}")
    page.glabel(L_PANELIO, u.pin("IOBus"), 6)
    page.todo(f"column {n} and I2C address 0x{0x1f + n:02x} are placeholders: the pages share the root sheet's one desk, "
              "so each takes its own column and expander.", TX, 146)
    return col, u


def field_node(page: Page, iobus_pins: list[tuple[float, float]], in_bytes: str, out_bytes: str) -> Placed:
    """The CMRInet node the page's bits belong to: its IOBus pin joins the drivers' IOBus wire."""
    n = page.number - 1   # the pages share one CMRInet line: node UA n
    rio = page.add("Railroad-HardwareIO", "Driver-CMRInet-Node", 110, FIELD_Y - 4, Address=str(n),
                   NodeType="C", InputBytes=in_bytes, OutputBytes=out_bytes)
    page.bus(iobus_pins, tail=rio.pin("IOBus"))
    page.glabel(L_TRANSPORT, rio.pin("Transport"), -12)
    page.todo(f"node UA{n} (NodeType C, {in_bytes} input and {out_bytes} output bytes) is a guess; the pages share the root "
              "sheet's one CMRInet line, so each takes its own UA.", HX, 98)
    return rio


def lamp_row(page: Page, col: Placed, u: Placed, row: int, color: str, value: str, indication: str) -> Placed:
    """A board lamp at the column's lamp row (1..3); its pin meets the MAX7313 A4/A5/A6 pin."""
    lamp = page.add("Railroad-Office", f"ModelLamp-{color}", COL[0], COL[1] - 56 + 4 * (row - 1), Value=value, Indication=indication)
    page.must((lamp, "~{LAMP}"), (u, {1: "A4", 2: "A5", 3: "A6"}[row]))
    return lamp


def page01() -> Page:
    pg = Page("01-track-circuit.kicad_sch", "Track Circuit", "Track Circuit", 2)
    common(pg)
    pg.intent = ("This page shows one track circuit. On the trackplan, two IRJ-Signal symbols bound the circuit and a "
                 "Track Circuit symbol names it 1T. In the field, a Device-TrackCircuit-Optical named 1T reports occupancy "
                 "on CMRInet input bit 1 of node UA1. In the office, a yellow board lamp on desk column 1 shows the "
                 "indication 1TK through MAX7313 pin A5.")
    # trackplan
    left = pg.add("Railroad-Trackplan", "IRJ-Signal", 70, TRACK_Y, 180, **{"CP Name": pg.cp_name})
    right = pg.add("Railroad-Trackplan", "IRJ-Signal", 150, TRACK_Y, 0, **{"CP Name": pg.cp_name})
    tc = pg.add("Railroad-Trackplan", "Track Circuit", 110, TRACK_Y, Value="1T", **{"CP Name": pg.cp_name})
    pg.track(left.pin("A"), tc.pin("TC"))
    pg.track(tc.pin("TC"), right.pin("A"))
    pg.junctions.append(tc.pin("TC"))
    pg.must((left, "A"), (tc, "TC"), (right, "A"))
    pg.todo("no track is drawn beyond either IRJ (their outer pins are open), and both IRJ-Signal SIGNAL pins are open "
            "(no masts on this page).", HX, 52)
    # field
    dev = pg.add("Railroad-Field", "Device-TrackCircuit-Optical", 60, FIELD_Y, Value="1T")
    ib = pg.add("Railroad-HardwareIO", "Driver-CMRInet-IB", *dev.pin("~{OCC}"), Bit="1")
    pg.must((dev, "~{OCC}"), (ib, "D"))
    rio = field_node(pg, [ib.pin("IOBus")], "1", "0")
    pg.must((ib, "IOBus"), (rio, "IOBus"))
    pg.note("Device and driver meet by coincident pins (Gilroy Caltrain pattern): ~{OCC} on IN.1.", HX, 94)
    # office
    col, u = office_column(pg)
    lamp_row(pg, col, u, 2, "YELLOW", "TRACK", "1TK")
    pg.todo("lamp row 1 (OS, red) and row 3 are empty on purpose; the switch and signal lever rows are empty.", TX, 148)
    pg.facts = [("Interlocking", "Track Circuit (from the sheet title)"), ("CP Name", "Track Circuit"),
                ("Track circuit", "1T, indication 1TK"), ("Field device", "Device-TrackCircuit-Optical 1T, ~{OCC} on CMRInet UA1 IN.1"),
                ("Desk column", "1, CP Name Track Circuit"), ("Board lamp", "TRACK (yellow), Indication 1TK, MAX7313 0x20 pin A5")]
    return pg


def page02() -> Page:
    pg = Page("02-powered-switch.kicad_sch", "Powered Switch", "Powered Switch", 3)
    common(pg)
    pg.intent = ("This page shows one powered switch. On the trackplan, Switch_Powered 1 sits between an IRJ-Signal on "
                 "each main-track side and an IRJ on the reverse leg; its TC field names the OS circuit 1T1. In the field, "
                 "a Device-Switch-OS named 1 takes its motor bit from CMRInet output bit 1 and reports N, R and OCC on "
                 "input bits 1, 2 and 3 of node UA2. In the office, lever 1 on desk column 2 sends NWS and RWS and shows "
                 "NWK and RWK through MAX7313 pins A8, A7, A1 and A2; a red OS lamp shows 1T1K through pin A4.")
    # trackplan (Gilroy Caltrain 771: mirror x, reverse leg down and to the right)
    sw = pg.add("Railroad-Trackplan", "Switch_Powered", 90, TRACK_Y, 0, "x", Value="1", **{"CP Name": pg.cp_name})
    left = pg.add("Railroad-Trackplan", "IRJ-Signal", 70, TRACK_Y, 180, **{"CP Name": pg.cp_name})
    normal = pg.add("Railroad-Trackplan", "IRJ-Signal", 130, TRACK_Y, 0, **{"CP Name": pg.cp_name})
    rev = pg.add("Railroad-Trackplan", "IRJ", 130, TRACK_Y + 13, 0)
    pg.track(left.pin("A"), sw.pin("C"))
    pg.track(sw.pin("N"), normal.pin("A"))
    pg.track(sw.pin("R"), rev.pin("A"))
    pg.must((left, "A"), (sw, "C"))
    pg.must((sw, "N"), (normal, "A"))
    pg.must((sw, "R"), (rev, "A"))
    pg.todo("no track is drawn beyond the IRJs (their outer pins are open); both IRJ-Signal SIGNAL pins are open "
            "(no masts on this page); the plain IRJ on the reverse leg copies Gilroy Caltrain 771.", HX, 52)
    # field (Gilroy Caltrain DevSW1: M on OUT.1, ~{N} ~{R} ~{OCC} on IN.1..3, all by coincident pins)
    dev = pg.add("Railroad-Field", "Device-Switch-OS", 68, FIELD_Y + 3, Value="1")
    ob = pg.add("Railroad-HardwareIO", "Driver-CMRInet-OB", *dev.pin("M"), Bit="1")
    ibn = pg.add("Railroad-HardwareIO", "Driver-CMRInet-IB", *dev.pin("~{N}"), Bit="1")
    ibr = pg.add("Railroad-HardwareIO", "Driver-CMRInet-IB", *dev.pin("~{R}"), Bit="2")
    ibo = pg.add("Railroad-HardwareIO", "Driver-CMRInet-IB", *dev.pin("~{OCC}"), Bit="3")
    for d, pin in ((ob, "M"), (ibn, "~{N}"), (ibr, "~{R}"), (ibo, "~{OCC}")):
        pg.must((dev, pin), (d, "D"))
    rio = field_node(pg, [d.pin("IOBus") for d in (ob, ibn, ibr, ibo)], "1", "1")
    pg.must((ob, "IOBus"), (ibn, "IOBus"), (ibr, "IOBus"), (ibo, "IOBus"), (rio, "IOBus"))
    pg.note("Device and drivers meet by coincident pins (Gilroy Caltrain pattern): M on OUT.1; ~{N}, ~{R}, ~{OCC} on IN.1, IN.2, IN.3.", HX, 94)
    # office (Gilroy Caltrain SWL4001 at column pin 5; lamps at rows 1..3)
    col, u = office_column(pg)
    lever = pg.add("Railroad-Office", "PanelSwitch", COL[0], COL[1] - 27, Value="1")
    pg.must((lever, "Column"), (col, "5"))
    for pin, upin in (("~{NWS}", "A8"), ("~{RWS}", "A7"), ("~{NWK}", "A1"), ("~{RWK}", "A2")):
        pg.must((lever, pin), (u, upin))
    lamp_row(pg, col, u, 1, "RED", "OS", "1T1K")
    pg.todo("lamp rows 2 and 3 and the signal lever row are empty on purpose.", TX, 148)
    pg.facts = [("Interlocking", "Powered Switch (from the sheet title)"), ("CP Name", "Powered Switch"),
                ("Switch", "1, powered; OS circuit 1T1 (TC field ${VALUE}T1); indication 1T1K"),
                ("Field device", "Device-Switch-OS 1: M on CMRInet UA2 OUT.1; ~{N} IN.1, ~{R} IN.2, ~{OCC} IN.3"),
                ("Desk column", "2, CP Name Powered Switch"),
                ("Lever", "PanelSwitch 1 (MAX7313 0x21): controls 1NWS (A8), 1RWS (A7); indications 1NWK (A1), 1RWK (A2)"),
                ("Board lamp", "OS (red), Indication 1T1K, MAX7313 0x21 pin A4")]
    return pg


def page03() -> Page:
    pg = Page("03-single-mast.kicad_sch", "Single Mast", "Single Mast", 4)
    common(pg)
    pg.intent = ("This page shows one controlled signal mast with one head. On the trackplan, Signal Mast Single 2 "
                 "stands on an IRJ-Signal. In the field, Device-Mast-Single 2 drives a Device-Head-TypeD on its pin A; "
                 "the head's APP feeds an Encoder-RYG whose G, Y and R inputs are CMRInet output bits 1, 2 and 3 of node "
                 "UA3. In the office, signal lever 2 on desk column 3 sends NGS, HS and SGS and shows NGK, SGK and TEK "
                 "through MAX7313 pins B2, B3, B4, B6, B7 and B8.")
    # trackplan (Gilroy Caltrain 774NAB: mast on the IRJ-Signal's SIGNAL pin by coincidence)
    irj = pg.add("Railroad-Trackplan", "IRJ-Signal", 110, TRACK_Y, 0, **{"CP Name": pg.cp_name})
    mast = pg.add("Railroad-Trackplan-Signals", "Signal Mast Single", *irj.pin("SIGNAL"), Value="2")
    pg.must((irj, "SIGNAL"), (mast, "SIGNAL"))
    pg.todo("no track is drawn on either side of the IRJ (its A and B pins are open); no track circuit, switch or "
            "opposing mast is drawn. The name 2 follows the talk, not the mast grammar (number, direction, head letters).", HX, 52)
    # field (Gilroy Caltrain 774NC chain: DevMast -> Head (pin A = IND) -> Encoder-RYG (APP) -> OUT bits G, Y, R)
    dev = pg.add("Railroad-Field-Signals", "Device-Mast-Single", 60, FIELD_Y, Value="2")
    head = pg.add("Railroad-Field-Signals", "Device-Head-TypeD", dev.pin("A")[0] + 16, FIELD_Y)   # IND is 16 units left of the anchor
    enc = pg.add("Railroad-Field-Signals", "Encoder-RYG", head.pin("APP")[0] + 16, FIELD_Y)         # APP likewise
    assert dev.pin("A") == head.pin("IND") and head.pin("APP") == enc.pin("APP")
    obg = pg.add("Railroad-HardwareIO", "Driver-CMRInet-OB", *enc.pin("~{G}"), Bit="1")
    oby = pg.add("Railroad-HardwareIO", "Driver-CMRInet-OB", *enc.pin("~{Y}"), Bit="2")
    obr = pg.add("Railroad-HardwareIO", "Driver-CMRInet-OB", *enc.pin("~{R}"), Bit="3")
    pg.must((dev, "A"), (head, "IND"))
    pg.must((head, "APP"), (enc, "APP"))
    for d, pin in ((obg, "~{G}"), (oby, "~{Y}"), (obr, "~{R}")):
        pg.must((enc, pin), (d, "D"))
    rio = field_node(pg, [d.pin("IOBus") for d in (obg, oby, obr)], "0", "1")
    pg.must((obg, "IOBus"), (oby, "IOBus"), (obr, "IOBus"), (rio, "IOBus"))
    pg.note("Mast, head, encoder and drivers meet by coincident pins (Gilroy Caltrain 774NC pattern): G, Y, R on OUT.1, OUT.2, OUT.3.", HX, 94)
    pg.todo("the head carries no Head letter and no Name on purpose (anonymous head on pin A, settled 2026-11-04); "
            "the compiler still reports both as missing.", HX, 100)
    # office (Luchessa SIG8785 at column pin 6)
    col, u = office_column(pg)
    lever = pg.add("Railroad-Office", "PanelSignal", COL[0], COL[1] - 11, Value="2")
    pg.must((lever, "Column"), (col, "6"))
    for pin, upin in (("~{NGS}", "B2"), ("~{HS}", "B3"), ("~{SGS}", "B4"), ("~{NGK}", "B6"), ("~{SGK}", "B7"), ("~{TEK}", "B8")):
        pg.must((lever, pin), (u, upin))
    pg.todo("the board lamp rows and the switch lever row are empty on purpose; the lever plate's own NGK/SGK/TEK lamps are its pins.", TX, 148)
    pg.facts = [("Interlocking", "Single Mast (from the sheet title)"), ("CP Name", "Single Mast"),
                ("Mast", "2, single, CONTROLLED; Indications empty (demand derived)"),
                ("Field mast", "Device-Mast-Single 2; head position A -> Device-Head-TypeD (anonymous) -> Encoder-RYG"),
                ("Head bits", "~{G} CMRInet UA3 OUT.1, ~{Y} OUT.2, ~{R} OUT.3"),
                ("Desk column", "3, CP Name Single Mast"),
                ("Lever", "PanelSignal 2 (MAX7313 0x22): controls 2NGS (B2), 2HS (B3), 2SGS (B4); indications 2NGK (B6), 2SGK (B7), 2TEK (B8)")]
    return pg


def root_page() -> Page:
    """The root: the sheet list and, once for the project, what SPCoast keeps on South-cTc (values copied from it)."""
    pg = Page("Examples.kicad_sch", "Examples", "", 1, paper="USLetter")
    pg.note("Railroad symbol library examples: one page per pattern the layout compiler derives.\n"
            "Drafted by tools/examples/build_examples.py (FieldUnit-Subdivision); tidied by hand in KiCad.", 10, 14)
    pg.heading("SHARED", 10, 78)
    pg.note("What every page shares, as SPCoast draws it on South-cTc: the Railroad, the OfficeUnit on its desk processor,\n"
            "the field processor, the CMRInet transport and encoding, and the AAR code line encoding. The pages reach these\n"
            f"through the global labels {L_PROCESSOR}, {L_PANELIO}, {L_TRANSPORT} and {L_CODELINE}.", 10, 84)
    pg.add("Railroad-Office", "Railroad", 30, 106, Value="Examples", Railroad="Southern Pacific", Region="Coast Line",
           Era="1960+", Rulebook="GCOR")
    desk = pg.add("Railroad-HardwareIO", "Processor", 70, 100, Value="ExamplesDesk", Board="cpNode-Xiao")
    office = pg.add("Railroad-Office", "OfficeUnit", 124, 99, Value="Examples", Style="US&S")
    pg.wire(desk.pin("Processor"), office.pin("Processor"))
    pg.glabel(L_PANELIO, desk.pin("IOBus"), 6)
    pg.must((desk, "Processor"), (office, "Processor"))
    fieldp = pg.add("Railroad-HardwareIO", "Processor", 70, 118, Value="ExamplesField", Board="MacOS")
    transport = pg.add("Railroad-Office", "Transport-CMRInet", 108, 117, Baud="28800", Port="/dev/cu.modemXXXX")
    pg.wire(fieldp.pin("Processor"), transport.pin("Processor"))
    pg.glabel(L_PROCESSOR, (fieldp.pin("Processor")[0] + 1, fieldp.pin("Processor")[1]))   # text runs right, along the wire
    enc_cmri = pg.add("Railroad-Office", "Encoding-CMRInet", 126, 130)
    corner = (transport.pin("Transport")[0], 130)
    pg.wire(transport.pin("Transport"), corner)
    pg.wire(corner, enc_cmri.pin("Transport"))
    pg.glabel(L_TRANSPORT, corner)
    pg.must((fieldp, "Processor"), (transport, "Processor"))
    pg.must((transport, "Transport"), (enc_cmri, "Transport"))
    aar = pg.add("Railroad-Office", "Encoding-AAR", 70, 140)
    pg.glabel(L_CODELINE, aar.pin("Codeline"), 6)
    pg.todo("Railroad, processors (boards), transport port and baud, and the US&S office style are copied from SPCoast "
            "as placeholders.", 10, 148)
    pg.todo("the field processor's IOBus and the AAR encoding's Transport are open, as on South-cTc (no MQTT transport drawn).", 10, 150)
    pg.intent = ("The root sheet lists the pages and holds, once for the project, the Railroad, the OfficeUnit and its "
                 "processor, the field processor, the CMRInet transport and encoding, and the AAR code line encoding.")
    return pg


def finish(page: Page) -> Page:
    """No-connects on the MAX7313 pins no lamp or lever uses (the Gilroy Caltrain panel draws them so)."""
    used = {pin for net in page.expect for pin in net}
    for p in page.symbols:
        if p.name.startswith("Driver-I2C-MAX7313"):
            for pin in lib_pins(p.lib, p.name):
                if (p.ref, pin.number) not in used and pin.name != "IOBus":
                    page.no_connects.append(p.pin(pin.number))
    return page


PAGES = [page01, page02, page03]


# ------------------------------------------------------------------ build

def sidecar(page: Page) -> str:
    rows = "\n".join(f"| {k} | {v} |" for k, v in page.facts)
    todos = "\n".join(f"- {t}" for t in page.todos)
    syms = "\n".join(f"- `{p.ref}` {p.lib_id}" + (f" `{p.values['Value']}`" if p.values.get("Value") else "") for p in page.symbols)
    return f"""# {page.title}

`{page.file}`, page {page.number} of the Examples project. Drafted by `tools/examples/build_examples.py`
(FieldUnit-Subdivision); tidied by hand in KiCad.

## Intent

{page.intent}

## Facts the compiler derives

| Fact | Value |
| --- | --- |
{rows}

## Symbols

{syms}

## TODO

{todos}
"""


def build(root: Page, pages: list[Page]):
    if OUT.resolve() == SPCOAST.resolve() or OUT.resolve().is_relative_to(SPCOAST.resolve()):
        sys.exit("refusing to write into Railroad/SPCoast")
    if list(OUT.glob("~*.lck")):
        sys.exit(f"{OUT} is open in KiCad (lock files); close it first")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "production").mkdir(exist_ok=True)
    for page in pages:
        (OUT / page.file).write_text(page_text(page))
        (OUT / page.file.replace(".kicad_sch", ".md")).write_text(sidecar(page))
    (OUT / root.file).write_text(page_text(root, pages))
    pro = json.loads((SPCOAST / "SPCoast.kicad_pro").read_text())
    pro["meta"]["filename"] = f"{PROJECT}.kicad_pro"
    pro["sheets"] = [[root.uuid, PROJECT]] + [[p.uuid, p.title] for p in pages]
    pro["schematic"]["top_level_sheets"] = [{"filename": f"{PROJECT}.kicad_sch", "name": PROJECT, "uuid": root.uuid}]
    pro["schematic"]["used_designators"] = ""
    pro["text_variables"] = {}
    (OUT / f"{PROJECT}.kicad_pro").write_text(json.dumps(pro, indent=2) + "\n")
    print(f"built {OUT}: {len(pages)} pages, {sum(len(p.symbols) for p in [root] + pages)} symbols")


# ------------------------------------------------------------------ check

def check(root: Page, pages: list[Page]) -> bool:
    ok = True
    sch = OUT / root.file
    with tempfile.TemporaryDirectory(dir=os.environ.get("EXAMPLES_SCRATCH")) as tmp:
        net = Path(tmp) / f"{PROJECT}.net"
        r = subprocess.run([KICAD_CLI, "sch", "export", "netlist", "--output", str(net), str(sch)], capture_output=True, text=True)
        if r.returncode or not net.is_file():
            print(r.stdout, r.stderr)
            return False
        model = NetlistReader().read(net)
    nets = [frozenset((n.reference, n.pin) for n in net.nodes) for net in model.nets]
    singles = {n for n in nets if len(n) == 1}
    print(f"netlist: {len(model.components)} components, {len(nets)} nets, {len(singles)} single-pin nets")
    for page in [root] + pages:
        refs = {p.ref for p in page.symbols}
        present = 0
        for want in page.expect:
            if any(want <= n for n in nets):
                present += 1
            else:
                ok = False
                print(f"  {page.file}: MISSING net {sorted(want)}")
        opens = sorted(sorted(n)[0] for n in singles if sorted(n)[0][0] in refs)
        print(f"  {page.file}: {present}/{len(page.expect)} expected nets present; open pins: "
              + ", ".join(f"{r}.{p}" for r, p in opens))
    for name in (L_PROCESSOR, L_CODELINE, L_TRANSPORT, L_PANELIO):
        hit = [n for n in model.nets if n.name == name]
        print(f"  net {name}: {len(hit[0].nodes) if hit else 0} pins across the project")
        ok &= bool(hit)
    erc = OUT / "production" / f"{PROJECT}-erc.rpt"
    subprocess.run([KICAD_CLI, "sch", "erc", "--output", str(erc), "--severity-all", str(sch)], capture_output=True)
    text = erc.read_text()
    print("ERC:", " | ".join(ln.strip() for ln in text.splitlines() if "ERC messages" in ln))
    return ok


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="check only")
    a = ap.parse_args()
    root = root_page()
    pages = [finish(f()) for f in PAGES]
    if not a.check:
        build(root, pages)
    sys.exit(0 if check(root, pages) else 1)
