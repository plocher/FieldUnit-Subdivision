"""Scenarios for the trackplan piece (semantics handoff item 2; ADR 0010 §4.1, C6; ADR 0011's three maps).

Each scenario's Given is a netlist fragment in relational form: a table of symbols with their fields, a table of
nets with their member pins. Its Then is a table of what the Layout Data Model File says. No fixture file: the
tables are the scenario. The SPCoast project is the integration gate, in ``SPCoastTrackplan`` below.
"""
from __future__ import annotations

import json
import shlex
import unittest
from dataclasses import replace

from tools import layout_model
from tools.layout_compiler import emit, seams, trackplan
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


def rows(ix, kind: str) -> list[dict]:
    """A track list's rows without their ids: an id is an opaque identity, not a fact a scenario states."""
    return [{k: v for k, v in r.items() if k != "id"} for r in ix["track"].get(kind, [])]


def sorted_rows(rs) -> list[str]:
    return sorted(json.dumps(r, sort_keys=True) for r in rs)


def at(sm, ref: str, side: str) -> str:
    """How the model names an unnamed row's side: the row's id (its symbol's UUID) and the side (three-maps D5, D10)."""
    return f"{sm.source.symbols[ref].uuid}.{side}"


def track_relations(ix) -> dict[str, list[str]]:
    """Every track side's relation in the interlocking, keyed by the side as a peer names it: ``X:835.C``, ``<id>.approach``."""
    out: dict[str, list[str]] = {}
    for name, a in ix.get("appliances", {}).items():
        for side, v in a.get("relations", {}).items():
            if isinstance(v, list):
                out[f"X:{name}.{side}"] = v
    for kind in ("joints", "ends", "policies"):
        for r in ix["track"].get(kind, []):
            for side, v in r.get("relations", {}).items():
                if isinstance(v, list):
                    out[f"{r.get('name') or r['id']}.{side}"] = v
    return out


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
        joints = sorted((j["relations"]["mast"], j["derived"]["circuits"]["governed"], j["derived"]["circuits"]["approach"],
                         j["relations"]["governed"]) for j in ix["track"]["joints"])
        self.assertEqual(joints, [
            ("X:836NAB", "X:835T1", "X:1NAT", ["X:835.C"]),
            ("X:836SA",  "X:835T1", "X:1SAT", ["X:835.N"]),
            ("X:836SB",  "X:835T1", "X:2SAT", ["X:835.R"]),
        ])
        self.assertEqual(rows(ix, "ends"), [{"given": {"Kind": "NEXT_CP"}, "derived": {"circuits": {"track": "X:1NAT"}},
                                             "relations": {"track": sorted([at(sm, "J1", "approach"), at(sm, "R1", "track"), "X:1NAT.TC"])}}])
        self.assertEqual(rows(ix, "policies"), [{"given": {"Kind": "RULE_261", "Direction": "BOTH"}, "derived": {"circuits": {"track": "X:1NAT"}},
                                                 "relations": {"track": sorted([at(sm, "J1", "approach"), at(sm, "NX1", "track"), "X:1NAT.TC"])}}])

    def test_a_signal_joints_sides_are_approach_and_governed(self):
        """ADR 0012 §8 and the table's D15: the governed side is the symbol's A pin, where the route it protects begins;
        the approach side its B pin. Its wires and its circuits use the same names; A and B appear nowhere."""
        sm, ix = compile_(ONE_SWITCH, ONE_SWITCH_NETS)
        j = next(j for j in ix["track"]["joints"] if j["relations"]["mast"] == "X:836SA")
        self.assertEqual(j["relations"], {"governed": ["X:835.N"], "approach": ["X:1SAT.TC"], "mast": "X:836SA"})
        self.assertEqual(j["derived"], {"circuits": {"governed": "X:835T1", "approach": "X:1SAT"}, "controlPoint": "X:East"})
        self.assertEqual(j["given"], {"Kind": "IRJ_SIGNAL", "CP": "East"})

    def test_a_policy_signs_and_a_next_cps_pin_is_the_track_side_whatever_the_library_calls_it(self):
        """RULE_261 draws its pin as Track, the others as To: one meaning, one side name (D15)."""
        given = """
H1   | House           | STRUCTURE | Kind=CONTROL_POINT CP_Name=East
TC1  | Track Circuit   | APPLIANCE | Appliance=track_circuit Name=1NAT
R1   | Rule261-DoT-BiDirectional | POLICY | Kind=RULE_261 Direction=BOTH
R2   | Rule251-DoT-Right | POLICY | Kind=RULE_251 Direction=RIGHT
NX1  | NextCP          | TRACK     | Kind=NEXT_CP Interlocking=Lick
"""
        sm, ix = compile_(given, "w | TC1.TC R1.Track R2.To NX1.To\n")
        self.assertEqual({str(r["derived"]) for r in ix["track"]["policies"] + ix["track"]["ends"]}, {str({"circuits": {"track": "X:1NAT"}})})

    def test_every_track_row_carries_its_symbols_uuid_as_its_id(self):
        """The table's D10: a row's identity is opaque and stable, the KiCad per-instance UUID of its symbol."""
        sm, ix = compile_(ONE_SWITCH, ONE_SWITCH_NETS)
        by_ref = {s.ref: s.uuid for s in sm.source.symbols.values()}
        ids = [r["id"] for kind in ("joints", "ends", "policies") for r in ix["track"][kind]]
        self.assertEqual(sorted(ids), sorted(by_ref[r] for r in ("J1", "J2", "J3", "NX1", "R1")))

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
        self.assertEqual(sorted_rows(rows(ix, "ends")), sorted_rows([
            {"given": {"Kind": "END_CTC"}, "derived": {"circuits": {"CTC": "X:2SAT"}}, "relations": {"CTC": ["X:2SAT.TC"], "DARK": ["X:1.C"]}},
            {"given": {"Kind": "INDUSTRY"}, "relations": {"EoT": ["X:1.N"]}},
            {"given": {"Kind": "INDUSTRY"}, "relations": {"EoT": ["X:1.R"]}},
        ]))
        self.assertNotIn("osCircuit", ix["appliances"]["1"].get("derived", {}))

    def test_unnamed_rows_on_dark_track_name_each_other_by_id(self):
        """The owner, 2026-10-27: a track pin's relations name every row or port its wire reaches, unnamed rows by id.
        Two unnamed rows on dark track with nothing between them state their connection; nothing is reported."""
        given = """
H1   | House           | STRUCTURE | Kind=CONTROL_POINT CP_Name=East
E1   | IRJ-END_CTC     | TRACK     | Kind=END_CTC
B1   | Bumper          | TRACK     | Kind=BUMPER
"""
        sm, ix = compile_(given, "dark | E1.DARK B1.EoT\n")
        self.assertEqual(sm.report.errors, [])
        self.assertEqual(diags(sm, "track"), [])
        rel = track_relations(ix)
        self.assertEqual(rel[at(sm, "E1", "DARK")], [at(sm, "B1", "EoT")])
        self.assertEqual(rel[at(sm, "B1", "EoT")], [at(sm, "E1", "DARK")])

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
        self.assertEqual(ix["track"]["links"], [{"derived": {"ports": ["X:795.R", "X:795D.R"], "circuit": "X:795T1"}}])
        self.assertEqual(ix["track"]["joints"][0]["derived"]["circuits"], {"governed": "X:795T1"})
        self.assertEqual(ix["appliances"]["795D"], {
            "given": {"Appliance": "switch", "Style": "derail", "IndicationCeiling": "STOP/RESTRICTING", "CP": "Gilroy"},
            "relations": {"C": [at(sm, "J1", "governed")], "R": ["X:795.R"]},
            "derived": {"osCircuit": "X:795T1", "controlPoint": "X:Gilroy"}})

    def test_a_reference_to_another_interlockings_circuit_names_the_track_but_is_no_appliance(self):
        given = """
H1   | House           | STRUCTURE | Kind=CONTROL_POINT CP_Name=East
J1   | IRJ             | TRACK     | Kind=IRJ
TC1  | Track Circuit   | APPLIANCE | Appliance=track_circuit Name=Corporal:2NAT CP=Corporal
TC2  | Track Circuit   | APPLIANCE | Appliance=track_circuit Name=1SAT CP=East
"""
        sm, ix = compile_(given, "a | J1.A TC1.TC\nb | J1.B TC2.TC\n")
        self.assertEqual(sm.report.errors, [])
        self.assertEqual(rows(ix, "joints"), [{"given": {"Kind": "IRJ"}, "derived": {"circuits": {"A": "Corporal:2NAT", "B": "X:1SAT"}},
                                               "relations": {"A": ["Corporal:2NAT.TC"], "B": ["X:1SAT.TC"]}}])
        self.assertEqual(sorted(ix["appliances"]), ["1SAT"])



