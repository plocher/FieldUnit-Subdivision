"""Unit tests for the symbol library overview page (tools/kicad_library_overview.py)."""

from __future__ import annotations

import io
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from html.parser import HTMLParser
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import kicad_library_overview as overview  # noqa: E402

# Two symbols in KiCad 10's tab-indented layout: Gadget has two units with Pin.* fields and a Description
# that needs both s-expression and HTML escaping; Marker is single-unit with a Kind field.
FIXTURE = '''(kicad_symbol_lib
\t(version 20251024)
\t(generator "kicad_symbol_editor")
\t(generator_version "10.0")
\t(symbol "Gadget"
\t\t(property "Reference" "G"
\t\t\t(at 0 0 0)
\t\t)
\t\t(property "Value" ""
\t\t\t(at 0 0 0)
\t\t\t(do_not_autoplace yes)
\t\t)
\t\t(property "Footprint" ""
\t\t\t(at 0 0 0)
\t\t)
\t\t(property "Datasheet" ""
\t\t\t(at 0 0 0)
\t\t)
\t\t(property "Description" "A <b>gadget</b> & its \\"friend\\""
\t\t\t(at 0 0 0)
\t\t)
\t\t(property "Role" "DEVICE"
\t\t\t(at 0 0 0)
\t\t)
\t\t(property "Appliance" "gadget"
\t\t\t(at 0 0 0)
\t\t)
\t\t(property "Pin.OCC" "binary out"
\t\t\t(at 0 0 0)
\t\t)
\t\t(property "Pin.EN" "binary in"
\t\t\t(at 0 0 0)
\t\t)
\t\t(property "hold_ms" "1500"
\t\t\t(at 0 0 0)
\t\t)
\t\t(symbol "Gadget_0_1"
\t\t\t(rectangle
\t\t\t\t(start -2.54 2.54)
\t\t\t\t(end 2.54 -2.54)
\t\t\t)
\t\t)
\t\t(symbol "Gadget_1_1"
\t\t\t(pin output line
\t\t\t\t(at 5.08 0 180)
\t\t\t\t(length 2.54)
\t\t\t\t(name "~{OCC}"
\t\t\t\t\t(effects
\t\t\t\t\t\t(font
\t\t\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t\t\t)
\t\t\t\t\t)
\t\t\t\t)
\t\t\t\t(number "1"
\t\t\t\t\t(effects
\t\t\t\t\t\t(font
\t\t\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t\t\t)
\t\t\t\t\t)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(symbol "Gadget_2_1"
\t\t\t(pin input line
\t\t\t\t(at -5.08 0 0)
\t\t\t\t(length 2.54)
\t\t\t\t(name "EN"
\t\t\t\t\t(effects
\t\t\t\t\t\t(font
\t\t\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t\t\t)
\t\t\t\t\t)
\t\t\t\t)
\t\t\t\t(number "2"
\t\t\t\t\t(effects
\t\t\t\t\t\t(font
\t\t\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t\t\t)
\t\t\t\t\t)
\t\t\t\t)
\t\t\t)
\t\t)
\t)
\t(symbol "Marker"
\t\t(property "Reference" "M"
\t\t\t(at 0 0 0)
\t\t)
\t\t(property "Value" "MARK"
\t\t\t(at 0 0 0)
\t\t)
\t\t(property "Description" "Plain marker"
\t\t\t(at 0 0 0)
\t\t)
\t\t(property "Role" "TRACK"
\t\t\t(at 0 0 0)
\t\t)
\t\t(property "Kind" "END_CTC"
\t\t\t(at 0 0 0)
\t\t)
\t\t(symbol "Marker_1_1"
\t\t\t(pin passive line
\t\t\t\t(at 0 0 0)
\t\t\t\t(length 2.54)
\t\t\t\t(name "T"
\t\t\t\t\t(effects
\t\t\t\t\t\t(font
\t\t\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t\t\t)
\t\t\t\t\t)
\t\t\t\t)
\t\t\t\t(number "1"
\t\t\t\t\t(effects
\t\t\t\t\t\t(font
\t\t\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t\t\t)
\t\t\t\t\t)
\t\t\t\t)
\t\t\t)
\t\t)
\t)
)
'''


class TableReader(HTMLParser):
    """Headers (first thead row), one list of cell texts per tbody row, and the ids and classes seen.
    Rows and headers come from the symbols table only (the first table); the conventions table is read apart."""

    def __init__(self):
        super().__init__()
        self.headers: list[str] = []
        self.rows: list[list[str]] = []
        self.ids: set[str] = set()
        self.classes: set[str] = set()
        self.images: list[str] = []
        self._section = None
        self._cell: list[str] | None = None
        self._header_row_done = False
        self._tables = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        self.classes.update((attrs.get("class") or "").split())
        if tag == "table":
            self._tables += 1
        if self._tables > 1:
            return
        if tag in ("thead", "tbody"):
            self._section = tag
        elif tag == "tr" and self._section == "tbody":
            self.rows.append([])
        elif tag in ("th", "td"):
            self._cell = []
        elif tag == "img":
            self.images.append(attrs.get("src", ""))

    def handle_endtag(self, tag):
        if tag in ("th", "td") and self._cell is not None:
            text = " ".join(" ".join(self._cell).split())
            if self._section == "thead" and tag == "th" and not self._header_row_done:
                self.headers.append(text)
            elif self._section == "tbody":
                self.rows[-1].append(text)
            self._cell = None
        elif tag == "tr" and self._section == "thead":
            self._header_row_done = True
        elif tag in ("thead", "tbody"):
            self._section = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)


class OverviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        cls.lib = root / "Fixture.kicad_sym"
        cls.lib.write_text(FIXTURE)
        cls.out = root / "overview"
        with redirect_stdout(io.StringIO()) as captured:
            rc = overview.main([str(cls.lib), "--out", str(cls.out), "--no-render", "--title", "Fixture <overview>"])
        cls.rc, cls.stdout = rc, captured.getvalue()
        cls.page = (cls.out / overview.PAGE_NAME).read_text()
        cls.table = TableReader()
        cls.table.feed(cls.page)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def row(self, symbol: str) -> dict[str, str]:
        for r in self.table.rows:
            if r[self.table.headers.index("Symbol")] == symbol:
                return dict(zip(self.table.headers, r))
        self.fail(f"no row for {symbol}")

    def test_run_reports_path_and_row_count(self):
        self.assertEqual(self.rc, 0)
        self.assertEqual(self.stdout.strip(), f"{self.out / overview.PAGE_NAME}: 2 rows")
        self.assertEqual(len(self.table.rows), 2)

    def test_every_field_is_a_column_in_stable_order(self):
        expected = ["Library", "Symbol", "Role", "Appliance", "Description", "Pins", "Units",
                    "Reference", "Value", "Footprint", "Datasheet", "Pin.EN", "Pin.OCC", "hold_ms", "Kind"]
        self.assertEqual(self.table.headers, expected)  # no Graphics column with --no-render
        self.assertEqual(self.table.images, [])
        self.assertNotIn("--w:", self.page)                  # no images, no image sizes

    def test_fields_pins_and_units_are_rendered(self):
        gadget = self.row("Gadget")
        self.assertEqual(gadget["Library"], "Fixture")
        self.assertEqual(gadget["Role"], "DEVICE")
        self.assertEqual(gadget["Pin.OCC"], "binary out")
        self.assertEqual(gadget["hold_ms"], "1500")
        self.assertEqual(gadget["Kind"], "")  # absent on Gadget
        self.assertEqual(gadget["Pins"], "~{OCC} (1) output = binary out EN (2) input = binary in")
        self.assertEqual(gadget["Units"], "common: (no pins) unit 1: ~{OCC} unit 2: EN")
        marker = self.row("Marker")
        self.assertEqual(marker["Value"], "MARK")
        self.assertEqual(marker["Kind"], "END_CTC")
        self.assertEqual(marker["Pins"], "T (1) passive")
        self.assertEqual(marker["Units"], "unit 1: T")

    def test_html_escaping(self):
        self.assertEqual(self.row("Gadget")["Description"], 'A <b>gadget</b> & its "friend"')
        self.assertIn("A &lt;b&gt;gadget&lt;/b&gt; &amp; its &quot;friend&quot;", self.page)
        self.assertNotIn("<b>gadget</b>", self.page)
        self.assertIn("<title>Fixture &lt;overview&gt;</title>", self.page)

    def test_page_has_sort_filter_and_column_controls(self):
        self.assertTrue({"search", "columns", "reset", "symbols", "count"} <= self.table.ids)
        self.assertIn("sortable", self.table.classes)
        self.assertIn("filters", self.table.classes)
        self.assertEqual(self.page.count('<input type="checkbox" value="'), len(self.table.headers))
        self.assertTrue({"colfilter", "colall", "colnone"} <= self.table.ids)
        self.assertIn('value="Role" checked> Role (2)</label>', self.page)          # always shown
        self.assertIn('value="Footprint"> Footprint (0)</label>', self.page)        # empty on every symbol: starts hidden
        self.assertIn('value="hold_ms" checked> hold_ms (1)</label>', self.page)    # filled on one symbol: shown
        self.assertIn("localStorage", self.page)
        self.assertNotIn("<script src=", self.page)  # no external dependency
        self.assertNotIn("<link ", self.page)

    def test_column_labels_carry_the_filled_row_count(self):
        labels = {"Library": 2, "Symbol": 2, "Role": 2, "Appliance": 1, "Description": 2, "Pins": 2, "Units": 2,
                  "Reference": 2, "Value": 1, "Footprint": 0, "Datasheet": 0, "Pin.EN": 1, "Pin.OCC": 1,
                  "hold_ms": 1, "Kind": 1}
        self.assertEqual(set(labels), set(self.table.headers))
        for name, n in labels.items():
            checked = " checked" if n or name in overview.ALWAYS_SHOWN else ""
            self.assertIn(f'<label><input type="checkbox" value="{name}"{checked}> {name} ({n})</label>', self.page)
        self.assertEqual(overview.column_count(overview.load_library(self.lib), "Pin.OCC"), 1)

    def test_storage_key_is_versioned(self):
        self.assertIn("'kicad-library-overview:v3:' + document.title", self.page)
        self.assertNotIn("'kicad-library-overview:' + document.title", self.page)
        self.assertNotIn("'kicad-library-overview:v2:' + document.title", self.page)  # v3: sort is a list

    def test_column_groups_with_counts(self):
        # Group label = "<group> (shown/total)" for the fixture; empty groups (Contract) are not emitted.
        for group, shown, total in (("Core", 7, 7), ("KiCad fields", 2, 4), ("Pin.*", 2, 2), ("Settings", 1, 1), ("Other", 1, 1)):
            self.assertIn(f'<input type="checkbox" class="grouptoggle" aria-label="show all {group} columns"> '
                          f'{group} <span class="n">({shown}/{total})</span></label>', self.page)
        self.assertNotIn('data-group="Contract"', self.page)
        self.assertEqual(self.page.count('class="grouptoggle"'), 5)
        self.assertEqual([overview.column_group(c) for c in self.table.headers],
                         ["Core"] * 7 + ["KiCad fields"] * 4 + ["Pin.*"] * 2 + ["Settings", "Other"])
        self.assertEqual(overview.column_group("IndicationToken"), "Contract")
        self.assertEqual(overview.column_group("ki_keywords"), "Settings")
        self.assertEqual(overview.column_group("Kind"), "Other")
        # Group order and default folds: Pin.* and Settings start closed, Core and the rest open.
        blocks = re.findall(r'<div class="colgroup( closed)?" data-group="([^"]+)">', self.page)
        self.assertEqual(blocks, [("", "Core"), ("", "KiCad fields"), (" closed", "Pin.*"), (" closed", "Settings"), ("", "Other")])
        self.assertEqual(self.page.count('<button type="button" class="fold"'), 5)
        # Every member entry sits in its group's block and headers carry the group for the context menu.
        self.assertIn('data-group="Pin.*"><div class="grouphead">', self.page)
        self.assertIn('<th class="sortable" draggable="true" data-col="Pin.EN" data-group="Pin.*">', self.page)
        self.assertIn('<th class="sortable" draggable="true" data-col="hold_ms" data-group="Settings">', self.page)
        self.assertIn('<div class="members"><label><input type="checkbox" value="Pin.EN" checked> Pin.EN (1)</label>'
                      '<label><input type="checkbox" value="Pin.OCC" checked> Pin.OCC (1)</label></div>', self.page)

    def test_bulk_actions_and_header_context_menu(self):
        self.assertTrue({"colcore", "colshowall", "colmenu"} <= self.table.ids)
        self.assertIn('<button type="button" id="colcore">Show only Core</button>', self.page)
        self.assertIn('<button type="button" id="colshowall">Show all</button>', self.page)
        self.assertIn('<div id="colmenu" role="menu" hidden>', self.page)
        for act in ("hide", "hidegroup", "core", "all"):
            self.assertIn(f'<button type="button" data-act="{act}">', self.page)
        self.assertIn("addEventListener('contextmenu'", self.page)
        self.assertIn("e.shiftKey", self.page)                      # range selection within a group
        self.assertIn("g.parent.indeterminate", self.page)          # tri-state parent
        self.assertIn("state.closed", self.page)                    # folded groups persist

    def test_multi_column_sort_markup_hooks(self):
        self.assertIn('thead th.asc::after{content:" " attr(data-rank) " \\25b2"', self.page)
        self.assertIn('thead th.desc::after{content:" " attr(data-rank) " \\25bc"', self.page)
        self.assertIn("heads[i].dataset.rank = rank + 1", self.page)
        self.assertIn("sort: []", self.page)                        # the default: no keys
        self.assertIn("state.sort.push({ col: col, dir: 'asc' })", self.page)
        self.assertIn("state.sort.splice(i, 1)", self.page)         # descending -> removed
        self.assertIn("return a.dataset.index - b.dataset.index;   // stable", self.page)

    def test_hiding_a_sort_column_drops_it_from_the_sort(self):
        # pruneSort drops every key whose column is hidden (showing it again does not restore it) and reports
        # whether one went; readToggles, the one path every hide action ends in, re-sorts when it did.
        self.assertIn("function pruneSort() {", self.page)
        self.assertIn("state.sort.filter(function (k) { return colIndex(k.col) >= 0 && state.hidden.indexOf(k.col) < 0; })",
                      self.page)
        self.assertIn("var resort = pruneSort();", self.page)
        self.assertIn("if (resort) { applySort(); }", self.page)
        self.assertIn("pruneSort();\n    var keys = state.sort.map(", self.page)   # a saved state is pruned at load too
        script = self.page[self.page.index("<script>"):]
        # Every way a column gets hidden calls readToggles: an entry click (shift-click range included), a group
        # parent, All/None (setVisibleToggles) and the bulk and header-menu actions (setToggles).
        self.assertGreaterEqual(script.count("readToggles();"), 4)
        for fn in ("function setVisibleToggles(on) {\n    toggles.forEach(function (b, i) { if (!labels[i].hidden) { b.checked = on; } });\n    readToggles();",
                   "function setToggles(wanted) {", "function showOnlyCore() { setToggles(", "function showAll() { setToggles(",
                   "function hideColumn(col) { setToggles(", "function hideGroup(name) { setToggles(",
                   "if (act === 'hide') { hideColumn(col); }", "else if (act === 'hidegroup') { hideGroup(groupOf[col]); }",
                   "else if (act === 'core') { showOnlyCore(); }", "g.last = n;\n        readToggles();",
                   "g.members.forEach(function (b) { b.checked = on; });\n      readToggles();"):
            self.assertIn(fn, script)
        self.assertIn("document.getElementById('colnone').addEventListener('click', function () { setVisibleToggles(false); });",
                      script)
        self.assertIn("document.getElementById('colcore').addEventListener('click', showOnlyCore);", script)

    def test_default_widths_fit_the_header_titles(self):
        # Each column's default width is the larger of its per-kind minimum and its measured title (canvas
        # measureText in the header's font plus padding, sort mark and slack), re-measured on every text-size
        # change and never saved; a width the user dragged (state.widths) wins.
        self.assertIn("function measureHeaders() {", self.page)
        self.assertIn("document.createElement('canvas').getContext('2d')", self.page)
        self.assertIn("ctx.font = cs.fontStyle + ' ' + cs.fontWeight + ' ' + cs.fontSize + ' ' + cs.fontFamily;", self.page)
        self.assertIn("parseFloat(cs.paddingLeft) + parseFloat(cs.paddingRight) + ctx.measureText(SORT_MARK).width + WIDTH_SLACK",
                      self.page)
        self.assertIn("measured[th.dataset.col] = Math.ceil(ctx.measureText(th.dataset.col).width + extra)", self.page)
        self.assertIn("function defaultWidth(col) { return Math.max(kindWidth(col), measured[col] || 0); }", self.page)
        for minimum in ("if (col === 'Pins' || col === 'Units') { return 220; }", "if (col === 'Description') { return 320; }",
                        "if (col === 'Symbol') { return 160; }", "return 120;"):
            self.assertIn(minimum, self.page)                   # the per-kind minimums stay
        self.assertIn("measureHeaders();                                          // the titles grew or shrank with the text\n"
                      "    applyWidths();", self.page)            # applyFont re-measures: S/M/L and the pt box both end there
        self.assertIn("+state.widths[th.dataset.col] > 0 ? +state.widths[th.dataset.col] : defaultWidth(th.dataset.col)", self.page)
        self.assertNotIn("measured:", self.page)                  # not part of state, so never saved
        self.assertIn("widths: {}", self.page)
        # The header keeps its ellipsis for a column the user drags narrower than its title.
        self.assertIn("thead th.sortable{cursor:pointer;user-select:none;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;", self.page)

    def test_page_has_resize_reorder_and_value_filter_controls(self):
        n = len(self.table.headers)
        self.assertEqual(self.page.count('<th class="sortable" draggable="true" data-col='), n)
        self.assertEqual(self.page.count('<span class="grip"'), n)
        self.assertIn("table-layout:fixed", self.page)
        self.assertEqual(self.page.count('<button type="button" class="funnel"'), n)  # no Graphics column here
        self.assertTrue({"valuepanel", "valuesearch", "valall", "valclear", "valuelist"} <= self.table.ids)
        self.assertIn("funnel", self.table.classes)
        for control in ("imgsize", "scalepx", "maxpx"):     # no graphics, no scale control
            self.assertNotIn(f'id="{control}"', self.page)

    def test_text_size_control(self):
        # S/M/L presets in points plus a "pt" box for any size; one body variable that every text rule inherits.
        self.assertTrue({"fontsize", "fontpt"} <= self.table.ids)
        self.assertIn('<select id="fontsize" aria-label="text size"><option value="S" selected>S</option>'
                      '<option value="M">M</option><option value="L">L</option>', self.page)
        self.assertIn('<input type="number" id="fontpt" min="4" max="72" step="0.5" value="10" '
                      'aria-label="text size in points"> pt</label>', self.page)
        self.assertIn("body{--fs:10pt;font-family:system-ui,sans-serif;font-size:var(--fs);", self.page)
        self.assertIn("var FONTS = { S: 10, M: 11.5, L: 13.5 };", self.page)
        self.assertIn("font: FONTS.S", self.page)                               # the default, restored by Reset view
        self.assertIn("document.body.style.setProperty('--fs', state.font + 'pt')", self.page)
        self.assertEqual(re.findall(r"font(?:-size)?:\s*[\d.]+px", self.page), [])  # no text size pinned in pixels


