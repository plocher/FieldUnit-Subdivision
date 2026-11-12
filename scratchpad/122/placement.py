"""Trackplan placement by CP Name, sheet or track net (the owner, 2026-11-11); re-runnable exact edits."""
from pathlib import Path
import json, sys
ROOT = Path(__file__).resolve().parents[2]

def edit(rel, pairs):
    p = ROOT / rel; t = p.read_text(encoding="utf-8")
    for old, new in pairs:
        n = t.count(old)
        if new in t and (old not in new or n == new.count(old)): print(f"{rel}: already applied")
        elif n == 1: t = t.replace(old, new)
        else: sys.exit(f"{rel}: {n} matches for {old[:60]!r}")
    p.write_text(t, encoding="utf-8")

edit("tools/layout_compiler/trackplan.py", [
("""def read(sm: Seams) -> Trackplan:
    out = Trackplan()
    on_track = track_nets(sm)
    for ix in sm.interlockings.values():
        syms = [s for s in sm.source.under(ix.sym.sheet, "APPLIANCE") + sm.source.under(ix.sym.sheet, "TRACK")
                + sm.source.under(ix.sym.sheet, "POLICY") if unit_of(sm, s) == ix.name]
        if syms:
            out.plans[ix.name] = _plan(sm, ix, syms, on_track)
    return out


def track_nets(sm: Seams) -> frozenset[str]:
    \"\"\"The nets that carry track: every net a track pin of any interlocking's trackplan symbol is on, whatever sheet it
    is drawn on (ADR 0013 §7.1).\"\"\"
    src = sm.source
    return frozenset(n.name for s in src.symbols.values() if on_trackplan(s) and unit_of(sm, s)
                     for pin, n in src.pins_of(s.ref).items() if is_track_pin(s, pin))


def unit_of(sm: Seams, s: Symbol) -> Optional[str]:
    \"\"\"The interlocking whose sheet is the nearest at or above the symbol's (ADR 0004 D12).\"\"\"
    hits = [ix for ix in sm.interlockings.values() if s.sheet.startswith(ix.sym.sheet)]
    return max(hits, key=lambda ix: len(ix.sym.sheet)).name if hits else None
""", """def read(sm: Seams) -> Trackplan:
    out = Trackplan()
    on_track = track_nets(sm)
    units = placements(sm)
    for ix in sm.interlockings.values():
        syms = [s for s in sm.source.where("APPLIANCE") + sm.source.where("TRACK") + sm.source.where("POLICY") if units.get(s.ref) == ix.name]
        if syms:
            out.plans[ix.name] = _plan(sm, ix, syms, on_track)
    return out


def track_nets(sm: Seams) -> frozenset[str]:
    \"\"\"The nets that carry track: every net a track pin of any interlocking's trackplan symbol is on, whatever sheet it
    is drawn on (ADR 0013 §7.1).\"\"\"
    src = sm.source
    return frozenset(n.name for s in src.symbols.values() if on_trackplan(s) and unit_of(sm, s)
                     for pin, n in src.pins_of(s.ref).items() if is_track_pin(s, pin))


def unit_of(sm: Seams, s: Symbol) -> Optional[str]:
    \"\"\"The interlocking a trackplan symbol belongs to (``placements``); None when it belongs to none.\"\"\"
    return placements(sm).get(s.ref)


def placements(sm: Seams) -> dict[str, Optional[str]]:
    \"\"\"Every trackplan symbol's interlocking, computed once per drawing (the owner, 2026-11-11). A symbol with Role
    ``TRACK``, ``APPLIANCE`` or ``POLICY`` is placed (1) by its ``CP Name`` when it names an interlocking or one of its
    houses, compared case-insensitively as the desk side compares them, even on another interlocking's sheet (sheet
    scope is a default, the owner 2026-10-28); (2) else by its sheet, the nearest interlocking at or above (ADR 0004
    D12); (3) else, drawn under no interlocking sheet, by its track net: when the nets on its track pins reach the
    track pins of exactly one interlocking's symbols it is that interlocking's (a NextCP on the parent sheet wired to a
    hierarchical net), taken to a fixpoint so a chain of such symbols is placed from its one placed end; (4) else it
    is ``trackplan.unit`` at missing and belongs to none, never dropped in silence.\"\"\"
    if sm.trackplan_units is not None:
        return sm.trackplan_units
    src = sm.source
    by_cp = {ix.name.casefold(): ix.name for ix in sm.interlockings.values()}
    by_cp.update({cp.casefold(): ix.name for ix in sm.interlockings.values() for cp in ix.houses})
    units: dict[str, Optional[str]] = {}
    pending: list[Symbol] = []
    for s in src.symbols.values():
        if not on_trackplan(s):
            continue
        cp = (s.get("CP Name") or "").strip().casefold()
        hits = [ix for ix in sm.interlockings.values() if s.sheet.startswith(ix.sym.sheet)]
        if cp in by_cp:
            units[s.ref] = by_cp[cp]
        elif hits:
            units[s.ref] = max(hits, key=lambda ix: len(ix.sym.sheet)).name
        else:
            pending.append(s)
    placed_some = True
    while pending and placed_some:
        placed_some = False
        for s in list(pending):
            reached = {units[o.ref] for pin, n in src.pins_of(s.ref).items() if is_track_pin(s, pin)
                       for p in n.others(s.ref) for o in (src.symbols[p.ref],) if on_trackplan(o) and is_track_pin(o, p.pin) and units.get(o.ref)}
            if len(reached) == 1:
                units[s.ref] = reached.pop()
                pending.remove(s)
                placed_some = True
    for s in pending:
        units[s.ref] = None
        sm.report.missing("trackplan.unit", f"a {s.kind or s.get('Appliance') or s.lib_id} belongs to no interlocking: name one with CP Name or draw it "
                          "under the interlocking's sheet", source=loc(s))
    sm.trackplan_units = units
    return units
"""),
("""        \"\"\"The interlocking a symbol is drawn under, cached.\"\"\"
""", """        \"\"\"The interlocking a symbol belongs to (``placements``), cached.\"\"\"
"""),
])

