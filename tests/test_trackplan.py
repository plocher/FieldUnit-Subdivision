"""Scenarios for the trackplan piece (semantics handoff item 2; ADR 0010 §4.1, C6).

Each scenario's Given is a netlist fragment in relational form: a table of symbols with their fields, a table of
nets with their member pins. Its Then is a table of what the Layout Data Model File says. No fixture file: the
tables are the scenario. The SPCoast project is the integration gate, in ``SPCoastTrackplan`` below.
"""
from __future__ import annotations

import shlex
import unittest

from tools import layout_model
from tools.layout_compiler import emit, seams
from tools.layout_compiler.source import Net, PinRef, Symbol, from_symbols
from tests.test_layout_compiler import NETLIST, PROJECT, SPCOAST_AVAILABLE, spcoast_source

SHEET = "/X/"
# The interlocking every scenario stands in: its declaration, its processor and its houses are scaffolding.
SCAFFOLD = """
IX1  | Interlocking | STRUCTURE | Kind=INTERLOCKING Name=X
P1   | Processor    | STRUCTURE | Kind=PROCESSOR Name=Alpha Board=cpNode
"""


def symbols(table: str) -> list[Symbol]:
    """Rows of ``ref | library symbol | Role | Field=value ...`` (a value with spaces in double quotes)."""
    out = []
    for line in filter(str.strip, table.splitlines()):
        ref, lib, role, fields = (c.strip() for c in line.split("|"))
        kv = {}
        for tok in shlex.split(fields):
            k, _, v = tok.partition("=")
            kv[k.replace("_", " ")] = v
        out.append(Symbol(ref, f"Railroad-Trackplan:{lib}", "", {"Role": role, **kv}, SHEET))
    return out


def nets(table: str) -> list[Net]:
    """Rows of ``net | REF.pin REF.pin ...``."""
    out = []
    for line in filter(str.strip, table.splitlines()):
        name, members = (c.strip() for c in line.split("|"))
        out.append(Net(name, tuple(PinRef(*m.split(".", 1)) for m in members.split())))
    return out


def compile_(sym_table: str, net_table: str):
    sm = seams.resolve(from_symbols(symbols(SCAFFOLD + sym_table), nets("n0 | IX1.Processor P1.Processor\n" + net_table)))
    return sm, emit.emit(sm)["interlockings"]["X"]


def codes(sm, severity: str) -> list[str]:
    return sorted(d.code for d in sm.report.diags if d.severity == severity)


def diags(sm, *prefixes: str) -> list[tuple[str, str]]:
    """The diagnostics as a table of (code, symbol reference): structured fields, never the message text."""
    return sorted((d.code, d.where.split(" ")[0].rsplit("/", 1)[-1]) for d in sm.report.diags if d.code.startswith(prefixes))


# One switch inside three signal joints of house East: the Sargent shape.
ONE_SWITCH = """
H1   | House            | STRUCTURE | Kind=CONTROL_POINT CP_Name=East
SW1  | Switch_Lock      | APPLIANCE | Appliance=switch Style=lock Name=835 TC=835T1 CP=East
J1   | IRJ-Signal       | TRACK     | Kind=IRJ_SIGNAL CP=East
J2   | IRJ-Signal       | TRACK     | Kind=IRJ_SIGNAL CP=East
J3   | IRJ-Signal       | TRACK     | Kind=IRJ_SIGNAL CP=East
M1   | Mast_Double      | APPLIANCE | Appliance=mast Style=double Name=836NAB
M2   | Mast_Single      | APPLIANCE | Appliance=mast Style=single Name=836SA
M3   | Mast_Dwarf       | APPLIANCE | Appliance=mast Style=dwarf Name=836SB
HA   | Signal Head - CPL | APPLIANCE | Appliance=head Style=CPL Name=A
HB   | Signal Head - CPL | APPLIANCE | Appliance=head Style=CPL Name=B
HC   | Signal Head - CL  | APPLIANCE | Appliance=head Style=CL Name=A
HD   | Signal Head - Semaphore-UQ | APPLIANCE | Appliance=head Style=UQ Name=B
TC1  | Track Circuit    | APPLIANCE | Appliance=track_circuit Name=1NAT CP=East
TC2  | Track Circuit    | APPLIANCE | Appliance=track_circuit Name=1SAT CP=East
TC3  | Track Circuit    | APPLIANCE | Appliance=track_circuit Name=2SAT CP=East
NX1  | NextCP           | TRACK     | Kind=NEXT_CP
R1   | Rule261-DoT-BiDirectional | POLICY | Kind=RULE_261 Direction=BOTH
"""
ONE_SWITCH_NETS = """
c    | SW1.C J1.A
n    | SW1.N J2.A
r    | SW1.R J3.A
w    | J1.B TC1.TC NX1.To R1.Track
e1   | J2.B TC2.TC
e2   | J3.B TC3.TC
s1   | J1.SIGNAL M1.SIGNAL
s2   | J2.SIGNAL M2.SIGNAL
s3   | J3.SIGNAL M3.SIGNAL
h1   | HA.M M1.H1
h2   | HB.M M1.H2
h3   | HC.M M2.H
h4   | HD.M M3.H
"""


