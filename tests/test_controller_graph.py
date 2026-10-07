"""Tests for the controller compiler and subdivision linker seams.

Seams under test (agreed 2026-09-29):
  1. kicad_services.NetlistReader.read — components carry sheetpath.
  2. controller_graph.compile_controller(netlist) -> ControllerFragment.
  3. link.link_subdivision(controller fragments, plant models) -> SubdivisionModel.

Ground truth for the golden assertions is the hand-written FieldUnit
examples/spcoast_ctc/IO-I2C.h bit map, frozen in the 2026-09-28 handoff.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "kicad"

if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from kicad_services.netlist_reader import NetlistReader
from controller_graph.compiler import compile_controller
from link.linker import link_subdivision
from controller_graph.types import (
    Codeline,
    ControllerFragment,
    Machine,
)


def read_luchessa_plant():
    with open(FIXTURES / "Luchessa.plant-model.json") as handle:
        return json.load(handle)


def read_golden():
    return NetlistReader().read(FIXTURES / "South-cTc.net")


def compile_minimal(mutate=None):
    """Compile the minimal controller fixture, optionally text-mutated."""
    text = (FIXTURES / "minimal_controller.net").read_text()
    if mutate is not None:
        text = mutate(text)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "mutated.net"
        path.write_text(text)
        return compile_controller(NetlistReader().read(path))


def errors(fragment):
    return [d for d in fragment.diagnostics if d.severity == "error"]


def drop_net(text, net_name):
    """Remove one 3-line net block from the minimal fixture text."""
    lines = text.splitlines(keepends=True)
    start = next(i for i, line in enumerate(lines) if net_name in line)
    return "".join(lines[:start] + lines[start + 3 :])


class NetlistSheetpathTests(unittest.TestCase):
    """Seam 1: the reader keeps each component's sheet path."""

    def test_reader_keeps_design_sheets(self):
        model = NetlistReader().read(FIXTURES / "South-cTc.net")
        self.assertIn("/", model.sheets)
        self.assertIn("/Luchessa/", model.sheets)
        self.assertIn("/Gilroy CalTrain/", model.sheets)

    def test_components_carry_sheetpath(self):
        model = NetlistReader().read(FIXTURES / "South-cTc.net")
        self.assertEqual(model.components["MACHINE2"].sheetpath, "/")
        self.assertEqual(model.components["COL4"].sheetpath, "/Luchessa/")
        self.assertEqual(
            model.components["CODELINE1"].sheetpath, "/Gilroy CalTrain/"
        )


class ControllerColumnTests(unittest.TestCase):
    """Seam 2: columns are CPs, named by CP Name, owned by their sheet."""

    def test_columns_are_cps_on_their_interlocking_sheet(self):
        fragment = compile_controller(read_golden())
        self.assertEqual(fragment.machine.name, "SPCoast South")
        self.assertEqual(fragment.machine.machine_type, "US&S506")
        cols = {c.number: c for c in fragment.columns}
        self.assertEqual(sorted(cols), [5, 6, 7])
        self.assertEqual(cols[5].cp_name, "CP Luchessa")
        self.assertEqual(cols[6].cp_name, "CP Gilroy")
        self.assertEqual(cols[7].cp_name, "CP Carnadero")
        self.assertEqual(cols[5].interlocking, "Luchessa")


class ControllerApplianceTests(unittest.TestCase):
    """Seam 2: appliance-to-column membership comes from nets."""

    def test_appliances_resolve_to_their_column(self):
        fragment = compile_controller(read_golden())
        apps = {(a.kind, a.name): a for a in fragment.appliances}
        # Reference trap: netlist ref SW784 holds plant switch 783.
        self.assertEqual(apps[("SWITCH_LEVER", "783")].column, 5)
        self.assertEqual(apps[("SIGNAL_LEVER", "784")].column, 5)
        self.assertEqual(apps[("SWITCH_LEVER", "795")].column, 6)
        self.assertEqual(apps[("SWITCH_LEVER", "799")].column, 7)
        self.assertEqual(apps[("MAINTAINER_CALL", "MC1")].column, 6)
        self.assertEqual(apps[("CODE", "CODE")].column, 7)


class ApplianceTokenTests(unittest.TestCase):
    """Seam 2: lamps carry IndicationToken lists; MCall carries ControlToken."""

    def test_lamp_and_control_tokens(self):
        fragment = compile_controller(read_golden())
        lamps = {
            a.indication_tokens: a
            for a in fragment.appliances
            if a.kind == "LAMP"
        }
        self.assertEqual(lamps[("783T1",)].column, 5)
        self.assertEqual(lamps[("1NAT",)].column, 6)
        self.assertEqual(lamps[("795T1", "2NAAT", "799T1")].column, 6)
        self.assertEqual(lamps[("MC1K",)].column, 6)
        mcall = next(
            a for a in fragment.appliances if a.kind == "MAINTAINER_CALL"
        )
        self.assertEqual(mcall.control_tokens, ("MC1S",))