edit("tools/layout_compiler/seams.py", [
("""    trackplan: Optional["object"] = None                             # trackplan.Trackplan: appliances and track as drawn
""", """    trackplan: Optional["object"] = None                             # trackplan.Trackplan: appliances and track as drawn
    trackplan_units: Optional[dict[str, Optional[str]]] = None        # trackplan.placements: each trackplan symbol's interlocking
"""),
])

edit("tools/layout_compiler/geometry.py", [
("""        trackplan = [s for s in src.symbols.values() if s.role in TRACKPLAN_ROLES and unit_of(sm, s) == ix.name]
        sheets = sorted({s.sheet for s in trackplan})
""", """        # The frame is the interlocking's own sheet (ADR 0010 C5): a row placed from another sheet, by CP Name or by its
        # track net (trackplan.placements), is in the model with no marker here.
        trackplan = [s for s in src.symbols.values() if s.role in TRACKPLAN_ROLES and unit_of(sm, s) == ix.name and s.sheet == ix.sym.sheet]
        sheets = sorted({s.sheet for s in trackplan})
"""),
])

reg = ROOT / "tools/layout_compiler/diagnostics.json"
d = json.loads(reg.read_text(encoding="utf-8"))
d["codes"]["trackplan.unit"] = {"level": "missing", "lifecycle": "active", "since": "0.4.0",
    "feature": "trackplan/trackplan_placement.feature#a NextCP on the sheet above wired to no interlocking's track belongs to none", "replacedBy": None}
d["codes"] = dict(sorted(d["codes"].items()))
reg.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

