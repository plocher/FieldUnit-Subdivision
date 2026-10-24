"""ADR 0010's worked example and pictures, generated from the Sargent trackplan sheet, never typed.

    uv run python docs/adr/0010/make_pictures.py [--railroad ~/Dropbox/KiCad/Railroad]

Writes, beside this script:

- ``geometry.schema.json``: the proposed ``$defs/geometry`` fragment for schema 3.1.0 (ADR 0010 §4).
- ``sargent.geometry.json``: Sargent's ``geometry`` object as the proposal would have the compiler write it, read
  from ``SPCoast/Sargent.kicad_sch`` (placements, wires, junctions) and ``SPCoast/production/SPCoast.net`` (which
  net is which circuit), normalised and in canonical form, validated against the fragment.
- ``sargent-geometry.svg``: the facts drawn: frame, polylines, placements, nothing styled.
- ``four-views.svg``: the four views the owner named, each derived from the same object.

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

# ---------------------------------------------------------------------------------------------------------------
# The proposed schema fragment (ADR 0010 §4). Coordinates are objects and polylines are strings because the
# canonical form sorts every list (ADR 0008 §4.8): a list's order never carries meaning.
# ---------------------------------------------------------------------------------------------------------------
GEOMETRY_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://spcoast.com/schemas/layout-model/v3.1.0-geometry.json",
    "title": "geometry (proposed for layout-model/v3.1.0, ADR 0010)",
    "description": "The drawing of one interlocking as a design fact: where each named thing sits and how the track runs, in the interlocking's own frame (millimetres from the top-left of its drawn extent, x right, y down). Joined to meaning by name only; never read for connectivity.",
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
        "placement": {
            "description": "Where a glyph sits: its origin, its turn (degrees, counter-clockwise as seen on the page, 0/90/180/270) and its mirror (x: top for bottom; y: left for right), applied mirror first. The glyph itself is the reader's.",
            "type": "object", "required": ["at"], "additionalProperties": False,
            "properties": {
                "at": {"$ref": "#/$defs/point"},
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
            "description": "One drawn run of track between two things: the circuit it belongs to (absent for dark track) and, where an end is an appliance's track port, that port by name (Sargent:835.R). An end at a joint or a marker is absent: the circuit's bounds are track's business.",
            "type": "object", "required": ["points"], "additionalProperties": False,
            "properties": {
                "points": {"$ref": "#/$defs/polyline"},
                "circuit": {"type": "string", "pattern": "^[^:/\\s][^:/]*:[^:/\\s][^:/]*$"},
                "from": {"type": "string", "pattern": "^[^:/\\s][^:/]*:[^:/\\s][^:/]*\\.[A-Za-z0-9_]+$"},
                "to": {"type": "string", "pattern": "^[^:/\\s][^:/]*:[^:/\\s][^:/]*\\.[A-Za-z0-9_]+$"},
            },
        },
        "marker": {
            "description": "A track symbol with no railroad name of its own (a joint, END CTC, NextCP, a milepost, a policy sign): its kind as the libraries spell it, its placement, and the circuit at each of its track pins, so a reader joins it to track by name.",
            "type": "object", "required": ["kind", "at"], "additionalProperties": False,
            "properties": {
                "kind": {"type": "string", "pattern": "^[A-Z][A-Z0-9_]*$"},
                "at": {"$ref": "#/$defs/point"},
                "rotation": {"type": "integer", "enum": [90, 180, 270]},
                "mirror": {"type": "string", "enum": ["x", "y"]},
                "circuits": {
                    "description": "The circuit at each track pin of the marker, by pin name; a pin on dark track is absent.",
                    "type": "object", "additionalProperties": {"type": "string", "pattern": "^[^:/\\s][^:/]*:[^:/\\s][^:/]*$"},
                },
            },
        },
    },
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
        symbols[props.get("Reference", "")] = {
            "lib": str(first(s, "lib_id")[1]).split(":")[1],
            "x": float(at[1]), "y": float(at[2]), "rotation": int(float(at[3])) if len(at) > 3 else 0,
            "mirror": str(mirror[1]) if mirror else "",
            "fields": props,
        }
    wires = [tuple((float(p[1]), float(p[2])) for p in kids(first(w, "pts"), "xy")) for w in kids(root, "wire")]
    junctions = {(float(first(j, "at")[1]), float(first(j, "at")[2])) for j in kids(root, "junction")}
    return symbols, wires, junctions


def read_library_pins(path: Path) -> dict[str, dict[str, tuple[float, float]]]:
    """Each trackplan symbol's pins by name, in glyph-local coordinates (x right, y up)."""
    root = load_kicad_file(path)
    out: dict[str, dict[str, tuple[float, float]]] = {}
    for sym in kids(root, "symbol"):
        name = str(sym[1])
        pins = {}
        for unit in kids(sym, "symbol"):
            for pin in kids(unit, "pin"):
                at = first(pin, "at")
                pins[str(first(pin, "name")[1])] = (float(at[1]), float(at[2]))
        out[name] = pins
    return out