class DriveBitGoldenTests(unittest.TestCase):
    """Golden: bindings match the hand-written spcoast_ctc IO-I2C.h map."""

    def test_luchessa_bit_map_matches_hand_written_desk(self):
        fragment = compile_controller(read_golden())
        apps = {a.reference: a for a in fragment.appliances}
        bound = {}
        for b in fragment.bindings:
            a = apps[b.appliance]
            key = (
                a.indication_tokens
                if a.kind == "LAMP"
                else (a.name, b.function)
            )
            bound[key] = (b.driver, b.bit)

        # Switch levers: NWS/RWS in, NWK/RWK lamps out (IO-I2C.h bits 7/6/0/1)
        for name, drv in (("783", "0x24"), ("795", "0x25"), ("799", "0x26")):
            self.assertEqual(bound[(name, "NWS")], (drv, 7))
            self.assertEqual(bound[(name, "RWS")], (drv, 6))
            self.assertEqual(bound[(name, "NWK")], (drv, 0))
            self.assertEqual(bound[(name, "RWK")], (drv, 1))
        # Signal lever 784 (IO-I2C.h bits 9/10/11 in, 13/14/15 out)
        for fn, bit in (
            ("NGS", 9), ("HS", 10), ("SGS", 11),
            ("NGK", 13), ("SGK", 14), ("TEK", 15),
        ):
            self.assertEqual(bound[("784", fn)], ("0x24", bit))
        self.assertEqual(bound[("MC1", "SW")], ("0x25", 2))
        self.assertEqual(bound[("CODE", "CODE")], ("0x26", 12))
        # Lamps, identified by their indication tokens
        self.assertEqual(bound[("783T1",)], ("0x24", 3))
        self.assertEqual(bound[("1NAT",)], ("0x25", 3))
        self.assertEqual(bound[("795T1", "2NAAT", "799T1")], ("0x25", 4))
        self.assertEqual(bound[("MC1K",)], ("0x25", 8))


class CodelineTests(unittest.TestCase):
    """Seam 2: one CODELINE per interlocking sheet; codeline-only = stub."""

    def test_one_codeline_per_sheet_with_stub_recognition(self):
        fragment = compile_controller(read_golden())
        lines = {c.interlocking: c for c in fragment.codelines}
        self.assertEqual(len(lines), 7)
        luchessa = lines["Luchessa"]
        self.assertEqual(luchessa.transport, "VIRTUAL")
        self.assertEqual(luchessa.station, "Luchessa")
        self.assertFalse(luchessa.stub)
        caltrain = lines["Gilroy CalTrain"]
        self.assertEqual(caltrain.station, "Gilroy CalTrain")
        self.assertEqual(caltrain.station_key, "gilroycaltrain")
        self.assertTrue(caltrain.stub)


class DiagnosticBaselineTests(unittest.TestCase):
    """Seam 2: clean inputs are silent; a netless netlist is an error."""

    def test_clean_minimal_controller_has_no_diagnostics(self):
        fragment = compile_minimal()
        self.assertEqual(fragment.diagnostics, [])
        self.assertEqual([c.number for c in fragment.columns], [1])
        self.assertFalse(fragment.codelines[0].stub)

    def test_panel_role_with_asserted_low_pins(self):
        """ADR 0003: Role PANEL; a ~{X} pin is function X, asserted-low."""

        def mutate(text):
            text = text.replace('(field (name "Role") "APPLIANCE")', '(field (name "Role") "PANEL")')
            return text.replace('(pinfunction "NWS_2")', '(pinfunction "~{NWS}_2")')

        fragment = compile_minimal(mutate=mutate)
        self.assertEqual(fragment.diagnostics, [])
        nws = [b for b in fragment.bindings if b.function == "NWS"]
        rws = [b for b in fragment.bindings if b.function == "RWS"]
        self.assertEqual([b.active_low for b in nws], [True])
        self.assertEqual([b.active_low for b in rws], [False])

    def test_golden_netlist_has_no_errors(self):
        self.assertEqual(errors(compile_controller(read_golden())), [])

    def test_components_with_zero_nets_is_an_error(self):
        fragment = compile_minimal(
            mutate=lambda text: text[: text.index("(nets")] + ")"
        )
        codes = [d.code for d in errors(fragment)]
        self.assertIn("netlist-no-nets", codes)


