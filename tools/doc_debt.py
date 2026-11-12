"""The two measures of ADR 0014 decision 2, reported, not enforced.

Trigger and blast radius: ``docs/agents/doc-map.json`` maps code globs to the documents that state their rules. Per
merged PR on main (a ``Merge pull request #N`` commit; plain commits when the range holds none) the report says which
triggers fired on the changed files and which mapped documents changed with them. A trigger with none of its documents
changed is a miss. Code or documents in another repo are not measurable here.

Accumulated debt: every registered diagnostic code (``tools/layout_compiler/diagnostics.json``,
``schemas/layout-model/rules/diagnostics.json``) and every feature scenario is read. Debt is each code with no scenario
(the registry's ``feature`` key resolving to one, or a scenario's text naming the code) and each code or scenario cited
by no ADR under ``docs/adr/`` and not by the symbols manual (the code string, or the scenario name, in the text), each
with the date of the commit that first added it to its registry or feature file.

Run as ``uv run python tools/doc_debt.py [--range A..B | --prs N | --since-tag TAG] [--write]``. Exit status is 0
whatever the numbers say: no gate until the numbers have been watched (ADR 0014 "Not decided").
"""
from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
DOC_MAP = ROOT / "docs" / "agents" / "doc-map.json"
REPORT = ROOT / "docs" / "doc-debt-report.md"
REGISTRIES = {  # registry file -> the features root its "feature" keys are relative to
    ROOT / "tools" / "layout_compiler" / "diagnostics.json": ROOT / "tools" / "layout_compiler" / "features",
    ROOT / "schemas" / "layout-model" / "rules" / "diagnostics.json": ROOT / "schemas" / "layout-model" / "rules" / "features",
}
ADR_DIR = ROOT / "docs" / "adr"
MANUAL = Path("~/Dropbox/KiCad/Railroad/symbols/manual.html").expanduser()
MERGE_PR = re.compile(r"^Merge pull request #(\d+)")
SCENARIO = re.compile(r"^\s*Scenario(?: Outline)?:\s*(.+?)\s*$")
DEFAULT_PRS = 15


# ----------------------------------------------------------------------------------------------------- git

def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout


def head(repo: Path) -> str:
    return git(repo, "rev-parse", "--short", "HEAD").strip()


# ------------------------------------------------------------------------------------------------- doc map

@dataclass(frozen=True)
class Document:
    path: str                  # a path or glob, relative to its repo
    anchor: str = ""           # the section heading a reader opens, "" for the whole document
    repo: str | None = None    # None: this repo; else a key of the map's "repos"

    @property
    def measurable(self) -> bool:
        return self.repo is None

    def __str__(self) -> str:
        p = f"{self.repo}:{self.path}" if self.repo else self.path
        return f"{p}#{self.anchor}" if self.anchor else p


@dataclass(frozen=True)
class Trigger:
    name: str
    code: tuple[str, ...]
    documents: tuple[Document, ...]
    repo: str | None = None

    @property
    def measurable(self) -> bool:
        return self.repo is None


@dataclass
class DocMap:
    triggers: list[Trigger]
    repos: dict[str, str]


def _document(spec) -> Document:
    if isinstance(spec, str):
        path, _, anchor = spec.partition("#")
        return Document(path, anchor)
    return Document(spec["path"], spec.get("anchor", ""), spec.get("repo"))


def load_doc_map(path: Path = DOC_MAP) -> DocMap:
    data = json.loads(path.read_text(encoding="utf-8"))
    triggers = [Trigger(t["name"], tuple(t["code"]), tuple(_document(d) for d in t["documents"]), t.get("repo"))
                for t in data["triggers"]]
    return DocMap(triggers, data.get("repos", {}))


def glob_match(pattern: str, path: str) -> bool:
    """A glob over a repo-relative path: ``*`` stays within one segment, ``**`` crosses segments."""
    out = ""
    i = 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
        elif pattern.startswith("**", i):
            out += ".*"
            i += 2
        elif pattern[i] == "*":
            out += "[^/]*"
            i += 1
        elif pattern[i] == "?":
            out += "[^/]"
            i += 1
        else:
            out += re.escape(pattern[i])
            i += 1
    return re.fullmatch(out, path) is not None


# ---------------------------------------------------------------------------------- trigger and blast radius

@dataclass
class Change:
    """A merged PR, or a plain commit when the range holds no merges."""
    sha: str
    title: str
    files: tuple[str, ...]
    pr: int | None = None

    @property
    def label(self) -> str:
        return f"PR #{self.pr}" if self.pr else self.sha[:7]


