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
    rotation: float = 0.0          # the direction the pin's line is drawn from (x, y), degrees, KiCad's library frame (y up)
    length: float = 0.0
    hidden: bool = False


@dataclass(frozen=True)
class SymbolGraphic:
    """One drawn element of a symbol unit, as the library states it (library frame, y up, KiCad's origin).

    ``kind`` is polyline, circle, arc, rectangle or text. ``points`` holds the polyline's vertices, the circle's
    centre, the arc's start, mid and end, the rectangle's two corners, or the text's anchor. Style values are
    KiCad's own: a stroke width of 0 means the context's default; a fill colour is (r, g, b, a) as written.
    """

    kind: str
    points: tuple[tuple[float, float], ...] = ()
    radius: float = 0.0
    text: str = ""
    size: float = 0.0
    rotation: float = 0.0
    justify: str = ""
    stroke_width: float = 0.0
    stroke_type: str = ""
    fill_type: str = ""
    fill_color: Optional[tuple[float, float, float, float]] = None


@dataclass(frozen=True)
class LibrarySymbol:
    """A top-level symbol definition from a .kicad_sym library."""

    name: str
    reference_prefix: str
    pins: tuple[SymbolPin, ...]
    properties: dict[str, str] = field(default_factory=dict)
    graphics: tuple[SymbolGraphic, ...] = ()


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
    sheetpath: str = ""
    tstamps: tuple[str, ...] = ()       # the symbol's UUID, one per unit; stable across annotation and moves

    @property
    def uuid(self) -> str:
        """The instance's own UUID: its first unit's, or empty when the export carries none."""
        return self.tstamps[0] if self.tstamps else ""

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
    sheets: list[str] = field(default_factory=list)
    sheet_files: dict[str, str] = field(default_factory=dict)   # sheet path ("/South-cTc/Sargent/") -> its .kicad_sch file name


@dataclass(frozen=True)
class SchematicPlacement:
    """One placed schematic symbol's source-space transform."""

    reference: str
    lib_id: str
    x: float
    y: float
    rotation: float
    mirror: str = ""
    properties: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class SchematicTitleBlock:
    """Title-block metadata extracted from one KiCad schematic."""

    title: str = ""
    revision: str = ""
    date: str = ""
    company: str = ""
    comments: dict[int, str] = field(default_factory=dict)


@dataclass
class SchematicPlacementModel:
    """Source-derived placed-symbol transforms for one schematic."""

    path: Path
    placements: dict[str, SchematicPlacement] = field(default_factory=dict)
    title_block: SchematicTitleBlock = field(default_factory=SchematicTitleBlock)
    wires: list[tuple[tuple[float, float], ...]] = field(default_factory=list)   # each wire's vertices as drawn
    junctions: set[tuple[float, float]] = field(default_factory=set)
