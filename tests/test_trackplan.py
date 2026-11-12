"""Scenarios for the KiCad importer's trackplan piece (semantics handoff item 2; ADR 0010 §4.1, C6; ADR 0011's three maps).

Each scenario's Given is a netlist fragment in relational form: a table of symbols with their fields, a table of
nets with their member pins. Its Then is a table of what the Layout Data Model File says. No fixture file: the
tables are the scenario. What is tested here is the importer's part: pins translated to sides, wires to
``relations``, fields to ``given``, ids, and the diagnostics about the drawing as drawn. What the rules derive from
those (circuits, control points, links, NextCP pairing, references) is tested on files alone in ``test_derive``; the
scenarios here still read ``derived`` where it shows that the importer stated enough. The SPCoast project is the
integration gate, in ``SPCoastTrackplan`` below.
"""
from __future__ import annotations

import json
import shlex
import unittest
from collections import Counter

from tools import layout_model
from tools.layout_compiler import emit, seams
from tools.layout_compiler.source import Net, PinRef, Symbol, from_symbols
from tools.railroad import codeline
from tests.test_layout_compiler import NETLIST, PROJECT, SPCOAST_AVAILABLE, spcoast_source

SHEET = "/X/"
# The interlocking every scenario stands in: its declaration, its processor and its houses are scaffolding.
SCAFFOLD = """
IX1  | Interlocking | STRUCTURE | Kind=INTERLOCKING Name=X
P1   | Processor    | STRUCTURE | Kind=PROCESSOR Name=Alpha Board=cpNode
"""


def symbols(table: str, sheet: str = SHEET) -> list[Symbol]:
    """Rows of ``ref | library symbol | Role | Field=value ...`` (a value with spaces in double quotes)."""
    out = []
    for line in filter(str.strip, table.splitlines()):
        ref, lib, role, fields = (c.strip() for c in line.split("|"))
        kv = {}
        for tok in shlex.split(fields):
            k, _, v = tok.partition("=")
            kv[k.replace("_", " ")] = v
        out.append(Symbol(ref, f"Railroad-Trackplan:{lib}", "", {"Role": role, **kv}, sheet))
    return out


def nets(table: str) -> list[Net]:
    """Rows of ``net | REF.pin REF.pin ...``; ``REF.UNIT.pin`` is a pin drawn in a named unit."""
    out = []
    for line in filter(str.strip, table.splitlines()):
        name, members = (c.strip() for c in line.split("|"))
        out.append(Net(name, tuple(_pin(m) for m in members.split())))
    return out


def _pin(text: str) -> PinRef:
    parts = text.split(".")
    return PinRef(parts[0], parts[2], unit=parts[1]) if len(parts) == 3 else PinRef(parts[0], parts[1])


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
    return sorted(((d.code, (d.where or d.source).split(" ")[0].rsplit("/", 1)[-1]) for d in sm.report.diags if d.code.startswith(prefixes)))


# One switch inside three signal joints of house East: the Sargent shape.
ONE_SWITCH = """
H1   | House            | STRUCTURE | Kind=CONTROL_POINT CP_Name=East
SW1  | Switch_Lock      | APPLIANCE | Appliance=switch Style=lock Name=835 TC=835T1 CP_Name=East
J1   | IRJ-Signal       | TRACK     | Kind=IRJ_SIGNAL CP_Name=East
J2   | IRJ-Signal       | TRACK     | Kind=IRJ_SIGNAL CP_Name=East
J3   | IRJ-Signal       | TRACK     | Kind=IRJ_SIGNAL CP_Name=East
M1   | Mast_Double      | APPLIANCE | Appliance=mast Style=double Kind=CONTROLLED Name=836NAB
M2   | Mast_Single      | APPLIANCE | Appliance=mast Style=single Kind=CONTROLLED Name=836SA
M3   | Mast_Dwarf       | APPLIANCE | Appliance=mast Style=dwarf Kind=CONTROLLED Name=836SB
HA   | Signal Head - CPL | APPLIANCE | Appliance=head Style=CPL Name=A
HB   | Signal Head - CPL | APPLIANCE | Appliance=head Style=CPL Name=B
HC   | Signal Head - CL  | APPLIANCE | Appliance=head Style=CL Name=A
HD   | Signal Head - Semaphore-UQ | APPLIANCE | Appliance=head Style=UQ Name=B
TC1  | Track Circuit    | APPLIANCE | Appliance=track_circuit Name=1NAT CP_Name=East
TC2  | Track Circuit    | APPLIANCE | Appliance=track_circuit Name=1SAT CP_Name=East
TC3  | Track Circuit    | APPLIANCE | Appliance=track_circuit Name=2SAT CP_Name=East
NX1  | NextCP           | TRACK     | Kind=NEXT_CP
R1   | GCOR Rule 9.14 DoT_Right | POLICY | Kind=GCOR_RULE_9_14 Direction=RIGHT
"""
ONE_SWITCH_NETS = """
c    | SW1.C J1.A
n    | SW1.N J2.A
r    | SW1.R J3.A
w    | J1.B TC1.TC NX1.To R1.To
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
        self.assertEqual(rows(ix, "policies"), [{"given": {"Kind": "GCOR_RULE_9_14", "Direction": "RIGHT"}, "derived": {"circuits": {"track": "X:1NAT"}},
                                                 "relations": {"track": sorted([at(sm, "J1", "approach"), at(sm, "NX1", "track"), "X:1NAT.TC"])}}])

    def test_a_signal_joints_sides_are_approach_and_governed(self):
        """ADR 0012 §8 and the table's D15: the governed side is the symbol's A pin, where the route it protects begins;
        the approach side its B pin. Its wires and its circuits use the same names; A and B appear nowhere."""
        sm, ix = compile_(ONE_SWITCH, ONE_SWITCH_NETS)
        j = next(j for j in ix["track"]["joints"] if j["relations"]["mast"] == "X:836SA")
        self.assertEqual(j["relations"], {"governed": ["X:835.N"], "approach": ["X:1SAT.TC"], "mast": "X:836SA"})
        self.assertEqual(j["derived"], {"circuits": {"governed": "X:835T1", "approach": "X:1SAT"}, "controlPoint": "X:East"})
        self.assertEqual(j["given"], {"Kind": "IRJ_SIGNAL", "CP Name": "East"})

    def test_a_policy_signs_and_a_next_cps_pin_is_the_track_side(self):
        """Every sign and a NextCP draw their one pin as To; the model names the side track: one meaning, one side
        name (D15). A regime marker and the current-of-traffic sign are read alike."""
        given = """
H1   | House           | STRUCTURE | Kind=CONTROL_POINT CP_Name=East
TC1  | Track Circuit   | APPLIANCE | Appliance=track_circuit Name=1NAT
R1   | GCOR Rule 6.13 Yard Limits | POLICY | Kind=GCOR_RULE_6_13
R2   | GCOR Rule 9.14 DoT_Right | POLICY | Kind=GCOR_RULE_9_14 Direction=RIGHT
NX1  | NextCP          | TRACK     | Kind=NEXT_CP Interlocking=Lick
"""
        sm, ix = compile_(given, "w | TC1.TC R1.To R2.To NX1.To\n")
        self.assertEqual({str(r["derived"]) for r in ix["track"]["policies"] + ix["track"]["ends"]}, {str({"circuits": {"track": "X:1NAT"}})})

    def test_every_track_row_carries_its_symbols_uuid_as_its_id(self):
        """The table's D10: a row's identity is opaque and stable, the KiCad per-instance UUID of its symbol."""
        sm, ix = compile_(ONE_SWITCH, ONE_SWITCH_NETS)
        by_ref = {s.ref: s.uuid for s in sm.source.symbols.values()}
        ids = [r["id"] for kind in ("joints", "ends", "policies") for r in ix["track"][kind]]
        self.assertEqual(sorted(ids), sorted(by_ref[r] for r in ("J1", "J2", "J3", "NX1", "R1")))

    def test_dark_track_has_no_circuit_and_an_end_names_the_port_it_meets(self):
        """Track beyond a plain joint with nothing to name it has no circuit (ADR 0013 §7.1: a regime boundary is a
        plain IRJ; the END_CTC end is retired)."""
        given = """
H1   | House           | STRUCTURE | Kind=CONTROL_POINT CP_Name=East
SW1  | Switch_Manual   | APPLIANCE | Appliance=switch Style=manual Name=1
J1   | IRJ             | TRACK     | Kind=IRJ
TC1  | Track Circuit   | APPLIANCE | Appliance=track_circuit Name=2SAT
I1   | Industry        | TRACK     | Kind=INDUSTRY
I2   | Industry        | TRACK     | Kind=INDUSTRY
"""
        sm, ix = compile_(given, """
