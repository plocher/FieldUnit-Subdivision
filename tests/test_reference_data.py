"""The reference data files (ADR 0012 §6; issue #134): every table under ``schemas/layout-model/reference/`` validates
against the schema beside it, carries its name, schema version and provenance date, is named in what a layout file's
``provenance.referenceData`` states, and ``tools/layout_model/reference.py`` holds no table literal. Then the per-entity
resolution (``reference_data.py``): the selection stated in the file, the rows resolved onto faces, positions, drivers
and code lines, and the user's tables and the explicit overrides."""
from __future__ import annotations

import ast
import json
import unittest

import jsonschema

from tools.layout_model import derive, reference, reference_data

TABLES = {"aspectNames", "codeLineCapacity", "codeLineSteps", "driverEncodings", "encodingTransportPairing", "headModels",
          "indicationTokens", "permissiveness", "policies", "regimes", "stations", "trainOrderInputs"}


class Files(unittest.TestCase):
    def test_every_table_has_a_schema_beside_it_and_validates(self):
        self.assertEqual(set(reference.tables()), TABLES)
        for t in reference.tables():
            with self.subTest(t):
                self.assertTrue(reference.schema_path(t).is_file(), f"{t}: no schema beside it")
                schema = json.loads(reference.schema_path(t).read_text(encoding="utf-8"))
                jsonschema.Draft202012Validator.check_schema(schema)
                errors = sorted(e.message for e in jsonschema.Draft202012Validator(schema).iter_errors(reference.load(t)))
                self.assertEqual(errors, [])

    def test_every_table_names_itself_its_schema_version_and_its_provenance_date(self):
        for t in reference.tables():
            doc = reference.load(t)
            self.assertEqual(doc["table"], t)
            self.assertEqual(doc["schemaVersion"], 0, f"{t}: no bump rules until the KiCad importer and FieldUnit work end to end")
            self.assertRegex(doc["version"], r"^\d{4}-\d{2}-\d{2}(\.\d+)?$")
            self.assertTrue(doc["provenance"].strip())

    def test_provenance_names_each_tables_file_and_version(self):
        prov = reference.provenance()
        self.assertEqual(set(prov), TABLES)
        for t, entry in prov.items():
            self.assertEqual(entry, {"file": f"layout-model/reference/{t}.json", "version": reference.load(t)["version"], "schemaVersion": 0})
            self.assertTrue((reference.FOLDER.parents[1] / entry["file"]).is_file())

    def test_the_loader_holds_no_table_literal(self):
        """A dict literal with a key, or a list, tuple or set literal of two or more elements, anywhere in reference.py is a
        table that belongs in a data file."""
        tree = ast.parse(reference.__file__ and open(reference.__file__, encoding="utf-8").read())
        literals = [n for n in ast.walk(tree) if (isinstance(n, ast.Dict) and any(isinstance(v, (ast.Constant, ast.Dict, ast.List, ast.Tuple)) for v in n.values))   # a dict of values, not a merge or a record built from lookups
                    or (isinstance(n, (ast.List, ast.Tuple, ast.Set)) and len(n.elts) > 1 and all(isinstance(e, ast.Constant) for e in n.elts))]
        self.assertEqual([ast.unparse(n) for n in literals], [])

    def test_the_tables_keep_the_rulings(self):
        """The rows moved from the literals unchanged: a few facts the owner ruled, read through the lookups."""
        self.assertEqual(reference.station_of("USS506"), "house")
        self.assertEqual(reference.station_of("AAR"), "interlocking")
        self.assertEqual(reference.indication_tokens("USS506")["lock"], ("{name}WLK", "{name}WLQK"))
        self.assertEqual(reference.TRANSPORT_OF_ENCODING["USS506"], "TIMECODE")
        self.assertEqual(reference.ENCODING_OF_IC, {"MQTT-JMRI": "JMRI"})
        self.assertEqual(reference.REGIMES[reference.CTC], "CTC")
        self.assertEqual(reference.regime_ceiling("GCOR_RULE_6_13"), "RESTRICTING")
        self.assertIsNone(reference.regime_ceiling(reference.CTC))
        self.assertEqual(reference.default_ceiling("industry"), "RESTRICTING")
        self.assertEqual(reference.default_ceiling("none"), "RESTRICTING")
        self.assertEqual(reference.least_permissive(["CLEAR", "RESTRICTING", "APPROACH"]), "RESTRICTING")
        self.assertEqual(reference.presents("TypeD"), ["STOP", "APPROACH", "ADVANCE_APPROACH", "CLEAR", "DARK"])
        self.assertEqual(reference.aspect_name("SPTCO-1969", "STOP", "PERMISSIVE"), "Stop and Proceed")
        self.assertEqual(reference.policy("GCOR"), None)
        self.assertEqual(reference.rows("policies"), {})


