"""Names and Styles as the rules read them: the one definition the reference derivation and the domain libraries share.

ADR 0003: a mast is its signal (lever and side) plus its heads' letters, ascending (rules 6 and 7); a gang id is a switch
name less its trailing letter, and the switch named by the id alone leads the gang (D8). ADR 0013 §4: "powered" is the
seam word, a switch or derail whose position the field unit knows and may move, never "has a motor"; a CP Name makes
nothing powered. The owner, 2026-11-09: a derail is a switch with the word ``derail`` in its Style, and the switch
vocabulary names its regime; a dependent derail (D8: its gang id names a switch gang) takes its switch's regime.
"""
from __future__ import annotations

import re
from typing import Any

POWERED = frozenset({"powered", "dual", "local"})   # the field unit knows and may move the points (ADR 0013 §4)
LOCKED = frozenset({"lock"})                       # an electric lock on a hand-throw switch: WLK/WLQK, not NWK/RWK
UNPOWERED = frozenset({"manual", "manual_sensed", "spring"}) | LOCKED   # by hand; may lie in a station-to-station block (ADR 0013 §4)
REGIMES = POWERED | UNPOWERED                      # the switch words; one of them states how a switch or derail is worked
HAND = UNPOWERED - LOCKED                          # worked by hand with no lever device at all
DERAIL = "derail"
LEVER = re.compile(r"^\d+")
MAST_NAME = re.compile(r"^(0?[1-9]\d{0,3}[LRNSEW])([A-Z]+)$")
GANG = re.compile(r"(?<=\d)[A-Z]$")
# ADR 0003 D1: a drawing uses N/S, E/W or L/R as local policy decides, with one fixed mapping: Left = North and West,
# Right = South and East. The code uses LEFT and RIGHT; the drawn letter stays in the name.
DIRECTION = {"L": "LEFT", "N": "LEFT", "W": "LEFT", "R": "RIGHT", "S": "RIGHT", "E": "RIGHT"}


def direction_of(letter: str) -> str | None:
    """The direction a drawn letter names, ``LEFT`` or ``RIGHT`` (ADR 0003 D1); None for any other letter."""
    return DIRECTION.get(letter)


def styles(given: dict[str, str]) -> list[str]:
    return sorted(x.strip() for x in given.get("Style", "").split(",") if x.strip())


def _given(name: str, appliances: dict[str, dict[str, Any]]) -> dict[str, str]:
    return appliances.get(name, {}).get("given", {})


def is_switch(given: dict[str, str]) -> bool:
    return given.get("Appliance") == "switch"


def is_derail(given: dict[str, str]) -> bool:
    """A derail: a switch with the word ``derail`` in its Style (the owner, 2026-11-09), ports C and R."""
    return is_switch(given) and DERAIL in styles(given)


def regime_word(given: dict[str, str]) -> str | None:
    """The one switch word a switch or derail states in its Style (``powered``, ``dual``, ``local``, ``lock``,
    ``manual_sensed``, ``manual``, ``spring``); None when it states none or more than one."""
    words = REGIMES & set(styles(given))
    return next(iter(words)) if len(words) == 1 else None


def gang_switches(name: str, appliances: dict[str, dict[str, Any]]) -> list[str]:
    """The switches and locks (no derails) whose gang id is ``name``'s, by name (ADR 0003 D8)."""
    lead = GANG.sub("", name)
    return sorted(n for n, a in appliances.items() if is_switch(a.get("given", {})) and not is_derail(a.get("given", {}))
                  and GANG.sub("", n) == lead)


def depends_on(name: str, appliances: dict[str, dict[str, Any]]) -> str | None:
    """The switch a dependent derail follows (ADR 0003 D8: its gang id names a switch or lock gang in the interlocking):
    the switch named by the id alone, else the gang's first member by name. None for an independent derail and for
    anything that is no derail."""
    if not is_derail(_given(name, appliances)):
        return None
    lead = GANG.sub("", name)
    gang = gang_switches(name, appliances)
    return None if not gang else lead if lead in gang else gang[0]


def regime(name: str, appliances: dict[str, dict[str, Any]]) -> str | None:
    """How a switch or derail is worked: its own switch word, or for a dependent derail its switch's, whatever its own
    word says (the owner, 2026-11-09). None for a switch that states no word and for anything that is no switch."""
    g = _given(name, appliances)
    if not is_switch(g):
        return None
    lead = depends_on(name, appliances)
    return regime(lead, appliances) if lead else regime_word(g)


def is_powered(name: str, appliances: dict[str, dict[str, Any]]) -> bool:
    """A powered switch or derail (ADR 0013 §4): one whose regime is ``powered``, ``dual`` or ``local``, so the field
    unit knows its position and may move it. A hand-throw switch (``manual``, ``manual_sensed``), a spring switch and
    an electrically locked hand-throw switch (``lock``) are not powered, whatever CP Name they state: §4 lets them lie
    in a station-to-station block, and a CP Name makes nothing powered. A dependent derail is powered when its switch
    is. False for a switch that states no regime word and for anything that is no switch."""
    return regime(name, appliances) in POWERED


def leads_gang(name: str, switches: set[str] | frozenset[str]) -> bool:
    """A switch that is no gang follower: its name is its gang id, or no switch is named by the id alone."""
    lead = GANG.sub("", name)
    return lead == name or lead not in switches


def lever_of(mast: str) -> str | None:
    """A mast's signal lever number (``784`` of ``784EAB``); None when the name is not ADR 0003's grammar."""
    return LEVER.match(mast).group(0) if MAST_NAME.match(mast) else None


def lever_class(name: str, appliances: dict[str, dict[str, Any]]) -> str | None:
    """The class of a field switch or derail the dispatcher works with a desk lever: ``switch`` (regime ``powered`` or
    ``dual``) or ``lock`` (an electric lock). None for every one that has no desk lever: a ``local`` one (its
    Local-Switch alone works it), a hand-throw one, a dependent derail (its switch's lever), a gang follower (it
    reports through its gang's lead), and for anything that is no switch."""
    g = _given(name, appliances)
    if not is_switch(g) or depends_on(name, appliances):
        return None
    switches = {n for n, a in appliances.items() if is_switch(a.get("given", {}))}
    if not leads_gang(name, switches):
        return None
    r = regime(name, appliances)
    return "lock" if r in LOCKED else "switch" if r in ("powered", "dual") else None
