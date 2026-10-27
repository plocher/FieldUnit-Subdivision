"""Gates for the milestone D KiCad importer (ADR 0009 §3.12, ADR 0008 rev 4, ADR 0011, ADR 0012 §4).

Two kinds. The rules are tested on small sources built in memory: a relation by its wire alone (the fallbacks of
ADR 0012 §4 retired), the three maps, the macro. What the reference derivation computes is tested in
``test_derive``. The relation table is tested on the SPCoast
project when it is present (``SPCOAST_PROJECT``, default ``~/Dropbox/KiCad/Railroad/SPCoast/SPCoast.kicad_sch``)
and kicad-cli can export its netlist fresh (the netlist rule, ``AGENTS.md``). ``SPCOAST_NETLIST`` names a saved netlist
instead, on a machine where kicad-cli cannot run; it is read only when it is still a snapshot of the Railroad
repository (``RAILROAD_REPO``, default ``~/Dropbox/KiCad/Railroad``: no uncommitted change under ``SPCoast/`` and
``symbols/``, no commit there newer than the file), and a stale one fails the gates loudly with what is stale. The
gates are skipped, never faked, when neither is at hand.
"""
from __future__ import annotations

import os
import unittest
from pathlib import Path

from tools import layout_model
from tools.layout_compiler import emit, seams
from tools.layout_compiler.source import Net, PinRef, Symbol, from_project, from_snapshot, from_symbols, kicad_cli_available

PROJECT = Path(os.environ.get("SPCOAST_PROJECT", Path.home() / "Dropbox/KiCad/Railroad/SPCoast/SPCoast.kicad_sch"))
NETLIST = Path(os.environ["SPCOAST_NETLIST"]) if os.environ.get("SPCOAST_NETLIST") else None
RAILROAD = Path(os.environ.get("RAILROAD_REPO", Path.home() / "Dropbox/KiCad/Railroad"))
SNAPSHOT_PATHS = ("SPCoast", "symbols")                    # what the SPCoast drawing is made of, in the Railroad repository


def spcoast_source():
    """The SPCoast drawing, exported fresh; a saved netlist only when the caller named one and it is still a snapshot
    (a stale one raises ``StaleNetlist``, so the gate fails loudly); None when neither is at hand."""
    if NETLIST is not None:
        return from_snapshot(NETLIST, RAILROAD, SNAPSHOT_PATHS) if NETLIST.is_file() else None
    if PROJECT.is_file() and kicad_cli_available():
        return from_project(PROJECT)
    return None


SPCOAST_AVAILABLE = (NETLIST is not None and NETLIST.is_file()) or (PROJECT.is_file() and kicad_cli_available())


def sym(ref, lib, sheet, value="", **fields):
    return Symbol(ref, f"Railroad-Office:{lib}", value, {k.replace("_", " ") if k == "CP_Name" else k: v for k, v in fields.items()}, sheet)


def net(name, *pins):
    return Net(name, tuple(PinRef(r, p) for r, p in pins))


def plant(wire_processor=True, two_processors=False, field_processor=None):
    """One interlocking on one sheet with one processor; optionally a second processor and a Processor field."""
    syms = [
        sym("RR1", "Railroad", "/", "SPCoast", Role="STRUCTURE", Kind="RAILROAD", Name="SPCoast"),
        sym("P1", "Processor", "/X/", "Alpha", Role="STRUCTURE", Kind="PROCESSOR", Name="Alpha", Board="cpNode"),
        sym("IX1", "Interlocking", "/X/", "X", Role="STRUCTURE", Kind="INTERLOCKING", Name="X", **({"Processor": field_processor} if field_processor else {})),
    ]
    if two_processors:
        syms.append(sym("P2", "Processor", "/X/", "Beta", Role="STRUCTURE", Kind="PROCESSOR", Name="Beta", Board="cpNode"))
    nets = [net("n1", ("IX1", "Processor"), ("P1", "Processor"))] if wire_processor else []
    return from_symbols(syms, nets)


