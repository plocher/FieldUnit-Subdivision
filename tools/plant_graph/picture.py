"""Static topology-picture projection for a compiled plant graph."""

from __future__ import annotations

import json
import math
import re
import textwrap
from collections import defaultdict, deque
from dataclasses import dataclass
from html import escape

from plant_graph.types import (
    EntityKind,
    NetClass,
    PlantEntity,
    PlantGraph,
    Indication,
    SignalRoute,
    BoardComponent,
    BoardComponentKind,
    TurnoutActuatorKind,
)


_MAST_KINDS = frozenset(
    {
        EntityKind.MAST_SINGLE,
        EntityKind.MAST_DOUBLE,
        EntityKind.MAST_DWARF,
    }
)
_TOPOLOGY_KINDS = frozenset(
    {
        EntityKind.SWITCH_POWERED,
        EntityKind.SWITCH_LOCK,
        EntityKind.IRJ,
        EntityKind.IRJ_SIGNAL,
        EntityKind.NEXT_CP,
        EntityKind.BUMPER,
        EntityKind.DIRECTION,
    }
)
_TRACK_NET_CLASSES = frozenset(
    {
        NetClass.TRACK,
        NetClass.DARK_TRACK,
        NetClass.SWITCH_OS,
    }
)
_NATURAL_PARTS_RE = re.compile(r"(\d+)")
_SWIM_LANE_COUNT = 6
_SWIM_WIDTH = 850
_SWIM_HEIGHT = 1100
_BOARD_WIDTH = 1800
_BOARD_HEIGHT = 1050
_BOARD_MARGIN = 24.0
_LOGICAL_COLUMN_WIDTH = 192.0
_ROUTE_COLORS = (
    "#B91C1C",
    "#C2410C",
    "#A16207",
    "#15803D",
    "#0F766E",
    "#0369A1",
    "#4338CA",
    "#7E22CE",
    "#BE185D",
    "#475569",
)
_ASPECT_COLORS = {
    "green": "#22C55E",
    "yellow": "#FACC15",
    "red": "#EF4444",
    "unlit": "#111827",
}


@dataclass(frozen=True)
class _AspectPresentation:
    """Presentation-only mapping of a static indication to route aspects."""

    route_color: str
    head_colors: tuple[str, ...]
    flashing_heads: tuple[int, ...] = ()


_INDICATION_ASPECTS: dict[Indication, _AspectPresentation] = {
    Indication.CLEAR: _AspectPresentation("#22C55E", ("green", "red")),
    Indication.ADVANCED_APPROACH: _AspectPresentation(
        "#FACC15", ("yellow", "red"), (0,)
    ),
    Indication.APPROACH: _AspectPresentation("#FACC15", ("yellow", "red")),
    Indication.DIVERGING_CLEAR: _AspectPresentation(
        "#22C55E", ("red", "green")
    ),
    Indication.DIVERGING_ADVANCED_APPROACH: _AspectPresentation(
        "#FACC15", ("red", "yellow"), (1,)
    ),
    Indication.DIVERGING_APPROACH: _AspectPresentation(
        "#FACC15", ("red", "yellow")
    ),
    Indication.SECONDARY_DIVERGING_CLEAR: _AspectPresentation(
        "#22C55E", ("red", "green")
    ),
    Indication.SECONDARY_DIVERGING_ADVANCED_APPROACH: _AspectPresentation(
        "#FACC15", ("red", "yellow"), (1,)
    ),
    Indication.SECONDARY_DIVERGING_APPROACH: _AspectPresentation(
        "#FACC15", ("red", "yellow")
    ),
    Indication.RESTRICTING: _AspectPresentation(
        "#EF4444", ("red", "red"), (0,)
    ),
    Indication.DIVERGING_RESTRICTING: _AspectPresentation(
        "#EF4444", ("red", "red"), (1,)
    ),
    Indication.STOP: _AspectPresentation("#EF4444", ("red", "red")),
    Indication.UNLIT: _AspectPresentation("#64748B", ("unlit",)),
}


@dataclass(frozen=True)
class _SwimLaneItem:
    """One selected-route traversal item placed on a swim lane."""

    label: str
    lane: int
    x: float
    y: float
    kind: str


def render_model_board_svg(
    graph: PlantGraph,
) -> str:
    """Render the accepted route-free dispatcher board."""
    if not graph.rail_rows:
        raise ValueError("A compiled rail layout is required for a model board")
    if not graph.board_components:
        raise ValueError("Resolved board components are required for a model board")
    return _render_resolved_layout_svg(graph)


def render_route_board_svg(
    graph: PlantGraph,
    route_name: str | None = None,
) -> str:
    """Render static route validation over the accepted compiled board."""
    if not graph.rail_rows:
        raise ValueError("A compiled rail layout is required for a route board")
    if not graph.board_components:
        raise ValueError("Resolved board components are required for a route board")
    return _render_resolved_layout_svg(
        graph,
        route_name=route_name,
        include_route_selector=route_name is None,
    )



def _layout_width_units(graph: PlantGraph) -> int:
    """Return the declared number of two-inch model-board columns."""
    return max(graph.board_width_units, 1)


def _layout_view_width(graph: PlantGraph) -> float:
    """Return the SVG view width for the graph's logical board columns."""
    return _LOGICAL_COLUMN_WIDTH * _layout_width_units(graph) + 2 * _BOARD_MARGIN


def _component_ports(component: BoardComponent) -> dict[str, object]:
    """Return one resolved component's ports indexed by their semantic names."""
    return {port.name: port for port in component.ports}


def _port_x(port: object) -> float:
    """Return an SVG x coordinate from a resolved logical board port."""
    return _BOARD_MARGIN + getattr(port, "x_units") * _LOGICAL_COLUMN_WIDTH


def _render_turnout(
    component: BoardComponent,
    y_by_row: dict[str, float],
    include_label: bool,
    include_realization: bool = True,
) -> list[str]:
    """Render one turnout directly from its canonical C/N/R port positions."""
    ports = _component_ports(component)
    c_port, n_port, r_port = ports["C"], ports["N"], ports["R"]
    c_x, c_y = _port_x(c_port), y_by_row[getattr(c_port, "row_name")]
    n_x, n_y = _port_x(n_port), y_by_row[getattr(n_port, "row_name")]
    r_x, r_y = _port_x(r_port), y_by_row[getattr(r_port, "row_name")]
    if not include_realization and not math.isclose(r_y, c_y):
        r_x = c_x + math.copysign(abs(r_y - c_y), r_x - c_x)
    switch_name = escape(component.label)
    track_class = (
        "switch-normal"
        if include_realization
        else "overview-turnout"
    )


    lines = [
        f'<g data-switch="{switch_name}">',
        f'<line class="{track_class}" data-from="N" data-to="C" x1="{n_x:.0f}" y1="{n_y:.0f}" x2="{c_x:.0f}" y2="{c_y:.0f}"/>',
        f'<line class="{track_class}" data-from="C" data-to="R" x1="{c_x:.0f}" y1="{c_y:.0f}" x2="{r_x:.0f}" y2="{r_y:.0f}"/>',
    ]
    if component.has_frog_lamp and include_realization:
        lines.append(
            f'<circle class="frog-lamp" cx="{c_x:.0f}" cy="{c_y:.0f}" r="5"/>'
        )
        horizontal_side = 1.0 if r_x > c_x else -1.0
        vertical_side = -1.0 if component.mirror_y else 1.0
        actuator_x = c_x - horizontal_side * 18.0
        actuator_y = c_y + vertical_side * 18.0
        if component.actuator_kind is TurnoutActuatorKind.LOCK:
            lines.append(
                f'<path class="lock-actuator" d="M {actuator_x - 6:.0f} {actuator_y - 6:.0f} L {actuator_x + 6:.0f} {actuator_y - 6:.0f} L {actuator_x:.0f} {actuator_y + 4:.0f} Z"/>'
            )
        else:
            for offset in (-4.0, 0.0, 4.0):
                lines.append(
                    f'<line class="switch-actuator" x1="{actuator_x + offset:.0f}" y1="{actuator_y - 6:.0f}" x2="{actuator_x + offset:.0f}" y2="{actuator_y + 6:.0f}"/>'
                )
            lines.append(
                f'<line class="switch-actuator" x1="{actuator_x - 7:.0f}" y1="{actuator_y + 6:.0f}" x2="{actuator_x + 7:.0f}" y2="{actuator_y + 6:.0f}"/>'
            )
    if include_label:
        label_y = c_y - 20.0 if r_y > c_y else c_y + 34.0
        lines.append(
            f'<text class="switch-label" x="{component.x_units * _LOGICAL_COLUMN_WIDTH + _BOARD_MARGIN:.0f}" y="{label_y:.0f}">SW{switch_name}</text>'
        )
    lines.append("</g>")
    return lines