class MembershipDiagnosticTests(unittest.TestCase):
    """Seam 2: §7 membership and drive-bit errors."""

    def test_appliance_without_column_is_an_error(self):
        fragment = compile_minimal(
            mutate=lambda t: drop_net(t, "Net-(SW1-Column)")
        )
        found = [d for d in errors(fragment) if d.code == "appliance-no-column"]
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].subject, "SW1")

    def test_appliance_on_two_columns_is_an_error(self):
        second_col = (
            '    (comp (ref "COL2")\n'
            '      (value "2")\n'
            "      (fields\n"
            '        (field (name "Role") "COLUMN")\n'
            '        (field (name "CP Name") "CP Beta"))\n'
            '      (libsource (lib "RailroadPanel") (part "PanelColumn"))\n'
            '      (sheetpath (names "/Alpha/") (tstamps "/aaaa/")))\n'
        )
        extra_node = (
            '      (node (ref "COL2") (pin "5") (pinfunction "Column_5")'
            ' (pintype "free"))\n'
        )

        def mutate(text):
            text = text.replace(
                '    (comp (ref "U1")', second_col + '    (comp (ref "U1")'
            )
            anchor = (
                '(node (ref "COL1") (pin "5") (pinfunction "Column_5")'
                ' (pintype "free"))\n'
            )
            return text.replace(anchor, anchor + extra_node, 1)

        fragment = compile_minimal(mutate=mutate)
        codes = {d.code: d for d in errors(fragment)}
        self.assertIn("appliance-multiple-columns", codes)
        self.assertEqual(codes["appliance-multiple-columns"].subject, "SW1")

    def test_unbound_function_pin_is_an_error(self):
        # KiCad still lists an unwired pin (as an unconnected- net), so the
        # realistic failure is a function net with no driver node on it.
        # The node is the net's last line, so one closing paren stays behind
        # to close the (now single-node) net.
        driver_node = (
            '      (node (ref "U1") (pin "8") (pinfunction "bit7_8")'
            ' (pintype "input"))'
        )
        fragment = compile_minimal(mutate=lambda t: t.replace(driver_node, ""))
        found = [d for d in errors(fragment) if d.code == "function-unbound"]
        self.assertEqual(len(found), 1)
        self.assertIn("NWS", found[0].message)


class ColumnRuleDiagnosticTests(unittest.TestCase):
    """Seam 2: §7 column rules — lever rule and CP Name."""

    def test_two_switch_levers_on_one_column_is_an_error(self):
        # Rewire the lamp into a second switch lever on COL1.
        def mutate(text):
            text = text.replace('(field (name "Kind") "LAMP")', '(field (name "Kind") "SWITCH_LEVER")')
            return text.replace('(field (name "IndicationToken") "10T1")', '(field (name "IndicationToken") "")')

        fragment = compile_minimal(mutate=mutate)
        codes = [d.code for d in errors(fragment)]
        self.assertIn("column-lever-rule", codes)

    def test_column_with_no_levers_is_an_error(self):
        fragment = compile_minimal(
            mutate=lambda t: t.replace(
                '(field (name "Kind") "SWITCH_LEVER")',
                '(field (name "Kind") "AUXILIARY")',
            )
        )
        codes = [d.code for d in errors(fragment)]
        self.assertIn("column-lever-rule", codes)

    def test_cp_name_placeholder_is_an_error(self):
        fragment = compile_minimal(
            mutate=lambda t: t.replace(
                '(field (name "CP Name") "CP Alpha")',
                '(field (name "CP Name") "CP NAME")',
            )
        )
        found = [d for d in errors(fragment) if d.code == "cp-name-unset"]
        self.assertEqual(len(found), 1)

    def test_cp_name_empty_is_an_error(self):
        fragment = compile_minimal(
            mutate=lambda t: t.replace(
                '(field (name "CP Name") "CP Alpha")',
                '(field (name "CP Name") "")',
            )
        )
        found = [d for d in errors(fragment) if d.code == "cp-name-unset"]
        self.assertEqual(len(found), 1)


CODELINE_BLOCK = (
    '    (comp (ref "CODELINE1")\n'
    '      (value "VIRTUAL")\n'
    "      (fields\n"
    '        (field (name "Role") "CODELINE")\n'
    '        (field (name "Station") "Alpha"))\n'
    '      (libsource (lib "RailroadPanel") (part "Codeline-Virtual"))\n'
    '      (sheetpath (names "/Alpha/") (tstamps "/aaaa/")))\n'
)


