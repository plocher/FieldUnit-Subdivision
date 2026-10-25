"""ADR 0010's worked example and pictures, generated from the Sargent trackplan sheet, never typed.

    uv run python docs/adr/0010/make_pictures.py [--railroad ~/Dropbox/KiCad/Railroad]

Writes, beside this script:

- ``geometry.schema.json``: the proposed fragment for schema 3.1.0 (ADR 0010 §4): ``$defs/geometry`` (one
  interlocking's placements, runs and markers) and ``$defs/glyphs`` (the glyphs a layout draws with, stated once).
- ``sargent.geometry.json``: ``{"geometry": ..., "glyphs": ...}``: Sargent's ``geometry`` object as the proposal would
  have the compiler write it under ``interlockings.Sargent``, and the ``glyphs`` it names, as they would sit under
  ``layout.glyphs``. Read from ``SPCoast/Sargent.kicad_sch`` (placements, wires, junctions), from
  ``symbols/Railroad-Trackplan.kicad_sym`` (each glyph's pins and shape) and from a netlist of the project that the
  script exports with kicad-cli, uses and deletes (which net is which circuit; a saved netlist is never read, since
  it may be stale). Normalised, in canonical form, validated against the fragment.
- ``sargent-geometry.svg``: the facts drawn: frame, polylines, placements, the written glyphs in grey.
- ``four-views.svg``: the four views the owner named, each derived from the same object; the model board, the route
  finder and the documentation packet draw the written glyphs, the thinline draws none.

This is a picture script, not the compiler piece: the placement reader for ``tools/layout_compiler`` comes after
ratification (handoff step 3). The s-expression loading is jBOM's, through ``tools/kicad_services``.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))

import jsonschema  # noqa: E402
from jbom.common.sexp_parser import load_kicad_file  # noqa: E402
from sexpdata import Symbol  # noqa: E402

from layout_compiler.source import from_netlist  # noqa: E402
from tools import layout_model  # noqa: E402

INTERLOCKING = "Sargent"
TRACKPLAN_ROLES = {"APPLIANCE", "TRACK", "POLICY"}
GLYPH_LIBRARY = "Railroad-Trackplan"

# ---------------------------------------------------------------------------------------------------------------
# The proposed schema fragment (ADR 0010 §4). Coordinates are objects and polylines are strings because the
# canonical form sorts every list (ADR 0008 §4.8): a list's order never carries meaning.
# ---------------------------------------------------------------------------------------------------------------
_QUALIFIED = "^[^:/\\s][^:/]*:[^:/\\s][^:/]*$"
_PORT = "^[^:/\\s][^:/]*:[^:/\\s][^:/]*\\.[A-Za-z0-9_]+$"
_GLYPH_KEY = "^[^:\\s][^:]*:[^:\\s][^:]*$"
_POINT = {"$ref": "#/$defs/point"}
_STYLE = {"stroke": {"$ref": "#/$defs/stroke"}, "fill": {"$ref": "#/$defs/fill"}}


def _primitive(kind: str, props: dict, required: list[str], description: str) -> dict:
    return {
        "description": description, "type": "object", "additionalProperties": False,
        "required": ["type", *required],
        "properties": {"type": {"const": kind}, **props, **_STYLE},
    }


GEOMETRY_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://spcoast.com/schemas/layout-model/v3.1.0-geometry.json",
    "title": "geometry and glyphs (proposed for layout-model/v3.1.0, ADR 0010)",
    "description": "The drawing as a design fact. geometry: where each named thing of one interlocking sits and how its track runs, in the interlocking's own frame (millimetres from the top-left of its drawn extent, x right, y down), joined to meaning by name only and never read for connectivity. glyphs: the pictures the placements name, each stated once with its ports and its shape, so every view is drawn from the Layout Data Model File alone.",
    "$defs": {
        "coordinate": {"type": "number"},
        "point": {
            "type": "object", "required": ["x", "y"], "additionalProperties": False,
            "properties": {"x": {"$ref": "#/$defs/coordinate"}, "y": {"$ref": "#/$defs/coordinate"}},
        },
        "polyline": {
            "description": "Ordered vertices, SVG points syntax: 'x,y x,y ...'. A string because a JSON list is sorted by the canonical form.",
            "type": "string", "pattern": "^-?\\d+(\\.\\d+)?,-?\\d+(\\.\\d+)?( -?\\d+(\\.\\d+)?,-?\\d+(\\.\\d+)?)+$",
        },
        "glyphKey": {"description": "The drawing's own name for a glyph: library and symbol, 'Railroad-Trackplan:Switch_Lock'. The library's version is in provenance.", "type": "string", "pattern": _GLYPH_KEY},
        "placement": {
            "description": "Where a glyph sits: its anchor (the glyph's origin, which is its bottom-left pin) on the page, its turn (degrees, counter-clockwise as seen on the page, 0/90/180/270) and its mirror (x: top for bottom; y: left for right), applied mirror first, then turn, then translate; and which glyph.",
            "type": "object", "required": ["at", "glyph"], "additionalProperties": False,
            "properties": {
                "at": _POINT,
                "glyph": {"$ref": "#/$defs/glyphKey"},
                "rotation": {"type": "integer", "enum": [90, 180, 270]},
                "mirror": {"type": "string", "enum": ["x", "y"]},
                "heads": {
                    "description": "A mast's heads by letter: a head cannot exist alone (view §4).",
                    "type": "object", "propertyNames": {"pattern": "^[A-Z]$"},
                    "additionalProperties": {"$ref": "#/$defs/placement"},
                },
            },
        },
        "track": {
            "description": "One drawn run of track between two things: the circuit it belongs to (absent for dark track) and, where an end is an appliance's track port, that port by name (Luchessa:783.R). An end at a joint or a marker is absent: the circuit's bounds are track's business.",
            "type": "object", "required": ["points"], "additionalProperties": False,
            "properties": {
                "points": {"$ref": "#/$defs/polyline"},
                "circuit": {"type": "string", "pattern": _QUALIFIED},
                "from": {"type": "string", "pattern": _PORT},
                "to": {"type": "string", "pattern": _PORT},
            },
        },
        "marker": {
            "description": "A track symbol with no railroad name of its own (a joint, END CTC, NextCP, an industry, a policy sign): its kind as the libraries spell it, its placement and glyph, and the circuit at each of its track pins, so a reader joins it to track by name.",
            "type": "object", "required": ["kind", "at", "glyph"], "additionalProperties": False,
            "properties": {
                "kind": {"type": "string", "pattern": "^[A-Z][A-Z0-9_]*$"},
                "at": _POINT,
                "glyph": {"$ref": "#/$defs/glyphKey"},
                "rotation": {"type": "integer", "enum": [90, 180, 270]},
                "mirror": {"type": "string", "enum": ["x", "y"]},
                "circuits": {
                    "description": "The circuit at each track pin of the marker, by pin name; a pin on dark track is absent.",
                    "type": "object", "additionalProperties": {"type": "string", "pattern": _QUALIFIED},
                },
            },
        },
        "stroke": {
            "description": "KiCad's stroke, written only where it is not the default: a width in millimetres (KiCad's 0 means 'the default, which depends on context' and is not written), a dash type other than solid.",
            "type": "object", "additionalProperties": False,
            "properties": {"width": {"type": "number", "exclusiveMinimum": 0}, "type": {"type": "string", "enum": ["dash", "dot", "dash_dot", "dash_dot_dot"]}},
        },
        "fill": {
            "description": "KiCad's fill, written only where there is one: outline (the stroke colour), background (the sheet's body colour) or a colour of its own.",
            "type": "object", "required": ["type"], "additionalProperties": False,
            "properties": {"type": {"type": "string", "enum": ["outline", "background", "color"]}, "color": {"type": "string", "pattern": "^#[0-9a-f]{6}$"}, "opacity": {"type": "number", "minimum": 0, "maximum": 1}},
        },
        "primitive": {
            "description": "One drawn element of a glyph, in the glyph's frame: millimetres, x right, y down, the anchor pin at 0,0.",
            "oneOf": [
                _primitive("polyline", {"points": {"$ref": "#/$defs/polyline"}}, ["points"], "Connected line segments."),
                _primitive("circle", {"center": _POINT, "radius": {"type": "number", "exclusiveMinimum": 0}}, ["center", "radius"], "A circle."),
                _primitive("arc", {"start": _POINT, "mid": _POINT, "end": _POINT}, ["start", "mid", "end"], "A circular arc through three points, as KiCad states it."),
                _primitive("rectangle", {"start": _POINT, "end": _POINT}, ["start", "end"], "An axis-aligned rectangle by two opposite corners."),
                _primitive("text", {"text": {"type": "string", "minLength": 1}, "at": _POINT, "size": {"type": "number", "exclusiveMinimum": 0},
                                    "rotation": {"type": "number"}, "justify": {"type": "string", "pattern": "^(left|right|top|bottom)( (left|right|top|bottom))?$"}},
                           ["text", "at", "size"], "Fixed text that is part of the picture (the H of a hand-thrown switch). A field shown through the symbol is not a primitive: the Layout Data Model File carries the field."),
            ],
        },
        "glyph": {
            "description": "One picture, stated once: its ports (every pin, by name, in the glyph's frame; the anchor pin is 0,0) and its shape. The shape is a list and the canonical form sorts it: drawing order is not a fact.",
            "type": "object", "required": ["ports", "shape"], "additionalProperties": False,
            "properties": {
                "ports": {"type": "object", "additionalProperties": _POINT},
                "shape": {"type": "array", "items": {"$ref": "#/$defs/primitive"}},
            },
        },
        "glyphs": {
            "description": "layout.glyphs: every glyph any interlocking's geometry names, by glyph key; nothing the layout does not draw.",
            "type": "object", "propertyNames": {"pattern": _GLYPH_KEY}, "additionalProperties": {"$ref": "#/$defs/glyph"},
        },
        "geometry": {
            "description": "interlockings.<name>.geometry.",
            "type": "object", "additionalProperties": False,
            "properties": {
                "appliances": {"type": "object", "additionalProperties": {"$ref": "#/$defs/placement"}},
                "houses": {"type": "object", "additionalProperties": {"$ref": "#/$defs/placement"}},
                "mileposts": {
                    "description": "Milepost anchors by milepost (ADR 0004 D7: the Value is the milepost, so it is the marker's name). Luchessa draws two; Sargent none.",
                    "type": "object", "propertyNames": {"pattern": "^\\d+(\\.\\d+)?$"}, "additionalProperties": {"$ref": "#/$defs/placement"},
                },
                "track": {"type": "array", "items": {"$ref": "#/$defs/track"}},
                "markers": {"type": "array", "items": {"$ref": "#/$defs/marker"}},
            },
        },
    },
    "type": "object", "additionalProperties": False, "required": ["geometry", "glyphs"],
    "properties": {"geometry": {"$ref": "#/$defs/geometry"}, "glyphs": {"$ref": "#/$defs/glyphs"}},
}


# ---------------------------------------------------------------------------------------------------------------
# Reading the sheet: placements, wires, junctions (jBOM's loader; the compiler piece will do this in kicad_services)
# ---------------------------------------------------------------------------------------------------------------
def kids(node, tag):
    return [x for x in node[1:] if isinstance(x, list) and x and x[0] == Symbol(tag)]


def first(node, tag):
    k = kids(node, tag)
    return k[0] if k else None


def read_sheet(path: Path):
    root = load_kicad_file(path)
    symbols = {}
    for s in kids(root, "symbol"):
        props = {str(p[1]): str(p[2]) for p in kids(s, "property")}
        at = first(s, "at")
        mirror = first(s, "mirror")
        lib_id = str(first(s, "lib_id")[1])
        symbols[props.get("Reference", "")] = {
            "lib_id": lib_id, "lib": lib_id.split(":")[1],
            "x": float(at[1]), "y": float(at[2]), "rotation": int(float(at[3])) if len(at) > 3 else 0,
            "mirror": str(mirror[1]) if mirror else "",
            "fields": props,
        }
    wires = [tuple((float(p[1]), float(p[2])) for p in kids(first(w, "pts"), "xy")) for w in kids(root, "wire")]
    junctions = {(float(first(j, "at")[1]), float(first(j, "at")[2])) for j in kids(root, "junction")}
    return symbols, wires, junctions


# ---------------------------------------------------------------------------------------------------------------
# Reading the library: each glyph's pins and shape, in KiCad's library frame (x right, y up, KiCad's origin)
# ---------------------------------------------------------------------------------------------------------------
def _xy(node) -> tuple[float, float]:
    return float(node[1]), float(node[2])


def _style(item) -> dict:
    """KiCad's stroke and fill, written only where they are not the default (ADR 0010 §4.9)."""
    out = {}
    st = first(item, "stroke")
    if st:
        s = {}
        w, t = first(st, "width"), first(st, "type")
        if w and float(w[1]) > 0:                      # KiCad's 0 is "the default, context dependent"
            s["width"] = float(w[1])
        if t and str(t[1]) not in ("default", "solid"):
            s["type"] = str(t[1])
        if s:
            out["stroke"] = s
    fl = first(item, "fill")
    if fl:
        t = first(fl, "type")
        if t and str(t[1]) != "none":
            f = {"type": str(t[1])}
            c = first(fl, "color")
            if c and str(t[1]) == "color":
                r, g, b, a = (float(v) for v in c[1:5])
                f["color"] = "#%02x%02x%02x" % (int(r), int(g), int(b))
                if a != 1:
                    f["opacity"] = a
            out["fill"] = f
    return out