class Circuits(unittest.TestCase):
    def test_a_switchs_legs_carry_its_os_circuit_and_each_joint_names_the_port_it_meets(self):
        sm, ix = compile_(ONE_SWITCH, ONE_SWITCH_NETS)
        self.assertEqual(sm.report.errors, [])
        rows = sorted((j["mast"], j["circuits"]["A"], j["circuits"]["B"], j["ports"]["A"]) for j in ix["track"]["joints"])
        self.assertEqual(rows, [
            ("X:836NAB", "X:835T1", "X:1NAT", ["X:835.C"]),
            ("X:836SA",  "X:835T1", "X:1SAT", ["X:835.N"]),
            ("X:836SB",  "X:835T1", "X:2SAT", ["X:835.R"]),
        ])
        self.assertEqual(ix["track"]["ends"], [{"kind": "NEXT_CP", "circuits": {"To": "X:1NAT"}}])
        self.assertEqual(ix["track"]["policies"], [{"kind": "RULE_261", "circuits": {"Track": "X:1NAT"}, "direction": "BOTH"}])

    def test_one_circuit_named_by_marker_and_by_tc_must_agree(self):
        sm, _ = compile_(ONE_SWITCH + "TC9 | Track Circuit | APPLIANCE | Appliance=track_circuit Name=9T\n", ONE_SWITCH_NETS.replace("c    | SW1.C J1.A", "c    | SW1.C J1.A TC9.TC"))
        self.assertIn("circuit.name.disagree", codes(sm, "error"))

    def test_two_markers_on_one_circuit_are_an_error(self):
        sm, _ = compile_(ONE_SWITCH + "TC9 | Track Circuit | APPLIANCE | Appliance=track_circuit Name=9T\n", ONE_SWITCH_NETS.replace("e1   | J2.B TC2.TC", "e1   | J2.B TC2.TC TC9.TC"))
        self.assertIn("circuit.names", codes(sm, "error"))

    def test_dark_track_has_no_circuit_and_an_end_names_the_port_it_meets(self):
        given = """
H1   | House           | STRUCTURE | Kind=CONTROL_POINT CP_Name=East
SW1  | Switch_Manual   | APPLIANCE | Appliance=switch Style=manual Name=1
E1   | IRJ-END_CTC     | TRACK     | Kind=END_CTC
TC1  | Track Circuit   | APPLIANCE | Appliance=track_circuit Name=2SAT
I1   | Industry        | TRACK     | Kind=INDUSTRY
I2   | Industry        | TRACK     | Kind=INDUSTRY
"""
        sm, ix = compile_(given, """
ctc  | E1.CTC TC1.TC
dark | E1.DARK SW1.C
in   | I1.EoT SW1.N
ir   | I2.EoT SW1.R
""")
        self.assertEqual(sm.report.errors, [])
        self.assertEqual(sorted(map(str, ix["track"]["ends"]), key=str), sorted(map(str, [
            {"kind": "END_CTC", "circuits": {"CTC": "X:2SAT"}, "ports": {"DARK": ["X:1.C"]}},
            {"kind": "INDUSTRY", "ports": {"EoT": ["X:1.N"]}},
            {"kind": "INDUSTRY", "ports": {"EoT": ["X:1.R"]}},
        ]), key=str))
        self.assertNotIn("osCircuit", ix["appliances"]["1"])

    def test_a_derail_joins_its_switchs_circuit_and_ports_that_meet_are_a_link(self):
        given = """
H1   | House           | STRUCTURE | Kind=CONTROL_POINT CP_Name=Gilroy
SW1  | Switch_Lock     | APPLIANCE | Appliance=switch Style=lock Name=795 TC=795T1 CP=Gilroy
D1   | Derail          | APPLIANCE | Appliance=switch Style=derail Name=795D IndicationCeiling=STOP/RESTRICTING CP=Gilroy
J1   | IRJ-Signal      | TRACK     | Kind=IRJ_SIGNAL CP=Gilroy
"""
        sm, ix = compile_(given, """
rr   | SW1.R D1.R
dc   | D1.C J1.A
""")
        self.assertEqual(sm.report.errors, [])
        self.assertEqual(ix["track"]["links"], [{"ports": ["X:795.R", "X:795D.R"], "circuit": "X:795T1"}])
        self.assertEqual(ix["track"]["joints"][0]["circuits"], {"A": "X:795T1"})
        self.assertEqual(ix["appliances"]["795D"], {"appliance": "switch", "style": "derail", "indicationCeiling": "STOP/RESTRICTING",
                                                    "osCircuit": "X:795T1", "controlPoint": "X:Gilroy"})

    def test_a_reference_to_another_interlockings_circuit_names_the_track_but_is_no_appliance(self):
        given = """
H1   | House           | STRUCTURE | Kind=CONTROL_POINT CP_Name=East
J1   | IRJ             | TRACK     | Kind=IRJ
TC1  | Track Circuit   | APPLIANCE | Appliance=track_circuit Name=Corporal:2NAT CP=Corporal
TC2  | Track Circuit   | APPLIANCE | Appliance=track_circuit Name=1SAT CP=East
"""
        sm, ix = compile_(given, "a | J1.A TC1.TC\nb | J1.B TC2.TC\n")
        self.assertEqual(sm.report.errors, [])
        self.assertEqual(ix["track"]["joints"], [{"kind": "IRJ", "circuits": {"A": "Corporal:2NAT", "B": "X:1SAT"}}])
        self.assertEqual(sorted(ix["appliances"]), ["1SAT"])


