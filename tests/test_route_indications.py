"""Tests for static and runtime route-signaling indication evaluation."""

from __future__ import annotations

import json

import sys
import unittest
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
from plant_graph.types import (
    CircuitRole,
    EntityKind,
    PlantEntity,
    PlantGraph,
    RouteEndKind,
    SignalRoute,
)
from parse_kicad_plant import render_json, render_text


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