def read_library(path: Path) -> dict[str, dict]:
    """Each symbol's pins by name and its drawn primitives, in the library frame (y up, KiCad's origin)."""
    root = load_kicad_file(path)
    out: dict[str, dict] = {}
    for sym in kids(root, "symbol"):
        pins: dict[str, tuple[float, float]] = {}
        shape: list[dict] = []
        for unit in kids(sym, "symbol"):
            for pin in kids(unit, "pin"):
                at = first(pin, "at")
                x, y = _xy(at)
                pins[str(first(pin, "name")[1])] = (x, y)
                length = float(first(pin, "length")[1]) if first(pin, "length") else 0.0
                hidden = first(pin, "hide") is not None and str(first(pin, "hide")[1]) == "yes"
                if length > 0 and not hidden:            # a pin's line is part of the picture
                    a = math.radians(float(at[3]) if len(at) > 3 else 0.0)
                    shape.append({"type": "polyline", "points": [(x, y), (x + length * math.cos(a), y + length * math.sin(a))]})
            for item in unit[1:]:
                if not (isinstance(item, list) and item and isinstance(item[0], Symbol)):
                    continue
                t = str(item[0])
                if t == "polyline":
                    shape.append({"type": t, "points": [_xy(p) for p in kids(first(item, "pts"), "xy")], **_style(item)})
                elif t == "circle":
                    shape.append({"type": t, "center": _xy(first(item, "center")), "radius": float(first(item, "radius")[1]), **_style(item)})
                elif t == "arc":
                    shape.append({"type": t, "start": _xy(first(item, "start")), "mid": _xy(first(item, "mid")), "end": _xy(first(item, "end")), **_style(item)})
                elif t == "rectangle":
                    shape.append({"type": t, "start": _xy(first(item, "start")), "end": _xy(first(item, "end")), **_style(item)})
                elif t == "text":
                    at = first(item, "at")
                    effects = first(item, "effects")
                    font = first(effects, "font") if effects else None
                    size = float(first(font, "size")[1]) if font and first(font, "size") else 1.27
                    prim = {"type": t, "text": str(item[1]), "at": _xy(at), "size": size}
                    if len(at) > 3 and float(at[3]):
                        prim["rotation"] = float(at[3])
                    if effects and first(effects, "justify"):
                        prim["justify"] = " ".join(str(v) for v in first(effects, "justify")[1:])
                    shape.append(prim)
        out[str(sym[1])] = {"pins": pins, "shape": shape}
    return out


