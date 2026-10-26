"""Which way does KiCad turn a symbol for ``(at x y 90)``? Asked of kicad-cli, not assumed (ADR 0010 §4.3's 90-degree fixture).

    uv run python tests/fixtures/kicad/rotation_probe.py [SHEET.kicad_sch] [--lib LIB.kicad_sym]

Copies the project (every .kicad_sch and the .kicad_pro beside the sheet) to a temporary directory, finds a
one-pin Railroad-Trackplan symbol on the sheet whose pin sits on a wire's end, turns that symbol by 90 and by 270
in the copy, and for each hypothesis of the turn's direction moves the wire's end to where the hypothesis says the
pin now is. kicad-cli exports the copy's netlist from the root sheet (a child sheet exported alone has no
annotation, so its symbols sit on no net); the hypothesis under which the wire still reaches the pin is KiCad's
convention. The result (2026-10-25): counter-clockwise as seen on
the page, which is what ``tests/test_geometry.py`` hard-codes and what the ADR's transform states.
"""
from __future__ import annotations

import argparse
import math
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))

from jbom.common.sexp_parser import load_kicad_file  # noqa: E402
from sexpdata import Symbol  # noqa: E402

from kicad_services.netlist_reader import NetlistReader, exported_netlist  # noqa: E402
from kicad_services.symbol_library_reader import SymbolLibraryReader  # noqa: E402


def kids(node, tag):
    return [x for x in node[1:] if isinstance(x, list) and x and x[0] == Symbol(tag)]


def first(node, tag):
    k = kids(node, tag)
    return k[0] if k else None


def ccw(lx, ly, deg):
    """Hypothesis CCW: library (y up) point turned counter-clockwise as seen on the page, then y flipped."""
    a = math.radians(deg)
    return lx * math.cos(a) - ly * math.sin(a), -(lx * math.sin(a) + ly * math.cos(a))


def cw(lx, ly, deg):
    return ccw(lx, ly, -deg)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet", nargs="?", type=Path, default=Path.home() / "Dropbox/KiCad/Railroad/SPCoast/Sargent.kicad_sch")
    ap.add_argument("--lib", type=Path, default=Path.home() / "Dropbox/KiCad/Railroad/symbols/Railroad-Trackplan.kicad_sym")
    ap.add_argument("--root", type=Path, default=Path.home() / "Dropbox/KiCad/Railroad/SPCoast/SPCoast.kicad_sch")
    a = ap.parse_args(argv)
    lib = SymbolLibraryReader().read(a.lib)
    root = load_kicad_file(a.sheet)
    wires = [tuple((float(p[1]), float(p[2])) for p in kids(first(w, "pts"), "xy")) for w in kids(root, "wire")]
    ends = {p for w in wires for p in (w[0], w[-1])}
    candidate = None
    for s in kids(root, "symbol"):
        lib_id = str(first(s, "lib_id")[1])
        if not lib_id.startswith("Railroad-Trackplan:"):
            continue
        sym = lib.get(lib_id.split(":")[1])
        at = first(s, "at")
        if sym is None or len(sym.pins) != 1 or (len(at) > 3 and float(at[3]) != 0) or first(s, "mirror"):
            continue
        x, y = float(at[1]), float(at[2])
        pin = sym.pins[0]
        page = (round(x + pin.x, 2), round(y - pin.y, 2))
        if page in ends and (pin.x, pin.y) != (0.0, 0.0):
            ref = next(str(p[2]) for p in kids(s, "property") if p[1] == "Reference")
            candidate = (ref, lib_id, x, y, pin, page)
            break
    if candidate is None:
        print("no unrotated one-pin trackplan symbol with an off-origin pin on a wire end", file=sys.stderr)
        return 2
    ref, lib_id, x, y, pin, page = candidate
    print(f"probe: {ref} {lib_id} at ({x}, {y}); pin {pin.name} library ({pin.x}, {pin.y}) lands on page {page}")
    text = a.sheet.read_text(encoding="utf-8")
    sym_block = re.search(r'\(symbol\n\t\t\(lib_id "%s"\)\n\t\t\(at %s %s 0\)' % (re.escape(lib_id), re.escape(fmt(x)), re.escape(fmt(y))), text)
    if sym_block is None:
        print("could not find the symbol's text", file=sys.stderr)
        return 2
    def reaches(edited: str) -> bool:
        with tempfile.TemporaryDirectory() as tmp:
            for f in list(a.sheet.parent.glob("*.kicad_sch")) + list(a.sheet.parent.glob("*.kicad_pro")):
                shutil.copy(f, Path(tmp) / f.name)
            (Path(tmp) / a.sheet.name).write_text(edited, encoding="utf-8")
            with exported_netlist(Path(tmp) / a.root.name) as net:
                model = NetlistReader().read(net)
        return any(any(nd.reference == ref for nd in n.nodes) and len(n.nodes) > 1 for n in model.nets)

    if not reaches(text):
        print("control failed: the wire does not reach the pin even unturned", file=sys.stderr)
        return 2
    results = {}
    for deg in (90, 270):
        for name, hyp in (("ccw", ccw), ("cw", cw)):
            dx, dy = hyp(pin.x, pin.y, deg)
            new = (round(x + dx, 2), round(y + dy, 2))
            edited = text[:sym_block.start()] + sym_block.group(0).replace(f"(at {fmt(x)} {fmt(y)} 0)", f"(at {fmt(x)} {fmt(y)} {deg})") + text[sym_block.end():]
            edited = edited.replace(f"(xy {fmt(page[0])} {fmt(page[1])})", f"(xy {fmt(new[0])} {fmt(new[1])})")
            results[(deg, name)] = reaches(edited)
            print(f"  rotation {deg}, hypothesis {name}: pin predicted at {new}; wire reaches it: {results[(deg, name)]}")
    winners = {name for (deg, name), ok in results.items() if ok}
    print("KiCad turns", "counter-clockwise" if winners == {"ccw"} else "clockwise" if winners == {"cw"} else f"undecided {results}", "as seen on the page")
    return 0


def fmt(v: float) -> str:
    return str(int(v)) if float(v).is_integer() else repr(round(v, 4))


if __name__ == "__main__":
    sys.exit(main())
