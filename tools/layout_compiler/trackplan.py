"""The trackplan as drawn: each interlocking's appliances and track rows, with what was stated as fields (``given``)
and as wires (``relations``) (ADR 0010 §4.1 and C6; ADR 0011 §2). Transient (ADR 0011 §1): everything the rules
compute from these (circuits, control points, links, NextCP pairing, the cross-interlocking reference check) is the
reference derivation's, ``tools/layout_model/derive.py``.

What is on the trackplan is decided by Role, never by library, symbol name or position: ``APPLIANCE``, ``TRACK`` and
``POLICY``, with the house (``STRUCTURE``, Kind ``CONTROL_POINT``) beside them. The geometry piece reads the same
symbols with the same test (``TRACKPLAN_ROLES``) and names a run's ends through the same ``pin_ref``.

A track pin's wire is ``relations.<side>``: every other track pin its net reaches (three-maps D5; the owner,
2026-10-27): a switch port, a track circuit marker's TC or a named row's side by qualified name, an unnamed row's side
by the row's ``id`` (``pin_ref``, the one form a run's ends use too). A track pin is a switch's port, a marker's TC and
every pin of a joint, an end or a policy sign but a signal joint's SIGNAL (``is_track_pin``); a pin never names its own
symbol, so the relation is symmetric and the track can be walked through ``relations`` alone. The KiCad importer
translates pin names into sides here (``side_of``, three-maps D15; ADR 0012 §8): a signal joint's ``A`` is
``governed`` and its ``B`` ``approach``; a policy sign's and a NextCP's one pin is ``track``. A row is identified by
``id``, its symbol's KiCad UUID (D10), and an end of track may also carry a name (an industry).

A name qualified with another interlocking's scope is a one-sided reference: it is no appliance here, and nothing is
written back to the thing it names (the owner, 2026-10-27). A track circuit marker so named (Sargent's ``Corporal:2NAT``)
is a consumer of that station's indication: a row of ``track.consumers`` with its symbol's UUID as ``id``, its fields
in ``given`` (its ``Name`` included, since a row has no name), and ``relations.indication``, the token it consumes,
the drawn name with the indications' ``K`` added at ingest (``Corporal:2NATK``; reference data). The neighbours name
its TC by the id, like any local row. A switch so named (``Corporal:1``) is still named by its port
(``Corporal:1.C``): what it consumes has no stated token form yet. The reference derivation checks both.

Diagnostics here are about the drawing as drawn: a symbol with no name or no UUID, two symbols with one name, two masts
on one signal joint (the file has one ``relations.mast``). Nothing here reads a coordinate, a net name, a reference or
``Value``; every name is read through ``key_of``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from tools.layout_model.reference import indication_tokens

from .seams import Seams, check_milepost, given_of, key_of, loc, qualify
from .source import Net, Symbol

TRACKPLAN_ROLES = frozenset({"APPLIANCE", "TRACK", "POLICY"})
# A switch's track ports, the one vocabulary of both pieces (geometry's ``to: "Luchessa:783.R"``, ADR 0010 §4.6).
SWITCH_PORTS = ("C", "N", "R")
DERAIL_PORTS = ("C", "R")
JOINTS = frozenset({"IRJ", "IRJ_SIGNAL"})
ENDS = frozenset({"END_CTC", "NEXT_CP", "BUMPER", "INDUSTRY"})


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


def is_consumer(interlocking: str, s: Symbol) -> bool:
    """A track circuit marker named for another interlocking's circuit (Sargent's ``Corporal:2NAT``): a consumer of that
    station's indication, a row of this interlocking with an id (the owner, 2026-10-27)."""
    return s.role == "APPLIANCE" and s.get("Appliance") == "track_circuit" and _foreign(key_of(s), interlocking)


def pin_ref(interlocking: str, s: Symbol, pin: str) -> Optional[str]:
    """How the model names a track pin, the one form of a side's relations and a run's ends (three-maps D5, D10, D15): a
    switch port, a marker's TC or a named track row's side by qualified name (``Luchessa:783.R``), an unnamed row's side
    by the row's id (``<uuid>.approach``), a consumer's TC by its id as well (``<uuid>.TC``). None for a pin that is not
    track and for a thing with neither."""
    if not is_track_pin(s, pin):
        return None
    if is_consumer(interlocking, s):
        return f"{s.uuid}.TC" if s.uuid else None
    name = key_of(s) if s.role != "POLICY" else ""
    if name:
        return port_ref(interlocking, name, side_of(s, pin))
    if s.role in ("TRACK", "POLICY"):
        return f"{s.uuid}.{side_of(s, pin)}" if s.uuid else None
    return None


