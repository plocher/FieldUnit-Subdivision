"""The reference derivation (ADR 0011 §5, ADR 0012 §4): a Layout Data Model File's ``given`` and ``relations`` in, every
``derived`` map out, with the diagnostics about the model's facts.

It needs the file and nothing else: no netlist, no KiCad, no importer. Any writer (the KiCad importer today, Studio
later) writes ``given`` and ``relations`` and calls ``derive``; a ``derived`` already in the file is ignored and
rebuilt (ADR 0011 §3 item 4: any edit re-derives). Incomplete is not in error (§6): a fact the rules cannot reach for
want of a stated one is absent, reported at ``missing``; facts that contradict each other derive nothing and are
reported at ``error``. Every code is in the registry, ``schemas/layout-model/rules/diagnostics.json``, which also
gives its level.

What it derives, all from the track pins' stated adjacency (three-maps D5: every track pin's ``relations.<side>``
names every other track pin its wire reaches, so the relation is symmetric):

- **Circuits.** The connected components of that adjacency, joined through a switch's ports (C, N, R; a derail's C,
  R) and through nothing else, so they stop at every joint and end, whose sides are different pins. A component is
  named by the track circuit marker on it, or else by the ``TC`` of a switch in it (its OS circuit); two names on one
  component are an error. A component with neither is dark track. From them: each row's ``derived.circuits``, a
  switch's ``osCircuit``, a run's ``derived.circuit`` (geometry's ends name the pins), and ``track.links``: switch
  ports that meet with no joint or end between.
- **A mast's sides on a double signal joint** (ADR 0013 §6): a joint of Kind ``IRJ_SIGNALS`` keeps its sides ``A``
  and ``B`` and states ``relations.masts`` (``{"A": mast, "B": mast}``); each mast's ``governed`` side is the side its
  pin names and its ``approach`` the other, written on the mast as ``derived.circuits`` in the shape a single joint's
  row carries (``{"governed": circuit, "approach": circuit}``, ADR 0012 §8). A double joint belongs to no control
  point: ADR 0013 §4 puts block track outside every interlocking and §5 has automatic masts state no CP Name.
- **A mast states Kind** (ADR 0013 §5): ``CONTROLLED``, ``ABSOLUTE`` or ``PERMISSIVE``, a stated fact. A mast with
  none, or with another word, is reported ``mast.kind`` at missing; nothing is inferred from a CP Name or a plate.
  An ``ABSOLUTE`` or ``PERMISSIVE`` mast that states a CP Name is ``mast.control_point`` at warning: the field is not
  read, since an automatic mast belongs to no control point.
- **A mast that is not CONTROLLED over a powered switch** (ADR 0013 §5): an ``ABSOLUTE`` or ``PERMISSIVE`` mast whose
  governed circuit (the side its joint pin names) holds a powered switch's or derail's port (``grammar.is_powered``,
  §4: Style ``powered`` or ``dual``, or a CP Name; spring and hand-throw switches are not powered) is reported
  ``mast.powered`` at warning. A check, never a source: it sets nothing.
- **A virtual circuit's members** (ADR 0013 §7.2): a track circuit of Style ``virtual`` is the one indication of the
  circuits its ``Members`` lists, resolved into ``derived.members``. One that lists none is ``circuit.members`` at
  missing; a member that is no circuit of this interlocking is ``circuit.member`` at error (one of another
  interlocking is checked as a reference). A boundary circuit is named like any circuit (§10) and may be a member. Which station qualifies it, and that it is at one end of the block, is
  the ``blocks`` library's.
- **A sign states its rule for the track it stands on** (ADR 0013 §8): a policy row that is not a plate states its
  Kind and Direction as given and the track pins it is on; its circuit is ``derived.circuits.track``. One on no track
  is ``policy.track`` at missing. A ``GCOR_RULE_9_14`` sign's Direction is the current of traffic, ``LEFT`` or
  ``RIGHT``; any other is ``policy.direction`` at missing. That one block's signs agree with each other and with its
  masts is the ``blocks`` library's.
- **The regime of every piece of track** (ADR 0013 §7.1 and decision 3; the owner, 2026-11-10): the unit is the
  joint-bounded piece, track connectivity through nets and switch ports across every interlocking, cut at every
  joint. A piece's regime is the GCOR Rule marker on it (``reference.REGIMES``: CTC, TWC, DTC, yard limits, other
  than main track; stated, never derived from signals); else the regime inherited across a joint from the piece
  beside it, through pieces with none of their own. Interlocking track inherits like any other track: a control point
  can be under a control operator without being under Chapter 10 (GCOR 6.4.2, 9.12.2; the owner, 2026-11-10), so
  membership in an interlocking is no regime source. Errors, not guesses: two different markers on one piece,
  ``regime.conflict``; a piece with no marker reachable from two different regimes, ``regime.ambiguous``. A piece
  with no regime is ``regime.none`` at missing. A CTC piece whose head-block signals are all ``ABSOLUTE`` is
  ``regime.absolute`` at warning (§4). Interlocking limits (a ``CONTROLLED`` mast governs into the piece, or it holds
  a dispatcher-controlled switch's or derail's port; §13) are a derived fact independent of regime: which regimes an
  interlocking's limits lie under is ``regime.limits`` at info, never an error. Each interlocking's ``track.pieces``
  lists the pieces its track touches with the regime and how it was found. A station-to-station block (decision 2) is a piece that holds no dispatcher-controlled switch and is
  signalled: a ``GCOR_RULE_9_14`` sign, masts facing both ways, or ``ABSOLUTE`` ends; the ``blocks`` library computes
  it. A regime boundary is a plain joint with a marker each side, or a joint declared one (``given.RegimeBoundary``
  ``yes``, the owner 2026-11-11), which passes no regime: each side states its own or inherits from elsewhere. The
  ``END_CTC`` end is retired.
- **A boundary track circuit** (ADR 0013 §10; ``Appliance track_circuit``, Style ``boundary``) states ``relations.A``
  and ``.B``, the two nets at its joint. It names no circuit: the marker on each net does. Its ``derived.circuits``
  are the circuits on its pins, in A, B order: what it counts toward.
- **A plate requires a PERMISSIVE mast** (ADR 0013 §5): a policy row of Kind ``RULE_290_G`` or ``RULE_290_R`` states
  ``relations.mast``; one on no mast, or on a mast that is not ``PERMISSIVE``, is ``plate.mast`` at error.
- **Control points** by propagation from the houses (the owner, 2026-10-26; ADR 0012 §4). An ``ABSOLUTE`` or
  ``PERMISSIVE`` mast belongs to no control point (ADR 0013 §5: automatic masts state no CP Name; §4: block track is
  outside every interlocking): it derives no ``controlPoint``, under one house as under several, and no chain runs
  through it. A mast with no Kind keeps today's handling (``mast.kind`` reports it).
- **A mast states its atoms** (ADR 0003 rules 5 to 7; the owner, 2026-11-12): ``given.signal``, the signal number;
  ``relations.facing``, the way it faces; ``given.heads``, the head letters top down, a comma list. The Name is a label
  composed of them, which the KiCad importer decomposes and nothing here reads. The k-th letter is the k-th position,
  the field mast device's pin A, B, C top down. ``mast.heads`` at error: a head wired beyond the last letter;
  ``mast.letters`` at error: one letter on two masts of one signal facing one way (rule 6). A mast that states no
  atoms is incomplete: it derives no letters and no lever link, and the writer says so (the importer's ``mast.name``).
- **A head is a position on its mast** (issue #80; the owner, 2026-11-04 and 2026-11-09): a head device has no name;
  its ``relations.mast`` and ``relations.position`` name the field mast device and the pin, A, B, C top down, its IND
  wire reaches; it derives ``letter``, the mast's letter for that pin. Its Style is its model, the index into the head
  model table (``reference.head_model``): the head derives ``presents``, the table's head words; a Style with no row is
  ``head.model`` at missing. The mast derives ``positions``, keyed by pin, each with its ``letter`` and the words it
  ``presents`` (what any head on it presents), and ``demand`` from an explicit ``Indications`` list until #62
  derives it. A mast with no field mast device or no head wired is ``mast.device`` at missing; two heads on one pin
  presenting different words are ``head.position`` at info; a single-position mast whose head cannot present a
  demanded word is ``mast.presents`` at info; a mast with several positions waits on the policy table (``positions``).
- **A signal lever works the masts of its signal** (ADR 0003 rule 5; the owner, 2026-11-12): a desk lever of Style
  ``signal`` serves its number in its interlocking, and derives ``masts``, every mast there whose ``given.signal`` is
  that number; a number no mast states is ``lever.serves`` at error. A ``CONTROLLED`` mast whose signal number no
  desk signal lever serves is ``mast.lever`` at missing (what works it is not drawn yet, like ``switch.lever``); an
  ``ABSOLUTE`` or ``PERMISSIVE`` mast is automatic and has none, so a desk signal lever none of whose masts is
  ``CONTROLLED`` is ``lever.masts`` at missing, the complement (the owner, 2026-11-13: Corporal's lever 832 before
  the renumber of Railroad 520c509, its masts PERMISSIVE).
- **A train order board** (``Appliance train_order``; the owner, 2026-11-03 and 2026-11-08) is an operator-controlled,
  non-vital indicator used in Time Table and Train Order territory: never a signal in the interlocking sense, never
  in a route, never in a control point. It derives no ``controlPoint`` and no chain runs through it (the exclusion an
  automatic mast has, ADR 0013 §5). Its ``relations.station`` names a timetable station of ``layout.stations``; one
  that names none is ``train_order.station`` at missing. No mast rule, lever rule or code line token reads it: the
  fascia control is local. The trackplan symbol has no pins, Style ``single`` or ``double`` as drawn. Its faces are
  the pins of the field mast device (Appliance ``train_order_mast``) that serves it by Name: a head device or a train
  order lever (Appliance ``lever``, Style ``train_order``) whose IND wire reaches a face pin is that face's
  (``relations.mast`` and ``relations.face``), so a face exists when something is wired to its pin. A double board's
  face pins name directions, N or W and S or E (ADR 0003 D1, ``grammar.direction_of``); a single board's one face
  takes the direction the glyph is turned to on the sheet, ``relations.facing``. The board derives ``faces``, each
  with ``direction`` and ``indications``, the words it can show: CLEAR, which nothing asserted shows, and the word of
  each input its lever binds (the ``trainOrderInputs`` table the layout's Rulebook selects, ``reference_data``: STOP shows STOP, SLOW APPROACH), with the ranked ``inputs`` and the ``rest`` word FieldUnit sets a face up with. Which word a face
  shows at run time, the most restrictive asserted input winning, is FieldUnit's behaviour (its issue #44), not a
  model fact. A board no field mast device serves, or whose device has no face wired, is ``train_order.device`` at
  missing; a face with no lever is ``train_order.lever`` at missing (facts not yet drawn); a face that names no
  direction, a single board's two faces, or a face two levers serve is ``train_order.face`` at error. Whether a
  signal mast's glyph is turned the way its Name's side letter says is the KiCad importer's check (``geometry.facing``):
  the file states one facing, the Name's.
- **Consumers of another station's indications** (the owner, 2026-10-27): a ``track.consumers`` row is a one-sided
  reference, ``relations.indication`` the token it consumes (``Corporal:2NATK``); a track circuit's token names the
  circuit the row stands on.
- **The code line** is checked, not stored (the owner, 2026-10-28): what each station receives and must send is the
  domain library ``tools/railroad/codeline.py``'s, computed on demand; every token a consumer states (a desk lever's,
  a desk lamp's, a consumer row's) must be one an appliance of the named interlocking can report there.
- **A lamp, contact or actuator on the track** (#82; the owner, 2026-11-09): its ``relations.track`` names the track
  pins its one pin is wired to, so it stands on that piece of track. ``derived.track`` is the piece's name: the circuit
  that names it; else the name of an end of track on it (an industry); else a name made from one of its pins
  (``track@<pin>``), reported ``appliance.track.unnamed`` at info. ``derived.circuits.track`` is the circuit, absent
  where none names the piece: track with no circuit is track like any other. A circuit of another interlocking there
  is ``appliance.circuit`` at error. The relation is one-sided: no track pin names the appliance's pin back. The
  three are read alike; no rule tells an actuator from a lamp.
- **Block track across sheets** (ADR 0013 §7.1, amending ADR 0009 §3.12): a track net that joins two interlockings
  (a pin of one names a pin of the other) is block track and is accepted when it is plain track; a foreign marker's
  TC on it names the component as a marker would (Sargent's 834 joint has ``Corporal:834T`` on its side A). It stays
  ``reference.track`` at error when the joining net holds a dispatcher-controlled switch or derail port of either
  interlocking (``grammar.dispatcher_controlled``: regime ``powered`` or ``dual``): such a switch lies within a
  control point, never in block track (§4), and interlocking track leaves an interlocking at a NextCP, a regime
  boundary or an end.
  A ``local`` switch is the crew's, not the dispatcher's, and like a hand-throw, spring or electrically locked
  hand-throw switch it may lie in the block (the owner, 2026-11-09). A wire that joins the legs of two
  interlockings' switches with no joint between them is accepted when neither port is dispatcher-controlled (the
  owner, 2026-11-13: Corporal's and Sargent's switch 1 are two crew-worked switches on the Beet Loader spur): no
  interlocking claims track that only a non-dispatcher switch stands on. The net creates no consumer and no
  indication token: the block's token is the codeline
  library's by R12 (§7.2, §12, §18.1). Blocks and interlocking limits are not computed here (the ``blocks`` library).
- **NextCP pairing** and the **cross-interlocking reference** check. A NextCP whose track is also drawn through to
  another interlocking's track is redundant (ADR 0013 §7.1: inside CTC a NextCP is no longer needed; it stays for an
  interlocking whose neighbour is not drawn), reported ``next_cp.drawn`` at warning.
- **A derail** is a switch with the word ``derail`` in its Style, ports C and R (the owner, 2026-11-09). It owns no OS
  circuit: its ``TC`` is not read, and like a lamp or contact it gets ``derived.track`` and ``derived.circuits.track``,
  the piece its ports lie on. Its regime is a switch word (``grammar.regime``); a dependent derail takes its switch's.
  **A dependent derail states its switch** (ADR 0003 D8; the owner, 2026-11-13): ``relations.switch``, the switch or
  lock of its interlocking it follows, which the KiCad importer states from the drawn gang id and nothing here reads
  from a Name (``grammar.depends_on`` reads the relation). The switch derives ``derails``, its dependents. A stated
  switch that is no switch or lock of the interlocking is ``derail.switch`` at error, and the derail is read as drawn,
  on its own. What works a switch or derail is read from the lever devices named for it (``control_sources``):
  ``switch.lever``, ``switch.lever.desk``, ``switch.lock.local``, ``switch.lever.hand`` and ``derail.regime``.
- An OfficeUnit's columns (``house``, ``interlocking``), every device's ``serves``, a desk lamp's ``indications`` and
  ``expression`` (its ``Indication``, ``tools/layout_model/expression.py``), a lever's ``controls`` and ``indications``
  from its per-pin ``Control.X`` and ``Indication.X``.

A track pin is named as the file names it: a switch port, a marker's TC or a named row's side by qualified name
(``Luchessa:783.R``), an unnamed row's side by the row's id (``<id>.approach``).
"""
from __future__ import annotations

