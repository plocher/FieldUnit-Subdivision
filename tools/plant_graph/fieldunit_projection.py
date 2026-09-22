"""Project a portable Interlocking Plant definition into FieldUnit JSON."""

from __future__ import annotations

import json
from typing import Any

_FIELDUNIT_INDICATION_ALIASES = {
    "ADVANCED_APPROACH": "ADVANCE_APPROACH",
}
_FIELDUNIT_INDICATIONS = frozenset(
    {
        "STOP",
        "CLEAR",
        "APPROACH",
        "ADVANCE_APPROACH",
        "MEDIUM_CLEAR",
        "DIVERGING_CLEAR",
        "MEDIUM_APPROACH",
        "DIVERGING_APPROACH",
        "APPROACH_MEDIUM",
        "APPROACH_SLOW",
        "APPROACH_DIVERGING",
        "SLOW_CLEAR",
        "SLOW_APPROACH",
        "RESTRICTING",
        "DIVERGING_RESTRICTING",
        "APPROACH_RESTRICTING",
        "CAB_SPEED",
    }
)


def project_fieldunit_plant(model: dict[str, Any]) -> dict[str, Any]:
    """Return one FieldUnit PlantSerializer-compatible interlocking payload.

    The projection keeps the complete geographic interlocking in one FieldUnit
    plant. Switches and derails use native FieldUnit arrays with optional OS
    bindings. Dependent ``*D`` derails are declared after their base switch and
    are omitted from route ``aligns`` (master alignment + combined KR only).
    Controlled Point allocation remains deferred until FieldUnit has native
    deployment bindings.
    """

    appliances = model["appliances"]
    dependent_derail_ids = {
        item["id"]
        for item in appliances["derails"]
        if item["controlMode"] == "dependent"
    }
    return {
        "name": model["identity"]["name"],
        "trackCircuits": [
            {"name": item["id"]}
            for item in appliances["trackCircuits"]
        ],
        "switches": [
            _appliance_with_optional_os(item["id"], item.get("osTrackCircuit"))
            for item in appliances["switches"]
        ],
        "derails": [
            _appliance_with_optional_os(item["id"], item.get("trackCircuit"))
            for item in appliances["derails"]
        ],
        "crossovers": [
            {
                "name": item["id"],
                "switchA": item["members"][0],
                "switchB": item["members"][1],
            }
            for item in appliances["controlGroups"]
            if item["kind"] == "crossover"
        ],
        "signalControls": [
            {"name": item["id"]}
            for item in appliances["signals"]
        ],
        "signalMasts": [
            {
                "name": item["id"],
                "type": _mast_type(item),
            }
            for item in appliances["masts"]
        ],
        "routes": [
            _project_route(route, dependent_derail_ids=dependent_derail_ids)
            for route in model["routes"]
        ],
        "projectionDeferred": {
            "document": model["document"],
            "profile": model["profile"],
            "controlledPoints": appliances["controlledPoints"],
            "derails": appliances["derails"],
            "topology": model["topology"],
            "terminals": model["terminals"],
            "routeTopology": [
                {
                    "route": route["id"],
                    "entryTerminal": route["entryTerminal"],
                    "exitTerminal": route["exitTerminal"],
                    "endKind": route["endKind"],
                    "exitFace": route["exitFace"],
                }
                for route in model["routes"]
            ],
        },
    }


def project_fieldunit_json(model: dict[str, Any]) -> str:
    """Return stable pretty JSON for FieldUnit PlantSerializer input."""

    return json.dumps(
        project_fieldunit_plant(model),
        indent=2,
        ensure_ascii=False,
    ) + "\n"


def _appliance_with_optional_os(
    name: str,
    os_track_circuit: str | None,
) -> dict[str, str]:
    """Return one switch/derail object with optional FieldUnit ``os`` binding."""

    item: dict[str, str] = {"name": name}
    if os_track_circuit:
        item["os"] = os_track_circuit
    return item


def _project_route(
    route: dict[str, Any],
    *,
    dependent_derail_ids: set[str],
) -> dict[str, Any]:
    """Project one portable route to the revised FieldUnit route vocabulary."""

    result: dict[str, Any] = {
        "name": route["name"],
        "governedBy": {
            "signal": route["signal"],
            "direction": route["direction"],
        },
        "displays": {
            "mast": route["mast"],
            "maxIndication": _fieldunit_indication(route["staticIndication"]),
        },
        "aligns": [
            {
                "switch": item["appliance"],
                "position": item["position"],
            }
            for item in route["alignments"]
            if item["appliance"] not in dependent_derail_ids
        ],
        "clears": route["clearTrackCircuits"],
    }
    if route["entrance"] is not None:
        result["entrance"] = route["entrance"]
    if route["approaching"] is not None:
        result["approaching"] = route["approaching"]
    return result


def _fieldunit_indication(indication: str) -> str:
    """Return a FieldUnit spelling or reject an unsafe indication downgrade."""

    fieldunit_indication = _FIELDUNIT_INDICATION_ALIASES.get(
        indication,
        indication,
    )
    if fieldunit_indication not in _FIELDUNIT_INDICATIONS:
        raise ValueError(
            "FieldUnit projection does not support portable indication "
            f"{indication!r}"
        )
    return fieldunit_indication


def _mast_type(mast: dict[str, Any]) -> str:
    """Return the FieldUnit mast type corresponding to portable mast facts."""

    if mast["kind"] == "dwarf":
        return "DWARF"
    heads = mast["heads"]

    if len(heads) == 1:
        return "ONE_HEAD"
    if len(heads) == 2:
        return "TWO_HEAD"
    if len(heads) == 3:
        return "THREE_HEAD"
    raise ValueError(f"Unsupported mast head count: {len(heads)}")