ctc  | J1.B TC1.TC
dark | J1.A SW1.C
in   | I1.EoT SW1.N
ir   | I2.EoT SW1.R
""")
        self.assertEqual(sm.report.errors, [])
        self.assertEqual(rows(ix, "joints"), [{"given": {"Kind": "IRJ"}, "derived": {"circuits": {"B": "X:2SAT"}}, "relations": {"A": ["X:1.C"], "B": ["X:2SAT.TC"]}}])
        self.assertEqual(sorted_rows(rows(ix, "ends")), sorted_rows([
            {"given": {"Kind": "INDUSTRY"}, "relations": {"EoT": ["X:1.N"]}},
            {"given": {"Kind": "INDUSTRY"}, "relations": {"EoT": ["X:1.R"]}},
        ]))
        self.assertNotIn("osCircuit", ix["appliances"]["1"].get("derived", {}))

    def test_unnamed_rows_on_dark_track_name_each_other_by_id(self):
        """The owner, 2026-10-27: a track pin's relations name every row or port its wire reaches, unnamed rows by id.
        Two unnamed rows on dark track with nothing between them state their connection; nothing is reported."""
        given = """
H1   | House           | STRUCTURE | Kind=CONTROL_POINT CP_Name=East
J1   | IRJ             | TRACK     | Kind=IRJ
B1   | Bumper          | TRACK     | Kind=BUMPER
"""
        sm, ix = compile_(given, "dark | J1.A B1.EoT\n")
        self.assertEqual(sm.report.errors, [])
        self.assertEqual(diags(sm, "track"), [])
        rel = track_relations(ix)
        self.assertEqual(rel[at(sm, "J1", "A")], [at(sm, "B1", "EoT")])
        self.assertEqual(rel[at(sm, "B1", "EoT")], [at(sm, "J1", "A")])

    def test_a_derail_joins_its_switchs_circuit_and_ports_that_meet_are_a_link(self):
        given = """
H1   | House           | STRUCTURE | Kind=CONTROL_POINT CP_Name=Gilroy
SW1  | Switch_Lock     | APPLIANCE | Appliance=switch Style=lock Name=795 TC=795T1 CP_Name=Gilroy
D1   | Derail          | APPLIANCE | Appliance=switch Style=derail,powered Name=795D IndicationCeiling=STOP/RESTRICTING CP_Name=Gilroy
J1   | IRJ-Signal      | TRACK     | Kind=IRJ_SIGNAL CP_Name=Gilroy
"""
        sm, ix = compile_(given, """
rr   | SW1.R D1.R
dc   | D1.C J1.A
""")
        self.assertEqual(sm.report.errors, [])
        self.assertEqual(ix["track"]["links"], [{"derived": {"ports": ["X:795.R", "X:795D.R"], "circuit": "X:795T1"}}])
        self.assertEqual(ix["track"]["joints"][0]["derived"]["circuits"], {"governed": "X:795T1"})
        self.assertEqual(ix["appliances"]["795D"], {
            "given": {"Appliance": "switch", "Style": "derail,powered", "IndicationCeiling": "STOP/RESTRICTING", "CP Name": "Gilroy"},
            "relations": {"C": [at(sm, "J1", "governed")], "R": ["X:795.R"]},
            "derived": {"track": "X:795T1", "circuits": {"track": "X:795T1"}, "controlPoint": "X:Gilroy"}})   # no OS circuit of its own: it lies in its switch's (the owner, 2026-11-09)

    def test_a_marker_named_for_another_interlockings_circuit_is_a_consumer_row_its_neighbours_name_by_id(self):
        """The owner, 2026-10-27: Sargent's Corporal:2NAT consumes Corporal's indication 2NATK; the K is added at ingest
        and the drawing is not edited. Its neighbours name it like any local row, by its id."""
        given = """
H1   | House           | STRUCTURE | Kind=CONTROL_POINT CP_Name=East
J1   | IRJ             | TRACK     | Kind=IRJ
TC1  | Track Circuit   | APPLIANCE | Appliance=track_circuit Name=Corporal:2NAT CP_Name=Corporal
TC2  | Track Circuit   | APPLIANCE | Appliance=track_circuit Name=1SAT CP_Name=East
"""
        sm, ix = compile_(given, "a | J1.A TC1.TC\nb | J1.B TC2.TC\n")
        self.assertEqual(sm.report.errors, [])
        self.assertEqual(rows(ix, "joints"), [{"given": {"Kind": "IRJ"}, "derived": {"circuits": {"B": "X:1SAT"}},
                                               "relations": {"A": [at(sm, "TC1", "TC")], "B": ["X:1SAT.TC"]}}])
        self.assertEqual(rows(ix, "consumers"), [{"given": {"Appliance": "track_circuit", "Name": "Corporal:2NAT", "CP Name": "Corporal"},
                                                  "relations": {"TC": [at(sm, "J1", "A")], "indication": "Corporal:2NATK"}}])
        self.assertEqual(sorted(ix["appliances"]), ["1SAT"])
        self.assertEqual(diags(sm, "reference"), [("reference.interlocking", "{}".format(sm.source.symbols["TC1"].uuid))])
        self.assertEqual(layout_model.errors(emit.emit(sm)), [])



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
SW1  | Switch_Powered   | APPLIANCE | Appliance=switch Style=powered Name=813 TC=813T1 CP_Name=North
SW2  | Switch_Powered   | APPLIANCE | Appliance=switch Style=powered Name=815 TC=815T1 CP_Name=North
SW3  | Switch_Powered   | APPLIANCE | Appliance=switch Style=powered Name=815A TC=815AT1
SW4  | Switch_Powered   | APPLIANCE | Appliance=switch Style=powered Name=817 TC=817T1 CP_Name=South
J1   | IRJ-Signal       | TRACK     | Kind=IRJ_SIGNAL CP_Name=North
J2   | IRJ-Signal       | TRACK     | Kind=IRJ_SIGNAL
J3   | IRJ-Signal       | TRACK     | Kind=IRJ_SIGNAL CP_Name=South
M1   | Mast_Single      | APPLIANCE | Appliance=mast Style=single Name=814SA
M2   | Mast_Single      | APPLIANCE | Appliance=mast Style=single Name=816NA CP_Name=South
M3   | Mast_Single      | APPLIANCE | Appliance=mast Style=single Name=818NA
Q1   | IRJ              | TRACK     | Kind=IRJ
Q2   | IRJ              | TRACK     | Kind=IRJ
Q3   | IRJ              | TRACK     | Kind=IRJ
Q4   | IRJ              | TRACK     | Kind=IRJ
TC1  | Track Circuit    | APPLIANCE | Appliance=track_circuit Name=1SAT
TC2  | Track Circuit    | APPLIANCE | Appliance=track_circuit Name=01T CP_Name=North
TC3  | Track Circuit    | APPLIANCE | Appliance=track_circuit Name=2NAT
TC4  | Track Circuit    | APPLIANCE | Appliance=track_circuit Name=1NAT CP_Name=North
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
    """The facts control point propagation reads, as the importer states them (the rule itself: ``test_derive``)."""

    def test_the_one_house_is_every_appliances_control_point(self):
        """Approach circuits included: a control point is the house whose field unit wires the appliance, not the
        routes its signals protect."""
        sm, ix = compile_("\n".join(l if "| House" in l else l.replace(" CP_Name=East", "") for l in ONE_SWITCH.split("\n")), ONE_SWITCH_NETS)
        self.assertEqual(sm.report.errors, [])
        self.assertEqual(control_points(ix), {n: "East" for n in ("835", "836NAB", "836SA", "836SB", "1NAT", "1SAT", "2SAT")})
        self.assertEqual({j["derived"]["controlPoint"] for j in ix["track"]["joints"]}, {"X:East"})
        self.assertEqual(ix["appliances"]["836NAB"]["heads"], {"A": {"given": {"Appliance": "head", "Style": "CPL"}},
                                                               "B": {"given": {"Appliance": "head", "Style": "CPL"}}})
        self.assertEqual(ix["appliances"]["836SB"]["heads"], {"B": {"given": {"Appliance": "head", "Style": "UQ"}}})
        self.assertNotIn("CP Name", ix["appliances"]["835"]["given"])          # stated nowhere: derived, never written as given

    def test_two_appliances_with_one_name_are_an_error(self):
        sm, _ = compile_(ONE_SWITCH.replace("Name=836SA", "Name=836NAB"), ONE_SWITCH_NETS)
        self.assertIn("appliance.duplicate", codes(sm, "error"))

    def test_a_maintainer_call_and_its_house_each_state_their_end_of_the_wire(self):
        given = """
