"""Traversable plant topology and combinatorial signal-route harvest."""

from __future__ import annotations

import itertools
import re
from collections import defaultdict
from typing import Iterable, Optional

from plant_graph.types import (
    Diagnostic,
    DiagnosticSeverity,
    EntityKind,
    NetClass,
    PlantGraph,
    PlantNet,
    PlantTerminal,
    RouteEndKind,
    SignalFace,
    SignalRoute,
)

_MAST_VALUE_RE = re.compile(r"^(\d+)([NS])([A-E]+)$")

# Switch pin numbers in the Railroad library.
_PIN_C = "1"
_PIN_N = "2"
_PIN_R = "3"

_SWITCH_KINDS = frozenset({EntityKind.SWITCH_POWERED, EntityKind.SWITCH_LOCK})
_IRJ_KINDS = frozenset({EntityKind.IRJ, EntityKind.IRJ_SIGNAL})
_MAST_KINDS = frozenset(
    {EntityKind.MAST_SINGLE, EntityKind.MAST_DOUBLE, EntityKind.MAST_DWARF}
)
_TRACK_NET_CLASSES = frozenset({NetClass.TRACK, NetClass.SWITCH_OS})


def harvest_routes(graph: PlantGraph) -> None:
    """Populate terminals, signal faces, and combinatoric routes on ``graph``."""
    topo = _TrackTopology(graph)
    graph.terminals = topo.terminals
    graph.signal_faces = topo.signal_faces
    graph.routes = topo.enumerate_routes()
    graph.diagnostics.extend(topo.diagnostics)