class SheetRuleDiagnosticTests(unittest.TestCase):
    """Seam 2: §7 sheet rules — one CODE, one CODELINE per drawn sheet."""

    def test_drawn_sheet_without_code_is_an_error(self):
        fragment = compile_minimal(
            mutate=lambda t: t.replace(
                '(field (name "Kind") "CODE")',
                '(field (name "Kind") "AUXILIARY")',
            )
        )
        self.assertIn("sheet-code-count", [d.code for d in errors(fragment)])

    def test_drawn_sheet_with_two_codes_is_an_error(self):
        fragment = compile_minimal(
            mutate=lambda t: t.replace(
                '(field (name "Kind") "LAMP")', '(field (name "Kind") "CODE")'
            )
        )
        self.assertIn("sheet-code-count", [d.code for d in errors(fragment)])

    def test_drawn_sheet_without_codeline_is_an_error(self):
        fragment = compile_minimal(
            mutate=lambda t: t.replace(CODELINE_BLOCK, "")
        )
        self.assertIn(
            "sheet-codeline-count", [d.code for d in errors(fragment)]
        )

    def test_empty_sheet_gets_a_defaulted_virtual_codeline(self):
        # A really empty stub page, without even a codeline symbol: we know
        # enough to fill in the blank, though it is only good for a doc
        # packet that says TBD.
        def mutate(text):
            return text.replace(
                '(tool "hand-written fixture")',
                '(tool "hand-written fixture")\n'
                '    (sheet (number "1") (name "/") (tstamps "/"))\n'
                '    (sheet (number "2") (name "/Alpha/") (tstamps "/aaaa/"))\n'
                '    (sheet (number "3") (name "/Beta/") (tstamps "/bbbb/"))',
            )

        fragment = compile_minimal(mutate=mutate)
        lines = {c.interlocking: c for c in fragment.codelines}
        beta = lines["Beta"]
        self.assertEqual(beta.transport, "VIRTUAL")
        self.assertEqual(beta.station, "Beta")
        self.assertTrue(beta.stub)
        self.assertTrue(beta.defaulted)
        self.assertFalse(lines["Alpha"].defaulted)
        infos = [
            d
            for d in fragment.diagnostics
            if d.code == "sheet-empty-defaulted"
        ]
        self.assertEqual([d.subject for d in infos], ["Beta"])
        # The root sheet never becomes a station.
        self.assertNotIn("", lines)

    def test_sheet_with_two_codelines_is_an_error(self):
        duplicate = CODELINE_BLOCK.replace("CODELINE1", "CODELINE9")
        fragment = compile_minimal(
            mutate=lambda t: t.replace(
                CODELINE_BLOCK, CODELINE_BLOCK + duplicate
            )
        )
        self.assertIn(
            "sheet-codeline-count", [d.code for d in errors(fragment)]
        )


class SymbolAndCodelineDiagnosticTests(unittest.TestCase):
    """Seam 2: §7 codeline validation, lamp tokens, Role/Kind checks."""

    def test_unknown_codeline_transport_is_an_error(self):
        fragment = compile_minimal(
            mutate=lambda t: t.replace('(value "VIRTUAL")', '(value "FOO")')
        )
        self.assertIn(
            "codeline-unknown-transport", [d.code for d in errors(fragment)]
        )

    def test_cmrinet_station_must_be_a_ua(self):
        def mutate(text):
            return text.replace('(value "VIRTUAL")', '(value "CMRInet")')

        fragment = compile_minimal(mutate=mutate)  # Station stays "Alpha"
        self.assertIn(
            "codeline-bad-station", [d.code for d in errors(fragment)]
        )

        def mutate_valid(text):
            text = text.replace('(value "VIRTUAL")', '(value "CMRInet")')
            return text.replace(
                '(field (name "Station") "Alpha")',
                '(field (name "Station") "42")',
            )

        fragment = compile_minimal(mutate=mutate_valid)
        self.assertNotIn(
            "codeline-bad-station", [d.code for d in errors(fragment)]
        )

    def test_mqtt_station_rejects_topic_metacharacters(self):
        def mutate(text):
            text = text.replace('(value "VIRTUAL")', '(value "MQTT")')
            return text.replace(
                '(field (name "Station") "Alpha")',
                '(field (name "Station") "Al/pha")',
            )

        fragment = compile_minimal(mutate=mutate)
        self.assertIn(
            "codeline-bad-station", [d.code for d in errors(fragment)]
        )

    def test_lamp_with_no_indication_tokens_is_an_error(self):
        fragment = compile_minimal(
            mutate=lambda t: t.replace(
                '(field (name "IndicationToken") "10T1")',
                '(field (name "IndicationToken") "")',
            )
        )
        found = [d for d in errors(fragment) if d.code == "lamp-no-tokens"]
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].subject, "LAMP1")

    def test_component_without_role_is_an_error(self):
        fragment = compile_minimal(
            mutate=lambda t: t.replace(
                '        (field (name "Role") "APPLIANCE")\n'
                '        (field (name "Kind") "SWITCH_LEVER"))',
                '        (field (name "Kind") "SWITCH_LEVER"))',
            )
        )
        found = [d for d in errors(fragment) if d.code == "missing-role"]
        self.assertEqual([d.subject for d in found], ["SW1"])

    def test_unknown_kind_is_an_error(self):
        fragment = compile_minimal(
            mutate=lambda t: t.replace(
                '(field (name "Kind") "SWITCH_LEVER")',
                '(field (name "Kind") "FROB")',
            )
        )
        self.assertIn("unknown-kind", [d.code for d in errors(fragment)])


