"""Geometry: the drawing as a design fact (ADR 0010, accepted 2026-10-24; ADR 0011 §7: always written).

Per interlocking, where every named trackplan thing sits, each run of track the designer drew, and every track
symbol with no railroad name, in the interlocking's own frame (millimetres from the top-left of its drawn extent,
x right, y down); and the glyphs those placements name, each stated once with its ports and its shape. Read from
the ``.kicad_sch`` files and the symbol libraries through ``kicad_services``, joined to the seam facts by
reference (a netlist identity) and to circuits through the netlist only. Nothing here is read for connectivity,
membership or a name (R2; DoD3): the rest of the Layout Data Model File is the same whether or not this runs.

Geometry's one contract with the semantic sections is identity (three-maps D10, ruled 2026-10-27): a placement is
keyed by its thing's railroad name, a marker names its track row by the row's ``id``, and a run's ends name the switch
port or the track row pin they meet (``relations.from``, ``.to``; D5). The importer finds those ends by where a run's
end lies on the page, and records the connection, never a coordinate fact. No semantic fact is copied here.

What is on the trackplan is decided by Role (§4.1): ``APPLIANCE``, ``TRACK``, ``POLICY``, plus the house, never by
library, symbol name or position (``trackplan.TRACKPLAN_ROLES``). A wire is track when it ends on a pin of a
trackplan symbol or is chained onto one that does. Which circuit a run carries is derived from what its ends meet by
the reference derivation (``tools/layout_model/derive.py``), never read here.
"""
from __future__ import annotations

import math
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .seams import Seams, key_of, loc
from .source import Symbol
from .trackplan import TRACKPLAN_ROLES, is_consumer, is_switch, pin_ref, unit_of

COORDINATE_DECIMALS = 2     # placements and runs sit on the drawing's grid (§4.2)
GLYPH_DECIMALS = 4          # a glyph's primitives have up to four

Point = tuple[float, float]


@dataclass
class Geometry:
    """The geometry piece's output: one ``geometry`` object per interlocking, the glyphs they name, the libraries read."""

    interlockings: dict[str, dict[str, Any]] = field(default_factory=dict)
    glyphs: dict[str, dict[str, Any]] = field(default_factory=dict)
    libraries: dict[str, str] = field(default_factory=dict)


# ------------------------------------------------------------------------------------------------- glyphs

def anchor_of(pins: dict[str, Point]) -> Point:
    """A glyph's origin is its bottom-left pin in its unrotated, unmirrored state: the lowest pin, then the leftmost
    (owner, 2026-10-24; §4.3). The library frame has y up, so lowest is least y. No pin: KiCad's origin."""
    if not pins:
        return (0.0, 0.0)
    return min(pins.values(), key=lambda p: (p[1], p[0]))


def _r(v: float, nd: int) -> float:
    return round(v, nd) + 0.0           # + 0.0 turns -0.0 into 0.0


def style_of(g) -> dict[str, Any]:
    """KiCad's stroke and fill, written only where not the default (§4.9): a width only when not 0 (0 means the
    context's default), a stroke type other than solid, a fill other than none; a colour as #rrggbb with its opacity."""
    out: dict[str, Any] = {}
    stroke: dict[str, Any] = {}
    if g.stroke_width > 0:
        stroke["width"] = _r(g.stroke_width, GLYPH_DECIMALS)
    if g.stroke_type not in ("", "default", "solid"):
        stroke["type"] = g.stroke_type
    if stroke:
        out["stroke"] = stroke
    if g.fill_type not in ("", "none"):
        fill: dict[str, Any] = {"type": g.fill_type}
        if g.fill_type == "color" and g.fill_color is not None:
            r, gg, b, a = g.fill_color
            fill["color"] = "#%02x%02x%02x" % (int(r), int(gg), int(b))
            if a != 1:
                fill["opacity"] = a
        out["fill"] = fill
    return out


