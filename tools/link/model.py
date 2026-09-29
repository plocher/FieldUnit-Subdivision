"""Serialize the linked subdivision model to the JSON generators read.

The JSON shape is deliberately informal for now (documented here, frozen as
a versioned schema once a second field-unit implementation exists and the
untested seams are named). Generators read only this document, never
KiCad files.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from link.types import SubdivisionModel


def subdivision_to_json(model: SubdivisionModel) -> dict[str, Any]:
    """Return the linked model as plain JSON data."""
    stations = []
    for station in model.stations:
        entry = asdict(station)
        entry["stationKey"] = station.codeline.station_key
        stations.append(entry)
    return {
        "kind": "subdivision-link",
        "stations": stations,
        "codelineInstances": [asdict(i) for i in model.instances],
        "controllers": [asdict(c) for c in model.controllers],
        "diagnostics": [asdict(d) for d in model.diagnostics],
        "sources": list(model.sources),
    }
