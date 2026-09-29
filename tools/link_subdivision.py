#!/usr/bin/env python3
"""Link controller fragments and portable plant models into one model.

The linker always emits; missing counterparts become placeholder stations
and generators decide what is fatal for their output. The exit code is
nonzero when any error-severity finding exists.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from controller_graph.compiler import compile_controller
from kicad_services.netlist_reader import NetlistReader
from link.linker import link_subdivision
from link.model import subdivision_to_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--controller",
        type=Path,
        action="append",
        default=[],
        help="Controller-project netlist (.net); repeatable",
    )
    parser.add_argument(
        "--plant",
        type=Path,
        action="append",
        default=[],
        help="Portable plant model (.json); repeatable",
    )
    parser.add_argument("--output", type=Path, help="Output file; default stdout")
    args = parser.parse_args()

    reader = NetlistReader()
    controllers = [
        compile_controller(reader.read(path)) for path in args.controller
    ]
    plants = [json.loads(path.read_text()) for path in args.plant]

    model = link_subdivision(controllers, plants)
    text = json.dumps(subdivision_to_json(model), indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text)
    else:
        sys.stdout.write(text)

    diagnostics = list(model.diagnostics)
    for controller in controllers:
        diagnostics.extend(controller.diagnostics)
    for diagnostic in diagnostics:
        print(
            f"{diagnostic.severity}: {diagnostic.code}: {diagnostic.message}",
            file=sys.stderr,
        )
    return 1 if any(d.severity == "error" for d in diagnostics) else 0


if __name__ == "__main__":
    raise SystemExit(main())