class ReviewFixCompilerTests(unittest.TestCase):
    """Fixes from the 2026-09-29 branch review: bad input must become a
    diagnostic, never a crash or a silent wrong answer."""

    def test_non_numeric_column_value_is_a_diagnostic_not_a_crash(self):
        fragment = compile_minimal(
            mutate=lambda t: t.replace('(value "1")', '(value "COLUMN")')
        )
        codes = [d.code for d in errors(fragment)]
        self.assertIn("column-number-invalid", codes)

    def test_non_numeric_machine_columns_is_a_diagnostic(self):
        fragment = compile_minimal(
            mutate=lambda t: t.replace(
                '(field (name "Columns") "2")',
                '(field (name "Columns") "fourteen")',
            )
        )
        codes = [d.code for d in errors(fragment)]
        self.assertIn("machine-columns-invalid", codes)
        self.assertEqual(fragment.machine.columns, 0)

    def test_duplicate_column_numbers_is_an_error(self):
        duplicate_col = (
            '    (comp (ref "COL9")\n'
            '      (value "1")\n'
            "      (fields\n"
            '        (field (name "Role") "COLUMN")\n'
            '        (field (name "CP Name") "CP Gamma"))\n'
            '      (libsource (lib "RailroadPanel") (part "PanelColumn"))\n'
            '      (sheetpath (names "/Alpha/") (tstamps "/aaaa/")))\n'
        )
        fragment = compile_minimal(
            mutate=lambda t: t.replace(
                '    (comp (ref "U1")', duplicate_col + '    (comp (ref "U1")'
            )
        )
        codes = [d.code for d in errors(fragment)]
        self.assertIn("column-number-duplicate", codes)

    def test_codeline_on_root_sheet_is_an_error(self):
        fragment = compile_minimal(
            mutate=lambda t: t.replace(
                '(part "Codeline-Virtual"))\n'
                '      (sheetpath (names "/Alpha/")',
                '(part "Codeline-Virtual"))\n'
                '      (sheetpath (names "/")',
            )
        )
        found = [d for d in errors(fragment) if d.code == "root-sheet-symbol"]
        self.assertEqual([d.subject for d in found], ["CODELINE1"])

    def test_two_function_pins_on_one_driver_bit_is_an_error(self):
        # Rewire the lamp onto the CODE button's bit 12.
        fragment = compile_minimal(
            mutate=lambda t: t.replace(
                '(node (ref "U1") (pin "4") (pinfunction "bit3_4")'
                ' (pintype "output"))',
                '(node (ref "U1") (pin "13") (pinfunction "bit12_13")'
                ' (pintype "output"))',
            )
        )
        found = [d for d in errors(fragment) if d.code == "driver-bit-shared"]
        self.assertEqual(len(found), 1)
        self.assertIn("bit 12", found[0].message)

    def test_net_with_two_driver_bits_is_an_error(self):
        extra = (
            '      (node (ref "U1") (pin "6") (pinfunction "bit5_6")'
            ' (pintype "output"))\n'
        )
        anchor = (
            '      (node (ref "U1") (pin "8") (pinfunction "bit7_8")'
            ' (pintype "input")))\n'
        )
        fragment = compile_minimal(
            mutate=lambda t: t.replace(
                anchor,
                extra + anchor,
            )
        )
        codes = [d.code for d in errors(fragment)]
        self.assertIn("net-multiple-driver-bits", codes)

    def test_machine_count_must_be_one(self):
        machine_block = (
            '    (comp (ref "MACHINE1")\n'
            '      (value "Test Machine")\n'
            "      (fields\n"
            '        (field (name "Role") "MACHINE")\n'
            '        (field (name "Type") "US&S506")\n'
            '        (field (name "Columns") "2"))\n'
            '      (libsource (lib "RailroadPanel") (part "CtcMachine"))\n'
            '      (sheetpath (names "/") (tstamps "/")))\n'
        )
        fragment = compile_minimal(
            mutate=lambda t: t.replace(machine_block, "")
        )
        codes = [d.code for d in errors(fragment)]
        self.assertIn("machine-count", codes)


class LinkerPairingTests(unittest.TestCase):
    """Seam 3: pairing by normalized name; unmatched sheets become
    placeholder stations, never fatal."""

    def test_luchessa_links_and_stubs_become_placeholders(self):
        model = link_subdivision(
            [compile_controller(read_golden())], [read_luchessa_plant()]
        )
        stations = {s.interlocking: s for s in model.stations}
        self.assertEqual(len(stations), 7)
        self.assertEqual(stations["Luchessa"].status, "linked")
        placeholders = [
            s.interlocking for s in model.stations if s.status == "placeholder"
        ]
        self.assertEqual(len(placeholders), 6)
        self.assertIn("Gilroy CalTrain", placeholders)
        # A placeholder is a recorded state, not an error.
        self.assertEqual(
            [d for d in model.diagnostics if d.severity == "error"], []
        )

    def test_plant_with_no_controller_sheet_is_info(self):
        plant = read_luchessa_plant()
        controller = compile_controller(read_golden())
        pruned = type(controller)(
            machine=controller.machine,
            columns=[],
            appliances=[],
            bindings=[],
            codelines=[c for c in controller.codelines if c.stub],
        )
        model = link_subdivision([pruned], [plant])
        infos = [
            d
            for d in model.diagnostics
            if d.severity == "info" and d.code == "plant-unattached"
        ]
        self.assertEqual([d.subject for d in infos], ["Luchessa"])


