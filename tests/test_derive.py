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
835    | appliance | Appliance=switch Style=lock TC=835T1 Indication=835T1K
836NAB | appliance | Appliance=mast Style=double Kind=CONTROLLED
836SA  | appliance | Appliance=mast Style=single Kind=CONTROLLED
836SB  | appliance | Appliance=mast Style=dwarf Kind=CONTROLLED
1NAT   | appliance | Appliance=track_circuit Indication=1NATK
1SAT   | appliance | Appliance=track_circuit Indication=1SATK
2SAT   | appliance | Appliance=track_circuit Indication=2SATK
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
795  | appliance | Appliance=switch Style=lock TC=795T1 Indication=795T1K
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

    def test_a_mast_states_what_it_is_or_is_missing(self):
        """ADR 0013 §5: Kind CONTROLLED, ABSOLUTE or PERMISSIVE is a stated fact; none, or another word, is missing."""
        _, diags = run(layout(X=interlocking(ONE_SWITCH.replace("Style=dwarf Kind=CONTROLLED", "Style=dwarf"), ONE_SWITCH_WIRES, "East")))
        self.assertEqual(only(diags, "mast"), [("mast.kind", "836SB")])
        _, diags = run(layout(X=interlocking(ONE_SWITCH.replace("Style=dwarf Kind=CONTROLLED", "Style=dwarf Kind=AUTOMATIC"), ONE_SWITCH_WIRES, "East")))
        self.assertEqual(only(diags, "mast"), [("mast.kind", "836SB")])
        self.assertEqual(derive.derive(layout(X=interlocking(ONE_SWITCH.replace("Style=dwarf Kind=CONTROLLED", "Style=dwarf"), ONE_SWITCH_WIRES, "East")))[1]
                         .by_code("mast.kind")[0].severity, "missing")
        for kind in ("CONTROLLED", "ABSOLUTE", "PERMISSIVE"):
            _, diags = run(layout(X=interlocking(ONE_SWITCH.replace("Style=dwarf Kind=CONTROLLED", f"Style=dwarf Kind={kind}"), ONE_SWITCH_WIRES, "East")))
            self.assertEqual(only(diags, "mast"), [], kind)

    def test_a_mast_that_is_not_controlled_over_a_powered_switch_is_a_warning(self):
        """ADR 0013 §5: a PERMISSIVE or ABSOLUTE mast whose governed circuit holds a powered switch or derail port (§4:
        Style powered or dual, or a CP Name) is reported; over an electric lock, a hand-throw switch or a switch on its
        approach side it is not; a CONTROLLED mast never is. The check sets nothing."""
        def masts(things: str, wires: str = ONE_SWITCH_WIRES) -> list[tuple[str, str]]:
            return only(run(layout(X=interlocking(things, wires, "East")))[1], "mast")
        permissive = ONE_SWITCH.replace("836SA  | appliance | Appliance=mast Style=single Kind=CONTROLLED",
                                        "836SA  | appliance | Appliance=mast Style=single Kind=PERMISSIVE")
        self.assertEqual(masts(permissive), [])                                                   # 835 is an electric lock
        self.assertEqual(masts(permissive.replace("Style=lock", "Style=powered")), [("mast.powered", "836SA")])
        self.assertEqual(masts(permissive.replace("Style=lock", "Style=manual_sensed CP_Name=East")), [])
        self.assertEqual(masts(permissive.replace("Style=lock", "Style=lock CP_Name=East")), [])
        self.assertEqual(masts(permissive.replace("Kind=PERMISSIVE", "Kind=ABSOLUTE").replace("Style=lock", "Style=dual")), [("mast.powered", "836SA")])
        self.assertEqual(masts(ONE_SWITCH.replace("Style=lock", "Style=powered")), [])            # all CONTROLLED
        d = derive.derive(layout(X=interlocking(permissive.replace("Style=lock", "Style=powered"), ONE_SWITCH_WIRES, "East")))[1].by_code("mast.powered")[0]
        self.assertEqual((d.severity, d.entities), ("warning", ("interlockings/X/appliances/836SA", "interlockings/X/appliances/835")))
        self.assertIn("passes powered switch 835 on X:835T1", d.text)
        # the switch on the approach side only: 836SA's governed side is J2.governed on 835.N; turn J2 around
        turned = ONE_SWITCH_WIRES.replace("n  | 835.N J2.governed", "n  | 835.N J2.approach").replace("e1 | J2.approach 1SAT.TC", "e1 | J2.governed 1SAT.TC")
        self.assertEqual(masts(permissive.replace("Style=lock", "Style=powered"), turned), [])

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


