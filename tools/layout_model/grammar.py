"""Names and Styles as the rules read them: the one definition the reference derivation and the domain libraries share.

ADR 0003: a mast is its signal (lever and side) plus its heads' letters, ascending (rules 6 and 7); a gang id is a switch
name less its trailing letter, and the switch named by the id alone leads the gang (D8). GLOSSARY: a powered switch has
a lever and reports its position; an electric lock (Style ``lock``) is worked by the dispatcher's lock lever.
"""
from __future__ import annotations

import re
from typing import Any

POWERED = frozenset({"powered", "dual"})           # switch Styles with a lever and NWK/RWK (GLOSSARY: powered switch)
LOCKED = frozenset({"lock"})                       # an electric lock: WLK/WLQK, not NWK/RWK (the owner, 2026-10-27)
LEVER = re.compile(r"^\d+")
MAST_NAME = re.compile(r"^(0?[1-9]\d{0,3}[LRNSEW])([A-Z]+)$")
GANG = re.compile(r"(?<=\d)[A-Z]$")


def styles(given: dict[str, str]) -> list[str]:
    return sorted(x.strip() for x in given.get("Style", "").split(",") if x.strip())


def leads_gang(name: str, switches: set[str] | frozenset[str]) -> bool:
    """A switch that is no gang follower: its name is its gang id, or no switch is named by the id alone."""
    lead = GANG.sub("", name)
    return lead == name or lead not in switches


def lever_of(mast: str) -> str | None:
    """A mast's signal lever number (``784`` of ``784EAB``); None when the name is not ADR 0003's grammar."""
    return LEVER.match(mast).group(0) if MAST_NAME.match(mast) else None


def lever_class(name: str, appliances: dict[str, dict[str, Any]]) -> str | None:
    """The class of a field switch the dispatcher works with a lever: ``switch`` (powered or dual) or ``lock`` (an
    electric lock). None for every switch that has no lever: a manual or manual_sensed switch, a derail (dependent or
    independent), a gang follower (it reports through its gang's lead), and for anything that is no switch."""
    g = appliances.get(name, {}).get("given", {})
    if g.get("Appliance") != "switch" or g.get("Style") == "derail":
        return None
    switches = {n for n, a in appliances.items() if a.get("given", {}).get("Appliance") == "switch"}
    if not leads_gang(name, switches):
        return None
    st = set(styles(g))
    return "lock" if LOCKED & st else "switch" if POWERED & st else None
