"""Tool-neutral portable Interlocking Plant Model projection.

This module deliberately consumes the KiCad-derived ``PlantGraph`` but does
not expose KiCad references, raw net names, symbol-library IDs, placements, or
renderer layout data as part of the public interchange contract.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from plant_graph.indications import RouteSignalingPolicy
from plant_graph.routes import _natural_sort_key
from plant_graph.types import (
    CircuitRole,
    EntityKind,
    Indication,
    NetClass,
    PlantGraph,
    RouteEndKind,
)


SCHEMA_ID = "https://fieldunit.dev/schema/interlocking-plant/v1.json"
SCHEMA_VERSION = "1.0.0"

_SWITCH_KINDS = frozenset(
    {EntityKind.SWITCH_POWERED, EntityKind.SWITCH_LOCK}
)
_DERAIL_KIND = EntityKind.DERAIL
_TOPOLOGY_NET_CLASSES = frozenset(
    {NetClass.TRACK, NetClass.DARK_TRACK, NetClass.SWITCH_OS}
)


@dataclass(frozen=True)
class InterlockingPlantModel:
    """Versioned, editor-neutral definition for one Interlocking Plant."""

    schema_id: str
    schema_version: str
    document: dict[str, str]
    profile: dict[str, str]
    identity: dict[str, Any]
    appliances: dict[str, Any]
    topology: dict[str, Any]
    terminals: tuple[dict[str, Any], ...]
    routes: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        """Return canonical JSON-compatible data without source-tool evidence."""

        return {
            "$schema": self.schema_id,
            "schemaVersion": self.schema_version,
            "document": self.document,
            "profile": self.profile,
            "identity": self.identity,
            "appliances": self.appliances,
            "topology": self.topology,
            "terminals": list(self.terminals),
            "routes": list(self.routes),
        }

    def to_json(self) -> str:
        """Return canonical, stable, pretty JSON for interchange and diffs."""

        return json.dumps(
            self.to_dict(),
            indent=2,
            sort_keys=False,
            ensure_ascii=False,
        ) + "\n"

def validate_interlocking_plant_model(
    model: InterlockingPlantModel,
) -> tuple[str, ...]:
    """Return semantic contract violations for one portable model.

    This validates referential integrity without adding a third-party JSON
    Schema dependency to the KiCad compiler toolchain.
    """

    payload = model.to_dict()
    appliances = payload["appliances"]
    topology = payload["topology"]
    errors: list[str] = []

    switch_ids = {item["id"] for item in appliances["switches"]}
    derail_ids = {item["id"] for item in appliances["derails"]}
    circuit_ids = {item["id"] for item in appliances["trackCircuits"]}
    terminal_ids = {item["id"] for item in payload["terminals"]}
    internal_node_ids = {item["id"] for item in topology["internalNodes"]}
    endpoint_ids = set(terminal_ids) | set(internal_node_ids)
    endpoint_ids.update(
        f"switch:{switch_id}:{port}"
        for switch_id in switch_ids
        for port in ("C", "N", "R")
    )
    endpoint_ids.update(
        f"derail:{derail_id}:{port}"
        for derail_id in derail_ids
        for port in ("C", "N")
    )

    groups_by_member: dict[str, dict[str, Any]] = {}
    for group in appliances["controlGroups"]:
        members = group["members"]
        if (
            group["kind"] != "crossover"
            or len(members) != 2
            or members[0] != group["id"]
            or members[1] != f"{group['id']}B"
        ):
            errors.append(f"invalid_control_group:{group['id']}")
        for member in members:
            if member not in switch_ids:
                errors.append(
                    f"control_group_unknown_switch:{group['id']}:{member}"
                )
            elif member in groups_by_member:
                errors.append(f"switch_multiple_control_groups:{member}")
            else:
                groups_by_member[member] = group

    for switch_id in switch_ids:
        if switch_id.endswith("B") and switch_id not in groups_by_member:
            errors.append(f"crossover_orphan_member:{switch_id}")
    masts_by_id = {item["id"]: item for item in appliances["masts"]}
    signals_by_id = {item["id"]: item for item in appliances["signals"]}
    mast_ids = set(masts_by_id)
    signal_ids = set(signals_by_id)
    controlled_point_member_ids = {
        "switch": switch_ids,
        "derail": derail_ids,
        "trackCircuit": circuit_ids,
        "mast": mast_ids,
    }

    for mast_id, mast in masts_by_id.items():
        if mast["signal"] not in signal_ids:
            errors.append(f"mast_unknown_signal:{mast_id}:{mast['signal']}")
        if mast["kind"] not in {"single", "double", "dwarf"}:
            errors.append(f"mast_invalid_kind:{mast_id}:{mast['kind']}")
        if not mast["heads"]:
            errors.append(f"mast_without_heads:{mast_id}")
        approach_terminal = mast["approachTerminal"]
        if approach_terminal is not None and approach_terminal not in terminal_ids:
            errors.append(
                f"mast_unknown_approach_terminal:{mast_id}:{approach_terminal}"
            )

    for signal_id, signal in signals_by_id.items():
        for mast_id in signal["masts"]:
            if mast_id not in mast_ids:
                errors.append(f"signal_unknown_mast:{signal_id}:{mast_id}")
            elif masts_by_id[mast_id]["signal"] != signal_id:
                errors.append(f"signal_mast_owner_mismatch:{signal_id}:{mast_id}")

    for controlled_point in appliances["controlledPoints"]:
        for member in controlled_point["members"]:
            expected_ids = controlled_point_member_ids.get(member["kind"])
            if expected_ids is None or member["id"] not in expected_ids:
                errors.append(
                    "controlled_point_unknown_member:"
                    f"{controlled_point['id']}:{member['kind']}:{member['id']}"
                )

    for derail in appliances["derails"]:
        derail_id = derail["id"]
        controlling_switch = derail["controllingSwitch"]
        if derail["controlMode"] == "dependent":
            if controlling_switch not in switch_ids:
                errors.append(
                    f"dependent_derail_unknown_switch:{derail_id}:{controlling_switch}"
                )
        elif derail["controlMode"] == "dispatcher":
            if controlling_switch is not None:
                errors.append(f"dispatcher_derail_has_controller:{derail_id}")
        else:
            errors.append(f"derail_invalid_control_mode:{derail_id}")
        track_circuit = derail["trackCircuit"]
        if track_circuit is not None and track_circuit not in circuit_ids:
            errors.append(
                f"derail_unknown_track_circuit:{derail_id}:{track_circuit}"
            )

    for segment in topology["segments"]:
        circuit = segment["trackCircuit"]
        if circuit not in {None, ""} and circuit not in circuit_ids:
            errors.append(
                f"segment_unknown_track_circuit:{segment['id']}:{circuit}"
            )
        for endpoint in segment["endpoints"]:
            if endpoint not in endpoint_ids:
                errors.append(
                    f"segment_unknown_endpoint:{segment['id']}:{endpoint}"
                )

    for route in payload["routes"]:
        route_id = route["id"]
        mast = masts_by_id.get(route["mast"])
        if route["signal"] not in signal_ids:
            errors.append(f"route_unknown_signal:{route_id}:{route['signal']}")
        if mast is None:
            errors.append(f"route_unknown_mast:{route_id}:{route['mast']}")
        elif (
            mast["signal"] != route["signal"]
            or mast["direction"] != route["direction"]
        ):
            errors.append(f"route_mast_binding_mismatch:{route_id}:{route['mast']}")
        if route["staticIndication"] not in {item.value for item in Indication}:
            errors.append(
                f"route_unknown_static_indication:{route_id}:"
                f"{route['staticIndication']}"
            )
        for field_name in ("entryTerminal", "exitTerminal"):
            terminal = route[field_name]
            if terminal is not None and terminal not in terminal_ids:
                errors.append(
                    f"route_unknown_terminal:{route['id']}:{field_name}:{terminal}"
                )
        for alignment in route["alignments"]:
            appliance = alignment["appliance"]
            if appliance not in switch_ids | derail_ids:
                errors.append(
                    f"route_unknown_alignment:{route['id']}:{appliance}"
                )
            if alignment["position"] not in {"NORMAL", "REVERSE"}:
                errors.append(
                    "route_invalid_alignment_position:"
                    f"{route_id}:{appliance}:{alignment['position']}"
                )
        for circuit in route["clearTrackCircuits"]:
            if circuit not in circuit_ids:
                errors.append(
                    f"route_unknown_clear_circuit:{route['id']}:{circuit}"
                )
        for field_name in ("entrance", "approaching"):
            circuit = route[field_name]
            if circuit is not None and circuit not in circuit_ids:
                errors.append(
                    f"route_unknown_{field_name}_circuit:{route['id']}:{circuit}"
                )
        exit_face = route["exitFace"]
        if exit_face is not None:
            exit_mast = masts_by_id.get(exit_face["mast"])
            if exit_face["signal"] not in signal_ids or exit_mast is None:
                errors.append(f"route_unknown_exit_face:{route_id}")
            elif (
                exit_mast["signal"] != exit_face["signal"]
                or exit_mast["direction"] != exit_face["direction"]
            ):
                errors.append(
                    f"route_exit_face_binding_mismatch:{route_id}:{exit_face['mast']}"
                )

    return tuple(sorted(set(errors)))


def compile_interlocking_plant_model(
    graph: PlantGraph,
    *,
    plant_name: str | None = None,
    plant_id: str | None = None,
) -> InterlockingPlantModel:
    """Project compiler evidence into a portable, semantic plant definition.

    The projection intentionally omits realization bindings, source provenance,
    layout coordinates, diagnostics, aliases, and renderer-only artifacts.
    Consumers requiring those facts receive a separate projection/binding.
    """

    terminal_ids = _terminal_ids(graph)
    internal_node_ids = _internal_node_ids(graph)
    indication_policy = RouteSignalingPolicy()

    named_circuits = sorted(
        {
            entity.canonical_name
            for entity in graph.entities.values()
            if entity.kind is EntityKind.TRACK_CIRCUIT
            and entity.canonical_name
        }
        | {circuit.name for circuit in graph.derived_track_circuits}
    )
    switch_os = {
        circuit.switch_name: circuit.name
        for circuit in graph.derived_track_circuits
    }
    switches = [
        {
            "id": entity.canonical_name,
            "osTrackCircuit": switch_os.get(entity.canonical_name),
        }
        for entity in sorted(
            (
                entity
                for entity in graph.entities.values()
                if entity.kind in _SWITCH_KINDS and entity.canonical_name
            ),
            key=lambda entity: entity.canonical_name,
        )
    ]
    control_groups = _derived_control_groups(switches)

    mast_kinds = {
        EntityKind.MAST_SINGLE: "single",
        EntityKind.MAST_DOUBLE: "double",
        EntityKind.MAST_DWARF: "dwarf",
    }
    masts = [
        {
            "id": face.mast_name,
            "signal": face.signal_name,
            "direction": face.direction,
            "mast": face.mast_name,
            "kind": mast_kinds[graph.entities[face.mast_reference].kind],
            "heads": list(
                sorted(
                    attachment.head_name
                    for attachment in graph.mast_heads
                    if attachment.mast_name == face.mast_name
                )
            ),
            "headLetters": face.head_letters,
            "approachTerminal": _terminal_id_for_reference(
                terminal_ids,
                face.approach_terminal,
            ),
        }
        for face in sorted(
            graph.signal_faces,
            key=lambda face: (
                face.signal_name,
                face.direction,
                face.mast_name,
            ),
        )
    ]

    routes = [
        _route_model(route, graph, terminal_ids, indication_policy)
        for route in sorted(graph.routes, key=lambda route: route.name)
    ]

    return InterlockingPlantModel(
        schema_id=SCHEMA_ID,
        schema_version=SCHEMA_VERSION,
        document=_document_model(graph, plant_name=plant_name),
        profile=_profile_model(graph),
        identity=_identity(graph, plant_name=plant_name, plant_id=plant_id),
        appliances={
            "controlledPoints": _controlled_point_models(graph, masts),
            "switches": switches,
            "derails": _derail_models(graph),
            "controlGroups": control_groups,
            "trackCircuits": [{"id": name} for name in named_circuits],
            "signals": _signal_models(masts),
            "masts": masts,
        },
        topology={
            "segments": _segment_models(
                graph,
                terminal_ids,
                internal_node_ids,
                _circuit_by_net(graph),
            ),
            "internalNodes": [
                {"id": identifier, "kind": kind}
                for _reference, (identifier, kind) in sorted(
                    internal_node_ids.items(),
                )
            ],
        },
        terminals=tuple(
            {
                "id": terminal_ids[terminal.reference],
                "designation": terminal.designation,
                "kind": terminal.kind.value,
                "rulebook": terminal.rulebook,
            }
            for terminal in sorted(
                graph.terminals,
                key=lambda terminal: (
                    terminal.designation,
                    terminal.kind.value,
                    terminal.reference,
                ),
            )
        ),
        routes=tuple(routes),
    )


def _identity(
    graph: PlantGraph,
    *,
    plant_name: str | None,
    plant_id: str | None,
) -> dict[str, str]:
    """Return explicit plant identity, never inferred from board sections."""

    del graph
    name = plant_name or "Unnamed Interlocking Plant"
    return {
        "id": plant_id or _slug(name),
        "name": name,
    }

def _document_model(
    graph: PlantGraph,
    *,
    plant_name: str | None,
) -> dict[str, str]:
    """Return KiCad design-document identity separate from model schema version."""

    comments = graph.document.comments
    return {
        "title": graph.document.title or plant_name or "Unnamed Interlocking Plant",
        "revision": graph.document.revision,
        "date": graph.document.date,
        "company": graph.document.company,
        "status": comments.get(9, ""),
    }

def _profile_model(graph: PlantGraph) -> dict[str, str]:
    """Project Luchessa-style title-block profile facts without transport policy."""

    comments = graph.document.comments
    return {
        "railroad": comments.get(4, ""),
        "division": comments.get(5, ""),
        "era": _profile_value(comments.get(6, ""), "era"),
        "ctc": _profile_value(comments.get(7, ""), "ctc"),
    }

def _profile_value(value: str, label: str) -> str:
    """Remove one case-insensitive ``label:`` prefix from a profile comment."""

    prefix = f"{label}:"
    if value.casefold().startswith(prefix):
        return value[len(prefix):].strip()
    return value.strip()

def _signal_models(masts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group each drawn mast under its dispatcher-controlled signal."""

    mast_ids_by_signal: dict[str, list[str]] = {}
    for mast in masts:
        mast_ids_by_signal.setdefault(mast["signal"], []).append(mast["id"])
    return [
        {"id": signal, "masts": sorted(mast_ids)}
        for signal, mast_ids in sorted(mast_ids_by_signal.items())
    ]

