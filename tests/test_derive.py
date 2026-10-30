"""Scenarios for the reference derivation, ``tools/layout_model/derive.py`` (ADR 0011 §5, ADR 0012 §4).

Each scenario's Given is a small Layout Data Model File written as tables, with no netlist and no KiCad: a table of
things (an appliance by name, or a track row by id, with its given fields and its stated relations), a table of wires
(the track pins one wire joins; each pin then names every other, the stated adjacency of three-maps D5), and the
houses. Its Then is what ``derived`` holds and the diagnostics as (code, the thing named). The committed SPCoast
example is the gate: stripped of every ``derived`` map and derived again, it is byte-identical.
"""
from __future__ import annotations

import copy
import shlex
import unittest
from pathlib import Path

from tools import layout_model
from tools.layout_model import derive
from tools.railroad import codeline

EXAMPLE = Path(__file__).resolve().parents[1] / "schemas" / "layout-model" / "examples" / "spcoast.layout.json"
LISTS = ("joints", "ends", "policies", "consumers")


def _fields(text: str) -> tuple[dict[str, str], dict[str, str]]:
    """``Key=value`` tokens into given; ``rel.key=value`` into relations (a value with spaces in double quotes)."""
    given, rel = {}, {}
    for tok in shlex.split(text):
        k, _, v = tok.partition("=")
        k = k.replace("_", " ") if k == "CP_Name" else k
        (rel if k.startswith("rel.") else given)[k.removeprefix("rel.")] = v
    return given, rel


def interlocking(things: str, wires: str = "", houses: str = "House", name: str = "X") -> dict:
    """Rows of ``key | appliance or joints/ends/policies | Field=value ... rel.mast=X:1NA``; a row's key is its id, and a
    row with ``name=`` is a named row. Wires are ``label | 835.C J1.governed ...``: a pin is a thing's key and its side,
    or a qualified pin of another interlocking (``Y:3NAT.TC``)."""
    ix: dict = {"houses": {}, "appliances": {}, "track": {}}
    for line in filter(str.strip, houses.splitlines() if "\n" in houses else [houses]):
        h, _, rest = line.strip().partition(" ")
        given, rel = _fields(rest)
        ix["houses"][h] = {k: v for k, v in (("given", given), ("relations", rel)) if v}
    rows: dict[str, dict] = {}
    for line in filter(str.strip, things.splitlines()):
        key, where, fields = (c.strip() for c in line.split("|"))
        given, rel = _fields(fields)
        if where == "appliance":
            ix["appliances"][key] = {"given": given, "relations": rel}
        else:
            row = {"id": key, "given": given, "relations": rel}
            if "name" in given:
                row["name"] = derive.qualify(given.pop("name"), name)
            ix["track"].setdefault(where, []).append(row)
            rows[key] = row

    def pin(p: str) -> str:
        thing, _, side = p.rpartition(".")
        if ":" in thing:
            return p
        if thing in rows:
            return f"{rows[thing].get('name') or thing}.{side}"
        return f"{name}:{thing}.{side}"

    def holder(p: str) -> dict | None:
        thing, _, side = p.rpartition(".")
        return ix["appliances"].get(thing) or rows.get(thing)

    for line in filter(str.strip, wires.splitlines()):
        _, members = (c.strip() for c in line.split("|"))
        pins = members.split()
        for p in pins:
            h = holder(p)
            if h is None:
                continue
            side = p.rpartition(".")[2]
            h["relations"][side] = sorted({pin(o) for o in pins if o.rpartition(".")[0] != p.rpartition(".")[0]})
    for a in list(ix["appliances"].values()) + list(rows.values()):
        a["relations"] = {k: v for k, v in a["relations"].items() if v}
        if not a["relations"]:
            del a["relations"]
    return {k: v for k, v in ix.items() if v}


def layout(**interlockings) -> dict:
    return {"schema": layout_model.SCHEMA_ID, "layout": {"name": "T"}, "interlockings": interlockings,
            "provenance": {"sourceType": "test", "writer": {"name": "tests", "version": "0"}}}


def run(model: dict) -> tuple[dict, list[tuple[str, str]]]:
    out, report = derive.derive(model)
    return out, sorted((d.code, d.where.rsplit("/", 1)[-1]) for d in report.diags)


def only(diags, *prefixes) -> list[tuple[str, str]]:
    return [d for d in diags if d[0].startswith(prefixes)]


def row(ix: dict, rid: str) -> dict:
    return next(r for k in LISTS for r in ix["track"].get(k, []) if r["id"] == rid)


# One switch inside three signal joints of house East: the Sargent shape.
ONE_SWITCH = """
835    | appliance | Appliance=switch Style=lock TC=835T1
836NAB | appliance | Appliance=mast Style=double
836SA  | appliance | Appliance=mast Style=single
836SB  | appliance | Appliance=mast Style=dwarf
1NAT   | appliance | Appliance=track_circuit
1SAT   | appliance | Appliance=track_circuit
2SAT   | appliance | Appliance=track_circuit
J1     | joints    | Kind=IRJ_SIGNAL rel.mast=X:836NAB
J2     | joints    | Kind=IRJ_SIGNAL rel.mast=X:836SA
J3     | joints    | Kind=IRJ_SIGNAL rel.mast=X:836SB
NX1    | ends      | Kind=NEXT_CP Interlocking=Lick
R1     | policies  | Kind=RULE_261 Direction=BOTH
"""
ONE_SWITCH_WIRES = """
c  | 835.C J1.governed
n  | 835.N J2.governed
r  | 835.R J3.governed
w  | J1.approach 1NAT.TC NX1.track R1.track
e1 | J2.approach 1SAT.TC
e2 | J3.approach 2SAT.TC
"""


