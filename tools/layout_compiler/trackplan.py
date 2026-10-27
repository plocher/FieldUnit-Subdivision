"""The trackplan: what each interlocking's appliances are, which circuits its track carries, and which control point
each appliance belongs to (ADR 0010 §4.1 and C6; the trackplan piece of the semantics handoff, item 2).

What is on the trackplan is decided by Role, never by library, symbol name or position: ``APPLIANCE``, ``TRACK`` and
``POLICY``, with the house (``STRUCTURE``, Kind ``CONTROL_POINT``) beside them. The geometry piece reads the same
symbols with the same test (``TRACKPLAN_ROLES``) and names a circuit through the same ``circuit_of_net``, so the two
pieces of schema 3.1.0 meet at one circuit name.

A **circuit** is the track a set of nets carries between joints: nets joined through a switch's ports (C to N, C to
R) and a derail's (C to R), split at every joint and end. Its name is the track circuit marker drawn on one of its
nets, or else the ``TC`` field of a switch in it, the OS circuit (the library's default is ``${Value}T1``, ADR 0003
D3); two different names on one circuit are an error. A circuit with neither is dark track and has no name.

**Control point** is the house whose field unit has the I/O for an appliance, vital or not; it is not the routes the
signals protect (the owner, 2026-10-26). The houses are the roots: an interlocking with one house gives it to every
appliance; with two or more, the stated ``CP`` fields are the roots and the rest inherit along their relations
(``_control_points``). Protection and authority limits (signal joints, END CTC, Rule 93) are the views' to derive from
the rows written here. A signal joint's sides are named for what they do (ADR 0012 §8): ``governed``, where the route
it protects begins (the symbol's ``A`` pin), and ``approach`` (its ``B`` pin); a policy sign's and a NextCP's one pin
is ``track`` whatever the library calls it. The KiCad importer translates the pin names here (``side_of``, three-maps
D15); no library pin is renamed. The circuit a Rule 93 sign stands on is inside the yard limits.

Every entity and row holds ``given`` (its fields as drawn), ``relations`` (its wires, by name) and ``derived`` (what
the rules compute) (ADR 0011 §2). A track pin's wire is ``relations.<side>``: every other track pin its net reaches
(three-maps D5; the owner, 2026-10-27): a switch port, a track circuit marker's TC or a named row's side by qualified
name, an unnamed row's side by the row's ``id`` (``pin_ref``, the one form a run's ends use too). A track pin is a
switch's port, a marker's TC and every pin of a joint, an end or a policy sign but a signal joint's SIGNAL
(``is_track_pin``); a pin never names its own symbol, so the relation is symmetric and the track can be walked
through ``relations`` alone. A row is identified by ``id``, its symbol's KiCad UUID (D10), and an end of track may
also carry a name (an industry).

A name qualified with another interlocking's scope (Sargent's marker ``Corporal:2NAT``) is a one-sided reference: it is
no row here and nothing is written back to the thing it names (the owner, 2026-10-27). Once every interlocking is read,
``_resolve_references`` checks that the thing exists, of the kind the drawing uses it as, with every port wired to it.

Nothing here reads a coordinate, a net name, a reference or ``Value``; every name is read through ``key_of``.
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Optional

from .seams import Seams, check_milepost, given_of, key_of, loc, qualify
from .source import Net, Symbol

TRACKPLAN_ROLES = frozenset({"APPLIANCE", "TRACK", "POLICY"})
# A switch's track ports, the one vocabulary of both pieces (geometry's ``to: "Luchessa:783.R"``, ADR 0010 §4.6).
SWITCH_PORTS = ("C", "N", "R")
DERAIL_PORTS = ("C", "R")
JOINTS = frozenset({"IRJ", "IRJ_SIGNAL"})
ENDS = frozenset({"END_CTC", "NEXT_CP", "BUMPER", "INDUSTRY"})
# ADR 0003: a mast is its signal (lever and side) plus its heads' letters, ascending (rules 6 and 7).
MAST_NAME = re.compile(r"^(0?[1-9]\d{0,3}[LRNSEW])([A-Z]+)$")
# ADR 0003 D8: a gang id is a switch name less its trailing letter; the switch named by the id alone leads the gang.
GANG = re.compile(r"(?<=\d)[A-Z]$")


def on_trackplan(s: Symbol) -> bool:
    return s.role in TRACKPLAN_ROLES


def is_switch(s: Symbol) -> bool:
    return s.role == "APPLIANCE" and s.get("Appliance") == "switch"


def ports_of(s: Symbol) -> tuple[str, ...]:
    """The track ports of a switch, a derail's two (Style ``derail``); none for anything else."""
    if not is_switch(s):
        return ()
    return DERAIL_PORTS if s.get("Style") == "derail" else SWITCH_PORTS


