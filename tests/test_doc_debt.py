"""The two measures of ADR 0014 decision 2 (``tools/doc_debt.py``) on a small git repository built here: a miss is a
trigger whose mapped documents stayed unchanged in the PR; debt is a code with no scenario, and a code or scenario no
ADR cites, dated by the commit that first added it. Nothing here reads this repo's own history or counts."""
from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools import doc_debt

REGISTRY = {"version": "0.1.0", "description": "test", "codes": {
    "lamp.track": {"level": "error", "lifecycle": "active", "since": "0.1.0", "feature": "lamp.feature#a lamp off track", "replacedBy": None},
    "lamp.name": {"level": "missing", "lifecycle": "active", "since": "0.1.0", "feature": None, "replacedBy": None},
    "lamp.old": {"level": "info", "lifecycle": "retired", "since": "0.1.0", "feature": None, "replacedBy": None},
}}
FEATURE = """Feature: A lamp
  Scenario: a lamp off track
    Given a lamp
    Then it is reported as an error
"""
DOC_MAP = {"about": "test", "repos": {"railroad": "/nowhere"}, "triggers": [
    {"name": "lamps", "code": ["src/lamp.py"], "documents": ["docs/adr/0001-lamps.md#Rule", "features/*.feature"]},
    {"name": "libraries", "repo": "railroad", "code": ["symbols/*.kicad_sym"], "documents": [{"repo": "railroad", "path": "manual.html"}]},
]}


class Repo:
    def __init__(self, root: Path):
        self.root = root
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "t@example.invalid")
        self.git("config", "user.name", "t")

    def git(self, *args: str, date: str = "2026-01-01") -> str:
        env = dict(os.environ, GIT_AUTHOR_DATE=f"{date}T12:00:00", GIT_COMMITTER_DATE=f"{date}T12:00:00")
        return subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True, text=True, env=env).stdout

    def write(self, rel: str, text: str) -> None:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def commit(self, message: str, date: str, **files: str) -> None:
        for rel, text in files.items():
            self.write(rel, text)
        self.git("add", *files)
        self.git("commit", "-q", "-m", message, date=date)

    def pr(self, number: int, title: str, date: str, **files: str) -> None:
        """A merged PR the way GitHub records it: a feature branch merged with ``Merge pull request #N``."""
        self.git("checkout", "-q", "-b", f"pr{number}")
        self.commit(title, date, **files)
        self.git("checkout", "-q", "main")
        self.git("merge", "-q", "--no-ff", "-m", f"Merge pull request #{number} from x/pr{number}\n\n{title}", f"pr{number}", date=date)