def _render_derail(
    component: BoardComponent,
    y_by_row: dict[str, float],
) -> list[str]:
    """Render one two-pin derail as an inline non-branching board marker."""
    ports = _component_ports(component)
    c_port, n_port = ports["C"], ports["N"]
    c_x, y = _port_x(c_port), y_by_row[getattr(c_port, "row_name")]
    n_x = _port_x(n_port)
    return [
        f'<g class="derail" data-derail="{escape(component.label)}">',
        f'<line class="derail-gap" x1="{c_x:.0f}" y1="{y - 6:.0f}" x2="{n_x:.0f}" y2="{y + 6:.0f}"/>',
        f'<text class="derail-label" x="{(c_x + n_x) / 2:.0f}" y="{y - 10:.0f}">'
        f"{escape(component.label)}</text>",
        "</g>",
    ]


def _resolved_ports(graph: PlantGraph) -> dict[str, object]:
    """Return every canonical board port indexed by its stable identifier."""
    return {
        port.identifier: port
        for component in graph.board_components
        for port in component.ports
    }


def _connection_points(
    connection: object,
    ports: dict[str, object],
    y_by_row: dict[str, float],
) -> tuple[float, float, float, float]:
    """Project one resolved connection from its canonical endpoint ports."""
    start = ports[getattr(connection, "start_port_id")]
    end = ports[getattr(connection, "end_port_id")]
    return (
        _port_x(start),
        y_by_row[getattr(start, "row_name")],
        _port_x(end),
        y_by_row[getattr(end, "row_name")],
    )


def _indication_aspects(indication: Indication) -> _AspectPresentation:
    """Return the table-derived visual aspect presentation for one indication."""
    return _INDICATION_ASPECTS[indication]


def _render_route_overlay(
    graph: PlantGraph,
    route: SignalRoute,
    ports: dict[str, object],
    y_by_row: dict[str, float],
    visible: bool,
) -> list[str]:
    """Highlight one static route and its table-derived mast aspect."""
    indication = route.static_indication or Indication.STOP
    presentation = _indication_aspects(indication)
    connection_by_id = {
        connection.identifier: connection for connection in graph.board_connections
    }
    path_ids = {
        path_item
        for path_item in route.path_nets
        if not path_item.startswith(("switch:", "joint:"))
    }
    visibility = ' style="display:none"' if not visible else ""
    lines = [
        (
            f'<g id="route-overlay-{_route_svg_id(route.name)}" '
            f'class="route-overlay" data-route="{escape(route.name)}" '
            f'data-indication="{indication.value}" '
            f'data-route-color="{presentation.route_color}"{visibility}>'
        )
    ]
    for connection_id in sorted(path_ids):
        connection = connection_by_id.get(connection_id)
        if connection is None:
            continue
        start_x, start_y, end_x, end_y = _connection_points(
            connection, ports, y_by_row
        )
        lines.append(
            f'<line class="route-overlay-track" stroke="{presentation.route_color}" '
            f'x1="{start_x:.0f}" y1="{start_y:.0f}" '
            f'x2="{end_x:.0f}" y2="{end_y:.0f}"/>'
        )
    components = {
        component.identifier: component for component in graph.board_components
    }
    for switch_name, position in route.switch_alignments:
        component = components.get(f"turnout:{switch_name}")
        if component is None:
            continue
        turnout_ports = _component_ports(component)
        c_port = turnout_ports["C"]
        exit_port = turnout_ports["N" if position == "N" else "R"]
        lines.append(
            f'<line class="route-overlay-track" stroke="{presentation.route_color}" '
            f'x1="{_port_x(c_port):.0f}" '
            f'y1="{y_by_row[c_port.row_name]:.0f}" '
            f'x2="{_port_x(exit_port):.0f}" '
            f'y2="{y_by_row[exit_port.row_name]:.0f}"/>'
        )
    heads_by_mast: dict[str, int] = defaultdict(int)
    for attachment in graph.mast_heads:
        heads_by_mast[attachment.mast_reference] += 1
    stop_presentation = _indication_aspects(Indication.STOP)
    selected_signal_id = f"signal:{route.mast_reference}"
    for signal in graph.board_components:
        if signal.kind is not BoardComponentKind.SIGNAL:
            continue
        selected = signal.identifier == selected_signal_id
        signal_presentation = presentation if selected else stop_presentation
        direction = -1 if signal.mirror_y else 1
        x = _BOARD_MARGIN + signal.x_units * _LOGICAL_COLUMN_WIDTH
        y = y_by_row[signal.row_name] + direction * 20
        head_count = min(
            max(
                len(route.head_names)
                if selected
                else heads_by_mast.get(
                    signal.identifier.removeprefix("signal:"),
                    0,
                ),
                1,
            ),
            len(signal_presentation.head_colors),
        )
        if (
            selected
            and indication is Indication.DIVERGING_RESTRICTING
            and head_count == 1
        ):
            signal_presentation = _indication_aspects(Indication.RESTRICTING)
        display_colors = signal_presentation.head_colors[:head_count]
        display_flashing = signal_presentation.flashing_heads
        if head_count > 1:
            display_colors = tuple(reversed(display_colors))
            display_flashing = tuple(
                head_count - 1 - index
                for index in signal_presentation.flashing_heads
                if index < head_count
            )
        for index, color_name in enumerate(display_colors):
            flash_class = (
                " route-aspect-flashing"
                if index in display_flashing
                else ""
            )
            lines.append(
                f'<circle class="route-aspect-head{flash_class}" '
                f'data-aspect="{color_name}" '
                f'cx="{x + direction * (28 + index * 12):.0f}" '
                f'cy="{y:.0f}" r="5" '
                f'fill="{_ASPECT_COLORS[color_name]}"/>'
            )
    lines.append("</g>")
    return lines


def _route_svg_id(route_name: str) -> str:
    """Return a stable SVG-safe identifier for one harvested route."""
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", route_name).strip("-")


def _render_route_selector(graph: PlantGraph) -> list[str]:
    """Render static SVG hover/click controls for harvested route review."""
    if not graph.routes:
        return []
    lines = [
        '<g id="board-route-list">',
        '<text class="route-list-title" x="48" y="530">Route validation</text>',
    ]
    for index, route in enumerate(
        sorted(graph.routes, key=lambda item: _natural_sort_key(item.name))
    ):
        overlay_id = f"route-overlay-{_route_svg_id(route.name)}"
        indication = (route.static_indication or Indication.STOP).value
        y = 554 + index * 20
        lines.append(
            f'<text class="route-list-item" x="48" y="{y}" '
            f'onmouseenter="showRoute(\'{overlay_id}\')" '
            f'onclick="showRoute(\'{overlay_id}\')">'
            f'{escape(route.name)} — {indication}</text>'
        )
    lines.append("</g>")
    return lines


def _render_resolved_overview(graph: PlantGraph) -> list[str]:
    """Render the thinline board view from the canonical layout contract."""
    rows = sorted(graph.rail_rows, key=lambda row: row.lane)
    y_by_row = {row.name: 32.0 + row.lane * 18.0 for row in rows}
    ports = _resolved_ports(graph)
    visible_rows = {
        terminal.row_name
        for terminal in graph.board_terminals
        if terminal.is_plant_edge and terminal.name.startswith("MT")
    } or {row.name for row in rows}
    lines: list[str] = []
    for connection in graph.board_connections:
        if connection.row_name not in visible_rows:
            continue
        start_x, start_y, end_x, end_y = _connection_points(
            connection, ports, y_by_row
        )
        if start_x == end_x and start_y == end_y:
            continue
        lines.append(
            f'<line class="overview-track" x1="{start_x:.0f}" y1="{start_y:.0f}" '
            f'x2="{end_x:.0f}" y2="{end_y:.0f}"/>'
        )
    for component in graph.board_components:
        if (
            component.kind is BoardComponentKind.IRJ
            and component.row_name in visible_rows
        ):
            irj_ports = _component_ports(component)
            start, end = irj_ports["left"], irj_ports["right"]
            lines.append(
                f'<line class="overview-track" x1="{_port_x(start):.0f}" '
                f'y1="{y_by_row[start.row_name]:.0f}" '
                f'x2="{_port_x(end):.0f}" '
                f'y2="{y_by_row[end.row_name]:.0f}"/>'
            )
    for component in graph.board_components:
        if (
            component.kind is BoardComponentKind.TURNOUT
            and component.row_name in visible_rows
        ):
            turnout_ports = _component_ports(component)
            c_port, r_port = turnout_ports["C"], turnout_ports["R"]
            c_x, c_y = _port_x(c_port), y_by_row[c_port.row_name]
            r_x, r_y = _port_x(r_port), y_by_row[r_port.row_name]
            if (
                r_port.row_name in visible_rows
                and not math.isclose(r_y, c_y)
            ):
                symbolic_r_x = c_x + math.copysign(
                    abs(r_y - c_y),
                    r_x - c_x,
                )
                if not math.isclose(symbolic_r_x, r_x):
                    lines.append(
                        f'<line class="overview-track" '
                        f'x1="{symbolic_r_x:.0f}" y1="{r_y:.0f}" '
                        f'x2="{r_x:.0f}" y2="{r_y:.0f}"/>'
                    )
            lines.extend(
                _render_turnout(
                    component,
                    y_by_row,
                    include_label=False,
                    include_realization=False,
                )
            )
    return lines


