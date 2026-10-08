"""Unit tests for the (Role, Kind) library lint (tools/contract/lint_libraries.py)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from contract.lint_libraries import lint, lint_keys  # noqa: E402

ROW = {"role": "DEVICE", "kind": "DETECTOR_OPTICAL", "block": "x", "symbols": ["L:Det"],
       "pins": {"OCC": "BIT out"}, "attributes": {"Hold_ms": "hold"}}


def sym(role="DEVICE", kind="DETECTOR_OPTICAL", pins=(("~{OCC}", "1", "output"),), **props):
    return {"properties": {"Role": role, "Kind": kind, **props}, "pins": list(pins), "extends": None}


def errors(findings):
    return [f.message for f in findings if f.severity == "error"]


class LintTests(unittest.TestCase):
    def test_conforming_symbol_is_clean(self):
        self.assertEqual(errors(lint({"row": [ROW]}, {"L:Det": sym(OCC="", Hold_ms="1500")})), [])

    def test_kind_mismatch_and_unlisted_symbol(self):
        found = errors(lint({"row": [ROW]}, {"L:Det": sym(kind="TRACK_CIRCUIT", OCC="", Hold_ms=""),
                                             "L:Other": sym(OCC="")}))
        self.assertTrue(any("!= table DEVICE/DETECTOR_OPTICAL" in m for m in found))
        self.assertTrue(any("not in the table" in m for m in found))

    def test_bit_pin_needs_its_polarity_attribute(self):
        found = errors(lint({"row": [ROW]}, {"L:Det": sym(Hold_ms="")}))
        self.assertEqual(found, ["BIT pin OCC has no polarity attribute OCC= (D6)"])

    def test_level_pin_must_not_carry_polarity(self):
        row = {**ROW, "kind": "HEAD_3LED_MUX2", "pins": {"S0": "LEVEL in"}, "attributes": {}}
        found = errors(lint({"row": [row]}, {"L:Det": sym(kind="HEAD_3LED_MUX2", pins=(("S0", "1", "input"),),
                                                          S0="")}))
        self.assertIn("LEVEL pin S0 carries a polarity attribute", found)

    def test_duplicate_pin_only_as_panel_two_state_token(self):
        row = {"role": "PANEL", "kind": "LOCK_LEVER_2LAMP_2CONTACT", "symbols": ["L:Det"],
               "pins": {"WLS": "BIT out"}}
        two = (("WLS", "1", "output"), ("~{WLS}", "2", "output"))
        self.assertEqual(errors(lint({"row": [row]}, {"L:Det": sym("PANEL", row["kind"], two, WLS="")})), [])
        device = {**row, "role": "DEVICE"}
        found = errors(lint({"row": [device]}, {"L:Det": sym("DEVICE", row["kind"], two, WLS="")}))
        self.assertTrue(any("appears 2 times" in m for m in found))

    def test_packaging_and_membership_pins_are_optional(self):
        row = {**ROW, "packaging": {"X": "BIT out"}, "membership": {"Column": "COLUMN"}}
        plain = sym(OCC="", Hold_ms="")
        full = sym(pins=(("~{OCC}", "1", "output"), ("~{X}", "2", "output"), ("Column", "3", "passive")),
                   OCC="", X="", Hold_ms="")
        self.assertEqual(errors(lint({"row": [row]}, {"L:Det": plain})), [])
        self.assertEqual(errors(lint({"row": [row]}, {"L:Det": full})), [])

    def test_unknown_attribute_and_role(self):
        row = {**ROW, "role": "COMPONENT"}
        found = errors(lint({"row": [row]}, {"L:Det": sym("COMPONENT", OCC="", Hold_ms="", Polarity="!OCC")}))
        self.assertTrue(any("naming axiom 4" in m for m in found))
        self.assertTrue(any("attribute Polarity" in m for m in found))


class DirectionTests(unittest.TestCase):
    def test_pin_type_must_match_the_direction(self):
        found = errors(lint({"row": [ROW]}, {"L:Det": sym(pins=(("~{OCC}", "1", "input"),), OCC="", Hold_ms="")}))
        self.assertTrue(any("pin ~{OCC} is input; DEVICE/DETECTOR_OPTICAL says output" in m for m in found))

    def test_token_pins_follow_their_suffix(self):
        row = {"role": "PANEL", "kind": "SWITCH_LEVER", "symbols": ["L:Lev"],
               "pins": {"NWS": "BIT in", "NWK": "BIT in"}}
        found = errors(lint({"row": [row]}, {}))
        self.assertTrue(any("pin NWS: a ...S token pin drives its line (out)" in m for m in found))
        self.assertFalse(any("pin NWK" in m for m in found))

    def test_device_pins_need_a_direction(self):
        row = {**ROW, "pins": {"OCC": "BIT"}}
        self.assertTrue(any("pin OCC: no direction" in m for m in errors(lint({"row": [row]}, {}))))


KEYS = {"namespace": {"timing": "durations"},
        "key": [{"key": "timing.hold_ms", "type": "ms", "levels": ["drawing", "layout"], "attribute": "Hold_ms"}]}
DELIVERED = {**ROW, "delivery": {"class": "OpticalDetectorDriver", "family": "DETECTOR",
                                 "implements": "ApplianceDriver"}}


class DeliveryAndKeyTests(unittest.TestCase):
    def test_device_row_with_seam_and_registered_key_is_clean(self):
        self.assertEqual(errors(lint({"row": [DELIVERED]}, {"L:Det": sym(OCC="", Hold_ms="")}, KEYS)), [])

    def test_family_must_match_the_kind(self):
        row = {**DELIVERED, "delivery": {**DELIVERED["delivery"], "family": "HEAD"}}
        found = errors(lint({"row": [row]}, {"L:Det": sym(OCC="", Hold_ms="")}, KEYS))
        self.assertIn("family HEAD is not the Kind's family DETECTOR", found)

    def test_device_attribute_needs_a_home(self):
        row = {**DELIVERED, "attributes": {"Hold_ms": "hold", "Mystery": "?"}}
        found = errors(lint({"row": [row]}, {"L:Det": sym(OCC="", Hold_ms="", Mystery="")}, KEYS))
        self.assertTrue(any("attribute Mystery must be exactly one of" in m for m in found))

    def test_key_registry_rules(self):
        bad = {"namespace": {"timing": ""}, "key": [
            {"key": "timing.a", "levels": ["drawing"], "attribute": "A"},
            {"key": "timing.a", "levels": ["drawing"]},
            {"key": "colour.b", "levels": ["layout"], "attribute": "A"},
            {"key": "timing.c", "levels": ["somewhere"]}]}
        found = [f.message for f in lint_keys(bad)[0]]
        self.assertIn("duplicate key", found)
        self.assertIn("namespace is not declared in [namespace]", found)
        self.assertTrue(any("already sets timing.a" in m for m in found))
        self.assertTrue(any("drawing is not a level" in m for m in found))
        self.assertTrue(any("not within" in m for m in found))


if __name__ == "__main__":
    unittest.main()
