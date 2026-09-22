"""Tests for the portable-to-FieldUnit projection module."""

from __future__ import annotations

import json
import sys
import unittest
from dataclasses import replace
from io import StringIO
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "kicad"

if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from kicad_services.netlist_reader import NetlistReader
from kicad_services.symbol_library_reader import SymbolLibraryReader
from kicad_services.types import LibrarySymbol, NetlistComponent, SymbolPin
from plant_graph.compiler import PlantGraphCompiler
from plant_graph.fieldunit_projection import (
    project_fieldunit_json,
    project_fieldunit_plant,
)
from plant_graph.model import (
    compile_interlocking_plant_model,
    validate_interlocking_plant_model,
)
from plant_graph.types import PlantEntity, EntityKind
import parse_kicad_plant


class FieldUnitProjectionTests(unittest.TestCase):
    """Projection from the portable model into FieldUnit PlantSerializer JSON."""

    def setUp(self) -> None:
        self.library = SymbolLibraryReader().read(
            FIXTURES / "minimal_railroad.kicad_sym"
        )
        self.netlist = NetlistReader().read(FIXTURES / "minimal_plant.net")

    def _model(self) -> dict:
        graph = PlantGraphCompiler().compile(self.library, self.netlist)
        return compile_interlocking_plant_model(
            graph,
            plant_name="Fixture Plant",
            plant_id="fixture-plant",
        ).to_dict()

    def test_projects_one_complete_interlocking_plant(self) -> None:
        projected = project_fieldunit_plant(self._model())

        self.assertEqual(projected["name"], "Fixture Plant")
        self.assertEqual(
            projected["switches"],
            [{"name": "783", "os": "783T1"}],
        )
        self.assertEqual(projected["derails"], [])
        self.assertEqual(projected["trackCircuits"], [{"name": "783T1"}])
        self.assertEqual(projected["crossovers"], [])
        self.assertEqual(projected["projectionDeferred"]["controlledPoints"], [])
        self.assertEqual(projected["projectionDeferred"]["derails"], [])
        self.assertIn("segments", projected["projectionDeferred"]["topology"])

    def test_projects_route_with_revised_fieldunit_vocabulary(self) -> None:
        model = self._model()
        model["routes"] = [
            {
                "id": "mt-industry",
                "name": "MT-Industry",
                "signal": "784",
                "mast": "784SAB",
                "direction": "LEFT",
                "alignments": [
                    {"appliance": "783", "position": "NORMAL"},
                ],
                "clearTrackCircuits": ["783T1"],
                "staticIndication": "CLEAR",
                "entrance": None,
                "approaching": None,
                "entryTerminal": None,
                "exitTerminal": None,
                "endKind": "dead_end",
                "exitFace": None,
            }
        ]
        projected = project_fieldunit_plant(model)

        self.assertEqual(len(projected["routes"]), 1)
        route = projected["routes"][0]
        self.assertEqual(
            route["governedBy"], {"signal": "784", "direction": "LEFT"}
        )
        self.assertEqual(route["displays"]["mast"], "784SAB")
        self.assertIn("maxIndication", route["displays"])
        self.assertEqual(
            route["aligns"], [{"switch": "783", "position": "NORMAL"}]
        )
        self.assertEqual(route["clears"], ["783T1"])
        self.assertNotIn("headIndex", route["displays"])
        model["routes"][0]["staticIndication"] = "ADVANCED_APPROACH"
        self.assertEqual(
            project_fieldunit_plant(model)["routes"][0]["displays"][
                "maxIndication"
            ],
            "ADVANCE_APPROACH",
        )
        model["routes"][0]["staticIndication"] = "SECONDARY_DIVERGING_CLEAR"
        with self.assertRaises(ValueError):
            project_fieldunit_plant(model)

    def test_projects_dependent_derail_natively_without_route_align(self) -> None:
        self.library.symbols["Switch_Powered_Derail"] = LibrarySymbol(
            name="Switch_Powered_Derail",
            reference_prefix="DERAIL",
            pins=(
                SymbolPin("1", "C", "passive"),
                SymbolPin("2", "N", "passive"),
            ),
        )
        self.netlist.components["DERAIL783"] = NetlistComponent(
            "DERAIL783",
            "783D",
            "Railroad",
            "Switch_Powered_Derail",
            fields={"CP": "CP Fixture"},
        )
        graph = PlantGraphCompiler().compile(self.library, self.netlist)
        model = compile_interlocking_plant_model(
            graph,
            plant_name="Fixture Plant",
            plant_id="fixture-plant",
        ).to_dict()
        model["routes"] = [
            {
                "id": "industry",
                "name": "Industry",
                "signal": "784",
                "mast": model["appliances"]["masts"][0]["id"],
                "direction": model["appliances"]["masts"][0]["direction"],
                "alignments": [
                    {"appliance": "783", "position": "REVERSE"},
                    {"appliance": "783D", "position": "NORMAL"},
                ],
                "clearTrackCircuits": ["783T1"],
                "staticIndication": "CLEAR",
                "entrance": None,
                "approaching": None,
                "entryTerminal": None,
                "exitTerminal": None,
                "endKind": "dead_end",
                "exitFace": None,
            }
        ]

        projected = project_fieldunit_plant(model)

        self.assertEqual(projected["derails"], [{"name": "783D"}])
        self.assertNotIn({"name": "783D"}, projected["switches"])
        self.assertEqual(
            projected["routes"][0]["aligns"],
            [{"switch": "783", "position": "REVERSE"}],
        )
        self.assertEqual(
            projected["projectionDeferred"]["derails"],
            [
                {
                    "id": "783D",
                    "controlMode": "dependent",
                    "controllingSwitch": "783",
                    "trackCircuit": None,
                }
            ],
        )

    def test_projects_independent_dispatcher_derail_with_os(self) -> None:
        model = self._model()
        model["appliances"]["derails"] = [
            {
                "id": "5",
                "controlMode": "dispatcher",
                "controllingSwitch": None,
                "trackCircuit": "5T1",
            }
        ]
        model["appliances"]["trackCircuits"].append({"id": "5T1"})

        projected = project_fieldunit_plant(model)

        self.assertEqual(
            projected["derails"],
            [{"name": "5", "os": "5T1"}],
        )
        self.assertEqual(
            projected["switches"],
            [{"name": "783", "os": "783T1"}],
        )

    def test_projects_controlled_points_as_deferred_binding(self) -> None:
        graph = PlantGraphCompiler().compile(self.library, self.netlist)
        graph.entities["HOUSE1"] = PlantEntity(
            reference="HOUSE1",
            kind=EntityKind.MAIN_HOUSE,
            lib_id="Railroad:MAIN HOUSE",
            value="CP Fixture",
            canonical_name="CP Fixture",
        )
        graph.entities["SW783"].fields["CP"] = "CP Fixture"
        model = compile_interlocking_plant_model(
            graph,
            plant_name="Fixture Plant",
            plant_id="fixture-plant",
        ).to_dict()

        projected = project_fieldunit_plant(model)

        controlled_points = projected["projectionDeferred"]["controlledPoints"]
        self.assertEqual(len(controlled_points), 1)
        self.assertEqual(controlled_points[0]["id"], "CP Fixture")
        self.assertIn(
            {"kind": "switch", "id": "783"}, controlled_points[0]["members"]
        )
        self.assertNotIn("controlledPoints", projected)

    def test_project_fieldunit_json_round_trips_through_json_loads(self) -> None:
        rendered = project_fieldunit_json(self._model())

        parsed = json.loads(rendered)

        self.assertEqual(parsed["name"], "Fixture Plant")
        self.assertEqual(
            parsed["projectionDeferred"]["document"],
            self._model()["document"],
        )
        self.assertEqual(
            parsed["projectionDeferred"]["profile"],
            self._model()["profile"],
        )
        self.assertTrue(rendered.endswith("\n"))
    def test_projects_dwarf_mast_by_kind_not_head_count(self) -> None:
        model = self._model()
        model["appliances"]["masts"][0]["kind"] = "dwarf"

        projected = project_fieldunit_plant(model)

        self.assertEqual(projected["signalMasts"][0]["type"], "DWARF")

    def test_rejects_mast_with_unsupported_head_count(self) -> None:
        model = self._model()
        model["appliances"]["masts"][0]["heads"] = ["A", "B", "C", "D"]

        with self.assertRaises(ValueError):
            project_fieldunit_plant(model)

    def test_portable_validation_rejects_route_mast_mismatch(self) -> None:
        model = self._model()
        model["routes"] = [
            {
                "id": "bad-route",
                "name": "Bad Route",
                "signal": "784",
                "mast": "784SAB",
                "direction": "LEFT",
                "alignments": [],
                "clearTrackCircuits": [],
                "staticIndication": "CLEAR",
                "entrance": None,
                "approaching": None,
                "entryTerminal": None,
                "exitTerminal": None,
                "endKind": "dead_end",
                "exitFace": None,
            }
        ]
        portable = compile_interlocking_plant_model(
            PlantGraphCompiler().compile(self.library, self.netlist),
            plant_name="Fixture Plant",
            plant_id="fixture-plant",
        )
        invalid_model = replace(portable, routes=tuple(model["routes"]))

        self.assertIn(
            "route_mast_binding_mismatch:bad-route:784SAB",
            validate_interlocking_plant_model(invalid_model),
        )
    def test_cli_exports_validated_fieldunit_json(self) -> None:
        graph = PlantGraphCompiler().compile(self.library, self.netlist)
        graph.diagnostics.clear()
        stdout = StringIO()
        argv = [
            "--library",
            str(FIXTURES / "minimal_railroad.kicad_sym"),
            "--netlist",
            str(FIXTURES / "minimal_plant.net"),
            "--format",
            "fieldunit-json",
            "--plant-name",
            "Fixture Plant",
        ]

        with mock.patch.object(
            parse_kicad_plant,
            "load_graph",
            return_value=graph,
        ), mock.patch("sys.stdout", stdout):
            self.assertEqual(parse_kicad_plant.main(argv), 0)

        projected = json.loads(stdout.getvalue())
        self.assertEqual(projected["name"], "Fixture Plant")
        self.assertIn("projectionDeferred", projected)

    def test_schema_matches_emitted_mast_and_route_contract(self) -> None:
        schema_path = ROOT / "schemas" / "interlocking-plant" / "v1.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        mast_schema = schema["$defs"]["mast"]
        route_schema = schema["$defs"]["route"]
        mast = self._model()["appliances"]["masts"][0]

        self.assertTrue(set(mast_schema["required"]) <= set(mast_schema["properties"]))
        self.assertEqual(set(mast), set(mast_schema["required"]))
        self.assertNotIn("heads", route_schema["required"])
        self.assertNotIn("heads", route_schema["properties"])


if __name__ == "__main__":
    unittest.main()
