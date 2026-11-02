"""Code line capacity and steps reference data (ADR 0013 §11, §18.3): a station's need is counted in steps, not tokens."""
import unittest

from tools.layout_model.reference import REFERENCE_DATA, code_line_capacity, code_line_steps


class CodeLineCapacity(unittest.TestCase):
    def test_506_station_with_switch_signal_os_and_mcall_is_full(self):
        steps = code_line_steps("USS506")
        need = sum(steps[c]["indications"] for c in ("switch", "signal", "track_circuit", "maintainer_call"))
        self.assertEqual(need, code_line_capacity("USS506")["indications"])

    def test_a_signal_levers_three_controls_take_two_steps(self):
        self.assertEqual(code_line_steps("USS506")["signal"]["controls"], 2)

    def test_unknown_steps_are_none(self):
        self.assertIsNone(code_line_steps("USS506")["lock"]["controls"])
        self.assertIsNone(code_line_steps("GRS_H"))

    def test_506c_carries_35_indications(self):
        self.assertEqual(code_line_capacity("USS506C")["indications"], 35)

    def test_aar_has_no_limit(self):
        self.assertIsNone(code_line_capacity("AAR")["indications"])

    def test_trade_off_rows(self):
        self.assertEqual([o["controls"] for o in code_line_capacity("GRS_H")["options"]], [4, 5, 6])

    def test_unknown_is_none_and_user_row_wins(self):
        self.assertIsNone(code_line_capacity("BITS"))
        self.assertEqual(code_line_capacity("USS506", {"USS506": {"indications": 9}})["indications"], 9)

    def test_versioned(self):
        self.assertIn("codeLineCapacity", REFERENCE_DATA)
        self.assertIn("codeLineSteps", REFERENCE_DATA)


if __name__ == "__main__":
    unittest.main()
