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
    SchematicPlacement,
    SchematicPlacementModel,
    SymbolPin,
)
from plant_graph.compiler import PlantGraphCompiler
from plant_graph.picture import render_layout_overview_svg, render_model_board_svg
from plant_graph.routes import (
    format_alignment,
    format_route_line,
)
from plant_graph.types import (
    CircuitRole,
    EntityKind,
    Indication,
    NetClass,
    PointTraversal,
    SchematicHeading,
    TurnoutHand,
)


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

    def test_derives_switch_hand_and_heading_from_source_geometry(self) -> None:
        placements = SchematicPlacementModel(path=Path("minimal_plant.kicad_sch"))
        placements.placements["SW783"] = SchematicPlacement(
            reference="SW783",
            lib_id="Railroad:Switch_Powered",
            x=100.0,
            y=100.0,
            rotation=0.0,
        )

        graph = PlantGraphCompiler().compile(self.library, self.netlist, placements)

        geometry = graph.switch_geometries["783"]
        self.assertEqual(geometry.cn_heading, SchematicHeading.LEFT)
        self.assertEqual(geometry.reverse_side, TurnoutHand.RIGHT)
    def test_compiles_layout_primitives_for_record_only_renderers(self) -> None:
        """Placed source compiles bases and terminals before either board renders."""
        placements = SchematicPlacementModel(path=Path("minimal_plant.kicad_sch"))
        placements.placements.update(
            {
                "DOT1": SchematicPlacement(
                    "DOT1",
                    "Railroad:Direction_BOTH",
                    10.0,
                    100.0,
                    0.0,
                ),
                "B1": SchematicPlacement(
                    "B1",
                    "Railroad:IRJ-Signal",
                    50.0,
                    100.0,
                    0.0,
                ),
                "SW783": SchematicPlacement(
                    "SW783",
                    "Railroad:Switch_Powered",
                    100.0,
                    100.0,
                    0.0,
                ),
                "S784S1": SchematicPlacement(
                    "S784S1",
                    "Railroad:Mast_Double",
                    50.0,
                    110.0,
                    0.0,
                ),
            }
        )

        graph = PlantGraphCompiler().compile(self.library, self.netlist, placements)

        self.assertTrue(graph.rail_rows)
        self.assertEqual(
            [(base.mast_name, base.irj_reference) for base in graph.signal_bases],
            [("784SAB", "B1")],
        )
        self.assertEqual(
            [(terminal.name, terminal.side) for terminal in graph.board_terminals],
            [("MT", "left")],
        )
        self.assertIn('class="overview-background"', render_model_board_svg(graph))
        self.assertIn("Controlled Point", render_layout_overview_svg(graph))

    def test_invalid_switch_indications_are_semantic_errors(self) -> None:
        self.netlist.components["SW783"] = NetlistComponent(
            "SW783",
            "~",
            "Railroad",
            "Switch_Powered",
            fields={"Indications": "CLEAR/NOT_AN_INDICATION"},
        )

        graph = PlantGraphCompiler().compile(self.library, self.netlist)

        self.assertIn(
            "invalid_switch_indications",
            {diagnostic.code for diagnostic in graph.diagnostics},
        )

    def test_mast_uses_value_as_proper_name(self) -> None:
        mast = self.graph.entities["S784S1"]
        self.assertEqual(mast.kind, EntityKind.MAST_DOUBLE)
        self.assertEqual(mast.canonical_name, "784SAB")
        head = self.graph.entities["H1"]
        self.assertEqual(head.kind, EntityKind.SIGNAL_HEAD)
        self.assertEqual(head.canonical_name, "A")
        self.assertEqual(
            [
                (attachment.mast_reference, attachment.head_name)
                for attachment in self.graph.mast_heads
            ],
            [("S784S1", "A")],
        )
        self.assertIn(
            "mast_head_grammar_mismatch",
            {diagnostic.code for diagnostic in self.graph.diagnostics},
        )

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
        # Build netlist: DOT_E - B1 - SW C/N - B2 - DOT_X and SW R - B3 - DOT_Y.
        # B2 carries an opposing mast, so NORTH is downstream of the source
        # mast's far interlocking limit. SOUTH has no such boundary evidence.
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
        library.symbols["Signal Head - CL"] = LibrarySymbol(
            name="Signal Head - CL",
            reference_prefix="H",
            pins=(SymbolPin("1", "M", "passive"),),
        )
        netlist = NetlistModel(path=Path("x.net"))
        netlist.components = {
            "DOT_E": NetlistComponent("DOT_E", "EAST", "Railroad", "Direction_BOTH", fields={"Rulebook": "261"}),
            "DOT_XN": NetlistComponent("DOT_XN", "NORTH", "Railroad", "Direction_BOTH", fields={"Rulebook": "261"}),
            "DOT_XR": NetlistComponent("DOT_XR", "SOUTH", "Railroad", "Direction_BOTH", fields={"Rulebook": "261"}),
            "B1": NetlistComponent("B1", "~", "Railroad", "IRJ-Signal"),
            "B2": NetlistComponent("B2", "~", "Railroad", "IRJ-Signal"),
            "B3": NetlistComponent("B3", "~", "Railroad", "IRJ"),
            "SW1": NetlistComponent(
                "SW1",
                "~",
                "Railroad",
                "Switch_Powered",
                fields={"Indications": "CLEAR/DIVERGING_CLEAR"},
            ),
            "S2N1": NetlistComponent("S2N1", "2NA", "Railroad", "Mast_Single"),
            "S4S1": NetlistComponent("S4S1", "4SA", "Railroad", "Mast_Single"),
            "H2": NetlistComponent("H2", "A", "Railroad", "Signal Head - CL"),
            "H4": NetlistComponent("H4", "A", "Railroad", "Signal Head - CL"),
        }
        netlist.nets = [
            Net("1", "/EAST", (NetNode("DOT_E", "2"), NetNode("B1", "2"))),
            Net("2", "Net-(B1-A)", (NetNode("B1", "1"), NetNode("SW1", "1"))),
            Net("3", "Net-(SW-N)", (NetNode("SW1", "2"), NetNode("B2", "1"))),
            Net("4", "/NORTH", (NetNode("B2", "2"), NetNode("DOT_XN", "1"))),
            Net("5", "Net-(SW-R)", (NetNode("SW1", "3"), NetNode("B3", "1"))),
            Net("6", "/SOUTH", (NetNode("B3", "2"), NetNode("DOT_XR", "1"))),
            Net("7", "Net-(SIG)", (NetNode("B1", "3"), NetNode("S2N1", "1"))),
            Net("8", "Net-(SIG4)", (NetNode("B2", "3"), NetNode("S4S1", "1"))),
            Net("9", "Net-(H2-M)", (NetNode("S2N1", "2"), NetNode("H2", "1"))),
            Net("10", "Net-(H4-M)", (NetNode("S4S1", "2"), NetNode("H4", "1"))),
        ]
        graph = PlantGraphCompiler().compile(library, netlist)
        self.assertGreaterEqual(len(graph.signal_faces), 1)
        self.assertGreaterEqual(len(graph.routes), 2)
        exits = {(r.exit_designation, dict(r.switch_alignments).get("1")) for r in graph.routes}
        self.assertIn(("NORTH", "N"), exits)
        self.assertIn(("SOUTH", "R"), exits)
        north_route = next(route for route in graph.routes if route.exit_net == "NORTH")
        north_roles = dict(north_route.circuit_roles)
        self.assertEqual(north_roles["EAST"], CircuitRole.ENTRANCE)
        self.assertEqual(north_roles["1T1"], CircuitRole.HOME_CLEAR)
        self.assertEqual(north_roles["NORTH"], CircuitRole.DOWNSTREAM)
        north_line = format_route_line(north_route)
        self.assertEqual(
            format_alignment((("799", "N"), ("783", "N"), ("795", "R"))),
            " 783 (795) 799 ",
        )
        self.assertIn("2(LEFT)", north_line)
        self.assertNotIn("2N(LEFT)", north_line)
        self.assertIn("entrance=EAST", north_line)
        self.assertIn("home-clear=1T1", north_line)
        self.assertIn("downstream=NORTH", north_line)
        self.assertEqual(north_route.static_indication, Indication.CLEAR)
        self.assertEqual(
            tuple(
                (
                    traversal.switch_name,
                    traversal.entry_pin,
                    traversal.exit_pin,
                    traversal.alignment,
                    traversal.point_traversal,
                )
                for traversal in north_route.switch_traversals
            ),
            (("1", "1", "2", "N", PointTraversal.FACING),),
        )

        south_route = next(route for route in graph.routes if route.exit_net == "SOUTH")
        south_roles = dict(south_route.circuit_roles)
        self.assertEqual(south_roles["EAST"], CircuitRole.ENTRANCE)
        self.assertEqual(south_roles["1T1"], CircuitRole.HOME_CLEAR)
        self.assertEqual(south_roles["SOUTH"], CircuitRole.UNRESOLVED)
        self.assertEqual(
            south_route.static_indication,
            Indication.DIVERGING_CLEAR,
        )
        self.assertEqual(
            tuple(
                (
                    traversal.switch_name,
                    traversal.entry_pin,
                    traversal.exit_pin,
                    traversal.alignment,
                    traversal.point_traversal,
                )
                for traversal in south_route.switch_traversals
            ),
            (("1", "1", "3", "R", PointTraversal.FACING),),
        )
        self.assertIn("unresolved=SOUTH", format_route_line(south_route))
        self.assertEqual(
            north_route.head_names,
            ("A",),
        )

    def test_one_pin_policy_markers_and_next_cp_define_route_limits(self) -> None:
        """Policy markers annotate nets; NextCP symbols form route endpoints."""
        library = LibraryModel(path=Path("x.kicad_sym"))
        library.symbols["NextCP"] = LibrarySymbol(
            name="NextCP",
            reference_prefix="CP",
            pins=(SymbolPin("1", "To", "passive"),),
        )
        library.symbols["Rule261-DoT-BiDirectional"] = LibrarySymbol(
            name="Rule261-DoT-BiDirectional",
            reference_prefix="DOT",
            pins=(SymbolPin("1", "To", "passive"),),
        )
        library.symbols["Track Circuit"] = LibrarySymbol(
            name="Track Circuit",
            reference_prefix="TC",
            pins=(SymbolPin("1", "To", "passive"),),
        )
        library.symbols["MAIN HOUSE"] = LibrarySymbol(
            name="MAIN HOUSE",
            reference_prefix="HOUSE",
            pins=(),
        )
        library.symbols["IRJ-Signal"] = LibrarySymbol(
            name="IRJ-Signal",
            reference_prefix="B",
            pins=(
                SymbolPin("1", "A", "bidirectional"),
                SymbolPin("2", "B", "bidirectional"),
                SymbolPin("3", "SIGNAL", "passive"),
            ),
        )
        library.symbols["Switch_Powered"] = LibrarySymbol(
            name="Switch_Powered",
            reference_prefix="SW",
            pins=(
                SymbolPin("1", "C", "passive"),
                SymbolPin("2", "N", "passive"),
                SymbolPin("3", "R", "passive"),
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
        library.symbols["Signal Head - CL"] = LibrarySymbol(
            name="Signal Head - CL",
            reference_prefix="H",
            pins=(SymbolPin("1", "M", "passive"),),
        )
        netlist = NetlistModel(path=Path("x.net"))
        netlist.components = {
            "HOUSE_W": NetlistComponent(
                "HOUSE_W", "CP West", "Railroad", "MAIN HOUSE"
            ),
            "HOUSE_E": NetlistComponent(
                "HOUSE_E", "CP East", "Railroad", "MAIN HOUSE"
            ),
            "CP_W": NetlistComponent("CP_W", "CP West", "Railroad", "NextCP"),
            "CP_E": NetlistComponent("CP_E", "CP East", "Railroad", "NextCP"),
            "DOT_W": NetlistComponent(
                "DOT_W", "MT", "Railroad", "Rule261-DoT-BiDirectional",
                fields={"Rulebook": "261", "Direction": "BOTH"},
            ),
            "DOT_E": NetlistComponent(
                "DOT_E", "MT", "Railroad", "Rule261-DoT-BiDirectional",
                fields={"Rulebook": "261", "Direction": "BOTH"},
            ),
            "B1": NetlistComponent(
                "B1", "~", "Railroad", "IRJ-Signal", fields={"CP": "CP West"}
            ),
            "B2": NetlistComponent(
                "B2", "~", "Railroad", "IRJ-Signal", fields={"CP": "CP East"}
            ),
            "SW1": NetlistComponent(
                "SW1", "~", "Railroad", "Switch_Powered", fields={"CP": "CP West"}
            ),
            "S2E1": NetlistComponent("S2E1", "2EA", "Railroad", "Mast_Single"),
            "S2W1": NetlistComponent("S2W1", "2WA", "Railroad", "Mast_Single"),
            "H_E": NetlistComponent("H_E", "A", "Railroad", "Signal Head - CL"),
            "H_W": NetlistComponent("H_W", "A", "Railroad", "Signal Head - CL"),
            "TC_W": NetlistComponent(
                "TC_W", "MT_W", "Railroad", "Track Circuit", fields={"CP": "CP West"}
            ),
            "TC_E": NetlistComponent(
                "TC_E", "MT_E", "Railroad", "Track Circuit", fields={"CP": "CP East"}
            ),
        }
        netlist.nets = [
            Net("1", "Net-(WEST)", (NetNode("CP_W", "1"), NetNode("DOT_W", "1"), NetNode("B1", "2"), NetNode("TC_W", "1"))),
            Net("2", "Net-(B1-A)", (NetNode("B1", "1"), NetNode("SW1", "1"))),
            Net("3", "Net-(SW-N)", (NetNode("SW1", "2"), NetNode("B2", "1"))),
            Net("4", "Net-(EAST)", (NetNode("B2", "2"), NetNode("DOT_E", "1"), NetNode("CP_E", "1"), NetNode("TC_E", "1"))),
            Net("5", "Net-(SIG-E)", (NetNode("B1", "3"), NetNode("S2E1", "1"))),
            Net("6", "Net-(SIG-W)", (NetNode("B2", "3"), NetNode("S2W1", "1"))),
            Net("7", "Net-(H-E)", (NetNode("S2E1", "2"), NetNode("H_E", "1"))),
            Net("8", "Net-(H-W)", (NetNode("S2W1", "2"), NetNode("H_W", "1"))),
            Net("9", "unconnected-(SW1-R)", (NetNode("SW1", "3", pintype="passive+no_connect"),)),
        ]
        graph = PlantGraphCompiler().compile(library, netlist)
        self.assertFalse(graph.has_errors(), graph.diagnostics)
        self.assertTrue(
            graph.routes,
            {
                "terminals": graph.terminals,
                "signal_faces": graph.signal_faces,
                "nets": graph.nets,
            },
        )
        self.assertEqual(graph.entities["DOT_W"].kind, EntityKind.OPERATING_POLICY)
        self.assertEqual(graph.entities["CP_E"].kind, EntityKind.NEXT_CP)
        self.assertEqual(graph.entities["TC_W"].kind, EntityKind.TRACK_CIRCUIT)
        eastbound = next(route for route in graph.routes if route.mast_name == "2EA")
        self.assertEqual(eastbound.direction, "RIGHT")
        self.assertEqual(eastbound.entry_terminal, "CP_W")
        self.assertEqual(eastbound.exit_terminal, "CP_E")
        self.assertEqual(eastbound.head_names, ("A",))
        self.assertEqual(
            dict(eastbound.circuit_roles),
            {
                "1T1": CircuitRole.HOME_CLEAR,
                "MT_E": CircuitRole.DOWNSTREAM,
                "MT_W": CircuitRole.ENTRANCE,
            },
        )
        reversed_convention = PlantGraphCompiler(
            mast_direction_map={"E": "LEFT", "W": "RIGHT"}
        ).compile(library, netlist)
        reversed_eastbound = next(
            route
            for route in reversed_convention.routes
            if route.mast_name == "2EA"
        )
        self.assertEqual(reversed_eastbound.direction, "LEFT")

    def test_rule_628_marker_defines_an_untracked_dark_segment(self) -> None:
        """A Rule 6.28 marker names dark track without creating a circuit."""
        library = LibraryModel(path=Path("x.kicad_sym"))
        library.symbols["Bumper"] = LibrarySymbol(
            name="Bumper",
            reference_prefix="B",
            pins=(SymbolPin("2", "B", "passive"),),
        )
        library.symbols["Rule6.28-OtherThanMain"] = LibrarySymbol(
            name="Rule6.28-OtherThanMain",
            reference_prefix="DOT",
            pins=(SymbolPin("1", "To", "passive"),),
        )
        netlist = NetlistModel(path=Path("x.net"))
        netlist.components = {
            "B1": NetlistComponent("B1", "~", "Railroad", "Bumper"),
            "DOT5": NetlistComponent(
                "DOT5", "Industry", "Railroad", "Rule6.28-OtherThanMain",
                fields={"Rulebook": "Rule 6.28", "Direction": "BOTH"},
            ),
        }
        netlist.nets = [
            Net("1", "Net-(B1-B)", (NetNode("B1", "2"), NetNode("DOT5", "1")))
        ]
        graph = PlantGraphCompiler().compile(library, netlist)
        self.assertEqual(graph.nets[0].net_class, NetClass.DARK_TRACK)
        self.assertNotIn(
            "unlabeled_track_net",
            {diagnostic.code for diagnostic in graph.diagnostics},
        )

    def test_rule_628_segment_terminates_route_at_preceding_irj(self) -> None:
        """Dark track beyond an IRJ is outside the controlling route."""
        from plant_graph.types import RouteEndKind

        library = LibraryModel(path=Path("x.kicad_sym"))
        library.symbols["NextCP"] = LibrarySymbol(
            name="NextCP", reference_prefix="CP", pins=(SymbolPin("1", "To", "passive"),)
        )
        library.symbols["Rule261-DoT-BiDirectional"] = LibrarySymbol(
            name="Rule261-DoT-BiDirectional", reference_prefix="DOT", pins=(SymbolPin("1", "To", "passive"),)
        )
        library.symbols["Rule6.28-OtherThanMain"] = LibrarySymbol(
            name="Rule6.28-OtherThanMain", reference_prefix="DOT", pins=(SymbolPin("1", "To", "passive"),)
        )
        library.symbols["Track Circuit"] = LibrarySymbol(
            name="Track Circuit", reference_prefix="TC", pins=(SymbolPin("1", "To", "passive"),)
        )
        library.symbols["IRJ"] = _irj_symbol()
        library.symbols["IRJ-Signal"] = LibrarySymbol(
            name="IRJ-Signal", reference_prefix="B",
            pins=(SymbolPin("1", "A", "bidirectional"), SymbolPin("2", "B", "bidirectional"), SymbolPin("3", "SIGNAL", "passive")),
        )
        library.symbols["Bumper"] = LibrarySymbol(
            name="Bumper", reference_prefix="B", pins=(SymbolPin("2", "B", "passive"),)
        )
        library.symbols["Mast_Single"] = LibrarySymbol(
            name="Mast_Single", reference_prefix="S", pins=(SymbolPin("1", "SIGNAL", "passive"), SymbolPin("2", "H", "passive")),
        )
        library.symbols["Signal Head - CL"] = LibrarySymbol(
            name="Signal Head - CL", reference_prefix="H", pins=(SymbolPin("1", "M", "passive"),)
        )
        netlist = NetlistModel(path=Path("x.net"))
        netlist.components = {
            "CP_W": NetlistComponent("CP_W", "CP West", "Railroad", "NextCP"),
            "DOT_W": NetlistComponent("DOT_W", "MT", "Railroad", "Rule261-DoT-BiDirectional", fields={"Rulebook": "261", "Direction": "BOTH"}),
            "TC_W": NetlistComponent("TC_W", "MT", "Railroad", "Track Circuit"),
            "TC_LOCAL": NetlistComponent("TC_LOCAL", "LOCAL", "Railroad", "Track Circuit"),
            "DOT_DARK": NetlistComponent("DOT_DARK", "Industry", "Railroad", "Rule6.28-OtherThanMain", fields={"Rulebook": "Rule 6.28", "Direction": "BOTH"}),
            "B1": NetlistComponent("B1", "~", "Railroad", "IRJ-Signal"),
            "B2": NetlistComponent("B2", "~", "Railroad", "IRJ"),
            "BUMP": NetlistComponent("BUMP", "~", "Railroad", "Bumper"),
            "S2E1": NetlistComponent("S2E1", "2EA", "Railroad", "Mast_Single"),
            "H1": NetlistComponent("H1", "A", "Railroad", "Signal Head - CL"),
        }
        netlist.nets = [
            Net("1", "Net-(APP)", (NetNode("CP_W", "1"), NetNode("DOT_W", "1"), NetNode("TC_W", "1"), NetNode("B1", "2"))),
            Net("2", "Net-(LOCAL)", (NetNode("B1", "1"), NetNode("B2", "1"), NetNode("TC_LOCAL", "1"))),
            Net("3", "Net-(DARK)", (NetNode("B2", "2"), NetNode("DOT_DARK", "1"), NetNode("BUMP", "2"))),
            Net("4", "Net-(SIG)", (NetNode("B1", "3"), NetNode("S2E1", "1"))),
            Net("5", "Net-(HEAD)", (NetNode("S2E1", "2"), NetNode("H1", "1"))),
        ]
        graph = PlantGraphCompiler().compile(library, netlist)
        route = next(route for route in graph.routes if route.mast_name == "2EA")
        self.assertEqual(route.end_kind, RouteEndKind.DARK_EXIT)
        self.assertEqual(route.exit_designation, "Industry")
        self.assertEqual(route.exit_terminal, "B2")
        self.assertEqual(route.clear_track_circuits, ("LOCAL",))
        self.assertNotIn("Industry", route.path_track_circuits)

    def test_next_face_end_stops_at_same_direction_approach(self) -> None:
        """Two same-direction faces: route from first ends at second approach."""
        from plant_graph.types import RouteEndKind

        library = LibraryModel(path=Path("x.kicad_sym"))
        library.symbols["Direction_BOTH"] = _direction_symbol()
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
        library.symbols["Switch_Powered"] = LibrarySymbol(
            name="Switch_Powered",
            reference_prefix="SW",
            pins=(
                SymbolPin("1", "C", "passive"),
                SymbolPin("2", "N", "passive"),
                SymbolPin("3", "R", "passive"),
            ),
        )
        netlist = NetlistModel(path=Path("x.net"))
        netlist.components = {
            "DOT_W": NetlistComponent(
                "DOT_W", "WEST", "Railroad", "Direction_BOTH", fields={"Rulebook": "261"}
            ),
            "DOT_E": NetlistComponent(
                "DOT_E", "EAST", "Railroad", "Direction_BOTH", fields={"Rulebook": "261"}
            ),
            "B2": NetlistComponent("B2", "~", "Railroad", "IRJ-Signal"),
            "B4": NetlistComponent("B4", "~", "Railroad", "IRJ-Signal"),
            "SW1": NetlistComponent("SW1", "~", "Railroad", "Switch_Powered"),
            "S2S1": NetlistComponent("S2S1", "2SAB", "Railroad", "Mast_Single"),
            "S4S1": NetlistComponent("S4S1", "4SAB", "Railroad", "Mast_Single"),
        }
        netlist.nets = [
            Net("1", "/WEST", (NetNode("DOT_W", "2"), NetNode("B2", "2"))),
            Net("2", "Net-(B2-A)", (NetNode("B2", "1"), NetNode("SW1", "1"))),
            Net("3", "Net-(SW-N)", (NetNode("SW1", "2"), NetNode("B4", "1"))),
            Net("4", "/EAST", (NetNode("B4", "2"), NetNode("DOT_E", "1"))),
            Net("5", "Net-(SIG2)", (NetNode("B2", "3"), NetNode("S2S1", "1"))),
            Net("6", "Net-(SIG4)", (NetNode("B4", "3"), NetNode("S4S1", "1"))),
            Net(
                "7",
                "unconnected-(SW1-R)",
                (NetNode("SW1", "3", pintype="passive+no_connect"),),
            ),
        ]
        graph = PlantGraphCompiler().compile(library, netlist)
        face2 = [r for r in graph.routes if r.mast_name == "2SAB"]
        self.assertTrue(face2)
        self.assertTrue(
            any(
                r.end_kind is RouteEndKind.NEXT_FACE and r.exit_face_mast == "4SAB"
                for r in face2
            )
        )
        self.assertFalse(
            any(
                r.mast_name == "2SAB"
                and r.exit_designation == "EAST"
                and r.end_kind is RouteEndKind.CP_LIMIT
                for r in graph.routes
            )
        )


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
        self.assertIn("demand", text)
        self.assertNotIn("signal(lever)", text)
        self.assertIn("entrance", text)
        self.assertIn("home-clear", text)
        self.assertIn("downstream", text)
        self.assertIn("unresolved", text)


if __name__ == "__main__":
    unittest.main()
