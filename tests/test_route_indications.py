"""Tests for static and runtime route-signaling indication evaluation."""

from __future__ import annotations

import json

import sys
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"

if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from plant_graph.indications import (
    Indication,
    RouteEvaluationState,
    RouteSignalingPolicy,
    SwitchRuntimeState,
    TrackCircuitRuntimeState,
    parse_switch_indications,
)
from plant_graph.picture import (
    _indication_aspects,
    render_dot,
    render_layout_overview_svg,
    render_model_board_svg,
    render_route_board_svg,
    render_route_comparison_svg,
    render_swim_lane_svg,
)
from plant_graph.types import (
    BoardTerminal,
    CircuitRole,
    EntityKind,
    PlantEntity,
    PlantGraph,
    PlantNet,
    NetClass,
    PointTraversal,
    RailRow,
    RailSpan,
    RouteEndKind,
    SignalBase,
    SignalRoute,
    SchematicHeading,
    SwitchGeometry,
    SwitchTraversal,
    TrackCircuitLamp,
    TurnoutActuatorKind,
    TurnoutHand,
    TurnoutLayout,
)
from parse_kicad_plant import render_json, render_text
from plant_graph.layout import resolve_board_components


def _route(
    switch_position: str,
    end_kind: RouteEndKind = RouteEndKind.CP_LIMIT,
) -> SignalRoute:
    return SignalRoute(
        name="MT-Branch",
        signal_name="784",
        direction="RIGHT",
        mast_reference="S784E1",
        mast_name="784EAB",
        head_letters="AB",
        entry_terminal="CP1",
        entry_net="1SA",
        entry_designation="MT",
        entry_rulebook="261",
        exit_terminal="CP2",
        exit_net="3NA",
        exit_designation="Branch",
        exit_rulebook="261",
        end_kind=end_kind,
        exit_face_mast="",
        exit_face_signal="",
        exit_face_direction="",
        switch_alignments=(("799", switch_position),),
        circuit_roles=(("2SA", CircuitRole.HOME_CLEAR),),
        clear_track_circuits=("2SA",),
        os_track_circuits=(),
        path_track_circuits=("2SA",),
        path_nets=("2SA",),
        head_names=("A", "B"),
    )


def _graph(indications: str = "CLEAR/DIVERGING_CLEAR") -> PlantGraph:
    graph = PlantGraph()
    graph.entities["SW799"] = PlantEntity(
        reference="SW799",
        kind=EntityKind.SWITCH_POWERED,
        lib_id="Railroad:Switch_Powered",
        value="799",
        canonical_name="799",
        fields={"Indications": indications},
    )
    return graph


def _layout_graph() -> PlantGraph:
    """Return a three-column layout fixture with a left-heading turnout."""
    graph = PlantGraph()
    graph.board_width_units = 3
    graph.rail_rows = [
        RailRow("branch", 0, 1, ("Industry",)),
        RailRow("main", 1, 0, ("MT",)),
    ]
    graph.rail_spans = [
        RailSpan(
            "main-left",
            "main",
            ("CP_W", "B1"),
            start_anchor=0,
            end_anchor=1,
            endpoint_anchors=(("CP_W", 0), ("B1", 1)),
            irj_endpoints=("B1",),
            is_dark=True,
        ),
        RailSpan(
            "main-right",
            "main",
            ("B1", "CP_E"),
            start_anchor=1,
            end_anchor=3,
            endpoint_anchors=(("B1", 1), ("CP_E", 3)),
            irj_endpoints=("B1",),
        ),
        RailSpan(
            "branch",
            "branch",
            ("SW795", "BUMP"),
            start_anchor=2,
            end_anchor=3,
            endpoint_anchors=(("BUMP", 3),),
            turnout_ports=(("795", "R", 2),),
        ),
    ]
    graph.turnout_layouts = [
        TurnoutLayout(
            "795",
            SchematicHeading.LEFT,
            "main",
            "main",
            "branch",
            order=2,
            actuator_kind=TurnoutActuatorKind.LOCK,
        )
    ]
    graph.track_circuit_lamps = [
        TrackCircuitLamp("MT", "main-right", "main", 1, 3)
    ]
    graph.signal_bases = [
        SignalBase("795EA", "S795E1", "B1", "main", "RIGHT", anchor=1)
    ]
    graph.board_terminals = [
        BoardTerminal("MT", "main", "left", anchor=0, is_plant_edge=True),
        BoardTerminal("Industry", "branch", "left", anchor=2),
        BoardTerminal("MT1", "main", "right", anchor=3, is_plant_edge=True),
    ]
    graph.entities.update(
        {
            reference: PlantEntity(
                reference=reference,
                kind=kind,
                lib_id="Railroad:test",
                value="",
                canonical_name=reference,
            )
            for reference, kind in {
                "CP_W": EntityKind.DIRECTION,
                "B1": EntityKind.IRJ_SIGNAL,
                "CP_E": EntityKind.DIRECTION,
                "BUMP": EntityKind.BUMPER,
            }.items()
        }
    )
    graph.longitudinal_positions = {0: 0.0, 1: 1.0, 2: 2.0, 3: 3.0}
    resolve_board_components(graph)
    return graph

