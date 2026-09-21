"""Compile a railroad PlantGraph from KiCad library + netlist models."""

from __future__ import annotations

import math
import re
from typing import Optional

from kicad_services.types import (
    LibraryModel,
    Net,
    NetlistComponent,
    NetlistModel,
    SchematicPlacementModel,
)
from plant_graph.layout import (
    LongitudinalInterval,
    LongitudinalLayoutSolver,
    resolve_board_components,
)
from plant_graph.types import (
    CircuitRole,
    DerivedTrackCircuit,
    Diagnostic,
    DiagnosticSeverity,
    EntityKind,
    NetClass,
    PlantDocument,
    PlantEntity,
    PlantGraph,
    PlantNet,
    SchematicHeading,
    RailRow,
    RailSpan,
    TurnoutLayout,
    SignalBase,
    BoardTerminal,
    BoardSection,
    SwitchGeometry,
    TrackCircuitLamp,
    TurnoutActuatorKind,
    TurnoutHand,
)

# Railroad part name → entity kind.
_PART_KIND: dict[str, EntityKind] = {
    "Switch_Powered": EntityKind.SWITCH_POWERED,
    "Switch_Lock": EntityKind.SWITCH_LOCK,
    "Switch_Powered_Derail": EntityKind.DERAIL,
    "IRJ": EntityKind.IRJ,
    "IRJ-Signal": EntityKind.IRJ_SIGNAL,
    "Mast_Single": EntityKind.MAST_SINGLE,
    "Mast_Double": EntityKind.MAST_DOUBLE,
    "Mast_Dwarf": EntityKind.MAST_DWARF,
    "Signal Head - CL": EntityKind.SIGNAL_HEAD,
    "Track Circuit": EntityKind.TRACK_CIRCUIT,
    "Direction_L": EntityKind.DIRECTION,
    "Direction_R": EntityKind.DIRECTION,
    "Direction_BOTH": EntityKind.DIRECTION,
    "Rule251-DoT-Left": EntityKind.OPERATING_POLICY,
    "Rule251-DoT-Right": EntityKind.OPERATING_POLICY,
    "Rule261-DoT-BiDirectional": EntityKind.OPERATING_POLICY,
    "Rule6.28-OtherThanMain": EntityKind.OPERATING_POLICY,
    "NextCP": EntityKind.NEXT_CP,
    "Bumper": EntityKind.BUMPER,
    "MAIN HOUSE": EntityKind.MAIN_HOUSE,
    "Maintainer": EntityKind.MAINTAINER,
    "MaintainerCall": EntityKind.MAINTAINER_CALL,
    "Route": EntityKind.ROUTE,
    "Milepost": EntityKind.MILEPOST,
}

# Pins that participate in track topology.
_TRACK_PINS: dict[EntityKind, frozenset[str]] = {
    EntityKind.SWITCH_POWERED: frozenset({"1", "2", "3"}),  # C/N/R
    EntityKind.SWITCH_LOCK: frozenset({"1", "2", "3"}),
    EntityKind.DERAIL: frozenset({"1", "2"}),  # C/N; derailing end is ballast
    EntityKind.IRJ: frozenset({"1", "2"}),  # A/B
    EntityKind.IRJ_SIGNAL: frozenset({"1", "2"}),  # A/B only; 3 is SIGNAL
    EntityKind.TRACK_CIRCUIT: frozenset({"1"}),
    EntityKind.DIRECTION: frozenset({"1", "2"}),
    EntityKind.OPERATING_POLICY: frozenset({"1"}),
    EntityKind.NEXT_CP: frozenset({"1"}),
    EntityKind.BUMPER: frozenset({"2"}),  # B
}

_SIGNAL_ATTACH_PINS: dict[EntityKind, frozenset[str]] = {
    EntityKind.IRJ_SIGNAL: frozenset({"3"}),
    EntityKind.MAST_SINGLE: frozenset({"1"}),
    EntityKind.MAST_DOUBLE: frozenset({"1"}),
    EntityKind.MAST_DWARF: frozenset({"1"}),
}

_HEAD_ATTACH_PINS: dict[EntityKind, frozenset[str]] = {
    EntityKind.MAST_SINGLE: frozenset({"2"}),
    EntityKind.MAST_DOUBLE: frozenset({"2", "3"}),
    EntityKind.MAST_DWARF: frozenset({"2"}),
    EntityKind.SIGNAL_HEAD: frozenset({"1"}),
}

_REQUIRED_PINS: dict[EntityKind, frozenset[str]] = {
    EntityKind.SWITCH_POWERED: frozenset({"1", "2", "3"}),
    EntityKind.SWITCH_LOCK: frozenset({"1", "2", "3"}),
    EntityKind.DERAIL: frozenset({"1", "2"}),
    EntityKind.IRJ: frozenset({"1", "2"}),
    EntityKind.IRJ_SIGNAL: frozenset({"1", "2", "3"}),
    EntityKind.MAST_SINGLE: frozenset({"1", "2"}),
    EntityKind.MAST_DOUBLE: frozenset({"1", "2", "3"}),
    EntityKind.MAST_DWARF: frozenset({"1", "2"}),
    EntityKind.SIGNAL_HEAD: frozenset({"1"}),
    # Direction is a plant terminal: exactly one live pin (enforced in routes).
}

_MAST_VALUE_RE = re.compile(r"^(\d+)([NSEW])([A-E]+)$")
_HEAD_VALUE_RE = re.compile(r"^[A-E]$")
_SWITCH_REF_RE = re.compile(r"^SW(.+)$")
_MAST_REF_RE = re.compile(r"^S(\d+)([NSEW])(\d+)$")
_DEFAULT_MAST_DIRECTION_MAP: dict[str, str] = {
    "N": "LEFT",
    "W": "LEFT",
    "S": "RIGHT",
    "E": "RIGHT",
}
_LAYOUT_ANCHOR_KINDS = frozenset(
    {
        EntityKind.SWITCH_POWERED,
        EntityKind.SWITCH_LOCK,
        EntityKind.DERAIL,
        EntityKind.IRJ,
        EntityKind.IRJ_SIGNAL,
        EntityKind.DIRECTION,
        EntityKind.NEXT_CP,
    }
)