def place(sym, local: tuple[float, float]) -> tuple[float, float]:
    """Glyph-local (y up) to page (y down): mirror, then rotate counter-clockwise on the page, then translate."""
    lx, ly = local
    if sym["mirror"] == "y":
        lx = -lx
    if sym["mirror"] == "x":
        ly = -ly
    a = math.radians(sym["rotation"])
    rx = lx * math.cos(a) - ly * math.sin(a)
    ry = lx * math.sin(a) + ly * math.cos(a)
    return round(sym["x"] + rx, 2), round(sym["y"] - ry, 2)


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


def build(railroad: Path, netlist: Path | None = None):
    sheet = railroad / "SPCoast" / f"{INTERLOCKING}.kicad_sch"
    symbols, wires, junctions = read_sheet(sheet)
    pins_by_lib = read_library_pins(railroad / "symbols" / "Railroad-Trackplan.kicad_sym")
    src = from_netlist(netlist or railroad / "SPCoast" / "production" / "SPCoast.net")
    netsyms = {r: s for r, s in src.symbols.items() if s.sheet.rstrip("/").endswith(INTERLOCKING)}

    trackplan = {r: s for r, s in symbols.items() if s["fields"].get("Role") in TRACKPLAN_ROLES}
    houses = {r: s for r, s in symbols.items() if s["fields"].get("Kind") == "CONTROL_POINT"}
    extent = list(trackplan.values()) + list(houses.values())
    ox = min(s["x"] for s in extent)
    oy = min(s["y"] for s in extent)

    def norm(xy):
        return {"x": round(xy[0] - ox, 2), "y": round(xy[1] - oy, 2)}

    def placement(s):
        p = {"at": norm((s["x"], s["y"]))}
        if s["rotation"]:
            p["rotation"] = s["rotation"]
        if s["mirror"]:
            p["mirror"] = s["mirror"]
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
    jsonschema.validate(geometry, GEOMETRY_SCHEMA)
    return geometry, (ox, oy)


# ---------------------------------------------------------------------------------------------------------------
# Pictures. The glyphs below are this script's own, as every view's are; the file carries none.
# ---------------------------------------------------------------------------------------------------------------
S = 8.0  # px per mm
SWITCH_PORTS = {"C": (-11.43, 0.0), "N": (17.78, 0.0), "R": (17.78, 16.51)}  # the Trackplan switch glyph, local, y up


def px(p):
    return p["x"] * S, p["y"] * S


def pts(points: str):
    return [tuple(float(v) for v in xy.split(",")) for xy in points.split(" ")]