@dataclass
class Plan:
    """One interlocking's trackplan as drawn."""

    name: str
    appliances: dict[str, dict[str, Any]] = field(default_factory=dict)
    track: dict[str, Any] = field(default_factory=dict)
    sources: dict[str, Symbol] = field(default_factory=dict)          # model path under the interlocking -> its symbol


@dataclass
class Trackplan:
    plans: dict[str, Plan] = field(default_factory=dict)


def read(sm: Seams) -> Trackplan:
    out = Trackplan()
    for ix in sm.interlockings.values():
        syms = [s for s in sm.source.under(ix.sym.sheet, "APPLIANCE") + sm.source.under(ix.sym.sheet, "TRACK")
                + sm.source.under(ix.sym.sheet, "POLICY") if unit_of(sm, s) == ix.name]
        if syms:
            out.plans[ix.name] = _plan(sm, ix, syms)
    return out


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

    def pin_refs(s: Symbol, pin: str) -> list[str]:
        """Every other track pin this pin's net reaches, each as ``pin_ref`` names it, sorted (the owner, 2026-10-27).
        ``others`` leaves out the symbol's own pins; a thing with no name and no id is reported where it is read."""
        return sorted({r for o, op in others(s, pin) if (r := pin_ref(ix.name, o, op))})

    track_nets = {n.name for s in syms for pin, n in src.pins_of(s.ref).items() if is_track_pin(s, pin)}
    consumers: list[dict[str, Any]] = []
    _shorted(syms, src, report, ix.name)

    # ------------------------------------------------------------------ appliances
    for s in syms:
        if s.role != "APPLIANCE" or s.get("Appliance") == "head":
            continue
        name = key_of(s)
        if not name:
            report.missing("appliance.name", f"{ix.name}: an {s.get('Appliance') or s.lib_id} has no Name", loc(s))
            continue
        appliance = s.get("Appliance")
        if ":" in name:                                                   # a reference to another interlocking's appliance
            wired = [p for p in (ports_of(s) if is_switch(s) else ("TC",) if appliance == "track_circuit" else ()) if net(s, p)]
            if _foreign(name, ix.name) and not wired:
                report.warning("reference.unwritten", f"{ix.name}: the {appliance or s.lib_id} {name} names another interlocking's "
                               "thing but nothing here uses it; not written", loc(s))
            elif is_consumer(ix.name, s):
                if not s.uuid:
                    report.missing("track.id", f"{ix.name}: the marker {name} has no KiCad UUID in the export, so its row has no id", loc(s))
                consumers.append(_maps({"id": s.uuid or None, "given": given_of(s, keyed=False),
                                        "relations": {"TC": pin_refs(s, "TC"), "indication": _indication(s, name, report)}}))
                if s.uuid:
                    plan.sources[f"track/consumers/{s.uuid}"] = s
            continue
        if name in plan.appliances:
            report.error("appliance.duplicate", f"{ix.name}: two appliances named {name!r} (ADR 0003 D8: names are unique in an interlocking)", loc(s))
            continue
        check_milepost(s, report, f"{ix.name}: {appliance} {name}")
        relations: dict[str, Any] = {}
        row: dict[str, Any] = {"given": given_of(s), "relations": relations}
        if appliance == "mast":
            row["heads"] = _heads(s, others, report, ix.name)
        elif is_switch(s):
            for p in ports_of(s):
                relations[p] = pin_refs(s, p)
        elif appliance == "track_circuit":
            relations["TC"] = pin_refs(s, "TC")
        elif appliance in ("lamp", "contact"):
            houses = [cp for cp, h in ix.houses.items() if h.maintainer_call == qualify(name, ix.name)]
            relations["house"] = f"{ix.name}:{houses[0]}" if len(houses) == 1 else None      # its MC wire (D8)
        if appliance in ("lamp", "contact") and net(s, "MC") and net(s, "MC").name in track_nets:
            report.info("appliance.on_track", f"{ix.name}: {appliance} {name}'s MC pin is on the track; not written", loc(s))
        plan.appliances[name] = _maps(row)
        plan.sources[f"appliances/{name}"] = s

    # ------------------------------------------------------------------ track
    named_track: dict[str, Symbol] = {}
    joints, ends, policies = [], [], []
    for s in syms:
        if s.role not in ("TRACK", "POLICY") or s.kind == "MILEPOST":
            continue
        relations: dict[str, Any] = {}
        row: dict[str, Any] = {"id": s.uuid or None, "given": given_of(s), "relations": relations}
        if not s.uuid:
            report.missing("track.id", f"{ix.name}: a {s.kind} has no KiCad UUID in the export, so its row has no id", loc(s))
        name = key_of(s) if s.role == "TRACK" else ""
        if name:
            if name in named_track or name in plan.appliances:
                report.error("track.duplicate", f"{ix.name}: two symbols named {name!r} (ADR 0003 D8: names are unique in an interlocking)", loc(s))
            named_track[name] = s
            row["name"] = qualify(name, ix.name)
        for p in src.pins_of(s.ref):
            if p != "SIGNAL":
                relations[side_of(s, p)] = pin_refs(s, p)
        if s.kind == "IRJ_SIGNAL":
            masts = [o for o, p in others(s, "SIGNAL") if o.get("Appliance") == "mast" and key_of(o)]
            if len(masts) > 1:
                report.error("joint.masts", f"{ix.name}: one signal joint carries masts {', '.join(sorted(key_of(m) for m in masts))}", loc(s))
            relations["mast"] = qualify(key_of(masts[0]), ix.name) if len(masts) == 1 else None
        row = _maps(row)
        kind = "policies" if s.role == "POLICY" else "joints" if s.kind in JOINTS else "ends"
        {"policies": policies, "joints": joints, "ends": ends}[kind].append(row)
        if s.uuid:
            plan.sources[f"track/{kind}/{s.uuid}"] = s
        if s.role == "TRACK" and s.kind not in JOINTS | ENDS:
            report.info("track.kind", f"{ix.name}: TRACK Kind {s.kind!r} is not one the KiCad importer reads; written with the ends", loc(s))
    plan.track = {k: v for k, v in {"joints": joints, "ends": ends, "policies": policies, "consumers": consumers}.items() if v}
    return plan