class Circuits(unittest.TestCase):
    """A circuit is a component of the stated adjacency, joined through a switch's ports and nothing else."""

    def test_components_stop_at_joints_and_a_switchs_ports_are_one_circuit(self):
        out, diags = run(layout(X=interlocking(ONE_SWITCH, ONE_SWITCH_WIRES, "East")))
        ix = out["interlockings"]["X"]
        self.assertEqual(diags, [("next_cp.off_layout", "X")])
        self.assertEqual({j: row(ix, j)["derived"]["circuits"] for j in ("J1", "J2", "J3")}, {
            "J1": {"governed": "X:835T1", "approach": "X:1NAT"},
            "J2": {"governed": "X:835T1", "approach": "X:1SAT"},
            "J3": {"governed": "X:835T1", "approach": "X:2SAT"}})
        self.assertEqual(row(ix, "NX1")["derived"], {"circuits": {"track": "X:1NAT"}})
        self.assertEqual(row(ix, "R1")["derived"], {"circuits": {"track": "X:1NAT"}})
        self.assertEqual(ix["appliances"]["835"]["derived"], {"osCircuit": "X:835T1", "controlPoint": "X:East"})
        self.assertEqual(layout_model.errors(out), [])

    def test_a_marker_names_its_circuit_over_a_switchs_tc_and_two_names_are_an_error(self):
        things = ONE_SWITCH + "9T | appliance | Appliance=track_circuit\n"
        _, diags = run(layout(X=interlocking(things, ONE_SWITCH_WIRES.replace("c  | 835.C J1.governed", "c  | 835.C J1.governed 9T.TC"), "East")))
        self.assertEqual(only(diags, "circuit"), [("circuit.name.disagree", "X")])
        _, diags = run(layout(X=interlocking(things, ONE_SWITCH_WIRES.replace("e1 | J2.approach 1SAT.TC", "e1 | J2.approach 1SAT.TC 9T.TC"), "East")))
        self.assertEqual(only(diags, "circuit"), [("circuit.names", "X")])

    def test_dark_track_has_no_circuit(self):
        things = """
1  | appliance | Appliance=switch Style=manual
E1 | ends      | Kind=END_CTC
2SAT | appliance | Appliance=track_circuit
I1 | ends      | Kind=INDUSTRY name="Gilroy Industry"
"""
        out, diags = run(layout(X=interlocking(things, "ctc | E1.CTC 2SAT.TC\ndark | E1.DARK 1.C\nin | I1.EoT 1.N\n", "East")))
        ix = out["interlockings"]["X"]
        self.assertEqual(diags, [])
        self.assertEqual(row(ix, "E1")["derived"], {"circuits": {"CTC": "X:2SAT"}})
        self.assertNotIn("derived", row(ix, "I1"))
        self.assertNotIn("osCircuit", ix["appliances"]["1"]["derived"])

    def test_ports_that_meet_with_no_joint_between_are_a_link(self):
        things = """
795  | appliance | Appliance=switch Style=lock TC=795T1
795D | appliance | Appliance=switch Style=derail
J1   | joints    | Kind=IRJ_SIGNAL
"""
        out, diags = run(layout(X=interlocking(things, "rr | 795.R 795D.R\ndc | 795D.C J1.governed\n", "Gilroy")))
        ix = out["interlockings"]["X"]
        self.assertEqual(ix["track"]["links"], [{"derived": {"ports": ["X:795.R", "X:795D.R"], "circuit": "X:795T1"}}])
        self.assertEqual(ix["appliances"]["795D"]["derived"]["osCircuit"], "X:795T1")
        self.assertEqual(row(ix, "J1")["derived"]["circuits"], {"governed": "X:795T1"})

    def test_a_runs_circuit_is_the_circuit_of_what_its_ends_meet(self):
        ix = interlocking(ONE_SWITCH, ONE_SWITCH_WIRES, "East")
        ix["geometry"] = {"track": [{"points": "0,0 1,0", "relations": {"from": "X:835.R", "to": "J3.governed"}},
                                    {"points": "0,1 1,1", "relations": {"to": "J3.approach"}},
                                    {"points": "0,2 1,2"}]}
        out, _ = run(layout(X=ix))
        self.assertEqual([t.get("derived") for t in out["interlockings"]["X"]["geometry"]["track"]],
                         [{"circuit": "X:835T1"}, {"circuit": "X:2SAT"}, None])


class Checks(unittest.TestCase):
    """Each fact inconsistency the derivation sees in the track, as one scenario."""

    def test_a_signal_joint_turned_around(self):
        wires = ONE_SWITCH_WIRES.replace("c  | 835.C J1.governed", "c  | 835.C J1.approach").replace("w  | J1.approach", "w  | J1.governed")
        _, diags = run(layout(X=interlocking(ONE_SWITCH, wires, "East")))
        self.assertEqual(only(diags, "joint"), [("joint.reversed", "J1")])

    def test_a_joint_with_one_circuit_on_both_sides(self):
        _, diags = run(layout(X=interlocking(ONE_SWITCH + "J9 | joints | Kind=IRJ\n",
                                             ONE_SWITCH_WIRES.replace("e1 | J2.approach 1SAT.TC", "e1 | J2.approach 1SAT.TC J9.A\ne3 | 1SAT.TC J9.B"), "East")))
        self.assertEqual(only(diags, "joint"), [("joint.loop", "J9")])

    def test_end_ctc_turned_around(self):
        things = "E1 | ends | Kind=END_CTC\n2SAT | appliance | Appliance=track_circuit\nI1 | ends | Kind=INDUSTRY\n"
        _, diags = run(layout(X=interlocking(things, "d | E1.DARK 2SAT.TC\nc | E1.CTC I1.EoT\n", "East")))
        self.assertEqual(diags, [("end_ctc.sides", "E1")])

    def test_a_mast_on_no_joint_and_on_two(self):
        _, diags = run(layout(X=interlocking(ONE_SWITCH.replace("rel.mast=X:836SB", ""), ONE_SWITCH_WIRES, "East")))
        self.assertEqual(only(diags, "mast"), [("mast.joint", "836SB")])
        _, diags = run(layout(X=interlocking(ONE_SWITCH.replace("rel.mast=X:836SB", "rel.mast=X:836SA"), ONE_SWITCH_WIRES, "East")))
        self.assertEqual(only(diags, "mast"), [("mast.joint", "836SB"), ("mast.joints", "836SA")])

    def test_a_mast_named_for_heads_it_does_not_carry_and_one_letter_on_two_masts(self):
        ix = interlocking(ONE_SWITCH, ONE_SWITCH_WIRES, "East")
        ix["appliances"]["836NAB"]["heads"] = {"A": {"given": {"Style": "CPL"}}, "C": {"given": {"Style": "CPL"}}}
        _, diags = run(layout(X=ix))
        self.assertEqual(only(diags, "mast"), [("mast.heads", "836NAB")])
        ix = interlocking(ONE_SWITCH.replace("836SA  |", "836NA  |").replace("X:836SA", "X:836NA"), ONE_SWITCH_WIRES, "East")
        _, diags = run(layout(X=ix))
        self.assertEqual(only(diags, "mast"), [("mast.letters", "836NA")])

    def test_a_switch_with_no_track_and_a_next_cp_that_names_nothing(self):
        out, diags = run(layout(X=interlocking("9 | appliance | Appliance=switch Style=lock TC=9T1\nN1 | ends | Kind=NEXT_CP\n", "", "East")))
        self.assertEqual(diags, [("next_cp.interlocking", "N1"), ("switch.track", "9")])
        self.assertNotIn("osCircuit", out["interlockings"]["X"]["appliances"]["9"]["derived"])

    def test_a_detection_block_in_tc_is_an_error(self):
        _, diags = run(layout(X=interlocking(ONE_SWITCH.replace("TC=835T1", "TC=835T1,835T2"), ONE_SWITCH_WIRES, "East")))
        self.assertEqual(only(diags, "switch"), [("switch.tc_block", "835")])


