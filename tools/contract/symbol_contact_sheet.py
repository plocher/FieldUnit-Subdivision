#!/usr/bin/env python3
"""Render the symbol libraries and write the contact sheet: baseline beside recipe output.

    python3 tools/contract/symbol_contact_sheet.py [--out DIR]

Renders every symbol of the three baseline libraries (InterlockingPlant) and the three output
libraries (Railroad) with `kicad-cli sym export svg` into <out>/svg-<library>/, one SVG per unit,
and writes <out>/contact-sheet.html: one row per recipe entry with the baseline symbol on the
left and every unit of the output symbol on the right, retired symbols last. The default <out>
is the Railroad repo's `symbols/production/`, which is gitignored.
"""

from __future__ import annotations

import argparse
import html
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_symbol_recipe import OUT, RECIPE, RETIRED, SOURCES, SRC, TARGETS  # noqa: E402

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
        name, _, unit = f.stem.rpartition("_unit")
        files.setdefault(name, []).append(f.name)
    return files


def imgs(folder: str, names: list[str]) -> str:
    return "".join(f'<img src="{folder}/{html.escape(n)}" title="{html.escape(n)}">' for n in names)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", type=Path, default=OUT / "production")
    a = ap.parse_args(argv)
    rendered = {}
    for lib, fn in SOURCES.items():
        rendered[lib] = render(SRC / fn, a.out / f"svg-{lib}")
    for lib in TARGETS:
        rendered[lib] = render(OUT / f"{lib}.kicad_sym", a.out / f"svg-{lib}")
    rows = []
    for e in RECIPE:
        src_lib, src_name = e["src"]
        out_lib, out_name = e["out"], e.get("name", src_name)
        rows.append(f"<tr><td>{html.escape(src_lib)}:{html.escape(src_name)}</td><td>{imgs('svg-' + src_lib, rendered[src_lib].get(src_name, []))}</td>"
                    f"<td>{imgs('svg-' + out_lib, rendered[out_lib].get(out_name, []))}</td><td>{html.escape(out_lib)}:{html.escape(out_name)}</td></tr>")
    for src_lib, src_name in sorted(RETIRED):
        rows.append(f"<tr><td>{html.escape(src_lib)}:{html.escape(src_name)}</td><td>{imgs('svg-' + src_lib, rendered[src_lib].get(src_name, []))}</td><td></td><td>retired</td></tr>")
    page = (f"<!doctype html><meta charset=utf-8><title>Symbol contact sheet</title><style>{STYLE}</style>\n"
            "<h1>Symbol contact sheet: baseline beside recipe output (every unit)</h1>"
            "<table><tr><th>Baseline</th><th>Old</th><th>New</th><th>Output</th></tr>\n" + "\n".join(rows) + "\n</table>\n")
    (a.out / "contact-sheet.html").write_text(page)
    print(f"{a.out / 'contact-sheet.html'}: {len(rows)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
