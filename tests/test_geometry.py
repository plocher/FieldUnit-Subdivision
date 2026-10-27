"""Gates for the geometry piece of the KiCad importer (ADR 0010; ADR 0011 §7; DoD2, DoD3, the §4.3 transform, §4.9 glyphs).

The rules are tested on symbols and placements built in memory: the anchor, the style rule, the glyph frame, the
transform for every orientation KiCad can write (the direction of a 90-degree turn was asked of kicad-cli by
``tests/fixtures/kicad/rotation_probe.py``, 2026-10-25: counter-clockwise as seen on the page), the chaining of
wires into runs. The project gates run on the SPCoast drawing as ``tests.test_layout_compiler.spcoast_source`` reads
it (a fresh export, or a saved ``SPCOAST_NETLIST`` checked as a snapshot first), never faked when absent. Geometry
joins the rest of the file by identity only (three-maps D10): markers name their track row by id, runs name what
their ends meet.
"""
from __future__ import annotations

import copy
import math
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from tools import layout_model
from tools.kicad_services import sch_text
from tools.kicad_services.types import LibrarySymbol, SchematicPlacement, SymbolGraphic, SymbolPin
from tools.layout_compiler import emit, geometry, seams
from tests.test_layout_compiler import NETLIST, PROJECT, SPCOAST_AVAILABLE, spcoast_source


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
SIDES = {"IRJ_SIGNAL": {"approach", "governed"}, "IRJ": {"A", "B"}, "NEXT_CP": {"track"}, "END_CTC": {"CTC", "DARK"},
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
        pl = SchematicPlacement("DOT3", "L:Rule261", 189.23, 71.12, 90.0)
        self.assertEqual(tuple(round(v, 2) for v in geometry.kicad_place(pl, (0.0, -2.54))), (191.77, 71.12))
        pl270 = SchematicPlacement("DOT3", "L:Rule261", 189.23, 71.12, 270.0)
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


@unittest.skipUnless(SPCOAST_AVAILABLE, f"SPCoast project not present or kicad-cli missing: {NETLIST or PROJECT}")
class SPCoastGeometry(unittest.TestCase):
    """The piece on the drawing: no error, the frame's facts as ADR 0010 §5 reads them, DoD2, DoD3, the pin check."""

    @classmethod
    def setUpClass(cls):
        cls.sm = seams.resolve(spcoast_source())
        cls.geo = geometry.read(cls.sm)
        cls.model = emit.emit(cls.sm, geometry=cls.geo)

    def test_no_geometry_error_and_every_interlocking_has_a_frame(self):
        self.assertEqual([str(d) for d in self.sm.report.errors], [])
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
        self.assertEqual([str(d) for d in self.sm.report.errors], [])
        self.assertEqual(layout_model.dumps(moved.interlockings), layout_model.dumps(self.geo.interlockings))
        self.assertEqual(layout_model.dumps(moved.glyphs), layout_model.dumps(self.geo.glyphs))

    def test_the_files_transform_lands_every_pin_where_kicads_did(self):
        self.assertEqual(geometry.check_transform(self.geo, self.sm), [])

    def test_sargent_as_adr_0010_section_5_reads_it(self):
        g = self.geo.interlockings["Sargent"]
        self.assertEqual(g["appliances"]["835"], {"at": {"x": 90.17, "y": 33.02}, "glyph": "Railroad-Trackplan:Switch_Lock", "mirror": "y"})
        self.assertEqual(set(g["appliances"]["836NAB"]["heads"]), {"A", "B"})
        self.assertEqual(g["appliances"]["836SA"]["rotation"], 180)
        self.assertIn("Corporal:2NAT", g["appliances"])
        self.assertEqual(g["houses"], {"Sargent": {"at": {"x": 91.44, "y": 0.0}, "glyph": "Railroad-Trackplan:House"}})
        self.assertEqual(len(g["appliances"]), 11)
        self.assertEqual(len(g["track"]), 4)
        runs = self.model["interlockings"]["Sargent"]["geometry"]["track"]                   # a run's circuit is derived
        self.assertEqual(sorted(t["derived"]["circuit"] for t in runs), ["Corporal:2NAT", "Sargent:1NAT", "Sargent:1SAT", "Sargent:2SAT"])
        self.assertEqual(len(g["markers"]), 12)
        rows = self.rows("Sargent")
        self.assertEqual(sum(1 for m in g["markers"] if rows[m["row"]]["given"]["Kind"] == "INDUSTRY"), 2)
        self.assertNotIn("mileposts", g)
        sw = self.geo.glyphs["Railroad-Trackplan:Switch_Lock"]
        self.assertEqual(sw["ports"], {"C": {"x": 0.0, "y": 0.0}, "N": {"x": 29.21, "y": 0.0}, "R": {"x": 29.21, "y": -16.51}})
        widths = [p["stroke"]["width"] for g_ in self.geo.glyphs.values() for p in g_["shape"] if "width" in p.get("stroke", {})]
        self.assertTrue(widths and all(w > 0 for w in widths))                         # KiCad's 0 is never written

    def rows(self, ix: str) -> dict[str, dict]:
        track = self.model["interlockings"][ix]["track"]
        return {r["id"]: r for k in ("joints", "ends", "policies") for r in track.get(k, [])}

    def test_luchessa_mileposts_and_the_runs_that_meet_a_switch_port(self):
        g = self.geo.interlockings["Luchessa"]
        self.assertEqual(sorted(g["mileposts"]), ["78.3", "79.3"])
        ports = sorted(v for t in g["track"] for v in t.get("relations", {}).values() if ":" in v)
        self.assertEqual(ports, ["Luchessa:783.R", "Luchessa:799.N", "Luchessa:799.R"])

    def test_every_marker_names_one_track_row_by_id_and_copies_none_of_its_facts(self):
        """Three-maps D10: a marker's one join key is its row's id; each row has exactly one marker."""
        for name, ix in self.model["interlockings"].items():
            rows = self.rows(name)
            markers = ix["geometry"]["markers"]
            self.assertEqual(sorted(m["row"] for m in markers), sorted(rows), name)
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
        sides = sorted(e.rsplit(".", 1)[1] for t in lu for e in t["relations"].values())
        self.assertEqual(sides, ["approach", "track"])                           # from the signal joint's approach side to the NextCP

    def test_every_glyph_named_is_written_and_nothing_else(self):
        named = {row["glyph"] for g in self.geo.interlockings.values() for row in geometry._every_placement(g)}
        self.assertEqual(named, set(self.geo.glyphs))
        self.assertEqual(self.model["provenance"]["libraries"].keys(), {"Railroad-Trackplan"})


if __name__ == "__main__":
    unittest.main()
