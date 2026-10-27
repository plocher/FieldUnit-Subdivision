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
- **Control points** by propagation from the houses (the owner, 2026-10-26; ADR 0012 §4).
- **Stations.** ``derived.indications`` and ``derived.controls`` on each station as its code line's encoding defines
  it (``reference.station_of``): each house on a US&S 506 line, the interlocking on an AAR token line. Indications are
  the tokens of the appliances and circuits whose control point the house is, named by the encoding through the
  reference data (``reference.indication_tokens``); controls are the desk levers' bindings that end in S, sent to the
  station of the column the lever sits in.
- **Consumers of another station's indications** (the owner, 2026-10-27): a ``track.consumers`` row is a one-sided
  reference, ``relations.indication`` the token it consumes (``Corporal:2NATK``). It resolves against the indications
  the named station sends; a track circuit's token names the circuit the row stands on.
- **NextCP pairing** and the **cross-interlocking reference** check.
- An OfficeUnit's columns (``house``, ``interlocking``) and every device's ``serves`` and ``shows``.

A track pin is named as the file names it: a switch port, a marker's TC or a named row's side by qualified name
(``Luchessa:783.R``), an unnamed row's side by the row's id (``<id>.approach``).
"""
from __future__ import annotations

import copy
import json
import re
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from . import reference
from .report import Report

RULES = "0.1.0"                     # the derivation's version, stamped as provenance.rules (ADR 0011 §3, ADR 0012 §7)
REGISTRY = Path(__file__).resolve().parents[2] / "schemas" / "layout-model" / "rules" / "diagnostics.json"

SWITCH_PORTS = ("C", "N", "R")
DERAIL_PORTS = ("C", "R")
TRACK_LISTS = ("joints", "ends", "policies")
ROW_LISTS = TRACK_LISTS + ("consumers",)          # every row with an id; a consumer has track but no circuits of its own
POWERED = frozenset({"powered", "dual"})           # switch Styles with a lever and NWK/RWK (GLOSSARY: powered switch)
LOCKED = frozenset({"lock"})                       # an electric lock: WLK/WLQK, not NWK/RWK (the owner, 2026-10-27)
LEVER = re.compile(r"^\d+")
JOINTS = frozenset({"IRJ", "IRJ_SIGNAL"})
# ADR 0003: a mast is its signal (lever and side) plus its heads' letters, ascending (rules 6 and 7).
MAST_NAME = re.compile(r"^(0?[1-9]\d{0,3}[LRNSEW])([A-Z]+)$")
# ADR 0003 D8: a gang id is a switch name less its trailing letter; the switch named by the id alone leads the gang.
GANG = re.compile(r"(?<=\d)[A-Z]$")


@lru_cache(maxsize=1)
def registry() -> dict[str, dict[str, Any]]:
    """The diagnostic registry (ADR 0012 §3.3): every code the derivation raises, with its level."""
    return json.loads(REGISTRY.read_text(encoding="utf-8"))["codes"]


def qualify(name: str, scope: str) -> str:
    """A reference is always the qualified name (ADR 0008 §4.5); a name already qualified keeps its scope."""
    return name if ":" in name else f"{scope}:{name}"


def foreign(name: str, scope: str) -> bool:
    """A name qualified with another interlocking's scope."""
    return ":" in name and name.partition(":")[0] != scope


def styles(given: dict[str, str]) -> list[str]:
    return sorted(x.strip() for x in given.get("Style", "").split(",") if x.strip())


