"""The routes library (``tools/railroad/routes.py``, issue #139). The rules are its features
(``schemas/layout-model/rules/features/logical/trackplan/routes.feature``); these tests cover the implementation and
the sufficiency gate of ADR 0012 §5.5 over the SPCoast example, frozen from the KiCad importer's output."""
from __future__ import annotations

import ast
import copy
import json
import unittest
from pathlib import Path

from tools.railroad import routes

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "schemas" / "layout-model" / "examples" / "spcoast.layout.json"

# FieldUnit's six hand-walked Corporal routes (tools/layoutgen/handwritten/Corporal_routes.h, FieldUnit e0bf31e):
# mast, alignment, circuits it clears, entrance. The stand-in does not check Christopher's 1NAT or 2NAT, by design.
CORPORAL = [
    ("830NAB", [("829", "NORMAL"), ("827", "NORMAL")], ["829T1", "827T1"], "829T1"),
    ("830NAB", [("829", "REVERSE")], ["829T1"], "829T1"),
    ("830SAB", [("829", "REVERSE")], ["829T1", "832T"], "829T1"),
    ("828SA", [("827", "NORMAL"), ("829", "NORMAL")], ["827T1", "829T1", "832T"], "827T1"),
    ("828SA", [("827", "REVERSE"), ("827D", "REVERSE")], ["827T1", "01T"], "827T1"),
    ("828NA", [("827", "REVERSE"), ("827D", "REVERSE")], ["827T1"], "827T1"),
]

# Luchessa's ten structural routes (ADR 0012 §9; FieldUnit docs/CTC_SUBDIVISION_AND_PLANT_DESIGN.md §8.1): by mast,
# the alignment of each.
LUCHESSA = {
    "784EAB": [{"783": "NORMAL", "795": "NORMAL", "799": "NORMAL"}, {"783": "NORMAL", "795": "NORMAL", "799": "REVERSE"},
               {"783": "REVERSE"}],
    "784EC": [{"795": "REVERSE", "795D": "REVERSE", "799": "NORMAL"}, {"795": "REVERSE", "795D": "REVERSE", "799": "REVERSE"}],
    "784WA": [{"783": "REVERSE"}],
    "784WBC": [{"783": "NORMAL", "795": "NORMAL", "799": "NORMAL"}, {"795": "REVERSE", "795D": "REVERSE", "799": "NORMAL"}],
    "784WD": [{"783": "NORMAL", "795": "NORMAL", "799": "REVERSE"}, {"795": "REVERSE", "795D": "REVERSE", "799": "REVERSE"}],
}


def bare(name: str, scope: str) -> str:
    b, _, n = name.partition(":")
    return n if b == scope else name


class Sufficiency(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        cls.found = routes.find(cls.model)

    def test_every_finding_is_missing_never_an_error(self):
        self.assertEqual({d.severity for d in self.found.report.diags} - {"missing"}, set())

    def test_every_controlled_mast_of_every_interlocking_has_a_route(self):
        for b, ix in self.model["interlockings"].items():
            for n, a in ix["appliances"].items():
                if a["given"].get("Appliance") == "mast" and a["given"].get("Kind") == "CONTROLLED":
                    self.assertTrue(self.found.of(f"{b}:{n}"), f"{b}:{n}")

    def test_corporal_matches_the_hand_walked_routes_in_alignment_circuits_and_entrance(self):
        got = sorted((bare(r.mast, "Corporal"), sorted((bare(s, "Corporal"), p) for s, p in r.alignment),
                      [bare(c, "Corporal") for c in r.circuits if c.startswith("Corporal:")], bare(r.entrance, "Corporal"))
                     for m, rs in self.found.routes.items() if m.startswith("Corporal:") for r in rs)
        want = sorted((m, sorted(a), c, e) for m, a, c, e in CORPORAL)
        self.assertEqual(got, want)

    def test_luchessa_has_its_ten_structural_routes(self):
        got = {bare(m, "Luchessa"): sorted((sorted({bare(s, "Luchessa"): p for s, p in r.alignment}.items()) for r in rs))
               for m, rs in self.found.routes.items() if m.startswith("Luchessa:")}
        want = {m: sorted(sorted(a.items()) for a in alignments) for m, alignments in LUCHESSA.items()}
        self.assertEqual(got, want)

    def test_a_route_of_830nab_states_every_term(self):
        r = next(r for r in self.found.of("Corporal:830NAB") if r.alignment == [("Corporal:829", "NORMAL"), ("Corporal:827", "NORMAL")])
        self.assertEqual(r.as_dict(), {
            "mast": "Corporal:830NAB", "demand": "830(LEFT)",
            "alignment": [{"appliance": "Corporal:829", "position": "NORMAL"}, {"appliance": "Corporal:827", "position": "NORMAL"}],
            "circuits": ["Corporal:829T1", "Corporal:827T1", "Christopher:2NAT"], "entrance": "Corporal:829T1",
            "approach": "Corporal:832T", "end": {"mast": "Christopher:816NAB", "demand": "Christopher:816(LEFT)"},
            "opposing": [{"mast": "Corporal:828SA", "demand": "828(RIGHT)"}], "ceiling": "CLEAR"})

    def test_the_library_writes_nothing_into_the_file(self):
        before = copy.deepcopy(self.model)
        routes.find(self.model)
        self.assertEqual(self.model, before)


class Boundaries(unittest.TestCase):
    def test_the_domain_libraries_do_not_import_the_importer(self):
        for path in (ROOT / "tools" / "railroad").glob("*.py"):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                names = [a.name for a in node.names] if isinstance(node, ast.Import) else \
                    [node.module or ""] if isinstance(node, ast.ImportFrom) else []
                self.assertFalse(any("layout_compiler" in n for n in names), path.name)

    def test_ceilings_that_differ_state_no_single_ceiling(self):
        r = routes.Route("X:1NA", ceilings=[{"appliance": "X:1", "position": "REVERSE", "word": "APPROACH"},
                                            {"appliance": "X:3", "position": "REVERSE", "word": "RESTRICTING"}])
        self.assertIsNone(r.ceiling)
        self.assertNotIn("ceiling", r.as_dict())
        self.assertEqual(len(r.as_dict()["ceilings"]), 2)


if __name__ == "__main__":
    unittest.main()
