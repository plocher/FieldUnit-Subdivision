"""The KiCad importer, milestone D: KiCad project to the Layout Data Model File (ADR 0008 rev 4, ADR 0009, ADR 0011).

Transient (ADR 0011 §1): it reads the drawing and writes ``given`` and ``relations``, then calls the reference
derivation, ``tools/layout_model/derive.py``, for ``derived`` (control points, circuits, links, NextCP pairing,
references, a column's house, a device's serves, a lamp's indications and expression). When it reports a derived
diagnostic it adds the drawing's location (``emit.sources``).

- ``source``: the one interface the importer reads, symbols with fields and nets with pin names, and its only
  implementation today, the kicad-cli netlist export read through ``kicad_services``.
- ``seams``: the explicit-seams model of ADR 0009 under ADR 0012 §4: every relation by its wire alone, missing when
  none is drawn. Macros ``<ROLE:KIND:Field>`` are expanded here.
- ``trackplan`` and ``geometry``: the trackplan's appliances and rows as drawn, and the drawing's placements, runs and
  glyphs.
- ``emit``: the facts as the schema ``layout-model/v3.1.0`` dictionary, derived, written canonically by ``layout_model``.

The importer writes nothing when it reports an error (ADR 0008 §4.6); its observations about the drawing stay in
its log. Its own import diagnostics, located in the drawing (``Diag.source``), are registered in ``diagnostics.json``
beside this file (ADR 0012 §3.3); the derivation's rule checks are registered with the schema.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

REGISTRY = Path(__file__).with_name("diagnostics.json")


@lru_cache(maxsize=1)
def registry() -> dict[str, dict[str, Any]]:
    """The import-diagnostic registry (ADR 0012 §3.3): every code the KiCad importer raises, with its level."""
    return json.loads(REGISTRY.read_text(encoding="utf-8"))["codes"]
