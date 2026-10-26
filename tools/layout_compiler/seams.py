"""The explicit-seams model (ADR 0009): what the drawing states, resolved by wire and by fallback, and checked.

Every relation of the §3.12 table is resolved twice. The explicit form follows a wire from a pin named for the
relation (``Processor``, ``Transport``, ``Codeline``, ``IOBus``, ``Column``). The implicit form follows the sheet
hierarchy or a field. When both resolve they must agree, or the compiler reports an error and writes no file. When
only one resolves, the compiler says so at ``info``. When neither does, the fact is ``missing``, which is the
tutorial prompt (ADR 0009 §3.10), not an error: absence is information (ADR 0008 §4.7).

Identity is the key attribute of each symbol (``Name`` on most, ``CP Name``, ``Column``, ``Address``, ``Head``);
``Value`` is drawing and is never read (ADR 0009 §3.10). A symbol without its key has no name and is reported.
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
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
# The keys the compiler reads (ADR 0009 §3.10) and KiCad's own; every other drawn field with content is a setting, written as drawn.
NOT_SETTINGS = {"Role", "Kind", "Style", "Appliance", "Name", "IC", "Address", "Bit", "Node", "Head", "Invert", "IndicationToken",
                "CP", "TC", "Transport", "Processor", "NodeType", "InputBytes", "OutputBytes", "IndicationCeiling",
                "Display", "Milepost", "CP Name", "Column", "Reference", "Value", "Footprint", "Datasheet", "Description",
                "Sheetname", "Sheetfile", "ki_keywords", "ki_fp_filters", "ki_description", "ki_locked", "Era", "Railroad",
                "Region", "Rulebook", "Direction"}


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
    board: str = ""
    description: str = ""
    syms: list[Symbol] = field(default_factory=list)
    drivers: dict[str, "Driver"] = field(default_factory=dict)        # by address on its bus


@dataclass
class Transport:
    name: str
    kind: str
    settings: dict[str, str] = field(default_factory=dict)
    anchors: set[str] = field(default_factory=set)                    # processor names, one per placed instance
    instances: dict[str, Symbol] = field(default_factory=dict)        # ref -> placed symbol
    nodes: dict[str, "Node"] = field(default_factory=dict)            # by UA


@dataclass
class Encoding:
    name: str
    kind: str
    role: str                                                        # CODELINE_ENCODING or IO_ENCODING
    sym: Symbol
    settings: dict[str, str] = field(default_factory=dict)
    transport: Optional[str] = None
    processor: Optional[str] = None                                   # the processor anchoring the transport instance it rides
    codeline_net: Optional[Net] = None


@dataclass
class Node:
    ua: str
    sym: Symbol
    ic: str = ""
    transport: Optional[str] = None
    node_type: str = ""
    input_bytes: Optional[int] = None
    output_bytes: Optional[int] = None
    bits: dict[str, "Driver"] = field(default_factory=dict)           # by IB.n / OB.n


@dataclass
class Driver:
    sym: Symbol
    ic: str
    address: str                                                     # on its bus: 0x20, D2, IB.3
    owner: Optional[str] = None                                       # route owner: a processor name or transport/UA
    settings: dict[str, str] = field(default_factory=dict)
    kind: str = ""                                                    # an encoded driver's object class: TURNOUT, SENSOR, SIGNALMAST, LIGHT
    syms: list[Symbol] = field(default_factory=list)                  # every symbol that draws it (a JMRI Turnout: command and feedback)


@dataclass
class House:
    cp_name: str
    sym: Symbol
    interlocking: Optional[str] = None
    milepost: Optional[float] = None
    maintainer_call: Optional[str] = None
    codeline: Optional[str] = None


@dataclass
class Interlocking:
    name: str
    sym: Symbol
    processor: Optional[str] = None
    codeline: Optional[str] = None
    houses: dict[str, House] = field(default_factory=dict)
    devices: list["Device"] = field(default_factory=list)


@dataclass
class Column:
    number: str
    sym: Symbol
    house: Optional[tuple[str, str]] = None                           # (interlocking, cp name)
    interlocking: Optional[str] = None
    office_unit: Optional[str] = None


@dataclass
class OfficeUnit:
    name: str
    sym: Symbol
    style: str = ""
    processor: Optional[str] = None
    columns: dict[str, Column] = field(default_factory=dict)
    devices: list["Device"] = field(default_factory=list)


@dataclass
class Binding:
    function: str
    route: str
    invert: bool = False                                              # the instance polarity override (Invert names the pin)


@dataclass
class Device:
    sym: Symbol
    appliance: str
    styles: list[str]
    serves: Optional[str] = None                                      # qualified railroad name
    head: Optional[str] = None
    shows: list[str] = field(default_factory=list)
    column: Optional[str] = None
    address: Optional[str] = None
    settings: dict[str, str] = field(default_factory=dict)
    bindings: list[Binding] = field(default_factory=list)


@dataclass
class Seams:
    source: Source
    report: Report
    railroad: dict[str, str] = field(default_factory=dict)
    processors: dict[str, Processor] = field(default_factory=dict)
    transports: dict[str, Transport] = field(default_factory=dict)
    encodings: dict[str, Encoding] = field(default_factory=dict)
    interlockings: dict[str, Interlocking] = field(default_factory=dict)
    office_units: dict[str, OfficeUnit] = field(default_factory=dict)
    trackplan: Optional["object"] = None                              # trackplan.Trackplan: appliances, track, circuits


# ---------------------------------------------------------------- helpers

def name_of(s: Symbol, report: Report) -> str:
    """The identity key: ``Name``, never ``Value`` (ADR 0009 §3.10; the owner, 2026-10-25). A symbol whose library lacks
    the attribute has no name, reported ``missing``: the fix is the attribute in the library and on its instances."""
    if "Name" in s.fields:                                            # stated, even empty: KiCad resolves ${Value} of "~" to nothing
        return s.get("Name")
    report.missing("identity.name", f"{s.lib_id} has no Name field, so it has no name; Value is never read", loc(s))
    return ""


def device_name(s: Symbol, report: Report) -> Optional[str]:
    """A device's own name, its appliance's (Name = ${Value} since 2026-10-24); empty or KiCad's "~" is no name."""
    n = name_of(s, report)
    return n if n and n != "~" else None