# A track symbol's pin, translated to the side it is (ADR 0012 §8; three-maps D15). Any other pin keeps its name.
SIDES = {"IRJ_SIGNAL": {"A": "governed", "B": "approach"}, "NEXT_CP": {"To": "track"}}
POLICY_SIDES = {"To": "track", "Track": "track"}


def side_of(s: Symbol, pin: str) -> str:
    """The functional name of a track symbol's pin: what the model calls the side, never the library's pin name."""
    if s.role == "POLICY":
        return POLICY_SIDES.get(pin, pin)
    return SIDES.get(s.kind, {}).get(pin, pin)


def port_ref(interlocking: str, name: str, port: str) -> str:
    """A switch port or a named track symbol's pin, by qualified name: ``Luchessa:783.R``, ``Luchessa:Gilroy Industry.EoT``."""
    return f"{qualify(name, interlocking)}.{port}"


def is_track_pin(s: Symbol, pin: str) -> bool:
    """A pin that carries track: a switch's (or derail's) port, a track circuit marker's TC, and every pin of a joint,
    an end or a policy sign but a signal joint's SIGNAL, which carries its mast. A milepost is no row and carries none."""
    if s.role in ("TRACK", "POLICY"):
        return s.kind != "MILEPOST" and pin != "SIGNAL"
    if is_switch(s):
        return pin in ports_of(s)
    return s.role == "APPLIANCE" and s.get("Appliance") == "track_circuit" and pin == "TC"


def pin_ref(interlocking: str, s: Symbol, pin: str) -> Optional[str]:
    """How the model names a track pin, the one form of a side's relations and a run's ends (three-maps D5, D10, D15): a
    switch port, a marker's TC or a named track row's side by qualified name (``Luchessa:783.R``), an unnamed row's side
    by the row's id (``<uuid>.approach``). None for a pin that is not track and for a thing with neither."""
    if not is_track_pin(s, pin):
        return None
    name = key_of(s) if s.role != "POLICY" else ""
    if name:
        return port_ref(interlocking, name, side_of(s, pin))
    if s.role in ("TRACK", "POLICY"):
        return f"{s.uuid}.{side_of(s, pin)}" if s.uuid else None
    return None


@dataclass(frozen=True)
class Reference:
    """A qualified name in one interlocking's drawing for a thing of another (the owner, 2026-10-27: one-sided; the
    thing it names must exist). ``kind`` is the Appliance it must be (``switch``, ``track_circuit``, ...), ``circuit``
    for any named circuit, or ``track`` for a named track row; ``ports`` are the pins or sides the drawing wires to."""

    kind: str
    name: str                                                             # qualified: ``Corporal:2NAT``
    ports: tuple[str, ...] = ()
    what: str = ""                                                        # how the referring drawing states it
    where: str = ""


@dataclass
class Plan:
    """One interlocking's trackplan, resolved."""

    name: str
    circuit_of: dict[str, Optional[str]] = field(default_factory=dict)        # net name -> qualified circuit
    appliances: dict[str, dict[str, Any]] = field(default_factory=dict)
    track: dict[str, Any] = field(default_factory=dict)
    references: list[Reference] = field(default_factory=list)             # to other interlockings' things, checked once all are read
    sides: dict[str, frozenset[str]] = field(default_factory=dict)        # a named thing -> the ports or sides it has


