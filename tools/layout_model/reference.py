"""Reference data: general facts, not layout data (ADR 0008 §4.7, ADR 0012 §6). A placeholder: the tables a writer and
the reference derivation share, each versioned so provenance can name it. Contents are TBD by the owner; only the
lookup and its override order are fixed: one lookup by key, the user's own table layered over the shipped default.
"""
from __future__ import annotations

from typing import Optional

# Versioned so provenance can name it.
REFERENCE_DATA = {"encodingTransportPairing": "2026-10-23", "driverEncodings": "2026-10-23", "indicationTokens": "2026-10-27.2", "stations": "2026-10-27", "codeLineCapacity": "2026-11-01", "codeLineSteps": "2026-11-01.3",
                  "trainOrderInputs": "2026-11-08", "regimes": "2026-11-10", "aspectNames": "2026-11-10"}
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


# What one code line type can carry, set by the physical machine (the owner, 2026-11-01): field stations per line, and
# controls and office indications per field station, each counted in function steps. A step is a timed pulse on the
# line; a token is symbolic (FieldUnit GLOSSARY §6, "A token is not a step"), so a station's need comes from
# ``CODE_LINE_STEPS``, never from its token count. None is no limit, or a limit the layout sets. Three forms: fixed per station; ``options``, a
# trade-off where more stations leave fewer controls (GRS Type H); ``steps``, one pool the railroad shares between
# station selection and functions (GRS Syncrostep). ``source`` names where the row comes from.
CODE_LINE_CAPACITY: dict[str, dict] = {
    "USS504": {"stations": 15, "controls": 7, "indications": 7, "source": "owner-supplied 2026-11-01, unverified"},
    "USS506": {"stations": 35, "controls": 7, "indications": 7, "source": "RRS506 (GLOSSARY §6); 506, 506A, 506B"},
    "USS506C": {"stations": 35, "controls": 7, "indications": 35, "source": "RRS506 (GLOSSARY §6)"},
    "GRS_K": {"stations": None, "controls": 8, "indications": 11,
              "source": "owner-supplied 2026-11-01, unverified; stations by the 8- or 10-step selection setup"},
    "GRS_H": {"options": ({"stations": 64, "controls": 4, "indications": 13},
                          {"stations": 32, "controls": 5, "indications": 13},
                          {"stations": 16, "controls": 6, "indications": 13}),
              "source": "owner-supplied 2026-11-01, unverified"},
    "GRS_SYNCROSTEP": {"steps": 13, "source": "owner-supplied 2026-11-01, unverified; apportioned per layout"},
    "AAR": {"stations": None, "controls": None, "indications": None, "source": "GLOSSARY: no capacity limit"},
}


def code_line_capacity(encoding: Optional[str], user: Optional[dict[str, dict]] = None) -> Optional[dict]:
    """The capacity row for a code line of ``encoding`` (its ``given.Kind``): the user's own row over the shipped one;
    None when neither has one (capacity unknown, never assumed)."""
    table = {**CODE_LINE_CAPACITY, **(user or {})}
    return table.get(encoding or "")


# The function steps each appliance class takes on a code line type, controls and office indications (the owner,
# 2026-11-01). A switch takes two each way: its pair says normal, reverse or neither ("don't change" as a control, "in
# motion" as an indication); both up is invalid. A signal lever's three controls (NGS, SGS, HS) take three steps: HS,
# the explicit stop, has its own (the owner, 2026-11-01). None is not known yet, never assumed.
CODE_LINE_STEPS: dict[str, dict[str, dict[str, Optional[int]]]] = {
    "USS506": {
        "switch": {"controls": 2, "indications": 2},
        "signal": {"controls": 3, "indications": 3},
        "lock": {"controls": 1, "indications": 2},             # a two-position lever, like a maintainer call
        "track_circuit": {"controls": 0, "indications": 1},
        "maintainer_call": {"controls": 1, "indications": 1},
    },
}


def code_line_steps(encoding: Optional[str], user: Optional[dict[str, dict]] = None) -> Optional[dict[str, dict[str, Optional[int]]]]:
    """The steps by appliance class for a code line of ``encoding``: the user's own classes over the shipped ones; None
    when neither has the type (steps unknown, never assumed)."""
    shipped, own = CODE_LINE_STEPS.get(encoding or ""), (user or {}).get(encoding or "")
    if shipped is None and own is None:
        return None
    return {**(shipped or {}), **(own or {})}


