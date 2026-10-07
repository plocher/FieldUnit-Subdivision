"""Text-level helpers for KiCad 10 s-expression files (.kicad_sch, .kicad_sym).

KiCad writes one node per line, tab-indented by depth. Editing the text in place
(rather than re-serialising a parsed tree) keeps every untouched byte as KiCad
wrote it, so a diff shows only the intended change. Gate an edit with a
kicad-cli round trip (`sym upgrade` / `sch export netlist`) where it matters.
"""

from __future__ import annotations

import re
from typing import Iterator


def end_of(text: str, start: int) -> int:
    """Index just past the s-expression that opens at text[start] == '('."""
    depth, j = 0, start
    while True:
        c = text[j]
        if c == '"':  # skip quoted strings (may contain parentheses)
            j += 1
            while text[j] != '"':
                j += 2 if text[j] == "\\" else 1
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1


def blocks(text: str, head: str, depth: int) -> Iterator[tuple[int, int]]:
    """(start, end) of every node '(head' that opens a line at the given tab depth."""
    pattern = re.compile(r"\n" + "\t" * depth + r"\(" + re.escape(head) + r"[\s\n)]")
    for m in pattern.finditer(text):
        s = m.start() + 1 + depth
        yield s, end_of(text, s)


def replace_spans(text: str, edits: list[tuple[int, int, str]]) -> str:
    """Apply non-overlapping (start, end, new) edits."""
    out, pos = [], 0
    for s, e, new in sorted(edits):
        out += [text[pos:s], new]
        pos = e
    return "".join(out) + text[pos:]
