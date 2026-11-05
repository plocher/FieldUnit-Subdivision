#!/usr/bin/env python3
"""Generate the symbols manual: one HTML page from the Railroad symbol libraries and the prose fragments.

    uv run python tools/contract/symbol_manual.py [--libdir DIR] [--prose DIR] [--out DIR] [--bindings FILE]

Facts come from the libraries only: each symbol's Description, its fields (who sets each one, shown or
hidden), its pins (kind from `Pin.<pin>`, direction) and its units, rendered by `kicad-cli sym export svg`.
The prose directory (default <libdir>/manual) holds what is hand-written:

    groups.toml     the groups in page order: id, title, library (the tab) and `match`, a selector over
                    library facts (`library`, `pin`, or any field such as Role, Appliance, Kind, Style, IC;
                    a value or a list of values). A symbol belongs to the first group that matches it.
    <id>.html       the usage paragraph of group <id>, an HTML fragment
    intro.html      the "About" tab, an HTML fragment (optional)

The page is <out>/index.html (default <libdir>/production/manual, gitignored), self-contained: style,
script and SVGs are inline. A symbol no group matches, a group that matches nothing and a group with no
fragment are reported on stderr and shown on the page; the exit status is then 1.

Rule links (the hook for the rule features of ADR 0012): `--bindings` names a JSON list of
{"match": selector, "pin": name or "field": name, "feature": "file#scenario", "href": url}. Each row of a
matching symbol's pin or field table then links to the feature. Without the file no link is drawn.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kicad_services.sch_text import library_fields, library_symbols  # noqa: E402

LIBDIR = Path.home() / "Dropbox/KiCad/Railroad/symbols"
LIBRARIES = ("Railroad-Trackplan", "Railroad-Trackplan-Signals", "Railroad-Office", "Railroad-Field",
             "Railroad-Field-Signals", "Railroad-HardwareIO")
KICAD_CLI = os.environ.get("KICAD_CLI") or shutil.which("kicad-cli") or "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
_NOT_FIELDS = frozenset({"Reference", "Footprint", "Datasheet", "Description", "ki_keywords", "ki_fp_filters",
                         "ki_locked"})
_SCALE = 4       # the drawings are shown at four times KiCad's sheet size, all symbols alike
_HERE = Path(__file__).resolve().parent


@dataclass
class Symbol:
    library: str
    name: str
    description: str
    fields: list[tuple[str, str, bool]]          # (field, library value, hidden); no standard or Pin.* field
    pins: list[tuple[str, str, str, str, str]]   # (name, number, kind, direction, units)
    units: list[tuple[int, str]] = field(default_factory=list)   # (unit number, inline svg)

    @property
    def anchor(self) -> str:
        return slug(f"{self.library}-{self.name}")

    def facts(self) -> dict[str, set[str]]:
        """What a selector can match: library, pin names and every field's library value."""
        out = {k: {v} for k, v, _ in self.fields}
        out["library"] = {self.library}
        out["pin"] = {bare(p[0]) for p in self.pins}
        return out


def slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-")


def bare(pin: str) -> str:
    """A pin name without KiCad's overbar markup: ~{LAMP} is LAMP."""
    m = re.fullmatch(r"~\{(.*)\}", pin)
    return m.group(1) if m else pin


def matches(selector: dict, facts: dict[str, set[str]]) -> bool:
    """True when every key of the selector has one of its values among the symbol's facts."""
    for key, want in selector.items():
        want = {want} if isinstance(want, str) else set(want)
        if not want & facts.get(key, set()):
            return False
    return True


def render_units(lib_file: Path) -> dict[str, list[tuple[int, str]]]:
    """{file stem before _unitN: [(unit, inline svg)]} from kicad-cli; the render is also the parse check."""
    out: dict[str, list[tuple[int, str]]] = {}
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([KICAD_CLI, "sym", "export", "svg", "-o", tmp, str(lib_file)], check=True, capture_output=True)
        for f in sorted(Path(tmp).iterdir()):
            stem, _, unit = f.stem.rpartition("_unit")
            svg = f.read_text()
            svg = svg[svg.index("<svg"):]
            svg = re.sub(r"<title>.*?</title>\s*|<desc>.*?</desc>\s*", "", svg, flags=re.S)
            svg = re.sub(r'(width|height)="([\d.]+)mm"', lambda m: f'{m.group(1)}="{float(m.group(2)) * _SCALE:.2f}mm"', svg, count=2)
            out.setdefault(stem, []).append((int(unit), svg))
    return {k: sorted(v) for k, v in out.items()}