# Two houses, the Christopher shape: switches 813 and 815 (with 815A in its gang) on North, 817 on South; siding 01T
# between 813's R and 817's R; 815's R meets 815A's R at a plain joint. Each signal states its house on the joint or on
# the mast; approach circuit 1NAT states North though South's signal bounds it.
TWO_HOUSES = """
813   | appliance | Appliance=switch Style=powered TC=813T1 CP_Name=North
815   | appliance | Appliance=switch Style=powered TC=815T1 CP_Name=North
815A  | appliance | Appliance=switch Style=powered TC=815AT1
817   | appliance | Appliance=switch Style=powered TC=817T1 CP_Name=South
814SA | appliance | Appliance=mast Style=single
816NA | appliance | Appliance=mast Style=single CP_Name=South
818NA | appliance | Appliance=mast Style=single
1SAT  | appliance | Appliance=track_circuit
01T   | appliance | Appliance=track_circuit CP_Name=North
2NAT  | appliance | Appliance=track_circuit
1NAT  | appliance | Appliance=track_circuit CP_Name=North
J1    | joints    | Kind=IRJ_SIGNAL CP_Name=North rel.mast=X:814SA
J2    | joints    | Kind=IRJ_SIGNAL rel.mast=X:816NA
J3    | joints    | Kind=IRJ_SIGNAL CP_Name=South rel.mast=X:818NA
Q1    | joints    | Kind=IRJ
Q2    | joints    | Kind=IRJ
Q3    | joints    | Kind=IRJ
Q4    | joints    | Kind=IRJ
"""
TWO_HOUSES_WIRES = """
a | J1.governed 813.C
b | J1.approach 1SAT.TC
c | 813.R Q1.A
d | Q1.B 01T.TC Q2.A
e | Q2.B 817.R
f | 813.N Q4.A
g | Q4.B 815.C
h | 815.R Q3.A
i | Q3.B 815A.R
j | 815A.C J2.governed
k | J2.approach 2NAT.TC
l | 817.C J3.governed
m | J3.approach 1NAT.TC
"""
NORTH_SOUTH = "North\nSouth"


def control_points(out: dict) -> dict[str, str]:
    return {n: a.get("derived", {}).get("controlPoint", "").removeprefix("X:") for n, a in out["interlockings"]["X"]["appliances"].items()}


