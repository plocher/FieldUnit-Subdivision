"""The SPCoast test corpus: the drawing at the commit ``schemas/layout-model/examples/spcoast.corpus.json`` pins.

The frozen example ``spcoast.layout.json`` was built from the same commit. The gates that need KiCad input read the
drawing there, never the live one, so an edit to the live drawing changes no gate (the owner, 2026-11-14). The
Railroad repository is checked out at the commit into a temporary directory once per test run (``kicad_services.
pinned``), each gate's netlist is exported there and deleted at once, the sheets and the pinned symbol libraries are read
there, and the checkout is removed when the run ends. The gates are skipped, never faked, without kicad-cli or
without the repository and the commit.
"""
from __future__ import annotations

import atexit
from contextlib import ExitStack
from pathlib import Path

from tools.kicad_services import pinned
from tools.layout_compiler.source import Source, from_project, kicad_cli_available

PIN_FILE = Path(__file__).resolve().parents[1] / "schemas" / "layout-model" / "examples" / "spcoast.corpus.json"
PIN = pinned.Pin.load(PIN_FILE)
AVAILABLE = PIN.available() and kicad_cli_available()
WHY_SKIPPED = f"SPCoast corpus {PIN.repository}@{PIN.commit} not present or kicad-cli missing"

_open = ExitStack()
atexit.register(_open.close)
_checkout: list[tuple[Path, dict[str, Path]]] = []


def spcoast_source() -> Source:
    """The corpus drawing read through a netlist exported now and deleted at once; one checkout per run."""
    if not _checkout:
        _checkout.append(_open.enter_context(pinned.opened(PIN)))
    project, libraries = _checkout[0]
    return from_project(project, libraries)
