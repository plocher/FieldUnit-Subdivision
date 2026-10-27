"""Is a saved netlist still a true snapshot of the KiCad project it was exported from?

A netlist is a cache of the project's state (the netlist rule, ``AGENTS.md``). A saved one is valid only when

(a) the project's repository has no uncommitted change under the paths the drawing is made of, and
(b) no commit touching those paths is newer than the netlist file.

Commit times are compared, never the drawing files' mtimes: a checkout rewrites mtimes. The check reports what is
stale; it never decides that a stale netlist is good enough.
"""
from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Sequence


class StaleNetlist(RuntimeError):
    """A saved netlist that no longer matches its project, with every reason in the message."""


def _git(repo: Path, *args: str) -> str:
    out = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, timeout=30)
    if out.returncode != 0:
        raise OSError(out.stderr.strip() or f"git {' '.join(args)} failed in {repo}")
    return out.stdout


def _when(seconds: float) -> str:
    return datetime.fromtimestamp(seconds).astimezone().isoformat(timespec="seconds")


def stale_reasons(netlist: Path, repo: Path, paths: Sequence[str]) -> list[str]:
    """Why ``netlist`` is not a snapshot of ``paths`` in the git repository ``repo``; empty when it is."""
    netlist, repo = Path(netlist), Path(repo)
    if not netlist.is_file():
        return [f"no netlist at {netlist}"]
    try:
        dirty = _git(repo, "status", "--porcelain", "--", *paths).splitlines()
        last = _git(repo, "log", "-1", "--format=%h%x09%ct%x09%s", "--", *paths).strip()
    except (OSError, subprocess.SubprocessError) as e:
        return [f"cannot read the history of {repo}: {e}"]
    reasons = []
    if dirty:
        shown = "; ".join(line.strip() for line in dirty[:10]) + (f"; and {len(dirty) - 10} more" if len(dirty) > 10 else "")
        reasons.append(f"{repo} has uncommitted changes under {', '.join(paths)}: {shown}")
    if last:
        sha, when, subject = last.split("\t", 2)
        mtime = netlist.stat().st_mtime
        if int(when) > mtime:
            reasons.append(f"commit {sha} ({_when(int(when))}, {subject!r}) touches {', '.join(paths)} and is newer than "
                           f"{netlist} ({_when(mtime)})")
    return reasons


def require_fresh(netlist: Path, repo: Path, paths: Sequence[str]) -> Path:
    """``netlist`` when it is a snapshot of ``paths`` in ``repo``; else raise ``StaleNetlist`` naming what is stale."""
    reasons = stale_reasons(netlist, repo, paths)
    if reasons:
        raise StaleNetlist(f"the netlist {netlist} is stale; export it again:\n  " + "\n  ".join(reasons))
    return Path(netlist)
