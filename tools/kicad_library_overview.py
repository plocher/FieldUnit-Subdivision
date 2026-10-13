#!/usr/bin/env python3
"""Write a static HTML overview of KiCad symbol libraries: every field, pin, unit and graphic.

    python3 tools/kicad_library_overview.py LIB.kicad_sym [LIB2.kicad_sym ...] [--out DIR] [--title TEXT] [--no-render]

One row per symbol: library, symbol name, every property (the standard KiCad fields first, then
Role, Appliance, Style, IC, Address, Invert, then Pin.* sorted, then the rest sorted), the pins
(name, number, electrical type and the Pin.<base> value when the symbol has one), the unit
structure, and one SVG per unit from `kicad-cli sym export svg`, written to <out>/svg-<library>/
and referenced by relative path. The page is plain HTML with inline CSS and JavaScript (no server,
no CDN): the table sorts on several columns at once (click a header to add it as the lowest key,
again to reverse it, a third time to drop it; each sorting header shows its priority and direction),
filters by a search box, per-column text boxes and a per-column value picker (a funnel button
listing the distinct values with counts), and shows or hides columns. The Columns control groups
them (Core, KiCad fields, Contract, Pin.*, Settings, Other), each group with a tri-state parent
checkbox, a shown/total count and a fold; shift-click selects a range within a group; a text
filter and All/None act on the filtered entries; "Show only Core" and "Show all" are one click, and
a right-click on a table header offers hide this column, hide its group, show only Core and show
all. Fields that no symbol fills start hidden. Column widths can be dragged at the header's right
edge and columns reordered by dragging a header onto another; the graphics have an S/M/L/XL size
control. The column set, order, widths, image size, sort keys and folded groups are remembered in
localStorage when available (under a versioned key); the value filters are not.

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
# Column groups of the Columns control, in display order. Core is ALWAYS_SHOWN; Pin.* is every Pin.<base>
# field; Settings is every lower_snake_case field; Other is whatever is left (Kind, ki_* excluded by Settings).
KICAD_FIELDS = ("Reference", "Value", "Footprint", "Datasheet")
CONTRACT_FIELDS = ("IC", "Address", "Invert", "Color", "IndicationToken", "IndicationCeiling", "CP", "TC",
                   "Processor", "Display", "Milepost")
GROUPS = ("Core", "KiCad fields", "Contract", "Pin.*", "Settings", "Other")
DEFAULT_CLOSED_GROUPS = ("Pin.*", "Settings")
_SNAKE_CASE = re.compile(r"^[a-z][a-z0-9_]*$")
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


def column_group(name: str) -> str:
    """The Columns-control group of a column: one of GROUPS."""
    if name in ALWAYS_SHOWN:
        return "Core"
    if name in KICAD_FIELDS:
        return "KiCad fields"
    if name in CONTRACT_FIELDS:
        return "Contract"
    if name.startswith("Pin."):
        return "Pin.*"
    if _SNAKE_CASE.match(name):
        return "Settings"
    return "Other"


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
.controls button,.controls select{font:inherit;padding:.25em .7em}
#count{color:#666}
[hidden]{display:none!important}
details.columns{position:relative}
details.columns summary{cursor:pointer;user-select:none}
#columns{position:absolute;z-index:3;background:#fff;border:1px solid #bbb;box-shadow:0 2px 8px #0003;
  padding:.5em .8em;min-width:40em;max-height:70vh;overflow:auto}
#columns p{margin:.2em 0 .5em}
#columns .colgroup{border-top:1px solid #ddd;padding:.3em 0}
#columns .grouphead{display:flex;align-items:center;gap:.3em;font-weight:600}
#columns .grouphead .fold{font:inherit;width:1.6em;padding:0;border:0;background:none;cursor:pointer;color:#669}
#columns .n{color:#666;font-weight:normal}
#columns .members{columns:3;column-gap:1.4em;padding-left:1.9em}
#columns .colgroup.closed .members{display:none}
#columns label{display:block;white-space:nowrap;break-inside:avoid}
#colmenu{position:absolute;z-index:5;background:#fff;border:1px solid #bbb;box-shadow:0 2px 8px #0003;padding:.3em 0;min-width:14em}
#colmenu button{display:block;width:100%;text-align:left;font:inherit;padding:.3em 1em;border:0;background:none;cursor:pointer}
#colmenu button:hover{background:#eef}
table{border-collapse:collapse;table-layout:fixed}
th,td{border:1px solid #ccc;padding:3px 5px;vertical-align:top;text-align:left;overflow-wrap:anywhere}
thead th{position:sticky;top:0;background:#eef;z-index:2}
thead th.sortable{cursor:pointer;user-select:none;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;padding-right:12px}
thead th.sortable::after{content:" \\2195";color:#99a}
thead th.asc::after{content:" " attr(data-rank) " \\25b2";color:#226}
thead th.desc::after{content:" " attr(data-rank) " \\25bc";color:#226}
thead th.dragging{opacity:.5}
thead th.dragover{outline:2px solid #58c;outline-offset:-2px}
thead th .grip{position:absolute;top:0;right:0;width:7px;height:100%;cursor:col-resize;user-select:none}
thead th .grip:hover{background:#9ab}
thead tr.filters th{top:1.9em;background:#f6f6fb;padding:1px 2px;font-weight:normal}
thead tr.filters .fwrap{display:flex;gap:2px}
thead tr.filters input{font:inherit;flex:1;min-width:0;box-sizing:border-box;padding:2px 3px}
thead tr.filters .funnel{font:inherit;padding:0 4px;border:1px solid #bbb;background:#fff;color:#669;cursor:pointer}
thead tr.filters .funnel.active{background:#cde;color:#126;border-color:#58c}
#valuepanel{position:absolute;z-index:4;background:#fff;border:1px solid #bbb;box-shadow:0 2px 8px #0003;
  padding:.5em .8em;min-width:16em;max-width:32em;max-height:60vh;overflow:auto}
#valuepanel input[type=search]{font:inherit;width:100%;box-sizing:border-box;padding:2px 3px}
#valuepanel p{margin:.4em 0}
#valuepanel button{font:inherit;padding:.15em .6em}
#valuepanel label{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#valuepanel .n{color:#666}
tbody tr:nth-child(even){background:#fafafa}
tbody tr:hover{background:#f0f4ff}
td.empty::after{content:"\\00b7";color:#aaa}
td.symbol{font-weight:600}
ul.pins,ul.units{margin:0;padding-left:1.1em}
ul.pins .num{color:#666}
ul.pins .etype{color:#36a}
ul.pins .cap{color:#262}
table[data-size=S]{--imgw:240px;--imgh:170px}
table[data-size=M]{--imgw:480px;--imgh:340px}
table[data-size=L]{--imgw:720px;--imgh:500px}
table[data-size=XL]{--imgw:1080px;--imgh:760px}
td.graphics img{width:var(--imgw,720px);height:auto;max-height:var(--imgh,500px);object-fit:contain;
  background:#fff;border:1px solid #ddd;box-sizing:border-box;margin:2px;vertical-align:top}
"""