H1   | House           | STRUCTURE | Kind=CONTROL_POINT CP_Name=East
H2   | House           | STRUCTURE | Kind=CONTROL_POINT CP_Name=West
MC1  | MaintainerCall  | APPLIANCE | Appliance=lamp Style=maintainer_call Name=MC1
"""
        sm, ix = compile_(given, "mc | H2.MC MC1.MC\n")
        self.assertEqual(control_points(ix), {"MC1": "West"})
        self.assertEqual(ix["appliances"]["MC1"]["relations"], {"house": "X:West"})          # each holder writes its end (D8)
        self.assertEqual(ix["houses"]["West"]["relations"], {"maintainerCall": "X:MC1"})

    def test_a_virtual_circuit_lists_its_members_and_follows_them(self):
        given = TWO_HOUSES + "V1 | Track Circuit_Virtual | APPLIANCE | Appliance=track_circuit Style=virtual Name=0100T Members=1SAT,01T\n"
        sm, ix = compile_(given, TWO_HOUSES_NETS)
        self.assertEqual(sm.report.errors, [])
        self.assertEqual(ix["appliances"]["0100T"], {
            "given": {"Appliance": "track_circuit", "Style": "virtual", "Members": "1SAT,01T"},
            "derived": {"members": ["X:1SAT", "X:01T"], "controlPoint": "X:North"}})

    def test_the_output_validates(self):
        for given, nets_ in ((ONE_SWITCH, ONE_SWITCH_NETS), (TWO_HOUSES, TWO_HOUSES_NETS)):
            sm, _ = compile_(given, nets_)
            self.assertEqual(layout_model.errors(emit.emit(sm)), [])


class OnTheTrack(unittest.TestCase):
    """A lamp's, contact's or actuator's one pin (#82): the track pins on its wire, the piece of track the derivation
    then places it on, the maintainer-call wire, and the one pin that is an error. Track with no circuit is track like
    any other (the owner, 2026-11-09)."""

    def test_through_a_switch_port_the_piece_is_named_by_the_switchs_os_circuit(self):
        given = ONE_SWITCH + "K1 | Sensor | APPLIANCE | Appliance=contact Name=HTR\n"
        sm, ix = compile_(given, ONE_SWITCH_NETS.replace("r    | SW1.R J3.A", "r    | SW1.R J3.A K1.SENSOR"))
        htr = ix["appliances"]["HTR"]
        self.assertIn("X:835.R", htr["relations"]["track"])
        self.assertEqual((htr["derived"]["track"], htr["derived"]["circuits"]), ("X:835T1", {"track": "X:835T1"}))
        self.assertEqual(diags(sm, "appliance"), [])

    def test_the_three_appliances_read_alike_whatever_their_pin_is_called(self):
        given = ONE_SWITCH + """
K1   | Sensor   | APPLIANCE | Appliance=contact Name=HTR
L1   | Lamp     | APPLIANCE | Appliance=lamp Name=NFL
A1   | Actuator | APPLIANCE | Appliance=actuator Name=HTR2
"""
        sm, ix = compile_(given, ONE_SWITCH_NETS.replace("e1   | J2.B TC2.TC", "e1   | J2.B TC2.TC K1.SENSOR L1.LAMP A1.ACTUATOR"))
        on = {n: ix["appliances"][n] for n in ("HTR", "NFL", "HTR2")}
        self.assertEqual({n: a["derived"]["track"] for n, a in on.items()}, {"HTR": "X:1SAT", "NFL": "X:1SAT", "HTR2": "X:1SAT"})
        self.assertEqual(len({tuple(a["relations"]["track"]) for a in on.values()}), 1)            # the same track pins, none of them another appliance's pin
        self.assertIn("X:1SAT.TC", on["HTR"]["relations"]["track"])
        self.assertEqual(ix["appliances"]["1SAT"]["relations"]["TC"], compile_(ONE_SWITCH, ONE_SWITCH_NETS)[1]["appliances"]["1SAT"]["relations"]["TC"])   # one-sided: no track pin names them back
        self.assertEqual(on["HTR2"]["given"], {"Appliance": "actuator"})
        self.assertEqual(layout_model.errors(emit.emit(sm)), [])

    def test_track_with_no_circuit_is_track_and_the_piece_gets_a_name(self):
        given = ONE_SWITCH + """
L1   | Lamp          | APPLIANCE | Appliance=lamp Name=NFL
L2   | Lamp          | APPLIANCE | Appliance=lamp Name=SFL
J9   | IRJ           | TRACK     | Kind=IRJ
I9   | Industry      | TRACK     | Kind=INDUSTRY Name=BeetLoader
"""
        sm, ix = compile_(given, ONE_SWITCH_NETS + "dark | J9.A L1.LAMP\nspur | J9.B I9.EoT L2.LAMP\n")
        nfl, sfl = ix["appliances"]["NFL"], ix["appliances"]["SFL"]
        self.assertEqual(sfl["derived"], {**sfl["derived"], "track": "X:BeetLoader"})          # an industry end names its track
        self.assertTrue(nfl["derived"]["track"].startswith("track@"))                          # nobody named this piece
        self.assertNotIn("circuits", nfl["derived"])
        self.assertNotIn("circuits", sfl["derived"])
        self.assertEqual(diags(sm, "appliance"), [("appliance.track.unnamed", "NFL")])        # information; no import error
        self.assertEqual(layout_model.errors(emit.emit(sm)), [])

    def test_a_maintainer_call_on_its_house_is_no_error_and_a_lamp_on_a_signal_wire_or_a_houses_codeline_pin_is(self):
        given = ONE_SWITCH + """
MC1  | MaintainerCall | APPLIANCE | Appliance=lamp Style=maintainer_call Name=1MC
L1   | Lamp           | APPLIANCE | Appliance=lamp Name=NFL
L2   | Lamp           | APPLIANCE | Appliance=lamp Name=SFL
"""
        sm, ix = compile_(given, ONE_SWITCH_NETS.replace("s1   | J1.SIGNAL M1.SIGNAL", "s1   | J1.SIGNAL M1.SIGNAL L1.LAMP")
                          + "mc | H1.MC MC1.MC\ncl | H1.Codeline L2.LAMP\n")
        self.assertEqual(ix["appliances"]["1MC"]["relations"], {"house": "X:East"})
        self.assertEqual([ix["appliances"][n].get("relations") for n in ("NFL", "SFL")], [None, None])
        self.assertEqual(diags(sm, "appliance"), [("appliance.track_pin", "L1"), ("appliance.track_pin", "L2")])


class Attributes(unittest.TestCase):
    def test_an_appliance_states_its_milepost(self):
        given = """
H1   | House           | STRUCTURE | Kind=CONTROL_POINT CP_Name=East
L1   | AUXILIARY       | APPLIANCE | Appliance=lamp Name=HBA Milepost=83.4
L2   | AUXILIARY       | APPLIANCE | Appliance=lamp Name=NFLK Milepost=north
"""
        sm, ix = compile_(given, "")
        self.assertEqual(ix["appliances"]["HBA"], {"given": {"Appliance": "lamp", "Milepost": "83.4"},
                                                   "derived": {"controlPoint": "X:East"}})
        self.assertEqual(diags(sm, "milepost"), [("milepost.number", "L2")])

    def test_every_stated_field_lands_in_given_as_drawn(self):
        """A field nothing reads is kept, never dropped (the owner, 2026-10-26; ADR 0011 §2)."""
        given = """
H1   | House           | STRUCTURE | Kind=CONTROL_POINT CP_Name=East
L1   | AUXILIARY       | APPLIANCE | Appliance=lamp Name=NFLK Display="North flasher" Column=7
"""
        sm, ix = compile_(given, "")
        self.assertEqual(ix["appliances"]["NFLK"]["given"], {"Appliance": "lamp", "Display": "North flasher", "Column": "7"})

    def test_an_empty_indication_is_stated_and_any_other_empty_field_is_absent(self):
        """An empty token field says there is deliberately no token; an absent one is not done yet (ADR 0008 §4.7)."""
        given = """
H1   | House           | STRUCTURE | Kind=CONTROL_POINT CP_Name=East
L1   | AUXILIARY       | APPLIANCE | Appliance=lamp Name=HBA Indication= Milepost=
L2   | AUXILIARY       | APPLIANCE | Appliance=lamp Name=NFL
"""
        sm, ix = compile_(given, "")
        self.assertEqual(ix["appliances"]["HBA"]["given"], {"Appliance": "lamp", "Indication": ""})
        self.assertEqual(ix["appliances"]["NFL"]["given"], {"Appliance": "lamp"})


class Ends(unittest.TestCase):
    def test_a_named_end_is_what_a_dark_pin_meets(self):
        """Luchessa's shape (Railroad 0ddd395): a regime boundary, a plain IRJ with END CTC on the circuit side and
        Rule 6.28 beyond, and the industry on the far side with no switch and no circuit between them."""
        given = """
