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
every pin of a joint, an end or a policy sign but a signal joint's SIGNAL pins (``is_track_pin``); a pin never names
its own symbol, so the relation is symmetric and the track can be walked through ``relations`` alone. The KiCad
importer translates pin names into sides here (``side_of``, three-maps D15; ADR 0012 §8): a signal joint's ``A`` is
``governed`` and its ``B`` ``approach``; a policy sign's and a NextCP's one pin is ``track``. A row is identified by
``id``, its symbol's KiCad UUID (D10), and an end of track may also carry a name (an industry).

A joint with a mast on each side is Kind ``IRJ_SIGNALS`` (ADR 0013 §6, 2026-11-02): pins ``A`` and ``B`` keep their
names, since approach and governed are relative to a mast, not to the joint; ``SIGNAL_A`` carries the mast that
governs into side A and ``SIGNAL_B`` the one into side B, stated as ``relations.masts`` (``{"A": mast, "B": mast}``,
qualified names). Nothing is read from rotation or from which mast is drawn first. Each mast's own approach and
governed sides are the reference derivation's.

A boundary track circuit is ``Appliance track_circuit`` with Style ``boundary`` (ADR 0013 §10, 2026-11-02): a detector at
a joint, with pins ``A`` and ``B`` on the two nets there. Both are track pins, stated as ``relations.A`` and ``.B`` like a
marker's ``TC``; it never names, splits or ends a circuit (the marker on each net does), and which circuits it counts
toward is the reference derivation's.

A plate is a POLICY of Kind ``RULE_290_G`` or ``RULE_290_R`` (ADR 0013 §5, 2026-11-02) whose pin ``To`` sits on a
mast's SIGNAL net: its row's relation is ``mast``, the mast on that net, and it has no track side; that the mast is
``PERMISSIVE`` is the reference derivation's check.

A policy sign that states a Name is a named row, as an industry end is: a ladder marker (Kind ``LADDER``, issue #145)
names its ladder, so its row carries ``name`` and its pin is named ``Watsonville:Arrival.track``. A POLICY whose Kind no
rule reads (not a GCOR Rule regime, the current-of-traffic sign, a plate or a ladder marker) is written as drawn; that
no rule reads it is the reference derivation's ``policy.kind``, a fact of the model, not of the drawing.

A track net is read across sheets (ADR 0013 §7.1, 2026-11-02): block track is drawn from one control point to the next,
a hierarchical label continues the run, and pairing comes from netlist connectivity, so a track pin's wire names every
other track pin on its net whatever sheet that pin is drawn on, each by its own sheet's interlocking (Sargent's 834
double joint names ``Corporal:834T.TC`` on its side A, and Corporal's 834T names the joint's pin by its id). No pairing
step exists. The same holds for a signal pin and a head's pin: a mast or a head on another sheet is read as drawn. A
symbol under no interlocking's sheet is left out, as it was. Whether such a net is block track or an error (a powered
switch on it) is the reference derivation's check.

