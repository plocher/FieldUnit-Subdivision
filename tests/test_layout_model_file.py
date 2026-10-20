"""Gates for the Layout Data Model File (ADR 0008): schema (DoD3), canonical round trip (DoD1), identity rules (§4.5)."""
import copy
import json
import unittest
from pathlib import Path

from tools import layout_model

EXAMPLE = Path(__file__).resolve().parents[1] / "schemas" / "layout-model" / "examples" / "spcoast-excerpt.json"


class LayoutModelFileTests(unittest.TestCase):
    def setUp(self):
        self.model = layout_model.read(EXAMPLE)

    def test_example_validates(self):
        self.assertEqual(layout_model.errors(self.model), [])

    def test_example_is_canonical_and_round_trips_byte_identical(self):
        text = EXAMPLE.read_text(encoding="utf-8")
        self.assertEqual(layout_model.dumps(layout_model.loads(text)), text)
        shuffled = json.loads(json.dumps(self.model))  # a fresh object, same facts
        shuffled["layout"]["processors"]["Sargent"]["chips"] = dict(reversed(list(shuffled["layout"]["processors"]["Sargent"]["chips"].items())))
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
        bad["interlockings"]["Sargent"]["devices"][0]["serves"] = "835"
        self.assertTrue(any("serves" in e for e in layout_model.errors(bad)))

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

    def test_natural_case_folded_order(self):
        names = ["Track 10", "track 2", "CP Gilroy", "cp  Carnadero", "13", "2"]
        self.assertEqual(sorted(names, key=layout_model.sort_key), ["2", "13", "cp  Carnadero", "CP Gilroy", "track 2", "Track 10"])

    def test_absent_is_absent(self):
        bare = {"schema": layout_model.SCHEMA_ID, "layout": {"name": "X"}, "interlockings": {"Y": {}}}
        self.assertEqual(layout_model.errors(bare), [])


if __name__ == "__main__":
    unittest.main()