H1   | House           | STRUCTURE | Kind=CONTROL_POINT CP_Name=East
J1   | IRJ             | TRACK     | Kind=IRJ
R1   | GCOR Rule 10 END_CTC | POLICY | Kind=GCOR_RULE_10
R2   | GCOR Rule 6.28 RestrictedSpeed | POLICY | Kind=GCOR_RULE_6_28
TC1  | Track Circuit   | APPLIANCE | Appliance=track_circuit Name=02T
I1   | Industry        | TRACK     | Kind=INDUSTRY Name="Gilroy Industry"
"""
        sm, ix = compile_(given, "ctc | J1.B TC1.TC R1.To\ndark | J1.A R2.To I1.EoT\n")
        self.assertEqual(sm.report.errors, [])
        self.assertEqual(rows(ix, "joints"), [{"given": {"Kind": "IRJ"}, "derived": {"circuits": {"B": "X:02T"}},
                                               "relations": {"A": sorted([at(sm, "R2", "track"), "X:Gilroy Industry.EoT"]), "B": sorted([at(sm, "R1", "track"), "X:02T.TC"])}}])
        self.assertEqual(rows(ix, "ends"), [{"name": "X:Gilroy Industry", "given": {"Kind": "INDUSTRY"}, "relations": {"EoT": sorted([at(sm, "J1", "A"), at(sm, "R2", "track")])}}])
        self.assertEqual(sorted_rows(rows(ix, "policies")), sorted_rows([
            {"given": {"Kind": "GCOR_RULE_10"}, "derived": {"circuits": {"track": "X:02T"}}, "relations": {"track": sorted([at(sm, "J1", "B"), "X:02T.TC"])}},
            {"given": {"Kind": "GCOR_RULE_6_28"}, "relations": {"track": sorted([at(sm, "J1", "A"), "X:Gilroy Industry.EoT"])}},
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
NX3  | NextCP          | TRACK     | Kind=NEXT_CP Interlocking=Hollister Style=off_layout
"""
        sm, ix = compile_(given, "")
        self.assertEqual(sorted_rows(rows(ix, "ends")), sorted_rows([{"given": {"Kind": "NEXT_CP", "Interlocking": "Lick"}}, {"given": {"Kind": "NEXT_CP"}},
                                                                     {"given": {"Kind": "NEXT_CP", "Interlocking": "Hollister", "Style": "off_layout"}}]))
        self.assertEqual(diags(sm, "next_cp.off_layout", "next_cp.drawn_neighbour"), [("next_cp.off_layout", "X")])    # Lick unmarked; Hollister marked (ADR 0013 §21 gap 7)


# A signal location in a block (ADR 0013 §6): one double joint with a mast on each side, 832T on side A and 834T on B.
DOUBLE_JOINT = """
H1   | House                         | STRUCTURE | Kind=CONTROL_POINT CP_Name=East
TC1  | Track Circuit                 | APPLIANCE | Appliance=track_circuit Name=832T
TC2  | Track Circuit                 | APPLIANCE | Appliance=track_circuit Name=834T
J1   | IRJ-Signals                   | TRACK     | Kind=IRJ_SIGNALS
M1   | Signal Mast Single PERMISSIVE | APPLIANCE | Appliance=mast Style=single Kind=PERMISSIVE Name=832NA
M2   | Signal Mast Single PERMISSIVE | APPLIANCE | Appliance=mast Style=single Kind=PERMISSIVE Name=832SA
"""
DOUBLE_JOINT_NETS = """
a    | J1.A TC1.TC
b    | J1.B TC2.TC
sa   | J1.SIGNAL_A M1.SIGNAL
sb   | J1.SIGNAL_B M2.SIGNAL
"""


class DoubleJoint(unittest.TestCase):
    """ADR 0013 §6: IRJ_SIGNALS joins the joints. Its sides keep their names A and B; SIGNAL_A and SIGNAL_B carry its
    masts, stated as relations.masts, and are no track pins. Nothing is read from rotation."""

    def test_a_double_joint_states_a_mast_on_each_side_and_its_sides_are_a_and_b(self):
        sm, ix = compile_(DOUBLE_JOINT, DOUBLE_JOINT_NETS)
        self.assertEqual(sm.report.errors, [])
        self.assertEqual(rows(ix, "joints"), [{"given": {"Kind": "IRJ_SIGNALS"},
                                               "relations": {"A": ["X:832T.TC"], "B": ["X:834T.TC"], "masts": {"A": "X:832NA", "B": "X:832SA"}},
                                               "derived": {"circuits": {"A": "X:832T", "B": "X:834T"}}}])
        self.assertEqual(diags(sm, "joint", "track.kind", "mast"), [])
        self.assertEqual(layout_model.errors(emit.emit(sm)), [])

    def test_each_mast_derives_its_governed_side_from_its_pin_and_its_approach_from_the_other(self):
        _, ix = compile_(DOUBLE_JOINT, DOUBLE_JOINT_NETS)
        self.assertEqual(ix["appliances"]["832NA"]["derived"]["circuits"], {"governed": "X:832T", "approach": "X:834T"})
        self.assertEqual(ix["appliances"]["832SA"]["derived"]["circuits"], {"governed": "X:834T", "approach": "X:832T"})

    def test_two_masts_on_one_signal_pin_are_an_error_and_a_side_with_none_is_absent(self):
        sm, ix = compile_(DOUBLE_JOINT, DOUBLE_JOINT_NETS.replace("sa   | J1.SIGNAL_A M1.SIGNAL", "sa   | J1.SIGNAL_A M1.SIGNAL M2.SIGNAL")
                          .replace("sb   | J1.SIGNAL_B M2.SIGNAL\n", ""))
        self.assertEqual(diags(sm, "joint"), [("joint.masts", "J1")])
        self.assertNotIn("masts", rows(ix, "joints")[0]["relations"])
        sm, ix = compile_(DOUBLE_JOINT, DOUBLE_JOINT_NETS.replace("sb   | J1.SIGNAL_B M2.SIGNAL\n", ""))
        self.assertEqual(diags(sm, "joint"), [])
        self.assertEqual(rows(ix, "joints")[0]["relations"]["masts"], {"A": "X:832NA"})


class AcrossSheets(unittest.TestCase):
    """ADR 0013 §7.1: block track is drawn from one control point to the next, across sheets; a hierarchical label
    continues the run and pairing comes from the netlist. A track net is read across sheets: each side names the other's
    pins by their own interlocking (a marker by qualified name, an unnamed row by its id). The Corporal to Sargent shape:
    834T is drawn on Y's sheet and reaches X's double joint through the label."""

    X = """
H1   | House            | STRUCTURE | Kind=CONTROL_POINT CP_Name=East
J1   | IRJ-Signals      | TRACK     | Kind=IRJ_SIGNALS
M1   | Mast_Single      | APPLIANCE | Appliance=mast Style=single Kind=PERMISSIVE Name=834NA
M2   | Mast_Single      | APPLIANCE | Appliance=mast Style=single Kind=PERMISSIVE Name=834SA
TC1  | Track Circuit    | APPLIANCE | Appliance=track_circuit Name=836T
"""
    Y = """
IX2  | Interlocking     | STRUCTURE | Kind=INTERLOCKING Name=Y
P2   | Processor        | STRUCTURE | Kind=PROCESSOR Name=Beta Board=cpNode
H2   | House            | STRUCTURE | Kind=CONTROL_POINT CP_Name=West
J2   | IRJ              | TRACK     | Kind=IRJ
TC2  | Track Circuit    | APPLIANCE | Appliance=track_circuit Name=834T
"""
    NETS = """
ToX  | J1.A TC2.TC J2.B
b    | J1.B TC1.TC
s1   | J1.SIGNAL_A M1.SIGNAL
s2   | J1.SIGNAL_B M2.SIGNAL
n1   | IX2.Processor P2.Processor
"""

    def setUp(self):
        syms = symbols(SCAFFOLD + self.X) + symbols(self.Y, "/Y/")
        self.sm = seams.resolve(from_symbols(syms, nets("n0 | IX1.Processor P1.Processor\n" + self.NETS)))
        self.model = emit.emit(self.sm)
        self.x, self.y = self.model["interlockings"]["X"], self.model["interlockings"]["Y"]

    def test_each_side_names_the_other_sheets_pins_by_their_own_interlocking(self):
        (j1,) = self.x["track"]["joints"]
        (j2,) = self.y["track"]["joints"]
        self.assertEqual(j1["relations"]["A"], [at(self.sm, "J2", "B"), "Y:834T.TC"])
        self.assertEqual(j1["relations"]["B"], ["X:836T.TC"])
        self.assertEqual(self.y["appliances"]["834T"]["relations"]["TC"], sorted([at(self.sm, "J1", "A"), at(self.sm, "J2", "B")]))
        self.assertEqual(j2["relations"]["B"], sorted([at(self.sm, "J1", "A"), "Y:834T.TC"]))
        self.assertEqual(j1["relations"]["masts"], {"A": "X:834NA", "B": "X:834SA"})
        self.assertEqual(diags(self.sm, "track", "joint", "appliance"), [])

    def test_the_other_sheets_marker_names_the_circuit_on_this_side_and_no_reference_is_raised(self):
        """The reference derivation's part (ADR 0013 §7.1): plain track across sheets is block track, Y's 834T names X's
        side A, and 834NA governs over it."""
        (j1,) = self.x["track"]["joints"]
        self.assertEqual(j1["derived"]["circuits"], {"A": "Y:834T", "B": "X:836T"})
        self.assertEqual(self.x["appliances"]["834NA"]["derived"]["circuits"], {"governed": "Y:834T", "approach": "X:836T"})
        self.assertEqual(self.x["appliances"]["834SA"]["derived"]["circuits"], {"governed": "X:836T", "approach": "Y:834T"})
        self.assertEqual(self.y["track"]["joints"][0]["derived"]["circuits"], {"B": "Y:834T"})
        self.assertEqual(diags(self.sm, "reference", "circuit"), [])
        self.assertNotIn("consumers", self.x["track"])


