#!/usr/bin/env python3
"""Refresh a schematic's embedded lib_symbols copies from the symbol library (KiCad's
"Update symbol from library" for the symbol definition only; instance fields untouched).

Usage: python3 refresh_embedded.py --lib RailroadPanel --symbols A,B,... [--check-rev REV] [--dry-run] sheet.kicad_sch...

--check-rev: before replacing, confirm each embedded copy equals the library at that git
revision (so the refresh carries only the changes made since). Mismatches are reported
and that sheet is not written.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from symlib_edit import end_of, split  # noqa: E402

LIBDIR = Path.home() / "Dropbox/KiCad/InterlockingPlant/symbols"


def embedded_form(lib, name, block):
    """Library block -> lib_symbols form: prefixed name, one more tab of indent."""
    b = block.replace(f'(symbol "{name}"', f'(symbol "{lib}:{name}"', 1)
    first, *rest = b.split("\n")
    return "\n".join([first] + [("\t" + ln) if ln else ln for ln in rest])


def normalise(b):
    """Whitespace-insensitive, and blind to Description text (documentation, not contract)."""
    return re.sub(r'\(property "Description" "[^"]*"', "", re.sub(r"\s+", " ", b))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lib", required=True)
    ap.add_argument("--symbols", required=True)
    ap.add_argument("--check-rev")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("sheets", nargs="+")
    a = ap.parse_args()
    names = a.symbols.split(",")
    path = LIBDIR / f"{a.lib}.kicad_sym"
    new = dict(split(path.read_text())[1])
    old = None
    if a.check_rev:
        txt = subprocess.check_output(["git", "-C", str(LIBDIR), "show", f"{a.check_rev}:symbols/{path.name}"],
                                      text=True)
        old = dict(split(txt)[1])
    for sheet in a.sheets:
        t = Path(sheet).read_text()
        ok, n = True, 0
        for name in names:
            m = re.search(r'\n\t\t\(symbol "' + re.escape(f"{a.lib}:{name}") + r'"\n', t)
            if not m:
                continue
            s = m.start() + 3
            e = end_of(t, s)
            if old is not None and normalise(t[s:e]) != normalise(embedded_form(a.lib, name, old[name])):
                print(f"  ! {sheet}: embedded {name} differs from library at {a.check_rev}")
                ok = False
                continue
            t = t[:s] + embedded_form(a.lib, name, new[name]) + t[e:]
            n += 1
        print(f"{sheet}: {n} refreshed{'' if ok else ' (NOT WRITTEN: mismatch)'}")
        if ok and not a.dry_run:
            Path(sheet).write_text(t)


if __name__ == "__main__":
    main()