def jmri_plant():
    """plant() plus MQTT wired to Alpha, the JMRI encoding wired to it, a switch 777 with a JMRI Turnout (command and
    feedback symbols) and a Mast 784EAB with a JMRI SignalMast, the drivers wired to Alpha's bus."""
    src = plant()
    for s in [
        sym("T1", "Transport-MQTT", "/X/", "MQTT", Role="TRANSPORT", Kind="MQTT", Name="MQTT"),
        sym("E1", "Encoding-JMRI", "/X/", "JMRI", Role="IO_ENCODING", Kind="JMRI", Name="JMRI"),
        sym("D1", "Device-Switch", "/X/", "777", Role="DEVICE", Appliance="switch", Name="777"),
        sym("M1", "Mast", "/X/", "784EAB", Role="DEVICE", Appliance="mast", Name="784EAB"),
        sym("J1", "Driver-JMRI-Turnout", "/X/", "", Role="IODRIVER", IC="MQTT-JMRI", Kind="TURNOUT", Address=""),
        sym("J2", "Driver-JMRI-Turnout-Feedback", "/X/", "", Role="IODRIVER", IC="MQTT-JMRI", Kind="TURNOUT", Address=""),
        sym("J3", "Driver-JMRI-SignalMast", "/X/", "", Role="IODRIVER", IC="MQTT-JMRI", Kind="SIGNALMAST", Address=""),
    ]:
        src.symbols[s.ref] = s
    nets = [net("m", ("D1", "M"), ("J1", "M")), net("n", ("D1", "~{N}"), ("J2", "~{N}")), net("r", ("D1", "~{R}"), ("J2", "~{R}")),
            net("i", ("M1", "IND"), ("J3", "IND")), net("t", ("E1", "Transport"), ("T1", "Transport")),
            net("bus", ("P1", "IOBus"), ("J1", "IOBus"), ("J2", "IOBus"), ("J3", "IOBus"))]
    processor = [net("n1", ("IX1", "Processor"), ("P1", "Processor"), ("T1", "Processor"))]
    return from_symbols(list(src.symbols.values()), processor + nets)