class LinkerCpCrossCheckTests(unittest.TestCase):
    """Seam 3: §7a — a column IS a CP; identity must hold across repos."""

    def link_golden(self, plant=None, controller=None):
        return link_subdivision(
            [controller or compile_controller(read_golden())],
            [plant if plant is not None else read_luchessa_plant()],
        )

    def test_luchessa_columns_match_plant_cps_cleanly(self):
        model = self.link_golden()
        cp_findings = [
            d for d in model.diagnostics if d.code.startswith("cp-")
        ]
        self.assertEqual(cp_findings, [])

    def test_column_naming_unknown_cp_is_an_error(self):
        plant = read_luchessa_plant()
        plant["appliances"]["controlledPoints"] = [
            cp
            for cp in plant["appliances"]["controlledPoints"]
            if cp["id"] != "CP Carnadero"
        ]
        model = self.link_golden(plant=plant)
        found = [d for d in model.diagnostics if d.code == "cp-unmatched"]
        self.assertEqual(len(found), 1)
        self.assertIn("CP Carnadero", found[0].message)

    def test_two_columns_naming_same_cp_is_an_error(self):
        from dataclasses import replace

        controller = compile_controller(read_golden())
        controller.columns = [
            replace(c, cp_name="CP Luchessa") if c.number == 6 else c
            for c in controller.columns
        ]
        model = self.link_golden(controller=controller)
        found = [d for d in model.diagnostics if d.code == "cp-duplicate"]
        self.assertEqual(len(found), 1)

    def test_plant_cp_without_column_is_a_warning(self):
        plant = read_luchessa_plant()
        plant["appliances"]["controlledPoints"].append(
            {"id": "CP Extra", "members": []}
        )
        model = self.link_golden(plant=plant)
        found = [d for d in model.diagnostics if d.code == "cp-uncontrolled"]
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].severity, "warning")


class LinkerApplianceCrossCheckTests(unittest.TestCase):
    """Seam 3: §7a — panel appliances vs plant appliances and circuits."""

    def link_golden(self, controller=None):
        return link_subdivision(
            [controller or compile_controller(read_golden())],
            [read_luchessa_plant()],
        )

    def test_golden_luchessa_cross_checks_clean(self):
        model = self.link_golden()
        self.assertEqual(
            [d for d in model.diagnostics if d.severity == "error"], []
        )
        infos = {d.code: d for d in model.diagnostics if d.severity == "info"}
        # Prototype check 2026-09-28: circuits nothing lamps.
        unlamped = [
            d.subject
            for d in model.diagnostics
            if d.code == "circuit-unlamped"
        ]
        self.assertEqual(sorted(unlamped), ["1SAT", "2NAT", "2SAT", "3NAT"])
        # Known gap: maintainer calls are not in the plant model yet, so
        # MC1S/MC1K are reported uncheckable, not silently accepted.
        self.assertIn("mcall-uncheckable", infos)

    def test_panel_lever_naming_no_plant_appliance_is_an_error(self):
        from dataclasses import replace

        controller = compile_controller(read_golden())
        controller.appliances = [
            replace(a, name="801")
            if a.kind == "SWITCH_LEVER" and a.name == "799"
            else a
            for a in controller.appliances
        ]
        model = self.link_golden(controller=controller)
        codes = [d.code for d in model.diagnostics if d.severity == "error"]
        self.assertIn("appliance-unmatched", codes)

    def test_plant_switch_without_lever_is_an_error(self):
        controller = compile_controller(read_golden())
        controller.appliances = [
            a
            for a in controller.appliances
            if not (a.kind == "SWITCH_LEVER" and a.name == "799")
        ]
        model = self.link_golden(controller=controller)
        found = [
            d for d in model.diagnostics if d.code == "plant-unlevered"
        ]
        self.assertEqual([d.subject for d in found], ["799"])

    def test_dependent_derail_needs_no_lever(self):
        model = self.link_golden()
        self.assertNotIn(
            "795D",
            [
                d.subject
                for d in model.diagnostics
                if d.code == "plant-unlevered"
            ],
        )

    def test_unresolvable_lamp_token_is_an_error(self):
        from dataclasses import replace

        controller = compile_controller(read_golden())
        controller.appliances = [
            replace(a, indication_tokens=("999T9",))
            if a.indication_tokens == ("1NAT",)
            else a
            for a in controller.appliances
        ]
        model = self.link_golden(controller=controller)
        found = [
            d for d in model.diagnostics if d.code == "lamp-token-unresolved"
        ]
        self.assertEqual(len(found), 1)
        self.assertIn("999T9", found[0].message)


def stub_fragment(machine_name, codelines):
    return ControllerFragment(
        machine=Machine(name=machine_name, machine_type="US&S506", columns=14),
        codelines=codelines,
    )