def anchor_of(pins: dict[str, tuple[float, float]]) -> tuple[float, float]:
    """The glyph's origin in the Layout Data Model File: its bottom-left pin, lowest first, then leftmost (owner, 2026-10-24).
    In the library frame y is up, so lowest is least y. A glyph with no pin keeps KiCad's origin."""
    if not pins:
        return (0.0, 0.0)
    return min(pins.values(), key=lambda p: (p[1], p[0]))


def glyph_frame(entry: dict) -> dict:
    """The library's glyph re-stated in the file's frame: anchor pin at 0,0, x right, y down, KiCad's own numbers."""
    ax, ay = anchor_of(entry["pins"])

    def pt(p):
        return {"x": round(p[0] - ax, 4) + 0.0, "y": round(-(p[1] - ay), 4) + 0.0}

    ports = {name: pt(p) for name, p in entry["pins"].items()}
    shape = []
    for prim in entry["shape"]:
        q = dict(prim)
        if prim["type"] == "polyline":
            q["points"] = " ".join(f"{pt(p)['x']},{pt(p)['y']}" for p in prim["points"])
        elif prim["type"] == "circle":
            q["center"] = pt(prim["center"])
        elif prim["type"] == "arc":
            q["start"], q["mid"], q["end"] = pt(prim["start"]), pt(prim["mid"]), pt(prim["end"])
        elif prim["type"] == "rectangle":
            q["start"], q["end"] = pt(prim["start"]), pt(prim["end"])
        elif prim["type"] == "text":
            q["at"] = pt(prim["at"])
        shape.append(q)
    return {"ports": ports, "shape": shape}


def place(sym, local: tuple[float, float]) -> tuple[float, float]:
    """KiCad's own transform, library frame (y up) to page (y down): mirror, rotate counter-clockwise, translate.
    Used to find where KiCad put each pin; the file's transform is ``page_of`` below, and build() asserts they agree."""
    lx, ly = local
    if sym["mirror"] == "y":
        lx = -lx
    if sym["mirror"] == "x":
        ly = -ly
    a = math.radians(sym["rotation"])
    rx = lx * math.cos(a) - ly * math.sin(a)
    ry = lx * math.sin(a) + ly * math.cos(a)
    return round(sym["x"] + rx, 2), round(sym["y"] - ry, 2)