import copy
import json
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from tools.railroad import codeline

from . import expression, reference
from . import reference_data as refdata
from .grammar import GANG, HAND, POWERED, depends_on, direction_of, dispatcher_controlled, is_derail, is_powered, regime, regime_word, styles
from . import sort_key
from .report import Report

RULES = "0.1.0"                     # the derivation's version, stamped as provenance.rules (ADR 0011 §3, ADR 0012 §7)
REGISTRY = Path(__file__).resolve().parents[2] / "schemas" / "layout-model" / "rules" / "diagnostics.json"

SWITCH_PORTS = ("C", "N", "R")
DERAIL_PORTS = ("C", "R")
TRACK_LISTS = ("joints", "ends", "policies")
STANDS_ON_TRACK = ("lamp", "contact", "actuator")    # appliances that state the track they stand on (#82)
ROW_LISTS = TRACK_LISTS + ("consumers",)          # every row with an id; a consumer has track but no circuits of its own
JOINTS = frozenset({"IRJ", "IRJ_SIGNAL", "IRJ_SIGNALS"})
DOUBLE_SIDES = {"A": "B", "B": "A"}             # a double joint's side to the other (ADR 0013 §6)
MAST_KINDS = frozenset({"CONTROLLED", "ABSOLUTE", "PERMISSIVE"})   # what a mast states it is (ADR 0013 §5)
CURRENTS = frozenset({"LEFT", "RIGHT"})                            # a GCOR_RULE_9_14 sign's current of traffic (ADR 0013 §8)
REGIME_BY = ("marker", "inherited")                # how a piece's regime was found (ADR 0013 §7.1)
PLATES = frozenset({"RULE_290_G", "RULE_290_R"})                   # a plate on a mast's SIGNAL net (ADR 0013 §5)


@lru_cache(maxsize=1)
def registry() -> dict[str, dict[str, Any]]:
    """The rule-check registry (ADR 0012 §3.3): every code the derivation raises, with its level."""
    return json.loads(REGISTRY.read_text(encoding="utf-8"))["codes"]


def qualify(name: str, scope: str) -> str:
    """A reference is always the qualified name (ADR 0008 §4.5); a name already qualified keeps its scope."""
    return name if ":" in name else f"{scope}:{name}"


def foreign(name: str, scope: str) -> bool:
    """A name qualified with another interlocking's scope."""
    return ":" in name and name.partition(":")[0] != scope


def ports_of(appliance: dict[str, Any]) -> tuple[str, ...]:
    """A switch's track ports, a derail's two (the word ``derail`` in its Style); none for anything else."""
    g = appliance.get("given", {})
    if g.get("Appliance") != "switch":
        return ()
    return DERAIL_PORTS if is_derail(g) else SWITCH_PORTS


def track_pins(relations: dict[str, Any]) -> dict[str, list[str]]:
    """The track sides a thing states: every relation that is a list of pins."""
    return {k: v for k, v in relations.items() if isinstance(v, list)}


def strip(model: dict[str, Any]) -> dict[str, Any]:
    """The file with every ``derived`` map removed, recursively, and with what held nothing else (a link row, the
    ``links`` list) and the rules stamp gone: the facts a writer states."""
    def walk(v: Any) -> Any:
        if isinstance(v, dict):
            out = {}
            for k, x in v.items():
                if k == "derived":
                    continue
                y = walk(x)
                if y in ({}, []) and x not in ({}, []):
                    continue
                out[k] = y
            return out
        if isinstance(v, list):
            return [y for x in v if not ((y := walk(x)) in ({}, []) and x not in ({}, []))]
        return v
    out = walk(copy.deepcopy(model))
    out.get("provenance", {}).pop("rules", None)
    return out


def derive(model: dict[str, Any], reference_data: Optional[dict[str, Any]] = None) -> tuple[dict[str, Any], Report]:
    """``model`` with every ``derived`` map rebuilt from its ``given`` and ``relations``, and the diagnostics.
    ``reference_data`` is the user's own, layered over the shipped defaults (ADR 0012 §6): today
    ``{"indicationTokens": {<encoding Kind or "default">: {<class>: (<template>, ...)}}}``."""
    m = strip(model)
    d = _Derivation(m, reference_data or {})
    d.run()
    return m, d.report


# ------------------------------------------------------------------------------------------------------------ union

class _Union:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def add(self, x: str) -> None:
        self.parent.setdefault(x, x)

    def find(self, x: str) -> str:
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def join(self, a: str, b: str) -> None:
        self.parent[self.find(a)] = self.find(b)

    def __contains__(self, x: str) -> bool:
        return x in self.parent


# ----------------------------------------------------------------------------------------------- one interlocking