class Adjacency(unittest.TestCase):
    """The owner, 2026-10-27: a track pin's relations name every row or port its wire reaches, unnamed rows by id, so a
    reader walks the track through ``relations`` alone, never through circuit names."""

    def test_an_unnamed_approach_side_names_every_neighbour_on_its_wire(self):
        """J1's approach wire reaches a NextCP, a Rule 261 sign and the 1NAT marker: all three, sorted, none by circuit."""
        sm, ix = compile_(ONE_SWITCH, ONE_SWITCH_NETS)
        rel = track_relations(ix)
        self.assertEqual(rel[at(sm, "J1", "approach")], sorted([at(sm, "NX1", "track"), at(sm, "R1", "track"), "X:1NAT.TC"]))
        self.assertEqual(ix["appliances"]["1NAT"]["relations"]["TC"],
                         sorted([at(sm, "J1", "approach"), at(sm, "NX1", "track"), at(sm, "R1", "track")]))
        self.assertEqual(ix["appliances"]["835"]["relations"], {"C": [at(sm, "J1", "governed")], "N": [at(sm, "J2", "governed")],
                                                                "R": [at(sm, "J3", "governed")]})
        self.assertEqual(layout_model.errors(emit.emit(sm)), [])

    def test_relations_are_symmetric(self):
        for shape, wires in ((ONE_SWITCH, ONE_SWITCH_NETS), (TWO_HOUSES, TWO_HOUSES_NETS)):
            sm, ix = compile_(shape, wires)
            rel = track_relations(ix)
            self.assertEqual([(a, b) for a, bs in rel.items() for b in bs if a not in rel.get(b, [])], [])

    def test_a_pin_never_names_its_own_symbol(self):
        """A joint whose two sides share one wire is an error, and still neither side names the other."""
        given = """
H1   | House           | STRUCTURE | Kind=CONTROL_POINT CP_Name=East
J1   | IRJ             | TRACK     | Kind=IRJ
TC1  | Track Circuit   | APPLIANCE | Appliance=track_circuit Name=1SAT
"""
        sm, ix = compile_(given, "a | J1.A J1.B TC1.TC\n")
        self.assertIn("joint.loop", codes(sm, "error"))
        self.assertEqual(ix["track"]["joints"][0]["relations"], {"A": ["X:1SAT.TC"], "B": ["X:1SAT.TC"]})

    def test_the_relations_do_not_depend_on_the_order_of_the_drawing(self):
        sm, ix = compile_(ONE_SWITCH, ONE_SWITCH_NETS)
        reordered = "\n".join(reversed(ONE_SWITCH.strip().splitlines()))
        wires = "\n".join(" | ".join((n, " ".join(reversed(m.split())))) for n, m in
                          (line.split(" | ") for line in reversed(ONE_SWITCH_NETS.strip().splitlines())))
        sm2, ix2 = compile_(reordered, wires)
        self.assertEqual(json.dumps(track_relations(ix), sort_keys=True), json.dumps(track_relations(ix2), sort_keys=True))