def settings_of(s: Symbol) -> dict[str, str]:
    return {k: v for k, v in s.fields.items() if k not in NOT_SETTINGS and not k.startswith("Pin.") and v.strip()}


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


def compare(explicit, implicit, what: str, where: str, report: Report, code: str = "seam"):
    """The §3.12 test: both forms name one thing. Returns the resolved value or None."""
    if explicit is not None and implicit is not None:
        if explicit != implicit:
            report.error(f"{code}.disagree", f"{what}: the wire says {explicit!r}, the fallback says {implicit!r}", where)
            return None
        return explicit
    if explicit is not None:
        report.info(f"{code}.explicit_only", f"{what}: {explicit!r} by wire; no fallback resolves", where)
        return explicit
    if implicit is not None:
        report.info(f"{code}.implicit_only", f"{what}: {implicit!r} by fallback; no wire", where)
        return implicit
    report.missing(f"{code}.missing", f"{what}: not stated", where)
    return None


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
            source.symbols[s.ref] = Symbol(s.ref, s.lib_id, s.value, {**s.fields, **changed}, s.sheet)


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
    sm.railroad = {k.lower(): s.get(k) for k in ("Name", "Railroad", "Region", "Era", "Rulebook") if s.get(k)}
    if not s.get("Name"):
        sm.report.missing("railroad.name", "the Railroad symbol has no Name", loc(s))


def _processors(sm: Seams) -> None:
    for s in sm.source.where("STRUCTURE", "PROCESSOR"):
        name = name_of(s, sm.report)
        if not name:
            sm.report.missing("entity.name", "a processor has no Name; it is not written", loc(s))
            continue
        p = sm.processors.setdefault(name, Processor(name))
        p.syms.append(s)
        for attr, fld in (("board", "Board"), ("description", "Description")):
            v = s.get(fld)
            if v and getattr(p, attr) and getattr(p, attr) != v:
                sm.report.error("entity.conflict", f"processor {name}: {fld} {getattr(p, attr)!r} on one instance, {v!r} on another", loc(s))
            elif v:
                setattr(p, attr, v)
    for p in sm.processors.values():
        if not p.board:
            sm.report.missing("processor.board", f"processor {p.name}: no Board", loc(p.syms[0]))


def _anchor_of(sm: Seams, s: Symbol) -> Optional[str]:
    """The processor on a symbol's Processor net (explicit)."""
    net = sm.source.net_of(s.ref, "Processor")
    if not net:
        return None
    procs = [sm.source.symbols[p.ref] for p in net.others(s.ref) if sm.source.symbols[p.ref].kind == "PROCESSOR" and p.pin == "Processor"]
    p = one(procs, "processors on one Processor net", loc(s), sm.report, "processor.net")
    return name_of(p, sm.report) if p else None