class _Plan:
    """One interlocking's track, as its relations state it."""

    def __init__(self, name: str, ix: dict[str, Any], report: "_Reporter") -> None:
        self.name, self.ix, self.r = name, ix, report
        self.appliances: dict[str, dict[str, Any]] = ix.get("appliances", {})
        self.track: dict[str, list[dict[str, Any]]] = ix.get("track", {})
        self.houses: dict[str, dict[str, Any]] = ix.get("houses", {})
        self.union = _Union()
        self.rows: dict[str, tuple[str, dict[str, Any]]] = {}        # pin prefix (name or id) -> (list, row)
        self.name_of: dict[str, Optional[str]] = {}                   # component root -> circuit, None for dark track
        self.namer: dict[str, dict[str, Any]] = {}                    # component root -> the marker or switch that names it
        self.cp: dict[int, Optional[str]] = {}                        # id(appliance or row) -> house

    def where(self, *parts: str) -> str:
        return "/".join(("interlockings", self.name) + parts)

    def house_paths(self, cp: str) -> tuple[str, ...]:
        """The model path of this interlocking's house named ``cp`` (names fold case), or none."""
        return tuple(self.where("houses", h) for h in self.houses if h.casefold() == cp.casefold())

    def pin(self, name: str, side: str) -> str:
        return f"{qualify(name, self.name)}.{side}"

    def row_prefix(self, row: dict[str, Any]) -> str:
        return row.get("name") or row.get("id", "")

    # -------------------------------------------------------------------------------------------- circuits

    def components(self) -> None:
        for name, a in self.appliances.items():
            pins = track_pins(a.get("relations", {}))
            for side, refs in pins.items():
                node = self.pin(name, side)
                self.union.add(node)
                for ref in refs:
                    self.union.join(node, ref)
            ported = [self.pin(name, p) for p in ports_of(a) if p in pins]
            for p in ported[1:]:
                self.union.join(ported[0], p)
        for kind in ROW_LISTS:
            for row in self.track.get(kind, []):
                prefix = self.row_prefix(row)
                self.rows[prefix] = (kind, row)
                for side, refs in track_pins(row.get("relations", {})).items():
                    node = f"{prefix}.{side}"
                    self.union.add(node)
                    for ref in refs:
                        self.union.join(node, ref)

    def region(self, node: str) -> Optional[str]:
        return self.union.find(node) if node in self.union else None

    def component(self, node: str) -> list[str]:
        """Every track pin in the node's connected component, the node included; none for a pin the track lacks."""
        r = self.region(node)
        return [n for n in self.union.parent if self.union.find(n) == r] if r else []

    def circuit(self, node: str) -> Optional[str]:
        r = self.region(node)
        return self.name_of.get(r) if r else None

    def name_circuits(self, consumed: dict[str, str], report: bool = True) -> None:
        """Each component's name: the marker on it, or a switch's TC (its OS circuit). ``consumed`` maps a consumer row's
        TC pin to the circuit whose indication it consumes, which names its component as a marker would."""
        add = self.r.add if report else (lambda *a, **k: None)
        named: dict[str, dict[str, set[str]]] = defaultdict(lambda: {"marker": set(), "os": set()})
        namer: dict[str, dict[str, Any]] = {}
        for name, a in self.appliances.items():
            g = a.get("given", {})
            pins = track_pins(a.get("relations", {}))
            if g.get("Appliance") == "track_circuit" and "TC" in pins and g.get("Style") != "boundary":   # a boundary names none (ADR 0013 §10)
                root = self.union.find(self.pin(name, "TC"))
                named[root]["marker"].add(qualify(name, self.name))
                namer[root] = a
            elif g.get("Appliance") == "switch" and g.get("TC") and not is_derail(g):     # a derail owns no OS circuit (the owner, 2026-11-09)
                port = next((p for p in ports_of(a) if p in pins), None)
                if port is None:
                    continue
                if "," in g["TC"]:
                    add("switch.tc_block", f"{self.name}: switch {name} lists several circuits in TC ({g['TC']}); a detection "
                        "block has no form in the model", self.where("appliances", name))
                    continue
                root = self.union.find(self.pin(name, port))
                named[root]["os"].add(qualify(g["TC"], self.name))
                namer.setdefault(root, a)
        for node, circuit in consumed.items():
            if node in self.union:
                named[self.union.find(node)]["marker"].add(circuit)
        for node in list(self.union.parent):                             # another sheet's marker on block track (ADR 0013 §7.1)
            thing, _, side = node.rpartition(".")
            if side == "TC" and foreign(thing, self.name):
                named[self.union.find(node)]["marker"].add(thing)
        self.name_of = {self.union.find(n): None for n in self.union.parent}
        self.namer = {}
        for root, names in named.items():
            markers, os_ = sorted(names["marker"]), sorted(names["os"])
            if len(markers) > 1 or len(os_) > 1:
                add("circuit.names", f"{self.name}: one circuit carries the names {', '.join(markers + os_)}; a joint is "
                    "missing or a TC is wrong", self.where())
                continue
            marker, os_name = (markers or [None])[0], (os_ or [None])[0]
            if marker and os_name and marker != os_name:
                add("circuit.name.disagree", f"{self.name}: the circuit {marker}: its marker says {marker!r}, a switch's "
                    f"TC says {os_name!r}", self.where())
                continue
            self.name_of[root] = marker or os_name
            if root in namer:
                self.namer[root] = namer[root]

    def stands_on(self, name: str) -> Optional[str]:
        """The track pin of a lamp, contact or actuator that states the track it stands on (#82); none for one that
        states no track."""
        a = self.appliances[name]
        on = a.get("given", {}).get("Appliance") in STANDS_ON_TRACK and a.get("relations", {}).get("track")
        return self.pin(name, "track") if on else None

    def piece(self, node: str) -> tuple[Optional[str], bool]:
        """The name of the piece of track a pin is on, and whether somebody stated it (the owner, 2026-11-09): the
        circuit that names the piece; else the name of an end of track on it (an industry), this interlocking's first
        by name; else a name made from one of its pins, ``track@<pin>``, a named thing's pin before a row's id, which
        nobody stated. A lamp's, contact's or actuator's own pin is no track pin and never makes the name. None for a
        pin the track lacks."""
        r = self.region(node)
        if r is None:
            return None, False
        if self.name_of.get(r):
            return self.name_of[r], True
        ends = sorted(row["name"] for prefix, (kind, row) in self.rows.items()
                      if kind == "ends" and row.get("name") and not foreign(row["name"], self.name)
                      and row.get("given", {}).get("Kind") != "NEXT_CP"
                      and any(self.region(f"{prefix}.{side}") == r for side in track_pins(row.get("relations", {}))))
        if ends:
            return ends[0], True
        own = {n for a in self.appliances if (n := self.stands_on(a))}
        pins = sorted((":" not in n, n) for n in self.component(node) if n not in own)
        return (f"track@{pins[0][1]}", False) if pins else (None, False)

    def consumers(self) -> list[dict[str, Any]]:
        return self.track.get("consumers", [])

    def _all_refs(self):
        for a in self.appliances.values():
            yield from track_pins(a.get("relations", {})).values()
        for _, row in self.rows.values():
            yield from track_pins(row.get("relations", {})).values()

    # --------------------------------------------------------------------------------------- control points

    def control_points(self) -> None:
        """Each appliance's and signal joint's control point (the owner, 2026-10-26).

        The houses are the roots. With one house it is every appliance's control point. With two or more, the stated
        ``CP`` fields and the maintainer calls' house are the roots, and the rest inherit along these edges: a gang's
        switch without a letter to its lettered switches (ADR 0003 D8) and a switch to the derails that state it
        (``relations.switch``); a switch to its OS circuit, the
        only chain an OS circuit follows; a mast and its signal joint, either way; a signal joint to the circuits on
        its two sides that hold no switch; a circuit across a plain joint to one that holds no switch; a virtual
        circuit's members to it. A stated field wins over every chain, silently, and stops the chains through it.
        Reached by chains from two houses and stating none is an error, and so is reached by none. A track circuit
        marker stands for its circuit."""
        houses = {h.casefold(): h for h in self.houses}
        apps = [(n, a) for n, a in self.appliances.items() if not _automatic_mast(a) and not _train_order(a)]   # no control point (ADR 0013 §5; the owner, 2026-11-03)
        joints = [row for row in self.track.get("joints", []) if row.get("given", {}).get("Kind") == "IRJ_SIGNAL"]

        def region(node: str) -> Optional[str]:
            r = self.region(node)
            return "r:" + r if r else None

        def key(name: str) -> str:
            return "a:" + name

        def node_of_app(name: str, a: dict[str, Any]) -> str:
            g = a.get("given", {})
            if g.get("Appliance") == "track_circuit" and g.get("Style") != "virtual" and region(self.pin(name, "TC")):
                return region(self.pin(name, "TC"))
            return key(name)

        things: list[tuple[str, dict[str, Any], str, str, str]] = []  # (node, entity, label for chains, what, where)
        for name, a in apps:
            things.append((node_of_app(name, a), a, name, f"{a.get('given', {}).get('Appliance') or 'appliance'} {name}",
                           self.where("appliances", name)))
        for row in joints:
            things.append(("j:" + row.get("id", ""), row, row.get("given", {}).get("Kind", ""), f"signal joint {row.get('id', '')}",
                           self.where("track", "joints", row.get("id", ""))))

        stated: dict[str, str] = {}
        origin: dict[str, str] = {}
        for node, e, label, what, where in things:
            cp = e.get("given", {}).get("CP Name")
            if not cp:
                continue
            h = houses.get(cp.casefold())
            if h is None:
                self.r.add("control_point.house", f"{self.name}: {what} names control point {cp!r}, which is no house of "
                           f"{self.name} ({', '.join(sorted(self.houses)) or 'none'})", where, (self.where(),))
                continue
            stated[node], origin[node] = h, label
        for name, a in apps:
            g = a.get("given", {})
            if g.get("Appliance") == "lamp" and g.get("Style") == "maintainer_call":
                calls = [cp for cp, h in self.houses.items() if h.get("relations", {}).get("maintainerCall") == qualify(name, self.name)]
                if len(calls) == 1:
                    if stated.get(key(name), calls[0]) != calls[0]:
                        self.r.add("control_point.disagree", f"{self.name}: lamp {name} is wired to house {calls[0]} and states "
                                   f"CP {stated[key(name)]!r}", self.where("appliances", name),
                                   (self.where("houses", calls[0]), *self.house_paths(stated[key(name)])))
                    stated[key(name)], origin[key(name)] = calls[0], name

        if len(self.houses) == 1:
            root = next(iter(self.houses))
            for _, e, *_ in things:
                self.cp[id(e)] = root
            return

        edges: dict[str, set[str]] = defaultdict(set)
        switches = {n: a for n, a in apps if a.get("given", {}).get("Appliance") == "switch"}
        switch_regions = {region(self.pin(n, p)) for n, a in switches.items() for p in ports_of(a) if region(self.pin(n, p))}
        for n, a in switches.items():
            for p in ports_of(a):
                if region(self.pin(n, p)):
                    edges[key(n)].add(region(self.pin(n, p)))
            lead = self.lead_of(n)
            if lead in switches and lead != n:
                edges[key(lead)].add(key(n))
        for row in joints:
            j = "j:" + row.get("id", "")
            mast = row.get("relations", {}).get("mast")
            if mast and not foreign(mast, self.name):
                m = mast.partition(":")[2]
                if self.appliances.get(m, {}).get("given", {}).get("Appliance") == "mast":
                    edges[j].add(key(m))
                    edges[key(m)].add(j)
            for side in ("governed", "approach"):
                r = region(f"{row.get('id', '')}.{side}")
                if r and r not in switch_regions:
                    edges[j].add(r)
        for row in self.track.get("joints", []):
            if row.get("given", {}).get("Kind") == "IRJ":
                p = self.row_prefix(row)
                ra, rb = region(f"{p}.A"), region(f"{p}.B")
                if ra and rb and ra != rb:
                    if rb not in switch_regions:
                        edges[ra].add(rb)
                    if ra not in switch_regions:
                        edges[rb].add(ra)
        circuit_regions = {c: "r:" + r for r, c in self.name_of.items() if c}
        for n, a in apps:
            g = a.get("given", {})
            if g.get("Appliance") == "track_circuit" and g.get("Style") == "virtual":
                for t in g.get("Members", "").split(","):
                    r = circuit_regions.get(qualify(t.strip(), self.name)) if t.strip() else None
                    if r:
                        edges[r].add(key(n))

        reach: dict[str, dict[str, str]] = defaultdict(dict)             # node -> house -> the stated thing it came from
        for seed, h in stated.items():
            seen, todo = {seed}, list(edges[seed])
            while todo:
                n = todo.pop()
                if n in seen or n in stated:
                    continue
                seen.add(n)
                reach[n].setdefault(h, origin[seed])
                todo.extend(edges[n])

        for node, e, label, what, where in things:
            if node in stated:
                self.cp[id(e)] = stated[node]
                continue
            found = reach.get(node, {})
            self.cp[id(e)] = next(iter(found)) if len(found) == 1 else None
            if node.startswith("j:") and e.get("relations", {}).get("mast"):
                continue                                                  # its mast reports for it
            if len(found) > 1:
                self.r.add("control_point.chains", f"{self.name}: {what} is reached from "
                           f"{' and '.join(f'{h} (by {via})' for h, via in sorted(found.items()))}; a CP Name on it settles which", where,
                           tuple(p for h in sorted(found) for p in self.house_paths(h)))
            elif not found:
                self.r.add("control_point.unreached", f"{self.name}: no house reaches {what}: no CP Name on it and no chain to one", where)
        for n, a in switches.items():
            lead = self.lead_of(n)
            if lead in switches and lead != n:
                mine, theirs = self.cp.get(id(a)), self.cp.get(id(switches[lead]))
                if mine and theirs and mine != theirs:
                    self.r.add("control_point.gang", f"{self.name}: switch {n} is on {mine} but its gang's {lead} is on {theirs}; "
                               "one gang is one lever", self.where("appliances", n),
                               (self.where("appliances", lead),))

    def lead_of(self, name: str) -> str:
        """The switch a switch or derail follows for its control point: a derail its stated switch (``relations.switch``;
        the owner, 2026-11-13), a lettered switch its gang's id (ADR 0003 D8); itself when it follows none."""
        if is_derail(self.appliances.get(name, {}).get("given", {})):
            return depends_on(name, self.appliances) or name
        return GANG.sub("", name)

    # -------------------------------------------------------------------------------------------------- write

    def mast_sides(self) -> dict[str, dict[str, Optional[str]]]:
        """Each mast on a double signal joint to its governed and approach circuits (ADR 0013 §6): governed is the
        circuit on the side its SIGNAL pin names, approach the circuit on the other side."""
        out: dict[str, dict[str, Optional[str]]] = {}
        for row in self.track.get("joints", []):
            if row.get("given", {}).get("Kind") != "IRJ_SIGNALS":
                continue
            prefix = self.row_prefix(row)
            for side, mast in row.get("relations", {}).get("masts", {}).items():
                if mast and not foreign(mast, self.name) and side in DOUBLE_SIDES:
                    out[mast.partition(":")[2]] = {"governed": self.circuit(f"{prefix}.{side}"),
                                                   "approach": self.circuit(f"{prefix}.{DOUBLE_SIDES[side]}")}
        return out

    def write(self) -> None:
        sides = self.mast_sides()
        for name, a in self.appliances.items():
            g = a.get("given", {})
            derived: dict[str, Any] = {}
            if g.get("Appliance") == "switch" and is_derail(g):                 # a derail owns no OS circuit: it lies in the circuit its ports are on (the owner, 2026-11-09)
                if (node := next((self.pin(name, p) for p in ports_of(a) if self.region(self.pin(name, p))), None)):
                    derived["track"] = self.piece(node)[0]
                    derived["circuits"] = {"track": c} if (c := self.circuit(node)) else None
            elif g.get("Appliance") == "switch":
                derived["osCircuit"] = next((c for p in ports_of(a) if (c := self.circuit(self.pin(name, p)))), None)
            if g.get("Appliance") == "mast" and name in sides:
                derived["circuits"] = sides[name]
            if g.get("Appliance") == "track_circuit" and g.get("Style") == "boundary":          # what it counts toward (ADR 0013 §10)
                derived["circuits"] = {p: self.circuit(self.pin(name, p)) for p in ("A", "B")}
            if g.get("Appliance") == "track_circuit" and g.get("Style") == "virtual":
                derived["members"] = [qualify(t.strip(), self.name) for t in g.get("Members", "").split(",") if t.strip()]
            if (node := self.stands_on(name)):                              # the piece it stands on, and its circuit (#82)
                derived["track"] = self.piece(node)[0]
                derived["circuits"] = {"track": c} if (c := self.circuit(node)) else None
            cp = self.cp.get(id(a))
            derived["controlPoint"] = f"{self.name}:{cp}" if cp else None
            _set_derived(a, derived)
        for kind in TRACK_LISTS:
            for row in self.track.get(kind, []):
                prefix = self.row_prefix(row)
                derived = {"circuits": {side: c for side in track_pins(row.get("relations", {}))
                                        if (c := self.circuit(f"{prefix}.{side}"))}}
                if row.get("given", {}).get("Kind") == "IRJ_SIGNAL":
                    cp = self.cp.get(id(row))
                    derived["controlPoint"] = f"{self.name}:{cp}" if cp else None
                _set_derived(row, derived)
        links = self.links()
        if links:
            self.track["links"] = links
        elif "links" in self.track:
            del self.track["links"]
        for run in self.ix.get("geometry", {}).get("track", []):
            ends = [run.get("relations", {}).get(k) for k in ("from", "to")]
            _set_derived(run, {"circuit": next((c for e in ends if e and (c := self.circuit(e))), None)})

    def links(self) -> list[dict[str, Any]]:
        """Switch ports that meet with no joint or end between them, with the circuit there."""
        out, seen = [], set()
        for name, a in self.appliances.items():
            pins = track_pins(a.get("relations", {}))
            for p in ports_of(a):
                if p not in pins:
                    continue
                group = frozenset([self.pin(name, p), *pins[p]])
                if group in seen:
                    continue
                seen.add(group)
                if any(self.rows.get(ref.rpartition(".")[0], ("policies",))[0] in ("joints", "ends") for ref in group):
                    continue
                at = sorted(ref for ref in group if self.is_switch_port(ref))
                if len(at) > 1:
                    out.append({"derived": _clean({"ports": at, "circuit": self.circuit(self.pin(name, p))})})
        return out

    def is_switch_port(self, ref: str) -> bool:
        thing, _, side = ref.rpartition(".")
        if foreign(thing, self.name):
            return side in SWITCH_PORTS
        a = self.appliances.get(thing.partition(":")[2]) if ":" in thing else None
        return a is not None and side in ports_of(a)

    # ------------------------------------------------------------------------------------------------- checks

    def checks(self) -> None:
        switch_regions = {self.region(self.pin(n, p)) for n, a in self.appliances.items() for p in ports_of(a)
                          if self.region(self.pin(n, p))}
        for row in self.track.get("joints", []):
            kind, p = row.get("given", {}).get("Kind"), self.row_prefix(row)
            a, b = ("governed", "approach") if kind == "IRJ_SIGNAL" else ("A", "B")
            ra, rb = self.region(f"{p}.{a}"), self.region(f"{p}.{b}")
            where = self.where("track", "joints", row.get("id", ""))
            if ra and ra == rb:
                self.r.add("joint.loop", f"{self.name}: a joint has one circuit ({self.circuit(f'{p}.{a}') or 'dark track'}) on both "
                           "sides; a joint elsewhere is missing", where)
            if kind == "IRJ_SIGNAL" and rb in switch_regions and ra not in switch_regions:
                self.r.add("joint.reversed", f"{self.name}: a signal joint has a switch on its approach side and none on its governed "
                           "side; governed is where the route it protects begins", where)
        for row in self.track.get("ends", []):
            g = row.get("given", {})
            where = self.where("track", "ends", row.get("id", ""))
            if g.get("Kind") == "NEXT_CP" and not g.get("Interlocking"):
                self.r.add("next_cp.interlocking", f"{self.name}: a NextCP states no Interlocking", where)
        for row in self.track.get("policies", []):
            g, where = row.get("given", {}), self.where("track", "policies", row.get("id", ""))
            if g.get("Kind") not in PLATES:                                                 # a sign states a rule for its track (ADR 0013 §8)
                if not track_pins(row.get("relations", {})):
                    self.r.add("policy.track", f"{self.name}: a {g.get('Kind') or 'policy'} sign stands on no track; a sign states its "
                               "rule for the track it stands on (ADR 0013 §8)", where)
                if g.get("Kind") == reference.CURRENT_OF_TRAFFIC and g.get("Direction") not in CURRENTS:
                    self.r.add("policy.direction", f"{self.name}: a GCOR_RULE_9_14 sign states {'Direction ' + repr(g['Direction']) if g.get('Direction') else 'no Direction'}; "
                               "the current of traffic is LEFT or RIGHT, the lever direction of the signals that govern with it (ADR 0013 §8)", where)
                continue
            mast = row.get("relations", {}).get("mast")
            m = self.appliances.get(mast.partition(":")[2]) if mast and not foreign(mast, self.name) else None
            if not mast:
                self.r.add("plate.mast", f"{self.name}: a {g['Kind']} plate is on no mast's SIGNAL wire", where)
            elif m is None or m.get("given", {}).get("Appliance") != "mast":
                self.r.add("plate.mast", f"{self.name}: a {g['Kind']} plate names {mast}, which is no mast of {self.name}", where)
            elif m.get("given", {}).get("Kind") != "PERMISSIVE":
                self.r.add("plate.mast", f"{self.name}: a {g['Kind']} plate is on mast {mast}, which is {m['given'].get('Kind') or 'of no Kind'}; "
                           "a plate requires a PERMISSIVE mast (ADR 0013 §5)", where, (self.where("appliances", mast.partition(":")[2]),))
        masts_of = defaultdict(int)
        governed: dict[str, str] = {}                                  # mast (qualified) -> the node its governed side is
        for row in self.track.get("joints", []):
            prefix = self.row_prefix(row)
            if row.get("relations", {}).get("mast"):
                masts_of[row["relations"]["mast"]] += 1
                governed[row["relations"]["mast"]] = f"{prefix}.governed"
            for side, mast in row.get("relations", {}).get("masts", {}).items():    # a double joint counts for each of its masts
                if mast:
                    masts_of[mast] += 1
                    governed[mast] = f"{prefix}.{side}"
        powered_at: dict[str, list[str]] = defaultdict(list)          # region -> the powered switches with a port on it
        for n, a in self.appliances.items():
            if is_powered(n, self.appliances):
                for p in ports_of(a):
                    if (r := self.region(self.pin(n, p))) and n not in powered_at[r]:
                        powered_at[r].append(n)
        letters_of_signal: dict[tuple[str, Optional[str]], dict[str, str]] = defaultdict(dict)
        own = {c for c in self.name_of.values() if c} | {qualify(k, self.name) for k, v in self.appliances.items()
                                                         if v.get("given", {}).get("Appliance") == "track_circuit"}   # what a Members may name: any circuit, a boundary too (ADR 0013 §10 names it like any circuit)
        for name, a in self.appliances.items():
            g = a.get("given", {})
            where = self.where("appliances", name)
            if g.get("Appliance") == "switch" and not any(p in track_pins(a.get("relations", {})) for p in ports_of(a)):
                self.r.add("switch.track", f"{self.name}: switch {name} has no track on any port", where)
            if g.get("Appliance") == "track_circuit" and g.get("Style") == "virtual":        # the block's one indication (ADR 0013 §7.2)
                members = [t.strip() for t in g.get("Members", "").split(",") if t.strip()]
                if not members:
                    self.r.add("circuit.members", f"{self.name}: virtual circuit {name} states no Members; a virtual circuit is the one "
                               "indication of the circuits it lists (ADR 0013 §7.2)", where)
                for t in members:
                    if not foreign(t, self.name) and qualify(t, self.name) not in own:
                        self.r.add("circuit.member", f"{self.name}: virtual circuit {name} lists {t} in Members, which is no circuit of "
                                   f"{self.name}", where)
            if (node := self.stands_on(name)):                              # a lamp, contact or actuator on the track (#82)
                kind, circuit = g["Appliance"], self.circuit(node)
                piece, stated = self.piece(node)
                if circuit and foreign(circuit, self.name):
                    self.r.add("appliance.circuit", f"{self.name}: {kind} {name} stands on {circuit}, a circuit of another "
                               "interlocking; it stands on a circuit of its own", where)
                elif piece and not stated:
                    self.r.add("appliance.track.unnamed", f"{self.name}: {kind} {name} stands on track nobody named, called "
                               f"{piece} here; a track circuit marker or a named end of track names it", where)
            if g.get("Appliance") != "mast":
                continue
            if g.get("Kind") not in MAST_KINDS:
                self.r.add("mast.kind", f"{self.name}: mast {name} states {'no Kind' if not g.get('Kind') else 'Kind ' + repr(g['Kind'])}; "
                           "a mast is CONTROLLED, ABSOLUTE or PERMISSIVE (ADR 0013 §5)", where)
            if _automatic_mast(a) and g.get("CP Name"):                                   # a stated fact not read (ADR 0013 §5)
                self.r.add("mast.control_point", f"{self.name}: mast {name} is {g['Kind']} and states CP Name {g['CP Name']!r}; an "
                           "automatic mast belongs to no control point (ADR 0013 §5), so the CP Name is not read", where)
            n = masts_of.get(qualify(name, self.name), 0)
            if n == 0:
                self.r.add("mast.joint", f"{self.name}: mast {name} stands on no signal joint", where)
            elif n > 1:
                self.r.add("mast.joints", f"{self.name}: mast {name} stands on {n} signal joints", where)
            if g.get("Kind") in MAST_KINDS - {"CONTROLLED"} and n == 1:                    # a check, never a source (ADR 0013 §5)
                over = powered_at.get(self.region(governed[qualify(name, self.name)]) or "", [])
                if over:
                    self.r.add("mast.powered", f"{self.name}: mast {name} is {g['Kind']} but its route passes powered "
                               f"{'switch' if len(over) == 1 else 'switches'} {', '.join(sorted(over, key=sort_key))} on "
                               f"{self.circuit(governed[qualify(name, self.name)]) or 'dark track'}; a mast over a powered switch "
                               "or derail is CONTROLLED (ADR 0013 §5)", where, tuple(self.where("appliances", s) for s in sorted(over, key=sort_key)))
            letters = head_letters(a)                                                   # the stated atoms, never the Name (the owner, 2026-11-12)
            if not letters:
                continue
            wired = sorted({d["relations"]["position"] for d in self.ix.get("devices", [])          # the positions heads are wired to (#80)
                            if d.get("given", {}).get("Appliance") == "head" and d.get("relations", {}).get("position")
                            and d["relations"].get("mast") == qualify(name, self.name)})
            pins = PINS[:len(letters)]                                                  # the k-th letter is the k-th pin, top down (#80)
            extra = [p for p in wired if p not in pins]
            if extra:
                self.r.add("mast.heads", f"{self.name}: mast {name} states {len(letters)} head{'s' * (len(letters) > 1)} "
                           f"({','.join(letters)}), but a head is wired to position{'s' * (len(extra) > 1)} {', '.join(extra)} of its field "
                           f"mast device, beyond pin {pins[-1]} (ADR 0003 rule 7; a head's position is the mast pin its IND reaches, "
                           "A, B, C top down, #80)", where)
            if g.get("signal"):
                signal = (g["signal"], a.get("relations", {}).get("facing"))               # one signal: the number and the way it faces (rule 5)
                for letter in letters:
                    other = letters_of_signal[signal].setdefault(letter, name)
                    if other != name:
                        self.r.add("mast.letters", f"{self.name}: signal {g['signal']} facing {signal[1] or 'an unstated way'} has head "
                                   f"{letter} on masts {other} and {name} (ADR 0003 rule 6)", where, (self.where("appliances", other),))

    # ------------------------------------------------------------------------------------- references

    def references(self) -> list[tuple[str, str, frozenset[str], str, str, frozenset[str]]]:
        """Every qualified name this interlocking states for another's thing: (kind, name, ports or sides it wires,
        how it is stated, where, the switch ports in the component the wire joins). One-sided (the owner, 2026-10-27):
        nothing is written back. A pin of another interlocking's thing (kind ``switch`` for a switch port, ``pin`` for
        a marker's TC, a boundary's side or a named row's side) is a track net drawn across sheets (ADR 0013 §7.1);
        the switch ports of its component, this interlocking's and the other's, decide whether it is block track."""
        out = []
        by_thing: dict[str, set[str]] = defaultdict(set)
        roots: dict[str, set[str]] = defaultdict(set)
        ports_of_root: dict[str, set[str]] = defaultdict(set)
        for node in list(self.union.parent):
            thing, _, side = node.rpartition(".")
            if self.is_switch_port(node):
                ports_of_root[self.union.find(node)].add(node)
            if foreign(thing, self.name) and thing not in self.rows:
                by_thing[thing].add(side)
                roots[thing].add(self.union.find(node))
        for thing, sides in sorted(by_thing.items()):
            kind = "switch" if sides & set(SWITCH_PORTS) else "pin"
            what = "the switch" if kind == "switch" else "the track circuit marker" if "TC" in sides else "the track pin"
            ports = frozenset(p for r in roots[thing] for p in ports_of_root[r])
            out.append((kind, thing, frozenset(sides), what, self.where(), ports))
        for prefix, (kind, row) in sorted(self.rows.items()):
            if row.get("name") and foreign(row["name"], self.name):
                out.append(("track", row["name"], frozenset(track_pins(row.get("relations", {}))),
                            f"the {row.get('given', {}).get('Kind', 'track row')}", self.where("track", kind, row.get("id", "")), frozenset()))
        for name, a in self.appliances.items():
            g = a.get("given", {})
            if g.get("Appliance") == "switch" and g.get("TC") and not is_derail(g) and foreign(g["TC"], self.name) and "," not in g["TC"]:
                out.append(("circuit", g["TC"], frozenset(), f"switch {name}'s TC", self.where("appliances", name), frozenset()))
            if g.get("Appliance") == "track_circuit" and g.get("Style") == "virtual":
                for t in g.get("Members", "").split(","):
                    if t.strip() and foreign(t.strip(), self.name):
                        out.append(("circuit", t.strip(), frozenset(), f"virtual circuit {name}'s Members",
                                    self.where("appliances", name), frozenset()))
        return out