@dataclass
class Trackplan:
    plans: dict[str, Plan] = field(default_factory=dict)

    def circuit_of_net(self, interlocking: str, net: Optional[Net]) -> Optional[str]:
        """The circuit a track net carries, qualified, or None for dark track and for a net that is not track."""
        if net is None or interlocking not in self.plans:
            return None
        return self.plans[interlocking].circuit_of.get(net.name)


class _Union:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def find(self, x: str) -> str:
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def join(self, a: str, b: str) -> None:
        self.parent[self.find(a)] = self.find(b)


def read(sm: Seams) -> Trackplan:
    out = Trackplan()
    for ix in sm.interlockings.values():
        syms = [s for s in sm.source.under(ix.sym.sheet, "APPLIANCE") + sm.source.under(ix.sym.sheet, "TRACK")
                + sm.source.under(ix.sym.sheet, "POLICY") if unit_of(sm, s) == ix.name]
        if syms:
            out.plans[ix.name] = _plan(sm, ix, syms)
    _pair_next_cps(sm, out)
    _resolve_references(sm, out)
    return out


def _resolve_references(sm: Seams, out: Trackplan) -> None:
    """Every qualified name for another interlocking's thing names one that exists, of the kind the drawing uses it as,
    with every port or side the drawing wires to (the owner, 2026-10-27). The reference is one-sided: nothing is
    written back to the thing it names. An interlocking not in the file is a warning; a thing or port missing from one
    that is, an error."""
    for a, plan in out.plans.items():
        for r in plan.references:
            b, _, n = r.name.partition(":")
            if b not in sm.interlockings:
                sm.report.warning("reference.interlocking", f"{a}: {r.what} {r.name} names {b}, which is no interlocking in this file", r.where)
                continue
            target = out.plans.get(b) or Plan(b)
            circuits = {c for c in target.circuit_of.values() if c} | {
                f"{b}:{k}" for k, v in target.appliances.items() if v.get("given", {}).get("Appliance") == "track_circuit"}
            row = target.appliances.get(n)
            if r.kind == "circuit":
                found, ports = r.name in circuits, None
            elif r.kind == "track":
                found, ports = n in target.sides and row is None, target.sides.get(n)
            elif r.kind == "track_circuit" and row is None:
                found, ports = r.name in circuits, None                   # a circuit named by a switch's TC, with no marker
            else:
                found, ports = row is not None and row.get("given", {}).get("Appliance") == r.kind, target.sides.get(n, frozenset())
            if not found:
                thing = "circuit" if r.kind in ("circuit", "track_circuit") else "track symbol" if r.kind == "track" else r.kind
                sm.report.error("reference.unresolved", f"{a}: {r.what} {r.name} names {b}, which has no {thing} {n}", r.where)
                continue
            lost = sorted(set(r.ports) - ports) if ports is not None else []
            if lost:
                sm.report.error("reference.unresolved", f"{a}: {r.what} {r.name} is wired at {', '.join(lost)}, but {b}'s {n} has no "
                                f"{'port' if r.kind == 'switch' else 'side'} {', '.join(lost)}", r.where)


def _pair_next_cps(sm: Seams, out: Trackplan) -> None:
    """A NextCP names the interlocking its track leads to; that interlocking's NextCPs lead back as many times. One
    beyond the layout (Lick, Hollister) is reported at info."""
    count: dict[tuple[str, str], int] = defaultdict(int)
    for a, plan in out.plans.items():
        for row in plan.track.get("ends", []):
            given = row.get("given", {})
            if given.get("Kind") == "NEXT_CP" and given.get("Interlocking"):
                count[(a, given["Interlocking"])] += 1
    for (a, b), n in sorted(count.items()):
        if b not in out.plans:
            sm.report.info("next_cp.off_layout", f"{a}: {n} NextCP{'s lead' if n > 1 else ' leads'} to {b}, which is not on this layout")
        elif count.get((b, a), 0) != n:
            sm.report.error("next_cp.pair", f"{a} has {n} NextCP{'s' * (n > 1)} to {b}, but {b} has {count.get((b, a), 0)} back to {a}")


