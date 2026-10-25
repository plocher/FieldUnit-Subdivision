"""The compiler's one input: placed symbols with their fields, and nets as sets of named pins.

Nothing else of KiCad crosses this seam. A symbol's ``sheet`` is its hierarchical path (``/South-cTc/Sargent/``) and
is the compiler's only notion of scope (ADR 0009 §3.9): a sheet is in scope of every sheet under it. Pin names are
the relation names of ADR 0009 §3.1; the kicad-cli export carries them as ``pinfunction`` ``<name>_<number>``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional


@dataclass(frozen=True)
class Symbol:
    ref: str
    lib_id: str
    value: str
    fields: dict[str, str]
    sheet: str

    @property
    def role(self) -> str:
        return self.fields.get("Role", "")

    @property
    def kind(self) -> str:
        return self.fields.get("Kind", "")

    def get(self, name: str) -> str:
        """A field's value, empty when absent: an empty attribute says nothing (ADR 0009 §3.9)."""
        return self.fields.get(name, "").strip()


@dataclass(frozen=True)
class PinRef:
    ref: str
    pin: str
    pintype: str = ""


@dataclass(frozen=True)
class Net:
    name: str
    pins: tuple[PinRef, ...]

    def others(self, ref: str) -> tuple[PinRef, ...]:
        return tuple(p for p in self.pins if p.ref != ref)


@dataclass
class Source:
    """The drawing as the compiler sees it."""

    path: Path
    symbols: dict[str, Symbol]
    nets: list[Net]
    sheets: list[str] = field(default_factory=list)
    project: Optional[Path] = None                                    # the KiCad project the drawing is: the one source
    _by_pin: dict[tuple[str, str], Net] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        for net in self.nets:
            for p in net.pins:
                self._by_pin[(p.ref, p.pin)] = net

    def net_of(self, ref: str, pin: str) -> Optional[Net]:
        """The net a symbol's pin lands on; None when the pin is open or absent."""
        net = self._by_pin.get((ref, pin))
        return net if net and len(net.pins) > 1 else None

    def pins_of(self, ref: str) -> dict[str, Net]:
        return {pin: net for (r, pin), net in self._by_pin.items() if r == ref and len(net.pins) > 1}

    def where(self, role: str, kind: Optional[str] = None) -> list[Symbol]:
        out = [s for s in self.symbols.values() if s.role == role and (kind is None or s.kind == kind)]
        return sorted(out, key=lambda s: (s.sheet, s.ref))

    def on_sheet(self, sheet: str, role: str, kind: Optional[str] = None) -> list[Symbol]:
        return [s for s in self.where(role, kind) if s.sheet == sheet]

    def under(self, sheet: str, role: str, kind: Optional[str] = None) -> list[Symbol]:
        """Symbols on ``sheet`` or any sheet below it (the folder)."""
        return [s for s in self.where(role, kind) if s.sheet.startswith(sheet)]


def in_scope(provider_sheet: str, sheet: str) -> bool:
    """A symbol on ``provider_sheet`` is in scope of ``sheet`` when it is on it or on an ancestor (ADR 0009 §3.9)."""
    return sheet.startswith(provider_sheet)


def pin_name(pinfunction: str, number: str) -> str:
    return pinfunction.rsplit("_", 1)[0] if pinfunction else number


def from_netlist(path: Path) -> Source:
    """Read a kicad-cli ``kicadsexpr`` netlist export through the generic KiCad services."""
    import sys
    tools = str(Path(__file__).resolve().parents[1])
    if tools not in sys.path:                     # kicad_services imports itself as a top-level package
        sys.path.insert(0, tools)
    from kicad_services.netlist_reader import NetlistReader

    model = NetlistReader().read(Path(path))
    symbols = {ref: Symbol(ref, c.lib_id, c.value, dict(c.fields), c.sheetpath or "/") for ref, c in model.components.items()}
    nets = [Net(n.name, tuple(PinRef(p.reference, pin_name(p.pinfunction, p.pin), p.pintype) for p in n.nodes)) for n in model.nets]
    root = Path(model.source) if model.source else None               # the export names the root schematic
    project = root.with_suffix(".kicad_pro") if root and root.with_suffix(".kicad_pro").is_file() else root
    return Source(Path(path), symbols, nets, list(model.sheets), project)


def from_symbols(symbols: Iterable[Symbol], nets: Iterable[Net], path: Path = Path("<memory>")) -> Source:
    """A source built in memory, for tests of the rules."""
    syms = list(symbols)
    return Source(path, {s.ref: s for s in syms}, list(nets), sorted({s.sheet for s in syms}))
