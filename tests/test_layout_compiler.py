"""Gates for the milestone D compiler (ADR 0009 §3.12, ADR 0008 rev 4).

Two kinds. The rules are tested on small sources built in memory: the explicit and implicit forms of a relation,
their disagreement, the macro, the scope rule, the head vocabulary. The relation table is tested on the SPCoast
project when it is present (``SPCOAST_PROJECT``, default ``~/Dropbox/KiCad/Railroad/SPCoast/SPCoast.kicad_sch``)
and kicad-cli can export its netlist fresh (the netlist rule, ``AGENTS.md``: a saved netlist is a cache and may be
stale; ``SPCOAST_NETLIST`` names one anyway on a machine without KiCad, and that caller answers for it). That gate
is the "both" copy of the three-copy experiment (ADR 0009 C7) and is skipped, never faked, when neither is at hand.
"""
from __future__ import annotations

import os
import unittest
from pathlib import Path

from tools import layout_model
from tools.layout_compiler import emit, seams
from tools.layout_compiler.source import Net, PinRef, Symbol, from_netlist, from_project, from_symbols, kicad_cli_available

PROJECT = Path(os.environ.get("SPCOAST_PROJECT", Path.home() / "Dropbox/KiCad/Railroad/SPCoast/SPCoast.kicad_sch"))
NETLIST = Path(os.environ["SPCOAST_NETLIST"]) if os.environ.get("SPCOAST_NETLIST") else None


def spcoast_source():
    """The SPCoast drawing, exported fresh; a saved netlist only when the caller named one; None when neither is at hand."""
    if NETLIST is not None:
        return from_netlist(NETLIST) if NETLIST.is_file() else None
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
    """plant() plus MQTT anchored on Alpha, the JMRI encoding on it, a switch 777 with a JMRI Turnout (command and feedback
    symbols) and a Mast 784EAB with a JMRI SignalMast; the drivers find Alpha as the one processor on the sheet."""
    src = plant()
    for s in [
        sym("T1", "Transport-MQTT", "/X/", "MQTT", Role="TRANSPORT", Kind="MQTT", Name="MQTT", Processor="Alpha"),
        sym("E1", "Encoding-JMRI", "/X/", "JMRI", Role="IO_ENCODING", Kind="JMRI", Name="JMRI", Transport="MQTT"),
        sym("D1", "Device-Switch", "/X/", "777", Role="DEVICE", Appliance="switch", Name="777"),
        sym("M1", "Mast", "/X/", "784EAB", Role="DEVICE", Appliance="mast", Name="784EAB"),
        sym("J1", "Driver-JMRI-Turnout", "/X/", "", Role="IODRIVER", IC="MQTT-JMRI", Kind="TURNOUT", Address=""),
        sym("J2", "Driver-JMRI-Turnout-Feedback", "/X/", "", Role="IODRIVER", IC="MQTT-JMRI", Kind="TURNOUT", Address=""),
        sym("J3", "Driver-JMRI-SignalMast", "/X/", "", Role="IODRIVER", IC="MQTT-JMRI", Kind="SIGNALMAST", Address=""),
    ]:
        src.symbols[s.ref] = s
    nets = [net("m", ("D1", "M"), ("J1", "M")), net("n", ("D1", "~{N}"), ("J2", "~{N}")), net("r", ("D1", "~{R}"), ("J2", "~{R}")),
            net("i", ("M1", "IND"), ("J3", "IND"))]
    return from_symbols(list(src.symbols.values()), list(src.nets) + nets)


