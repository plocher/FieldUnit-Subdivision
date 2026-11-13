"""A symbol's units: their names in the libraries and each pin's unit in the importer's input; and the lint of a train
order board's symbols, the trackplan board, the field mast whose pins are its faces, and the fascia lever (the owner,
2026-11-08)."""
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


def library(units: list[tuple[int, str | None, list]], name: str = "Device-TrainOrder", fields: dict[str, str] | None = None, **props: str) -> str:
    """A one-symbol library text: ``units`` are (number, unit name or None, pins); ``fields`` replaces the default
    train order unit device's fields, ``props`` adds to them."""
    if fields is None:
        fields = {"Role": "DEVICE", "Appliance": "train_order", "Name": "${Value}", "Pin.STOP": "binary", "Pin.SLOW": "binary",
                  "Pin.CALLON": "binary", "Pin.IND": "indication"}
    fields = {**fields, **props}
    return ('(kicad_symbol_lib\n\t(version 20251024)\n\t(generator "kicad_symbol_editor")\n\t(symbol "' + name + '"\n'
            + _prop("Reference", "D") + '\t\t(property "Value" ""\n\t\t\t(at 0 0 0)\n\t\t\t(do_not_autoplace yes)\n\t\t)\n'
            + "".join(_prop(k, v) for k, v in fields.items())
            + '\t\t(property "ki_locked" ""\n\t\t\t(at 0 0 0)\n\t\t)\n'
            + "".join(_unit(name, u, n, p) for u, n, p in units) + "\t)\n)\n")


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

    def test_two_pins_of_one_name_are_read_by_unit_only_and_refused_when_a_unit_has_no_name(self):
        """Same-named pins never overwrite each other: in named units of their own they are read by unit and left out
        of pins_of; one of them in no named unit, or two in one unit, is refused."""
        d1 = Symbol("D1", "Railroad-Field:Device-TrainOrder", "", {"Role": "DEVICE", "Appliance": "train_order", "Name": "Gilroy"}, "/X/")
        x1 = Symbol("X1", "Railroad-HardwareIO:Driver", "", {"Role": "IODRIVER", "IC": "MAX7311", "Address": "0x20"}, "/X/")
        both = [Net("ns", (PinRef("D1", "STOP", unit="N"), PinRef("X1", "A0"))), Net("ss", (PinRef("D1", "STOP", unit="S"), PinRef("X1", "A1")))]
        src = from_symbols([d1, x1], both)
        self.assertEqual(sorted(src.pins_of("D1")), [])
        self.assertIsNone(src.net_of("D1", "STOP"))
        self.assertEqual({u: sorted(p) for u, p in src.pins_of_units("D1").items()}, {"N": ["STOP"], "S": ["STOP"]})
        for second in (PinRef("D1", "STOP"), PinRef("D1", "STOP", unit="N")):
            with self.assertRaises(ValueError) as e:
                from_symbols([d1, x1], [both[0], Net("ss", (second, PinRef("X1", "A1")))])
            self.assertIn("Railroad-Field:Device-TrainOrder(Gilroy): 2 pins named 'STOP'", str(e.exception))   # located by symbol and Name, never by reference
        unnamed = [Net("a", (PinRef("D1", "STOP"), PinRef("X1", "A0"))), Net("b", (PinRef("D1", "STOP"), PinRef("X1", "A1")))]
        src = from_symbols([d1, x1], unnamed)                            # repeats in unnamed units read as before: the last wins
        self.assertEqual(src.net_of("D1", "STOP").name, "b")

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


MAST = {"Role": "DEVICE", "Appliance": "train_order_mast", "Name": "${Value}"}
LEVER = {"Role": "DEVICE", "Appliance": "lever", "Style": "train_order", "Name": "${Value}", "Pin.STOP": "binary", "Pin.SLOW": "binary"}
BOARD = {"Role": "APPLIANCE", "Appliance": "train_order", "Name": "${Value}", "Station": "", "Style": "double"}
LEVER_PINS = [("IND", "1", "input"), ("~{STOP}", "2", "output"), ("~{SLOW}", "3", "output")]


