#!/usr/bin/env python3
"""Write a static HTML overview of KiCad symbol libraries: every field, pin, unit and graphic.

    python3 tools/kicad_library_overview.py LIB.kicad_sym [LIB2.kicad_sym ...] [--out DIR] [--title TEXT] [--no-render]

One row per symbol: library, symbol name, every property (the standard KiCad fields first, then
Role, Appliance, Style, IC, Address, Invert, then Pin.* sorted, then the rest sorted), the pins
(name, number, electrical type and the Pin.<base> value when the symbol has one), the unit
structure, and one SVG per unit from `kicad-cli sym export svg`, written to <out>/svg-<library>/
and referenced by relative path. The page is plain HTML with inline CSS and JavaScript (no server,
no CDN): the table sorts on any column, filters by a search box and per-column boxes, and shows
or hides columns (with a filter and All/None for the dozens of Pin.* fields); fields that no symbol
fills start hidden; the column set and sort order are remembered in localStorage when available.

The default <out> is <directory of the first library>/production/overview/ (the Railroad repo
gitignores production/). `--no-render` skips kicad-cli and omits the graphics column.
"""

from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kicad_services.sch_text import library_standard_properties, library_symbols  # noqa: E402

KICAD_CLI_APP = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
PAGE_NAME = "library-overview.html"
LEAD_FIELDS = ("Role", "Appliance", "Style")            # shown first, before the graphics
NAMED_FIELDS = ("Description", "IC", "Address", "Invert", "Reference", "Value", "Footprint", "Datasheet")
FIXED_HEAD = ("Library", "Symbol", "Extends")
ALWAYS_SHOWN = {"Library", "Symbol", "Extends", "Role", "Appliance", "Style", "Graphics", "Description", "Pins", "Units"}
_SVG_NAME = re.compile(r"^(.*)_unit(\d+)$")


@dataclass
class Symbol:
    library: str
    name: str
    fields: dict[str, str]
    pins: list[tuple[str, str, str]]          # (name, number, electrical type)
    units: dict[int, list[str]]               # unit number -> pin names (0 = common to all units)
    extends: str | None = None
    graphics: list[str] = field(default_factory=list)  # SVG paths relative to the page


def find_kicad_cli() -> str | None:
    """kicad-cli from KICAD_CLI, then PATH, then the macOS app bundle; None when absent."""
    for candidate in (os.environ.get("KICAD_CLI"), shutil.which("kicad-cli"), KICAD_CLI_APP):
        if candidate and Path(candidate).is_file():
            return candidate
    return None


def pin_base(name: str) -> str:
    """The Pin.<base> field name for a pin: `~{OCC}` (overbar) has the base `OCC`."""
    m = re.match(r"^~\{(.+)\}$", name)
    return m.group(1) if m else name


def property_columns(names: set[str]) -> list[str]:
    """Stable column order for the union of field names across the symbols: Role, Appliance, Style,
    Description, the other named fields, Pin.* sorted, then everything else sorted."""
    head = [n for n in LEAD_FIELDS + NAMED_FIELDS if n in names]
    pins = sorted(n for n in names if n.startswith("Pin."))
    rest = sorted(names - set(head) - set(pins), key=lambda n: (n.lower(), n))
    return head + pins + rest


def load_library(lib_file: Path) -> list[Symbol]:
    """The symbols of one library in file order; a derived symbol inherits what it does not restate."""
    text = lib_file.read_text()
    standard = library_standard_properties(text)
    symbols = library_symbols(text)
    out: dict[str, Symbol] = {}
    for name, sym in symbols.items():
        fields = {**standard.get(name, {}), **sym["properties"]}
        s = Symbol(lib_file.stem, name, fields, list(sym["pins"]), dict(sym["units"]), sym["extends"])
        parent = out.get(s.extends) if s.extends else None
        if parent:
            s.fields = {**parent.fields, **s.fields}
            s.pins = s.pins or parent.pins
            s.units = s.units or parent.units
        out[name] = s
    return list(out.values())


def render(kicad_cli: str, lib_file: Path, svg_dir: Path) -> dict[str, list[str]]:
    """{symbol name: [svg file names]} after rendering every unit of lib_file into svg_dir."""
    shutil.rmtree(svg_dir, ignore_errors=True)
    svg_dir.mkdir(parents=True)
    subprocess.run([kicad_cli, "sym", "export", "svg", "-o", str(svg_dir), str(lib_file)],
                   check=True, capture_output=True)
    files: dict[str, list[tuple[int, str]]] = {}
    for f in svg_dir.iterdir():
        m = _SVG_NAME.match(f.stem)
        if m and f.suffix == ".svg":
            files.setdefault(m.group(1), []).append((int(m.group(2)), f.name))
    return {name: [n for _, n in sorted(units)] for name, units in files.items()}