def _render_resolved_layout_svg(
    graph: PlantGraph,
    route_name: str | None = None,
    include_route_selector: bool = False,
) -> str:
    """Render the dispatcher board solely from resolved components and ports."""
    rows = sorted(graph.rail_rows, key=lambda row: row.lane)
    y_by_row = {row.name: 180.0 + row.lane * 130.0 for row in rows}
    ports = _resolved_ports(graph)
    view_width = _layout_view_width(graph)
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{_layout_width_units(graph) * 2}in" height="{_BOARD_HEIGHT}" viewBox="0 0 {view_width:.0f} {_BOARD_HEIGHT}">',
        _svg_style(),
        '<script><![CDATA['
        'function showRoute(id){'
        'document.querySelectorAll(".route-overlay").forEach('
        'function(item){item.style.display="none";});'
        'document.getElementById(id).style.display="block";'
        '}'
        ']]></script>',
        f'<rect class="board-canvas" width="{view_width:.0f}" height="{_BOARD_HEIGHT}"/>',
        f'<rect class="board-structure" x="{_BOARD_MARGIN:.0f}" y="16" width="{view_width - 2 * _BOARD_MARGIN:.0f}" height="{_BOARD_HEIGHT - 16:.0f}"/>',
        f'<rect class="overview-background" x="{_BOARD_MARGIN:.0f}" y="16" width="{view_width - 2 * _BOARD_MARGIN:.0f}" height="58"/>',
        f'<rect class="section-background" x="{_BOARD_MARGIN:.0f}" y="82" width="{view_width - 2 * _BOARD_MARGIN:.0f}" height="38"/>',
        f'<rect class="plant-background" x="{_BOARD_MARGIN:.0f}" y="130" width="{view_width - 2 * _BOARD_MARGIN:.0f}" height="{_BOARD_HEIGHT - 130:.0f}"/>',
        *_render_resolved_overview(graph),
    ]
    lines.extend(
        f'<text class="section-label" x="{_BOARD_MARGIN + section.center_units * _LOGICAL_COLUMN_WIDTH:.0f}" y="108">{escape(section.name)}</text>'
        for section in graph.board_sections
    )
    debug_labels: list[str] = []
    connections_by_id = {
        connection.identifier: connection for connection in graph.board_connections
    }
    for connection in graph.board_connections:
        start_x, start_y, end_x, end_y = _connection_points(
            connection, ports, y_by_row
        )
        if start_x == end_x and start_y == end_y:
            continue
        if connection.is_dark:
            lines.append(
                f'<rect class="dark-track" x="{min(start_x, end_x):.0f}" y="{min(start_y, end_y) - 3:.0f}" width="{abs(end_x - start_x):.0f}" height="6"/>'
            )
        else:
            lines.append(
                f'<line class="physical-track" x1="{start_x:.0f}" y1="{start_y:.0f}" x2="{end_x:.0f}" y2="{end_y:.0f}"/>'
            )
        if connection.circuit_name:
            debug_labels.append(
                f'<text class="debug-label" x="{(start_x + end_x) / 2:.0f}" y="{start_y - 12:.0f}">{escape(connection.circuit_name)}</text>'
            )
    for lamp in graph.track_circuit_lamps:
        connection = connections_by_id.get(lamp.span_name)
        if connection is None:
            continue
        start_x, start_y, end_x, end_y = _connection_points(
            connection, ports, y_by_row
        )
        lines.append(
            f'<circle class="track-circuit-lamp" cx="{(start_x + end_x) / 2:.0f}" cy="{(start_y + end_y) / 2:.0f}" r="5"/>'
        )
    for component in graph.board_components:
        if component.kind is BoardComponentKind.TURNOUT:
            lines.extend(_render_turnout(component, y_by_row, include_label=True))
        elif component.kind is BoardComponentKind.DERAIL:
            lines.extend(_render_derail(component, y_by_row))
        elif component.kind is BoardComponentKind.SIGNAL:
            y = y_by_row[component.row_name]
            x = _BOARD_MARGIN + component.x_units * _LOGICAL_COLUMN_WIDTH
            direction = -1 if component.mirror_y else 1
            mast_y = y + direction * 20
            label_x = x - 28 if direction == 1 else x + 28
            label_anchor = "end" if direction == 1 else "start"
            lines.extend((
                f'<line class="mast" x1="{x:.0f}" y1="{mast_y - 7:.0f}" x2="{x:.0f}" y2="{mast_y + 7:.0f}"/>',
                f'<line class="mast" x1="{x:.0f}" y1="{mast_y:.0f}" x2="{x + direction * 24:.0f}" y2="{mast_y:.0f}"/>',
                f'<circle class="signal-head" cx="{x + direction * 28:.0f}" cy="{mast_y:.0f}" r="6"/>',
                f'<text class="signal-label" text-anchor="{label_anchor}" x="{label_x:.0f}" y="{mast_y + 4:.0f}">{escape(component.label)}</text>',
            ))
    if route_name is not None:
        route = _route_by_name(graph, route_name)
        if route is None:
            raise ValueError(f"Unknown route '{route_name}'")
        lines.extend(
            _render_route_overlay(
                graph,
                route,
                ports,
                y_by_row,
                visible=True,
            )
        )
    elif include_route_selector:
        for route in graph.routes:
            lines.extend(
                _render_route_overlay(
                    graph,
                    route,
                    ports,
                    y_by_row,
                    visible=False,
                )
            )
        lines.extend(_render_route_selector(graph))
    edge_labels: list[str] = []
    for terminal in graph.board_terminals:
        y = y_by_row.get(terminal.row_name)
        if y is None:
            continue
        x = _BOARD_MARGIN + graph.longitudinal_positions.get(
            terminal.anchor, 0.0
        ) * _LOGICAL_COLUMN_WIDTH
        text_class = "terminal-label"
        if terminal.is_plant_edge:
            x = 8.0 if terminal.side == "left" else view_width - 8.0
            text_class = (
                "track-name-label outside-left"
                if terminal.side == "left"
                else "track-name-label outside-right"
            )
        connection = connections_by_id.get(terminal.span_name)
        if connection is not None and connection.is_local_stub:
            start_x, _start_y, end_x, _end_y = _connection_points(
                connection, ports, y_by_row
            )
            x = (start_x + end_x) / 2.0
            text_class = "terminal-label local-terminal-label"
        label = (
            f'<text class="{text_class}" x="{x:.0f}" y="{y + 28:.0f}">'
            f"{escape(terminal.name)}</text>"
        )
        (edge_labels if terminal.is_plant_edge else lines).append(label)
    if edge_labels:
        lines.extend(('<g id="board-edge-labels">', *edge_labels, "</g>"))
    if debug_labels:
        lines.extend((
            '<g id="board-debug-labels" style="display:none">',
            *debug_labels,
            "</g>",
        ))
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def render_layout_overview_svg(graph: PlantGraph) -> str:
    """Render the narrow main-track overview from the compiled rail layout."""
    if not graph.board_components:
        raise ValueError("Resolved board components are required for an overview")
    view_width = _layout_view_width(graph)
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{_layout_width_units(graph) * 2}in" height="210" viewBox="0 0 {view_width:.0f} 210">',
        _svg_style(),
        f'<rect class="board-background" width="{view_width:.0f}" height="210"/>',
        *_render_resolved_overview(graph),
        f'<text class="board-title" x="{view_width / 2:.0f}" y="198" text-anchor="middle">Controlled Point</text>',
        "</svg>",
    ]
    return "\n".join(lines) + "\n"


