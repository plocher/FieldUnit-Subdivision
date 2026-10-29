"""Diagnostics: one problem, one code (ADR 0012 §3.3). Shared by every writer of the Layout Data Model File: the
reference derivation reports about the model's facts, the KiCad importer about the drawing as drawn.

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
    where: str = ""
    source: str = ""                  # a writer's own location of the thing, beside the model path (the KiCad importer's)
    about: str = ""                   # the model path a writer locates, when it is not ``where`` (a summary's first thing)

    def __str__(self) -> str:
        return (f"{self.severity}: {self.code}: {self.text}" + (f"  [{self.where}]" if self.where else "")
                + (f"  at {self.source}" if self.source else ""))


class Report:
    def __init__(self) -> None:
        self.diags: list[Diag] = []

    def add(self, severity: str, code: str, text: str, where: str = "", about: str = "") -> None:
        self.diags.append(Diag(severity, code, text, where, about=about))

    def error(self, code, text, where=""):
        self.add(ERROR, code, text, where)

    def warning(self, code, text, where=""):
        self.add(WARNING, code, text, where)

    def info(self, code, text, where=""):
        self.add(INFO, code, text, where)

    def missing(self, code, text, where=""):
        self.add(MISSING, code, text, where)

    @property
    def errors(self) -> list[Diag]:
        return [d for d in self.diags if d.severity == ERROR]

    def by_code(self, code: str) -> list[Diag]:
        return [d for d in self.diags if d.code == code]

    def counts(self) -> dict[str, int]:
        return {k: sum(1 for d in self.diags if d.severity == k) for k in LEVELS}
