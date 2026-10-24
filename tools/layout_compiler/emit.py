"""The seam facts as the Layout Data Model File, schema ``layout-model/v3.0.0`` (ADR 0008 rev 4).

Only what the drawing states lands here, resolved to names (ADR 0008 §4.4, §4.5). Nothing derived is written:
stations, the seam a transport serves, the path from a lever to its appliance are the reader library's to compute.
Absent is absent (§4.7). The dictionary is written canonically by ``layout_model`` (§4.8).
"""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Any, Optional

from .seams import Seams

SCHEMA = "layout-model/v3.0.0"
COMPILER = {"name": "layout_compiler", "version": "0.1.0"}


def _clean(d: dict) -> dict:
    return {k: v for k, v in d.items() if v not in (None, "", [], {})}


def _describe(path: Path) -> Optional[str]:
    try:
        out = subprocess.run(["git", "describe", "--always", "--dirty"], cwd=path.parent, capture_output=True, text=True, timeout=10)
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def emit(sm: Seams, source_path: Optional[Path] = None) -> dict[str, Any]:
    layout: dict[str, Any] = dict(sm.railroad)
    layout["transports"] = {
        t.name: _clean({
            "kind": t.kind,
            "params": dict(t.params),
            "anchors": sorted(t.anchors),
            "nodes": {n.ua: _clean({"nodeType": n.node_type, "inputBytes": n.input_bytes, "outputBytes": n.output_bytes,
                                    "bits": {a: _clean({"settings": d.settings}) for a, d in n.bits.items()}})
                      for n in t.nodes.values()},
        }) for t in sm.transports.values()}
    layout["codelines"] = {
        e.name: _clean({"encoding": e.kind, "transport": e.transport, "processor": e.processor, "settings": e.settings})
        for e in sm.encodings.values() if e.role == "CODELINE_ENCODING"}
    layout["ioEncodings"] = {
        e.name: _clean({"encoding": e.kind, "transport": e.transport, "processor": e.processor, "settings": e.settings})
        for e in sm.encodings.values() if e.role == "IO_ENCODING"}
    layout["processors"] = {
        p.name: _clean({"board": p.board,
                        "drivers": {a: _clean({"ic": d.ic, "settings": d.settings}) for a, d in p.drivers.items()}})
        for p in sm.processors.values()}

    def device(d) -> dict:
        return _clean({
            "type": _clean({"appliance": d.appliance, "style": d.styles[0] if len(d.styles) == 1 else d.styles}),
            "serves": d.serves, "head": d.head, "shows": d.shows, "column": d.column, "address": d.address,
            "settings": d.settings, "bindings": [{"function": b.function, "route": b.route} for b in d.bindings]})

    interlockings = {
        ix.name: _clean({
            "codeline": ix.codeline,
            "fieldUnit": _clean({"processor": ix.processor}),
            "houses": {h.cp_name: _clean({"milepost": h.milepost, "maintainerCall": h.maintainer_call}) for h in ix.houses.values()},
            "devices": [device(d) for d in ix.devices],
        }) for ix in sm.interlockings.values()}
    office_units = {
        ou.name: _clean({
            "style": ou.style,
            "processor": ou.processor,
            "columns": {c.number: _clean({"house": f"{c.house[0]}:{c.house[1]}" if c.house else None,
                                          "interlocking": None if c.house else c.interlocking}) for c in ou.columns.values()},
            "devices": [device(d) for d in ou.devices],
        }) for ou in sm.office_units.values()}

    provenance: dict[str, Any] = {"sourceType": "KiCad", "compiler": dict(COMPILER)}
    src = source_path or sm.source.path
    if src and Path(src).is_file():
        text = Path(src).read_bytes()
        provenance["source"] = _clean({"path": Path(src).name, "sha256": hashlib.sha256(text).hexdigest(), "describe": _describe(Path(src))})
    return _clean({"schema": SCHEMA, "layout": _clean(layout), "interlockings": interlockings, "officeUnits": office_units, "provenance": provenance})