class ControlPoints(unittest.TestCase):
    """Control point by propagation along the stated relations (the owner, 2026-10-26)."""

    def test_the_one_house_is_every_appliances_control_point(self):
        out, diags = run(layout(X=interlocking(ONE_SWITCH, ONE_SWITCH_WIRES, "East")))
        self.assertEqual(only(diags, "control_point"), [])
        self.assertEqual(set(control_points(out).values()), {"East"})
        self.assertEqual({row(out["interlockings"]["X"], j)["derived"]["controlPoint"] for j in ("J1", "J2", "J3")}, {"X:East"})
        self.assertNotIn("CP Name", out["interlockings"]["X"]["appliances"]["835"]["given"])

    def test_two_houses_chain_from_the_stated_fields(self):
        """815A follows its gang's 815; 1SAT follows its signal joint, 2NAT the mast of its joint; 1NAT's own field wins
        over South's signal, silently."""
        out, diags = run(layout(X=interlocking(TWO_HOUSES, TWO_HOUSES_WIRES, NORTH_SOUTH)))
        self.assertEqual(only(diags, "control_point"), [])
        self.assertEqual(control_points(out), {
            "813": "North", "815": "North", "815A": "North", "817": "South",
            "814SA": "North", "816NA": "South", "818NA": "South",
            "1SAT": "North", "01T": "North", "2NAT": "South", "1NAT": "North"})

    def test_a_circuit_two_houses_reach_states_which(self):
        _, diags = run(layout(X=interlocking(TWO_HOUSES.replace("Appliance=track_circuit CP_Name=North\n2NAT", "Appliance=track_circuit\n2NAT"),
                                             TWO_HOUSES_WIRES, NORTH_SOUTH)))
        self.assertEqual(only(diags, "control_point"), [("control_point.chains", "01T")])

    def test_an_appliance_no_house_reaches_is_an_error(self):
        _, diags = run(layout(X=interlocking(TWO_HOUSES + "NFLK | appliance | Appliance=lamp Style=non_vital\n", TWO_HOUSES_WIRES, NORTH_SOUTH)))
        self.assertEqual(only(diags, "control_point"), [("control_point.unreached", "NFLK")])

    def test_a_gang_split_across_houses_is_a_warning(self):
        out, diags = run(layout(X=interlocking(TWO_HOUSES.replace("TC=815AT1", "TC=815AT1 CP_Name=South"), TWO_HOUSES_WIRES, NORTH_SOUTH)))
        self.assertEqual(only(diags, "control_point"), [("control_point.gang", "815A")])
        self.assertEqual(control_points(out)["815A"], "South")
        (d,) = derive.derive(layout(X=interlocking(TWO_HOUSES.replace("TC=815AT1", "TC=815AT1 CP_Name=South"), TWO_HOUSES_WIRES,
                                                   NORTH_SOUTH)))[1].by_code("control_point.gang")
        self.assertEqual(d.entities, ("interlockings/X/appliances/815A", "interlockings/X/appliances/815"))  # every party (ADR 0012 §3.3)

    def test_a_control_point_that_is_no_house_is_an_error(self):
        _, diags = run(layout(X=interlocking(ONE_SWITCH.replace("Kind=IRJ_SIGNAL rel.mast=X:836NAB", "Kind=IRJ_SIGNAL CP_Name=Nowhere rel.mast=X:836NAB"),
                                             ONE_SWITCH_WIRES, "East")))
        self.assertEqual(only(diags, "control_point"), [("control_point.house", "J1")])

    def test_a_maintainer_call_belongs_to_the_house_that_names_it(self):
        things = "MC1 | appliance | Appliance=lamp Style=maintainer_call rel.house=X:West\n"
        out, diags = run(layout(X=interlocking(things, "", "East\nWest rel.maintainerCall=X:MC1")))
        self.assertEqual(control_points(out), {"MC1": "West"})
        _, diags = run(layout(X=interlocking(things.replace("maintainer_call", "maintainer_call CP_Name=East"), "", "East\nWest rel.maintainerCall=X:MC1")))
        self.assertEqual(only(diags, "control_point"), [("control_point.disagree", "MC1")])
        (d,) = derive.derive(layout(X=interlocking(things.replace("maintainer_call", "maintainer_call CP_Name=East"), "",
                                                   "East\nWest rel.maintainerCall=X:MC1")))[1].by_code("control_point.disagree")
        self.assertEqual(d.entities, ("interlockings/X/appliances/MC1", "interlockings/X/houses/West", "interlockings/X/houses/East"))

    def test_a_virtual_circuit_lists_its_members_and_follows_them(self):
        things = TWO_HOUSES + "0100T | appliance | Appliance=track_circuit Style=virtual Members=1SAT,01T\n"
        out, diags = run(layout(X=interlocking(things, TWO_HOUSES_WIRES, NORTH_SOUTH)))
        self.assertEqual(only(diags, "control_point"), [])
        self.assertEqual(out["interlockings"]["X"]["appliances"]["0100T"]["derived"], {"members": ["X:1SAT", "X:01T"], "controlPoint": "X:North"})


def pair(a_to_b: int, b_to_a: int) -> dict:
    a = interlocking("\n".join(f"N{i} | ends | Kind=NEXT_CP Interlocking=B" for i in range(a_to_b)), "", "A", "A")
    b = interlocking("\n".join(f"N{i} | ends | Kind=NEXT_CP Interlocking=A" for i in range(b_to_a)), "", "B", "B")
    return layout(A=a, B=b)


class NextCPs(unittest.TestCase):
    def test_next_cps_lead_back_as_often_as_they_lead_out(self):
        self.assertEqual(run(pair(2, 2))[1], [])
        self.assertEqual(run(pair(2, 1))[1], [("next_cp.pair", "A"), ("next_cp.pair", "B")])
        self.assertEqual([d.entities for d in derive.derive(pair(2, 1))[1].by_code("next_cp.pair")],
                         [("interlockings/A", "interlockings/B"), ("interlockings/B", "interlockings/A")])

    def test_one_beyond_the_layout_is_info(self):
        out, diags = run(layout(X=interlocking("N1 | ends | Kind=NEXT_CP Interlocking=Lick\n", "", "East")))
        self.assertEqual(diags, [("next_cp.off_layout", "X")])


def on_line(m: dict, *names: str, kind: str = "AAR") -> dict:
    """The interlockings ``names`` on one code line of encoding ``kind``."""
    m["layout"]["codelines"] = {"Line": {"given": {"Kind": kind}}}
    for n in names:
        m["interlockings"][n].setdefault("relations", {})["codeline"] = "Line"
    return m


def lever(name: str, *functions: str, column: str | None = None, **fields: str) -> dict:
    """A desk lever bound at each function, with the bulk change's per-pin fields: Control.<f> = name+f on a pin ending in
    S, Indication.<f> = name+f on one ending in K, an empty Control.UNUSED; ``fields`` adds or overrides
    (``Control_NWS=...`` for Control.NWS, None to leave a field out)."""
    given = {"Appliance": "lever", "Name": name}
    for f in functions:
        if f == "UNUSED":
            given["Control.UNUSED"] = ""
        elif f.endswith("S"):
            given[f"Control.{f}"] = f"{name}{f}"
        elif f.endswith("K"):
            given[f"Indication.{f}"] = f"{name}{f}"
    for k, v in fields.items():
        key = k.replace("_", ".", 1)
        if v is None:
            given.pop(key, None)
        else:
            given[key] = v
    rel = {"bindings": {f: f"P/0x20/A{i}" for i, f in enumerate(functions)}}
    if column:
        rel["column"] = column
    return {"given": given, "relations": rel}


def lamp(indication: str, interlocking: str = "X", **given: str) -> dict:
    """A desk lamp on the panel sheet of ``interlocking`` (its relations.interlocking), with its Indication expression."""
    return {"given": {"Appliance": "lamp", "Style": "board", **({"Indication": indication} if indication else {}), **given},
            "relations": {"interlocking": interlocking}}


def desk(m: dict, columns: dict[str, str], devices: list[dict]) -> dict:
    """An OfficeUnit Desk with ``columns`` (number to CP Name) and ``devices``."""
    m["officeUnits"] = {"Desk": {"columns": {n: {"given": {"CP Name": cp}} for n, cp in columns.items()}, "devices": devices}}
    return m