# --- page -----------------------------------------------------------------------------------

STYLE = """
body{font:13px/1.4 system-ui,sans-serif;margin:1em;color:#222;background:#fff}
h1{font-size:1.4em;margin:0 0 .3em}
.meta{color:#666;margin-bottom:.8em}
.controls{display:flex;flex-wrap:wrap;gap:.6em 1.2em;align-items:center;margin-bottom:.8em}
.controls input[type=search]{font:inherit;padding:.3em .5em;width:22em;max-width:100%}
.controls button{font:inherit;padding:.25em .7em}
#count{color:#666}
details.columns{position:relative}
details.columns summary{cursor:pointer;user-select:none}
details.columns div{position:absolute;z-index:3;background:#fff;border:1px solid #bbb;box-shadow:0 2px 8px #0003;
  padding:.5em .8em;columns:3;column-gap:1.4em;min-width:36em;max-height:60vh;overflow:auto}
details.columns label{display:block;white-space:nowrap;break-inside:avoid}
table{border-collapse:collapse;width:100%}
th,td{border:1px solid #ccc;padding:3px 5px;vertical-align:top;text-align:left;overflow-wrap:anywhere}
thead th{position:sticky;top:0;background:#eef;z-index:2}
thead th.sortable{cursor:pointer;user-select:none;white-space:nowrap}
thead th.sortable::after{content:" \\2195";color:#99a}
thead th.asc::after{content:" \\2191";color:#226}
thead th.desc::after{content:" \\2193";color:#226}
thead tr.filters th{top:1.9em;background:#f6f6fb;padding:1px 2px;font-weight:normal}
thead tr.filters input{font:inherit;width:100%;box-sizing:border-box;padding:2px 3px}
tbody tr:nth-child(even){background:#fafafa}
tbody tr:hover{background:#f0f4ff}
td.wrap{min-width:12em;max-width:28em}
td.empty::after{content:"\\00b7";color:#aaa}
td.symbol{font-weight:600;white-space:nowrap}
ul.pins,ul.units{margin:0;padding-left:1.1em;min-width:10em}
ul.pins li,ul.units li{white-space:nowrap}
ul.pins .num{color:#666}
ul.pins .etype{color:#36a}
ul.pins .cap{color:#262}
td.graphics{white-space:nowrap}
td.graphics img{max-width:240px;max-height:170px;background:#fff;border:1px solid #ddd;margin:2px;vertical-align:top}
"""