class DoubleJoint(unittest.TestCase):
    """ADR 0013 §6: a joint of Kind IRJ_SIGNALS with relations.masts counts as the signal joint of each mast; each mast's
    governed circuit is the side its pin names, its approach the other."""

    def block(self, masts: dict) -> dict:
        ix = interlocking("832T | appliance | Appliance=track_circuit\n834T | appliance | Appliance=track_circuit\n"
                          "832NA | appliance | Appliance=mast Style=single Kind=PERMISSIVE\n"
                          "832SA | appliance | Appliance=mast Style=single Kind=PERMISSIVE\n"
                          "J1 | joints | Kind=IRJ_SIGNALS\n", "a | J1.A 832T.TC\nb | J1.B 834T.TC\n", "East")
        row(ix, "J1").setdefault("relations", {})["masts"] = masts
        return layout(X=ix)

    def test_a_mast_on_a_double_joint_stands_on_a_joint_and_has_its_sides(self):
        out, diags = run(self.block({"A": "X:832NA", "B": "X:832SA"}))
        self.assertEqual(only(diags, "mast", "joint"), [])
        apps = out["interlockings"]["X"]["appliances"]
        self.assertEqual(apps["832NA"]["derived"]["circuits"], {"governed": "X:832T", "approach": "X:834T"})
        self.assertEqual(apps["832SA"]["derived"]["circuits"], {"governed": "X:834T", "approach": "X:832T"})
        self.assertEqual(row(out["interlockings"]["X"], "J1")["derived"], {"circuits": {"A": "X:832T", "B": "X:834T"}})
        self.assertEqual(layout_model.errors(out), [])

    def test_a_boundary_track_circuit_counts_toward_the_circuit_on_each_pin_and_names_none(self):
        """ADR 0013 §10: derived.circuits on the boundary, A then B; the markers name the circuits, never the boundary."""
        m = self.block({"A": "X:832NA", "B": "X:832SA"})
        ix = m["interlockings"]["X"]
        ix["appliances"]["833T"] = {"given": {"Appliance": "track_circuit", "Style": "boundary"},
                                    "relations": {"A": ["J1.A", "X:832T.TC"], "B": ["J1.B", "X:834T.TC"]}}
        out, diags = run(m)
        self.assertEqual(only(diags, "circuit"), [])
        self.assertEqual(out["interlockings"]["X"]["appliances"]["833T"]["derived"]["circuits"], {"A": "X:832T", "B": "X:834T"})
        self.assertEqual(row(out["interlockings"]["X"], "J1")["derived"]["circuits"], {"A": "X:832T", "B": "X:834T"})
        del ix["appliances"]["834T"]
        out, diags = run(m)
        self.assertEqual(only(diags, "circuit"), [])
        self.assertEqual(out["interlockings"]["X"]["appliances"]["833T"]["derived"]["circuits"], {"A": "X:832T"})
        self.assertEqual(layout_model.errors(out), [])

    def test_a_plate_requires_a_permissive_mast(self):
        """ADR 0013 §5: a plate on no mast, on a mast the file lacks, or on one that is not PERMISSIVE is an error."""
        def plated(mast: str | None, kind: str = "PERMISSIVE") -> list[tuple[str, str]]:
            m = self.block({"A": "X:832NA", "B": "X:832SA"})
            ix = m["interlockings"]["X"]
            ix["appliances"]["832SA"]["given"]["Kind"] = kind
            ix["track"]["policies"] = [{"id": "PL1", "given": {"Kind": "RULE_290_G"}, **({"relations": {"mast": mast}} if mast else {})}]
            return only(run(m)[1], "plate")
        self.assertEqual(plated("X:832SA"), [])
        self.assertEqual(plated(None), [("plate.mast", "PL1")])
        self.assertEqual(plated("X:9NA"), [("plate.mast", "PL1")])
        self.assertEqual(plated("X:832SA", "CONTROLLED"), [("plate.mast", "PL1")])
        self.assertEqual(plated("X:832SA", ""), [("plate.mast", "PL1")])

    def test_an_automatic_mast_belongs_to_no_control_point(self):
        """ADR 0013 §5 and §4: under one house every appliance is the house's, but an ABSOLUTE or PERMISSIVE mast derives no
        controlPoint (absent, no diagnostic); a CONTROLLED one on the same double joint derives the house."""
        m = self.block({"A": "X:832NA", "B": "X:832SA"})
        m["interlockings"]["X"]["appliances"]["832NA"]["given"]["Kind"] = "CONTROLLED"
        out, diags = run(m)
        apps = out["interlockings"]["X"]["appliances"]
        self.assertEqual(apps["832NA"]["derived"]["controlPoint"], "X:East")
        self.assertNotIn("controlPoint", apps["832SA"]["derived"])
        self.assertEqual(apps["832T"]["derived"]["controlPoint"], "X:East")
        self.assertEqual(only(diags, "control_point"), [])
        m["interlockings"]["X"]["appliances"]["832SA"]["given"]["Kind"] = "ABSOLUTE"
        self.assertNotIn("controlPoint", run(m)[0]["interlockings"]["X"]["appliances"]["832SA"].get("derived", {}))

    def test_a_permissive_mast_on_a_double_joint_over_a_powered_derail_is_a_warning(self):
        """ADR 0013 §5 on a double joint: 832SA governs into side B (834T); an independent derail with a CP Name there is
        powered (§4), one that follows a hand-throw lock is not."""
        m = self.block({"A": "X:832NA", "B": "X:832SA"})
        ix = m["interlockings"]["X"]
        ix["appliances"]["9D"] = {"given": {"Appliance": "switch", "Style": "derail", "CP Name": "East"}, "relations": {"C": ["J1.B", "X:834T.TC"]}}
        row(ix, "J1")["relations"]["B"] = ["X:834T.TC", "X:9D.C"]
        ix["appliances"]["834T"]["relations"]["TC"] = ["J1.B", "X:9D.C"]
        self.assertEqual(only(run(m)[1], "mast"), [("mast.powered", "832SA")])
        ix["appliances"]["9"] = {"given": {"Appliance": "switch", "Style": "lock", "CP Name": "East"}, "relations": {"C": ["J1.B"]}}
        self.assertEqual(only(run(m)[1], "mast"), [])

    def test_a_side_with_no_mast_leaves_that_mast_on_no_joint_and_one_mast_on_both_sides_is_on_two(self):
        out, diags = run(self.block({"A": "X:832NA"}))
        self.assertEqual(only(diags, "mast"), [("mast.joint", "832SA")])
        self.assertNotIn("circuits", out["interlockings"]["X"]["appliances"]["832SA"].get("derived", {}))
        _, diags = run(self.block({"A": "X:832NA", "B": "X:832NA"}))
        self.assertEqual(only(diags, "mast"), [("mast.joint", "832SA"), ("mast.joints", "832NA")])