class RouteSignalingPolicyTests(unittest.TestCase):
    """Route caps and runtime gates are evaluated through the public policy seam."""
    def _ready_state(self) -> RouteEvaluationState:
        """Return a fully permissive runtime state for the sample route."""
        return RouteEvaluationState(
            signal_demands={"784": "RIGHT"},
            switches={
                "799": SwitchRuntimeState(
                    position="R",
                    correspondence=True,
                    locked=True,
                    os_vacant=True,
                )
            },
            track_circuits={
                "2SA": TrackCircuitRuntimeState(vacant=True, healthy=True)
            },
        )

    def test_switch_indications_override_reverse_default(self) -> None:
        policy = RouteSignalingPolicy()
        graph = _graph()

        self.assertEqual(
            policy.static_indication(_route("N"), graph),
            Indication.CLEAR,
        )
        self.assertEqual(
            policy.static_indication(_route("R"), graph),
            Indication.DIVERGING_CLEAR,
        )
        self.assertEqual(
            policy.static_indication(_route("R", RouteEndKind.DARK_EXIT), graph),
            Indication.RESTRICTING,
        )

    def test_advanced_approach_switch_override(self) -> None:
        self.assertEqual(
            RouteSignalingPolicy().static_indication(
                _route("R"),
                _graph("CLEAR/ADVANCED_APPROACH"),
            ),
            Indication.ADVANCED_APPROACH,
        )

    def test_facing_reverse_uses_switch_diverging_cap(self) -> None:
        route = replace(
            _route("R"),
            switch_traversals=(
                SwitchTraversal(
                    switch_name="799",
                    entry_pin="1",
                    exit_pin="3",
                    alignment="R",
                    point_traversal=PointTraversal.FACING,
                ),
            ),
        )

        self.assertEqual(
            RouteSignalingPolicy().static_indication(
                route,
                _graph("CLEAR/DIVERGING_APPROACH"),
            ),
            Indication.DIVERGING_APPROACH,
        )

    def test_trailing_reverse_defaults_to_approach(self) -> None:
        route = replace(
            _route("R"),
            switch_traversals=(
                SwitchTraversal(
                    switch_name="799",
                    entry_pin="3",
                    exit_pin="1",
                    alignment="R",
                    point_traversal=PointTraversal.TRAILING,
                ),
            ),
        )

        self.assertEqual(
            RouteSignalingPolicy().static_indication(
                route,
                _graph("CLEAR/DIVERGING_APPROACH"),
            ),
            Indication.APPROACH,
        )

    def test_dark_exit_preserves_facing_diverging_geometry(self) -> None:
        facing = replace(
            _route("R", RouteEndKind.DARK_EXIT),
            switch_traversals=(
                SwitchTraversal(
                    switch_name="799",
                    entry_pin="1",
                    exit_pin="3",
                    alignment="R",
                    point_traversal=PointTraversal.FACING,
                ),
            ),
        )
        trailing = replace(
            _route("R", RouteEndKind.DARK_EXIT),
            switch_traversals=(
                SwitchTraversal(
                    switch_name="799",
                    entry_pin="3",
                    exit_pin="1",
                    alignment="R",
                    point_traversal=PointTraversal.TRAILING,
                ),
            ),
        )

        policy = RouteSignalingPolicy()
        graph = _graph()
        self.assertEqual(
            policy.static_indication(facing, graph),
            Indication.DIVERGING_RESTRICTING,
        )
        self.assertEqual(
            policy.static_indication(trailing, graph),
            Indication.RESTRICTING,
        )

    def test_switch_indications_normalize_case_and_word_separators(self) -> None:
        for spelling in (
            "clear/diverging clear",
            "CLEAR / diverging-clear",
            "Clear/Diverging_Clear",
        ):
            with self.subTest(spelling=spelling):
                self.assertEqual(
                    parse_switch_indications(spelling),
                    (Indication.CLEAR, Indication.DIVERGING_CLEAR),
                )

    def test_mvp_indication_vocabulary_is_accepted(self) -> None:
        documented_indications = (
            Indication.CLEAR,
            Indication.ADVANCED_APPROACH,
            Indication.APPROACH,
            Indication.DIVERGING_CLEAR,
            Indication.DIVERGING_ADVANCED_APPROACH,
            Indication.DIVERGING_APPROACH,
            Indication.SECONDARY_DIVERGING_CLEAR,
            Indication.SECONDARY_DIVERGING_ADVANCED_APPROACH,
            Indication.SECONDARY_DIVERGING_APPROACH,
            Indication.STOP,
            Indication.UNLIT,
        )

        for indication in documented_indications:
            with self.subTest(indication=indication):
                self.assertEqual(
                    parse_switch_indications(f"CLEAR/{indication.value}"),
                    (Indication.CLEAR, indication),
                )

    def test_cli_projections_include_compiled_static_indication(self) -> None:
        graph = _graph()
        graph.routes = [_route("R")]
        graph.routes = RouteSignalingPolicy().compile_static_indications(graph)

        self.assertEqual(
            graph.routes[0].static_indication,
            Indication.DIVERGING_CLEAR,
        )

        self.assertIn("DIVERGING_CLEAR", render_text(graph))
        rendered_route = json.loads(render_json(graph))["routes"][0]
        self.assertEqual(rendered_route["static_indication"], "DIVERGING_CLEAR")
        self.assertIn("DIVERGING_CLEAR", rendered_route["presentation"])

    def test_layout_renderers_use_logical_width_and_heading_aware_turnouts(self) -> None:
        graph = _layout_graph()

        board = render_model_board_svg(graph)
        overview = render_layout_overview_svg(graph)

        self.assertIn('width="6in"', board)
        self.assertIn('width="6in"', overview)
        self.assertIn('data-switch="795"', board)
        self.assertIn('data-from="N" data-to="C"', board)
        self.assertIn('data-from="C" data-to="R"', board)
        ports = {
            port.identifier: port
            for component in graph.board_components
            for port in component.ports
        }
        self.assertLess(
            ports["turnout:795:R"].x_units,
            ports["turnout:795:C"].x_units,
        )
        self.assertEqual(
            next(
                connection.start_port_id
                for connection in graph.board_connections
                if connection.identifier == "branch"
            ),
            "turnout:795:R",
        )
        self.assertIn(
            'data-from="C" data-to="R" x1="431" y1="310" x2="350" y2="180"',
            board,
        )
        self.assertIn('class="dark-track"', board)
        self.assertIn('class="track-circuit-lamp"', board)
        self.assertIn('class="frog-lamp"', board)
        self.assertIn('class="lock-actuator"', board)
        self.assertIn(
            ".switch-normal,.switch-leg{stroke:#FFF;stroke-width:6;fill:none}",
            board,
        )
        self.assertNotIn('class="irj-gap"', board)
        self.assertIn('class="dark-track" x="24" y="307" width="185"', board)
        self.assertIn('class="physical-track" x1="223" y1="310"', board)
        self.assertNotIn('class="lane-label"', board)
        edge_labels = board.split('<g id="board-edge-labels">', 1)[1]
        self.assertIn(">MT</text>", edge_labels)
        self.assertIn(">MT1</text>", edge_labels)
        self.assertNotIn(">Industry</text>", edge_labels)
        self.assertIn(
            'class="signal-label" text-anchor="end" x="188" y="334">795EA</text>',
            board,
        )
        self.assertIn('class="mast" x1="216" y1="323"', board)
        self.assertIn('r="6"', board)
        self.assertIn(">SW795</text>", board)
        self.assertIn('class="switch-label" x="408" y="344">SW795</text>', board)
        self.assertIn('data-switch="795"', overview)

    def test_board_route_overlay_uses_table_aspects_and_preserves_base(self) -> None:
        graph = _layout_graph()
        route = replace(
            _route("R"),
            name="Fixture-Diverging",
            mast_reference="S795E1",
            mast_name="795EA",
            switch_alignments=(("795", "R"),),
            path_nets=("main-left", "main-right", "branch"),
            static_indication=Indication.DIVERGING_CLEAR,
        )
        graph.routes = [route]

        base = render_model_board_svg(graph)
        overlay = render_route_board_svg(graph, route_name=route.name)

        self.assertNotIn('class="route-overlay"', base)
        self.assertNotIn('id="board-route-list"', base)
        interactive = render_route_board_svg(graph)
        self.assertIn('id="board-route-list"', interactive)
        self.assertIn("function showRoute(id)", interactive)
        self.assertIn("onmouseenter=", interactive)
        self.assertIn(
            'data-route="Fixture-Diverging" data-indication="DIVERGING_CLEAR"',
            overlay,
        )
        self.assertIn('stroke="#22C55E"', overlay)
        self.assertIn('data-aspect="red"', overlay)
        self.assertIn('data-aspect="green"', overlay)
        self.assertLess(
            overlay.index('data-aspect="green"'),
            overlay.index('data-aspect="red"'),
        )
        self.assertIn('data-from="C" data-to="R"', overlay)
        with self.assertRaisesRegex(ValueError, "Expected exactly one route"):
            render_route_board_svg(graph, route_name="unknown")

    def test_indication_aspect_palette_reflects_route_aspect_table(self) -> None:
        self.assertEqual(
            _indication_aspects(Indication.CLEAR).head_colors,
            ("green", "red"),
        )
        self.assertEqual(
            _indication_aspects(Indication.DIVERGING_CLEAR).head_colors,
            ("red", "green"),
        )
        self.assertEqual(
            _indication_aspects(Indication.ADVANCED_APPROACH).flashing_heads,
            (0,),
        )
        self.assertEqual(
            _indication_aspects(Indication.DIVERGING_RESTRICTING).flashing_heads,
            (1,),
        )

    def test_single_head_diverging_restricting_uses_restricting_aspect(self) -> None:
        graph = _layout_graph()
        route = replace(
            _route("R", RouteEndKind.DARK_EXIT),
            name="Fixture-Diverging-Restricting",
            mast_reference="S795E1",
            mast_name="795EA",
            switch_alignments=(("795", "R"),),
            path_nets=("branch",),
            head_names=("A",),
            static_indication=Indication.DIVERGING_RESTRICTING,
        )
        graph.routes = [route]

        svg = render_route_board_svg(graph, route_name=route.name)

        self.assertIn('data-indication="DIVERGING_RESTRICTING"', svg)
        self.assertEqual(svg.count('<circle class="route-aspect-head'), 1)
        self.assertIn('route-aspect-head route-aspect-flashing', svg)
    def test_dot_projection_includes_topology_and_route_overlay(self) -> None:
        graph = _graph()
        graph.nets = [
            PlantNet(
                name="2SA",
                net_class=NetClass.TRACK,
                raw_name="/2SA",
                nodes=(("SW799", "1"),),
                authoritative_label=True,
            )
        ]
        graph.routes = [
            replace(
                _route("R"),
                path_nets=("2SA", "switch:799:R"),
            )
        ]

        dot = render_dot(graph, route_name="MT-Branch")

        self.assertIn("digraph PlantTopology", dot)
        self.assertIn('rankdir=LR, size="8.5,11!", ratio=fill', dot)
        self.assertIn("Track\\n2SA", dot)
        self.assertIn("Route: MT-Branch", dot)
        self.assertIn("penwidth=3", dot)
        self.assertIn("style=invis, weight=100", dot)

    def test_swim_lane_projection_raises_source_right_reverse_branch(self) -> None:
        graph = _graph()
        graph.switch_geometries["799"] = SwitchGeometry(
            switch_name="799",
            cn_heading=SchematicHeading.RIGHT,
            reverse_side=TurnoutHand.RIGHT,
        )
        graph.routes = [
            replace(
                _route("R"),
                path_nets=("switch:799:R",),
                switch_traversals=(
                    SwitchTraversal(
                        switch_name="799",
                        entry_pin="1",
                        exit_pin="3",
                        alignment="R",
                        point_traversal=PointTraversal.FACING,
                    ),
                ),
            )
        ]

        svg = render_swim_lane_svg(graph, route_name="MT-Branch")

        self.assertIn('width="850" height="1100"', svg)
        self.assertIn("C→N remains in lane", svg)
        self.assertIn("SW799 R F", svg)
        self.assertIn('d="M 72 300 L 132 180 L 192 180"', svg)

    def test_swim_lane_projection_preserves_terminal_channels_across_routes(
        self,
    ) -> None:
        graph = _graph()
        for switch_name in ("783", "795", "799"):
            graph.switch_geometries[switch_name] = SwitchGeometry(
                switch_name=switch_name,
                cn_heading=SchematicHeading.RIGHT,
                reverse_side=TurnoutHand.RIGHT,
            )

        def crossing(
            switch_name: str,
            entry_pin: str,
            exit_pin: str,
            alignment: str,
        ) -> SwitchTraversal:
            return SwitchTraversal(
                switch_name=switch_name,
                entry_pin=entry_pin,
                exit_pin=exit_pin,
                alignment=alignment,
                point_traversal=(
                    PointTraversal.FACING
                    if entry_pin == "1"
                    else PointTraversal.TRAILING
                ),
            )

        graph.routes = [
            replace(
                _route("N"),
                name="MT-MT1",
                entry_designation="MT",
                exit_designation="MT1",
                path_nets=("switch:783:N",),
                switch_traversals=(crossing("783", "1", "2", "N"),),
            ),
            replace(
                _route("N"),
                name="MT-MT2",
                entry_designation="MT",
                exit_designation="MT2",
                path_nets=(
                    "switch:783:R",
                    "switch:795:N",
                    "switch:799:N",
                ),
                switch_traversals=(
                    crossing("783", "1", "3", "R"),
                    crossing("795", "2", "1", "N"),
                    crossing("799", "1", "2", "N"),
                ),
            ),
            replace(
                _route("R"),
                name="MT2-Industry",
                entry_designation="MT2",
                exit_designation="Industry",
                path_nets=("switch:799:N", "switch:795:R"),
                switch_traversals=(
                    crossing("799", "2", "1", "N"),
                    crossing("795", "1", "3", "R"),
                ),
            ),
        ]

        svg = render_swim_lane_svg(graph, route_name="MT2-Industry")

        self.assertIn('d="M 72 300 L 132 300 L 192 180 L 252 180"', svg)

    def test_model_board_renders_all_routes_with_legend_and_wrapped_boxes(self) -> None:
        graph = _graph()
        graph.routes = [
            replace(
                _route("N"),
                name="Main Through",
                entry_designation="Mainline West",
                exit_designation="Mainline East",
                path_nets=("joint:B1",),
            ),
            replace(
                _route("R"),
                name="Branch Diverging",
                entry_designation="Mainline West",
                exit_designation="Industry Spur",
                path_nets=("switch:799:R",),
                switch_traversals=(
                    SwitchTraversal(
                        switch_name="799",
                        entry_pin="1",
                        exit_pin="3",
                        alignment="R",
                        point_traversal=PointTraversal.FACING,
                    ),
                ),
            ),
        ]
        graph.switch_geometries["799"] = SwitchGeometry(
            switch_name="799",
            cn_heading=SchematicHeading.RIGHT,
            reverse_side=TurnoutHand.RIGHT,
        )

        svg = render_route_comparison_svg(graph)

        self.assertIn('width="1800" height="1050"', svg)
        self.assertIn("Route legend", svg)
        self.assertEqual(svg.count('class="board-route"'), 2)
        self.assertIn('data-route="Main Through"', svg)
        self.assertIn("M 190 ", svg)
        self.assertIn(" 1270 ", svg)
        self.assertEqual(svg.count('class="switch-leg"'), 2)
        self.assertEqual(svg.count('class="mast"'), 2)
        self.assertIn('class="signal-irj"', svg)
        self.assertNotIn("Mainline West", svg)
        self.assertIn('id="route-indication-0"', svg)
        self.assertIn("onmouseenter=", svg)

    def test_malformed_switch_indications_fail_closed(self) -> None:
        graph = _graph()
        graph.entities["SW799"] = PlantEntity(
            reference="SW799",
            kind=EntityKind.SWITCH_POWERED,
            lib_id="Railroad:Switch_Powered",
            value="799",
            canonical_name="799",
            fields={"Indications": "CLEAR/NOT_AN_INDICATION"},
        )

        self.assertEqual(
            RouteSignalingPolicy().static_indication(_route("R"), graph),
            Indication.STOP,
        )

    def test_failed_runtime_predicate_returns_stop(self) -> None:
        policy = RouteSignalingPolicy()
        route = _route("R")
        state = RouteEvaluationState(
            signal_demands={"784": "RIGHT"},
            switches=self._ready_state().switches,
            track_circuits={
                "2SA": TrackCircuitRuntimeState(vacant=False, healthy=True)
            },
        )

        result = policy.evaluate(route, _graph(), state)

        self.assertEqual(result.indication, Indication.STOP)
        self.assertEqual(result.blockers, ("track_circuit_occupied:2SA",))

    def test_valid_runtime_predicates_return_static_indication(self) -> None:
        policy = RouteSignalingPolicy()
        route = _route("R")

        result = policy.evaluate(route, _graph(), self._ready_state())

        self.assertEqual(result.indication, Indication.DIVERGING_CLEAR)
        self.assertEqual(result.blockers, ())

    def test_unavailable_or_invalid_runtime_inputs_fail_closed(self) -> None:
        policy = RouteSignalingPolicy()
        route = _route("R")
        ready = self._ready_state()
        states = (
            (
                RouteEvaluationState(
                    signal_demands={},
                    switches=ready.switches,
                    track_circuits=ready.track_circuits,
                ),
                ("demand_not_granted:784:RIGHT",),
            ),
            (
                RouteEvaluationState(
                    signal_demands=ready.signal_demands,
                    switches={
                        "799": SwitchRuntimeState(
                            position="N",
                            correspondence=True,
                            locked=True,
                            os_vacant=True,
                        )
                    },
                    track_circuits=ready.track_circuits,
                ),
                ("switch_misaligned:799:R",),
            ),
            (
                RouteEvaluationState(
                    signal_demands=ready.signal_demands,
                    switches={
                        "799": SwitchRuntimeState(
                            position="R",
                            correspondence=False,
                            locked=True,
                            os_vacant=True,
                        )
                    },
                    track_circuits=ready.track_circuits,
                ),
                ("switch_no_correspondence:799",),
            ),
            (
                RouteEvaluationState(
                    signal_demands=ready.signal_demands,
                    switches={
                        "799": SwitchRuntimeState(
                            position="R",
                            correspondence=True,
                            locked=False,
                            os_vacant=True,
                        )
                    },
                    track_circuits=ready.track_circuits,
                ),
                ("switch_unlocked:799",),
            ),
            (
                RouteEvaluationState(
                    signal_demands=ready.signal_demands,
                    switches={
                        "799": SwitchRuntimeState(
                            position="R",
                            correspondence=True,
                            locked=True,
                            os_vacant=False,
                        )
                    },
                    track_circuits=ready.track_circuits,
                ),
                ("switch_os_occupied:799",),
            ),
            (
                RouteEvaluationState(
                    signal_demands=ready.signal_demands,
                    switches=ready.switches,
                    track_circuits={},
                ),
                ("track_circuit_unavailable:2SA",),
            ),
            (
                RouteEvaluationState(
                    signal_demands=ready.signal_demands,
                    switches=ready.switches,
                    track_circuits={
                        "2SA": TrackCircuitRuntimeState(
                            vacant=True,
                            healthy=False,
                        )
                    },
                ),
                ("track_circuit_unhealthy:2SA",),
            ),
        )

        for state, expected_blockers in states:
            with self.subTest(blockers=expected_blockers):
                result = policy.evaluate(route, _graph(), state)
                self.assertEqual(result.indication, Indication.STOP)
                self.assertEqual(result.blockers, expected_blockers)
