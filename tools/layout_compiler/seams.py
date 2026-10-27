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
from collections import defaultdict
from dataclasses import dataclass, field, replace
from typing import Optional

from .source import Net, Source, Symbol, in_scope

MACRO = re.compile(r"<([A-Z_]+):([A-Z_]*):([\w .]+)>")
ERROR, WARNING, INFO, MISSING = "error", "warning", "info", "missing"
# Reference data, general, not layout data (ADR 0008 §4.7). Versioned so provenance can name it.
REFERENCE_DATA = {"encodingTransportPairing": "2026-10-23", "driverEncodings": "2026-10-23"}
# An encoding's Kind pairs with its transport's Kind (ADR 0009 §3.10).
TRANSPORT_OF_ENCODING = {"AAR": "MQTT", "USS506": "TIMECODE", "BITS": "TIMECODE", "JMRI": "MQTT", "CMRI": "CMRI"}
# A driver whose IC is an encoding needs that I/O encoding on its processor (ADR 0009 §3.3, §3.6, §3.12 "IC native or encoded").
ENCODING_OF_IC = {"MQTT-JMRI": "JMRI"}
# KiCad's own housekeeping (ADR 0011 §2), and Role, which only picks the collection (three-maps D1): never in given.
HOUSEKEEPING = frozenset({"Reference", "Value", "Footprint", "Datasheet", "Description", "Sheetname", "Sheetfile", "Role"})


@dataclass(frozen=True)
class Diag:
    severity: str
    code: str
    text: str
    where: str = ""

    def __str__(self) -> str:
        return f"{self.severity}: {self.code}: {self.text}" + (f"  [{self.where}]" if self.where else "")


class Report:
    def __init__(self) -> None:
        self.diags: list[Diag] = []

    def add(self, severity: str, code: str, text: str, where: str = "") -> None:
        self.diags.append(Diag(severity, code, text, where))

    def error(self, code, text, where=""):
        self.add(ERROR, code, text, where)

    def warning(self, code, text, where=""):
        self.add(WARNING, code, text, where)

    def info(self, code, text, where=""):
        self.add(INFO, code, text, where)

    def missing(self, code, text, where=""):
        self.add(MISSING, code, text, where)

    @property
    def errors(self) -> list[Diag]:
        return [d for d in self.diags if d.severity == ERROR]

    def by_code(self, code: str) -> list[Diag]:
        return [d for d in self.diags if d.code == code]


def loc(s: Symbol) -> str:
    return f"{s.sheet}{s.ref} {s.lib_id} {s.value!r}"


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
    syms: list[Symbol] = field(default_factory=list)                  # every symbol that draws it (a JMRI Turnout: command and feedback)


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
class Column:
    number: str
    sym: Symbol
    given: dict[str, str] = field(default_factory=dict)
    house: Optional[tuple[str, str]] = None                           # (interlocking, cp name), derived from CP Name
    interlocking: Optional[str] = None                                # derived: the house's interlocking, else the folder's
    folder: Optional[str] = None                                      # stated by the sheet hierarchy alone (three-maps D6)
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
    function: str
    route: str


@dataclass
class Device:
    sym: Symbol
    appliance: str
    styles: list[str]
    given: dict[str, str] = field(default_factory=dict)              # its Name included: a row has no identity
    serves: Optional[str] = None                                      # derived: qualified railroad name
    head: Optional[str] = None
    shows: list[str] = field(default_factory=list)                    # derived
    column: Optional[str] = None                                      # relation: the OfficeUnit-qualified column
    interlocking: Optional[str] = None                                # relation: the folder, for a device in no column (D6)
    mast: Optional[str] = None                                        # relation: a head device's IND wire to its Mast
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
    office_units: dict[str, OfficeUnit] = field(default_factory=dict)
    trackplan: Optional["object"] = None                              # trackplan.Trackplan: appliances, track, circuits


# ---------------------------------------------------------------- helpers

# The key attribute of each kind of symbol, by Role and Kind (a Kind of None covers the Role): where a symbol keeps its
# identity is decided here and nowhere else (the owner, 2026-10-26). Every other symbol's key is ``Name``. A CMRInet
# Node's and a driver's key is its ``Address``, unique within its owner (three-maps D11); a bit's ``IB.n`` and an
# encoded driver's ``Kind.served`` are computed keys, so those symbols have no key field.
KEYS = {("STRUCTURE", "CONTROL_POINT"): "CP Name", ("COLUMN", None): "Column", ("IODRIVER", None): "Address"}


