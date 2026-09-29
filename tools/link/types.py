"""Domain types for the linked subdivision model."""

from __future__ import annotations

from dataclasses import dataclass, field

from controller_graph.types import (
    Codeline,
    Column,
    ControllerFragment,
    Diagnostic,
)


@dataclass
class Station:
    """One interlocking's attachment to a codeline.

    status:
      linked       controller sheet paired with a plant model; cross-checked.
      placeholder  controller sheet (often a stub) with no plant model; a
                   benign declared placeholder, an error only when a
                   generator dereferences it.
    """

    interlocking: str
    status: str
    codeline: Codeline
    columns: list[Column] = field(default_factory=list)
    plant_id: str = ""
    controller: str = ""  # machine name; several controllers may attach (M:N)


@dataclass
class CodelineInstance:
    """One derived codeline: same transport plus same Broker (MQTT) or
    Port (C/MRI). Station keys must be unique within an instance."""

    transport: str
    discriminator: str  # Broker, Port, or "" (VIRTUAL)
    stations: list[str] = field(default_factory=list)  # interlocking names


@dataclass
class SubdivisionModel:
    """Link output: the logical model generators read."""

    stations: list[Station] = field(default_factory=list)
    instances: list[CodelineInstance] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)
    controllers: list[ControllerFragment] = field(default_factory=list)
    sources: list[dict[str, str]] = field(default_factory=list)
