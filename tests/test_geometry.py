"""Gates for the geometry piece of the KiCad importer (ADR 0010; ADR 0011 §7; DoD2, DoD3, the §4.3 transform, §4.9 glyphs).

The rules are tested on symbols and placements built in memory: the anchor, the style rule, the glyph frame, the
transform for every orientation KiCad can write (the direction of a 90-degree turn was asked of kicad-cli by
``tests/fixtures/kicad/rotation_probe.py``, 2026-10-25: counter-clockwise as seen on the page), the chaining of
wires into runs. The project gates run on the SPCoast test corpus as ``tests.spcoast_corpus.spcoast_source`` reads it (the
drawing at the pinned commit, a fresh export), never faked when absent. Geometry
joins the rest of the file by identity only (three-maps D10): markers name their track row by id, runs name what
their ends meet.
"""
from __future__ import annotations

import copy
import math
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS) not in sys.path:                       # kicad_services imports itself as a top-level package
    sys.path.insert(0, str(TOOLS))

from kicad_services.schematic_reader import SchematicPlacementReader  # noqa: E402
from tools import layout_model
from tools.kicad_services import sch_text
from tools.kicad_services.types import LibrarySymbol, SchematicPlacement, SymbolGraphic, SymbolPin
from tools.layout_compiler import emit, geometry, seams
from tests.spcoast_corpus import AVAILABLE as SPCOAST_AVAILABLE, WHY_SKIPPED, spcoast_source


def pin(name, x, y, rotation=0.0, length=0.0, hidden=False, number=None):
    return SymbolPin(number or name, name, "passive", x, y, rotation, length, hidden)


def switch_like():
    """A three-pin glyph shaped like a switch: C at the library origin's left, N right, R up and right (y up)."""
    return LibrarySymbol("Sw", "SW", (pin("C", -11.43, 0.0), pin("N", 17.78, 0.0, 180.0), pin("R", 17.78, 16.51, 180.0)),
                         graphics=(SymbolGraphic("polyline", ((-11.43, 0.0), (17.78, 0.0)), stroke_width=0.4064, stroke_type="default", fill_type="none"),
                                   SymbolGraphic("polyline", ((0.0, 0.0), (17.78, 16.51)), stroke_width=0, stroke_type="default", fill_type="none"),
                                   SymbolGraphic("circle", ((2.54, -5.08),), radius=1.27, stroke_width=0, stroke_type="default", fill_type="color", fill_color=(255.0, 255.0, 0.0, 1.0)),
                                   SymbolGraphic("text", ((5.08, 2.54),), text="H", size=1.27, justify="left bottom")))


# The sides of each track row as the model names them (ADR 0012 §8; three-maps D15); a policy sign's is track.
SIDES = {"IRJ_SIGNAL": {"approach", "governed"}, "IRJ": {"A", "B"}, "IRJ_SIGNALS": {"A", "B"}, "NEXT_CP": {"track"},
         "INDUSTRY": {"EoT"}, "BUMPER": {"EoT"}}


