"""The explicit-seams model (ADR 0009, ADR 0012 §4): what the drawing states, resolved by wire, and checked.

Every relation of the §3.12 table has one form: a wire from a pin named for the relation (``Processor``,
``Transport``, ``Codeline``, ``IOBus``, ``Column``). The implicit fallbacks (the one processor on the sheet, the
code line in the folder, the ``Processor`` and ``Transport`` fields, the one CMRInet Node on the sheet) retired with
ADR 0012 §4: a relation with no wire is ``missing``, the tutorial prompt (ADR 0009 §3.10), not an error: absence is
information (ADR 0008 §4.7). A field that once served as a fallback stays in ``given``, read by nothing.

Every entity keeps what was stated as it was stated (ADR 0011 §2): ``given`` is every field less KiCad's
housekeeping, ``Role``, the library's ``Pin.*`` contract and the key field (``given_of``); a wire becomes a named
relation. Identity is the key attribute of each symbol, read only through ``key_of`` (``Name`` on most; ``key_field``
names the others); ``Value`` is drawing and is never read (ADR 0009 §3.10). A symbol without its key has no name and
is reported.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from typing import Optional

from tools.layout_model.reference import ENCODING_OF_IC, TRANSPORT_OF_ENCODING
from tools.layout_model.report import Report

from .source import Net, Source, Symbol, in_scope

MACRO = re.compile(r"<([A-Z_]+):([A-Z_]*):([\w .]+)>")
# KiCad's own housekeeping (ADR 0011 §2), and Role, which only picks the collection (three-maps D1): never in given.
HOUSEKEEPING = frozenset({"Reference", "Value", "Footprint", "Datasheet", "Description", "Sheetname", "Sheetfile", "Role"})
PIN_TOKENS = ("Control.", "Indication.")                              # per-pin tokens: Control.<pin>, Indication.<pin>


def token_field(k: str) -> bool:
    """A token field, ``Indication`` or a per-pin ``Control.<pin>``/``Indication.<pin>``: stated even when empty, where
    the empty field is the statement that there is no token and an absent one is not done yet (ADR 0008 §4.7)."""
    return k == "Indication" or k.startswith(PIN_TOKENS)


def loc(s: Symbol, pin: Optional[str] = None) -> str:
    """Where a symbol is in the drawing, in the drawing's own terms and never by KiCad reference (the owner, 2026-11-13:
    nothing locates a thing by REFDES): its sheet, then ``library:symbol(Name)``, the Name its key attribute
    (``key_of``: Name, CP Name, Column, Address; empty for a thing with none, an anonymous head or a track row, which
    the model knows by its row id), and ``.pin`` where one pin is meant:
    ``/South-cTc/Sargent/Railroad-Trackplan:Switch_Powered(836).R``. An import diagnostic's location is this, in
    ``Diag.source`` (ADR 0012 §3.3); ``where`` is for a model path."""
    return f"{s.sheet}{s.lib_id}({key_of(s)})" + (f".{pin}" if pin else "")


# ---------------------------------------------------------------- entities

@dataclass
class Processor:
    name: str
    given: dict[str, str] = field(default_factory=dict)              # merged over its placements
    syms: list[Symbol] = field(default_factory=list)
    drivers: dict[str, "Driver"] = field(default_factory=dict)        # by address on its bus


@dataclass
class Transport:
    name: str
    kind: str
    given: dict[str, str] = field(default_factory=dict)              # merged over its placements
    anchors: set[str] = field(default_factory=set)                    # processor names, one per placed instance
    instances: dict[str, Symbol] = field(default_factory=dict)        # ref -> placed symbol
    nodes: dict[str, "Node"] = field(default_factory=dict)            # by UA


@dataclass
class Encoding:
    name: str
    kind: str
    role: str                                                        # CODELINE_ENCODING or IO_ENCODING
    sym: Symbol
    given: dict[str, str] = field(default_factory=dict)
    transport: Optional[str] = None
    processor: Optional[str] = None                                   # the processor anchoring the transport instance it rides
    codeline_net: Optional[Net] = None


@dataclass
class Node:
    ua: str
    sym: Symbol
    given: dict[str, str] = field(default_factory=dict)
    transport: Optional[str] = None
    input_bytes: Optional[int] = None
    output_bytes: Optional[int] = None
    bits: dict[str, "Driver"] = field(default_factory=dict)           # by IB.n / OB.n


@dataclass
class Driver:
    sym: Symbol
    ic: str
    address: str                                                     # on its bus: 0x20, D2, IB.3
    owner: Optional[str] = None                                       # route owner: a processor name or transport/UA
    given: dict[str, str] = field(default_factory=dict)
    kind: str = ""                                                    # an encoded driver's object class: TURNOUT, SENSOR, SIGNALMAST, LIGHT
    syms: list[Symbol] = field(default_factory=list)                  # every symbol that draws it (a JMRI Turnout: command and feedback, the one merge)


@dataclass
class House:
    cp_name: str
    sym: Symbol
    given: dict[str, str] = field(default_factory=dict)
    interlocking: Optional[str] = None
    maintainer_call: Optional[str] = None
    codeline: Optional[str] = None


@dataclass
class Interlocking:
    name: str
    sym: Symbol
    given: dict[str, str] = field(default_factory=dict)
    processor: Optional[str] = None
    codeline: Optional[str] = None
    houses: dict[str, House] = field(default_factory=dict)
    devices: list["Device"] = field(default_factory=list)


@dataclass
class Station:
    """A timetable station (the owner, 2026-11-03): a place on the line a train order signal, a house or a milepost
    belongs to, named by its Name and stated with its Milepost. Not a code line station (``reference.STATION``: a
    house or an interlocking that is addressed on a code line): the two words name different things."""
    name: str
    sym: Symbol
    given: dict[str, str] = field(default_factory=dict)
    interlocking: Optional[str] = None                                # relation: the interlocking whose sheet it is drawn under


@dataclass
class Column:
    number: str
    sym: Symbol
    given: dict[str, str] = field(default_factory=dict)
    folder: Optional[str] = None                                      # stated by the sheet hierarchy alone (three-maps D6)
    sheet_folder: Optional[str] = None                                # the interlocking whose sheet it is drawn under
    office_unit: Optional[str] = None


@dataclass
class OfficeUnit:
    name: str
    sym: Symbol
    given: dict[str, str] = field(default_factory=dict)
    processor: Optional[str] = None
    columns: dict[str, Column] = field(default_factory=dict)
    devices: list["Device"] = field(default_factory=list)


@dataclass
class Binding:
    """A device pin's wire to a driver pin, with the facts the drawing states about it: the driver pin's number on its
    symbol, the direction from the device pin's electrical type, and the sense, asserted low or high."""
    function: str
    route: str
    number: str = ""                                                  # the driver pin's number, as its symbol states it
    direction: Optional[str] = None                                   # "output": the logic drives the device pin; "input": it reads it
    sense: str = "low"                                                # the asserted level: the pin's drawn mark, flipped by Invert