def page_of(pl: dict, local: tuple[float, float]) -> tuple[float, float]:
    """The placement transform of ADR 0010 §4.3, all in the file's frame (y down): mirror the glyph-local point
    (mirror y negates x, mirror x negates y), turn it counter-clockwise as seen on the page by ``rotation``, and
    add ``at``. Counter-clockwise on a y-down page is x' = x cos + y sin, y' = -x sin + y cos."""
    x, y = local
    if pl.get("mirror") == "y":
        x = -x
    if pl.get("mirror") == "x":
        y = -y
    a = math.radians(pl.get("rotation", 0))
    return pl["at"]["x"] + x * math.cos(a) + y * math.sin(a), pl["at"]["y"] - x * math.sin(a) + y * math.cos(a)


# ---------------------------------------------------------------------------------------------------------------
# Building the geometry object
# ---------------------------------------------------------------------------------------------------------------
def chain(wires, breaks: set) -> list[list[tuple[float, float]]]:
    """Join wire segments end to end into polylines, breaking at the given points (ports), merging collinear runs."""
    segs = [list(w) for w in wires]
    polylines = []
    while segs:
        line = segs.pop()
        grown = True
        while grown:
            grown = False
            for s in list(segs):
                for end, other in ((line[-1], line[0]), (line[0], line[-1])):
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
        # merge collinear vertices
        out = [line[0]]
        for p, q in zip(line[1:-1], line[2:]):
            a, b = out[-1], p
            if (b[0] - a[0]) * (q[1] - b[1]) != (b[1] - a[1]) * (q[0] - b[0]):
                out.append(p)
        out.append(line[-1])
        polylines.append(out)
    return polylines


def fresh_netlist(project_root: Path):
    """Export the project's netlist to a temporary file; the caller deletes it. Never a saved copy (owner, 2026-10-24)."""
    from kicad_services.netlist_reader import KicadCliNetlistExporter

    return KicadCliNetlistExporter().export(project_root / "SPCoast" / "SPCoast.kicad_sch")


def build(railroad: Path, netlist: Path | None = None):
    sheet = railroad / "SPCoast" / f"{INTERLOCKING}.kicad_sch"
    symbols, wires, junctions = read_sheet(sheet)
    library = read_library(railroad / "symbols" / f"{GLYPH_LIBRARY}.kicad_sym")
    pins_by_lib = {name: e["pins"] for name, e in library.items()}
    if netlist is None:
        tmp = fresh_netlist(railroad)
        try:
            src = from_netlist(tmp)
        finally:
            tmp.unlink(missing_ok=True)
    else:
        src = from_netlist(netlist)
    netsyms = {r: s for r, s in src.symbols.items() if s.sheet.rstrip("/").endswith(INTERLOCKING)}

    trackplan = {r: s for r, s in symbols.items() if s["fields"].get("Role") in TRACKPLAN_ROLES}
    houses = {r: s for r, s in symbols.items() if s["fields"].get("Kind") == "CONTROL_POINT"}
    extent = list(trackplan.values()) + list(houses.values())
    ox = min(s["x"] for s in extent)
    oy = min(s["y"] for s in extent)

    def norm(xy):
        return {"x": round(xy[0] - ox, 2) + 0.0, "y": round(xy[1] - oy, 2) + 0.0}

    glyphs: dict[str, dict] = {}

    def placement(s):
        """at is where the glyph's anchor pin landed on the page; the glyph is named, and stated once in glyphs."""
        entry = library[s["lib"]]
        p = {"at": norm(place(s, anchor_of(entry["pins"]))), "glyph": s["lib_id"]}
        if s["rotation"]:
            p["rotation"] = s["rotation"]
        if s["mirror"]:
            p["mirror"] = s["mirror"]
        if s["lib_id"] not in glyphs:
            glyphs[s["lib_id"]] = glyph_frame(entry)
        # the file's transform over the file's glyph lands every pin where KiCad's transform over the library did
        for pin, local in entry["pins"].items():
            port = glyphs[s["lib_id"]]["ports"][pin]
            x, y = page_of(p, (port["x"], port["y"]))
            assert (round(x, 2), round(y, 2)) == tuple(norm(place(s, local)).values()), (s["lib_id"], pin)
        return p

    def name_of(ref):
        return netsyms[ref].value  # Name = ${Value} on every trackplan appliance (owner, 2026-10-24)

    # which circuit is each track net
    def circuit_of_net(net):
        for p in net.pins:
            s = netsyms.get(p.ref)
            if s and s.fields.get("Appliance") == "track_circuit":
                v = s.value
                return v if ":" in v else f"{INTERLOCKING}:{v}"
        # Picture-level approximation of the OS rule (the semantics piece owns it, handoff-compiler-semantics step 2):
        # a powered or locked switch's C, N and R nets are its OS circuit, <switch>T1 unless TC says otherwise; a
        # hand-thrown switch beyond END CTC has no circuit, so its legs are dark track.
        for p in net.pins:
            s = netsyms.get(p.ref)
            if s and s.fields.get("Appliance") == "switch" and s.fields.get("Style") in ("powered", "lock", "dual") and p.pin in ("C", "N", "R"):
                tc = s.fields.get("TC", "").replace("${VALUE}", s.value) or f"{s.value}T1"
                return f"{INTERLOCKING}:{tc}"
        return None

    # ports: every track pin of every trackplan symbol, on the page
    port_at: dict[tuple[float, float], tuple[str, str]] = {}
    for ref, s in trackplan.items():
        for pin, local in pins_by_lib.get(s["lib"], {}).items():
            port_at[place(s, local)] = (ref, pin)
    net_of_port = {(p.ref, p.pin): n for n in src.nets for p in n.pins}

    appliances, masts = {}, {}
    for ref, s in trackplan.items():
        f = s["fields"]
        if f.get("Role") != "APPLIANCE":
            continue
        if f.get("Appliance") == "head":
            continue
        appliances[name_of(ref)] = placement(s)
        if f.get("Appliance") == "mast":
            masts[ref] = name_of(ref)
    for ref, s in trackplan.items():
        if s["fields"].get("Appliance") == "head":
            net = net_of_port.get((ref, "M"))
            mast_ref = next(p.ref for p in net.pins if p.ref != ref)
            appliances[masts[mast_ref]].setdefault("heads", {})[name_of(ref)] = placement(s)

    house_geom = {s["fields"]["CP Name"]: placement(s) for s in houses.values()}

    track = []
    # A run of track breaks where track passes through or ends at a symbol (a joint, a switch, END CTC, NextCP, a
    # bumper), not where a lamp, a circuit marker or a sign merely touches it.
    through = {xy for xy, (ref, _pin) in port_at.items()
               if trackplan[ref]["fields"].get("Role") == "TRACK" or trackplan[ref]["fields"].get("Appliance") == "switch"}
    track_wires = [w for w in wires if any(p in port_at for p in w)]
    grown = True
    while grown:  # a wire joined end to end to a track wire is track too (I/O bus wires never are)
        grown = False
        ends = {p for w in track_wires for p in w}
        for w in wires:
            if w not in track_wires and any(p in ends for p in w):
                track_wires.append(w); grown = True
    for line in chain(track_wires, through):
        ends = [port_at.get(line[0]), port_at.get(line[-1])]
        net = next((net_of_port[e] for e in ends if e and e in net_of_port), None)
        row = {"points": " ".join(f"{norm(p)['x']},{norm(p)['y']}" for p in line)}
        circuit = circuit_of_net(net) if net else None
        if circuit:
            row["circuit"] = circuit
        for key, e in zip(("from", "to"), ends):
            if e and trackplan[e[0]]["fields"].get("Role") == "APPLIANCE" and trackplan[e[0]]["fields"].get("Appliance") == "switch":
                row[key] = f"{INTERLOCKING}:{name_of(e[0])}.{e[1]}"
        track.append(row)

    markers, mileposts = [], {}
    for ref, s in trackplan.items():
        if s["fields"].get("Role") == "APPLIANCE":
            continue
        if s["fields"].get("Kind") == "MILEPOST":
            mileposts[s["fields"]["Value"]] = placement(s)
            continue
        row = {"kind": s["fields"]["Kind"], **placement(s)}
        circuits = {}
        for pin in pins_by_lib.get(s["lib"], {}):
            net = net_of_port.get((ref, pin))
            c = circuit_of_net(net) if net else None
            if c:
                circuits[pin] = c
        if circuits:
            row["circuits"] = circuits
        markers.append(row)

    geometry = {"appliances": appliances, "houses": house_geom, "track": track, "markers": markers}
    if mileposts:
        geometry["mileposts"] = mileposts
    example = {"geometry": geometry, "glyphs": glyphs}
    jsonschema.validate(example, GEOMETRY_SCHEMA)
    return example, (ox, oy)


