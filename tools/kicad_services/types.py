"""Domain types for generic KiCad library and netlist reads."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class SymbolPin:
    """One pin on a library symbol unit."""

    number: str
    name: str
    electrical_type: str
    x: float = 0.0
    y: float = 0.0


@dataclass(frozen=True)
class LibrarySymbol:
    """A top-level symbol definition from a .kicad_sym library."""

    name: str
    reference_prefix: str
    pins: tuple[SymbolPin, ...]
    properties: dict[str, str] = field(default_factory=dict)


@dataclass
class LibraryModel:
    """Parsed symbol library."""

    path: Path
    symbols: dict[str, LibrarySymbol] = field(default_factory=dict)

    def get(self, name: str) -> Optional[LibrarySymbol]:
        """Return a symbol by library name, or None."""
        return self.symbols.get(name)


@dataclass(frozen=True)
class NetlistComponent:
    """One component instance from a KiCad netlist export."""

    reference: str
    value: str
    lib: str
    part: str
    fields: dict[str, str] = field(default_factory=dict)

    @property
    def lib_id(self) -> str:
        """Return lib:part identifier."""
        return f"{self.lib}:{self.part}"


@dataclass(frozen=True)
class NetNode:
    """One pin attachment on a net."""

    reference: str
    pin: str
    pinfunction: str = ""
    pintype: str = ""


@dataclass(frozen=True)
class Net:
    """One net with zero or more connected nodes."""

    code: str
    name: str
    nodes: tuple[NetNode, ...]


@dataclass
class NetlistModel:
    """Parsed KiCad netlist (kicadsexpr export)."""

    path: Path
    source: str = ""
    components: dict[str, NetlistComponent] = field(default_factory=dict)
    nets: list[Net] = field(default_factory=list)


@dataclass(frozen=True)
class SchematicPlacement:
    """One placed schematic symbol's source-space transform."""

    reference: str
    lib_id: str
    x: float
    y: float
    rotation: float
    mirror: str = ""


@dataclass
class SchematicPlacementModel:
    """Source-derived placed-symbol transforms for one schematic."""

    path: Path
    placements: dict[str, SchematicPlacement] = field(default_factory=dict)