class RuleTests(unittest.TestCase):
    def test_explicit_and_implicit_agree(self):
        sm = seams.resolve(plant())
        self.assertEqual(sm.interlockings["X"].processor, "Alpha")
        self.assertEqual(sm.report.errors, [])
        self.assertFalse(sm.report.by_code("unit.processor.explicit_only"))

    def test_wire_only_when_two_processors_share_the_sheet(self):
        sm = seams.resolve(plant(two_processors=True))
        self.assertEqual(sm.interlockings["X"].processor, "Alpha")
        self.assertTrue(sm.report.by_code("unit.processor.explicit_only"))

    def test_fallback_only_when_no_wire(self):
        sm = seams.resolve(plant(wire_processor=False))
        self.assertEqual(sm.interlockings["X"].processor, "Alpha")
        self.assertTrue(sm.report.by_code("unit.processor.implicit_only"))

    def test_missing_when_neither(self):
        sm = seams.resolve(plant(wire_processor=False, two_processors=True))
        self.assertIsNone(sm.interlockings["X"].processor)
        self.assertTrue(sm.report.by_code("unit.processor.missing"))

    def test_disagreement_is_an_error(self):
        src = plant(two_processors=True)
        # a transport wired to Alpha whose Processor field says Beta: the wire and the fallback disagree (§3.12)
        src.symbols["T1"] = sym("T1", "Transport-MQTT", "/X/", "MQTT", Role="TRANSPORT", Kind="MQTT", Name="MQTT", Processor="Beta")
        src.nets.append(net("n2", ("T1", "Processor"), ("P1", "Processor")))
        sm = seams.resolve(from_symbols(src.symbols.values(), src.nets))
        self.assertTrue(sm.report.by_code("transport.anchor.disagree"))
        self.assertTrue(sm.report.errors)

    def test_macro_expands_in_scope(self):
        src = plant()
        src.symbols["E1"] = sym("E1", "Encoding-AAR", "/", "AAR", Role="CODELINE_ENCODING", Kind="AAR", Name="AAR", Topic="ctc/<STRUCTURE:RAILROAD:Name>/codeline/")
        sm = seams.resolve(src)
        self.assertEqual(sm.encodings["AAR"].settings["Topic"], "ctc/SPCoast/codeline/")

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
        rows = {d.serves: d for d in sm.interlockings["X"].devices}
        self.assertEqual([(b.function, b.route) for b in rows["X:777"].bindings],
                         [("M", "Alpha/TURNOUT.777/M"), ("N", "Alpha/TURNOUT.777/N"), ("R", "Alpha/TURNOUT.777/R")])
        self.assertEqual((rows["X:784EAB"].appliance, [(b.function, b.route) for b in rows["X:784EAB"].bindings]),
                         ("mast", [("IND", "Alpha/SIGNALMAST.784EAB/IND")]))
        self.assertFalse(sm.report.by_code("driver.address"))
        self.assertFalse(sm.report.by_code("identity.name"))
        model = emit.emit(sm)
        self.assertEqual(model["layout"]["processors"]["Alpha"]["drivers"]["TURNOUT.777"], {"ic": "MQTT-JMRI", "kind": "TURNOUT"})
        self.assertEqual(layout_model.errors(model), [])

    def test_a_drawn_address_overrides_the_derived_jmri_key(self):
        src = jmri_plant()
        s = src.symbols["J1"]
        src.symbols["J1"] = Symbol(s.ref, s.lib_id, s.value, {**s.fields, "Address": "MT777"}, s.sheet)
        sm = seams.resolve(src)
        self.assertEqual(set(sm.processors["Alpha"].drivers), {"MT777", "TURNOUT.777", "SIGNALMAST.784EAB"})   # the feedback symbol still derives its key
        self.assertTrue(sm.report.by_code("driver.address.override"))
        self.assertEqual(sm.report.errors, [])

    def test_an_encoded_driver_without_kind_has_no_key(self):
        src = jmri_plant()
        s = src.symbols["J1"]
        src.symbols["J1"] = Symbol(s.ref, s.lib_id, s.value, {k: v for k, v in s.fields.items() if k != "Kind"}, s.sheet)
        sm = seams.resolve(src)
        self.assertTrue(sm.report.by_code("driver.kind"))
        self.assertEqual([x.ref for d in sm.processors["Alpha"].drivers.values() for x in d.syms], ["J2", "J3"])


    def test_head_vocabulary(self):
        src = plant()
        src.symbols.update({
            "M1": sym("M1", "Mast_Single", "/X/", "100NA", Role="APPLIANCE", Appliance="mast", Name="100NA", Style="single"),
            "H1": sym("H1", "Signal Head - CPL", "/X/", "A", Role="APPLIANCE", Appliance="head", Name="A", Style="CPL"),
            "DM1": sym("DM1", "Mast", "/X/", "100NA", Role="DEVICE", Appliance="mast", Name="100NA"),
            "DH1": sym("DH1", "Device-Head-CL-Pixel", "/X/", "~", Role="DEVICE", Appliance="head", Style="CL", Head="A"),
        })
        src.nets += [net("h", ("H1", "M"), ("M1", "H")), net("ind", ("DH1", "IND"), ("DM1", "IND"))]
        src = from_symbols(src.symbols.values(), src.nets)
        sm = seams.resolve(src)
        self.assertTrue(any("778" not in d.text and "100NA head A as CPL" in d.text for d in sm.report.by_code("head.vocabulary")))

    def test_semaphore_lamp_is_allowed(self):
        src = plant()
        src.symbols.update({
            "M1": sym("M1", "Mast_Dwarf", "/X/", "100SB", Role="APPLIANCE", Appliance="mast", Name="100SB", Style="dwarf"),
            "H1": sym("H1", "Signal Head - Semaphore-UQ", "/X/", "B", Role="APPLIANCE", Appliance="head", Name="B", Style="UQ"),
            "DM1": sym("DM1", "Mast", "/X/", "100SB", Role="DEVICE", Appliance="mast", Name="100SB"),
            "DA": sym("DA", "Device-Head-Semaphore-UQ", "/X/", "~", Role="DEVICE", Appliance="head", Style="UQ", Head="B"),
            "DL": sym("DL", "Device-Head-CL-RGB", "/X/", "~", Role="DEVICE", Appliance="head", Style="CL", Head="B"),
        })
        src.nets += [net("h", ("H1", "M"), ("M1", "H")), net("ind", ("DA", "IND"), ("DL", "IND"), ("DM1", "IND"))]
        sm = seams.resolve(from_symbols(src.symbols.values(), src.nets))
        self.assertEqual(sm.report.by_code("head.vocabulary"), [])

    def test_emitted_model_validates(self):
        sm = seams.resolve(plant())
        model = emit.emit(sm)
        self.assertEqual(layout_model.errors(model), [])
        self.assertEqual(layout_model.dumps(layout_model.loads(layout_model.dumps(model))), layout_model.dumps(model))


