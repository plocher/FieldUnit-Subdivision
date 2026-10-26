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

**Control point membership** is derived from the signals: an ``IRJ-Signal`` states its control point in ``CP`` (the
one place the field lives, ADR 0009 and the unify decisions) and stands with its ``A`` pin inside the limits it
governs. A circuit bounded on its ``A`` sides by the signal joints of one control point belongs to it, and so does
every appliance in it; a mast belongs to the control point of the joint its ``SIGNAL`` pin stands on; a maintainer
call to the house its ``MC`` pin is wired to. An appliance's own ``CP`` field is the fallback, and the two must agree;
the field retires when every value agrees with the derivation (handoff item 6).

Nothing here reads a coordinate, a net name, a reference or ``Value``.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Optional

from .seams import Seams, compare, loc, qualify, settings_of
from .source import Net, Symbol

TRACKPLAN_ROLES = frozenset({"APPLIANCE", "TRACK", "POLICY"})
# A switch's track ports, the one vocabulary of both pieces (geometry's ``to: "Luchessa:783.R"``, ADR 0010 §4.6).
SWITCH_PORTS = ("C", "N", "R")
DERAIL_PORTS = ("C", "R")
JOINTS = frozenset({"IRJ", "IRJ_SIGNAL"})
ENDS = frozenset({"END_CTC", "NEXT_CP", "BUMPER", "INDUSTRY"})
# The fields the trackplan piece reads; with seams.NOT_SETTINGS they are never written as settings.
READ = {"CP", "TC", "IndicationCeiling", "IndicationToken", "Direction", "Display"}


def on_trackplan(s: Symbol) -> bool:
    return s.role in TRACKPLAN_ROLES


def is_switch(s: Symbol) -> bool:
    return s.role == "APPLIANCE" and s.get("Appliance") == "switch"


def ports_of(s: Symbol) -> tuple[str, ...]:
    """The track ports of a switch, a derail's two (Style ``derail``); none for anything else."""
    if not is_switch(s):
        return ()
    return DERAIL_PORTS if s.get("Style") == "derail" else SWITCH_PORTS


def port_ref(interlocking: str, name: str, port: str) -> str:
    """A switch port by qualified name: ``Luchessa:783.R``."""
    return f"{qualify(name, interlocking)}.{port}"


@dataclass
class Plan:
    """One interlocking's trackplan, resolved."""

    name: str
    circuit_of: dict[str, Optional[str]] = field(default_factory=dict)        # net name -> qualified circuit
    appliances: dict[str, dict[str, Any]] = field(default_factory=dict)
    track: dict[str, Any] = field(default_factory=dict)


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
                + sm.source.under(ix.sym.sheet, "POLICY") if _unit_of(sm, s) == ix.name]
        if syms:
            out.plans[ix.name] = _plan(sm, ix, syms)
    return out