# A train order board's face (the owner, 2026-11-05 and 2026-11-08, docs/review/signal-symbols-worklist.md "Rulings
# 2026-11-08: train order boards"): a fascia lever (Appliance ``lever``, Style ``train_order``) serves one face and
# has the inputs STOP and SLOW. Nothing asserted shows CLEAR; otherwise the most restrictive asserted input wins, in
# this table's order from the most restrictive: STOP shows STOP (orders to pick up), SLOW APPROACH (orders handed up
# on the fly). CALLON is not a train order control: it is the block signal's indication, used with the board to bring
# a train stopped at the block boundary up to the station (the owner, 2026-11-08). The fascia control is local: no
# code line carries it. The words are indications (FieldUnit docs/GLOSSARY.md), never a colour or a blade angle. The
# run-time logic is FieldUnit's (FieldUnit issue #44); the derivation states only what a face can show from the
# inputs its lever binds (``derive.train_orders``). The feature's table of what a face shows is checked against this
# order by its step alone.
TRAIN_ORDER_INPUTS = (("STOP", "STOP"), ("SLOW", "APPROACH"))
TRAIN_ORDER_CLEAR = "CLEAR"


# The regimes a piece of track may be under (ADR 0013 §7.1 and decision 3; the owner, 2026-11-10; Railroad 0ddd395): each
# a GCOR Rule POLICY marker's Kind, with the chapter or rule title of the GCOR 8th edition as the owner opened it
# (2026-11-10, ticket #113). The GCOR prefix scopes the vocabulary to one rulebook; a later Studio presents the era's
# set. Nothing era-specific yet. A regime is stated by its marker, never derived from signals (GCOR 10.1: CTC limits
# are designated in the timetable); the marker's extent is derived (``derive.regimes``). The current-of-traffic sign
# is a direction fact, not a regime, and may share a piece with one (§8).
REGIMES: dict[str, str] = {
    "GCOR_RULE_10": "CTC",                                         # Chapter 10
    "GCOR_RULE_14": "TWC",                                         # Chapter 14, track warrant control
    "GCOR_RULE_16": "DTC",                                         # Chapter 16, direct traffic control
    "GCOR_RULE_6_13": "Yard Limits",
    "GCOR_RULE_6_28": "Movement on Other than Main Track",
}
CTC = "GCOR_RULE_10"                                               # the regime of track within a control point
CURRENT_OF_TRAFFIC = "GCOR_RULE_9_14"                              # "Movement with the Current of Traffic": Direction LEFT or RIGHT
# JMRI "aspect names" (never shortened to "aspect"), the string a JMRI signal mast driver publishes for a mast's
# indication (the owner, 2026-11-05, issue #96; the seam is JMRI's MqttSignalMast: ``"<aspect name>; Lit; Unheld"``).
# Keyed by signal system, then indication, then the mast's Kind (ADR 0013 §5: CONTROLLED, ABSOLUTE, PERMISSIVE): a row
# is one name for every Kind, or a map by Kind where the system folds the plate into the name (SP's STOP is "Home
# Signal Red" on a controlled or absolute mast, "Stop and Proceed" on a permissive one). Our indication vocabulary does
# not change. An indication with no row is not presentable in that system. The tables are ours and editable; JMRI's
# ``xml/signals/<system>/aspects.xml`` is a source for names, not an authority, and its appearance files and
# aspectMappings are not adopted. ``basic`` adds RESTRICTING, which JMRI's basic lacks. In SPTCO-1969, lunar was
# dropped in later eras (red over yellow): an edit to the DIVERGING_RESTRICTING row. ADVANCE_APPROACH and the
# speed-signalling words have no row there; the owner expects them absent on western roads.
ASPECT_NAMES: dict[str, dict[str, object]] = {
    "basic": {
        "CLEAR": "Clear",
        "APPROACH": "Approach",
        "STOP": "Stop",
        "DIVERGING_CLEAR": "Diverging Clear",
        "DIVERGING_APPROACH": "Diverging Approach",
        "RESTRICTING": "Restricting",
    },
    "SPTCO-1969": {
        "CLEAR": "Block Signal Green",
        "APPROACH": "Approach Signal Yellow",
        "RESTRICTING": "Restricting",
        "STOP": {"CONTROLLED": "Home Signal Red", "ABSOLUTE": "Home Signal Red", "PERMISSIVE": "Stop and Proceed"},
        "DIVERGING_CLEAR": "Block Signal Green for Diverging Route",
        "APPROACH_DIVERGING": "Block Signal Yellow over Green",
        "APPROACH_MEDIUM": "Approach Medium - Flashing Yellow",
        "DIVERGING_APPROACH": "Home Signal Yellow for Diverging Route",
        "DIVERGING_RESTRICTING": "Home Signal Red over Lunar",
    },
}


def signal_systems(user: Optional[dict[str, dict[str, object]]] = None) -> set[str]:
    """The signal systems a table names, shipped and the user's own."""
    return set(ASPECT_NAMES) | set(user or {})


def aspect_name(system: Optional[str], indication: str, kind: Optional[str], user: Optional[dict[str, dict[str, object]]] = None) -> Optional[str]:
    """The aspect name a JMRI signal mast driver publishes for ``indication`` on a mast of ``kind`` in ``system``: the
    user's own row over the shipped one; None when neither has it (not presentable in that system, never guessed)."""
    for table in (user or {}, ASPECT_NAMES):
        row = table.get(system or "", {}).get(indication)
        if row is None:
            continue
        if isinstance(row, dict):
            return row.get(kind or "")
        return row
    return None
