"""Gates for the netlist snapshot check (``kicad_services.snapshot``; the netlist rule, ``AGENTS.md``).

A saved netlist is valid only while its repository has no uncommitted change under the drawing's paths and no commit
touching them is newer than the netlist file. Each scenario builds a throwaway git repository with fixed commit times
and sets the netlist's mtime; the real Railroad repository is never touched.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.kicad_services import snapshot
from tools.layout_compiler import source

PATHS = ("SPCoast", "symbols")
T0 = 1_790_000_000                                      # a fixed commit time; the netlist is placed before or after it


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name) / "Railroad"
        (self.repo / "SPCoast").mkdir(parents=True)
        (self.repo / "symbols").mkdir()
        (self.repo / "docs").mkdir()
        (self.repo / "SPCoast" / "SPCoast.kicad_sch").write_text("(kicad_sch)\n")
        (self.repo / "symbols" / "Railroad-Trackplan.kicad_sym").write_text("(kicad_symbol_lib)\n")
        (self.repo / "docs" / "notes.md").write_text("notes\n")
        self.git("init", "-q")
        self.commit("the drawing", T0, ".")
        self.netlist = Path(self._tmp.name) / "SPCoast.net"
        self.netlist.write_text("(export)\n")

    def tearDown(self):
        self._tmp.cleanup()

    def git(self, *args, when=None):
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com", "GIT_COMMITTER_NAME": "t",
               "GIT_COMMITTER_EMAIL": "t@example.com", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull}
        if when is not None:
            env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = f"@{when} +0000"
        subprocess.run(["git", *args], cwd=self.repo, env=env, check=True, capture_output=True)

    def commit(self, message, when, *paths):
        self.git("add", *paths)
        self.git("commit", "-q", "-m", message, when=when)

    def exported_at(self, when):
        os.utime(self.netlist, (when, when))

    def test_a_netlist_newer_than_every_commit_of_a_clean_drawing_is_fresh(self):
        self.exported_at(T0 + 60)
        self.assertEqual(snapshot.stale_reasons(self.netlist, self.repo, PATHS), [])
        self.assertEqual(snapshot.require_fresh(self.netlist, self.repo, PATHS), self.netlist)

    def test_a_commit_to_the_drawing_after_the_export_makes_it_stale(self):
        self.exported_at(T0 + 60)
        (self.repo / "symbols" / "Railroad-Trackplan.kicad_sym").write_text("(kicad_symbol_lib (symbol x))\n")
        self.commit("a library edit", T0 + 120, "symbols")
        reasons = snapshot.stale_reasons(self.netlist, self.repo, PATHS)
        self.assertEqual(len(reasons), 1)
        self.assertIn("a library edit", reasons[0])
        with self.assertRaises(snapshot.StaleNetlist):
            snapshot.require_fresh(self.netlist, self.repo, PATHS)

    def test_commit_time_counts_not_the_files_mtime(self):
        """A checkout rewrites mtimes: a drawing file touched now, with no commit after the export, is still fresh."""
        self.exported_at(T0 + 60)
        sch = self.repo / "SPCoast" / "SPCoast.kicad_sch"
        os.utime(sch, (T0 + 600, T0 + 600))
        self.assertEqual(snapshot.stale_reasons(self.netlist, self.repo, PATHS), [])

    def test_a_commit_elsewhere_in_the_repository_does_not(self):
        self.exported_at(T0 + 60)
        (self.repo / "docs" / "notes.md").write_text("more notes\n")
        self.commit("docs only", T0 + 120, "docs")
        self.assertEqual(snapshot.stale_reasons(self.netlist, self.repo, PATHS), [])

    def test_an_uncommitted_change_to_the_drawing_makes_it_stale(self):
        self.exported_at(T0 + 60)
        (self.repo / "SPCoast" / "SPCoast.kicad_sch").write_text("(kicad_sch (wire))\n")
        reasons = snapshot.stale_reasons(self.netlist, self.repo, PATHS)
        self.assertEqual(len(reasons), 1)
        self.assertIn("uncommitted", reasons[0])
        self.assertIn("SPCoast/SPCoast.kicad_sch", reasons[0])

    def test_a_new_untracked_sheet_makes_it_stale(self):
        self.exported_at(T0 + 60)
        (self.repo / "SPCoast" / "Sargent.kicad_sch").write_text("(kicad_sch)\n")
        self.assertTrue(snapshot.stale_reasons(self.netlist, self.repo, PATHS))

    def test_both_reasons_are_reported(self):
        self.exported_at(T0 - 60)
        (self.repo / "symbols" / "Railroad-Trackplan.kicad_sym").write_text("(kicad_symbol_lib (symbol y))\n")
        self.assertEqual(len(snapshot.stale_reasons(self.netlist, self.repo, PATHS)), 2)

    def test_no_netlist_or_no_repository_is_reported_not_skipped(self):
        self.assertEqual(snapshot.stale_reasons(self.netlist.with_name("none.net"), self.repo, PATHS)[0][:12], "no netlist a")
        self.exported_at(T0 + 60)
        self.assertIn("cannot read the history", snapshot.stale_reasons(self.netlist, Path(self._tmp.name), PATHS)[0])

    def test_the_importer_reads_a_saved_netlist_only_through_the_check(self):
        """``source.from_snapshot`` raises before it reads a stale netlist."""
        self.exported_at(T0 - 60)
        with self.assertRaises(RuntimeError) as caught:
            source.from_snapshot(self.netlist, self.repo, PATHS)
        self.assertIn("is stale", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