def ports_of(appliance: dict[str, Any]) -> tuple[str, ...]:
    """A switch's track ports, a derail's two (Style ``derail``); none for anything else."""
    g = appliance.get("given", {})
    if g.get("Appliance") != "switch":
        return ()
    return DERAIL_PORTS if g.get("Style") == "derail" else SWITCH_PORTS


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
        self.by_house: dict[str, set[str]] = {}                       # house -> the tokens of what its control point is
        self.cp: dict[int, Optional[str]] = {}                        # id(appliance or row) -> house

    def where(self, *parts: str) -> str:
        return "/".join(("interlockings", self.name) + parts)

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
            if g.get("Appliance") == "track_circuit" and "TC" in pins:
                root = self.union.find(self.pin(name, "TC"))
                named[root]["marker"].add(qualify(name, self.name))
                namer[root] = a
            elif g.get("Appliance") == "switch" and g.get("TC"):
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

    # ------------------------------------------------------------------------------------------- indications

    def indications(self, templates: dict[str, tuple[str, ...]]) -> dict[str, Optional[str]]:
        """Each house's office indications (``derived.indications``), and every token this interlocking's station sends,
        mapped to the circuit it indicates (None for a token of an appliance). A house sends the tokens of what its
        control point is: its own circuits (a marker's or, with none, the switch whose TC names it), its powered
        switches and electric locks that lead their gang, its signal levers, its maintainer calls and other lamps, and its
        virtual circuits. A dependent derail has no tokens of
        its own (GLOSSARY: dependent derail); the rest is pending (manual and independent switches, gang followers, a
        mast's own token)."""
        by_house: dict[str, set[str]] = defaultdict(set)
        sent: dict[str, Optional[str]] = {}

        def send(house: Optional[str], cls: str, circuit: Optional[str] = None, **names: str) -> None:
            if not house or cls not in templates:
                return
            for t in templates[cls]:
                token = reference.indication_of(names["name"], t) if t.endswith("{name}K") else t.format(**names)
                by_house[house].add(token)
                sent[token] = circuit

        for root, circuit in self.name_of.items():
            if circuit and not foreign(circuit, self.name) and root in self.namer:
                bare = circuit.partition(":")[2]
                send(self.cp.get(id(self.namer[root])), "track_circuit", circuit, name=bare)
        switches = {n for n, a in self.appliances.items() if a.get("given", {}).get("Appliance") == "switch"}
        for name, a in self.appliances.items():
            g = a.get("given", {})
            house = self.cp.get(id(a))
            leads = GANG.sub("", name) == name or GANG.sub("", name) not in switches
            if g.get("Appliance") == "switch" and LOCKED & set(styles(g)) and leads:
                send(house, "lock", name=name)
            elif g.get("Appliance") == "switch" and POWERED & set(styles(g)) and leads:
                send(house, "switch", name=name)
            elif g.get("Appliance") == "mast" and MAST_NAME.match(name):
                send(house, "signal", lever=LEVER.match(name).group(0))
            elif g.get("Appliance") == "lamp" and g.get("Style") == "maintainer_call":
                send(house, "maintainer_call", name=name)
            elif g.get("Appliance") == "lamp":
                send(house, "lamp", name=name)
            elif g.get("Appliance") == "track_circuit" and g.get("Style") == "virtual":
                send(house, "track_circuit", qualify(name, self.name), name=name)
        self.by_house = {h: by_house.get(h, set()) for h in self.houses}
        return sent

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
        switch without a letter to its lettered switches and derails (ADR 0003 D8); a switch to its OS circuit, the
        only chain an OS circuit follows; a mast and its signal joint, either way; a signal joint to the circuits on
        its two sides that hold no switch; a circuit across a plain joint to one that holds no switch; a virtual
        circuit's members to it. A stated field wins over every chain, silently, and stops the chains through it.
        Reached by chains from two houses and stating none is an error, and so is reached by none. A track circuit
        marker stands for its circuit."""
        houses = {h.casefold(): h for h in self.houses}
        apps = list(self.appliances.items())
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
            cp = e.get("given", {}).get("CP")
            if not cp:
                continue
            h = houses.get(cp.casefold())
            if h is None:
                self.r.add("control_point.house", f"{self.name}: {what} names control point {cp!r}, which is no house of "
                           f"{self.name} ({', '.join(sorted(self.houses)) or 'none'})", where)
                continue
            stated[node], origin[node] = h, label
        for name, a in apps:
            g = a.get("given", {})
            if g.get("Appliance") == "lamp" and g.get("Style") == "maintainer_call":
                calls = [cp for cp, h in self.houses.items() if h.get("relations", {}).get("maintainerCall") == qualify(name, self.name)]
                if len(calls) == 1:
                    if stated.get(key(name), calls[0]) != calls[0]:
                        self.r.add("control_point.disagree", f"{self.name}: lamp {name} is wired to house {calls[0]} and states "
                                   f"CP {stated[key(name)]!r}", self.where("appliances", name))
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
            lead = GANG.sub("", n)
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
                for t in g.get("IndicationToken", "").split(","):
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
                           f"{' and '.join(f'{h} (by {via})' for h, via in sorted(found.items()))}; a CP field on it settles which", where)
            elif not found:
                self.r.add("control_point.unreached", f"{self.name}: no house reaches {what}: no CP field on it and no chain to one", where)
        for n, a in switches.items():
            lead = GANG.sub("", n)
            if lead in switches and lead != n:
                mine, theirs = self.cp.get(id(a)), self.cp.get(id(switches[lead]))
                if mine and theirs and mine != theirs:
                    self.r.add("control_point.gang", f"{self.name}: switch {n} is on {mine} but its gang's {lead} is on {theirs}; "
                               "one gang is one lever", self.where("appliances", n))

    # -------------------------------------------------------------------------------------------------- write

    def write(self) -> None:
        for name, a in self.appliances.items():
            g = a.get("given", {})
            derived: dict[str, Any] = {}
            if g.get("Appliance") == "switch":
                derived["osCircuit"] = next((c for p in ports_of(a) if (c := self.circuit(self.pin(name, p)))), None)
            if g.get("Appliance") == "track_circuit" and g.get("Style") == "virtual":
                derived["members"] = [qualify(t.strip(), self.name) for t in g.get("IndicationToken", "").split(",") if t.strip()]
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
            g, p = row.get("given", {}), self.row_prefix(row)
            where = self.where("track", "ends", row.get("id", ""))
            if g.get("Kind") == "END_CTC":
                pins = track_pins(row.get("relations", {}))
                if self.circuit(f"{p}.DARK") or ("CTC" in pins and not self.circuit(f"{p}.CTC")):
                    self.r.add("end_ctc.sides", f"{self.name}: END CTC has {self.circuit(f'{p}.DARK') or 'a circuit'} on DARK or dark "
                               "track on CTC; CTC is the side under the dispatcher's control", where)
            if g.get("Kind") == "NEXT_CP" and not g.get("Interlocking"):
                self.r.add("next_cp.interlocking", f"{self.name}: a NextCP states no Interlocking", where)
        masts_of = defaultdict(int)
        for row in self.track.get("joints", []):
            if row.get("relations", {}).get("mast"):
                masts_of[row["relations"]["mast"]] += 1
        letters_of_signal: dict[str, dict[str, str]] = defaultdict(dict)
        for name, a in self.appliances.items():
            g = a.get("given", {})
            where = self.where("appliances", name)
            if g.get("Appliance") == "switch" and not any(p in track_pins(a.get("relations", {})) for p in ports_of(a)):
                self.r.add("switch.track", f"{self.name}: switch {name} has no track on any port", where)
            if g.get("Appliance") != "mast":
                continue
            n = masts_of.get(qualify(name, self.name), 0)
            if n == 0:
                self.r.add("mast.joint", f"{self.name}: mast {name} stands on no signal joint", where)
            elif n > 1:
                self.r.add("mast.joints", f"{self.name}: mast {name} stands on {n} signal joints", where)
            m = MAST_NAME.match(name)
            if m is None:
                self.r.add("mast.grammar", f"{self.name}: mast {name} is not a signal and its head letters (ADR 0003); not checked", where)
                continue
            heads = sorted(a.get("heads", {}))
            if heads and list(m.group(2)) != heads:
                self.r.add("mast.heads", f"{self.name}: mast {name} names heads {m.group(2)}, but the heads drawn on it are "
                           f"{''.join(heads)} (ADR 0003 rule 7)", where)
            for letter in m.group(2):
                other = letters_of_signal[m.group(1)].setdefault(letter, name)
                if other != name:
                    self.r.add("mast.letters", f"{self.name}: signal {m.group(1)} has head {letter} on masts {other} and {name} "
                               "(ADR 0003 rule 6)", where)

    # ------------------------------------------------------------------------------------- references

    def references(self) -> list[tuple[str, str, frozenset[str], str, str]]:
        """Every qualified name this interlocking states for another's thing: (kind, name, ports or sides it wires,
        how it is stated, where). One-sided (the owner, 2026-10-27): nothing is written back."""
        out = []
        by_thing: dict[str, set[str]] = defaultdict(set)
        for refs in self._all_refs():
            for ref in refs:
                thing, _, side = ref.rpartition(".")
                if foreign(thing, self.name) and thing not in self.rows:
                    by_thing[thing].add(side)
        for thing, sides in sorted(by_thing.items()):
            kind = "marker" if "TC" in sides else "switch"
            out.append((kind, thing, frozenset(sides), "the track circuit marker" if kind == "marker" else "the switch", self.where()))
        for prefix, (kind, row) in sorted(self.rows.items()):
            if row.get("name") and foreign(row["name"], self.name):
                out.append(("track", row["name"], frozenset(track_pins(row.get("relations", {}))),
                            f"the {row.get('given', {}).get('Kind', 'track row')}", self.where("track", kind, row.get("id", ""))))
        for name, a in self.appliances.items():
            g = a.get("given", {})
            if g.get("Appliance") == "switch" and g.get("TC") and foreign(g["TC"], self.name) and "," not in g["TC"]:
                out.append(("circuit", g["TC"], frozenset(), f"switch {name}'s TC", self.where("appliances", name)))
            if g.get("Appliance") == "track_circuit" and g.get("Style") == "virtual":
                for t in g.get("IndicationToken", "").split(","):
                    if t.strip() and foreign(t.strip(), self.name):
                        out.append(("circuit", t.strip(), frozenset(), f"virtual circuit {name}'s IndicationToken",
                                    self.where("appliances", name)))
        return out

    def sides(self) -> dict[str, frozenset[str]]:
        """The ports or sides each named thing of this interlocking has: a switch's by its Style, a marker's TC, a named
        row's wired sides."""
        out: dict[str, frozenset[str]] = {}
        for name, a in self.appliances.items():
            g = a.get("given", {})
            if g.get("Appliance") == "switch":
                out[name] = frozenset(ports_of(a))
            elif g.get("Appliance") == "track_circuit":
                out[name] = frozenset({"TC"})
        for _, row in self.rows.values():
            if row.get("name") and not foreign(row["name"], self.name):
                out[row["name"].partition(":")[2]] = frozenset(track_pins(row.get("relations", {})))
        return out


