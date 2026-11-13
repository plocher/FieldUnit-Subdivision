"""Code line capacity and steps reference data (ADR 0013 §11, §21): a station's need is counted in steps, not tokens."""
import unittest

from tools.layout_model.reference import HEAD_MODELS, code_line_capacity, code_line_steps, head_model, policy, presents, provenance


class CodeLineCapacity(unittest.TestCase):
    def test_506_station_with_switch_signal_os_and_mcall_is_full(self):
        steps = code_line_steps("USS506")
        need = sum(steps[c]["indications"] for c in ("switch", "signal", "track_circuit", "maintainer_call"))
        self.assertEqual(need, code_line_capacity("USS506")["indications"])

    def test_a_signal_levers_three_controls_take_three_steps(self):
        self.assertEqual(code_line_steps("USS506")["signal"]["controls"], 3)

    def test_unknown_steps_are_none(self):
        self.assertIsNone(code_line_steps("GRS_H"))

    def test_an_electric_lock_lever_takes_one_control_step(self):
        self.assertEqual(code_line_steps("USS506")["lock"]["controls"], 1)

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
        self.assertIn("codeLineCapacity", provenance())
        self.assertIn("codeLineSteps", provenance())


if __name__ == "__main__":
    unittest.main()


class HeadModels(unittest.TestCase):
    """The head model table (#80): Style -> head word -> outputs; presents is the keys; a Style with no row is None."""

    def test_type_d_presents_the_seed_words_in_order(self):
        self.assertEqual(presents("TypeD"), ["STOP", "APPROACH", "ADVANCE_APPROACH", "CLEAR", "DARK"])
        self.assertEqual(head_model("TypeD")["STOP"], {"lamp": "R"})

    def test_the_semaphore_styles_name_their_arm_positions(self):
        self.assertEqual(presents("LQ2"), ["STOP", "CLEAR", "DARK"])
        self.assertEqual(presents("UQ3"), ["STOP", "APPROACH", "CLEAR", "DARK"])
        self.assertEqual(head_model("UQ3")["DARK"], {"arm": None, "lamp": "off"})

    def test_every_row_names_its_source_and_every_style_placed_has_a_row(self):
        self.assertEqual([s for s, row in HEAD_MODELS.items() if not row.get("source")], [])
        self.assertTrue({"TypeD", "SA", "H2", "LQ2", "LQ3", "UQ3"} <= set(HEAD_MODELS))

    def test_an_unknown_style_is_none_never_guessed_and_the_user_table_layers_over(self):
        self.assertIsNone(presents("CPL"))
        self.assertIsNone(presents(None))
        self.assertEqual(presents("CPL", {"CPL": {"words": {"STOP": {}, "CLEAR": {}}}}), ["STOP", "CLEAR"])
        self.assertIn("headModels", provenance())

    def test_no_policy_table_is_seeded(self):
        self.assertIsNone(policy("GCOR"))