def key_field(s: Symbol) -> Optional[str]:
    if s.role == "IODRIVER" and not s.get("NodeType") and (s.get("Bit") or s.get("IC") in ENCODING_OF_IC):
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
        report.missing(f"identity.{k.replace(' ', '_').lower()}", f"{s.lib_id} has no {k} field, so it has no name; Value is never read", loc(s))
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
            report.error("milepost.number", f"{what}: Milepost {s.get('Milepost')!r} is not a number", loc(s))


def given_of(s: Symbol, keyed: bool = True) -> dict[str, str]:
    """Every field the person stated, keyed as drawn, as KiCad states it (ADR 0011 §2): less KiCad's housekeeping,
    ``Role`` (D1), the library's ``Pin.*`` contract (D2) and, for a keyed entity, its key field. An empty field or
    KiCad's ``~`` is not stated (D21). A row without identity (a device) keeps its ``Name`` (``keyed=False``)."""
    key = key_field(s) if keyed else None
    return {k: v for k, v in s.fields.items()
            if k not in HOUSEKEEPING and k != key and not k.startswith(("ki_", "Pin.")) and v.strip() not in ("", "~")}


def merge_given(have: dict[str, str], s: Symbol, what: str, report: Report) -> None:
    """One entity drawn several times states one set of facts: each placement's ``given`` merged, a conflict an error."""
    for k, v in given_of(s).items():
        if k in have and have[k] != v:
            report.error("entity.conflict", f"{what}: {k} {have[k]!r} on one placement, {v!r} on another", loc(s))
            continue
        have[k] = v


def styles_of(s: Symbol) -> list[str]:
    return sorted(x.strip() for x in s.get("Style").split(",") if x.strip())


def qualify(name: str, scope: str) -> str:
    """A reference is always the qualified name (ADR 0008 §4.5); a token already qualified keeps its scope."""
    return name if ":" in name else f"{scope}:{name}"


def base(pin: str) -> str:
    return pin[2:-1] if pin.startswith("~{") and pin.endswith("}") else pin


def one(items: list, what: str, where: str, report: Report, code: str) -> Optional[object]:
    """Exactly one, or report and None: the rule every scope lookup shares."""
    if len(items) == 1:
        return items[0]
    if len(items) > 1:
        report.error(code, f"{len(items)} {what} where one is expected", where)
    return None


def stated(value, what: str, where: str, report: Report, code: str):
    """A relation has one form, its wire (ADR 0012 §4): the value it names, or ``missing`` when none is drawn."""
    if value is None:
        report.missing(f"{code}.missing", f"{what}: no wire states it", where)
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
                        report.error("macro.scope", f"no symbol with Role {role} Kind {kind!r} in scope for {m.group(0)}", loc(s))
                    return m.group(0)
                if fld not in c.fields:
                    report.error("macro.field", f"{c.lib_id} has no field {fld} for {m.group(0)}", loc(s))
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
    _houses(seams)
    _nodes(seams)
    _drivers(seams)
    _columns(seams)
    _devices(seams)
    _heads(seams)
    _reach(seams)
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
        sm.report.missing("railroad.name", "the Railroad symbol has no Name", loc(s))