class GraphicsPageTests(unittest.TestCase):
    """build_page with the graphics column, without kicad-cli: the size control and the Graphics count."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        lib = Path(cls.tmp.name) / "Fixture.kicad_sym"
        lib.write_text(FIXTURE)
        cls.symbols = symbols = overview.load_library(lib)
        symbols[0].graphics = ["svg-Fixture/Gadget_unit1.svg", "svg-Fixture/Gadget_unit2.svg"]
        symbols[0].sizes = {"svg-Fixture/Gadget_unit1.svg": (24.257, 110.998)}   # unit 2: size unknown
        symbols[1].graphics = ["svg-Fixture/Marker_unit1.svg"]
        symbols[1].sizes = {"svg-Fixture/Marker_unit1.svg": (2.64, 3.4)}
        cls.page, cls.columns = overview.build_page(symbols, "Graphics fixture", [lib], graphics=True)
        cls.table = TableReader()
        cls.table.feed(cls.page)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_graphics_column_count_and_images(self):
        self.assertEqual(self.table.headers[:6], ["Library", "Symbol", "Role", "Appliance", "Graphics", "Description"])
        self.assertIn('value="Graphics" checked> Graphics (2)</label>', self.page)
        self.assertEqual(self.table.images, ["svg-Fixture/Gadget_unit1.svg", "svg-Fixture/Gadget_unit2.svg",
                                             "svg-Fixture/Marker_unit1.svg"])
        self.assertEqual(self.page.count('loading="lazy"'), 3)

    def test_graphics_scale_control(self):
        # Four presets in px per mm of drawing, named on the control, L (30) the default, plus a hidden "custom"
        # entry the select shows when the px/mm box holds another value (as the text control does with its pt
        # box). One scale for the whole page: every symbol SVG is at the same scale, so no rule may size a cell
        # differently from the rest.
        self.assertTrue({"imgsize", "scalepx", "maxpx"} <= self.table.ids)
        self.assertIn('<select id="imgsize" aria-label="graphics scale preset">', self.page)
        options = re.findall(r'<option value="(\w*)"( selected| hidden)?>([^<]*)</option>',
                             re.search(r'<select id="imgsize"[^>]*>(.*?)</select>', self.page).group(1))
        self.assertEqual(options, [("S", "", "S (10 px/mm)"), ("M", "", "M (20 px/mm)"), ("L", " selected", "L (30 px/mm)"),
                                   ("XL", "", "XL (45 px/mm)"), ("", " hidden", "custom")])
        # The two number boxes: px per mm (2 to 100, step 1, default 30) and the optional ceiling on an image's
        # longer side: empty ("none") by default, 200 to 20000 px in steps of 50 when typed.
        self.assertIn('<input type="number" id="scalepx" min="2" max="100" step="1" value="30" '
                      'aria-label="graphics scale in px per mm"> px/mm</label>', self.page)
        self.assertIn('<input type="number" id="maxpx" min="200" max="20000" step="50" value="" placeholder="none" '
                      'aria-label="ceiling on an image\'s longer side in px (empty for none)"> max px</label>', self.page)
        for gone in ("px/pin", "pinpx", "--p:", "--ppp", "pinUnits", "MIN_PINS", "PINLESS"):
            self.assertNotIn(gone, self.page)
        self.assertFalse(hasattr(overview, "unit_pins"))                                   # the pin-count rule is gone
        self.assertFalse(hasattr(overview, "IMG_PX_PER_PIN"))
        self.assertEqual((overview.IMG_SCALES, overview.IMG_SCALE_DEFAULT, overview.IMG_SCALE_RANGE),
                         ({"S": 10, "M": 20, "L": 30, "XL": 45}, 30, (2, 100, 1)))
        self.assertIsNone(overview.IMG_CEILING_DEFAULT)                                    # no ceiling by default ...
        self.assertEqual(overview.IMG_FLOOR, 0)                                            # ... and no floor
        self.assertEqual(overview.IMG_CEILING_RANGE, (200, 20000, 50))
        self.assertEqual(overview.css_ceiling(), overview.IMG_UNLIMITED_PX)
        self.assertEqual(overview.css_ceiling(600), 600)
        self.assertEqual((overview.nominal_px(), overview.nominal_px(10), overview.nominal_px(30, 600)), (720, 240, 600))
        # The script carries the same numbers and keeps them in state.scale and state.ceiling (null for none),
        # restored on load and both back to the defaults on Reset view; an old `size` letter or `ppp` (px per
        # pin) in storage is ignored, and so is the ceiling saved beside a `ppp` (that page capped by default).
        self.assertIn("var SCALES = { S: 10, M: 20, L: 30, XL: 45 };", self.page)
        self.assertIn("var SCALE_MIN = 2, SCALE_MAX = 100, SCALE_DEFAULT = 30;", self.page)
        self.assertIn("var CEIL_MIN = 200, CEIL_MAX = 20000, CEIL_DEFAULT = null;", self.page)
        self.assertIn("var UNLIMITED = 10000000;", self.page)
        self.assertIn("var FLOOR = 0;", self.page)
        self.assertIn("scale: SCALE_DEFAULT, ceiling: CEIL_DEFAULT, font: FONTS.S", self.page)
        self.assertIn("if (isScale(s.scale)) { state.scale = s.scale; }", self.page)
        self.assertIn("if (s.ppp === undefined && (s.ceiling === null || isCeiling(s.ceiling))) { state.ceiling = s.ceiling; }",
                      self.page)
        for gone in ("state.size", "data-size", "state.ppp", "s.ppp)", "isPpp"):
            self.assertNotIn(gone, self.page)
        for handler in ("if (SCALES[scaleSelect.value]) { state.scale = SCALES[scaleSelect.value]; save(); applyScale(); }",
                        "if (isScale(n)) { state.scale = n; save(); applyScale(); }",
                        "if (ceilInput.value === '' || n === 0) { state.ceiling = null; save(); applyScale(); }",
                        "else if (isCeiling(n)) { state.ceiling = n; save(); applyScale(); }"):
            self.assertIn(handler, self.page)
        self.assertIn("var shown = state.ceiling === null ? '' : String(state.ceiling);", self.page)   # the box shows "none"

    def test_graphics_sizing_css_is_driven_by_table_variables(self):
        # The table carries --scale, --floor, --ceil and --nom and each img of known size its --w/--h in mm; the
        # CSS defaults match the control defaults (floor 0, no ceiling: the far-off sentinel) and the script sets
        # the same table variables from state, so the images resize with no per-image JS beyond the capped marks.
        self.assertIn("table#symbols{--scale:30;--floor:0;--ceil:10000000;--nom:720px}", self.page)
        for var in ("--scale", "--floor", "--ceil", "--nom"):
            self.assertIn(f"table.style.setProperty('{var}', ", self.page)
        self.assertIn("table.style.setProperty('--floor', FLOOR);", self.page)
        self.assertIn("table.style.setProperty('--ceil', ceilingPx());", self.page)
        self.assertIn("function ceilingPx() { return state.ceiling === null ? UNLIMITED : state.ceiling; }", self.page)
        for gone in ("--img", "--ar", "--s:", "--n:", "var(--p"):
            self.assertNotIn(gone, self.page)
        # An image of unknown size is drawn in the nominal square (24 mm at the scale, at least 240 px, never
        # above a ceiling).
        rule = re.search(r"td\.graphics img\{[^}]*\}", self.page).group(0)
        self.assertIn("td.graphics img{width:var(--nom,720px);height:var(--nom,720px);", rule)
        self.assertIn("box-sizing:content-box", rule)
        self.assertIn("function nominal() { return Math.min(Math.max(state.scale * NOMINAL_MM, COLUMN_MIN), ceilingPx()); }", self.page)
        self.assertEqual(overview.IMG_NOMINAL_MM, 24)
        # The sized image: both sides are mm x one factor, the scale itself unless the clamp bites: the floor is 0
        # (never bites) and the ceiling the sentinel unless the user typed one. Both sides scale together so the
        # aspect holds; the border sits outside the content box so the drawing itself is exactly that size. No
        # object-fit, nothing depends on the intrinsic size.
        self.assertIn("td.graphics img.mm{--f:clamp(calc(var(--floor,0) / max(var(--w), var(--h))), var(--scale,30), "
                      "calc(var(--ceil,10000000) / max(var(--w), var(--h))));\n"
                      "  width:calc(var(--w) * var(--f) * 1px);height:calc(var(--h) * var(--f) * 1px)}", self.page)
        for rule in re.findall(r"td\.graphics img(?:\.mm)?\{[^}]*\}", self.page):
            for absent in ("max-width", "max-height", "height:auto", "object-fit"):
                self.assertNotIn(absent, rule)
        # A capped image (mm longer side x scale above a typed ceiling) is marked by the script: the class `capped`
        # (a dashed border) and a title suffix naming the ceiling and the scale it got; with no ceiling, nothing.
        self.assertIn("td.graphics img.capped{border-style:dashed;border-color:#c60}", self.page)
        self.assertIn("var capped = state.ceiling !== null && longer > 0 && longer * state.scale > state.ceiling;", self.page)
        self.assertIn("img.classList.toggle('capped', capped);", self.page)
        self.assertIn("img.dataset.title + ' (capped at ' + state.ceiling + ' px, '", self.page)
        self.assertIn("(Math.round(state.ceiling / longer * 10) / 10) + ' px/mm)'", self.page)
        # The Graphics column's default width is the widest row of units (the images' widths as the CSS draws them
        # at the scale plus their borders and margins, plus the cell padding and border), between 240 and 2400 px,
        # recomputed whenever the scale or the ceiling changes; a dragged width wins. Multi-unit images stay inline.
        self.assertIn("var COLUMN_MIN = 240, COLUMN_MAX = 2400;", self.page)
        self.assertIn("function imageSize(img) {", self.page)
        self.assertIn("if (!(w > 0 && h > 0)) { return [nominal(), nominal()]; }", self.page)
        self.assertIn("var f = Math.max(FLOOR / Math.max(w, h), Math.min(state.scale, ceilingPx() / Math.max(w, h)));", self.page)
        self.assertIn("return [w * f, h * f];", self.page)
        self.assertIn("function measureGraphics() {", self.page)
        self.assertIn("total += imageSize(i)[0] + perImage;", self.page)
        self.assertIn("graphicsWidth = Math.min(Math.max(COLUMN_MIN, Math.ceil(widest + perCell + WIDTH_SLACK)), COLUMN_MAX);", self.page)
        self.assertIn("markCapped();\n    measureGraphics();\n    applyWidths();", self.page)
        self.assertIn("if (col === 'Graphics') { return graphicsWidth; }", self.page)
        self.assertEqual((overview.IMG_COLUMN_MIN, overview.IMG_COLUMN_MAX), (240, 2400))
        self.assertNotIn("graphicsWidth:", self.page)         # not part of state, so never saved
        self.assertNotIn("display:block", re.search(r"td\.graphics img\{[^}]*\}", self.page).group(0))

    def test_graphics_has_no_value_filter(self):
        n = len(self.table.headers)
        self.assertEqual(self.page.count('<button type="button" class="funnel"'), n - 1)  # Graphics has no value filter
        self.assertEqual(self.page.count('<span class="grip"'), n)

    def test_image_size_is_emitted_as_custom_properties(self):
        # Width and height in mm to 2 decimals on each img of known size, with the class the CSS scale rule keys
        # on; an image of unknown size has neither (the CSS draws it in the nominal square). Nothing else about
        # the symbol (pins, units) reaches the img: one scale for all.
        imgs = re.findall(r"<img [^>]*>", self.page)
        self.assertEqual(len(imgs), 3)
        self.assertIn('src="svg-Fixture/Gadget_unit1.svg"', imgs[0])
        self.assertTrue(imgs[0].endswith(' loading="lazy" class="mm" style="--w:24.26;--h:111.00">'), imgs[0])
        self.assertIn('src="svg-Fixture/Gadget_unit2.svg"', imgs[1])
        self.assertTrue(imgs[1].endswith(' loading="lazy">'), imgs[1])
        self.assertNotIn("--w", imgs[1])
        self.assertNotIn("mm", imgs[1])
        self.assertTrue(imgs[2].endswith(' loading="lazy" class="mm" style="--w:2.64;--h:3.40">'), imgs[2])
        self.assertEqual(self.page.count("--w:"), 2)                    # once per sized img, nowhere else

    def test_svg_size_mm_reads_the_root_tag(self):
        # kicad-cli writes width and height in mm on the root element; any CSS length unit converts to mm
        # (unitless is px at 96 per inch); a missing or unparsable attribute, a zero side, a file without an
        # <svg> tag or a missing file -> None.
        def size(root: str):
            f = Path(self.tmp.name) / "size.svg"
            f.write_text('<?xml version="1.0" standalone="no"?>\n<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"\n'
                         ' "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n' + root + "\n<title>width=\"9mm\"</title></svg>\n")
            return overview.svg_size_mm(f)

        kicad = ('<svg\n  xmlns="http://www.w3.org/2000/svg"\n  version="1.1"\n'
                 '  width="24.2570mm" height="110.9980mm" viewBox="0.0000 0.0000 24.2570 110.9980">')
        self.assertEqual(size(kicad), (24.257, 110.998))                                  # mm: exact
        self.assertEqual(size('<svg width="96px" height="192px">'), (25.4, 50.8))           # px at 96 per inch
        self.assertEqual(size('<svg height="192" width="96">'), (25.4, 50.8))               # unitless = px, any order
        self.assertEqual(size('<svg width="1in" height="2in">'), (25.4, 50.8))              # inches
        self.assertEqual(size('<svg width="1cm" height="72pt">'), (10.0, 25.4))             # cm and points
        self.assertEqual(size('<svg width="1in" height="25.4mm">'), (25.4, 25.4))           # mixed units
        self.assertIsNone(size('<svg height="150px">'))                                     # width missing
        self.assertIsNone(size('<svg width="300px">'))                                      # height missing
        self.assertIsNone(size('<svg viewBox="0 0 300 150">'))                              # neither
        self.assertIsNone(size('<svg width="100%" height="150px">'))                        # not a length
        self.assertIsNone(size('<svg width="300px" height="0px">'))                         # zero side
        self.assertIsNone(size('<svg width="abc" height="150px">'))
        self.assertIsNone(overview.svg_size_mm(Path(self.tmp.name) / "missing.svg"))
        self.assertIsNone(overview.svg_size_mm(Path(self.tmp.name) / "Fixture.kicad_sym"))  # no <svg> tag
        self.assertFalse(hasattr(overview, "svg_aspect"))                                  # retired with --ar

    def test_property_column_order(self):
        names = {"zeta", "Alpha", "Pin.B", "Pin.A", "Invert", "Role", "Description", "Reference", "Style"}
        self.assertEqual(overview.property_columns(names),
                         ["Role", "Style", "Description", "Invert", "Reference", "Pin.A", "Pin.B", "Alpha", "zeta"])

    def test_pin_base(self):
        self.assertEqual(overview.pin_base("~{OCC}"), "OCC")
        self.assertEqual(overview.pin_base("EN"), "EN")


def sym(name: str, fields: dict[str, str], units: dict[int, list[str]], library: str = "Lib",
        outputs: tuple[str, ...] = ()) -> overview.Symbol:
    """An in-memory symbol: pins numbered in order, outputs as named, Column passive, every other pin an input."""
    etype = lambda p: "output" if p in outputs else "passive" if p == "Column" else "input"
    pins = [(p, str(i + 1), etype(p)) for i, p in enumerate(p for u in sorted(units) for p in units[u])]
    return overview.Symbol(library, name, dict(fields), pins, units)


# PANEL levers: a switch lever stating one of its four per-pin tokens on the wrong pin direction and one naming no
# pin; a maintainer-call lever in the superseded whole-symbol form with a level lamp pin; a lock lever with its
# deliberate UNUSED pin and Invert. A model board lamp with IndicationToken, a retiring PANEL lamp, a trackplan
# maintainer call (APPLIANCE) carrying Indication, a switch drawn with and without an OS circuit, and one field
# device kind drawn twice.
LEVER_SWITCH = sym("LeverSwitch", {"Role": "PANEL", "Appliance": "lever", "Style": "switch", "Name": "${Value}",
                                   "Control.NWS": "${Value}NWS", "Control.NWK": "${Value}NWK", "Indication.XX": "x",
                                   "Pin.NWS": "binary", "Pin.RWS": "binary", "Pin.NWK": "binary"},
                   {1: ["Column", "~{NWS}", "~{RWS}"], 2: ["~{NWK}"]}, outputs=("~{NWS}", "~{RWS}"))
LEVER_MCALL = sym("LeverMCall", {"Role": "PANEL", "Appliance": "lever", "Style": "maintainer_call",
                                 "Name": "${Value}MC", "Control": "${Name}S", "Indication": "${Name}K",
                                 "Pin.MCS": "binary", "Pin.MCK": "level"},
                  {1: ["Column", "~{MCS}"], 2: ["~{MCK}"]}, library="Office", outputs=("~{MCS}",))
LEVER_LOCK = sym("LeverLock", {"Role": "PANEL", "Appliance": "lever", "Style": "lock", "Name": "${Value}",
                               "Invert": "WLK", "Control.UNUSED": "", "Control.WLS": "a", "Indication.WLK": "!${Value}WLK",
                               "Pin.UNUSED": "binary", "Pin.WLS": "binary", "Pin.WLK": "binary"},
                 {1: ["Column", "~{UNUSED}", "~{WLS}"], 2: ["~{WLK}"]}, outputs=("~{UNUSED}", "~{WLS}"))
BOARD_LAMP = sym("BoardLamp", {"Role": "PANEL", "Appliance": "lamp", "Style": "board", "Name": "${Value}",
                               "IndicationToken": "", "Pin.LAMP": "binary"}, {1: ["~{LAMP}"]})
OLD_LAMP = sym("OldLamp", {"Role": "PANEL", "Appliance": "lamp", "Style": "indication", "Name": "${Value}",
                           "IndicationToken": "", "Pin.LAMP": "level"}, {1: ["Column", "~{LAMP}"]})
TRACK_MCALL = sym("TrackMCall", {"Role": "APPLIANCE", "Appliance": "lamp", "Style": "maintainer_call",
                                 "Name": "${Value}MC", "Indication": "${Name}K", "Pin.MCK": "level"},
                  {1: ["MC"]}, library="Trackplan")
TRACK_SWITCH = sym("TrackSwitch", {"Role": "APPLIANCE", "Appliance": "switch", "Style": "powered", "Name": "${Value}",
                                   "TC": "${VALUE}T1", "Indication": "${TC}K"}, {1: ["C", "N", "R"]})
TRACK_SWITCH_NO_TC = sym("TrackSwitchNoTC", {"Role": "APPLIANCE", "Appliance": "switch", "Style": "powered",
                                             "Name": "${Value}", "TC": "", "Indication": ""}, {1: ["C", "N", "R"]})
LAMP_A = sym("LampA", {"Role": "DEVICE", "Appliance": "lamp", "Name": "${Value}", "Pin.LAMP": "binary", "Address": "",
                       "Invert": "LAMP"}, {1: ["~{LAMP}"]})
LAMP_B = sym("LampB", {"Role": "DEVICE", "Appliance": "lamp", "Name": "${Value}", "Pin.LAMP": "level", "hold_ms": "5"},
             {1: ["~{LAMP}"]})
ALL = [LEVER_SWITCH, LEVER_MCALL, LEVER_LOCK, BOARD_LAMP, OLD_LAMP, TRACK_MCALL, TRACK_SWITCH, TRACK_SWITCH_NO_TC, LAMP_A, LAMP_B]


class ConventionsTests(unittest.TestCase):
    def setUp(self):
        self.kinds = overview.convention_kinds(ALL)
        self.by_symbol = {s.name: (k, cells) for k in self.kinds for s, cells in zip(k.symbols, k.cells)}

    def cell(self, symbol: str, column: str) -> overview.Cell:
        return self.by_symbol[symbol][1][column]

    def flags(self, symbol: str) -> list[str]:
        return [f for c in self.by_symbol[symbol][1].values() for f in c.flags]

    def test_kinds_are_keyed_by_fields_never_by_name(self):
        labels = [k.label for k in self.kinds]
        self.assertEqual(len(self.kinds), 8)
        self.assertIn("Role=PANEL · Appliance=lever · Style=switch", labels)
        lamps = self.by_symbol["LampA"][0]
        self.assertEqual([s.name for s in lamps.symbols], ["LampA", "LampB"])   # one kind, two drawings
        self.assertEqual(lamps.label, "Role=DEVICE · Appliance=lamp")

    def test_cells_show_the_raw_macros_pins_and_units(self):
        self.assertEqual(self.cell("LeverMCall", "Name").text, "${Value}MC")
        self.assertEqual(self.cell("LeverMCall", "Control").text, "${Name}S")
        self.assertEqual(self.cell("LeverSwitch", "Control").text, overview.ABSENT)
        self.assertEqual(self.cell("LeverMCall", "Pins").text, "MCS=binary, MCK=level")     # Column is a seam pin
        self.assertEqual(self.cell("LeverMCall", "Units").text, "1 [binary]: Column MCS; 2 [level]: MCK")
        self.assertEqual(self.cell("LampB", "Other fields").text, "hold_ms=5")
        self.assertNotIn("Control.NWS", self.cell("LeverSwitch", "Other fields").text)   # per-pin tokens have their column

    def test_symbols_of_one_kind_that_disagree_are_flagged(self):
        for name in ("LampA", "LampB"):
            self.assertTrue(any("disagree" in f for f in self.cell(name, "Other fields").flags), name)  # Invert
            self.assertFalse(self.cell(name, "Name").flags, name)                                       # both ${Value}
        panel = [sym(n, {"Role": "PANEL", "Appliance": "lamp", "Style": "board", "Name": "${Value}", "Indication": "",
                         "Pin.LAMP": d}, {1: ["~{LAMP}"]}) for n, d in (("P1", "binary"), ("P2", "level"))]
        kind = overview.convention_kinds(panel)[0]
        self.assertTrue(all(any("disagree" in f for f in row["Pins"].flags) for row in kind.cells))   # binary vs level

    def test_g1_never_compares_a_devices_address(self):
        heads = [sym(n, {"Role": "DEVICE", "Appliance": "head", "Style": "CL", "Head": "${Value}", **f}, {1: ["IND"]})
                 for n, f in (("Pixel", {"Address": ""}), ("RGB", {}))]
        kind = overview.convention_kinds(heads)[0]
        self.assertFalse(any(row["Other fields"].flags for row in kind.cells))

    def test_g1_never_compares_settings(self):
        devices = [sym(n, {"Role": "DEVICE", "Appliance": "track_circuit", "Name": "${Value}", **f}, {1: ["IND"]})
                   for n, f in (("Current", {}), ("Optical", {"hold_ms": "1500"}))]
        kind = overview.convention_kinds(devices)[0]
        self.assertFalse(any(row["Other fields"].flags for row in kind.cells))

    def test_a_device_or_drivers_pins_and_units_are_its_hardware_and_not_compared(self):
        for name in ("LampA", "LampB"):                                                             # binary vs level
            self.assertFalse(any("disagree" in f for f in self.cell(name, "Pins").flags), name)
            self.assertFalse(any("disagree" in f for f in self.cell(name, "Units").flags), name)

    def test_r1_a_panel_lever_states_a_token_per_function_pin(self):
        tokens = self.cell("LeverSwitch", "Tokens")
        self.assertIn("Control.NWS=${Value}NWS", tokens.text)
        self.assertIn("RWS: " + overview.ABSENT, tokens.text)
        self.assertIn("R1: missing Control.RWS", tokens.flags)
        self.assertIn("R1: Control.NWK on an input pin; Indication.NWK expected", tokens.flags)
        self.assertNotIn("R1: missing Indication.NWK", tokens.flags)              # the wrong-direction one is flagged instead
        self.assertIn("R1: Indication.XX names no pin", tokens.flags)
        self.assertNotIn("R1: missing Control.NWS", tokens.flags)
        self.assertFalse(self.cell("LeverSwitch", "Control").flags)          # the whole-symbol form is not asked for

    def test_r1_an_empty_field_is_a_deliberate_none_and_an_absent_one_not_done_yet(self):
        tokens = self.cell("LeverLock", "Tokens")
        self.assertIn("Control.UNUSED= (none, deliberate)", tokens.text)
        self.assertEqual(tokens.flags, [])                                  # WLS and WLK state theirs
        undone = sym("LeverLock2", {**LEVER_LOCK.fields}, LEVER_LOCK.units, outputs=("~{UNUSED}", "~{WLS}"))
        del undone.fields["Control.UNUSED"]
        self.assertEqual(overview.tokens_cell(undone).flags, ["R1: missing Control.UNUSED"])

    def test_r1_the_whole_symbol_form_on_a_lever_is_superseded(self):
        for f in ("Control", "Indication"):
            self.assertEqual(len(self.cell("LeverMCall", f).flags), 1)
            self.assertTrue(self.cell("LeverMCall", f).flags[0].startswith("R1: superseded"))
        self.assertIn("R1: missing Control.MCS", self.cell("LeverMCall", "Tokens").flags)
        self.assertIn("R1: missing Indication.MCK", self.cell("LeverMCall", "Tokens").flags)

    def test_r2_a_model_board_lamp_states_one_indication(self):
        self.assertEqual(self.cell("BoardLamp", "Indication").flags,
                         ["R2: missing; a model board lamp states one Indication expression"])
        self.assertTrue(any(f.startswith("IndicationToken: R2: superseded") for f in self.cell("BoardLamp", "Other fields").flags))
        self.assertEqual(self.cell("BoardLamp", "Tokens").flags, [])        # no Indication.LAMP expected
        self.assertFalse(self.cell("BoardLamp", "Control").flags)

    def test_r3_an_appliance_states_what_it_reports(self):
        self.assertFalse(self.flags("TrackSwitch"))                         # ${TC}K
        self.assertFalse(self.flags("TrackSwitchNoTC"))                     # no OS circuit: stated empty, and G1 agrees
        self.assertFalse(self.cell("TrackMCall", "Indication").flags)       # the maintainer call is not asked yet
        appliance = lambda **f: sym("A", {"Role": "APPLIANCE", **f}, {1: ["TC"]})
        self.assertEqual(overview.reporter_flags(appliance(Appliance="track_circuit")),
                         ["R3: missing; an appliance states what it reports"])
        self.assertEqual(overview.reporter_flags(appliance(Appliance="switch", TC="${VALUE}T1", Indication="")),
                         ["R3: empty, but the switch has an OS circuit (TC)"])
        self.assertEqual(overview.reporter_flags(appliance(Appliance="mast", Indication="x")),
                         ["R3: unexpected; this appliance reports nothing"])
        self.assertEqual(overview.reporter_flags(appliance(Appliance="lamp", Indication="${Name}K")), [])

    def test_r4_invert_on_a_panel_symbol_is_superseded_and_never_asked_for(self):
        self.assertTrue(any(f.startswith("Invert: R4: superseded") for f in self.cell("LeverLock", "Other fields").flags))
        self.assertFalse(any("Invert" in f for f in self.flags("LeverSwitch")))     # its absence is not flagged
        self.assertFalse(any("Invert" in f for f in self.flags("LampA")))           # DEVICE keeps Invert

    def test_r5_a_panel_lamp_pin_states_binary(self):
        self.assertIn("R5: lamp pin MCK is level; lamp pins state binary", self.cell("LeverMCall", "Pins").flags)
        self.assertFalse(any(f.startswith("R5") for f in self.flags("BoardLamp")))
        self.assertFalse(any(f.startswith("R5") for f in self.flags("LampB")))      # a DEVICE pin is not a panel lamp

    def test_r6_a_retiring_kind_is_marked_and_not_flagged(self):
        kind = self.by_symbol["OldLamp"][0]
        self.assertTrue(kind.retiring)
        self.assertTrue(kind.label.endswith("(retiring)"))
        self.assertEqual(kind.flagged, 0)                                   # level LAMP, IndicationToken, no Indication

    def test_g2_asks_for_the_key_field_the_importer_reads(self):
        house = sym("House", {"Role": "STRUCTURE", "Kind": "CONTROL_POINT", "CP Name": ""}, {1: ["MC"]})
        bare = sym("BareHouse", {"Role": "STRUCTURE", "Kind": "CONTROL_POINT"}, {1: ["MC"]})
        joint = sym("IRJ", {"Role": "TRACK", "Kind": "IRJ"}, {1: ["A", "B"]})
        industry = sym("Industry", {"Role": "TRACK", "Kind": "INDUSTRY", "Name": "${Value}"}, {1: ["A"]})
        sign = sym("Rule251", {"Role": "POLICY", "Kind": "RULE_251"}, {1: ["A"]})
        bit = sym("IB", {"Role": "IODRIVER", "IC": "CMRI", "Bit": ""}, {1: ["D"]})
        cells = {s.name: c for k in overview.convention_kinds([house, bare, joint, industry, sign, bit])
                 for s, c in zip(k.symbols, k.cells)}
        self.assertEqual(cells["House"]["Name"].flags, [])                  # keyed by CP Name, not Name
        self.assertIn("missing CP Name; the KiCad importer keys a STRUCTURE by it", cells["BareHouse"]["Name"].flags)
        for name in ("IRJ", "Rule251", "IB"):                               # a row's id, or a computed key
            self.assertEqual(cells[name]["Name"].flags, [], name)

    def test_g3_never_asks_for_a_field_only_another_style_carries(self):
        plain = sym("TC", {"Role": "APPLIANCE", "Appliance": "track_circuit", "Name": "${Value}",
                           "Indication": "${Name}K"}, {1: ["TC"]})
        virtual = sym("TCV", {"Role": "APPLIANCE", "Appliance": "track_circuit", "Style": "virtual",
                              "Name": "${Value}", "Indication": "${Name}K", "Members": "", "CP Name": ""}, {1: ["TC"]})
        lamp = sym("Aux", {"Role": "APPLIANCE", "Appliance": "lamp", "Name": "${Value}", "Indication": "${Name}K",
                           "CP Name": ""}, {1: ["MC"]})
        call = sym("MCall", {"Role": "APPLIANCE", "Appliance": "lamp", "Style": "maintainer_call", "Name": "${Value}MC"},
                   {1: ["MC"]})
        cells = {s.name: c for k in overview.convention_kinds([plain, virtual, lamp, call]) for s, c in zip(k.symbols, k.cells)}
        self.assertEqual(cells["TC"]["Other fields"].flags, [])                     # Members and CP Name: virtual's
        self.assertEqual(cells["MCall"]["Other fields"].flags, [])          # its house's MC wire, not CP Name

    def test_a_pin_field_naming_no_pin_is_flagged(self):
        pins = self.cell("TrackMCall", "Pins")
        self.assertEqual(pins.text, "Pin.MCK=level (no pin)")                     # MC is a seam pin: not listed
        self.assertEqual(self.cell("TrackMCall", "Units").text, "1 [seam]: MC")
        self.assertEqual(pins.flags, ["Pin.MCK names no pin"])

    def test_other_fields_compare_in_the_family_and_settings_never(self):
        self.assertTrue(any("missing Invert" in f for f in self.cell("LampB", "Other fields").flags))
        self.assertFalse(any("missing Address" in f for f in self.cell("LampB", "Other fields").flags))  # hardware
        self.assertFalse(any("hold_ms" in f for f in self.cell("LampA", "Other fields").flags))

    def test_page_has_the_conventions_tab_with_lint_messages(self):
        page, _ = overview.build_page([LEVER_SWITCH, LEVER_MCALL], "T", [], graphics=False)
        self.assertIn('<table id="conventions">', page)
        self.assertIn('data-tab="conventions"', page)
        self.assertEqual(page.count('<tbody data-flagged='), 2)
        self.assertIn('class="flag"', page)


class LintMessagesTests(unittest.TestCase):
    def test_each_symbol_carries_the_lints_messages_without_its_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            lib = Path(tmp) / "Fixture.kicad_sym"
            lib.write_text(FIXTURE)
            gadget = {s.name: s for s in overview.load_library(lib)}["Gadget"]
        self.assertTrue(gadget.lint)
        self.assertTrue(all(not m.startswith("Fixture:Gadget") for _, m in gadget.lint))
        self.assertIn(("error", "Pin.OCC = 'binary out' is not in the vocabulary (one primary word; direction is the pin type)"),
                      gadget.lint)

    def test_control_and_indication_are_contract_fields_not_settings(self):
        from contract.lint_symbol_fields import lint_symbol
        props = {"Role": "PANEL", "Appliance": "lever", "Style": "board", "Name": "${Value}MC",
                 "Control": "${Name}S", "Indication": "${Name}K", "Pin.MCS": "binary"}
        sym_dict = {"properties": props, "pins": [("~{MCS}", "1", "input")], "units": {1: ["~{MCS}"]},
                    "locked": False, "value_autoplace": False}
        self.assertEqual(lint_symbol("L", "S", sym_dict), [])
        per_pin = {**sym_dict, "properties": {"Role": "PANEL", "Appliance": "lever", "Style": "board", "Name": "${Value}",
                                              "Control.MCS": "${Value}MCS", "Indication.MCS": "", "Pin.MCS": "binary"}}
        self.assertEqual(lint_symbol("L", "S", per_pin), [])                    # per-pin tokens, an empty one included
        stray = {**per_pin, "properties": {**per_pin["properties"], "Indication.MCK": "${Value}MCK"}}
        self.assertEqual(lint_symbol("L", "S", stray), [("error", "L:S: Indication.MCK names no pin")])
        lamp = {**sym_dict, "properties": {"Role": "PANEL", "Appliance": "lamp", "Style": "board", "Name": "${Value}",
                                           "Indication": "1NATK | !Watsonville:837T1K", "Pin.LAMP": "binary"},
                "pins": [("~{LAMP}", "1", "input")], "units": {1: ["~{LAMP}"]}}
        self.assertEqual(lint_symbol("L", "S", lamp), [])
        self.assertIn("Control", overview.CONTRACT_FIELDS)
        self.assertIn("Indication", overview.CONTRACT_FIELDS)


if __name__ == "__main__":
    unittest.main()
