"""The routes of each mast (domain library, ADR 0012 §5.1 and §5.3; issue #139): per controlled mast, its single-path
routes, each with the static terms FieldUnit's evaluation reads. Computed on demand from a derived Layout Data Model
File; nothing is written into it.

A route belongs to the mast that displays it (the owner, 2026-11-13). Its terms:

- ``mast`` and ``demand``: the mast and its entering signal demand ``<signal>(<direction>)`` (``830(LEFT)``), the
  mast's ``given.signal`` and ``relations.facing``. The demand is present only when a desk signal lever works the
  mast (the lever's ``derived.masts``); a mast no lever works has routes with no ``demand``.
- ``alignment``: every switch and derail passed, in walk order, with its one position. A derail is passed C to R or R
  to C, so it is ``REVERSE`` (its through position).
- ``circuits``: the circuits passed, in walk order; ``entrance`` the first, the circuit the mast governs into (the
  knockdown circuit). ``approach``: the circuit on the approach side of the mast's joint, where one is stated.
- ``end``: the next mast that governs the same movement, ``{"mast": ..., "demand": ...}``, the demand under the same
  rule as the entering one (an automatic mast is named with no ``demand``); or a limit, ``{"limit": ...}``: the Kind
  of an end of track (``NEXT_CP``, ``BUMPER``, ``INDUSTRY``), or ``REGIME`` (with ``from`` and ``to``) at a joint
  where the regime of the track changes and the track beyond is not interlocking track (ADR 0013 §7.1: a regime
  boundary, the successor of the retired END_CTC end; §13: interlocking track is a piece a CONTROLLED mast governs
  into or that holds a dispatcher-controlled switch's port). A regime boundary inside an interlocking (Gilroy
  Caltrain's yard limits between 771 and 773) is passed. No ``end``: the walk could not finish, reported
  ``route.end`` at missing.
- ``opposing``: the masts on the route's track that govern against the movement, each ``{"mast": ..., "demand":
  ...}`` with the demand under the same rule. A converging movement is a different alignment, so a different route,
  and no term here.
- ``ceiling``: the word an ``IndicationCeiling`` stated on an appliance the route passes gives for the position it is
  passed in (the field is ``NORMAL/REVERSE``; 827D ``STOP/RESTRICTING`` passed ``REVERSE`` gives ``RESTRICTING``);
  ``ceilings`` the stated sources. A route that passes none is ``CLEAR``, stated (the owner, 2026-11-13): each term
  contributes one indication from its own value set and CLEAR is the unrestricted contribution under the least
  permissive. The heuristics of ADR 0012 §5.4 (a switch reversed gives APPROACH, ...) are policies reference data
  with no rows yet; they join as contributions when the rows land (#62). A route that passes stated ceilings with
  different words keeps them all in ``ceilings`` and states no single ``ceiling``: their order is reference data.

The walk (ADR 0012 §5.3) follows the track's stated adjacency and each joint's masts: the direction is the movement
along the track, never LEFT or RIGHT. Crossing a joint from side X to side Y, a mast that governs into Y governs the
same movement and ends the route; one that governs into X opposes it. A route through another interlocking's track
names that interlocking's things by qualified name, its demands too (``Christopher:816(LEFT)``).

The vital boundary (ADR 0012 §5.2): no locking and no evaluation. Names are never parsed: the library reads the
stated atoms (``given.signal``, ``relations.facing``, the lever's ``derived.masts``, a joint's ``relations.mast`` or
``relations.masts``, a derail's port names) and the derived circuits and regimes, under ADR 0011's reader policy.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

from tools.layout_model.grammar import dispatcher_controlled, is_derail
from tools.layout_model.report import MISSING, Report

VERSION = "0.1.0"                 # this library's version (ADR 0012 §7), pre-release with the rules
RULES_MAJOR = 0                   # the MAJOR of the rules it reads (ADR 0012 §7)

OTHER_SIDE = {"A": "B", "B": "A", "approach": "governed", "governed": "approach"}
POSITION = {"N": "NORMAL", "R": "REVERSE"}
LIMITS = frozenset({"NEXT_CP", "BUMPER", "INDUSTRY"})
CLEAR = "CLEAR"                   # the unrestricted contribution (the owner, 2026-11-13)
JOINTS = frozenset({"IRJ", "IRJ_SIGNAL", "IRJ_SIGNALS"})


@dataclass
class Route:
    mast: str                                            # qualified
    demand: Optional[str] = None
    alignment: list[tuple[str, str]] = field(default_factory=list)   # (switch, NORMAL | REVERSE), walk order
    circuits: list[str] = field(default_factory=list)
    approach: Optional[str] = None
    end: Optional[dict[str, str]] = None
    opposing: list[dict[str, str]] = field(default_factory=list)
    ceilings: list[dict[str, str]] = field(default_factory=list)   # {appliance, position, word}

    @property
    def entrance(self) -> Optional[str]:
        return self.circuits[0] if self.circuits else None

    @property
    def ceiling(self) -> Optional[str]:
        words = {c["word"] for c in self.ceilings}
        return CLEAR if not words else words.pop() if len(words) == 1 else None

    def label(self) -> str:
        return f"{self.mast} [{', '.join(f'{s} {p}' for s, p in self.alignment) or 'no switch'}]"

    def as_dict(self) -> dict[str, Any]:
        """The route as plain JSON; a term not stated is an absent key."""
        out: dict[str, Any] = {"mast": self.mast}
        if self.demand:
            out["demand"] = self.demand
        out["alignment"] = [{"appliance": s, "position": p} for s, p in self.alignment]
        out["circuits"] = list(self.circuits)
        if self.entrance:
            out["entrance"] = self.entrance
        if self.approach:
            out["approach"] = self.approach
        if self.end:
            out["end"] = dict(self.end)
        out["opposing"] = [dict(o) for o in self.opposing]
        if self.ceiling:
            out["ceiling"] = self.ceiling
        if self.ceilings:
            out["ceilings"] = [dict(c) for c in self.ceilings]
        return out


@dataclass
class Routes:
    routes: dict[str, list[Route]]                       # qualified mast -> its routes, walk order
    report: Report

    def of(self, mast: str) -> list[Route]:
        return self.routes.get(mast, [])


# ------------------------------------------------------------------------------------------------- the track

@dataclass(frozen=True)
class _Pin:
    kind: str                     # switch | joint | end | marker
    owner: str                    # qualified appliance name or row prefix
    side: str
    interlocking: str


class _Track:
    """Every interlocking's track pins, joined into nets by their stated adjacency (ADR 0011: a pin's relation names
    every pin its wire reaches), with what each pin is."""

    def __init__(self, model: dict[str, Any]) -> None:
        self.model = model
        self.pins: dict[str, _Pin] = {}
        self.parent: dict[str, str] = {}
        self.appliances: dict[str, tuple[str, dict[str, Any]]] = {}     # qualified name -> (interlocking, appliance)
        self.rows: dict[str, tuple[str, str, dict[str, Any]]] = {}      # prefix -> (interlocking, list, row)
        self.circuit_of_pin: dict[str, str] = {}
        self.regime_of: dict[str, str] = {}                             # piece name -> regime
        self.mast_joint: dict[str, tuple[str, str]] = {}                # qualified mast -> (joint prefix, governed side)
        self.joint_masts: dict[str, list[tuple[str, str]]] = {}         # joint prefix -> [(mast, governed side)]
        for b, ix in model.get("interlockings", {}).items():
            for n, a in ix.get("appliances", {}).items():
                q = f"{b}:{n}"
                self.appliances[q] = (b, a)
                g, rel, d = a.get("given", {}), a.get("relations", {}), a.get("derived", {})
                if g.get("Appliance") == "switch":
                    for port in (("C", "R") if is_derail(g) else ("C", "N", "R")):
                        if isinstance(rel.get(port), list):
                            self._add(f"{q}.{port}", _Pin("switch", q, port, b), rel[port])
                            circuit = d.get("circuits", {}).get("track") if is_derail(g) else d.get("osCircuit")
                            if circuit:
                                self.circuit_of_pin[f"{q}.{port}"] = circuit
                elif g.get("Appliance") == "track_circuit":
                    for side in ("TC", "A", "B"):
                        if isinstance(rel.get(side), list):
                            self._add(f"{q}.{side}", _Pin("marker", q, side, b), rel[side])
                            if side == "TC" and g.get("Style") != "boundary":
                                self.circuit_of_pin[f"{q}.TC"] = q
            for kind, rows in ix.get("track", {}).items():
                if not isinstance(rows, list):
                    continue
                for row in rows:
                    prefix = row.get("name") or row.get("id")
                    if not prefix:
                        if kind == "pieces":
                            pd = row.get("derived", {})
                            if pd.get("regime"):
                                for key in (pd.get("circuit"), pd.get("name")):
                                    if key:
                                        self.regime_of[key] = pd["regime"]
                        continue
                    self.rows[prefix] = (b, kind, row)
                    rk = row.get("given", {}).get("Kind")
                    pk = "joint" if kind == "joints" and rk in JOINTS else "end" if kind == "ends" else "marker"
                    circuits = row.get("derived", {}).get("circuits", {})
                    for side, refs in row.get("relations", {}).items():
                        if isinstance(refs, list):
                            self._add(f"{prefix}.{side}", _Pin(pk, prefix, side, b), refs)
                            if circuits.get(side):
                                self.circuit_of_pin[f"{prefix}.{side}"] = circuits[side]
                    if pk == "joint":
                        rel = row.get("relations", {})
                        masts = []
                        if rel.get("mast"):
                            masts.append((rel["mast"], "governed"))
                        for side, m in (rel.get("masts") or {}).items():
                            masts.append((m, side))
                        self.joint_masts[prefix] = masts
                        for m, side in masts:
                            self.mast_joint.setdefault(m, (prefix, side))
        self.nets: dict[str, list[str]] = {}
        for p in self.parent:
            self.nets.setdefault(self._find(p), []).append(p)
        self.levered = {m for ou in model.get("officeUnits", {}).values() for dev in ou.get("devices", [])
                        for m in dev.get("derived", {}).get("masts", [])}

    # union-find over stated adjacency
    def _add(self, pin: str, what: _Pin, refs: Iterable[str]) -> None:
        self.pins[pin] = what
        self.parent.setdefault(pin, pin)
        for r in refs:
            self.parent.setdefault(r, r)
            self._join(pin, r)

    def _find(self, x: str) -> str:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def _join(self, a: str, b: str) -> None:
        self.parent[self._find(a)] = self._find(b)

    def net(self, pin: str) -> list[str]:
        return self.nets.get(self._find(pin), []) if pin in self.parent else []

    def circuit(self, net: list[str]) -> Optional[str]:
        return next((self.circuit_of_pin[p] for p in sorted(net) if p in self.circuit_of_pin), None)

    def regime(self, net: list[str]) -> Optional[str]:
        """The regime of the piece a net is on (``track.pieces``): by its circuit, else by the name of an end on it,
        else by a pin-made name (``track@<pin>``)."""
        c = self.circuit(net)
        if c and c in self.regime_of:
            return self.regime_of[c]
        for p in net:
            w = self.pins.get(p)
            if w and w.kind == "end" and w.owner in self.regime_of:
                return self.regime_of[w.owner]
            if f"track@{p}" in self.regime_of:
                return self.regime_of[f"track@{p}"]
        return None

    def interlocking_track(self, pin: str) -> bool:
        """Whether the joint-bounded piece of track a pin is on is interlocking track (ADR 0013 §13, as the reference
        derivation reads it): a CONTROLLED mast governs into it, or it holds a dispatcher-controlled switch's or
        derail's port. The piece is the pin's net and every net joined to it through a switch's or derail's ports."""
        todo, nets = [pin], set()
        while todo:
            p = todo.pop()
            root = self._find(p) if p in self.parent else None
            if root is None or root in nets:
                continue
            nets.add(root)
            for q in self.nets.get(root, []):
                w = self.pins.get(q)
                if w is None:
                    continue
                if w.kind == "switch":
                    b, a = self.appliances[w.owner]
                    if dispatcher_controlled(w.owner.partition(":")[2], self.model["interlockings"][b].get("appliances", {})):
                        return True
                    todo.extend(f"{w.owner}.{port}" for port in ("C", "N", "R") if f"{w.owner}.{port}" in self.parent)
                elif w.kind == "joint":
                    if any(side == w.side and self.appliance(m).get("given", {}).get("Kind") == "CONTROLLED"
                           for m, side in self.joint_masts.get(w.owner, [])):
                        return True
        return False

    def appliance(self, q: str) -> dict[str, Any]:
        return self.appliances.get(q, ("", {}))[1]

    def demand(self, mast: str, scope: str) -> Optional[str]:
        """``<signal>(<direction>)`` of a mast a desk signal lever works; qualified when it is not of ``scope``."""
        if mast not in self.levered:
            return None
        a = self.appliance(mast)
        signal, facing = a.get("given", {}).get("signal"), a.get("relations", {}).get("facing")
        if not signal or not facing:
            return None
        b = mast.partition(":")[0]
        return f"{signal}({facing})" if b == scope else f"{b}:{signal}({facing})"

    def named(self, mast: str, scope: str) -> dict[str, str]:
        out = {"mast": mast}
        d = self.demand(mast, scope)
        if d:
            out["demand"] = d
        return out


# --------------------------------------------------------------------------------------------------- the walk

def _path(q: str) -> str:
    b, _, n = q.partition(":")
    return f"interlockings/{b}/appliances/{n}"


def find(model: dict[str, Any]) -> Routes:
    """Every controlled mast's routes in a derived model, with the findings about what stops a route from finishing.
    Every finding is at ``missing``: an unfinished route is incomplete, never in error (ADR 0012 §5.5)."""
    t = _Track(model)
    report = Report()

    def add(code: str, text: str, where: str, entities: tuple[str, ...] = ()) -> None:
        report.add(MISSING, code, text, where, (where, *entities))

    out: dict[str, list[Route]] = {}
    entered_at_points: set[str] = set()
    passed: set[str] = set()
    for q, (b, a) in sorted(t.appliances.items()):
        g = a.get("given", {})
        if g.get("Appliance") != "mast" or g.get("Kind") != "CONTROLLED":
            continue
        joint = t.mast_joint.get(q)
        if joint is None:
            continue                                          # on no joint: the derivation reports mast.joint
        prefix, side = joint
        start = f"{prefix}.{side}"
        approach_pin = f"{prefix}.{OTHER_SIDE[side]}"
        seed = Route(q, t.demand(q, b), approach=t.circuit_of_pin.get(approach_pin) or t.circuit(t.net(approach_pin)))
        routes: list[Route] = []
        _walk(t, b, seed, start, frozenset(), routes, entered_at_points, add)
        for r in routes:
            passed.update(s for s, _ in r.alignment)
        out[q] = routes
    for s in sorted(passed):                                  # ADR 0012 §5.5: a facing switch no signal enters
        b, a = t.appliances[s]
        if is_derail(a.get("given", {})) or s in entered_at_points \
                or not dispatcher_controlled(s.partition(":")[2], model["interlockings"][b].get("appliances", {})):
            continue
        add("route.entering", f"switch {s} is dispatcher-controlled and passed by routes, but no route enters it at its "
            "points: no signal governs a movement facing it", _path(s))
    return Routes(out, report)


def _walk(t: _Track, scope: str, r: Route, pin: str, seen: frozenset[str], out: list[Route],
          entered_at_points: set[str], add) -> None:
    """Continue ``r`` into the net of ``pin``, entered through ``pin``; every finished or stopped route goes to ``out``."""
    net = t.net(pin)
    c = t.circuit(net) if net else None
    if c and (not r.circuits or r.circuits[-1] != c):
        r.circuits.append(c)
    exits = [p for p in sorted(net) if p != pin and t.pins.get(p) and t.pins[p].kind in ("switch", "joint", "end")]
    if not exits:
        add("route.end", f"the route {r.label()} runs onto track that ends with nothing stated beyond "
            f"{c or 'dark track'}", _path(r.mast))
        out.append(r)
        return
    for x in exits:
        w = t.pins[x]
        branch = _copy(r)
        if w.kind == "end":
            kind = t.rows[w.owner][2].get("given", {}).get("Kind", "")
            branch.end = {"limit": kind} if kind in LIMITS else None
            if branch.end is None:
                add("route.end", f"the route {branch.label()} reaches an end of Kind {kind or 'none'}, no limit", _path(r.mast))
            out.append(branch)
        elif w.kind == "switch":
            _switch(t, scope, branch, x, w, seen, out, entered_at_points, add)
        else:
            _joint(t, scope, branch, x, w, net, seen, out, entered_at_points, add)


def _switch(t, scope, r, x, w, seen, out, entered_at_points, add) -> None:
    a = t.appliance(w.owner)
    g = a.get("given", {})
    if w.owner in seen:
        add("route.end", f"the route {r.label()} returns to switch {w.owner}", _path(r.mast))
        out.append(r)
        return
    if is_derail(g):
        legs = [("R", "REVERSE")] if w.side == "C" else [("C", "REVERSE")]
    elif w.side == "C":
        entered_at_points.add(w.owner)
        legs = [("N", "NORMAL"), ("R", "REVERSE")]
    else:
        legs = [("C", POSITION[w.side])]
    for leg, position in legs:
        branch = _copy(r) if len(legs) > 1 else r
        branch.alignment.append((w.owner, position))
        ceiling = g.get("IndicationCeiling", "").strip()
        if ceiling:
            words = [x.strip() for x in ceiling.split("/")]
            if len(words) == 2:
                branch.ceilings.append({"appliance": w.owner, "position": position,
                                        "word": words[0 if position == "NORMAL" else 1]})
        nxt = f"{w.owner}.{leg}"
        if nxt not in t.parent:
            add("route.end", f"the route {branch.label()} leaves switch {w.owner} by {leg}, which is wired to nothing",
                _path(branch.mast))
            out.append(branch)
            continue
        _walk(t, scope, branch, nxt, seen | {w.owner}, out, entered_at_points, add)


def _joint(t, scope, r, x, w, net, seen, out, entered_at_points, add) -> None:
    other = OTHER_SIDE.get(w.side)
    nxt = f"{w.owner}.{other}" if other else None
    ending = None
    for m, governed in t.joint_masts.get(w.owner, []):
        if m == r.mast:
            continue
        if governed == w.side:
            if all(o["mast"] != m for o in r.opposing):
                r.opposing.append(t.named(m, scope))
        elif governed == other:
            ending = m
    if ending:
        r.end = t.named(ending, scope)
        out.append(r)
        return
    if nxt is None or nxt not in t.parent:
        add("route.end", f"the route {r.label()} crosses a joint to a side wired to nothing", _path(r.mast))
        out.append(r)
        return
    here, there = t.regime(net), t.regime(t.net(nxt))
    if here and there and here != there and not t.interlocking_track(nxt):
        r.end = {"limit": "REGIME", "from": here, "to": there}
        out.append(r)
        return
    _walk(t, scope, r, nxt, seen, out, entered_at_points, add)


def _copy(r: Route) -> Route:
    return Route(r.mast, r.demand, list(r.alignment), list(r.circuits), r.approach, dict(r.end) if r.end else None,
                 [dict(o) for o in r.opposing], [dict(c) for c in r.ceilings])
