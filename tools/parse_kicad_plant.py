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
from kicad_services.schematic_reader import SchematicPlacementReader  # noqa: E402
from plant_graph.compiler import PlantGraphCompiler  # noqa: E402
from plant_graph.indications import RouteSignalingPolicy  # noqa: E402
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
    parser.add_argument(
        "--aliases",
        type=Path,
        default=None,
        help="Optional JSON object mapping graph identity strings to display/MP names",
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
        placements = (
            SchematicPlacementReader().read(args.schematic)
            if args.schematic is not None
            else None
        )
        graph = PlantGraphCompiler().compile(library, netlist, placements)
        if args.aliases is not None:
            import json as _json

            data = _json.loads(args.aliases.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise SystemExit("--aliases must be a JSON object of string:string")
            graph.name_aliases = {str(k): str(v) for k, v in data.items()}
        return graph
    finally:
        if temp_net is not None and temp_net.exists():
            temp_net.unlink(missing_ok=True)


def render_text(graph: PlantGraph) -> str:
    """Render a human-readable inventory."""
    indication_policy = RouteSignalingPolicy()
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
        "  route                        mast     heads    alignment        demand         end              "
        "entrance      home-clear               downstream       unresolved       indication"
    )
    if not graph.routes:
        lines.append("  (none)")
    for route in graph.routes:
        indication = indication_policy.static_indication(route, graph).value
        lines.append("  " + format_route_line(route, indication))
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
    indication_policy = RouteSignalingPolicy()
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
        "switch_geometries": [
            {
                "switch": geometry.switch_name,
                "cn_heading": geometry.cn_heading.value,
                "reverse_side": geometry.reverse_side.value,
            }
            for geometry in sorted(
                graph.switch_geometries.values(),
                key=lambda item: item.switch_name,
            )
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
        "mast_heads": [
            {
                "mast_reference": attachment.mast_reference,
                "mast_name": attachment.mast_name,
                "mast_pin": attachment.mast_pin,
                "head_reference": attachment.head_reference,
                "head_name": attachment.head_name,
            }
            for attachment in graph.mast_heads
        ],
        "rail_layout": {
            "width_units": graph.board_width_units,
            "anchor_positions": dict(graph.longitudinal_positions),
            "components": [
                {
                    "identifier": component.identifier,
                    "kind": component.kind.value,
                    "label": component.label,
                    "x_units": component.x_units,
                    "row_name": component.row_name,
                    "mirror_x": component.mirror_x,
                    "mirror_y": component.mirror_y,
                    "actuator_kind": (
                        component.actuator_kind.value
                        if component.actuator_kind is not None
                        else None
                    ),
                    "has_frog_lamp": component.has_frog_lamp,
                    "ports": [
                        {
                            "identifier": port.identifier,
                            "name": port.name,
                            "x_units": port.x_units,
                            "row_name": port.row_name,
                        }
                        for port in component.ports
                    ],
                }
                for component in graph.board_components
            ],
            "connections": [
                {
                    "identifier": connection.identifier,
                    "row_name": connection.row_name,
                    "start_port_id": connection.start_port_id,
                    "end_port_id": connection.end_port_id,
                    "circuit_name": connection.circuit_name,
                    "is_dark": connection.is_dark,
                    "is_local_stub": connection.is_local_stub,
                }
                for connection in graph.board_connections
            ],
            "sections": [
                {
                    "name": section.name,
                    "index": section.index,
                    "center_units": section.center_units,
                }
                for section in graph.board_sections
            ],
            "rows": [
                {
                    "name": row.name,
                    "lane": row.lane,
                    "priority": row.priority,
                    "circuits": list(row.circuits),
                }
                for row in graph.rail_rows
            ],
            "spans": [
                {
                    "name": span.name,
                    "row_name": span.row_name,
                    "endpoints": list(span.endpoints),
                    "circuit_name": span.circuit_name,
                    "order": span.order,
                    "start_anchor": span.start_anchor,
                    "end_anchor": span.end_anchor,
                    "endpoint_anchors": [
                        {"reference": reference, "anchor": anchor}
                        for reference, anchor in span.endpoint_anchors
                    ],
                    "irj_endpoints": list(span.irj_endpoints),
                    "is_dark": span.is_dark,
                    "is_local_stub": span.is_local_stub,
                    "local_stub_direction": span.local_stub_direction,
                    "turnout_ports": [
                        {
                            "switch_name": switch_name,
                            "port": port,
                            "anchor": anchor,
                        }
                        for switch_name, port, anchor in span.turnout_ports
                    ],
                }
                for span in graph.rail_spans
            ],
            "turnouts": [
                {
                    "switch_name": turnout.switch_name,
                    "cn_heading": turnout.cn_heading.value,
                    "c_row": turnout.c_row,
                    "n_row": turnout.n_row,
                    "r_row": turnout.r_row,
                    "anchor": turnout.order,
                    "actuator_kind": turnout.actuator_kind.value,
                    "has_frog_lamp": turnout.has_frog_lamp,
                    "actuator_flipped": turnout.actuator_flipped,
                    "section_index": turnout.section_index,
                }
                for turnout in graph.turnout_layouts
            ],
            "track_circuit_lamps": [
                {
                    "circuit_name": lamp.circuit_name,
                    "span_name": lamp.span_name,
                    "row_name": lamp.row_name,
                    "start_anchor": lamp.start_anchor,
                    "end_anchor": lamp.end_anchor,
                }
                for lamp in graph.track_circuit_lamps
            ],
            "signal_bases": [
                {
                    "mast_name": base.mast_name,
                    "mast_reference": base.mast_reference,
                    "irj_reference": base.irj_reference,
                    "row_name": base.row_name,
                    "direction": base.direction,
                    "anchor": base.anchor,
                }
                for base in graph.signal_bases
            ],
            "terminals": [
                {
                    "name": terminal.name,
                    "row_name": terminal.row_name,
                    "side": terminal.side,
                    "anchor": terminal.anchor,
                    "is_plant_edge": terminal.is_plant_edge,
                    "span_name": terminal.span_name,
                }
                for terminal in graph.board_terminals
            ],
        },
        "routes": [
            {
                "name": r.name,
                "signal_name": r.signal_name,
                "direction": r.direction,
                "mast_reference": r.mast_reference,
                "mast_name": r.mast_name,
                "head_letters": r.head_letters,
                "head_names": list(r.head_names),
                "end_kind": r.end_kind.value,
                "exit_face_mast": r.exit_face_mast,
                "exit_face_signal": r.exit_face_signal,
                "exit_face_direction": r.exit_face_direction,
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
                "circuit_roles": [
                    {"track_circuit": circuit, "role": role.value}
                    for circuit, role in r.circuit_roles
                ],
                "clear_track_circuits": list(r.clear_track_circuits),
                "os_track_circuits": list(r.os_track_circuits),
                "path_track_circuits": list(r.path_track_circuits),
                "path_nets": list(r.path_nets),
                "switch_traversals": [
                    {
                        "switch": traversal.switch_name,
                        "entry_pin": traversal.entry_pin,
                        "exit_pin": traversal.exit_pin,
                        "alignment": traversal.alignment,
                        "point_traversal": traversal.point_traversal.value,
                    }
                    for traversal in r.switch_traversals
                ],
                "static_indication": indication_policy.static_indication(
                    r, graph
                ).value,
                "presentation": format_route_line(
                    r,
                    indication_policy.static_indication(r, graph).value,
                ),
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
        "name_aliases": dict(graph.name_aliases),
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