def _one_in_scope(syms: list[Symbol], sheet: str) -> Optional[Symbol]:
    """The implicit scope rule of ADR 0009 §3.12: the one symbol on the sheet. (Widening it to ancestor sheets was
    withdrawn after the 2026-10-23 review: a processor alone on the root would silently own every unwired unit.)"""
    on_sheet = [s for s in syms if s.sheet == sheet]
    return on_sheet[0] if len(on_sheet) == 1 else None


def _one_processor_on_sheet(sm: Seams, sheet: str) -> Optional[str]:
    p = _one_in_scope(sm.source.where("STRUCTURE", "PROCESSOR"), sheet)
    return name_of(p, sm.report) if p else None


def _transports(sm: Seams) -> None:
    for s in sm.source.where("TRANSPORT"):
        name = name_of(s, sm.report)
        if not name:
            sm.report.missing("entity.name", "a transport has no Name; it is not written", loc(s))
            continue
        t = sm.transports.setdefault(name, Transport(name, s.kind))
        if t.kind != s.kind:
            sm.report.error("entity.conflict", f"transport {name}: Kind {t.kind} and {s.kind}", loc(s))
        for k, v in settings_of(s).items():
            if t.settings.get(k, v) != v:
                sm.report.error("entity.conflict", f"transport {name}: {k} {t.settings[k]!r} and {v!r}", loc(s))
            t.settings[k] = v
        t.instances[s.ref] = s
        explicit = _anchor_of(sm, s)
        # ADR 0009 §3.12: the Processor field; the OfficeUnit's processor for a code line transport (0005 S3)
        implicit = s.get("Processor") or None
        if implicit is None and _carries_codeline(sm, s) and len(sm.office_units) == 1:
            implicit = next(iter(sm.office_units.values())).processor
        anchor = compare(explicit, implicit, f"transport {name} anchored on", loc(s), sm.report, "transport.anchor")
        if anchor:
            if anchor not in sm.processors:
                sm.report.error("transport.anchor", f"transport {name}: anchor {anchor!r} is not a processor", loc(s))
            t.anchors.add(anchor)


def _carries_codeline(sm: Seams, transport_sym: Symbol) -> bool:
    net = sm.source.net_of(transport_sym.ref, "Transport")
    return bool(net) and any(sm.source.symbols[p.ref].role == "CODELINE_ENCODING" for p in net.others(transport_sym.ref))


def _transport_on_net(sm: Seams, s: Symbol) -> Optional[tuple[str, Symbol]]:
    net = sm.source.net_of(s.ref, "Transport")
    if not net:
        return None
    ts = [sm.source.symbols[p.ref] for p in net.others(s.ref) if sm.source.symbols[p.ref].role == "TRANSPORT" and p.pin == "Transport"]
    t = one(ts, "transports on one Transport net", loc(s), sm.report, "transport.net")
    return (name_of(t, sm.report), t) if t else None


def _encodings(sm: Seams) -> None:
    for s in sm.source.where("CODELINE_ENCODING") + sm.source.where("IO_ENCODING"):
        name = name_of(s, sm.report)
        if not name:
            sm.report.missing("entity.name", "a encoding has no Name; it is not written", loc(s))
            continue
        if name in sm.encodings:
            sm.report.error("entity.duplicate", f"two encodings named {name!r}", loc(s))
            continue
        e = Encoding(name, s.kind, s.role, s, settings_of(s))
        hit = _transport_on_net(sm, s)
        explicit = hit[0] if hit else None
        want_kind = TRANSPORT_OF_ENCODING.get(s.kind)
        implicit = s.get("Transport") or None
        if implicit is None and want_kind:
            of_kind = [t for t in sm.transports.values() if t.kind == want_kind]
            implicit = of_kind[0].name if len(of_kind) == 1 else None
        e.transport = compare(explicit, implicit, f"encoding {name} rides", loc(s), sm.report, "encoding.transport")
        if e.transport:
            t = sm.transports[e.transport]
            if want_kind and t.kind != want_kind:
                sm.report.error("encoding.kind", f"encoding {name} ({s.kind}) rides {t.name} ({t.kind}); {s.kind} pairs with {want_kind}", loc(s))
            # the instance it rides is the transport symbol on its net; that instance's anchor is the encoding's processor
            inst = hit[1] if hit else None
            if inst is not None:
                e.processor = _anchor_of(sm, inst)
            elif len(t.anchors) == 1:
                e.processor = next(iter(t.anchors))
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