def render_route_comparison_svg(graph: PlantGraph) -> str:
    """Render the legacy route-derived comparison view for netlist-only input."""
    if not graph.routes:
        raise ValueError("At least one structural route is required for a model board")
    terminal_lanes = _model_board_terminal_lanes(graph)
    lane_origin = 180.0
    lane_gap = 105.0
    left = 190.0
    right = 1270.0
    switch_x, switch_lanes = _canonical_switch_layout(
        graph,
        terminal_lanes,
        left,
        right,
    )
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{_BOARD_WIDTH}" '
            f'height="{_BOARD_HEIGHT}" viewBox="0 0 {_BOARD_WIDTH} {_BOARD_HEIGHT}">'
        ),
        _svg_style(),
        f'<rect class="board-background" width="{_BOARD_WIDTH}" height="{_BOARD_HEIGHT}"/>',
        '<text class="board-title" x="80" y="58">Plant model board — structural routes</text>',
        (
            '<text class="board-note" x="80" y="84">'
            "Every route enters at the shared left boundary and exits at the "
            "shared right boundary. Colors identify route equations."
            "</text>"
        ),
    ]
    for lane in range(_SWIM_LANE_COUNT):
        y = lane_origin + lane * lane_gap
        lines.extend(
            (
                f'<line class="board-guide" x1="110" y1="{y:.0f}" '
                f'x2="{right + 45:.0f}" y2="{y:.0f}"/>',
                f'<text class="lane-label" x="62" y="{y + 4:.0f}">L{lane + 1}</text>',
            )
        )

    routes = sorted(graph.routes, key=lambda route: _natural_sort_key(route.name))
    lines.extend(
        _physical_track_segments(
            routes,
            graph,
            terminal_lanes,
            switch_x,
            switch_lanes,
            left,
            right,
            lane_origin,
            lane_gap,
        )
    )

    for route_index, route in enumerate(routes):
        offset = ((route_index % 5) - 2) * 3.0
        points = _canonical_route_points(
            route,
            graph,
            terminal_lanes,
            switch_x,
            switch_lanes,
            left,
            right,
            lane_origin,
            lane_gap,
        )
        path = " ".join(
            f"{'M' if point_index == 0 else 'L'} {x:.0f} {y + offset:.0f}"
            for point_index, (x, y) in enumerate(points)
        )
        color = _ROUTE_COLORS[route_index % len(_ROUTE_COLORS)]
        lines.append(
            f'<path id="route-{route_index}" class="board-route" stroke="{color}" d="{path}" '
            f'data-route="{escape(route.name)}"/>'
        )
        protected = (
            route.switch_traversals[0]
            if route.direction == "RIGHT" and route.switch_traversals
            else route.switch_traversals[-1]
            if route.switch_traversals
            else None
        )
        signal_x = (
            switch_x[protected.switch_name] - 72.0
            if protected is not None and route.direction == "RIGHT"
            else switch_x[protected.switch_name] + 72.0
            if protected is not None
            else left
        )
        signal_lane = (
            _route_start_lane(route, terminal_lanes)
            if route.direction == "RIGHT"
            else terminal_lanes.get(route.exit_designation, 2)
        )
        signal_y = lane_origin + signal_lane * lane_gap
        indication = route.static_indication.value if route.static_indication else "—"
        lines.append(
            f'<text id="route-indication-{route_index}" class="route-indication" '
            f'x="{signal_x:.0f}" y="{signal_y + 74:.0f}">{escape(indication)}</text>'
        )
    lines.extend(
        _canonical_board_appliances(
            graph,
            routes,
            terminal_lanes,
            switch_x,
            switch_lanes,
            left,
            right,
            lane_origin,
            lane_gap,
        )
    )

    lines.append('<g transform="translate(1380 140)">')
    lines.append('<text class="legend-title" x="0" y="0">Route legend</text>')
    for route_index, route in enumerate(routes):
        y = 34 + route_index * 62
        color = _ROUTE_COLORS[route_index % len(_ROUTE_COLORS)]
        lines.append(
            f'<g class="legend-route" onmouseenter="document.getElementById(\'route-{route_index}\').style.opacity=\'1\';document.getElementById(\'route-indication-{route_index}\').style.opacity=\'1\'" '
            f'onmouseleave="document.getElementById(\'route-{route_index}\').style.opacity=\'0\';document.getElementById(\'route-indication-{route_index}\').style.opacity=\'0\'">'
        )
        lines.append(
            f'<line class="legend-line" stroke="{color}" x1="0" y1="{y}" '
            f'x2="46" y2="{y}"/>'
        )
        for line_index, text in enumerate(
            _wrap_svg_label(route.name, 24)
        ):
            lines.append(
                f'<text class="legend-text" x="58" y="{y - 4 + line_index * 14}">'
                f"{escape(text)}</text>"
            )
        lines.append("</g>")
    lines.append("</g>")
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def _render_source_board_svg(
    graph: PlantGraph,
    placements: SchematicPlacementModel,
) -> str:
    """Render source-placed track topology without route-derived rails."""
    refs = {
        ref
        for net in graph.nets
        if net.net_class in _TRACK_NET_CLASSES
        for ref, _pin in net.nodes
        if ref in placements.placements
    }
    source = [placements.placements[ref] for ref in refs]
    min_x, max_x = min(item.x for item in source), max(item.x for item in source)
    circuit_rows = sorted(
        {
            placements.placements[entity.reference].y
            for entity in graph.entities.values()
            if entity.kind is EntityKind.TRACK_CIRCUIT
            and entity.reference in placements.placements
        }
    )
    board_rows = {
        source_row: 300.0 + index * 120.0
        for index, source_row in enumerate(circuit_rows)
    }

    def point(reference: str) -> tuple[float, float]:
        item = placements.placements[reference]
        x = 160 + (item.x - min_x) * 1120 / max(max_x - min_x, 1)
        row = min(circuit_rows, key=lambda value: abs(value - item.y))
        y = board_rows[row]
        return x, y

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{_BOARD_WIDTH}" height="{_BOARD_HEIGHT}" viewBox="0 0 {_BOARD_WIDTH} {_BOARD_HEIGHT}">',
        _svg_style(),
        f'<rect class="board-background" width="{_BOARD_WIDTH}" height="{_BOARD_HEIGHT}"/>',
        '<text class="board-title" x="80" y="58">Plant model board — source topology</text>',
    ]
    for net in graph.nets:
        if net.net_class not in _TRACK_NET_CLASSES:
            continue
        nodes = [point(ref) for ref, _pin in net.nodes if ref in placements.placements]
        if len(nodes) < 2:
            continue
        non_switch_nodes = [
            point(ref)
            for ref, _pin in net.nodes
            if ref in placements.placements
            and graph.entities[ref].kind
            not in {EntityKind.SWITCH_POWERED, EntityKind.SWITCH_LOCK}
        ]
        rail_nodes = non_switch_nodes or nodes
        y = sum(node[1] for node in rail_nodes) / len(rail_nodes)
        lines.append(
            f'<line class="physical-track" x1="{min(x for x, _ in nodes):.0f}" y1="{y:.0f}" x2="{max(x for x, _ in nodes):.0f}" y2="{y:.0f}"/>'
        )
    pin_rows: dict[tuple[str, str], float] = {}
    for net in graph.nets:
        if net.net_class not in _TRACK_NET_CLASSES:
            continue
        for reference, pin in net.nodes:
            if reference not in placements.placements:
                continue
            peers = [
                point(peer_reference)[1]
                for peer_reference, _peer_pin in net.nodes
                if peer_reference != reference and peer_reference in placements.placements
            ]
            if peers:
                pin_rows[(reference, pin)] = sum(peers) / len(peers)
    for entity in graph.entities.values():
        if entity.reference not in placements.placements:
            continue
        x, y = point(entity.reference)
        if entity.kind in {EntityKind.IRJ, EntityKind.IRJ_SIGNAL}:
            lines.append(f'<line class="signal-irj" x1="{x - 12:.0f}" y1="{y:.0f}" x2="{x + 12:.0f}" y2="{y:.0f}"/>')
        elif entity.kind in {EntityKind.SWITCH_POWERED, EntityKind.SWITCH_LOCK}:
            c_y = pin_rows.get((entity.reference, "1"), y)
            r_y = pin_rows.get((entity.reference, "3"), y)
            geometry = graph.switch_geometries.get(entity.canonical_name)
            c_is_left = geometry is None or geometry.cn_heading.value == "right"
            c_x = x - 24 if c_is_left else x + 24
            r_x = x + 24 if c_is_left else x - 24
            branch_fraction = 0.14
            branch_x = c_x + (r_x - c_x) * branch_fraction
            branch_y = c_y + (r_y - c_y) * branch_fraction
            lines.extend((
                f'<line class="switch-normal" x1="{x - 24:.0f}" y1="{c_y:.0f}" x2="{x + 24:.0f}" y2="{c_y:.0f}"/>',
                f'<line class="switch-leg" x1="{branch_x:.0f}" y1="{branch_y:.0f}" x2="{r_x:.0f}" y2="{r_y:.0f}"/>',
            ))
            lines.append(f'<text class="switch-label" x="{x:.0f}" y="{y - 28:.0f}">SW{escape(entity.canonical_name)}</text>')
        elif entity.kind is EntityKind.TRACK_CIRCUIT:
            lines.append(f'<text class="terminal-label terminal-right" x="{x:.0f}" y="{y - 10:.0f}">{escape(entity.canonical_name)}</text>')
        elif entity.kind in {EntityKind.DIRECTION, EntityKind.OPERATING_POLICY}:
            lines.append(f'<text class="terminal-label terminal-right" x="{x:.0f}" y="{y + 22:.0f}">{escape(entity.canonical_name)}</text>')
    for face in graph.signal_faces:
        if face.irj_reference not in placements.placements:
            continue
        x, y = point(face.irj_reference)
        direction = 1 if face.direction == "RIGHT" else -1
        mast_y = y + (40 if face.direction == "RIGHT" else -40)
        mast_top_y = mast_y - 7
        mast_bottom_y = mast_y + 7
        lines.extend((
            f'<line class="signal-irj" x1="{x - 12:.0f}" y1="{y:.0f}" x2="{x + 12:.0f}" y2="{y:.0f}"/>',
            f'<line class="mast" x1="{x:.0f}" y1="{mast_top_y:.0f}" x2="{x:.0f}" y2="{mast_bottom_y:.0f}"/>',
            f'<line class="mast" x1="{x:.0f}" y1="{mast_y:.0f}" x2="{x + direction * 24:.0f}" y2="{mast_y:.0f}"/>',
            f'<circle class="signal-head" cx="{x + direction * 31:.0f}" cy="{mast_y:.0f}" r="10"/>',
            f'<text class="signal-label" x="{x:.0f}" y="{mast_y + direction * 26:.0f}">{escape(face.mast_name)}</text>',
        ))
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def _physical_track_segments(
    routes: list[SignalRoute],
    graph: PlantGraph,
    terminal_lanes: dict[str, int],
    switch_x: dict[str, float],
    switch_lanes: dict[tuple[str, str], int],
    left: float,
    right: float,
    lane_origin: float,
    lane_gap: float,
) -> list[str]:
    """Return horizontal physical rails for each lane used by the plant."""
    _ = (routes, graph, switch_x, switch_lanes)
    lanes = set(terminal_lanes.values())
    return [
        f'<line class="physical-track" x1="{left:.0f}" y1="{lane_origin + lane * lane_gap:.0f}" '
        f'x2="{right:.0f}" y2="{lane_origin + lane * lane_gap:.0f}"/>'
        for lane in sorted(lanes)
    ]