def glyph_of(sym) -> dict[str, Any]:
    """A library symbol as a glyph in the Layout Data Model File's frame: its anchor pin at 0,0, x right, y down,
    KiCad's own numbers; every pin as a port; its pin lines and graphics as primitives (§4.9)."""
    pins = {p.name: (p.x, p.y) for p in sym.pins}
    ax, ay = anchor_of(pins)

    def pt(p: Point) -> dict[str, float]:
        return {"x": _r(p[0] - ax, GLYPH_DECIMALS), "y": _r(-(p[1] - ay), GLYPH_DECIMALS)}

    def points(ps) -> str:
        return " ".join(f"{pt(p)['x']},{pt(p)['y']}" for p in ps)

    shape: list[dict[str, Any]] = []
    for p in sym.pins:
        if p.length > 0 and not p.hidden:            # a pin's drawn line is part of the picture
            a = math.radians(p.rotation)
            shape.append({"type": "polyline", "points": points([(p.x, p.y), (p.x + p.length * math.cos(a), p.y + p.length * math.sin(a))])})
    for g in sym.graphics:
        prim: dict[str, Any] = {"type": g.kind}
        if g.kind == "polyline":
            prim["points"] = points(g.points)
        elif g.kind == "circle":
            prim["center"], prim["radius"] = pt(g.points[0]), _r(g.radius, GLYPH_DECIMALS)
        elif g.kind == "arc":
            prim["start"], prim["mid"], prim["end"] = (pt(p) for p in g.points)
        elif g.kind == "rectangle":
            prim["start"], prim["end"] = (pt(p) for p in g.points)
        elif g.kind == "text":
            prim.update({"text": g.text, "at": pt(g.points[0]), "size": _r(g.size, GLYPH_DECIMALS)})
            if g.rotation:
                prim["rotation"] = g.rotation
            if g.justify:
                prim["justify"] = g.justify
        else:
            continue
        prim.update(style_of(g))
        shape.append(prim)
    return {"ports": {name: pt(p) for name, p in pins.items()}, "shape": shape}


# ---------------------------------------------------------------------------------------------- transforms

def kicad_place(pl, local: Point) -> Point:
    """KiCad's own transform of a library-frame point (y up) to the page (y down): mirror, turn counter-clockwise
    as seen on the page, translate. The direction of the turn was asked of kicad-cli, not assumed
    (``tests/fixtures/kicad/rotation_probe.py``, 2026-10-25)."""
    lx, ly = local
    if pl.mirror == "y":
        lx = -lx
    if pl.mirror == "x":
        ly = -ly
    a = math.radians(pl.rotation)
    rx = lx * math.cos(a) - ly * math.sin(a)
    ry = lx * math.sin(a) + ly * math.cos(a)
    return pl.x + rx, pl.y - ry


def page_of(placement: dict[str, Any], local: Point) -> Point:
    """The placement transform of ADR 0010 §4.3, stated in the Layout Data Model File's frame throughout (y down):
    mirror the glyph-local point (mirror y negates x, mirror x negates y), turn it counter-clockwise as seen on the
    page by ``rotation`` (x' = x cos + y sin, y' = -x sin + y cos), add ``at``."""
    x, y = local
    if placement.get("mirror") == "y":
        x = -x
    if placement.get("mirror") == "x":
        y = -y
    a = math.radians(placement.get("rotation", 0))
    return placement["at"]["x"] + x * math.cos(a) + y * math.sin(a), placement["at"]["y"] - x * math.sin(a) + y * math.cos(a)


def _rounded(p: Point) -> Point:
    return (_r(p[0], COORDINATE_DECIMALS), _r(p[1], COORDINATE_DECIMALS))


# --------------------------------------------------------------------------------------------- runs of track

def chain(wires: list[tuple[Point, ...]], breaks: set[Point]) -> list[list[Point]]:
    """Join wire segments end to end into polylines, breaking where a run passes through a port, and merge
    collinear vertices (a junction where a lamp's pin touched the line is a KiCad artifact, §4.1)."""
    segs = [list(w) for w in wires]
    out: list[list[Point]] = []
    while segs:
        line = segs.pop(0)
        grown = True
        while grown:
            grown = False
            for s in list(segs):
                for end in (line[-1], line[0]):
                    if end in breaks:
                        continue
                    if s[0] == end or s[-1] == end:
                        piece = s if s[0] == end else s[::-1]
                        line = line + piece[1:] if end == line[-1] else piece[::-1][:-1] + line
                        segs.remove(s)
                        grown = True
                        break
                if grown:
                    break
        merged = [line[0]]
        for p, q in zip(line[1:-1], line[2:]):
            a, b = merged[-1], p
            if (b[0] - a[0]) * (q[1] - b[1]) != (b[1] - a[1]) * (q[0] - b[0]):
                merged.append(p)
        merged.append(line[-1])
        out.append(merged)
    return out