def _codeline_in_folder(sm: Seams, sheet: str) -> Optional[str]:
    encs = [e.name for e in sm.encodings.values() if e.role == "CODELINE_ENCODING" and e.sym.sheet.startswith(sheet)]
    if len(encs) == 1:
        return encs[0]
    lines = [e.name for e in sm.encodings.values() if e.role == "CODELINE_ENCODING"]
    return lines[0] if len(lines) == 1 else None


def _interlockings(sm: Seams) -> None:
    for s in sm.source.where("STRUCTURE", "INTERLOCKING"):
        name = s.get("Name")
        if not name:
            sm.report.missing("interlocking.name", "an Interlocking symbol has no Name", loc(s))
            continue
        if name in sm.interlockings:
            sm.report.error("entity.duplicate", f"two interlockings named {name!r}", loc(s))
            continue
        ix = Interlocking(name, s)
        ix.processor = compare(_anchor_of(sm, s), _one_processor_on_sheet(sm, s.sheet), f"FieldUnit {name} runs on", loc(s), sm.report, "unit.processor")
        if ix.processor and ix.processor not in sm.processors:
            sm.report.error("unit.processor", f"FieldUnit {name}: {ix.processor!r} is not a processor", loc(s))
        ix.codeline = compare(_codeline_of(sm, s), _codeline_in_folder(sm, s.sheet), f"FieldUnit {name} on its line", loc(s), sm.report, "unit.codeline")
        sm.interlockings[name] = ix


def _unit_of_sheet(sm: Seams, sheet: str) -> Optional[Interlocking]:
    """The interlocking whose sheet is this sheet or an ancestor of it (the folder)."""
    hits = [ix for ix in sm.interlockings.values() if in_scope(ix.sym.sheet, sheet)]
    return max(hits, key=lambda ix: len(ix.sym.sheet)) if hits else None


def _houses(sm: Seams) -> None:
    for s in sm.source.where("STRUCTURE", "CONTROL_POINT"):
        cp = s.get("CP Name")
        if not cp:
            sm.report.missing("house.cp_name", "a House has no CP Name", loc(s))
            continue
        h = House(cp, s)
        ix = _unit_of_sheet(sm, s.sheet)
        if ix is None:
            sm.report.error("house.interlocking", f"house {cp}: no Interlocking on its sheet or above", loc(s))
            continue
        h.interlocking = ix.name
        if s.get("Milepost"):
            try:
                h.milepost = float(s.get("Milepost"))
            except ValueError:
                sm.report.error("house.milepost", f"house {cp}: Milepost {s.get('Milepost')!r} is not a number", loc(s))
        line = compare(_codeline_of(sm, s), ix.codeline, f"house {cp} is a station on", loc(s), sm.report, "house.codeline")
        h.codeline = line
        if line and ix.codeline and line != ix.codeline:
            sm.report.error("house.codeline", f"house {cp} sits on {line!r} but its interlocking {ix.name} is on {ix.codeline!r}", loc(s))
        mc = sm.source.net_of(s.ref, "MC")
        if mc:
            calls = [sm.source.symbols[p.ref] for p in mc.others(s.ref) if sm.source.symbols[p.ref].role == "APPLIANCE"]
            c = one(calls, "maintainer calls on one MC net", loc(s), sm.report, "house.mc")
            if c is not None:
                h.maintainer_call = qualify(name_of(c, sm.report), ix.name)
        if cp in ix.houses:
            sm.report.error("entity.duplicate", f"two houses named {cp!r} in {ix.name}", loc(s))
        ix.houses[cp] = h