@unittest.skipUnless(SPCOAST_AVAILABLE, f"SPCoast project not present or kicad-cli missing: {NETLIST or PROJECT}")
class SPCoastRelationTable(unittest.TestCase):
    """ADR 0009 §3.12 on the 'both' copy: every explicit relation agrees with its fallback or stands alone; none disagree."""

    @classmethod
    def setUpClass(cls):
        cls.sm = seams.resolve(spcoast_source())

    def test_no_disagreement_between_wire_and_fallback(self):
        self.assertEqual([str(d) for d in self.sm.report.diags if d.code.endswith(".disagree")], [])

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
        self.assertEqual(e["AAR Tokens"].settings["Topic"], "ctc/SPCoast/codeline/")

    def test_cmrinet_node_and_its_bits(self):
        node = self.sm.transports["CMRInet"].nodes["30"]
        self.assertEqual((node.node_type, node.input_bytes, node.output_bytes), ("C", 2, 3))
        self.assertEqual(sum(1 for a in node.bits if a.startswith("IB")), 14)
        self.assertEqual(sum(1 for a in node.bits if a.startswith("OB")), 20)
        self.assertEqual(self.sm.report.by_code("node.bytes"), [])

    def test_stations_derive_from_houses_and_columns(self):
        ou = self.sm.office_units["SPCoast South"]
        self.assertEqual(ou.processor, "JohnCTC")
        self.assertEqual({c.number: c.house for c in ou.columns.values() if c.house},
                         {"5": ("Luchessa", "Luchessa"), "6": ("Luchessa", "Gilroy"), "7": ("Luchessa", "Carnadero")})
        self.assertEqual(len(self.sm.report.by_code("column.cp_name")), 11)

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
        masts = [d for ix in self.sm.interlockings.values() for d in ix.devices if d.appliance == "mast"]
        self.assertEqual(len(masts), 38)
        self.assertEqual([b.route for d in self.sm.interlockings["Gilroy Interchange"].devices if d.serves == "Gilroy Interchange:778NC" and d.appliance == "mast" for b in d.bindings],
                         ["Gilroy/SIGNALMAST.778NC/IND"])

    def test_layout_facts_from_the_railroad_symbol(self):
        self.assertEqual(self.sm.railroad, {"name": "SPCoast", "railroad": "Southern Pacific", "region": "Coast Line", "era": "1960+", "rulebook": "GCOR"})

    def test_model_validates_and_round_trips(self):
        model = emit.emit(self.sm)
        self.assertEqual(layout_model.errors(model), [])
        text = layout_model.dumps(model)
        self.assertEqual(layout_model.dumps(layout_model.loads(text)), text)

    def test_drawing_has_no_errors(self):
        """The compiler writes no file while this fails; the head vocabulary at Gilroy Interchange is the open item."""
        self.assertEqual([str(d) for d in self.sm.report.errors], [])


if __name__ == "__main__":
    unittest.main()