def _ordered(points: list[Point]) -> list[Point]:
    """A run has no direction of its own: state it from its lesser end so a reversed drawing writes the same row."""
    return points if points[0] <= points[-1] else points[::-1]


# ------------------------------------------------------------------------------------------------- reading

class _Project:
    """The project's sheets and libraries, each read once."""

    def __init__(self, project_dir: Path, libraries: Optional[dict[str, Path]]):
        import sys
        tools = str(Path(__file__).resolve().parents[1])
        if tools not in sys.path:
            sys.path.insert(0, tools)
        from kicad_services.library_table import library_paths
        from kicad_services.schematic_reader import SchematicPlacementReader
        from kicad_services.symbol_library_reader import SymbolLibraryReader

        self.dir = project_dir
        self.libraries = libraries if libraries is not None else library_paths(project_dir)
        self._sheets: dict[str, Any] = {}
        self._libs: dict[str, Any] = {}
        self._sheet_reader = SchematicPlacementReader()
        self._lib_reader = SymbolLibraryReader()

    def sheet(self, file: str):
        if file not in self._sheets:
            self._sheets[file] = self._sheet_reader.read(self.dir / file)
        return self._sheets[file]

    def symbol(self, lib_id: str):
        lib, _, name = lib_id.partition(":")
        if lib not in self._libs:
            path = self.libraries.get(lib)
            self._libs[lib] = self._lib_reader.read(path) if path and path.is_file() else None
        model = self._libs[lib]
        return model.get(name) if model else None

    def version(self, lib: str) -> Optional[str]:
        path = self.libraries.get(lib)
        if not path or not path.is_file():
            return None
        try:
            out = subprocess.run(["git", "describe", "--always", "--dirty"], cwd=path.parent, capture_output=True, text=True, timeout=10)
            return out.stdout.strip() or None
        except (OSError, subprocess.SubprocessError):
            return None


def read(sm: Seams, project_dir: Optional[Path] = None, libraries: Optional[dict[str, Path]] = None) -> Geometry:
    """Every interlocking's geometry and the glyphs they name. ``project_dir`` is where the sheets are (the project's
    own directory unless a test points at a copy); ``libraries`` maps library names to files (KiCad's tables unless
    given). Errors go to ``sm.report`` and an interlocking with one writes no geometry."""
    out = Geometry()
    src = sm.source
    if project_dir is None:
        if src.project is None:
            sm.report.error("geometry.project", "the export names no project, so its sheets cannot be read")
            return out
        project_dir = Path(src.project).parent
    project = _Project(Path(project_dir), libraries)

    for ix in sm.interlockings.values():
        trackplan = [s for s in src.symbols.values() if s.role in TRACKPLAN_ROLES and unit_of(sm, s) == ix.name]
        sheets = sorted({s.sheet for s in trackplan})
        if not sheets:
            continue                                                     # nothing drawn: absent is absent
        if len(sheets) > 1:
            sm.report.error("geometry.sheets", f"{ix.name}: its trackplan spans {len(sheets)} sheets ({', '.join(sheets)}) and has no single frame (ADR 0010 §4.10)", loc(ix.sym))
            continue
        sheet = sheets[0]
        file = src.sheet_files.get(sheet)
        if not file:
            sm.report.error("geometry.sheet", f"{ix.name}: the export names no file for sheet {sheet}", loc(ix.sym))
            continue
        model = project.sheet(file)
        geometry = _interlocking(sm, ix, trackplan, model, project, out)
        if geometry is not None:
            out.interlockings[ix.name] = geometry
    for lib in sorted({k.partition(":")[0] for k in out.glyphs}):
        version = project.version(lib)
        if version:
            out.libraries[lib] = version
    return out