class Membership(unittest.TestCase):
    def test_signals_give_every_appliance_inside_and_every_mast_its_control_point(self):
        """Signals protect routes through the interlocking: the approach circuits outside the joints have no control
        point, whatever their CP field says (the owner, 2026-10-25; approach blocks wait for ABS/APB)."""
        sm, ix = compile_(ONE_SWITCH, ONE_SWITCH_NETS)
        table = {n: (a["appliance"], a.get("controlPoint")) for n, a in ix["appliances"].items()}
        self.assertEqual(table, {
            "835": ("switch", "X:East"),
            "836NAB": ("mast", "X:East"), "836SA": ("mast", "X:East"), "836SB": ("mast", "X:East"),
            "1NAT": ("track_circuit", None), "1SAT": ("track_circuit", None), "2SAT": ("track_circuit", None),
        })
        self.assertEqual(ix["appliances"]["836NAB"]["heads"], {"A": {"style": "CPL"}, "B": {"style": "CPL"}})
        self.assertEqual(ix["appliances"]["836SB"]["heads"], {"B": {"style": "UQ"}})
        # derived and stated agree on the switch; an approach circuit's CP field is not written; a mast is derived only
        self.assertEqual(diags(sm, "appliance.control_point", "control_point"), [
            ("appliance.control_point.explicit_only", "M1"), ("appliance.control_point.explicit_only", "M2"),
            ("appliance.control_point.explicit_only", "M3"),
            ("control_point.unprotected", "TC1"), ("control_point.unprotected", "TC2"), ("control_point.unprotected", "TC3"),
        ])

    def test_a_cp_field_that_disagrees_with_the_signals_is_an_error(self):
        given = ONE_SWITCH.replace("CP_Name=East", "CP_Name=East\nH2 | House | STRUCTURE | Kind=CONTROL_POINT CP_Name=West", 1)
        sm, _ = compile_(given.replace("TC=835T1 CP=East", "TC=835T1 CP=West"), ONE_SWITCH_NETS)
        self.assertEqual(codes(sm, "error"), ["appliance.control_point.disagree"])

    def test_a_circuit_bounded_by_two_control_points_is_the_cp_fields_to_say(self):
        given = ONE_SWITCH.replace("CP_Name=East", "CP_Name=East\nH2 | House | STRUCTURE | Kind=CONTROL_POINT CP_Name=West", 1)
        given = given.replace("J3   | IRJ-Signal       | TRACK     | Kind=IRJ_SIGNAL CP=East", "J3 | IRJ-Signal | TRACK | Kind=IRJ_SIGNAL CP=West")
        sm, ix = compile_(given, ONE_SWITCH_NETS)
        self.assertEqual(sm.report.errors, [])
        self.assertEqual(len(sm.report.by_code("control_point.shared")), 1)
        self.assertEqual((ix["appliances"]["835"]["controlPoint"], ix["appliances"]["836SB"]["controlPoint"]), ("X:East", "X:West"))

    def test_a_control_point_that_is_no_house_is_an_error(self):
        sm, _ = compile_(ONE_SWITCH.replace("Kind=IRJ_SIGNAL CP=East", "Kind=IRJ_SIGNAL CP=Nowhere", 1), ONE_SWITCH_NETS)
        self.assertIn("control_point.house", codes(sm, "error"))

    def test_a_signal_joint_without_cp_belongs_to_the_one_house(self):
        sm, ix = compile_(ONE_SWITCH.replace("Kind=IRJ_SIGNAL CP=East", "Kind=IRJ_SIGNAL", 1), ONE_SWITCH_NETS)
        self.assertEqual(sm.report.errors, [])
        self.assertEqual(ix["appliances"]["836NAB"]["controlPoint"], "X:East")

    def test_two_appliances_with_one_name_are_an_error(self):
        sm, _ = compile_(ONE_SWITCH.replace("Name=836SA", "Name=836NAB"), ONE_SWITCH_NETS)
        self.assertIn("appliance.duplicate", codes(sm, "error"))

    def test_protection_crosses_plain_joints_between_switches_but_not_into_the_yard(self):
        """Watsonville's shape: a ladder of switches joined by plain joints behind one signal; a track between two ladder
        switches is inside; a yard track off one switch is outside (the owner, 2026-10-25)."""
        given = """
H1   | House         | STRUCTURE | Kind=CONTROL_POINT CP_Name=Yard
J1   | IRJ-Signal    | TRACK     | Kind=IRJ_SIGNAL CP=Yard
SW1  | Switch_Powered | APPLIANCE | Appliance=switch Style=powered Name=15 TC=15T1
SW2  | Switch_Powered | APPLIANCE | Appliance=switch Style=powered Name=17 TC=17T1
SW3  | Switch_Powered | APPLIANCE | Appliance=switch Style=powered Name=19 TC=19T1
P1   | IRJ           | TRACK     | Kind=IRJ
P2   | IRJ           | TRACK     | Kind=IRJ
P3   | IRJ           | TRACK     | Kind=IRJ
P4   | IRJ           | TRACK     | Kind=IRJ
TCa  | Track Circuit | APPLIANCE | Appliance=track_circuit Name=2AT CP=Yard
TCy  | Track Circuit | APPLIANCE | Appliance=track_circuit Name=7BT CP=Yard
B1   | Bumper        | TRACK     | Kind=BUMPER
"""
        sm, ix = compile_(given, """
in   | J1.A SW1.C
l1   | SW1.N P1.A
l2   | P1.B SW2.C
a1   | SW2.N P2.A
a2   | P2.B TCa.TC P3.A
a3   | P3.B SW3.R
y1   | SW1.R P4.A
y2   | P4.B TCy.TC B1.EoT
""")
        self.assertEqual(sm.report.errors, [])
        self.assertEqual({n: a.get("controlPoint") for n, a in ix["appliances"].items()},
                         {"15": "X:Yard", "17": "X:Yard", "19": None, "2AT": "X:Yard", "7BT": None})

    def test_a_switch_in_dark_track_has_no_control_point(self):
        given = """
H1   | House           | STRUCTURE | Kind=CONTROL_POINT CP_Name=East
SW1  | Switch_Manual_Sensed | APPLIANCE | Appliance=switch Style=manual_sensed Name=1 CP=East
E1   | IRJ-END_CTC     | TRACK     | Kind=END_CTC
"""
        sm, ix = compile_(given, "dark | E1.DARK SW1.C\n")
        self.assertEqual(sm.report.errors, [])
        self.assertNotIn("controlPoint", ix["appliances"]["1"])
        self.assertEqual(len(sm.report.by_code("control_point.unprotected")), 1)

    def test_a_lamp_keeps_its_cp_field(self):
        given = """
H1   | House           | STRUCTURE | Kind=CONTROL_POINT CP_Name=East
L1   | AUXILIARY       | APPLIANCE | Appliance=lamp Style=non_vital Name=NFLK CP=East
"""
        sm, ix = compile_(given, "")
        self.assertEqual(ix["appliances"]["NFLK"]["controlPoint"], "X:East")

    def test_a_maintainer_call_belongs_to_the_house_it_is_wired_to(self):
        given = """
H1   | House           | STRUCTURE | Kind=CONTROL_POINT CP_Name=East
H2   | House           | STRUCTURE | Kind=CONTROL_POINT CP_Name=West
MC1  | MaintainerCall  | APPLIANCE | Appliance=lamp Style=maintainer_call Name=MC1
"""
        sm, ix = compile_(given, "mc | H2.MC MC1.MC\n")
        self.assertEqual(ix["appliances"]["MC1"]["controlPoint"], "X:West")

    def test_a_virtual_circuit_lists_its_members(self):
        given = """
H1   | House                 | STRUCTURE | Kind=CONTROL_POINT CP_Name=East
V1   | Track Circuit_Virtual | APPLIANCE | Appliance=track_circuit Style=virtual Name=0100T IndicationToken=15T1,17T1 CP=East
"""
        sm, ix = compile_(given, "")
        self.assertEqual(ix["appliances"]["0100T"], {"appliance": "track_circuit", "style": "virtual", "members": ["X:15T1", "X:17T1"]})

    def test_the_output_validates(self):
        sm, _ = compile_(ONE_SWITCH, ONE_SWITCH_NETS)
        self.assertEqual(layout_model.errors(emit.emit(sm)), [])