# A device pin's KiCad electrical type, as the direction of its binding from the logic's side (ADR 0017 decision 3):
# a pin the device takes in is driven by the logic; a pin it puts out is read. Drivers have no direction of their own
# (the owner, 2026-10-07): only the device pin's type is read. Any other type states none.
DIRECTION_OF_PINTYPE = {"input": "output", "output": "input", "open_collector": "input", "open_emitter": "input"}


@dataclass
class Device:
    sym: Symbol
    appliance: str
    styles: list[str]
    given: dict[str, str] = field(default_factory=dict)              # its Name included: a row has no identity
    column: Optional[str] = None                                      # relation: the OfficeUnit-qualified column
    interlocking: Optional[str] = None                                # relation: the folder, for a device in no column (D6)
    mast: Optional[str] = None                                        # relation: a head's or a train order lever's IND wire to its field mast device
    face: Optional[str] = None                                        # relation: the train order mast pin that wire reaches, the face (the owner, 2026-11-08)
    position: Optional[str] = None                                    # relation: the signal mast pin that wire reaches, the head's position A, B, C (#80)
    bindings: list[Binding] = field(default_factory=list)


@dataclass
class Seams:
    source: Source
    report: Report
    railroad: Optional[str] = None                                    # the layout's name
    railroad_given: dict[str, str] = field(default_factory=dict)
    processors: dict[str, Processor] = field(default_factory=dict)
    transports: dict[str, Transport] = field(default_factory=dict)
    encodings: dict[str, Encoding] = field(default_factory=dict)
    interlockings: dict[str, Interlocking] = field(default_factory=dict)
    stations: dict[str, Station] = field(default_factory=dict)        # timetable stations, layout-level, by Name
    office_units: dict[str, OfficeUnit] = field(default_factory=dict)
    trackplan: Optional["object"] = None                             # trackplan.Trackplan: appliances and track as drawn
    trackplan_units: Optional[dict[str, Optional[str]]] = None        # trackplan.placements: each trackplan symbol's interlocking
    trackplan_units: Optional[dict[str, Optional[str]]] = None        # trackplan.placements: each trackplan symbol's interlocking
    derived: bool = False                                             # the reference derivation's diagnostics are in report


# ---------------------------------------------------------------- helpers

# The key attribute of each kind of symbol, by Role and Kind (a Kind of None covers the Role): where a symbol keeps its
# identity is decided here and nowhere else (the owner, 2026-10-26). Every other symbol's key is ``Name``. A CMRInet
# Node's and a driver's key is its ``Address``, unique within its owner (three-maps D11); a bit's ``IB.n`` and an
# encoded driver's ``Kind.served`` are computed keys, so those symbols have no key field.
KEYS = {("STRUCTURE", "CONTROL_POINT"): "CP Name", ("STRUCTURE", "STATION"): "Name", ("COLUMN", None): "Column",
        ("IODRIVER", None): "Address"}

# A CMRInet driver states what it is in ``Kind`` (the owner, 2026-10-30): ``NODE``, keyed by its Address (its UA), or
# one of its bits, ``IB`` or ``OB``, whose Kind is its direction. ``NodeType`` is an ordinary node setting.
CMRI_BIT_KINDS = ("IB", "OB")


def is_cmri_node(s: Symbol) -> bool:
    return s.role == "IODRIVER" and s.get("IC") == "CMRI" and s.kind == "NODE"


def is_cmri_bit(s: Symbol) -> bool:
    return s.role == "IODRIVER" and s.get("IC") == "CMRI" and s.kind in CMRI_BIT_KINDS


def key_field(s: Symbol) -> Optional[str]:
    if s.role == "IODRIVER" and (is_cmri_bit(s) or s.get("IC") in ENCODING_OF_IC):
        return None
    return KEYS.get((s.role, s.kind)) or KEYS.get((s.role, None)) or "Name"


def key_of(s: Symbol, report: Optional[Report] = None) -> str:
    """The symbol's identity, from its key attribute, never ``Value`` (ADR 0009 §3.10; the owner, 2026-10-25). Empty or
    KiCad's ``~`` is no name. With a report, a symbol whose library lacks the attribute is reported ``missing``: the fix
    is the attribute in the library and on its instances. Without one the name is optional, as on an end of track."""
    k = key_field(s)
    if k is None:
        return ""
    if k in s.fields:                                                 # stated, even empty: KiCad resolves ${Value} of "~" to nothing
        v = s.get(k)
        return "" if v == "~" else v
    if report is not None:
        report.missing(f"identity.{k.replace(' ', '_').lower()}", f"{s.lib_id} has no {k} field, so it has no name; Value is never read", source=loc(s))
    return ""


def device_name(s: Symbol, report: Report) -> Optional[str]:
    """A device's own name, its appliance's (Name = ${Value} since 2026-10-24)."""
    return key_of(s, report) or None


def check_milepost(s: Symbol, report: Report, what: str) -> None:
    """The ``Milepost`` a symbol states is numeric text: optional, general geographic context (the owner, 2026-10-26).
    It stays in ``given`` as drawn; a reader that wants a number parses it (ADR 0011 §2)."""
    if s.get("Milepost"):
        try:
            float(s.get("Milepost"))
        except ValueError:
            report.error("milepost.number", f"{what}: Milepost {s.get('Milepost')!r} is not a number", source=loc(s))


def given_of(s: Symbol, keyed: bool = True) -> dict[str, str]:
    """Every field the person stated, keyed as drawn, as KiCad states it (ADR 0011 §2): less KiCad's housekeeping,
    ``Role`` (D1), the library's ``Pin.*`` contract (D2) and, for a keyed entity, its key field. An empty field or
    KiCad's ``~`` is not stated (D21), except a token field (``token_field``) on any symbol: there the empty field is the
    statement that there is no token (the owner, 2026-10-28 and 10-29), written as "". A row without
    identity (a device) keeps its ``Name`` (``keyed=False``)."""
    key = key_field(s) if keyed else None
    out = {}
    for k, v in s.fields.items():
        if k in HOUSEKEEPING or k == key or k.startswith(("ki_", "Pin.")):
            continue
        if v.strip() not in ("", "~"):
            out[k] = v
        elif token_field(k):
            out[k] = ""
    return out