class RuleTests(unittest.TestCase):
    def test_the_wire_states_the_processor(self):
        sm = seams.resolve(plant())
        self.assertEqual(sm.interlockings["X"].processor, "Alpha")
        self.assertEqual(sm.report.errors, [])
        self.assertEqual([d.severity for d in sm.report.diags if d.code.startswith("unit.processor")], [])

    def test_the_wire_decides_when_two_processors_share_the_sheet(self):
        sm = seams.resolve(plant(two_processors=True))
        self.assertEqual(sm.interlockings["X"].processor, "Alpha")
        self.assertFalse(sm.report.by_code("unit.processor.missing"))

    def test_no_wire_is_missing_even_with_one_processor_on_the_sheet(self):
        """ADR 0012 §4: "the one Processor on the sheet" retired; without its wire the relation is missing, not guessed."""
        for two in (False, True):
            sm = seams.resolve(plant(wire_processor=False, two_processors=two))
            self.assertIsNone(sm.interlockings["X"].processor)
            self.assertEqual([d.severity for d in sm.report.by_code("unit.processor.missing")], ["missing"])
            self.assertNotIn("relations", emit.emit(sm)["interlockings"]["X"])

    def test_a_processor_field_is_given_and_read_by_nothing(self):
        """A transport wired to Alpha whose Processor field says Beta: the field is no longer a second form (ADR 0012
        §4); it stays in given as drawn, and the anchor is the wire's."""
        src = plant(two_processors=True)
        src.symbols["T1"] = sym("T1", "Transport-MQTT", "/X/", "MQTT", Role="TRANSPORT", Kind="MQTT", Name="MQTT", Processor="Beta")
        src.nets.append(net("n2", ("T1", "Processor"), ("P2", "Processor")))
        sm = seams.resolve(from_symbols(src.symbols.values(), src.nets))
        self.assertEqual(sm.report.errors, [])
        t = emit.emit(sm)["layout"]["transports"]["MQTT"]
        self.assertEqual(t, {"given": {"Kind": "MQTT", "Processor": "Beta"}, "relations": {"anchors": ["Beta"]}})

    def test_given_is_every_stated_field_less_housekeeping_the_key_and_empty_fields(self):
        """ADR 0011 §2 and the table's D1, D2, D21: Role, KiCad's housekeeping, Pin.*, the key field and an empty or ~ field
        are not stated; every other field is, whether or not any reader consumes it."""
        drawn = sym("T1", "Transport-MQTT", "/X/", "MQTT", Role="TRANSPORT", Kind="MQTT", Name="MQTT", Broker="10.0.0.1:1883",
                    Reference="T1", Value="MQTT", Footprint="", Datasheet="~", Description="A broker", Sheetname="X",
                    Sheetfile="x.kicad_sch", ki_keywords="mqtt", **{"Pin.Processor": "IN", "Retain": "yes", "Spare": " "})
        self.assertEqual(seams.given_of(drawn), {"Kind": "MQTT", "Broker": "10.0.0.1:1883", "Retain": "yes"})
        self.assertEqual(seams.given_of(drawn, keyed=False)["Name"], "MQTT")      # a row without identity keeps its Name
        house = sym("H1", "House", "/X/", "", Role="STRUCTURE", Kind="CONTROL_POINT", CP_Name="East", Milepost="81.3")
        self.assertEqual(seams.given_of(house), {"Kind": "CONTROL_POINT", "Milepost": "81.3"})
        driver = sym("U1", "MCP23017", "/X/", "", Role="IODRIVER", IC="MCP23017", Address="0x20", frequency_hz="50")
        self.assertEqual(seams.given_of(driver), {"IC": "MCP23017", "frequency_hz": "50"})   # Address is its key (D11)

    def test_one_entity_placed_twice_states_one_given(self):
        src = plant()
        src.symbols["T1"] = sym("T1", "Transport-MQTT", "/X/", "MQTT", Role="TRANSPORT", Kind="MQTT", Name="MQTT", Broker="a")
        src.symbols["T2"] = sym("T2", "Transport-MQTT", "/", "MQTT", Role="TRANSPORT", Kind="MQTT", Name="MQTT", Broker="b")
        sm = seams.resolve(from_symbols(src.symbols.values(), src.nets))
        self.assertEqual([d.code for d in sm.report.errors], ["entity.conflict"])

    def test_macro_expands_in_scope(self):
        src = plant()
        src.symbols["E1"] = sym("E1", "Encoding-AAR", "/", "AAR", Role="CODELINE_ENCODING", Kind="AAR", Name="AAR", Topic="ctc/<STRUCTURE:RAILROAD:Name>/codeline/")
        sm = seams.resolve(src)
        self.assertEqual(sm.encodings["AAR"].given["Topic"], "ctc/SPCoast/codeline/")

    def test_macro_with_two_in_scope_is_an_error(self):
        src = plant()
        src.symbols["RR2"] = sym("RR2", "Railroad", "/", "Other", Role="STRUCTURE", Kind="RAILROAD", Name="Other")
        src.symbols["E1"] = sym("E1", "Encoding-AAR", "/", "AAR", Role="CODELINE_ENCODING", Kind="AAR", Name="AAR", Topic="ctc/<STRUCTURE:RAILROAD:Name>/codeline/")
        sm = seams.resolve(src)
        self.assertTrue(sm.report.by_code("macro.scope"))
        self.assertTrue(all(d.severity == "error" for d in sm.report.by_code("macro.scope")))

    def test_macro_names_a_missing_field(self):
        src = plant()
        src.symbols["E1"] = sym("E1", "Encoding-AAR", "/", "AAR", Role="CODELINE_ENCODING", Kind="AAR", Name="AAR", Topic="<STRUCTURE:RAILROAD:Nope>")
        sm = seams.resolve(src)
        self.assertTrue(sm.report.by_code("macro.field"))

    def test_a_symbol_without_name_is_unnamed_never_its_value(self):
        """The owner (2026-10-25): the Value fallback is gone; a symbol without its key is reported and not written."""
        src = plant()
        src.symbols["OU1"] = sym("OU1", "OfficeUnit", "/", "Desk", Role="OFFICE_UNIT", Style="US&S")
        sm = seams.resolve(src)
        self.assertEqual(sm.office_units, {})
        self.assertTrue(sm.report.by_code("identity.name"))
        self.assertTrue(sm.report.by_code("entity.name"))

    def test_jmri_driver_is_keyed_by_kind_and_served_device(self):
        """ADR 0005 S4, R11 and the owner (2026-10-24): an encoded driver carries no address; its key is Kind.name of the
        device it serves; a Turnout's command and feedback symbols are one driver; a Mast is a row with its IND binding."""
        sm = seams.resolve(jmri_plant())
        self.assertEqual(sm.report.errors, [])
        drivers = sm.processors["Alpha"].drivers
        self.assertEqual(set(drivers), {"TURNOUT.777", "SIGNALMAST.784EAB"})
        self.assertEqual((drivers["TURNOUT.777"].kind, len(drivers["TURNOUT.777"].syms)), ("TURNOUT", 2))
        model = emit.emit(sm)
        rows = {d["derived"]["serves"]: d for d in model["interlockings"]["X"]["devices"]}
        self.assertEqual(rows["X:777"]["relations"], {"bindings": {"M": "Alpha/TURNOUT.777/M", "N": "Alpha/TURNOUT.777/N", "R": "Alpha/TURNOUT.777/R"}})
        self.assertEqual((rows["X:784EAB"]["given"], rows["X:784EAB"]["relations"]),
                         ({"Appliance": "mast", "Name": "784EAB"}, {"bindings": {"IND": "Alpha/SIGNALMAST.784EAB/IND"}}))
        self.assertFalse(sm.report.by_code("driver.address"))
        self.assertFalse(sm.report.by_code("identity.name"))
        self.assertEqual(model["layout"]["processors"]["Alpha"]["drivers"]["TURNOUT.777"], {"given": {"IC": "MQTT-JMRI", "Kind": "TURNOUT"}})
        self.assertEqual(model["layout"]["ioEncodings"]["JMRI"], {"given": {"Kind": "JMRI"}, "relations": {"transport": "MQTT", "processor": "Alpha"}})
        self.assertEqual(layout_model.errors(model), [])

    def test_a_driver_on_no_bus_is_missing_not_the_one_processor_on_the_sheet(self):
        """ADR 0012 §4: a driver's bus is its IOBus wire alone."""
        src = jmri_plant()
        sm = seams.resolve(from_symbols(src.symbols.values(), [n for n in src.nets if n.name != "bus"]))
        self.assertEqual(sm.processors["Alpha"].drivers, {})
        self.assertEqual(len(sm.report.by_code("driver.bus.missing")), 3)

    def test_a_drawn_address_overrides_the_derived_jmri_key(self):
        src = jmri_plant()
        s = src.symbols["J1"]
        src.symbols["J1"] = Symbol(s.ref, s.lib_id, s.value, {**s.fields, "Address": "MT777"}, s.sheet)
        sm = seams.resolve(src)
        self.assertEqual(set(sm.processors["Alpha"].drivers), {"MT777", "TURNOUT.777", "SIGNALMAST.784EAB"})   # the feedback symbol still derives its key
        self.assertTrue(sm.report.by_code("driver.address.override"))
        self.assertEqual(sm.report.errors, [])
        self.assertEqual(sm.processors["Alpha"].drivers["MT777"].given["Address"], "MT777")   # an override is stated, not a key field

    def test_an_encoded_driver_without_kind_has_no_key(self):
        src = jmri_plant()
        s = src.symbols["J1"]
        src.symbols["J1"] = Symbol(s.ref, s.lib_id, s.value, {k: v for k, v in s.fields.items() if k != "Kind"}, s.sheet)
        sm = seams.resolve(src)
        self.assertTrue(sm.report.by_code("driver.kind"))
        self.assertEqual([x.ref for d in sm.processors["Alpha"].drivers.values() for x in d.syms], ["J2", "J3"])


    def test_emitted_model_validates(self):
        sm = seams.resolve(plant())
        model = emit.emit(sm)
        self.assertEqual(layout_model.errors(model), [])
        self.assertEqual(layout_model.dumps(layout_model.loads(layout_model.dumps(model))), layout_model.dumps(model))


