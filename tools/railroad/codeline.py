"""The code line between the office and its field stations (domain library, ADR 0012 §5): per station, the control
tokens it receives and the indication tokens it must send, computed on demand from a derived model. Nothing here is
stored in the file (the owner, 2026-10-28: station packets are not stored); the reference derivation checks the model
with the same function (``stations``), so there is one definition.

What a station is depends on its code line's encoding (``reference.station_of``; the owner, 2026-10-27): on a US&S 506
line each house is a station, on an AAR token line the interlocking is one.

- **Levers.** A desk lever's ``derived.controls`` and ``derived.indications`` go to the station of the desk column the
  lever sits in: on a per-house line the house its column resolves to (``derived.house``), else the column's
  interlocking (the owner, 2026-10-28). That station does all the code line work for the lever; its field unit drives
  masts in other houses internally, unseen by the office. A lever's tokens need no reporter, only an appliance it
  serves (the derivation's ``lever.serves``).
- **Lamps and consumer rows.** Panels define token content (the owner, 2026-10-28): what a station must send is the
  union of the indication tokens its consumers state. A lamp's or a consumer row's token belongs to the station of the
  appliance that reports it (``reporters``): on a per-house line the house that is its ``derived.controlPoint``. A lamp
  has nothing to do with columns. The reporter is the appliance that states the token: a track circuit its own, any
  other field appliance through the desk device that serves it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterator, Optional

from tools.layout_model import expression, reference
from tools.layout_model.grammar import lever_class, styles

StationKey = tuple[str, Optional[str]]                 # (interlocking, house); house None: the interlocking is the station


@dataclass
class Station:
    interlocking: str
    house: Optional[str]                               # None on a line whose station is the interlocking
    controls: set[str] = field(default_factory=set)    # bare tokens (783NWS)
    indications: set[str] = field(default_factory=set)  # bare tokens it must send (783NWK)

    @property
    def key(self) -> StationKey:
        return (self.interlocking, self.house)


@dataclass(frozen=True)
class Problem:
    """A consumer whose token no station can serve. ``kind``: ``interlocking`` (the named interlocking is not in the
    file), ``codeline`` (it is on no code line, so what it sends is unknown), ``unresolved`` (no appliance of it can
    report the token), ``station`` (appliances of two houses report it, on a line whose station is a house).
    ``where`` is the consumer; ``parties`` the other entities it is about, by model path: the interlocking it fails to
    resolve against when the file has it, and for ``station`` the appliances that report the token."""
    kind: str
    where: str
    text: str
    parties: tuple[str, ...] = ()


@dataclass(frozen=True)
class Reporter:
    """A field appliance that can report a token: the token's class, the appliance, and the circuit for a track
    circuit's token (a switch reports its OS circuit, named by its TC)."""
    cls: str
    appliance: str
    circuit: Optional[str] = None


@dataclass
class Codeline:
    stations: dict[StationKey, Station]
    problems: list[Problem]


# --------------------------------------------------------------------------------------------- encoding

def encoding(model: dict[str, Any], interlocking: str) -> Optional[str]:
    """The ``given.Kind`` of the code line an interlocking is on; None when it is on none."""
    line = model.get("interlockings", {}).get(interlocking, {}).get("relations", {}).get("codeline")
    return model.get("layout", {}).get("codelines", {}).get(line, {}).get("given", {}).get("Kind") if line else None


def scope(model: dict[str, Any], interlocking: str) -> Optional[str]:
    """What one station of this interlocking is: ``house`` or ``interlocking``; None when it is on no code line."""
    ix = model.get("interlockings", {}).get(interlocking)
    if ix is None or not ix.get("relations", {}).get("codeline"):
        return None
    return reference.station_of(encoding(model, interlocking))


def templates(model: dict[str, Any], interlocking: Optional[str], user: Optional[dict] = None) -> dict[str, tuple[str, ...]]:
    return reference.indication_tokens(encoding(model, interlocking) if interlocking else None, user)


# ------------------------------------------------------------------------------ which appliance reports a token

