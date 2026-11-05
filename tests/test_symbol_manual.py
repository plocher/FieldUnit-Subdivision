"""The symbols manual generator: what it reads from a library, group selection and the rule-link hook."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from contract.symbol_manual import Symbol, bare, link_cell, matches, symbol_html  # noqa: E402
from kicad_services.sch_text import library_fields  # noqa: E402

LIBRARY = """(kicad_symbol_lib
\t(symbol "Contact"
\t\t(property "Value" ""
\t\t\t(at 0 0 0)
\t\t)
\t\t(property "Role" "APPLIANCE"
\t\t\t(at 0 0 0)
\t\t\t(hide yes)
\t\t)
\t\t(property "Description" "A \\"dry\\" contact."
\t\t\t(at 0 0 0)
\t\t\t(hide yes)
\t\t)
\t)
)
"""


def contact() -> Symbol:
    return Symbol("Railroad-Trackplan", "Contact", "A contact.",
                  [("Value", "", False), ("Name", "${Value}", True), ("Role", "APPLIANCE", True), ("Appliance", "contact", True)],
                  [("~{TRACK}", "1", "", "passive", "")])


class LibraryFields(unittest.TestCase):
    def test_every_field_in_file_order_with_value_and_visibility(self):
        self.assertEqual(library_fields(LIBRARY)["Contact"],
                         [("Value", "", False), ("Role", "APPLIANCE", True), ("Description", 'A "dry" contact.', True)])


class Selection(unittest.TestCase):
    def test_a_selector_matches_on_fields_library_and_bare_pin_names(self):
        facts = contact().facts()
        self.assertTrue(matches({"Role": "APPLIANCE", "Appliance": ["lamp", "contact"]}, facts))
        self.assertTrue(matches({"library": "Railroad-Trackplan", "pin": "TRACK"}, facts))
        self.assertFalse(matches({"Role": "APPLIANCE", "Appliance": "lamp"}, facts))
        self.assertFalse(matches({"IC": "GPIO"}, facts))

    def test_bare_pin_name(self):
        self.assertEqual(bare("~{LAMP}"), "LAMP")
        self.assertEqual(bare("Column"), "Column")


class Page(unittest.TestCase):
    def test_who_sets_a_field(self):
        page = symbol_html(Symbol("L", "S", "", [("Value", "222", False), ("Name", "${Value}", True), ("TC", "", False)], []), [])
        rows = dict(r.split("</td><td>")[:2] for r in page.split("<tr id=")[1:])
        who = {k.split("<td>")[1]: ("you" in v) for k, v in rows.items()}
        self.assertEqual(who, {"Value": True, "Name": False, "TC": True})

    def test_a_binding_links_the_matching_pin_row_only(self):
        binding = {"match": {"Appliance": ["lamp", "contact"]}, "pin": "TRACK", "feature": "logical/x.feature#wired to track",
                   "href": "x.html"}
        self.assertIn('href="x.html"', link_cell(contact(), "pin", "TRACK", [binding]))
        self.assertEqual(link_cell(contact(), "field", "TRACK", [binding]), "")
        self.assertEqual(link_cell(contact(), "pin", "MC", [binding]), "")
        self.assertNotIn("<th>Rule</th>", symbol_html(contact(), []))
        self.assertIn("<th>Rule</th>", symbol_html(contact(), [binding]))


if __name__ == "__main__":
    unittest.main()
