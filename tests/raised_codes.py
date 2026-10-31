"""Every diagnostic code a package raises, read from its source: the gate's evidence for the two registries (ADR 0012
§3.3). A rule check is raised through the derivation's reporter (``self.r.add("code", ...)``, ``add("code", ...)``) or
a domain library's problem kind (``derive._Derivation.PROBLEM_CODES``); an import diagnostic through
``report.error/warning/info/missing("code", ...)``, ``one(..., "code")`` (error) or ``stated(..., "code")`` (missing,
the code with ``.missing``). A code built at run time is listed by the rule that builds it."""
from __future__ import annotations

import ast
from pathlib import Path

LEVEL_OF_METHOD = {"error": "error", "warning": "warning", "info": "info", "missing": "missing"}


def _calls(path: Path):
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Call):
            yield node


def _literal(node) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def import_codes(package: Path) -> dict[str, set[str]]:
    """Each code the KiCad importer raises, to the levels it raises it at; a code it cannot read is under ``None``."""
    out: dict[str, set[str]] = {}
    for path in sorted(package.glob("*.py")):
        for call in _calls(path):
            f = call.func
            name = f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else None
            if isinstance(f, ast.Attribute) and name in LEVEL_OF_METHOD and call.args:
                code = _literal(call.args[0])
                if code is None and isinstance(call.args[0], ast.JoinedStr) and ast.unparse(call.args[0])[2:].startswith("identity."):
                    continue                                          # identity.<key field>: listed by key_codes()
                if code is None and isinstance(call.args[0], (ast.Name, ast.JoinedStr)) and path.name == "seams.py" \
                        and ast.unparse(call.args[0]) in ("code", "f'{code}.missing'"):
                    continue                                          # one() and stated(): their callers name the code
                out.setdefault(code, set()).add(LEVEL_OF_METHOD[name])
            elif isinstance(f, ast.Name) and name in ("one", "stated") and len(call.args) == 5:
                code = _literal(call.args[4])
                if name == "one":
                    out.setdefault(code, set()).add("error")
                else:
                    out.setdefault(None if code is None else f"{code}.missing", set()).add("missing")
    return out


def key_codes() -> dict[str, set[str]]:
    """``identity.<key field>``: a symbol whose library lacks its key field (``seams.key_of``), one per key field."""
    from tools.layout_compiler import seams
    fields = set(seams.KEYS.values()) | {"Name"}
    return {f"identity.{k.replace(' ', '_').lower()}": {"missing"} for k in fields}


def rule_codes(*paths: Path) -> set[str | None]:
    """Each code the reference derivation and the domain libraries raise through the derivation's reporter."""
    out: set[str | None] = set()
    for path in paths:
        for call in _calls(path):
            f = call.func
            if (isinstance(f, ast.Attribute) and f.attr == "add" and ast.unparse(f.value) == "self.r") \
                    or (isinstance(f, ast.Name) and f.id == "add"):
                if call.args and ast.unparse(call.args[0]) == "self.PROBLEM_CODES[p.kind]":
                    continue                                          # the domain library's kinds: PROBLEM_CODES
                out.add(_literal(call.args[0]) if call.args else None)
    from tools.layout_model import derive
    return out | set(derive._Derivation.PROBLEM_CODES.values())