# Two houses, the Christopher shape: switches 813 and 815 (with 815A in its gang) on North, 817 on South; siding 01T
# between 813's R and 817's R; 815's R meets 815A's R at a plain joint. Each signal states its house on the joint or on
# the mast (the designer's choice); approach circuit 1NAT states North though South's signal bounds it.
TWO_HOUSES = """
H1   | House            | STRUCTURE | Kind=CONTROL_POINT CP_Name=North
H2   | House            | STRUCTURE | Kind=CONTROL_POINT CP_Name=South
SW1  | Switch_Powered   | APPLIANCE | Appliance=switch Style=powered Name=813 TC=813T1 CP=North
SW2  | Switch_Powered   | APPLIANCE | Appliance=switch Style=powered Name=815 TC=815T1 CP=North
SW3  | Switch_Powered   | APPLIANCE | Appliance=switch Style=powered Name=815A TC=815AT1
SW4  | Switch_Powered   | APPLIANCE | Appliance=switch Style=powered Name=817 TC=817T1 CP=South
J1   | IRJ-Signal       | TRACK     | Kind=IRJ_SIGNAL CP=North
J2   | IRJ-Signal       | TRACK     | Kind=IRJ_SIGNAL
J3   | IRJ-Signal       | TRACK     | Kind=IRJ_SIGNAL CP=South
M1   | Mast_Single      | APPLIANCE | Appliance=mast Style=single Name=814SA
M2   | Mast_Single      | APPLIANCE | Appliance=mast Style=single Name=816NA CP=South
M3   | Mast_Single      | APPLIANCE | Appliance=mast Style=single Name=818NA
Q1   | IRJ              | TRACK     | Kind=IRJ
Q2   | IRJ              | TRACK     | Kind=IRJ
Q3   | IRJ              | TRACK     | Kind=IRJ
Q4   | IRJ              | TRACK     | Kind=IRJ
TC1  | Track Circuit    | APPLIANCE | Appliance=track_circuit Name=1SAT
TC2  | Track Circuit    | APPLIANCE | Appliance=track_circuit Name=01T CP=North
TC3  | Track Circuit    | APPLIANCE | Appliance=track_circuit Name=2NAT
TC4  | Track Circuit    | APPLIANCE | Appliance=track_circuit Name=1NAT CP=North
"""
TWO_HOUSES_NETS = """
a    | J1.A SW1.C
b    | J1.B TC1.TC
c    | SW1.R Q1.A
d    | Q1.B TC2.TC Q2.A
e    | Q2.B SW4.R
f    | SW1.N Q4.A
g    | Q4.B SW2.C
h    | SW2.R Q3.A
i    | Q3.B SW3.R
j    | SW3.C J2.A
k    | J2.B TC3.TC
l    | SW4.C J3.A
m    | J3.B TC4.TC
s1   | J1.SIGNAL M1.SIGNAL
s2   | J2.SIGNAL M2.SIGNAL
s3   | J3.SIGNAL M3.SIGNAL
"""