class CodelineInstanceTests(unittest.TestCase):
    """Seam 3: instances derive from type + Broker (MQTT) or Port (C/MRI)."""

    def test_virtual_stations_share_one_instance(self):
        model = link_subdivision(
            [compile_controller(read_golden())], [read_luchessa_plant()]
        )
        self.assertEqual(len(model.instances), 1)
        instance = model.instances[0]
        self.assertEqual(instance.transport, "VIRTUAL")
        self.assertEqual(len(instance.stations), 7)
        self.assertIn("Luchessa", instance.stations)

    def test_mqtt_instances_split_by_broker(self):
        fragment = stub_fragment(
            "M",
            [
                Codeline("A", "MQTT", "A", True, {"Broker": "brokerX"}),
                Codeline("B", "MQTT", "B", True, {"Broker": "brokerX"}),
                Codeline("C", "MQTT", "C", True, {"Broker": "brokerY"}),
            ],
        )
        model = link_subdivision([fragment], [])
        brokers = sorted(
            (i.discriminator, sorted(i.stations)) for i in model.instances
        )
        self.assertEqual(
            brokers, [("brokerX", ["A", "B"]), ("brokerY", ["C"])]
        )

    def test_duplicate_station_key_within_instance_is_an_error(self):
        fragment = stub_fragment(
            "M",
            [
                Codeline("Alpha", "VIRTUAL", "Big Sur", True),
                Codeline("Beta", "VIRTUAL", "BIGSUR", True),
            ],
        )
        model = link_subdivision([fragment], [])
        found = [
            d
            for d in model.diagnostics
            if d.code == "station-key-duplicate" and d.severity == "error"
        ]
        self.assertEqual(len(found), 1)

    def test_multiple_topicroots_on_one_broker_is_a_warning(self):
        fragment = stub_fragment(
            "M",
            [
                Codeline("A", "MQTT", "A", True, {"Broker": "b", "TopicRoot": "r1"}),
                Codeline("B", "MQTT", "B", True, {"Broker": "b", "TopicRoot": "r2"}),
            ],
        )
        model = link_subdivision([fragment], [])
        found = [
            d for d in model.diagnostics if d.code == "topicroot-mixed"
        ]
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].severity, "warning")

    def test_normalization_warning_accompanies_a_caused_collision(self):
        # "Big Sur" and "BIGSUR" collide only after normalization, so the
        # duplicate error carries a normalization warning for context.
        fragment = stub_fragment(
            "M",
            [
                Codeline("Alpha", "VIRTUAL", "Big Sur", True),
                Codeline("Beta", "VIRTUAL", "BIGSUR", True),
            ],
        )
        model = link_subdivision([fragment], [])
        warnings = [
            d
            for d in model.diagnostics
            if d.code == "station-key-normalized"
        ]
        self.assertEqual(len(warnings), 1)
        self.assertIn("Big Sur", warnings[0].message)

    def test_no_normalization_warning_without_a_finding(self):
        # Multi-word stations normalize routinely; that alone is not news.
        model = link_subdivision(
            [compile_controller(read_golden())], [read_luchessa_plant()]
        )
        self.assertEqual(
            [
                d
                for d in model.diagnostics
                if d.code == "station-key-normalized"
            ],
            [],
        )

    def test_no_normalization_warning_for_literal_duplicates(self):
        # Identical raw names are a plain duplicate; normalization played
        # no part in the collision.
        fragment = stub_fragment(
            "M",
            [
                Codeline("Alpha", "VIRTUAL", "Corporal", True),
                Codeline("Beta", "VIRTUAL", "Corporal", True),
            ],
        )
        model = link_subdivision([fragment], [])
        codes = [d.code for d in model.diagnostics]
        self.assertIn("station-key-duplicate", codes)
        self.assertNotIn("station-key-normalized", codes)

    def test_inconsistent_baud_on_one_port_is_an_error(self):
        fragment = stub_fragment(
            "M",
            [
                Codeline("A", "CMRInet", "1", True, {"Port": "p1", "Baud": "9600"}),
                Codeline("B", "CMRInet", "2", True, {"Port": "p1", "Baud": "19200"}),
            ],
        )
        model = link_subdivision([fragment], [])
        codes = [d.code for d in model.diagnostics if d.severity == "error"]
        self.assertIn("codeline-baud-mismatch", codes)