SCRIPT = r"""
(function () {
  'use strict';
  var KEY = 'kicad-library-overview:' + document.title;
  var table = document.getElementById('symbols');
  var heads = Array.prototype.slice.call(table.tHead.rows[0].cells);
  var filterCells = Array.prototype.slice.call(table.tHead.rows[1].cells);
  var filters = filterCells.map(function (c) { return c.querySelector('input'); });
  var rows = Array.prototype.slice.call(table.tBodies[0].rows);
  rows.forEach(function (r, i) { r.dataset.index = i; });
  var search = document.getElementById('search');
  var count = document.getElementById('count');
  var toggles = Array.prototype.slice.call(document.querySelectorAll('#columns input[type=checkbox]'));
  var labels = toggles.map(function (b) { return b.parentNode; });
  var colfilter = document.getElementById('colfilter');
  var defaultHidden = toggles.filter(function (b) { return !b.checked; }).map(function (b) { return b.value; });
  var state = { hidden: defaultHidden.slice(), sort: null };

  function load() {
    try {
      var s = JSON.parse(localStorage.getItem(KEY));
      if (s && Array.isArray(s.hidden)) { state = { hidden: s.hidden, sort: s.sort || null }; }
    } catch (e) { /* storage unavailable or corrupt: defaults */ }
  }
  function applyColumnFilter() {
    var q = colfilter.value.toLowerCase();
    labels.forEach(function (l, i) { l.hidden = !!q && toggles[i].value.toLowerCase().indexOf(q) < 0; });
  }
  function setVisibleToggles(on) {
    toggles.forEach(function (b, i) { if (!labels[i].hidden) { b.checked = on; } });
    state.hidden = toggles.filter(function (b) { return !b.checked; }).map(function (b) { return b.value; });
    save();
    applyColumns();
  }
  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) { /* ignore */ }
  }
  function cellText(cell) {
    return cell.dataset.sort !== undefined ? cell.dataset.sort : cell.textContent.trim();
  }
  function applyColumns() {
    var hidden = {};
    state.hidden.forEach(function (n) { hidden[n] = true; });
    heads.forEach(function (th, i) {
      var on = !hidden[th.dataset.col];
      th.hidden = !on;
      filterCells[i].hidden = !on;
      rows.forEach(function (r) { r.cells[i].hidden = !on; });
      toggles[i].checked = on;
    });
  }
  function applyFilter() {
    var q = search.value.toLowerCase();
    var shown = 0;
    rows.forEach(function (r) {
      var ok = !q || r.textContent.toLowerCase().indexOf(q) >= 0;
      for (var i = 0; ok && i < filters.length; i++) {
        if (filters[i] && filters[i].value) {
          ok = cellText(r.cells[i]).toLowerCase().indexOf(filters[i].value.toLowerCase()) >= 0;
        }
      }
      r.hidden = !ok;
      if (ok) { shown++; }
    });
    count.textContent = shown + ' of ' + rows.length + ' symbols';
  }
  function applySort() {
    heads.forEach(function (th) { th.classList.remove('asc', 'desc'); });
    var order = rows.slice();
    if (state.sort) {
      var i = -1;
      heads.forEach(function (th, k) { if (th.dataset.col === state.sort.col) { i = k; } });
      if (i >= 0) {
        heads[i].classList.add(state.sort.dir);
        var dir = state.sort.dir === 'desc' ? -1 : 1;
        order.sort(function (a, b) {
          var x = cellText(a.cells[i]), y = cellText(b.cells[i]);
          if (x === '' && y !== '') { return 1; }   // empty cells last either way
          if (y === '' && x !== '') { return -1; }
          var c = x.localeCompare(y, undefined, { numeric: true, sensitivity: 'base' });
          return c !== 0 ? c * dir : a.dataset.index - b.dataset.index;
        });
      }
    }
    var body = table.tBodies[0];
    order.forEach(function (r) { body.appendChild(r); });
  }

  heads.forEach(function (th) {
    if (!th.classList.contains('sortable')) { return; }
    th.addEventListener('click', function () {
      var col = th.dataset.col;
      if (state.sort && state.sort.col === col) {
        state.sort = state.sort.dir === 'asc' ? { col: col, dir: 'desc' } : null;
      } else {
        state.sort = { col: col, dir: 'asc' };
      }
      save();
      applySort();
    });
  });
  toggles.forEach(function (box) {
    box.addEventListener('change', function () {
      state.hidden = toggles.filter(function (b) { return !b.checked; }).map(function (b) { return b.value; });
      save();
      applyColumns();
    });
  });
  search.addEventListener('input', applyFilter);
  colfilter.addEventListener('input', applyColumnFilter);
  document.getElementById('colall').addEventListener('click', function () { setVisibleToggles(true); });
  document.getElementById('colnone').addEventListener('click', function () { setVisibleToggles(false); });
  filters.forEach(function (f) { if (f) { f.addEventListener('input', applyFilter); } });
  document.getElementById('reset').addEventListener('click', function () {
    search.value = '';
    filters.forEach(function (f) { if (f) { f.value = ''; } });
    colfilter.value = '';
    applyColumnFilter();
    state = { hidden: defaultHidden.slice(), sort: null };
    try { localStorage.removeItem(KEY); } catch (e) { /* ignore */ }
    applyColumns();
    applySort();
    applyFilter();
  });

  load();
  applyColumns();
  applySort();
  applyFilter();
})();
"""


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def pins_cell(sym: Symbol) -> str:
    if not sym.pins:
        return "<td></td>"
    items = []
    for name, number, etype in sym.pins:
        cap = sym.fields.get("Pin." + pin_base(name))
        items.append(f'<li>{esc(name)} <span class="num">({esc(number)})</span> <span class="etype">{esc(etype)}</span>'
                     + (f' <span class="cap">= {esc(cap)}</span>' if cap else "") + "</li>")
    return '<td><ul class="pins">' + "".join(items) + "</ul></td>"


def units_cell(sym: Symbol) -> str:
    if not sym.units:
        return "<td></td>"
    items = []
    for unit in sorted(sym.units):
        label = "common" if unit == 0 else f"unit {unit}"
        pins = ", ".join(sym.units[unit]) or "(no pins)"
        items.append(f"<li>{label}: {esc(pins)}</li>")
    n = len([u for u in sym.units if u != 0])
    return f'<td data-sort="{n}"><ul class="units">' + "".join(items) + "</ul></td>"


def graphics_cell(sym: Symbol) -> str:
    imgs = "".join(f'<img src="{esc(p)}" alt="{esc(Path(p).stem)}" title="{esc(p)}" loading="lazy">' for p in sym.graphics)
    return f'<td class="graphics" data-sort="{len(sym.graphics)}">{imgs}</td>'


def field_cell(sym: Symbol, name: str) -> str:
    value = sym.fields.get(name)
    if value is None:
        return "<td></td>"
    cls = "wrap" if name in ("Description", "ki_keywords") or len(value) > 40 else ""
    if not value:
        cls = (cls + " empty").strip()
    return f'<td class="{cls}">{esc(value)}</td>' if cls else f"<td>{esc(value)}</td>"


