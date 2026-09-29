"""Shared CLI reporting for controller/link diagnostics."""

from __future__ import annotations

import sys
from typing import Iterable, TextIO

from controller_graph.types import Diagnostic


def report_diagnostics(
    diagnostics: Iterable[Diagnostic], stream: TextIO = sys.stderr
) -> int:
    """Print diagnostics one per line; return the process exit code
    (nonzero when any error-severity finding exists)."""
    exit_code = 0
    for diagnostic in diagnostics:
        print(
            f"{diagnostic.severity}: {diagnostic.code}: "
            f"{diagnostic.message}",
            file=stream,
        )
        if diagnostic.severity == "error":
            exit_code = 1
    return exit_code
