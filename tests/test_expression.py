"""Indication expressions (tools/layout_model/expression.py): the grammar of a desk lamp's ``Indication`` and a lever
pin's ``Indication.<pin>`` (the owner, 2026-10-28), as a table of text in, normalized text and tokens out."""

from __future__ import annotations

import unittest

from tools.layout_model import expression

# (source, normalized text, tokens consumed in first-use order)
CASES = [
    ("1NATK", "1NATK", ["1NATK"]),
    ("  Watsonville:837T1K ", "Watsonville:837T1K", ["Watsonville:837T1K"]),
    ("1NATK|2NATK", "1NATK | 2NATK", ["1NATK", "2NATK"]),
    ("1NATK, 2NATK,3NATK", "1NATK | 2NATK | 3NATK", ["1NATK", "2NATK", "3NATK"]),       # a comma is or (transition)
    ("!835WLK", "!835WLK", ["835WLK"]),
    ("!!835WLK", "!!835WLK", ["835WLK"]),
    ("a & b | c", "a & b | c", ["a", "b", "c"]),                                     # & binds tighter than |
    ("a & (b | c)", "a & (b | c)", ["a", "b", "c"]),
    ("(a | b) | (c | a)", "a | b | c | a", ["a", "b", "c"]),                         # same operator flattened; tokens once
    ("!(a & b)", "!(a & b)", ["a", "b"]),
    ("((a))", "a", ["a"]),
]

BAD = ["", "   ", "a |", "| a", "a & & b", "(a", "a)", "a b", "!", "()", "a,"]


class Expressions(unittest.TestCase):
    def test_the_table(self):
        for source, text, tokens in CASES:
            with self.subTest(source=source):
                self.assertEqual(expression.normalize(source), (text, tokens))

    def test_normalized_text_parses_back_to_itself(self):
        for _, text, tokens in CASES:
            with self.subTest(text=text):
                self.assertEqual(expression.normalize(text), (text, tokens))

    def test_malformed_expressions_are_errors_naming_the_position(self):
        for source in BAD:
            with self.subTest(source=source):
                with self.assertRaises(expression.ExpressionError) as e:
                    expression.parse(source)
                self.assertIn("expected at", str(e.exception))

    def test_tokens_are_mapped_to_qualify_them(self):
        q = lambda t: t if ":" in t else f"Luchessa:{t}"
        self.assertEqual(expression.normalize("1NATK | !Watsonville:837T1K", q),
                         ("Luchessa:1NATK | !Watsonville:837T1K", ["Luchessa:1NATK", "Watsonville:837T1K"]))


if __name__ == "__main__":
    unittest.main()