# ---------------------------------------------------------------------------------------------------------------
# Pictures. The model board, the route finder and the packet draw the written glyphs; the thinline draws none.
# ---------------------------------------------------------------------------------------------------------------
S = 8.0  # px per mm


def px(p):
    return p["x"] * S, p["y"] * S


def pts(points: str):
    return [tuple(float(v) for v in xy.split(",")) for xy in points.split(" ")]


def local_to_page(pl, local):
    """A placement's transform (page_of) scaled to pixels."""
    x, y = page_of(pl, local)
    return x * S, y * S


STYLE = """
  text { font-family: Helvetica, Arial, sans-serif; }
  .t { font-size: 12px; fill: #222; }
  .s { font-size: 10px; fill: #555; }
  .h { font-size: 15px; font-weight: bold; fill: #111; }
  .track { stroke: #222; stroke-width: 2.5; fill: none; }
  .dark { stroke: #999; stroke-width: 2.5; stroke-dasharray: 5 4; fill: none; }
  .frame { stroke: #c33; stroke-width: 1; fill: none; stroke-dasharray: 3 3; }
  .glyph { stroke: #06c; stroke-width: 1.5; fill: none; }
  .port { fill: #06c; }
  .house { stroke: #a60; stroke-width: 1.5; fill: #fff3d6; }
  .marker { stroke: #393; stroke-width: 1.5; fill: #fff; }
  .mk { font-size: 9px; fill: #393; font-weight: bold; }
  .lamp { stroke: #222; stroke-width: 1.2; fill: #fff; }
  .route { stroke: #d22; stroke-width: 7; fill: none; opacity: .5; stroke-linecap: round; stroke-linejoin: round; }
  .panel { stroke: #bbb; fill: #fff; }
  .g { stroke: #222; stroke-width: 1.2; fill: none; stroke-linecap: round; stroke-linejoin: round; }
  .gf { stroke: #aaa; stroke-width: 1; fill: none; stroke-linecap: round; stroke-linejoin: round; }
"""


def svg(width, height, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" viewBox="0 0 {width:.0f} {height:.0f}">'
            f'<title>{title}</title><style>{STYLE}</style><rect width="100%" height="100%" fill="white"/>{body}</svg>')


def poly(cls, points_px):
    return f'<polyline class="{cls}" points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in points_px)}"/>'


def arc_points(start, mid, end, n=16):
    """Points along KiCad's three-point arc, in the glyph's frame."""
    (x1, y1), (x2, y2), (x3, y3) = start, mid, end
    d = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    if abs(d) < 1e-9:
        return [start, mid, end]
    ux = ((x1 ** 2 + y1 ** 2) * (y2 - y3) + (x2 ** 2 + y2 ** 2) * (y3 - y1) + (x3 ** 2 + y3 ** 2) * (y1 - y2)) / d
    uy = ((x1 ** 2 + y1 ** 2) * (x3 - x2) + (x2 ** 2 + y2 ** 2) * (x1 - x3) + (x3 ** 2 + y3 ** 2) * (x2 - x1)) / d
    r = math.hypot(x1 - ux, y1 - uy)
    a1, a2, a3 = (math.atan2(y - uy, x - ux) for x, y in (start, mid, end))
    # sweep from a1 to a3 passing through a2
    def ccw(a, b):
        return (b - a) % (2 * math.pi)
    sweep = ccw(a1, a3) if ccw(a1, a2) <= ccw(a1, a3) else -ccw(a3, a1)
    return [(ux + r * math.cos(a1 + sweep * i / n), uy + r * math.sin(a1 + sweep * i / n)) for i in range(n + 1)]


