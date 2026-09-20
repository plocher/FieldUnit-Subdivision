"""Read placed-symbol transforms from a KiCad schematic source."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from kicad_services import types as ktypes
from kicad_services.netlist_reader import NetlistParseError


class SchematicPlacementReader:
    """Extract source-space symbol placement without topology interpretation."""

    def read(self, schematic_path: Path) -> ktypes.SchematicPlacementModel:
        """Return placed-symbol transforms indexed by reference."""
        if not schematic_path.is_file():
            raise FileNotFoundError(f"Schematic not found: {schematic_path}")
        try:
            from jbom.common.sexp_parser import load_kicad_file
            from sexpdata import Symbol
        except ImportError as exc:
            raise NetlistParseError(
                f"jbom/sexpdata required to parse schematic: {exc}",
                schematic_path,
            ) from exc
        try:
            root = load_kicad_file(schematic_path)
        except Exception as exc:  # noqa: BLE001
            raise NetlistParseError(
                f"Failed to parse schematic: {exc}",
                schematic_path,
            ) from exc
        if not isinstance(root, list) or not root or root[0] != Symbol("kicad_sch"):
            raise NetlistParseError(f"Root node is not kicad_sch: {schematic_path}")
        model = ktypes.SchematicPlacementModel(path=schematic_path)
        for node in root[1:]:
            placement = self._parse_symbol(node)
            if placement is not None:
                model.placements[placement.reference] = placement
        return model

    def _parse_symbol(self, node: Any) -> ktypes.SchematicPlacement | None:
        """Parse one placed top-level symbol record."""
        from sexpdata import Symbol

        if not (isinstance(node, list) and node and node[0] == Symbol("symbol")):
            return None
        lib_id = ""
        reference = ""
        x = y = rotation = 0.0
        mirror = ""
        for item in node[1:]:
            if not (isinstance(item, list) and item):
                continue
            if item[0] == Symbol("lib_id") and len(item) >= 2:
                lib_id = str(item[1])
            elif item[0] == Symbol("at") and len(item) >= 3:
                x, y = float(item[1]), float(item[2])
                if len(item) >= 4:
                    rotation = float(item[3])
            elif item[0] == Symbol("mirror") and len(item) >= 2:
                mirror = str(item[1]).lower()
            elif item[0] == Symbol("property") and len(item) >= 3:
                if item[1] == "Reference":
                    reference = str(item[2])
        if not reference or not lib_id:
            return None
        return ktypes.SchematicPlacement(reference, lib_id, x, y, rotation, mirror)
