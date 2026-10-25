# Handoff: ADR 0010, geometry and the four views of the trackplan

> Closed 2026-10-25. ADR 0010 is accepted (2026-10-24, `6b99317`). Items 1 and 2 below are done; items 3 and 4
> continue as ADR 0010 C2 and C3 in `handoff-compiler-semantics-2026-10-24.md`, the one handoff for the compiler
> segment. Kept as the record of the asks and defaults the ADR started from.

Written 2026-10-24 at the close of the ADR 0008 rev 4 segment, for the session that proposes ADR 0010. It runs in
parallel with `handoff-compiler-semantics-2026-10-24.md`, the trackplan semantics; the two meet at the
`appliances` and `track` objects (both pieces read the same symbols) and at the schema's next minor version.

## Where things stand

- **ADR 0008 rev 4** (`docs/adr/0008-layout-data-model-file.md`) is accepted (2026-10-24, Subdivision `a3f1e35`).
  The Layout Data Model File is the public interface: `schemas/layout-model/v3.0.0.json`; the example
  `schemas/layout-model/examples/spcoast.layout.json` is the compiler's output on the SPCoast project, never typed.
  `geometry` is a key of every interlocking and office unit and is typed as an **open object with nothing inside**
  (schema lines for `interlocking.geometry` and `officeUnit.geometry`); §4.3 says appliances, track and geometry are
  open until the trackplan piece of the compiler lands, C4 says fixing them is a minor version (3.1.0), §10 lists
  "geometry in detail" as out of scope. The compiler (`tools/layout_compiler/`) writes nothing there.
- **The design rule already exists**: `docs/review/layout-model-view-2026-10-16.md` §4.7 and O12. The drawing is a
  design fact; the trackplan sheet is drawn to look like the railroad and Studio's canvas will be drawn the same
  way. Per interlocking the compiler records placements of track, appliance and marker symbols (position, rotation,
  mirror) and the track segments as polylines, in a normalised frame, and **never uses them for connectivity**
  (`AGENTS.md`: netlist and ERC are ground truth). The model board, the thinline diagram and the doc package derive
  their styles from it; milepost anchors order interlockings along the subdivision (ADR 0004 D7). The view says the
  section's detail is written against the existing picture generator as its first consumer.
- **The first consumer exists as a proof of concept**: `tools/plant_graph/layout.py` ("pure longitudinal layout
  solving for static plant board projections") and `tools/plant_graph/picture.py` ("static topology-picture
  projection"), with `tools/render_plant_picture.py` (needs Graphviz `dot`). They read the archived per-project
  drawings through the old compiler, not the Layout Data Model File. They are evidence of what a view needs, not a
  reference for how the file should look (`AGENTS.md`: the old compilers are proofs of concept).
- **The owner's four views** (2026-10-24): a "thinline" mainline-only view; a "modelboard" schematic view; a "route
  finder" debug and analysis view; a "documentation packet" printed and web view. The owner: "Way back, we ALSO put
  great effort into capturing the geographic layout of the trackplan and appliances such that the graphical
  trackplan could be recreated and manipulated into" these. None is supported by the file today, and the owner asked
  whether that was missed. It was not missed; it was deferred, and it is now this segment's work.
- **The drawing** is the Railroad project at `d51f78e` on `feat/deployment-cases` (`~/Dropbox/KiCad/Railroad`,
  pushed), ERC 0. Every placed symbol the compiler names carries `Name` = `${Value}`; the trackplan symbols are
  `Railroad-Trackplan` (APPLIANCE, TRACK, POLICY, STRUCTURE roles; Kinds in ADR 0009 §3.10). Placement is not in the
  netlist: it is in the `.kicad_sch` files (`(symbol ... (at x y rot) (mirror ...))`, `(wire (pts ...))`, labels),
  read today only by the edit scripts' helpers (`SPCoast/edits/2026-10-21-explicit-seams.py`: `instances`,
  `inst_at`) and by `tools/kicad_services` (schematic placement reader; reuse it, do not write a new parser).

## The work, in order

1. **Read before writing**: the view §3 (Sargent worked) and §4.7; ADR 0008 §4.3, §4.4 (the KiCad boundary and the
   R2 test "would Studio need it?"), §4.7, §4.8 (canonical form), C4, C8; ADR 0009 §3.10 (the trackplan Roles and
   Kinds) and §3.12; `AGENTS.md` "KiCad conventions the compiler relies on" (plant schematics); the two plant_graph
   modules above as the first consumer; ADR 0004 D7 (mileposts). Then the Sargent and Luchessa trackplan sheets in
   KiCad, with the owner, to see what the thinline must drop and the model board must keep.
