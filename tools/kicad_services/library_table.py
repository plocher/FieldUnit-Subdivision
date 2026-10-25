"""Where a symbol library lives: KiCad's ``sym-lib-table``, the project's first and then the user's."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional

_LIB = re.compile(r'\(lib\s+\(name\s+"([^"]*)"\).*?\(uri\s+"([^"]*)"\)', re.S)


def user_table() -> Optional[Path]:
    """The user's global table (macOS: ``~/Library/Preferences/kicad/<version>/sym-lib-table``, newest version)."""
    base = Path(os.environ.get("KICAD_CONFIG_HOME", Path.home() / "Library/Preferences/kicad"))
    versioned = [p for p in base.glob("*/sym-lib-table") if re.fullmatch(r"\d+(\.\d+)*", p.parent.name)]   # not a renamed backup
    found = sorted(versioned, key=lambda p: [int(x) for x in p.parent.name.split(".")])
    return found[-1] if found else None


def read_table(path: Path, project_dir: Optional[Path] = None) -> dict[str, Path]:
    """Library name to file, ``${KIPRJMOD}`` and the environment expanded."""
    text = path.read_text(encoding="utf-8", errors="replace")
    out: dict[str, Path] = {}
    for name, uri in _LIB.findall(text):
        if project_dir is not None:
            uri = uri.replace("${KIPRJMOD}", str(project_dir))
        out[name] = Path(os.path.expandvars(uri)).expanduser()
    return out


def library_paths(project_dir: Optional[Path] = None) -> dict[str, Path]:
    """Every library KiCad would see from this project: the project table over the user table."""
    out: dict[str, Path] = {}
    user = user_table()
    if user is not None and user.is_file():
        out.update(read_table(user))
    if project_dir is not None and (project_dir / "sym-lib-table").is_file():
        out.update(read_table(project_dir / "sym-lib-table", project_dir))
    return out