def _unit_of(sm: Seams, s: Symbol) -> Optional[str]:
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
            named[union.find(net(s, "TC").name)]["marker"].append(qualify(s.get("Name"), ix.name))
        elif is_switch(s) and s.get("TC"):
            n = next((net(s, p) for p in ports_of(s) if net(s, p)), None)
            if n is None:
                continue
            if "," in s.get("TC"):
                report.error("switch.tc_block", f"{ix.name}: switch {s.get('Name')} lists several circuits in TC ({s.get('TC')}); "
                             "a detection block has no form in schema 3.1.0", loc(s))
                continue
            named[union.find(n.name)]["os"].append(qualify(s.get("TC"), ix.name))
    circuit_of_region: dict[str, Optional[str]] = {}
    for region, names in named.items():
        markers, os_ = sorted(set(names["marker"])), sorted(set(names["os"]))
        if len(markers) > 1 or len(os_) > 1:
            report.error("circuit.names", f"{ix.name}: one circuit carries the names {', '.join(markers + os_)}; a joint is missing "
                         "or a TC is wrong", f"sheet {ix.sym.sheet}")
            continue
        marker, os_name = (markers or [None])[0], (os_ or [None])[0]
        circuit_of_region[region] = compare(marker, os_name, f"{ix.name}: the circuit {marker or os_name}", f"sheet {ix.sym.sheet}",
                                            _Quiet(report), "circuit.name")
    plan.circuit_of = {n: circuit_of_region.get(union.find(n)) for n in track_nets}

    def circuit(s: Symbol, pin: str) -> Optional[str]:
        n = net(s, pin)
        return plan.circuit_of.get(n.name) if n else None

    # ------------------------------------------------------------------ control points
    houses = {h.casefold(): h for h in ix.houses}
    one_house = next(iter(ix.houses)) if len(ix.houses) == 1 else None

    def house(cp: str, s: Symbol) -> Optional[str]:
        h = houses.get(cp.casefold())
        if h is None:
            report.error("control_point.house", f"{ix.name}: {s.get('Name') or s.kind} names control point {cp!r}, which is no house of "
                         f"{ix.name} ({', '.join(sorted(ix.houses)) or 'none'})", loc(s))
        return h

    joint_cp: dict[str, Optional[str]] = {}
    region_cps: dict[str, set[str]] = defaultdict(set)
    for s in syms:
        if s.kind != "IRJ_SIGNAL":
            continue
        stated = house(s.get("CP"), s) if s.get("CP") else None
        cp = compare(stated, one_house, f"{ix.name}: a signal joint's control point", loc(s), report, "joint.control_point")
        joint_cp[s.ref] = cp
        a = net(s, "A")
        if a is not None and cp:
            region_cps[union.find(a.name)].add(cp)
        if a is None or not any(is_switch(o) for o, _ in others(s, "A")) and not _region_has_switch(union, a.name, syms, src):
            report.info("joint.inside", f"{ix.name}: a signal joint (CP {cp!r}) has no switch on its A side; A is the side inside the "
                        "limits it governs", loc(s))

    def derived(s: Symbol, pin: str) -> Optional[str]:
        n = net(s, pin)
        cps = region_cps.get(union.find(n.name), set()) if n else set()
        if len(cps) > 1:
            report.info("control_point.shared", f"{ix.name}: {s.get('Name')} is in a circuit bounded by the signals of "
                        f"{', '.join(sorted(cps))}; the signals do not say which control point it belongs to", loc(s))
        return next(iter(cps)) if len(cps) == 1 else None

    # ------------------------------------------------------------------ appliances
    for s in syms:
        if s.role != "APPLIANCE" or s.get("Appliance") == "head":
            continue
        name = s.get("Name")
        if not name or name == "~":
            report.missing("appliance.name", f"{ix.name}: an {s.get('Appliance') or s.lib_id} has no Name", loc(s))
            continue
        if ":" in name:
            continue                                                      # a reference to another interlocking's appliance
        if name in plan.appliances:
            report.error("appliance.duplicate", f"{ix.name}: two appliances named {name!r} (ADR 0003 D8: names are unique in an interlocking)", loc(s))
            continue
        appliance = s.get("Appliance")
        row: dict[str, Any] = {"appliance": appliance, "style": s.get("Style") or None,
                               "settings": {k: v for k, v in settings_of(s).items() if k not in READ}}
        explicit = None
        if appliance == "mast":
            joints = [o for o, p in others(s, "SIGNAL") if o.kind == "IRJ_SIGNAL" and p == "SIGNAL"]
            if len(joints) == 1:
                explicit = joint_cp.get(joints[0].ref)
            elif not joints:
                report.missing("mast.joint", f"{ix.name}: mast {name} stands on no signal joint", loc(s))
            else:
                report.error("mast.joint", f"{ix.name}: mast {name} stands on {len(joints)} signal joints", loc(s))
            row["heads"] = _heads(s, others, report, ix.name)
        elif is_switch(s):
            explicit = derived(s, "C")
            if s.get("TC") and "," not in s.get("TC"):
                row["osCircuit"] = qualify(s.get("TC"), ix.name)
            row["indicationCeiling"] = s.get("IndicationCeiling") or None
        elif appliance == "track_circuit":
            if net(s, "TC"):
                explicit = derived(s, "TC")
            if s.get("Style") == "virtual":
                row["members"] = [qualify(t.strip(), ix.name) for t in s.get("IndicationToken").split(",") if t.strip()]
        elif appliance == "lamp" and s.get("Style") == "maintainer_call":
            calls = [cp for cp, h in ix.houses.items() if h.maintainer_call == qualify(name, ix.name)]
            explicit = calls[0] if len(calls) == 1 else None
        field_cp = house(s.get("CP"), s) if s.get("CP") else None
        cp = compare(explicit, field_cp, f"{ix.name}: {appliance} {name} in control point", loc(s), report, "appliance.control_point")
        row["controlPoint"] = f"{ix.name}:{cp}" if cp else None
        if appliance in ("lamp", "contact") and net(s, "MC") and net(s, "MC").name in plan.circuit_of:
            report.info("appliance.on_track", f"{ix.name}: {appliance} {name}'s MC pin is on the track of {circuit(s, 'MC') or 'dark track'}; "
                        "not written", loc(s))
        plan.appliances[name] = {k: v for k, v in row.items() if v not in (None, "", [], {})}

    # ------------------------------------------------------------------ track
    joints, ends, policies = [], [], []
    for s in syms:
        if s.role not in ("TRACK", "POLICY") or s.kind == "MILEPOST":
            continue
        row: dict[str, Any] = {"kind": s.kind}
        pins = [p for p in src.pins_of(s.ref) if p != "SIGNAL"]
        circuits = {p: circuit(s, p) for p in pins}
        row["circuits"] = {p: c for p, c in circuits.items() if c}
        ports: dict[str, list[str]] = {}
        for p in pins:
            at = sorted(port_ref(ix.name, o.get("Name"), op) for o, op in others(s, p) if op in ports_of(o) and o.get("Name"))
            if at:
                ports[p] = at
        row["ports"] = ports
        if s.kind == "IRJ_SIGNAL":
            masts = [o for o, p in others(s, "SIGNAL") if o.get("Appliance") == "mast" and o.get("Name")]
            row["mast"] = qualify(masts[0].get("Name"), ix.name) if len(masts) == 1 else None
            row["controlPoint"] = f"{ix.name}:{joint_cp[s.ref]}" if joint_cp.get(s.ref) else None
        if s.role == "POLICY":
            row["direction"] = s.get("Direction") or None
        row = {k: v for k, v in row.items() if v not in (None, "", [], {})}
        (policies if s.role == "POLICY" else joints if s.kind in JOINTS else ends).append(row)
        if s.role == "TRACK" and s.kind not in JOINTS | ENDS:
            report.info("track.kind", f"{ix.name}: TRACK Kind {s.kind!r} is not one this compiler reads; written with the ends", loc(s))
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
            at = sorted(port_ref(ix.name, o.get("Name"), op) for o, op in members if op in ports_of(o) and o.get("Name"))
            if len(at) > 1:
                links.append({"ports": at, **({"circuit": plan.circuit_of[n.name]} if plan.circuit_of.get(n.name) else {})})
    mileposts = sorted(s.get("Name") for s in syms if s.kind == "MILEPOST" and s.get("Name"))
    plan.track = {k: v for k, v in {"joints": joints, "ends": ends, "policies": policies, "links": links, "mileposts": mileposts}.items() if v}
    return plan