# --------------------------------------------------------------------------------------------------------- the file

class _Reporter:
    """The report, with each code's level from the registry."""

    def __init__(self) -> None:
        self.report = Report()

    def add(self, code: str, text: str, where: str = "", parties: tuple[str, ...] = ()) -> None:
        """A finding names every entity it is about (ADR 0012 §3.3): ``where``, the primary one, then the other
        ``parties`` of a relationship."""
        entry = registry().get(code)
        if entry is None:
            raise KeyError(f"diagnostic code {code!r} is not in the registry {REGISTRY}")
        entities = tuple(dict.fromkeys(e for e in (where, *parties) if e))
        self.report.add(entry["level"], code, text, where, entities)


class _Derivation:
    def __init__(self, model: dict[str, Any], reference_data: dict[str, Any]) -> None:
        self.m = model
        self.ref = reference_data
        self.rd = refdata.Resolver(model, reference_data)   # the tables resolved per entity (ADR 0012 §6)
        self.r = _Reporter()
        self.report = self.r.report
        self.plans: dict[str, _Plan] = {}

    # ------------------------------------------------------------------------------------------- consumers

    def consumed(self, plan: _Plan) -> dict[str, str]:
        """Each consumer row's TC pin to the circuit its indication stands for, where the token names one circuit of
        the named interlocking (``codeline.circuit_of``)."""
        out = {}
        for row in plan.consumers():
            circuit = codeline.circuit_of(self.m, row.get("relations", {}).get("indication", ""))
            if circuit and "TC" in track_pins(row.get("relations", {})):
                out[f"{row.get('id', '')}.TC"] = circuit
        return out

    def resolve_consumers(self) -> None:
        """A consumer row states the token it consumes; whether a station sends it is ``codeline``'s check."""
        for a, plan in self.plans.items():
            for row in plan.consumers():
                if not row.get("relations", {}).get("indication"):
                    self.r.add("reference.indication", f"{a}: a consumer row states no indication",
                               plan.where("track", "consumers", row.get("id", "")))

    # Each kind of codeline.Problem as its diagnostic code (ADR 0012 §3.3).
    PROBLEM_CODES = {"interlocking": "reference.interlocking", "codeline": "reference.codeline",
                     "unresolved": "reference.unresolved", "station": "reference.station"}

    def codeline(self) -> None:
        """Every token a consumer states is one an appliance of the named interlocking can report, at one station: the
        domain library's own computation, so the check and what a generator reads are one definition (the owner,
        2026-10-28). An interlocking not in the file is a warning, one on no code line missing, a token no appliance
        reports an error."""
        for p in codeline.stations(self.m).problems:
            self.r.add(self.PROBLEM_CODES[p.kind], p.text, p.where, p.parties)

    def run(self) -> None:
        for name, ix in self.m.get("interlockings", {}).items():
            plan = _Plan(name, ix, self.r)
            plan.components()
            plan.name_circuits({}, report=False)
            plan.control_points()
            self.plans[name] = plan
        for plan in self.plans.values():
            plan.name_circuits(self.consumed(plan))
            plan.write()
            plan.checks()
        self.next_cps()
        self.resolve_references()
        self.regimes()
        self.resolve_consumers()
        self.columns()
        self.devices()
        self.desk()
        self.levers()
        self.codeline()
        self.derails()
        self.rd.resolve_layout()
        self.control_sources()
        self.positions()
        self.train_orders()
        self.reach()
        self.jmri_masts()
        if "provenance" in self.m:
            self.m["provenance"]["rules"] = RULES

    # -------------------------------------------------------------------------------------------- next cp

    def next_cps(self) -> None:
        """A NextCP names the interlocking its track leads to; that interlocking's NextCPs lead back as many times. One
        marked ``Style off_layout`` says its interlocking will never be drawn (ADR 0013 §21 gap 7; the owner, 2026-11-03):
        nothing is reported for it and it counts toward no pair, since nothing pairs back; the mark on one whose
        interlocking is in the file lies, ``next_cp.drawn_neighbour`` at warning. One beyond the layout without the mark
        is reported at info. One whose track is also drawn through to another interlocking's track is redundant,
        ``next_cp.drawn`` at warning (ADR 0013 §7.1: block track is drawn from one control point to the next and
        replaces the NextCP inside CTC; it stays for a neighbour that is not drawn)."""
        count: dict[tuple[str, str], int] = defaultdict(int)
        for a, plan in self.plans.items():
            for row in plan.track.get("ends", []):
                g = row.get("given", {})
                if g.get("Kind") == "NEXT_CP" and g.get("Interlocking") and not _off_layout(row):
                    count[(a, g["Interlocking"])] += 1
        for a, plan in self.plans.items():
            for row in plan.track.get("ends", []):
                g = row.get("given", {})
                if g.get("Kind") != "NEXT_CP":
                    continue
                if _off_layout(row) and g.get("Interlocking") in self.plans:
                    self.r.add("next_cp.drawn_neighbour", f"{a}: a NextCP to {g['Interlocking']} is marked off_layout, but {g['Interlocking']} "
                               f"is on this layout", plan.where("track", "ends", row.get("id", "")), (f"interlockings/{g['Interlocking']}",))
                drawn = sorted(x for n in plan.component(f"{plan.row_prefix(row)}.track") if (x := self.drawn_in_other(a, n)))
                if drawn:
                    self.r.add("next_cp.drawn", f"{a}: a NextCP{' to ' + g['Interlocking'] if g.get('Interlocking') else ''} stands on "
                               f"track that is drawn through to {', '.join(dict.fromkeys(x.partition(':')[0] for x in drawn))}'s "
                               f"({', '.join(drawn)}); inside CTC the drawn block replaces it (ADR 0013 §7.1)",
                               plan.where("track", "ends", row.get("id", "")),
                               tuple(dict.fromkeys(f"interlockings/{x.partition(':')[0]}" for x in drawn)))
        for (a, b), n in sorted(count.items()):
            if b not in self.plans:
                self.r.add("next_cp.off_layout", f"{a}: {n} NextCP{'s lead' if n > 1 else ' leads'} to {b}, which is not on this layout",
                           f"interlockings/{a}")
            elif count.get((b, a), 0) != n:
                self.r.add("next_cp.pair", f"{a} has {n} NextCP{'s' * (n > 1)} to {b}, but {b} has {count.get((b, a), 0)} back to {a}",
                           f"interlockings/{a}", (f"interlockings/{b}",))

    def drawn_in_other(self, a: str, ref: str) -> Optional[str]:
        """Where a track pin named in interlocking ``a``'s relations is another interlocking's drawn track (ADR 0013
        §7.1): a pin qualified for another interlocking, or an unnamed row's side whose id is a row of another plan in
        the file. The pin as ``<interlocking>:<pin>``, or None."""
        thing, _, side = ref.rpartition(".")
        if ":" in thing:
            return ref if foreign(thing, a) else None
        for b, plan in self.plans.items():
            if b != a and thing in plan.rows:
                return f"{b}:{ref}"
        return None

    # ----------------------------------------------------------------------------------------- references

    def _appliance_path(self, b: str, n: str) -> tuple[str, ...]:
        """The model path of interlocking ``b``'s appliance ``n``, when the file has it."""
        plan = self.plans.get(b)
        return (f"interlockings/{b}/appliances/{n}",) if plan is not None and n in plan.appliances else ()

    def dispatcher_port(self, ref: str) -> bool:
        """Whether a switch port, by its qualified name, is a dispatcher-controlled switch's or derail's (ADR 0013 §4,
        ``grammar.dispatcher_controlled``: regime ``powered`` or ``dual``). A port of a switch the file does not have
        cannot be shown not to be: it counts as one."""
        thing, _, side = ref.rpartition(".")
        b, _, n = thing.partition(":")
        plan = self.plans.get(b)
        return True if plan is None or n not in plan.appliances else dispatcher_controlled(n, plan.appliances)

    def resolve_references(self) -> None:
        """A qualified name for another interlocking's thing. A track net that joins two interlockings (a pin of one
        names a pin of the other) is block track, drawn across sheets (ADR 0013 §7.1): accepted when it is plain track,
        with no consumer and no token (the block's token is the codeline library's, R12). It is ``reference.track`` at
        error when the joining net holds a dispatcher-controlled switch or derail port of either interlocking: such a
        switch lies within a control point, never in block track (§4), and interlocking track leaves an interlocking
        at a NextCP, a regime boundary or an end (ADR 0009 §3.12, which §7.1 narrows to interlocking track). A local, hand-throw,
        spring or electrically locked hand-throw switch may lie in the block (the owner, 2026-11-09). A track row named for another interlocking is that error too (the
        owner, 2026-10-28). A circuit named in a field (a switch's TC, a virtual circuit's members) names one that
        exists: an interlocking not in the file is a warning, a circuit missing from one that is an error. Each finding
        names the referring thing, then the interlocking and appliance it names when the file has them."""
        for a, plan in self.plans.items():
            for kind, name, ports, what, where, switch_ports in plan.references():
                b, _, n = name.partition(":")
                target = (f"interlockings/{b}",) if b in self.plans else ()
                if kind in ("switch", "pin"):
                    controlled = sorted(p for p in switch_ports if self.dispatcher_port(p))
                    if controlled:
                        self.r.add("reference.track", f"{a}: {what} {name} joins this interlocking's track to {b}'s on a wire that holds "
                                   f"dispatcher-controlled switch port{'s' if len(controlled) > 1 else ''} {', '.join(controlled)}; a "
                                   "dispatcher-controlled switch or derail (powered or dual) lies within a control point, never in block "
                                   "track (ADR 0013 §4), and interlocking track leaves an interlocking at a NextCP, a regime "
                                   "boundary or an end (ADR 0009 §3.12)", where, target + self._appliance_path(b, n))
                    continue                                              # plain track across sheets: block track (§7.1)
                if kind == "track":
                    self.r.add("reference.track", f"{a}: {what} {name} joins this interlocking's track to {b}'s; track leaves an "
                               "interlocking at a NextCP, a regime boundary or an end, and another interlocking's state is only its indications",
                               where, target + self._appliance_path(b, n))
                    continue
                if b not in self.plans:
                    self.r.add("reference.interlocking", f"{a}: {what} {name} names {b}, which is no interlocking in this file", where)
                    continue
                plan_b = self.plans[b]
                circuits = {c for c in plan_b.name_of.values() if c} | {
                    f"{b}:{k}" for k, v in plan_b.appliances.items()
                    if v.get("given", {}).get("Appliance") == "track_circuit"}          # a boundary is named like any circuit (ADR 0013 §10)
                if name not in circuits:
                    self.r.add("reference.unresolved", f"{a}: {what} {name} names {b}, which has no circuit {n}", where, target)

    # -------------------------------------------------------------------------------------- office units

    # --------------------------------------------------------------------------------------------- regimes

    def _mast_kind(self, mast: str) -> Optional[str]:
        b, _, n = mast.partition(":")
        plan = self.plans.get(b)
        return plan.appliances.get(n, {}).get("given", {}).get("Kind") if plan else None

    def regimes(self) -> None:
        """The regime of every joint-bounded piece of track (ADR 0013 §7.1, decision 3; the owner, 2026-11-10). The
        unit is the piece: track connectivity through nets and switch ports across every interlocking, cut at every
        joint. A piece's regime is the GCOR Rule marker on it (``reference.REGIMES``); else the regime inherited across
        joints from the pieces beside it, through pieces with none of their own, so one marker covers a run cut into
        blocks or circuits, and a siding inside CTC limits is CTC (GCOR 10.1). Interlocking track inherits like any
        other track: a control point can be under a control operator without being under Chapter 10 (GCOR 6.4.2,
        9.12.2; the owner, 2026-11-10), so membership in an interlocking is no regime source. Errors, not guesses: two
        different markers on one piece are ``regime.conflict``; a piece with no marker reachable from two different
        regimes is ``regime.ambiguous``; such a piece gets no regime and passes none on. A joint declared a regime
        boundary (``given.RegimeBoundary`` ``yes``, any joint Kind; the owner, 2026-11-11) adds no adjacency: nothing
        inherits across it, and each side states its own regime or inherits from elsewhere. A piece with no regime is
        ``regime.none`` at missing. A CTC piece whose head-block signals (the masts that govern into it) are all
        ``ABSOLUTE`` is ``regime.absolute`` at warning: an automatic signal gives no authority and Chapter 10 gives
        signal-indication authority (§4). Interlocking limits are a derived fact independent of regime (GCOR glossary:
        the tracks between outer opposing absolute signals; §13), read here as a piece a ``CONTROLLED`` mast governs
        into or that holds a dispatcher-controlled switch's or derail's port (``grammar.dispatcher_controlled``): the
        regimes those pieces lie under are told at info, ``regime.limits``, one note per interlocking, never an error.
        Each interlocking's ``track.pieces`` lists the pieces its track touches, each named as the interlocking names
        its track (``piece``), with its circuit, its regime and how it was found (``marker``, ``inherited``). The
        current-of-traffic sign is a direction fact, not a regime, and may share a piece with one (§8)."""
        union = _Union()
        for plan in self.plans.values():
            for node in plan.union.parent:
                union.add(node)
                union.join(node, plan.union.find(node))
        touched: dict[str, dict[str, str]] = defaultdict(dict)                 # piece -> plan -> a node of that plan on it
        for a in sorted(self.plans):
            for node in sorted(self.plans[a].union.parent):
                touched[union.find(node)].setdefault(a, node)
        stated: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))   # piece -> Kind -> marker paths
        limits: dict[str, set[str]] = defaultdict(set)                           # piece -> the interlockings whose limits it lies in
        heads: dict[str, list[tuple[str, Optional[str]]]] = defaultdict(list)   # piece -> (mast, Kind) governing into it
        adjacent: dict[str, set[str]] = defaultdict(set)
        for a, plan in self.plans.items():
            for row in plan.track.get("policies", []):
                kind, node = row.get("given", {}).get("Kind"), f"{plan.row_prefix(row)}.track"
                if kind in reference.REGIMES and node in union:
                    stated[union.find(node)][kind].append(plan.where("track", "policies", row.get("id", "")))
            for n, app in plan.appliances.items():
                if dispatcher_controlled(n, plan.appliances):
                    for p in ports_of(app):
                        if (node := plan.pin(n, p)) in union:
                            limits[union.find(node)].add(a)
            for row in plan.track.get("joints", []):
                kind, p, rel = row.get("given", {}).get("Kind"), plan.row_prefix(row), row.get("relations", {})
                sides = ("governed", "approach") if kind == "IRJ_SIGNAL" else ("A", "B")
                roots = [union.find(f"{p}.{s}") for s in sides if f"{p}.{s}" in union]
                boundary = row.get("given", {}).get("RegimeBoundary", "").strip().casefold() == "yes"   # declared: passes no regime
                if len(roots) == 2 and roots[0] != roots[1] and not boundary:
                    adjacent[roots[0]].add(roots[1])
                    adjacent[roots[1]].add(roots[0])
                governs = {"governed": rel.get("mast")} if kind == "IRJ_SIGNAL" else rel.get("masts", {}) if kind == "IRJ_SIGNALS" else {}
                for side, mast in governs.items():
                    if mast and f"{p}.{side}" in union:
                        heads[union.find(f"{p}.{side}")].append((mast, self._mast_kind(mast)))
        for root, masts in heads.items():                                       # inside a home signal: interlocking limits (ADR 0013 §13)
            for mast, kind in masts:
                if kind == "CONTROLLED" and mast.partition(":")[0] in self.plans:
                    limits[root].add(mast.partition(":")[0])

        def name_of(root: str) -> tuple[str, str]:
            """The piece's name as the first interlocking on it names it, and that interlocking."""
            a, node = next(iter(touched[root].items()))
            return self.plans[a].piece(node)[0] or node, a

        regime: dict[str, tuple[str, str]] = {}                                 # piece -> (Kind, how)
        broken: set[str] = set()                                                # pieces whose regime is an error: none, and none passed on
        for root in sorted(stated, key=name_of):
            kinds, (name, a) = stated[root], name_of(root)
            paths = tuple(p for k in sorted(kinds) for p in kinds[k])
            if len(kinds) > 1:
                self.r.add("regime.conflict", f"{a}: the piece {name} carries two regimes, {' and '.join(sorted(kinds))}; a joint "
                           "is missing or a marker is wrong (ADR 0013 §7.1)", paths[0], paths[1:])
                broken.add(root)
            else:
                regime[root] = (next(iter(kinds)), "marker")
        reach: dict[str, set[str]] = defaultdict(set)
        for src, (kind, _) in regime.items():
            frontier, seen = [src], {src}
            while frontier:
                frontier = [n for r in frontier for n in adjacent[r] if n not in seen and n not in regime and n not in broken
                            and not seen.add(n)]
                for n in frontier:
                    reach[n].add(kind)
        for root in sorted(reach, key=name_of):
            kinds, (name, a) = reach[root], name_of(root)
            if len(kinds) == 1:
                regime[root] = (next(iter(kinds)), "inherited")
            else:
                self.r.add("regime.ambiguous", f"{a}: the piece {name} carries no regime marker and is reachable from "
                           f"{' and '.join(sorted(kinds))}; a marker on it or a boundary beside it is missing (ADR 0013 §7.1)",
                           self.plans[a].where())
                broken.add(root)
        for root in sorted(touched, key=name_of):
            if root not in regime and root not in broken:
                name, a = name_of(root)
                self.r.add("regime.none", f"{a}: the piece {name} is under no regime: no marker on it, no dispatcher-controlled "
                           "switch, and none to inherit across a joint (ADR 0013 §7.1)", self.plans[a].where())
        for root in sorted(regime, key=name_of):
            kind, how = regime[root]
            if kind == reference.CTC and heads[root] and all(k == "ABSOLUTE" for _, k in heads[root]):
                name, a = name_of(root)
                masts = ", ".join(m for m, _ in sorted(heads[root]))
                self.r.add("regime.absolute", f"{a}: the CTC piece {name} has ABSOLUTE head-block signals ({masts}); an automatic "
                           "signal gives no authority where Chapter 10 gives signal-indication authority (ADR 0013 §4)",
                           stated[root][kind][0] if root in stated else self.plans[a].where(),
                           tuple(self.plans[m.partition(':')[0]].where("appliances", m.partition(":")[2]) for m, _ in sorted(heads[root])
                                 if m.partition(":")[0] in self.plans))
        for a in sorted(self.plans):                                            # which regimes an interlocking's limits lie under: a fact, never an error
            under = sorted({regime[r][0] for r, names in limits.items() if a in names and r in regime})
            if under:
                self.r.add("regime.limits", f"{a}: its interlocking limits lie under {', '.join(under)}"
                           f"{' (' + ', '.join(reference.REGIMES[k] for k in under) + ')' if all(k in reference.REGIMES for k in under) else ''}",
                           self.plans[a].where())
        for a, plan in self.plans.items():
            rows = []
            for root, plans in touched.items():
                if a not in plans:
                    continue
                node = plans[a]
                kind, how = regime.get(root, (None, None))
                rows.append({"derived": _clean({"name": plan.piece(node)[0] or node, "circuit": plan.circuit(node), "regime": kind, "by": how})})
            rows.sort(key=lambda r: r["derived"]["name"])
            if rows:
                plan.track["pieces"] = rows
            elif "pieces" in plan.track:
                del plan.track["pieces"]

    def _house_by_cp(self, cp: str) -> Optional[tuple[str, str]]:
        hits = [(i, h) for i, ix in self.m.get("interlockings", {}).items() for h in ix.get("houses", {}) if h.casefold() == cp.casefold()]
        return hits[0] if len(hits) == 1 else None

    def _interlocking_by_name(self, name: str) -> Optional[str]:
        hits = [i for i in self.m.get("interlockings", {}) if i.casefold() == name.casefold()]
        return hits[0] if len(hits) == 1 else None

    def columns(self) -> None:
        """A column's ``CP Name`` names a house or an interlocking (the owner, 2026-10-28); without one, its
        interlocking is its sheet's (``relations.interlocking``). A house is matched first, so a house named like its
        interlocking (Luchessa) is the house. Its station depends on the interlocking's code line: on an AAR token line
        the station is the interlocking, so a house named is location only; on a line whose station is a house (US&S
        506) the column must resolve to a house: naming the interlocking is ``column.house``, naming nothing
        ``column.cp_name``. A house with two columns on a 506 line is two station addresses."""
        for ou_name, ou in self.m.get("officeUnits", {}).items():
            by_house: dict[tuple[str, str], list[str]] = defaultdict(list)
            for number, c in ou.get("columns", {}).items():
                where = f"officeUnits/{ou_name}/columns/{number}"
                cp = c.get("given", {}).get("CP Name")
                house, ixn = None, None
                if cp:
                    house = self._house_by_cp(cp)
                    ixn = house[0] if house else self._interlocking_by_name(cp)
                    if ixn is None:
                        self.r.add("column.house", f"column {number}: CP Name {cp!r} names no house and no interlocking", where)
                folder = ixn or c.get("relations", {}).get("interlocking")
                if folder and codeline.scope(self.m, folder) == "house":
                    if cp and house is None and ixn:
                        self.r.add("column.house", f"column {number}: CP Name {cp!r} names the interlocking, but {ixn}'s code line makes "
                                   f"each house a station ({', '.join(sorted(self.m['interlockings'][ixn].get('houses', {})))}); name one",
                                   where, (f"interlockings/{ixn}",))
                    elif not cp:
                        self.r.add("column.cp_name", f"column {number}: no CP Name, and {folder}'s code line makes each house a station; "
                                   "which house it is, is not stated", where, (f"interlockings/{folder}",))
                if house:
                    by_house[house].append(number)
                _set_derived(c, {"house": f"{house[0]}:{house[1]}" if house else None, "interlocking": ixn})
            for (ixn, cp), nums in by_house.items():
                if len(nums) > 1 and codeline.scope(self.m, ixn) == "house":
                    self.r.add("station.columns", f"house {cp} of {ixn} has columns {', '.join(nums)} on a US&S 506 line: two station "
                               "addresses", f"interlockings/{ixn}",
                               (f"interlockings/{ixn}/houses/{cp}", *(f"officeUnits/{ou_name}/columns/{n}" for n in nums)))

    # ------------------------------------------------------------------------------------------- devices

    def devices(self) -> None:
        """A device serves the appliance its ``Name`` names in its scope, a head device or a train order lever the mast
        device its IND wire reaches (``relations.mast``; the face, ``relations.face``, derives in ``train_orders``: the
        owner, 2026-11-03, 2026-11-08); a
        lamp consumes the tokens of its ``Indication`` expression, resolved in its scope (``lamp``). A lever's scope is
        its column's interlocking, else its own ``relations.interlocking``. A model board lamp (Appliance ``lamp``, Style
        ``board``) never uses a column: its scope is its own ``relations.interlocking``, the panel sheet it is drawn on
        (ADR 0009 §3.12). An appliance's indication lamps are not lamp devices but ``Indication.X`` pins on its lever, so
        they follow the lever's column (``desk``). Every ``lamp`` device is scoped as a board lamp today. A code lever
        serves the station, not an appliance."""
        for name, ix in self.m.get("interlockings", {}).items():
            for i, dev in enumerate(ix.get("devices", [])):
                g = dev.get("given", {})
                derived: dict[str, Any] = {}
                if g.get("Appliance") == "head" or (g.get("Appliance") == "lever" and "train_order" in styles(g)):
                    derived["serves"] = dev.get("relations", {}).get("mast")     # the mast device its IND wire reaches (the owner, 2026-11-03, 2026-11-08)
                elif g.get("Name"):
                    derived["serves"] = qualify(g["Name"], name)
                else:
                    self.r.add("device.serves", f"device {g.get('Appliance')}: no appliance name", f"interlockings/{name}/devices/{i}")
                if self._code_lever(g):
                    derived.pop("serves", None)
                _set_derived(dev, derived)
        for ou_name, ou in self.m.get("officeUnits", {}).items():
            for i, dev in enumerate(ou.get("devices", [])):
                g, rel = dev.get("given", {}), dev.get("relations", {})
                where = f"officeUnits/{ou_name}/devices/{i}"
                derived = {}
                if g.get("Appliance") == "lamp":
                    derived.update(self.lamp(g, rel.get("interlocking"), where))
                else:
                    scope = None
                    if rel.get("column"):
                        ou_of, _, number = rel["column"].partition(":")
                        col = self.m.get("officeUnits", {}).get(ou_of, {}).get("columns", {}).get(number)
                        if col is not None:
                            scope = col.get("derived", {}).get("interlocking") or col.get("relations", {}).get("interlocking")
                    scope = scope or rel.get("interlocking")
                    if g.get("Name") and scope and not self._code_lever(g):
                        derived["serves"] = qualify(g["Name"], scope)
                _set_derived(dev, derived)

    def lamp(self, g: dict[str, str], scope: Optional[str], where: str) -> dict[str, Any]:
        """A desk lamp's ``indications`` (the tokens it consumes, qualified in its scope) and ``expression`` (its
        ``Indication`` normalized, the tokens qualified), the owner, 2026-10-28. Without ``Indication`` the legacy
        ``IndicationToken`` is read instead (a comma list, each circuit given the K of an indication), reported at info so
        what is unconverted shows; with neither, ``lamp.token``."""
        name = g.get("Name", "")
        if g.get("Indication", "").strip():
            source = g["Indication"]
        elif g.get("IndicationToken", "").strip():
            template = codeline.templates(self.m, scope, self.ref.get("indicationTokens")).get("track_circuit", ("{name}K",))[0]
            legacy = [reference.indication_of(t.strip(), template) for t in g["IndicationToken"].split(",") if t.strip()]
            source = " | ".join(legacy)
            self.r.add("desk.legacy_token", f"panel lamp {name!r}: no Indication; read from the legacy IndicationToken "
                       f"{g['IndicationToken']!r} as {source}", where)
        else:
            self.r.add("lamp.token", f"panel lamp {name!r}: no Indication", where)
            return {}
        try:
            text, tokens = expression.normalize(source, lambda t: qualify(t, scope) if scope else t)
        except expression.ExpressionError as e:
            self.r.add("desk.expression", f"panel lamp {name!r}: Indication does not parse: {e}", where)
            return {}
        return {"indications": tokens, "expression": text} if scope else {}

    # ---------------------------------------------------------------------------------------------- desk

    def desk(self) -> None:
        """A desk lever's tokens are its per-pin fields (the owner, 2026-10-27, 2026-10-28): for each bound pin X,
        ``Control.X`` is a control (``783NWS``) and ``Indication.X`` an indication expression whose tokens the desk
        consumes (``!795WLK``); an empty field binds none (``Control.UNUSED``), and a bound pin with neither is reported
        (``desk.token``), never filled in from the lever's name. The lever serves an appliance of its interlocking: a
        switch or lock it works, a maintainer call, or a signal lever's masts (``lever.serves``); a signal lever whose
        masts are all automatic works nothing the dispatcher controls, ``lever.masts`` at missing (the complement of
        ``mast.lever``; the owner, 2026-11-13). Which station receives
        and sends what is the code line's (``codeline``); the code lever binds nothing of a station."""
        for ou_name, ou in self.m.get("officeUnits", {}).items():
            for i, dev in enumerate(ou.get("devices", [])):
                g, d = dev.get("given", {}), dev.get("derived", {})
                if g.get("Appliance") != "lever" or not d.get("serves"):
                    continue
                where = f"officeUnits/{ou_name}/devices/{i}"
                b, _, n = d["serves"].partition(":")
                what = f"lever {n}"
                controls, tokens = self.lever_tokens(g, dev.get("relations", {}).get("bindings", {}), b, what, where)
                _set_derived(dev, {**d, "controls": controls, "indications": tokens})
                ix = self.m.get("interlockings", {}).get(b)
                if ix is None:
                    continue
                masts = self._masts_of_signal(ix, b, n)
                if masts:                                                             # a signal lever works the masts of its signal (rule 5)
                    _set_derived(dev, {**dev["derived"], "masts": masts})
                    kinds = {m: ix["appliances"][m.partition(":")[2]].get("given", {}).get("Kind") for m in masts}
                    if "signal" in styles(g) and "CONTROLLED" not in kinds.values():       # the complement of mast.lever (the owner, 2026-11-13)
                        self.r.add("lever.masts", f"{what} is a signal lever on a column of the office, but no mast of signal {n} in {b} is "
                                   f"CONTROLLED ({', '.join(f'{m.partition(chr(58))[2]} is {k or 'of no Kind'}' for m, k in kinds.items())}); an "
                                   "automatic mast has no lever, so what the lever works is not drawn yet", where,
                                   tuple(f"interlockings/{b}/appliances/{m.partition(':')[2]}" for m in masts))
                elif n not in ix.get("appliances", {}):
                    self.r.add("lever.serves", f"{what} serves {d['serves']}, but {b} has no switch, lock, maintainer call or mast of "
                               f"signal {n}", where, (f"interlockings/{b}",))

    @staticmethod
    def _masts_of_signal(ix: dict[str, Any], b: str, n: str) -> list[str]:
        """The masts of interlocking ``ix`` (named ``b``) that state signal number ``n``, qualified and sorted: what a desk
        signal lever numbered ``n`` works (the owner, 2026-11-12: from the stated atom, never from a Name)."""
        apps = ix.get("appliances", {})
        return sorted((qualify(m, b) for m, a in apps.items()
                       if a.get("given", {}).get("Appliance") == "mast" and a["given"].get("signal") == n), key=sort_key)

    def levers(self) -> None:
        """A CONTROLLED mast is the dispatcher's (ADR 0013 §5): a desk signal lever of its signal number is on a column
        of the office, serving it. One with none is ``mast.lever`` at missing (what works it is not drawn yet, as
        ``switch.lever`` says of a powered switch): Sargent's 836NAB, 836SA and 836SB (the owner, 2026-11-12). An
        ABSOLUTE or PERMISSIVE mast is automatic and has no lever; a mast that states no signal number is incomplete
        and not asked."""
        served = {dev.get("derived", {}).get("serves") for ou in self.m.get("officeUnits", {}).values() for dev in ou.get("devices", [])
                  if dev.get("given", {}).get("Appliance") == "lever" and "signal" in styles(dev.get("given", {}))}
        for name, ix in self.m.get("interlockings", {}).items():
            for mast, a in ix.get("appliances", {}).items():
                g = a.get("given", {})
                if g.get("Appliance") != "mast" or g.get("Kind") != "CONTROLLED" or not g.get("signal"):
                    continue
                if qualify(g["signal"], name) not in served:
                    self.r.add("mast.lever", f"{name}: mast {mast} is CONTROLLED, signal {g['signal']}, but no desk signal lever {g['signal']} "
                               f"serves {name} on any column; what works it is not drawn yet", f"interlockings/{name}/appliances/{mast}",
                               (f"interlockings/{name}",))

    def derails(self) -> None:
        """A dependent derail states its switch (ADR 0003 D8; the owner, 2026-11-13): ``relations.switch``, the switch or
        lock of its own interlocking it follows, which the KiCad importer states from the drawn gang id; nothing here
        reads a Name. The switch derives ``derails``, its dependents, qualified and sorted. A stated switch that is no
        switch or lock of the interlocking (absent, another interlocking's, or itself a derail) is ``derail.switch`` at
        error; the derail is then read as drawn, on its own (``grammar.depends_on`` returns none for it)."""
        for b, plan in self.plans.items():
            dependents: dict[str, list[str]] = defaultdict(list)
            for n, a in plan.appliances.items():
                stated = a.get("relations", {}).get("switch")
                if not is_derail(a.get("given", {})) or not stated:
                    continue
                sb, _, sn = stated.rpartition(":")
                target = plan.appliances.get(sn, {}).get("given", {}) if sb in ("", b) else {}
                if target.get("Appliance") != "switch" or is_derail(target):
                    self.r.add("derail.switch", f"{b}: derail {n} states switch {stated}, which is no switch or lock of {b}; a dependent "
                               "derail follows a switch of its own interlocking (ADR 0003 D8)", plan.where("appliances", n), (plan.where(),))
                    continue
                dependents[sn].append(qualify(n, b))
            for sn, names in dependents.items():
                a = plan.appliances[sn]
                _set_derived(a, {**a.get("derived", {}), "derails": sorted(names, key=sort_key)})

    def control_sources(self) -> None:
        """What works each switch or derail, read from the lever devices named for it (the owner, 2026-11-09): a desk
        lever (an OfficeUnit device) or a field lever (an interlocking device: Local-Switch, Local-Lock, Local-Derail),
        each serving the appliance its Name names, Style ``switch`` or ``lock``. The regime (``grammar.regime``) says
        what to expect: ``powered`` a desk lever; ``dual`` the desk lever with a Local-Lock and Local-Switch for the
        crew's release and throw; ``local`` a Local-Switch alone; ``lock`` the dispatcher's lock lever and the same
        field pair, a Local-Lock asking the release and a Local-Switch throwing the model's points, the switch device
        reporting NWK/RWK (the owner, 2026-11-09: Christopher 813 and 817 are the reference); a hand-throw one nothing. A gang follower and a dependent derail are worked through their lead and are not
        read. Reported: a powered, dual or local one that no switch lever of either kind serves, ``switch.lever`` at
        missing (no control source yet), and so is a ``lock`` one with no Local-Switch; a ``local`` one a desk lever
        serves, ``switch.lever.desk`` at error; a ``dual`` or ``lock`` one with no Local-Lock, ``switch.lock.local`` at
        missing; a hand-throw one (``manual``,
        ``manual_sensed``, ``spring``) any lever serves, ``switch.lever.hand`` at error; a dependent derail drawn
        ``local`` or ``manual``, ``derail.regime`` at error (it takes its switch's regime)."""
        def levers_of(devices: list[dict[str, Any]]) -> dict[str, list[set[str]]]:
            """Served appliance -> each lever device's Style words. A lever works the switch unless it is a lock lever."""
            out: dict[str, list[set[str]]] = defaultdict(list)
            for dev in devices:
                g = dev.get("given", {})
                if g.get("Appliance") == "lever" and dev.get("derived", {}).get("serves"):
                    out[dev["derived"]["serves"]].append(set(styles(g)))
            return out

        desk = levers_of([dev for ou in self.m.get("officeUnits", {}).values() for dev in ou.get("devices", [])])
        for b, plan in self.plans.items():
            local = levers_of(self.m["interlockings"][b].get("devices", []))
            switches = {n for n, a in plan.appliances.items() if a.get("given", {}).get("Appliance") == "switch"}
            for n in sorted(switches, key=sort_key):
                g, q, where = plan.appliances[n]["given"], f"{b}:{n}", plan.where("appliances", n)
                what = f"derail {n}" if is_derail(g) else f"switch {n}"
                if (lead := depends_on(n, plan.appliances)):
                    if regime_word(g) in ("local", "manual"):
                        self.r.add("derail.regime", f"{b}: {what} is drawn {regime_word(g)} but follows switch {lead} (ADR 0003 D8) and "
                                   f"takes its regime, {regime(n, plan.appliances) or 'unstated'}; a dependent derail is not worked on its own", where,
                                   (plan.where("appliances", lead),))
                    continue
                if GANG.sub("", n) != n and GANG.sub("", n) in switches:                       # a gang follower
                    continue
                r, levers = regime(n, plan.appliances), desk[q] + local[q]
                words = sorted(set().union(*levers)) if levers else []
                if r in POWERED and not any("lock" not in st for st in levers):
                    self.r.add("switch.lever", f"{b}: {what} is {r} but no switch lever is named for it, on the desk or in the field; "
                               "what works it is not drawn yet", where)
                if r == "lock" and not any("lock" not in st for st in local[q]):
                    self.r.add("switch.lever", f"{b}: {what} is an electric lock but no Local-Switch is named for it; the crew's throw "
                               "of the points after the release is not drawn yet", where)
                if r == "local" and desk[q]:
                    self.r.add("switch.lever.desk", f"{b}: {what} is local, worked from its Local-Switch alone, but a desk lever "
                               f"({', '.join(sorted(set().union(*desk[q])))}) is named for it", where)
                if r in ("dual", "lock") and not any("lock" in st for st in local[q]):
                    self.r.add("switch.lock.local", f"{b}: {what} is {'dual' if r == 'dual' else 'an electric lock'} but has no Local-Lock; "
                               "the crew's release before throwing it by hand is not drawn yet", where)
                if r in HAND and levers:
                    self.r.add("switch.lever.hand", f"{b}: {what} is {r}, worked by hand, but a lever ({', '.join(words) or 'no Style'}) is "
                               "named for it", where)

    def lever_tokens(self, g: dict[str, str], bindings: dict[str, Any], b: str, what: str,
                     where: str) -> tuple[list[str], list[str]]:
        """(controls, indications) of a lever from its bound pins' ``Control.X`` and ``Indication.X``, each token
        qualified in ``b``, in binding order: an empty field binds none, a missing one is ``desk.token``, an expression
        that does not parse ``desk.expression``."""
        controls: list[str] = []
        indications: list[str] = []
        for pin in sorted(bindings):
            stated = [f for f in (f"Control.{pin}", f"Indication.{pin}") if f in g]
            if not stated:
                self.r.add("desk.token", f"{what}: pin {pin} is bound but states no Control.{pin} or Indication.{pin}", where)
                continue
            if g.get(f"Control.{pin}", "").strip():
                controls.append(qualify(g[f"Control.{pin}"].strip(), b))
            if g.get(f"Indication.{pin}", "").strip():
                try:
                    _, consumed = expression.normalize(g[f"Indication.{pin}"], lambda t: qualify(t, b))
                except expression.ExpressionError as e:
                    self.r.add("desk.expression", f"{what}: Indication.{pin} does not parse: {e}", where)
                    continue
                indications += [t for t in consumed if t not in indications]
        return controls, indications

    @staticmethod
    def _code_lever(g: dict[str, str]) -> bool:
        return g.get("Appliance") == "lever" and "code" in styles(g)

    # --------------------------------------------------------------------------------------------- heads

    def positions(self) -> None:
        """A head is a position on its mast (issue #80; the owner, 2026-11-04 and 2026-11-09): a head device's
        ``relations.mast`` and ``relations.position`` name the field mast device and the pin (A, B, C top down) its IND
        wire reaches. Its Style is its model: ``derived.presents`` is the head words of its model table,
        ``reference.head_model`` (the keys); a Style with no row is ``head.model`` at missing, what it presents unknown,
        never guessed. Any number of heads may share a pin (a fascia repeater of a mast hidden from the aisle, a head
        upgrade with both in service): the position presents what any of them presents, and two heads on one pin with
        different words are ``head.position`` at info, naming the pin, the heads and the difference: a normal
        configuration, never an error. The mast derives ``positions``, each with the words it presents, and ``demand``,
        the words it must show: an explicit ``Indications`` list, the settled exception, until the demand derivation lands
        with #62 (a mast that states none derives no demand and nothing is reported for it). ``positions`` is keyed by
        the pin (the owner, 2026-11-12): the mast's stated head letters give pins A, B, C their ``letter``, and the heads
        wired give each pin what it ``presents``; a head derives its pin's ``letter`` too. The pin is the physical fact
        every seam already uses (the device's wiring, a driver's key), the letter the railroad's name; keying by the
        letter would let A mean pin A on one mast and head A on another, which is the reading this retires. A mast no field mast
        device serves, or whose device has no head wired, is ``mast.device`` at missing. The match, demand ⊆ presents: on
        a mast with one position the head shows the mast's indication itself, so a demanded word the position does not
        present is ``mast.presents`` at info (what the head does with it is its table's indication filter, never an
        error); a mast with several positions shows its indication through the policy table, ``reference.policy``, resolved
        per position as ``shows`` (mast indication -> head word) where the rulebook has a row for the head count; none is
        seeded yet, so nothing is written or reported for it. A head on a train order mast's face (``relations.face``) is the
        board's (``train_orders``), not read here."""
        user = self.ref.get("headModels")
        for name, ix in self.m.get("interlockings", {}).items():
            served: dict[str, list[str]] = defaultdict(list)                        # mast -> its field mast device rows
            on: dict[tuple[str, str], list[tuple[int, dict[str, Any]]]] = defaultdict(list)   # (mast, position) -> its heads
            for i, dev in enumerate(ix.get("devices", [])):
                g, rel = dev.get("given", {}), dev.get("relations", {})
                serves = dev.get("derived", {}).get("serves") or ""
                if serves.partition(":")[0] != name:
                    continue
                mast, where = serves.partition(":")[2], f"interlockings/{name}/devices/{i}"
                if g.get("Appliance") == "mast":
                    served[mast].append(where)
                elif g.get("Appliance") == "head" and rel.get("position") and not rel.get("face"):
                    words = reference.presents(g.get("Style"), user)
                    if words is None:
                        self.r.add("head.model", f"{name}: the head at position {rel['position']} of {mast} is Style {g.get('Style')!r}, which "
                                   f"names no head model table row ({', '.join(sorted(reference.HEAD_MODELS, key=sort_key))}); "
                                   "what it presents is not known", where)
                    else:
                        _set_derived(dev, {**dev.get("derived", {}), "presents": words})
                    on[(mast, rel["position"])].append((i, dev))
            presented: dict[str, dict[str, list[str]]] = defaultdict(dict)          # mast -> position -> the words it presents
            for (mast, pos), heads in sorted(on.items(), key=lambda kv: (sort_key(kv[0][0]), sort_key(kv[0][1]))):
                union: list[str] = []
                for _, d in heads:
                    union += [w for w in d.get("derived", {}).get("presents", []) if w not in union]
                presented[mast][pos] = union
                sets = {tuple(d.get("derived", {}).get("presents", [])) for _, d in heads}
                if len(heads) > 1 and len(sets) > 1:
                    paths = tuple(f"interlockings/{name}/devices/{i}" for i, _ in heads)
                    mast_path = (f"interlockings/{name}/appliances/{mast}",) if mast in ix.get("appliances", {}) else ()
                    each = "; ".join(f"{d.get('given', {}).get('Style')} presents {', '.join(d.get('derived', {}).get('presents', [])) or 'nothing known'}"
                                     for _, d in heads)
                    self.r.add("head.position", f"{name}: position {pos} of {mast} has {len(heads)} heads that present different words "
                               f"({each}); the position presents {', '.join(union)}. A repeater or a head upgrade with both in service "
                               "is a normal configuration", paths[0], paths[1:] + mast_path)
            for mast, a in ix.get("appliances", {}).items():
                if a.get("given", {}).get("Appliance") != "mast":
                    continue
                where = f"interlockings/{name}/appliances/{mast}"
                letters = dict(zip(PINS, head_letters(a)))                              # the k-th stated letter is pin k (the owner, 2026-11-12)
                presents = presented.get(mast, {})
                pins = sorted(set(letters) | set(presents), key=sort_key)
                shows = self.rd.shows(len(pins)) or [None] * len(pins)          # the policy row for this head count, if any
                positions = {pin: _clean({"letter": letters.get(pin), "presents": presents.get(pin), "shows": shows[k]})
                             for k, pin in enumerate(pins)}
                for (m, pin), heads in on.items():                                      # a head derives its mast's letter for its pin
                    if m == mast:
                        for _, d in heads:
                            _set_derived(d, {**d.get("derived", {}), "letter": letters.get(pin)})
                demand = [w.strip() for w in a.get("given", {}).get("Indications", "").split(",") if w.strip()]
                _set_derived(a, {**a.get("derived", {}), "positions": positions, "demand": demand})
                if mast not in served:
                    self.r.add("mast.device", f"{name}: mast {mast} has no field mast device; a mast device named for it, with a head on "
                               "each position pin, is expected", where)
                elif not presents:
                    self.r.add("mast.device", f"{name}: mast {mast}: its field mast device has no head wired to a position pin", where,
                               tuple(served[mast]))
                if demand and len(positions) == 1 and presents:
                    (pos, words), = presents.items()
                    cannot = [w for w in demand if w not in words]
                    if cannot:
                        self.r.add("mast.presents", f"{name}: mast {mast} must show {', '.join(demand)}, but position {pos} presents "
                                   f"{', '.join(words)}: it cannot present {', '.join(cannot)}; what its head shows for them is its "
                                   "model table's business", where, tuple(f"interlockings/{name}/devices/{i}" for i, _ in on[(mast, pos)]))

    # -------------------------------------------------------------------------------------- train orders

    def train_orders(self) -> None:
        """A train order board stands at a timetable station (the owner, 2026-11-03): its ``relations.station`` names
        an entry of ``layout.stations`` (names fold case, as every name does). One that names none, or states none,
        is ``train_order.station`` at missing: the station is a fact not yet drawn, not a contradiction.

        Its faces are the pins of the field mast device (Appliance ``train_order_mast``) that serves it by Name (the
        owner, 2026-11-08): a head device or a train order lever whose IND wire reaches a face pin states
        ``relations.face``, so the faces are the pins something is wired to. A double board's face pins name
        directions (ADR 0003 D1); a single board's one face takes ``relations.facing``, the way its glyph is turned.
        Each face derives ``direction`` and ``indications``, the words it can show: CLEAR, which nothing asserted
        shows, and the word of each input its lever binds, with the ranked ``inputs`` and the ``rest`` word (the ``trainOrderInputs`` row the layout's Rulebook selects, resolved by ``reference_data``; the board's ``Rest`` and ``Shows.<input>`` override it). A board no device
        serves, or whose device has no face wired, is ``train_order.device`` at missing, and a face with no lever
        ``train_order.lever`` at missing: facts not yet drawn. A face that names no direction, a single board's second
        face, or a face two levers serve is ``train_order.face`` at error: wrong, not incomplete."""
        stations = {n.casefold() for n in self.m.get("layout", {}).get("stations", {})}
        for name, ix in self.m.get("interlockings", {}).items():
            masts: dict[str, list[int]] = defaultdict(list)                     # board -> its train_order_mast devices
            on_face: dict[tuple[str, str], dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))   # (board, face) -> heads, levers
            for i, dev in enumerate(ix.get("devices", [])):
                g, rel = dev.get("given", {}), dev.get("relations", {})
                serves = dev.get("derived", {}).get("serves") or ""
                if serves.partition(":")[0] != name:
                    continue
                board = serves.partition(":")[2]
                if g.get("Appliance") == "train_order_mast":
                    masts[board].append(i)
                elif rel.get("face") and g.get("Appliance") in ("head", "lever"):
                    on_face[(board, rel["face"])][g["Appliance"]].append(i)
            for n, a in ix.get("appliances", {}).items():
                if not _train_order(a):
                    continue
                here = f"interlockings/{name}/appliances/{n}"
                station = a.get("relations", {}).get("station")
                if not station:
                    self.r.add("train_order.station", f"{name}: train order board {n} states no Station", here)
                elif station.casefold() not in stations:
                    self.r.add("train_order.station", f"{name}: train order board {n} stands at station {station!r}, which the layout "
                               f"does not draw ({', '.join(sorted(self.m.get('layout', {}).get('stations', {}), key=sort_key)) or 'no stations'})",
                               here)
                if not masts.get(n):
                    self.r.add("train_order.device", f"{name}: train order board {n} has no field mast device; a train_order_mast device "
                               "named for it, with a head and a train_order lever on each face pin, is expected", here)
                    continue
                mast_paths = tuple(f"interlockings/{name}/devices/{i}" for i in masts[n])
                wired = sorted({f for (b, f) in on_face if b == n}, key=sort_key)
                if not wired:
                    self.r.add("train_order.device", f"{name}: train order board {n}: its field mast device has no face wired; a head "
                               "or a train_order lever on a face pin makes the face", here, mast_paths)
                    continue
                single = "double" not in styles(a.get("given", {}))
                faces: dict[str, Any] = {}
                for k, face in enumerate(wired):
                    parties = on_face[(n, face)]
                    paths = tuple(f"interlockings/{name}/devices/{i}" for kind in ("head", "lever") for i in parties[kind])
                    at = paths[0]
                    if single and k:
                        self.r.add("train_order.face", f"{name}: train order board {n} is single but faces {', '.join(wired)} are wired; "
                                   "a single board has one face", at, (here,) + paths[1:])
                        continue
                    direction = direction_of(face) if not single or direction_of(face) else a.get("relations", {}).get("facing")
                    if direction is None:
                        text = (f"{name}: train order board {n} face {face!r} names no direction; a double board's face pins are N, S, E or W"
                                if not single else
                                f"{name}: train order board {n} faces no direction: its glyph is turned a quarter; a single board faces "
                                "the way it is drawn, left or right")
                        self.r.add("train_order.face", text, at, (here,) + paths[1:])
                        continue
                    levers = parties["lever"]
                    if not levers:
                        self.r.add("train_order.lever", f"{name}: train order board {n} face {face} has no lever; a train_order lever with "
                                   "its IND on the face pin is expected", at, (here,) + paths[1:])
                    elif len(levers) > 1:
                        self.r.add("train_order.face", f"{name}: train order board {n} face {face} is served by {len(levers)} levers; one "
                                   "expected", f"interlockings/{name}/devices/{levers[0]}", (here,) + tuple(f"interlockings/{name}/devices/{i}" for i in levers[1:]))
                    bound = {b for i in levers for b in ix["devices"][i].get("relations", {}).get("bindings", {})}
                    faces[face] = {"direction": direction, **self.rd.train_order_face(bound, a.get("given", {}))}
                _set_derived(a, {**a.get("derived", {}), "faces": faces})

    # --------------------------------------------------------------------------------------------- reach

    def reach(self) -> None:
        """A driver whose IC is an encoding needs that I/O encoding on its processor (ADR 0009 §3.6). A processor reaches
        the transports it anchors and, through the code line of each FieldUnit it runs, that code line's transport
        (ADR 0008 §4.9: the reach is derived from the code line, never drawn as an anchor), written as
        ``derived.transports`` for consumers (ADR 0013 §11). An anchored instance that no I/O encoding and no code line
        rides, on a processor that already reaches that transport through a code line, duplicates what the code line
        says: ``transport.reach`` at info (ADR 0008 §4.9; the owner, 2026-11-03)."""
        layout = self.m.get("layout", {})
        for p, proc in layout.get("processors", {}).items():
            for address, d in proc.get("drivers", {}).items():
                ic = d.get("given", {}).get("IC")
                kind = reference.ENCODING_OF_IC.get(ic)
                if kind and not any(e.get("given", {}).get("Kind") == kind and e.get("relations", {}).get("processor") == p
                                    for e in layout.get("ioEncodings", {}).values()):
                    self.r.add("driver.encoding", f"driver {ic} {address} on {p}: no {kind} I/O encoding rides a transport anchored on {p}",
                               f"layout/processors/{p}/drivers/{address}", (f"layout/processors/{p}",))
        anchored: dict[str, set[str]] = defaultdict(set)                      # processor -> the transports it anchors
        for t, tr in layout.get("transports", {}).items():
            for p in tr.get("relations", {}).get("anchors", []):
                anchored[p].add(t)
        ridden: set[tuple[str, str]] = set()                                  # (transport, processor) an encoding rides
        for e in list(layout.get("codelines", {}).values()) + list(layout.get("ioEncodings", {}).values()):
            rel = e.get("relations", {})
            if rel.get("transport") and rel.get("processor"):
                ridden.add((rel["transport"], rel["processor"]))
        via: dict[str, dict[str, list[tuple[str, str]]]] = defaultdict(lambda: defaultdict(list))   # processor -> transport -> (FieldUnit, code line)
        for name, ix in self.m.get("interlockings", {}).items():
            rel = ix.get("relations", {})
            e = layout.get("codelines", {}).get(rel.get("codeline")) if rel.get("codeline") else None
            t = e.get("relations", {}).get("transport") if e else None
            if t and rel.get("processor"):
                via[rel["processor"]][t].append((name, rel["codeline"]))
        for p, proc in layout.get("processors", {}).items():
            proc.setdefault("derived", {})["transports"] = sorted(anchored[p] | set(via[p]), key=sort_key)
            for t in sorted(anchored[p] & set(via[p]), key=sort_key):
                if (t, p) in ridden:
                    continue
                units = sorted(via[p][t], key=lambda u: sort_key(u[0]))
                lines = sorted({c for _, c in units}, key=sort_key)
                self.r.add("transport.reach", f"processor {p} anchors an {t} instance nothing rides; its FieldUnit{'s' * (len(units) > 1)} "
                           f"{', '.join(x for x, _ in units)} already reach{'es' * (len(units) == 1)} {t} through code line"
                           f"{'s' * (len(lines) > 1)} {', '.join(lines)}",
                           f"layout/transports/{t}", (f"layout/processors/{p}",) + tuple(f"interlockings/{x}" for x, _ in units))

    # ------------------------------------------------------------------------------------- JMRI signal mast drivers

    def jmri_masts(self) -> None:
        """A JMRI signal mast driver (IC an encoding, Kind ``SIGNALMAST``) is a whole-mast consumer (the owner,
        2026-11-05, issue #96): it takes the mast's indication for the positions on its net. The device rows whose
        bindings reach it say which: a mast device's bound position pins, or the face of a head whose own pin reaches it
        (the owner, 2026-11-10); written as ``derived.mast`` and ``derived.positions``. It publishes on the topic the
        JMRI encoding's ``Topic`` prefixes and its ``Address`` ends (``derived.topic``; without an Address the tail is
        the published name, whose form is issue #99's, so nothing is written). Its JMRI signal system, the
        folder under JMRI's xml/signals whose aspect names it publishes (the owner, 2026-11-11), is its own
        ``JMRI.SignalSystem``, else its encoding's (``derived.jmriSignalSystem``): neither stated is
        ``driver.jmri.signal_system`` at missing; a system no table names (``reference.signal_systems``) is
        ``driver.signal_system.unknown`` at error."""
        layout = self.m.get("layout", {})
        reached: dict[str, dict[str, Any]] = {}                                  # processor/address -> {mast, positions}
        for name, ix in self.m.get("interlockings", {}).items():
            for dev in ix.get("devices", []):
                g, rel = dev.get("given", {}), dev.get("relations", {})
                if g.get("Appliance") not in ("mast", "train_order_mast", "head"):
                    continue
                for pin, routes in rel.get("bindings", {}).items():
                    for route in (routes if isinstance(routes, list) else [routes]):
                        parts = route.split("/")
                        if len(parts) != 3:
                            continue
                        hit = reached.setdefault(f"{parts[0]}/{parts[1]}", {"mast": None, "positions": set()})
                        if g.get("Appliance") == "head":
                            hit["mast"] = rel.get("mast")
                            for k in ("face", "position"):                   # a face's head, or a position's (#80)
                                if rel.get(k):
                                    hit["positions"].add(rel[k])
                        else:
                            hit["mast"] = dev.get("derived", {}).get("serves")
                            hit["positions"].add(pin)
        systems = reference.signal_systems(self.ref.get("aspectNames"))
        for p, proc in layout.get("processors", {}).items():
            for address, d in proc.get("drivers", {}).items():
                g = d.get("given", {})
                if reference.ENCODING_OF_IC.get(g.get("IC")) is None or g.get("Kind") != "SIGNALMAST":
                    continue
                where = f"layout/processors/{p}/drivers/{address}"
                enc = next((e for e in layout.get("ioEncodings", {}).values()
                            if e.get("given", {}).get("Kind") == reference.ENCODING_OF_IC[g["IC"]] and e.get("relations", {}).get("processor") == p), {})
                derived: dict[str, Any] = {}
                hit = reached.get(f"{p}/{address}")
                if hit and hit["mast"]:
                    derived["mast"] = hit["mast"]
                    derived["positions"] = sorted(hit["positions"], key=sort_key)
                if g.get("Address") and enc.get("given", {}).get("Topic"):
                    derived["topic"] = enc["given"]["Topic"] + g["Address"]
                system = g.get("JMRI.SignalSystem") or enc.get("given", {}).get("JMRI.SignalSystem")
                if not system:
                    self.r.add("driver.jmri.signal_system", f"driver {g['IC']} {address} on {p}: no JMRI.SignalSystem on it or on its JMRI encoding; "
                               "the aspect names it publishes are not stated", where)
                elif system not in systems:
                    self.r.add("driver.signal_system.unknown", f"driver {g['IC']} {address} on {p}: signal system {system!r} names no "
                               f"aspect name table ({', '.join(sorted(systems))})", where)
                else:
                    derived["jmriSignalSystem"] = system
                    ix_name, _, mast = (derived.get("mast") or "").partition(":")
                    kind = self.m.get("interlockings", {}).get(ix_name, {}).get("appliances", {}).get(mast, {}).get("given", {}).get("Kind")
                    derived["aspectNames"] = self.rd.aspect_names(system, kind)     # indication -> the name it publishes
                _set_derived(d, derived)