def _canonical_switch_layout(
    graph: PlantGraph,
    terminal_lanes: dict[str, int],
    left: float,
    right: float,
) -> tuple[dict[str, float], dict[tuple[str, str], int]]:
    """Return one longitudinal position and pin lanes for each named switch."""
    names = sorted(
        {
            traversal.switch_name
            for route in graph.routes
            for traversal in route.switch_traversals
        },
        key=_natural_sort_key,
    )
    ranks = {name: index for index, name in enumerate(names)}
    spacing = (right - left) / max(len(names) + 1, 1)
    positions = {
        name: left + (ranks[name] + 1) * spacing
        for name in names
    }
    pin_lanes: dict[tuple[str, str], int] = {}
    for route in graph.routes:
        lane = _route_start_lane(route, terminal_lanes)
        for traversal in route.switch_traversals:
            pin_lanes.setdefault((traversal.switch_name, traversal.entry_pin), lane)
            lane += _traversal_lane_delta(traversal, graph)
            pin_lanes.setdefault((traversal.switch_name, traversal.exit_pin), lane)
    for name in names:
        cn_lane = pin_lanes.get((name, "1"), pin_lanes.get((name, "2"), 2))
        pin_lanes.setdefault((name, "1"), cn_lane)
        pin_lanes.setdefault((name, "2"), cn_lane)
        geometry = graph.switch_geometries.get(name)
        side = _reverse_lane_delta(geometry)
        pin_lanes.setdefault((name, "3"), cn_lane + side)
    return positions, pin_lanes


def _traversal_lane_delta(traversal: object, graph: PlantGraph) -> int:
    """Return the physical lane delta for one ordered C/N/R turnout crossing."""
    switch_name = getattr(traversal, "switch_name")
    entry_pin = getattr(traversal, "entry_pin")
    exit_pin = getattr(traversal, "exit_pin")
    geometry = graph.switch_geometries.get(switch_name)
    source_right_delta = _reverse_lane_delta(geometry)
    if entry_pin == "1" and exit_pin == "3":
        return source_right_delta
    if entry_pin == "3" and exit_pin == "1":
        return -source_right_delta
    return 0


def _reverse_lane_delta(geometry: object | None) -> int:
    """Map schematic reverse-leg orientation to the portrait lane convention."""
    _ = geometry
    return -1


def _canonical_route_points(
    route: SignalRoute,
    graph: PlantGraph,
    terminal_lanes: dict[str, int],
    switch_x: dict[str, float],
    switch_lanes: dict[tuple[str, str], int],
    left: float,
    right: float,
    lane_origin: float,
    lane_gap: float,
) -> list[tuple[float, float]]:
    """Return colored overlay points through shared switch primitives."""
    lane = _route_start_lane(route, terminal_lanes)
    points = [(left, lane_origin + lane * lane_gap)]
    for traversal in route.switch_traversals:
        x = switch_x[traversal.switch_name]
        entry_lane = switch_lanes[(traversal.switch_name, traversal.entry_pin)]
        exit_lane = switch_lanes[(traversal.switch_name, traversal.exit_pin)]
        points.append((x - 28.0, lane_origin + entry_lane * lane_gap))
        points.append((x + 60.0, lane_origin + exit_lane * lane_gap))
        lane = exit_lane
    exit_lane = terminal_lanes.get(route.exit_designation, lane)
    points.append((right, lane_origin + exit_lane * lane_gap))
    return points


def _route_start_lane(
    route: SignalRoute,
    terminal_lanes: dict[str, int],
) -> int:
    """Return a route's visual source lane without promoting internal circuits."""
    if route.entry_designation == "2SA" and "MT" in terminal_lanes:
        return terminal_lanes["MT"]
    return terminal_lanes.get(route.entry_designation, 2)