@dataclass
class Fired:
    trigger: Trigger
    code_files: tuple[str, ...]
    documents_changed: tuple[Document, ...]
    documents_unchanged: tuple[Document, ...]

    @property
    def measurable(self) -> bool:
        return self.trigger.measurable and any(d.measurable for d in self.trigger.documents)

    @property
    def miss(self) -> bool:
        return self.measurable and not self.documents_changed


@dataclass
class ChangeReport:
    change: Change
    fired: list[Fired]

    @property
    def misses(self) -> list[Fired]:
        return [f for f in self.fired if f.miss]


def changes_in_range(repo: Path, rev_range: str) -> list[Change]:
    """The merged PRs in ``A..B`` on the first-parent line, oldest first; every commit when none is a PR merge."""
    log = git(repo, "log", "--first-parent", "--reverse", "--format=%x02%H%x00%s%x00%b", rev_range)
    rows = [rec.split("\x00", 2) for rec in log.split("\x02") if rec.strip()]
    merges = [(sha, subject, body) for sha, subject, body in rows if MERGE_PR.match(subject)]
    out = []
    if merges:
        for sha, subject, body in merges:
            files = git(repo, "diff", "--name-only", f"{sha}^1", sha).split()
            title = body.strip().splitlines()[0] if body.strip() else subject  # GitHub puts the PR title in the body
            out.append(Change(sha, title, tuple(sorted(files)), int(MERGE_PR.match(subject).group(1))))
    else:
        for sha, subject, _ in rows:
            files = git(repo, "diff-tree", "--no-commit-id", "--name-only", "-r", "--root", sha).split()
            out.append(Change(sha, subject, tuple(sorted(files))))
    return out


def default_range(repo: Path, prs: int = DEFAULT_PRS, since_tag: str | None = None) -> str:
    """Since ``since_tag``, else from before the oldest of the last ``prs`` merged PRs on the first-parent line."""
    if since_tag:
        return f"{since_tag}..HEAD"
    log = git(repo, "log", "--first-parent", "--format=%H%x00%s", "HEAD")
    merges = [sha for line in log.splitlines() if line for sha, subject in [line.split("\x00", 1)] if MERGE_PR.match(subject)]
    if not merges:
        return f"HEAD~{min(prs, len(log.splitlines()) - 1)}..HEAD"
    oldest = merges[: prs][-1]
    return f"{oldest}^1..HEAD"


def blast_radius(doc_map: DocMap, change: Change) -> ChangeReport:
    fired = []
    for trigger in doc_map.triggers:
        if not trigger.measurable:
            continue  # its code is in another repo: this repo's history cannot see it fire
        code_files = tuple(f for f in change.files if any(glob_match(g, f) for g in trigger.code))
        if not code_files:
            continue
        changed, unchanged = [], []
        for doc in trigger.documents:
            if doc.measurable and any(glob_match(doc.path, f) for f in change.files):
                changed.append(doc)
            else:
                unchanged.append(doc)
        fired.append(Fired(trigger, code_files, tuple(changed), tuple(unchanged)))
    return ChangeReport(change, fired)


# --------------------------------------------------------------------------------------- accumulated debt

@dataclass(frozen=True)
class Scenario:
    file: Path          # the feature file
    key: str            # "<relative file>#<name>", the registry's form
    name: str
    text: str           # the scenario's lines, steps included


def load_registry(path: Path) -> dict[str, dict]:
    """The codes of a registry, the shape ``tests/test_diagnostic_registries.py`` reads through ``registry()``."""
    return json.loads(path.read_text(encoding="utf-8"))["codes"]


def scenarios_under(root: Path) -> list[Scenario]:
    out = []
    for file in sorted(root.rglob("*.feature")):
        lines = file.read_text(encoding="utf-8").splitlines()
        starts = [(i, m.group(1)) for i, line in enumerate(lines) if (m := SCENARIO.match(line))]
        for n, (i, name) in enumerate(starts):
            end = starts[n + 1][0] if n + 1 < len(starts) else len(lines)
            rel = file.relative_to(root).as_posix()
            out.append(Scenario(file, f"{rel}#{name}", name, "\n".join(lines[i:end])))
    return out


@dataclass
class CodeDebt:
    code: str
    registry: Path
    level: str
    lifecycle: str
    scenario: str | None       # the scenario key that specifies it, None when none does
    cited_by: tuple[str, ...]
    first_commit: str | None   # ISO date of the commit that first added the code to its registry


@dataclass
class ScenarioDebt:
    scenario: Scenario
    cited_by: tuple[str, ...]
    first_commit: str | None