(ROOT / "tools/layout_compiler/features/trackplan/trackplan_placement.feature").write_text('''Feature: A trackplan symbol's interlocking, as drawn
  A symbol with Role TRACK, APPLIANCE or POLICY is placed by its CP Name when it names an
  interlocking or one of its houses, else by its sheet, the nearest interlocking at or above,
  else by its track net when the nets on its track pins reach exactly one interlocking's track;
  a symbol none of these places is reported, never dropped. (the owner, 2026-11-11; sheet scope
  is a default, 2026-10-28)

  Background:
    Given this drawing of interlocking "X":
      | Ref | Symbol                           | Role      | Kind          | Appliance     | Name | CP Name |
      | H1  | Railroad-Trackplan:House         | STRUCTURE | CONTROL_POINT |               |      | East    |
      | TC1 | Railroad-Trackplan:Track Circuit | APPLIANCE |               | track_circuit | 1NAT |         |
      | J1  | Railroad-Trackplan:IRJ           | TRACK     | IRJ           |               |      |         |

  Scenario: a NextCP on the sheet above wired to one interlocking's track is that interlocking's
    Given these symbols on the sheet above:
      | Ref | Symbol                              | Role  | Kind    | Interlocking | Style      |
      | N1  | Railroad-Trackplan:NextCP Not Modeled | TRACK | NEXT_CP | Lick         | off_layout |
    And these nets:
      | Net | Pins             |
      | NMT | TC1.TC J1.B N1.To |
    When the drawing is imported
    Then the row "N1" is in interlocking "X"
    And the row "N1" is written with Interlocking "Lick"
    And the row "N1" names "X:1NAT.TC" on side track

  @trackplan.unit
  Scenario: a NextCP on the sheet above wired to no interlocking's track belongs to none
    Given these symbols on the sheet above:
      | Ref | Symbol                              | Role  | Kind    | Interlocking |
      | N1  | Railroad-Trackplan:NextCP Not Modeled | TRACK | NEXT_CP | Lick         |
      | J9  | Railroad-Trackplan:IRJ                | TRACK | IRJ     |              |
    And these nets:
      | Net | Pins      |
      | t   | TC1.TC J1.B |
      | n   | N1.To J9.A  |
    When the drawing is imported
    Then it is reported as missing on "N1"
    And it is reported as missing on "J9"
    And no row is written for "N1"

  Scenario: a track circuit on another interlocking's sheet with the CP Name of a house of X is X's
    Given this drawing of interlocking "Y":
      | Ref | Symbol                           | Role      | Kind          | Appliance     | Name | CP Name |
      | H2  | Railroad-Trackplan:House         | STRUCTURE | CONTROL_POINT |               |      | West    |
      | TC2 | Railroad-Trackplan:Track Circuit | APPLIANCE |               | track_circuit | 2NAT | East    |
    And these nets:
      | Net | Pins        |
      | t   | TC1.TC J1.B |
    When the drawing is imported
    Then "2NAT" is in interlocking "X"
''', encoding="utf-8")

edit("tools/layout_compiler/features/steps/import_steps.py" if (ROOT / "tools/layout_compiler/features/steps/import_steps.py").exists() else sorted((ROOT / "tools/layout_compiler/features/steps").glob("*.py"))[0].relative_to(ROOT).as_posix(), [
("""@given("these symbols too:")
""", """@given("these symbols on the sheet above:")
def parent_symbols(context):
    \"\"\"Symbols on the root sheet, above every interlocking's (a NextCP wired to a hierarchical net).\"\"\"
    for row in context.table:
        fields = {h: row[h].strip() for h in row.headings if h not in ("Ref", "Symbol") and row[h].strip()}
        context.symbols.append(Symbol(row["Ref"].strip(), row["Symbol"].strip(), "", fields, "/"))


@given("these symbols too:")
"""),
("""def _pin_name(context, pin: str) -> str:
""", """@then('the row "{ref}" is in interlocking "{name}"')
def row_in(context, ref, name):
    rid = context.seams.source.symbols[ref].uuid
    hits = [n for n, ix in context.model["interlockings"].items() for rows in ix.get("track", {}).values() for r in rows if r.get("id") == rid]
    assert hits == [name], f"{ref}: in {hits}, not [{name!r}]"


@then('no row is written for "{ref}"')
def no_row(context, ref):
    rid = context.seams.source.symbols[ref].uuid
    hits = [n for n, ix in context.model["interlockings"].items() for rows in ix.get("track", {}).values() for r in rows if r.get("id") == rid]
    assert not hits, f"{ref}: a row in {hits}"


@then('"{name}" is in interlocking "{ix}"')
def appliance_in(context, name, ix):
    hits = [n for n, i in context.model["interlockings"].items() if name in i.get("appliances", {})]
    assert hits == [ix], f"{name}: in {hits}, not [{ix!r}]"


def _pin_name(context, pin: str) -> str:
"""),
])
print("ok")