def draw_glyph(pl, glyph, cls="g", colour=True) -> str:
    """One placement's glyph on the page: each primitive through the placement transform, styled as written."""
    out = []
    for prim in glyph["shape"]:
        style = ""
        st, fl = prim.get("stroke", {}), prim.get("fill")
        if st.get("width"):
            style += f"stroke-width:{st['width'] * S:.1f};"
        if st.get("type"):
            style += {"dash": "stroke-dasharray:6 3;", "dot": "stroke-dasharray:1.5 3;", "dash_dot": "stroke-dasharray:6 3 1.5 3;", "dash_dot_dot": "stroke-dasharray:6 3 1.5 3 1.5 3;"}[st["type"]]
        if fl and colour:
            fill = fl.get("color", "#888") if fl["type"] == "color" else ("#ddd" if fl["type"] == "background" else "#222")
            style += f"fill:{fill};" + (f"fill-opacity:{fl['opacity']};" if "opacity" in fl else "")
        attr = f' style="{style}"' if style else ""
        t = prim["type"]
        if t == "polyline":
            out.append(f'<polyline class="{cls}" points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in (local_to_page(pl, p) for p in pts(prim["points"])))}"{attr}/>')
        elif t == "circle":
            cx, cy = local_to_page(pl, (prim["center"]["x"], prim["center"]["y"]))
            out.append(f'<circle class="{cls}" cx="{cx:.1f}" cy="{cy:.1f}" r="{prim["radius"] * S:.1f}"{attr}/>')
        elif t == "arc":
            ps = arc_points(*((p["x"], p["y"]) for p in (prim["start"], prim["mid"], prim["end"])))
            out.append(f'<polyline class="{cls}" points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in (local_to_page(pl, p) for p in ps))}"{attr}/>')
        elif t == "rectangle":
            a, b = prim["start"], prim["end"]
            corners = [(a["x"], a["y"]), (b["x"], a["y"]), (b["x"], b["y"]), (a["x"], b["y"]), (a["x"], a["y"])]
            out.append(f'<polyline class="{cls}" points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in (local_to_page(pl, p) for p in corners))}"{attr}/>')
        elif t == "text":
            x, y = local_to_page(pl, (prim["at"]["x"], prim["at"]["y"]))
            anchor = "start" if "left" in prim.get("justify", "") else "end" if "right" in prim.get("justify", "") else "middle"
            out.append(f'<text x="{x:.1f}" y="{y + prim["size"] * S * 0.35:.1f}" text-anchor="{anchor}" style="font-size:{prim["size"] * S:.1f}px;fill:#222;stroke:none">{prim["text"]}</text>')
    return "".join(out)


def every_placement(g):
    """(name, placement) for everything in a geometry object that names a glyph."""
    for name, a in g["appliances"].items():
        yield name, a
        for letter, hp in a.get("heads", {}).items():
            yield f"{name}{letter}", hp
    for name, h in g["houses"].items():
        yield name, h
    for name, m in g.get("mileposts", {}).items():
        yield name, m
    for m in g["markers"]:
        yield m["kind"], m


def extent(g):
    xs = [p[0] for t in g["track"] for p in pts(t["points"])] + [a["at"]["x"] for a in g["appliances"].values()] + [h["at"]["x"] for h in g["houses"].values()]
    ys = [p[1] for t in g["track"] for p in pts(t["points"])] + [a["at"]["y"] for a in g["appliances"].values()] + [h["at"]["y"] for h in g["houses"].values()]
    return max(xs), max(ys)