def _region_has_switch(union: _Union, net_name: str, syms: list[Symbol], src) -> bool:
    root = union.find(net_name)
    return any(n is not None and union.find(n.name) == root for s in syms for n in (src.net_of(s.ref, p) for p in ports_of(s)))


def _heads(mast: Symbol, others, report, interlocking: str) -> dict[str, Any]:
    """A mast's heads by letter, each with the Style the trackplan draws (ADR 0009 §3.7)."""
    heads: dict[str, Any] = {}
    for pin in ("H", "H1", "H2", "H3", "H4"):
        for o, p in others(mast, pin):
            if o.get("Appliance") != "head" or p != "M":
                continue
            letter = o.get("Name")
            if not letter:
                report.missing("head.letter", f"{interlocking}: a head on mast {mast.get('Name')} has no Name (its letter)", loc(o))
                continue
            if letter in heads:
                report.error("head.duplicate", f"{interlocking}: mast {mast.get('Name')} has two heads {letter}", loc(o))
            heads[letter] = {"style": o.get("Style")} if o.get("Style") else {}
    return heads


class _Quiet:
    """A report that keeps the errors of ``compare`` and drops its infos: a circuit named by its marker alone, or by its
    switch's TC alone, is the ordinary case and says nothing."""

    def __init__(self, report) -> None:
        self.report = report

    def error(self, *a, **k):
        self.report.error(*a, **k)

    def info(self, *a, **k):
        pass

    def missing(self, *a, **k):
        pass
