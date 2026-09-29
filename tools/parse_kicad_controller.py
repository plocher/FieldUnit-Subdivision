#!/usr/bin/env python3
"""Compile a controller-project netlist into a controller fragment.

The fragment is per-project, local facts only. Cross-project checks belong
to link_subdivision.py. Diagnostics never block emission; the exit code is
nonzero when any error-severity finding exists.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from controller_graph.compiler import compile_controller
from controller_graph.report import report_diagnostics
from kicad_services.netlist_reader import KicadCliNetlistExporter, NetlistReader


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--netlist", type=Path, help="Existing kicadsexpr .net")
    parser.add_argument(
        "--schematic", type=Path, help="Schematic (exports netlist via kicad-cli)"
    )
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--output", type=Path, help="Output file; default stdout")
    parser.add_argument("--kicad-cli", type=Path, help="Explicit kicad-cli path")
    args = parser.parse_args()

    netlist_path = args.netlist
    if netlist_path is None:
        if args.schematic is None:
            parser.error("one of --netlist or --schematic is required")
        exporter = KicadCliNetlistExporter(kicad_cli=args.kicad_cli)
        netlist_path = exporter.export(args.schematic)

    fragment = compile_controller(NetlistReader().read(netlist_path))

    if args.format == "json":
        doc = asdict(fragment)
        doc["kind"] = "controller-fragment"
        text = json.dumps(doc, indent=2, sort_keys=True) + "\n"
    else:
        lines = [
            f"machine: {fragment.machine.name} "
            f"({fragment.machine.machine_type}, "
            f"{fragment.machine.columns} columns)"
        ]
        for column in fragment.columns:
            lines.append(
                f"column {column.number}: {column.cp_name} "
                f"[{column.interlocking}]"
            )
        for codeline in fragment.codelines:
            stub = " (stub)" if codeline.stub else ""
            lines.append(
                f"codeline {codeline.interlocking}: {codeline.transport} "
                f"station {codeline.station!r}{stub}"
            )
        for binding in fragment.bindings:
            lines.append(
                f"bind {binding.appliance}.{binding.function} -> "
                f"{binding.driver} bit {binding.bit}"
            )
        text = "\n".join(lines) + "\n"

    if args.output:
        args.output.write_text(text)
    else:
        sys.stdout.write(text)

    return report_diagnostics(fragment.diagnostics)


if __name__ == "__main__":
    raise SystemExit(main())