def _processors(sm: Seams) -> None:
    for s in sm.source.where("STRUCTURE", "PROCESSOR"):
        name = key_of(s, sm.report)
        if not name:
            sm.report.missing("entity.name", "a processor has no Name; it is not written", loc(s))
            continue
        p = sm.processors.setdefault(name, Processor(name))
        p.syms.append(s)
        merge_given(p.given, s, f"processor {name}", sm.report)
    for p in sm.processors.values():
        if not p.given.get("Board"):
            sm.report.missing("processor.board", f"processor {p.name}: no Board", loc(p.syms[0]))


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
            sm.report.missing("entity.name", "a transport has no Name; it is not written", loc(s))
            continue
        t = sm.transports.setdefault(name, Transport(name, s.kind))
        if t.kind != s.kind:
            sm.report.error("entity.conflict", f"transport {name}: Kind {t.kind} and {s.kind}", loc(s))
        merge_given(t.given, s, f"transport {name}", sm.report)
        t.instances[s.ref] = s
        anchor = stated(_anchor_of(sm, s), f"transport {name} anchored on", loc(s), sm.report, "transport.anchor")
        if anchor:
            if anchor not in sm.processors:
                sm.report.error("transport.anchor", f"transport {name}: anchor {anchor!r} is not a processor", loc(s))
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
            sm.report.missing("entity.name", "a encoding has no Name; it is not written", loc(s))
            continue
        if name in sm.encodings:
            sm.report.error("entity.duplicate", f"two encodings named {name!r}", loc(s))
            continue
        e = Encoding(name, s.kind, s.role, s, given_of(s))
        hit = _transport_on_net(sm, s)
        want_kind = TRANSPORT_OF_ENCODING.get(s.kind)
        e.transport = stated(hit[0] if hit else None, f"encoding {name} rides", loc(s), sm.report, "encoding.transport")
        if e.transport:
            t = sm.transports[e.transport]
            if want_kind and t.kind != want_kind:
                sm.report.error("encoding.kind", f"encoding {name} ({s.kind}) rides {t.name} ({t.kind}); {s.kind} pairs with {want_kind}", loc(s))
            # the instance it rides is the transport symbol on its net; that instance's anchor is the encoding's processor (D7)
            e.processor = _anchor_of(sm, hit[1])
            if e.processor is None:
                sm.report.missing("encoding.processor", f"encoding {name}: the transport instance it rides has no anchor", loc(s))
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
            sm.report.missing("interlocking.name", "an Interlocking symbol has no Name", loc(s))
            continue
        if name in sm.interlockings:
            sm.report.error("entity.duplicate", f"two interlockings named {name!r}", loc(s))
            continue
        ix = Interlocking(name, s, given_of(s))
        ix.processor = stated(_anchor_of(sm, s), f"FieldUnit {name} runs on", loc(s), sm.report, "unit.processor")
        if ix.processor and ix.processor not in sm.processors:
            sm.report.error("unit.processor", f"FieldUnit {name}: {ix.processor!r} is not a processor", loc(s))
        ix.codeline = stated(_codeline_of(sm, s), f"FieldUnit {name} on its line", loc(s), sm.report, "unit.codeline")
        sm.interlockings[name] = ix


def _unit_of_sheet(sm: Seams, sheet: str) -> Optional[Interlocking]:
    """The interlocking whose sheet is this sheet or an ancestor of it (the folder)."""
    hits = [ix for ix in sm.interlockings.values() if in_scope(ix.sym.sheet, sheet)]
    return max(hits, key=lambda ix: len(ix.sym.sheet)) if hits else None


def _houses(sm: Seams) -> None:
    for s in sm.source.where("STRUCTURE", "CONTROL_POINT"):
        cp = key_of(s, sm.report)
        if not cp:
            sm.report.missing("house.cp_name", "a House has no CP Name", loc(s))
            continue
        h = House(cp, s, given_of(s))
        ix = _unit_of_sheet(sm, s.sheet)
        if ix is None:
            sm.report.error("house.interlocking", f"house {cp}: no Interlocking on its sheet or above", loc(s))
            continue
        h.interlocking = ix.name
        check_milepost(s, sm.report, f"house {cp}")
        line = _codeline_of(sm, s)                                     # stated only where wired; never required of a house
        h.codeline = line
        if line and ix.codeline and line != ix.codeline:
            sm.report.error("house.codeline", f"house {cp} sits on {line!r} but its interlocking {ix.name} is on {ix.codeline!r}", loc(s))
        mc = sm.source.net_of(s.ref, "MC")
        if mc:
            calls = [sm.source.symbols[p.ref] for p in mc.others(s.ref) if sm.source.symbols[p.ref].role == "APPLIANCE"]
            c = one(calls, "maintainer calls on one MC net", loc(s), sm.report, "house.mc")
            if c is not None:
                h.maintainer_call = qualify(key_of(c, sm.report), ix.name)
        if cp in ix.houses:
            sm.report.error("entity.duplicate", f"two houses named {cp!r} in {ix.name}", loc(s))
        ix.houses[cp] = h


