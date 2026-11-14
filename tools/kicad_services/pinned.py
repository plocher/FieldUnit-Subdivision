"""A KiCad project as it was at one commit: a temporary checkout of a git repository, read only, deleted after use.

A test corpus is a drawing frozen at a commit, so the gates do not change when the owner edits the live drawing. The
checkout is a shared clone (``git clone --shared``: the source repository is only read) with a sparse checkout of the
paths the drawing is made of, detached at the commit. A clone, not ``git archive``: the importer's provenance is the
``git describe`` of the project and of each library, and a clone answers it as the source repository does.

The global ``sym-lib-table`` names the live libraries; ``libraries`` gives the table with every library in the
checkout's symbol directory put in place of the one of the same name, for the readers that take a library map.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional, Sequence


@dataclass(frozen=True)
class Pin:
    """A drawing frozen at a commit: the repository, the commit, the paths it is made of, its root sheet and its
    symbol directory (both relative to the repository)."""

    repository: Path
    commit: str
    paths: tuple[str, ...]
    project: str
    symbols: str

    @classmethod
    def load(cls, path: Path) -> "Pin":
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(Path(d["repository"]).expanduser(), d["commit"], tuple(d["paths"]), d["project"], d["symbols"])

    def available(self) -> bool:
        """The repository is here and holds the commit."""
        if not (self.repository / ".git").exists():
            return False
        try:
            out = subprocess.run(["git", "cat-file", "-e", f"{self.commit}^{{commit}}"], cwd=self.repository,
                                 capture_output=True, timeout=30)
        except (OSError, subprocess.SubprocessError):
            return False
        return out.returncode == 0


def _git(cwd: Path, *args: str) -> None:
    out = subprocess.run(["git", "-c", "advice.detachedHead=false", *args], cwd=cwd, capture_output=True, text=True, timeout=120)
    if out.returncode != 0:
        raise OSError(out.stderr.strip() or f"git {' '.join(args)} failed in {cwd}")


@contextmanager
def checkout(repository: Path, commit: str, paths: Sequence[str]) -> Iterator[Path]:
    """The repository's ``paths`` at ``commit`` in a temporary directory, removed on exit."""
    tmp = Path(tempfile.mkdtemp(prefix="kicad-pinned-"))
    try:
        work = tmp / Path(repository).name
        _git(tmp, "clone", "--quiet", "--shared", "--no-checkout", str(Path(repository).resolve()), str(work))
        _git(work, "sparse-checkout", "set", "--no-cone", *(f"/{p.strip('/')}/" for p in paths))
        _git(work, "checkout", "--quiet", "--detach", commit)
        yield work
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def libraries(symbols_dir: Path, project_dir: Optional[Path] = None) -> dict[str, Path]:
    """KiCad's tables for ``project_dir``, with each ``*.kicad_sym`` in ``symbols_dir`` in place of the library of its name."""
    from .library_table import library_paths
    out = library_paths(project_dir)
    out.update({f.stem: f for f in sorted(Path(symbols_dir).glob("*.kicad_sym"))})
    return out


@contextmanager
def opened(pin: Pin) -> Iterator[tuple[Path, dict[str, Path]]]:
    """The pinned root sheet and its library map, in a checkout removed on exit."""
    with checkout(pin.repository, pin.commit, pin.paths) as work:
        project = work / pin.project
        yield project, libraries(work / pin.symbols, project.parent)