class Boundary(unittest.TestCase):
    """ADR 0013 §10: a boundary track circuit is a detector at a joint, Appliance track_circuit with Style boundary, its
    A and B on the two nets there. It is an appliance with relations.A and .B; it names no circuit (the marker on each
    net does), and its derived circuits are what it counts toward, in A, B order."""

    BOUNDARY = "TC3  | Track Circuit IR Boundary | APPLIANCE | Appliance=track_circuit Style=boundary Name=833T Indication=833TK\n"
    NETS = DOUBLE_JOINT_NETS.replace("a    | J1.A TC1.TC", "a    | J1.A TC1.TC TC3.A").replace("b    | J1.B TC2.TC", "b    | J1.B TC2.TC TC3.B")

    def test_a_boundary_is_an_appliance_on_the_two_nets_at_its_joint_and_names_no_circuit(self):
        sm, ix = compile_(DOUBLE_JOINT + self.BOUNDARY, self.NETS)
        self.assertEqual(sm.report.errors, [])
        self.assertEqual(ix["appliances"]["833T"], {
            "given": {"Appliance": "track_circuit", "Style": "boundary", "Indication": "833TK"},
            "relations": {"A": sorted([at(sm, "J1", "A"), "X:832T.TC"]), "B": sorted([at(sm, "J1", "B"), "X:834T.TC"])},
            "derived": {"circuits": {"A": "X:832T", "B": "X:834T"}, "controlPoint": "X:East"}})
        self.assertEqual(list(ix["appliances"]["833T"]["derived"]["circuits"]), ["A", "B"])
        self.assertEqual(rows(ix, "joints")[0]["derived"]["circuits"], {"A": "X:832T", "B": "X:834T"})   # the markers name them
        self.assertEqual(rows(ix, "joints")[0]["relations"]["A"], sorted([at(sm, "J1", "A").replace(at(sm, "J1", "A"), "X:832T.TC"), "X:833T.A"]))
        self.assertEqual(diags(sm, "circuit", "track"), [])
        self.assertEqual(layout_model.errors(emit.emit(sm)), [])

    def test_a_boundary_with_no_marker_on_a_side_leaves_that_side_dark_rather_than_naming_it(self):
        sm, ix = compile_(DOUBLE_JOINT.replace("TC2  | Track Circuit                 | APPLIANCE | Appliance=track_circuit Name=834T\n", "") + self.BOUNDARY,
                          self.NETS.replace(" TC2.TC", ""))
        self.assertEqual(ix["appliances"]["833T"]["derived"]["circuits"], {"A": "X:832T"})
        self.assertEqual(rows(ix, "joints")[0]["derived"]["circuits"], {"A": "X:832T"})
        self.assertEqual(diags(sm, "circuit"), [])

    def test_both_pins_on_one_wire_are_shorted(self):
        sm, _ = compile_(DOUBLE_JOINT + self.BOUNDARY, self.NETS.replace(" TC3.B", "").replace(" TC3.A", " TC3.A TC3.B"))
        self.assertEqual(diags(sm, "track.shorted"), [("track.shorted", "TC3")])


class Plates(unittest.TestCase):
    """ADR 0013 §5: a plate (RULE_290_G, RULE_290_R) is a POLICY whose To pin sits on a mast's SIGNAL net. Its row
    states the mast and no track side; that the mast is PERMISSIVE is the derivation's check."""

    PLATE = "PL1  | Signal Mast Plate-G | POLICY | Kind=RULE_290_G\n"

    def test_a_plate_states_the_mast_on_its_net_and_no_track(self):
        sm, ix = compile_(DOUBLE_JOINT + self.PLATE, DOUBLE_JOINT_NETS.replace("sb   | J1.SIGNAL_B M2.SIGNAL", "sb   | J1.SIGNAL_B M2.SIGNAL PL1.To"))
        self.assertEqual(sm.report.errors, [])
        self.assertEqual(rows(ix, "policies"), [{"given": {"Kind": "RULE_290_G"}, "relations": {"mast": "X:832SA"}}])
        self.assertEqual(diags(sm, "plate", "joint", "track"), [])
        self.assertNotIn("PL1.To", str(track_relations(ix)))
        self.assertEqual(layout_model.errors(emit.emit(sm)), [])

    def test_a_plate_on_no_mast_or_on_a_controlled_mast_is_an_error(self):
        sm, ix = compile_(DOUBLE_JOINT + self.PLATE, DOUBLE_JOINT_NETS + "x    | PL1.To TC2.TC\n")
        plate = sm.source.symbols["PL1"].uuid                               # a rule check names the row by its id
        self.assertEqual(diags(sm, "plate"), [("plate.mast", plate)])
        self.assertNotIn("relations", rows(ix, "policies")[0])
        sm, _ = compile_(DOUBLE_JOINT.replace("Kind=PERMISSIVE Name=832SA", "Kind=CONTROLLED Name=832SA") + self.PLATE,
                         DOUBLE_JOINT_NETS.replace("sb   | J1.SIGNAL_B M2.SIGNAL", "sb   | J1.SIGNAL_B M2.SIGNAL PL1.To"))
        self.assertEqual(diags(sm, "plate"), [("plate.mast", plate)])
        self.assertEqual([d.severity for d in sm.report.by_code("plate.mast")], ["error"])


class Checks(unittest.TestCase):
    """What only the drawing shows, as one scenario: (code, the symbol it names)."""

    def check(self, sym_table: str, net_table: str, want: list[tuple[str, str]]):
        sm, _ = compile_(sym_table, net_table)
        self.assertEqual([x for x in diags(sm, *{c for c, _ in want}) if x[0] in {c for c, _ in want}], want)

    def test_two_masts_on_one_signal_joint(self):
        self.check(ONE_SWITCH, ONE_SWITCH_NETS.replace("s2   | J2.SIGNAL M2.SIGNAL", "s2   | J2.SIGNAL M2.SIGNAL M3.SIGNAL")
                   .replace("s3   | J3.SIGNAL M3.SIGNAL\n", ""), [("joint.masts", "J2")])

class References(unittest.TestCase):
    """A qualified name for another interlocking's thing is one-sided (the owner, 2026-10-27): the importer writes no
    appliance for it. A marker is a consumer row (``Circuits``); a switch is named by its port. ``test_derive`` checks
    that each resolves."""

    def test_a_switch_reference_is_named_by_its_port_is_an_error_and_an_unwired_one_is_reported(self):
        """The owner, 2026-10-28: track wired to another interlocking's switch is an error (``reference.track``)."""
        given = """
H1   | House            | STRUCTURE | Kind=CONTROL_POINT CP_Name=East
J1   | IRJ              | TRACK     | Kind=IRJ
SW1  | Switch_Lock      | APPLIANCE | Appliance=switch Style=lock Name=Y:5
L1   | AUXILIARY        | APPLIANCE | Appliance=lamp Name=Y:SFLK
"""
        sm, ix = compile_(given, "a | J1.A SW1.R\n")
        self.assertEqual(ix["track"]["joints"][0]["relations"], {"A": ["Y:5.R"]})
        self.assertNotIn("appliances", ix)
        self.assertEqual(diags(sm, "reference"), [("reference.track", "X"), ("reference.unwritten", "L1")])
        self.assertEqual([d.severity for d in sm.report.by_code("reference.unwritten")], ["warning"])

    CONSUMER = """
H1   | House           | STRUCTURE | Kind=CONTROL_POINT CP_Name=East
J1   | IRJ             | TRACK     | Kind=IRJ
TC1  | Track Circuit   | APPLIANCE | Appliance=track_circuit Name=Corporal:2NAT {}
"""

    def test_a_consumer_reads_its_indication_field_and_falls_back_to_its_name_at_info(self):
        """The owner, 2026-10-28: a remote consumer marker's token is its Indication field (``${Name}K`` to be a library
        macro), qualified in the scope its Name names; without one, its Name and K, reported so the unconverted show."""
        for field, token, legacy in (("Indication=2NATXK", "Corporal:2NATXK", []), ("Indication=Corporal:2NATK", "Corporal:2NATK", []),
                                     ("", "Corporal:2NATK", [("consumer.legacy_token", "TC1")])):
            sm, ix = compile_(self.CONSUMER.format(field), "a | J1.A TC1.TC\n")
            self.assertEqual(ix["track"]["consumers"][0]["relations"]["indication"], token, field)
            self.assertEqual(diags(sm, "consumer"), legacy, field)
            self.assertEqual([d.severity for d in sm.report.by_code("consumer.legacy_token")], ["info"] if legacy else [])


class Shorted(unittest.TestCase):
    def test_two_track_pins_of_one_symbol_on_one_wire_are_an_error(self):
        """The owner, 2026-10-28: a switch's N and R wired to each other with nothing between; a correct drawing has
        insulated joints between them. The relations cannot state it, since a pin never names its own symbol."""
        sm, ix = compile_(ONE_SWITCH, ONE_SWITCH_NETS.replace("n    | SW1.N J2.A\nr    | SW1.R J3.A", "n    | SW1.N SW1.R J2.A J3.A"))
        self.assertEqual(diags(sm, "track.shorted"), [("track.shorted", "SW1")])
        self.assertNotIn("X:835.N", ix["appliances"]["835"]["relations"]["R"])
        sm, _ = compile_(ONE_SWITCH, ONE_SWITCH_NETS)
        self.assertEqual(diags(sm, "track.shorted"), [])


