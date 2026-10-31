"""Diagnostics: one problem, one code (ADR 0012 §3.3). Two kinds share this shape. A rule check (the reference
derivation, the domain libraries) is about the model's facts: ``where`` is its primary entity's model path and
``entities`` every entity it is about, one for a fact wrong in itself, every party for a relationship. An import
diagnostic (the KiCad importer) is about translating the drawing: its location is ``source``, in the drawing's terms,
and ``where`` is empty unless it has a model path. The importer also puts in ``source`` where in the drawing a rule
check's entities are; that is the importer's work, not the finding's.

Levels, most severe first: error, warning, info, missing (ADR 0011 §6: missing is incomplete, never in error).
"""
from __future__ import annotations

from dataclasses import dataclass

ERROR, WARNING, INFO, MISSING = "error", "warning", "info", "missing"
LEVELS = (ERROR, WARNING, INFO, MISSING)


@dataclass(frozen=True)
class Diag:
    severity: str
    code: str
    text: str
    where: str = ""                   # the model path of the primary entity, empty when there is none
    source: str = ""                  # the writer's own location (the KiCad importer's: sheet, reference, symbol, Name)
    entities: tuple[str, ...] = ()    # a rule check's every entity by model path, ``where`` first

    def __str__(self) -> str:
        return (f"{self.severity}: {self.code}: {self.text}" + (f"  [{self.where}]" if self.where else "")
                + (f"  at {self.source}" if self.source else ""))


class Report:
    def __init__(self) -> None:
        self.diags: list[Diag] = []

    def add(self, severity: str, code: str, text: str, where: str = "", entities: tuple[str, ...] = (), source: str = "") -> None:
        self.diags.append(Diag(severity, code, text, where, source, tuple(entities)))

    def error(self, code, text, where="", source=""):
        self.add(ERROR, code, text, where, source=source)

    def warning(self, code, text, where="", source=""):
        self.add(WARNING, code, text, where, source=source)

    def info(self, code, text, where="", source=""):
        self.add(INFO, code, text, where, source=source)

    def missing(self, code, text, where="", source=""):
        self.add(MISSING, code, text, where, source=source)

    @property
    def errors(self) -> list[Diag]:
        return [d for d in self.diags if d.severity == ERROR]

    def by_code(self, code: str) -> list[Diag]:
        return [d for d in self.diags if d.code == code]

    def counts(self) -> dict[str, int]:
        return {k: sum(1 for d in self.diags if d.severity == k) for k in LEVELS}