class _TrackTopology:
    """Build track adjacency and enumerate signal-governed routes."""

    def __init__(self, graph: PlantGraph) -> None:
        self.graph = graph
        self.diagnostics: list[Diagnostic] = []
        # port key "REF:PIN" -> net names touching it
        self.port_nets: dict[str, set[str]] = defaultdict(set)
        # undirected net hub edges among ports sharing a track/os net
        self.net_neighbors: dict[str, set[str]] = defaultdict(set)
        # IRJ joint crossings (A <-> B)
        self.joint_neighbors: dict[str, set[str]] = defaultdict(set)
        self.terminals: list[PlantTerminal] = []
        self.terminal_by_port: dict[str, PlantTerminal] = {}
        self.signal_faces: list[SignalFace] = []
        # approach port "REF:PIN" -> face (for next-face ends in direction of travel)
        self.face_by_approach_port: dict[str, SignalFace] = {}
        self._index_nets()
        self._index_irj_joints()
        self._index_terminals()
        self._index_signal_faces()

    def _port(self, ref: str, pin: str) -> str:
        return f"{ref}:{pin}"

    def _index_nets(self) -> None:
        for net in self.graph.nets:
            if net.net_class not in _TRACK_NET_CLASSES:
                continue
            ports: list[str] = []
            for ref, pin in net.nodes:
                ent = self.graph.entities.get(ref)
                if ent is None:
                    continue
                if ent.kind in _SWITCH_KINDS or ent.kind in _IRJ_KINDS:
                    ports.append(self._port(ref, pin))
                elif ent.kind is EntityKind.DIRECTION:
                    # Live DoT pin only (unconnected NC nets are not TRACK/OS).
                    ports.append(self._port(ref, pin))
                elif ent.kind is EntityKind.BUMPER:
                    ports.append(self._port(ref, pin))
            for p in ports:
                self.port_nets[p].add(net.name)
            for i, a in enumerate(ports):
                for b in ports[i + 1 :]:
                    self.net_neighbors[a].add(b)
                    self.net_neighbors[b].add(a)

    def _index_irj_joints(self) -> None:
        for ref, ent in self.graph.entities.items():
            if ent.kind not in _IRJ_KINDS:
                continue
            a = self._port(ref, "1")
            b = self._port(ref, "2")
            # Joint is crossable for train movement even though circuits differ.
            self.joint_neighbors[a].add(b)
            self.joint_neighbors[b].add(a)

    def _index_terminals(self) -> None:
        for ref, ent in self.graph.entities.items():
            if ent.kind is EntityKind.DIRECTION:
                live = self._live_direction_pins(ref)
                if len(live) == 0:
                    self.diagnostics.append(
                        Diagnostic(
                            severity=DiagnosticSeverity.SEMANTIC,
                            code="direction_fully_unconnected",
                            message=(
                                f"Direction terminal '{ref}' has no live track pin"
                            ),
                            entity_ref=ref,
                        )
                    )
                    continue
                if len(live) > 1:
                    self.diagnostics.append(
                        Diagnostic(
                            severity=DiagnosticSeverity.SEMANTIC,
                            code="direction_both_pins_live",
                            message=(
                                f"Direction terminal '{ref}' has both pins on track "
                                f"({sorted(live)}); terminal DoT must use one live pin"
                            ),
                            entity_ref=ref,
                        )
                    )
                    continue
                pin = next(iter(live))
                net_name = self._primary_net(self._port(ref, pin))
                term = PlantTerminal(
                    reference=ref,
                    kind=ent.kind,
                    port_pin=pin,
                    net_name=net_name,
                    designation=ent.canonical_name or ent.value,
                    rulebook=(ent.fields.get("Rulebook") or "").strip(),
                )
                self.terminals.append(term)
                self.terminal_by_port[self._port(ref, pin)] = term
            elif ent.kind is EntityKind.BUMPER:
                pin = "2"
                port = self._port(ref, pin)
                if port not in self.port_nets and port not in self.net_neighbors:
                    continue
                net_name = self._primary_net(port)
                term = PlantTerminal(
                    reference=ref,
                    kind=ent.kind,
                    port_pin=pin,
                    net_name=net_name,
                    designation=net_name if net_name else ref,
                    rulebook="",
                )
                self.terminals.append(term)
                self.terminal_by_port[port] = term

    def _live_direction_pins(self, ref: str) -> set[str]:
        live: set[str] = set()
        for net in self.graph.nets:
            if net.net_class not in _TRACK_NET_CLASSES:
                continue
            for r, pin in net.nodes:
                if r == ref:
                    live.add(pin)
        return live

    def _primary_net(self, port: str) -> str:
        names = self.port_nets.get(port) or set()
        labeled = sorted(n for n in names if not n.startswith("Net-"))
        if labeled:
            return labeled[0]
        return sorted(names)[0] if names else ""

    def _index_signal_faces(self) -> None:
        # IRJ-Signal -> mast via signal_attachment nets.
        irj_to_masts: dict[str, list[str]] = defaultdict(list)
        for net in self.graph.nets:
            if net.net_class is not NetClass.SIGNAL_ATTACHMENT:
                continue
            irj_ref = None
            mast_ref = None
            for ref, pin in net.nodes:
                ent = self.graph.entities.get(ref)
                if ent is None:
                    continue
                if ent.kind is EntityKind.IRJ_SIGNAL and pin == "3":
                    irj_ref = ref
                elif ent.kind in _MAST_KINDS and pin == "1":
                    mast_ref = ref
            if irj_ref and mast_ref:
                irj_to_masts[irj_ref].append(mast_ref)

        for irj_ref, mast_refs in sorted(irj_to_masts.items()):
            approach_pin, plant_pin = self._irj_face_pins(irj_ref)
            if approach_pin is None or plant_pin is None:
                self.diagnostics.append(
                    Diagnostic(
                        severity=DiagnosticSeverity.SEMANTIC,
                        code="signal_irj_face_ambiguous",
                        message=(
                            f"Signal IRJ '{irj_ref}' could not classify approach vs "
                            "plant track pins"
                        ),
                        entity_ref=irj_ref,
                    )
                )
                continue
            approach_port = self._port(irj_ref, approach_pin)
            approach_net = self._primary_net(approach_port)
            approach_terminal = self._terminal_from_approach(irj_ref, approach_pin)
            for mast_ref in mast_refs:
                mast = self.graph.entities[mast_ref]
                match = _MAST_VALUE_RE.match(mast.canonical_name or mast.value or "")
                if not match:
                    continue
                signal_name, direction, heads = match.groups()
                face = SignalFace(
                    signal_name=signal_name,
                    direction=direction,
                    mast_reference=mast_ref,
                    mast_name=mast.canonical_name,
                    irj_reference=irj_ref,
                    approach_pin=approach_pin,
                    plant_pin=plant_pin,
                    approach_net=approach_net,
                    approach_terminal=approach_terminal,
                    head_letters=heads,
                )
                self.signal_faces.append(face)
                self.face_by_approach_port[self._port(irj_ref, approach_pin)] = face

    def _irj_face_pins(self, irj_ref: str) -> tuple[Optional[str], Optional[str]]:
        """Return (approach_pin, plant_pin) for a Signal IRJ.

        Heuristic used on Luchessa-style drawings:
        - pin whose net neighbors a DoT/Bumper (possibly via the joint's track
          net only) without a switch is the approach side;
        - pin that neighbors a switch OS pin is the plant side.
        """
        pin_roles: dict[str, set[str]] = {"1": set(), "2": set()}
        for pin in ("1", "2"):
            port = self._port(irj_ref, pin)
            for nb in self.net_neighbors.get(port, set()):
                ref = nb.split(":", 1)[0]
                ent = self.graph.entities.get(ref)
                if ent is None:
                    continue
                if ent.kind in _SWITCH_KINDS:
                    pin_roles[pin].add("switch")
                elif ent.kind is EntityKind.DIRECTION:
                    pin_roles[pin].add("terminal")
                elif ent.kind is EntityKind.BUMPER:
                    pin_roles[pin].add("terminal")
                elif ent.kind in _IRJ_KINDS:
                    pin_roles[pin].add("irj")
            # Also: follow only TRACK (labeled) net to a terminal one hop away.
            for net_name in self.port_nets.get(port, set()):
                net = self._net_by_name(net_name)
                if net is None or net.net_class is not NetClass.TRACK:
                    continue
                for ref, _p in net.nodes:
                    ent = self.graph.entities.get(ref)
                    if ent and ent.kind in (EntityKind.DIRECTION, EntityKind.BUMPER):
                        pin_roles[pin].add("terminal")

        approach = None
        plant = None
        for pin, roles in pin_roles.items():
            if "terminal" in roles and "switch" not in roles:
                approach = pin
            if "switch" in roles:
                plant = pin
        # Fallback common drawing convention: B/2 approach, A/1 plant.
        if approach is None and plant is not None:
            approach = "2" if plant == "1" else "1"
        if plant is None and approach is not None:
            plant = "1" if approach == "2" else "2"
        if approach is None and plant is None:
            # Last resort: prefer pin with labeled track net as approach.
            for pin in ("2", "1"):
                port = self._port(irj_ref, pin)
                nets = self.port_nets.get(port, set())
                if any(not n.startswith("Net-") for n in nets):
                    approach = pin
                    plant = "1" if pin == "2" else "2"
                    break
        return approach, plant

    def _net_by_name(self, name: str) -> Optional[PlantNet]:
        for net in self.graph.nets:
            if net.name == name or net.raw_name == name:
                return net
        return None

    def _terminal_from_approach(self, irj_ref: str, approach_pin: str) -> str:
        port = self._port(irj_ref, approach_pin)
        for nb in self.net_neighbors.get(port, set()):
            if nb in self.terminal_by_port:
                return self.terminal_by_port[nb].reference
        # Same net membership search.
        for net_name in self.port_nets.get(port, set()):
            net = self._net_by_name(net_name)
            if not net:
                continue
            for ref, pin in net.nodes:
                key = self._port(ref, pin)
                if key in self.terminal_by_port:
                    return self.terminal_by_port[key].reference
        return ""

    def enumerate_routes(self) -> list[SignalRoute]:
        switch_ref = {
            ent.canonical_name: ent.reference
            for ent in self.graph.entities.values()
            if ent.kind in _SWITCH_KINDS and ent.canonical_name
        }
        routes: list[SignalRoute] = []
        seen: set[tuple] = set()

        for face in self.signal_faces:
            start = self._port(face.irj_reference, face.plant_pin)
            approach_port = self._port(face.irj_reference, face.approach_pin)
            if face.approach_terminal:
                entry_term_obj = next(
                    (t for t in self.terminals if t.reference == face.approach_terminal),
                    None,
                )
            else:
                entry_term_obj = None
            entry_designation = (
                entry_term_obj.designation if entry_term_obj else face.approach_net
            )
            entry_rulebook = entry_term_obj.rulebook if entry_term_obj else ""
            entry_terminal_ref = (
                entry_term_obj.reference if entry_term_obj else face.approach_terminal
            )
            entry_net = face.approach_net
            forbidden = {approach_port}
            if entry_term_obj is not None:
                forbidden.add(
                    self._port(entry_term_obj.reference, entry_term_obj.port_pin)
                )

            for end_port, path_nets, alignments in self._walk(
                start=start,
                switch_ref=switch_ref,
                forbidden_ports=forbidden,
                entry_irj=face.irj_reference,
                travel_direction=face.direction,
                start_mast=face.mast_reference,
            ):
                end_info = self._classify_end(end_port, face)
                if end_info is None:
                    continue
                (
                    end_kind,
                    exit_desig,
                    exit_net,
                    exit_term_ref,
                    exit_rulebook,
                    exit_face_mast,
                    exit_face_signal,
                    exit_face_dir,
                ) = end_info
                if exit_desig == entry_designation and end_kind is not RouteEndKind.NEXT_FACE:
                    continue
                switch_tuple = tuple(sorted(alignments.items()))
                key = (
                    face.mast_reference,
                    entry_terminal_ref,
                    end_kind.value,
                    exit_desig,
                    exit_face_mast,
                    switch_tuple,
                )
                if key in seen:
                    continue
                seen.add(key)
                name = f"{entry_designation}-{exit_desig}"
                os_tcs = tuple(f"{sw}T1" for sw, _pos in switch_tuple)
                path_tcs = _labeled_path_track_circuits(
                    path_nets,
                    entry_net=entry_net,
                    exit_net=exit_net,
                )
                clears = tuple(dict.fromkeys([*os_tcs, *path_tcs]))
                routes.append(
                    SignalRoute(
                        name=name,
                        signal_name=face.signal_name,
                        direction=face.direction,
                        mast_reference=face.mast_reference,
                        mast_name=face.mast_name,
                        head_letters=face.head_letters,
                        entry_terminal=entry_terminal_ref,
                        entry_net=entry_net,
                        entry_designation=entry_designation,
                        entry_rulebook=entry_rulebook,
                        exit_terminal=exit_term_ref,
                        exit_net=exit_net,
                        exit_designation=exit_desig,
                        exit_rulebook=exit_rulebook,
                        end_kind=end_kind,
                        exit_face_mast=exit_face_mast,
                        exit_face_signal=exit_face_signal,
                        exit_face_direction=exit_face_dir,
                        switch_alignments=switch_tuple,
                        clear_track_circuits=clears,
                        os_track_circuits=os_tcs,
                        path_track_circuits=path_tcs,
                        path_nets=tuple(path_nets),
                    )
                )

        routes.sort(
            key=lambda r: (
                r.signal_name,
                r.direction,
                r.mast_reference,
                r.entry_designation,
                r.exit_designation,
                r.switch_alignments,
            )
        )
        return routes

    def _walk(
        self,
        start: str,
        switch_ref: dict[str, str],
        forbidden_ports: set[str],
        entry_irj: str,
        travel_direction: str,
        start_mast: str,
    ) -> Iterable[tuple[str, list[str], dict[str, str]]]:
        """DFS yielding (end_port, path_nets, used_alignments).

        Ends at: DoT/bumper terminals, or another face's approach pin that
        protects the same direction of travel (next-face end). Opposite-facing
        faces are not ends (e.g. industry dwarf does not end inbound moves).
        """
        ref_to_switch_name = {v: k for k, v in switch_ref.items()}
        stack: list[tuple[str, list[str], list[str], dict[str, str]]] = [
            (start, [start], [], {})
        ]
        results: list[tuple[str, list[str], dict[str, str]]] = []

        while stack:
            port, path, nets, aligns = stack.pop()
            if port != start and self._is_route_end(
                port, travel_direction, start_mast, forbidden_ports
            ):
                results.append((port, nets, dict(aligns)))
                continue

            for nxt, via_net, align_add in self._neighbors_branching(
                port, aligns, ref_to_switch_name, entry_irj
            ):
                if nxt in path or nxt in forbidden_ports:
                    continue
                new_aligns = dict(aligns)
                new_aligns.update(align_add)
                new_nets = list(nets)
                if via_net and (not new_nets or new_nets[-1] != via_net):
                    new_nets.append(via_net)
                stack.append((nxt, path + [nxt], new_nets, new_aligns))

        return results

    def _is_route_end(
        self,
        port: str,
        travel_direction: str,
        start_mast: str,
        forbidden_ports: set[str],
    ) -> bool:
        if port in forbidden_ports:
            return False
        face = self.face_by_approach_port.get(port)
        if face is not None:
            if face.mast_reference == start_mast:
                return False
            # Same direction of travel => next protecting face in this move.
            return face.direction == travel_direction
        return port in self.terminal_by_port

    def _classify_end(
        self,
        end_port: str,
        start_face: SignalFace,
    ) -> tuple[RouteEndKind, str, str, str, str, str, str, str] | None:
        """Return end metadata or None if not a valid end."""
        face = self.face_by_approach_port.get(end_port)
        if face is not None and face.direction == start_face.direction:
            if face.mast_reference == start_face.mast_reference:
                return None
            desig = face.mast_name
            if face.approach_terminal:
                term = next(
                    (t for t in self.terminals if t.reference == face.approach_terminal),
                    None,
                )
                if term is not None:
                    desig = term.designation
            return (
                RouteEndKind.NEXT_FACE,
                desig,
                face.approach_net,
                face.approach_terminal,
                "",
                face.mast_name,
                face.signal_name,
                face.direction,
            )
        term = self.terminal_by_port.get(end_port)
        if term is None:
            return None
        if term.kind is EntityKind.BUMPER:
            kind = RouteEndKind.DEAD_END
        else:
            kind = RouteEndKind.CP_LIMIT
        return (
            kind,
            term.designation,
            term.net_name,
            term.reference,
            term.rulebook,
            "",
            "",
            "",
        )


    def _walk_fixed(
        self,
        start: str,
        alignments: dict[str, str],
        switch_ref: dict[str, str],
        forbidden_ports: set[str],
        entry_irj: str,
    ) -> Iterable[tuple[str, list[str], dict[str, str]]]:
        """Walk with every switch locked to ``alignments`` (no branching)."""
        ref_to_switch_name = {v: k for k, v in switch_ref.items()}
        stack: list[tuple[str, list[str], list[str]]] = [(start, [start], [])]
        results: list[tuple[str, list[str], dict[str, str]]] = []
        while stack:
            port, path, nets = stack.pop()
            if port in self.terminal_by_port and port not in forbidden_ports:
                results.append((port, nets, dict(alignments)))
                continue
            for nxt, via_net, _delta in self._neighbors_fixed(
                port, alignments, ref_to_switch_name, entry_irj
            ):
                if nxt in path or nxt in forbidden_ports:
                    continue
                new_nets = list(nets)
                if via_net and (not new_nets or new_nets[-1] != via_net):
                    new_nets.append(via_net)
                stack.append((nxt, path + [nxt], new_nets))
        return results

    def _neighbors_fixed(
        self,
        port: str,
        aligns: dict[str, str],
        ref_to_switch_name: dict[str, str],
        entry_irj: str,
    ) -> list[tuple[str, str, dict[str, str]]]:
        """Neighbors under a fully specified switch plant."""
        out: list[tuple[str, str, dict[str, str]]] = []
        ref, pin = port.split(":", 1)
        ent = self.graph.entities.get(ref)
        for nb in self.net_neighbors.get(port, set()):
            out.append((nb, self._shared_net(port, nb), {}))
        for nb in self.joint_neighbors.get(port, set()):
            if ref == entry_irj:
                continue
            out.append((nb, f"joint:{ref}", {}))
        if ent and ent.kind in _SWITCH_KINDS:
            sw_name = ent.canonical_name
            pos = aligns.get(sw_name, "N")
            c = self._port(ref, _PIN_C)
            n = self._port(ref, _PIN_N)
            r = self._port(ref, _PIN_R)
            if pin == _PIN_C:
                dest = n if pos == "N" else r
                out.append((dest, f"switch:{sw_name}:{pos}", {}))
            elif pin == _PIN_N and pos == "N":
                out.append((c, f"switch:{sw_name}:N", {}))
            elif pin == _PIN_R and pos == "R":
                out.append((c, f"switch:{sw_name}:R", {}))
        seen: set[str] = set()
        uniq: list[tuple[str, str, dict[str, str]]] = []
        for item in out:
            if item[0] not in seen:
                seen.add(item[0])
                uniq.append(item)
        return uniq

    def _neighbors_branching(
        self,
        port: str,
        aligns: dict[str, str],
        ref_to_switch_name: dict[str, str],
        entry_irj: str,
    ) -> list[tuple[str, str, dict[str, str]]]:
        """Return (next_port, via_net, alignment_delta) with switch branching."""
        out: list[tuple[str, str, dict[str, str]]] = []
        ref, pin = port.split(":", 1)
        ent = self.graph.entities.get(ref)

        for nb in self.net_neighbors.get(port, set()):
            via = self._shared_net(port, nb)
            out.append((nb, via, {}))

        for nb in self.joint_neighbors.get(port, set()):
            # Do not recross the entry signal IRJ back toward its approach.
            if ref == entry_irj:
                continue
            out.append((nb, f"joint:{ref}", {}))

        if ent and ent.kind in _SWITCH_KINDS:
            sw_name = ent.canonical_name
            c = self._port(ref, _PIN_C)
            n = self._port(ref, _PIN_N)
            r = self._port(ref, _PIN_R)
            if pin == _PIN_C:
                if sw_name in aligns:
                    pos = aligns[sw_name]
                    dest = n if pos == "N" else r
                    out.append((dest, f"switch:{sw_name}:{pos}", {}))
                else:
                    out.append((n, f"switch:{sw_name}:N", {sw_name: "N"}))
                    out.append((r, f"switch:{sw_name}:R", {sw_name: "R"}))
            elif pin == _PIN_N:
                if aligns.get(sw_name, "N") == "N":
                    delta = {} if sw_name in aligns else {sw_name: "N"}
                    out.append((c, f"switch:{sw_name}:N", delta))
            elif pin == _PIN_R:
                if aligns.get(sw_name, "R") == "R":
                    delta = {} if sw_name in aligns else {sw_name: "R"}
                    out.append((c, f"switch:{sw_name}:R", delta))

        seen: set[str] = set()
        uniq: list[tuple[str, str, dict[str, str]]] = []
        for item in out:
            if item[0] not in seen:
                seen.add(item[0])
                uniq.append(item)
        return uniq

    def _shared_net(self, a: str, b: str) -> str:
        sa = self.port_nets.get(a, set())
        sb = self.port_nets.get(b, set())
        common = sa & sb
        if not common:
            return ""
        labeled = sorted(n for n in common if not n.startswith("Net-"))
        return labeled[0] if labeled else sorted(common)[0]



