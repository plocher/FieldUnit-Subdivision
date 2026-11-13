"""The KiCad importer's one input: placed symbols with their fields, and nets as sets of named pins.

Nothing else of KiCad crosses this seam. A symbol's ``sheet`` is its hierarchical path (``/South-cTc/Sargent/``) and
is the importer's only notion of scope (ADR 0009 §3.9): a sheet is in scope of every sheet under it. Pin names are
the relation names of ADR 0009 §3.1; the kicad-cli export carries them as ``pinfunction`` ``<name>_<number>``. A
symbol's ``uuid`` is its per-instance KiCad UUID, the stable opaque identity of a track row (three-maps D10).

A pin carries the name of the symbol unit it is drawn in (``PinRef.unit``; KiCad's ``unit_name``, read from the
library the export names, since the netlist carries only the pin number), empty for a unit with no name. A symbol
whose units repeat a pin name (a train order device: STOP in each face's unit) is read by unit (``pins_of_units``),
and ``pins_of`` leaves those pins out; a repeated name with pins in a named unit that are not each in a named unit of
their own cannot be read and is refused (``ValueError``). A repeated name in unnamed units (a column's membership pins)
is read as before, the last wire winning; every other symbol has one pin of each name.
"""
from __future__ import annotations

import uuid as _uuid
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Iterable, Optional, Sequence


@dataclass(frozen=True)
class Symbol:
    ref: str
    lib_id: str
    value: str
    fields: dict[str, str]
    sheet: str
    uuid: str = ""                                                    # the instance's own KiCad UUID

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
    unit: str = ""                                                    # the name of the unit the pin is drawn in; "" when it has none


@dataclass(frozen=True)
class Net:
    name: str
    pins: tuple[PinRef, ...]

    def others(self, ref: str) -> tuple[PinRef, ...]:
        return tuple(p for p in self.pins if p.ref != ref)


@dataclass
class Source:
    """The drawing as the KiCad importer sees it."""

    path: Path
    symbols: dict[str, Symbol]
    nets: list[Net]
    sheets: list[str] = field(default_factory=list)
    project: Optional[Path] = None                                    # the KiCad project the drawing is: the one source
    sheet_files: dict[str, str] = field(default_factory=dict)         # sheet path -> .kicad_sch file name, from the export
    _by_pin: dict[tuple[str, str], Net] = field(default_factory=dict, repr=False)
    _by_unit: dict[tuple[str, str, str], Net] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        units: dict[tuple[str, str], list[str]] = {}                  # (ref, pin name) -> the units of the pins so named
        for net in self.nets:
            for p in net.pins:
                units.setdefault((p.ref, p.pin), []).append(p.unit)
        for (ref, pin), found in units.items():
            named = [u for u in found if u]
            if named and len(found) > 1 and ("" in found or len(set(named)) < len(named)):
                where = ", ".join(f"unit {u!r}" if u else "a unit with no name" for u in found)
                s = self.symbols.get(ref)
                what = f"{s.sheet}{s.lib_id}({s.fields.get('Name', '')})" if s else "a symbol"
                raise ValueError(f"{what}: {len(found)} pins named {pin!r} ({where}); pins of one name in named units are read "
                                 "by unit, so each must be in a named unit of its own")
        for net in self.nets:
            for p in net.pins:
                if not p.unit or len(units[(p.ref, p.pin)]) == 1:         # read by name; repeats in unnamed units keep the last, as before
                    self._by_pin[(p.ref, p.pin)] = net
                if p.unit:
                    self._by_unit[(p.ref, p.unit, p.pin)] = net

    def net_of(self, ref: str, pin: str) -> Optional[Net]:
        """The net a symbol's pin lands on; None when the pin is open or absent."""
        net = self._by_pin.get((ref, pin))
        return net if net and len(net.pins) > 1 else None

    def pins_of(self, ref: str) -> dict[str, Net]:
        return {pin: net for (r, pin), net in self._by_pin.items() if r == ref and len(net.pins) > 1}

    def pins_of_units(self, ref: str) -> dict[str, dict[str, Net]]:
        """A symbol's wired pins by the name of the unit each is drawn in: {unit name: {pin: net}}. A pin in a unit
        with no name is under ``""``. Two pins of one name in named units are in units of their own (``__post_init__``),
        so ``pins_of`` has every pin but those, and this has every pin."""
        out: dict[str, dict[str, Net]] = {}
        for (r, unit, pin), net in self._by_unit.items():
            if r == ref and len(net.pins) > 1:
                out.setdefault(unit, {})[pin] = net
        for (r, pin), net in self._by_pin.items():
            if r == ref and len(net.pins) > 1 and (r, "", pin) not in self._by_unit and not any(pin in pins for pins in out.values()):
                out.setdefault("", {})[pin] = net
        return out

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