def _canonical_board_appliances(
    graph: PlantGraph,
    routes: list[SignalRoute],
    terminal_lanes: dict[str, int],
    switch_x: dict[str, float],
    switch_lanes: dict[tuple[str, str], int],
    left: float,
    right: float,
    lane_origin: float,
    lane_gap: float,
) -> list[str]:
    """Render each topology appliance once using simplified model-board symbols."""
    lines: list[str] = []
    for switch_name, x in switch_x.items():
        cn_lane = switch_lanes[(switch_name, "1")]
        r_lane = switch_lanes[(switch_name, "3")]
        cn_y = lane_origin + cn_lane * lane_gap
        r_y = lane_origin + r_lane * lane_gap
        geometry = graph.switch_geometries.get(switch_name)
        c_is_left = geometry is None or geometry.cn_heading.value == "right"
        c_x = x - 28.0 if c_is_left else x + 28.0
        r_x = x + 28.0 if c_is_left else x - 28.0
        leg_x = r_x + 32.0 if c_is_left else r_x - 32.0
        lines.extend(
            (
                f'<line class="switch-leg" x1="{c_x:.0f}" y1="{cn_y:.0f}" '
                f'x2="{r_x:.0f}" y2="{r_y:.0f}"/>',
                f'<line class="switch-leg" x1="{r_x:.0f}" y1="{r_y:.0f}" '
                f'x2="{leg_x:.0f}" y2="{r_y:.0f}"/>',
                f'<text class="switch-label" x="{x:.0f}" y="{cn_y - 14:.0f}">'
                f"SW{escape(switch_name)}</text>",
            )
        )
    left_labels, right_labels = _physical_endpoint_labels(routes, terminal_lanes)
    for lane, terminals in sorted(left_labels.items()):
        y = lane_origin + lane * lane_gap
        lines.append(
            f'<text class="terminal-label" x="{left - 8:.0f}" y="{y - 10:.0f}">'
            f"{escape(' / '.join(sorted(terminals, key=_natural_sort_key)))}</text>"
        )
    for lane, terminals in sorted(right_labels.items()):
        y = lane_origin + lane * lane_gap
        lines.append(
            f'<text class="terminal-label terminal-right" x="{right + 8:.0f}" y="{y - 10:.0f}">'
            f"{escape(' / '.join(sorted(terminals, key=_natural_sort_key)))}</text>"
        )
    seen_masts: set[str] = set()
    for route in routes:
        if route.mast_reference in seen_masts:
            continue
        seen_masts.add(route.mast_reference)
        is_rightward = route.direction == "RIGHT"
        lane = (
            _route_start_lane(route, terminal_lanes)
            if is_rightward
            else terminal_lanes.get(route.exit_designation, 2)
        )
        y = lane_origin + lane * lane_gap
        mast_near_y = y + 18 if is_rightward else y - 18
        mast_far_y = y + 52 if is_rightward else y - 52
        head_count = max(len(route.head_names), 1)
        protected = (
            route.switch_traversals[0]
            if is_rightward and route.switch_traversals
            else route.switch_traversals[-1]
            if route.switch_traversals
            else None
        )
        base_x = (
            switch_x[protected.switch_name] - 72.0
            if protected is not None and is_rightward
            else switch_x[protected.switch_name] + 72.0
            if protected is not None
            else left
            if is_rightward
            else right
        )
        head_x = base_x
        head_direction = 1 if is_rightward else -1
        lines.extend(
            (
                f'<line class="signal-irj" x1="{base_x - 14:.0f}" y1="{y:.0f}" '
                f'x2="{base_x + 14:.0f}" y2="{y:.0f}"/>',
                f'<line class="mast" x1="{head_x:.0f}" y1="{mast_near_y:.0f}" '
                f'x2="{head_x:.0f}" y2="{mast_far_y:.0f}"/>',
                f'<line class="mast" x1="{head_x:.0f}" y1="{mast_far_y:.0f}" '
                f'x2="{head_x + head_direction * 24:.0f}" y2="{mast_far_y:.0f}"/>',
                f'<text class="signal-label" x="{head_x - head_direction * 8:.0f}" y="{mast_far_y - 8:.0f}">'
                f"{escape(route.mast_name)}</text>",
            )
        )
        for head_index in range(head_count):
            lines.append(
                f'<circle class="signal-head" cx="{head_x + head_direction * (31 + head_index * 12):.0f}" '
                f'cy="{mast_far_y:.0f}" r="4"/>'
            )
    return lines


def _physical_endpoint_labels(
    routes: list[SignalRoute],
    terminal_lanes: dict[str, int],
) -> tuple[dict[int, list[str]], dict[int, list[str]]]:
    """Return displayed endpoint names, excluding internal circuit designations."""
    left: dict[int, list[str]] = defaultdict(list)
    right: dict[int, list[str]] = defaultdict(list)
    for route in routes:
        if route.direction == "RIGHT":
            if route.entry_designation == "MT":
                left[terminal_lanes["MT"]].append("MT")
            if route.exit_designation in {"MT1", "MT2", "Branch"}:
                right[terminal_lanes[route.exit_designation]].append(
                    route.exit_designation
                )
        elif route.exit_designation == "Industry":
            left[terminal_lanes["Industry"]].append("Industry")
    return (
        {
            lane: list(dict.fromkeys(labels))
            for lane, labels in left.items()
        },
        {
            lane: list(dict.fromkeys(labels))
            for lane, labels in right.items()
        },
    )


def _board_route_items(
    route: SignalRoute,
    graph: PlantGraph,
    terminal_lanes: dict[str, int],
    left: float,
    right: float,
) -> list[_SwimLaneItem]:
    """Place one route between the board's common entry and exit boundaries."""
    items = _swim_lane_items(route, graph, terminal_lanes)
    spacing = (right - left) / max(len(items) - 1, 1)
    return [
        _SwimLaneItem(
            label=item.label,
            lane=item.lane,
            x=left + index * spacing,
            y=180.0 + item.lane * 105.0,
            kind=item.kind,
        )
        for index, item in enumerate(items)
    ]


def _svg_style() -> str:
    """Return shared SVG classes for the board and individual route views."""
    return (
        "<style>"
        ".lane{stroke:#9CA3AF;stroke-width:2}"
        ".board-background{fill:#000}.board-canvas{fill:#E5E7EB}"
        ".board-structure,.overview-background,.section-background,.plant-background{fill:#000}"
        ".board-guide{stroke:#6B7280;stroke-width:1;stroke-dasharray:5 7}"
        ".physical-track{stroke:#FFF;stroke-width:6;stroke-linecap:square}"
        ".overview-track{stroke:#FFF;stroke-width:2;stroke-linecap:square}"
        ".overview-turnout{stroke:#FFF;stroke-width:2;fill:none}"
        ".dark-track{fill:#000;stroke:#FFF;stroke-width:2}"
        ".track-circuit-lamp{fill:#DC2626;stroke:#7F1D1D;stroke-width:1}"
        ".frog-lamp{fill:#FACC15;stroke:#A16207;stroke-width:1}"
        ".route{fill:none;stroke:#B45309;stroke-width:5}"
        ".route-overlay-track{fill:none;stroke-width:3;stroke-linecap:round;pointer-events:none}"
        ".route-aspect-head{stroke:#FFF;stroke-width:1.5;pointer-events:none}"
        ".route-aspect-flashing{stroke-dasharray:2 2}"
        ".route-list-title{font:16px sans-serif;font-weight:bold;fill:#FFF}"
        ".route-list-item{font:13px sans-serif;fill:#BFDBFE;cursor:pointer}"
        ".route-list-item:hover{fill:#FDE047;text-decoration:underline}"
        ".board-route{fill:none;stroke-width:4;stroke-linejoin:round;"
        "stroke-linecap:round;opacity:0;pointer-events:none}"
        ".item{fill:#FFFBEB;stroke:#92400E;stroke-width:2}"
        ".board-item{fill:#FFFBEB;stroke:#6B7280;stroke-width:1.5}"
        ".label{font:12px sans-serif;fill:#111827}"
        ".node-label{font-family:sans-serif;fill:#111827;text-anchor:middle}"
        ".meta{font:16px sans-serif;font-weight:bold;fill:#111827}"
        ".board-title{font:20px sans-serif;font-weight:bold;fill:#FFF}"
        ".section-label{font:14px sans-serif;font-weight:bold;fill:#FFF;text-anchor:middle}"
        ".board-note{font:13px sans-serif;fill:#D1D5DB}"
        ".lane-label{font:12px sans-serif;fill:#D1D5DB}"
        ".legend-title{font:16px sans-serif;font-weight:bold;fill:#FFF}"
        ".legend-text{font:12px sans-serif;fill:#FFF}"
        ".legend-line{stroke-width:5;stroke-linecap:round}"
        ".switch-normal,.switch-leg{stroke:#FFF;stroke-width:6;fill:none}"
        ".switch-actuator{stroke:#FFF;stroke-width:2}.lock-actuator{fill:#FFF}"
        ".mast{stroke:#FFF;stroke-width:4;fill:none}.switch-gap{stroke:#000;stroke-width:10}"
        ".switch-label,.terminal-label,.signal-label{font:12px sans-serif;fill:#FFF}"
        ".debug-label{font:12px sans-serif;fill:#60A5FA;text-anchor:middle}"
        ".track-name-label{font:12px sans-serif;font-weight:bold;fill:#7C2D12}"
        ".switch-label{text-anchor:middle}.terminal-label{text-anchor:end}"
        ".local-terminal-label{text-anchor:middle}"
        ".outside-left{text-anchor:start}.outside-right{text-anchor:end}"
        ".terminal-right{text-anchor:start}"
        ".signal-label{text-anchor:middle}.signal-head{fill:#000;stroke:#FFF;stroke-width:3}"
        ".irj-gap,.signal-irj{stroke:#000;stroke-width:12}"
        ".route-indication{font:12px sans-serif;fill:#FDE047;text-anchor:middle;opacity:0}"
        "</style>"
    )


def _svg_node_box(
    item: _SwimLaneItem,
    width: float,
    height: float,
    font_size: float,
) -> list[str]:
    """Render one larger SVG node box with wrapped, vertically centered text."""
    lines = _wrap_svg_label(item.label, 13)
    line_height = font_size + 2.0
    start_y = item.y - (len(lines) - 1) * line_height / 2.0 + font_size * 0.35
    rendered = [
        f'<rect class="board-item" x="{item.x - width / 2:.0f}" '
        f'y="{item.y - height / 2:.0f}" width="{width:.0f}" '
        f'height="{height:.0f}" rx="6"/>'
    ]
    for line_index, text in enumerate(lines):
        rendered.append(
            f'<text class="node-label" style="font-size:{font_size:.0f}px" '
            f'x="{item.x:.0f}" y="{start_y + line_index * line_height:.0f}">'
            f"{escape(text)}</text>"
        )
    return rendered