class GlyphRules(unittest.TestCase):
    def test_anchor_is_the_lowest_then_leftmost_pin(self):
        self.assertEqual(geometry.anchor_of({"C": (-11.43, 0.0), "N": (17.78, 0.0), "R": (17.78, 16.51)}), (-11.43, 0.0))
        self.assertEqual(geometry.anchor_of({"A": (-2.54, 0.0), "B": (2.54, 0.0)}), (-2.54, 0.0))     # a joint: its left pin
        self.assertEqual(geometry.anchor_of({"Track": (0.0, -2.54)}), (0.0, -2.54))                 # one pin: that pin
        self.assertEqual(geometry.anchor_of({"lo": (5.0, -1.0), "left": (-5.0, 0.0)}), (5.0, -1.0))  # lowest wins over leftmost
        self.assertEqual(geometry.anchor_of({}), (0.0, 0.0))

    def test_style_is_written_only_where_not_kicads_default(self):
        plain = SymbolGraphic("polyline", stroke_width=0, stroke_type="default", fill_type="none")
        self.assertEqual(geometry.style_of(plain), {})
        wide = SymbolGraphic("polyline", stroke_width=0.4064, stroke_type="solid", fill_type="none")
        self.assertEqual(geometry.style_of(wide), {"stroke": {"width": 0.4064}})
        dashed = SymbolGraphic("polyline", stroke_width=0, stroke_type="dash", fill_type="outline")
        self.assertEqual(geometry.style_of(dashed), {"stroke": {"type": "dash"}, "fill": {"type": "outline"}})
        red = SymbolGraphic("circle", fill_type="color", fill_color=(255.0, 0.0, 0.0, 0.5))
        self.assertEqual(geometry.style_of(red), {"fill": {"type": "color", "color": "#ff0000", "opacity": 0.5}})
        opaque = SymbolGraphic("circle", fill_type="color", fill_color=(0.0, 128.0, 0.0, 1.0))
        self.assertEqual(geometry.style_of(opaque), {"fill": {"type": "color", "color": "#008000"}})

    def test_glyph_is_stated_in_the_files_frame_with_its_anchor_at_the_origin(self):
        g = geometry.glyph_of(switch_like())
        self.assertEqual(g["ports"], {"C": {"x": 0.0, "y": 0.0}, "N": {"x": 29.21, "y": 0.0}, "R": {"x": 29.21, "y": -16.51}})   # y down: R rises
        kinds = sorted(p["type"] for p in g["shape"])
        self.assertEqual(kinds, ["circle", "polyline", "polyline", "text"])
        straight = next(p for p in g["shape"] if p["type"] == "polyline" and p.get("stroke"))
        self.assertEqual(straight, {"type": "polyline", "points": "0.0,0.0 29.21,0.0", "stroke": {"width": 0.4064}})
        diverging = next(p for p in g["shape"] if p["type"] == "polyline" and not p.get("stroke"))
        self.assertEqual(diverging, {"type": "polyline", "points": "11.43,0.0 29.21,-16.51"})                      # width 0: no width
        circle = next(p for p in g["shape"] if p["type"] == "circle")
        self.assertEqual(circle, {"type": "circle", "center": {"x": 13.97, "y": 5.08}, "radius": 1.27, "fill": {"type": "color", "color": "#ffff00"}})
        text = next(p for p in g["shape"] if p["type"] == "text")
        self.assertEqual(text, {"type": "text", "text": "H", "at": {"x": 16.51, "y": -2.54}, "size": 1.27, "justify": "left bottom"})

    def test_a_pins_drawn_line_is_a_primitive_and_a_hidden_or_zero_length_pin_draws_nothing(self):
        sym = LibrarySymbol("P", "P", (pin("A", 0.0, 0.0, 0.0, 2.54), pin("B", 5.08, 0.0, 90.0, 2.54, hidden=True), pin("Z", 2.54, 0.0)))
        g = geometry.glyph_of(sym)
        self.assertEqual(g["shape"], [{"type": "polyline", "points": "0.0,0.0 2.54,0.0"}])
        self.assertEqual(set(g["ports"]), {"A", "B", "Z"})