def control_points(ix) -> dict[str, str]:
    return {n: a.get("derived", {}).get("controlPoint", "").removeprefix("X:") for n, a in ix["appliances"].items()}


class Membership(unittest.TestCase):
    """Control point by propagation from the houses (the owner, 2026-10-26): a table of what each appliance is on."""

    def test_the_one_house_is_every_appliances_control_point(self):
        """Approach circuits included: a control point is the house whose field unit wires the appliance, not the
        routes its signals protect."""
        sm, ix = compile_(ONE_SWITCH.replace(" CP=East", ""), ONE_SWITCH_NETS)
        self.assertEqual(sm.report.errors, [])
        self.assertEqual(control_points(ix), {n: "East" for n in ("835", "836NAB", "836SA", "836SB", "1NAT", "1SAT", "2SAT")})
        self.assertEqual({j["derived"]["controlPoint"] for j in ix["track"]["joints"]}, {"X:East"})
        self.assertEqual(diags(sm, "control_point", "appliance.control_point", "joint.control_point"), [])
        self.assertEqual(ix["appliances"]["836NAB"]["heads"], {"A": {"given": {"Appliance": "head", "Style": "CPL"}},
                                                               "B": {"given": {"Appliance": "head", "Style": "CPL"}}})
        self.assertEqual(ix["appliances"]["836SB"]["heads"], {"B": {"given": {"Appliance": "head", "Style": "UQ"}}})
        self.assertNotIn("CP", ix["appliances"]["835"]["given"])          # stated nowhere: derived, never written as given

    def test_a_dark_switch_belongs_to_the_one_house(self):
        given = """
H1   | House           | STRUCTURE | Kind=CONTROL_POINT CP_Name=East
SW1  | Switch_Manual_Sensed | APPLIANCE | Appliance=switch Style=manual_sensed Name=1
E1   | IRJ-END_CTC     | TRACK     | Kind=END_CTC
"""
        sm, ix = compile_(given, "dark | E1.DARK SW1.C\n")
        self.assertEqual(sm.report.errors, [])
        self.assertEqual(control_points(ix), {"1": "East"})

    def test_two_houses_chains_from_the_stated_fields(self):
        """815A follows its gang's 815; 815AT1 follows 815A though signals of both houses bound it; 1SAT follows its
        signal joint, 2NAT the mast of its joint; 1NAT's own field wins over South's signal, silently."""
        sm, ix = compile_(TWO_HOUSES, TWO_HOUSES_NETS)
        self.assertEqual(sm.report.errors, [])
        self.assertEqual(control_points(ix), {
            "813": "North", "815": "North", "815A": "North", "817": "South",
            "814SA": "North", "816NA": "South", "818NA": "South",
            "1SAT": "North", "01T": "North", "2NAT": "South", "1NAT": "North",
        })
        self.assertEqual(diags(sm, "control_point"), [])

    def test_a_circuit_two_houses_reach_states_which(self):
        sm, _ = compile_(TWO_HOUSES.replace("Name=01T CP=North", "Name=01T"), TWO_HOUSES_NETS)
        self.assertEqual(diags(sm, "control_point"), [("control_point.chains", "TC2")])

    def test_an_appliance_no_house_reaches_is_an_error(self):
        given = TWO_HOUSES + "L1 | AUXILIARY | APPLIANCE | Appliance=lamp Style=non_vital Name=NFLK\n"
        given += "L2 | AUXILIARY | APPLIANCE | Appliance=lamp Style=non_vital Name=Other:SFLK\n"   # another interlocking's: no CP
        sm, ix = compile_(given, TWO_HOUSES_NETS)
        self.assertEqual(diags(sm, "control_point"), [("control_point.unreached", "L1")])
        self.assertNotIn("Other:SFLK", ix["appliances"])

    def test_a_gang_split_across_houses_is_a_warning(self):
        sm, ix = compile_(TWO_HOUSES.replace("Name=815A TC=815AT1", "Name=815A TC=815AT1 CP=South"), TWO_HOUSES_NETS)
        self.assertEqual(diags(sm, "control_point"), [("control_point.gang", "SW3")])
        self.assertEqual(control_points(ix)["815A"], "South")

    def test_a_control_point_that_is_no_house_is_an_error(self):
        sm, _ = compile_(ONE_SWITCH.replace("Kind=IRJ_SIGNAL CP=East", "Kind=IRJ_SIGNAL CP=Nowhere", 1), ONE_SWITCH_NETS)
        self.assertEqual(diags(sm, "control_point"), [("control_point.house", "J1")])

    def test_two_appliances_with_one_name_are_an_error(self):
        sm, _ = compile_(ONE_SWITCH.replace("Name=836SA", "Name=836NAB"), ONE_SWITCH_NETS)
        self.assertIn("appliance.duplicate", codes(sm, "error"))

    def test_a_maintainer_call_belongs_to_the_house_it_is_wired_to(self):
        given = """
H1   | House           | STRUCTURE | Kind=CONTROL_POINT CP_Name=East
H2   | House           | STRUCTURE | Kind=CONTROL_POINT CP_Name=West
MC1  | MaintainerCall  | APPLIANCE | Appliance=lamp Style=maintainer_call Name=MC1
"""
        sm, ix = compile_(given, "mc | H2.MC MC1.MC\n")
        self.assertEqual(control_points(ix), {"MC1": "West"})
        self.assertEqual(ix["appliances"]["MC1"]["relations"], {"house": "X:West"})          # each holder writes its end (D8)
        self.assertEqual(ix["houses"]["West"]["relations"], {"maintainerCall": "X:MC1"})
        sm, _ = compile_(given.replace("Name=MC1", "Name=MC1 CP=East"), "mc | H2.MC MC1.MC\n")
        self.assertEqual(diags(sm, "control_point"), [("control_point.disagree", "MC1")])

    def test_a_virtual_circuit_lists_its_members_and_follows_them(self):
        given = TWO_HOUSES + "V1 | Track Circuit_Virtual | APPLIANCE | Appliance=track_circuit Style=virtual Name=0100T IndicationToken=1SAT,01T\n"
        sm, ix = compile_(given, TWO_HOUSES_NETS)
        self.assertEqual(sm.report.errors, [])
        self.assertEqual(ix["appliances"]["0100T"], {
            "given": {"Appliance": "track_circuit", "Style": "virtual", "IndicationToken": "1SAT,01T"},
            "derived": {"members": ["X:1SAT", "X:01T"], "controlPoint": "X:North"}})

    def test_the_output_validates(self):
        for given, nets_ in ((ONE_SWITCH, ONE_SWITCH_NETS), (TWO_HOUSES, TWO_HOUSES_NETS)):
            sm, _ = compile_(given, nets_)
            self.assertEqual(layout_model.errors(emit.emit(sm)), [])


