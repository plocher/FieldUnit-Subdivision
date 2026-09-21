"""Pure longitudinal layout solving for static plant board projections."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING

from plant_graph.types import (
    BoardComponent,
    BoardComponentKind,
    BoardConnection,
    BoardPort,
    EntityKind,
    SchematicHeading,
)

if TYPE_CHECKING:
    from plant_graph.types import PlantGraph, RailSpan


@dataclass(frozen=True)
class LongitudinalInterval:
    """One ordered anchor interval with a hard minimum and flexible priority."""

    start_anchor: int
    end_anchor: int
    minimum_units: float
    flexibility_weight: float


class LongitudinalLayoutSolver:
    """Resolve ordered semantic anchors inside a fixed Main House width."""

    def solve(
        self,
        anchor_count: int,
        width_units: float,
        intervals: tuple[LongitudinalInterval, ...],
        fixed_positions: dict[int, float] | None = None,
    ) -> dict[int, float]:
        """Return monotonically increasing positions indexed by semantic anchor."""
        if anchor_count < 2:
            raise ValueError("At least two anchors are required")
        if width_units <= 0:
            raise ValueError("Layout width must be positive")
        expected = tuple(range(anchor_count - 1))
        by_start = {interval.start_anchor: interval for interval in intervals}
        if tuple(sorted(by_start)) != expected:
            raise ValueError("Intervals must cover each adjacent anchor pair once")
        if any(interval.end_anchor != interval.start_anchor + 1 for interval in intervals):
            raise ValueError("Intervals must connect adjacent ordered anchors")
        if any(interval.minimum_units < 0 for interval in intervals):
            raise ValueError("Interval minimums cannot be negative")
        if any(interval.flexibility_weight <= 0 for interval in intervals):
            raise ValueError("Interval flexibility weights must be positive")

        fixed = dict(fixed_positions or {})
        if 0 in fixed and fixed[0] != 0.0:
            raise ValueError("The first anchor must be fixed at zero")
        if (
            anchor_count - 1 in fixed
            and fixed[anchor_count - 1] != width_units
        ):
            raise ValueError("The final anchor must equal the layout width")
        fixed[0] = 0.0
        fixed[anchor_count - 1] = width_units
        if any(anchor < 0 or anchor >= anchor_count for anchor in fixed):
            raise ValueError("Fixed anchor is outside the layout")

        fixed_anchors = tuple(sorted(fixed))
        if any(
            fixed[right] <= fixed[left]
            for left, right in zip(fixed_anchors, fixed_anchors[1:])
        ):
            raise ValueError("Fixed anchors must increase with anchor order")

        positions: dict[int, float] = {}
        for first, last in zip(fixed_anchors, fixed_anchors[1:]):
            ordered = tuple(by_start[index] for index in range(first, last))
            minimum_total = sum(
                interval.minimum_units for interval in ordered
            )
            available = fixed[last] - fixed[first]
            if minimum_total > available:
                raise ValueError(
                    "Layout minimums exceed available fixed anchor width"
                )
            remaining = available - minimum_total
            weight_total = sum(
                interval.flexibility_weight for interval in ordered
            )
            positions[first] = fixed[first]
            for interval in ordered:
                distance = (
                    interval.minimum_units
                    + remaining
                    * interval.flexibility_weight
                    / weight_total
                )
                positions[interval.end_anchor] = (
                    positions[interval.start_anchor] + distance
                )
            positions[last] = fixed[last]
        return positions


_TURNOUT_HALF_UNITS = 0.12
_TURNOUT_BRANCH_RUN_UNITS = 0.42
_INLINE_GAP_HALF_UNITS = 0.035
_LOCAL_STUB_LENGTH_UNITS = 0.38
_TURNOUT_SIGNAL_DOGLEG_CLEARANCE_UNITS = 0.25


def resolve_board_components(graph: PlantGraph) -> None:
    """Populate canonical transformed ports and rail connections for one board."""
    components: list[BoardComponent] = []
    ports: dict[str, BoardPort] = {}
    turnouts = {turnout.switch_name: turnout for turnout in graph.turnout_layouts}

    def add_component(component: BoardComponent) -> None:
        components.append(component)
        for port in component.ports:
            if port.identifier in ports:
                raise ValueError(f"Duplicate board port '{port.identifier}'")
            ports[port.identifier] = port

    def add_port(
        component_id: str,
        name: str,
        x_units: float,
        row_name: str,
    ) -> BoardPort:
        return BoardPort(
            identifier=f"{component_id}:{name}",
            component_id=component_id,
            name=name,
            x_units=x_units,
            row_name=row_name,
        )

    for turnout in graph.turnout_layouts:
        component_id = f"turnout:{turnout.switch_name}"
        center_x = graph.longitudinal_positions[turnout.order]
        fallback_row = turnout.c_row or graph.rail_rows[0].name
        c_row = turnout.c_row or fallback_row
        n_row = turnout.n_row or fallback_row
        r_row = turnout.r_row or fallback_row
        mirror_x = turnout.cn_heading is SchematicHeading.LEFT
        direction = -1.0 if mirror_x else 1.0
        c_x = center_x - direction * _TURNOUT_HALF_UNITS
        n_x = center_x + direction * _TURNOUT_HALF_UNITS
        r_x = c_x + direction * _TURNOUT_BRANCH_RUN_UNITS
        add_component(
            BoardComponent(
                identifier=component_id,
                kind=BoardComponentKind.TURNOUT,
                label=turnout.switch_name,
                x_units=center_x,
                row_name=c_row,
                mirror_x=mirror_x,
                mirror_y=turnout.actuator_flipped,
                actuator_kind=turnout.actuator_kind,
                has_frog_lamp=turnout.has_frog_lamp,
                ports=(
                    add_port(component_id, "C", c_x, c_row),
                    add_port(component_id, "N", n_x, n_row),
                    add_port(component_id, "R", r_x, r_row),
                ),
            )
        )
    spans_by_endpoint: dict[str, list[RailSpan]] = defaultdict(list)

    span_rows_by_endpoint: dict[str, set[str]] = defaultdict(set)
    endpoint_anchor: dict[str, int] = {}
    for span in graph.rail_spans:
        for reference, anchor in span.endpoint_anchors:
            spans_by_endpoint[reference].append(span)
            span_rows_by_endpoint[reference].add(span.row_name)
            endpoint_anchor.setdefault(reference, anchor)
    irj_x_overrides: dict[str, float] = {}
    for span in graph.rail_spans:
        r_port_ids = (
            f"turnout:{switch_name}:R"
            for switch_name, port_name, _anchor in span.turnout_ports
            if port_name == "R"
        )
        r_port = next(
            (ports[port_id] for port_id in r_port_ids if port_id in ports),
            None,
        )
        if r_port is None:
            continue
        for reference, _anchor in span.endpoint_anchors:
            entity = graph.entities.get(reference)
            if entity is None or entity.kind not in {
                EntityKind.IRJ,
                EntityKind.IRJ_SIGNAL,
            }:
                continue
            continuation_x = [
                graph.longitudinal_positions[anchor]
                for peer in spans_by_endpoint[reference]
                if peer is not span
                for peer_reference, anchor in peer.endpoint_anchors
                if peer_reference != reference
            ]
            if not continuation_x:
                continue
            nearest = min(
                continuation_x,
                key=lambda value: abs(value - r_port.x_units),
            )
            irj_x_overrides[reference] = (
                r_port.x_units
                - _INLINE_GAP_HALF_UNITS
                - _TURNOUT_SIGNAL_DOGLEG_CLEARANCE_UNITS
                if nearest < r_port.x_units
                else (
                    r_port.x_units
                    + _INLINE_GAP_HALF_UNITS
                    + _TURNOUT_SIGNAL_DOGLEG_CLEARANCE_UNITS
                )
            )

    for reference, anchor in sorted(endpoint_anchor.items()):
        entity = graph.entities.get(reference)
        if entity is None:
            continue
        row_names = span_rows_by_endpoint[reference]
        row_name = sorted(row_names)[0] if row_names else ""
        x_units = irj_x_overrides.get(
            reference,
            graph.longitudinal_positions[anchor],
        )
        if entity.kind in {EntityKind.IRJ, EntityKind.IRJ_SIGNAL}:
            component_id = f"irj:{reference}"
            add_component(
                BoardComponent(
                    identifier=component_id,
                    kind=BoardComponentKind.IRJ,
                    label=reference,
                    x_units=x_units,
                    row_name=row_name,
                    ports=(
                        add_port(
                            component_id,
                            "left",
                            x_units - _INLINE_GAP_HALF_UNITS,
                            row_name,
                        ),
                        add_port(
                            component_id,
                            "right",
                            x_units + _INLINE_GAP_HALF_UNITS,
                            row_name,
                        ),
                    ),
                )
            )
        elif entity.kind is EntityKind.DERAIL:
            component_id = f"derail:{reference}"
            add_component(
                BoardComponent(
                    identifier=component_id,
                    kind=BoardComponentKind.DERAIL,
                    label=entity.canonical_name or reference,
                    x_units=x_units,
                    row_name=row_name,
                    ports=(
                        add_port(
                            component_id,
                            "C",
                            x_units - _INLINE_GAP_HALF_UNITS,
                            row_name,
                        ),
                        add_port(
                            component_id,
                            "N",
                            x_units + _INLINE_GAP_HALF_UNITS,
                            row_name,
                        ),
                    ),
                )
            )
        elif entity.kind not in {
            EntityKind.SWITCH_POWERED,
            EntityKind.SWITCH_LOCK,
        }:
            component_id = f"anchor:{reference}"
            add_component(
                BoardComponent(
                    identifier=component_id,
                    kind=BoardComponentKind.TERMINAL,
                    label=entity.canonical_name or reference,
                    x_units=x_units,
                    row_name=row_name,
                    ports=(add_port(component_id, "track", x_units, row_name),),
                )
            )

    for terminal in graph.board_terminals:
        component_id = f"terminal:{terminal.name}"
        if any(component.identifier == component_id for component in components):
            continue
        x_units = graph.longitudinal_positions.get(terminal.anchor, 0.0)
        add_component(
            BoardComponent(
                identifier=component_id,
                kind=BoardComponentKind.TERMINAL,
                label=terminal.name,
                x_units=x_units,
                row_name=terminal.row_name,
                ports=(
                    add_port(component_id, "track", x_units, terminal.row_name),
                ),
            )
        )

    for signal in graph.signal_bases:
        component_id = f"signal:{signal.mast_reference}"
        if any(component.identifier == component_id for component in components):
            continue
        x_units = next(
            (
                component.x_units
                for component in components
                if component.identifier == f"irj:{signal.irj_reference}"
            ),
            graph.longitudinal_positions.get(signal.anchor, 0.0),
        )
        add_component(
            BoardComponent(
                identifier=component_id,
                kind=BoardComponentKind.SIGNAL,
                label=signal.mast_name,
                x_units=x_units,
                row_name=signal.row_name,
                mirror_y=signal.direction == "LEFT",
            )
        )

    def turnout_port_id(span: RailSpan, anchor: int) -> str | None:
        for switch_name, port_name, port_anchor in span.turnout_ports:
            if port_anchor == anchor and switch_name in turnouts:
                return f"turnout:{switch_name}:{port_name}"
        return None

    def anchor_port_id(reference: str, other_x: float) -> str | None:
        entity = graph.entities.get(reference)
        if entity is None:
            return None
        if entity.kind in {EntityKind.IRJ, EntityKind.IRJ_SIGNAL}:
            component_id = f"irj:{reference}"
            center = next(
                component.x_units
                for component in components
                if component.identifier == component_id
            )
            side = "right" if other_x >= center else "left"
            return f"{component_id}:{side}"
        if entity.kind is EntityKind.DERAIL:
            component_id = f"derail:{reference}"
            center = next(
                component.x_units
                for component in components
                if component.identifier == component_id
            )
            side = "N" if other_x >= center else "C"
            return f"{component_id}:{side}"
        component_id = f"anchor:{reference}"
        if f"{component_id}:track" in ports:
            return f"{component_id}:track"
        return None

    connections: list[BoardConnection] = []
    for span in graph.rail_spans:
        start_x = graph.longitudinal_positions.get(span.start_anchor, 0.0)
        end_x = graph.longitudinal_positions.get(span.end_anchor, start_x)
        start_port = turnout_port_id(span, span.start_anchor)
        end_port = turnout_port_id(span, span.end_anchor)
        endpoint_by_anchor = defaultdict(list)
        for reference, anchor in span.endpoint_anchors:
            endpoint_by_anchor[anchor].append(reference)
        if start_port is None:
            for reference in endpoint_by_anchor[span.start_anchor]:
                start_port = anchor_port_id(
                    reference,
                    (
                        ports[end_port].x_units
                        if end_port is not None
                        else end_x
                    ),
                )
                if start_port is not None:
                    break
        if end_port is None:
            for reference in endpoint_by_anchor[span.end_anchor]:
                end_port = anchor_port_id(
                    reference,
                    (
                        ports[start_port].x_units
                        if start_port is not None
                        else start_x
                    ),
                )
                if end_port is not None:
                    break
        if span.is_local_stub:
            anchor_port = start_port or end_port
            if anchor_port is None:
                continue
            direction = -1.0 if span.local_stub_direction == "left" else 1.0
            anchor_reference = next(
                (
                    reference
                    for references in endpoint_by_anchor.values()
                    for reference in references
                    if graph.entities.get(reference, None) is not None
                    and graph.entities[reference].kind
                    in {EntityKind.IRJ, EntityKind.IRJ_SIGNAL}
                ),
                "",
            )
            if anchor_reference:
                anchor_port = (
                    f"irj:{anchor_reference}:"
                    f"{'left' if direction < 0.0 else 'right'}"
                )
            stub_id = f"stub:{span.name}"
            anchor = ports[anchor_port]
            stub_port = add_port(
                stub_id,
                "end",
                anchor.x_units + direction * _LOCAL_STUB_LENGTH_UNITS,
                span.row_name,
            )
            add_component(
                BoardComponent(
                    identifier=stub_id,
                    kind=BoardComponentKind.TERMINAL,
                    label="",
                    x_units=stub_port.x_units,
                    row_name=span.row_name,
                    ports=(stub_port,),
                )
            )
            start_port, end_port = anchor_port, stub_port.identifier
        if start_port is None or end_port is None or start_port == end_port:
            continue
        connections.append(
            BoardConnection(
                identifier=span.name,
                row_name=span.row_name,
                start_port_id=start_port,
                end_port_id=end_port,
                circuit_name=span.circuit_name,
                is_dark=span.is_dark,
                is_local_stub=span.is_local_stub,
            )
        )
    port_uses: dict[str, int] = defaultdict(int)
    for connection in connections:
        for port_id in (connection.start_port_id, connection.end_port_id):
            port = ports[port_id]
            if port.row_name != connection.row_name:
                raise ValueError(
                    f"Connection '{connection.identifier}' uses port "
                    f"'{port_id}' on a different row"
                )
            port_uses[port_id] += 1
    shared_ports = sorted(
        port_id for port_id, count in port_uses.items() if count > 1
    )
    if shared_ports:
        raise ValueError(
            "Board ports cannot terminate more than one connection: "
            + ", ".join(shared_ports)
        )
    graph.board_components = components
    graph.board_connections = connections
