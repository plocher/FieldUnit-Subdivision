"""The ladders of a layout (domain library, ADR 0012 §5.6; issue #145, a POC): from each ``LADDER`` marker, the facing walk
that finds the ladder's switches and the ordered choices a selector offers. The reference derivation calls ``find``
and writes the results into ``derived`` (ADR 0015: derived results are written at save), so the selector's choices and
each ladder switch's control source are in the file.

The rules (the owner, 2026-11-13):

1. **A ladder is every facing-point switch from its start leg up to a trailing point.** The marker is a policy sign on
   the start leg. The walk goes from the marker's piece both ways along the track, across every joint: one way meets
   the start switch trailing (at N or R), the other meets the first ladder switch at C, so the direction needs no
   orientation. It continues through each switch entered at C and stops where the next switch on a path is met at N
   or R (trailing), or at an end of track. A derail on the way is passed (C to R, R to C) and is no ladder switch.
2. **Choices, in a deterministic order.** At each ladder switch the spine is the leg that leads to the next ladder
   switch (N or R); the other leg is the next choice; the last switch gives R, then N. Where both legs lead to ladder
   switches, N's sub-ladder comes before R's. Each choice is its leg (the switch port, ``Watsonville:17.R``) with its
   alignment, every ladder switch from the start in walk order with its position. Detent 1 is nearest the start.

Findings: a ladder marker with no Name (``ladder.name``); a marker from which no way meets a switch at its points
(``ladder.start``), or both ways do (``ladder.direction``); a leg that reaches neither a trailing point nor an end of
track (``ladder.leg``, the choice is kept); a switch on two ladders (``ladder.shared``). Which selector serves a
ladder, and the control source it gives the switches, are the reference derivation's (``derive.ladders``).

The vital boundary (ADR 0012 §5.2): a choice is an alignment and nothing more. The desk turns it into ordinary
``NWS``/``RWS`` controls; the field unit lines and locks as for any lever. Nothing here implements locking. Names are
never parsed: the walk reads the stated adjacency, through ``routes.Track``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from tools.layout_model.grammar import LADDER, is_derail
from tools.layout_model.report import Report

from .routes import OTHER_SIDE, POSITION, Track

VERSION = "0.1.0"                 # this library's version (ADR 0012 §7), pre-release with the rules
RULES_MAJOR = 0


@dataclass
class Choice:
    leg: str                                              # the switch port, qualified: Watsonville:17.R
    alignment: list[tuple[str, str]]                      # (switch, NORMAL | REVERSE), from the start, walk order

    def label(self) -> str:
        """``17R: 15N 17R``, the owner's notation: the leg, then the alignment, each switch unqualified."""
        def short(s: str, p: str) -> str:
            return f"{s.partition(':')[2]}{p[0]}"
        sw, _, port = self.leg.rpartition(".")
        return f"{sw.partition(':')[2]}{port}: {' '.join(short(s, p) for s, p in self.alignment)}"

    def as_dict(self, detent: int) -> dict[str, Any]:
        return {"detent": detent, "leg": self.leg,
                "alignment": [{"appliance": s, "position": p} for s, p in self.alignment]}


@dataclass
class Ladder:
    name: str                                             # qualified: Watsonville:Arrival
    where: str                                            # the marker row's model path
    start: Optional[str] = None                           # the start switch's port the start leg meets: Watsonville:837.R
    switches: list[str] = field(default_factory=list)    # walk order
    choices: list[Choice] = field(default_factory=list)  # detent order


@dataclass
class Ladders:
    ladders: dict[str, Ladder]                            # qualified name -> ladder
    report: Report

    def of(self, switch: str) -> list[Ladder]:
        return [lad for lad in self.ladders.values() if switch in lad.switches]


# An outcome of following the track from a pin: ("facing", switch) a switch entered at C; ("trailing", switch, port) a
# switch entered at N or R; ("end", kind) an end of track; ("open", why) neither.

def _leave(t: Track, pin: str, seen: frozenset[str]) -> tuple:
    """Follow the track out of ``pin`` (a switch port or a joint side) to the next switch or end."""
    if pin not in t.parent:
        return ("open", f"{pin} is wired to nothing")
    exits = [p for p in sorted(t.net(pin)) if p != pin and t.pins.get(p) and t.pins[p].kind in ("switch", "joint", "end")]
    if not exits:
        return ("open", f"the track beyond {pin} ends with nothing stated")
    if len(exits) > 1:
        return ("open", f"the wire at {pin} reaches {', '.join(exits)} with no switch between")
    return _enter(t, exits[0], seen)