class Attributes(unittest.TestCase):
    def test_an_appliance_states_its_milepost(self):
        given = """
H1   | House           | STRUCTURE | Kind=CONTROL_POINT CP_Name=East
L1   | AUXILIARY       | APPLIANCE | Appliance=lamp Style=non_vital Name=HBA Milepost=83.4
L2   | AUXILIARY       | APPLIANCE | Appliance=lamp Style=non_vital Name=NFLK Milepost=north
"""
        sm, ix = compile_(given, "")
        self.assertEqual(ix["appliances"]["HBA"], {"given": {"Appliance": "lamp", "Style": "non_vital", "Milepost": "83.4"},
                                                   "derived": {"controlPoint": "X:East"}})
        self.assertEqual(diags(sm, "milepost"), [("milepost.number", "L2")])

    def test_every_stated_field_lands_in_given_as_drawn(self):
        """A field nothing reads is kept, never dropped (the owner, 2026-10-26; ADR 0011 §2)."""
        given = """
H1   | House           | STRUCTURE | Kind=CONTROL_POINT CP_Name=East
L1   | AUXILIARY       | APPLIANCE | Appliance=lamp Style=non_vital Name=NFLK Display="North flasher" Column=7
"""
        sm, ix = compile_(given, "")
        self.assertEqual(ix["appliances"]["NFLK"]["given"], {"Appliance": "lamp", "Style": "non_vital", "Display": "North flasher", "Column": "7"})