# --------------------------------------------------------------------------------------------------------- the file

class _Reporter:
    """The report, with each code's level from the registry."""

    def __init__(self) -> None:
        self.report = Report()

    def add(self, code: str, text: str, where: str = "") -> None:
        entry = registry().get(code)
        if entry is None:
            raise KeyError(f"diagnostic code {code!r} is not in the registry {REGISTRY}")
        self.report.add(entry["level"], code, text, where)


class _Derivation:
    def __init__(self, model: dict[str, Any], reference_data: dict[str, Any]) -> None:
        self.m = model
        self.ref = reference_data
        self.r = _Reporter()
        self.report = self.r.report
        self.plans: dict[str, _Plan] = {}
        self.sent: dict[str, Optional[dict[str, Optional[str]]]] = {}   # interlocking -> token -> circuit; None: no code line
        self.scope: dict[str, Optional[str]] = {}                       # interlocking -> "house" or "interlocking"; None: no code line
        self.controls: dict[tuple[str, Optional[str]], set[str]] = defaultdict(set)   # (interlocking, house or None) -> controls

    # ------------------------------------------------------------------------------------------ indications

    def indications(self) -> None:
        """Every station's office indications, named by its code line's encoding (reference data). An interlocking on
        no code line sends none: its indications are absent, not empty."""
        for name, plan in self.plans.items():
            line = plan.ix.get("relations", {}).get("codeline")
            if not line:
                self.sent[name] = None
                continue
            kind = self.m.get("layout", {}).get("codelines", {}).get(line, {}).get("given", {}).get("Kind")
            self.sent[name] = plan.indications(reference.indication_tokens(kind, self.ref.get("indicationTokens")))
            self.scope[name] = reference.station_of(kind)

    def station_sends(self, b: str, house: Optional[str]) -> set[str]:
        """What one station of interlocking ``b`` sends: one house's tokens on a line whose station is a house, every
        house's on a line whose station is the interlocking."""
        plan = self.plans[b]
        if self.scope.get(b) == "house":
            return plan.by_house.get(house or "", set())
        return set().union(*plan.by_house.values()) if plan.by_house else set()

    def stations(self) -> None:
        """``derived.controls`` and ``derived.indications`` on each station as its code line's encoding defines it
        (the owner, 2026-10-27): on a US&S 506 line each house, on an AAR token line the interlocking."""
        for b, plan in self.plans.items():
            scope = self.scope.get(b)
            if scope is None:
                continue
            if scope == "house":
                for h, house in plan.houses.items():
                    _set_derived(house, {"indications": sorted(plan.by_house.get(h, ())), "controls": sorted(self.controls.get((b, h), ()))})
            else:
                _set_derived(plan.ix, {"indications": sorted(self.station_sends(b, None)), "controls": sorted(self.controls.get((b, None), ()))})

    def consumed(self, plan: _Plan) -> dict[str, str]:
        """Each consumer row's TC pin to the circuit its indication stands for, where the token resolves to one."""
        out = {}
        for row in plan.consumers():
            token = row.get("relations", {}).get("indication", "")
            b, _, t = token.partition(":")
            circuit = (self.sent.get(b) or {}).get(t)
            if circuit and "TC" in track_pins(row.get("relations", {})):
                out[f"{row.get('id', '')}.TC"] = circuit
        return out

    def resolve_consumers(self) -> None:
        """A consumer's indication is one the named station sends (the owner, 2026-10-27): an error when the station is in
        the file and does not send it; a warning when the station is not in the file; missing when the station states no
        code line, so what it sends is unknown."""
        for a, plan in self.plans.items():
            for row in plan.consumers():
                where = plan.where("track", "consumers", row.get("id", ""))
                token = row.get("relations", {}).get("indication")
                if not token:
                    self.r.add("reference.indication", f"{a}: a consumer row states no indication", where)
                    continue
                b, _, t = token.partition(":")
                if b not in self.plans:
                    self.r.add("reference.interlocking", f"{a}: the consumer of {token} names {b}, which is no interlocking in this file", where)
                elif self.sent.get(b) is None:
                    self.r.add("reference.codeline", f"{a}: the consumer of {token} names {b}, which is on no code line, so what it "
                               "sends is unknown", where)
                elif t not in self.sent[b]:
                    self.r.add("reference.unresolved", f"{a}: the consumer of {token} names {b}, which sends no indication {t}", where)

    def run(self) -> None:
        for name, ix in self.m.get("interlockings", {}).items():
            plan = _Plan(name, ix, self.r)
            plan.components()
            plan.name_circuits({}, report=False)
            plan.control_points()
            self.plans[name] = plan
        self.indications()
        for plan in self.plans.values():
            plan.name_circuits(self.consumed(plan))
            plan.write()
            plan.checks()
        self.next_cps()
        self.resolve_references()
        self.resolve_consumers()
        self.columns()
        self.devices()
        self.desk()
        self.stations()
        self.heads()
        self.reach()
        if "provenance" in self.m:
            self.m["provenance"]["rules"] = RULES

    # -------------------------------------------------------------------------------------------- next cp

    def next_cps(self) -> None:
        """A NextCP names the interlocking its track leads to; that interlocking's NextCPs lead back as many times. One
        beyond the layout (Lick, Hollister) is reported at info."""
        count: dict[tuple[str, str], int] = defaultdict(int)
        for a, plan in self.plans.items():
            for row in plan.track.get("ends", []):
                g = row.get("given", {})
                if g.get("Kind") == "NEXT_CP" and g.get("Interlocking"):
                    count[(a, g["Interlocking"])] += 1
        for (a, b), n in sorted(count.items()):
            if b not in self.plans:
                self.r.add("next_cp.off_layout", f"{a}: {n} NextCP{'s lead' if n > 1 else ' leads'} to {b}, which is not on this layout",
                           f"interlockings/{a}")
            elif count.get((b, a), 0) != n:
                self.r.add("next_cp.pair", f"{a} has {n} NextCP{'s' * (n > 1)} to {b}, but {b} has {count.get((b, a), 0)} back to {a}",
                           f"interlockings/{a}")

    # ----------------------------------------------------------------------------------------- references

    def resolve_references(self) -> None:
        """Every qualified name for another interlocking's thing names one that exists, of the kind it is used as,
        with every port or side wired to it (the owner, 2026-10-27). An interlocking not in the file is a warning; a
        thing or port missing from one that is, an error."""
        for a, plan in self.plans.items():
            for kind, name, ports, what, where in plan.references():
                b, _, n = name.partition(":")
                if kind == "marker":
                    self.r.add("reference.marker", f"{a}: a track pin names {name}.TC, another interlocking's marker; a reference to it "
                               "is a consumer row of its indication (relations.indication)", where)
                    continue
                if b not in self.plans:
                    self.r.add("reference.interlocking", f"{a}: {what} {name} names {b}, which is no interlocking in this file", where)
                    continue
                target = self.plans[b]
                circuits = {c for c in target.name_of.values() if c} | {
                    f"{b}:{k}" for k, v in target.appliances.items() if v.get("given", {}).get("Appliance") == "track_circuit"}
                sides = target.sides()
                row = target.appliances.get(n)
                if kind == "circuit":
                    found, have = name in circuits, None
                elif kind == "track":
                    found, have = n in sides and row is None, sides.get(n)
                else:
                    found, have = row is not None and row.get("given", {}).get("Appliance") == kind, sides.get(n, frozenset())
                if not found:
                    thing = "circuit" if kind == "circuit" else "track symbol" if kind == "track" else kind
                    self.r.add("reference.unresolved", f"{a}: {what} {name} names {b}, which has no {thing} {n}", where)
                    continue
                lost = sorted(set(ports) - have) if have is not None else []
                if lost:
                    self.r.add("reference.unresolved", f"{a}: {what} {name} is wired at {', '.join(lost)}, but {b}'s {n} has no "
                               f"{'port' if kind == 'switch' else 'side'} {', '.join(lost)}", where)

    # -------------------------------------------------------------------------------------- office units

    def _house_by_cp(self, cp: str) -> Optional[tuple[str, str]]:
        hits = [(i, h) for i, ix in self.m.get("interlockings", {}).items() for h in ix.get("houses", {}) if h.casefold() == cp.casefold()]
        return hits[0] if len(hits) == 1 else None

    def columns(self) -> None:
        """A column's house is its ``CP Name``, resolved over every interlocking's houses; its interlocking is the house's.
        A 506 station is a house addressed by its column, so a house with two columns on a 506 line is two addresses."""
        for ou_name, ou in self.m.get("officeUnits", {}).items():
            by_house: dict[tuple[str, str], list[str]] = defaultdict(list)
            for number, c in ou.get("columns", {}).items():
                where = f"officeUnits/{ou_name}/columns/{number}"
                cp = c.get("given", {}).get("CP Name")
                house = None
                if cp:
                    house = self._house_by_cp(cp)
                    if house is None:
                        self.r.add("column.house", f"column {number}: CP Name {cp!r} names no house", where)
                    else:
                        by_house[house].append(number)
                else:
                    folder = c.get("relations", {}).get("interlocking")
                    self.r.add("column.cp_name", f"column {number}: no CP Name; only relations.interlocking places it in {folder or '?'}", where)
                _set_derived(c, {"house": f"{house[0]}:{house[1]}" if house else None, "interlocking": house[0] if house else None})
            for (ixn, cp), nums in by_house.items():
                if len(nums) > 1 and self._codeline_kind(ixn) == "USS506":
                    self.r.add("station.columns", f"house {cp} of {ixn} has columns {', '.join(nums)} on a US&S 506 line: two station "
                               "addresses", f"interlockings/{ixn}")

    def _codeline_kind(self, interlocking: str) -> Optional[str]:
        line = self.m.get("interlockings", {}).get(interlocking, {}).get("relations", {}).get("codeline")
        return self.m.get("layout", {}).get("codelines", {}).get(line, {}).get("given", {}).get("Kind") if line else None

    # ------------------------------------------------------------------------------------------- devices

    def devices(self) -> None:
        """A device serves the appliance its ``Name`` names in its scope, a head device the mast its IND wire reaches; a
        lamp shows its ``IndicationToken`` resolved in its scope. A panel device's scope is its column's interlocking,
        else its own ``relations.interlocking``. A code lever serves the station, not an appliance."""
        for name, ix in self.m.get("interlockings", {}).items():
            for i, dev in enumerate(ix.get("devices", [])):
                g = dev.get("given", {})
                derived: dict[str, Any] = {}
                if g.get("Appliance") == "head":
                    derived["serves"] = dev.get("relations", {}).get("mast")
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
                scope = None
                if rel.get("column"):
                    ou_of, _, number = rel["column"].partition(":")
                    col = self.m.get("officeUnits", {}).get(ou_of, {}).get("columns", {}).get(number)
                    if col is not None:
                        scope = col.get("derived", {}).get("interlocking") or col.get("relations", {}).get("interlocking")
                scope = scope or rel.get("interlocking")
                derived = {}
                if g.get("Appliance") == "lamp":
                    tokens = [t.strip() for t in g.get("IndicationToken", "").split(",") if t.strip()]
                    template = self.templates(scope).get("track_circuit", ("{name}K",))[0]
                    derived["shows"] = [qualify(reference.indication_of(t, template), scope) for t in tokens] if scope else None
                    if not tokens:
                        self.r.add("lamp.token", f"panel lamp {g.get('Name', '')!r}: no IndicationToken", where)
                elif g.get("Name") and scope and not self._code_lever(g):
                    derived["serves"] = qualify(g["Name"], scope)
                _set_derived(dev, derived)

    def templates(self, interlocking: Optional[str]) -> dict[str, tuple[str, ...]]:
        line = self.m.get("interlockings", {}).get(interlocking or "", {}).get("relations", {}).get("codeline")
        kind = self.m.get("layout", {}).get("codelines", {}).get(line, {}).get("given", {}).get("Kind") if line else None
        return reference.indication_tokens(kind, self.ref.get("indicationTokens"))

    # ---------------------------------------------------------------------------------------------- desk

    def desk(self) -> None:
        """The office's side of each code line (the owner, 2026-10-27). A lever's controls are its name and each binding
        that ends in S (``783NWS``, ``784HS``, ``795WLS``, ``MC1S``); a lever's bindings that end in K and a lamp's
        ``shows`` are the indications the desk consumes. Both belong to the station of the desk column the device sits
        in, whatever it serves: on a US&S 506 line the house its column names (``CP Name``), on an AAR token line the
        column's interlocking. Each consumed indication must be one that station sends. ``UNUSED`` and the code lever bind
        nothing of a station."""
        for ou_name, ou in self.m.get("officeUnits", {}).items():
            for i, dev in enumerate(ou.get("devices", [])):
                g, d = dev.get("given", {}), dev.get("derived", {})
                where = f"officeUnits/{ou_name}/devices/{i}"
                if g.get("Appliance") == "lamp":
                    tokens, mine, what = d.get("shows", []), [], f"the lamp {g.get('Name', '')}"
                elif g.get("Appliance") == "lever" and d.get("serves"):
                    b, _, n = d["serves"].partition(":")
                    keys = sorted(dev.get("relations", {}).get("bindings", {}))
                    mine = [f"{n}{k}" for k in keys if k.endswith("S")]
                    tokens = [f"{b}:{n}{k}" for k in keys if k.endswith("K")]
                    what = f"lever {n}"
                    _set_derived(dev, {**d, "controls": [f"{b}:{t}" for t in mine], "indications": tokens})
                else:
                    continue
                if not tokens and not mine:
                    continue
                b = (tokens[0] if tokens else d["serves"]).partition(":")[0]
                found, house = self.station_of(ou_name, dev, b)
                if not found:
                    self.r.add("desk.station", f"{what} sits in no column that names a house, and {b}'s code line makes each house a "
                               f"station, so which station its {', '.join(mine + tokens)} belong to is not stated", where)
                    continue
                self.controls[(b, house)].update(mine)
                for token in tokens:
                    self.consume(what, token, where, house)

    def station_of(self, ou_name: str, dev: dict[str, Any], b: str) -> tuple[bool, Optional[str]]:
        """The station of a desk device: (stated, its house, or None for the interlocking). On a line whose station is a
        house it is the house its column's ``CP Name`` names; elsewhere the interlocking."""
        if self.scope.get(b) != "house":
            return True, None
        col = dev.get("relations", {}).get("column", "")
        ou_of, _, number = col.partition(":")
        c = self.m.get("officeUnits", {}).get(ou_of or ou_name, {}).get("columns", {}).get(number, {})
        house = c.get("derived", {}).get("house", "")
        hb, _, h = house.partition(":")
        return (True, h) if house and hb == b else (False, None)

    def consume(self, what: str, token: str, where: str, house: Optional[str] = None) -> None:
        """One indication a consumer expects, checked against what the named station sends: the error, warning and
        missing of ``resolve_consumers``. ``house`` names the station on a line whose station is a house; without it the
        interlocking's houses together are checked (a consumer row names only the interlocking)."""
        b, _, t = token.partition(":")
        if b not in self.plans:
            self.r.add("reference.interlocking", f"{what} consumes {token}, but {b} is no interlocking in this file", where)
        elif self.sent.get(b) is None:
            self.r.add("reference.codeline", f"{what} consumes {token}, but {b} is on no code line, so what it sends is unknown", where)
        elif t not in (self.station_sends(b, house) if house else self.sent[b]):
            station = f"{b}'s station {house}" if house else b
            self.r.add("reference.unresolved", f"{what} consumes {token}, but {station} sends no indication {t}", where)

    @staticmethod
    def _code_lever(g: dict[str, str]) -> bool:
        return g.get("Appliance") == "lever" and "code" in styles(g)

    # --------------------------------------------------------------------------------------------- heads

    def heads(self) -> None:
        """A head device to its trackplan head by mast name and letter; the vocabularies must match (ADR 0009 §3.7)."""
        for name, ix in self.m.get("interlockings", {}).items():
            plan: dict[tuple[str, str], str] = {}
            for mast, a in ix.get("appliances", {}).items():
                for letter, h in a.get("heads", {}).items():
                    plan[(mast, letter)] = h.get("given", {}).get("Style", "")
            by_head: dict[tuple[str, str], list[tuple[int, dict[str, Any]]]] = defaultdict(list)
            for i, d in enumerate(ix.get("devices", [])):
                g, serves = d.get("given", {}), d.get("derived", {}).get("serves")
                if g.get("Appliance") == "head" and serves and g.get("Head"):
                    by_head[(serves.partition(":")[2], g["Head"])].append((i, d))
            for (mast, letter), devs in sorted(by_head.items()):
                where = f"interlockings/{name}/devices/{devs[0][0]}"
                style = plan.get((mast, letter))
                if style is None:
                    self.r.add("head.plan", f"{name}: head devices for {mast} head {letter}, but the trackplan draws no such head", where)
                    continue
                primary = [d for _, d in devs if style in styles(d["given"])]
                lamps = [d for _, d in devs if style not in styles(d["given"]) and style in ("UQ", "LQ")
                         and (d["given"].get("Appliance") == "lamp" or "CL" in styles(d["given"]))]
                for i, d in devs:
                    if d not in primary and d not in lamps:
                        self.r.add("head.vocabulary", f"{name}: the trackplan draws {mast} head {letter} as {style}, but its device is "
                                   f"{d['given'].get('Style')}. Fix: change the trackplan head, or bind a {style} device",
                                   f"interlockings/{name}/devices/{i}")
                wrong = [d for _, d in devs if d not in primary and d not in lamps]
                if len(primary) > 1 or (not primary and not wrong):
                    self.r.add("head.vocabulary", f"{name}: {mast} head {letter} ({style}) has {len(primary)} devices of its style; "
                               "one expected", where)

    # --------------------------------------------------------------------------------------------- reach

    def reach(self) -> None:
        """A driver whose IC is an encoding needs that I/O encoding on its processor (ADR 0009 §3.6). A FieldUnit reaches
        its code line's transport through the code line; when its processor anchors no instance of that transport, the
        layout relies on that derivation, reported at info."""
        layout = self.m.get("layout", {})
        for p, proc in layout.get("processors", {}).items():
            for address, d in proc.get("drivers", {}).items():
                ic = d.get("given", {}).get("IC")
                kind = reference.ENCODING_OF_IC.get(ic)
                if kind and not any(e.get("given", {}).get("Kind") == kind and e.get("relations", {}).get("processor") == p
                                    for e in layout.get("ioEncodings", {}).values()):
                    self.r.add("driver.encoding", f"driver {ic} {address} on {p}: no {kind} I/O encoding rides a transport anchored on {p}",
                               f"layout/processors/{p}/drivers/{address}")
        for name, ix in self.m.get("interlockings", {}).items():
            rel = ix.get("relations", {})
            e = layout.get("codelines", {}).get(rel.get("codeline")) if rel.get("codeline") else None
            t = e.get("relations", {}).get("transport") if e else None
            if t and rel.get("processor") and rel["processor"] not in layout.get("transports", {}).get(t, {}).get("relations", {}).get("anchors", []):
                self.r.add("transport.reach", f"FieldUnit {name} reaches {t} through its code line {rel['codeline']}; its processor "
                           f"{rel['processor']} anchors no {t} instance", f"interlockings/{name}")


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
