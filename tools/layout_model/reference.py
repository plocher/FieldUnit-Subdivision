"""Reference data: general facts, not layout data (ADR 0008 §4.7, ADR 0012 §6). The tables are JSON data files under the
schema folder, ``schemas/layout-model/reference/<table>.json``, each with its schema beside it, a ``schemaVersion``
(0 until the KiCad importer and FieldUnit work end to end) and a ``version``, its provenance date (the owner, 2026-11-13: the
files are the source, not an output; there is no second compiler). This module loads them and holds no table literal
(gate ``tests/test_reference_data.py``). The lookups keep one shape: one lookup by key, the user's own table layered over
the shipped one, the user's wins; a key with no row is None, never guessed. Per-entity resolution into ``derived`` is
``reference_data.py``.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

FOLDER = Path(__file__).resolve().parents[2] / "schemas" / "layout-model" / "reference"
FILE_PREFIX = "layout-model/reference/"               # a table's file as provenance names it, relative to schemas/


def tables() -> list[str]:
    """Every table the folder holds, by name (a file's stem; its schema is beside it)."""
    return sorted(p.stem for p in FOLDER.glob("*.json") if not p.name.endswith(".schema.json"))


def path(table: str) -> Path:
    return FOLDER / f"{table}.json"


def schema_path(table: str) -> Path:
    return FOLDER / f"{table}.schema.json"


@lru_cache(maxsize=None)
def load(table: str) -> dict[str, Any]:
    """The whole file of ``table``: ``table``, ``schemaVersion``, ``version``, ``provenance``, ``rows`` and the table's
    own constants. Read once."""
    return json.loads(path(table).read_text(encoding="utf-8"))


def rows(table: str) -> dict[str, Any]:
    return load(table)["rows"]


def provenance() -> dict[str, dict[str, Any]]:
    """What a layout file states in ``provenance.referenceData``: each table's file, version and schema version."""
    return {t: {"file": FILE_PREFIX + path(t).name, "version": load(t)["version"], "schemaVersion": load(t)["schemaVersion"]}
            for t in tables()}


# Loaded names the importer and the derivation read directly.
TRANSPORT_OF_ENCODING: dict[str, str] = rows("encodingTransportPairing")       # an encoding's Kind to its transport's Kind
ENCODING_OF_IC: dict[str, str] = rows("driverEncodings")                      # a driver IC that is an encoding, to its Kind
REGIMES: dict[str, str] = rows("regimes")                                     # GCOR Rule Kind to its title
CTC: str = load("regimes")["ctc"]                                             # the regime of track within a control point
CURRENT_OF_TRAFFIC: str = load("regimes")["currentOfTraffic"]                 # a direction fact, not a regime
HEAD_MODELS: dict[str, dict[str, Any]] = rows("headModels")                   # Style to its row (source, words)


def indication_tokens(encoding: Optional[str], user: Optional[dict[str, dict[str, Any]]] = None) -> dict[str, tuple[str, ...]]:
    """The token templates by appliance class for a code line of ``encoding`` (its ``given.Kind``): the shipped default,
    then the shipped table for that encoding, then the user's own default and table for it; the later wins per class."""
    out: dict[str, tuple[str, ...]] = {}
    for table in (rows("indicationTokens"), user or {}):
        out.update({k: tuple(v) for k, v in table.get("default", {}).items()})
        if encoding:
            out.update({k: tuple(v) for k, v in table.get(encoding, {}).items()})
    return out


def indication_of(name: str, template: str = "{name}K") -> str:
    """The token a desk lamp's or a drawn reference's circuit names: the template applied, unless the name is a token
    already (it ends in K, as ``MC1K`` does; FieldUnit's AarTextCodec adds K only when it is absent)."""
    return name if name[-1:].upper() == "K" else template.format(name=name)


def station_of(encoding: Optional[str], user: Optional[dict[str, str]] = None) -> str:
    """What one station on a code line of ``encoding`` is: ``house`` or ``interlocking``; an encoding not listed takes
    the default."""
    table = {**rows("stations"), **(user or {})}
    return table.get(encoding or "", table["default"])


def code_line_capacity(encoding: Optional[str], user: Optional[dict[str, dict]] = None) -> Optional[dict]:
    """The capacity row for a code line of ``encoding`` (its ``given.Kind``): the user's own row over the shipped one;
    None when neither has one (capacity unknown, never assumed)."""
    table = {**rows("codeLineCapacity"), **(user or {})}
    return table.get(encoding or "")


def code_line_steps(encoding: Optional[str], user: Optional[dict[str, dict]] = None) -> Optional[dict[str, dict[str, Optional[int]]]]:
    """The steps by appliance class for a code line of ``encoding``: the user's own classes over the shipped ones; None
    when neither has the type (steps unknown, never assumed)."""
    shipped, own = rows("codeLineSteps").get(encoding or ""), (user or {}).get(encoding or "")
    if shipped is None and own is None:
        return None
    return {**(shipped or {}), **(own or {})}


def train_order_inputs(rulebook: Optional[str], user: Optional[dict[str, dict[str, Any]]] = None) -> tuple[str, dict[str, Any]]:
    """The train order face row the layout's ``rulebook`` selects, and the key it resolved to: the user's own row for the
    rulebook, else the shipped one, else each table's ``default``. A row is ``{"inputs": [{"input", "indication"}, ...],
    "rest": word}``, the inputs ranked from the most restrictive (FieldUnit ADR 0010 D1, D2)."""
    for key in ((rulebook,) if rulebook else ()) + ("default",):
        for table in (user or {}, rows("trainOrderInputs")):
            if key in table:
                return key, table[key]
    raise KeyError("the trainOrderInputs table has no default row")


def signal_systems(user: Optional[dict[str, dict[str, object]]] = None) -> set[str]:
    """The signal systems a table names, shipped and the user's own."""
    return set(rows("aspectNames")) | set(user or {})


def aspect_name(system: Optional[str], indication: str, kind: Optional[str], user: Optional[dict[str, dict[str, object]]] = None) -> Optional[str]:
    """The aspect name a JMRI signal mast driver publishes for ``indication`` on a mast of ``kind`` in ``system``: the
    user's own row over the shipped one; None when neither has it (not presentable in that system, never guessed)."""
    for table in (user or {}, rows("aspectNames")):
        row = table.get(system or "", {}).get(indication)
        if row is None:
            continue
        if isinstance(row, dict):
            return row.get(kind or "")
        return row
    return None


def aspect_names(system: Optional[str], kind: Optional[str], user: Optional[dict[str, dict[str, object]]] = None) -> dict[str, str]:
    """Every indication ``system`` presents on a mast of ``kind``, to its aspect name, in the tables' order; the user's
    rows over the shipped ones."""
    out: dict[str, str] = {}
    for table in (rows("aspectNames"), user or {}):
        for indication in table.get(system or "", {}):
            name = aspect_name(system, indication, kind, user)
            if name is not None:
                out[indication] = name
    return out


def head_model(style: Optional[str], user: Optional[dict[str, dict[str, object]]] = None) -> Optional[dict[str, dict[str, object]]]:
    """The head model table of a head of ``style`` (its ``given.Style``): head word -> its outputs; the user's own row
    over the shipped one; None when neither has it (what the head presents is unknown, never guessed)."""
    for table in (user or {}, rows("headModels")):
        row = table.get(style or "")
        if row is not None:
            return dict(row["words"])
    return None


def presents(style: Optional[str], user: Optional[dict[str, dict[str, object]]] = None) -> Optional[list[str]]:
    """The head words a head of ``style`` can show: the keys of its model table, in the table's order; None for a Style
    with no row."""
    words = head_model(style, user)
    return None if words is None else list(words)


def policy(rulebook: Optional[str], user: Optional[dict[str, object]] = None) -> Optional[dict[str, dict[str, list[str]]]]:
    """The head policy of ``rulebook``: head count (a string) -> mast indication -> the head word of each position top
    down (the owner's lookup, 2026-11-13). The user's own row over the shipped one; None when neither has the rulebook.
    No row is shipped yet: the rows land with the demand derivation (#62), so a mast derives no ``shows`` until then."""
    for table in (user or {}, rows("policies")):
        row = table.get(rulebook or "")
        if row is not None:
            return row
    return None