class TransformRules(unittest.TestCase):
    """§4.3: the transform stated in the Layout Data Model File's frame lands every pin where KiCad's does."""

    def test_kicad_turns_counter_clockwise_as_seen_on_the_page(self):
        """The probe's fact (2026-10-25): a pin below the origin (library 0,-2.54) turned by 90 lands to the right."""
        pl = SchematicPlacement("DOT3", "L:GCOR Rule 9.14 DoT_Left", 189.23, 71.12, 90.0)
        self.assertEqual(tuple(round(v, 2) for v in geometry.kicad_place(pl, (0.0, -2.54))), (191.77, 71.12))
        pl270 = SchematicPlacement("DOT3", "L:GCOR Rule 9.14 DoT_Left", 189.23, 71.12, 270.0)
        self.assertEqual(tuple(round(v, 2) for v in geometry.kicad_place(pl270, (0.0, -2.54))), (186.69, 71.12))

    def test_every_orientation_kicad_can_write_agrees_pin_by_pin(self):
        sym = switch_like()
        glyph = geometry.glyph_of(sym)
        pins = {p.name: (p.x, p.y) for p in sym.pins}
        anchor = geometry.anchor_of(pins)
        for rotation in (0.0, 90.0, 180.0, 270.0):
            for mirror in ("", "x", "y"):
                pl = SchematicPlacement("S1", "L:Sw", 100.33, 50.8, rotation, mirror)
                at = geometry.kicad_place(pl, anchor)
                row = {"at": {"x": at[0], "y": at[1]}, "rotation": int(rotation), "mirror": mirror}
                for name, local in pins.items():
                    want = geometry.kicad_place(pl, local)
                    port = glyph["ports"][name]
                    got = geometry.page_of(row, (port["x"], port["y"]))
                    self.assertAlmostEqual(got[0], want[0], 6, (rotation, mirror, name))
                    self.assertAlmostEqual(got[1], want[1], 6, (rotation, mirror, name))

    def test_the_stated_formula(self):
        """A glyph-local point turned 90 counter-clockwise on a y-down page: (x, y) -> (y, -x) before translation."""
        self.assertEqual(tuple(round(v, 4) for v in geometry.page_of({"at": {"x": 0, "y": 0}, "rotation": 90}, (10.0, 2.0))), (2.0, -10.0))
        self.assertEqual(tuple(round(v, 4) for v in geometry.page_of({"at": {"x": 0, "y": 0}, "mirror": "y"}, (10.0, 2.0))), (-10.0, 2.0))
        self.assertEqual(tuple(round(v, 4) for v in geometry.page_of({"at": {"x": 0, "y": 0}, "mirror": "x"}, (10.0, 2.0))), (10.0, -2.0))
        # mirror first: (10, 2) -> (-10, 2); then the turn: (2, 10); then translate
        self.assertEqual(tuple(round(v, 4) for v in geometry.page_of({"at": {"x": 1, "y": 1}, "mirror": "y", "rotation": 90}, (10.0, 2.0))), (3.0, 11.0))


class RunRules(unittest.TestCase):
    def test_wires_chain_end_to_end_break_at_ports_and_drop_collinear_vertices(self):
        wires = [((0.0, 0.0), (10.0, 0.0)), ((10.0, 0.0), (20.0, 0.0)), ((20.0, 0.0), (20.0, 5.0)), ((20.0, 5.0), (30.0, 5.0))]
        self.assertEqual(geometry.chain(wires, set()), [[(0.0, 0.0), (20.0, 0.0), (20.0, 5.0), (30.0, 5.0)]])
        two = geometry.chain(wires, {(20.0, 0.0)})                                     # a port in the middle splits the run
        self.assertEqual(sorted(geometry._ordered(r) for r in two), [[(0.0, 0.0), (20.0, 0.0)], [(20.0, 0.0), (20.0, 5.0), (30.0, 5.0)]])

    def test_a_run_is_stated_from_its_lesser_end(self):
        self.assertEqual(geometry._ordered([(5.0, 1.0), (1.0, 1.0)]), [(1.0, 1.0), (5.0, 1.0)])
        self.assertEqual(geometry._ordered([(1.0, 1.0), (5.0, 1.0)]), [(1.0, 1.0), (5.0, 1.0)])