def merge_given(have: dict[str, str], s: Symbol, what: str, report: Report) -> None:
    """One entity drawn several times states one set of facts: each placement's ``given`` merged, a conflict an error."""
    for k, v in given_of(s).items():
        if k in have and have[k] != v:
            report.error("entity.conflict", f"{what}: {k} {have[k]!r} on one placement, {v!r} on another", source=loc(s))
            continue
        have[k] = v


def styles_of(s: Symbol) -> list[str]:
    return sorted(x.strip() for x in s.get("Style").split(",") if x.strip())


def qualify(name: str, scope: str) -> str:
    """A reference is always the qualified name (ADR 0008 §4.5); a token already qualified keeps its scope."""
    return name if ":" in name else f"{scope}:{name}"


def base(pin: str) -> str:
    return pin[2:-1] if pin.startswith("~{") and pin.endswith("}") else pin


def one(items: list, what: str, at: str, report: Report, code: str) -> Optional[object]:
    """Exactly one, or report and None: the rule every scope lookup shares."""
    if len(items) == 1:
        return items[0]
    if len(items) > 1:
        report.error(code, f"{len(items)} {what} where one is expected", source=at)
    return None


def stated(value, what: str, at: str, report: Report, code: str):
    """A relation has one form, its wire (ADR 0012 §4): the value it names, or ``missing`` when none is drawn."""
    if value is None:
        report.missing(f"{code}.missing", f"{what}: no wire states it", source=at)
    return value


def expand_macros(source: Source, report: Report) -> None:
    """``<ROLE:KIND:Field>`` -> that field of the one symbol with that Role and Kind in scope (owner's ruling 2026-10-23)."""
    for s in list(source.symbols.values()):
        changed = {}
        for k, v in s.fields.items():
            if not MACRO.search(v):
                continue

            def sub(m: re.Match) -> str:
                role, kind, fld = m.groups()
                cands = [c for c in source.where(role, kind) if in_scope(c.sheet, s.sheet)]
                c = one(cands, f"symbols with Role {role} Kind {kind!r} in scope", loc(s), report, "macro.scope")
                if c is None:
                    if not cands:
                        report.error("macro.scope", f"no symbol with Role {role} Kind {kind!r} in scope for {m.group(0)}", source=loc(s))
                    return m.group(0)
                if fld not in c.fields:
                    report.error("macro.field", f"{c.lib_id} has no field {fld} for {m.group(0)}", source=loc(s))
                    return m.group(0)
                return c.fields[fld]
            changed[k] = MACRO.sub(sub, v)
        if changed:
            source.symbols[s.ref] = replace(s, fields={**s.fields, **changed})


# ---------------------------------------------------------------- resolution

def resolve(source: Source) -> Seams:
    report = Report()
    expand_macros(source, report)
    seams = Seams(source, report)
    _railroad(seams)
    _processors(seams)
    _office_units(seams)
    _transports(seams)
    _encodings(seams)
    _interlockings(seams)
    _stations(seams)
    _houses(seams)
    _nodes(seams)
    _drivers(seams)
    _columns(seams)
    _devices(seams)
    from . import trackplan                                           # it builds on the seam helpers
    seams.trackplan = trackplan.read(seams)
    return seams


def _railroad(sm: Seams) -> None:
    syms = sm.source.where("STRUCTURE", "RAILROAD")
    s = one(syms, "Railroad symbols", "", sm.report, "railroad.count")
    if s is None:
        if not syms:
            sm.report.missing("railroad.missing", "no Railroad symbol: the layout's name, railroad, region, era and rulebook are not stated")
        return
    sm.railroad = key_of(s) or None
    sm.railroad_given = given_of(s)
    if not key_of(s):
        sm.report.missing("railroad.name", "the Railroad symbol has no Name", source=loc(s))


def _processors(sm: Seams) -> None:
    for s in sm.source.where("STRUCTURE", "PROCESSOR"):
        name = key_of(s, sm.report)
        if not name:
            sm.report.missing("entity.name", "a processor has no Name; it is not written", source=loc(s))
            continue
        p = sm.processors.setdefault(name, Processor(name))
        p.syms.append(s)
        merge_given(p.given, s, f"processor {name}", sm.report)
    for p in sm.processors.values():
        if not p.given.get("Board"):
            sm.report.missing("processor.board", f"processor {p.name}: no Board", source=loc(p.syms[0]))


def _anchor_of(sm: Seams, s: Symbol) -> Optional[str]:
    """The processor on a symbol's Processor net (explicit)."""
    net = sm.source.net_of(s.ref, "Processor")
    if not net:
        return None
    procs = [sm.source.symbols[p.ref] for p in net.others(s.ref) if sm.source.symbols[p.ref].kind == "PROCESSOR" and p.pin == "Processor"]
    p = one(procs, "processors on one Processor net", loc(s), sm.report, "processor.net")
    return key_of(p, sm.report) if p else None


def _transports(sm: Seams) -> None:
    for s in sm.source.where("TRANSPORT"):
        name = key_of(s, sm.report)
        if not name:
            sm.report.missing("entity.name", "a transport has no Name; it is not written", source=loc(s))
            continue
        t = sm.transports.setdefault(name, Transport(name, s.kind))
        if t.kind != s.kind:
            sm.report.error("entity.conflict", f"transport {name}: Kind {t.kind} and {s.kind}", source=loc(s))
        merge_given(t.given, s, f"transport {name}", sm.report)
        t.instances[s.ref] = s
        anchor = stated(_anchor_of(sm, s), f"transport {name} anchored on", loc(s), sm.report, "transport.anchor")
        if anchor:
            if anchor not in sm.processors:
                sm.report.error("transport.anchor", f"transport {name}: anchor {anchor!r} is not a processor", source=loc(s))
            t.anchors.add(anchor)


def _transport_on_net(sm: Seams, s: Symbol) -> Optional[tuple[str, Symbol]]:
    net = sm.source.net_of(s.ref, "Transport")
    if not net:
        return None
    ts = [sm.source.symbols[p.ref] for p in net.others(s.ref) if sm.source.symbols[p.ref].role == "TRANSPORT" and p.pin == "Transport"]
    t = one(ts, "transports on one Transport net", loc(s), sm.report, "transport.net")
    return (key_of(t, sm.report), t) if t else None