def _office_units(sm: Seams) -> None:
    for s in sm.source.where("OFFICE_UNIT"):
        name = key_of(s, sm.report)
        if not name:
            sm.report.missing("entity.name", "a office unit has no Name; it is not written", loc(s))
            continue
        if name in sm.office_units:
            sm.report.error("entity.duplicate", f"two office units named {name!r}", loc(s))
            continue
        ou = OfficeUnit(name, s, given_of(s))
        ou.processor = stated(_anchor_of(sm, s), f"OfficeUnit {name} runs on", loc(s), sm.report, "office.processor")
        if ou.processor and ou.processor not in sm.processors:
            sm.report.error("office.processor", f"OfficeUnit {name}: {ou.processor!r} is not a processor", loc(s))
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
        elif o.role == "IODRIVER" and o.get("NodeType"):
            t = next((tn for tn, t in sm.transports.items() if o.get("Address") in t.nodes and t.nodes[o.get("Address")].sym.ref == o.ref), None)
            owners.append(f"{t}/{o.get('Address')}" if t else None)
    owners = [o for o in owners if o]
    return owners[0] if len(owners) == 1 else (one(owners, "bus providers on one IOBus net", loc(s), sm.report, "bus.net") if owners else None)


def _nodes(sm: Seams) -> None:
    for s in sm.source.where("IODRIVER"):
        if not s.get("NodeType"):
            continue
        ua = s.get("Address")
        if not ua:
            sm.report.missing("node.address", "a CMRInet Node has no Address (its UA)", loc(s))
            continue
        n = Node(ua, s, given_of(s))
        for attr, fld in (("input_bytes", "InputBytes"), ("output_bytes", "OutputBytes")):
            if s.get(fld):
                try:
                    setattr(n, attr, int(s.get(fld)))
                except ValueError:
                    sm.report.error("node.bytes", f"CMRInet Node {ua}: {fld} {s.get(fld)!r} is not a number", loc(s))
            else:
                sm.report.missing("node.bytes", f"CMRInet Node {ua}: no {fld}", loc(s))
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
        if s.get("NodeType"):
            continue
        ic = s.get("IC")
        is_bit = bool(s.get("Bit"))
        if is_bit:
            d_net = sm.source.net_of(s.ref, "D")
            direction = next((p.pintype for p in (d_net.pins if d_net else ()) if p.ref == s.ref), "")
            if direction not in ("input", "output"):
                sm.report.error("bit.direction", f"CMRInet bit {s.value!r}: pin D is {direction!r}; input (IB) or output (OB) expected", loc(s))
                continue
            address = f"{'IB' if direction == 'input' else 'OB'}.{s.get('Bit')}"
        else:
            address = s.get("Address")
            if ic in ENCODING_OF_IC:
                address = _encoded_address(sm, s, address)
        d = Driver(s, ic, address, given=given_of(s), kind=s.kind, syms=[s])
        where = loc(s)
        d.owner = stated(_bus_owner(sm, s), f"driver {ic} {address or s.value!r} on a bus", where, sm.report, "driver.bus")
        if not ic:
            sm.report.missing("driver.ic", "a driver has no IC", where)
        if d.owner is None:
            continue
        if "/" in d.owner:
            tn, ua = d.owner.split("/", 1)
            node = sm.transports[tn].nodes[ua]
            if not is_bit:
                sm.report.error("bus.kind", f"driver {ic} {address!r} sits on CMRInet Node {ua}'s bus; only its bits do", where)
                continue
            if address in node.bits:
                sm.report.error("bit.duplicate", f"CMRInet Node {ua}: two bits at {address}", where)
            node.bits[address] = d
        else:
            if is_bit:
                sm.report.error("bus.kind", f"CMRInet bit {address} sits on processor {d.owner}'s bus; a bit sits on a node's", where)
                continue
            p = sm.processors[d.owner]
            if not address:
                if ic not in ENCODING_OF_IC:                           # an encoded driver without one was reported by _encoded_address
                    sm.report.missing("driver.address", f"driver {ic} ({s.lib_id.split(':')[1]}) on {p.name} has no Address; its bindings are absent", where)
                continue
            if address in p.drivers:
                first = p.drivers[address]
                if ic in ENCODING_OF_IC and first.ic == ic and first.kind == d.kind:
                    first.syms.append(s)                               # one JMRI object drawn twice: a Turnout's command and its feedback
                    if first.given != d.given:
                        sm.report.error("entity.conflict", f"driver {address} on {p.name}: its symbols state different fields", where)
                    continue
                sm.report.error("driver.duplicate", f"processor {p.name}: two drivers at {address}", where)
            p.drivers[address] = d
    for t in sm.transports.values():
        for n in t.nodes.values():
            for prefix, declared in (("IB", n.input_bytes), ("OB", n.output_bytes)):
                used = [int(a.split(".")[1]) for a in n.bits if a.startswith(prefix)]
                if used and declared is not None and max(used) > declared * 8:
                    sm.report.error("node.bytes", f"CMRInet Node {n.ua}: {prefix} bit {max(used)} used but {declared} byte(s) declared", loc(n.sym))