def draw_facts(ex, origin) -> str:
    g, glyphs = ex["geometry"], ex["glyphs"]
    w, h = extent(g)
    b = ['<g transform="translate(40,90)">']
    b.append('<text class="h" x="0" y="-66">Sargent: the geometry facts, as the Layout Data Model File would hold them (docs/adr/0010/sargent.geometry.json)</text>')
    b.append(f'<text class="s" x="0" y="-48">Frame: millimetres from the top-left of the drawn extent, x right, y down. The KiCad sheet origin was {origin[0]}, {origin[1]} mm away and is not written.</text>')
    dark = " Grey dashes: a track row of no circuit, ending at a switch port." if any("circuit" not in t for t in g["track"]) else ""
    b.append(f'<text class="s" x="0" y="-34">Blue dot: a placement\'s at, the glyph\'s bottom-left pin (name, r = rotation, m = mirror). Blue ring: a head on its mast. Black line: a track row with its circuit.{dark}</text>')
    b.append(f'<text class="s" x="0" y="-20">Green diamond: a marker, numbered in the table. Grey: the {len(glyphs)} written glyphs, each stated once in glyphs{{}} and drawn here through the placement transform. Dashed red: the extent.</text>')
    b.append(f'<rect class="frame" x="0" y="0" width="{w*S:.0f}" height="{h*S:.0f}"/>')
    b.append('<text class="s" x="2" y="-4">0,0</text>')
    for _name, pl in every_placement(g):
        b.append(draw_glyph(pl, glyphs[pl["glyph"]], "gf", colour=False))
    for t in g["track"]:
        cls = "track" if "circuit" in t else "dark"
        p = pts(t["points"])
        b.append(poly(cls, [(x * S, y * S) for x, y in p]))
        mx, my = (p[0][0] + p[-1][0]) / 2 * S, (p[0][1] + p[-1][1]) / 2 * S
        label = t.get("circuit", "no circuit")
        if "to" in t:
            label += f" → {t['to']}"
        if "from" in t:
            label = f"{t['from']} → " + label
        b.append(f'<text class="s" x="{mx:.0f}" y="{my+14:.0f}" text-anchor="middle">{label}</text>')
    for name, hp in g["houses"].items():
        x, y = px(hp["at"])
        b.append(f'<circle class="port" cx="{x:.1f}" cy="{y:.1f}" r="3.5"/><text class="t" x="{x+6}" y="{y+4}">house {name}</text>')
    for name, a in g["appliances"].items():
        x, y = px(a["at"])
        b.append(f'<circle class="port" cx="{x:.1f}" cy="{y:.1f}" r="3.5"/>')
        note = name + (f" r{a['rotation']}" if a.get("rotation") else "") + (f" m{a['mirror']}" if a.get("mirror") else "")
        b.append(f'<text class="t" x="{x+5:.0f}" y="{y-8:.0f}">{note}</text>')
        for letter, hp in a.get("heads", {}).items():
            hx, hy = px(hp["at"])
            b.append(f'<circle class="glyph" cx="{hx:.1f}" cy="{hy:.1f}" r="4.5"/>')
    table, seen = [], {}
    for i, m in enumerate(g["markers"], 1):
        x, y = px(m["at"])
        k = seen.get((x, y), 0); seen[(x, y)] = k + 1          # two markers may share an anchor (a sign on a joint)
        b.append(f'<rect class="marker" x="{x-5}" y="{y-5}" width="10" height="10" transform="rotate(45 {x} {y})"/>')
        b.append(f'<text class="mk" x="{x+7+k*12:.0f}" y="{y+13:.0f}">{i}</text>')
        c = ", ".join(f"{k} {v}" for k, v in m.get("circuits", {}).items())
        orient = (f" r{m['rotation']}" if m.get("rotation") else "") + (f" m{m['mirror']}" if m.get("mirror") else "")
        table.append(f'<text class="s" x="0" y="{i*15}"><tspan class="mk">{i}</tspan>  {m["kind"]}{orient} at {m["at"]["x"]}, {m["at"]["y"]}  ({m["glyph"].split(":")[1]})  —  {c}</text>')
    b.append(f'<g transform="translate(0,{h*S+36:.0f})"><text class="t" x="0" y="0">markers</text>{"".join(table)}</g>')
    gl = [f'<text class="s" x="0" y="{i*15}">{k}: ports {", ".join(f"{n} {p["x"]},{p["y"]}" for n, p in v["ports"].items())}; {len(v["shape"])} primitives</text>'
          for i, (k, v) in enumerate(sorted(glyphs.items()), 1)]
    b.append(f'<g transform="translate(540,{h*S+36:.0f})"><text class="t" x="0" y="0">glyphs (anchor pin at 0,0; y down)</text>{"".join(gl)}</g>')
    b.append("</g>")
    rows = max(len(g["markers"]), len(glyphs))
    return svg(w * S + 80, h * S + 90 + 60 + 15 * rows + 20, "".join(b), "ADR 0010: Sargent geometry facts")


