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
    """Headers (first thead row), one list of cell texts per tbody row, and the ids and classes seen."""

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

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        self.classes.update((attrs.get("class") or "").split())
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

    def test_page_has_resize_reorder_and_value_filter_controls(self):
        n = len(self.table.headers)
        self.assertEqual(self.page.count('<th class="sortable" draggable="true" data-col='), n)
        self.assertEqual(self.page.count('<span class="grip"'), n)
        self.assertIn("table-layout:fixed", self.page)
        self.assertEqual(self.page.count('<button type="button" class="funnel"'), n)  # no Graphics column here
        self.assertTrue({"valuepanel", "valuesearch", "valall", "valclear", "valuelist"} <= self.table.ids)
        self.assertIn("funnel", self.table.classes)
        self.assertNotIn('id="imgsize"', self.page)  # no graphics, no size control

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
        symbols = overview.load_library(lib)
        symbols[0].graphics = ["svg-Fixture/Gadget_unit1.svg", "svg-Fixture/Gadget_unit2.svg"]
        cls.page, cls.columns = overview.build_page(symbols, "Graphics fixture", [lib], graphics=True)
        cls.table = TableReader()
        cls.table.feed(cls.page)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_graphics_column_count_and_images(self):
        self.assertEqual(self.table.headers[:6], ["Library", "Symbol", "Role", "Appliance", "Graphics", "Description"])
        self.assertIn('value="Graphics" checked> Graphics (1)</label>', self.page)
        self.assertEqual(self.table.images, ["svg-Fixture/Gadget_unit1.svg", "svg-Fixture/Gadget_unit2.svg"])
        self.assertEqual(self.page.count('loading="lazy"'), 2)

    def test_graphics_size_control_and_no_value_filter(self):
        self.assertIn('<select id="imgsize"', self.page)
        for size in ("S", "M", "XL"):
            self.assertIn(f'<option value="{size}">{size}</option>', self.page)
        self.assertIn('<option value="L" selected>L</option>', self.page)
        self.assertIn('<table id="symbols" data-size="L">', self.page)
        self.assertIn("table[data-size=L]{--imgw:720px;--imgh:500px}", self.page)
        # The image box follows the size variables: width set (not only capped, since the SVGs are smaller than
        # every box), height by aspect up to --imgh, contained. max-width alone never enlarged the intrinsic size.
        self.assertIn("td.graphics img{width:var(--imgw,720px);height:auto;max-height:var(--imgh,500px);object-fit:contain", self.page)
        self.assertNotIn("td.graphics img{max-width", self.page)
        n = len(self.table.headers)
        self.assertEqual(self.page.count('<button type="button" class="funnel"'), n - 1)  # Graphics has no value filter
        self.assertEqual(self.page.count('<span class="grip"'), n)

    def test_property_column_order(self):
        names = {"zeta", "Alpha", "Pin.B", "Pin.A", "Invert", "Role", "Description", "Reference", "Style"}
        self.assertEqual(overview.property_columns(names),
                         ["Role", "Style", "Description", "Invert", "Reference", "Pin.A", "Pin.B", "Alpha", "zeta"])

    def test_pin_base(self):
        self.assertEqual(overview.pin_base("~{OCC}"), "OCC")
        self.assertEqual(overview.pin_base("EN"), "EN")


if __name__ == "__main__":
    unittest.main()