def _interlocking(sm: Seams, ix, trackplan: list[Symbol], model, project: _Project, out: Geometry) -> Optional[dict[str, Any]]:
    src, report = sm.source, sm.report
    errors_before = len(report.errors)
    symbols = src.symbols
    houses = [h for h in ix.houses.values() if h.sym.sheet == ix.sym.sheet]

    # every placed thing with its library symbol and its pins on the page (KiCad's transform over the library)
    placed: dict[str, tuple[Any, Any, dict[str, Point]]] = {}
    for s in trackplan + [h.sym for h in houses]:
        pl = model.placements.get(s.ref)
        if pl is None:
            report.error("geometry.placement", f"{ix.name}: {s.ref} ({s.lib_id}) is in the export but not on sheet {model.path.name}", loc(s))
            continue
        sym = project.symbol(pl.lib_id)
        if sym is None:
            report.error("geometry.library", f"{ix.name}: no library symbol for {pl.lib_id} (KiCad's library tables name no file, or the file lacks it)", loc(s))
            continue
        placed[s.ref] = (pl, sym, {p.name: _rounded(kicad_place(pl, (p.x, p.y))) for p in sym.pins})
    if len(report.errors) > errors_before:
        return None

    glyph_cache: dict[str, dict[str, Any]] = {}

    def glyph(pl, sym) -> dict[str, Any]:
        if pl.lib_id not in glyph_cache:
            glyph_cache[pl.lib_id] = glyph_of(sym)
        return glyph_cache[pl.lib_id]

    def anchor_page(ref: str) -> Point:
        pl, sym, _ = placed[ref]
        return _rounded(kicad_place(pl, anchor_of({p.name: (p.x, p.y) for p in sym.pins})))

    # ports and runs on the page, before the frame is known
    port_at: dict[Point, tuple[str, str]] = {}
    for ref, (pl, sym, pins) in placed.items():
        if symbols[ref].role in TRACKPLAN_ROLES:
            for pin, xy in pins.items():
                port_at[xy] = (ref, pin)
    through = {xy for xy, (ref, _) in port_at.items() if symbols[ref].role == "TRACK" or is_switch(symbols[ref])}
    track_wires = [w for w in model.wires if any(p in port_at for p in (w[0], w[-1]))]
    grown = True
    while grown:                                                          # chained end to end onto track is track (§4.1)
        grown = False
        ends = {p for w in track_wires for p in (w[0], w[-1])}
        for w in model.wires:
            if w not in track_wires and (w[0] in ends or w[-1] in ends):
                track_wires.append(w)
                grown = True
    runs = [_ordered(line) for line in chain(track_wires, through)]

    # the frame: the least x and the least y over every placement and run (§4.2)
    anchors = {ref: anchor_page(ref) for ref in placed}
    xs = [a[0] for a in anchors.values()] + [p[0] for line in runs for p in line]
    ys = [a[1] for a in anchors.values()] + [p[1] for line in runs for p in line]
    ox, oy = min(xs), min(ys)

    def norm(p: Point) -> dict[str, float]:
        return {"x": _r(p[0] - ox, COORDINATE_DECIMALS), "y": _r(p[1] - oy, COORDINATE_DECIMALS)}

    def placement(ref: str) -> dict[str, Any]:
        pl, sym, _ = placed[ref]
        row: dict[str, Any] = {"at": norm(anchors[ref]), "glyph": pl.lib_id}
        if pl.rotation:
            row["rotation"] = int(pl.rotation)
        if pl.mirror:
            row["mirror"] = pl.mirror
        out.glyphs.setdefault(pl.lib_id, glyph(pl, sym))
        return row

    def net_of(ref: str, pin: str):
        return src.net_of(ref, pin)

    def end_ref(ref: str, pin: str) -> Optional[str]:
        """What a run's end meets (three-maps D5): a switch's port or a track row's side, in the one form the rows'
        relations use (``trackplan.pin_ref``). A run's end is never a track circuit marker's TC."""
        s = symbols[ref]
        return pin_ref(ix.name, s, pin) if is_switch(s) or s.role in ("TRACK", "POLICY") else None

    appliances: dict[str, Any] = {}
    masts: dict[str, str] = {}
    consumer_markers: list[dict[str, Any]] = []
    for s in trackplan:
        if s.role != "APPLIANCE" or s.get("Appliance") == "head" or s.ref not in placed:
            continue
        name = key_of(s, report)
        if not name:
            report.missing("geometry.name", f"{ix.name}: an {s.lib_id} has no Name; its placement is not written", loc(s))
            continue
        if is_consumer(ix.name, s) and s.uuid and src.net_of(s.ref, "TC"):
            consumer_markers.append({"row": s.uuid, **placement(s.ref)})   # a consumer is a row: its marker names it by id (D10)
            continue
        appliances[name] = placement(s.ref)
        if s.get("Appliance") == "mast":
            masts[s.ref] = name
    for s in trackplan:                                                   # a head nests under its mast by letter (§4.5)
        if s.get("Appliance") != "head" or s.ref not in placed:
            continue
        net = net_of(s.ref, "M")
        owner = next((p.ref for p in net.others(s.ref) if p.ref in masts), None) if net else None
        if owner is None:
            report.missing("geometry.head", f"{ix.name}: head {s.ref} is on no mast's M pin; its placement is not written", loc(s))
            continue
        appliances[masts[owner]].setdefault("heads", {})[key_of(s, report)] = placement(s.ref)

    house_rows = {h.cp_name: placement(h.sym.ref) for h in houses if h.sym.ref in placed}

    track: list[dict[str, Any]] = []
    for line in runs:
        ends = [port_at.get(line[0]), port_at.get(line[-1])]
        for end, xy in zip(ends, (line[0], line[-1])):
            if end is None and xy not in model.junctions:
                report.error("geometry.run_end", f"{ix.name}: a run of track ends at {xy} where no trackplan pin and no junction is", f"sheet {model.path.name}")
        row: dict[str, Any] = {"points": " ".join(f"{norm(p)['x']},{norm(p)['y']}" for p in line)}
        relations = {key: end_ref(*e) for key, e in zip(("from", "to"), ends) if e and end_ref(*e)}
        if relations:
            row["relations"] = relations
        track.append(row)

    markers: list[dict[str, Any]] = list(consumer_markers)
    mileposts: dict[str, Any] = {}
    for s in trackplan:
        if s.role == "APPLIANCE" or s.ref not in placed:
            continue
        if s.role == "TRACK" and s.kind == "MILEPOST":
            mileposts[key_of(s, report)] = placement(s.ref)
            continue
        if not s.uuid:
            report.missing("geometry.marker", f"{ix.name}: a {s.kind} has no KiCad UUID, so its marker names no row; not written", loc(s))
            continue
        markers.append({"row": s.uuid, **placement(s.ref)})            # the marker joins its track row by id (D10)

    if len(report.errors) > errors_before:
        return None
    geometry: dict[str, Any] = {"appliances": appliances, "houses": house_rows, "track": track, "markers": markers}
    if mileposts:
        geometry["mileposts"] = mileposts
    return geometry


