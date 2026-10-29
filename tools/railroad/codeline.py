"""The code line between the office and its field stations (domain library, ADR 0012 §5): per station, the control
tokens it receives and the indication tokens it must send, computed on demand from a derived model. Nothing here is
stored in the file (the owner, 2026-10-28: station packets are not stored); the reference derivation checks the model
with the same function (``stations``), so there is one definition.

What a station is depends on its code line's encoding (``reference.station_of``; the owner, 2026-10-27): on a US&S 506
line each house is a station, on an AAR token line the interlocking is one.

- **Controls.** A desk lever's ``derived.controls`` go to the station of the desk column the lever sits in: on a
  per-house line the house its column resolves to (``derived.house``), else the column's interlocking.
- **Indications.** Panels define token content (the owner, 2026-10-28): what a station must send is the union of the
  indication tokens its consumers state, the desk levers' and lamps' ``derived.indications`` and the remote consumer
  markers' ``relations.indication``. Field appliances carry no tokens. Each token belongs to the station of the
  appliance that reports it (``reporters``): on a per-house line the house that is its ``derived.controlPoint``. A lamp
  has nothing to do with columns.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterator, Optional

from tools.layout_model import reference
from tools.layout_model.grammar import lever_class, lever_of, styles

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
    report the token), ``station`` (appliances of two houses report it, on a line whose station is a house)."""
    kind: str
    where: str
    text: str


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

# INTERIM (the owner, 2026-10-28): panels define token content, so which field appliance reports a token is not yet a
# stated fact. Until it is, the reference data's indication templates are read backwards, here and nowhere else: a
# token is reported by an appliance of the class whose template, filled with the appliance's name (or a mast's lever),
# gives the token (``{name}K`` a track circuit, a switch's OS circuit by its TC, a maintainer call or another lamp;
# ``{name}NWK`` a powered switch; ``{name}WLK`` an electric lock; ``{lever}NGK`` a signal lever's masts). An appliance
# the dispatcher does not control reports nothing of its own: a manual or manual_sensed switch, a derail, a gang
# follower (``grammar.lever_class``), and a mast has no K of its own. To be revisited with the token rulings.

def _matches(template: str, token: str) -> Iterator[dict[str, str]]:
    pattern = re.escape(template).replace(re.escape("{name}"), "(?P<name>.+)").replace(re.escape("{lever}"), r"(?P<lever>\d+)")
    m = re.fullmatch(pattern, token)
    if m:
        yield m.groupdict()
    if template.endswith("{name}K") and token[-1:] in ("K", "k"):
        yield {"name": token}                          # a name that ends in K is the token already (reference.indication_of)


def _candidates(cls: str, names: dict[str, str], apps: dict[str, dict[str, Any]]) -> Iterator[Reporter]:
    n = names.get("name", "")
    g = apps.get(n, {}).get("given", {})
    if cls == "track_circuit":
        if g.get("Appliance") == "track_circuit":
            yield Reporter(cls, n, n)
        for s, a in apps.items():
            if a.get("given", {}).get("Appliance") == "switch" and a["given"].get("TC", "").strip() == n:
                yield Reporter(cls, s, n)
    elif cls in ("switch", "lock"):
        if lever_class(n, apps) == cls:
            yield Reporter(cls, n)
    elif cls == "signal":
        for m, a in sorted(apps.items()):
            if a.get("given", {}).get("Appliance") == "mast" and lever_of(m) == names.get("lever"):
                yield Reporter(cls, m)
    elif cls == "maintainer_call":
        if g.get("Appliance") == "lamp" and "maintainer_call" in styles(g):
            yield Reporter(cls, n)
    elif cls == "lamp":
        if g.get("Appliance") == "lamp" and "maintainer_call" not in styles(g):
            yield Reporter(cls, n)


def reporters(ix: dict[str, Any], token: str, tmpl: dict[str, tuple[str, ...]]) -> list[Reporter]:
    """The appliances of one interlocking that can report ``token`` (bare), by the interim template lookup above."""
    apps = ix.get("appliances", {})
    out: list[Reporter] = []
    for cls, temps in tmpl.items():
        for t in temps:
            for names in _matches(t, token):
                out += [r for r in _candidates(cls, names, apps) if r not in out]
    return out


def circuit_of(model: dict[str, Any], token: str, user: Optional[dict] = None) -> Optional[str]:
    """The circuit a qualified track circuit token indicates (``Corporal:2NATK`` is ``Corporal:2NAT``), where one
    appliance of that interlocking reports it as a track circuit; None otherwise."""
    b, _, t = token.partition(":")
    ix = model.get("interlockings", {}).get(b)
    if ix is None:
        return None
    circuits = {r.circuit for r in reporters(ix, t, templates(model, b, user)) if r.circuit}
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
            problems.append(Problem("codeline", where, f"{what} consumes {token}, but {b} is on no code line, so what it sends is unknown"))
            return
        reps = reporters(ixs[b], t, templates(model, b, user))
        if not reps:
            problems.append(Problem("unresolved", where, f"{what} consumes {token}, but no appliance of {b} reports {t}"))
            return
        if sc == "interlocking":
            out[(b, None)].indications.add(t)
            return
        houses = {cp.partition(":")[2] for r in reps
                  if (cp := ixs[b].get("appliances", {}).get(r.appliance, {}).get("derived", {}).get("controlPoint"))}
        if len(houses) > 1:
            problems.append(Problem("station", where, f"{what} consumes {token}, which appliances of houses {', '.join(sorted(houses))} "
                                    f"report; {b}'s code line makes each house a station"))
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
                if key in out:
                    out[key].controls.update(t.partition(":")[2] for t in d.get("controls", []) if t.partition(":")[0] == b)
                what = f"lever {d['serves'].partition(':')[2]}"
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