@unittest.skipUnless(SPCOAST_AVAILABLE, f"SPCoast project not present or kicad-cli missing: {NETLIST or PROJECT}")
class SPCoastRelationTable(unittest.TestCase):
    """ADR 0009 §3.12 under ADR 0012 §4: every relation of the table is stated by its wire; no fallback remains."""

    @classmethod
    def setUpClass(cls):
        cls.sm = seams.resolve(spcoast_source())
        cls.model = emit.emit(cls.sm)

    def test_every_relation_is_wired(self):
        """ADR 0012 §4's evidence: SPCoast resolves every relation by wire, so retiring the fallbacks leaves none missing."""
        retired = ("unit.processor", "office.processor", "unit.codeline", "driver.bus", "transport.anchor", "encoding.transport", "node.transport")
        self.assertEqual([str(d) for d in self.sm.report.diags if d.code.startswith(retired)], [])
        self.assertEqual([str(d) for d in self.sm.report.diags if d.code.endswith((".disagree", ".explicit_only", ".implicit_only"))], [])

    def test_units_on_their_lines(self):
        lines = {n: ix.codeline for n, ix in self.sm.interlockings.items()}
        self.assertEqual(lines["Luchessa"], "US&S 506")
        self.assertEqual({v for k, v in lines.items() if k != "Luchessa"}, {"AAR Tokens"})

    def test_units_run_on_their_processors(self):
        procs = {n: ix.processor for n, ix in self.sm.interlockings.items()}
        self.assertEqual(procs["Gilroy Caltrain"], "SPCoastApp")
        self.assertEqual(procs["Gilroy Interchange"], "Gilroy")
        for n in ("Christopher", "Corporal", "Luchessa", "Sargent", "Watsonville"):
            self.assertEqual(procs[n], n)

    def test_transports_anchored_once_per_connecting_processor(self):
        t = self.sm.transports
        self.assertEqual(t["MQTT"].anchors, {"JohnCTC", "Gilroy"})
        self.assertEqual(t["CMRInet"].anchors, {"SPCoastApp"})
        self.assertEqual(t["TimeCode"].anchors, {"JohnCTC"})

    def test_encodings_ride_their_instances(self):
        e = self.sm.encodings
        self.assertEqual((e["AAR Tokens"].transport, e["AAR Tokens"].processor), ("MQTT", "JohnCTC"))
        self.assertEqual((e["JMRI"].transport, e["JMRI"].processor), ("MQTT", "Gilroy"))
        self.assertEqual((e["US&S 506"].transport, e["US&S 506"].processor), ("TimeCode", "JohnCTC"))
        self.assertEqual((e["CMRInet"].transport, e["CMRInet"].processor), ("CMRInet", "SPCoastApp"))
        self.assertEqual(e["AAR Tokens"].given["Topic"], "ctc/SPCoast/codeline/")
        self.assertEqual(self.model["layout"]["codelines"]["AAR Tokens"]["relations"], {"transport": "MQTT", "processor": "JohnCTC"})

    def test_cmrinet_node_and_its_bits(self):
        node = self.sm.transports["CMRInet"].nodes["30"]
        self.assertEqual((node.given["NodeType"], node.input_bytes, node.output_bytes), ("C", 2, 3))
        self.assertEqual(self.model["layout"]["transports"]["CMRInet"]["nodes"]["30"]["given"],
                         {"IC": "CMRI", "NodeType": "C", "InputBytes": "2", "OutputBytes": "3"})
        self.assertEqual(sum(1 for a in node.bits if a.startswith("IB")), 14)
        self.assertEqual(sum(1 for a in node.bits if a.startswith("OB")), 20)
        self.assertEqual(self.sm.report.by_code("node.bytes"), [])

    def test_stations_derive_from_houses_and_columns(self):
        ou = self.sm.office_units["SPCoast South"]
        self.assertEqual(ou.processor, "JohnCTC")
        columns = self.model["officeUnits"]["SPCoast South"]["columns"]
        self.assertEqual({n: c["derived"]["house"] for n, c in columns.items() if "derived" in c},
                         {"5": "Luchessa:Luchessa", "6": "Luchessa:Gilroy", "7": "Luchessa:Carnadero"})
        self.assertEqual(len(self.sm.report.by_code("column.cp_name")), 11)
        self.assertEqual(columns["5"], {"given": {"CP Name": "Luchessa"}, "derived": {"house": "Luchessa:Luchessa", "interlocking": "Luchessa"}})

    def test_membership_stated_only_by_the_sheet_hierarchy_is_a_relation(self):
        """Three-maps D6: the 11 columns without a CP Name and the 34 board lamps carry relations.interlocking."""
        ou = self.model["officeUnits"]["SPCoast South"]
        self.assertEqual({n: c["relations"]["interlocking"] for n, c in ou["columns"].items() if "relations" in c},
                         {"1": "Gilroy Caltrain", "2": "Gilroy Caltrain", "3": "Gilroy Interchange", "4": "Gilroy Interchange",
                          "8": "Christopher", "9": "Christopher", "10": "Christopher", "11": "Corporal", "12": "Corporal",
                          "13": "Sargent", "14": "Watsonville"})
        board = [d for d in ou["devices"] if d["given"].get("Style") == "board"]
        self.assertEqual(len(board), 34)
        self.assertEqual([d for d in board if "interlocking" not in d.get("relations", {}) or "column" in d.get("relations", {})], [])

    def test_a_column_reference_is_qualified_by_its_office_unit(self):
        cols = {d["relations"]["column"] for d in self.model["officeUnits"]["SPCoast South"]["devices"] if "column" in d.get("relations", {})}
        self.assertEqual(cols, {f"SPCoast South:{n}" for n in range(1, 15)})

    def test_every_key_is_a_name_never_a_value(self):
        """The owner (2026-10-24): every symbol the compiler names carries Name = ${Value}; Value is never read."""
        self.assertEqual(self.sm.report.by_code("identity.name"), [])

    def test_jmri_drivers_keyed_by_object_and_device_and_masts_are_rows(self):
        gilroy = self.sm.processors["Gilroy"].drivers
        self.assertEqual({k for k in gilroy if "." in k},
                         {"TURNOUT.777", "TURNOUT.781", "SENSOR.777", "SENSOR.781", "SENSOR.01T", "SENSOR.02T", "SENSOR.1SAT", "SENSOR.1NAT",
                          "SIGNALMAST.778NC", "SIGNALMAST.778SC", "SIGNALMAST.778NAB", "SIGNALMAST.778SAB", "LIGHT.MC1", "LIGHT.MC2"})
        self.assertEqual(len(gilroy["TURNOUT.777"].syms), 2)
        self.assertEqual(self.sm.report.by_code("driver.address"), [])
        masts = [d for ix in self.model["interlockings"].values() for d in ix["devices"] if d["given"]["Appliance"] == "mast"]
        self.assertEqual(len(masts), 38)
        self.assertEqual([r for d in masts if d["derived"]["serves"] == "Gilroy Interchange:778NC" for r in d.get("relations", {}).get("bindings", {}).items()],
                         [("IND", "Gilroy/SIGNALMAST.778NC/IND")])

    def test_a_head_device_states_its_mast_and_serves_it(self):
        heads = [d for ix in self.model["interlockings"].values() for d in ix["devices"] if d["given"]["Appliance"] == "head"]
        self.assertEqual(len(heads), 47)
        self.assertEqual([d for d in heads if d["relations"].get("mast") != d["derived"].get("serves") or "Name" in d["given"]], [])

    def test_layout_facts_from_the_railroad_symbol(self):
        self.assertEqual({"name": self.model["layout"]["name"], "given": self.model["layout"]["given"]},
                         {"name": "SPCoast", "given": {"Kind": "RAILROAD", "Railroad": "Southern Pacific", "Region": "Coast Line", "Era": "1960+", "Rulebook": "GCOR"}})

    def test_model_validates_and_round_trips(self):
        model = self.model
        self.assertEqual(layout_model.errors(model), [])
        text = layout_model.dumps(model)
        self.assertEqual(layout_model.dumps(layout_model.loads(text)), text)

    def test_drawing_has_no_errors(self):
        """The KiCad importer writes no file while this fails."""
        self.assertEqual([str(d) for d in self.sm.report.errors], [])


if __name__ == "__main__":
    unittest.main()