class LabelRules(unittest.TestCase):
    """ADR 0013 §7.1: a hierarchical label continues a run. The reader states each label as drawn, its name and anchor;
    geometry states a run's end on one as ``label:<Name>`` and nothing else."""

    SHEET = """(kicad_sch (version 20250114) (generator "eeschema") (generator_version "9.0") (uuid "0")
  (paper "A4")
  (lib_symbols)
  (wire (pts (xy 10 20) (xy 30 20)) (stroke (width 0) (type default)) (uuid "1"))
  (hierarchical_label "ToSargentMT" (shape bidirectional) (at 30 20 0) (effects (font (size 1.27 1.27)) (justify left)) (uuid "2"))
  (hierarchical_label "Beet Loader 1" (shape input) (at 30 40 180) (uuid "3"))
)
"""

    def test_the_reader_states_every_hierarchical_label_with_its_name_and_anchor(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.kicad_sch"
            path.write_text(self.SHEET, encoding="utf-8")
            model = SchematicPlacementReader().read(path)
        self.assertEqual([(lb.name, lb.x, lb.y, lb.rotation, lb.shape) for lb in model.hierarchical_labels],
                         [("ToSargentMT", 30.0, 20.0, 0.0, "bidirectional"), ("Beet Loader 1", 30.0, 40.0, 180.0, "input")])
        self.assertEqual(model.wires, [((10.0, 20.0), (30.0, 20.0))])            # a label is no wire and no junction
        self.assertEqual(model.junctions, set())

    def test_a_label_end_is_the_labels_name_and_the_schema_takes_it(self):
        self.assertEqual(geometry.LABEL_END + "ToSargentMT", "label:ToSargentMT")
        run = {"points": "0.0,0.0 10.0,0.0", "relations": {"from": "Luchessa:783.R", "to": "label:Beet Loader 1"}}
        self.assertEqual(layout_model.errors({**layout_model.loads(layout_model.dumps(_minimal_file(run)))}), [])


def _minimal_file(run: dict) -> dict:
    """The least Layout Data Model File that holds one run of geometry, for the schema check."""
    return {"schema": layout_model.SCHEMA_ID, "layout": {"name": "T"},
            "interlockings": {"X": {"geometry": {"appliances": {}, "houses": {}, "track": [run], "markers": []}}},
            "provenance": {"sourceType": "test", "writer": {"name": "tests", "version": "0"}}}


@unittest.skipUnless(SPCOAST_AVAILABLE, WHY_SKIPPED)
class SPCoastGeometry(unittest.TestCase):
    """The piece on the drawing: no error, the frame's facts as ADR 0010 §5 reads them, DoD2, DoD3, the pin check."""

    @classmethod
    def setUpClass(cls):
        cls.sm = seams.resolve(spcoast_source())
        cls.geo = geometry.read(cls.sm)
        cls.model = emit.emit(cls.sm, geometry=cls.geo)

    def test_no_geometry_error_and_every_interlocking_has_a_frame(self):
        self.assertEqual([str(d) for d in self.sm.report.errors if not d.code.startswith("regime.")], [])   # the regime findings are the owner's redraw (#113, #118)
        self.assertEqual(sorted(self.geo.interlockings), sorted(self.sm.interlockings))

    def test_model_validates_against_3_1_0_and_round_trips(self):
        self.assertEqual(self.model["schema"], emit.SCHEMA)
        self.assertEqual(layout_model.errors(self.model), [])
        text = layout_model.dumps(self.model)
        self.assertEqual(layout_model.dumps(layout_model.loads(text)), text)

    def test_dod3_nothing_but_geometry_comes_from_a_coordinate(self):
        off = emit.emit(self.sm)
        on = copy.deepcopy(self.model)
        for ix in on["interlockings"].values():
            ix.pop("geometry", None)
        on["layout"].pop("glyphs")
        on["provenance"].pop("libraries")
        on["schema"] = off["schema"]
        self.assertEqual(layout_model.dumps(on), layout_model.dumps(off))

    def test_dod2_a_sheet_move_changes_nothing(self):
        """Every coordinate of Sargent's trackplan sheet translated by (17.78, -5.08): the geometry is byte-identical."""
        sheet = self.sm.source.sheet_files[self.sm.interlockings["Sargent"].sym.sheet]
        project_dir = Path(self.sm.source.project).parent
        with tempfile.TemporaryDirectory() as tmp:
            for f in project_dir.glob("*.kicad_sch"):
                shutil.copy(f, Path(tmp) / f.name)
            text = (Path(tmp) / sheet).read_text(encoding="utf-8")
            start = next(e for _, e in sch_text.blocks(text, "lib_symbols", 1))       # the embedded library is not the drawing
            head, body = text[:start], text[start:]
            dx, dy = 17.78, -5.08
            body = re.sub(r"\((at|xy) (-?\d+(?:\.\d+)?) (-?\d+(?:\.\d+)?)",
                          lambda m: f"({m.group(1)} {round(float(m.group(2)) + dx, 2):g} {round(float(m.group(3)) + dy, 2):g}", body)
            (Path(tmp) / sheet).write_text(head + body, encoding="utf-8")
            moved = geometry.read(self.sm, project_dir=Path(tmp))
        self.assertEqual([str(d) for d in self.sm.report.errors if not d.code.startswith("regime.")], [])   # the regime findings are the owner's redraw (#113, #118)
        self.assertEqual(layout_model.dumps(moved.interlockings), layout_model.dumps(self.geo.interlockings))
        self.assertEqual(layout_model.dumps(moved.glyphs), layout_model.dumps(self.geo.glyphs))

    def test_the_files_transform_lands_every_pin_where_kicads_did(self):
        self.assertEqual(geometry.check_transform(self.geo, self.sm), [])

    def test_sargent_as_adr_0010_section_5_reads_it(self):
        """Sargent's sheet since the block POC (Railroad 56ff2e1, 2a1696e, 31954c5): the 834 signal location with its
        two masts and plate, 836T, and the block track leaving through the hierarchical net NMT in place of the consumer of
        Corporal:2NAT; the frame moved with the drawing."""
        g = self.geo.interlockings["Sargent"]
        self.assertEqual(g["appliances"]["835"], {"at": {"x": 78.74, "y": 33.02}, "glyph": "Railroad-Trackplan:Switch_Lock", "mirror": "y"})
        self.assertEqual(set(g["appliances"]["836NAB"]), {"at", "glyph"})                 # a mast's geometry carries no heads since the anonymous-head step (#80; Railroad 9fcf779)
        self.assertEqual(g["appliances"]["836SA"]["rotation"], 180)
        self.assertNotIn("Corporal:2NAT", g["appliances"])                       # no consumer is drawn; 836T is Sargent's own
        self.assertEqual(g["houses"], {"Sargent": {"at": {"x": 80.01, "y": 0.0}, "glyph": "Railroad-Trackplan:House"}})
        self.assertEqual(len(g["appliances"]), 12)
        self.assertEqual(len(g["track"]), 6)
        runs = self.model["interlockings"]["Sargent"]["geometry"]["track"]                   # a run's circuit is derived
        self.assertEqual(sorted(t["derived"]["circuit"] for t in runs if "derived" in t),
                         ["Corporal:834T", "Sargent:1NAT", "Sargent:1T1", "Sargent:1T1", "Sargent:2SAT", "Sargent:836T"])   # 834T reaches the 834 joint through NMT (ADR 0013 §7.1)
        self.assertEqual(sorted(t["relations"]["from"] for t in runs if t.get("derived", {}).get("circuit") == "Sargent:1T1"), ["Sargent:1.N", "Sargent:1.R"])   # the Beet Loader spur carries switch 1's OS circuit since Railroad 0ddd395 (Switch_Local 1, TC 1T1)
        self.assertIn("label:NMT", next(t["relations"].values() for t in runs if t.get("derived", {}).get("circuit") == "Corporal:834T"))   # the hierarchical net NMT since Railroad eef8217 (ToCorporalMT before)
        self.assertEqual(len(g["markers"]), 10)                                  # Railroad eef8217: the NextCP toward Watsonville gone (the block is a shared net); 11 at 9fcf779
        rows = self.rows("Sargent")
        self.assertEqual(sum(1 for m in g["markers"] if rows[m["row"]]["given"].get("Kind") == "INDUSTRY"), 2)
        self.assertNotIn("mileposts", g)
        sw = self.geo.glyphs["Railroad-Trackplan:Switch_Lock"]
        self.assertEqual(sw["ports"], {"C": {"x": 0.0, "y": 0.0}, "N": {"x": 29.21, "y": 0.0}, "R": {"x": 29.21, "y": -16.51}})
        widths = [p["stroke"]["width"] for g_ in self.geo.glyphs.values() for p in g_["shape"] if "width" in p.get("stroke", {})]
        self.assertTrue(widths and all(w > 0 for w in widths))                         # KiCad's 0 is never written

    def rows(self, ix: str) -> dict[str, dict]:
        track = self.model["interlockings"][ix]["track"]
        return {r["id"]: r for k in ("joints", "ends", "policies", "consumers") for r in track.get(k, [])}

    def test_luchessa_mileposts_and_the_runs_that_meet_a_switch_port(self):
        g = self.geo.interlockings["Luchessa"]
        self.assertEqual(sorted(g["mileposts"]), ["78.3", "79.3"])
        ports = sorted(v for t in g["track"] for v in t.get("relations", {}).values() if ":" in v and not v.startswith(geometry.LABEL_END))
        self.assertEqual(ports, ["Luchessa:783.R", "Luchessa:799.N", "Luchessa:799.R"])
        labels = sorted(v for t in g["track"] for v in t.get("relations", {}).values() if v.startswith(geometry.LABEL_END))
        self.assertEqual(labels, ["label:NMT", "label:SMT1", "label:SMT2"])          # Luchessa's three block circuits leave by hierarchical nets (Railroad eef8217)

    def test_every_marker_names_one_track_row_by_id_and_copies_none_of_its_facts(self):
        """Three-maps D10: a marker's one join key is its row's id; each row drawn on the interlocking's sheet has exactly
        one marker, and a row placed from another sheet (ADR 0010 C5: the frame is the one sheet) has none: GCaltrain's
        Lick NextCP on the South-cTc sheet (Railroad eef8217; placed by its track net, the owner 2026-11-11)."""
        for name, ix in self.model["interlockings"].items():
            rows = self.rows(name)
            markers = ix["geometry"]["markers"]
            own = {s.uuid for s in self.sm.source.symbols.values() if s.sheet == self.sm.interlockings[name].sym.sheet}
            self.assertEqual(sorted(m["row"] for m in markers), sorted(r for r in rows if r in own), name)
            self.assertEqual([rows[r]["given"] for r in rows if r not in own],
                             [{"Kind": "NEXT_CP", "Interlocking": "Lick", "Style": "off_layout"}] if name == "GCaltrain" else [], name)
            self.assertEqual([m for m in markers if set(m) - {"row", "at", "glyph", "rotation", "mirror"}], [], name)

    def test_a_runs_ends_are_relations_to_a_switch_port_or_a_track_row_side(self):
        """Three-maps D5 extended: from and to name the switch port or the track row pin a run meets, by name or by the row's
        id and its side as the model names it; never a coordinate."""
        for name, ix in self.model["interlockings"].items():
            rows = self.rows(name)
            for t in ix["geometry"]["track"]:
                for end in t.get("relations", {}).values():
                    if ":" in end:
                        continue                                                   # a switch port or a named row's pin, by name
                    row, side = end.rsplit(".", 1)
                    self.assertIn(row, rows, (name, end))
                    kind = rows[row]["given"]["Kind"]
                    self.assertIn(side, SIDES.get(kind, {"track"}), (name, end, kind))
        lu = [t for t in self.model["interlockings"]["Luchessa"]["geometry"]["track"] if t.get("derived", {}).get("circuit") == "Luchessa:1NAT"]
        sides = sorted(e if e.startswith(geometry.LABEL_END) else e.rsplit(".", 1)[1] for t in lu for e in t["relations"].values())
        self.assertEqual(sides, ["approach", "label:SMT2"])                      # from the signal joint's approach side to the hierarchical net SMT2 (Railroad eef8217; a NextCP's track side before)

    def test_a_run_that_ends_on_a_hierarchical_label_states_the_labels_name(self):
        """ADR 0013 §7.1 (Railroad eef8217): every interlocking's block circuits leave its sheet by hierarchical nets, NMT
        and SMT (Luchessa's two south mains SMT1 and SMT2; Christopher's siding sheet has none of its own); the Beet
        Loader labels carry dark track between Corporal's and Sargent's sheets. Each such run ends on the label's name,
        no coordinate and nothing from the other sheet; the circuit it carries is the derivation's."""
        ends = {name: sorted(e for t in ix["geometry"]["track"] for e in t.get("relations", {}).values() if e.startswith("label:"))
                for name, ix in self.model["interlockings"].items()}
        self.assertEqual(ends, {"Christopher": [], "Corporal": ["label:Beet Loader 1", "label:Beet Loader 2", "label:SMT"],
                                "GCaltrain": ["label:NMT", "label:SMT"], "Gilroy": ["label:NMT", "label:SMT"],
                                "Luchessa": ["label:NMT", "label:SMT1", "label:SMT2"],
                                "Sargent": ["label:Beet Loader 1", "label:Beet Loader 2", "label:NMT", "label:SMT"], "Watsonville": ["label:NMT"]})
        out = next(t for t in self.model["interlockings"]["Corporal"]["geometry"]["track"] if t.get("relations", {}).get("to") == "label:SMT")
        self.assertEqual([k for k in out["relations"] if out["relations"][k].startswith("label:")], ["to"])   # the name only
        self.assertEqual(out["derived"], {"circuit": "Corporal:834T"})            # from the far end, the joint's B side
        self.assertEqual(self.sm.report.by_code("geometry.run_end"), [])

    def test_where_a_boundary_pin_sits_on_a_joints_pin_the_run_names_the_joint(self):
        """ADR 0013 §10 (Railroad 2a1696e): 833T's A and B sit on the double joint's A and B at 832. A run's end names the
        track row there, the joint's side, never the boundary's pin; the boundary is in geometry as an appliance."""
        g = self.model["interlockings"]["Corporal"]
        joint = next(j for j in g["track"]["joints"] if j["given"]["Kind"] == "IRJ_SIGNALS")["id"]
        ends = sorted(e for t in g["geometry"]["track"] for e in t.get("relations", {}).values())
        self.assertIn(f"{joint}.A", ends)
        self.assertIn(f"{joint}.B", ends)
        self.assertEqual([e for e in ends if e.startswith("Corporal:833T")], [])
        self.assertEqual(g["geometry"]["appliances"]["833T"]["glyph"], "Railroad-Trackplan:Track Circuit IR Boundary")

    def test_every_glyph_named_is_written_and_nothing_else(self):
        named = {row["glyph"] for g in self.geo.interlockings.values() for row in geometry._every_placement(g)}
        self.assertEqual(named, set(self.geo.glyphs))
        self.assertEqual(self.model["provenance"]["libraries"].keys(), {"Railroad-Trackplan"})


class Facing(unittest.TestCase):
    """Which way a mast glyph faces (the owner, 2026-11-08): unturned LEFT, a half turn RIGHT, a mirror across y swaps
    them, a quarter turn neither. The same transform as the file's placement transform, so the sheet and the file agree."""

    def test_the_glyphs_turn_says_which_trains_it_faces(self):
        self.assertEqual(geometry.facing({"at": {"x": 0, "y": 0}}), "LEFT")
        self.assertEqual(geometry.facing({"at": {"x": 0, "y": 0}, "rotation": 180}), "RIGHT")
        self.assertEqual(geometry.facing({"at": {"x": 0, "y": 0}, "mirror": "y"}), "RIGHT")
        self.assertEqual(geometry.facing({"at": {"x": 0, "y": 0}, "rotation": 180, "mirror": "y"}), "LEFT")
        self.assertEqual(geometry.facing({"at": {"x": 0, "y": 0}, "rotation": 180, "mirror": "x"}), "RIGHT")
        self.assertIsNone(geometry.facing({"at": {"x": 0, "y": 0}, "rotation": 90}))
        self.assertIsNone(geometry.facing({"at": {"x": 0, "y": 0}, "rotation": 270}))


if __name__ == "__main__":
    unittest.main()