class Checks(unittest.TestCase):
    """Each fact inconsistency the trackplan piece can see, as one scenario: (code, the symbol it names)."""

    def check(self, sym_table: str, net_table: str, want: list[tuple[str, str]]):
        sm, _ = compile_(sym_table, net_table)
        self.assertEqual([x for x in diags(sm, *{c for c, _ in want}) if x[0] in {c for c, _ in want}], want)

    def test_a_signal_joint_turned_around(self):
        self.check(ONE_SWITCH, ONE_SWITCH_NETS.replace("c    | SW1.C J1.A", "c    | SW1.C J1.B").replace("w    | J1.B", "w    | J1.A"),
                   [("joint.reversed", "J1")])

    def test_a_joint_with_one_circuit_on_both_sides(self):
        given = ONE_SWITCH + "J9 | IRJ | TRACK | Kind=IRJ\n"
        self.check(given, ONE_SWITCH_NETS.replace("e1   | J2.B TC2.TC", "e1   | J2.B TC2.TC J9.A J9.B"), [("joint.loop", "J9")])

    def test_end_ctc_turned_around(self):
        given = """
H1   | House           | STRUCTURE | Kind=CONTROL_POINT CP_Name=East
E1   | IRJ-END_CTC     | TRACK     | Kind=END_CTC
TC1  | Track Circuit   | APPLIANCE | Appliance=track_circuit Name=2SAT
I1   | Industry        | TRACK     | Kind=INDUSTRY
"""
        self.check(given, "d | E1.DARK TC1.TC\nc | E1.CTC I1.EoT\n", [("end_ctc.sides", "E1")])

    def test_two_masts_on_one_signal_joint(self):
        self.check(ONE_SWITCH, ONE_SWITCH_NETS.replace("s2   | J2.SIGNAL M2.SIGNAL", "s2   | J2.SIGNAL M2.SIGNAL M3.SIGNAL")
                   .replace("s3   | J3.SIGNAL M3.SIGNAL\n", ""), [("joint.masts", "J2")])

    def test_a_mast_on_no_joint(self):
        self.check(ONE_SWITCH, ONE_SWITCH_NETS.replace("s3   | J3.SIGNAL M3.SIGNAL\n", ""), [("mast.joint", "M3")])

    def test_a_mast_named_for_heads_it_does_not_carry(self):
        sm, _ = compile_(ONE_SWITCH.replace("Name=836NAB", "Name=836NCD"), ONE_SWITCH_NETS)
        self.assertEqual(codes(sm, "error"), ["mast.heads"])

    def test_one_head_letter_on_two_masts_of_one_signal(self):
        given = ONE_SWITCH.replace("Name=836SA", "Name=836NA").replace("Signal Head - CL  | APPLIANCE | Appliance=head Style=CL Name=A",
                                                                          "Signal Head - CL  | APPLIANCE | Appliance=head Style=CL Name=A")
        sm, _ = compile_(given, ONE_SWITCH_NETS)
        self.assertIn("mast.letters", codes(sm, "error"))

    def test_a_switch_with_no_track(self):
        given = """
H1   | House           | STRUCTURE | Kind=CONTROL_POINT CP_Name=East
SW1  | Switch_Lock     | APPLIANCE | Appliance=switch Style=lock Name=9 TC=9T1 CP=East
"""
        sm, ix = compile_(given, "")
        self.assertEqual(diags(sm, "switch.track"), [("switch.track", "SW1")])
        self.assertNotIn("osCircuit", ix["appliances"]["9"])