class ReviewFixLinkerTests(unittest.TestCase):
    """Fixes from the 2026-09-29 branch review: linker edge cases."""

    def test_lock_lever_is_uncheckable_info_not_a_false_error(self):
        from dataclasses import replace

        controller = compile_controller(read_golden())
        controller.appliances = [
            replace(a, kind="LOCK_LEVER")
            if a.kind == "SWITCH_LEVER" and a.name == "795"
            else a
            for a in controller.appliances
        ]
        model = link_subdivision([controller], [read_luchessa_plant()])
        codes = [d.code for d in model.diagnostics]
        self.assertNotIn("appliance-unmatched", codes)
        self.assertIn("lock-uncheckable", codes)
        # 795 lost its switch lever, and that is still reported.
        self.assertIn(
            "795",
            [
                d.subject
                for d in model.diagnostics
                if d.code == "plant-unlevered"
            ],
        )

    def test_baud_mismatch_reported_once_per_port(self):
        fragment = stub_fragment(
            "M",
            [
                Codeline("A", "CMRInet", "1", True, {"Port": "p1", "Baud": "9600"}),
                Codeline("B", "CMRInet", "2", True, {"Port": "p1", "Baud": "19200"}),
                Codeline("C", "CMRInet", "3", True, {"Port": "p1", "Baud": "9600"}),
                Codeline("D", "CMRInet", "4", True, {"Port": "p1", "Baud": "9600"}),
            ],
        )
        model = link_subdivision([fragment], [])
        found = [
            d for d in model.diagnostics if d.code == "codeline-baud-mismatch"
        ]
        self.assertEqual(len(found), 1)

    def test_topicroot_warning_reported_once_per_broker(self):
        fragment = stub_fragment(
            "M",
            [
                Codeline("A", "MQTT", "A", True, {"Broker": "b", "TopicRoot": "r1"}),
                Codeline("B", "MQTT", "B", True, {"Broker": "b", "TopicRoot": "r2"}),
                Codeline("C", "MQTT", "C", True, {"Broker": "b", "TopicRoot": "r2"}),
            ],
        )
        model = link_subdivision([fragment], [])
        found = [d for d in model.diagnostics if d.code == "topicroot-mixed"]
        self.assertEqual(len(found), 1)

    def test_mn_controllers_share_a_station_without_false_duplicate(self):
        # Design doc: Controller M:N CodeLine. Two machines controlling the
        # same interlocking on one codeline instance is a legal topology.
        desk = stub_fragment(
            "Dispatcher",
            [Codeline("Luchessa", "MQTT", "Luchessa", True, {"Broker": "b"})],
        )
        tower = stub_fragment(
            "Tower",
            [Codeline("Luchessa", "MQTT", "Luchessa", True, {"Broker": "b"})],
        )
        model = link_subdivision([desk, tower], [])
        codes = [d.code for d in model.diagnostics if d.severity == "error"]
        self.assertNotIn("station-key-duplicate", codes)
        self.assertIn(
            "station-mn-attached",
            [d.code for d in model.diagnostics],
        )
        instance = model.instances[0]
        self.assertEqual(instance.stations, ["Luchessa"])

    def test_cp_name_matching_folds_case_only(self):
        from dataclasses import replace

        # Case-only difference matches...
        controller = compile_controller(read_golden())
        controller.columns = [
            replace(c, cp_name="cp luchessa") if c.number == 5 else c
            for c in controller.columns
        ]
        model = link_subdivision([controller], [read_luchessa_plant()])
        self.assertNotIn(
            "cp-unmatched", [d.code for d in model.diagnostics]
        )
        # ...but whitespace is part of the name (AGENTS.md: only case is
        # folded, so 'Luchessa' and 'CP Luchessa' stay distinct).
        controller = compile_controller(read_golden())
        controller.columns = [
            replace(c, cp_name="CPLuchessa") if c.number == 5 else c
            for c in controller.columns
        ]
        model = link_subdivision([controller], [read_luchessa_plant()])
        self.assertIn("cp-unmatched", [d.code for d in model.diagnostics])


class ModelJsonTests(unittest.TestCase):
    """Seam 3: the linked model serializes to the JSON generators read,
    recording the sources it was built from."""

    def test_subdivision_model_serializes_with_sources(self):
        from link.model import subdivision_to_json

        model = link_subdivision(
            [compile_controller(read_golden())], [read_luchessa_plant()]
        )
        doc = subdivision_to_json(model)
        json.dumps(doc)  # must be plain JSON data
        stations = {s["interlocking"]: s for s in doc["stations"]}
        self.assertEqual(stations["Luchessa"]["status"], "linked")
        self.assertEqual(stations["Luchessa"]["stationKey"], "luchessa")
        self.assertEqual(
            doc["controllers"][0]["machine"]["name"], "SPCoast South"
        )
        kinds = {s["kind"] for s in doc["sources"]}
        self.assertEqual(kinds, {"controller-netlist", "plant-model"})
        for source in doc["sources"]:
            self.assertEqual(len(source["sha256"]), 64)
        controller_src = next(
            s for s in doc["sources"] if s["kind"] == "controller-netlist"
        )
        self.assertTrue(controller_src["path"].endswith("South-cTc.net"))


class CliSmokeTests(unittest.TestCase):
    """CLI front ends stay thin; one smoke test each."""

    def run_cli(self, *argv):
        import subprocess

        return subprocess.run(
            [sys.executable, *argv],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )

    def test_parse_kicad_controller_cli(self):
        result = self.run_cli(
            "tools/parse_kicad_controller.py",
            "--netlist",
            str(FIXTURES / "South-cTc.net"),
            "--format",
            "json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        doc = json.loads(result.stdout)
        self.assertEqual(doc["machine"]["name"], "SPCoast South")
        self.assertEqual(len(doc["codelines"]), 7)

    def test_link_subdivision_cli(self):
        result = self.run_cli(
            "tools/link_subdivision.py",
            "--controller",
            str(FIXTURES / "South-cTc.net"),
            "--plant",
            str(FIXTURES / "Luchessa.plant-model.json"),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        doc = json.loads(result.stdout)
        stations = {s["interlocking"]: s for s in doc["stations"]}
        self.assertEqual(stations["Luchessa"]["status"], "linked")


if __name__ == "__main__":
    unittest.main()