class PlantGraphCompiler:
    """Railroad domain compiler over generic KiCad models."""
    def __init__(self, mast_direction_map: Optional[dict[str, str]] = None) -> None:
        """Configure mast-suffix normalization for one railroad convention."""
        self._mast_direction_map = dict(_DEFAULT_MAST_DIRECTION_MAP)
        if mast_direction_map is not None:
            self._mast_direction_map.update(
                {
                    suffix.upper(): direction.upper()
                    for suffix, direction in mast_direction_map.items()
                }
            )

    def compile(
        self,
        library: LibraryModel,
        netlist: NetlistModel,
        placements: SchematicPlacementModel | None = None,
    ) -> PlantGraph:
        """Build a PlantGraph and diagnostics from library + netlist.

        Args:
            library: Shared Railroad (or compatible) symbol library model.
            netlist: Parsed schematic netlist model.

        Returns:
            In-memory PlantGraph. Callers inspect ``has_errors()`` before
            any downstream projection.
        """
        graph = PlantGraph(mast_direction_map=dict(self._mast_direction_map))
        if placements is not None:
            graph.document = PlantDocument(
                title=placements.title_block.title,
                revision=placements.title_block.revision,
                date=placements.title_block.date,
                company=placements.title_block.company,
                comments=dict(placements.title_block.comments),
            )
        self._build_entities(graph, library, netlist)
        self._classify_nets(graph, netlist)
        self._check_required_pins(graph, netlist)
        self._derive_os_circuits(graph)
        if placements is not None:
            self._derive_switch_geometries(graph, library, netlist, placements)
        self._check_track_net_labels(graph)
        self._check_cp_allocations(graph)
        self._check_dependent_derail_allocations(graph)
        self._check_switch_indications(graph)
        self._check_library_coverage(graph, library)
        # Topology + combinatoric signal routes (DoT terminals, switch N/R).
        from plant_graph.routes import harvest_routes

        harvest_routes(graph)
        for route in graph.routes:
            unresolved = [
                circuit
                for circuit, role in route.circuit_roles
                if role is CircuitRole.UNRESOLVED
            ]
            if unresolved:
                graph.diagnostics.append(
                    Diagnostic(
                        severity=DiagnosticSeverity.SEMANTIC,
                        code="unresolved_route_circuit",
                        message=(
                            f"Route '{route.name}' has unresolved circuit role(s): "
                            f"{unresolved}"
                        ),
                        entity_ref=route.mast_reference,
                    )
                )
        from plant_graph.indications import RouteSignalingPolicy

        graph.routes = RouteSignalingPolicy().compile_static_indications(graph)
        if placements is not None:
            self._derive_board_layout(graph, placements)
        return graph

    def _derive_board_layout(
        self,
        graph: PlantGraph,
        placements: SchematicPlacementModel,
    ) -> None:
        """Compile coordinate-free board facts from placed source appliances."""
        main_houses = sorted(
            (
                (placements.placements[entity.reference].x, entity.canonical_name)
                for entity in graph.entities.values()
                if entity.kind is EntityKind.MAIN_HOUSE
                and entity.reference in placements.placements
            )
        )
        graph.board_width_units = max(1, len(main_houses))
        if len(main_houses) == 1:
            section_centers = (graph.board_width_units / 2.0,)
        elif main_houses:
            left_margin = 0.45
            right_margin = 0.75
            spacing = (
                graph.board_width_units - left_margin - right_margin
            ) / (len(main_houses) - 1)
            section_centers = tuple(
                left_margin + index * spacing
                for index in range(len(main_houses))
            )
        else:
            section_centers = ()
        graph.board_sections = [
            BoardSection(
                name=name,
                index=index,
                center_units=section_centers[index],
            )
            for index, (_x, name) in enumerate(main_houses)
        ]
        x_values = self._layout_x_values(graph, placements)

        ordered_nets = sorted(
            (
                net
                for net in graph.nets
                if net.net_class
                in {NetClass.TRACK, NetClass.DARK_TRACK, NetClass.SWITCH_OS}
            ),
            key=lambda net: min(
                (
                    placements.placements[reference].x
                    for reference, _pin in net.nodes
                    if reference in placements.placements
                ),
                default=0.0,
            ),
        )
        for net in ordered_nets:
            endpoints = tuple(sorted({reference for reference, _pin in net.nodes}))
            layout_endpoints = tuple(
                endpoint
                for endpoint in endpoints
                if endpoint in placements.placements
                and graph.entities[endpoint].kind in _LAYOUT_ANCHOR_KINDS
            )
            endpoint_anchors = tuple(
                sorted(
                    (
                        endpoint,
                        min(
                            (
                                placements.placements[endpoint].x
                                for _reference, _pin in net.nodes
                                if _reference == endpoint
                                and endpoint in placements.placements
                            ),
                            default=0.0,
                        ),
                    )
                    for endpoint in layout_endpoints
                )
            )
            start_x = min((anchor for _endpoint, anchor in endpoint_anchors), default=0.0)
            end_x = max((anchor for _endpoint, anchor in endpoint_anchors), default=0.0)
            start_anchor = x_values.index(start_x) if start_x in x_values else 0
            end_anchor = x_values.index(end_x) if end_x in x_values else 0
            endpoint_anchor_by_reference = {
                endpoint: x_values.index(anchor) if anchor in x_values else 0
                for endpoint, anchor in endpoint_anchors
            }
            circuit = next(
                (
                    graph.entities[item].canonical_name
                    for item in endpoints
                    if graph.entities[item].kind is EntityKind.TRACK_CIRCUIT
                ),
                "",
            )
            bumper_x = [
                placements.placements[reference].x
                for reference in endpoints
                if graph.entities[reference].kind is EntityKind.BUMPER
                and reference in placements.placements
            ]
            is_local_stub = (
                net.net_class is NetClass.DARK_TRACK and bool(bumper_x)
            )
            local_stub_direction = (
                "left"
                if is_local_stub and min(bumper_x) < start_x
                else "right"
                if is_local_stub
                else ""
            )
            graph.rail_spans.append(
                RailSpan(
                    net.name,
                    "",
                    endpoints,
                    circuit,
                    start_anchor,
                    start_anchor,
                    end_anchor,
                    tuple(
                        (
                            endpoint,
                            endpoint_anchor_by_reference[endpoint],
                        )
                        for endpoint, anchor in endpoint_anchors
                    ),
                    tuple(
                        endpoint
                        for endpoint in endpoints
                        if graph.entities[endpoint].kind
                        in {EntityKind.IRJ, EntityKind.IRJ_SIGNAL}
                    ),
                    tuple(
                        (
                            graph.entities[reference].canonical_name,
                            {"1": "C", "2": "N", "3": "R"}[pin],
                            endpoint_anchor_by_reference[reference],
                        )
                        for reference, pin in net.nodes
                        if graph.entities[reference].kind
                        in {EntityKind.SWITCH_POWERED, EntityKind.SWITCH_LOCK}
                        and pin in {"1", "2", "3"}
                    ),
                    net.net_class is NetClass.DARK_TRACK,
                    is_local_stub,
                    local_stub_direction,
                )
            )
        self._derive_topology_rows(graph)
        self._derive_layout_attachments(graph, placements)
        self._solve_longitudinal_positions(graph)
        resolve_board_components(graph)

    def _derive_topology_rows(self, graph: PlantGraph) -> None:
        """Assign rail rows by C/N/R and IRJ topology, anchored at main track."""
        port_net = {
            (reference, pin): net.name
            for net in graph.nets
            if net.net_class
            in {NetClass.TRACK, NetClass.DARK_TRACK, NetClass.SWITCH_OS}
            for reference, pin in net.nodes
        }
        adjacent: dict[str, list[tuple[str, int]]] = {}
        if not graph.turnout_layouts:
            graph.turnout_layouts = [
                TurnoutLayout(
                    entity.canonical_name,
                    graph.switch_geometries[entity.canonical_name].cn_heading,
                    "",
                    "",
                    "",
                    order,
                )
                for order, entity in enumerate(
                    sorted(
                        (
                            entity
                            for entity in graph.entities.values()
                            if entity.kind
                            in {EntityKind.SWITCH_POWERED, EntityKind.SWITCH_LOCK}
                            and entity.canonical_name in graph.switch_geometries
                        ),
                        key=lambda entity: entity.canonical_name,
                    )
                )
            ]

        def connect(first: str, second: str, delta: int) -> None:
            if not first or not second:
                return
            adjacent.setdefault(first, []).append((second, delta))
            adjacent.setdefault(second, []).append((first, -delta))

        for entity in graph.entities.values():
            if entity.kind in {EntityKind.IRJ, EntityKind.IRJ_SIGNAL}:
                connect(
                    port_net.get((entity.reference, "1"), ""),
                    port_net.get((entity.reference, "2"), ""),
                    0,
                )
            elif entity.kind in {EntityKind.SWITCH_POWERED, EntityKind.SWITCH_LOCK}:
                c_net = port_net.get((entity.reference, "1"), "")
                n_net = port_net.get((entity.reference, "2"), "")
                r_net = port_net.get((entity.reference, "3"), "")
                connect(c_net, n_net, 0)
                geometry = graph.switch_geometries.get(entity.canonical_name)
                reverse_delta = self._layout_reverse_delta(geometry)
                connect(c_net, r_net, reverse_delta)
            elif entity.kind is EntityKind.DERAIL:
                connect(
                    port_net.get((entity.reference, "1"), ""),
                    port_net.get((entity.reference, "2"), ""),
                    0,
                )

        lanes: dict[str, int] = {}
        pending = [
            terminal.net_name
            for terminal in graph.terminals
            if terminal.designation == "MT" and terminal.net_name in adjacent
        ]
        if not pending:
            pending = [name for name in ("1SA",) if name in adjacent]
        if not pending:
            pending = sorted(adjacent)
        for seed in pending:
            lanes[seed] = 0
        while pending:
            current = pending.pop(0)
            if current not in lanes:
                continue
            for neighbor, delta in adjacent.get(current, []):
                proposed = lanes[current] + delta
                if neighbor not in lanes:
                    lanes[neighbor] = proposed
                    pending.append(neighbor)
        if not lanes:
            return
        grouped: dict[int, list[str]] = {}
        for net_name, lane in lanes.items():
            grouped.setdefault(lane, []).append(net_name)
        graph.rail_rows = [
            RailRow(
                name=f"rail-{lane:+d}",
                lane=lane + 1,
                priority=abs(lane),
                circuits=tuple(sorted(names)),
            )
            for lane, names in sorted(grouped.items())
        ]
        row_for_net = {
            name: f"rail-{lane:+d}"
            for name, lane in lanes.items()
        }
        graph.rail_spans = [
            RailSpan(
                span.name,
                row_for_net.get(span.name, span.row_name),
                span.endpoints,
                span.circuit_name,
                span.order,
                span.start_anchor,
                span.end_anchor,
                span.endpoint_anchors,
                span.irj_endpoints,
                span.turnout_ports,
                span.is_dark,
                span.is_local_stub,
                span.local_stub_direction,
            )
            for span in graph.rail_spans
        ]
        graph.turnout_layouts = [
            TurnoutLayout(
                turnout.switch_name,
                turnout.cn_heading,
                row_for_net.get(port_net.get((f"SW{turnout.switch_name}", "1"), ""), turnout.c_row),
                row_for_net.get(port_net.get((f"SW{turnout.switch_name}", "2"), ""), turnout.n_row),
                row_for_net.get(port_net.get((f"SW{turnout.switch_name}", "3"), ""), turnout.r_row),
                turnout.order,
            )
            for turnout in graph.turnout_layouts
        ]

    def _derive_layout_attachments(
        self,
        graph: PlantGraph,
        placements: SchematicPlacementModel,
    ) -> None:
        """Attach turnouts, signal bases, and terminals to solved layout rows."""
        port_net = {
            (reference, pin): net.name
            for net in graph.nets
            if net.net_class
            in {NetClass.TRACK, NetClass.DARK_TRACK, NetClass.SWITCH_OS}
            for reference, pin in net.nodes
        }
        row_for_net = {
            span.name: span.row_name
            for span in graph.rail_spans
        }

        def row_for_reference(reference: str) -> str:
            rows = {
                row_for_net[net_name]
                for (net_reference, _pin), net_name in port_net.items()
                if net_reference == reference and net_name in row_for_net
            }
            return sorted(rows)[0] if rows else ""

        x_values = self._layout_x_values(graph, placements)

        def anchor_for_reference(reference: str) -> int:
            placement = placements.placements.get(reference)
            if placement is None or not x_values:
                return 0
            if placement.x in x_values:
                return x_values.index(placement.x)
            return min(
                range(len(x_values)),
                key=lambda index: abs(x_values[index] - placement.x),
            )

        turnouts = sorted(
            (
                entity
                for entity in graph.entities.values()
                if entity.kind in {EntityKind.SWITCH_POWERED, EntityKind.SWITCH_LOCK}
                and entity.canonical_name in graph.switch_geometries
            ),
            key=lambda entity: (
                anchor_for_reference(entity.reference),
                entity.canonical_name,
            ),
        )
        section_by_name = {
            section.name: section
            for section in graph.board_sections
        }
        graph.turnout_layouts = [
            TurnoutLayout(
                switch_name=entity.canonical_name,
                cn_heading=graph.switch_geometries[entity.canonical_name].cn_heading,
                c_row=row_for_net.get(port_net.get((entity.reference, "1"), ""), ""),
                n_row=row_for_net.get(port_net.get((entity.reference, "2"), ""), ""),
                r_row=row_for_net.get(port_net.get((entity.reference, "3"), ""), ""),
                order=anchor_for_reference(entity.reference),
                actuator_kind=(
                    TurnoutActuatorKind.LOCK
                    if entity.kind is EntityKind.SWITCH_LOCK
                    else TurnoutActuatorKind.SWITCH
                ),
                actuator_flipped=(
                    placements.placements[entity.reference].mirror == "y"
                ),
                section_index=(
                    section_by_name[
                        (entity.fields.get("CP") or "").strip()
                    ].index
                    if (entity.fields.get("CP") or "").strip()
                    in section_by_name
                    else None
                ),
            )
            for entity in turnouts
        ]
        graph.signal_bases = [
            SignalBase(
                mast_name=face.mast_name,
                mast_reference=face.mast_reference,
                irj_reference=face.irj_reference,
                row_name=row_for_reference(face.irj_reference),
                direction=face.direction,
                anchor=anchor_for_reference(face.irj_reference),
            )
            for face in graph.signal_faces
        ]
        if not placements.placements:
            return
        terminal_placements = [
            placements.placements[terminal.reference]
            for terminal in graph.terminals
            if terminal.reference in placements.placements
        ]
        if not terminal_placements:
            return
        left_x = min(placement.x for placement in terminal_placements)
        right_x = max(placement.x for placement in terminal_placements)
        graph.board_terminals = [
            BoardTerminal(
                name=terminal.designation,
                row_name=row_for_net.get(terminal.net_name, ""),
                side=(
                    "left"
                    if abs(placements.placements[terminal.reference].x - left_x)
                    <= abs(placements.placements[terminal.reference].x - right_x)
                    else "right"
                ),
                anchor=anchor_for_reference(terminal.reference),
                is_plant_edge=terminal.kind is EntityKind.NEXT_CP,
                span_name=terminal.net_name,
            )
            for terminal in graph.terminals
            if terminal.reference in placements.placements
        ]
        graph.track_circuit_lamps = [
            TrackCircuitLamp(
                circuit_name=span.circuit_name,
                span_name=span.name,
                row_name=span.row_name,
                start_anchor=span.start_anchor,
                end_anchor=span.end_anchor,
            )
            for span in graph.rail_spans
            if span.circuit_name and not span.is_dark
        ]

    @staticmethod
    def _solve_longitudinal_positions(graph: PlantGraph) -> None:
        """Resolve board anchors with protected signal doglegs and dark-track slack."""
        anchors = {
            anchor
            for span in graph.rail_spans
            for anchor in (span.start_anchor, span.end_anchor)
        }
        anchors.update(turnout.order for turnout in graph.turnout_layouts)
        anchors.update(signal.anchor for signal in graph.signal_bases)
        anchors.update(terminal.anchor for terminal in graph.board_terminals)
        if len(anchors) < 2:
            graph.longitudinal_positions = {0: 0.0}
            return
        anchor_count = max(anchors) + 1
        dark_intervals = {
            interval
            for span in graph.rail_spans
            if span.is_dark
            for interval in range(span.start_anchor, span.end_anchor)
        }
        signal_anchors = {
            signal.irj_reference: signal.anchor
            for signal in graph.signal_bases
        }
        dogleg_intervals = {
            min(signal_anchors[reference], turnout_anchor)
            for span in graph.rail_spans
            for reference, _anchor in span.endpoint_anchors
            if reference in signal_anchors
            for _switch_name, _port, turnout_anchor in span.turnout_ports
            if abs(signal_anchors[reference] - turnout_anchor) == 1
        }
        edge_circuit_intervals = {
            interval
            for span in graph.rail_spans
            if span.circuit_name
            and (span.start_anchor == 0 or span.end_anchor == anchor_count - 1)
            for interval in range(span.start_anchor, span.end_anchor)
        }
        intervals = tuple(
            LongitudinalInterval(
                start_anchor=index,
                end_anchor=index + 1,
                minimum_units=(
                    0.25
                    if index in dogleg_intervals
                    else 0.18
                    if index in edge_circuit_intervals
                    else 0.06
                ),
                flexibility_weight=(
                    2.0
                    if index in dogleg_intervals
                    else 3.0
                    if index in edge_circuit_intervals
                    else 0.15
                    if index in dark_intervals
                    else 1.0
                ),
            )
            for index in range(anchor_count - 1)
        )
        fixed_positions = {
            turnout.order: graph.board_sections[turnout.section_index].center_units
            for turnout in graph.turnout_layouts
            if turnout.section_index is not None
        }
        section_turnouts = sorted(
            (
                turnout
                for turnout in graph.turnout_layouts
                if turnout.section_index is not None
            ),
            key=lambda turnout: turnout.order,
        )
        for span in graph.rail_spans:
            if not span.circuit_name:
                continue
            for left, right in zip(section_turnouts, section_turnouts[1:]):
                if not (
                    left.order < span.start_anchor < span.end_anchor < right.order
                ):
                    continue
                midpoint = (
                    fixed_positions[left.order] + fixed_positions[right.order]
                ) / 2.0
                fixed_positions[span.start_anchor] = midpoint - 0.20
                fixed_positions[span.end_anchor] = midpoint + 0.20
        graph.longitudinal_positions = LongitudinalLayoutSolver().solve(
            anchor_count=anchor_count,
            width_units=float(graph.board_width_units),
            intervals=intervals,
            fixed_positions=fixed_positions,
        )

    @staticmethod
    def _layout_x_values(
        graph: PlantGraph,
        placements: SchematicPlacementModel,
    ) -> list[float]:
        """Return source positions for semantic model-board anchor devices."""
        return sorted(
            {
                placements.placements[entity.reference].x
                for entity in graph.entities.values()
                if entity.kind in _LAYOUT_ANCHOR_KINDS
                and entity.reference in placements.placements
            }
        )

    @staticmethod
    def _layout_reverse_delta(geometry: SwitchGeometry | None) -> int:
        """Return the global board-row delta for a turnout C-to-R crossing."""
        if geometry is None:
            return -1
        delta = 1 if geometry.reverse_side is TurnoutHand.LEFT else -1
        if geometry.cn_heading in {SchematicHeading.LEFT, SchematicHeading.DOWN}:
            delta *= -1
        return delta

    def _derive_switch_geometries(
        self,
        graph: PlantGraph,
        library: LibraryModel,
        netlist: NetlistModel,
        placements: SchematicPlacementModel,
    ) -> None:
        """Derive C-to-N heading and reverse-leg hand from source symbol geometry."""
        for reference, entity in graph.entities.items():
            if entity.kind not in {
                EntityKind.SWITCH_POWERED,
                EntityKind.SWITCH_LOCK,
            }:
                continue
            placement = placements.placements.get(reference)
            component = netlist.components.get(reference)
            if placement is None or component is None or not entity.canonical_name:
                continue
            symbol = library.get(component.part)
            if symbol is None:
                continue
            by_name = {pin.name.upper(): pin for pin in symbol.pins}
            if not {"C", "N", "R"} <= by_name.keys():
                continue
            c = self._transform_pin(
                by_name["C"].x, by_name["C"].y, placement.rotation, placement.mirror
            )
            n = self._transform_pin(
                by_name["N"].x, by_name["N"].y, placement.rotation, placement.mirror
            )
            r = self._transform_pin(
                by_name["R"].x, by_name["R"].y, placement.rotation, placement.mirror
            )
            cn_x, cn_y = n[0] - c[0], n[1] - c[1]
            cr_x, cr_y = r[0] - c[0], r[1] - c[1]
            cross = cn_x * cr_y - cn_y * cr_x
            if (
                (math.isclose(cn_x, 0.0) and math.isclose(cn_y, 0.0))
                or math.isclose(cross, 0.0)
            ):
                continue
            graph.switch_geometries[entity.canonical_name] = SwitchGeometry(
                switch_name=entity.canonical_name,
                cn_heading=self._schematic_heading(cn_x, cn_y),
                # KiCad schematic coordinates increase downward, so positive
                # screen-space cross product means the R leg is to the right.
                reverse_side=(
                    TurnoutHand.RIGHT if cross > 0.0 else TurnoutHand.LEFT
                ),
            )

    @staticmethod
    def _rotate_pin(x: float, y: float, rotation: float) -> tuple[float, float]:
        """Return a library pin vector after its placed-symbol rotation."""
        radians = math.radians(rotation)
        return (
            x * math.cos(radians) - y * math.sin(radians),
            x * math.sin(radians) + y * math.cos(radians),
        )

    @classmethod
    def _transform_pin(
        cls,
        x: float,
        y: float,
        rotation: float,
        mirror: str,
    ) -> tuple[float, float]:
        """Return a pin vector after KiCad reflection and rotation."""
        if mirror == "y":
            x = -x
        elif mirror == "x":
            y = -y
        return cls._rotate_pin(x, y, rotation)

    @staticmethod
    def _schematic_heading(x: float, y: float) -> SchematicHeading:
        """Return the dominant page-axis direction for a C-to-N vector."""
        if abs(x) >= abs(y):
            return SchematicHeading.RIGHT if x > 0 else SchematicHeading.LEFT
        return SchematicHeading.DOWN if y > 0 else SchematicHeading.UP

    def _build_entities(
        self,
        graph: PlantGraph,
        library: LibraryModel,
        netlist: NetlistModel,
    ) -> None:
        for ref, comp in sorted(netlist.components.items()):
            kind = _PART_KIND.get(comp.part, EntityKind.UNKNOWN)
            if kind is EntityKind.UNKNOWN:
                graph.diagnostics.append(
                    Diagnostic(
                        severity=DiagnosticSeverity.SEMANTIC,
                        code="unknown_symbol",
                        message=f"Unknown railroad symbol part '{comp.part}'",
                        entity_ref=ref,
                    )
                )
            canonical, name_diags = self._canonical_name(kind, comp)
            graph.diagnostics.extend(name_diags)
            graph.entities[ref] = PlantEntity(
                reference=ref,
                kind=kind,
                lib_id=comp.lib_id,
                value=comp.value,
                canonical_name=canonical,
                fields=dict(comp.fields),
            )
            # Pin-contract drift: library must know the part when present.
            if comp.part and library.get(comp.part) is None:
                graph.diagnostics.append(
                    Diagnostic(
                        severity=DiagnosticSeverity.SEMANTIC,
                        code="missing_library_symbol",
                        message=(
                            f"Netlist part '{comp.part}' is not in the shared library"
                        ),
                        entity_ref=ref,
                    )
                )
            elif comp.part:
                self._check_pin_contract(graph, ref, comp, library)

    def _canonical_name(
        self,
        kind: EntityKind,
        comp: NetlistComponent,
    ) -> tuple[str, list[Diagnostic]]:
        diags: list[Diagnostic] = []
        ref = comp.reference
        value = (comp.value or "").strip()
        if value == "~":
            value = ""

        if kind in (EntityKind.SWITCH_POWERED, EntityKind.SWITCH_LOCK):
            match = _SWITCH_REF_RE.match(ref)
            if not match:
                diags.append(
                    Diagnostic(
                        severity=DiagnosticSeverity.SEMANTIC,
                        code="bad_switch_reference",
                        message=f"Switch reference '{ref}' does not match SW<name>",
                        entity_ref=ref,
                    )
                )
                return ref, diags
            return match.group(1), diags

        if kind is EntityKind.DERAIL:
            match = re.fullmatch(r"(\d+)(D)?", value.upper())
            if match is None:
                diags.append(
                    Diagnostic(
                        severity=DiagnosticSeverity.SEMANTIC,
                        code="bad_derail_value",
                        message=(
                            f"DERAIL '{ref}' Value '{value}' must be a unique "
                            "numeric control ID or <switch>D"
                        ),
                        entity_ref=ref,
                    )
                )
                return value or ref, diags
            return f"{match.group(1)}{'D' if match.group(2) else ''}", diags

        if kind in (
            EntityKind.MAST_SINGLE,
            EntityKind.MAST_DOUBLE,
            EntityKind.MAST_DWARF,
        ):
            if not value:
                diags.append(
                    Diagnostic(
                        severity=DiagnosticSeverity.SEMANTIC,
                        code="missing_mast_value",
                        message=f"Mast '{ref}' has empty Value (expected proper name)",
                        entity_ref=ref,
                    )
                )
                return ref, diags
            if not _MAST_VALUE_RE.match(value):
                diags.append(
                    Diagnostic(
                        severity=DiagnosticSeverity.SEMANTIC,
                        code="bad_mast_value",
                        message=(
                            f"Mast '{ref}' Value '{value}' does not match "
                            "<signal><N|S><heads>"
                        ),
                        entity_ref=ref,
                    )
                )
            ref_match = _MAST_REF_RE.match(ref)
            val_match = _MAST_VALUE_RE.match(value)
            if ref_match and val_match:
                if ref_match.group(1) != val_match.group(1) or ref_match.group(
                    2
                ) != val_match.group(2):
                    diags.append(
                        Diagnostic(
                            severity=DiagnosticSeverity.WARNING,
                            code="mast_ref_value_mismatch",
                            message=(
                                f"Mast '{ref}' Reference signal/dir does not match "
                                f"Value '{value}'"
                            ),
                            entity_ref=ref,
                        )
                    )
            return value, diags

        if kind is EntityKind.SIGNAL_HEAD:
            if not value or not _HEAD_VALUE_RE.match(value):
                diags.append(
                    Diagnostic(
                        severity=DiagnosticSeverity.SEMANTIC,
                        code="bad_head_value",
                        message=(
                            f"Head '{ref}' Value '{value}' must be a single head letter"
                        ),
                        entity_ref=ref,
                    )
                )
            return value or ref, diags

        if kind is EntityKind.TRACK_CIRCUIT:
            if not value:
                diags.append(
                    Diagnostic(
                        severity=DiagnosticSeverity.SEMANTIC,
                        code="missing_track_circuit_name",
                        message=f"Track Circuit '{ref}' needs a Value name",
                        entity_ref=ref,
                    )
                )
            return value or ref, diags

        if kind is EntityKind.DIRECTION:
            if not value:
                diags.append(
                    Diagnostic(
                        severity=DiagnosticSeverity.SEMANTIC,
                        code="missing_dot_value",
                        message=(
                            f"Direction marker '{ref}' needs an operating-designation Value"
                        ),
                        entity_ref=ref,
                    )
                )
            if not (comp.fields.get("Rulebook") or "").strip():
                diags.append(
                    Diagnostic(
                        severity=DiagnosticSeverity.SEMANTIC,
                        code="missing_dot_rulebook",
                        message=f"Direction marker '{ref}' needs a Rulebook field",
                        entity_ref=ref,
                    )
                )
            return value or ref, diags

        if kind is EntityKind.OPERATING_POLICY:
            if not value:
                diags.append(
                    Diagnostic(
                        severity=DiagnosticSeverity.SEMANTIC,
                        code="missing_policy_track_name",
                        message=(
                            f"Operating policy marker '{ref}' needs a track-name Value"
                        ),
                        entity_ref=ref,
                    )
                )
            for field_name in ("Rulebook", "Direction"):
                if not (comp.fields.get(field_name) or "").strip():
                    diags.append(
                        Diagnostic(
                            severity=DiagnosticSeverity.SEMANTIC,
                            code=f"missing_policy_{field_name.lower()}",
                            message=(
                                f"Operating policy marker '{ref}' needs a "
                                f"{field_name} field"
                            ),
                            entity_ref=ref,
                        )
                    )
            return value or ref, diags

        if kind in (
            EntityKind.NEXT_CP,
            EntityKind.MAIN_HOUSE,
            EntityKind.MAINTAINER_CALL,
            EntityKind.ROUTE,
        ):
            return value or ref, diags

        if kind in (EntityKind.IRJ, EntityKind.IRJ_SIGNAL, EntityKind.BUMPER):
            # IRJs/Bumpers are not user-named; technical ref is enough.
            return ref, diags

        if kind is EntityKind.MILEPOST:
            return value or ref, diags

        if kind is EntityKind.MAINTAINER:
            return value or ref, diags

        return ref, diags

    def _check_pin_contract(
        self,
        graph: PlantGraph,
        ref: str,
        comp: NetlistComponent,
        library: LibraryModel,
    ) -> None:
        symbol = library.get(comp.part)
        if symbol is None:
            return
        required = _REQUIRED_PINS.get(_PART_KIND.get(comp.part, EntityKind.UNKNOWN))
        if not required:
            return
        lib_nums = {pin.number for pin in symbol.pins}
        missing = sorted(required - lib_nums)
        if missing:
            graph.diagnostics.append(
                Diagnostic(
                    severity=DiagnosticSeverity.SEMANTIC,
                    code="library_pin_contract",
                    message=(
                        f"Library symbol '{comp.part}' missing required pin numbers "
                        f"{missing}"
                    ),
                    entity_ref=ref,
                )
            )

    def _track_circuits_on_net(
        self,
        graph: PlantGraph,
        net: Net,
    ) -> list[PlantEntity]:
        """Return Track Circuit marker entities attached to one rail net."""
        return [
            entity
            for node in net.nodes
            if (entity := graph.entities.get(node.reference)) is not None
            and entity.kind is EntityKind.TRACK_CIRCUIT
        ]

    def _classify_nets(self, graph: PlantGraph, netlist: NetlistModel) -> None:
        for net in netlist.nets:
            net_class = self._classify_one_net(graph, net)
            if net_class is NetClass.TRACK and self._has_dark_track_marker(
                graph,
                net,
            ):
                net_class = NetClass.DARK_TRACK
            label = self._authoritative_label(net.name)
            track_circuits = self._track_circuits_on_net(graph, net)
            if len(track_circuits) > 1:
                graph.diagnostics.append(
                    Diagnostic(
                        severity=DiagnosticSeverity.SEMANTIC,
                        code="multiple_track_circuits_on_net",
                        message=(
                            f"Rail net '{net.name}' has multiple Track Circuit "
                            f"markers: {[tc.reference for tc in track_circuits]}"
                        ),
                        entity_ref=",".join(tc.reference for tc in track_circuits),
                    )
                )
            track_circuit = track_circuits[0] if len(track_circuits) == 1 else None
            if track_circuit is not None:
                display = track_circuit.canonical_name
                authoritative = True
                if label is not None and label != display:
                    graph.diagnostics.append(
                        Diagnostic(
                            severity=DiagnosticSeverity.SEMANTIC,
                            code="track_label_circuit_mismatch",
                            message=(
                                f"Rail net label '{label}' disagrees with Track "
                                f"Circuit '{display}'"
                            ),
                            entity_ref=track_circuit.reference,
                        )
                    )
            else:
                display = label if label is not None else net.name
                authoritative = label is not None
            graph.nets.append(
                PlantNet(
                    name=display,
                    net_class=net_class,
                    raw_name=net.name,
                    nodes=tuple((n.reference, n.pin) for n in net.nodes),
                    authoritative_label=authoritative,
                )
            )

    def _has_dark_track_marker(self, graph: PlantGraph, net: Net) -> bool:
        """Return True when a Rule 6.28 marker defines an untracked segment."""
        for node in net.nodes:
            entity = graph.entities.get(node.reference)
            if entity is None or entity.kind is not EntityKind.OPERATING_POLICY:
                continue
            rulebook = (entity.fields.get("Rulebook") or "").lower()
            if rulebook.replace("rule", "").strip().startswith("6.28"):
                return True
        return False

    def _classify_one_net(self, graph: PlantGraph, net: Net) -> NetClass:
        if net.name.startswith("unconnected-"):
            return NetClass.UNCONNECTED

        roles: set[str] = set()
        touches_switch_os = False
        for node in net.nodes:
            entity = graph.entities.get(node.reference)
            if entity is None:
                continue
            kind = entity.kind
            pin = node.pin
            if kind in (EntityKind.SWITCH_POWERED, EntityKind.SWITCH_LOCK) and pin in {
                "1",
                "2",
                "3",
            }:
                touches_switch_os = True
            if pin in _TRACK_PINS.get(kind, frozenset()):
                roles.add("track")
            if pin in _SIGNAL_ATTACH_PINS.get(kind, frozenset()):
                roles.add("signal")
            if pin in _HEAD_ATTACH_PINS.get(kind, frozenset()):
                roles.add("head")

        if roles == {"signal"}:
            return NetClass.SIGNAL_ATTACHMENT
        if roles == {"head"}:
            return NetClass.HEAD_ATTACHMENT
        if "signal" in roles and "track" not in roles and "head" not in roles:
            return NetClass.SIGNAL_ATTACHMENT
        if "head" in roles and "track" not in roles:
            return NetClass.HEAD_ATTACHMENT
        if touches_switch_os and "track" in roles:
            # C/N/R legs belong to derived <switch>T1; not separately labeled.
            return NetClass.SWITCH_OS
        if "track" in roles:
            return NetClass.TRACK
        return NetClass.OTHER

    def _authoritative_label(self, raw_name: str) -> Optional[str]:
        """Return user label if net name is not KiCad-generated."""
        name = raw_name.strip()
        if not name:
            return None
        if name.startswith("unconnected-"):
            return None
        if name.startswith("Net-(") or name.startswith("Net-"):
            return None
        if name.startswith("/"):
            name = name[1:]
        if not name:
            return None
        return name

    def _check_required_pins(self, graph: PlantGraph, netlist: NetlistModel) -> None:
        connected: dict[str, set[str]] = {ref: set() for ref in graph.entities}
        intentional_nc: dict[str, set[str]] = {ref: set() for ref in graph.entities}
        bare_open: dict[str, set[str]] = {ref: set() for ref in graph.entities}

        for net in netlist.nets:
            for node in net.nodes:
                if node.reference not in connected:
                    continue
                if self._node_is_intentional_nc(net.name, node.pintype):
                    intentional_nc[node.reference].add(node.pin)
                elif net.name.startswith("unconnected-"):
                    bare_open[node.reference].add(node.pin)
                else:
                    connected[node.reference].add(node.pin)

        for ref, entity in graph.entities.items():
            required = _REQUIRED_PINS.get(entity.kind)
            if not required:
                continue

            if entity.kind is EntityKind.DIRECTION:
                self._check_direction_pins(
                    graph,
                    ref,
                    required,
                    connected.get(ref, set()),
                    intentional_nc.get(ref, set()),
                    bare_open.get(ref, set()),
                )
                continue

            # Intentional NC satisfies a required pin (e.g. unused bumper end).
            missing = sorted(
                required
                - connected.get(ref, set())
                - intentional_nc.get(ref, set())
            )
            if missing:
                graph.diagnostics.append(
                    Diagnostic(
                        severity=DiagnosticSeverity.SEMANTIC,
                        code="unconnected_required_pin",
                        message=(
                            f"{entity.kind.value} '{ref}' required pins not connected: "
                            f"{missing}"
                        ),
                        entity_ref=ref,
                    )
                )

        # Mast SIGNAL must attach to an IRJ-Signal SIGNAL pin.
        for net in graph.nets:
            if net.net_class is not NetClass.SIGNAL_ATTACHMENT:
                continue
            kinds = []
            for ref, pin in net.nodes:
                ent = graph.entities.get(ref)
                if ent:
                    kinds.append((ent.kind, pin, ref))
            has_irj = any(
                k is EntityKind.IRJ_SIGNAL and pin == "3" for k, pin, _ in kinds
            )
            has_mast = any(
                k
                in (
                    EntityKind.MAST_SINGLE,
                    EntityKind.MAST_DOUBLE,
                    EntityKind.MAST_DWARF,
                )
                and pin == "1"
                for k, pin, _ in kinds
            )
            if has_mast and not has_irj:
                refs = ",".join(r for _, _, r in kinds)
                graph.diagnostics.append(
                    Diagnostic(
                        severity=DiagnosticSeverity.SEMANTIC,
                        code="mast_signal_not_on_irj",
                        message=(
                            f"Signal attachment net '{net.raw_name}' connects a Mast "
                            "SIGNAL pin without an IRJ-Signal SIGNAL pin"
                        ),
                        entity_ref=refs,
                    )
                )

    def _node_is_intentional_nc(self, net_name: str, pintype: str) -> bool:
        """Return True when KiCad marks a pin as intentionally not connected.

        kicad-cli netlists use pintype suffixes such as ``passive+no_connect``
        when a no-connect helper is placed on the pin.
        """
        pt = (pintype or "").lower()
        if "no_connect" in pt:
            return True
        # Defensive: some exports only encode NC in the synthetic net name.
        return net_name.startswith("unconnected-") and "no_connect" in pt

    def _check_direction_pins(
        self,
        graph: PlantGraph,
        ref: str,
        required: frozenset[str],
        connected: set[str],
        intentional_nc: set[str],
        bare_open: set[str],
    ) -> None:
        """Apply DoT pin connectivity policy.

        - Intentional NC (no-connect helper) → ignore that pin.
        - One pin connected, other bare-open (no helper) → warning.
        - Both pins bare-open / neither connected nor NC → semantic error.
        """
        satisfied = connected | intentional_nc
        unresolved = required - satisfied

        if not unresolved:
            return

        if not connected and not intentional_nc:
            graph.diagnostics.append(
                Diagnostic(
                    severity=DiagnosticSeverity.SEMANTIC,
                    code="direction_fully_unconnected",
                    message=(
                        f"Direction marker '{ref}' has no connected track pin "
                        f"(open pins: {sorted(required)})"
                    ),
                    entity_ref=ref,
                )
            )
            return

        # At least one side is in-circuit; remaining open pins lack NC helper.
        open_pins = sorted(unresolved)
        graph.diagnostics.append(
            Diagnostic(
                severity=DiagnosticSeverity.WARNING,
                code="direction_open_pin_without_nc",
                message=(
                    f"Direction marker '{ref}' has open pin(s) {open_pins} "
                    "without a no-connect helper"
                ),
                entity_ref=ref,
            )
        )

    def _derive_os_circuits(self, graph: PlantGraph) -> None:
        for entity in graph.entities.values():
            if entity.kind not in {
                EntityKind.SWITCH_POWERED,
                EntityKind.SWITCH_LOCK,
                EntityKind.DERAIL,
            }:
                continue
            if not entity.canonical_name:
                continue
            source_value = entity.fields.get("TC")
            if source_value is None:
                if entity.kind is EntityKind.DERAIL:
                    continue
                name = f"{entity.canonical_name}T1"
            else:
                name = source_value.strip()
                if not name:
                    continue
            graph.derived_track_circuits.append(
                DerivedTrackCircuit(
                    name=name,
                    switch_name=entity.canonical_name,
                    reason="standard_switch_os",
                )
            )

    def _check_track_net_labels(self, graph: PlantGraph) -> None:
        """Require labels only on user-facing track path nets.

        Ignored (no label required):
        - signal_attachment / head_attachment
        - unconnected (including intentional NC on DoT/Bumper)
        - switch_os (C/N/R legs covered by derived ``<switch>T1``)
        """
        for net in graph.nets:
            if net.net_class not in (NetClass.TRACK, NetClass.DARK_TRACK):
                continue
            if any(
                graph.entities[reference].kind is EntityKind.DERAIL
                for reference, _pin in net.nodes
                if reference in graph.entities
            ):
                continue
            if net.authoritative_label:
                continue
            if net.net_class is NetClass.DARK_TRACK:
                continue
            severity = (
                DiagnosticSeverity.WARNING
                if len(net.nodes) < 2
                else DiagnosticSeverity.SEMANTIC
            )
            graph.diagnostics.append(
                Diagnostic(
                    severity=severity,
                    code="unlabeled_track_net",
                    message=(
                        f"Track net '{net.raw_name}' has no authoritative label"
                    ),
                    entity_ref=",".join(f"{r}:{p}" for r, p in net.nodes),
                )
            )

    def _check_cp_allocations(self, graph: PlantGraph) -> None:
        """Warn when allocated appliances do not resolve to a Main House Value."""
        main_house_names = {
            entity.canonical_name
            for entity in graph.entities.values()
            if entity.kind is EntityKind.MAIN_HOUSE and entity.canonical_name
        }
        allocated_kinds = frozenset(
            {
                EntityKind.SWITCH_POWERED,
                EntityKind.SWITCH_LOCK,
                EntityKind.IRJ_SIGNAL,
                EntityKind.TRACK_CIRCUIT,
            }
        )
        for entity in graph.entities.values():
            if entity.kind not in allocated_kinds:
                continue
            cp_name = (entity.fields.get("CP") or "").strip()
            if not cp_name:
                graph.diagnostics.append(
                    Diagnostic(
                        severity=DiagnosticSeverity.WARNING,
                        code="missing_cp_allocation",
                        message=(
                            f"{entity.kind.value} '{entity.reference}' has no CP "
                            "allocation"
                        ),
                        entity_ref=entity.reference,
                    )
                )
            elif cp_name not in main_house_names:
                graph.diagnostics.append(
                    Diagnostic(
                        severity=DiagnosticSeverity.WARNING,
                        code="unknown_cp_allocation",
                        message=(
                            f"{entity.kind.value} '{entity.reference}' references "
                            f"unknown Main House Value '{cp_name}'"
                        ),
                        entity_ref=entity.reference,
                    )
                )
    def _check_dependent_derail_allocations(self, graph: PlantGraph) -> None:
        """Warn when a ``<switch>D`` derail is assigned outside its switch CP."""

        switches = {
            entity.canonical_name: entity
            for entity in graph.entities.values()
            if entity.kind in {EntityKind.SWITCH_POWERED, EntityKind.SWITCH_LOCK}
            and entity.canonical_name
        }
        for derail in graph.entities.values():
            if (
                derail.kind is not EntityKind.DERAIL
                or not derail.canonical_name.endswith("D")
            ):
                continue
            switch_name = derail.canonical_name[:-1]
            switch = switches.get(switch_name)
            if switch is None:
                graph.diagnostics.append(
                    Diagnostic(
                        severity=DiagnosticSeverity.SEMANTIC,
                        code="dependent_derail_unknown_switch",
                        message=(
                            f"Dependent DERAIL '{derail.reference}' references "
                            f"unknown controlling switch '{switch_name}'"
                        ),
                        entity_ref=derail.reference,
                    )
                )
                continue
            derail_cp = (derail.fields.get("CP") or "").strip()
            switch_cp = (switch.fields.get("CP") or "").strip()
            if derail_cp and switch_cp and derail_cp != switch_cp:
                graph.diagnostics.append(
                    Diagnostic(
                        severity=DiagnosticSeverity.WARNING,
                        code="dependent_derail_cp_mismatch",
                        message=(
                            f"Dependent DERAIL '{derail.reference}' is allocated "
                            f"to '{derail_cp}', but switch '{switch.reference}' "
                            f"is allocated to '{switch_cp}'"
                        ),
                        entity_ref=derail.reference,
                    )
                )

    def _check_switch_indications(self, graph: PlantGraph) -> None:
        """Require a valid NORMAL/REVERSE pair when a switch overrides caps."""
        from plant_graph.indications import parse_switch_indications

        for entity in graph.entities.values():
            if entity.kind not in {
                EntityKind.SWITCH_POWERED,
                EntityKind.SWITCH_LOCK,
            }:
                continue
            value = (entity.fields.get("Indications") or "").strip()
            if not value:
                continue
            try:
                parse_switch_indications(value)
            except ValueError as exc:
                graph.diagnostics.append(
                    Diagnostic(
                        severity=DiagnosticSeverity.SEMANTIC,
                        code="invalid_switch_indications",
                        message=(
                            f"Switch '{entity.reference}' Indications "
                            f"'{value}' is invalid: {exc}"
                        ),
                        entity_ref=entity.reference,
                    )
                )

    def _check_library_coverage(
        self,
        graph: PlantGraph,
        library: LibraryModel,
    ) -> None:
        # Informational: library may contain symbols unused by this plant.
        _ = library
        _ = graph
