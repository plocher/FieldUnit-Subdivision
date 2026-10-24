#!/usr/bin/env python3
"""Compile a KiCad project's netlist to the Layout Data Model File (milestone D; ADR 0008 rev 4, ADR 0009).

    uv run python tools/compile_layout.py NETLIST.net -o layout.json [--log LOG] [--quiet]

The netlist is a kicad-cli ``kicadsexpr`` export of the project's root sheet. Diagnostics go to the log (stderr by
default): errors, then warnings, infos and the missing facts. An error means no file is written (ADR 0008 §4.6).
Exit 0 when a file is written, 1 on errors, 2 on a bad invocation.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from layout_compiler import emit, seams, source  # noqa: E402
from tools import layout_model  # noqa: E402

ORDER = {"error": 0, "warning": 1, "info": 2, "missing": 3}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("netlist", type=Path)
    ap.add_argument("-o", "--output", type=Path, required=True)
    ap.add_argument("--log", type=Path, help="write diagnostics here instead of stderr")
    ap.add_argument("--quiet", action="store_true", help="errors only on stderr")
    a = ap.parse_args(argv)
    if not a.netlist.is_file():
        print(f"no such netlist: {a.netlist}", file=sys.stderr)
        return 2
    sm = seams.resolve(source.from_netlist(a.netlist))
    diags = sorted(sm.report.diags, key=lambda d: (ORDER.get(d.severity, 9), d.code, d.where))
    lines = [str(d) for d in diags if not (a.quiet and d.severity != "error")]
    if a.log:
        a.log.write_text("\n".join(str(d) for d in diags) + "\n", encoding="utf-8")
    else:
        for line in lines:
            print(line, file=sys.stderr)
    counts = {k: sum(1 for d in diags if d.severity == k) for k in ORDER}
    summary = ", ".join(f"{v} {k}" for k, v in counts.items() if v)
    if sm.report.errors:
        print(f"{len(sm.report.errors)} error(s); no file written ({summary})", file=sys.stderr)
        return 1
    model = emit.emit(sm, a.netlist)
    errors = layout_model.errors(model)
    if errors:
        for e in errors:
            print(f"schema: {e}", file=sys.stderr)
        print("the model does not validate; no file written", file=sys.stderr)
        return 1
    layout_model.write(a.output, model)
    print(f"wrote {a.output} ({summary or 'clean'})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