def read_library(lib_file: Path) -> list[Symbol]:
    text = lib_file.read_text()
    fields = library_fields(text)
    rendered = render_units(lib_file)
    by_slug = {slug(k): v for k, v in rendered.items()}
    out = []
    for name, sym in library_symbols(text).items():
        f = fields[name]
        values = {k: v for k, v, _ in f}
        units_of: dict[str, list[int]] = {}
        for unit, names in sym["units"].items():
            for n in names:
                units_of.setdefault(n, []).append(unit)
        many = len({u for u in sym["units"] if u}) > 1
        pins, seen = [], set()
        for pname, number, etype in sym["pins"]:
            if (pname, number) in seen:
                continue
            seen.add((pname, number))
            units = ", ".join("all" if u == 0 else str(u) for u in sorted(set(units_of.get(pname, [])))) if many else ""
            pins.append((pname, number, values.get(f"Pin.{bare(pname)}", ""), etype, units))
        out.append(Symbol(
            library=lib_file.stem, name=name, description=values.get("Description", ""),
            fields=[(k, v, h) for k, v, h in f if k not in _NOT_FIELDS and not k.startswith("Pin.")],
            pins=pins, units=rendered.get(name) or by_slug.get(slug(name), [])))
    return out


def link_cell(symbol: Symbol, kind: str, name: str, bindings: list[dict]) -> str:
    """The rule links of one pin or field row: every binding whose selector matches the symbol."""
    facts = symbol.facts()
    links = [f'<a href="{html.escape(b.get("href", "#"))}">{html.escape(b["feature"])}</a>'
             for b in bindings if b.get(kind) == name and matches(b.get("match", {}), facts)]
    return "<br>".join(links)


def symbol_html(s: Symbol, bindings: list[dict]) -> str:
    e = html.escape
    rules = bool(bindings)
    rule_th = "<th>Rule</th>" if rules else ""
    rows = []
    named = "${Value}" in dict((k, v) for k, v, _ in s.fields).get("Name", "")
    for k, v, hidden in s.fields:
        # Empty means the user fills it. Value is also the user's when Name follows it: its library text is a sample.
        by_user = v == "" or (k == "Value" and named)
        who = '<span class="user">you</span>' if by_user else '<span class="fixed">the symbol</span>'
        rule = f"<td>{link_cell(s, 'field', k, bindings)}</td>" if rules else ""
        rows.append(f'<tr id="{s.anchor}-field-{slug(k)}"><td>{e(k)}</td><td>{who}</td><td><code>{e(v)}</code></td>'
                    f'<td>{"hidden" if hidden else "shown"}</td>{rule}</tr>')
    fields = ('<table class="fields"><caption>Fields</caption><tr><th>Field</th><th>Set by</th><th>Library value</th>'
              f'<th>On the sheet</th>{rule_th}</tr>{"".join(rows)}</table>') if rows else ""
    has_units = any(p[4] for p in s.pins)
    rows = []
    for name, number, kind, direction, units in s.pins:
        rule = f"<td>{link_cell(s, 'pin', bare(name), bindings)}</td>" if rules else ""
        low = ' <span class="low">asserted low</span>' if name.startswith("~{") else ""
        unit = f"<td>{e(units)}</td>" if has_units else ""
        rows.append(f'<tr id="{s.anchor}-pin-{slug(bare(name))}-{slug(number)}"><td>{e(bare(name))}{low}</td><td>{e(number)}</td>'
                    f"{unit}<td>{e(kind)}</td><td>{e(direction)}</td>{rule}</tr>")
    pins = ('<table class="pins"><caption>Pins</caption><tr><th>Pin</th><th>Number</th>'
            f'{"<th>Unit</th>" if has_units else ""}<th>Kind</th><th>Direction</th>{rule_th}</tr>{"".join(rows)}</table>') if rows else ""
    figs = "".join(f'<figure>{svg}<figcaption>unit {u}</figcaption></figure>' if len(s.units) > 1 else f"<figure>{svg}</figure>"
                   for u, svg in s.units)
    desc = f"<p class=\"description\">{e(s.description)}</p>" if s.description else '<p class="description none">No Description.</p>'
    return (f'<article class="symbol" id="{s.anchor}"><h3><span class="lib">{e(s.library)}:</span>{e(s.name)}</h3>{desc}'
            f'<div class="units">{figs}</div>{fields}{pins}</article>')