# Reporters state what they report: an appliance reports a token because it states it, never because a template filled
# with its name gives it. A track circuit states its own (``Indication``, ``${Name}K`` in the library). No other field
# appliance states a token: it is matched by Name to the desk device that serves it (``derived.serves``), whose bound
# pins' ``Indication.X`` map its tokens (``815NWK``, ``813WLK``, ``1MCK``). A field that names one token states it,
# negated or not (``!813WLK``); an expression over several tokens is a composite the desk consumes, and reports nothing.
# A missing field is not done yet: the token is then unresolved, never filled in. A mast reports nothing (the owner,
# 2026-10-28): a signal lever serves no appliance, and its tokens are its column's station's.
#
# INTERIM: two kinds of reporter state no token anywhere yet, so for them alone the reference data's indication
# templates are still read backwards: a switch reports its OS circuit, named by its TC (``{name}K``: ``783T1K``), and a
# field lamp other than a maintainer call reports ``{name}K``, or its name when that ends in K (``HBAK``, ``NFLK``). To
# be removed when they state theirs.

def _stated(text: str) -> Optional[str]:
    """The one token a field states: a single token, negated or not; None for an expression over several, or none."""
    try:
        tree = expression.parse(text)
    except expression.ExpressionError:
        return None
    while tree[0] == "not":
        tree = tree[1]
    return tree[1] if tree[0] == "token" else None


def _states(text: str, interlocking: str, token: str) -> bool:
    """Whether a field states ``token`` (bare) of ``interlocking``; a qualified token keeps its scope."""
    s, _, t = (_stated(text) or "").rpartition(":")
    return bool(t) and (not s or s.casefold() == interlocking.casefold()) and t.casefold() == token.casefold()


def _class(name: str, apps: dict[str, dict[str, Any]]) -> str:
    g = apps.get(name, {}).get("given", {})
    if g.get("Appliance") == "lamp":
        return "maintainer_call" if "maintainer_call" in styles(g) else "lamp"
    return lever_class(name, apps) or g.get("Appliance", "")


def _matches(template: str, token: str) -> Iterator[str]:
    """INTERIM: the names a ``{name}`` template gives ``token`` for."""
    m = re.fullmatch(re.escape(template).replace(re.escape("{name}"), "(?P<name>.+)"), token)
    if m:
        yield m["name"]
    if template.endswith("{name}K") and token[-1:] in ("K", "k"):
        yield token                                    # a name that ends in K is the token already (reference.indication_of)


def reporters(model: dict[str, Any], interlocking: str, token: str, user: Optional[dict] = None) -> list[Reporter]:
    """The appliances of one interlocking that report ``token`` (bare): those that state it, by their own field or their
    desk device's, and the interim template lookup above."""
    apps = model.get("interlockings", {}).get(interlocking, {}).get("appliances", {})
    out: list[Reporter] = []

    def found(r: Reporter) -> None:
        if r not in out:
            out.append(r)

    for n, a in apps.items():
        g = a.get("given", {})
        if g.get("Appliance") == "track_circuit" and _states(g.get("Indication", ""), interlocking, token):
            found(Reporter("track_circuit", n, n))
    for ou in model.get("officeUnits", {}).values():
        for dev in ou.get("devices", []):
            b, _, n = dev.get("derived", {}).get("serves", "").partition(":")
            if b != interlocking or n not in apps:
                continue
            g = dev.get("given", {})
            if any(_states(g.get(f"Indication.{pin}", ""), interlocking, token) for pin in dev.get("relations", {}).get("bindings", {})):
                found(Reporter(_class(n, apps), n))
    tmpl = templates(model, interlocking, user)
    for name in (x for t in tmpl.get("track_circuit", ()) for x in _matches(t, token)):          # INTERIM: OS circuits
        for s, a in apps.items():
            if a.get("given", {}).get("Appliance") == "switch" and a["given"].get("TC", "").strip() == name:
                found(Reporter("track_circuit", s, name))
    for name in (x for t in tmpl.get("lamp", ()) for x in _matches(t, token)):                   # INTERIM: field lamps
        if _class(name, apps) == "lamp":
            found(Reporter("lamp", name))
    return out


def circuit_of(model: dict[str, Any], token: str, user: Optional[dict] = None) -> Optional[str]:
    """The circuit a qualified track circuit token indicates (``Corporal:2NATK`` is ``Corporal:2NAT``), where one
    appliance of that interlocking reports it as a track circuit; None otherwise."""
    b, _, t = token.partition(":")
    if b not in model.get("interlockings", {}):
        return None
    circuits = {r.circuit for r in reporters(model, b, t, user) if r.circuit}
    return f"{b}:{circuits.pop()}" if len(circuits) == 1 else None


# ------------------------------------------------------------------------------------------------ stations

