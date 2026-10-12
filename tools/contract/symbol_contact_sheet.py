#!/usr/bin/env python3
"""Render the symbol libraries and write the contact sheet, every unit of every symbol.

    python3 tools/contract/symbol_contact_sheet.py [--libdir DIR] [--out DIR]

Renders RailroadPlant, RailroadDevice and RailroadDesk with `kicad-cli sym export svg` into
<out>/svg-<library>/, one SVG per unit, and writes <out>/contact-sheet.html: one row per symbol
with its Role, Appliance, Style or IC and all of its units. The default <out> is the Railroad
repo's `symbols/production/`, which is gitignored. The render is also the parse check.
"""

from __future__ import annotations

import argparse
import html
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kicad_services.sch_text import library_symbols  # noqa: E402

LIBDIR = Path.home() / "Dropbox/KiCad/Railroad/symbols"
LIBRARIES = ("RailroadPlant", "RailroadDevice", "RailroadDesk")
KICAD_CLI = os.environ.get("KICAD_CLI") or shutil.which("kicad-cli") or "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
STYLE = ("body{font:13px sans-serif}table{border-collapse:collapse}td,th{border:1px solid #ccc;padding:4px;"
         "vertical-align:top}img{max-width:260px;max-height:200px;background:#fff;margin:2px}")


def render(lib_file: Path, out_dir: Path) -> dict[str, list[str]]:
    """{symbol name: [svg file names]} after rendering lib_file into out_dir."""
    shutil.rmtree(out_dir, ignore_errors=True)
    out_dir.mkdir(parents=True)
    subprocess.run([KICAD_CLI, "sym", "export", "svg", "-o", str(out_dir), str(lib_file)],
                   check=True, capture_output=True)
    files: dict[str, list[str]] = {}
    for f in sorted(out_dir.iterdir()):
        name, _, _ = f.stem.rpartition("_unit")
        files.setdefault(name, []).append(f.name)
    return files


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--libdir", type=Path, default=LIBDIR)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args(argv)
    out = a.out or a.libdir / "production"
    rows = []
    for lib in LIBRARIES:
        lib_file = a.libdir / f"{lib}.kicad_sym"
        files = render(lib_file, out / f"svg-{lib}")
        for name, sym in library_symbols(lib_file.read_text()).items():
            p = sym["properties"]
            key = " : ".join(x for x in (p.get("Role", ""), p.get("Appliance", p.get("IC", "")), p.get("Style", "")) if x)
            imgs = "".join(f'<img src="svg-{lib}/{html.escape(f)}" title="{html.escape(f)}">' for f in files.get(name, []))
            rows.append(f"<tr><td>{lib}</td><td>{html.escape(name)}</td><td>{html.escape(key)}</td><td>{imgs}</td></tr>")
    page = (f"<!doctype html><meta charset=utf-8><title>Symbol contact sheet</title><style>{STYLE}</style>\n"
            "<h1>Symbol contact sheet</h1><table><tr><th>Library</th><th>Symbol</th><th>Role : Appliance or IC : Style</th><th>Units</th></tr>\n"
            + "\n".join(rows) + "\n</table>\n")
    (out / "contact-sheet.html").write_text(page)
    print(f"{out / 'contact-sheet.html'}: {len(rows)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