def _services():
    import sys
    tools = str(Path(__file__).resolve().parents[1])
    if tools not in sys.path:                     # kicad_services imports itself as a top-level package
        sys.path.insert(0, tools)
    from kicad_services import netlist_reader
    return netlist_reader


def from_netlist(path: Path, libraries: Optional[dict[str, Path]] = None) -> Source:
    """Read a kicad-cli ``kicadsexpr`` netlist export through the generic KiCad services.

    A saved netlist is a cache of the project's state (the netlist rule, ``AGENTS.md``): a caller that passes one
    answers for its freshness. ``from_project`` is the form that cannot be stale. ``libraries`` maps library names
    to files (KiCad's tables for the export's project unless a test points elsewhere); they name each pin's unit."""
    model = _services().NetlistReader().read(Path(path))
    symbols = {ref: Symbol(ref, c.lib_id, c.value, dict(c.fields), c.sheetpath or "/", c.uuid) for ref, c in model.components.items()}
    root = Path(model.source) if model.source else None               # the export names the root schematic
    project = root.with_suffix(".kicad_pro") if root and root.with_suffix(".kicad_pro").is_file() else root
    units = _UnitNames(project.parent if project else None, libraries, {ref: c.lib_id for ref, c in model.components.items()})
    nets = [Net(n.name, tuple(PinRef(p.reference, pin_name(p.pinfunction, p.pin), p.pintype, units.of(p.reference, p.pin)) for p in n.nodes))
            for n in model.nets]
    return Source(Path(path), symbols, nets, list(model.sheets), project, dict(model.sheet_files))


class _UnitNames:
    """The unit name of each pin, from the library symbol the export names for its component; each library is read
    once, and one that cannot be found or read names no unit (every pin is then in an unnamed unit)."""

    def __init__(self, project_dir: Optional[Path], libraries: Optional[dict[str, Path]], lib_ids: dict[str, str]):
        self.lib_ids = lib_ids
        self._libraries = libraries
        self._project_dir = project_dir
        self._models: dict[str, object] = {}

    def _paths(self) -> dict[str, Path]:
        if self._libraries is None:
            try:
                _services()
                from kicad_services.library_table import library_paths
                self._libraries = library_paths(self._project_dir)
            except Exception:                                         # no KiCad tables here: no unit names
                self._libraries = {}
        return self._libraries

    def _symbol(self, lib_id: str):
        lib, _, name = lib_id.partition(":")
        if lib not in self._models:
            path = self._paths().get(lib)
            model = None
            if path and path.is_file():
                try:
                    _services()
                    from kicad_services.symbol_library_reader import SymbolLibraryReader
                    model = SymbolLibraryReader().read(path)
                except Exception:                                     # an unreadable library names no unit
                    model = None
            self._models[lib] = model
        model = self._models[lib]
        return model.get(name) if model else None

    def of(self, ref: str, pin_number: str) -> str:
        sym = self._symbol(self.lib_ids.get(ref, "")) if ref in self.lib_ids else None
        return sym.unit_name_of(pin_number) if sym else ""


def from_snapshot(netlist: Path, repo: Path, paths: Sequence[str]) -> Source:
    """A saved netlist, read only when it is still a snapshot of ``paths`` in the git repository ``repo``
    (``kicad_services.snapshot``); a stale one raises ``StaleNetlist`` naming what is stale."""
    _services()
    from kicad_services import snapshot
    return from_netlist(snapshot.require_fresh(Path(netlist), Path(repo), paths))


def from_project(schematic: Path) -> Source:
    """The drawing read through a netlist exported now and deleted at once (the netlist rule; needs kicad-cli)."""
    with _services().exported_netlist(Path(schematic)) as net:
        return from_netlist(net)


def kicad_cli_available() -> bool:
    return _services().KicadCliNetlistExporter().available()


def from_path(path: Path) -> Source:
    """``from_project`` for a ``.kicad_sch``, ``from_netlist`` for anything else."""
    path = Path(path)
    return from_project(path) if path.suffix == ".kicad_sch" else from_netlist(path)


def from_symbols(symbols: Iterable[Symbol], nets: Iterable[Net], path: Path = Path("<memory>")) -> Source:
    """A source built in memory, for tests of the rules. A symbol without a UUID is given one derived from its
    reference, so a scenario's rows have a stable identity as a drawing's do."""
    syms = [s if s.uuid else replace(s, uuid=str(_uuid.uuid5(_uuid.NAMESPACE_URL, f"memory:{s.ref}"))) for s in symbols]
    return Source(path, {s.ref: s for s in syms}, list(nets), sorted({s.sheet for s in syms}))