def _served_device(sm: Seams, s: Symbol) -> Optional[str]:
    """The one device wired to a driver's function pins; two is an error."""
    names: set[str] = set()
    for pin, net in sm.source.pins_of(s.ref).items():
        if pin == "IOBus":
            continue
        for p in net.others(s.ref):
            o = sm.source.symbols[p.ref]
            if o.role in ("DEVICE", "PANEL"):
                n = device_name(o, sm.report)
                if n:
                    names.add(n)
    if len(names) > 1:
        sm.report.error("driver.serves", f"driver {s.get('IC')} {s.kind} serves two devices: {', '.join(sorted(names))}", loc(s))
        return None
    return next(iter(names), None)


def _encoded_address(sm: Seams, s: Symbol, drawn: str) -> str:
    """An encoded driver (a JMRI object) carries no address of its own: it is keyed by its object class, the symbol's
    Kind, and the name of the device it serves, ``TURNOUT.777`` (ADR 0005 S4 and R11; the owner, 2026-10-24). A drawn
    Address overrides that, reported at info."""
    served = _served_device(sm, s)
    if drawn:
        sm.report.info("driver.address.override", f"driver {s.get('IC')} {s.kind}: Address {drawn!r} overrides the served device's name {served!r}", loc(s))
        return drawn
    if not s.kind:
        sm.report.missing("driver.kind", f"driver {s.get('IC')} serving {served!r}: no Kind, its object class; it has no key", loc(s))
        return ""
    if served is None:
        sm.report.missing("driver.serves", f"driver {s.get('IC')} {s.kind}: wired to no device; it has no key", loc(s))
        return ""
    return f"{s.kind}.{served}"


def _reach(sm: Seams) -> None:
    """Two checks across entities. A driver whose IC is an encoding needs that I/O encoding on its processor (ADR 0009
    §3.6, §3.12 'IC native or encoded'). A FieldUnit reaches its code line's transport through the code line; when its
    processor anchors no instance of that transport, the drawing relies on that derivation, reported at info (review
    2026-10-23 finding 5; the owner decides whether the §3.12 check 'an anchor per connecting processor' stands)."""
    for p in sm.processors.values():
        for d in p.drivers.values():
            kind = ENCODING_OF_IC.get(d.ic)
            if kind and not any(e.role == "IO_ENCODING" and e.kind == kind and e.processor == p.name for e in sm.encodings.values()):
                sm.report.error("driver.encoding", f"driver {d.ic} {d.address} on {p.name}: no {kind} I/O encoding rides a transport anchored on {p.name}", loc(d.sym))
    for ix in sm.interlockings.values():
        e = sm.encodings.get(ix.codeline) if ix.codeline else None
        if e and e.transport and ix.processor and ix.processor not in sm.transports[e.transport].anchors:
            sm.report.info("transport.reach", f"FieldUnit {ix.name} reaches {e.transport} through its code line {e.name}; its processor {ix.processor} anchors no {e.transport} instance", loc(ix.sym))


def _house_by_cp(sm: Seams, cp: str) -> Optional[tuple[str, str]]:
    hits = [(ix.name, h.cp_name) for ix in sm.interlockings.values() for h in ix.houses.values() if h.cp_name.casefold() == cp.casefold()]
    return hits[0] if len(hits) == 1 else None