def unit_of(sm: Seams, s: Symbol) -> Optional[str]:
    """The interlocking whose sheet is the nearest at or above the symbol's (ADR 0004 D12)."""
    hits = [ix for ix in sm.interlockings.values() if s.sheet.startswith(ix.sym.sheet)]
    return max(hits, key=lambda ix: len(ix.sym.sheet)).name if hits else None


def _plan(sm: Seams, ix, syms: list[Symbol]) -> Plan:
    src, report = sm.source, sm.report
    plan = Plan(ix.name)
    refs = {s.ref for s in syms}

    def net(s: Symbol, pin: str) -> Optional[Net]:
        return src.net_of(s.ref, pin)

    def others(s: Symbol, pin: str) -> list[tuple[Symbol, str]]:
        n = net(s, pin)
        return [(src.symbols[p.ref], p.pin) for p in n.others(s.ref) if p.ref in refs] if n else []

    # ------------------------------------------------------------------ circuits
    union = _Union()
    track_nets: set[str] = set()
    for s in syms:
        if s.role != "TRACK" and not is_switch(s) and s.get("Appliance") != "track_circuit":
            continue
        for pin, n in src.pins_of(s.ref).items():
            if s.role == "TRACK" or pin in ports_of(s) or pin == "TC":
                track_nets.add(n.name)
                union.find(n.name)
        ports = [net(s, p) for p in ports_of(s)]
        ports = [p for p in ports if p is not None]
        for p in ports[1:]:
            union.join(ports[0].name, p.name)

    named: dict[str, dict[str, list[str]]] = defaultdict(lambda: {"marker": [], "os": []})
    for s in syms:
        if s.role == "APPLIANCE" and s.get("Appliance") == "track_circuit" and net(s, "TC"):
            named[union.find(net(s, "TC").name)]["marker"].append(qualify(key_of(s), ix.name))
        elif is_switch(s) and s.get("TC"):
            n = next((net(s, p) for p in ports_of(s) if net(s, p)), None)
            if n is None:
                continue
            if "," in s.get("TC"):
                report.error("switch.tc_block", f"{ix.name}: switch {key_of(s)} lists several circuits in TC ({s.get('TC')}); "
                             "a detection block has no form in schema 3.1.0", loc(s))
                continue
            named[union.find(n.name)]["os"].append(qualify(s.get("TC"), ix.name))
            if _foreign(s.get("TC"), ix.name):
                plan.references.append(Reference("circuit", s.get("TC"), (), f"switch {key_of(s)}'s TC", loc(s)))
    circuit_of_region: dict[str, Optional[str]] = {}
    for region, names in named.items():
        markers, os_ = sorted(set(names["marker"])), sorted(set(names["os"]))
        if len(markers) > 1 or len(os_) > 1:
            report.error("circuit.names", f"{ix.name}: one circuit carries the names {', '.join(markers + os_)}; a joint is missing "
                         "or a TC is wrong", f"sheet {ix.sym.sheet}")
            continue
        marker, os_name = (markers or [None])[0], (os_ or [None])[0]
        if marker and os_name and marker != os_name:
            report.error("circuit.name.disagree", f"{ix.name}: the circuit {marker}: its marker says {marker!r}, a switch's TC "
                         f"says {os_name!r}", f"sheet {ix.sym.sheet}")
            continue
        circuit_of_region[region] = marker or os_name
    plan.circuit_of = {n: circuit_of_region.get(union.find(n)) for n in track_nets}

    def circuit(s: Symbol, pin: str) -> Optional[str]:
        n = net(s, pin)
        return plan.circuit_of.get(n.name) if n else None

    # ------------------------------------------------------------------ control points
    cp_of = _control_points(sm, ix, syms, union, net, others, circuit_names={c: r for r, c in circuit_of_region.items() if c})

    def pin_refs(s: Symbol, pin: str) -> list[str]:
        """Every other track pin this pin's net reaches, each as ``pin_ref`` names it, sorted (the owner, 2026-10-27).
        ``others`` leaves out the symbol's own pins; a thing with no name and no id is reported where it is read."""
        return sorted({r for o, op in others(s, pin) if (r := pin_ref(ix.name, o, op))})

    # ------------------------------------------------------------------ appliances
    for s in syms:
        if s.role != "APPLIANCE" or s.get("Appliance") == "head":
            continue
        name = key_of(s)
        if not name:
            report.missing("appliance.name", f"{ix.name}: an {s.get('Appliance') or s.lib_id} has no Name", loc(s))
            continue
        if ":" in name:                                                   # a reference to another interlocking's appliance
            if _foreign(name, ix.name):
                appliance = s.get("Appliance")
                wired = ports_of(s) if is_switch(s) else ("TC",) if appliance == "track_circuit" else ()
                plan.references.append(Reference(appliance or s.lib_id, name, tuple(p for p in wired if net(s, p)),
                                                 f"the {'track circuit marker' if appliance == 'track_circuit' else appliance or s.lib_id}",
                                                 loc(s)))
            continue
        if name in plan.appliances:
            report.error("appliance.duplicate", f"{ix.name}: two appliances named {name!r} (ADR 0003 D8: names are unique in an interlocking)", loc(s))
            continue
        appliance = s.get("Appliance")
        check_milepost(s, report, f"{ix.name}: {appliance} {name}")
        relations: dict[str, Any] = {}
        derived: dict[str, Any] = {}
        row: dict[str, Any] = {"given": given_of(s), "relations": relations, "derived": derived}
        if appliance == "mast":
            joints = [o for o, p in others(s, "SIGNAL") if o.kind == "IRJ_SIGNAL" and p == "SIGNAL"]
            if not joints:
                report.missing("mast.joint", f"{ix.name}: mast {name} stands on no signal joint", loc(s))
            elif len(joints) > 1:
                report.error("mast.joint", f"{ix.name}: mast {name} stands on {len(joints)} signal joints", loc(s))
            row["heads"] = _heads(s, others, report, ix.name)
        elif is_switch(s):
            derived["osCircuit"] = next((circuit(s, p) for p in ports_of(s) if circuit(s, p)), None)
            if not any(net(s, p) for p in ports_of(s)):
                report.missing("switch.track", f"{ix.name}: switch {name} has no track on any port", loc(s))
            for p in ports_of(s):
                relations[p] = pin_refs(s, p)
        elif appliance == "track_circuit":
            relations["TC"] = pin_refs(s, "TC")
            if s.get("Style") == "virtual":
                derived["members"] = [qualify(t.strip(), ix.name) for t in s.get("IndicationToken").split(",") if t.strip()]
                plan.references += [Reference("circuit", m, (), f"virtual circuit {name}'s IndicationToken", loc(s))
                                    for m in derived["members"] if _foreign(m, ix.name)]
        elif appliance in ("lamp", "contact"):
            houses = [cp for cp, h in ix.houses.items() if h.maintainer_call == qualify(name, ix.name)]
            relations["house"] = f"{ix.name}:{houses[0]}" if len(houses) == 1 else None      # its MC wire (D8)
        cp = cp_of.get(s.ref)
        derived["controlPoint"] = f"{ix.name}:{cp}" if cp else None
        if appliance in ("lamp", "contact") and net(s, "MC") and net(s, "MC").name in plan.circuit_of:
            report.info("appliance.on_track", f"{ix.name}: {appliance} {name}'s MC pin is on the track of {circuit(s, 'MC') or 'dark track'}; "
                        "not written", loc(s))
        plan.appliances[name] = _maps(row)
        if is_switch(s):
            plan.sides[name] = frozenset(ports_of(s))
        elif appliance == "track_circuit":
            plan.sides[name] = frozenset({"TC"})

    letters_of_signal: dict[str, dict[str, str]] = defaultdict(dict)
    for name, a in plan.appliances.items():
        if a["given"].get("Appliance") != "mast":
            continue
        m = MAST_NAME.match(name)
        if m is None:
            report.info("mast.grammar", f"{ix.name}: mast {name} is not a signal and its head letters (ADR 0003); not checked")
            continue
        heads = sorted(a.get("heads", {}))
        if heads and list(m.group(2)) != heads:
            report.error("mast.heads", f"{ix.name}: mast {name} names heads {m.group(2)}, but the heads drawn on it are "
                         f"{''.join(heads)} (ADR 0003 rule 7)")
        for letter in m.group(2):
            other = letters_of_signal[m.group(1)].setdefault(letter, name)
            if other != name:
                report.error("mast.letters", f"{ix.name}: signal {m.group(1)} has head {letter} on masts {other} and {name} "
                             "(ADR 0003 rule 6)")

    # ------------------------------------------------------------------ track
    def region(s: Symbol, pin: str) -> Optional[str]:
        n = net(s, pin)
        return union.find(n.name) if n else None

    switch_regions = {region(s, p) for s in syms for p in ports_of(s) if region(s, p)}
    named_track: dict[str, Symbol] = {}
    joints, ends, policies = [], [], []
    for s in syms:
        if s.role not in ("TRACK", "POLICY") or s.kind == "MILEPOST":
            continue
        relations: dict[str, Any] = {}
        derived: dict[str, Any] = {}
        row: dict[str, Any] = {"id": s.uuid or None, "given": given_of(s), "relations": relations, "derived": derived}
        if not s.uuid:
            report.missing("track.id", f"{ix.name}: a {s.kind} has no KiCad UUID in the export, so its row has no id", loc(s))
        name = key_of(s) if s.role == "TRACK" else ""
        if name:
            if name in named_track or name in plan.appliances:
                report.error("track.duplicate", f"{ix.name}: two symbols named {name!r} (ADR 0003 D8: names are unique in an interlocking)", loc(s))
            named_track[name] = s
            row["name"] = qualify(name, ix.name)
            sides = tuple(sorted(side_of(s, p) for p in src.pins_of(s.ref) if p != "SIGNAL"))
            if _foreign(name, ix.name):
                plan.references.append(Reference("track", name, sides, f"the {s.kind}", loc(s)))
            else:
                plan.sides[name] = frozenset(sides)
        pins = [p for p in src.pins_of(s.ref) if p != "SIGNAL"]
        derived["circuits"] = {side_of(s, p): circuit(s, p) for p in pins if circuit(s, p)}
        for p in pins:
            relations[side_of(s, p)] = pin_refs(s, p)
        if s.kind in JOINTS and region(s, "A") and region(s, "A") == region(s, "B"):
            report.error("joint.loop", f"{ix.name}: a joint has one circuit ({circuit(s, 'A') or 'dark track'}) on both sides; a joint "
                         "elsewhere is missing", loc(s))
        if s.kind == "END_CTC" and (circuit(s, "DARK") or (net(s, "CTC") and not circuit(s, "CTC"))):
            report.error("end_ctc.sides", f"{ix.name}: END CTC has {circuit(s, 'DARK') or 'a circuit'} on DARK or dark track on CTC; "
                         "CTC is the side under the dispatcher's control", loc(s))
        if s.kind == "IRJ_SIGNAL":
            if region(s, "B") in switch_regions and region(s, "A") not in switch_regions:
                report.error("joint.reversed", f"{ix.name}: a signal joint has a switch on its B side and none on its A side; "
                             "A is where the route it protects begins", loc(s))
            masts = [o for o, p in others(s, "SIGNAL") if o.get("Appliance") == "mast" and key_of(o)]
            if len(masts) > 1:
                report.error("joint.masts", f"{ix.name}: one signal joint carries masts {', '.join(sorted(key_of(m) for m in masts))}", loc(s))
            relations["mast"] = qualify(key_of(masts[0]), ix.name) if len(masts) == 1 else None
            derived["controlPoint"] = f"{ix.name}:{cp_of[s.ref]}" if cp_of.get(s.ref) else None
        if s.kind == "NEXT_CP" and not s.get("Interlocking"):
            report.missing("next_cp.interlocking", f"{ix.name}: a NextCP states no Interlocking", loc(s))
        row = _maps(row)
        (policies if s.role == "POLICY" else joints if s.kind in JOINTS else ends).append(row)
        if s.role == "TRACK" and s.kind not in JOINTS | ENDS:
            report.info("track.kind", f"{ix.name}: TRACK Kind {s.kind!r} is not one the KiCad importer reads; written with the ends", loc(s))
    links = []                                                            # switch ports that meet with no joint or end between
    seen: set[str] = set()
    for s in syms:
        for p in ports_of(s):
            n = net(s, p)
            if n is None or n.name in seen:
                continue
            seen.add(n.name)
            members = [(src.symbols[x.ref], x.pin) for x in n.pins if x.ref in refs]
            if any(o.role == "TRACK" for o, _ in members):
                continue
            at = sorted(port_ref(ix.name, key_of(o), op) for o, op in members if op in ports_of(o) and key_of(o))
            if len(at) > 1:                                               # computed from the ports' relations (D5)
                links.append(_maps({"derived": {"ports": at, "circuit": plan.circuit_of.get(n.name)}}))
    plan.track = {k: v for k, v in {"joints": joints, "ends": ends, "policies": policies, "links": links}.items() if v}
    return plan