2. **ADR 0010, proposed, one ask: ratify.** Architecture ADR method (`feedback-architecture-adr-method`): cited
   rules first, then derivation; tag each rule model / representation / operating; pictures first (a worked Sargent
   geometry excerpt and the four views sketched from it); decisions requested up front, one line each, with a
   default. The decisions the owner has to make, with the defaults this session would propose:
   - **What is a geometry fact.** Default: per interlocking, each trackplan symbol's placement (position, rotation,
     mirror, the symbol it is), each track wire as a polyline, each label with its anchor; per office unit, each
     column's and panel device's placement. Nothing a view styles (colour, line weight, font) and nothing a view
     derives (the mainline, routes, the subdivision strip).
   - **The frame.** Default: a normalised frame per interlocking (origin and scale fixed by rule, not KiCad's sheet
     coordinates), so the R2 test passes: Studio needs every placement; no view needs a KiCad coordinate. Decide
     whether the sheet's own frame and scale are recorded in `provenance` for round-tripping to KiCad.
   - **Ordering along the subdivision.** Default: by the `Milepost` of each house (ADR 0004 D7), with the
     `NextCP` and `END_CTC` track symbols as the adjacency facts; the subdivision strip is derived, not written.
   - **Where it lives.** Default: `interlockings.<name>.geometry` and `officeUnits.<name>.geometry`, keyed by the
     entity names of `appliances`, `track` and `devices` so a view joins geometry to meaning by name (ADR 0008 §4.5:
     relations by name, no ids). Decide how a track wire without a named circuit is keyed.
   - **The gates.** Default: the four views are reader-side consumers that gate the section (ADR 0008 §3 style):
     the picture generator re-targeted to read the file is the first; the thinline is the hardest reduction and the
     second. A geometry fact no view reads is not written (view O13: absence is information; one source per fact).
   - **Version.** Default: schema 3.1.0, a minor version (C4), with `appliances` and `track` fixed in the same
     version by the semantics segment or in the one before; agree the order with that session.
3. **The compiler piece** only after ratification: a placement reader in `tools/layout_compiler/` over the
   `.kicad_sch` files through `tools/kicad_services`, emitting `geometry`; the example regenerated; tests that the
   normalised frame is stable under a sheet move and that no connectivity is inferred from it.
4. **The first view**: `render_plant_picture.py` reading the file instead of the archived drawings, as the first
   gate; then the thinline. The model board, route finder and doc package are later segments, each a reader.

## Rules this session must keep

- Vocabulary: FieldUnit `docs/GLOSSARY.md` (the seam vocabulary was added on branch
  `docs/glossary-seams-2026-10-24`, not yet merged) and ADR 0009 §3.11: OfficeUnit, FieldUnit, CMRInet Node,
  Driver, head device, columns, processor; KiCad symbol units are units; interlocking, house, control point, field
  station as the glossary says. Say "the Layout Data Model File" or "the JSON" for the artifact and "the Layout
  Data Model" for the model; the owner finds "file" alone ambiguous.
- Proposals are ADRs with the asks first and defaults; a question gets an answer and discussion, and no ADR, library
  or memory edit until the owner says a point is settled; ask decisions in plain text, never choice cards.
- Netlist and ERC are ground truth for connectivity; geometry never infers a connection. Reuse
  `tools/kicad_services`; write no new s-expression parser.
- Any drawing edit is a dated script in Railroad `SPCoast/edits/` with a `--check` gate (netlist diff against the
  committed baseline, exact field deltas, ERC no new type and no count grown); baseline the owner's uncommitted edits
  first; check for `~*.lck` and a running KiCad before touching a `.kicad_sch`; derived files go in
  `SPCoast/production/` (gitignored; `SPCoast.net` is the current export). Never refresh a cached symbol whose
  library pins moved. Library edits never reach placed instances: script the instances too.
- Run Python as `uv run python`; `kicad-cli` at `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`.
- Commit finished work every turn with Conventional Commits and a "Verified:" section; never push unless the owner
  asks (they asked on 2026-10-24 for that session's branches); the owner merges.
- `Value` is never read by the compiler: every key is a functionally named attribute carrying `${Value}`. A new
  symbol that the compiler must name gets `Name` (or the functional key) in the library and on its instances.