def stations(model: dict, ref: dict | None = None) -> tuple[dict, list[tuple[str, str]], codeline.Codeline]:
    """The derivation's diagnostics, and the code line computed from its output: (station -> (controls, indications))."""
    out, report = derive.derive(model, ref)
    line = codeline.stations(out, (ref or {}).get("indicationTokens"))
    diags = sorted((d.code, d.where.rsplit("/", 1)[-1]) for d in report.diags)
    return {k: (sorted(s.controls), sorted(s.indications)) for k, s in line.stations.items()}, diags, line


class Codeline(unittest.TestCase):
    """What each station receives and must send is computed on demand, never stored (the owner, 2026-10-28): its
    controls are the levers' ``Control.X`` of the desk columns it is the station of; its indications are the union of
    the tokens its consumers state, each at the station of the appliance that reports it (``tools/railroad/codeline.py``)."""

    THINGS = ONE_SWITCH + "MC1 | appliance | Appliance=lamp Style=maintainer_call\n"

    def test_on_an_aar_line_the_interlocking_is_the_one_station_and_sends_what_its_consumers_state(self):
        m = desk(on_line(layout(X=interlocking(self.THINGS, ONE_SWITCH_WIRES, "East")), "X"), {"1": "East"}, [
            lever("835", "WLS", "WLK", "WLQK", "UNUSED", column="Desk:1"),
            lever("836", "NGS", "SGS", "HS", "NGK", "SGK", "TEK", column="Desk:1"),
            lever("MC1", "S", "K", column="Desk:1"), lamp("1NATK | MC1K | 835T1K")])
        got, diags, _ = stations(m)
        self.assertEqual(only(diags, "reference", "desk", "lever", "appliance"), [])
        self.assertEqual(got, {("X", None): (["835WLS", "836HS", "836NGS", "836SGS", "MC1S"],
                                             ["1NATK", "835T1K", "835WLK", "835WLQK", "836NGK", "836SGK", "836TEK", "MC1K"])})
        out, _ = derive.derive(m)
        self.assertNotIn("derived", out["interlockings"]["X"])
        self.assertNotIn("derived", out["interlockings"]["X"]["houses"]["East"])
        self.assertEqual(layout_model.errors(out), [])

    def test_on_a_506_line_a_levers_tokens_follow_its_column_and_a_lamps_the_reporting_appliance(self):
        """The owner, 2026-10-28: lever 816 sits in North's column, so North does all its code line work, 816HS and
        816NGK, though its mast 816NA is South's; masts report nothing. A lamp has nothing to do with columns: 2NATK is
        South's, 01TK North's."""
        m = desk(on_line(layout(X=interlocking(TWO_HOUSES, TWO_HOUSES_WIRES, NORTH_SOUTH)), "X", kind="USS506"),
                 {"1": "North", "2": "South"}, [lever("816", "HS", "NGK", column="Desk:1"), lamp("2NATK | 01TK")])
        got, diags, _ = stations(m)
        self.assertEqual(only(diags, "reference", "desk"), [])
        self.assertEqual(got, {("X", "North"): (["816HS"], ["01TK", "816NGK"]), ("X", "South"): ([], ["2NATK"])})

    def test_appliances_the_dispatcher_does_not_control_report_nothing(self):
        """A manual switch, a derail, a gang follower (it reports through its lead) a mast's own K, and a mast as the reporter of a signal lever's token (masts report nothing)."""
        things = TWO_HOUSES + "1 | appliance | Appliance=switch Style=manual CP_Name=North\n795D | appliance | Appliance=switch Style=derail CP_Name=North\n"
        m = desk(on_line(layout(X=interlocking(things, TWO_HOUSES_WIRES, NORTH_SOUTH)), "X"), {}, [
            lamp(t) for t in ("1NWK", "795DNWK", "815ANWK", "814SAK", "816NGK", "815NWK")])
        got, diags, _ = stations(m)
        self.assertEqual(only(diags, "reference"), [("reference.unresolved", str(i)) for i in range(5)])
        self.assertEqual(got[("X", None)][1], ["815NWK"])

    def test_a_name_that_ends_in_k_is_its_token_and_an_os_circuit_is_its_switchs(self):
        things = ONE_SWITCH + "HBA | appliance | Appliance=lamp Style=non_vital\nNFLK | appliance | Appliance=lamp Style=non_vital\n" \
                              "0100T | appliance | Appliance=track_circuit Style=virtual Members=1NAT\n"
        m = desk(on_line(layout(X=interlocking(things, ONE_SWITCH_WIRES, "East")), "X"), {}, [lamp("HBAK | NFLK | 0100TK | 835T1K")])
        got, diags, _ = stations(m)
        self.assertEqual(only(diags, "reference"), [])
        self.assertEqual(got[("X", None)][1], ["0100TK", "835T1K", "HBAK", "NFLK"])

    def test_a_lamp_token_two_houses_report_is_a_warning(self):
        """815A's TC names 815AT1 (North, by its gang); a marker 815AT1 states South."""
        things = TWO_HOUSES + "815AT1 | appliance | Appliance=track_circuit CP_Name=South\n"
        m = desk(on_line(layout(X=interlocking(things, TWO_HOUSES_WIRES, NORTH_SOUTH)), "X", kind="USS506"), {}, [lamp("815AT1K")])
        _, diags, line = stations(m)
        self.assertEqual(only(diags, "reference"), [("reference.station", "0")])
        self.assertEqual([p.kind for p in line.problems], ["station"])

    def test_the_users_reference_data_overrides_the_default(self):
        m = desk(on_line(layout(X=interlocking("9T | appliance | Appliance=track_circuit\n", "", "East")), "X"), {},
                 [lamp("9TKK"), lamp("9TK")])
        got, diags, _ = stations(m, {"indicationTokens": {"AAR": {"track_circuit": ("{name}KK",)}}})
        self.assertEqual(got[("X", None)][1], ["9TKK"])
        self.assertEqual(only(diags, "reference"), [("reference.unresolved", "1")])

    def test_a_station_not_in_the_file_is_a_warning_and_one_on_no_code_line_is_missing(self):
        m = desk(on_line(layout(X=interlocking(self.THINGS, ONE_SWITCH_WIRES, "East"), Y=interlocking("", "", "West", "Y")), "X"), {},
                 [lamp("Z:1TK"), lamp("Y:1TK")])
        got, diags, _ = stations(m)
        self.assertEqual(only(diags, "reference"), [("reference.codeline", "1"), ("reference.interlocking", "0")])
        self.assertEqual(set(got), {("X", None)})