# Two houses, the Christopher shape: switches 813 and 815 (with 815A in its gang) on North, 817 on South; siding 01T
# between 813's R and 817's R; 815's R meets 815A's R at a plain joint. Each signal states its house on the joint or on
# the mast; approach circuit 1NAT states North though South's signal bounds it.
TWO_HOUSES = """
813   | appliance | Appliance=switch Style=powered TC=813T1 Indication=813T1K CP_Name=North
815   | appliance | Appliance=switch Style=powered TC=815T1 Indication=815T1K CP_Name=North
815A  | appliance | Appliance=switch Style=powered TC=815AT1 Indication=815AT1K
817   | appliance | Appliance=switch Style=powered TC=817T1 Indication=817T1K CP_Name=South
814SA | appliance | Appliance=mast Style=single Kind=CONTROLLED
816NA | appliance | Appliance=mast Style=single Kind=CONTROLLED CP_Name=South
818NA | appliance | Appliance=mast Style=single Kind=CONTROLLED
1SAT  | appliance | Appliance=track_circuit Indication=1SATK
01T   | appliance | Appliance=track_circuit CP_Name=North Indication=01TK
2NAT  | appliance | Appliance=track_circuit Indication=2NATK
1NAT  | appliance | Appliance=track_circuit CP_Name=North Indication=1NATK
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
        _, diags = run(layout(X=interlocking(TWO_HOUSES.replace("Appliance=track_circuit CP_Name=North Indication=01TK", "Appliance=track_circuit Indication=01TK"),
                                             TWO_HOUSES_WIRES, NORTH_SOUTH)))
        self.assertEqual(only(diags, "control_point"), [("control_point.chains", "01T")])

    def test_an_appliance_no_house_reaches_is_an_error(self):
        _, diags = run(layout(X=interlocking(TWO_HOUSES + "NFLK | appliance | Appliance=lamp\n", TWO_HOUSES_WIRES, NORTH_SOUTH)))
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

    def test_one_marked_off_layout_is_reported_nothing_and_pairs_with_nothing(self):
        """ADR 0013 §21 gap 7 (the owner, 2026-11-03): Style off_layout states the interlocking will never be drawn."""
        out, diags = run(layout(X=interlocking("N1 | ends | Kind=NEXT_CP Interlocking=Lick Style=off_layout\n", "", "East")))
        self.assertEqual(only(diags, "next_cp"), [])
        self.assertEqual(row(out["interlockings"]["X"], "N1")["given"], {"Kind": "NEXT_CP", "Interlocking": "Lick", "Style": "off_layout"})
        m = pair(2, 1)
        m["interlockings"]["A"]["track"]["ends"][0]["given"]["Style"] = "off_layout"      # A: one marked, one not; B: one back
        self.assertEqual(only(run(m)[1], "next_cp"), [("next_cp.drawn_neighbour", "N0")])

    def test_the_mark_on_a_neighbour_that_is_drawn_lies(self):
        m = pair(1, 1)
        m["interlockings"]["A"]["track"]["ends"][0]["given"]["Style"] = "off_layout"
        self.assertEqual(only(run(m)[1], "next_cp"), [("next_cp.drawn_neighbour", "N0"), ("next_cp.pair", "B")])
        (d,) = derive.derive(m)[1].by_code("next_cp.drawn_neighbour")
        self.assertEqual((d.severity, d.entities), ("warning", ("interlockings/A/track/ends/N0", "interlockings/B")))
        self.assertEqual(d.text, "A: a NextCP to B is marked off_layout, but B is on this layout")

    def test_a_next_cp_whose_track_is_drawn_through_to_the_neighbour_is_redundant(self):
        """ADR 0013 §7.1: block track drawn across sheets replaces the NextCP inside CTC. A's NextCP to B stands on a wire
        that also reaches B's marker (by name) or B's joint (by its id): warning, with B as the second party, and the
        drawn circuit stands. A NextCP on a wire that reaches no other interlocking's track is kept, as is next_cp.pair."""
        a = interlocking("N1 | ends | Kind=NEXT_CP Interlocking=B\n", "w | N1.track B:2T.TC\n", "A", "A")
        b = interlocking("N2 | ends | Kind=NEXT_CP Interlocking=A\n2T | appliance | Appliance=track_circuit\nJ9 | joints | Kind=IRJ\n",
                         "w | N2.track 2T.TC\n", "B", "B")
        out, diags = run(layout(A=a, B=b))
        self.assertEqual(diags, [("next_cp.drawn", "N1")])
        d = derive.derive(layout(A=a, B=b))[1].by_code("next_cp.drawn")[0]
        self.assertEqual((d.severity, d.entities), ("warning", ("interlockings/A/track/ends/N1", "interlockings/B")))
        self.assertIn("drawn through to B's (B:2T.TC)", d.text)
        self.assertEqual(row(out["interlockings"]["A"], "N1")["derived"]["circuits"], {"track": "B:2T"})
        by_id = interlocking("N1 | ends | Kind=NEXT_CP Interlocking=B\n", "", "A", "A")
        row(by_id, "N1")["relations"] = {"track": ["J9.B"]}                                   # B's unnamed joint, by its id
        self.assertEqual(run(layout(A=by_id, B=b))[1], [("next_cp.drawn", "N1")])
        self.assertEqual(run(pair(1, 1))[1], [])


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