A mast's Name is KiCad shorthand for three atoms (ADR 0003 rules 5 to 7; the owner, 2026-11-12: the atoms are stated,
the Name is a label, and nothing downstream reads it): ``grammar.mast_atoms`` decomposes it into ``given.signal`` (the
signal number, ``784``), ``relations.facing`` (the side letter's direction, D1: N and W ``LEFT``, S and E ``RIGHT``) and
``given.heads`` (the head letters top down, ``B,C``; the k-th letter is the k-th pin of the field mast device). A Name
that is not the grammar states none of them, ``mast.name`` at missing. ``emit.facts`` checks the glyph's turn against the
stated facing (``geometry.facing``) and states it from the glyph only where the Name does not.

A derail's Name carries ADR 0003 D8 the same way (the owner, 2026-11-13): its gang id names the switch or lock gang it
follows, read once here by ``grammar.derail_switch`` over the interlocking's switch names and stated as
``relations.switch`` (``X:795`` on ``795D``); a derail whose gang id names no switch states none and is independent.
The derivation reads the stated relation and never the Name (``grammar.depends_on``).

A train order board is ``Appliance train_order`` (the owner, 2026-11-03, 2026-11-08): an operator-controlled, non-vital
indicator, never a signal in the interlocking sense, never in a route and never in a control point, so it has its own
appliance word and no code path that reads masts sees it. Its Style, ``single`` or ``double``, is the symbol drawn, as a
signal mast's is. The trackplan symbol has no pins: its faces are the pins of its field mast device, and the heads and
levers wired to them (``seams._mast_on_ind``). Its ``Station`` field names the timetable station it stands at,
``relations.station`` (unqualified: stations are layout entities). It has no track pin: one with any pin on a track net
is the import error ``train_order.track``. Which way a single board faces is its glyph's turn on the sheet,
``relations.facing`` (``emit.facts`` writes it from the geometry, ``geometry.facing``).

A lamp, contact or actuator (``Appliance lamp``, ``contact``, ``actuator``; #82) has one pin, SENSOR, LAMP or ACTUATOR,
a maintainer call's MC. On a track net it states the track the appliance stands on, ``relations.track``: every track pin
on that net, as any track side names them. Track that names no circuit is track like any other (the owner, 2026-11-09);
which piece it is and what the piece is called are the reference derivation's. The relation is one-sided: the appliance's
pin is no track pin, so no other thing names it and its wire alone never makes a net track. On a house's MC pin it is
the house's maintainer call, ``relations.house``. On any other wire it is the import error ``appliance.track_pin``. Not
wired, the appliance states no track and stands at its Milepost and CP Name. The three are read alike; no rule tells an
actuator from a lamp (the map's fog).

A name qualified with another interlocking's scope is a one-sided reference: it is no appliance here, and nothing is
written back to the thing it names (the owner, 2026-10-27). A track circuit marker so named (Sargent's ``Corporal:2NAT``)
is a consumer of that station's indication: a row of ``track.consumers`` with its symbol's UUID as ``id``, its fields
in ``given`` (its ``Name`` included, since a row has no name), and ``relations.indication``, the token it consumes: its
``Indication`` field, else the drawn name with the indications' ``K`` added at ingest (``Corporal:2NATK``; reference
data), reported at info. The neighbours name its TC by the id, like any local row. A switch so named (``Corporal:1``)
is named by its port (``Corporal:1.C``), which the reference derivation reports as an error (the owner, 2026-10-28).
An off-track symbol so named that nothing is wired to is a warning, ``reference.unwritten``.

Diagnostics here are about the drawing as drawn: a symbol with no name or no UUID, two symbols with one name, two masts
on one SIGNAL pin of a signal joint (the file has one mast per pin), two track pins of one symbol on one wire
(``track.shorted``). Nothing here reads a coordinate, a net name, a reference or
``Value``; every name is read through ``key_of``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from tools.layout_model.grammar import derail_switch, mast_atoms
from tools.layout_model.reference import indication_tokens

from .seams import Seams, check_milepost, given_of, key_of, loc, qualify, styles_of, token_field
from .source import Net, Symbol

TRACKPLAN_ROLES = frozenset({"APPLIANCE", "TRACK", "POLICY"})
# A switch's track ports, the one vocabulary of both pieces (geometry's ``to: "Luchessa:783.R"``, ADR 0010 §4.6).
SWITCH_PORTS = ("C", "N", "R")
DERAIL_PORTS = ("C", "R")
JOINTS = frozenset({"IRJ", "IRJ_SIGNAL", "IRJ_SIGNALS"})
ENDS = frozenset({"NEXT_CP", "BUMPER", "INDUSTRY"})                # a regime boundary is a plain IRJ with a marker each side (ADR 0013 §7.1)
SIGNAL_PINS = frozenset({"SIGNAL", "SIGNAL_A", "SIGNAL_B"})       # a signal joint's pins that carry a mast, never track
PLATES = frozenset({"RULE_290_G", "RULE_290_R"})                   # a POLICY on a mast's SIGNAL net, not on the track (ADR 0013 §5)
BOUNDARY_PINS = ("A", "B")                                         # a boundary track circuit's two track pins (ADR 0013 §10)
STANDS_ON_TRACK = frozenset({"lamp", "contact", "actuator"})      # appliances that state the track they stand on by their one pin (#82)


def on_trackplan(s: Symbol) -> bool:
    return s.role in TRACKPLAN_ROLES


def is_switch(s: Symbol) -> bool:
    return s.role == "APPLIANCE" and s.get("Appliance") == "switch"


def ports_of(s: Symbol) -> tuple[str, ...]:
    """The track ports of a switch, a derail's two (the word ``derail`` in its Style); none for anything else."""
    if not is_switch(s):
        return ()
    return DERAIL_PORTS if "derail" in styles_of(s) else SWITCH_PORTS


def is_boundary(s: Symbol) -> bool:
    """A boundary track circuit: a detector at a joint, on the two nets there (ADR 0013 §10)."""
    return s.role == "APPLIANCE" and s.get("Appliance") == "track_circuit" and s.get("Style") == "boundary"


def circuit_pins(s: Symbol) -> tuple[str, ...]:
    """A track circuit appliance's track pins: a marker's ``TC``, a boundary's ``A`` and ``B``, a virtual circuit's none."""
    if s.role != "APPLIANCE" or s.get("Appliance") != "track_circuit":
        return ()
    return BOUNDARY_PINS if is_boundary(s) else () if s.get("Style") == "virtual" else ("TC",)


# A track symbol's pin, translated to the side it is (ADR 0012 §8; three-maps D15). Any other pin keeps its name.
SIDES = {"IRJ_SIGNAL": {"A": "governed", "B": "approach"}, "NEXT_CP": {"To": "track"}}
POLICY_SIDES = {"To": "track"}


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
    an end or a policy sign but a signal joint's SIGNAL pins, which carry its masts. A milepost is no row and carries
    none."""
    if s.role == "POLICY":
        return s.kind not in PLATES
    if s.role == "TRACK":
        return s.kind != "MILEPOST" and pin not in SIGNAL_PINS
    if is_switch(s):
        return pin in ports_of(s)
    return pin in circuit_pins(s)


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
    name = key_of(s)
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
    on_track = track_nets(sm)
    units = placements(sm)
    for ix in sm.interlockings.values():
        syms = [s for s in sm.source.where("APPLIANCE") + sm.source.where("TRACK") + sm.source.where("POLICY") if units.get(s.ref) == ix.name]
        if syms:
            out.plans[ix.name] = _plan(sm, ix, syms, on_track)
    return out


def track_nets(sm: Seams) -> frozenset[str]:
    """The nets that carry track: every net a track pin of any interlocking's trackplan symbol is on, whatever sheet it
    is drawn on (ADR 0013 §7.1)."""
    src = sm.source
    return frozenset(n.name for s in src.symbols.values() if on_trackplan(s) and unit_of(sm, s)
                     for pin, n in src.pins_of(s.ref).items() if is_track_pin(s, pin))


def unit_of(sm: Seams, s: Symbol) -> Optional[str]:
    """The interlocking a trackplan symbol belongs to (``placements``); None when it belongs to none."""
    return placements(sm).get(s.ref)


def placements(sm: Seams) -> dict[str, Optional[str]]:
    """Every trackplan symbol's interlocking, computed once per drawing (the owner, 2026-11-11). A symbol with Role
    ``TRACK``, ``APPLIANCE`` or ``POLICY`` is placed (1) by its ``CP Name`` when it names an interlocking or one of its
    houses, compared case-insensitively as the desk side compares them, even on another interlocking's sheet (sheet
    scope is a default, the owner 2026-10-28); (2) else by its sheet, the nearest interlocking at or above (ADR 0004
    D12); (3) else, drawn under no interlocking sheet, by its track net: when the nets on its track pins reach the
    track pins of exactly one interlocking's symbols it is that interlocking's (a NextCP on the parent sheet wired to a
    hierarchical net), taken to a fixpoint so a chain of such symbols is placed from its one placed end; (4) else it
    is ``trackplan.unit`` at missing and belongs to none, never dropped in silence."""
    if sm.trackplan_units is not None:
        return sm.trackplan_units
    src = sm.source
    by_cp = {ix.name.casefold(): ix.name for ix in sm.interlockings.values()}
    by_cp.update({cp.casefold(): ix.name for ix in sm.interlockings.values() for cp in ix.houses})
    units: dict[str, Optional[str]] = {}
    pending: list[Symbol] = []
    for s in src.symbols.values():
        if not on_trackplan(s):
            continue
        cp = (s.get("CP Name") or "").strip().casefold()
        hits = [ix for ix in sm.interlockings.values() if s.sheet.startswith(ix.sym.sheet)]
        if cp in by_cp:
            units[s.ref] = by_cp[cp]
        elif hits:
            units[s.ref] = max(hits, key=lambda ix: len(ix.sym.sheet)).name
        else:
            pending.append(s)
    placed_some = True
    while pending and placed_some:
        placed_some = False
        for s in list(pending):
            reached = {units[o.ref] for pin, n in src.pins_of(s.ref).items() if is_track_pin(s, pin)
                       for p in n.others(s.ref) for o in (src.symbols[p.ref],) if on_trackplan(o) and is_track_pin(o, p.pin) and units.get(o.ref)}
            if len(reached) == 1:
                units[s.ref] = reached.pop()
                pending.remove(s)
                placed_some = True
    for s in pending:
        units[s.ref] = None
        sm.report.missing("trackplan.unit", f"a {s.kind or s.get('Appliance') or s.lib_id} belongs to no interlocking: name one with CP Name or draw it "
                          "under the interlocking's sheet", source=loc(s))
    sm.trackplan_units = units
    return units


def _plan(sm: Seams, ix, syms: list[Symbol], track_nets: frozenset[str] = frozenset()) -> Plan:
    src, report = sm.source, sm.report
    plan = Plan(ix.name)
    units: dict[str, Optional[str]] = {}

    def unit(s: Symbol) -> Optional[str]:
        """The interlocking a symbol belongs to (``placements``), cached."""
        if s.ref not in units:
            units[s.ref] = unit_of(sm, s)
        return units[s.ref]

    def net(s: Symbol, pin: str) -> Optional[Net]:
        return src.net_of(s.ref, pin)

    def others(s: Symbol, pin: str) -> list[tuple[Symbol, str]]:
        """Every other pin on the pin's net, whatever sheet it is drawn on (ADR 0013 §7.1: a hierarchical label
        continues the run; pairing comes from the netlist). A symbol under no interlocking is left out, as before."""
        n = net(s, pin)
        return [(src.symbols[p.ref], p.pin) for p in n.others(s.ref) if unit(src.symbols[p.ref])] if n else []

    def pin_refs(s: Symbol, pin: str) -> list[str]:
        """Every other track pin this pin's net reaches, each as ``pin_ref`` names it in its own interlocking, sorted
        (the owner, 2026-10-27; ADR 0013 §7.1). ``others`` leaves out the symbol's own pins; a thing with no name and
        no id is reported where it is read."""
        return sorted({r for o, op in others(s, pin) if (r := pin_ref(unit(o), o, op))})

    consumers: list[dict[str, Any]] = []
    switch_names = {key_of(x) for x in syms if x.role == "APPLIANCE" and x.get("Appliance") == "switch" and "derail" not in styles_of(x)}
    _shorted(syms, src, report, ix.name)

    # ------------------------------------------------------------------ appliances
    for s in syms:
        if s.role != "APPLIANCE":
            continue
        name = key_of(s)
        if not name:
            report.missing("appliance.name", f"{ix.name}: an {s.get('Appliance') or s.lib_id} has no Name", source=loc(s))
            continue
        appliance = s.get("Appliance")
        if ":" in name:                                                   # a reference to another interlocking's appliance
            wired = [p for p in (ports_of(s) or circuit_pins(s)) if net(s, p)]
            if _foreign(name, ix.name) and not wired:
                report.warning("reference.unwritten", f"{ix.name}: the {appliance or s.lib_id} {name} names another interlocking's "
                               "thing but nothing here uses it; not written", source=loc(s))
            elif is_consumer(ix.name, s):
                if not s.uuid:
                    report.missing("track.id", f"{ix.name}: the marker {name} has no KiCad UUID in the export, so its row has no id", source=loc(s))
                consumers.append(_maps({"id": s.uuid or None, "given": given_of(s, keyed=False),
                                        "relations": {"TC": pin_refs(s, "TC"), "indication": _indication(s, name, report)}}))
                if s.uuid:
                    plan.sources[f"track/consumers/{s.uuid}"] = s
            continue
        if name in plan.appliances:
            report.error("appliance.duplicate", f"{ix.name}: two appliances named {name!r} (ADR 0003 D8: names are unique in an interlocking)", source=loc(s))
            continue
        check_milepost(s, report, f"{ix.name}: {appliance} {name}")
        relations: dict[str, Any] = {}
        row: dict[str, Any] = {"given": given_of(s), "relations": relations}
        if appliance == "train_order":                                # a train order board (the owner, 2026-11-03, 2026-11-08)
            relations["station"] = s.get("Station") or None             # its timetable station, a layout entity
            on = sorted(p for p, n in src.pins_of(s.ref).items() if n.name in track_nets)
            if on:
                report.error("train_order.track", f"{ix.name}: train order board {name} has its {', '.join(on)} on the track; "
                             "a train order board has no track pin", source=loc(s))
        elif appliance == "mast":                                     # its Name's atoms, stated (ADR 0003 rules 5 to 7)
            atoms = mast_atoms(name)
            if atoms is None:
                report.missing("mast.name", f"{ix.name}: mast {name}: its Name is not a signal number, a side letter and head letters "
                               "(ADR 0003 rules 5 to 7, 784WBC), so its signal, facing and heads are not stated", source=loc(s))
            else:
                row["given"]["signal"], relations["facing"], row["given"]["heads"] = atoms[0], atoms[1], ",".join(atoms[2])
        elif is_switch(s):
            for p in ports_of(s):
                relations[p] = pin_refs(s, p)
            if "derail" in styles_of(s) and (lead := derail_switch(name, switch_names)):   # a dependent derail states its switch (ADR 0003 D8; the owner, 2026-11-13)
                relations["switch"] = qualify(lead, ix.name)
        elif appliance == "track_circuit":
            for p in circuit_pins(s):                                   # a marker's TC; a boundary's A and B (ADR 0013 §10)
                relations[p] = pin_refs(s, p)
        elif appliance in STANDS_ON_TRACK:                              # one pin: the track it stands on, or its house's MC (#82)
            houses = [cp for cp, h in ix.houses.items() if h.maintainer_call == qualify(name, ix.name)]
            relations["house"] = f"{ix.name}:{houses[0]}" if len(houses) == 1 else None      # its MC wire (D8)
            relations["track"] = _track_at(s, src, track_nets, pin_refs, report, f"{ix.name}: {appliance} {name}")
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
            report.missing("track.id", f"{ix.name}: a {s.kind} has no KiCad UUID in the export, so its row has no id", source=loc(s))
        name = key_of(s)                                                 # an industry end, a ladder marker (issue #145)
        if name:
            if name in named_track or name in plan.appliances:
                report.error("track.duplicate", f"{ix.name}: two symbols named {name!r} (ADR 0003 D8: names are unique in an interlocking)", source=loc(s))
            named_track[name] = s
            row["name"] = qualify(name, ix.name)
        for p in src.pins_of(s.ref):
            if is_track_pin(s, p):
                relations[side_of(s, p)] = pin_refs(s, p)
        if s.kind == "IRJ_SIGNAL":
            relations["mast"] = _mast_on(s, "SIGNAL", others, report, unit)
        elif s.kind == "IRJ_SIGNALS":                                    # a mast on each side (ADR 0013 §6)
            relations["masts"] = {side: m for side in ("A", "B") if (m := _mast_on(s, f"SIGNAL_{side}", others, report, unit))}
        elif s.role == "POLICY" and s.kind in PLATES:                     # a plate on a mast's SIGNAL net (ADR 0013 §5)
            relations["mast"] = _mast_on(s, "To", others, None, unit)      # two masts there are the joint's error already
        row = _maps(row)
        kind = "policies" if s.role == "POLICY" else "joints" if s.kind in JOINTS else "ends"
        {"policies": policies, "joints": joints, "ends": ends}[kind].append(row)
        if s.uuid:
            plan.sources[f"track/{kind}/{s.uuid}"] = s
        if s.role == "TRACK" and s.kind not in JOINTS | ENDS:
            report.info("track.kind", f"{ix.name}: TRACK Kind {s.kind!r} is not one the KiCad importer reads; written with the ends", source=loc(s))
    plan.track = {k: v for k, v in {"joints": joints, "ends": ends, "policies": policies, "consumers": consumers}.items() if v}
    return plan


def _track_at(s: Symbol, src, track_nets: frozenset[str], pin_refs, report, what: str) -> list[str]:
    """The track a lamp, contact or actuator stands on: every track pin on the net its pin is wired to, named as a track
    side names them (``pin_refs``). Track that names no circuit is track like any other. Its pin on a house's MC pin is
    its maintainer-call wire, stated as ``relations.house``. Its pin on any other wire is the import error
    ``appliance.track_pin``. Not wired, it states none and stands at its Milepost and CP Name."""
    refs: set[str] = set()
    for pin, n in src.pins_of(s.ref).items():
        if n.name in track_nets:
            refs.update(pin_refs(s, pin))
        elif not any(p.pin == "MC" and src.symbols[p.ref].role == "STRUCTURE" and src.symbols[p.ref].kind == "CONTROL_POINT" for p in n.others(s.ref)):
            report.error("appliance.track_pin", f"{what}'s {pin} pin is on a wire that is not track; a lamp, contact or actuator is "
                         "wired to the track it stands on, to its house's MC pin, or not at all", source=loc(s))
    return sorted(refs)


def _mast_on(joint: Symbol, pin: str, others, report, unit) -> Optional[str]:
    """The one mast on a symbol's pin (a signal joint's SIGNAL pin, a plate's To), by its own interlocking's qualified
    name (``unit``; ADR 0013 §7.1 reads the net across sheets); two there are an error (one pin, one mast) where a
    report is given, none is absent."""
    masts = [o for o, p in others(joint, pin) if o.get("Appliance") == "mast" and key_of(o)]
    if len(masts) > 1 and report is not None:
        report.error("joint.masts", f"{unit(joint)}: one signal joint carries masts {', '.join(sorted(key_of(m) for m in masts))} on its {pin} pin",
                     source=loc(joint))
    return qualify(key_of(masts[0]), unit(masts[0])) if len(masts) == 1 else None


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
    report.info("consumer.legacy_token", f"the consumer {name} states no Indication; read from its Name as {token}", source=loc(s))
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
                report.error("track.shorted", f"{interlocking}: {s.get('Appliance') or s.kind or s.lib_id} {key_of(s) or 'with no name'} has "
                             f"{' and '.join(sorted(sides))} on one wire with nothing between; insulated joints belong there", source=loc(s))


def _foreign(name: str, interlocking: str) -> bool:
    """A name qualified with another interlocking's scope."""
    return ":" in name and name.partition(":")[0] != interlocking


def _maps(row: dict[str, Any]) -> dict[str, Any]:
    """A row with its empty values and empty maps left out: absent is absent, but a token field stated empty stays
    (ADR 0008 §4.7)."""
    out: dict[str, Any] = {}
    for k, v in row.items():
        if isinstance(v, dict) and k in ("given", "relations", "derived", "circuits"):
            v = _maps(v)
        if v not in (None, "", [], {}) or (v == "" and token_field(k)):
            out[k] = v
    return out