class References(unittest.TestCase):
    """A reference to another interlocking's thing is one-sided (the owner, 2026-10-27). A marker so named is a consumer
    of the named station's indication: it resolves against what that station's appliances report. A switch port or a
    track row so named is an error (the owner, 2026-10-28)."""

    Y = interlocking("""
5    | appliance | Appliance=switch Style=lock TC=5T1
6    | appliance | Appliance=switch Style=derail
3NAT | appliance | Appliance=track_circuit
J5   | joints    | Kind=IRJ
""", "y1 | 5.C 6.C\ny2 | 5.N J5.A\ny3 | J5.B 3NAT.TC\n", "West", "Y")

    def model(self, things: str, wires: str, line: bool = True) -> dict:
        x = interlocking("J1 | joints | Kind=IRJ\n1SAT | appliance | Appliance=track_circuit\n" + things, "b | J1.B 1SAT.TC\n" + wires, "East")
        m = layout(X=x, Y=copy.deepcopy(self.Y))
        return on_line(m, "X", "Y") if line else on_line(m, "X")

    def consumer(self, token: str) -> str:
        return f"K1 | consumers | Appliance=track_circuit rel.indication={token}\n"

    def check(self, things: str, wires: str, line: bool = True) -> list[tuple[str, str]]:
        return only(run(self.model(things, wires, line))[1], "reference")

    def test_a_consumer_resolves_against_what_the_station_reports_and_names_the_circuit(self):
        m = self.model(self.consumer("Y:3NATK"), "a | J1.A K1.TC\n")
        out, diags = run(m)
        self.assertEqual(only(diags, "reference"), [])
        self.assertEqual(row(out["interlockings"]["X"], "J1")["derived"]["circuits"], {"A": "Y:3NAT", "B": "X:1SAT"})
        self.assertNotIn("derived", row(out["interlockings"]["X"], "K1"))
        self.assertEqual(layout_model.errors(out), [])
        self.assertIn("3NATK", stations(m)[0][("Y", None)][1])

    def test_an_indication_no_appliance_reports_is_an_error(self):
        self.assertEqual(self.check(self.consumer("Y:4NATK"), "a | J1.A K1.TC\n"), [("reference.unresolved", "K1")])
        (d,) = derive.derive(self.model(self.consumer("Y:4NATK"), "a | J1.A K1.TC\n"))[1].by_code("reference.unresolved")
        self.assertEqual(d.entities[1:], ("interlockings/Y",))       # the consumer, then the interlocking it fails against
        self.assertTrue(d.entities[0].startswith("interlockings/X/track/consumers/"))

    def test_a_station_not_in_the_file_is_a_warning_and_one_on_no_code_line_is_missing(self):
        self.assertEqual(self.check(self.consumer("Z:2NATK"), "a | J1.A K1.TC\n"), [("reference.interlocking", "K1")])
        self.assertEqual(self.check(self.consumer("Y:3NATK"), "a | J1.A K1.TC\n", line=False), [("reference.codeline", "K1")])

    def test_a_pin_of_another_interlockings_marker_is_no_form(self):
        self.assertEqual(self.check("", "a | J1.A Y:3NAT.TC\n"), [("reference.marker", "X")])

    def test_track_wired_to_another_interlockings_switch_or_track_row_is_an_error(self):
        self.assertEqual(self.check("", "a | J1.A Y:5.R Y:6.R\n"), [("reference.track", "X"), ("reference.track", "X")])
        self.assertIn("track leaves an interlocking at a NextCP or an END_CTC",
                      derive.derive(self.model("", "a | J1.A Y:5.R\n"))[1].by_code("reference.track")[0].text)
        self.assertEqual(self.check("I1 | ends | Kind=INDUSTRY name=Y:Cannery\n", "a | J1.A I1.EoT\n"), [("reference.track", "I1")])

    def test_a_circuit_named_in_a_field_must_exist_too(self):
        things = "9 | appliance | Appliance=switch Style=lock TC=Y:9T1\n1VT | appliance | Appliance=track_circuit Style=virtual Members=Y:3NAT,Y:8NAT\n"
        self.assertEqual(self.check(things, "a | J1.A 9.C\n"), [("reference.unresolved", "1VT"), ("reference.unresolved", "9")])


class Columns(unittest.TestCase):
    """A column's CP Name names a house or an interlocking; what it must name depends on the code line's encoding (the
    owner, 2026-10-28)."""

    def model(self, kind: str, columns: dict[str, dict]) -> dict:
        m = on_line(layout(X=interlocking("", "", NORTH_SOUTH)), "X", kind=kind)
        m["officeUnits"] = {"Desk": {"columns": columns}}
        return m

    def derived(self, kind: str, columns: dict[str, dict]) -> tuple[dict, list[tuple[str, str]]]:
        out, diags = run(self.model(kind, columns))
        return {n: c.get("derived") for n, c in out["officeUnits"]["Desk"]["columns"].items()}, only(diags, "column", "station")

    COLUMNS = {"1": {"given": {"CP Name": "north"}}, "2": {"given": {"CP Name": "X"}}, "3": {"relations": {"interlocking": "X"}}}

    def test_on_an_aar_line_a_column_names_the_interlocking_or_a_house_as_location(self):
        got, diags = self.derived("AAR", self.COLUMNS)
        self.assertEqual(got, {"1": {"house": "X:North", "interlocking": "X"}, "2": {"interlocking": "X"}, "3": None})
        self.assertEqual(diags, [])

    def test_on_a_506_line_a_column_must_name_a_house(self):
        got, diags = self.derived("USS506", self.COLUMNS)
        self.assertEqual(got["1"], {"house": "X:North", "interlocking": "X"})
        self.assertEqual(diags, [("column.cp_name", "3"), ("column.house", "2")])

    def test_a_cp_name_that_names_nothing_is_an_error_and_two_columns_of_one_506_house_are_two_addresses(self):
        _, diags = self.derived("AAR", {"1": {"given": {"CP Name": "Nowhere"}}, "2": {"given": {"CP Name": "North"}}, "3": {"given": {"CP Name": "North"}}})
        self.assertEqual(diags, [("column.house", "1")])
        _, diags = self.derived("USS506", {"2": {"given": {"CP Name": "North"}}, "3": {"given": {"CP Name": "North"}}})
        self.assertEqual(diags, [("station.columns", "X")])