def draw_views(ex) -> str:
    """Four reductions of one object. Each reduction is sketched here by hand; the real one is the view's logic."""
    g, glyphs = ex["geometry"], ex["glyphs"]
    main = {"Corporal:2NAT", "Sargent:1SAT", "Sargent:835T1", "Sargent:1NAT"}  # the circuits under a Rule 261 sign
    s = 0.6  # the panel scale
    pw, ph = 760, 340

    def port(name, pin):
        pl = g["appliances"][name]
        p = glyphs[pl["glyph"]]["ports"][pin]
        return local_to_page(pl, (p["x"], p["y"]))

    def thin_mast(name, a):
        """The thinline's own mast: a stroke and a ring per head. The thinline draws no glyph (ADR 0010 §5)."""
        mx, my = px(a["at"])
        up = 1 if a.get("rotation") == 180 else -1      # a mast turned 180 stands below its track
        side = 1 if a.get("rotation") == 180 else -1
        out = [f'<line class="glyph" x1="{mx:.1f}" y1="{my:.1f}" x2="{mx:.1f}" y2="{my+up*12:.1f}"/>']
        for i, _ in enumerate(a["heads"]):
            out.append(f'<circle class="glyph" cx="{mx+side*(9+i*11):.1f}" cy="{my+up*12:.1f}" r="5"/>')
        out.append(f'<text class="s" x="{mx:.0f}" y="{my+up*26+(6 if up>0 else 0):.0f}" text-anchor="middle">{name}</text>')
        return "".join(out)

    def thin_lamp(name):
        lx, ly = px(g["appliances"][name]["at"])
        return f'<circle class="lamp" cx="{lx:.1f}" cy="{ly:.1f}" r="5"/><text class="s" x="{lx:.0f}" y="{ly-9:.0f}" text-anchor="middle">{name}</text>'

    def nextcp_labels():
        out = []
        for m in g["markers"]:
            if m["kind"] == "NEXT_CP":
                x, y = px(m["at"])
                dest = m["circuits"]["To"].split(":")[0] if not m["circuits"]["To"].startswith("Sargent") else "Watsonville"
                anchor = "end" if x < 100 else "start"
                out.append(f'<text class="t" x="{x + (-8 if x < 100 else 8):.0f}" y="{y+4:.0f}" text-anchor="{anchor}">to {dest}</text>')
        return "".join(out)

    def board_full(route=None):
        """The model board: every row and every written glyph at its placement, names from the keys."""
        b = []
        for t in g["track"]:
            b.append(poly("track" if "circuit" in t else "dark", [(x * S, y * S) for x, y in pts(t["points"])]))
        for _name, pl in every_placement(g):
            b.append(draw_glyph(pl, glyphs[pl["glyph"]], "g"))
        if route:
            for seg in route:
                b.append(poly("route", seg))
        for name, a in g["appliances"].items():
            x, y = px(a["at"])
            below = a.get("rotation") == 180 or "heads" not in a
            b.append(f'<text class="s" x="{x:.0f}" y="{y + (22 if below else -14):.0f}" text-anchor="middle">{name}</text>')
        hx, hy = px(g["houses"]["Sargent"]["at"])
        b.append(f'<text class="s" x="{hx:.0f}" y="{hy-20:.0f}" text-anchor="middle">CP Sargent</text>')
        b.append(nextcp_labels())
        return "".join(b)

    def thinline():
        # one continuous line from NextCP to NextCP: the main rows and the switch's C–N leg, joints closed
        xs = [p[0] * S for t in g["track"] if t.get("circuit") in main for p in pts(t["points"])]
        y = g["appliances"]["1SAT"]["at"]["y"] * S
        b = [poly("track", [(min(xs), y), (max(xs), y)])]
        for name in ("Corporal:2NAT", "1SAT", "1NAT"):
            b.append(thin_lamp(name))
        for name, a in g["appliances"].items():
            if "heads" in a and name != "836SB":           # 836SB governs the siding; it leaves with it
                b.append(thin_mast(name, a))
        b.append(nextcp_labels())
        return "".join(b)

    # the route finder's overlay: 1NAT, 835 reverse, 2SAT, painted over the rows and the switch's own diverging leg
    c, r = port("835", "C"), port("835", "R")
    sw = g["appliances"]["835"]
    leg = next((pts(p["points"]) for p in glyphs[sw["glyph"]]["shape"] if p["type"] == "polyline"
                and any((q["x"], q["y"]) == (x, y) for q in [glyphs[sw["glyph"]]["ports"]["R"]] for x, y in pts(p["points"]))), None)
    leg_px = [local_to_page(sw, p) for p in leg] if leg else [c, r]
    if leg_px[0] != r and leg_px[-1] == r:
        pass
    elif leg_px[0] == r:
        leg_px = leg_px[::-1]
    nat = [p for t in g["track"] if t.get("circuit") == "Sargent:1NAT" for p in pts(t["points"])]
    sat2 = [p for t in g["track"] if t.get("circuit") == "Sargent:2SAT" for p in pts(t["points"])]
    route = [[(max(x for x, _ in nat) * S, c[1]), c], [c, *leg_px], [r, (min(x for x, _ in sat2) * S, r[1])]]

    docs_rows = "".join(f'<text class="s" x="0" y="{18+i*13}">{n} at {a["at"]["x"]}, {a["at"]["y"]}{" r"+str(a["rotation"]) if a.get("rotation") else ""}{" m"+a["mirror"] if a.get("mirror") else ""}  {a["glyph"].split(":")[1]}</text>'
                        for i, (n, a) in enumerate(g["appliances"].items()))
    panels = [
        ("1. Thinline: the main track as one line, no glyphs",
         "keeps: rows whose circuit stands under a Rule 261 sign, closed into one line; the circuits' lamps; the masts that govern it; the NextCP ends. drops: the siding (Rule 105) and its mast, the industries, the switch, every joint, the house, every glyph.",
         f'<g transform="translate(70,100) scale({s})">{thinline()}</g>'),
        ("2. Model board: every placement, drawn with the written glyphs",
         f"keeps: every row; every placement drawn with its glyph from glyphs{{}} ({len(glyphs)} here) through the placement transform, with the drawn strokes and fills; names from the keys. styles: the board's for track and labels only.",
         f'<g transform="translate(70,100) scale({s})">{board_full()}</g>'),
        ("3. Route finder: the board plus an evaluated route",
         "836NB: 1NAT, 835 reverse, 2SAT, laid over the same rows and the switch glyph's own diverging leg (its R port). The route is the evaluator's (view §5); geometry only says where to paint it.",
         f'<g transform="translate(70,100) scale({s})">{board_full(route)}</g>'),
        ("4. Documentation packet: the board at print scale beside its tables",
         "the picture generator's board, re-targeted to the Layout Data Model File, printed with the appliance, device and binding tables the packet already lists.",
         f'<g transform="translate(20,110) scale({s*0.6})">{board_full()}</g><g transform="translate(450,110)"><text class="t" x="0" y="0">appliances (placement excerpt)</text>{docs_rows}</g>'),
    ]
    body = []
    for i, (title, sub, content) in enumerate(panels):
        tx, ty = (i % 2) * (pw + 20) + 10, (i // 2) * (ph + 20) + 10
        subtitle = "".join(f'<text class="s" x="12" y="{42+j*13}">{line}</text>' for j, line in enumerate(textwrap.wrap(sub, 125)))
        body.append(f'<g transform="translate({tx},{ty})"><rect class="panel" width="{pw}" height="{ph}"/>'
                    f'<text class="h" x="12" y="24">{title}</text>{subtitle}{content}</g>')
    return svg(2 * pw + 40, 2 * ph + 40, "".join(body), "ADR 0010: the four views from one geometry object")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--railroad", type=Path, default=Path.home() / "Dropbox/KiCad/Railroad")
    ap.add_argument("--netlist", type=Path, default=None, help="read this netlist instead of exporting a fresh one with kicad-cli")
    ap.add_argument("--out", type=Path, default=HERE, help="write the four files here instead of beside the script")
    a = ap.parse_args(argv)
    example, origin = build(a.railroad, a.netlist)
    out = a.out
    (out / "geometry.schema.json").write_text(json.dumps(GEOMETRY_SCHEMA, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    text = layout_model.dumps(example)
    (out / "sargent.geometry.json").write_text(text, encoding="utf-8")
    assert layout_model.dumps(layout_model.loads(text)) == text, "not canonical"
    jsonschema.validate(layout_model.loads(text), GEOMETRY_SCHEMA)
    (out / "sargent-geometry.svg").write_text(draw_facts(example, origin), encoding="utf-8")
    (out / "four-views.svg").write_text(draw_views(example), encoding="utf-8")
    g = example["geometry"]
    print(f"wrote 4 files to {out}; origin was KiCad {origin}; {len(g['track'])} track rows, {len(g['markers'])} markers, "
          f"{len(g['appliances'])} appliances, {len(example['glyphs'])} glyphs, {sum(len(v['shape']) for v in example['glyphs'].values())} primitives")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