def _columns(sm: Seams) -> None:
    for s in sm.source.where("COLUMN"):
        number = key_of(s, sm.report)
        where = loc(s)
        if not number:
            sm.report.missing("column.number", "a PanelColumn has no Column number", where)
            continue
        c = Column(number, s, given_of(s))
        folder = _unit_of_sheet(sm, s.sheet)
        if s.get("CP Name"):
            c.house = _house_by_cp(sm, s.get("CP Name"))
            if c.house is None:
                sm.report.error("column.house", f"column {number}: CP Name {s.get('CP Name')!r} names no house", where)
            else:
                c.interlocking = c.house[0]
                if folder and folder.name != c.interlocking:
                    sm.report.error("column.house", f"column {number}: house {c.house[1]} is in {c.interlocking}, the column is drawn under {folder.name}", where)
        else:
            sm.report.missing("column.cp_name", f"column {number}: no CP Name; only its sheet says it is in {folder.name if folder else '?'}", where)
            c.folder = folder.name if folder else None                 # membership by hierarchy alone, written as a relation (D6)
            c.interlocking = c.folder
        ou = one(list(sm.office_units.values()), "office units", where, sm.report, "column.office") if len(sm.office_units) != 1 else next(iter(sm.office_units.values()))
        if ou is None:
            continue
        c.office_unit = ou.name
        if number in ou.columns:
            sm.report.error("column.duplicate", f"OfficeUnit {ou.name}: two columns numbered {number}", where)
        ou.columns[number] = c
    for ou in sm.office_units.values():
        # a 506 station is a house addressed by its column; a house with two columns on a 506 line is two addresses
        by_house = defaultdict(list)
        for c in ou.columns.values():
            if c.house:
                by_house[c.house].append(c.number)
        for (ixn, cp), nums in by_house.items():
            ix = sm.interlockings.get(ixn)
            enc = sm.encodings.get(ix.codeline) if ix and ix.codeline else None
            if enc and enc.kind == "USS506" and len(nums) > 1:
                sm.report.error("station.columns", f"house {cp} of {ixn} has columns {', '.join(nums)} on a US&S 506 line: two station addresses", loc(ix.sym))


def _driver_route(sm: Seams, p) -> Optional[tuple[Driver, str]]:
    """The driver whose pin this is, and the route owner/address/pin."""
    o = sm.source.symbols[p.ref]
    if o.role != "IODRIVER" or o.get("NodeType"):
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


def _devices(sm: Seams) -> None:
    for s in sm.source.where("DEVICE") + sm.source.where("PANEL"):
        appliance = s.get("Appliance")
        name = device_name(s, sm.report)
        dev = Device(s, appliance, styles_of(s), given=given_of(s, keyed=False))
        where = loc(s)
        scope: Optional[str] = None
        if s.role == "PANEL":
            col_net = sm.source.net_of(s.ref, "Column")
            cols = [sm.source.symbols[p.ref] for p in col_net.others(s.ref)] if col_net else []
            cols = [c for c in cols if c.role == "COLUMN"]
            col = one(cols, "columns on one Column net", where, sm.report, "device.column") if cols else None
            ou = next(iter(sm.office_units.values()), None) if len(sm.office_units) == 1 else None
            if col is not None and ou is not None:
                column = ou.columns.get(key_of(col))
                dev.column = f"{ou.name}:{column.number}" if column else None     # qualified by its OfficeUnit (D19)
                scope = column.interlocking if column else None
            elif s.get("Style") != "board" and col_net is None:
                sm.report.missing("device.column", f"panel {appliance} {s.value!r} is in no column", where)
            if scope is None:
                folder = _unit_of_sheet(sm, s.sheet)
                scope = dev.interlocking = folder.name if folder else None  # membership by hierarchy alone (D6)
            if ou is None:
                sm.report.error("device.office", f"panel device {s.value!r}: no single OfficeUnit", where)
                continue
            if appliance == "lamp":
                dev.shows = [qualify(t.strip(), scope or "") for t in s.get("IndicationToken").split(",") if t.strip()]
                if not dev.shows:
                    sm.report.missing("lamp.token", f"panel lamp {s.value!r}: no IndicationToken", where)
            else:
                dev.serves = qualify(name, scope or "") if name else None
            ou.devices.append(dev)
        else:
            ix = _unit_of_sheet(sm, s.sheet)
            if ix is None:
                sm.report.error("device.interlocking", f"device {appliance} {s.value!r}: no Interlocking on its sheet or above", where)
                continue
            if appliance == "head":
                dev.head = s.get("Head") or None
                ind = sm.source.net_of(s.ref, "IND")
                masts = [sm.source.symbols[p.ref] for p in ind.others(s.ref)] if ind else []
                masts = [m for m in masts if m.get("Appliance") == "mast" and m.role == "DEVICE"]
                m = one(masts, "masts on one IND net", where, sm.report, "head.mast") if masts else None
                if m is None:
                    sm.report.missing("head.mast", f"head device {s.lib_id.split(':')[1]} letter {dev.head!r}: wired to no Mast", where)
                else:
                    dev.mast = dev.serves = qualify(device_name(m, sm.report) or "", ix.name)
                if not dev.head:
                    sm.report.missing("head.letter", "a head device has no Head letter", where)
            elif name:
                dev.serves = qualify(name, ix.name)                    # an appliance's device, or a Mast: one row per device (the owner, 2026-10-24)
            else:
                sm.report.missing("device.serves", f"device {appliance}: no appliance name", where)
            ix.devices.append(dev)
        if dev.appliance == "lever" and "code" in dev.styles:
            dev.serves = None                                          # the code lever serves the station, not an appliance; its Value is a label
        inverted = {x.strip() for x in s.get("Invert").split(",") if x.strip()}
        for pin, net in sorted(sm.source.pins_of(s.ref).items()):
            if pin == "Column" or (pin == "IND" and appliance != "mast"):   # a head's IND wire reaches its Mast; the Mast's IND is its own binding
                continue
            for p in net.others(s.ref):
                hit = _driver_route(sm, p)
                if hit:
                    dev.bindings.append(Binding(base(pin), hit[1]))
        for name in sorted(inverted - {base(pin) for pin in sm.source.pins_of(s.ref)}):
            sm.report.error("device.invert", f"Invert names {name}, not a wired pin of this device", where)
        dev.bindings.sort(key=lambda b: (b.function, b.route))