@unittest.skipUnless(SPCOAST_AVAILABLE, f"SPCoast project not present or kicad-cli missing: {NETLIST or PROJECT}")
class SPCoastTrackplan(unittest.TestCase):
    """The integration gate: the trackplan of the live project, as the relation table's trackplan rows read it."""

    @classmethod
    def setUpClass(cls):
        cls.sm = seams.resolve(spcoast_source())
        cls.model = emit.emit(cls.sm)

    def ix(self, name):
        return self.model["interlockings"][name]

    def test_every_mast_stands_on_one_signal_joint_and_has_its_control_point(self):
        masts = [(i, n, a) for i, ix in self.model["interlockings"].items() for n, a in ix.get("appliances", {}).items() if a["appliance"] == "mast"]
        self.assertEqual([(i, n) for i, n, a in masts if "controlPoint" not in a], [])
        joints = [j for ix in self.model["interlockings"].values() for j in ix.get("track", {}).get("joints", []) if j["kind"] == "IRJ_SIGNAL"]
        self.assertEqual(len(joints), 35)
        self.assertEqual([j for j in joints if "mast" not in j or "controlPoint" not in j], [])

    def test_no_derived_membership_disagrees_with_a_cp_field(self):
        self.assertEqual(self.sm.report.by_code("appliance.control_point.disagree"), [])
        self.assertEqual(self.sm.report.by_code("control_point.house"), [])

    def test_sargents_os_circuit_is_on_its_three_signal_joints(self):
        joints = [j for j in self.ix("Sargent")["track"]["joints"] if j["kind"] == "IRJ_SIGNAL"]
        self.assertEqual(sorted((j["circuits"]["A"], j["ports"]["A"][0]) for j in joints),
                         [("Sargent:835T1", "Sargent:835.C"), ("Sargent:835T1", "Sargent:835.N"), ("Sargent:835T1", "Sargent:835.R")])

    def test_luchessa_houses_and_its_derail(self):
        a = self.ix("Luchessa")["appliances"]
        self.assertEqual({n: a[n]["controlPoint"] for n in ("783", "795", "795D", "799")},
                         {"783": "Luchessa:Luchessa", "795": "Luchessa:Gilroy", "795D": "Luchessa:Gilroy", "799": "Luchessa:Carnadero"})
        self.assertEqual(self.ix("Luchessa")["track"]["links"], [{"ports": ["Luchessa:795.R", "Luchessa:795D.R"], "circuit": "Luchessa:795T1"}])
        self.assertEqual(self.ix("Luchessa")["track"]["mileposts"], ["78.3", "79.3"])

    def test_no_circuit_carries_two_names(self):
        self.assertEqual(self.sm.report.by_code("circuit.names") + self.sm.report.by_code("circuit.name.disagree"), [])


if __name__ == "__main__":
    unittest.main()