def _enter(t: Track, x: str, seen: frozenset[str]) -> tuple:
    """Arrive at the track pin ``x``: a switch, an end, or a joint, which is crossed."""
    if x in seen:
        return ("open", f"the track returns to {x}")
    seen = seen | {x}
    w = t.pins[x]
    if w.kind == "end":
        return ("end", t.rows[w.owner][2].get("given", {}).get("Kind", ""))
    if w.kind == "joint":
        other = OTHER_SIDE.get(w.side)
        if other is None:
            return ("open", f"the joint side {x} has no other side")
        return _leave(t, f"{w.owner}.{other}", seen)
    if is_derail(t.appliance(w.owner).get("given", {})):          # passed, C to R or R to C
        return _leave(t, f"{w.owner}.{'R' if w.side == 'C' else 'C'}", seen)
    return ("facing", w.owner) if w.side == "C" else ("trailing", w.owner, w.side)


def _reporter(report: Report):
    """``add(code, text, where, entities)``, each code at its registered level (ADR 0012 §3.3)."""
    from tools.layout_model.derive import registry          # late: the reference derivation calls this library

    def add(code: str, text: str, where: str, entities: tuple[str, ...] = ()) -> None:
        report.add(registry()[code]["level"], code, text, where, tuple(dict.fromkeys((where, *entities))))
    return add


def _path(b: str, prefix: str) -> str:
    return f"interlockings/{b}/track/policies/{prefix}"


def find(model: dict[str, Any]) -> Ladders:
    """Every ladder marker's ladder in a model whose track relations are stated, with the findings."""
    t = Track(model)
    report = Report()
    add = _reporter(report)
    out: dict[str, Ladder] = {}
    for b, ix in model.get("interlockings", {}).items():
        for row in ix.get("track", {}).get("policies", []):
            if row.get("given", {}).get("Kind") != LADDER:
                continue
            where = _path(b, row.get("id", ""))
            if not row.get("name"):
                add("ladder.name", f"{b}: a ladder marker states no Name; no selector can serve it", where)
                continue
            lad = Ladder(row["name"], where)
            out[lad.name] = lad
            _walk(t, lad, f"{row['name']}.track", add)
    owners: dict[str, list[str]] = {}
    for lad in out.values():
        for s in lad.switches:
            owners.setdefault(s, []).append(lad.name)
    for s, names in sorted(owners.items()):
        if len(names) > 1:
            b, _, n = s.partition(":")
            add("ladder.shared", f"switch {s} is on the ladders {', '.join(names)}; a switch is on one ladder",
                f"interlockings/{b}/appliances/{n}", tuple(out[x].where for x in names))
    return Ladders(out, report)


def _walk(t: Track, lad: Ladder, marker: str, add) -> None:
    exits = [p for p in sorted(t.net(marker)) if p != marker and t.pins.get(p) and t.pins[p].kind in ("switch", "joint", "end")]
    ways = [_enter(t, x, frozenset({marker})) for x in exits]
    facing = [w[1] for w in ways if w[0] == "facing"]
    trailing = [f"{w[1]}.{w[2]}" for w in ways if w[0] == "trailing"]
    if len(facing) > 1:
        add("ladder.direction", f"ladder {lad.name}: both ways from the marker meet a switch at its points "
            f"({', '.join(facing)}); the marker stands on the start leg, with the start switch trailing one way", lad.where)
        return
    if not facing:
        add("ladder.start", f"ladder {lad.name}: no way from the marker meets a switch at its points; the ladder's "
            "first switch is not drawn yet", lad.where)
        return
    lad.start = trailing[0] if len(trailing) == 1 else None
    _switch(t, lad, facing[0], [], add)


def _switch(t: Track, lad: Ladder, sw: str, alignment: list[tuple[str, str]], add) -> None:
    lad.switches.append(sw)
    reach = {port: _leave(t, f"{sw}.{port}", frozenset()) for port in ("N", "R")}
    for port, r in reach.items():                          # a ladder switch met again is a loop, no sub-ladder
        if r[0] == "facing" and r[1] in lad.switches:
            reach[port] = ("open", f"the track returns to switch {r[1]}")
    spine = [p for p in ("N", "R") if reach[p][0] == "facing"]

    def choice(port: str) -> None:
        lad.choices.append(Choice(f"{sw}.{port}", alignment + [(sw, POSITION[port])]))
        if reach[port][0] == "open":
            add("ladder.leg", f"ladder {lad.name}: the leg {sw}.{port} reaches neither a trailing point nor an end "
                f"of track ({reach[port][1]})", lad.where)

    if not spine:                                          # the last switch: R, then N
        choice("R")
        choice("N")
    elif len(spine) == 1:                                  # the other leg is the next choice, then the spine's
        choice("R" if spine[0] == "N" else "N")
        _switch(t, lad, reach[spine[0]][1], alignment + [(sw, POSITION[spine[0]])], add)
    else:                                                  # N's sub-ladder before R's
        for port in ("N", "R"):
            _switch(t, lad, reach[port][1], alignment + [(sw, POSITION[port])], add)
