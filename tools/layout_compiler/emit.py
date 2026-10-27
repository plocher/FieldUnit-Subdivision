"""The seam and trackplan facts as the Layout Data Model File, schema ``layout-model/v3.1.0`` (ADR 0008 rev 4, ADR 0010,
ADR 0011).

Every entity and row holds three maps (ADR 0011 §2): ``given``, what the person stated as fields, as drawn;
``relations``, what the person stated as wires, each the name it reaches; ``derived``, what the rules compute and
nothing stated. Collections and identities stay outside the maps. Absent is absent (§4.7): an empty map is not
written. The dictionary is written canonically by ``layout_model`` (§4.8).
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Optional

from .geometry import Geometry
from .seams import REFERENCE_DATA, Seams

SCHEMA = "layout-model/v3.1.0"                    # reshaped in place to the three maps (ADR 0011 §9; no release yet)
WRITER = {"name": "layout_compiler", "version": "0.4.0"}
RULES = "0.1.0"                                   # the derivation's version; pre-release until rules 1.0.0 ship (ADR 0012 §7)


def _clean(d: dict) -> dict:
    return {k: v for k, v in d.items() if v not in (None, "", [], {})}


def _entity(given: Optional[dict] = None, relations: Optional[dict] = None, derived: Optional[dict] = None, **rest) -> dict:
    """An entity or a row: its three maps, each without empty values, then whatever else it holds (collections)."""
    return _clean({"given": _clean(dict(given or {})), "relations": _clean(dict(relations or {})),
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
    return _entity(d.given,
                   {"column": d.column, "interlocking": d.interlocking, "mast": d.mast, "bindings": _bindings(d)},
                   {"serves": d.serves, "shows": d.shows})


def emit(sm: Seams, source_path: Optional[Path] = None, geometry: Optional[Geometry] = None) -> dict[str, Any]:
    """The Layout Data Model File. ``source_path`` is kept for callers; the project is the source. The KiCad importer
    always passes ``geometry`` (ADR 0011 §7); a source built in memory has no sheets and passes none."""
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
                         columns={c.number: _entity(c.given, {"interlocking": c.folder},
                                                    {"house": f"{c.house[0]}:{c.house[1]}" if c.house else None,
                                                     "interlocking": c.house[0] if c.house else None})
                                  for c in ou.columns.values()},
                         devices=[_device(d) for d in ou.devices])
        for ou in sm.office_units.values()}

    provenance: dict[str, Any] = {"sourceType": "KiCad", "writer": dict(WRITER), "rules": RULES,
                                  "referenceData": dict(REFERENCE_DATA), "source": _source(sm.source.project)}
    if geometry is not None:
        provenance["libraries"] = dict(geometry.libraries)
    return _clean({"schema": SCHEMA, "layout": _clean(layout), "interlockings": interlockings, "officeUnits": office_units,
                   "provenance": _clean(provenance)})