def stations(model: dict) -> tuple[dict, list[tuple[str, str]], codeline.Codeline]:
    """The derivation's diagnostics, and the code line computed from its output: (station -> (controls, indications))."""
    out, report = derive.derive(model)
    line = codeline.stations(out)
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

    def test_a_field_appliance_reports_what_the_desk_device_serving_it_states(self):
        """A field appliance other than a track circuit states no token: the desk device that serves it does, per bound
        pin. A manual switch, a derail, a gang follower and a mast no device states a token for report nothing; nor does
        a mast for a signal lever's token, since a signal lever serves no appliance (masts report nothing)."""
        things = TWO_HOUSES + "1 | appliance | Appliance=switch Style=manual CP_Name=North\n795D | appliance | Appliance=switch Style=derail CP_Name=North\n"
        m = desk(on_line(layout(X=interlocking(things, TWO_HOUSES_WIRES, NORTH_SOUTH)), "X"), {"1": "North"}, [
            *(lamp(t) for t in ("1NWK", "795DNWK", "815ANWK", "814SAK", "816NGK", "815NWK")),
            lever("815", "NWS", "NWK", column="Desk:1"), lever("816", "NGS", "NGK", column="Desk:1")])
        got, diags, _ = stations(m)
        self.assertEqual(only(diags, "reference"), [("reference.unresolved", str(i)) for i in range(5)])
        out, _ = derive.derive(m)
        self.assertEqual(codeline.reporters(out, "X", "815NWK"), [codeline.Reporter("switch", "815")])
        self.assertEqual(codeline.reporters(out, "X", "816NGK"), [])

    def test_a_reporter_states_one_token_and_a_missing_field_is_unresolved(self):
        """A field naming one token states it, negated or not; an expression over several is a composite the desk
        consumes and states none. A track circuit with no Indication reports nothing: it is not done yet, never filled
        in from the reference data's template."""
        things = TWO_HOUSES.replace("2NAT  | appliance | Appliance=track_circuit Indication=2NATK", "2NAT  | appliance | Appliance=track_circuit")
        m = desk(on_line(layout(X=interlocking(things, TWO_HOUSES_WIRES, NORTH_SOUTH)), "X"), {"1": "North", "2": "South"}, [
            lever("815", "NWK", "RWK", column="Desk:1", Indication_RWK="815RWK & 1NATK"),
            lever("817", "NWK", column="Desk:2", Indication_NWK="!X:817NWK"),
            *(lamp(t) for t in ("815NWK", "815RWK", "817NWK", "2NATK"))])
        _, diags, _ = stations(m)
        self.assertEqual(only(diags, "reference"), [("reference.unresolved", "3"), ("reference.unresolved", "5")])
        out, _ = derive.derive(m)
        self.assertEqual(codeline.reporters(out, "X", "817nwk"), [codeline.Reporter("switch", "817")])

    def test_a_field_lamp_and_a_switchs_os_circuit_report_what_they_state(self):
        """A field lamp states its own token, a switch its OS circuit's, a virtual track circuit its own."""
        things = ONE_SWITCH + "HBA | appliance | Appliance=lamp Indication=HBAK\n" \
                              "NFL | appliance | Appliance=lamp Indication=NFLK\n" \
                              "0100T | appliance | Appliance=track_circuit Style=virtual Members=1NAT Indication=0100TK\n"
        m = desk(on_line(layout(X=interlocking(things, ONE_SWITCH_WIRES, "East")), "X"), {}, [lamp("HBAK | NFLK | 0100TK | 835T1K")])
        got, diags, line = stations(m)
        self.assertEqual(only(diags, "reference"), [])
        self.assertEqual(got[("X", None)][1], ["0100TK", "835T1K", "HBAK", "NFLK"])
        self.assertEqual(codeline.reporters(derive.derive(m)[0], "X", "835T1K"), [codeline.Reporter("track_circuit", "835", "835T1")])

    def test_a_lamp_token_two_houses_report_is_a_warning(self):
        """815A's TC names 815AT1 (North, by its gang); a marker 815AT1 states South."""
        things = TWO_HOUSES + "815AT1 | appliance | Appliance=track_circuit CP_Name=South Indication=815AT1K\n"
        m = desk(on_line(layout(X=interlocking(things, TWO_HOUSES_WIRES, NORTH_SOUTH)), "X", kind="USS506"), {}, [lamp("815AT1K")])
        _, diags, line = stations(m)
        self.assertEqual(only(diags, "reference"), [("reference.station", "0")])
        self.assertEqual([p.kind for p in line.problems], ["station"])

    def test_a_token_no_appliance_states_is_unresolved_never_filled_in_from_a_template(self):
        """A switch with no Indication states no OS circuit token; HBA states none; the templates are not read."""
        things = "9 | appliance | Appliance=switch Style=powered TC=9T1\nHBA | appliance | Appliance=lamp\n" \
                 "9T | appliance | Appliance=track_circuit Indication=9TK\n"
        m = desk(on_line(layout(X=interlocking(things, "", "East")), "X"), {}, [lamp("9T1K"), lamp("HBAK"), lamp("9TK")])
        got, diags, _ = stations(m)
        self.assertEqual(got[("X", None)][1], ["9TK"])
        self.assertEqual(only(diags, "reference"), [("reference.unresolved", "0"), ("reference.unresolved", "1")])

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
5    | appliance | Appliance=switch Style=lock TC=5T1 Indication=5T1K
6    | appliance | Appliance=switch Style=derail
7    | appliance | Appliance=switch Style=powered TC=7T1 Indication=7T1K
8    | appliance | Appliance=switch Style=derail CP_Name=West
3NAT | appliance | Appliance=track_circuit Indication=3NATK
J5   | joints    | Kind=IRJ
""", "y1 | 5.C 6.C\ny2 | 5.N J5.A\ny3 | J5.B 3NAT.TC\ny4 | 7.C 8.C\n", "West", "Y")

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

    def test_plain_track_drawn_to_another_interlockings_marker_is_block_track_and_names_the_circuit(self):
        """ADR 0013 §7.1: a track net joining two interlockings is block track; the other sheet's marker names the circuit
        on this side, and no consumer and no token come of it (the block's token is the codeline library's, R12)."""
        out, diags = run(self.model("", "a | J1.A Y:3NAT.TC\n"))
        self.assertEqual(only(diags, "reference"), [])
        self.assertEqual(row(out["interlockings"]["X"], "J1")["derived"]["circuits"], {"A": "Y:3NAT", "B": "X:1SAT"})
        self.assertNotIn("consumers", out["interlockings"]["X"]["track"])
        self.assertNotIn("3NATK", stations(self.model("", "a | J1.A Y:3NAT.TC\n"))[0][("Y", None)][1])

    def test_a_joining_wire_with_a_hand_throw_switch_is_block_track_too(self):
        """ADR 0013 §4: a hand-throw switch may lie in a block; Y's 5 (Style lock) on the wire is no error, and the wire's
        circuit is Y's 5T1 through its TC (named by Y's own switch, so dark here: no marker names it)."""
        self.assertEqual(self.check("", "a | J1.A Y:5.R\n"), [])

    def test_a_joining_wire_with_a_powered_switch_or_derail_is_an_error(self):
        """ADR 0013 §4 and §7.1: a piece with a powered switch or derail is never block track, so the wire is interlocking
        track and leaves an interlocking only at a NextCP or an END_CTC (ADR 0009 §3.12); a switch the file lacks counts
        as powered."""
        self.assertEqual(self.check("", "a | J1.A Y:7.R Y:8.R\n"), [("reference.track", "X"), ("reference.track", "X")])
        self.assertIn("powered switch port Y:7.R", derive.derive(self.model("", "a | J1.A Y:7.R\n"))[1].by_code("reference.track")[0].text)
        d = derive.derive(self.model("", "a | J1.A Y:7.R\n"))[1].by_code("reference.track")[0]
        self.assertEqual(d.entities, ("interlockings/X", "interlockings/Y", "interlockings/Y/appliances/7"))
        self.assertEqual(self.check("9 | appliance | Appliance=switch Style=powered\n", "a | J1.A Y:3NAT.TC 9.C\n"), [("reference.track", "X")])
        self.assertEqual(self.check("9 | appliance | Appliance=switch Style=derail CP_Name=East\n", "a | J1.A Y:3NAT.TC 9.C\n"), [("reference.track", "X")])
        self.assertEqual(self.check("9 | appliance | Appliance=switch Style=lock CP_Name=East\n", "a | J1.A Y:3NAT.TC 9.C\n"), [])
        self.assertEqual(self.check("9 | appliance | Appliance=switch Style=manual_sensed CP_Name=East\n", "a | J1.A Y:3NAT.TC 9.C\n"), [])
        dependent = "9 | appliance | Appliance=switch Style=lock CP_Name=East\n9D | appliance | Appliance=switch Style=derail CP_Name=East\n"
        self.assertEqual(self.check(dependent, "a | J1.A Y:3NAT.TC 9.C 9D.C\n"), [])   # a dependent derail follows its lock

    def test_a_track_row_named_for_another_interlocking_is_an_error(self):
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
        out, diags = run(self.model([lamp("1NATK|!X:MC1K, 835T1K"), lever("MC1", "S", "K")]))
        self.assertEqual(out["officeUnits"]["Desk"]["devices"][0]["derived"],
                         {"indications": ["X:1NATK", "X:MC1K", "X:835T1K"], "expression": "X:1NATK | !X:MC1K | X:835T1K"})
        self.assertEqual(only(diags, "desk", "lamp", "reference"), [])

    def test_a_lamp_without_indication_falls_back_to_its_legacy_token_at_info(self):
        out, diags = run(self.model([lamp("", IndicationToken="1NAT, MC1K"), lamp("1NATK", IndicationToken="9T"), lever("MC1", "S", "K")]))
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
        ix = interlocking(f"{mast} | appliance | Appliance=mast Style=single Kind=CONTROLLED\n", "", "East")
        ix["appliances"][mast]["heads"] = {mast[-1]: {"given": {"Appliance": "head", "Style": style}}}
        ix["devices"] = [{"given": {"Appliance": a, "Style": s, "Head": mast[-1]}, "relations": {"mast": f"X:{mast}"}} for a, s in devices]
        return only(run(layout(X=ix))[1], "head")

    def test_a_device_of_another_style_than_its_trackplan_head_is_an_error(self):
        self.assertEqual(self.check("100NA", "CPL", [("head", "CL")]), [("head.vocabulary", "0")])

    def test_a_semaphores_night_lamp_is_allowed(self):
        self.assertEqual(self.check("100SB", "UQ", [("head", "UQ"), ("head", "CL")]), [])


class TrainOrders(unittest.TestCase):
    """A train order signal (Appliance train_order; the owner, 2026-11-03): never in a control point, its heads facing
    the direction their letters name (ADR 0003 D1), standing at a timetable station of layout.stations."""

    TO = "Gilroy | appliance | Appliance=train_order Station=Gilroy rel.station=Gilroy\n"

    def model(self, plan=(TWO_HOUSES, TWO_HOUSES_WIRES, NORTH_SOUTH), stations=("Gilroy",)) -> dict:
        things, wires, houses = plan
        ix = interlocking(things + self.TO, wires, houses)
        ix["appliances"]["Gilroy"]["heads"] = {k: {"given": {"Appliance": "head", "Style": "LQ"}} for k in ("N", "S")}
        m = layout(X=ix)
        m["layout"]["stations"] = {s: {"given": {"Milepost": "77.9"}} for s in stations}
        return m

    def test_it_derives_no_control_point_and_breaks_no_chain(self):
        for plan in ((TWO_HOUSES, TWO_HOUSES_WIRES, NORTH_SOUTH), (ONE_SWITCH, ONE_SWITCH_WIRES, "East")):
            out, diags = run(self.model(plan))
            self.assertEqual(only(diags, "control_point", "train_order", "mast", "lever", "interlocking"), [], plan[2])
            to = out["interlockings"]["X"]["appliances"]["Gilroy"]
            self.assertNotIn("controlPoint", to.get("derived", {}), plan[2])
            self.assertEqual({n: cp for n, cp in control_points(out).items() if n != "Gilroy"}, control_points(run(layout(X=interlocking(*plan)))[0]))

    def test_each_head_faces_the_direction_its_letter_names(self):
        out, _ = run(self.model())
        heads = out["interlockings"]["X"]["appliances"]["Gilroy"]["heads"]
        self.assertEqual({k: h["derived"] for k, h in heads.items()}, {"N": {"direction": "LEFT"}, "S": {"direction": "RIGHT"}})
        self.assertEqual(layout_model.errors(out), [])
        mast = out["interlockings"]["X"]["appliances"]["814SA"]
        self.assertEqual([h for h in mast.get("heads", {}).values() if "derived" in h], [])         # a mast's head derives none

    def test_a_station_the_layout_does_not_draw_is_missing(self):
        _, diags = run(self.model(stations=("Lick",)))
        self.assertEqual(only(diags, "train_order"), [("train_order.station", "Gilroy")])
        _, diags = run(self.model(stations=("gilroy",)))                                           # names fold case
        self.assertEqual(only(diags, "train_order"), [])
        m = self.model()
        del m["interlockings"]["X"]["appliances"]["Gilroy"]["relations"]
        self.assertEqual(only(run(m)[1], "train_order"), [("train_order.station", "Gilroy")])


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


def wired(m: dict, anchors: dict[str, list[str]], codelines: dict[str, tuple[str, str]] = {}, encodings: dict[str, tuple[str, str]] = {},
          runs: dict[str, str] = {}) -> dict:
    """Transports by name with the processors that anchor them; code lines and I/O encodings as name: (transport, processor);
    each interlocking's processor. Every processor named is in ``layout.processors``."""
    layout = m["layout"]
    layout["transports"] = {t: {"given": {"Kind": t}, "relations": {"anchors": ps}} for t, ps in anchors.items()}
    layout["codelines"] = {c: {"given": {"Kind": "AAR"}, "relations": {"transport": t, "processor": p}} for c, (t, p) in codelines.items()}
    layout["ioEncodings"] = {e: {"given": {"Kind": e}, "relations": {"transport": t, "processor": p}} for e, (t, p) in encodings.items()}
    names = {p for ps in anchors.values() for p in ps} | {p for _, p in codelines.values()} | {p for _, p in encodings.values()} | set(runs.values())
    layout["processors"] = {p: {"given": {"Kind": "PROCESSOR"}} for p in sorted(names)}
    for ix, p in runs.items():
        m["interlockings"][ix].setdefault("relations", {})["processor"] = p
    return m


