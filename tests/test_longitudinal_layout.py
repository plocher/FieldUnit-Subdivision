"""Tests for semantic longitudinal model-board layout."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"

if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from plant_graph.layout import LongitudinalInterval, LongitudinalLayoutSolver


class LongitudinalLayoutSolverTests(unittest.TestCase):
    """The solver preserves topology order inside a fixed logical width."""

    def test_prioritizes_a_signal_dogleg_over_compressible_dark_track(self) -> None:
        intervals = (
            LongitudinalInterval(0, 1, 0.08, 0.15),
            LongitudinalInterval(1, 2, 0.08, 0.15),
            LongitudinalInterval(2, 3, 0.45, 2.0),
            LongitudinalInterval(3, 4, 0.08, 1.0),
        )

        positions = LongitudinalLayoutSolver().solve(
            anchor_count=5,
            width_units=3.0,
            intervals=intervals,
        )

        self.assertEqual(positions[0], 0.0)
        self.assertEqual(positions[4], 3.0)
        self.assertGreaterEqual(positions[3] - positions[2], 0.45)
        self.assertLess(positions[2] - positions[1], positions[3] - positions[2])
        self.assertEqual(positions, dict(sorted(positions.items())))

    def test_honors_fixed_section_centers_while_solving_intervals(self) -> None:
        intervals = tuple(
            LongitudinalInterval(index, index + 1, 0.06, 1.0)
            for index in range(6)
        )

        positions = LongitudinalLayoutSolver().solve(
            anchor_count=7,
            width_units=3.0,
            intervals=intervals,
            fixed_positions={2: 0.5, 4: 1.5, 6: 3.0},
        )

        self.assertEqual(positions[0], 0.0)
        self.assertEqual(positions[2], 0.5)
        self.assertEqual(positions[4], 1.5)
        self.assertEqual(positions[6], 3.0)
        self.assertTrue(
            all(
                positions[index] < positions[index + 1]
                for index in range(6)
            )
        )


if __name__ == "__main__":
    unittest.main()