SCRIPT = r"""
(function () {
  'use strict';
  var KEY = 'kicad-library-overview:v3:' + document.title;   // v3: sort is a list of keys; closed column groups
  var SIZES = { S: 240, M: 480, L: 720, XL: 1080 };           // image box width per size setting
  var table = document.getElementById('symbols');
  var headRow = table.tHead.rows[0], filterRow = table.tHead.rows[1];
  var rows = Array.prototype.slice.call(table.tBodies[0].rows);
  rows.forEach(function (r, i) { r.dataset.index = i; });
  var heads, filterCells, filters;                             // re-read from the DOM after a reorder
  var search = document.getElementById('search');
  var count = document.getElementById('count');
  var columnsBox = document.getElementById('columns');
  var toggles = Array.prototype.slice.call(columnsBox.querySelectorAll('.members input[type=checkbox]'));
  var labels = toggles.map(function (b) { return b.parentNode; });
  var toggleFor = {}, groupOf = {};
  toggles.forEach(function (b) { toggleFor[b.value] = b; groupOf[b.value] = b.closest('.colgroup').dataset.group; });
  var groups = Array.prototype.slice.call(columnsBox.querySelectorAll('.colgroup')).map(function (g) {
    return { name: g.dataset.group, box: g, parent: g.querySelector('.grouptoggle'), fold: g.querySelector('.fold'),
             n: g.querySelector('.grouphead .n'),
             members: toggles.filter(function (b) { return groupOf[b.value] === g.dataset.group; }), last: -1 };
  });
  var colfilter = document.getElementById('colfilter');
  var sizeSelect = document.getElementById('imgsize');
  var panel = document.getElementById('valuepanel');
  var valueSearch = document.getElementById('valuesearch');
  var valueList = document.getElementById('valuelist');
  var menu = document.getElementById('colmenu');
  var defaultHidden = toggles.filter(function (b) { return !b.checked; }).map(function (b) { return b.value; });
  var defaultClosed = groups.filter(function (g) { return g.box.classList.contains('closed'); }).map(function (g) { return g.name; });
  var defaultOrder;
  var state, valueFilter = {}, panelCol = null, menuCol = null, resizing = false, dragCol = null;

  function readHeads() {
    heads = Array.prototype.slice.call(headRow.cells);
    filterCells = Array.prototype.slice.call(filterRow.cells);
    filters = filterCells.map(function (c) { return c.querySelector('input'); });
  }
  readHeads();
  defaultOrder = heads.map(function (th) { return th.dataset.col; });

  function defaults() {
    return { hidden: defaultHidden.slice(), sort: [], widths: {}, order: defaultOrder.slice(), size: 'L',
             closed: defaultClosed.slice() };
  }
  state = defaults();

  function isKey(k) { return k && typeof k.col === 'string' && (k.dir === 'asc' || k.dir === 'desc'); }
  function load() {
    try {
      var s = JSON.parse(localStorage.getItem(KEY));
      if (s && Array.isArray(s.hidden)) {
        state = defaults();
        state.hidden = s.hidden;
        if (Array.isArray(s.sort)) { state.sort = s.sort.filter(isKey); } else if (isKey(s.sort)) { state.sort = [s.sort]; }
        if (s.widths && typeof s.widths === 'object') { state.widths = s.widths; }
        if (Array.isArray(s.order)) { state.order = s.order; }
        if (SIZES[s.size]) { state.size = s.size; }
        if (Array.isArray(s.closed)) { state.closed = s.closed; }
      }
    } catch (e) { /* storage unavailable or corrupt: defaults */ }
  }
  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) { /* ignore */ }
  }
  function elementOf(e) {
    var t = e.target;
    return t && t.nodeType === 1 ? t : (t && t.parentElement) || document.documentElement;
  }
  function cellText(cell) {
    return cell.dataset.sort !== undefined ? cell.dataset.sort : cell.textContent.trim();
  }
  function cellValue(cell) { return cell.textContent.replace(/\s+/g, ' ').trim(); }
  function colIndex(col) {
    for (var i = 0; i < heads.length; i++) { if (heads[i].dataset.col === col) { return i; } }
    return -1;
  }

  // --- columns: visibility, order, widths, image size ---
  function defaultWidth(col) {
    if (col === 'Graphics') { return SIZES[state.size] + 16; }
    if (col === 'Pins' || col === 'Units') { return 220; }
    if (col === 'Description') { return 320; }
    if (col === 'Symbol') { return 160; }
    return 120;
  }
  function applyWidths() {
    var total = 0;
    heads.forEach(function (th) {
      var w = +state.widths[th.dataset.col] > 0 ? +state.widths[th.dataset.col] : defaultWidth(th.dataset.col);
      th.style.width = w + 'px';
      if (!th.hidden) { total += w; }
    });
    table.style.width = total + 'px';
  }
  function applySize() {
    table.dataset.size = state.size;
    if (sizeSelect) { sizeSelect.value = state.size; }
    applyWidths();
  }
  function applyOrder() {
    var current = heads.map(function (th) { return th.dataset.col; });
    var order = state.order.filter(function (c) { return current.indexOf(c) >= 0; });
    current.forEach(function (c) { if (order.indexOf(c) < 0) { order.push(c); } });
    state.order = order;
    if (order.join('\n') === current.join('\n')) { return; }
    [headRow, filterRow].concat(rows).forEach(function (r) {
      var cells = Array.prototype.slice.call(r.cells);
      order.forEach(function (c) { r.appendChild(cells[current.indexOf(c)]); });
    });
    readHeads();
  }
  function moveColumn(from, to) {
    var order = heads.map(function (th) { return th.dataset.col; });
    order.splice(order.indexOf(from), 1);
    order.splice(order.indexOf(to), 0, from);
    state.order = order;
    applyOrder();
    save();
  }
  function applyColumnFilter() {
    // A text filter shows the matching entries of every group, folded or not; groups without a match are hidden.
    var q = colfilter.value.toLowerCase();
    labels.forEach(function (l, i) { l.hidden = !!q && toggles[i].value.toLowerCase().indexOf(q) < 0; });
    groups.forEach(function (g) {
      var any = g.members.some(function (b) { return !b.parentNode.hidden; });
      g.box.hidden = !!q && !any;
      g.box.classList.toggle('closed', !q && state.closed.indexOf(g.name) >= 0);
      g.fold.textContent = g.box.classList.contains('closed') ? '▸' : '▾';
      g.fold.title = g.box.classList.contains('closed') ? 'Expand' : 'Collapse';
    });
  }
  function readToggles() {
    state.hidden = toggles.filter(function (b) { return !b.checked; }).map(function (b) { return b.value; });
    save();
    applyColumns();
  }
  function setVisibleToggles(on) {
    toggles.forEach(function (b, i) { if (!labels[i].hidden) { b.checked = on; } });
    readToggles();
  }
  function setToggles(wanted) {                                // wanted(col) -> true, false or undefined (leave)
    toggles.forEach(function (b) { var on = wanted(b.value); if (on !== undefined) { b.checked = on; } });
    readToggles();
  }
  function showOnlyCore() { setToggles(function (c) { return groupOf[c] === 'Core'; }); }
  function showAll() { setToggles(function () { return true; }); }
  function hideColumn(col) { setToggles(function (c) { return c === col ? false : undefined; }); }
  function hideGroup(name) { setToggles(function (c) { return groupOf[c] === name ? false : undefined; }); }
  function updateGroups() {
    groups.forEach(function (g) {
      var n = g.members.filter(function (b) { return b.checked; }).length;
      g.parent.checked = n === g.members.length;
      g.parent.indeterminate = n > 0 && n < g.members.length;
      g.n.textContent = '(' + n + '/' + g.members.length + ')';
    });
  }
  function applyColumns() {
    var hidden = {};
    state.hidden.forEach(function (n) { hidden[n] = true; });
    heads.forEach(function (th, i) {
      var on = !hidden[th.dataset.col];
      th.hidden = !on;
      filterCells[i].hidden = !on;
      rows.forEach(function (r) { r.cells[i].hidden = !on; });
      toggleFor[th.dataset.col].checked = on;
    });
    updateGroups();
    applyWidths();
  }
  function toggleGroupFold(g) {
    var i = state.closed.indexOf(g.name);
    if (i >= 0) { state.closed.splice(i, 1); } else { state.closed.push(g.name); }
    save();
    applyColumnFilter();
  }

  // --- rows: filter and sort ---
  function applyFilter() {
    var q = search.value.toLowerCase();
    var active = [];
    heads.forEach(function (th, i) {
      var text = filters[i] && filters[i].value ? filters[i].value.toLowerCase() : '';
      var values = valueFilter[th.dataset.col] || null;
      if (text || values) { active.push({ i: i, text: text, values: values }); }
    });
    var shown = 0;
    rows.forEach(function (r) {
      var ok = !q || r.textContent.toLowerCase().indexOf(q) >= 0;
      for (var k = 0; ok && k < active.length; k++) {
        var cell = r.cells[active[k].i];
        if (active[k].text) { ok = cellText(cell).toLowerCase().indexOf(active[k].text) >= 0; }
        if (ok && active[k].values) { ok = !!active[k].values[cellValue(cell)]; }
      }
      r.hidden = !ok;
      if (ok) { shown++; }
    });
    count.textContent = shown + ' of ' + rows.length + ' symbols';
  }
  function applySort() {
    // state.sort lists the keys by priority: [{col, dir}, ...]. Every sorting header shows "<rank> ▲|▼".
    heads.forEach(function (th) { th.classList.remove('asc', 'desc'); th.removeAttribute('data-rank'); });
    state.sort = state.sort.filter(function (k) { return colIndex(k.col) >= 0; });
    var keys = state.sort.map(function (k, rank) {
      var i = colIndex(k.col);
      heads[i].classList.add(k.dir);
      heads[i].dataset.rank = rank + 1;
      return { i: i, dir: k.dir === 'desc' ? -1 : 1 };
    });
    var order = rows.slice();
    if (keys.length) {
      order.sort(function (a, b) {
        for (var k = 0; k < keys.length; k++) {
          var x = cellText(a.cells[keys[k].i]), y = cellText(b.cells[keys[k].i]);
          if (x === '' && y !== '') { return 1; }   // empty cells last either way, per key
          if (y === '' && x !== '') { return -1; }
          var c = x.localeCompare(y, undefined, { numeric: true, sensitivity: 'base' });
          if (c !== 0) { return c * keys[k].dir; }
        }
        return a.dataset.index - b.dataset.index;   // stable: original row order
      });
    }
    var body = table.tBodies[0];
    order.forEach(function (r) { body.appendChild(r); });
  }
  function cycleSort(col) {
    // not a key -> appended ascending; ascending -> descending; descending -> removed
    var i = -1;
    state.sort.forEach(function (k, n) { if (k.col === col) { i = n; } });
    if (i < 0) { state.sort.push({ col: col, dir: 'asc' }); }
    else if (state.sort[i].dir === 'asc') { state.sort[i] = { col: col, dir: 'desc' }; }
    else { state.sort.splice(i, 1); }
    save();
    applySort();
  }

  // --- value filter panel (Excel-style; a working filter, never saved) ---
  function markFunnels() {
    filterCells.forEach(function (c, i) {
      var b = c.querySelector('.funnel');
      if (!b) { return; }
      var on = !!valueFilter[heads[i].dataset.col];
      b.classList.toggle('active', on);
      b.textContent = on ? '▼' : '▽';
      b.title = on ? 'Value filter active (click to edit)' : 'Filter by value';
    });
  }
  function openPanel(i) {
    var col = heads[i].dataset.col;
    var counts = {}, keys = [];
    rows.forEach(function (r) {
      var v = cellValue(r.cells[i]);
      if (!Object.prototype.hasOwnProperty.call(counts, v)) { counts[v] = 0; keys.push(v); }
      counts[v]++;
    });
    keys.sort(function (a, b) {
      if (a === '') { return -1; }
      if (b === '') { return 1; }
      return a.localeCompare(b, undefined, { numeric: true, sensitivity: 'base' });
    });
    var selected = valueFilter[col];
    valueList.innerHTML = '';
    keys.forEach(function (k) {
      var label = document.createElement('label');
      var box = document.createElement('input');
      box.type = 'checkbox';
      box.value = k;
      box.checked = !selected || !!selected[k];
      label.title = k === '' ? '(blank)' : k;
      label.appendChild(box);
      label.appendChild(document.createTextNode(' ' + label.title + ' '));
      var n = document.createElement('span');
      n.className = 'n';
      n.textContent = '(' + counts[k] + ')';
      label.appendChild(n);
      valueList.appendChild(label);
    });
    valueSearch.value = '';
    panelCol = col;
    panel.hidden = false;
    var rect = filterCells[i].querySelector('.funnel').getBoundingClientRect();
    var left = rect.left + window.pageXOffset;
    var maxLeft = window.pageXOffset + document.documentElement.clientWidth - panel.offsetWidth - 8;
    panel.style.left = Math.max(0, Math.min(left, maxLeft)) + 'px';
    panel.style.top = (rect.bottom + window.pageYOffset + 2) + 'px';
    valueSearch.focus();
  }
  function closePanel() { panel.hidden = true; panelCol = null; }
  function readPanel() {
    var boxes = Array.prototype.slice.call(valueList.querySelectorAll('input'));
    if (boxes.every(function (b) { return b.checked; })) {
      delete valueFilter[panelCol];
    } else {
      var m = {};
      boxes.forEach(function (b) { if (b.checked) { m[b.value] = true; } });
      valueFilter[panelCol] = m;
    }
    markFunnels();
    applyFilter();
  }
  function applyValueSearch() {
    var q = valueSearch.value.toLowerCase();
    Array.prototype.slice.call(valueList.children).forEach(function (l) {
      l.hidden = !!q && l.title.toLowerCase().indexOf(q) < 0;
    });
  }
  function setPanelBoxes(on) {
    Array.prototype.slice.call(valueList.children).forEach(function (l) {
      if (!l.hidden) { l.querySelector('input').checked = on; }
    });
    readPanel();
  }

  // --- header events: sort, resize, reorder ---
  headRow.addEventListener('click', function (e) {
    var el = elementOf(e), th = el.closest('th');
    if (!th || resizing || el.classList.contains('grip')) { return; }
    cycleSort(th.dataset.col);
  });
  // --- header context menu: hide this column, hide its group, show only Core, show all ---
  function closeMenu() { menu.hidden = true; menuCol = null; }
  headRow.addEventListener('contextmenu', function (e) {
    var th = elementOf(e).closest('th');
    if (!th) { return; }
    e.preventDefault();
    closePanel();
    menuCol = th.dataset.col;
    menu.querySelector('[data-act=hide]').textContent = 'Hide this column (' + menuCol + ')';
    menu.querySelector('[data-act=hidegroup]').textContent = 'Hide all ' + groupOf[menuCol] + ' columns';
    menu.hidden = false;
    var maxLeft = window.pageXOffset + document.documentElement.clientWidth - menu.offsetWidth - 8;
    menu.style.left = Math.max(0, Math.min(e.pageX, maxLeft)) + 'px';
    menu.style.top = e.pageY + 'px';
  });
  menu.addEventListener('click', function (e) {
    var act = elementOf(e).closest('button') ? elementOf(e).closest('button').dataset.act : null;
    var col = menuCol;
    closeMenu();
    if (act === 'hide') { hideColumn(col); }
    else if (act === 'hidegroup') { hideGroup(groupOf[col]); }
    else if (act === 'core') { showOnlyCore(); }
    else if (act === 'all') { showAll(); }
  });
  headRow.addEventListener('mousedown', function (e) {
    var el = elementOf(e);
    if (!el.classList.contains('grip')) { return; }
    e.preventDefault();
    e.stopPropagation();
    var th = el.parentNode, startX = e.clientX, startW = th.getBoundingClientRect().width;
    resizing = true;
    function move(ev) {
      state.widths[th.dataset.col] = Math.max(40, Math.round(startW + ev.clientX - startX));
      applyWidths();
    }
    function up() {
      document.removeEventListener('mousemove', move);
      document.removeEventListener('mouseup', up);
      save();
      setTimeout(function () { resizing = false; }, 0);   // swallow the click that follows the mouseup
    }
    document.addEventListener('mousemove', move);
    document.addEventListener('mouseup', up);
  });
  headRow.addEventListener('dragstart', function (e) {
    var th = elementOf(e).closest('th');
    if (!th || resizing) { e.preventDefault(); return; }
    dragCol = th.dataset.col;
    th.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', dragCol);
  });
  headRow.addEventListener('dragover', function (e) {
    var th = elementOf(e).closest('th');
    if (!th || !dragCol || th.dataset.col === dragCol) { return; }
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    th.classList.add('dragover');
  });
  headRow.addEventListener('dragleave', function (e) {
    var th = elementOf(e).closest('th');
    if (th) { th.classList.remove('dragover'); }
  });
  headRow.addEventListener('drop', function (e) {
    var th = elementOf(e).closest('th');
    if (!th || !dragCol) { return; }
    e.preventDefault();
    th.classList.remove('dragover');
    if (th.dataset.col !== dragCol) { moveColumn(dragCol, th.dataset.col); }
  });
  headRow.addEventListener('dragend', function () {
    heads.forEach(function (th) { th.classList.remove('dragging', 'dragover'); });
    dragCol = null;
  });

  // --- filter row and panel events ---
  filterRow.addEventListener('click', function (e) {
    var el = elementOf(e);
    if (!el.classList.contains('funnel')) { return; }
    var i = filterCells.indexOf(el.closest('th'));
    if (panelCol === heads[i].dataset.col) { closePanel(); } else { openPanel(i); }
  });
  filters.forEach(function (f) { if (f) { f.addEventListener('input', applyFilter); } });
  valueList.addEventListener('change', readPanel);
  valueSearch.addEventListener('input', applyValueSearch);
  document.getElementById('valall').addEventListener('click', function () { setPanelBoxes(true); });
  document.getElementById('valclear').addEventListener('click', function () { setPanelBoxes(false); });
  document.addEventListener('mousedown', function (e) {
    var el = elementOf(e);
    if (!panel.hidden && !panel.contains(el) && !el.classList.contains('funnel')) { closePanel(); }
    if (!menu.hidden && !menu.contains(el)) { closeMenu(); }
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { closePanel(); closeMenu(); }
  });

  // --- Columns control: entries (shift-click selects a range within the group), group parents, folds, bulk ---
  groups.forEach(function (g) {
    g.members.forEach(function (box, n) {
      box.addEventListener('click', function (e) {
        var on = box.checked;                                  // already toggled by the click
        if (e.shiftKey && g.last >= 0 && g.last !== n) {
          var lo = Math.min(g.last, n), hi = Math.max(g.last, n);
          for (var k = lo; k <= hi; k++) { if (!g.members[k].parentNode.hidden) { g.members[k].checked = on; } }
        }
        g.last = n;
        readToggles();
      });
    });
    g.parent.addEventListener('click', function () {
      var on = g.parent.checked;                               // an indeterminate parent becomes checked
      g.members.forEach(function (b) { b.checked = on; });
      readToggles();
    });
    g.fold.addEventListener('click', function () { toggleGroupFold(g); });
  });
  search.addEventListener('input', applyFilter);
  colfilter.addEventListener('input', applyColumnFilter);
  document.getElementById('colall').addEventListener('click', function () { setVisibleToggles(true); });
  document.getElementById('colnone').addEventListener('click', function () { setVisibleToggles(false); });
  document.getElementById('colcore').addEventListener('click', showOnlyCore);
  document.getElementById('colshowall').addEventListener('click', showAll);
  if (sizeSelect) {
    sizeSelect.addEventListener('change', function () {
      if (SIZES[sizeSelect.value]) { state.size = sizeSelect.value; save(); applySize(); }
    });
  }
  document.getElementById('reset').addEventListener('click', function () {
    search.value = '';
    filters.forEach(function (f) { if (f) { f.value = ''; } });
    colfilter.value = '';
    valueFilter = {};
    closePanel();
    closeMenu();
    state = defaults();
    try { localStorage.removeItem(KEY); } catch (e) { /* ignore */ }
    applyAll();
  });

  function applyAll() {
    applyOrder();
    applyColumns();
    applyColumnFilter();
    applySize();
    applySort();
    markFunnels();
    applyFilter();
  }
  load();
  applyAll();
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


def column_count(symbols: list[Symbol], column: str) -> int:
    """How many symbols fill the column: a non-empty field value, an image, a pin or a unit."""
    if column in ("Library", "Symbol"):
        return len(symbols)
    filled = {"Extends": lambda s: s.extends, "Graphics": lambda s: s.graphics,
              "Pins": lambda s: s.pins, "Units": lambda s: s.units}.get(column, lambda s: s.fields.get(column))
    return sum(1 for s in symbols if filled(s))


def column_groups_html(columns: list[str], shown: set[str], counts: dict[str, int]) -> list[str]:
    """One .colgroup block per non-empty group in GROUPS order: a fold button, a tri-state parent checkbox
    (the script sets its state), the shown/total count and one checkbox per member column."""
    blocks = []
    for group in GROUPS:
        members = [c for c in columns if column_group(c) == group]
        if not members:
            continue
        closed = " closed" if group in DEFAULT_CLOSED_GROUPS else ""
        fold = "&#9656;" if closed else "&#9662;"
        n = sum(1 for c in members if c in shown)
        labels = "".join(f'<label><input type="checkbox" value="{esc(c)}"{" checked" if c in shown else ""}> '
                         f'{esc(c)} ({counts[c]})</label>' for c in members)
        blocks.append(f'<div class="colgroup{closed}" data-group="{esc(group)}">'
                      f'<div class="grouphead"><button type="button" class="fold" title="{"Expand" if closed else "Collapse"}" '
                      f'aria-label="fold {esc(group)}">{fold}</button>'
                      f'<label><input type="checkbox" class="grouptoggle" aria-label="show all {esc(group)} columns"> '
                      f'{esc(group)} <span class="n">({n}/{len(members)})</span></label></div>'
                      f'<div class="members">{labels}</div></div>')
    return blocks


def build_page(symbols: list[Symbol], title: str, libraries: list[Path], graphics: bool) -> tuple[str, list[str]]:
    """(html, column names)."""
    props = property_columns({n for s in symbols for n in s.fields})
    head = [c for c in FIXED_HEAD if c != "Extends" or any(s.extends for s in symbols)]
    lead = [c for c in LEAD_FIELDS if c in props]
    desc = ["Description"] if "Description" in props else []
    rest = [p for p in props if p not in lead and p != "Description"]
    columns = head + lead + (["Graphics"] if graphics else []) + desc + ["Pins", "Units"] + rest
    unfilterable = {"Graphics"}
    counts = {c: column_count(symbols, c) for c in columns}
    # The rest of the fields start hidden when no symbol fills them; the Columns control shows them.
    shown = {c for c in columns if c in ALWAYS_SHOWN or counts[c] > 0}

    header = "".join(f'<th class="sortable" draggable="true" data-col="{esc(c)}" data-group="{esc(column_group(c))}">{esc(c)}'
                     f'<span class="grip" title="Drag to resize"></span></th>' for c in columns)
    filter_row = "".join("<th></th>" if c in unfilterable else
                         f'<th><div class="fwrap"><input type="search" placeholder="filter" aria-label="filter {esc(c)}">'
                         f'<button type="button" class="funnel" title="Filter by value" aria-label="filter {esc(c)} by value">'
                         f'&#9661;</button></div></th>'
                         for c in columns)
    toggles = "".join(column_groups_html(columns, shown, counts))
    size_control = ('<label>Graphics <select id="imgsize" aria-label="graphics size">'
                    + "".join(f'<option value="{s}"{" selected" if s == "L" else ""}>{s}</option>' for s in ("S", "M", "L", "XL"))
                    + "</select></label>") if graphics else ""

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
<p class="meta">{len(symbols)} symbols from {sources}. Click a header to add it to the sort as the last key (again to reverse
it, a third time to remove it); sorting headers show their priority and direction. Drag a header onto another to reorder,
drag its right edge to resize; right-click a header to hide it or its group. The funnel in a filter cell picks values.
Pins read name (number) electrical type = Pin.&lt;base&gt; value. A middle dot marks a field that is present but empty.</p>
<div class="controls">
<input type="search" id="search" placeholder="search all columns" aria-label="search all columns">
<details class="columns"><summary>Columns</summary><div id="columns">
<p class="colbulk"><button type="button" id="colcore">Show only Core</button> <button type="button" id="colshowall">Show all</button></p>
<p class="colctl"><input type="search" id="colfilter" placeholder="filter columns" aria-label="filter columns">
<button type="button" id="colall">All</button> <button type="button" id="colnone">None</button> <span class="n">(filtered entries)</span></p>
{toggles}</div></details>
{size_control}
<button type="button" id="reset">Reset view</button>
<span id="count"></span>
</div>
<table id="symbols" data-size="L">
<thead>
<tr class="headers">{header}</tr>
<tr class="filters">{filter_row}</tr>
</thead>
<tbody>
{chr(10).join(rows)}
</tbody>
</table>
<div id="valuepanel" hidden>
<input type="search" id="valuesearch" placeholder="search values" aria-label="search values">
<p><button type="button" id="valall">Select all</button> <button type="button" id="valclear">Clear</button></p>
<div id="valuelist"></div>
</div>
<div id="colmenu" role="menu" hidden>
<button type="button" data-act="hide">Hide this column</button>
<button type="button" data-act="hidegroup">Hide all columns of its group</button>
<button type="button" data-act="core">Show only Core</button>
<button type="button" data-act="all">Show all</button>
</div>
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