def _controlled_point_models(
    graph: PlantGraph,
    masts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Project Main House appliance allocations declared by CP source fields."""

    controlled_points = sorted(
        entity.canonical_name
        for entity in graph.entities.values()
        if entity.kind is EntityKind.MAIN_HOUSE and entity.canonical_name
    )
    members: dict[str, list[dict[str, str]]] = {
        controlled_point: [] for controlled_point in controlled_points
    }
    kinds = {
        EntityKind.SWITCH_POWERED: "switch",
        EntityKind.SWITCH_LOCK: "switch",
        EntityKind.DERAIL: "derail",
        EntityKind.TRACK_CIRCUIT: "trackCircuit",
    }
    for entity in graph.entities.values():
        kind = kinds.get(entity.kind)
        controlled_point = (entity.fields.get("CP") or "").strip()
        if kind and controlled_point in members and entity.canonical_name:
            members[controlled_point].append(
                {"kind": kind, "id": entity.canonical_name}
            )
    face_by_mast = {
        face.mast_name: face
        for face in graph.signal_faces
    }
    for mast in masts:
        source_face = face_by_mast[mast["id"]]
        controlled_point = (
            graph.entities[source_face.irj_reference].fields.get("CP") or ""
        ).strip()
        if controlled_point in members:
            members[controlled_point].append(
                {"kind": "mast", "id": mast["id"]}
            )
    return [
        {
            "id": controlled_point,
            "members": sorted(
                members[controlled_point],
                key=lambda member: (member["kind"], member["id"]),
            ),
        }
        for controlled_point in controlled_points
    ]

def _derail_models(graph: PlantGraph) -> list[dict[str, str | None]]:
    """Project two-pin derails and their control relationship from source values."""
    track_circuit_by_derail = {
        circuit.switch_name: circuit.name
        for circuit in graph.derived_track_circuits
        if circuit.switch_name.endswith("D")
    }

    derails: list[dict[str, str | None]] = []
    for entity in sorted(
        (
            entity
            for entity in graph.entities.values()
            if entity.kind is _DERAIL_KIND and entity.canonical_name
        ),
        key=lambda entity: entity.canonical_name,
    ):
        dependent = entity.canonical_name.endswith("D")
        derails.append(
            {
                "id": entity.canonical_name,
                "controlMode": "dependent" if dependent else "dispatcher",
                "controllingSwitch": entity.canonical_name[:-1] if dependent else None,
                "trackCircuit": track_circuit_by_derail.get(entity.canonical_name),
            }
        )
    return derails

def _derived_control_groups(
    switches: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Derive ganged crossover control from the prototype ``783``/``783B`` convention."""

    switch_ids = {switch["id"] for switch in switches}
    groups: list[dict[str, Any]] = []
    for switch_id in sorted(switch_ids):
        if not switch_id.endswith("B"):
            continue
        primary = switch_id[:-1]
        if primary in switch_ids:
            groups.append(
                {
                    "id": primary,
                    "kind": "crossover",
                    "members": [primary, switch_id],
                    "commandMode": "ganged",
                    "correspondenceRule": "all_members",
                }
            )
    return groups


def _terminal_ids(graph: PlantGraph) -> dict[str, str]:
    """Return deterministic IDs without exposing source references publicly."""

    result: dict[str, str] = {}
    counts: dict[str, int] = {}
    for terminal in sorted(
        graph.terminals,
        key=lambda terminal: (
            terminal.designation,
            terminal.kind.value,
            terminal.reference,
        ),
    ):
        stem = f"terminal:{_slug(terminal.designation)}:{terminal.kind.value}"
        ordinal = counts.get(stem, 0) + 1
        counts[stem] = ordinal
        result[terminal.reference] = f"{stem}:{ordinal}"
    return result


def _internal_node_ids(graph: PlantGraph) -> dict[str, tuple[str, str]]:
    """Create opaque semantic IDs for unnamed IRJ and bumper topology nodes."""

    result: dict[str, tuple[str, str]] = {}
    ordinal = 0
    for entity in sorted(graph.entities.values(), key=lambda entity: entity.reference):
        if entity.kind not in {
            EntityKind.IRJ,
            EntityKind.IRJ_SIGNAL,
            EntityKind.BUMPER,
        }:
            continue
        ordinal += 1
        kind = (
            "signal_irj"
            if entity.kind is EntityKind.IRJ_SIGNAL
            else "irj"
            if entity.kind is EntityKind.IRJ
            else "bumper"
        )
        result[entity.reference] = (f"{kind}:{ordinal}", kind)
    return result


def _segment_models(
    graph: PlantGraph,
    terminal_ids: dict[str, str],
    internal_node_ids: dict[str, tuple[str, str]],
    circuit_by_net: dict[str, str],
) -> list[dict[str, Any]]:
    """Project track nets into topology segments using semantic endpoint IDs."""

    segments: list[dict[str, Any]] = []
    for ordinal, net in enumerate(
        sorted(
            (
                net
                for net in graph.nets
                if net.net_class in _TOPOLOGY_NET_CLASSES
            ),
            key=lambda net: (
                net.name,
                net.net_class.value,
                net.nodes,
            ),
        ),
        start=1,
    ):
        endpoints = sorted(
            filter(
                None,
                (
                    _endpoint_id(
                        graph,
                        reference,
                        pin,
                        terminal_ids,
                        internal_node_ids,
                    )
                    for reference, pin in net.nodes
                ),
            )
        )
        segments.append(
            {
                "id": f"segment:{ordinal}",
                "kind": net.net_class.value,
                "trackCircuit": circuit_by_net.get(net.name),
                "endpoints": endpoints,
            }
        )
    return segments


def _circuit_by_net(graph: PlantGraph) -> dict[str, str]:
    """Map a rail net to its explicit Track Circuit marker, if any."""

    mapping: dict[str, str] = {}
    for net in graph.nets:
        names = {
            graph.entities[reference].canonical_name
            for reference, _pin in net.nodes
            if reference in graph.entities
            and graph.entities[reference].kind is EntityKind.TRACK_CIRCUIT
            and graph.entities[reference].canonical_name
        }
        if len(names) == 1:
            mapping[net.name] = next(iter(names))
    return mapping


def _endpoint_id(
    graph: PlantGraph,
    reference: str,
    pin: str,
    terminal_ids: dict[str, str],
    internal_node_ids: dict[str, tuple[str, str]],
) -> str | None:
    if reference in terminal_ids:
        return terminal_ids[reference]
    if reference in internal_node_ids:
        return internal_node_ids[reference][0]
    entity = graph.entities.get(reference)
    if entity is None:
        return None
    if entity.kind in _SWITCH_KINDS:
        port = {"1": "C", "2": "N", "3": "R"}.get(pin)
        if port:
            return f"switch:{entity.canonical_name}:{port}"
    if entity.kind is _DERAIL_KIND:
        port = {"1": "C", "2": "N"}.get(pin)
        if port:
            return f"derail:{entity.canonical_name}:{port}"
    return None


def _route_model(
    route: Any,
    graph: PlantGraph,
    terminal_ids: dict[str, str],
    indication_policy: RouteSignalingPolicy,
) -> dict[str, Any]:
    entrance = _route_circuit(route, CircuitRole.ENTRANCE)
    approaching = _route_circuit(route, CircuitRole.DOWNSTREAM)

    return {
        "id": _slug(route.name),
        "name": route.name,
        "signal": route.signal_name,
        "mast": route.mast_name,
        "direction": route.direction,
        "alignments": _route_alignments(route),
        "clearTrackCircuits": list(route.clear_track_circuits),
        "staticIndication": indication_policy.static_indication(route, graph).value,
        "entrance": entrance,
        "approaching": approaching,
        "entryTerminal": _terminal_id_for_reference(
            terminal_ids,
            route.entry_terminal,
        ),
        "exitTerminal": _terminal_id_for_reference(
            terminal_ids,
            route.exit_terminal,
        ),
        "endKind": route.end_kind.value,
        "exitFace": (
            {
                "signal": route.exit_face_signal,
                "direction": route.exit_face_direction,
                "mast": route.exit_face_mast,
            }
            if route.end_kind is RouteEndKind.NEXT_FACE
            else None
        ),
    }

def _route_circuit(route: Any, role: CircuitRole) -> str | None:
    """Return one FieldUnit route circuit for a semantic circuit role."""

    circuits = [
        circuit
        for circuit, circuit_role in route.circuit_roles
        if circuit_role is role
    ]
    return circuits[0] if len(circuits) == 1 else None

def _route_alignments(route: Any) -> list[dict[str, str]]:
    """Return switch-like NORMAL/REVERSE proof requirements in name order."""

    alignments = [
        {
            "appliance": switch,
            "position": "NORMAL" if position == "N" else "REVERSE",
        }
        for switch, position in route.switch_alignments
    ]
    alignments.extend(
        {
            "appliance": derail,
            "position": "NORMAL",
        }
        for derail in route.derail_requirements
    )
    return sorted(alignments, key=lambda item: _natural_sort_key(item["appliance"]))

def _terminal_id_for_reference(
    terminal_ids: dict[str, str],
    reference: str,
) -> str | None:
    return terminal_ids.get(reference) if reference else None


def _face_id(signal: str, direction: str, mast: str) -> str:
    return f"face:{_slug(signal)}:{direction.lower()}:{_slug(mast)}"


def _slug(value: str) -> str:
    """Return a stable, readable identifier from a semantic display string."""

    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "unnamed"