def build_page(symbols: list[Symbol], title: str, libraries: list[Path], graphics: bool) -> tuple[str, list[str]]:
    """(html, column names)."""
    props = property_columns({n for s in symbols for n in s.fields})
    head = [c for c in FIXED_HEAD if c != "Extends" or any(s.extends for s in symbols)]
    lead = [c for c in LEAD_FIELDS if c in props]
    desc = ["Description"] if "Description" in props else []
    rest = [p for p in props if p not in lead and p != "Description"]
    columns = head + lead + (["Graphics"] if graphics else []) + desc + ["Pins", "Units"] + rest
    unfilterable = {"Graphics"}
    # The rest of the fields start hidden when no symbol gives them a value; the Columns control shows them.
    shown = {c for c in columns if c in ALWAYS_SHOWN or any(s.fields.get(c) for s in symbols)}

    header = "".join(f'<th class="sortable" data-col="{esc(c)}">{esc(c)}</th>' for c in columns)
    filter_row = "".join("<th></th>" if c in unfilterable else
                         f'<th><input type="search" placeholder="filter" aria-label="filter {esc(c)}"></th>'
                         for c in columns)
    toggles = "".join(f'<label><input type="checkbox" value="{esc(c)}"{" checked" if c in shown else ""}> {esc(c)}</label>'
                      for c in columns)

    def cell(s: Symbol, c: str) -> str:
        if c == "Library":
            return f"<td>{esc(s.library)}</td>"
        if c == "Symbol":
            return f'<td class="symbol">{esc(s.name)}</td>'
        if c == "Extends":
            return f"<td>{esc(s.extends or '')}</td>"
        if c == "Graphics":
            return graphics_cell(s)
        if c == "Pins":
            return pins_cell(s)
        if c == "Units":
            return units_cell(s)
        return field_cell(s, c)

    rows = ["<tr>" + "".join(cell(s, c) for c in columns) + "</tr>" for s in symbols]

    sources = ", ".join(esc(p.name) for p in libraries)
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<style>{STYLE}</style>
</head>
<body>
<h1>{esc(title)}</h1>
<p class="meta">{len(symbols)} symbols from {sources}. Click a header to sort (again to reverse, a third time to clear).
Pins read name (number) electrical type = Pin.&lt;base&gt; value. A middle dot marks a field that is present but empty.</p>
<div class="controls">
<input type="search" id="search" placeholder="search all columns" aria-label="search all columns">
<details class="columns"><summary>Columns</summary><div id="columns">
<p class="colctl"><input type="search" id="colfilter" placeholder="filter columns" aria-label="filter columns">
<button type="button" id="colall">All</button> <button type="button" id="colnone">None</button></p>
{toggles}</div></details>
<button type="button" id="reset">Reset view</button>
<span id="count"></span>
</div>
<table id="symbols">
<thead>
<tr class="headers">{header}</tr>
<tr class="filters">{filter_row}</tr>
</thead>
<tbody>
{chr(10).join(rows)}
</tbody>
</table>
<script>{SCRIPT}</script>
</body>
</html>
"""
    return page, columns


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("libraries", nargs="+", type=Path, metavar="LIB.kicad_sym")
    ap.add_argument("--out", type=Path, default=None, help="output directory (default: <first library dir>/production/overview)")
    ap.add_argument("--title", default="KiCad symbol library overview")
    ap.add_argument("--no-render", action="store_true", help="skip kicad-cli; omit the graphics column")
    a = ap.parse_args(argv)

    for lib in a.libraries:
        if not lib.is_file():
            ap.error(f"not a file: {lib}")
    out = a.out or a.libraries[0].resolve().parent / "production" / "overview"
    out.mkdir(parents=True, exist_ok=True)

    kicad_cli = None
    if not a.no_render:
        kicad_cli = find_kicad_cli()
        if not kicad_cli:
            ap.error("kicad-cli not found (set KICAD_CLI, add it to PATH, or pass --no-render)")

    symbols: list[Symbol] = []
    for lib in a.libraries:
        loaded = load_library(lib)
        if kicad_cli:
            svg_dir = out / f"svg-{lib.stem}"
            files = render(kicad_cli, lib, svg_dir)
            for s in loaded:
                s.graphics = [f"{svg_dir.name}/{f}" for f in files.get(s.name, [])]
        symbols += loaded

    page, _ = build_page(symbols, a.title, a.libraries, graphics=kicad_cli is not None)
    page_file = out / PAGE_NAME
    page_file.write_text(page)
    print(f"{page_file}: {len(symbols)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
