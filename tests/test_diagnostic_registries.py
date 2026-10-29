"""The two registries of ADR 0012 §3.3, each checked against its own raisers. Rule checks (the reference derivation and
the domain libraries) are registered with the schema; import diagnostics (the KiCad importer) in
``tools/layout_compiler/diagnostics.json``. Every raised code is registered in its raiser's registry, at the level it is
raised; every active code is raised; no code is in both."""
from __future__ import annotations

import unittest
from pathlib import Path

import tools.layout_compiler as importer
from tests import raised_codes
from tools.layout_model import derive

ROOT = Path(__file__).resolve().parents[1]
LEVELS = ("error", "warning", "info", "missing")


def rule_raised() -> set[str]:
    return raised_codes.rule_codes(*(ROOT / "tools" / "layout_model").glob("*.py"), *(ROOT / "tools" / "railroad").glob("*.py"))


def import_raised() -> dict[str, set[str]]:
    out = raised_codes.import_codes(ROOT / "tools" / "layout_compiler")
    out.update(raised_codes.key_codes())
    return out


class Registries(unittest.TestCase):
    def test_every_entry_has_a_level_and_a_lower_case_code(self):
        for reg in (derive.registry(), importer.registry()):
            for code, entry in reg.items():
                self.assertIn(entry["level"], LEVELS, code)
                self.assertIn(entry["lifecycle"], ("proposed", "active", "deprecated", "retired"), code)
                self.assertEqual(code, code.lower())

    def test_every_rule_check_raised_is_registered_and_every_active_one_raised(self):
        raised = rule_raised()
        self.assertNotIn(None, raised, "a rule check whose code is not a literal")
        self.assertEqual(sorted(raised - set(derive.registry())), [])
        self.assertEqual(sorted(c for c, e in derive.registry().items() if e["lifecycle"] == "active" and c not in raised), [])

    def test_every_import_diagnostic_raised_is_registered_at_its_level_and_every_active_one_raised(self):
        raised, reg = import_raised(), importer.registry()
        self.assertNotIn(None, raised, "an import diagnostic whose code is not a literal")
        self.assertEqual(sorted(set(raised) - set(reg)), [])
        self.assertEqual(sorted(c for c, e in reg.items() if e["lifecycle"] == "active" and c not in raised), [])
        self.assertEqual(sorted(c for c, levels in raised.items() if levels != {reg[c]["level"]}), [])  # one code, one level

    def test_no_code_is_both_a_rule_check_and_an_import_diagnostic(self):
        self.assertEqual(sorted(set(derive.registry()) & set(importer.registry())), [])
        self.assertEqual(sorted(rule_raised() & set(import_raised())), [])


if __name__ == "__main__":
    unittest.main()