@dataclass
class Debt:
    codes: list[CodeDebt] = field(default_factory=list)
    scenarios: list[ScenarioDebt] = field(default_factory=list)

    @property
    def codes_without_scenario(self) -> list[CodeDebt]:
        return [c for c in self.codes if c.scenario is None and c.lifecycle != "retired"]

    @property
    def codes_uncited(self) -> list[CodeDebt]:
        return [c for c in self.codes if not c.cited_by and c.lifecycle != "retired"]

    @property
    def scenarios_uncited(self) -> list[ScenarioDebt]:
        return [s for s in self.scenarios if not s.cited_by]


def scenario_of(code: str, entry: dict, scenarios: list[Scenario]) -> str | None:
    """The registry's ``feature`` key when a scenario answers to it; else the first scenario whose text names the code."""
    keys = {s.key: s for s in scenarios}
    wanted = entry.get("feature")
    if wanted and wanted in keys:
        return wanted
    for s in scenarios:
        if code in s.text:
            return s.key
    return None


def citations(needle: str, documents: dict[str, str]) -> tuple[str, ...]:
    """The documents (label -> text) whose text contains the needle."""
    return tuple(label for label, text in documents.items() if needle in text)


def first_commit_dates(repo: Path, file: Path, needles: Iterable[str]) -> dict[str, str | None]:
    """For each needle, the ISO date of the oldest commit whose patch to ``file`` adds a line containing it; one git
    call per file. A needle no commit added (a working-tree edit) is None."""
    pending = set(needles)
    found: dict[str, str | None] = {n: None for n in pending}
    if not pending:
        return found
    rel = file.resolve().relative_to(repo.resolve()).as_posix()
    log = git(repo, "log", "--reverse", "--follow", "--format=%x01%ad", "--date=short", "-p", "--", rel)
    date = None
    for line in log.splitlines():
        if line.startswith("\x01"):
            date = line[1:]
        elif line.startswith("+") and not line.startswith("+++"):
            for n in [n for n in pending if n in line]:
                found[n] = date
                pending.discard(n)
            if not pending:
                break
    return found


def load_documents(adr_dir: Path = ADR_DIR, manual: Path | None = MANUAL) -> dict[str, str]:
    docs = {p.name: p.read_text(encoding="utf-8") for p in sorted(adr_dir.glob("*.md"))}
    if manual and manual.exists():
        docs["symbols/manual.html"] = manual.read_text(encoding="utf-8")
    return docs


def accumulated_debt(repo: Path, registries: dict[Path, Path], documents: dict[str, str]) -> Debt:
    debt = Debt()
    for registry, features_root in sorted(registries.items()):
        codes = load_registry(registry)
        scenarios = scenarios_under(features_root) if features_root.exists() else []
        dates = first_commit_dates(repo, registry, (f'"{c}"' for c in codes))
        for code in sorted(codes):
            e = codes[code]
            debt.codes.append(CodeDebt(code, registry, e.get("level", ""), e.get("lifecycle", ""),
                                       scenario_of(code, e, scenarios), citations(code, documents), dates[f'"{code}"']))
        by_file: dict[Path, list[Scenario]] = {}
        for s in scenarios:
            by_file.setdefault(s.file, []).append(s)
        for file, group in sorted(by_file.items()):
            dates = first_commit_dates(repo, file, (s.name for s in group))
            for s in group:
                debt.scenarios.append(ScenarioDebt(s, citations(s.name, documents), dates[s.name]))
    return debt


# ------------------------------------------------------------------------------------------------ report

def age_days(iso: str | None, today: dt.date) -> str:
    return "" if iso is None else str((today - dt.date.fromisoformat(iso)).days)