class DocDebt(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Repo(Path(self.tmp.name))
        r = self.repo
        r.commit("seed", "2026-01-01", **{
            "diagnostics.json": json.dumps(REGISTRY, indent=1),
            "features/lamp.feature": FEATURE,
            "docs/adr/0001-lamps.md": "# Lamps\n\n## Rule\n\nA lamp off track is `lamp.track`.\n",
            "docs/agents/doc-map.json": json.dumps(DOC_MAP),
            "src/lamp.py": "x = 1\n",
        })
        r.pr(1, "fix: lamp rule, with its ADR", "2026-01-10", **{"src/lamp.py": "x = 2\n", "docs/adr/0001-lamps.md": "# Lamps\n\n## Rule\n\nA lamp off track is `lamp.track`, amended.\n"})
        r.pr(2, "fix: lamp rule, code only", "2026-01-20", **{"src/lamp.py": "x = 3\n"})
        r.pr(3, "docs: unrelated", "2026-01-25", **{"README.md": "hi\n"})
        self.doc_map = doc_debt.load_doc_map(r.root / "docs" / "agents" / "doc-map.json")

    def tearDown(self):
        self.tmp.cleanup()

    def test_a_pr_whose_trigger_fired_with_no_mapped_document_is_a_miss(self):
        changes = doc_debt.changes_in_range(self.repo.root, "main~3..main")
        self.assertEqual([c.pr for c in changes], [1, 2, 3])
        self.assertEqual(changes[1].title, "fix: lamp rule, code only")
        reports = [doc_debt.blast_radius(self.doc_map, c) for c in changes]
        self.assertEqual([len(r.fired) for r in reports], [1, 1, 0])
        self.assertEqual([len(r.misses) for r in reports], [0, 1, 0])
        self.assertEqual([str(d) for d in reports[0].fired[0].documents_changed], ["docs/adr/0001-lamps.md#Rule"])
        self.assertEqual(reports[1].fired[0].code_files, ("src/lamp.py",))
        self.assertEqual([t.name for t in self.doc_map.triggers if not t.measurable], ["libraries"])  # not measurable here

    def test_plain_commits_are_walked_when_the_range_holds_no_merge(self):
        self.repo.commit("chore: direct to main", "2026-02-01", **{"src/lamp.py": "x = 4\n"})
        changes = doc_debt.changes_in_range(self.repo.root, "main~1..main")
        self.assertEqual([c.pr for c in changes], [None])
        self.assertEqual(changes[0].files, ("src/lamp.py",))
        self.assertEqual(doc_debt.default_range(self.repo.root, prs=2), f"{self.repo.git('rev-parse', 'main~2').strip()}^1..HEAD")

    def test_glob_match(self):
        self.assertTrue(doc_debt.glob_match("tools/*.py", "tools/a.py"))
        self.assertFalse(doc_debt.glob_match("tools/*.py", "tools/x/a.py"))
        self.assertTrue(doc_debt.glob_match("f/**/*.feature", "f/a/b/c.feature"))
        self.assertTrue(doc_debt.glob_match("f/**/*.feature", "f/c.feature"))

    def test_debt_names_the_code_without_scenario_the_uncited_items_and_their_age(self):
        r = self.repo
        r.commit("feat: a new code", "2026-02-10", **{"diagnostics.json": json.dumps({**REGISTRY, "codes": {
            **REGISTRY["codes"], "lamp.new": {"level": "error", "lifecycle": "active", "since": "0.2.0", "feature": None, "replacedBy": None}}}, indent=1),
            "features/lamp.feature": FEATURE + "\n  Scenario: a new lamp\n    Then lamp.new is reported\n"})
        documents = doc_debt.load_documents(r.root / "docs" / "adr", manual=None)
        debt = doc_debt.accumulated_debt(r.root, {r.root / "diagnostics.json": r.root / "features"}, documents)
        by_code = {c.code: c for c in debt.codes}
        self.assertEqual(by_code["lamp.track"].scenario, "lamp.feature#a lamp off track")   # the registry's key
        self.assertEqual(by_code["lamp.new"].scenario, "lamp.feature#a new lamp")           # a step names the code
        self.assertEqual([c.code for c in debt.codes_without_scenario], ["lamp.name"])     # retired lamp.old not counted
        self.assertEqual(by_code["lamp.track"].cited_by, ("0001-lamps.md",))
        self.assertEqual([c.code for c in debt.codes_uncited], ["lamp.name", "lamp.new"])
        self.assertEqual([s.scenario.name for s in debt.scenarios_uncited], ["a lamp off track", "a new lamp"])
        self.assertEqual(by_code["lamp.name"].first_commit, "2026-01-01")
        self.assertEqual(by_code["lamp.new"].first_commit, "2026-02-10")
        self.assertEqual({s.scenario.name: s.first_commit for s in debt.scenarios}, {"a lamp off track": "2026-01-01", "a new lamp": "2026-02-10"})
        self.assertEqual(doc_debt.age_days("2026-02-10", dt.date(2026, 2, 15)), "5")
        self.assertEqual(doc_debt.age_days(None, dt.date(2026, 2, 15)), "")

    def test_an_edit_not_yet_committed_has_no_date(self):
        self.repo.write("features/lamp.feature", FEATURE + "\n  Scenario: uncommitted\n    Then nothing\n")
        dates = doc_debt.first_commit_dates(self.repo.root, self.repo.root / "features" / "lamp.feature", ["uncommitted", "a lamp off track"])
        self.assertEqual(dates, {"uncommitted": None, "a lamp off track": "2026-01-01"})

    def test_the_report_renders_deterministically_with_its_date_and_commit(self):
        changes = doc_debt.changes_in_range(self.repo.root, "main~3..main")
        reports = [doc_debt.blast_radius(self.doc_map, c) for c in changes]
        documents = doc_debt.load_documents(self.repo.root / "docs" / "adr", manual=None)
        debt = doc_debt.accumulated_debt(self.repo.root, {self.repo.root / "diagnostics.json": self.repo.root / "features"}, documents)
        args = (self.repo.root, "main~3..main", self.doc_map, reports, debt, dt.date(2026, 3, 1), "abc1234", False)
        text = doc_debt.render(*args)
        self.assertEqual(text, doc_debt.render(*args))
        self.assertIn("on 2026-03-01 at commit `abc1234`", text)
        self.assertIn("**1 misses**", text)
        self.assertIn("| PR #2 fix: lamp rule, code only | lamps | `src/lamp.py` |  | `docs/adr/0001-lamps.md#Rule`<br>`features/*.feature` | miss |", text)
        self.assertIn("not measurable here: libraries (`railroad:symbols/*.kicad_sym`)", text)
        self.assertIn("| Codes without a scenario | 1 |", text)
        self.assertIn("| Scenarios uncited | 1 |", text)


if __name__ == "__main__":
    unittest.main()
