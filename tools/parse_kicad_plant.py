#!/usr/bin/env python3
"""On-demand KiCad plant-graph parser/validator CLI.

Builds an in-memory Plant Graph from a Railroad symbol library and a
schematic (via kicad-cli netlist export). Prints diagnostics and a human
inventory to stdout. Does not write graph files or modify KiCad sources.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from kicad_services.netlist_reader import (  # noqa: E402
    KicadCliNetlistExporter,
    NetlistParseError,
    NetlistReader,
)
from kicad_services.symbol_library_reader import (  # noqa: E402
    SymbolLibraryParseError,
    SymbolLibraryReader,
)
from plant_graph.compiler import PlantGraphCompiler  # noqa: E402
from plant_graph.routes import (  # noqa: E402
    build_route_proof,
    format_route_line,
)
from plant_graph.types import DiagnosticSeverity, NetClass, PlantGraph  # noqa: E402


def build_arg_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Parse a KiCad interlocking schematic into a plant graph inventory."
    )
    parser.add_argument(
        "--library",
        type=Path,
        required=True,
        help="Path to Railroad.kicad_sym (or compatible library)",
    )
    parser.add_argument(
        "--schematic",
        type=Path,
        help="Path to .kicad_sch (exports netlist via kicad-cli)",
    )
    parser.add_argument(
        "--netlist",
        type=Path,
        help="Path to an existing kicadsexpr .net (skips kicad-cli)",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Stdout format (default: text)",
    )
    parser.add_argument(
        "--kicad-cli",
        type=Path,
        default=None,
        help="Optional explicit path to kicad-cli",
    )
    return parser


def load_graph(args: argparse.Namespace) -> PlantGraph:
    """Load library + netlist and compile the plant graph."""
    if not args.schematic and not args.netlist:
        raise SystemExit("Provide --schematic and/or --netlist")

    library = SymbolLibraryReader().read(args.library)

    netlist_path: Path
    temp_net: Path | None = None
    try:
        if args.netlist:
            netlist_path = args.netlist
        else:
            exporter = KicadCliNetlistExporter(kicad_cli=args.kicad_cli)
            fd, name = tempfile.mkstemp(prefix="plant_net_", suffix=".net")
            Path(name).unlink(missing_ok=True)
            import os

            os.close(fd)
            temp_net = Path(name)
            netlist_path = exporter.export(args.schematic, temp_net)

        netlist = NetlistReader().read(netlist_path)
        return PlantGraphCompiler().compile(library, netlist)
    finally:
        if temp_net is not None and temp_net.exists():
            temp_net.unlink(missing_ok=True)


def render_text(graph: PlantGraph) -> str:
    """Render a human-readable inventory."""
    lines: list[str] = []
    lines.append("Plant Graph Inventory")
    lines.append("=====================")
    lines.append("")
    lines.append("Entities:")
    for ref, ent in sorted(graph.entities.items()):
        lines.append(
            f"  {ref:12}  {ent.kind.value:16}  name={ent.canonical_name!r}  "
            f"value={ent.value!r}  {ent.lib_id}"
        )
    lines.append("")
    lines.append("Derived track circuits:")
    if not graph.derived_track_circuits:
        lines.append("  (none)")
    for tc in graph.derived_track_circuits:
        lines.append(f"  {tc.name}  (from switch {tc.switch_name})")
    lines.append("")
    lines.append("Nets:")
    for net in graph.nets:
        flag = "label" if net.authoritative_label else "auto"
        nodes = ", ".join(f"{r}:{p}" for r, p in net.nodes)
        lines.append(
            f"  [{net.net_class.value:18}] ({flag:5}) {net.name:24}  {nodes}"
        )
    lines.append("")
    lines.append("Terminals:")
    if not graph.terminals:
        lines.append("  (none)")
    for term in graph.terminals:
        rb = f" rule={term.rulebook}" if term.rulebook else ""
        lines.append(
            f"  {term.reference:8}  {term.kind.value:12}  "
            f"desig={term.designation!r}  net={term.net_name!r}{rb}"
        )
    lines.append("")
    lines.append("Signal faces:")
    if not graph.signal_faces:
        lines.append("  (none)")
    for face in graph.signal_faces:
        lines.append(
            f"  signal {face.signal_name}{face.direction}  mast={face.mast_name}  "
            f"irj={face.irj_reference}  approach={face.approach_net}  "
            f"term={face.approach_terminal}"
        )
    lines.append("")
    lines.append("Route table (valid):")
    lines.append(
        "  route                        mast     alignment        signal(lever)  clear TCs                 indication"
    )
    if not graph.routes:
        lines.append("  (none)")
    for route in graph.routes:
        lines.append("  " + format_route_line(route))
    # Internal completeness check only — do not present impossible pairs as product.
    proof = build_route_proof(graph)
    valid_pair_set = set(tuple(p) for p in proof["valid_pairs"])
    reachable_pair_set = set(tuple(p) for p in proof["reachable_pairs"])
    if valid_pair_set != reachable_pair_set:
        missing = sorted(reachable_pair_set - valid_pair_set)
        extra = sorted(valid_pair_set - reachable_pair_set)
        lines.append("")
        lines.append("Route harvest completeness:")
        lines.append(
            f"  WARNING harvest/proof mismatch "
            f"(missing_from_harvest={missing}, extra_in_harvest={extra})"
        )
    lines.append("")
    lines.append("Diagnostics:")
    if not graph.diagnostics:
        lines.append("  (none)")
    for diag in graph.diagnostics:
        where = f" [{diag.entity_ref}]" if diag.entity_ref else ""
        lines.append(
            f"  {diag.severity.value.upper():8} {diag.code:28} {diag.message}{where}"
        )
    lines.append("")
    track = sum(1 for n in graph.nets if n.net_class is NetClass.TRACK)
    labeled = sum(
        1
        for n in graph.nets
        if n.net_class is NetClass.TRACK and n.authoritative_label
    )
    switch_os = sum(1 for n in graph.nets if n.net_class is NetClass.SWITCH_OS)
    lines.append(
        f"Summary: {len(graph.entities)} entities, {len(graph.nets)} nets "
        f"({labeled}/{track} track labeled, {switch_os} switch_os), "
        f"{len(graph.terminals)} terminals, {len(graph.signal_faces)} faces, "
        f"{len(graph.routes)} routes, "
        f"{len(graph.errors())} errors, "
        f"{sum(1 for d in graph.diagnostics if d.severity is DiagnosticSeverity.WARNING)} warnings"
    )
    return "\n".join(lines) + "\n"


def render_json(graph: PlantGraph) -> str:
    """Render a debug JSON projection (stdout only)."""
    payload: dict[str, Any] = {
        "entities": [
            {
                "reference": e.reference,
                "kind": e.kind.value,
                "canonical_name": e.canonical_name,
                "value": e.value,
                "lib_id": e.lib_id,
                "fields": e.fields,
            }
            for e in graph.entities.values()
        ],
        "derived_track_circuits": [
            {
                "name": t.name,
                "switch_name": t.switch_name,
                "reason": t.reason,
            }
            for t in graph.derived_track_circuits
        ],
        "terminals": [
            {
                "reference": t.reference,
                "kind": t.kind.value,
                "designation": t.designation,
                "rulebook": t.rulebook,
                "net_name": t.net_name,
                "port_pin": t.port_pin,
            }
            for t in graph.terminals
        ],
        "signal_faces": [
            {
                "signal_name": f.signal_name,
                "direction": f.direction,
                "mast_reference": f.mast_reference,
                "mast_name": f.mast_name,
                "irj_reference": f.irj_reference,
                "approach_net": f.approach_net,
                "approach_terminal": f.approach_terminal,
            }
            for f in graph.signal_faces
        ],
        "routes": [
            {
                "name": r.name,
                "signal_name": r.signal_name,
                "direction": r.direction,
                "mast_reference": r.mast_reference,
                "mast_name": r.mast_name,
                "entry_terminal": r.entry_terminal,
                "entry_net": r.entry_net,
                "entry_designation": r.entry_designation,
                "entry_rulebook": r.entry_rulebook,
                "exit_terminal": r.exit_terminal,
                "exit_net": r.exit_net,
                "exit_designation": r.exit_designation,
                "exit_rulebook": r.exit_rulebook,
                "switch_alignments": [
                    {"switch": n, "position": p} for n, p in r.switch_alignments
                ],
                "clear_track_circuits": list(r.clear_track_circuits),
                "path_nets": list(r.path_nets),
                "presentation": format_route_line(r),
            }
            for r in graph.routes
        ],
        "nets": [
            {
                "name": n.name,
                "raw_name": n.raw_name,
                "class": n.net_class.value,
                "authoritative_label": n.authoritative_label,
                "nodes": [{"ref": r, "pin": p} for r, p in n.nodes],
            }
            for n in graph.nets
        ],
        "route_completeness": (
            lambda p: {
                "ok": set(map(tuple, p["valid_pairs"])) == set(map(tuple, p["reachable_pairs"])),
                "valid_route_count": p["valid_route_count"],
                "full_switch_combos": p["combo_count"],
            }
        )(build_route_proof(graph)),
        "diagnostics": [
            {
                "severity": d.severity.value,
                "code": d.code,
                "message": d.message,
                "entity_ref": d.entity_ref,
            }
            for d in graph.diagnostics
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    try:
        graph = load_graph(args)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except (SymbolLibraryParseError, NetlistParseError) as exc:
        print(f"syntax error: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        sys.stdout.write(render_json(graph))
    else:
        sys.stdout.write(render_text(graph))

    return 1 if graph.has_errors() else 0


if __name__ == "__main__":
    raise SystemExit(main())
