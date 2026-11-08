"""A symbol's units: their names in the libraries, each pin's unit in the importer's input, and the lint of a train
order board's field device, whose units are its faces (the owner, 2026-11-05)."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from contract.lint_symbol_fields import lint_symbol  # noqa: E402
from kicad_services.sch_text import library_symbols  # noqa: E402
from kicad_services.symbol_library_reader import SymbolLibraryReader  # noqa: E402
from tools.layout_compiler.source import Net, PinRef, Symbol, from_netlist, from_symbols  # noqa: E402


def _pin(name: str, number: str, etype: str) -> str:
    return (f'\t\t\t(pin {etype} line\n\t\t\t\t(at 0 0 0)\n\t\t\t\t(length 2.54)\n'
            f'\t\t\t\t(name "{name}"\n\t\t\t\t\t(effects\n\t\t\t\t\t\t(font\n\t\t\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t\t\t)\n\t\t\t\t\t)\n\t\t\t\t)\n'
            f'\t\t\t\t(number "{number}"\n\t\t\t\t\t(effects\n\t\t\t\t\t\t(font\n\t\t\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t\t\t)\n\t\t\t\t\t)\n\t\t\t\t)\n\t\t\t)\n')


def _prop(name: str, value: str) -> str:
    return f'\t\t(property "{name}" "{value}"\n\t\t\t(at 0 0 0)\n\t\t)\n'


def _unit(symbol: str, unit: int, name: str | None, pins: list[tuple[str, str, str]]) -> str:
    head = f'\t\t(symbol "{symbol}_{unit}_1"\n' + (f'\t\t\t(unit_name "{name}")\n' if name else "")
    return head + "".join(_pin(*p) for p in pins) + "\t\t)\n"


def face_pins(unit: int) -> list[tuple[str, str, str]]:
    n = (unit - 1) * 4
    return [("STOP", str(n + 1), "input"), ("SLOW", str(n + 2), "input"), ("CALLON", str(n + 3), "input"), ("IND", str(n + 4), "output")]


def library(units: list[tuple[int, str | None, list]], **props: str) -> str:
    fields = {"Role": "DEVICE", "Appliance": "train_order", "Name": "${Value}", "Pin.STOP": "binary", "Pin.SLOW": "binary",
              "Pin.CALLON": "binary", "Pin.IND": "indication", **props}
    return ('(kicad_symbol_lib\n\t(version 20251024)\n\t(generator "kicad_symbol_editor")\n\t(symbol "Device-TrainOrder"\n'
            + _prop("Reference", "D") + '\t\t(property "Value" ""\n\t\t\t(at 0 0 0)\n\t\t\t(do_not_autoplace yes)\n\t\t)\n'
            + "".join(_prop(k, v) for k, v in fields.items())
            + '\t\t(property "ki_locked" ""\n\t\t\t(at 0 0 0)\n\t\t)\n'
            + "".join(_unit("Device-TrainOrder", u, n, p) for u, n, p in units) + "\t)\n)\n")


TWO_FACES = library([(1, "N", face_pins(1)), (2, "S", face_pins(2))])


class UnitNames(unittest.TestCase):
    def test_the_text_reader_lists_the_units_names(self):
        sym = library_symbols(TWO_FACES)["Device-TrainOrder"]
        self.assertEqual(sym["unit_names"], {1: "N", 2: "S"})
        self.assertEqual(sym["units"][2], ["STOP", "SLOW", "CALLON", "IND"])
        self.assertEqual(library_symbols(library([(1, None, face_pins(1))]))["Device-TrainOrder"]["unit_names"], {})

    def test_the_library_reader_gives_each_pin_its_unit_and_the_units_their_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            lib = Path(tmp) / "Fixture.kicad_sym"
            lib.write_text(TWO_FACES)
            sym = SymbolLibraryReader().read(lib).get("Device-TrainOrder")
        self.assertEqual(sym.unit_names, {1: "N", 2: "S"})
        self.assertEqual({p.number: p.unit for p in sym.pins}, {str(n): 1 + (n - 1) // 4 for n in range(1, 9)})
        self.assertEqual((sym.unit_name_of("1"), sym.unit_name_of("8"), sym.unit_name_of("9")), ("N", "S", ""))


NETLIST = """(export (version "E")
  (design (source "{sch}"))
  (components
    (comp (ref "D1") (value "Gilroy")
      (fields (field (name "Role") "DEVICE") (field (name "Appliance") "train_order") (field (name "Name") "Gilroy"))
      (libsource (lib "Fixture") (part "Device-TrainOrder"))
      (sheetpath (names "/X/") (tstamps "/aaaa/")))
    (comp (ref "X1") (value "0x20")
      (fields (field (name "Role") "IODRIVER") (field (name "IC") "MAX7311") (field (name "Address") "0x20"))
      (libsource (lib "Nowhere") (part "Driver"))
      (sheetpath (names "/X/") (tstamps "/aaaa/"))))
  (nets
    (net (code "1") (name "ns") (node (ref "D1") (pin "1") (pinfunction "STOP_1") (pintype "input")) (node (ref "X1") (pin "1") (pinfunction "A0_1") (pintype "output")))
    (net (code "2") (name "ss") (node (ref "D1") (pin "5") (pinfunction "STOP_5") (pintype "input")) (node (ref "X1") (pin "2") (pinfunction "A1_2") (pintype "output")))))