def selector_text(selector: dict) -> str:
    return ", ".join(f"{k} {v if isinstance(v, str) else ' or '.join(v)}" for k, v in selector.items() if k != "library")


def build(libdir: Path, prose: Path, bindings: list[dict]) -> tuple[str, list[str]]:
    """(page, problems)."""
    e = html.escape
    problems: list[str] = []
    symbols = [s for lib in LIBRARIES for s in read_library(libdir / f"{lib}.kicad_sym")]
    groups = tomllib.loads((prose / "groups.toml").read_text())["group"] if (prose / "groups.toml").exists() else []
    if not groups:
        problems.append(f"{prose / 'groups.toml'}: no groups")
    members: dict[str, list[Symbol]] = {g["id"]: [] for g in groups}
    stray: list[Symbol] = []
    for s in symbols:
        facts = s.facts()
        home = next((g for g in groups if matches(g["match"], facts)), None)
        (members[home["id"]] if home else stray).append(s)
        if not s.units:
            problems.append(f"{s.library}:{s.name}: no rendered unit")
    for s in stray:
        problems.append(f"{s.library}:{s.name}: no group matches it")

    tabs, navs = [], []
    for lib in LIBRARIES:
        body, nav = [], []
        for g in (g for g in groups if g["library"] == lib):
            syms = members[g["id"]]
            frag = prose / f"{g['id']}.html"
            if not syms:
                problems.append(f"group {g['id']}: matches no symbol")
            if frag.exists():
                text = frag.read_text()
            else:
                problems.append(f"group {g['id']}: no fragment {frag.name}")
                text = '<p class="none">No usage text yet.</p>'
            gid = f"group-{slug(g['id'])}"
            body.append(f'<details class="group" id="{gid}" open><summary><h2>{e(g["title"])}</h2>'
                        f'<span class="match">{e(selector_text(g["match"]))}</span></summary>'
                        f'<div class="prose">{text}</div>{"".join(symbol_html(s, bindings) for s in syms)}</details>')
            nav.append(f'<li><a href="#{gid}">{e(g["title"])}</a><ul>'
                       + "".join(f'<li><a href="#{s.anchor}">{e(s.name)}</a></li>' for s in syms) + "</ul></li>")
        strays = [s for s in stray if s.library == lib]
        if strays:
            body.append('<details class="group" id="group-none-' + slug(lib) + '" open><summary><h2>Not in a group</h2></summary>'
                        + "".join(symbol_html(s, bindings) for s in strays) + "</details>")
        tabs.append(f'<section class="tab" id="tab-{slug(lib)}" hidden>{"".join(body)}</section>')
        navs.append(f'<ul class="index" data-tab="tab-{slug(lib)}" hidden>{"".join(nav)}</ul>')
    intro = (prose / "intro.html").read_text() if (prose / "intro.html").exists() else ""
    buttons = ('<button data-tab="tab-about">About</button>' if intro else "") + "".join(
        f'<button data-tab="tab-{slug(lib)}">{e(lib.removeprefix("Railroad-"))}</button>' for lib in LIBRARIES)
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Railroad symbols manual</title>
<style>
{(_HERE / "symbol_manual.css").read_text()}</style></head>
<body>
<header><h1>Railroad symbols manual</h1><nav class="tabs">{buttons}</nav>
<span class="tools"><button id="open-all">Show all groups</button><button id="close-all">Hide all groups</button></span></header>
<div class="layout"><nav class="side">{"".join(navs)}</nav>
<main>{f'<section class="tab prose" id="tab-about" hidden>{intro}</section>' if intro else ""}{"".join(tabs)}</main></div>
<script>
{(_HERE / "symbol_manual.js").read_text()}</script>
</body></html>
"""
    return page, problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--libdir", type=Path, default=LIBDIR)
    ap.add_argument("--prose", type=Path, default=None, help="groups.toml and the fragments (default <libdir>/manual)")
    ap.add_argument("--out", type=Path, default=None, help="output directory (default <libdir>/production/manual)")
    ap.add_argument("--bindings", type=Path, default=None, help="JSON list of rule links (see the module text)")
    a = ap.parse_args(argv)
    out = a.out or a.libdir / "production" / "manual"
    bindings = json.loads(a.bindings.read_text()) if a.bindings else []
    page, problems = build(a.libdir, a.prose or a.libdir / "manual", bindings)
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(page)
    for p in problems:
        print(p, file=sys.stderr)
    print(f"{out / 'index.html'}: {len(page) // 1024} KiB, {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