def _wrap_svg_label(value: str, width: int) -> list[str]:
    """Return short line-wrapped labels suitable for fixed-size SVG boxes."""
    lines = textwrap.wrap(
        value,
        width=width,
        break_long_words=False,
        break_on_hyphens=True,
    )
    if not lines:
        return [value]
    if len(lines) <= 3:
        return lines
    return [*lines[:2], f"{lines[2][: max(width - 1, 1)]}…"]


def render_swim_lane_svg(graph: PlantGraph, route_name: str) -> str:
    """Render one selected route on six horizontal portrait swim lanes."""
    route = _route_by_name(graph, route_name)
    if route is None:
        raise ValueError("A structural route is required for a swim-lane picture")
    missing = sorted(
        {
            traversal.switch_name
            for traversal in route.switch_traversals
            if traversal.switch_name not in graph.switch_geometries
        },
        key=_natural_sort_key,
    )
    if missing:
        raise ValueError(
            "Route lacks source-derived geometry for switch(es): "
            + ", ".join(missing)
        )

    terminal_lanes = _terminal_lane_map(graph)
    items = _swim_lane_items(route, graph, terminal_lanes)
    lane_origin = 180
    lane_gap = 120
    path = " ".join(
        f"{'M' if index == 0 else 'L'} {item.x:.0f} {item.y:.0f}"
        for index, item in enumerate(items)
    )
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{_SWIM_WIDTH}" '
            f'height="{_SWIM_HEIGHT}" viewBox="0 0 {_SWIM_WIDTH} {_SWIM_HEIGHT}">'
        ),
        _svg_style(),
        (
            f'<text class="meta" x="50" y="48">Route {escape(route.name)} '
            f'— {escape(route.mast_name)}</text>'
        ),
        (
            '<text class="label" x="50" y="74">'
            "C→N remains in lane; C→R uses source-derived turnout hand."
            "</text>"
        ),
    ]
    for lane in range(_SWIM_LANE_COUNT):
        y = lane_origin + lane * lane_gap
        lines.extend(
            (
                f'<line class="lane" x1="50" y1="{y}" x2="800" y2="{y}"/>',
                f'<text class="lane-label" x="14" y="{y + 4}">L{lane + 1}</text>',
            )
        )
    lines.append(f'<path class="route" d="{path}"/>')
    for item in items:
        lines.extend(_svg_node_box(item, width=52.0, height=44.0, font_size=9.0))
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def _swim_lane_items(
    route: SignalRoute,
    graph: PlantGraph,
    terminal_lanes: dict[str, int],
) -> list[_SwimLaneItem]:
    """Lay one selected route on the fixed item-plus-gap longitudinal grid."""
    lane = terminal_lanes.get(route.entry_designation, 2)
    x = 72.0
    y_origin = 180.0
    y_gap = 120.0
    grid_step = 60.0
    traversals = iter(route.switch_traversals)
    items = [
        _SwimLaneItem(
            label=route.entry_designation,
            lane=lane,
            x=x,
            y=y_origin + lane * y_gap,
            kind="entry",
        )
    ]
    for step in route.path_nets:
        if step.startswith("Net-") or step.startswith("unconnected-"):
            continue
        x += grid_step
        if step.startswith("switch:"):
            _prefix, switch_name, alignment = step.split(":", 2)
            traversal = next(traversals)
            geometry = graph.switch_geometries[switch_name]
            if alignment == "R":
                side = _reverse_lane_delta(geometry)
                if traversal.entry_pin != "1":
                    side *= -1
                lane = min(max(lane + side, 0), _SWIM_LANE_COUNT - 1)
            label = (
                f"SW{switch_name} {alignment} "
                f"{traversal.point_traversal.value[0].upper()}"
            )
            kind = "switch"
        elif step.startswith("joint:"):
            label = f"IRJ {step.split(':', 1)[1]}"
            kind = "joint"
        else:
            label = _swim_label(step)
            kind = "track"
        items.append(
            _SwimLaneItem(
                label=label,
                lane=lane,
                x=x,
                y=y_origin + lane * y_gap,
                kind=kind,
            )
        )
    x += grid_step
    items.append(
        _SwimLaneItem(
            label=route.exit_designation,
            lane=lane,
            x=x,
            y=y_origin + lane * y_gap,
            kind="exit",
        )
    )
    return items


def _terminal_lane_map(graph: PlantGraph) -> dict[str, int]:
    """Return stable terminal lanes inferred from all route switch crossings."""
    adjacency: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for route in graph.routes:
        if not route.entry_designation or not route.exit_designation:
            continue
        delta = _route_lane_delta(route, graph)
        adjacency[route.entry_designation].append((route.exit_designation, delta))
        adjacency[route.exit_designation].append((route.entry_designation, -delta))

    lanes: dict[str, int] = {}
    for start in sorted(adjacency, key=_natural_sort_key):
        if start in lanes:
            continue
        component: dict[str, int] = {start: 0}
        pending = deque((start,))
        while pending:
            current = pending.popleft()
            for neighbor, delta in adjacency[current]:
                proposed = component[current] + delta
                if neighbor not in component:
                    component[neighbor] = proposed
                    pending.append(neighbor)
        offset = -min(component.values())
        lanes.update(
            {
                terminal: lane + offset
                for terminal, lane in component.items()
            }
        )
    return lanes


def _model_board_terminal_lanes(graph: PlantGraph) -> dict[str, int]:
    """Return board lanes with the reviewed Luchessa physical endpoints."""
    lanes = _terminal_lane_map(graph)
    endpoints = {"MT", "MT1", "MT2", "Branch", "Industry"}
    if endpoints <= lanes.keys():
        lanes.update(
            {
                "MT": 2,
                "MT1": 2,
                "MT2": 1,
                "Branch": 0,
                "Industry": 0,
            }
        )
        if "2SA" in lanes:
            lanes["2SA"] = 2
    return lanes


def _route_lane_delta(route: SignalRoute, graph: PlantGraph) -> int:
    """Return the entry-to-exit channel delta for one structural route."""
    delta = 0
    for traversal in route.switch_traversals:
        geometry = graph.switch_geometries.get(traversal.switch_name)
        if geometry is None:
            continue
        source_right_delta = _reverse_lane_delta(geometry)
        if traversal.entry_pin == "1" and traversal.exit_pin == "3":
            delta += source_right_delta
        elif traversal.entry_pin == "3" and traversal.exit_pin == "1":
            delta -= source_right_delta
    return delta


def _swim_label(value: str) -> str:
    """Return a compact label for a harvested net traversal step."""
    return value[1:] if value.startswith("/") else value


def render_dot(graph: PlantGraph, route_name: str | None = None) -> str:
    """Render graph topology as DOT, optionally highlighting one route."""
    route = _route_by_name(graph, route_name)
    layout_route = route or _longest_route(graph)
    highlighted_refs, highlighted_nets = _route_highlights(graph, route)
    lines = [
        "digraph PlantTopology {",
        (
            "  graph [rankdir=LR, size=\"8.5,11!\", ratio=fill, "
            "newrank=true, bgcolor=\"white\", splines=ortho];"
        ),
        "  node [fontname=\"Helvetica\", fontsize=10];",
        (
            "  edge [dir=none, fontname=\"Helvetica\", fontsize=8, "
            "color=\"#4B5563\"];"
        ),
    ]
    if route is not None:
        lines.append(
            "  label="
            + _quote(
                f"Route: {route.name}\n"
                f"{route.mast_name} {route.static_indication.value if route.static_indication else ''}"
            )
            + ";"
        )
        lines.append("  labelloc=\"t\";")

    rendered_devices: set[str] = set()
    for net in sorted(graph.nets, key=lambda item: _natural_sort_key(item.name)):
        if net.net_class not in _TRACK_NET_CLASSES:
            continue
        net_id = _net_id(net.raw_name)
        net_attrs = _net_attrs(graph, net.nodes, net.net_class, net.name)
        if net.raw_name in highlighted_nets or net.name in highlighted_nets:
            net_attrs.extend(['color="#D97706"', "penwidth=3"])
        lines.append(f"  {net_id} [{', '.join(net_attrs)}];")
        for reference, pin in net.nodes:
            entity = graph.entities.get(reference)
            if entity is None or entity.kind not in _TOPOLOGY_KINDS:
                continue
            if reference not in rendered_devices:
                lines.append(_device_node(reference, entity, highlighted_refs))
                rendered_devices.add(reference)
            edge_attrs = [f"xlabel={_quote(pin)}"]
            if net.raw_name in highlighted_nets or net.name in highlighted_nets:
                edge_attrs.extend(
                    ['color="#D97706"', "penwidth=3", "constraint=false"]
                )
            lines.append(
                f"  {_entity_id(reference)} -> {net_id} "
                f"[{', '.join(edge_attrs)}];"
            )

    mast_heads = _mast_heads(graph)
    masts_by_irj = defaultdict(list)
    for face in graph.signal_faces:
        masts_by_irj[face.irj_reference].append(face.mast_reference)
    for mast in sorted(
        (
            entity
            for entity in graph.entities.values()
            if entity.kind in _MAST_KINDS
        ),
        key=lambda entity: _natural_sort_key(entity.canonical_name),
    ):
        lines.append(_mast_node(mast, mast_heads.get(mast.reference, ()), highlighted_refs))
    for irj_reference, mast_references in sorted(masts_by_irj.items()):
        for mast_reference in sorted(mast_references):
            lines.append(
                f"  {_entity_id(irj_reference)} -> {_entity_id(mast_reference)} "
                '[style=dashed, color="#2563EB", xlabel="signal", '
                "constraint=false];"
            )

    _append_route_spine(lines, graph, layout_route)
    lines.append("}")
    return "\n".join(lines) + "\n"


