"""The seam and trackplan facts as the Layout Data Model File, schema ``layout-model/v3.1.0`` (ADR 0008 rev 4, ADR 0010,
ADR 0011).

The KiCad importer writes two of the three maps (ADR 0011 §2): ``given``, what the person stated as fields, as drawn,
and ``relations``, what the person stated as wires, each the name it reaches (``facts``). ``derived``, what the rules
compute, is the reference derivation's (``tools/layout_model/derive.py``), which ``emit`` calls, adding its
diagnostics to the importer's log. Collections and identities stay outside the maps. Absent is absent (§4.7): an
empty map is not written. The dictionary is written canonically by ``layout_model`` (§4.8).
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Optional

from tools.layout_model import derive as derivation
from tools.layout_model.reference import REFERENCE_DATA

from .geometry import Geometry
from .seams import PIN_TOKENS, Seams
from .seams import loc as seams_loc

SCHEMA = "layout-model/v3.1.0"                    # reshaped in place to the three maps (ADR 0011 §9; no release yet)
WRITER = {"name": "layout_compiler", "version": "0.4.0"}


def _clean(d: dict) -> dict:
    return {k: v for k, v in d.items() if v not in (None, "", [], {})}


def _entity(given: Optional[dict] = None, relations: Optional[dict] = None, derived: Optional[dict] = None, **rest) -> dict:
    """An entity or a row: its three maps, each without empty values, then whatever else it holds (collections). An
    empty per-pin ``Control.<pin>`` or ``Indication.<pin>`` in ``given`` is kept: it states the pin binds no token."""
    stated = {k: v for k, v in (given or {}).items() if v not in (None, "", [], {}) or k.startswith(PIN_TOKENS)}
    return _clean({"given": stated, "relations": _clean(dict(relations or {})),
                   "derived": _clean(dict(derived or {})), **rest})


def _git(args: list[str], cwd: Path) -> Optional[str]:
    try:
        out = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=10)
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def _source(project: Optional[Path]) -> dict[str, Any]:
    """The one source is the KiCad project, a layout property (ADR 0008 §4.6; the owner, 2026-10-19): its path relative
    to its repository and that repository's describe. The netlist is an export, never named."""
    if project is None:
        return {}
    top = _git(["rev-parse", "--show-toplevel"], project.parent)
    path = str(project.resolve().relative_to(Path(top).resolve())) if top and project.resolve().is_relative_to(Path(top).resolve()) else project.name
    return _clean({"path": path, "describe": _git(["describe", "--always", "--dirty"], project.parent)})


def _bindings(d) -> dict[str, Any]:
    """A device's wires to driver pins, function to route (three-maps D3); a function bound twice keeps both routes."""
    out: dict[str, list[str]] = {}
    for b in d.bindings:
        out.setdefault(b.function, []).append(b.route)
    return {f: routes[0] if len(routes) == 1 else sorted(routes) for f, routes in out.items()}


def _device(d) -> dict:
    return _entity(d.given, {"column": d.column, "interlocking": d.interlocking, "mast": d.mast, "bindings": _bindings(d)})


def emit(sm: Seams, source_path: Optional[Path] = None, geometry: Optional[Geometry] = None) -> dict[str, Any]:
    """The Layout Data Model File: the drawing's facts (``facts``) with every ``derived`` map filled by the reference
    derivation. Its diagnostics join the importer's in ``sm.report``, once however often this is called. ``source_path``
    is kept for callers; the project is the source. The KiCad importer always passes ``geometry`` (ADR 0011 §7); a
    source built in memory has no sheets and passes none."""
    model, report = derivation.derive(facts(sm, geometry))
    if not sm.derived:
        sm.report.diags.extend(report.diags)
        _check_folders(sm, model)
        sm.derived = True
    return model


def _check_folders(sm: Seams, model: dict[str, Any]) -> None:
    """A column whose CP Name names a house of one interlocking, drawn under another's sheet: the drawing disagrees with
    itself, which only the importer sees (the sheet is no fact of the file)."""
    for ou in sm.office_units.values():
        for c in ou.columns.values():
            ixn = model.get("officeUnits", {}).get(ou.name, {}).get("columns", {}).get(c.number, {}).get("derived", {}).get("interlocking")
            if ixn and c.sheet_folder and c.sheet_folder != ixn:
                sm.report.error("column.folder", f"column {c.number}: house {c.given.get('CP Name')} is in {ixn}, the column is drawn "
                                f"under {c.sheet_folder}", seams_loc(c.sym))


def facts(sm: Seams, geometry: Optional[Geometry] = None) -> dict[str, Any]:
    """What the drawing states: every ``given`` and ``relations``, the collections, geometry and provenance; no
    ``derived``."""
    layout: dict[str, Any] = {"name": sm.railroad, "given": sm.railroad_given}
    layout["transports"] = {
        t.name: _entity(t.given, {"anchors": sorted(t.anchors)},
                        nodes={n.ua: _entity(n.given, bits={a: _entity(d.given) for a, d in n.bits.items()}) for n in t.nodes.values()})
        for t in sm.transports.values()}
    for key, role in (("codelines", "CODELINE_ENCODING"), ("ioEncodings", "IO_ENCODING")):
        layout[key] = {e.name: _entity(e.given, {"transport": e.transport, "processor": e.processor})
                       for e in sm.encodings.values() if e.role == role}
    layout["processors"] = {p.name: _entity(p.given, drivers={a: _entity(d.given) for a, d in p.drivers.items()})
                            for p in sm.processors.values()}
    if geometry is not None:
        layout["glyphs"] = dict(geometry.glyphs)

    plans = sm.trackplan.plans if sm.trackplan else {}
    interlockings = {
        ix.name: _entity(ix.given, {"codeline": ix.codeline, "processor": ix.processor},
                         houses={h.cp_name: _entity(h.given, {"maintainerCall": h.maintainer_call, "codeline": h.codeline})
                                 for h in ix.houses.values()},
                         appliances=plans[ix.name].appliances if ix.name in plans else None,
                         track=plans[ix.name].track if ix.name in plans else None,
                         devices=[_device(d) for d in ix.devices],
                         geometry=geometry.interlockings.get(ix.name) if geometry else None)
        for ix in sm.interlockings.values()}
    office_units = {
        ou.name: _entity(ou.given, {"processor": ou.processor},
                         columns={c.number: _entity(c.given, {"interlocking": c.folder}) for c in ou.columns.values()},
                         devices=[_device(d) for d in ou.devices])
        for ou in sm.office_units.values()}

    provenance: dict[str, Any] = {"sourceType": "KiCad", "writer": dict(WRITER),
                                  "referenceData": dict(REFERENCE_DATA), "source": _source(sm.source.project)}
    if geometry is not None:
        provenance["libraries"] = dict(geometry.libraries)
    return _clean({"schema": SCHEMA, "layout": _clean(layout), "interlockings": interlockings, "officeUnits": office_units,
                   "provenance": _clean(provenance)})