def _heads(sm: Seams) -> None:
    """Head device to trackplan head by mast name and letter; the vocabularies must match (ADR 0009 §3.7)."""
    for ix in sm.interlockings.values():
        # trackplan heads: Name is the letter, M pin to a Mast_* whose Name is the mast name (Name = ${Value}, 2026-10-24)
        plan: dict[tuple[str, str], str] = {}
        for h in sm.source.under(ix.sym.sheet, "APPLIANCE"):
            if h.get("Appliance") != "head":
                continue
            net = sm.source.net_of(h.ref, "M")
            masts = [sm.source.symbols[p.ref] for p in net.others(h.ref)] if net else []
            masts = [m for m in masts if m.role == "APPLIANCE" and m.get("Appliance") == "mast"]
            if len(masts) == 1:
                plan[(key_of(masts[0], sm.report), key_of(h, sm.report))] = h.get("Style")   # the trackplan head's Name is its letter
        by_head: dict[tuple[str, str], list[Device]] = defaultdict(list)
        for d in ix.devices:
            if d.appliance == "head" and d.serves and d.head:
                by_head[(d.serves.split(":", 1)[1], d.head)].append(d)
        for (mast, letter), devs in sorted(by_head.items()):
            style = plan.get((mast, letter))
            if style is None:
                sm.report.error("head.plan", f"{ix.name}: head devices for {mast} head {letter}, but the trackplan draws no such head", loc(devs[0].sym))
                continue
            primary = [d for d in devs if style in d.styles]
            lamps = [d for d in devs if style not in d.styles and style in ("UQ", "LQ") and (d.appliance == "lamp" or "CL" in d.styles)]
            wrong = [d for d in devs if d not in primary and d not in lamps]
            for d in wrong:                                            # the §3.7 error, one per device
                sm.report.error("head.vocabulary", f"{ix.name}: the trackplan draws {mast} head {letter} as {style}, but its device is "
                                f"{d.sym.lib_id.split(':')[1]}. Fix: change the trackplan head, or bind a {style} device", loc(d.sym))
            if len(primary) > 1 or (not primary and not wrong):
                sm.report.error("head.vocabulary", f"{ix.name}: {mast} head {letter} ({style}) has {len(primary)} devices of its style; one expected", loc(devs[0].sym))