# the SPCoast gates: Lick is GCaltrain's off-layout end on NMT, placed by its track net from the South-cTc sheet
edit("tests/test_trackplan.py", [
("""        # the interlockings share their block circuits by hierarchical nets, so of the 16 NextCPs only Luchessa's to
        # Hollister (off_layout) remains; Christopher's siding is a controlled siding (two dwarf signal joints in place
""", """        # the interlockings share their block circuits by hierarchical nets, so of the 16 NextCPs only the two off-layout
        # ends remain, Luchessa's to Hollister and GCaltrain's to Lick (drawn on the South-cTc sheet, placed by its
        # track net NMT, the owner 2026-11-11); Christopher's siding is a controlled siding (two dwarf signal joints in place
"""),
("""{"IRJ": 55, "IRJ_SIGNAL": 38, "IRJ_SIGNALS": 2, "NEXT_CP": 1, "BUMPER": 3, "INDUSTRY": 5, "RULE_290_G": 1})
""", """{"IRJ": 55, "IRJ_SIGNAL": 38, "IRJ_SIGNALS": 2, "NEXT_CP": 2, "BUMPER": 3, "INDUSTRY": 5, "RULE_290_G": 1})
"""),
("""    def test_the_blocks_are_shared_nets_and_the_one_next_cp_left_is_off_layout(self):
        \"\"\"Railroad eef8217: the interlockings share their block circuits through hierarchical nets, one circuit per shared
        net named by the station whose processor reads it, so a neighbour's joint stands on it; the only NextCP left
        leads off the layout to Hollister.\"\"\"
        ends = [(i, e["given"]) for i, ix in self.model["interlockings"].items() for e in ix["track"].get("ends", []) if e["given"]["Kind"] == "NEXT_CP"]
        self.assertEqual(ends, [("Luchessa", {"Kind": "NEXT_CP", "Interlocking": "Hollister", "Style": "off_layout"})])
        self.assertEqual(self.sm.report.by_code("next_cp.pair") + self.sm.report.by_code("next_cp.off_layout"), [])
""", """    def test_the_blocks_are_shared_nets_and_the_next_cps_left_lead_off_the_layout(self):
        \"\"\"Railroad eef8217: the interlockings share their block circuits through hierarchical nets, one circuit per shared
        net named by the station whose processor reads it, so a neighbour's joint stands on it; the two NextCPs left
        lead off the layout, Luchessa's to Hollister on its own sheet and GCaltrain's to Lick, drawn on the South-cTc
        sheet above every interlocking and placed by its track net NMT (``trackplan.placements``, the owner 2026-11-11).\"\"\"
        ends = {i: (e["given"], e["derived"]["circuits"]) for i, ix in self.model["interlockings"].items() for e in ix["track"].get("ends", []) if e["given"]["Kind"] == "NEXT_CP"}
        self.assertEqual(ends, {"GCaltrain": ({"Kind": "NEXT_CP", "Interlocking": "Lick", "Style": "off_layout"}, {"track": "GCaltrain:1SAT"}),
                                "Luchessa": ({"Kind": "NEXT_CP", "Interlocking": "Hollister", "Style": "off_layout"}, {"track": "Luchessa:3NAT"})})
        self.assertEqual(self.sm.source.symbols[trackplan_ref(self.sm, "Lick")].sheet, "/South-cTc/")
        self.assertEqual(self.sm.report.by_code("next_cp.pair") + self.sm.report.by_code("next_cp.off_layout") + self.sm.report.by_code("trackplan.unit"), [])
"""),
("""    def ix(self, name):
        return self.model["interlockings"][name]

    def test_every_mast_stands_on_one_signal_joint_and_has_its_control_point(self):
""", """    def ix(self, name):
        return self.model["interlockings"][name]

    def test_every_mast_stands_on_one_signal_joint_and_has_its_control_point(self):
"""),
])
edit("tests/test_geometry.py", [
("""        \"\"\"Three-maps D10: a marker's one join key is its row's id; each row has exactly one marker.\"\"\"
        for name, ix in self.model["interlockings"].items():
            rows = self.rows(name)
            markers = ix["geometry"]["markers"]
            self.assertEqual(sorted(m["row"] for m in markers), sorted(rows), name)
""", """        \"\"\"Three-maps D10: a marker's one join key is its row's id; each row drawn on the interlocking's sheet has exactly
        one marker, and a row placed from another sheet (ADR 0010 C5: the frame is the one sheet) has none: GCaltrain's
        Lick NextCP on the South-cTc sheet (Railroad eef8217; placed by its track net, the owner 2026-11-11).\"\"\"
        for name, ix in self.model["interlockings"].items():
            rows = self.rows(name)
            markers = ix["geometry"]["markers"]
            own = {s.uuid for s in self.sm.source.symbols.values() if s.sheet == self.sm.interlockings[name].sym.sheet}
            self.assertEqual(sorted(m["row"] for m in markers), sorted(r for r in rows if r in own), name)
            self.assertEqual([rows[r]["given"] for r in rows if r not in own],
                             [{"Kind": "NEXT_CP", "Interlocking": "Lick", "Style": "off_layout"}] if name == "GCaltrain" else [], name)
"""),
])