def _labeled_path_track_circuits(
    path_nets: list[str],
    entry_net: str = "",
    exit_net: str = "",
) -> tuple[str, ...]:
    """Labeled track nets traversed on the route (schematic TC / net names).

    Skips synthetic walker tags (joint:/switch:/Net-*). Entry and exit nets are
    included when labeled. MP-style renames (780SA, …) are a schematic concern.
    """
    ordered: list[str] = []
    seen: set[str] = set()

    def add(name: str) -> None:
        name = (name or "").strip()
        if not name:
            return
        if name.startswith("joint:") or name.startswith("switch:"):
            return
        if name.startswith("Net-") or name.startswith("unconnected-"):
            return
        if name.startswith("/"):
            name = name[1:]
        if not name or name in seen:
            return
        seen.add(name)
        ordered.append(name)

    add(entry_net)
    for net in path_nets:
        add(net)
    add(exit_net)
    return tuple(ordered)

def format_alignment(switch_alignments: tuple[tuple[str, str], ...]) -> str:
    """Prototype alignment string: bare=Normal, (name)=Reverse, joined."""
    parts: list[str] = []
    for name, pos in switch_alignments:
        if pos == "R":
            parts.append(f"({name})")
        else:
            parts.append(str(name))
    return "".join(parts) if parts else "-"


