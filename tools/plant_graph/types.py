"""Railroad plant-graph domain types."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class DiagnosticSeverity(str, Enum):
    """Diagnostic classification for the plant parser."""

    SYNTAX = "syntax"
    SEMANTIC = "semantic"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class Diagnostic:
    """One parser/validator finding."""

    severity: DiagnosticSeverity
    code: str
    message: str
    entity_ref: str = ""


class EntityKind(str, Enum):
    """Functional entity kinds derived from Railroad symbol types."""

    SWITCH_POWERED = "switch_powered"
    SWITCH_LOCK = "switch_lock"
    IRJ = "irj"
    IRJ_SIGNAL = "irj_signal"
    MAST_SINGLE = "mast_single"
    MAST_DOUBLE = "mast_double"
    MAST_DWARF = "mast_dwarf"
    SIGNAL_HEAD = "signal_head"
    DIRECTION = "direction"
    BUMPER = "bumper"
    MAINTAINER = "maintainer"
    MILEPOST = "milepost"
    UNKNOWN = "unknown"


class NetClass(str, Enum):
    """Plant-level classification of a KiCad net."""

    TRACK = "track"
    SWITCH_OS = "switch_os"  # C/N/R legs covered by derived <switch>T1
    SIGNAL_ATTACHMENT = "signal_attachment"
    HEAD_ATTACHMENT = "head_attachment"
    UNCONNECTED = "unconnected"
    OTHER = "other"


@dataclass(frozen=True)
class PlantEntity:
    """One placed railroad symbol instance in the plant graph."""

    reference: str
    kind: EntityKind
    lib_id: str
    value: str
    canonical_name: str
    fields: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class PlantNet:
    """One net after plant classification."""

    name: str
    net_class: NetClass
    raw_name: str
    nodes: tuple[tuple[str, str], ...]  # (reference, pin)
    authoritative_label: bool


@dataclass(frozen=True)
class DerivedTrackCircuit:
    """Compiler-derived track circuit (not a KiCad net)."""

    name: str
    switch_name: str
    reason: str


@dataclass(frozen=True)
class PlantTerminal:
    """Plant entry/exit terminal (DoT or Bumper)."""

    reference: str
    kind: EntityKind
    port_pin: str
    net_name: str
    designation: str
    rulebook: str


@dataclass(frozen=True)
class SignalFace:
    """One mast face of a signal at a Signal IRJ."""

    signal_name: str
    direction: str
    mast_reference: str
    mast_name: str
    irj_reference: str
    approach_pin: str
    plant_pin: str
    approach_net: str
    approach_terminal: str


@dataclass(frozen=True)
class SignalRoute:
    """One combinatoric plant route governed by a signal face."""

    name: str
    signal_name: str
    direction: str
    mast_reference: str
    mast_name: str
    entry_terminal: str
    entry_net: str
    entry_designation: str
    entry_rulebook: str
    exit_terminal: str
    exit_net: str
    exit_designation: str
    exit_rulebook: str
    switch_alignments: tuple[tuple[str, str], ...]  # (switch_name, N|R)
    clear_track_circuits: tuple[str, ...]  # OS + path TCs required clear for the route
    os_track_circuits: tuple[str, ...]  # derived <switch>T1 on path
    path_track_circuits: tuple[str, ...]  # labeled track nets on path (2NA, …)
    path_nets: tuple[str, ...]


@dataclass
class PlantGraph:
    """In-memory plant graph projection for one interlocking schematic."""

    entities: dict[str, PlantEntity] = field(default_factory=dict)
    nets: list[PlantNet] = field(default_factory=list)
    derived_track_circuits: list[DerivedTrackCircuit] = field(default_factory=list)
    terminals: list[PlantTerminal] = field(default_factory=list)
    signal_faces: list[SignalFace] = field(default_factory=list)
    routes: list[SignalRoute] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)

    def errors(self) -> list[Diagnostic]:
        """Return syntax and semantic diagnostics."""
        return [
            d
            for d in self.diagnostics
            if d.severity
            in (DiagnosticSeverity.SYNTAX, DiagnosticSeverity.SEMANTIC)
        ]

    def has_errors(self) -> bool:
        """Return True if any blocking diagnostic exists."""
        return bool(self.errors())
