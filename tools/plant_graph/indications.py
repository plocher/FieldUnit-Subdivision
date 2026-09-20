"""Static route indication caps and fail-closed runtime evaluation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
import re

from plant_graph.types import (
    EntityKind,
    Indication,
    PlantEntity,
    PlantGraph,
    PointTraversal,
    RouteEndKind,
    SignalRoute,
)


# Conservative MVP cap order only. A regime profile supplies the later,
# authoritative aspect and speed semantics for these non-total relationships.
_RESTRICTIVENESS: dict[Indication, int] = {
    Indication.STOP: 0,
    Indication.UNLIT: 0,
    Indication.RESTRICTING: 1,
    Indication.DIVERGING_RESTRICTING: 1,
    Indication.APPROACH: 2,
    Indication.DIVERGING_APPROACH: 2,
    Indication.SECONDARY_DIVERGING_APPROACH: 2,
    Indication.DIVERGING_CLEAR: 3,
    Indication.DIVERGING_ADVANCED_APPROACH: 3,
    Indication.SECONDARY_DIVERGING_CLEAR: 3,
    Indication.SECONDARY_DIVERGING_ADVANCED_APPROACH: 3,
    Indication.ADVANCED_APPROACH: 4,
    Indication.CLEAR: 5,
}
_SWITCH_CAP_INDICATIONS = frozenset(Indication) - {
    Indication.DIVERGING_RESTRICTING,
}


@dataclass(frozen=True)
class SwitchRuntimeState:
    """Live evidence required to use one lined switch in a route."""

    position: str
    correspondence: bool
    locked: bool
    os_vacant: bool


@dataclass(frozen=True)
class TrackCircuitRuntimeState:
    """Live occupancy and health evidence for one required track circuit."""

    vacant: bool
    healthy: bool


@dataclass(frozen=True)
class RouteEvaluationState:
    """Runtime inventory used to gate one structural route."""

    signal_demands: Mapping[str, str] = field(default_factory=dict)
    switches: Mapping[str, SwitchRuntimeState] = field(default_factory=dict)
    track_circuits: Mapping[str, TrackCircuitRuntimeState] = field(
        default_factory=dict
    )


@dataclass(frozen=True)
class RouteEvaluation:
    """Result of evaluating one structural route against live evidence."""

    indication: Indication
    blockers: tuple[str, ...] = ()



def parse_switch_indications(value: str) -> tuple[Indication, Indication]:
    """Parse a switch's ``NORMAL/REVERSE`` indication property.

    Raises:
        ValueError: The property is not exactly two supported standard
            indications in normal/reverse order.
    """
    values = [_normalize_indication_name(part) for part in value.split("/")]
    if len(values) != 2 or any(not part for part in values):
        raise ValueError("Indications must be NORMAL/REVERSE")
    try:
        normal, reverse = Indication(values[0]), Indication(values[1])
    except ValueError as exc:
        raise ValueError(
            "Indications must contain supported standard Indications"
        ) from exc
    if normal not in _SWITCH_CAP_INDICATIONS or reverse not in _SWITCH_CAP_INDICATIONS:
        raise ValueError(
            "Indications cannot contain derived route-only Indications"
        )
    return normal, reverse


def _normalize_indication_name(value: str) -> str:
    """Return the canonical uppercase identifier for one indication spelling."""
    return re.sub(r"[\s_-]+", "_", value.strip().upper())


class RouteSignalingPolicy:
    """Compile static route caps and apply fail-closed runtime gates."""
    def compile_static_indications(
        self,
        graph: PlantGraph,
    ) -> list[SignalRoute]:
        """Return routes annotated with their compiled static indications."""
        return [
            replace(
                route,
                static_indication=self._derive_static_indication(route, graph),
            )
            for route in graph.routes
        ]

    def static_indication(self, route: SignalRoute, graph: PlantGraph) -> Indication:
        """Return ``route``'s compiled static cap or derive one for a fixture."""
        if route.static_indication is not None:
            return route.static_indication
        return self._derive_static_indication(route, graph)

    def _derive_static_indication(
        self,
        route: SignalRoute,
        graph: PlantGraph,
    ) -> Indication:
        """Return the most restrictive static cap for an uncompiled route.
        A dark exit always caps the route at Restricting. Facing traversals
        contribute their configured Normal/Reverse cap; trailing R→C
        traversals default to Approach. Otherwise normal geometry defaults to
        Clear and reverse geometry to Approach.
        Invalid source data fails closed to Stop; the compiler separately
        diagnoses the malformed property at data intake.
        """
        caps: list[Indication] = []
        if route.end_kind is RouteEndKind.DARK_EXIT:
            caps.append(
                Indication.DIVERGING_RESTRICTING
                if any(
                    traversal.alignment == "R"
                    and traversal.point_traversal is PointTraversal.FACING
                    for traversal in route.switch_traversals
                )
                else Indication.RESTRICTING
            )

        switches = self._switches_by_name(graph)
        traversal_by_switch = {
            traversal.switch_name: traversal
            for traversal in route.switch_traversals
        }
        for switch_name, position in route.switch_alignments:
            traversal = traversal_by_switch.get(switch_name)
            if (
                position == "R"
                and traversal is not None
                and traversal.point_traversal is PointTraversal.TRAILING
            ):
                caps.append(Indication.APPROACH)
                continue
            cap = self._switch_cap(switches.get(switch_name), position)
            if cap is Indication.STOP:
                return Indication.STOP
            caps.append(cap)

        return min(caps or [Indication.CLEAR], key=_RESTRICTIVENESS.__getitem__)

    def evaluate(
        self,
        route: SignalRoute,
        graph: PlantGraph,
        state: RouteEvaluationState,
    ) -> RouteEvaluation:
        """Evaluate one route, returning Stop unless every required gate passes."""
        blockers = self._runtime_blockers(route, state)
        if blockers:
            return RouteEvaluation(Indication.STOP, tuple(blockers))
        return RouteEvaluation(self.static_indication(route, graph))


    def _switches_by_name(self, graph: PlantGraph) -> dict[str, PlantEntity]:
        """Return powered or locked switches keyed by canonical switch name."""
        return {
            entity.canonical_name: entity
            for entity in graph.entities.values()
            if entity.kind in {EntityKind.SWITCH_POWERED, EntityKind.SWITCH_LOCK}
            and entity.canonical_name
        }

    def _switch_cap(
        self,
        switch: PlantEntity | None,
        position: str,
    ) -> Indication:
        """Return one switch's static cap, failing closed for invalid source data."""
        default = Indication.CLEAR if position == "N" else Indication.APPROACH
        if switch is None:
            return default
        raw_value = (switch.fields.get("Indications") or "").strip()
        if not raw_value:
            return default
        try:
            normal, reverse = parse_switch_indications(raw_value)
        except ValueError:
            return Indication.STOP
        return normal if position == "N" else reverse if position == "R" else Indication.STOP

    def _runtime_blockers(
        self,
        route: SignalRoute,
        state: RouteEvaluationState,
    ) -> list[str]:
        """Return unmet demand, switch, lock, OS, and clear-track predicates."""
        blockers: list[str] = []
        required_demand = route.direction.upper()
        actual_demand = (state.signal_demands.get(route.signal_name) or "").upper()
        if actual_demand != required_demand:
            blockers.append(
                f"demand_not_granted:{route.signal_name}:{required_demand}"
            )

        for switch_name, required_position in route.switch_alignments:
            switch = state.switches.get(switch_name)
            if switch is None:
                blockers.append(f"switch_unavailable:{switch_name}")
                continue
            if switch.position.upper() != required_position:
                blockers.append(
                    f"switch_misaligned:{switch_name}:{required_position}"
                )
            if not switch.correspondence:
                blockers.append(f"switch_no_correspondence:{switch_name}")
            if not switch.locked:
                blockers.append(f"switch_unlocked:{switch_name}")
            if not switch.os_vacant:
                blockers.append(f"switch_os_occupied:{switch_name}")

        for circuit in route.clear_track_circuits:
            track = state.track_circuits.get(circuit)
            if track is None:
                blockers.append(f"track_circuit_unavailable:{circuit}")
                continue
            if not track.healthy:
                blockers.append(f"track_circuit_unhealthy:{circuit}")
            if not track.vacant:
                blockers.append(f"track_circuit_occupied:{circuit}")
        return blockers