class OfficeUnits(unittest.TestCase):
    def model(self) -> dict:
        m = layout(X=interlocking("", "", "East"), Y=interlocking("2 | appliance | Appliance=switch Style=powered\n", "", "West", "Y"))
        m["interlockings"]["X"]["devices"] = [
            {"given": {"Appliance": "switch", "Name": "1"}},
            {"given": {"Appliance": "head", "Head": "A"}, "relations": {"mast": "X:2NA"}},
            {"given": {"Appliance": "lever", "Style": "code", "Name": "Code"}}]
        m["officeUnits"] = {"Desk": {"columns": {"1": {"given": {"CP Name": "east"}}, "2": {"relations": {"interlocking": "Y"}}},
                                     "devices": [lamp("", "X", IndicationToken="1T, 2T"),
                                                 {"given": {"Appliance": "lever", "Name": "3"}, "relations": {"column": "Desk:2"}},
                                                 {"given": {"Appliance": "lever", "Name": "2"}, "relations": {"column": "Desk:2"}},
                                                 lamp("", "Y", IndicationToken="4T")]}}
        return m

    def test_a_columns_house_is_its_cp_name_and_a_device_resolves_in_its_scope(self):
        out, diags = run(self.model())
        ou = out["officeUnits"]["Desk"]
        self.assertEqual(ou["columns"]["1"]["derived"], {"house": "X:East", "interlocking": "X"})
        self.assertNotIn("derived", ou["columns"]["2"])
        self.assertEqual([d.get("derived") for d in ou["devices"]],
                         [{"indications": ["X:1TK", "X:2TK"], "expression": "X:1TK | X:2TK"}, {"serves": "Y:3"}, {"serves": "Y:2"},
                          {"indications": ["Y:4TK"], "expression": "Y:4TK"}])
        self.assertEqual([d.get("derived") for d in out["interlockings"]["X"]["devices"]], [{"serves": "X:1"}, {"serves": "X:2NA"}, None])
        self.assertEqual(diags, [("desk.legacy_token", "0"), ("desk.legacy_token", "3"), ("head.plan", "1"), ("lever.serves", "1"),
                                 ("reference.codeline", "0"), ("reference.codeline", "0"), ("reference.codeline", "3"), ("switch.track", "2")])

    def test_a_lamp_in_a_column_is_still_in_its_sheets_interlocking(self):
        """A lamp has nothing to do with columns (the owner, 2026-10-28): its scope is its relations.interlocking."""
        m = self.model()
        m["officeUnits"]["Desk"]["devices"][0]["relations"]["column"] = "Desk:2"
        self.assertEqual(run(m)[0]["officeUnits"]["Desk"]["devices"][0]["derived"]["indications"], ["X:1TK", "X:2TK"])


class Desk(unittest.TestCase):
    """The office's side of the code line (the owner, 2026-10-27, 2026-10-28): each bound lever pin's ``Control.X`` is a
    control, each ``Indication.X`` an expression whose tokens the desk consumes, as are a lamp's ``Indication``'s. An
    empty per-pin field binds none; a missing one is reported, never made up from the lever's name."""

    THINGS = ONE_SWITCH + "MC1 | appliance | Appliance=lamp Style=maintainer_call\n"

    def model(self, devices: list[dict]) -> dict:
        m = on_line(layout(X=interlocking(self.THINGS, ONE_SWITCH_WIRES, "East")), "X")
        return desk(m, {"1": "East"}, [d if d["given"]["Appliance"] == "lamp" else
                                       {**d, "relations": {**d.get("relations", {}), "column": "Desk:1"}} for d in devices])

    def test_a_levers_tokens_are_its_per_pin_fields_never_its_name(self):
        lv = lever("835", "WLS", "WLK", "WLQK", "UNUSED", Control_WLS="X:835WLS", Indication_WLK="!835WLK",
                   Indication_WLQK="835WLQK & (1NATK | X:MC1K)")
        out, diags = run(self.model([lv]))
        self.assertEqual(out["officeUnits"]["Desk"]["devices"][0]["derived"],
                         {"serves": "X:835", "controls": ["X:835WLS"], "indications": ["X:835WLK", "X:835WLQK", "X:1NATK", "X:MC1K"]})
        self.assertEqual(only(diags, "desk"), [])

    def test_a_bound_pin_with_no_token_field_is_missing_and_binds_nothing(self):
        m = self.model([lever("835", "NWS", "NWK", Control_NWS=None)])
        out, diags = run(m)
        self.assertEqual(only(diags, "desk"), [("desk.token", "0")])
        self.assertEqual(out["officeUnits"]["Desk"]["devices"][0]["derived"], {"serves": "X:835", "indications": ["X:835NWK"]})
        self.assertEqual(stations(m)[0][("X", None)][0], [])

    def test_an_indication_that_does_not_parse_is_an_error(self):
        _, diags = run(self.model([lever("835", "NWK", Indication_NWK="835NWK |"), lamp("(1NATK")]))
        self.assertEqual(only(diags, "desk"), [("desk.expression", "0"), ("desk.expression", "1")])

    def test_a_lamp_reads_its_indication_expression(self):
        out, diags = run(self.model([lamp("1NATK|!X:MC1K, 835T1K")]))
        self.assertEqual(out["officeUnits"]["Desk"]["devices"][0]["derived"],
                         {"indications": ["X:1NATK", "X:MC1K", "X:835T1K"], "expression": "X:1NATK | !X:MC1K | X:835T1K"})
        self.assertEqual(only(diags, "desk", "lamp", "reference"), [])

    def test_a_lamp_without_indication_falls_back_to_its_legacy_token_at_info(self):
        out, diags = run(self.model([lamp("", IndicationToken="1NAT, MC1K"), lamp("1NATK", IndicationToken="9T")]))
        devs = out["officeUnits"]["Desk"]["devices"]
        self.assertEqual(devs[0]["derived"], {"indications": ["X:1NATK", "X:MC1K"], "expression": "X:1NATK | X:MC1K"})
        self.assertEqual(devs[1]["derived"]["indications"], ["X:1NATK"])           # Indication wins; no fallback
        self.assertEqual(only(diags, "desk", "reference"), [("desk.legacy_token", "0")])
        _, report = derive.derive(self.model([lamp("", IndicationToken="1NAT")]))
        self.assertEqual([d.severity for d in report.by_code("desk.legacy_token")], ["info"])

    def test_an_indication_no_appliance_reports_is_an_error(self):
        """A lever's own tokens need no reporter (its column's station does the work); a lamp's do."""
        _, diags = run(self.model([lever("835", "NWS", "NWK"), lamp("9TK")]))
        self.assertEqual(only(diags, "reference"), [("reference.unresolved", "1")])

    def test_a_lever_serves_a_switch_a_maintainer_call_or_its_masts(self):
        _, diags = run(self.model([lever("835", "WLS"), lever("836", "HS"), lever("MC1", "S"), lever("999", "HS")]))
        self.assertEqual(only(diags, "lever"), [("lever.serves", "3")])