def local_to_page(pl, local):
    """A placement's transform, as the schema fragment defines it: mirror, rotate counter-clockwise, translate."""
    lx, ly = local
    if pl.get("mirror") == "y":
        lx = -lx
    if pl.get("mirror") == "x":
        ly = -ly
    a = math.radians(pl.get("rotation", 0))
    rx = lx * math.cos(a) - ly * math.sin(a)
    ry = lx * math.sin(a) + ly * math.cos(a)
    return (pl["at"]["x"] + rx) * S, (pl["at"]["y"] - ry) * S


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
"""


def svg(width, height, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" viewBox="0 0 {width:.0f} {height:.0f}">'
            f'<title>{title}</title><style>{STYLE}</style><rect width="100%" height="100%" fill="white"/>{body}</svg>')


def poly(cls, points_px):
    return f'<polyline class="{cls}" points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in points_px)}"/>'


def extent(g):
    xs = [p[0] for t in g["track"] for p in pts(t["points"])] + [a["at"]["x"] for a in g["appliances"].values()] + [h["at"]["x"] for h in g["houses"].values()]
    ys = [p[1] for t in g["track"] for p in pts(t["points"])] + [a["at"]["y"] for a in g["appliances"].values()] + [h["at"]["y"] for h in g["houses"].values()]
    return max(xs), max(ys)


def draw_facts(g, origin) -> str:
    w, h = extent(g)
    b = ['<g transform="translate(40,90)">']
    b.append('<text class="h" x="0" y="-66">Sargent: the geometry facts, as the file would hold them (docs/adr/0010/sargent.geometry.json)</text>')
    b.append(f'<text class="s" x="0" y="-48">Frame: millimetres from the top-left of the drawn extent, x right, y down. The KiCad sheet origin was {origin[0]}, {origin[1]} mm away and is not written.</text>')
    b.append('<text class="s" x="0" y="-34">Blue dot: a placement (name, r = rotation, m = mirror). Blue ring: a head on its mast. Black line: a track row with its circuit. Grey dashes: a track row of no circuit, ending at a switch port.</text>')
    b.append('<text class="s" x="0" y="-20">Green diamond: a marker, numbered in the table. Dashed red: the extent. Nothing here is a glyph: the glyphs are each view\'s own.</text>')
    b.append(f'<rect class="frame" x="0" y="0" width="{w*S:.0f}" height="{h*S:.0f}"/>')
    b.append('<text class="s" x="2" y="-4">0,0</text>')
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
        b.append(f'<rect class="house" x="{x-16}" y="{y-11}" width="32" height="22"/><text class="t" x="{x+20}" y="{y+4}">house {name}</text>')
    for name, a in g["appliances"].items():
        x, y = px(a["at"])
        b.append(f'<circle class="port" cx="{x:.1f}" cy="{y:.1f}" r="3.5"/>')
        note = name + (f" r{a['rotation']}" if a.get("rotation") else "") + (f" m{a['mirror']}" if a.get("mirror") else "")
        dy = -8 if "heads" in a or name in ("835", "1") else -8
        b.append(f'<text class="t" x="{x+5:.0f}" y="{y+dy:.0f}">{note}</text>')
        for letter, hp in a.get("heads", {}).items():
            hx, hy = px(hp["at"])
            b.append(f'<circle class="glyph" cx="{hx:.1f}" cy="{hy:.1f}" r="4.5"/>')
    table = []
    for i, m in enumerate(g["markers"], 1):
        x, y = px(m["at"])
        b.append(f'<rect class="marker" x="{x-5}" y="{y-5}" width="10" height="10" transform="rotate(45 {x} {y})"/>')
        b.append(f'<text class="mk" x="{x+7:.0f}" y="{y+13:.0f}">{i}</text>')
        c = ", ".join(f"{k} {v}" for k, v in m.get("circuits", {}).items())
        orient = (f" r{m['rotation']}" if m.get("rotation") else "") + (f" m{m['mirror']}" if m.get("mirror") else "")
        table.append(f'<text class="s" x="0" y="{i*15}"><tspan class="mk">{i}</tspan>  {m["kind"]}{orient} at {m["at"]["x"]}, {m["at"]["y"]}  —  {c}</text>')
    b.append(f'<g transform="translate(0,{h*S+36:.0f})"><text class="t" x="0" y="0">markers</text>{"".join(table)}</g>')
    b.append("</g>")
    return svg(w * S + 80, h * S + 90 + 60 + 15 * len(g["markers"]) + 20, "".join(b), "ADR 0010: Sargent geometry facts")


def draw_views(g) -> str:
    """Four reductions of one object. Each reduction is sketched here by hand; the real one is the view's logic."""
    main = {"Corporal:2NAT", "Sargent:1SAT", "Sargent:835T1", "Sargent:1NAT"}  # the circuits under a Rule 261 sign
    s = 0.6  # the panel scale
    pw, ph = 760, 340

    def switch_legs(name, which=("N", "R")):
        pl = g["appliances"][name]
        c = local_to_page(pl, SWITCH_PORTS["C"])
        out = []
        if "N" in which:
            out.append([c, local_to_page(pl, SWITCH_PORTS["N"])])
        if "R" in which:
            out.append([c, (pl["at"]["x"] * S, pl["at"]["y"] * S), local_to_page(pl, SWITCH_PORTS["R"])])
        return out

    def mast(name, a):
        mx, my = px(a["at"])
        up = 1 if a.get("rotation") == 180 else -1      # a mast turned 180 stands below its track
        side = 1 if a.get("rotation") == 180 else -1
        out = [f'<line class="glyph" x1="{mx:.1f}" y1="{my:.1f}" x2="{mx:.1f}" y2="{my+up*12:.1f}"/>']
        for i, _ in enumerate(a["heads"]):
            out.append(f'<circle class="glyph" cx="{mx+side*(9+i*11):.1f}" cy="{my+up*12:.1f}" r="5"/>')
        out.append(f'<text class="s" x="{mx:.0f}" y="{my+up*26+(6 if up>0 else 0):.0f}" text-anchor="middle">{name}</text>')
        return "".join(out)

    def lamp(name):
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
        b = []
        for t in g["track"]:
            b.append(poly("track" if "circuit" in t else "dark", [(x * S, y * S) for x, y in pts(t["points"])]))
        for name in ("835", "1"):
            for leg in switch_legs(name):
                b.append(poly("track" if name == "835" else "dark", leg))
            x, y = px(g["appliances"][name]["at"])
            b.append(f'<text class="s" x="{x:.0f}" y="{y+18:.0f}" text-anchor="middle">{name}</text>')
        for m in g["markers"]:
            x, y = px(m["at"])
            if m["kind"] in ("IRJ", "IRJ_SIGNAL"):
                b.append(f'<line class="marker" x1="{x:.1f}" y1="{y-6:.1f}" x2="{x:.1f}" y2="{y+6:.1f}"/>')
            elif m["kind"] == "END_CTC":
                b.append(f'<text class="s" x="{x:.0f}" y="{y-9:.0f}" text-anchor="middle">END CTC</text>')
        if route:
            for seg in route:
                b.append(poly("route", seg))
        for name in ("Corporal:2NAT", "1SAT", "2SAT", "1NAT"):
            b.append(lamp(name))
        for name, a in g["appliances"].items():
            if "heads" in a:
                b.append(mast(name, a))
        hx, hy = px(g["houses"]["Sargent"]["at"])
        b.append(f'<rect class="house" x="{hx-14}" y="{hy-9}" width="28" height="18"/><text class="s" x="{hx:.0f}" y="{hy-13:.0f}" text-anchor="middle">CP Sargent</text>')
        b.append(nextcp_labels())
        return "".join(b)

    def thinline():
        # one continuous line from NextCP to NextCP: the main rows and the switch's C–N leg, joints closed
        xs = [p[0] * S for t in g["track"] if t.get("circuit") in main for p in pts(t["points"])]
        y = g["appliances"]["1SAT"]["at"]["y"] * S
        b = [poly("track", [(min(xs), y), (max(xs), y)])]
        for name in ("Corporal:2NAT", "1SAT", "1NAT"):
            b.append(lamp(name))
        for name, a in g["appliances"].items():
            if "heads" in a and name != "836SB":           # 836SB governs the siding; it leaves with it
                b.append(mast(name, a))
        b.append(nextcp_labels())
        return "".join(b)

    pl = g["appliances"]["835"]
    c = local_to_page(pl, SWITCH_PORTS["C"])
    r = local_to_page(pl, SWITCH_PORTS["R"])
    nat = [p for t in g["track"] if t.get("circuit") == "Sargent:1NAT" for p in pts(t["points"])]
    sat2 = [p for t in g["track"] if t.get("circuit") == "Sargent:2SAT" for p in pts(t["points"])]
    route = [[(max(x for x, _ in nat) * S, c[1]), c], [c, (pl["at"]["x"] * S, pl["at"]["y"] * S), r], [r, (min(x for x, _ in sat2) * S, r[1])]]

    docs_rows = "".join(f'<text class="s" x="0" y="{18+i*13}">{n} at {a["at"]["x"]}, {a["at"]["y"]}{" r"+str(a["rotation"]) if a.get("rotation") else ""}{" m"+a["mirror"] if a.get("mirror") else ""}</text>'
                        for i, (n, a) in enumerate(g["appliances"].items()))
    panels = [
        ("1. Thinline: the main track as one line",
         "keeps: rows whose circuit stands under a Rule 261 sign, closed into one line; the circuits' lamps; the masts that govern it; the NextCP ends. drops: the siding (Rule 105) and its mast, dark track, the switch, every joint, the house.",
         f'<g transform="translate(70,100) scale({s})">{thinline()}</g>'),
        ("2. Model board: every placement, with the board's own glyphs",
         "keeps: every row, switch legs and joint ticks at their placements, a lamp at each circuit's placement, masts with their heads, the house. styles: the board's.",
         f'<g transform="translate(70,100) scale({s})">{board_full()}</g>'),
        ("3. Route finder: the board plus an evaluated route",
         "836NB: 1NAT, 835 reverse, 2SAT, laid over the same rows and legs. The route is the evaluator's (view §5); geometry only says where to paint it.",
         f'<g transform="translate(70,100) scale({s})">{board_full(route)}</g>'),
        ("4. Documentation packet: the board at print scale beside its tables",
         "the picture generator's board, re-targeted to the file, printed with the appliance, device and binding tables the packet already lists.",
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
    ap.add_argument("--netlist", type=Path, default=None, help="a netlist export other than production/SPCoast.net")
    ap.add_argument("--out", type=Path, default=HERE, help="write the four files here instead of beside the script")
    a = ap.parse_args(argv)
    geometry, origin = build(a.railroad, a.netlist)
    out = a.out
    (out / "geometry.schema.json").write_text(json.dumps(GEOMETRY_SCHEMA, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    text = layout_model.dumps(geometry)
    (out / "sargent.geometry.json").write_text(text, encoding="utf-8")
    assert layout_model.dumps(layout_model.loads(text)) == text, "not canonical"
    jsonschema.validate(layout_model.loads(text), GEOMETRY_SCHEMA)
    (out / "sargent-geometry.svg").write_text(draw_facts(geometry, origin), encoding="utf-8")
    (out / "four-views.svg").write_text(draw_views(geometry), encoding="utf-8")
    print(f"wrote 4 files to {out}; origin was KiCad {origin}; {len(geometry['track'])} track rows, {len(geometry['markers'])} markers, {len(geometry['appliances'])} appliances")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