class Ends(unittest.TestCase):
    def test_a_named_end_is_what_a_dark_pin_meets(self):
        """Luchessa's shape: an industry on END CTC's DARK pin, no switch and no circuit between them."""
        given = """
H1   | House           | STRUCTURE | Kind=CONTROL_POINT CP_Name=East
E1   | IRJ-END_CTC     | TRACK     | Kind=END_CTC
TC1  | Track Circuit   | APPLIANCE | Appliance=track_circuit Name=02T
I1   | Industry        | TRACK     | Kind=INDUSTRY Name="Gilroy Industry"
"""
        sm, ix = compile_(given, "ctc | E1.CTC TC1.TC\ndark | E1.DARK I1.EoT\n")
        self.assertEqual(sm.report.errors, [])
        self.assertEqual(sorted_rows(rows(ix, "ends")), sorted_rows([
            {"given": {"Kind": "END_CTC"}, "derived": {"circuits": {"CTC": "X:02T"}}, "relations": {"CTC": ["X:02T.TC"], "DARK": ["X:Gilroy Industry.EoT"]}},
            {"name": "X:Gilroy Industry", "given": {"Kind": "INDUSTRY"}, "relations": {"EoT": [at(sm, "E1", "DARK")]}},
        ]))
        self.assertEqual(layout_model.errors(emit.emit(sm)), [])

    def test_a_name_used_twice_is_an_error(self):
        given = """
H1   | House           | STRUCTURE | Kind=CONTROL_POINT CP_Name=East
I1   | Industry        | TRACK     | Kind=INDUSTRY Name=Cannery
I2   | Industry        | TRACK     | Kind=INDUSTRY Name=Cannery
"""
        sm, _ = compile_(given, "")
        self.assertEqual(diags(sm, "track.duplicate"), [("track.duplicate", "I2")])

    def test_a_next_cp_names_where_it_leads(self):
        given = """
H1   | House           | STRUCTURE | Kind=CONTROL_POINT CP_Name=East
NX1  | NextCP          | TRACK     | Kind=NEXT_CP Interlocking=Lick
NX2  | NextCP          | TRACK     | Kind=NEXT_CP
"""
        sm, ix = compile_(given, "")
        self.assertEqual(sorted_rows(rows(ix, "ends")), sorted_rows([{"given": {"Kind": "NEXT_CP", "Interlocking": "Lick"}}, {"given": {"Kind": "NEXT_CP"}}]))
        self.assertEqual(diags(sm, "next_cp"), [("next_cp.interlocking", "NX2"), ("next_cp.off_layout", "")])

    def test_next_cps_lead_back_as_often_as_they_lead_out(self):
        tp = trackplan.Trackplan({
            "A": trackplan.Plan("A", track={"ends": [{"given": {"Kind": "NEXT_CP", "Interlocking": "B"}}] * 2}),
            "B": trackplan.Plan("B", track={"ends": [{"given": {"Kind": "NEXT_CP", "Interlocking": "A"}}]}),
        })
        sm = seams.Seams(None, seams.Report())
        trackplan._pair_next_cps(sm, tp)
        self.assertEqual([d.code for d in sm.report.errors], ["next_cp.pair", "next_cp.pair"])


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
        self.assertNotIn("osCircuit", ix["appliances"]["9"].get("derived", {}))