def check_transform(geometry: Geometry, sm: Seams, project_dir: Optional[Path] = None, libraries: Optional[dict[str, Path]] = None) -> list[str]:
    """The file's transform over the written glyphs lands every pin of every placement where KiCad's transform over
    the library put it (§4.3). Returns the disagreements; the gate wants none."""
    src = sm.source
    project = _Project(Path(project_dir) if project_dir else Path(src.project).parent, libraries)
    bad: list[str] = []
    for ix in sm.interlockings.values():
        g = geometry.interlockings.get(ix.name)
        if g is None:
            continue
        trackplan = [s for s in src.symbols.values() if s.role in TRACKPLAN_ROLES and s.sheet == ix.sym.sheet]
        houses = [h.sym for h in ix.houses.values() if h.sym.sheet == ix.sym.sheet]
        model = project.sheet(src.sheet_files[ix.sym.sheet])
        for s in trackplan + houses:                                      # page coordinates on both sides: the frame cancels
            pl = model.placements[s.ref]
            sym = project.symbol(pl.lib_id)
            glyph = geometry.glyphs[pl.lib_id]
            anchor = kicad_place(pl, anchor_of({p.name: (p.x, p.y) for p in sym.pins}))
            row = {"at": {"x": anchor[0], "y": anchor[1]}, "rotation": int(pl.rotation), "mirror": pl.mirror}
            for pin in sym.pins:
                want = kicad_place(pl, (pin.x, pin.y))
                port = glyph["ports"][pin.name]
                got = page_of(row, (port["x"], port["y"]))
                if _rounded(got) != _rounded(want):
                    bad.append(f"{ix.name} {s.ref} {pl.lib_id} pin {pin.name}: file transform {_rounded(got)} != KiCad {_rounded(want)}")
    return bad


def _every_placement(g: dict[str, Any]):
    for row in list(g.get("appliances", {}).values()) + list(g.get("houses", {}).values()) + list(g.get("mileposts", {}).values()) + g.get("markers", []):
        yield row
        for head in row.get("heads", {}).values():
            yield head