class Reach(unittest.TestCase):
    """ADR 0008 §4.9 (the owner, 2026-10-24 and 2026-11-03): a FieldUnit reaches its code line's transport through the
    code line, written as its processor's ``derived.transports``; an anchored instance nothing rides on a processor that
    already reaches that transport through a code line is an unneeded duplicate, ``transport.reach`` at info."""

    def model(self, **kw) -> dict:
        m = on_line(layout(X=interlocking(ONE_SWITCH, ONE_SWITCH_WIRES, "East")), "X")
        return wired(m, codelines={"Line": ("MQTT", "Office")}, runs={"X": "Field"}, **kw)

    def transports(self, out: dict) -> dict[str, list[str]]:
        return {p: proc["derived"]["transports"] for p, proc in out["layout"]["processors"].items()}

    def test_a_field_processor_that_anchors_nothing_reaches_its_code_lines_transport_and_nothing_is_reported(self):
        out, diags = run(self.model(anchors={"MQTT": ["Office"]}))
        self.assertEqual(only(diags, "transport"), [])
        self.assertEqual(self.transports(out), {"Field": ["MQTT"], "Office": ["MQTT"]})

    def test_an_anchor_nothing_rides_beside_the_code_lines_reach_is_an_unneeded_duplicate(self):
        m = self.model(anchors={"MQTT": ["Field", "Office"]})
        out, diags = run(m)
        self.assertEqual(only(diags, "transport"), [("transport.reach", "MQTT")])
        (d,) = derive.derive(m)[1].by_code("transport.reach")
        self.assertEqual(d.severity, "info")
        self.assertEqual(d.entities, ("layout/transports/MQTT", "layout/processors/Field", "interlockings/X"))
        self.assertEqual(d.text, "processor Field anchors an MQTT instance nothing rides; its FieldUnit X already reaches MQTT through code line Line")
        self.assertEqual(self.transports(out), {"Field": ["MQTT"], "Office": ["MQTT"]})

    def test_an_anchor_an_encoding_rides_is_not_a_duplicate(self):
        """Gilroy Caltrain's shape: the field processor anchors MQTT for its JMRI I/O encoding and its code line rides
        MQTT elsewhere; the office's anchor is ridden by the code line."""
        out, diags = run(self.model(anchors={"MQTT": ["Field", "Office"]}, encodings={"JMRI": ("MQTT", "Field")}))
        self.assertEqual(only(diags, "transport"), [])

    def test_an_anchor_of_a_transport_no_code_line_reaches_is_listed_and_not_reported(self):
        out, diags = run(self.model(anchors={"MQTT": ["Office"], "CMRInet": ["Field"]}))
        self.assertEqual(only(diags, "transport"), [])
        self.assertEqual(self.transports(out), {"Field": ["CMRInet", "MQTT"], "Office": ["MQTT"]})


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
        self.assertEqual(report.counts(), {"error": 0, "warning": 0, "info": 0, "missing": 2})    # 2 interlocking.no_lever (Railroad 28647dc)


if __name__ == "__main__":
    unittest.main()
