"""Unit tests for the symbol library overview page (tools/kicad_library_overview.py)."""

from __future__ import annotations

import io
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
        self.assertEqual(self.page.count('type="checkbox"'), len(self.table.headers))
        self.assertTrue({"colfilter", "colall", "colnone"} <= self.table.ids)
        self.assertIn('value="Role" checked> Role', self.page)          # always shown
        self.assertIn('value="Footprint"> Footprint', self.page)        # empty on every symbol: starts hidden
        self.assertIn('value="hold_ms" checked> hold_ms', self.page)    # filled on one symbol: shown
        self.assertIn("localStorage", self.page)
        self.assertNotIn("<script src=", self.page)  # no external dependency
        self.assertNotIn("<link ", self.page)

    def test_property_column_order(self):
        names = {"zeta", "Alpha", "Pin.B", "Pin.A", "Invert", "Role", "Description", "Reference", "Style"}
        self.assertEqual(overview.property_columns(names),
                         ["Role", "Style", "Description", "Invert", "Reference", "Pin.A", "Pin.B", "Alpha", "zeta"])

    def test_pin_base(self):
        self.assertEqual(overview.pin_base("~{OCC}"), "OCC")
        self.assertEqual(overview.pin_base("EN"), "EN")


if __name__ == "__main__":
    unittest.main()