class References(unittest.TestCase):
    """A qualified name for another interlocking's thing is one-sided, and the thing must exist (the owner, 2026-10-27).
    Interlocking Y is drawn on its own sheet; X's drawing names Y's things."""

    Y = """
IX2  | Interlocking     | STRUCTURE | Kind=INTERLOCKING Name=Y
P2   | Processor        | STRUCTURE | Kind=PROCESSOR Name=Beta Board=cpNode
H2   | House            | STRUCTURE | Kind=CONTROL_POINT CP_Name=West
SW5  | Switch_Lock      | APPLIANCE | Appliance=switch Style=lock Name=5 TC=5T1
SW6  | Switch_Lock      | APPLIANCE | Appliance=switch Style=derail Name=6
TC5  | Track Circuit    | APPLIANCE | Appliance=track_circuit Name=3NAT
J5   | IRJ              | TRACK     | Kind=IRJ
"""
    Y_NETS = """
y0   | IX2.Processor P2.Processor
y1   | SW5.C SW6.C
y2   | SW5.N J5.A
y3   | J5.B TC5.TC
"""
    X = """
H1   | House            | STRUCTURE | Kind=CONTROL_POINT CP_Name=East
J1   | IRJ              | TRACK     | Kind=IRJ
"""

    def compile_(self, refs: str, ref_nets: str):
        y = [replace(s, sheet="/Y/") for s in symbols(self.Y)]
        sm = seams.resolve(from_symbols(symbols(SCAFFOLD + self.X + refs) + y,
                                        nets("n0 | IX1.Processor P1.Processor\n" + self.Y_NETS + ref_nets)))
        return sm

    def test_a_reference_that_resolves_gives_no_diagnostic(self):
        sm = self.compile_("""
TC1  | Track Circuit    | APPLIANCE | Appliance=track_circuit Name=Y:3NAT
SW1  | Switch_Lock      | APPLIANCE | Appliance=switch Style=lock Name=Y:5
SW2  | Switch_Lock      | APPLIANCE | Appliance=switch Style=derail Name=Y:6
TC2  | Track Circuit    | APPLIANCE | Appliance=track_circuit Name=Y:5T1
""", "a | J1.A TC1.TC\nb | J1.B SW1.R SW2.R\nc | SW1.C TC2.TC\n")
        self.assertEqual(diags(sm, "reference"), [])
        self.assertEqual(sm.report.errors, [])

    def test_a_circuit_or_switch_the_named_interlocking_does_not_have_is_an_error(self):
        sm = self.compile_("""
TC1  | Track Circuit    | APPLIANCE | Appliance=track_circuit Name=Y:4NAT
SW1  | Switch_Lock      | APPLIANCE | Appliance=switch Style=lock Name=Y:7
SW2  | Switch_Lock      | APPLIANCE | Appliance=switch Style=lock Name=Y:3NAT
""", "a | J1.A TC1.TC\nb | J1.B SW1.R SW2.R\n")
        self.assertEqual(diags(sm, "reference"), [("reference.unresolved", "SW1"), ("reference.unresolved", "SW2"),
                                                  ("reference.unresolved", "TC1")])

    def test_a_port_the_named_switch_does_not_have_is_an_error(self):
        sm = self.compile_("""
SW2  | Switch_Lock      | APPLIANCE | Appliance=switch Style=lock Name=Y:6
""", "a | J1.A SW2.N\n")
        self.assertEqual(diags(sm, "reference"), [("reference.unresolved", "SW2")])
        self.assertIn("no port N", sm.report.by_code("reference.unresolved")[0].text)

    def test_a_circuit_named_in_a_field_must_exist_too(self):
        sm = self.compile_("""
SW1  | Switch_Lock      | APPLIANCE | Appliance=switch Style=lock Name=9 TC=Y:9T1 CP=East
TC1  | Track Circuit    | APPLIANCE | Appliance=track_circuit Style=virtual Name=1VT IndicationToken=Y:3NAT,Y:8NAT
""", "a | J1.A SW1.C\n")
        self.assertEqual(diags(sm, "reference"), [("reference.unresolved", "SW1"), ("reference.unresolved", "TC1")])

    def test_an_interlocking_not_in_the_file_is_a_warning(self):
        sm = self.compile_("""
TC1  | Track Circuit    | APPLIANCE | Appliance=track_circuit Name=Z:2NAT
""", "a | J1.A TC1.TC\n")
        self.assertEqual(diags(sm, "reference"), [("reference.interlocking", "TC1")])
        self.assertEqual(codes(sm, "warning"), ["reference.interlocking"])


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
        masts = [(i, n, a) for i, ix in self.model["interlockings"].items() for n, a in ix.get("appliances", {}).items() if a["given"]["Appliance"] == "mast"]
        self.assertEqual([(i, n) for i, n, a in masts if "controlPoint" not in a.get("derived", {})], [])
        joints = [j for ix in self.model["interlockings"].values() for j in ix.get("track", {}).get("joints", []) if j["given"]["Kind"] == "IRJ_SIGNAL"]
        self.assertEqual(len(joints), 35)
        self.assertEqual([j for j in joints if "mast" not in j.get("relations", {}) or "controlPoint" not in j["derived"]], [])
        self.assertEqual([j for j in joints if set(j["derived"].get("circuits", {})) - {"approach", "governed"}], [])

    def test_every_track_row_has_its_own_id(self):
        ids = [r["id"] for ix in self.model["interlockings"].values() for k in ("joints", "ends", "policies") for r in ix.get("track", {}).get(k, [])]
        self.assertEqual(len(ids), 56 + 35 + 18 + 5 + 3 + 3 + 29)
        self.assertEqual(len(set(ids)), len(ids))

    def test_every_appliance_has_its_control_point_and_no_chain_is_broken(self):
        self.assertEqual([d for d in self.sm.report.diags if d.code.startswith("control_point")], [])
        self.assertEqual([(i, n) for i, ix in self.model["interlockings"].items() for n, a in ix.get("appliances", {}).items()
                          if "controlPoint" not in a.get("derived", {})], [])

    def test_every_next_cp_names_where_it_leads_and_is_answered(self):
        ends = [(i, e["given"].get("Interlocking")) for i, ix in self.model["interlockings"].items() for e in ix["track"].get("ends", [])
                if e["given"]["Kind"] == "NEXT_CP"]
        self.assertEqual(len(ends), 18)
        self.assertEqual([e for e in ends if not e[1]], [])
        self.assertEqual(sorted(b for a, b in ends if a == "Christopher"), ["Corporal", "Corporal", "Luchessa", "Luchessa"])
        self.assertEqual(self.sm.report.by_code("next_cp.pair"), [])

    def test_luchessas_industry_is_what_end_ctcs_dark_pin_meets(self):
        ends = self.ix("Luchessa")["track"]["ends"]
        end_ctc = next(e for e in ends if e["relations"].get("DARK") == ["Luchessa:Gilroy Industry.EoT"])
        self.assertEqual((end_ctc["given"], end_ctc["derived"]), ({"Kind": "END_CTC"}, {"circuits": {"CTC": "Luchessa:02T"}}))
        industry = next(e for e in ends if e.get("name") == "Luchessa:Gilroy Industry")
        self.assertEqual((industry["given"], industry["relations"]), ({"Kind": "INDUSTRY"}, {"EoT": [f"{end_ctc['id']}.DARK"]}))

    def test_sargents_hot_box_alarm_states_its_milepost(self):
        self.assertEqual(self.ix("Sargent")["appliances"]["HBA"]["given"]["Milepost"], "83.4")

    def test_sargents_os_circuit_is_on_its_three_signal_joints(self):
        joints = [j for j in self.ix("Sargent")["track"]["joints"] if j["given"]["Kind"] == "IRJ_SIGNAL"]
        self.assertEqual(sorted((j["derived"]["circuits"]["governed"], j["relations"]["governed"][0]) for j in joints),
                         [("Sargent:835T1", "Sargent:835.C"), ("Sargent:835T1", "Sargent:835.N"), ("Sargent:835T1", "Sargent:835.R")])

    def test_luchessa_houses_and_its_derail(self):
        a = self.ix("Luchessa")["appliances"]
        self.assertEqual({n: a[n]["derived"]["controlPoint"] for n in ("783", "795", "795D", "799")},
                         {"783": "Luchessa:Luchessa", "795": "Luchessa:Gilroy", "795D": "Luchessa:Gilroy", "799": "Luchessa:Carnadero"})
        self.assertEqual(self.ix("Luchessa")["track"]["links"], [{"derived": {"ports": ["Luchessa:795.R", "Luchessa:795D.R"], "circuit": "Luchessa:795T1"}}])

    def test_every_track_relation_is_named_back_in_its_interlocking(self):
        """The owner, 2026-10-27: symmetric adjacency on the drawing. A reference to another interlocking's thing
        (``Corporal:2NAT.TC``) has no row here to name it back."""
        for name, ix in self.model["interlockings"].items():
            rel = {}
            for n, a in ix.get("appliances", {}).items():
                rel.update({f"{name}:{n}.{side}": v for side, v in a.get("relations", {}).items() if isinstance(v, list)})
            for kind in ("joints", "ends", "policies"):
                for r in ix.get("track", {}).get(kind, []):
                    rel.update({f"{r.get('name') or r['id']}.{side}": v for side, v in r.get("relations", {}).items() if isinstance(v, list)})
            own = [(a, b) for a, bs in rel.items() for b in bs if not (":" in b and not b.startswith(f"{name}:"))]
            self.assertEqual([(a, b) for a, b in own if a not in rel.get(b, [])], [], name)
            self.assertEqual([a for a, bs in rel.items() if any(b.rsplit(".", 1)[0] == a.rsplit(".", 1)[0] for b in bs)], [], name)

    def test_no_circuit_carries_two_names(self):
        self.assertEqual(self.sm.report.by_code("circuit.names") + self.sm.report.by_code("circuit.name.disagree"), [])


if __name__ == "__main__":
    unittest.main()
