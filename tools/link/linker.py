"""Link controller fragments with portable plant models."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from controller_graph.types import ControllerFragment, Diagnostic, station_key

from link.types import CodelineInstance, Station, SubdivisionModel


def _derive_instances(model: SubdivisionModel) -> None:
    """Instances: same transport plus same Broker (MQTT) or Port (C/MRI).
    Station keys must be unique within an instance; one C/MRI port has one
    Baud."""
    instances: dict[tuple[str, str], CodelineInstance] = {}
    keys_seen: dict[tuple[str, str], dict[str, str]] = {}
    port_bauds: dict[str, set[str]] = {}
    broker_roots: dict[str, set[str]] = {}
    for station in model.stations:
        codeline = station.codeline
        if codeline.transport == "MQTT":
            discriminator = codeline.params.get("Broker", "")
        elif codeline.transport == "CMRInet":
            discriminator = codeline.params.get("Port", "")
        else:
            discriminator = ""
        instance_id = (codeline.transport, discriminator)
        instance = instances.setdefault(
            instance_id,
            CodelineInstance(
                transport=codeline.transport, discriminator=discriminator
            ),
        )
        instance.stations.append(station.interlocking)

        seen = keys_seen.setdefault(instance_id, {})
        key = codeline.station_key
        if key in seen:
            model.diagnostics.append(
                Diagnostic(
                    severity="error",
                    code="station-key-duplicate",
                    subject=codeline.station,
                    message=(
                        f"stations {seen[key]!r} and {codeline.station!r} "
                        f"normalise to the same key {key!r} on one "
                        f"{codeline.transport} codeline"
                    ),
                )
            )
        else:
            seen[key] = codeline.station

        if codeline.transport == "MQTT":
            broker = codeline.params.get("Broker", "")
            roots = broker_roots.setdefault(broker, set())
            roots.add(codeline.params.get("TopicRoot", ""))
            if len(roots) == 2:  # warn once, on the first mix
                model.diagnostics.append(
                    Diagnostic(
                        severity="warning",
                        code="topicroot-mixed",
                        subject=broker,
                        message=(
                            f"broker {broker!r} carries multiple TopicRoot "
                            "values; allowed, but usually unintended"
                        ),
                    )
                )
        if codeline.transport == "CMRInet":
            port = codeline.params.get("Port", "")
            baud = codeline.params.get("Baud", "")
            bauds = port_bauds.setdefault(port, set())
            bauds.add(baud)
            if len(bauds) > 1:
                model.diagnostics.append(
                    Diagnostic(
                        severity="error",
                        code="codeline-baud-mismatch",
                        subject=port,
                        message=(
                            f"C/MRI port {port!r} is declared with "
                            f"multiple Baud values {sorted(bauds)}"
                        ),
                    )
                )

    model.instances = [
        instances[key] for key in sorted(instances)
    ]
    for instance in model.instances:
        instance.stations.sort()


def _plant_name(plant: dict[str, Any]) -> str:
    return plant.get("identity", {}).get("name", "")


def _cross_check_cps(
    model: SubdivisionModel,
    interlocking: str,
    columns: list,
    plant: dict[str, Any],
) -> None:
    """§7a: a column IS a CP. CP Name must name a plant CP of the same
    interlocking, uniquely; a plant CP with no column is only a warning."""
    plant_cps = {
        station_key(cp.get("id", "")): cp.get("id", "")
        for cp in plant.get("appliances", {}).get("controlledPoints", [])
    }
    seen: dict[str, int] = {}
    for column in columns:
        key = station_key(column.cp_name)
        if key not in plant_cps:
            model.diagnostics.append(
                Diagnostic(
                    severity="error",
                    code="cp-unmatched",
                    subject=str(column.number),
                    message=(
                        f"column {column.number} names {column.cp_name!r}, "
                        f"which is not a controlled point of plant "
                        f"{interlocking}"
                    ),
                )
            )
            continue
        if key in seen:
            model.diagnostics.append(
                Diagnostic(
                    severity="error",
                    code="cp-duplicate",
                    subject=str(column.number),
                    message=(
                        f"columns {seen[key]} and {column.number} both name "
                        f"CP {column.cp_name!r}"
                    ),
                )
            )
            continue
        seen[key] = column.number
    for key, cp_name in sorted(plant_cps.items()):
        if key not in seen:
            model.diagnostics.append(
                Diagnostic(
                    severity="warning",
                    code="cp-uncontrolled",
                    subject=cp_name,
                    message=(
                        f"plant CP {cp_name} of {interlocking} has no "
                        "column; it is not dispatcher-controlled from this "
                        "machine"
                    ),
                )
            )


def _cross_check_appliances(
    model: SubdivisionModel,
    interlocking: str,
    appliances: list,
    plant: dict[str, Any],
) -> None:
    """§7a: panel appliances name plant appliances of this interlocking;
    every dispatcher-controlled plant appliance has a lever (dependent
    derails exempt); lamp tokens resolve to plant circuits."""
    plant_appliances = plant.get("appliances", {})

    def ids(kind: str) -> dict[str, str]:
        return {
            entry.get("id", "").casefold(): entry.get("id", "")
            for entry in plant_appliances.get(kind, [])
        }

    switches = ids("switches")
    signals = ids("signals")
    circuits = ids("trackCircuits")

    lever_targets = {"SWITCH_LEVER": switches, "LOCK_LEVER": {}, "SIGNAL_LEVER": signals}
    levered: set[str] = set()
    lamped: set[str] = set()
    mcall_reported = False
    for appliance in appliances:
        if appliance.kind in lever_targets:
            target = lever_targets[appliance.kind]
            key = appliance.name.casefold()
            if key in target:
                levered.add(key)
            else:
                model.diagnostics.append(
                    Diagnostic(
                        severity="error",
                        code="appliance-unmatched",
                        subject=appliance.name,
                        message=(
                            f"panel {appliance.kind} {appliance.name!r} "
                            f"names no matching plant appliance of "
                            f"{interlocking}"
                        ),
                    )
                )
        elif appliance.kind == "MAINTAINER_CALL" and not mcall_reported:
            mcall_reported = True
            model.diagnostics.append(
                Diagnostic(
                    severity="info",
                    code="mcall-uncheckable",
                    subject=appliance.name,
                    message=(
                        "maintainer calls are not in the portable plant "
                        f"model yet; {appliance.name} of {interlocking} "
                        "cannot be cross-checked (known gap)"
                    ),
                )
            )
        elif appliance.kind == "LAMP":
            for token in appliance.indication_tokens:
                key = token.casefold()
                if key in circuits:
                    lamped.add(key)
                elif key.startswith("mc") and key.endswith("k"):
                    if not mcall_reported:
                        mcall_reported = True
                        model.diagnostics.append(
                            Diagnostic(
                                severity="info",
                                code="mcall-uncheckable",
                                subject=token,
                                message=(
                                    "maintainer calls are not in the "
                                    "portable plant model yet; lamp token "
                                    f"{token} of {interlocking} cannot be "
                                    "cross-checked (known gap)"
                                ),
                            )
                        )
                else:
                    model.diagnostics.append(
                        Diagnostic(
                            severity="error",
                            code="lamp-token-unresolved",
                            subject=appliance.reference,
                            message=(
                                f"lamp token {token!r} resolves to no track "
                                f"circuit or maintainer-call indication of "
                                f"{interlocking}"
                            ),
                        )
                    )

    for key, name in sorted(switches.items() | signals.items()):
        if key not in levered:
            model.diagnostics.append(
                Diagnostic(
                    severity="error",
                    code="plant-unlevered",
                    subject=name,
                    message=(
                        f"plant appliance {name} of {interlocking} is "
                        "dispatcher-controlled but has no panel lever"
                    ),
                )
            )
    for key, name in sorted(circuits.items()):
        if key not in lamped:
            model.diagnostics.append(
                Diagnostic(
                    severity="info",
                    code="circuit-unlamped",
                    subject=name,
                    message=(
                        f"track circuit {name} of {interlocking} is shown "
                        "by no lamp on this machine"
                    ),
                )
            )


def link_subdivision(
    controllers: list[ControllerFragment],
    plants: list[dict[str, Any]],
) -> SubdivisionModel:
    """Link compiled fragments into one subdivision model.

    Pairing is by name, normalized like station keys. Every controller
    interlocking sheet yields a station; a sheet with no plant model is a
    placeholder, and a plant with no sheet is info (it may belong to
    another controller, M:N).
    """
    model = SubdivisionModel(controllers=list(controllers))
    plants_by_key = {station_key(_plant_name(p)): p for p in plants}
    attached_plants: set[str] = set()

    for controller in controllers:
        model.sources.append(
            {
                "kind": "controller-netlist",
                "path": controller.source_path,
                "sha256": controller.source_sha256,
            }
        )
    for plant in plants:
        canonical = json.dumps(plant, sort_keys=True).encode("utf-8")
        model.sources.append(
            {
                "kind": "plant-model",
                "id": plant.get("identity", {}).get("id", ""),
                "sha256": hashlib.sha256(canonical).hexdigest(),
            }
        )

    for controller in controllers:
        for codeline in controller.codelines:
            key = station_key(codeline.interlocking)
            plant = plants_by_key.get(key)
            columns = [
                c
                for c in controller.columns
                if c.interlocking == codeline.interlocking
            ]
            if plant is None:
                model.stations.append(
                    Station(
                        interlocking=codeline.interlocking,
                        status="placeholder",
                        codeline=codeline,
                        columns=columns,
                    )
                )
                continue
            attached_plants.add(key)
            model.stations.append(
                Station(
                    interlocking=codeline.interlocking,
                    status="linked",
                    codeline=codeline,
                    columns=columns,
                    plant_id=plant.get("identity", {}).get("id", ""),
                )
            )
            _cross_check_cps(model, codeline.interlocking, columns, plant)
            station_appliances = [
                a
                for a in controller.appliances
                if a.interlocking == codeline.interlocking
            ]
            _cross_check_appliances(
                model, codeline.interlocking, station_appliances, plant
            )

    for key, plant in plants_by_key.items():
        if key not in attached_plants:
            model.diagnostics.append(
                Diagnostic(
                    severity="info",
                    code="plant-unattached",
                    subject=_plant_name(plant),
                    message=(
                        f"plant {_plant_name(plant)} has no controller "
                        "sheet here; it may be controlled by another "
                        "controller or not yet be on this machine"
                    ),
                )
            )

    model.stations.sort(key=lambda s: s.interlocking)
    _derive_instances(model)
    return model