def _encodings(sm: Seams) -> None:
    for s in sm.source.where("CODELINE_ENCODING") + sm.source.where("IO_ENCODING"):
        name = key_of(s, sm.report)
        if not name:
            sm.report.missing("entity.name", "a encoding has no Name; it is not written", source=loc(s))
            continue
        if name in sm.encodings:
            sm.report.error("entity.duplicate", f"two encodings named {name!r}", source=loc(s))
            continue
        e = Encoding(name, s.kind, s.role, s, given_of(s))
        hit = _transport_on_net(sm, s)
        want_kind = TRANSPORT_OF_ENCODING.get(s.kind)
        e.transport = stated(hit[0] if hit else None, f"encoding {name} rides", loc(s), sm.report, "encoding.transport")
        if e.transport:
            t = sm.transports[e.transport]
            if want_kind and t.kind != want_kind:
                sm.report.error("encoding.kind", f"encoding {name} ({s.kind}) rides {t.name} ({t.kind}); {s.kind} pairs with {want_kind}", source=loc(s))
            # the instance it rides is the transport symbol on its net; that instance's anchor is the encoding's processor (D7)
            e.processor = _anchor_of(sm, hit[1])
            if e.processor is None:
                sm.report.missing("encoding.processor", f"encoding {name}: the transport instance it rides has no anchor", source=loc(s))
        if s.role == "CODELINE_ENCODING":
            e.codeline_net = sm.source.net_of(s.ref, "Codeline")
        sm.encodings[name] = e


def _codeline_of(sm: Seams, s: Symbol) -> Optional[str]:
    net = sm.source.net_of(s.ref, "Codeline")
    if not net:
        return None
    encs = [e.name for e in sm.encodings.values() if e.codeline_net is not None and e.codeline_net.name == net.name]
    return encs[0] if len(encs) == 1 else (one(encs, "code lines on one Codeline net", loc(s), sm.report, "codeline.net") if encs else None)


def _interlockings(sm: Seams) -> None:
    for s in sm.source.where("STRUCTURE", "INTERLOCKING"):
        name = key_of(s, sm.report)
        if not name:
            sm.report.missing("interlocking.name", "an Interlocking symbol has no Name", source=loc(s))
            continue
        if name in sm.interlockings:
            sm.report.error("entity.duplicate", f"two interlockings named {name!r}", source=loc(s))
            continue
        ix = Interlocking(name, s, given_of(s))
        ix.processor = stated(_anchor_of(sm, s), f"FieldUnit {name} runs on", loc(s), sm.report, "unit.processor")
        if ix.processor and ix.processor not in sm.processors:
            sm.report.error("unit.processor", f"FieldUnit {name}: {ix.processor!r} is not a processor", source=loc(s))
        ix.codeline = stated(_codeline_of(sm, s), f"FieldUnit {name} on its line", loc(s), sm.report, "unit.codeline")
        sm.interlockings[name] = ix


def _unit_of_sheet(sm: Seams, sheet: str) -> Optional[Interlocking]:
    """The interlocking whose sheet is this sheet or an ancestor of it (the folder)."""
    hits = [ix for ix in sm.interlockings.values() if in_scope(ix.sym.sheet, sheet)]
    return max(hits, key=lambda ix: len(ix.sym.sheet)) if hits else None


def _stations(sm: Seams) -> None:
    """A timetable station (STRUCTURE, Kind STATION; the owner, 2026-11-03) is a layout entity keyed by its Name: its
    Milepost and every other stated field are ``given``, and the interlocking whose sheet it is drawn under is
    ``relations.interlocking`` (ADR 0004 D12: a symbol belongs to the INTERLOCKING on its sheet or the nearest ancestor
    sheet that has one), absent for a station drawn under none. Two stations with one Name are an error: a station is
    one place on the line. It is not a code line station (``reference.STATION``)."""
    for s in sm.source.where("STRUCTURE", "STATION"):
        name = key_of(s, sm.report)
        if not name:
            sm.report.missing("entity.name", "a station has no Name; it is not written", source=loc(s))
            continue
        if name.casefold() in {n.casefold() for n in sm.stations}:
            sm.report.error("station.duplicate", f"two stations named {name!r}; a timetable station is one place on the line", source=loc(s))
            continue
        st = Station(name, s, given_of(s))
        check_milepost(s, sm.report, f"station {name}")
        ix = _unit_of_sheet(sm, s.sheet)
        st.interlocking = ix.name if ix else None
        sm.stations[name] = st


def _houses(sm: Seams) -> None:
    for s in sm.source.where("STRUCTURE", "CONTROL_POINT"):
        cp = key_of(s, sm.report)
        if not cp:
            sm.report.missing("house.cp_name", "a House has no CP Name", source=loc(s))
            continue
        h = House(cp, s, given_of(s))
        ix = _unit_of_sheet(sm, s.sheet)
        if ix is None:
            sm.report.error("house.interlocking", f"house {cp}: no Interlocking on its sheet or above", source=loc(s))
            continue
        h.interlocking = ix.name
        check_milepost(s, sm.report, f"house {cp}")
        line = _codeline_of(sm, s)                                     # stated only where wired; never required of a house
        h.codeline = line
        if line and ix.codeline and line != ix.codeline:
            sm.report.error("house.codeline", f"house {cp} sits on {line!r} but its interlocking {ix.name} is on {ix.codeline!r}", source=loc(s))
        mc = sm.source.net_of(s.ref, "MC")
        if mc:
            calls = [sm.source.symbols[p.ref] for p in mc.others(s.ref) if sm.source.symbols[p.ref].role == "APPLIANCE"]
            c = one(calls, "maintainer calls on one MC net", loc(s), sm.report, "house.mc")
            if c is not None:
                h.maintainer_call = qualify(key_of(c, sm.report), ix.name)
        if cp in ix.houses:
            sm.report.error("entity.duplicate", f"two houses named {cp!r} in {ix.name}", source=loc(s))
        ix.houses[cp] = h


def _office_units(sm: Seams) -> None:
    for s in sm.source.where("OFFICE_UNIT"):
        name = key_of(s, sm.report)
        if not name:
            sm.report.missing("entity.name", "a office unit has no Name; it is not written", source=loc(s))
            continue
        if name in sm.office_units:
            sm.report.error("entity.duplicate", f"two office units named {name!r}", source=loc(s))
            continue
        ou = OfficeUnit(name, s, given_of(s))
        ou.processor = stated(_anchor_of(sm, s), f"OfficeUnit {name} runs on", loc(s), sm.report, "office.processor")
        if ou.processor and ou.processor not in sm.processors:
            sm.report.error("office.processor", f"OfficeUnit {name}: {ou.processor!r} is not a processor", source=loc(s))
        sm.office_units[name] = ou