def _foreign(name: str, interlocking: str) -> bool:
    """A name qualified with another interlocking's scope."""
    return ":" in name and name.partition(":")[0] != interlocking


def _maps(row: dict[str, Any]) -> dict[str, Any]:
    """A row with its empty values and empty maps left out: absent is absent (ADR 0008 §4.7)."""
    out: dict[str, Any] = {}
    for k, v in row.items():
        if isinstance(v, dict) and k in ("given", "relations", "derived", "circuits"):
            v = _maps(v)
        if v not in (None, "", [], {}):
            out[k] = v
    return out


def _control_points(sm: Seams, ix, syms: list[Symbol], union: _Union, net, others,
                    circuit_names: dict[str, str]) -> dict[str, Optional[str]]:
    """Each appliance's and signal joint's control point, by symbol reference (the owner, 2026-10-26).

    The houses are the roots. On a sheet with one house it is every appliance's control point. With two or more, the
    stated ``CP`` fields and the maintainer calls' ``MC`` wires are the roots, and the rest inherit along these edges:
    a gang's switch without a letter to its lettered switches and derails (ADR 0003 D8); a switch to its OS circuit,
    the only chain an OS circuit follows; a mast and its signal joint, either way; a signal joint to the circuits on its
    two sides that hold no switch; a circuit across a plain joint to one that holds no switch; a virtual circuit's members
    to it. A stated field wins over every chain, silently, and stops the chains through it. Reached by chains from two
    houses and stating none is an error, and so is reached by none: the graph is incomplete. A track circuit marker
    stands for its circuit."""
    report = sm.report
    houses = {h.casefold(): h for h in ix.houses}
    apps = [s for s in syms if s.role == "APPLIANCE" and s.get("Appliance") != "head" and key_of(s) and ":" not in key_of(s)]
    joints = [s for s in syms if s.kind == "IRJ_SIGNAL"]

    def region(s: Symbol, pin: str) -> Optional[str]:
        n = net(s, pin)
        return "r:" + union.find(n.name) if n else None

    def node(s: Symbol) -> str:
        if s.get("Appliance") == "track_circuit" and s.get("Style") != "virtual" and region(s, "TC"):
            return region(s, "TC")
        return s.ref

    def what(s: Symbol) -> str:
        return f"{s.get('Appliance') or 'signal joint'} {key_of(s) or loc(s)}"

    stated: dict[str, str] = {}
    origin: dict[str, Symbol] = {}
    for s in apps + joints:
        if not s.get("CP"):
            continue
        h = houses.get(s.get("CP").casefold())
        if h is None:
            report.error("control_point.house", f"{ix.name}: {what(s)} names control point {s.get('CP')!r}, which is no house of "
                         f"{ix.name} ({', '.join(sorted(ix.houses)) or 'none'})", loc(s))
            continue
        stated[node(s)], origin[node(s)] = h, s
    for s in apps:
        if s.get("Appliance") == "lamp" and s.get("Style") == "maintainer_call":
            calls = [cp for cp, h in ix.houses.items() if h.maintainer_call == qualify(key_of(s), ix.name)]
            if len(calls) == 1:
                if stated.get(s.ref, calls[0]) != calls[0]:
                    report.error("control_point.disagree", f"{ix.name}: {what(s)} is wired to house {calls[0]} and states CP "
                                 f"{stated[s.ref]!r}", loc(s))
                stated[s.ref], origin[s.ref] = calls[0], s

    if len(ix.houses) == 1:
        root = next(iter(ix.houses))
        return {s.ref: root for s in apps + joints}

    edges: dict[str, set[str]] = defaultdict(set)
    switch_regions = {region(s, p) for s in apps for p in ports_of(s) if region(s, p)}
    switches = {key_of(s): s for s in apps if is_switch(s)}
    for s in switches.values():
        for p in ports_of(s):
            if region(s, p):
                edges[s.ref].add(region(s, p))
        lead = switches.get(GANG.sub("", key_of(s)))
        if lead is not None and lead is not s:
            edges[lead.ref].add(s.ref)
    for s in joints:
        for o, p in others(s, "SIGNAL"):
            if o.get("Appliance") == "mast" and p == "SIGNAL":
                edges[s.ref].add(o.ref)
                edges[o.ref].add(s.ref)
        for side in ("A", "B"):
            r = region(s, side)
            if r and r not in switch_regions:
                edges[s.ref].add(r)
    for s in syms:
        if s.kind == "IRJ":
            a, b = region(s, "A"), region(s, "B")
            if a and b and a != b:
                if b not in switch_regions:
                    edges[a].add(b)
                if a not in switch_regions:
                    edges[b].add(a)
    for s in apps:
        if s.get("Appliance") == "track_circuit" and s.get("Style") == "virtual":
            for t in s.get("IndicationToken").split(","):
                r = circuit_names.get(qualify(t.strip(), ix.name)) if t.strip() else None
                if r:
                    edges["r:" + r].add(s.ref)

    reach: dict[str, dict[str, str]] = defaultdict(dict)                 # node -> house -> the stated symbol it came from
    for seed, h in stated.items():
        seen, todo = {seed}, list(edges[seed])
        while todo:
            n = todo.pop()
            if n in seen or n in stated:
                continue
            seen.add(n)
            reach[n].setdefault(h, key_of(origin[seed]) or origin[seed].kind)
            todo.extend(edges[n])

    out: dict[str, Optional[str]] = {}
    for s in apps + joints:
        n = node(s)
        if n in stated:
            out[s.ref] = stated[n]
            continue
        found = reach.get(n, {})
        out[s.ref] = next(iter(found)) if len(found) == 1 else None
        if s in joints and any(o.get("Appliance") == "mast" for o, _ in others(s, "SIGNAL")):
            continue                                                      # its mast reports for it
        if len(found) > 1:
            report.error("control_point.chains", f"{ix.name}: {what(s)} is reached from "
                         f"{' and '.join(f'{h} (by {via})' for h, via in sorted(found.items()))}; a CP field on it settles which", loc(s))
        elif not found:
            report.error("control_point.unreached", f"{ix.name}: no house reaches {what(s)}: no CP field on it and no chain to one",
                         loc(s))
    for s in switches.values():
        lead = switches.get(GANG.sub("", key_of(s)))
        if lead is not None and lead is not s and out.get(s.ref) and out.get(lead.ref) and out[s.ref] != out[lead.ref]:
            report.warning("control_point.gang", f"{ix.name}: switch {key_of(s)} is on {out[s.ref]} but its gang's {key_of(lead)} is on "
                           f"{out[lead.ref]}; one gang is one lever", loc(s))
    return out


def _heads(mast: Symbol, others, report, interlocking: str) -> dict[str, Any]:
    """A mast's heads by letter, each with its own ``given``: the Style the trackplan draws (ADR 0009 §3.7)."""
    heads: dict[str, Any] = {}
    for pin in ("H", "H1", "H2", "H3", "H4"):
        for o, p in others(mast, pin):
            if o.get("Appliance") != "head" or p != "M":
                continue
            letter = key_of(o)
            if not letter:
                report.missing("head.letter", f"{interlocking}: a head on mast {key_of(mast)} has no Name (its letter)", loc(o))
                continue
            if letter in heads:
                report.error("head.duplicate", f"{interlocking}: mast {key_of(mast)} has two heads {letter}", loc(o))
            heads[letter] = _maps({"given": given_of(o)})                 # a head is an entity nested under its mast (D9)
    return heads
