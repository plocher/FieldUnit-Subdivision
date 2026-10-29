"""Reference data: general facts, not layout data (ADR 0008 §4.7, ADR 0012 §6). A placeholder: the tables a writer and
the reference derivation share, each versioned so provenance can name it. Contents are TBD by the owner; only the
lookup and its override order are fixed: one lookup by key, the user's own table layered over the shipped default.
"""
from __future__ import annotations

from typing import Optional

# Versioned so provenance can name it.
REFERENCE_DATA = {"encodingTransportPairing": "2026-10-23", "driverEncodings": "2026-10-23", "indicationTokens": "2026-10-27.2", "stations": "2026-10-27"}
# An encoding's Kind pairs with its transport's Kind (ADR 0009 §3.10).
TRANSPORT_OF_ENCODING = {"AAR": "MQTT", "USS506": "TIMECODE", "BITS": "TIMECODE", "JMRI": "MQTT", "CMRI": "CMRI"}
# A driver whose IC is an encoding needs that I/O encoding on its processor (ADR 0009 §3.3, §3.6, §3.12 "IC native or encoded").
ENCODING_OF_IC = {"MQTT-JMRI": "JMRI"}

# The office indications a station sends on its code line, by the code line's encoding Kind: each a list of token
# templates by appliance class. By the AAR nomenclature behind every code line, controls end in S and indications in K
# (the owner, 2026-10-27; ADR 0011 amendment), so every encoding shares the default until a railroad or an encoding
# says otherwise. The forms are FieldUnit's (docs/GLOSSARY.md §10.3, "FieldUnit tokens by appliance"; WireCodec.h's
# AarTextCodec): a track circuit `<name>K`; a switch `<name>NWK`, `<name>RWK`; an electric lock `<name>WLK`,
# `<name>WLQK`, not NWK/RWK (the owner, 2026-10-27); a signal lever `<lever>NGK`, `<lever>SGK`, `<lever>TEK`; a
# maintainer call `<name>K`. A virtual track circuit and a non-vital lamp appliance (`NFLK`, `HBA`) send `<name>K`, the
# form the desk's lamps consume (settled by the desk, 2026-10-27). A name that ends in K is the token already
# (``indication_of``). ``{name}`` is the appliance's or circuit's name, ``{lever}`` a signal's lever number.
# A station's controls are not here: they are the desk levers' bindings that end in S (the owner, 2026-10-27).
INDICATION_TOKENS: dict[str, dict[str, tuple[str, ...]]] = {
    "default": {
        "track_circuit": ("{name}K",),
        "switch": ("{name}NWK", "{name}RWK"),
        "lock": ("{name}WLK", "{name}WLQK"),
        "signal": ("{lever}NGK", "{lever}SGK", "{lever}TEK"),
        "maintainer_call": ("{name}K",),
        "lamp": ("{name}K",),                     # a non-vital lamp (a flasher, a hot box alarm): the desk's form (2026-10-27)
    },
}


def indication_tokens(encoding: Optional[str], user: Optional[dict[str, dict[str, tuple[str, ...]]]] = None) -> dict[str, tuple[str, ...]]:
    """The token templates by appliance class for a code line of ``encoding`` (its ``given.Kind``): the shipped default,
    then the shipped table for that encoding, then the user's own default and table for it; the later wins per class."""
    out: dict[str, tuple[str, ...]] = {}
    for table in (INDICATION_TOKENS, user or {}):
        out.update(table.get("default", {}))
        if encoding:
            out.update(table.get(encoding, {}))
    return out


def indication_of(name: str, template: str = "{name}K") -> str:
    """The token a desk lamp's or a drawn reference's circuit names: the template applied, unless the name is a token
    already (it ends in K, as ``MC1K`` does; FieldUnit's AarTextCodec adds K only when it is absent)."""
    return name if name[-1:] in ("K", "k") else template.format(name=name)


# What one station on a code line is, by the code line's encoding Kind (the owner, 2026-10-27): on a US&S 506 line each
# house answers at its own address; on an AAR token line, which has no vocabulary limit, the interlocking is one station.
# An encoding not listed takes the default.
STATION = {"default": "interlocking", "USS506": "house", "AAR": "interlocking"}


def station_of(encoding: Optional[str], user: Optional[dict[str, str]] = None) -> str:
    table = {**STATION, **(user or {})}
    return table.get(encoding or "", table["default"])