class NoLever(unittest.TestCase):
    """The 832 lesson (the owner, 2026-10-28): switches and locks the dispatcher works over a code line with no desk lever
    serving them are one missing fact per interlocking, since an NX selection the drawing cannot state yet may work
    them. A manual switch, a derail and a gang follower need none; masts are not checked yet."""

    def warnings(self, levers: list[str], line: bool = True) -> list[tuple[str, str]]:
        things = TWO_HOUSES + "1 | appliance | Appliance=switch Style=manual_sensed CP_Name=North\n" \
                              "795D | appliance | Appliance=switch Style=derail CP_Name=North\n"
        m = layout(X=interlocking(things, TWO_HOUSES_WIRES, NORTH_SOUTH))
        if line:
            on_line(m, "X")
        desk(m, {"1": "X"}, [lever(n, "NWS", column="Desk:1") for n in levers])
        self.report = derive.derive(m)[1]
        return only(run(m)[1], "appliance", "interlocking")

    def test_switches_with_no_lever_are_one_missing_fact_of_their_interlocking(self):
        self.assertEqual(self.warnings(["813", "815"]), [("interlocking.no_lever", "X")])
        (d,) = self.report.by_code("interlocking.no_lever")
        self.assertEqual((d.severity, d.where, d.entities), ("missing", "interlockings/X", ("interlockings/X", "interlockings/X/appliances/817")))
        self.assertIn("1 powered switch has no desk lever in this file; how the dispatcher works it (an NX selection, another office unit) is not drawn yet (817)", d.text)
        self.warnings([])
        self.assertIn("3 powered switches have no desk lever in this file; how the dispatcher works them (an NX selection, another office unit) is not drawn yet (813, 815, 817)",
                      self.report.by_code("interlocking.no_lever")[0].text)
        self.assertEqual(self.warnings(["813", "815", "817"]), [])

    def test_an_interlocking_on_no_code_line_has_no_dispatcher(self):
        self.assertEqual(self.warnings([], line=False), [])


class Heads(unittest.TestCase):
    def check(self, mast: str, style: str, devices: list[tuple[str, str]]) -> list[tuple[str, str]]:
        ix = interlocking(f"{mast} | appliance | Appliance=mast Style=single\n", "", "East")
        ix["appliances"][mast]["heads"] = {mast[-1]: {"given": {"Appliance": "head", "Style": style}}}
        ix["devices"] = [{"given": {"Appliance": a, "Style": s, "Head": mast[-1]}, "relations": {"mast": f"X:{mast}"}} for a, s in devices]
        return only(run(layout(X=ix))[1], "head")

    def test_a_device_of_another_style_than_its_trackplan_head_is_an_error(self):
        self.assertEqual(self.check("100NA", "CPL", [("head", "CL")]), [("head.vocabulary", "0")])

    def test_a_semaphores_night_lamp_is_allowed(self):
        self.assertEqual(self.check("100SB", "UQ", [("head", "UQ"), ("head", "CL")]), [])


class Strip(unittest.TestCase):
    def test_strip_removes_every_derived_map_and_what_held_nothing_else(self):
        m = {"a": {"given": {"x": "1"}, "derived": {"y": 2}}, "track": {"links": [{"derived": {"ports": []}}]},
             "rows": [{"derived": {}}, {}], "provenance": {"rules": "0.1.0", "writer": {}}}
        self.assertEqual(derive.strip(m), {"a": {"given": {"x": "1"}}, "rows": [{}], "provenance": {"writer": {}}})

    def test_derive_ignores_a_derived_already_in_the_file(self):
        m = layout(X=interlocking(ONE_SWITCH, ONE_SWITCH_WIRES, "East"))
        stale = copy.deepcopy(m)
        stale["interlockings"]["X"]["appliances"]["835"]["derived"] = {"osCircuit": "X:999T", "controlPoint": "X:West"}
        self.assertEqual(layout_model.dumps(derive.derive(stale)[0]), layout_model.dumps(derive.derive(m)[0]))


class SPCoastExample(unittest.TestCase):
    """The gate (ADR 0011 §5): the committed example, stripped of every derived map and derived again, is the same
    bytes, with the importer's diagnostic counts."""

    def test_strip_then_derive_is_the_example(self):
        text = EXAMPLE.read_text(encoding="utf-8")
        stripped = derive.strip(layout_model.loads(text))
        self.assertNotIn('"derived"', layout_model.dumps(stripped))
        self.assertNotIn("rules", stripped["provenance"])
        out, report = derive.derive(stripped)
        self.assertEqual(layout_model.dumps(out), text)
        self.assertEqual(report.counts(), {"error": 0, "warning": 0, "info": 8, "missing": 2})


if __name__ == "__main__":
    unittest.main()