def _office_units(sm: Seams) -> None:
    for s in sm.source.where("OFFICE_UNIT"):
        name = name_of(s, sm.report)
        if not name:
            sm.report.missing("entity.name", "a office unit has no Name; it is not written", loc(s))
            continue
        if name in sm.office_units:
            sm.report.error("entity.duplicate", f"two office units named {name!r}", loc(s))
            continue
        ou = OfficeUnit(name, s, s.get("Style"))
        ou.processor = compare(_anchor_of(sm, s), _one_processor_on_sheet(sm, s.sheet), f"OfficeUnit {name} runs on", loc(s), sm.report, "office.processor")
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
            owners.append(name_of(o, sm.report))
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
        n = Node(ua, s, ic=s.get("IC"), node_type=s.get("NodeType"))
        for attr, fld in (("input_bytes", "InputBytes"), ("output_bytes", "OutputBytes")):
            if s.get(fld):
                try:
                    setattr(n, attr, int(s.get(fld)))
                except ValueError:
                    sm.report.error("node.bytes", f"CMRInet Node {ua}: {fld} {s.get(fld)!r} is not a number", loc(s))
            else:
                sm.report.missing("node.bytes", f"CMRInet Node {ua}: no {fld}", loc(s))
        hit = _transport_on_net(sm, s)
        n.transport = compare(hit[0] if hit else None, s.get("Transport") or None, f"CMRInet Node {ua} on its line", loc(s), sm.report, "node.transport")
        if n.transport:
            t = sm.transports[n.transport]
            if ua in t.nodes:                                          # one entity on several sheets (ADR 0009 §3.9)
                have = t.nodes[ua]
                for attr in ("node_type", "input_bytes", "output_bytes", "ic"):
                    a, b = getattr(have, attr), getattr(n, attr)
                    if a and b and a != b:
                        sm.report.error("entity.conflict", f"CMRInet Node {ua} on {t.name}: {attr} {a!r} on one instance, {b!r} on another", loc(s))
                    elif b and not a:
                        setattr(have, attr, b)
                continue
            t.nodes[ua] = n


def _node_in_scope(sm: Seams, s: Symbol) -> Optional[str]:
    """Implicit bus for a CMRInet bit: the one node on the sheet, or the node its Node field names (ADR 0009 §3.12)."""
    nodes = [(t.name, n) for t in sm.transports.values() for n in t.nodes.values()]
    if s.get("Node"):
        hits = [f"{tn}/{n.ua}" for tn, n in nodes if n.ua == s.get("Node")]
        return hits[0] if len(hits) == 1 else None
    hit = _one_in_scope([n.sym for _, n in nodes], s.sheet)
    return next((f"{tn}/{n.ua}" for tn, n in nodes if hit is not None and n.sym.ref == hit.ref), None)


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
            implicit = _node_in_scope(sm, s)
        else:
            address = s.get("Address")
            implicit = s.get("Processor") or _one_processor_on_sheet(sm, s.sheet)
            if ic in ENCODING_OF_IC:
                address = _encoded_address(sm, s, address)
        d = Driver(s, ic, address, settings=settings_of(s), kind=s.kind, syms=[s])
        where = loc(s)
        d.owner = compare(_bus_owner(sm, s), implicit, f"driver {ic} {address or s.value!r} on a bus", where, sm.report, "driver.bus")
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
                    if first.settings != d.settings:
                        sm.report.error("entity.conflict", f"driver {address} on {p.name}: its symbols state different settings", where)
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
        number = s.get("Column")
        where = loc(s)
        if not number:
            sm.report.missing("column.number", "a PanelColumn has no Column number", where)
            continue
        c = Column(number, s)
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
            sm.report.missing("column.cp_name", f"column {number}: no CP Name; its interlocking {folder.name if folder else '?'} is read from the folder", where)
            c.interlocking = folder.name if folder else None
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
        dev = Device(s, appliance, styles_of(s), settings=settings_of(s), address=s.get("Address") or None)
        where = loc(s)
        scope: Optional[str] = None
        if s.role == "PANEL":
            col_net = sm.source.net_of(s.ref, "Column")
            cols = [sm.source.symbols[p.ref] for p in col_net.others(s.ref)] if col_net else []
            cols = [c for c in cols if c.role == "COLUMN"]
            col = one(cols, "columns on one Column net", where, sm.report, "device.column") if cols else None
            ou = next(iter(sm.office_units.values()), None) if len(sm.office_units) == 1 else None
            if col is not None and ou is not None:
                column = ou.columns.get(col.get("Column"))
                dev.column = column.number if column else None
                scope = column.interlocking if column else None
            elif s.get("Style") != "board" and col_net is None:
                sm.report.missing("device.column", f"panel {appliance} {s.value!r} is in no column", where)
            if scope is None:
                folder = _unit_of_sheet(sm, s.sheet)
                scope = folder.name if folder else None
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
                    dev.serves = qualify(device_name(m, sm.report) or "", ix.name)
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
                    dev.bindings.append(Binding(base(pin), hit[1], base(pin) in inverted))
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
                plan[(name_of(masts[0], sm.report), name_of(h, sm.report))] = h.get("Style")   # the trackplan head's Name is its letter
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