def _bus_owner(sm: Seams, s: Symbol) -> Optional[str]:
    """The owner of the IOBus net a driver's IOBus pin lands on: a processor name, or transport/UA for a CMRInet Node."""
    net = sm.source.net_of(s.ref, "IOBus")
    if not net:
        return None
    owners = []
    for p in net.others(s.ref):
        o = sm.source.symbols[p.ref]
        if p.pin != "IOBus":
            continue
        if o.kind == "PROCESSOR":
            owners.append(key_of(o, sm.report))
        elif is_cmri_node(o):
            t = next((tn for tn, t in sm.transports.items() if o.get("Address") in t.nodes and t.nodes[o.get("Address")].sym.ref == o.ref), None)
            owners.append(f"{t}/{o.get('Address')}" if t else None)
    owners = [o for o in owners if o]
    return owners[0] if len(owners) == 1 else (one(owners, "bus providers on one IOBus net", loc(s), sm.report, "bus.net") if owners else None)


def _nodes(sm: Seams) -> None:
    for s in sm.source.where("IODRIVER"):
        if not is_cmri_node(s):
            continue
        ua = s.get("Address")
        if not ua:
            sm.report.missing("node.address", "a CMRInet Node has no Address (its UA)", source=loc(s))
            continue
        n = Node(ua, s, given_of(s))
        for attr, fld in (("input_bytes", "InputBytes"), ("output_bytes", "OutputBytes")):
            if s.get(fld):
                try:
                    setattr(n, attr, int(s.get(fld)))
                except ValueError:
                    sm.report.error("node.bytes.number", f"CMRInet Node {ua}: {fld} {s.get(fld)!r} is not a number", source=loc(s))
            else:
                sm.report.missing("node.bytes", f"CMRInet Node {ua}: no {fld}", source=loc(s))
        hit = _transport_on_net(sm, s)
        n.transport = stated(hit[0] if hit else None, f"CMRInet Node {ua} on its line", loc(s), sm.report, "node.transport")
        if n.transport:
            t = sm.transports[n.transport]
            if ua in t.nodes:                                          # one entity on several sheets (ADR 0009 §3.9)
                have = t.nodes[ua]
                merge_given(have.given, s, f"CMRInet Node {ua} on {t.name}", sm.report)
                for attr in ("input_bytes", "output_bytes"):
                    if getattr(have, attr) is None:
                        setattr(have, attr, getattr(n, attr))
                continue
            t.nodes[ua] = n


def _drivers(sm: Seams) -> None:
    for s in sm.source.where("IODRIVER"):
        if is_cmri_node(s):
            continue
        ic = s.get("IC")
        if ic == "CMRI" and not is_cmri_bit(s):
            sm.report.missing("driver.kind", f"CMRInet driver {s.value!r}: {f'Kind {s.kind!r}' if s.kind else 'no Kind'}; NODE, IB or OB says whether it is the node or one of its bits", source=loc(s))
            continue
        is_bit = is_cmri_bit(s)
        if is_bit:
            if not s.get("Bit"):
                sm.report.missing("bit.number", f"CMRInet {s.kind} bit {s.value!r}: no Bit; it has no key", source=loc(s))
                continue
            address = f"{s.kind}.{s.get('Bit')}"                       # its direction is its Kind, never the pin's type
        else:
            address = s.get("Address")
            if ic in ENCODING_OF_IC:
                address = _encoded_address(sm, s, address)
        d = Driver(s, ic, address, given=given_of(s), kind=s.kind, syms=[s])
        at = loc(s)
        d.owner = stated(_bus_owner(sm, s), f"driver {ic} {address or s.value!r} on a bus", at, sm.report, "driver.bus")
        if not ic:
            sm.report.missing("driver.ic", "a driver has no IC", source=at)
        if d.owner is None:
            continue
        if "/" in d.owner:
            tn, ua = d.owner.split("/", 1)
            node = sm.transports[tn].nodes[ua]
            if not is_bit:
                sm.report.error("bus.kind", f"driver {ic} {address!r} sits on CMRInet Node {ua}'s bus; only its bits do", source=at)
                continue
            if address in node.bits:
                sm.report.error("bit.duplicate", f"CMRInet Node {ua}: two bits at {address}", source=at)
            node.bits[address] = d
        else:
            if is_bit:
                sm.report.error("bus.kind", f"CMRInet bit {address} sits on processor {d.owner}'s bus; a bit sits on a node's", source=at)
                continue
            p = sm.processors[d.owner]
            if not address:
                if ic not in ENCODING_OF_IC:                           # an encoded driver without one was reported by _encoded_address
                    sm.report.missing("driver.address", f"driver {ic} ({s.lib_id.split(':')[1]}) on {p.name} has no Address; its bindings are absent", source=at)
                continue
            if address in p.drivers:
                first = p.drivers[address]
                if _one_turnout(sm, first, d):                        # one JMRI Turnout drawn twice: its command and its feedback (the owner, 2026-11-10)
                    first.syms.append(s)
                    if first.given != d.given:
                        sm.report.error("entity.conflict", f"driver {address} on {p.name}: its symbols state different fields", source=at)
                    continue
                sm.report.error("driver.duplicate", f"processor {p.name}: two drivers at {address}; two objects of one key, which is never a merge "
                                "unless they are a Turnout's command and feedback", source=at)
            p.drivers[address] = d
    for t in sm.transports.values():
        for n in t.nodes.values():
            for prefix, declared in (("IB", n.input_bytes), ("OB", n.output_bytes)):
                used = [int(a.split(".")[1]) for a in n.bits if a.startswith(prefix)]
                if used and declared is not None and max(used) > declared * 8:
                    sm.report.error("node.bytes.range", f"CMRInet Node {n.ua}: {prefix} bit {max(used)} used but {declared} byte(s) declared", source=loc(n.sym))


def _one_turnout(sm: Seams, first: Driver, second: Driver) -> bool:
    """Two symbols at one key are one JMRI object only when they are a Turnout's command and its feedback (the owner,
    2026-11-10): both encoded, Kind ``TURNOUT``, and their wires reach no common device pin (the command drives M, the
    feedback reads N and R). Anything else at one key is ``driver.duplicate``."""
    if first.ic not in ENCODING_OF_IC or second.ic != first.ic or first.kind != "TURNOUT" or second.kind != "TURNOUT":
        return False
    touched = [set().union(*(set(_served(sm, x, quiet=True)[2]) for x in d.syms)) for d in (first, second)]
    return not (touched[0] & touched[1])


def _anonymous(o: Symbol) -> bool:
    """A nameless device that serves under its mast: a head, or a train order lever (the owner, 2026-11-04, 2026-11-08)."""
    return o.get("Appliance") == "head" or (o.get("Appliance") == "lever" and "train_order" in styles_of(o))