def _indication(s: Symbol, name: str, report) -> str:
    """The indication token a remote consumer marker consumes: its ``Indication`` field, qualified in the scope its
    ``Name`` names (the owner, 2026-10-28: ``Indication=${Name}K`` is to be a library field macro). Without one, the
    legacy form: by the AAR nomenclature behind every code line, the circuit's name with the indications' K added
    (``Corporal:2NAT`` is ``Corporal:2NATK``; the owner, 2026-10-27), the reference data's default template, reported
    at info so what is unconverted shows."""
    scope, _, circuit = name.partition(":")
    if s.get("Indication"):
        return qualify(s.get("Indication"), scope)
    token = f"{scope}:" + indication_tokens(None)["track_circuit"][0].format(name=circuit)
    report.info("consumer.legacy_token", f"the consumer {name} states no Indication; read from its Name as {token}", loc(s))
    return token


def _shorted(syms: list[Symbol], src, report, interlocking: str) -> None:
    """Two track pins of one symbol on one net (a switch's N and R wired to each other with nothing between): an error
    (the owner, 2026-10-28; a correct drawing has insulated joints, and maybe a track circuit, between them). The
    relations cannot state it, since a pin never names its own symbol."""
    for s in syms:
        by_net: dict[str, list[str]] = {}
        for pin, n in src.pins_of(s.ref).items():
            if is_track_pin(s, pin):
                by_net.setdefault(n.name, []).append(side_of(s, pin))
        for sides in by_net.values():
            if len(sides) > 1:
                report.error("track.shorted", f"{interlocking}: {s.get('Appliance') or s.kind or s.lib_id} {key_of(s) or s.ref} has "
                             f"{' and '.join(sorted(sides))} on one wire with nothing between; insulated joints belong there", loc(s))


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