"""


class PinUnits(unittest.TestCase):
    def test_a_fragment_states_a_pins_unit_and_the_source_reads_pins_by_unit(self):
        d1 = Symbol("D1", "Railroad-Field:Device-TrainOrder", "", {"Role": "DEVICE", "Appliance": "train_order", "Name": "Gilroy"}, "/X/")
        x1 = Symbol("X1", "Railroad-HardwareIO:Driver", "", {"Role": "IODRIVER", "IC": "MAX7311", "Address": "0x20"}, "/X/")
        src = from_symbols([d1, x1], [Net("ns", (PinRef("D1", "STOP", unit="N"), PinRef("X1", "A0"))),
                                       Net("ss", (PinRef("D1", "STOP", unit="S"), PinRef("X1", "A1"))),
                                       Net("i", (PinRef("D1", "IND"), PinRef("X1", "A2")))])
        by_unit = src.pins_of_units("D1")
        self.assertEqual({u: sorted(pins) for u, pins in by_unit.items()}, {"N": ["STOP"], "S": ["STOP"], "": ["IND"]})
        self.assertEqual((by_unit["N"]["STOP"].name, by_unit["S"]["STOP"].name), ("ns", "ss"))
        self.assertEqual(src.pins_of_units("X1"), {"": {"A0": by_unit["N"]["STOP"], "A1": by_unit["S"]["STOP"], "A2": by_unit[""]["IND"]}})

    def test_a_netlist_names_each_pins_unit_from_the_library_the_export_names(self):
        """The netlist carries pin numbers; the library says which unit each is drawn in and what the unit is called.
        A library that cannot be found names no unit."""
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "Fixture.kicad_sym").write_text(TWO_FACES)
            net = Path(tmp) / "x.net"
            net.write_text(NETLIST.format(sch=str(Path(tmp) / "x.kicad_sch")))
            src = from_netlist(net, libraries={"Fixture": Path(tmp) / "Fixture.kicad_sym"})
            self.assertEqual({u: sorted(p) for u, p in src.pins_of_units("D1").items()}, {"N": ["STOP"], "S": ["STOP"]})
            self.assertEqual(sorted((p.ref, p.pin, p.unit) for n in src.nets for p in n.pins),
                             [("D1", "STOP", "N"), ("D1", "STOP", "S"), ("X1", "A0", ""), ("X1", "A1", "")])
            src = from_netlist(net, libraries={})
            self.assertEqual(src.pins_of_units("D1"), {"": {"STOP": src.net_of("D1", "STOP")}})


class TrainOrderDeviceLint(unittest.TestCase):
    """The lint of a train order board's field device (the owner, 2026-11-05): one unit per face named N, S, E or W;
    each unit STOP, SLOW, CALLON in (binary) and IND out (indication); no Style, Kind or code line token."""

    def lint(self, text: str) -> list[str]:
        sym = library_symbols(text)["Device-TrainOrder"]
        return [m.removeprefix("L:Device-TrainOrder: ") for s, m in lint_symbol("L", "Device-TrainOrder", sym) if s == "error"]

    def test_two_faces_and_one_face_pass(self):
        self.assertEqual(self.lint(TWO_FACES), [])
        self.assertEqual(self.lint(library([(1, "W", face_pins(1))])), [])

    def test_a_unit_without_a_face_name_fails(self):
        self.assertEqual(self.lint(library([(1, None, face_pins(1))])), ["unit 1 has no name; a face is a unit named one of N, S, E, W"])
        self.assertEqual(self.lint(library([(1, "A", face_pins(1))])), ["unit 1 is named 'A'; a face is a unit named one of N, S, E, W"])

    def test_a_faces_pins_are_its_three_inputs_and_one_output(self):
        self.assertIn("unit 1 has pins CALLON, SLOW, STOP; a face has STOP, SLOW, CALLON in and IND out", self.lint(library([(1, "N", face_pins(1)[:3])])))
        two_ind = library([(1, "N", face_pins(1) + [("IND", "9", "output")])])
        self.assertEqual(self.lint(two_ind), ["unit 1 has pins CALLON, IND, IND, SLOW, STOP; a face has STOP, SLOW, CALLON in and IND out"])
        self.assertEqual(self.lint(library([(1, "N", [("STOP", "1", "output"), ("SLOW", "2", "input"), ("CALLON", "3", "input"), ("IND", "4", "output")])])),
                         ["pin STOP is output; a face's STOP is an input"])
        self.assertEqual(self.lint(library([(1, "N", face_pins(1))], **{"Pin.SLOW": "level"})),
                         ["Pin.SLOW = 'level'; a face's SLOW is binary"])
        self.assertEqual(self.lint(library([(1, "N", face_pins(1))], **{"Pin.IND": "binary"})),
                         ["Pin.IND = 'binary'; a face's IND is indication"])

    def test_no_code_line_token_and_no_style_or_kind(self):
        self.assertEqual(self.lint(library([(1, "N", face_pins(1))], IndicationToken="GilroyK")),
                         ["field IndicationToken: a train order board's control is local; no code line token"])
        self.assertIn("field Control.STOP: a train order board's control is local; no code line token",
                      self.lint(library([(1, "N", face_pins(1))], **{"Control.STOP": "${Value}S"})))
        self.assertEqual(self.lint(library([(1, "N", face_pins(1))], Style="board")), ["a train order device states no Style; its faces are its units"])


if __name__ == "__main__":
    unittest.main()