def _anonymous_served(sm: Seams, o: Symbol) -> Optional[str]:
    """The name a nameless head or train order lever serves under: its mast's name and the mast pin its IND wire reaches,
    ``Gilroy.E`` (the owner, 2026-11-10: the key carries the facts the wires state; #80's head position = mast pin,
    applied to the lever too). One mast pin reached, or nothing: two is the device's own finding (``_mast_on_ind``)."""
    if not _anonymous(o):
        return None
    ind = sm.source.net_of(o.ref, "IND")
    under = {(key_of(sm.source.symbols[p.ref]), base(p.pin)) for p in ind.others(o.ref)
             if sm.source.symbols[p.ref].role == "DEVICE" and sm.source.symbols[p.ref].get("Appliance") in ("mast", "train_order_mast")} if ind else set()
    if len(under) != 1:
        return None
    mast, pin = next(iter(under))
    return f"{mast}.{pin}" if mast else None


def _function_pins(o: Symbol) -> set[str]:
    """A device's function pins: the ones its library's ``Pin.*`` contract declares, less the IND that places a nameless
    head or lever under its mast (membership, not a function). A symbol with no contract has none: a wired pin the
    contract does not declare is not a function (ADR 0012 §4, no fallbacks)."""
    declared = {k[4:] for k in o.fields if k.startswith("Pin.")}
    if _anonymous(o):
        declared.discard("IND")
    return declared


def _served(sm: Seams, s: Symbol, quiet: bool = False) -> tuple[Optional[str], Optional[Symbol], dict[str, str]]:
    """The one device wired to a driver's function pins: the name it serves under (a nameless head or lever under its
    mast pin, ``_anonymous_served``), the device, and the device pins the driver's wires reach, each with the driver
    pin that reaches it (base names, without the overline). Two devices is ``driver.serves.two``; none is
    (None, None, {})."""
    hits: dict[str, tuple[Symbol, dict[str, str]]] = {}
    for pin, net in sm.source.pins_of(s.ref).items():
        if pin == "IOBus":
            continue
        for p in net.others(s.ref):
            o = sm.source.symbols[p.ref]
            if o.role in ("DEVICE", "PANEL"):
                n = key_of(o) or _anonymous_served(sm, o)
                if n is None and key_field(o) not in o.fields and not quiet:
                    device_name(o, sm.report)                          # reports the missing key field, as before
                if n:
                    hits.setdefault(n, (o, {}))[1][base(p.pin)] = base(pin)
    if len(hits) > 1:
        if not quiet:
            sm.report.error("driver.serves.two", f"driver {s.get('IC')} {s.kind} serves two devices: {', '.join(sorted(hits))}", source=loc(s))
        return None, None, {}
    if not hits:
        return None, None, {}
    name, (o, pins) = next(iter(hits.items()))
    return name, o, pins


def _encoded_address(sm: Seams, s: Symbol, drawn: str) -> str:
    """An encoded driver (a JMRI object) carries no address of its own: it is keyed by its object class, the symbol's
    Kind, and what its wires state (ADR 0005 S4 and R11; the owner, 2026-10-24, 2026-11-10 and 2026-11-11):
    ``Kind.served[.functions]``. ``served`` is the name of the device it serves, ``TURNOUT.777``, or for a nameless
    head or train order lever the mast pin its IND reaches, ``SIGNALMAST.Gilroy.E``. The functions come from the pin
    names alone: a driver pin named like the device pin it lands on serves that function by its own definition and
    adds nothing (the Turnout's M, N and R on the switch's M, N and R keep ``TURNOUT.777``); a driver pin named
    otherwise reads the function it is wired to and takes the device pin's name, ``SENSOR.777.OCC`` for a Sensor's S
    on the switch's OCC, ``SENSOR.777.WLQK`` on the lock lever's WLQK, ``SENSOR.Gilroy.E.STOP`` on the train order
    lever's STOP; sorted, shortest first. A SignalMast on a mast, a train order mast or a head stands in for positions
    instead: it carries the positions its net reaches unless that is every one, ``SIGNALMAST.778NAB.A`` and
    ``SIGNALMAST.778NAB``. A drawn Address is a stated field, written as drawn and reported at info; it is not the key."""
    served, o, touched = _served(sm, s)
    if drawn:
        sm.report.info("driver.address.override", f"driver {s.get('IC')} {s.kind}: Address {drawn!r} is stated beside the key the wires give, {served!r}", source=loc(s))
    if not s.kind:
        sm.report.missing("driver.kind", f"driver {s.get('IC')} serving {served!r}: no Kind, its object class; it has no key", source=loc(s))
        return ""
    if served is None:
        sm.report.missing("driver.serves", f"driver {s.get('IC')} {s.kind}: wired to no device; it has no key", source=loc(s))
        return ""
    key = f"{s.kind}.{served}"
    if s.kind == "SIGNALMAST" and o.get("Appliance") in ("mast", "train_order_mast", "head"):
        positions = _function_pins(o)
        functions = set(touched) if len(positions) > 1 and not positions <= set(touched) else set()
    else:
        functions = {device_pin for device_pin, driver_pin in touched.items() if driver_pin != device_pin}
    if functions:
        key += "." + ".".join(sorted(functions, key=lambda x: (len(x), x)))
    return key


def _columns(sm: Seams) -> None:
    for s in sm.source.where("COLUMN"):
        number = key_of(s, sm.report)
        at = loc(s)
        if not number:
            sm.report.missing("column.number", "a PanelColumn has no Column number", source=at)
            continue
        c = Column(number, s, given_of(s))
        folder = _unit_of_sheet(sm, s.sheet)
        c.sheet_folder = folder.name if folder else None
        if not s.get("CP Name"):
            c.folder = c.sheet_folder                                  # membership by hierarchy alone, written as a relation (D6)
        ou = one(list(sm.office_units.values()), "office units", at, sm.report, "column.office") if len(sm.office_units) != 1 else next(iter(sm.office_units.values()))
        if ou is None:
            continue
        c.office_unit = ou.name
        if number in ou.columns:
            sm.report.error("column.duplicate", f"OfficeUnit {ou.name}: two columns numbered {number}", source=at)
        ou.columns[number] = c


