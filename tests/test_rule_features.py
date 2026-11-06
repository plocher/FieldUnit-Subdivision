"""The rules as features (ADR 0012 §3): two roots, each with its registry. The model features, what any writer of the
Layout Data Model File must pass, are with the schema; the import features, how a KiCad drawing becomes facts, are
with the importer. A scenario's diagnostic code is its tag; a registry entry's ``feature`` is ``file#scenario``.
The gate: every link resolves both ways, every step has a definition, and behave passes every scenario not tagged
``@pending`` (a rule stated before its implementation)."""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

from behave.parser import parse_file

import tools.layout_compiler as importer
from tools.layout_model import derive

ROOT = Path(__file__).resolve().parents[1]
ROOTS = {"model": (ROOT / "schemas" / "layout-model" / "rules" / "features", derive.registry),
         "import": (ROOT / "tools" / "layout_compiler" / "features", importer.registry)}
NOT_CODES = frozenset({"pending"})


def scenarios(root: Path) -> list[tuple[str, str, frozenset[str]]]:
    """(file relative to the root, scenario name, its tags and its feature's) for every scenario under ``root``."""
    out = []
    for path in sorted(root.rglob("*.feature")):
        feature = parse_file(str(path))
        for s in feature.scenarios:
            out.append((path.relative_to(root).as_posix(), s.name, frozenset(map(str, feature.tags + s.tags))))
    return out


def behave(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-m", "behave", "--no-color", *args], cwd=root, capture_output=True, text=True)


class Features(unittest.TestCase):
    def test_every_registry_link_names_a_scenario_tagged_with_its_code(self):
        for kind, (root, registry) in ROOTS.items():
            tagged = {(f"{file}#{name}"): tags for file, name, tags in scenarios(root)}
            for code, entry in registry().items():
                if entry["feature"] is not None:
                    self.assertIn(entry["feature"], tagged, f"{kind}: {code}")
                    self.assertIn(code, tagged[entry["feature"]], f"{kind}: {entry['feature']} is not tagged @{code}")

    def test_every_scenario_tag_is_a_code_of_its_own_registry_that_links_to_a_scenario(self):
        for kind, (root, registry) in ROOTS.items():
            reg = registry()
            for file, name, tags in scenarios(root):
                for tag in tags - NOT_CODES:
                    self.assertIn(tag, reg, f"{kind}: {file}#{name}")
                    self.assertIsNotNone(reg[tag]["feature"], f"{kind}: {tag} names no scenario")

    def test_a_code_is_active_only_when_a_scenario_that_runs_names_it(self):
        for kind, (root, registry) in ROOTS.items():
            runs = {t for _, _, tags in scenarios(root) if "pending" not in tags for t in tags}
            for code, entry in registry().items():
                if entry["feature"] is not None and code not in runs:
                    self.assertEqual(entry["lifecycle"], "proposed", f"{kind}: {code} is named only by pending scenarios")

    def test_scenario_names_are_unique_in_a_file(self):
        for kind, (root, _) in ROOTS.items():
            names = [f"{file}#{name}" for file, name, _ in scenarios(root)]
            self.assertEqual(sorted(n for n in set(names) if names.count(n) > 1), [], kind)

    def test_every_step_has_a_definition(self):
        for kind, (root, _) in ROOTS.items():
            run = behave(root, "--dry-run")
            self.assertNotIn("undefined", run.stdout.splitlines()[-2], f"{kind}:\n{run.stdout[-2000:]}")

    def test_behave_passes_every_scenario_that_is_not_pending(self):
        for kind, (root, _) in ROOTS.items():
            run = behave(root, "--tags=not @pending")
            self.assertEqual(run.returncode, 0, f"{kind}:\n{run.stdout[-3000:]}{run.stderr[-2000:]}")


if __name__ == "__main__":
    unittest.main()