class TrainOrder(unittest.TestCase):
    """A train order board (Appliance train_order; the owner, 2026-11-03, 2026-11-08): an operator-controlled non-vital
    indicator at a timetable station, Style single or double as drawn, with no pins. Its faces are the pins of its
    field mast device (Appliance train_order_mast): a head or a fascia lever (Appliance lever, Style train_order) whose
    IND wire reaches a face pin is that face's. The importer's part: the appliance row with its station relation, each
    head's and lever's mast and face, the lever's bindings, and the diagnostics about the drawing."""

    STATION = """
ST1  | Station          | STRUCTURE | Kind=STATION Name=Gilroy Milepost=77.9
H1   | House            | STRUCTURE | Kind=CONTROL_POINT CP_Name=East
TC1  | Track Circuit    | APPLIANCE | Appliance=track_circuit Name=1NAT
NX1  | NextCP           | TRACK     | Kind=NEXT_CP Interlocking=Lick
"""
    SIGNAL = "TO1  | Train Order Mast Double | APPLIANCE | Appliance=train_order Style=double Name=Gilroy Station=Gilroy\n"
    TRACK = "w | TC1.TC NX1.To\n"
    FIELD = """
DM1  | Device-TrainOrder-Mast-Double | DEVICE   | Appliance=train_order_mast Name=Gilroy
HE   | Device-Head-Semaphore-UQ      | DEVICE   | Appliance=head Style=UQ
HW   | Device-Head-Semaphore-UQ      | DEVICE   | Appliance=head Style=UQ
LE   | Local-TrainOrder              | DEVICE   | Appliance=lever Style=train_order
LW   | Local-TrainOrder              | DEVICE   | Appliance=lever Style=train_order
X1   | Driver-I2C-MAX7311            | IODRIVER | IC=MAX7311 Address=0x20
"""
    BUS = "bus | P1.IOBus X1.IOBus\n"
    FACES = "e | DM1.E HE.IND LE.IND\nw | DM1.W HW.IND LW.IND\nes | LE.STOP X1.A0\nel | LE.SLOW X1.A1\nws | LW.STOP X1.A2\n"

    @staticmethod
    def by_ref(sm, ix) -> dict[str, dict]:
        return {d.sym.ref: row for d, row in zip(sm.interlockings["X"].devices, ix["devices"])}

    def test_the_board_is_an_appliance_with_its_station_and_no_heads(self):
        sm, ix = compile_(self.STATION + self.SIGNAL, self.TRACK)
        self.assertEqual(sm.report.errors, [])
        to = ix["appliances"]["Gilroy"]
        self.assertEqual(to["given"], {"Appliance": "train_order", "Style": "double", "Station": "Gilroy"})
        self.assertEqual(to["relations"], {"station": "Gilroy"})                            # facing is the geometry's; none in a fragment
        self.assertNotIn("heads", to)                                                        # the trackplan symbol has no pins
        self.assertEqual(emit.emit(sm)["layout"]["stations"]["Gilroy"], {"given": {"Kind": "STATION", "Milepost": "77.9"}, "relations": {"interlocking": "X"}})
        self.assertEqual(layout_model.errors(emit.emit(sm)), [])

    def test_its_faces_are_its_field_masts_pins_each_with_its_head_and_its_lever(self):
        """The owner, 2026-11-08: a head's or a lever's IND wire reaches a face pin of the train order mast device; the
        lever's STOP and SLOW bind to the driver pins their wires reach; the mast device itself binds nothing."""
        sm, ix = compile_(self.STATION + self.SIGNAL + self.FIELD, self.TRACK + self.BUS + self.FACES)
        self.assertEqual(sm.report.errors, [])
        self.assertEqual(diags(sm, "train_order.", "head.", "lever."), [])
        devs = self.by_ref(sm, ix)
        self.assertEqual(devs["DM1"], {"given": {"Appliance": "train_order_mast", "Name": "Gilroy"}, "derived": {"serves": "X:Gilroy"}})
        self.assertEqual(devs["HE"]["relations"], {"mast": "X:Gilroy", "face": "E"})
        self.assertEqual(devs["HW"]["relations"], {"mast": "X:Gilroy", "face": "W"})
        self.assertEqual(devs["LE"]["relations"], {"mast": "X:Gilroy", "face": "E", "bindings": {"SLOW": "Alpha/0x20/A1", "STOP": "Alpha/0x20/A0"}})
        self.assertEqual(devs["LW"]["relations"], {"mast": "X:Gilroy", "face": "W", "bindings": {"STOP": "Alpha/0x20/A2"}})
        self.assertEqual({r: d["derived"] for r, d in devs.items() if r != "X1"}, {r: {"serves": "X:Gilroy"} for r in ("DM1", "HE", "HW", "LE", "LW")})
        self.assertEqual(layout_model.errors(emit.emit(sm)), [])

    def test_a_lever_wired_to_no_face_is_missing_and_to_two_faces_an_error(self):
        """Not yet drawn, then wrong (the owner, 2026-11-08). A head on two face pins is head.masts, as on two masts."""
        sm, ix = compile_(self.STATION + self.SIGNAL + self.FIELD, self.TRACK + self.BUS + "es | LE.STOP X1.A0\n")
        self.assertEqual(diags(sm, "lever."), [("lever.face", "LE"), ("lever.face", "LW")])
        self.assertEqual(sm.report.by_code("lever.face")[0].severity, "missing")
        self.assertNotIn("mast", self.by_ref(sm, ix)["LE"].get("relations", {}))
        sm, ix = compile_(self.STATION + self.SIGNAL + self.FIELD, self.TRACK + self.BUS + "ew | DM1.E DM1.W LE.IND\n")
        self.assertEqual(diags(sm, "lever.faces"), [("lever.faces", "LE")])
        (d,) = sm.report.by_code("lever.faces")
        self.assertEqual(d.severity, "error")
        self.assertIn("2 faces of train order mast 'Gilroy' (E, W)", d.text)
        sm, _ = compile_(self.STATION + self.SIGNAL + self.FIELD, self.TRACK + "ew | DM1.E DM1.W HE.IND\n")
        self.assertEqual(diags(sm, "head.masts"), [("head.masts", "HE")])
        self.assertEqual(diags(sm, "head.letter"), [("head.letter", "HE"), ("head.letter", "HW")])   # a head on no face has no letter either

    def test_a_pin_on_the_track_is_an_error(self):
        sm, ix = compile_(self.STATION + self.SIGNAL, "w | TC1.TC NX1.To TO1.H\n")
        self.assertEqual(diags(sm, "train_order.track"), [("train_order.track", "TO1")])
        self.assertEqual(ix["track"]["ends"][0]["relations"]["track"], ["X:1NAT.TC"])     # the H pin is no track pin