def stations(model: dict[str, Any], user: Optional[dict] = None) -> Codeline:
    """Every station of every interlocking on a code line, with the controls it receives and the indications it must
    send, and the consumers whose token no station serves. ``model`` is derived (ADR 0011 reader policy): it reads the
    appliances' ``controlPoint``, the columns' ``house`` and the desk devices' ``serves``, ``controls`` and
    ``indications``. ``user`` is the user's indication templates (``reference.indication_tokens``)."""
    ixs = model.get("interlockings", {})
    out: dict[StationKey, Station] = {}
    for b, ix in ixs.items():
        sc = scope(model, b)
        if sc == "house":
            for h in ix.get("houses", {}):
                out[(b, h)] = Station(b, h)
        elif sc == "interlocking":
            out[(b, None)] = Station(b, None)
    problems: list[Problem] = []

    def indication(token: str, what: str, where: str) -> None:
        b, _, t = token.partition(":")
        if b not in ixs:
            problems.append(Problem("interlocking", where, f"{what} consumes {token}, but {b} is no interlocking in this file"))
            return
        sc = scope(model, b)
        if sc is None:
            problems.append(Problem("codeline", where, f"{what} consumes {token}, but {b} is on no code line, so what it sends is unknown",
                                    (f"interlockings/{b}",)))
            return
        reps = reporters(model, b, t, user)
        if not reps:
            problems.append(Problem("unresolved", where, f"{what} consumes {token}, but no appliance of {b} reports {t}",
                                    (f"interlockings/{b}",)))
            return
        if sc == "interlocking":
            out[(b, None)].indications.add(t)
            return
        houses = {cp.partition(":")[2] for r in reps
                  if (cp := ixs[b].get("appliances", {}).get(r.appliance, {}).get("derived", {}).get("controlPoint"))}
        if len(houses) > 1:
            problems.append(Problem("station", where, f"{what} consumes {token}, which appliances of houses {', '.join(sorted(houses))} "
                                    f"report; {b}'s code line makes each house a station",
                                    (f"interlockings/{b}", *sorted({f"interlockings/{b}/appliances/{r.appliance}" for r in reps}))))
        elif houses and (b, next(iter(houses))) in out:
            out[(b, next(iter(houses)))].indications.add(t)
        # no house: the appliance's control point is unreached, reported by the derivation

    for ou_name, ou in model.get("officeUnits", {}).items():
        for i, dev in enumerate(ou.get("devices", [])):
            g, d = dev.get("given", {}), dev.get("derived", {})
            where = f"officeUnits/{ou_name}/devices/{i}"
            if g.get("Appliance") == "lever" and d.get("serves"):
                b = d["serves"].partition(":")[0]
                key = _column_station(model, ou_name, dev, b)
                mine = lambda tokens: {t.partition(":")[2] for t in tokens if t.partition(":")[0] == b}  # noqa: E731
                if key in out:
                    out[key].controls.update(mine(d.get("controls", [])))
                    out[key].indications.update(mine(d.get("indications", [])))
                what = f"lever {d['serves'].partition(':')[2]}"
                for token in d.get("indications", []):
                    if token.partition(":")[0] != b:            # another interlocking's indication: resolved like a lamp's
                        indication(token, what, where)
                continue
            elif g.get("Appliance") == "lamp":
                what = f"the lamp {g.get('Name', '')}".rstrip()
            else:
                continue
            for token in d.get("indications", []):
                indication(token, what, where)
    for a, ix in ixs.items():
        for row in ix.get("track", {}).get("consumers", []):
            token = row.get("relations", {}).get("indication")
            if token:
                indication(token, f"{a}: the consumer of {token}", f"interlockings/{a}/track/consumers/{row.get('id', '')}")
    return Codeline(out, problems)


def _column_station(model: dict[str, Any], ou_name: str, dev: dict[str, Any], b: str) -> Optional[StationKey]:
    """The station of the desk column a lever sits in: the house its column resolves to on a per-house line, else the
    interlocking."""
    sc = scope(model, b)
    if sc != "house":
        return (b, None) if sc else None
    ou_of, _, number = dev.get("relations", {}).get("column", "").partition(":")
    house = model.get("officeUnits", {}).get(ou_of or ou_name, {}).get("columns", {}).get(number, {}).get("derived", {}).get("house", "")
    hb, _, h = house.partition(":")
    return (b, h) if house and hb == b else None
