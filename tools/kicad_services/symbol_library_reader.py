"""Symbol library reader service.

Reads KiCad ``.kicad_sym`` libraries and returns, for each top-level symbol, its pin contracts and its drawn
graphics (polyline, circle, arc, rectangle, text, with KiCad's stroke and fill as written). Uses jBOM
S-expression helpers when available. Nothing here interprets a symbol: that is the caller's.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, List, Optional

from kicad_services import types as ktypes

# Ensure jBOM path bootstrap runs.
import kicad_services  # noqa: F401


class SymbolLibraryParseError(Exception):
    """Raised when a symbol library cannot be parsed."""

    def __init__(self, message: str, path: Optional[Path] = None) -> None:
        self.path = path
        super().__init__(message)


class SymbolLibraryReader:
    """Pure service for reading KiCad symbol libraries."""

    def validate(self, library_path: Path) -> bool:
        """Return True if path looks like a readable .kicad_sym file."""
        if not library_path.is_file():
            return False
        if library_path.suffix.lower() != ".kicad_sym":
            return False
        try:
            first = library_path.read_text(encoding="utf-8", errors="replace")[:64]
        except OSError:
            return False
        return "(kicad_symbol_lib" in first

    def read(self, library_path: Path) -> ktypes.LibraryModel:
        """Read a symbol library and return its pin contracts.

        Args:
            library_path: Path to a ``.kicad_sym`` file.

        Returns:
            LibraryModel with top-level symbols and aggregated unit pins.

        Raises:
            FileNotFoundError: If the file does not exist.
            SymbolLibraryParseError: If the file cannot be parsed.
        """
        if not library_path.exists():
            raise FileNotFoundError(f"Symbol library not found: {library_path}")
        if not self.validate(library_path):
            raise SymbolLibraryParseError(
                f"Invalid or unreadable symbol library: {library_path}",
                library_path,
            )

        try:
            from jbom.common.sexp_parser import load_kicad_file
            from sexpdata import Symbol
        except ImportError as exc:
            raise SymbolLibraryParseError(
                f"jbom/sexpdata required to parse symbol libraries: {exc}",
                library_path,
            ) from exc

        try:
            sexp = load_kicad_file(library_path)
        except Exception as exc:  # noqa: BLE001 - surface as parse error
            raise SymbolLibraryParseError(
                f"Failed to parse symbol library: {exc}",
                library_path,
            ) from exc

        if not isinstance(sexp, list) or not sexp or sexp[0] != Symbol("kicad_symbol_lib"):
            raise SymbolLibraryParseError(
                f"Root node is not kicad_symbol_lib: {library_path}",
                library_path,
            )

        model = ktypes.LibraryModel(path=library_path)
        for child in sexp[1:]:
            if not (isinstance(child, list) and child and child[0] == Symbol("symbol")):
                continue
            if len(child) < 2 or not isinstance(child[1], str):
                continue
            name = child[1]
            # Skip unit bodies accidentally walked as top-level (they use Name_u_v).
            if self._is_unit_symbol_name(name):
                continue
            symbol = self._parse_top_symbol(child, name)
            model.symbols[name] = symbol
        return model

    def _is_unit_symbol_name(self, name: str) -> bool:
        parts = name.rsplit("_", 2)
        return len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit()

    def _parse_top_symbol(self, node: List[Any], name: str) -> ktypes.LibrarySymbol:
        from sexpdata import Symbol

        properties: dict[str, str] = {}
        pins: list[ktypes.SymbolPin] = []
        graphics: list[ktypes.SymbolGraphic] = []
        seen: set[tuple[str, str]] = set()

        for item in node[1:]:
            if not (isinstance(item, list) and item):
                continue
            tag = item[0]
            if tag == Symbol("property") and len(item) >= 3:
                key, val = item[1], item[2]
                if isinstance(key, str) and isinstance(val, str):
                    properties[key] = val
            elif tag == Symbol("symbol"):
                # Unit body: collect pins and graphics.
                for pin in self._parse_unit_pins(item):
                    key = (pin.number, pin.name)
                    if key not in seen:
                        seen.add(key)
                        pins.append(pin)
                graphics.extend(self._parse_unit_graphics(item))

        reference_prefix = properties.get("Reference", "")
        return ktypes.LibrarySymbol(
            name=name,
            reference_prefix=reference_prefix,
            pins=tuple(pins),
            properties=properties,
            graphics=tuple(graphics),
        )

    @staticmethod
    def _child(node: List[Any], tag: str) -> Optional[List[Any]]:
        from sexpdata import Symbol

        for child in node[1:]:
            if isinstance(child, list) and child and child[0] == Symbol(tag):
                return child
        return None

    @staticmethod
    def _xy(node: List[Any]) -> tuple[float, float]:
        return float(node[1]), float(node[2])

    def _style(self, item: List[Any]) -> dict[str, Any]:
        """KiCad's stroke and fill exactly as written (width 0 and type default included)."""
        out: dict[str, Any] = {}
        stroke = self._child(item, "stroke")
        if stroke is not None:
            w, t = self._child(stroke, "width"), self._child(stroke, "type")
            out["stroke_width"] = float(w[1]) if w else 0.0
            out["stroke_type"] = str(t[1]) if t else ""
        fill = self._child(item, "fill")
        if fill is not None:
            t, c = self._child(fill, "type"), self._child(fill, "color")
            out["fill_type"] = str(t[1]) if t else ""
            if c is not None and len(c) >= 5:
                out["fill_color"] = tuple(float(v) for v in c[1:5])
        return out

    def _parse_unit_graphics(self, unit_node: List[Any]) -> list[ktypes.SymbolGraphic]:
        from sexpdata import Symbol

        out: list[ktypes.SymbolGraphic] = []
        for item in unit_node[1:]:
            if not (isinstance(item, list) and item and isinstance(item[0], Symbol)):
                continue
            kind = str(item[0])
            if kind == "polyline":
                pts = self._child(item, "pts")
                points = tuple(self._xy(p) for p in (pts[1:] if pts else []) if isinstance(p, list) and p and p[0] == Symbol("xy"))
                out.append(ktypes.SymbolGraphic(kind, points, **self._style(item)))
            elif kind == "circle":
                centre, radius = self._child(item, "center"), self._child(item, "radius")
                out.append(ktypes.SymbolGraphic(kind, (self._xy(centre),), radius=float(radius[1]) if radius else 0.0, **self._style(item)))
            elif kind == "arc":
                points = tuple(self._xy(self._child(item, k)) for k in ("start", "mid", "end"))
                out.append(ktypes.SymbolGraphic(kind, points, **self._style(item)))
            elif kind == "rectangle":
                points = tuple(self._xy(self._child(item, k)) for k in ("start", "end"))
                out.append(ktypes.SymbolGraphic(kind, points, **self._style(item)))
            elif kind == "text" and len(item) >= 2 and isinstance(item[1], str):
                at = self._child(item, "at")
                effects = self._child(item, "effects")
                font = self._child(effects, "font") if effects else None
                size = self._child(font, "size") if font else None
                justify = self._child(effects, "justify") if effects else None
                out.append(ktypes.SymbolGraphic(
                    kind, (self._xy(at),) if at else (), text=item[1],
                    size=float(size[1]) if size else 0.0,
                    rotation=float(at[3]) if at and len(at) > 3 else 0.0,
                    justify=" ".join(str(v) for v in justify[1:]) if justify else ""))
        return out

    def _parse_unit_pins(self, unit_node: List[Any]) -> list[ktypes.SymbolPin]:
        from sexpdata import Symbol

        pins: list[ktypes.SymbolPin] = []
        for item in unit_node[1:]:
            if not (isinstance(item, list) and item and item[0] == Symbol("pin")):
                continue
            electrical = ""
            if len(item) > 1 and not isinstance(item[1], list):
                electrical = str(item[1])
            pin_name = ""
            pin_number = ""
            x = 0.0
            y = 0.0
            rotation = 0.0
            length = 0.0
            hidden = False
            for child in item[1:]:
                if not (isinstance(child, list) and child):
                    continue
                if child[0] == Symbol("name") and len(child) >= 2 and isinstance(child[1], str):
                    pin_name = child[1]
                elif child[0] == Symbol("number") and len(child) >= 2 and isinstance(
                    child[1], str
                ):
                    pin_number = child[1]
                elif child[0] == Symbol("at") and len(child) >= 3:
                    x = float(child[1])
                    y = float(child[2])
                    if len(child) >= 4:
                        rotation = float(child[3])
                elif child[0] == Symbol("length") and len(child) >= 2:
                    length = float(child[1])
                elif child[0] == Symbol("hide") and len(child) >= 2:
                    hidden = str(child[1]) == "yes"
            if pin_number:
                pins.append(
                    ktypes.SymbolPin(
                        number=pin_number,
                        name=pin_name,
                        electrical_type=electrical,
                        x=x,
                        y=y,
                        rotation=rotation,
                        length=length,
                        hidden=hidden,
                    )
                )
        return pins
