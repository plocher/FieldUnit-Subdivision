"""The Layout Data Model File (ADR 0008): schema lookup, validation and the canonical serialisation.

The compiler (milestone D) writes the file with ``dumps``; the reader library writes it back with the
same function, so read-then-write is byte-identical (ADR 0008 DoD1). ``validate`` is the gate of
DoD3. Nothing here knows KiCad.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import jsonschema

SCHEMA_ID = "layout-model/v2.0.0"            # rev 3 (ADR 0008); kept until rev 4 is ratified
SCHEMA_V3 = "layout-model/v3.0.0"            # rev 4 on ADR 0009: the compiler writes this
SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas" / "layout-model"
SCHEMA_PATH = SCHEMA_DIR / "v2.0.0.json"

_DIGITS = re.compile(r"(\d+)")
_SPACES = re.compile(r"\s+")


def schema_path(model: Any = None) -> Path:
    """The schema a model names in its ``schema`` string (``layout-model/<version>``); v2.0.0 when it names none."""
    sid = model.get("schema") if isinstance(model, dict) else None
    version = sid.split("/", 1)[1] if isinstance(sid, str) and sid.startswith("layout-model/") and "/" in sid else "v2.0.0"
    path = SCHEMA_DIR / f"{version}.json"
    return path if path.is_file() else SCHEMA_PATH


def load_schema(model: Any = None) -> dict[str, Any]:
    return json.loads(schema_path(model).read_text(encoding="utf-8"))


def validate(model: Any) -> None:
    """Raise ``jsonschema.ValidationError`` when ``model`` is not a Layout Data Model File."""
    jsonschema.Draft202012Validator(load_schema(model)).validate(model)


def errors(model: Any) -> list[str]:
    v = jsonschema.Draft202012Validator(load_schema(model))
    return sorted(f"{'/'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}" for e in v.iter_errors(model))


def sort_key(text: str) -> tuple:
    """Natural order, case folded, internal whitespace collapsed (ADR 0008 §4.8)."""
    folded = _SPACES.sub(" ", text.casefold().strip())
    # (0, number) before (1, text) so that mixed parts always compare; numbers first.
    return tuple((0, int(part), "") if part.isdigit() else (1, 0, part) for part in _DIGITS.split(folded) if part != "")


def canonical(value: Any) -> Any:
    """The same data with every dictionary in key order and every list in element order."""
    if isinstance(value, dict):
        return {k: canonical(value[k]) for k in sorted(value, key=sort_key)}
    if isinstance(value, list):
        items = [canonical(v) for v in value]
        return sorted(items, key=lambda v: sort_key(json.dumps(v, ensure_ascii=False, separators=(",", ":"))))
    return value


def dumps(model: Any) -> str:
    """The canonical text: two-space indent, UTF-8 (no escaping), one trailing newline."""
    return json.dumps(canonical(model), ensure_ascii=False, indent=2) + "\n"


def loads(text: str) -> Any:
    return json.loads(text)


def read(path: Path) -> Any:
    return loads(path.read_text(encoding="utf-8"))


def write(path: Path, model: Any) -> None:
    path.write_text(dumps(model), encoding="utf-8")
