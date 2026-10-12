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


_STANDARD_PROPERTIES = frozenset({"Reference", "Value", "Footprint", "Datasheet", "Description",
                                  "ki_keywords", "ki_fp_filters"})
_PROPERTY = re.compile(r'\n\t\t\(property "((?:[^"\\]|\\.)*)" "((?:[^"\\]|\\.)*)"')


def unquote(s: str) -> str:
    """The value of a KiCad s-expression string body: undo the backslash escapes."""
    return re.sub(r"\\(.)", lambda m: {"n": "\n", "t": "\t"}.get(m.group(1), m.group(1)), s)


def library_standard_properties(text: str) -> dict[str, dict[str, str]]:
    """{symbol name: {standard field: value}} for the fields library_symbols() omits.

    Values are unescaped (a Description may hold a quoted word); fields a symbol lacks are absent.
    """
    out = {}
    for s, e in blocks(text, "symbol", 1):
        b = text[s:e]
        name = re.match(r'\(symbol "([^"]+)"', b).group(1)
        out[name] = {unquote(k): unquote(v) for k, v in _PROPERTY.findall(b) if k in _STANDARD_PROPERTIES}
    return out


def library_symbols(text: str) -> dict[str, dict]:
    """Top-level symbols of a .kicad_sym text.

    Returns {name: {"properties": {...}, "pins": [(name, number, electrical_type)], "extends": str|None,
    "units": {unit number: [pin names]}, "locked": bool, "value_autoplace": bool}};
    "properties" omits KiCad's standard fields; "locked" is KiCad's "units are not interchangeable".
    """
    out = {}
    for s, e in blocks(text, "symbol", 1):
        b = text[s:e]
        name = re.match(r'\(symbol "([^"]+)"', b).group(1)
        props = {k: v for k, v in re.findall(r'\n\t\t\(property "([^"]+)" "([^"]*)"', b)
                 if k not in _STANDARD_PROPERTIES}
        pins = [(n, num, ty) for ty, n, num in
                re.findall(r'\(pin (\w+) \w+[\s\S]*?\(name "([^"]*)"[\s\S]*?\(number "([^"]*)"', b)]
        ext = re.search(r'\n\t\t\(extends "([^"]+)"', b)
        units: dict[int, list[str]] = {}
        for us, ue in blocks(b, "symbol", 2):
            ub = b[us:ue]
            unit = int(re.match(r'\(symbol "(?:[^"\\]|\\.)*_(\d+)_\d+"', ub).group(1))
            units.setdefault(unit, []).extend(re.findall(r'\(pin \w+ \w+[\s\S]*?\(name "([^"]*)"', ub))
        value = re.search(r'\n\t\t\(property "Value" ', b)
        value_block = b[value.start() + 1:end_of(b, value.start() + 3)] if value else ""
        out[name] = {"properties": props, "pins": pins, "extends": ext.group(1) if ext else None,
                     "units": units, "locked": '\n\t\t(property "ki_locked"' in b,
                     "value_autoplace": "(do_not_autoplace yes)" not in value_block}
    return out
