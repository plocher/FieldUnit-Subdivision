"""Tests for KiCad services and plant-graph compiler seams."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "kicad"

if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from kicad_services.netlist_reader import KicadCliNetlistExporter, NetlistReader
from kicad_services.symbol_library_reader import SymbolLibraryReader
from kicad_services.types import (
    LibraryModel,
    LibrarySymbol,
    Net,
    NetlistComponent,
    NetlistModel,
    NetNode,
    SymbolPin,
)
from plant_graph.compiler import PlantGraphCompiler
from plant_graph.types import EntityKind, NetClass


def _irj_symbol() -> LibrarySymbol:
    return LibrarySymbol(
        name="IRJ",
        reference_prefix="B",
        pins=(
            SymbolPin("1", "A", "bidirectional"),
            SymbolPin("2", "B", "bidirectional"),
        ),
    )


def _direction_symbol() -> LibrarySymbol:
    return LibrarySymbol(
        name="Direction_BOTH",
        reference_prefix="DOT",
        pins=(
            SymbolPin("1", "", "passive"),
            SymbolPin("2", "", "passive"),
        ),
    )


class SymbolLibraryReaderTests(unittest.TestCase):
    """Seam 1: SymbolLibraryReader.read → pin contracts."""

    def test_reads_pin_contracts_from_fixture_library(self) -> None:
        model = SymbolLibraryReader().read(FIXTURES / "minimal_railroad.kicad_sym")
        self.assertIn("IRJ", model.symbols)
        self.assertIn("IRJ-Signal", model.symbols)
        self.assertIn("Switch_Powered", model.symbols)

        irj = model.symbols["IRJ"]
        self.assertEqual(irj.reference_prefix, "B")
        self.assertEqual(
            {(p.number, p.name) for p in irj.pins},
            {("1", "A"), ("2", "B")},
        )

        signal_irj = model.symbols["IRJ-Signal"]
        self.assertEqual(
            {(p.number, p.name) for p in signal_irj.pins},
            {("1", "A"), ("2", "B"), ("3", "SIGNAL")},
        )

        sw = model.symbols["Switch_Powered"]
        self.assertEqual(
            {(p.number, p.name) for p in sw.pins},
            {("1", "C"), ("2", "N"), ("3", "R")},
        )


class NetlistReaderTests(unittest.TestCase):
    """Seam 2: NetlistReader.read → components and nets."""

    def test_reads_components_and_nets_from_fixture(self) -> None:
        model = NetlistReader().read(FIXTURES / "minimal_plant.net")
        self.assertEqual(model.source, "minimal_plant.kicad_sch")
        self.assertIn("SW783", model.components)
        self.assertEqual(model.components["SW783"].part, "Switch_Powered")
        self.assertEqual(model.components["DOT1"].value, "MT")
        self.assertEqual(model.components["DOT1"].fields.get("Rulebook"), "261")
        self.assertEqual(model.components["S784S1"].value, "784SAB")

        by_name = {net.name: net for net in model.nets}
        self.assertIn("/MT_WEST", by_name)
        west = by_name["/MT_WEST"]
        self.assertEqual(
            {(n.reference, n.pin) for n in west.nodes},
            {("B1", "1"), ("DOT1", "2")},
        )
        signal = by_name["Net-(B1-SIGNAL)"]
        self.assertEqual(
            {(n.reference, n.pin) for n in signal.nodes},
            {("B1", "3"), ("S784S1", "1")},
        )


class PlantGraphCompilerTests(unittest.TestCase):
    """Seam 4: compile_plant_graph inventory and classification."""

    def setUp(self) -> None:
        self.library = SymbolLibraryReader().read(
            FIXTURES / "minimal_railroad.kicad_sym"
        )
        self.netlist = NetlistReader().read(FIXTURES / "minimal_plant.net")
        self.graph = PlantGraphCompiler().compile(self.library, self.netlist)

    def test_switch_canonical_name_and_os_circuit(self) -> None:
        sw = self.graph.entities["SW783"]
        self.assertEqual(sw.kind, EntityKind.SWITCH_POWERED)
        self.assertEqual(sw.canonical_name, "783")
        self.assertEqual(
            [tc.name for tc in self.graph.derived_track_circuits],
            ["783T1"],
        )

    def test_mast_uses_value_as_proper_name(self) -> None:
        mast = self.graph.entities["S784S1"]
        self.assertEqual(mast.kind, EntityKind.MAST_DOUBLE)
        self.assertEqual(mast.canonical_name, "784SAB")
        head = self.graph.entities["H1"]
        self.assertEqual(head.kind, EntityKind.SIGNAL_HEAD)
        self.assertEqual(head.canonical_name, "A")

    def test_classifies_track_vs_attachment_and_switch_os(self) -> None:
        by_raw = {n.raw_name: n for n in self.graph.nets}
        self.assertEqual(by_raw["/MT_WEST"].net_class, NetClass.TRACK)
        self.assertTrue(by_raw["/MT_WEST"].authoritative_label)
        self.assertEqual(by_raw["/MT_WEST"].name, "MT_WEST")

        self.assertEqual(
            by_raw["Net-(B1-SIGNAL)"].net_class, NetClass.SIGNAL_ATTACHMENT
        )
        self.assertFalse(by_raw["Net-(B1-SIGNAL)"].authoritative_label)

        self.assertEqual(by_raw["Net-(H1-M)"].net_class, NetClass.HEAD_ATTACHMENT)

        # IRJ B ↔ Switch C is part of derived OS circuit; no label required.
        os_leg = by_raw["Net-(B1-A)"]
        self.assertEqual(os_leg.net_class, NetClass.SWITCH_OS)
        codes = {d.code for d in self.graph.diagnostics}
        self.assertNotIn("unlabeled_track_net", codes)

    def test_direction_keeps_rulebook(self) -> None:
        dot = self.graph.entities["DOT1"]
        self.assertEqual(dot.kind, EntityKind.DIRECTION)
        self.assertEqual(dot.canonical_name, "MT")
        self.assertEqual(dot.fields.get("Rulebook"), "261")

    def test_unlabeled_non_os_track_net_is_semantic_error(self) -> None:
        library = LibraryModel(path=Path("x.kicad_sym"))
        library.symbols["IRJ"] = _irj_symbol()
        netlist = NetlistModel(path=Path("x.net"))
        netlist.components = {
            "B1": NetlistComponent("B1", "~", "Railroad", "IRJ"),
            "B2": NetlistComponent("B2", "~", "Railroad", "IRJ"),
        }
        netlist.nets = [
            Net(
                code="1",
                name="Net-(B1-B2)",
                nodes=(
                    NetNode("B1", "2"),
                    NetNode("B2", "1"),
                ),
            )
        ]
        graph = PlantGraphCompiler().compile(library, netlist)
        track = [n for n in graph.nets if n.net_class is NetClass.TRACK]
        self.assertEqual(len(track), 1)
        self.assertIn("unlabeled_track_net", {d.code for d in graph.diagnostics})

    def test_direction_intentional_nc_is_ignored(self) -> None:
        library = LibraryModel(path=Path("x.kicad_sym"))
        library.symbols["Direction_BOTH"] = _direction_symbol()
        library.symbols["IRJ"] = _irj_symbol()
        netlist = NetlistModel(path=Path("x.net"))
        netlist.components = {
            "DOT1": NetlistComponent(
                "DOT1",
                "MT",
                "Railroad",
                "Direction_BOTH",
                fields={"Rulebook": "261"},
            ),
            "B1": NetlistComponent("B1", "~", "Railroad", "IRJ"),
        }
        netlist.nets = [
            Net(
                code="1",
                name="/MT",
                nodes=(
                    NetNode("DOT1", "2"),
                    NetNode("B1", "1"),
                ),
            ),
            Net(
                code="2",
                name="unconnected-(DOT1-Pad1)",
                nodes=(NetNode("DOT1", "1", pintype="passive+no_connect"),),
            ),
        ]
        graph = PlantGraphCompiler().compile(library, netlist)
        dot_codes = {
            d.code for d in graph.diagnostics if d.entity_ref == "DOT1"
        }
        self.assertNotIn("direction_open_pin_without_nc", dot_codes)
        self.assertNotIn("direction_fully_unconnected", dot_codes)
        self.assertNotIn("unconnected_required_pin", dot_codes)

    def test_direction_terminal_one_live_pin_ok_without_nc_helper(self) -> None:
        """Terminal DoT needs one live track pin; bare open other pin is fine."""
        library = LibraryModel(path=Path("x.kicad_sym"))
        library.symbols["Direction_BOTH"] = _direction_symbol()
        library.symbols["IRJ"] = _irj_symbol()
        netlist = NetlistModel(path=Path("x.net"))
        netlist.components = {
            "DOT1": NetlistComponent(
                "DOT1",
                "MT",
                "Railroad",
                "Direction_BOTH",
                fields={"Rulebook": "261"},
            ),
            "B1": NetlistComponent("B1", "~", "Railroad", "IRJ"),
        }
        netlist.nets = [
            Net(
                code="1",
                name="/MT",
                nodes=(
                    NetNode("DOT1", "2"),
                    NetNode("B1", "1"),
                ),
            ),
            Net(
                code="2",
                name="unconnected-(DOT1-Pad1)",
                nodes=(NetNode("DOT1", "1", pintype="passive"),),
            ),
        ]
        graph = PlantGraphCompiler().compile(library, netlist)
        self.assertEqual(len(graph.terminals), 1)
        self.assertEqual(graph.terminals[0].reference, "DOT1")
        self.assertEqual(graph.terminals[0].designation, "MT")
        codes = {d.code for d in graph.diagnostics if d.entity_ref == "DOT1"}
        self.assertNotIn("direction_both_pins_live", codes)
        self.assertNotIn("direction_fully_unconnected", codes)



    def test_harvests_routes_for_signal_faces_on_minimal_switch(self) -> None:
        """One switch between two DoT terminals yields N and R routes."""
        library = LibraryModel(path=Path("x.kicad_sym"))
        library.symbols["IRJ"] = _irj_symbol()
        library.symbols["Direction_BOTH"] = _direction_symbol()
        library.symbols["Switch_Powered"] = LibrarySymbol(
            name="Switch_Powered",
            reference_prefix="SW",
            pins=(
                SymbolPin("1", "C", "passive"),
                SymbolPin("2", "N", "passive"),
                SymbolPin("3", "R", "passive"),
            ),
        )
        # Build netlist: DOT_E - B1 - SW C/N - B2 - DOT_X  and SW R - B3 - DOT_Y
        # Use IRJ-Signal + mast so a signal face exists.
        from kicad_services.types import LibrarySymbol as LS
        library.symbols["IRJ-Signal"] = LibrarySymbol(
            name="IRJ-Signal",
            reference_prefix="B",
            pins=(
                SymbolPin("1", "A", "bidirectional"),
                SymbolPin("2", "B", "bidirectional"),
                SymbolPin("3", "SIGNAL", "passive"),
            ),
        )
        library.symbols["Mast_Single"] = LibrarySymbol(
            name="Mast_Single",
            reference_prefix="S",
            pins=(
                SymbolPin("1", "SIGNAL", "passive"),
                SymbolPin("2", "H", "passive"),
            ),
        )
        netlist = NetlistModel(path=Path("x.net"))
        netlist.components = {
            "DOT_E": NetlistComponent("DOT_E", "EAST", "Railroad", "Direction_BOTH", fields={"Rulebook": "261"}),
            "DOT_XN": NetlistComponent("DOT_XN", "NORTH", "Railroad", "Direction_BOTH", fields={"Rulebook": "261"}),
            "DOT_XR": NetlistComponent("DOT_XR", "SOUTH", "Railroad", "Direction_BOTH", fields={"Rulebook": "261"}),
            "B1": NetlistComponent("B1", "~", "Railroad", "IRJ-Signal"),
            "B2": NetlistComponent("B2", "~", "Railroad", "IRJ"),
            "B3": NetlistComponent("B3", "~", "Railroad", "IRJ"),
            "SW1": NetlistComponent("SW1", "~", "Railroad", "Switch_Powered"),
            "S2N1": NetlistComponent("S2N1", "2NAB", "Railroad", "Mast_Single"),
        }
        netlist.nets = [
            Net("1", "/EAST", (NetNode("DOT_E", "2"), NetNode("B1", "2"))),
            Net("2", "Net-(B1-A)", (NetNode("B1", "1"), NetNode("SW1", "1"))),
            Net("3", "Net-(SW-N)", (NetNode("SW1", "2"), NetNode("B2", "1"))),
            Net("4", "/NORTH", (NetNode("B2", "2"), NetNode("DOT_XN", "1"))),
            Net("5", "Net-(SW-R)", (NetNode("SW1", "3"), NetNode("B3", "1"))),
            Net("6", "/SOUTH", (NetNode("B3", "2"), NetNode("DOT_XR", "1"))),
            Net("7", "Net-(SIG)", (NetNode("B1", "3"), NetNode("S2N1", "1"))),
        ]
        graph = PlantGraphCompiler().compile(library, netlist)
        self.assertGreaterEqual(len(graph.signal_faces), 1)
        self.assertGreaterEqual(len(graph.routes), 2)
        exits = {(r.exit_designation, dict(r.switch_alignments).get("1")) for r in graph.routes}
        self.assertIn(("NORTH", "N"), exits)
        self.assertIn(("SOUTH", "R"), exits)


class KicadCliExporterSmokeTests(unittest.TestCase):
    """Seam 3: exporter discovery (no required KiCad for unit suite)."""

    def test_discover_reports_boolean(self) -> None:
        exporter = KicadCliNetlistExporter()
        self.assertIsInstance(exporter.available(), bool)


class CliSmokeTests(unittest.TestCase):
    """Seam 5: CLI text inventory over fixture netlist."""

    def test_cli_text_inventory_from_netlist_fixture(self) -> None:
        import runpy
        from io import StringIO
        from unittest import mock

        cli = ROOT / "tools" / "parse_kicad_plant.py"
        argv = [
            str(cli),
            "--library",
            str(FIXTURES / "minimal_railroad.kicad_sym"),
            "--netlist",
            str(FIXTURES / "minimal_plant.net"),
            "--format",
            "text",
        ]
        stdout = StringIO()
        exit_code = 0
        with mock.patch.object(sys, "argv", argv), mock.patch("sys.stdout", stdout):
            try:
                runpy.run_path(str(cli), run_name="__main__")
            except SystemExit as exc:
                exit_code = exc.code if isinstance(exc.code, int) else 1
        text = stdout.getvalue()
        # Inventory always prints; fixture may still flag incomplete switch legs.
        self.assertIn(exit_code, (0, 1))
        self.assertIn("SW783", text)
        self.assertIn("783T1", text)
        self.assertIn("signal_attachment", text)
        self.assertIn("switch_os", text)


if __name__ == "__main__":
    unittest.main()
