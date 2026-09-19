"""Compile a railroad PlantGraph from KiCad library + netlist models."""

from __future__ import annotations

import re
from typing import Optional

from kicad_services.types import LibraryModel, Net, NetlistComponent, NetlistModel
from plant_graph.types import (
    DerivedTrackCircuit,
    Diagnostic,
    DiagnosticSeverity,
    EntityKind,
    NetClass,
    PlantEntity,
    PlantGraph,
    PlantNet,
)

# Railroad part name → entity kind.
_PART_KIND: dict[str, EntityKind] = {
    "Switch_Powered": EntityKind.SWITCH_POWERED,
    "Switch_Lock": EntityKind.SWITCH_LOCK,
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
        self._build_entities(graph, library, netlist)
        self._classify_nets(graph, netlist)
        self._check_required_pins(graph, netlist)
        self._derive_os_circuits(graph)
        self._check_track_net_labels(graph)
        self._check_cp_allocations(graph)
        self._check_switch_indications(graph)
        self._check_library_coverage(graph, library)
        # Topology + combinatoric signal routes (DoT terminals, switch N/R).
        from plant_graph.routes import harvest_routes

        harvest_routes(graph)
        from plant_graph.indications import RouteSignalingPolicy

        graph.routes = RouteSignalingPolicy().compile_static_indications(graph)
        return graph

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
            if entity.kind not in (
                EntityKind.SWITCH_POWERED,
                EntityKind.SWITCH_LOCK,
            ):
                continue
            if not entity.canonical_name:
                continue
            name = f"{entity.canonical_name}T1"
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
