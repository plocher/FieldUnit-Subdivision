"""Netlist reader and optional kicad-cli exporter services."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, List, Optional

from kicad_services import types as ktypes

import kicad_services  # noqa: F401


class NetlistParseError(Exception):
    """Raised when a KiCad netlist cannot be parsed."""

    def __init__(self, message: str, path: Optional[Path] = None) -> None:
        self.path = path
        super().__init__(message)


class NetlistReader:
    """Pure service for reading KiCad kicadsexpr netlist exports."""

    def validate(self, netlist_path: Path) -> bool:
        """Return True if path looks like a readable netlist export."""
        if not netlist_path.is_file():
            return False
        try:
            first = netlist_path.read_text(encoding="utf-8", errors="replace")[:80]
        except OSError:
            return False
        return first.lstrip().startswith("(export")

    def read(self, netlist_path: Path) -> ktypes.NetlistModel:
        """Read a kicadsexpr netlist file.

        Args:
            netlist_path: Path to a netlist produced by
                ``kicad-cli sch export netlist``.

        Returns:
            NetlistModel with components and nets.

        Raises:
            FileNotFoundError: If the file does not exist.
            NetlistParseError: If the file cannot be parsed.
        """
        if not netlist_path.exists():
            raise FileNotFoundError(f"Netlist not found: {netlist_path}")
        if not self.validate(netlist_path):
            raise NetlistParseError(
                f"Invalid or unreadable netlist: {netlist_path}",
                netlist_path,
            )

        try:
            from jbom.common.sexp_parser import load_kicad_file
            from sexpdata import Symbol
        except ImportError as exc:
            raise NetlistParseError(
                f"jbom/sexpdata required to parse netlists: {exc}",
                netlist_path,
            ) from exc

        try:
            sexp = load_kicad_file(netlist_path)
        except Exception as exc:  # noqa: BLE001
            raise NetlistParseError(
                f"Failed to parse netlist: {exc}",
                netlist_path,
            ) from exc

        if not isinstance(sexp, list) or not sexp or sexp[0] != Symbol("export"):
            raise NetlistParseError(
                f"Root node is not export: {netlist_path}",
                netlist_path,
            )

        model = ktypes.NetlistModel(path=netlist_path)
        for child in sexp[1:]:
            if not (isinstance(child, list) and child):
                continue
            tag = child[0]
            if tag == Symbol("design"):
                model.source = self._design_source(child)
            elif tag == Symbol("components"):
                for comp_node in child[1:]:
                    comp = self._parse_component(comp_node)
                    if comp is not None:
                        model.components[comp.reference] = comp
            elif tag == Symbol("nets"):
                for net_node in child[1:]:
                    net = self._parse_net(net_node)
                    if net is not None:
                        model.nets.append(net)
        return model

    def _design_source(self, design_node: List[Any]) -> str:
        from sexpdata import Symbol

        for item in design_node[1:]:
            if (
                isinstance(item, list)
                and item
                and item[0] == Symbol("source")
                and len(item) >= 2
                and isinstance(item[1], str)
            ):
                return item[1]
        return ""

    def _parse_component(self, node: Any) -> Optional[ktypes.NetlistComponent]:
        from sexpdata import Symbol

        if not (isinstance(node, list) and node and node[0] == Symbol("comp")):
            return None

        reference = ""
        value = ""
        lib = ""
        part = ""
        fields: dict[str, str] = {}

        for item in node[1:]:
            if not (isinstance(item, list) and item):
                continue
            tag = item[0]
            if tag == Symbol("ref") and len(item) >= 2 and isinstance(item[1], str):
                reference = item[1]
            elif tag == Symbol("value") and len(item) >= 2 and isinstance(item[1], str):
                value = item[1]
            elif tag == Symbol("libsource"):
                for sub in item[1:]:
                    if not (isinstance(sub, list) and sub):
                        continue
                    if sub[0] == Symbol("lib") and len(sub) >= 2 and isinstance(sub[1], str):
                        lib = sub[1]
                    elif sub[0] == Symbol("part") and len(sub) >= 2 and isinstance(sub[1], str):
                        part = sub[1]
            elif tag == Symbol("fields"):
                for field_node in item[1:]:
                    parsed = self._parse_field(field_node)
                    if parsed is not None:
                        fields[parsed[0]] = parsed[1]
            elif tag == Symbol("property") and len(item) >= 3:
                # Alternate property shape: (property (name "X") (value "Y"))
                name = ""
                val = ""
                for sub in item[1:]:
                    if not (isinstance(sub, list) and sub):
                        continue
                    if sub[0] == Symbol("name") and len(sub) >= 2 and isinstance(sub[1], str):
                        name = sub[1]
                    elif sub[0] == Symbol("value") and len(sub) >= 2 and isinstance(
                        sub[1], str
                    ):
                        val = sub[1]
                if name:
                    fields.setdefault(name, val)

        if not reference:
            return None
        return ktypes.NetlistComponent(
            reference=reference,
            value=value,
            lib=lib,
            part=part,
            fields=fields,
        )

    def _parse_field(self, node: Any) -> Optional[tuple[str, str]]:
        from sexpdata import Symbol

        if not (isinstance(node, list) and node and node[0] == Symbol("field")):
            return None
        name = ""
        value = ""
        # Shapes:
        #   (field (name "Rulebook") "261")
        #   (field (name "Footprint"))
        for item in node[1:]:
            if isinstance(item, list) and item and item[0] == Symbol("name") and len(item) >= 2:
                if isinstance(item[1], str):
                    name = item[1]
            elif isinstance(item, str):
                value = item
        if not name:
            return None
        return name, value

    def _parse_net(self, node: Any) -> Optional[ktypes.Net]:
        from sexpdata import Symbol

        if not (isinstance(node, list) and node and node[0] == Symbol("net")):
            return None

        code = ""
        name = ""
        nodes: list[ktypes.NetNode] = []
        for item in node[1:]:
            if not (isinstance(item, list) and item):
                continue
            tag = item[0]
            if tag == Symbol("code") and len(item) >= 2:
                code = str(item[1])
            elif tag == Symbol("name") and len(item) >= 2 and isinstance(item[1], str):
                name = item[1]
            elif tag == Symbol("node"):
                net_node = self._parse_node(item)
                if net_node is not None:
                    nodes.append(net_node)
        if not name and not code:
            return None
        return ktypes.Net(code=code, name=name, nodes=tuple(nodes))

    def _parse_node(self, node: List[Any]) -> Optional[ktypes.NetNode]:
        from sexpdata import Symbol

        reference = ""
        pin = ""
        pinfunction = ""
        pintype = ""
        for item in node[1:]:
            if not (isinstance(item, list) and item):
                continue
            tag = item[0]
            if tag == Symbol("ref") and len(item) >= 2 and isinstance(item[1], str):
                reference = item[1]
            elif tag == Symbol("pin") and len(item) >= 2 and isinstance(item[1], str):
                pin = item[1]
            elif tag == Symbol("pinfunction") and len(item) >= 2 and isinstance(item[1], str):
                pinfunction = item[1]
            elif tag == Symbol("pintype") and len(item) >= 2 and isinstance(item[1], str):
                pintype = item[1]
        if not reference or not pin:
            return None
        return ktypes.NetNode(
            reference=reference,
            pin=pin,
            pinfunction=pinfunction,
            pintype=pintype,
        )


class KicadCliNetlistExporter:
    """Export a schematic netlist via ``kicad-cli sch export netlist``."""

    def __init__(self, kicad_cli: Optional[Path] = None) -> None:
        """Configure the exporter.

        Args:
            kicad_cli: Explicit path to kicad-cli. If omitted, uses
                ``KICAD_CLI`` env or common macOS install locations.
        """
        self.kicad_cli = kicad_cli or self._discover_kicad_cli()

    def _discover_kicad_cli(self) -> Path:
        env = os.environ.get("KICAD_CLI")
        if env:
            return Path(env)
        candidates = [
            Path("/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"),
            Path("/Applications/KiCad New.app/Contents/MacOS/kicad-cli"),
            Path("/usr/local/bin/kicad-cli"),
            Path("/usr/bin/kicad-cli"),
        ]
        for path in candidates:
            if path.is_file():
                return path
        return Path("kicad-cli")

    def available(self) -> bool:
        """Return True if kicad-cli can be executed."""
        cli = self.kicad_cli
        if cli.is_file():
            return True
        from shutil import which

        return which(str(cli)) is not None

    def export(self, schematic_path: Path, output_path: Optional[Path] = None) -> Path:
        """Export a netlist for ``schematic_path``.

        Args:
            schematic_path: Path to a ``.kicad_sch`` file.
            output_path: Optional destination. If omitted, a temporary
                ``.net`` file is created.

        Returns:
            Path to the written netlist.

        Raises:
            FileNotFoundError: If the schematic or kicad-cli is missing.
            NetlistParseError: If the export command fails.
        """
        if not schematic_path.is_file():
            raise FileNotFoundError(f"Schematic not found: {schematic_path}")
        if not self.available():
            raise FileNotFoundError(f"kicad-cli not found: {self.kicad_cli}")

        if output_path is None:
            fd, name = tempfile.mkstemp(prefix="kicad_netlist_", suffix=".net")
            os.close(fd)
            output_path = Path(name)

        cmd = [
            str(self.kicad_cli),
            "sch",
            "export",
            "netlist",
            "--format",
            "kicadsexpr",
            str(schematic_path),
            "-o",
            str(output_path),
        ]
        try:
            completed = subprocess.run(
                cmd,
                check=False,
                capture_output=True,
                text=True,
            )
        except OSError as exc:
            raise NetlistParseError(
                f"Failed to run kicad-cli: {exc}",
                schematic_path,
            ) from exc

        if completed.returncode != 0:
            raise NetlistParseError(
                "kicad-cli netlist export failed: "
                f"{completed.stderr.strip() or completed.stdout.strip()}",
                schematic_path,
            )
        if not output_path.is_file():
            raise NetlistParseError(
                f"kicad-cli reported success but wrote no file: {output_path}",
                schematic_path,
            )
        return output_path