def lever_direction(mast_direction: str) -> str:
    """Map mast geographic face to cTc lever side (Luchessa/US&S desk habit)."""
    if mast_direction == "S":
        return "RIGHT"
    if mast_direction == "N":
        return "LEFT"
    return mast_direction


def format_route_line(route: SignalRoute, indication: str = "") -> str:
    """Scannable prototype route line.

    route  mast  alignment  signal(lever)  end  clears...  [indication]
    """
    align = format_alignment(route.switch_alignments)
    lever = lever_direction(route.direction)
    sig = f"{route.signal_name}{route.direction}({lever})"
    clears = " ".join(route.clear_track_circuits) if route.clear_track_circuits else "-"
    ind = indication if indication else "—"
    end = route.end_kind.value
    if route.end_kind is RouteEndKind.NEXT_FACE and route.exit_face_mast:
        end = f"next:{route.exit_face_mast}"
    return (
        f"{route.name:28} {route.mast_name:8} {align:16} "
        f"{sig:14} {end:16} {clears:24} {ind}"
    )


def build_route_proof(graph: PlantGraph) -> dict:
    """Full combinatoric proof of valid vs impossible face/exit pairs.

    For each signal face and every full switch N/R assignment, walk with that
    plant locked and record reachable exit terminals. Compare to the
    harvested valid route set.
    """
    topo = _TrackTopology(graph)
    # Rebuild indexes only — faces/terminals already on graph; use graph lists.
    topo.terminals = list(graph.terminals)
    topo.terminal_by_port = {
        topo._port(t.reference, t.port_pin): t for t in graph.terminals
    }
    topo.signal_faces = list(graph.signal_faces)

    switches = sorted(
        {
            ent.canonical_name
            for ent in graph.entities.values()
            if ent.kind in _SWITCH_KINDS and ent.canonical_name
        }
    )
    switch_ref = {
        ent.canonical_name: ent.reference
        for ent in graph.entities.values()
        if ent.kind in _SWITCH_KINDS and ent.canonical_name
    }
    all_exits = sorted({t.designation for t in graph.terminals})

    # valid pairs from harvested routes
    valid_pairs: set[tuple[str, str, str]] = set()
    # (mast, entry_desig, exit_desig)
    for r in graph.routes:
        valid_pairs.add((r.mast_name, r.entry_designation, r.exit_designation))

    face_rows: list[dict] = []
    reachable_pairs: set[tuple[str, str, str]] = set()

    if switches:
        combos = list(itertools.product(("N", "R"), repeat=len(switches)))
    else:
        combos = [()]

    for face in graph.signal_faces:
        start = topo._port(face.irj_reference, face.plant_pin)
        approach_port = topo._port(face.irj_reference, face.approach_pin)
        entry_term = next(
            (t for t in graph.terminals if t.reference == face.approach_terminal),
            None,
        )
        entry_desig = entry_term.designation if entry_term else face.approach_net
        forbidden = {approach_port}
        if entry_term is not None:
            forbidden.add(topo._port(entry_term.reference, entry_term.port_pin))

        exits_by_combo: list[dict] = []
        ever_exits: set[str] = set()
        for combo in combos:
            aligns = dict(zip(switches, combo)) if switches else {}
            reached: set[str] = set()
            for end_port, _nets, _al in topo._walk_fixed(
                start=start,
                alignments=aligns,
                switch_ref=switch_ref,
                forbidden_ports=forbidden,
                entry_irj=face.irj_reference,
            ):
                term = topo.terminal_by_port.get(end_port)
                if term is None:
                    continue
                if term.designation == entry_desig:
                    continue
                reached.add(term.designation)
                ever_exits.add(term.designation)
                reachable_pairs.add((face.mast_name, entry_desig, term.designation))
            exits_by_combo.append(
                {
                    "alignments": format_alignment(tuple(sorted(aligns.items()))),
                    "exits": sorted(reached),
                }
            )

        impossible_exits = sorted(set(all_exits) - ever_exits - {entry_desig})
        face_rows.append(
            {
                "mast": face.mast_name,
                "signal": f"{face.signal_name}{face.direction}",
                "entry": entry_desig,
                "combo_count": len(combos),
                "reachable_exits": sorted(ever_exits),
                "impossible_exits": impossible_exits,
                "combos": exits_by_combo,
            }
        )

    impossible_pairs = sorted(
        {
            (m, e, x)
            for _face in graph.signal_faces
            for m, e in {
                (
                    f.mast_name,
                    next(
                        (
                            t.designation
                            for t in graph.terminals
                            if t.reference == f.approach_terminal
                        ),
                        f.approach_net,
                    ),
                )
                for f in graph.signal_faces
            }
            for x in all_exits
            if x != e and (m, e, x) not in reachable_pairs
        }
    )
    # simpler impossible pair list from face_rows
    impossible_pairs = []
    for row in face_rows:
        for x in row["impossible_exits"]:
            impossible_pairs.append((row["mast"], row["entry"], x))

    return {
        "switches": switches,
        "combo_count": len(combos),
        "valid_route_count": len(graph.routes),
        "valid_pairs": sorted(valid_pairs),
        "reachable_pairs": sorted(reachable_pairs),
        "impossible_pairs": impossible_pairs,
        "faces": face_rows,
    }