def _mast_on_ind(sm: Seams, s: Symbol, at: str, lever: bool = False) -> tuple[Optional[Symbol], Optional[str]]:
    """The field mast device a head's or a train order lever's IND wire reaches, and the pin of it the wire lands on: a
    signal mast device (Appliance ``mast``) has one passive pin per head position, A, B, C top down, and a head on that
    pin's net is that position's (issue #80; the owner, 2026-11-04: a head is anonymous, keyed by its mast and the pin);
    a train order mast device (Appliance ``train_order_mast``) has one passive pin per face, and a head or a lever on
    that pin's net is that face's (the owner, 2026-11-08). A head reaches a signal mast or a train order mast; a lever
    reaches a train order mast only. Nothing reached is ``head.mast`` or ``lever.face`` at missing (the mast, the
    position or the face is not yet drawn); two masts, or two pins of one, is ``head.masts`` or ``lever.faces`` at
    error. Any number of heads may share a pin (the owner, 2026-11-09): what each presents is the derivation's."""
    ind = sm.source.net_of(s.ref, "IND")
    kinds = ("train_order_mast",) if lever else ("mast", "train_order_mast")
    hits = [p for p in ind.others(s.ref) if sm.source.symbols[p.ref].role == "DEVICE" and sm.source.symbols[p.ref].get("Appliance") in kinds] if ind else []
    what = "train order lever" if lever else f"head device {s.lib_id.split(':')[1]}"
    if not hits:
        if lever:
            sm.report.missing("lever.face", f"{what}: its IND is wired to no face pin of a train order mast device; the face it serves is not yet drawn", source=at)
        else:
            sm.report.missing("head.mast", f"{what}: wired to no Mast or train order mast device", source=at)
        return None, None
    masts = sorted({p.ref for p in hits})
    if len(masts) > 1:
        text = f"{what}: its IND reaches {len(masts)} mast devices ({', '.join(masts)}); one expected"
        if lever:
            sm.report.error("lever.faces", text, source=at)
        else:
            sm.report.error("head.masts", text, source=at)
        return None, None
    m = sm.source.symbols[masts[0]]
    faces = sorted({base(p.pin) for p in hits})
    if len(faces) > 1:
        text = (f"{what}: its IND reaches {len(faces)} faces of train order mast {key_of(m)!r} ({', '.join(faces)}); a head or a lever is one face's"
                if m.get("Appliance") == "train_order_mast" else
                f"{what}: its IND reaches {len(faces)} positions of mast {key_of(m)!r} ({', '.join(faces)}); a head is one position's")
        if lever:
            sm.report.error("lever.faces", text, source=at)
        else:
            sm.report.error("head.masts", text, source=at)
        return None, None
    return m, faces[0]


def _driver_route(sm: Seams, p) -> Optional[tuple[Driver, str]]:
    """The driver whose pin this is, and the route owner/address/pin."""
    o = sm.source.symbols[p.ref]
    if o.role != "IODRIVER" or is_cmri_node(o):
        return None
    for proc in sm.processors.values():
        for d in proc.drivers.values():
            if any(x.ref == o.ref for x in d.syms):
                return d, f"{proc.name}/{d.address}/{base(p.pin)}"
    for t in sm.transports.values():
        for n in t.nodes.values():
            for d in n.bits.values():
                if any(x.ref == o.ref for x in d.syms):
                    return d, f"{t.name}/{n.ua}/{d.address}/{base(p.pin)}"
    return None


def _route_processor(sm: Seams, route: str) -> Optional[str]:
    """The processor a binding's route reaches: its owner, or for a bit of a CMRInet Node the one processor that anchors
    the Node's line (ADR 0009 §3: remote I/O is an attachment, not a processor). None when the line has no one anchor."""
    owner = route.split("/", 1)[0]
    if owner in sm.processors:
        return owner
    t = sm.transports.get(owner)
    return next(iter(t.anchors)) if t is not None and len(t.anchors) == 1 else None


def _sides_reached(sm: Seams, bindings: list[Binding]) -> tuple[set[str], set[str]]:
    """The office units and the interlockings whose processors a device's bindings reach (ADR 0017 decision 2). A
    processor that runs an office unit and a field unit names no side (ADR 0017 §6.2): the sheet decides."""
    ous: set[str] = set()
    ixs: set[str] = set()
    for b in bindings:
        p = _route_processor(sm, b.route)
        if p is None:
            continue
        o = {ou.name for ou in sm.office_units.values() if ou.processor == p}
        i = {ix.name for ix in sm.interlockings.values() if ix.processor == p}
        if o and i:
            continue
        ous |= o
        ixs |= i
    return ous, ixs


def _field_unit(sm: Seams, s: Symbol, name: Optional[str], reached: set[str], what: str, at: str) -> Optional[Interlocking]:
    """The interlocking of a device bound to field units' processors. One reached is it. A processor that runs the
    field units of several interlockings (GLOSSARY "field processor"; SPCoastApp) names the side, not the interlocking:
    the interlocking whose trackplan has the appliance the device serves decides, then the sheet (ADR 0017 §4)."""
    if len(reached) == 1:
        return sm.interlockings[next(iter(reached))]
    served = name or (_anonymous_served(sm, s) or "").rsplit(".", 1)[0]
    owners = {u.name for a in sm.source.where("APPLIANCE") if served and key_of(a).casefold() == served.casefold()
              and (u := _unit_of_sheet(sm, a.sheet)) is not None and u.name in reached}
    if len(owners) == 1:
        return sm.interlockings[next(iter(owners))]
    sheet = _unit_of_sheet(sm, s.sheet)
    if sheet is not None and sheet.name in reached:
        return sheet
    sm.report.error("device.interlocking", f"{what}: bound to the field units of {', '.join(sorted(reached))}; neither the appliance it "
                    "serves nor its sheet says which interlocking it is", source=at)
    return None


def _column_of(sm: Seams, s: Symbol, at: str) -> tuple[Optional[Net], Optional[Symbol]]:
    """A device's wired Column pin and the column on its net (ADR 0017 decision 4: membership is the wire, not Role)."""
    col_net = sm.source.net_of(s.ref, "Column")
    cols = [c for c in (sm.source.symbols[p.ref] for p in col_net.others(s.ref)) if c.role == "COLUMN"] if col_net else []
    return col_net, (one(cols, "columns on one Column net", at, sm.report, "device.columns") if cols else None)


def _office_of_sheet(sm: Seams, sheet: str) -> Optional[OfficeUnit]:
    hits = [ou for ou in sm.office_units.values() if in_scope(ou.sym.sheet, sheet)]
    return max(hits, key=lambda ou: len(ou.sym.sheet)) if hits else None