def _rel(path: Path, repo: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        return str(path)


def render(repo: Path, rev_range: str, doc_map: DocMap, reports: list[ChangeReport], debt: Debt, today: dt.date,
           commit: str, manual_read: bool) -> str:
    L = [f"# Documentation debt report", "",
         f"Generated by `uv run python tools/doc_debt.py --range {rev_range} --write` on {today.isoformat()} at commit "
         f"`{commit}`. The two measures of ADR 0014 decision 2, reported, not enforced. Do not edit by hand.", ""]
    # -- trigger and blast radius
    misses = sum(len(r.misses) for r in reports)
    fired = sum(len(r.fired) for r in reports)
    kind = "merged PRs" if any(r.change.pr for r in reports) else "commits"
    L += ["## Trigger and blast radius", "",
          f"Range `{rev_range}`: {len(reports)} {kind}, {fired} triggers fired, **{misses} misses** (a trigger whose "
          "mapped documents all stayed unchanged). Code and documents in another repo are not measurable here.", "",
          "| Change | Trigger | Code changed | Documents changed | Documents unchanged | Result |",
          "|---|---|---|---|---|---|"]
    elsewhere = [t for t in doc_map.triggers if not t.measurable]
    for r in reports:
        if not r.fired:
            L.append(f"| {r.change.label} {_short(r.change.title)} | (none) | | | | |")
        for f in r.fired:
            result = "miss" if f.miss else ("not measurable here" if not f.measurable else "ok")
            L.append(f"| {r.change.label} {_short(r.change.title)} | {f.trigger.name} | {_cells(f.code_files)} | "
                     f"{_cells(map(str, f.documents_changed))} | {_cells(map(str, f.documents_unchanged))} | {result} |")
    if elsewhere:
        L += ["", "Triggers whose code lives in another repo, not measurable here: " +
              ", ".join(f"{t.name} (`{t.repo}:{'`, `'.join(t.code)}`)" for t in elsewhere) + "."]
    # -- accumulated debt
    cited_in = "the ADRs under `docs/adr/`" + (" and the symbols manual" if manual_read else
                                               " (the symbols manual was not found, so counts as citing nothing)")
    L += ["", "## Accumulated debt", "",
          f"{len(debt.codes)} registered codes, {len(debt.scenarios)} feature scenarios. Citations are looked for in "
          f"{cited_in}: a code string or a scenario name appearing in the text. Age is in days from the commit that "
          "first added the item to its registry or feature file, as of the report date. Retired codes are not counted.", ""]
    L += [f"### Codes without a scenario: {len(debt.codes_without_scenario)}", "",
          "| Code | Registry | Level | Lifecycle | First commit | Age |", "|---|---|---|---|---|---|"]
    for c in debt.codes_without_scenario:
        L.append(f"| `{c.code}` | {_rel(c.registry, repo)} | {c.level} | {c.lifecycle} | {c.first_commit or ''} | {age_days(c.first_commit, today)} |")
    L += ["", f"### Codes cited by no ADR and not by the manual: {len(debt.codes_uncited)}", "",
          "| Code | Registry | Level | Lifecycle | Scenario | First commit | Age |", "|---|---|---|---|---|---|---|"]
    for c in debt.codes_uncited:
        L.append(f"| `{c.code}` | {_rel(c.registry, repo)} | {c.level} | {c.lifecycle} | {c.scenario or ''} | {c.first_commit or ''} | {age_days(c.first_commit, today)} |")
    L += ["", f"### Scenarios cited by no ADR and not by the manual: {len(debt.scenarios_uncited)}", "",
          "| Feature | Scenario | First commit | Age |", "|---|---|---|---|"]
    for s in debt.scenarios_uncited:
        L.append(f"| {_rel(s.scenario.file, repo)} | {s.scenario.name} | {s.first_commit or ''} | {age_days(s.first_commit, today)} |")
    L += ["", "## Totals", "",
          "| Measure | Count |", "|---|---|",
          f"| Triggers fired in range | {fired} |",
          f"| Misses in range | {misses} |",
          f"| Registered codes (not retired) | {sum(1 for c in debt.codes if c.lifecycle != 'retired')} |",
          f"| Codes without a scenario | {len(debt.codes_without_scenario)} |",
          f"| Codes uncited | {len(debt.codes_uncited)} |",
          f"| Feature scenarios | {len(debt.scenarios)} |",
          f"| Scenarios uncited | {len(debt.scenarios_uncited)} |", ""]
    return "\n".join(L)


def _short(title: str, n: int = 60) -> str:
    t = title.strip().replace("|", "\\|")
    return "" if not t else (t if len(t) <= n else t[: n - 1] + "…")


def _cells(items) -> str:
    return "<br>".join(f"`{i}`" for i in items)


# -------------------------------------------------------------------------------------------------- CLI

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--range", help="git range A..B of main's first-parent line; default: the last --prs merged PRs")
    p.add_argument("--prs", type=int, default=DEFAULT_PRS, help=f"how many merged PRs the default range covers ({DEFAULT_PRS})")
    p.add_argument("--since-tag", help="default range from this tag to HEAD instead")
    p.add_argument("--write", action="store_true", help=f"write {REPORT.relative_to(ROOT)}; else print the report")
    p.add_argument("--doc-map", type=Path, default=DOC_MAP)
    a = p.parse_args(argv)
    rev_range = a.range or default_range(ROOT, a.prs, a.since_tag)
    doc_map = load_doc_map(a.doc_map)
    reports = [blast_radius(doc_map, c) for c in changes_in_range(ROOT, rev_range)]
    documents = load_documents()
    debt = accumulated_debt(ROOT, REGISTRIES, documents)
    text = render(ROOT, rev_range, doc_map, reports, debt, dt.date.today(), head(ROOT), "symbols/manual.html" in documents)
    if a.write:
        REPORT.write_text(text, encoding="utf-8")
        print(f"wrote {REPORT.relative_to(ROOT)}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