class Locations(unittest.TestCase):
    def test_a_derived_diagnostic_keeps_its_model_path_and_the_importer_adds_the_symbol(self):
        """10c: derive names the model path; the importer appends sheet, reference, library symbol and Value."""
        sm, _ = compile_(ONE_SWITCH, ONE_SWITCH_NETS.replace("s3   | J3.SIGNAL M3.SIGNAL\n", ""))
        (d,) = sm.report.by_code("mast.joint")
        self.assertEqual(d.where, "interlockings/X/appliances/836SB")
        self.assertEqual(d.source, "/X/M3 Railroad-Trackplan:Mast_Dwarf ''")
        self.assertTrue(str(d).endswith("at /X/M3 Railroad-Trackplan:Mast_Dwarf ''"))
        (d,) = [d for d in sm.report.by_code("next_cp.interlocking")]
        self.assertTrue(d.where.startswith("interlockings/X/track/ends/") and d.source.startswith("/X/NX1 "))

    def test_an_import_diagnostic_is_located_in_the_drawing_not_the_model(self):
        """ADR 0012 §3.3: an import diagnostic's location is in KiCad terms, in ``source``; it has no model path."""
        sm, _ = compile_(ONE_SWITCH, ONE_SWITCH_NETS.replace("n    | SW1.N J2.A\nr    | SW1.R J3.A", "n    | SW1.N SW1.R J2.A J3.A"))
        (d,) = sm.report.by_code("track.shorted")
        self.assertEqual((d.where, d.entities), ("", ()))
        self.assertEqual(d.source, "/X/SW1 Railroad-Trackplan:Switch_Lock ''")

    def test_the_importer_locates_every_party_of_a_relationship(self):
        """ADR 0012 §3.3: a rule check names every entity it is about; the importer locates each in the drawing."""
        sm, _ = compile_(ONE_SWITCH.replace("Name=836SB", "Name=836SAB"), ONE_SWITCH_NETS)
        (d,) = sm.report.by_code("mast.letters")
        self.assertEqual(d.entities, ("interlockings/X/appliances/836SAB", "interlockings/X/appliances/836SA"))
        self.assertEqual(d.source, "/X/M3 Railroad-Trackplan:Mast_Dwarf ''; /X/M2 Railroad-Trackplan:Mast_Single ''")
        self.assertTrue(str(d).endswith("[interlockings/X/appliances/836SAB]  at /X/M3 Railroad-Trackplan:Mast_Dwarf ''; "
                                        "/X/M2 Railroad-Trackplan:Mast_Single ''"))


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
        automatic = sorted((i, n) for i, n, a in masts if a["given"].get("Kind") in ("ABSOLUTE", "PERMISSIVE"))
        self.assertEqual(automatic, [("Corporal", "832NA"), ("Corporal", "832SA"), ("Sargent", "834NA"), ("Sargent", "834SA")])
        self.assertEqual([(i, n) for i, n, a in masts if ("controlPoint" in a.get("derived", {})) == ((i, n) in automatic)], [])   # ADR 0013 §5
        joints = [j for ix in self.model["interlockings"].values() for j in ix.get("track", {}).get("joints", []) if j["given"]["Kind"] == "IRJ_SIGNAL"]
        self.assertEqual(len(joints), 36)                                   # Watsonville's 838SAB joint (Railroad 253b666)
        self.assertEqual([j for j in joints if "mast" not in j.get("relations", {}) or "controlPoint" not in j["derived"]], [])
        self.assertEqual([j for j in joints if set(j["derived"].get("circuits", {})) - {"approach", "governed"}], [])

    def test_every_track_row_has_its_own_id(self):
        ids = [r["id"] for ix in self.model["interlockings"].values() for k in ("joints", "ends", "policies") for r in ix.get("track", {}).get(k, [])]
        # IRJ, IRJ_SIGNAL, IRJ_SIGNALS; NEXT_CP, BUMPER, INDUSTRY; policies by Kind with the one plate: the Corporal to
        # Sargent block drawn across sheets (Railroad 56ff2e1, 2a1696e, 31954c5) replaced that NextCP pair; the three
        # CTC boundaries are plain IRJs with a marker each side (Railroad 0ddd395). Read from Railroad 9fcf779 with the
        # owner's uncommitted edits of 2026-11-10 (two BEGIN CTC faces beyond Watsonville's yard IRJs); the policy
        # counts move with that redraw, the joints and ends do not.
        kinds = Counter(r["given"]["Kind"] for ix in self.model["interlockings"].values() for k in ("joints", "ends", "policies") for r in ix.get("track", {}).get(k, []))
        self.assertEqual({k: v for k, v in kinds.items() if not k.startswith("GCOR_")}, {"IRJ": 57, "IRJ_SIGNAL": 36, "IRJ_SIGNALS": 2, "NEXT_CP": 16, "BUMPER": 3, "INDUSTRY": 5, "RULE_290_G": 1})
        self.assertEqual({k: v for k, v in kinds.items() if k.startswith("GCOR_")}, {"GCOR_RULE_9_14": 10, "GCOR_RULE_10": 5, "GCOR_RULE_14": 2, "GCOR_RULE_6_13": 5, "GCOR_RULE_6_28": 4})
        self.assertEqual(len(ids), sum(kinds.values()))
        self.assertEqual(len(set(ids)), len(ids))

    def test_every_appliance_has_its_control_point_and_no_chain_is_broken(self):
        self.assertEqual([d for d in self.sm.report.diags if d.code.startswith("control_point")], [])
        self.assertEqual([(i, n) for i, ix in self.model["interlockings"].items() for n, a in ix.get("appliances", {}).items()
                          if "controlPoint" not in a.get("derived", {}) and a["given"].get("Kind") not in ("ABSOLUTE", "PERMISSIVE")
                          and a["given"]["Appliance"] != "train_order"], [])                # never in a control point (the owner, 2026-11-03)

    def test_every_next_cp_names_where_it_leads_and_is_answered(self):
        ends = [(i, e["given"].get("Interlocking")) for i, ix in self.model["interlockings"].items() for e in ix["track"].get("ends", [])
                if e["given"]["Kind"] == "NEXT_CP"]
        self.assertEqual(len(ends), 16)          # the Corporal to Sargent pair is gone: the block is drawn (Railroad 56ff2e1, 2a1696e)
        self.assertEqual([e for e in ends if not e[1]], [])
        self.assertEqual(sorted(b for a, b in ends if a == "Christopher"), ["Corporal", "Corporal", "Luchessa", "Luchessa"])
        self.assertEqual(self.sm.report.by_code("next_cp.pair"), [])

    def test_luchessas_industry_lead_is_beyond_a_regime_boundary(self):
        """Railroad 0ddd395: a plain IRJ with END CTC on the circuit side (02T) and Rule 6.28 beyond, where the one-ended
        lead to Gilroy Industry lies under its own regime (ADR 0013 §7.1)."""
        ix = self.ix("Luchessa")
        industry = next(e for e in ix["track"]["ends"] if e.get("name") == "Luchessa:Gilroy Industry")
        joint = next(j for j in ix["track"]["joints"] if f"{j['id']}.A" in industry["relations"]["EoT"])
        self.assertEqual((joint["given"], joint["derived"]), ({"Kind": "IRJ"}, {"circuits": {"B": "Luchessa:02T"}}))
        signs = {p["given"]["Kind"]: p for p in ix["track"]["policies"] if p["given"]["Kind"].startswith("GCOR_RULE_") and p["given"]["Kind"] != "GCOR_RULE_9_14"}
        self.assertEqual(signs["GCOR_RULE_6_28"]["relations"]["track"], sorted([f"{joint['id']}.A", "Luchessa:Gilroy Industry.EoT"]))
        self.assertIn(f"{joint['id']}.B", signs["GCOR_RULE_10"]["relations"]["track"])
        pieces = {p["derived"]["name"]: p["derived"] for p in ix["track"]["pieces"]}
        self.assertEqual(pieces["Luchessa:Gilroy Industry"], {"name": "Luchessa:Gilroy Industry", "regime": "GCOR_RULE_6_28", "by": "marker"})
        self.assertEqual(pieces["Luchessa:02T"], {"name": "Luchessa:02T", "circuit": "Luchessa:02T", "regime": "GCOR_RULE_10", "by": "marker"})

    def test_the_beet_loader_and_gilroy_caltrains_yard_carry_their_regimes(self):
        """Railroad 0ddd395: TWC beyond Corporal's and Sargent's boundaries, where the Beet Loader tracks rejoin the two
        sheets; yard limits on Gilroy Caltrain's bumper tracks (ADR 0013 §7.1)."""
        for name in ("Corporal", "Sargent"):
            pieces = {p["derived"]["name"]: p["derived"] for p in self.ix(name)["track"]["pieces"]}
            self.assertEqual(pieces[f"{name}:1T1"], {"name": f"{name}:1T1", "circuit": f"{name}:1T1", "regime": "GCOR_RULE_14", "by": "marker"}, name)
        yard = [p["derived"] for p in self.ix("Gilroy Caltrain")["track"]["pieces"] if p["derived"].get("regime") == "GCOR_RULE_6_13" and p["derived"]["by"] == "marker"]
        self.assertEqual(len(yard), 3)                                # the three bumper tracks; what inherits from them is the rules' business

    def test_sargents_hot_box_alarm_states_its_milepost(self):
        self.assertEqual(self.ix("Sargent")["appliances"]["HBA"]["given"]["Milepost"], "83.5")      # moved in Railroad 0ddd395

    def test_sargents_os_circuit_is_on_its_three_signal_joints(self):
        joints = [j for j in self.ix("Sargent")["track"]["joints"] if j["given"]["Kind"] == "IRJ_SIGNAL"]
        self.assertEqual(sorted((j["derived"]["circuits"]["governed"], j["relations"]["governed"][0]) for j in joints),
                         [("Sargent:835T1", "Sargent:835.C"), ("Sargent:835T1", "Sargent:835.N"), ("Sargent:835T1", "Sargent:835.R")])

    def test_luchessa_houses_and_its_derail(self):
        a = self.ix("Luchessa")["appliances"]
        self.assertEqual({n: a[n]["derived"]["controlPoint"] for n in ("783", "795", "795D", "799")},
                         {"783": "Luchessa:Luchessa", "795": "Luchessa:Gilroy", "795D": "Luchessa:Gilroy", "799": "Luchessa:Carnadero"})
        self.assertEqual(self.ix("Luchessa")["track"]["links"], [{"derived": {"ports": ["Luchessa:795.R", "Luchessa:795D.R"], "circuit": "Luchessa:795T1"}}])

    def test_every_track_relation_is_named_back_across_the_file(self):
        """The owner, 2026-10-27: symmetric adjacency on the drawing, consumer rows included; since the block POC a track net
        is read across sheets (ADR 0013 §7.1, Railroad 31954c5), so a pin another interlocking names (Sargent's 834 joint
        names Corporal:834T.TC) names it back from its own interlocking, and every pin named is a pin of the file."""
        rel = {}
        for name, ix in self.model["interlockings"].items():
            for n, a in ix.get("appliances", {}).items():
                rel.update({f"{name}:{n}.{side}": v for side, v in a.get("relations", {}).items() if isinstance(v, list)})
            for kind in ("joints", "ends", "policies", "consumers"):
                for r in ix.get("track", {}).get(kind, []):
                    rel.update({f"{r.get('name') or r['id']}.{side}": v for side, v in r.get("relations", {}).items() if isinstance(v, list)})
        self.assertEqual([(a, b) for a, bs in rel.items() for b in bs if b not in rel], [])
        self.assertEqual([(a, b) for a, bs in rel.items() for b in bs if a not in rel[b]], [])
        self.assertEqual([a for a, bs in rel.items() if any(b.rsplit(".", 1)[0] == a.rsplit(".", 1)[0] for b in bs)], [])
        across = sorted({(a.partition(":")[0], b.partition(":")[0]) for a, bs in rel.items() for b in bs
                         if ":" in a and ":" in b and a.partition(":")[0] != b.partition(":")[0]})
        self.assertEqual(across, [("Corporal", "Sargent"), ("Sargent", "Corporal")])      # the one block drawn across sheets

    def test_no_cross_interlocking_consumer_is_drawn_today(self):
        """Sargent's consumer of Corporal:2NATK went with the block POC (Railroad 56ff2e1, 2a1696e): the track between
        Corporal and Sargent is drawn, not paired, so no interlocking draws a marker named for another's circuit, no
        reference is raised, and no track relation names a thing outside the file's interlockings."""
        refs = {n: ix["track"].get("consumers", []) for n, ix in self.model["interlockings"].items()}
        self.assertEqual({n: cs for n, cs in refs.items() if cs}, {})
        self.assertNotIn("2NATK", codeline.stations(self.model).stations[("Corporal", None)].indications)
        self.assertEqual([d for d in self.sm.report.diags if d.code.startswith("reference")], [])
        foreign = [b for ix in self.model["interlockings"].values() for k in ("joints", "ends", "policies")
                   for r in ix["track"].get(k, []) for v in r.get("relations", {}).values() if isinstance(v, list) for b in v
                   if ":" in b and not b.startswith(tuple(f"{n}:" for n in self.model["interlockings"]))]
        self.assertEqual(foreign, [])

    def test_the_poc_signal_locations_are_double_joints_with_a_mast_on_each_side(self):
        """ADR 0013 §2 and §6 (Railroad 2a1696e, 31954c5): 832 on Corporal's sheet, 834 on Sargent's; each mast's governed
        side is the side its pin names. 834T is drawn on Corporal's sheet and reaches Sargent's 834 joint through the
        ToSargentMT / ToCorporalMT labels (§7.1; ``test_the_block_track_is_read_across_sheets``)."""
        double = {n: [j for j in self.ix(n)["track"]["joints"] if j["given"]["Kind"] == "IRJ_SIGNALS"] for n in ("Corporal", "Sargent")}
        self.assertEqual({n: [j["relations"]["masts"] for j in js] for n, js in double.items()},
                         {"Corporal": [{"A": "Corporal:832NA", "B": "Corporal:832SA"}], "Sargent": [{"A": "Sargent:834NA", "B": "Sargent:834SA"}]})
        self.assertEqual(double["Corporal"][0]["derived"]["circuits"], {"A": "Corporal:832T", "B": "Corporal:834T"})
        self.assertEqual(self.ix("Corporal")["appliances"]["832NA"]["derived"]["circuits"], {"governed": "Corporal:832T", "approach": "Corporal:834T"})
        self.assertEqual(self.ix("Corporal")["appliances"]["832SA"]["derived"]["circuits"], {"governed": "Corporal:834T", "approach": "Corporal:832T"})
        self.assertEqual(self.ix("Sargent")["appliances"]["834SA"]["derived"]["circuits"]["governed"], "Sargent:836T")
        plates = [(n, p["given"]["Kind"], p["relations"].get("mast")) for n, ix in self.model["interlockings"].items()
                  for p in ix["track"].get("policies", []) if p["given"]["Kind"].startswith("RULE_290")]
        self.assertEqual(plates, [("Sargent", "RULE_290_G", "Sargent:834SA")])      # the one plate drawn: on a PERMISSIVE mast
        self.assertEqual(self.sm.report.by_code("plate.mast"), [])
        boundary = self.ix("Corporal")["appliances"]["833T"]                   # the detector at 832, on 832T and 834T
        self.assertEqual((boundary["given"]["Style"], boundary["derived"]["circuits"]), ("boundary", {"A": "Corporal:832T", "B": "Corporal:834T"}))
        self.assertIn("Corporal:833T.A", double["Corporal"][0]["relations"]["A"])
        self.assertEqual(self.sm.report.by_code("circuit.names"), [])             # the boundary names no circuit
        self.assertEqual(self.sm.report.by_code("mast.joint") + self.sm.report.by_code("track.kind"), [])

    def test_the_block_track_is_read_across_sheets(self):
        """ADR 0013 §7.1 (Railroad 31954c5): Corporal's 834T runs through ToSargentMT to Sargent's 834 double joint, whose
        side A names Corporal:834T.TC and Corporal's 833T boundary, derives Corporal:834T, and 834NA governs over it;
        Corporal's 834T names the joint's pin by its id. Plain track across sheets is block track: no reference.track,
        no consumer, no token. No NextCP stands on drawn block track (next_cp.drawn) and no PERMISSIVE mast governs
        over a powered switch (mast.powered): both counts are zero on this drawing."""
        s, c = self.ix("Sargent"), self.ix("Corporal")
        joint = next(j for j in s["track"]["joints"] if j["given"]["Kind"] == "IRJ_SIGNALS")
        self.assertEqual(sorted(x for x in joint["relations"]["A"] if ":" in x), ["Corporal:833T.B", "Corporal:834T.TC"])
        self.assertEqual(joint["derived"]["circuits"], {"A": "Corporal:834T", "B": "Sargent:836T"})
        self.assertEqual(s["appliances"]["834NA"]["derived"]["circuits"], {"governed": "Corporal:834T", "approach": "Sargent:836T"})
        self.assertIn(f"{joint['id']}.A", c["appliances"]["834T"]["relations"]["TC"])
        self.assertEqual(c["appliances"]["833T"]["derived"]["circuits"], {"A": "Corporal:832T", "B": "Corporal:834T"})
        self.assertEqual(self.sm.report.by_code("reference.track") + self.sm.report.by_code("reference.marker"), [])
        self.assertEqual(len(self.sm.report.by_code("next_cp.drawn")), 0)
        self.assertEqual(len(self.sm.report.by_code("mast.powered")), 0)
        # Railroad 9fcf779: 15 switch.lever (Watsonville's 3 to 25, Gilroy Caltrain 771, Gilroy's locks 777 and 781) and
        # 2 switch.lock.local are settled; identity.name and head.letter are the anonymous head devices, #80's; the
        # regime findings are the owner's redraw in progress (#113, #118); driver.signal_system is Gilroy's six JMRI signal
        # mast drivers with no SignalSystem drawn yet (#85). No warning: Lick and Hollister are marked off_layout and no
        # mast lacks its Kind.
        missing = Counter(d.code for d in self.sm.report.diags if d.severity == "missing")
        self.assertEqual({k: v for k, v in missing.items() if k.startswith("switch.")}, {"switch.lever": 15, "switch.lock.local": 2})
        heads = [d for ix in self.model["interlockings"].values() for d in ix["devices"] if d["given"]["Appliance"] == "head"]
        self.assertEqual(missing["identity.name"], len(heads))
        self.assertEqual(set(missing) - {"switch.lever", "switch.lock.local", "identity.name", "head.letter", "driver.signal_system"} - {k for k in missing if k.startswith("regime.")}, set())
        self.assertEqual(self.sm.report.counts()["warning"], 0)

    def test_a_mast_states_its_kind_or_is_reported_missing(self):
        """ADR 0013 §5. The library's mast symbols carry a fixed Kind (Railroad 1695d48), but that commit touched no placed
        field: a placement states its Kind only once it is updated from the library, which the owner's edits and the
        edits/add_mast_kind.py sweep of 2026-11-03 did for every placement. As of the Railroad working tree of
        2026-11-03 (31954c5 plus uncommitted edits to the seven sheets and the library), all 40 masts state theirs:
        the four PERMISSIVE automatics of the Corporal to Sargent block and 36 CONTROLLED. Nothing is reported, and
        nothing is inferred: a mast with no Kind would be ``mast.kind`` at missing."""
        masts = {(i, n): a["given"].get("Kind") for i, ix in self.model["interlockings"].items() for n, a in ix.get("appliances", {}).items()
                 if a["given"]["Appliance"] == "mast"}
        self.assertEqual(len(masts), 40)
        self.assertEqual(sorted(v for v in masts.values() if v == "PERMISSIVE"), ["PERMISSIVE"] * 4)
        self.assertEqual({v for v in masts.values()}, {"CONTROLLED", "PERMISSIVE"})
        self.assertEqual(self.sm.report.by_code("mast.kind"), [])

    def test_no_circuit_carries_two_names(self):
        self.assertEqual(self.sm.report.by_code("circuit.names") + self.sm.report.by_code("circuit.name.disagree"), [])


if __name__ == "__main__":
    unittest.main()