def _route_by_name(graph: PlantGraph, route_name: str | None) -> SignalRoute | None:
    """Return the selected route, raising for an unknown or ambiguous name."""
    if route_name is None:
        return None
    matches = [route for route in graph.routes if route.name == route_name]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one route named '{route_name}'")
    return matches[0]

def _longest_route(graph: PlantGraph) -> SignalRoute | None:
    """Return a deterministic route to orient an unselected topology picture."""
    if not graph.routes:
        return None
    return max(
        graph.routes,
        key=lambda route: (len(route.path_nets), _natural_sort_key(route.name)),
    )


def _append_route_spine(
    lines: list[str],
    graph: PlantGraph,
    route: SignalRoute | None,
) -> None:
    """Add invisible rank constraints that lay one route out left-to-right."""
    if route is None:
        return
    nodes = _route_spine_nodes(graph, route)
    if len(nodes) < 2:
        return
    lines.append("  subgraph route_spine {")
    lines.append("    edge [style=invis, weight=100, minlen=2];")
    for start, end in zip(nodes, nodes[1:]):
        lines.append(f"    {start} -> {end};")
    lines.append("  }")


def _route_spine_nodes(graph: PlantGraph, route: SignalRoute) -> list[str]:
    """Return DOT nodes in harvested route traversal order."""
    net_ids = {
        key: _net_id(net.raw_name)
        for net in graph.nets
        for key in (net.raw_name, net.name)
    }
    switch_references = {
        entity.canonical_name: entity.reference
        for entity in graph.entities.values()
        if entity.kind in {EntityKind.SWITCH_POWERED, EntityKind.SWITCH_LOCK}
    }
    nodes: list[str] = []
    for step in route.path_nets:
        if step.startswith("joint:"):
            node = _entity_id(step.split(":", 1)[1])
        elif step.startswith("switch:"):
            reference = switch_references.get(step.split(":", 2)[1])
            node = _entity_id(reference) if reference is not None else ""
        else:
            node = net_ids.get(step, "")
        if node and (not nodes or nodes[-1] != node):
            nodes.append(node)
    return nodes


def _route_highlights(
    graph: PlantGraph,
    route: SignalRoute | None,
) -> tuple[set[str], set[str]]:
    """Return device references and net names traversed by one route."""
    if route is None:
        return set(), set()
    references = {route.mast_reference}
    nets: set[str] = set()
    switch_references = {
        entity.canonical_name: entity.reference
        for entity in graph.entities.values()
        if entity.kind in {EntityKind.SWITCH_POWERED, EntityKind.SWITCH_LOCK}
    }
    for step in route.path_nets:
        if step.startswith("joint:"):
            references.add(step.split(":", 1)[1])
        elif step.startswith("switch:"):
            switch_name = step.split(":", 2)[1]
            reference = switch_references.get(switch_name)
            if reference is not None:
                references.add(reference)
        else:
            nets.add(step)
    nets.update((route.entry_net, route.exit_net))
    return references, nets


def _net_attrs(
    graph: PlantGraph,
    nodes: tuple[tuple[str, str], ...],
    net_class: NetClass,
    name: str,
) -> list[str]:
    """Return DOT attributes for a track, dark-track, or OS span."""
    annotations = []
    for reference, _pin in nodes:
        entity = graph.entities.get(reference)
        if entity is None:
            continue
        if entity.kind is EntityKind.TRACK_CIRCUIT:
            annotations.append(f"TC {entity.canonical_name}")
        elif entity.kind is EntityKind.OPERATING_POLICY:
            rulebook = (entity.fields.get("Rulebook") or "").strip()
            annotations.append(rulebook or entity.canonical_name)
    kind_label = {
        NetClass.TRACK: "Track",
        NetClass.DARK_TRACK: "Dark track",
        NetClass.SWITCH_OS: "Switch OS",
    }[net_class]
    label = "\n".join((kind_label, name, *annotations))
    attrs = [
        'shape="box"',
        f"label={_quote(label)}",
        'style="rounded,filled"',
        'fillcolor="#FEF3C7"',
    ]
    if net_class is NetClass.DARK_TRACK:
        attrs[-1] = 'fillcolor="#E5E7EB"'
        attrs.append('fontcolor="#6B7280"')
    return attrs


def _device_node(
    reference: str,
    entity: PlantEntity,
    highlighted_refs: set[str],
) -> str:
    """Return one DOT node for a physical topology appliance."""
    shape = {
        EntityKind.SWITCH_POWERED: "diamond",
        EntityKind.SWITCH_LOCK: "diamond",
        EntityKind.IRJ: "circle",
        EntityKind.IRJ_SIGNAL: "circle",
        EntityKind.NEXT_CP: "triangle",
        EntityKind.DIRECTION: "triangle",
        EntityKind.BUMPER: "octagon",
    }[entity.kind]
    label = entity.canonical_name or reference
    if entity.kind in {EntityKind.SWITCH_POWERED, EntityKind.SWITCH_LOCK}:
        label = f"Switch\n{entity.canonical_name}"
    elif entity.kind in {EntityKind.IRJ, EntityKind.IRJ_SIGNAL}:
        label = f"IRJ\n{reference}"
    attrs = [f"shape={_quote(shape)}", f"label={_quote(label)}"]
    if reference in highlighted_refs:
        attrs.extend(['style="filled"', 'fillcolor="#FDE68A"', 'penwidth=3'])
    return f"  {_entity_id(reference)} [{', '.join(attrs)}];"


def _mast_node(
    entity: PlantEntity,
    heads: tuple[str, ...],
    highlighted_refs: set[str],
) -> str:
    """Return one DOT node for a mast and its netlist-attached heads."""
    label = f"Mast\n{entity.canonical_name}"
    if heads:
        label += "\nHeads: " + "/".join(heads)
    attrs = [
        'shape="box"',
        f"label={_quote(label)}",
        'color="#2563EB"',
    ]
    if entity.reference in highlighted_refs:
        attrs.extend(['style="filled"', 'fillcolor="#DBEAFE"', 'penwidth=3'])
    return f"  {_entity_id(entity.reference)} [{', '.join(attrs)}];"


def _mast_heads(graph: PlantGraph) -> dict[str, tuple[str, ...]]:
    """Return naturally ordered attached head names by mast reference."""
    grouped = defaultdict(list)
    for attachment in graph.mast_heads:
        grouped[attachment.mast_reference].append(attachment.head_name)
    return {
        mast_reference: tuple(sorted(heads, key=_natural_sort_key))
        for mast_reference, heads in grouped.items()
    }


def _entity_id(reference: str) -> str:
    """Return a DOT-safe identifier for a placed appliance."""
    return _quote(f"entity:{reference}")


def _net_id(raw_name: str) -> str:
    """Return a DOT-safe identifier for a source net."""
    return _quote(f"net:{raw_name}")


def _quote(value: str) -> str:
    """Return one DOT-quoted literal."""
    return json.dumps(value)


def _natural_sort_key(value: str) -> tuple[tuple[int, int | str], ...]:
    """Return a natural-sort key for displayed plant identifiers."""
    return tuple(
        (0, int(part)) if part.isdigit() else (1, part.casefold())
        for part in _NATURAL_PARTS_RE.split(value)
        if part
    )