def model(**layout_given: str) -> dict:
    return {"schema": "layout-model/v3.4.0", "layout": {"name": "T", "given": {"Kind": "RAILROAD", **layout_given},
                                                        "codelines": {"L": {"given": {"Kind": "USS506"}}, "M": {"given": {"Kind": "AAR"}}}},
            "interlockings": {}, "provenance": {"sourceType": "test", "writer": {"name": "t", "version": "0"}}}


class Resolution(unittest.TestCase):
    def test_the_layout_states_its_selection_and_derives_the_row_each_table_resolved_to(self):
        out, _ = derive.derive(model(Railroad="Southern Pacific", Era="1960+", Rulebook="GCOR"))
        self.assertEqual(out["layout"]["given"]["Rulebook"], "GCOR")                      # stated, never copied
        self.assertEqual(out["layout"]["derived"]["reference"], {"trainOrderInputs": "default"})

    def test_a_rulebook_with_its_own_rows_resolves_to_them(self):
        user = {"trainOrderInputs": {"SP": {"inputs": [{"input": "STOP", "indication": "STOP"}], "rest": "CLEAR"}},
                "policies": {"SP": {"2": {"CLEAR": ["CLEAR", "STOP"], "STOP": ["STOP", "STOP"]}}}}
        out, _ = derive.derive(model(Rulebook="SP"), user)
        self.assertEqual(out["layout"]["derived"]["reference"], {"trainOrderInputs": "SP", "policies": "SP"})
        r = reference_data.Resolver(model(Rulebook="SP"), user)
        self.assertEqual(r.shows(2), [{"CLEAR": "CLEAR", "STOP": "STOP"}, {"CLEAR": "STOP", "STOP": "STOP"}])
        self.assertIsNone(r.shows(3))
        self.assertIsNone(reference_data.Resolver(model(Rulebook="GCOR"), user).shows(2))

    def test_a_code_line_derives_what_its_station_is_and_its_token_templates(self):
        out, _ = derive.derive(model())
        lines = out["layout"]["codelines"]
        self.assertEqual(lines["L"]["derived"]["station"], "house")
        self.assertEqual(lines["M"]["derived"]["station"], "interlocking")
        self.assertEqual(lines["L"]["derived"]["tokens"]["switch"], ["{name}NWK", "{name}RWK"])
        self.assertEqual(lines["M"]["derived"]["tokens"], lines["L"]["derived"]["tokens"])

    def test_a_face_resolves_its_ranked_inputs_rest_and_words_with_the_boards_overrides(self):
        r = reference_data.Resolver(model(Rulebook="GCOR"))
        self.assertEqual(r.train_order_face({"SLOW", "STOP"}, {}),
                         {"inputs": {"1": {"input": "STOP", "indication": "STOP"}, "2": {"input": "SLOW", "indication": "APPROACH"}},
                          "rest": "CLEAR", "indications": ["APPROACH", "CLEAR", "STOP"]})
        self.assertEqual(r.train_order_face({"SLOW"}, {"Rest": "APPROACH", "Shows.SLOW": "RESTRICTING"}),
                         {"inputs": {"1": {"input": "SLOW", "indication": "RESTRICTING"}}, "rest": "APPROACH", "indications": ["APPROACH", "RESTRICTING"]})
        self.assertEqual(r.train_order_face(set(), {}), {"rest": "CLEAR", "indications": ["CLEAR"]})      # no input: absent is absent

    def test_aspect_names_resolve_for_a_system_and_a_mast_kind(self):
        r = reference_data.Resolver(model())
        self.assertEqual(r.aspect_names("SPTCO-1969", "PERMISSIVE")["STOP"], "Stop and Proceed")
        self.assertEqual(r.aspect_names("basic", None)["STOP"], "Stop")
        self.assertNotIn("STOP", r.aspect_names("SPTCO-1969", None))               # a Kind-split row needs the Kind
        self.assertEqual(r.aspect_names("SP-1890", "CONTROLLED"), {})


if __name__ == "__main__":
    unittest.main()