def _file_office(sm: Seams, s: Symbol, dev: Device, ou: OfficeUnit, col_net: Optional[Net], col: Optional[Symbol], at: str) -> None:
    """A desk device: its column from its wired Column pin; one in no column, or a lamp, is its panel sheet's
    interlocking's by hierarchy alone (D6; a lamp is its panel sheet's, never its column's, 2026-10-28). A Role PANEL
    device with no Column wire and no Style ``board`` is still ``device.column`` at missing until Role PANEL retires
    (ADR 0017 decision 7)."""
    placed = False
    if col is not None:
        column = ou.columns.get(key_of(col))
        dev.column = f"{ou.name}:{column.number}" if column else None     # qualified by its OfficeUnit (D19)
        placed = bool(column is not None and (column.given.get("CP Name") or column.folder))
    elif s.role == "PANEL" and s.get("Style") != "board" and col_net is None and dev.appliance != "lamp":
        sm.report.missing("device.column", f"panel {dev.appliance} {s.value!r} is in no column", source=at)
    if not placed or dev.appliance == "lamp":
        folder = _unit_of_sheet(sm, s.sheet)
        dev.interlocking = folder.name if folder else None             # membership by hierarchy alone (D6)
    ou.devices.append(dev)


def _file_field(sm: Seams, s: Symbol, dev: Device, ix: Interlocking, at: str) -> None:
    """A field device: a head's IND wire reaches a position pin of its mast, or a train order mast's face pin (#80; the
    owner, 2026-11-03, 2026-11-08); a fascia train order lever serves the face its IND wire reaches."""
    if dev.appliance == "head":
        m, pin = _mast_on_ind(sm, s, at)
        if m is not None:
            dev.mast = qualify(device_name(m, sm.report) or "", ix.name)
            if m.get("Appliance") == "train_order_mast":
                dev.face = pin
            else:
                dev.position = pin
    elif dev.appliance == "lever" and "train_order" in dev.styles:
        m, dev.face = _mast_on_ind(sm, s, at, lever=True)
        if m is not None:
            dev.mast = qualify(device_name(m, sm.report) or "", ix.name)
    ix.devices.append(dev)


def _devices(sm: Seams) -> None:
    """Each device, filed under the side its bindings reach (ADR 0017 decisions 2 and 4): bound to an office unit's
    processor, that office unit's; to a field unit's, that field unit's interlocking's (``_field_unit``). A device with
    no binding is the desk's when its Column pin is wired, else its sheet's: the interlocking whose sheet it is under,
    else the office unit's. Role is not read for the side or the column. Reported: bindings that reach both sides,
    ``device.sides`` at error; a side the sheet contradicts (a field device under another interlocking's sheet, or
    under none; a desk device under none of its office unit's sheets), ``device.side.sheet`` at warning; a wired Column
    pin on a device bound to a field unit, ``device.column.field`` at error."""
    for s in sm.source.where("DEVICE") + sm.source.where("PANEL"):
        appliance = s.get("Appliance")
        name = None if _anonymous(s) else device_name(s, sm.report)   # a head or a train order lever has no name of its own (the owner, 2026-11-04, 2026-11-08)
        dev = Device(s, appliance, styles_of(s), given=given_of(s, keyed=False))
        at = loc(s)
        inverted = {x.strip() for x in s.get("Invert").split(",") if x.strip()}
        for pin, net in sorted(sm.source.pins_of(s.ref).items()):
            if pin == "Column" or (pin == "IND" and appliance != "mast"):   # a head's or a train order lever's IND wire reaches its mast device, whose own IND is its binding
                continue
            own = next((q for q in net.pins if q.ref == s.ref and q.pin == pin), None)
            pintype = (own.pintype if own else "").split("+")[0]
            low = pin != base(pin)                                     # ~{X}: asserted low (ADR 0004 D9); a plain name asserted high
            sense = "low" if low != (base(pin) in inverted) else "high"   # Invert names a pin whose sense is the other one (ADR 0008 §2)
            for p in net.others(s.ref):
                hit = _driver_route(sm, p)
                if hit:
                    direction = DIRECTION_OF_PINTYPE.get(pintype)
                    if direction is None:
                        sm.report.missing("binding.direction", f"device {appliance} {name or s.value!r}: pin {base(pin)} is typed "
                                          f"{pintype or 'nothing'}, so its binding to {hit[1]} states no direction", source=loc(s, base(pin)))
                    dev.bindings.append(Binding(base(pin), hit[1], p.number, direction, sense))
        for n in sorted(inverted - {base(pin) for pin in sm.source.pins_of(s.ref)}):
            sm.report.error("device.invert", f"Invert names {n}, not a wired pin of this device", source=at)
        dev.bindings.sort(key=lambda b: (b.function, b.route))
        what = f"device {appliance} {name or s.value!r}"
        ous, ixs = _sides_reached(sm, dev.bindings)
        col_net, col = _column_of(sm, s, at)
        if ous and ixs:
            sm.report.error("device.sides", f"{what}: its bindings reach the office unit {', '.join(sorted(ous))} and the field unit of "
                            f"{', '.join(sorted(ixs))}; a device is on one side", source=at)
            continue
        if ous:
            ou = one([sm.office_units[o] for o in sorted(ous)], "office units reached by one device's bindings", at, sm.report, "device.office")
            if ou is None:
                continue
            if not in_scope(ou.sym.sheet, s.sheet):
                sm.report.warning("device.side.sheet", f"{what}: bound to office unit {ou.name}'s processor but drawn under none of its sheets", source=at)
            _file_office(sm, s, dev, ou, col_net, col, at)
        elif ixs:
            ix = _field_unit(sm, s, name, ixs, what, at)
            if ix is None:
                continue
            if col is not None:
                sm.report.error("device.column.field", f"{what}: bound to {ix.name}'s field unit, but its Column pin is wired to column "
                                f"{key_of(col)}; a column is the desk's", source=at)
            sheet = _unit_of_sheet(sm, s.sheet)
            if sheet is not ix:
                sm.report.warning("device.side.sheet", f"{what}: bound to {ix.name}'s field unit but drawn under "
                                  f"{sheet.name + chr(39) + 's' if sheet else 'no interlocking'} sheet", source=at)
            _file_field(sm, s, dev, ix, at)
        elif col is not None:
            ou = next(iter(sm.office_units.values()), None) if len(sm.office_units) == 1 else None
            if ou is None:
                sm.report.error("device.office", f"{what}: in a column but no single OfficeUnit", source=at)
                continue
            _file_office(sm, s, dev, ou, col_net, col, at)
        elif (ix := _unit_of_sheet(sm, s.sheet)) is not None:
            _file_field(sm, s, dev, ix, at)
        elif (ou := _office_of_sheet(sm, s.sheet)) is not None:
            _file_office(sm, s, dev, ou, col_net, col, at)
        else:
            sm.report.error("device.interlocking", f"{what}: no binding, no column, and no Interlocking or OfficeUnit on its sheet or above", source=at)
