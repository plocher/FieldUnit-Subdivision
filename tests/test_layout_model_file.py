"""Gates for the Layout Data Model File (ADR 0008, ADR 0011): schema (DoD3), canonical round trip (DoD1), identity rules
(§4.5), the three maps (ADR 0011 §2) and geometry's identity contract (three-maps D10)."""
import copy
import json
import unittest
from pathlib import Path

from tools import layout_model

EXAMPLE = Path(__file__).resolve().parents[1] / "schemas" / "layout-model" / "examples" / "spcoast.layout.json"


class LayoutModelFileTests(unittest.TestCase):
    def setUp(self):
        self.model = layout_model.read(EXAMPLE)

    def test_example_validates(self):
        self.assertEqual(layout_model.errors(self.model), [])

    def test_example_is_canonical_and_round_trips_byte_identical(self):
        text = EXAMPLE.read_text(encoding="utf-8")
        self.assertEqual(layout_model.dumps(layout_model.loads(text)), text)
        shuffled = json.loads(json.dumps(self.model))  # a fresh object, same facts
        shuffled["layout"]["processors"]["Sargent"]["drivers"] = dict(reversed(list(shuffled["layout"]["processors"]["Sargent"]["drivers"].items())))
        shuffled["interlockings"]["Sargent"]["devices"].reverse()
        self.assertEqual(layout_model.dumps(shuffled), text)

    def test_schema_string_is_the_version(self):
        self.assertEqual(self.model["schema"], layout_model.SCHEMA_ID)
        bad = copy.deepcopy(self.model)
        bad["schema"] = "layout-model/1"
        self.assertTrue(any(e.startswith("schema:") for e in layout_model.errors(bad)))

    def test_a_name_may_not_contain_a_colon(self):
        bad = copy.deepcopy(self.model)
        bad["interlockings"]["Gilroy:Caltrain"] = bad["interlockings"].pop("Gilroy Caltrain")
        self.assertTrue(layout_model.errors(bad))

    def test_a_reference_is_always_qualified(self):
        bad = copy.deepcopy(self.model)
        bad["interlockings"]["Sargent"]["devices"][0]["derived"]["serves"] = "835"
        self.assertTrue(any("serves" in e for e in layout_model.errors(bad)))
        bad = copy.deepcopy(self.model)
        bad["officeUnits"]["SPCoast South"]["devices"][0]["relations"]["column"] = "12"     # a column is qualified by its OfficeUnit (D19)
        self.assertTrue(any("column" in e for e in layout_model.errors(bad)))

    def test_a_device_row_has_no_identity(self):
        bad = copy.deepcopy(self.model)
        bad["interlockings"]["Sargent"]["devices"][0]["id"] = "dev-1"
        self.assertTrue(any("'id'" in e for e in layout_model.errors(bad)))

    def test_nothing_below_the_layout_carries_provenance_or_diagnostics(self):
        for key in ("source", "diagnostics", "sheet"):
            bad = copy.deepcopy(self.model)
            bad["interlockings"]["Sargent"][key] = {}
            self.assertTrue(layout_model.errors(bad), key)
        bad = copy.deepcopy(self.model)
        bad["diagnostics"] = []
        self.assertTrue(layout_model.errors(bad))

    def test_a_processor_is_a_layout_entity(self):
        bad = copy.deepcopy(self.model)
        bad["interlockings"]["Sargent"]["processors"] = {}
        self.assertTrue(any("processors" in e for e in layout_model.errors(bad)))

    def test_every_entity_holds_the_three_maps_and_nothing_flat(self):
        """ADR 0011 §2: settings and the typed copies of stated fields are gone; a drawn field lives in given only."""
        for path, key, value in ((("layout", "processors", "Sargent"), "board", "cpNode"),
                                 (("layout", "transports", "MQTT"), "settings", {"Broker": "x"}),
                                 (("interlockings", "Sargent", "houses", "Sargent"), "milepost", 83.0),
                                 (("interlockings", "Sargent", "appliances", "835"), "controlPoint", "Sargent:Sargent"),
                                 (("interlockings", "Sargent"), "fieldUnit", {"processor": "Sargent"})):
            bad = copy.deepcopy(self.model)
            node = bad
            for k in path:
                node = node[k]
            node[key] = value
            self.assertTrue(layout_model.errors(bad), (path, key))

    def test_given_holds_strings_as_drawn_and_never_housekeeping(self):
        for key, value in (("Value", "835"), ("Footprint", "x"), ("Role", "APPLIANCE"), ("Pin.C", "passive"), ("ki_keywords", "x"), ("Milepost", 83.4)):
            bad = copy.deepcopy(self.model)
            bad["interlockings"]["Sargent"]["appliances"]["835"]["given"][key] = value
            self.assertTrue(layout_model.errors(bad), key)
        bad = copy.deepcopy(self.model)
        bad["interlockings"]["Sargent"]["houses"]["Sargent"]["given"]["Milepost"] = "north"
        self.assertTrue(layout_model.errors(bad))

    def test_a_signal_joints_sides_are_approach_and_governed(self):
        joints = [j for j in self.model["interlockings"]["Sargent"]["track"]["joints"] if j["given"]["Kind"] == "IRJ_SIGNAL"]
        self.assertEqual({side for j in joints for side in j["derived"]["circuits"]}, {"approach", "governed"})
        bad = copy.deepcopy(self.model)
        bad["interlockings"]["Sargent"]["track"]["joints"][0]["derived"]["ports"] = {"A": ["Sargent:835.C"]}
        self.assertTrue(layout_model.errors(bad))                                  # wires are relations, never derived (D5)

    def test_a_marker_names_its_row_by_id_and_copies_nothing(self):
        g = self.model["interlockings"]["Sargent"]["geometry"]
        ids = {r["id"] for k in ("joints", "ends", "policies", "consumers") for r in self.model["interlockings"]["Sargent"]["track"][k]}
        self.assertEqual({m["row"] for m in g["markers"]}, ids)
        for key, value in (("kind", "IRJ"), ("circuits", {"A": "Sargent:1NAT"}), ("name", "Sargent:Cannery")):
            bad = copy.deepcopy(self.model)
            bad["interlockings"]["Sargent"]["geometry"]["markers"][0][key] = value
            self.assertTrue(layout_model.errors(bad), key)
        bad = copy.deepcopy(self.model)
        del bad["interlockings"]["Sargent"]["geometry"]["markers"][0]["row"]
        self.assertTrue(layout_model.errors(bad))

    def test_a_runs_ends_are_relations_and_its_circuit_derived(self):
        runs = self.model["interlockings"]["Luchessa"]["geometry"]["track"]
        self.assertTrue(all("from" in t["relations"] or "to" in t["relations"] for t in runs))
        bad = copy.deepcopy(self.model)
        bad["interlockings"]["Luchessa"]["geometry"]["track"][0]["circuit"] = "Luchessa:1NAT"
        self.assertTrue(layout_model.errors(bad))
        bad = copy.deepcopy(self.model)
        bad["interlockings"]["Luchessa"]["geometry"]["track"][0]["relations"]["to"] = "somewhere"
        self.assertTrue(layout_model.errors(bad))

    def test_a_consumer_row_consumes_an_indication_and_a_house_sends_its_own(self):
        """The owner, 2026-10-27: a reference to another interlocking's circuit is a consumer of its indication."""
        consumer = self.model["interlockings"]["Sargent"]["track"]["consumers"][0]
        self.assertEqual(consumer["relations"]["indication"], "Corporal:2NATK")
        self.assertIn("2NATK", self.model["interlockings"]["Corporal"]["houses"]["Corporal"]["derived"]["indications"])
        for key, value in (("indication", "Corporal:2NAT"), ("indication", "2NATK"), ("mast", "Sargent:836NAB")):
            bad = copy.deepcopy(self.model)
            bad["interlockings"]["Sargent"]["track"]["consumers"][0]["relations"][key] = value
            self.assertTrue(layout_model.errors(bad), (key, value))
        bad = copy.deepcopy(self.model)
        bad["interlockings"]["Corporal"]["houses"]["Corporal"]["derived"]["indications"].append("Sargent:2NATK")
        self.assertTrue(layout_model.errors(bad))

    def test_provenance_names_its_writer_and_rules(self):
        self.assertEqual(self.model["provenance"]["writer"]["name"], "layout_compiler")
        self.assertEqual(self.model["provenance"]["rules"], "0.1.0")
        bad = copy.deepcopy(self.model)
        bad["provenance"]["compiler"] = bad["provenance"].pop("writer")
        self.assertTrue(layout_model.errors(bad))

    def test_natural_case_folded_order(self):
        names = ["Track 10", "track 2", "CP Gilroy", "cp  Carnadero", "13", "2"]
        self.assertEqual(sorted(names, key=layout_model.sort_key), ["2", "13", "cp  Carnadero", "CP Gilroy", "track 2", "Track 10"])

    def test_absent_is_absent(self):
        bare = {"schema": layout_model.SCHEMA_ID, "layout": {"name": "X"}, "interlockings": {"Y": {}}}
        self.assertEqual(layout_model.errors(bare), [])


if __name__ == "__main__":
    unittest.main()