class TrainOrderSymbolLint(unittest.TestCase):
    """The lint of a train order board's symbols (the owner, 2026-11-08): the trackplan board states Style single or
    double and Station and has no pins; the field mast has one passive pin per face, a double mast's named N, S, E
    or W, Pin.<pin>=indication; the fascia lever's IND is the face it serves (a membership pin, no Pin.IND) and its
    function pins are STOP and SLOW, binary outputs; no code line token on the lever."""

    def lint(self, text: str, name: str) -> list[str]:
        sym = library_symbols(text)[name]
        return [m.removeprefix(f"L:{name}: ") for s, m in lint_symbol("L", name, sym) if s == "error"]

    def mast(self, pins: list[tuple[str, str, str]], **props: str) -> list[str]:
        fields = {**MAST, **{f"Pin.{n}": "indication" for n, _, _ in pins}}
        return self.lint(library([(1, None, pins)], "Device-TrainOrder-Mast", fields, **props), "Device-TrainOrder-Mast")

    def test_a_double_mast_has_two_direction_pins_and_a_single_one_pin_of_any_name(self):
        self.assertEqual(self.mast([("E", "1", "passive"), ("W", "2", "passive")]), [])
        self.assertEqual(self.mast([("N", "1", "passive"), ("S", "2", "passive")]), [])
        self.assertEqual(self.mast([("TO", "1", "passive")]), [])
        self.assertEqual(self.mast([("A", "1", "passive"), ("B", "2", "passive")]),
                         ["a double train order mast's pins are two of N, S, E, W, the direction each face serves; this has A, B"])
        self.assertEqual(self.mast([]), ["a train order mast has one passive pin per face; this has none"])
        self.assertIn("pin E is input; a field mast's position pin is passive, so a consumer may take one position or several tied together",
                      self.mast([("E", "1", "input"), ("W", "2", "passive")]))
        self.assertIn("Pin.E = 'binary'; a field mast's pins are kind indication", self.mast([("E", "1", "passive"), ("W", "2", "passive")], **{"Pin.E": "binary"}))
        self.assertIn("a field mast states no Style; the pin set states the head count", self.mast([("E", "1", "passive"), ("W", "2", "passive")], Style="double"))

    def lever(self, pins=LEVER_PINS, fields: dict[str, str] = LEVER, **props: str) -> list[str]:
        return self.lint(library([(1, None, pins)], "Local-TrainOrder", fields, **props), "Local-TrainOrder")

    def test_a_lever_has_ind_for_its_face_and_stop_and_slow_as_binary_outputs(self):
        self.assertEqual(self.lever(), [])
        self.assertEqual(self.lever([("~{STOP}", "2", "output"), ("~{SLOW}", "3", "output")]),
                         ["a train order lever has an IND pin, the face it serves, wired to the mast's face pin"])
        self.assertEqual(self.lever([("IND", "1", "output"), ("~{STOP}", "2", "output"), ("~{SLOW}", "3", "output")]),
                         ["pin IND is output; a train order lever's IND is an input, the face it serves"])
        self.assertIn("Pin.IND: a train order lever's IND is the face it serves, not a capability", self.lever(**{"Pin.IND": "indication"}))
        self.assertIn("a train order lever's function pins are STOP, SLOW; this has CALLON, SLOW, STOP",
                      self.lever(LEVER_PINS + [("~{CALLON}", "4", "output")], **{"Pin.CALLON": "binary"}))
        self.assertIn("pin ~{STOP} is input; a train order lever's STOP is an output",
                      self.lever([("IND", "1", "input"), ("~{STOP}", "2", "input"), ("~{SLOW}", "3", "output")]))
        self.assertIn("Pin.SLOW = 'level'; a train order lever's SLOW is binary", self.lever(**{"Pin.SLOW": "level"}))

    def test_no_code_line_token_on_a_lever(self):
        self.assertEqual(self.lever(IndicationToken="GilroyK"), ["field IndicationToken: a train order board's control is local; no code line token"])
        self.assertIn("field Control.STOP: a train order board's control is local; no code line token", self.lever(**{"Control.STOP": "${Value}S"}))

    def board(self, pins=(), **props: str) -> list[str]:
        fields = {**BOARD, **props}
        return self.lint(library([(1, None, list(pins))], "Train Order Mast Double", fields), "Train Order Mast Double")

    def test_a_trackplan_board_states_style_and_station_and_has_no_pins(self):
        self.assertEqual(self.board(), [])
        self.assertEqual(self.board(Style="single"), [])
        self.assertEqual(self.board(Style="dwarf"), ["a train order board states Style, one of single, double; this has dwarf"])
        self.assertIn("a train order board has no pins; its faces are its field mast's; this has H", self.board([("H", "1", "passive")]))
        fields = {k: v for k, v in BOARD.items() if k != "Station"}
        self.assertEqual(self.lint(library([(1, None, [])], "Train Order Mast Double", fields), "Train Order Mast Double"),
                         ["a train order board states Station, the timetable station it stands at"])


if __name__ == "__main__":
    unittest.main()


class SwitchSymbolLint(unittest.TestCase):
    """The lint of a switch or derail symbol (the owner, 2026-11-09): its Style states exactly one regime word from
    grammar.REGIMES; derail may stand beside it; none or two is a symbol contract defect, caught here and never a
    model finding."""

    PORTS = [("C", "1", "passive"), ("N", "2", "passive"), ("R", "3", "passive")]

    def lint(self, style: str, name: str = "Switch_Powered") -> list[str]:
        fields = {"Role": "APPLIANCE", "Appliance": "switch", "Name": "${Value}", "Style": style}
        sym = library_symbols(library([(1, None, self.PORTS)], name, fields))[name]
        return [m.removeprefix(f"L:{name}: ") for s, m in lint_symbol("L", name, sym) if s == "error"]

    def test_a_switch_states_one_regime_word_and_a_derail_adds_the_word_derail(self):
        for style in ("powered", "dual", "local", "lock", "manual_sensed", "manual", "spring", "derail,powered", "derail, manual"):
            self.assertEqual(self.lint(style), [], style)
        want = "a switch or derail states exactly one regime word in Style, one of dual, local, lock, manual, manual_sensed, powered, spring, with derail beside it on a derail; this has "
        self.assertEqual(self.lint("derail"), [want + "none"])
        self.assertEqual(self.lint(""), [want + "none"])
        self.assertEqual(self.lint("powered,dual"), [want + "powered, dual"])