PINS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"                   # the field mast device's position pins, top down (#80)


def head_letters(appliance: dict[str, Any]) -> list[str]:
    """A mast's stated head letters top down (``given.heads``, a comma list; the owner, 2026-11-12); none when it states
    none. The k-th letter is the field mast device's k-th pin."""
    return [x.strip() for x in appliance.get("given", {}).get("heads", "").split(",") if x.strip()]


def _off_layout(row: dict[str, Any]) -> bool:
    """A NextCP marked ``Style off_layout``: its interlocking will never be drawn (ADR 0013 §21 gap 7)."""
    return row.get("given", {}).get("Style") == "off_layout"


def _automatic_mast(appliance: dict[str, Any]) -> bool:
    """A mast that states Kind ``ABSOLUTE`` or ``PERMISSIVE``: automatic, of no control point (ADR 0013 §5)."""
    g = appliance.get("given", {})
    return g.get("Appliance") == "mast" and g.get("Kind") in MAST_KINDS - {"CONTROLLED"}


def _train_order(appliance: dict[str, Any]) -> bool:
    """A train order board (``Appliance train_order``; the owner, 2026-11-03): never in a control point, a route or a
    mast rule."""
    return appliance.get("given", {}).get("Appliance") == "train_order"


def _clean(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v not in (None, "", [], {})}


def _set_derived(entity: dict[str, Any], derived: dict[str, Any]) -> None:
    """Absent is absent (ADR 0008 §4.7): an empty value and an empty map are not written."""
    d = {k: (_clean(v) if isinstance(v, dict) else v) for k, v in derived.items()}
    d = _clean(d)
    if d:
        entity["derived"] = d
    else:
        entity.pop("derived", None)
