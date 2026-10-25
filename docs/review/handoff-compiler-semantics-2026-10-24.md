# Handoff: the semantic compiler, after ADR 0008 rev 4 and ADR 0010

Written 2026-10-24 at the close of the ADR 0008 rev 4 segment; revised 2026-10-25 after ADR 0010's acceptance, when
the owner pivoted to the compiler itself. This is now the one handoff for the milestone D compiler segment. The
parallel geometry handoff (`handoff-0010-geometry-2026-10-24.md`) is closed: its ADR is accepted, and its compiler
and view items continue here as C1, C2 and C3 of ADR 0010, interleaved with the seven semantics items below.

## Where things stand

- **ADR 0008 rev 4** is accepted (2026-10-24, Subdivision `a3f1e35`); `schemas/layout-model/v3.0.0.json` is the
  public interface, `tools/layout_model` validates and writes canonically, `tools/layout_compiler/` (the seam
  reader: `source.py`, `seams.py`, `emit.py`; CLI `tools/compile_layout.py NETLIST -o OUT [--log] [--quiet]`) writes
  `schemas/layout-model/examples/spcoast.layout.json` from a netlist of the Railroad project
  (`schemas/layout-model/examples/make_spcoast_layout.py`). Two compiles are byte-identical. 184 tests
  (`uv run python -m unittest discover -s tests -q`); `tests/test_layout_compiler.py` proves ADR 0009 §3.12 on the
  SPCoast netlist when present and the rules on in-memory sources (`plant()`, `jmri_plant()` builders).
- **ADR 0010, geometry and the four views, is accepted** (2026-10-24, Subdivision `6b99317` on branch
  `docs/adr-0010-geometry`, not pushed; the owner merges). It fixes the `geometry` fragment per interlocking
  (placements by name with every `at` at the glyph's bottom-left pin, runs of track as rows with SVG points strings
  and their circuit, unnamed track symbols as marker rows joined by circuit, switch ports as `to:
  "Luchessa:783.R"`), `layout.glyphs{}` (every glyph written once, keyed by library and symbol name, KiCad's stroke
  and fill where not default, width 0 written as no width), the frame (millimetres, KiCad's numbers unrounded,
  y down, mirror then rotate then translate), membership by Role (§4.1: `APPLIANCE`, `TRACK`, `POLICY`, plus the
  house as `STRUCTURE` with Kind `CONTROL_POINT`; never by library, name or position; a wire is track when it ends
  on a trackplan pin, its circuit from the netlist), order along the subdivision derived from mileposts and
  `NextCP`, and the office unit's geometry empty. Its gates are DoD1 to DoD4 (the four views read the Layout Data
  Model File; byte-identical under a sheet move; byte-identical outside `geometry` with the placement reader off;
  every key has a consumer). Its consequences C1 to C8 are the compiler work folded in below; C5 is already in
  `AGENTS.md`.
- **The geometry reference implementation** is `docs/adr/0010/make_pictures.py`: it reads the trackplan sheets with
  jBOM's loader and the `Railroad-Trackplan` library, exports its own netlist to a temp file, writes
  `docs/adr/0010/sargent.geometry.json` (1086 lines, 19 glyphs, 74 primitives) against
  `docs/adr/0010/geometry.schema.json`, and asserts its y-down transform over the written glyphs against KiCad's
  library-frame transform for every pin of every placement. It is the worked form of the ratified fragment, written
  for pictures, not a compiler module: C2 moves its reading into `tools/kicad_services` and `tools/layout_compiler`
  and the picture script becomes a consumer of the Layout Data Model File (C3), so no second parser survives.
- **What the compiler resolves today** (ADR 0009 §3.12, every relation by wire and by fallback, disagreement an
  error): the Railroad symbol's layout facts; processors; office units and their columns (house by `CP Name`, else
  interlocking by folder); transports (anchors = drawn instances) and the encodings riding them; interlockings and
  houses (milepost, maintainer call); CMRInet Nodes by UA with their bits; drivers on buses (chips by `Address`,
  bits by `IB.n`/`OB.n`, JMRI objects by `Kind.servedDevice`); devices, one row each, masts included, with bindings
  as routes and `Invert` as `invert`; heads to trackplan heads (§3.7 vocabulary). Macros `<ROLE:KIND:Field>` are
  expanded. Reports on SPCoast: 66 info (`*.explicit_only`, `transport.reach`), 11 missing (`column.cp_name`), 0
  errors, 0 `identity.value`.
- **What it does not read yet**: the trackplan's meaning and its geometry. `interlocking.appliances`,
  `interlocking.track` and `interlocking.geometry` are open objects (schema; ADR 0008 §4.3, C4: fixing them is a
  minor version). `_heads` already walks the trackplan for head Style and mast names, and `_houses` for maintainer
  calls; nothing else of `Railroad-Trackplan` is read. The old proof-of-concept compiler
  `tools/plant_graph/compiler.py` (`_PART_KIND`, routes, indications) knows the conventions and is evidence of them,
  never the reference (`AGENTS.md`; order of authority).
- **The drawing**: Railroad `b309d9a` on `feat/deployment-cases` (not pushed), ERC 0, lint
  `tools/contract/lint_symbol_fields.py` 0 errors. Since `d51f78e` every symbol the compiler names carries `Name` =
  `${Value}` (a trackplan head's `Name` is its letter) and `Columns` is gone from the OfficeUnit. Since `37a0dcd` the
  owner's Industry symbol (Role `TRACK`, Kind `INDUSTRY`, one pin: "track exists past this point, but is not drawn")
  replaces the stubs drawn into dark track at Sargent, Corporal and Luchessa, and Luchessa's industry spur has an END
  CTC; so no run of track on the project ends anywhere but at a symbol. Since `b309d9a` `Driver-JMRI-Light` carries
  one Kind (`LIGHT`). Luchessa's switch ports 783.R, 799.N and 799.R are met by wires directly; 783 and 795 share
  IRJ B7002. The Trackplan library has 39 symbols and no `extends`; Role, Kind and Style are not one to one with a
  symbol (switch and powered switch in four orientations, three track circuit markers, two IRJs, two Rule 251, two
  derails), which is why glyphs are keyed by library and symbol name and nothing is keyed by glyph.
- **The netlist rule** (owner, 2026-10-24, `AGENTS.md` Commands): netlists are a cached version of the KiCad
  project's state and become invalid whenever the project is modified; (A) never use a stale cached netlist;
  (B) a generated netlist is volatile, created in a temp location and deleted when its immediate use is complete
  (`KicadCliNetlistExporter` in `tools/kicad_services/netlist_reader.py` exports one). The compiler test's default
  `SPCOAST_NETLIST` and `make_spcoast_layout.py`'s default still name `SPCoast/production/SPCoast.net` with no
  staleness check: item 0 below.
- **Rulings of 2026-10-24 in force** (recorded in ADR 0008 §8 and C11): no key from `Value`, no exception ("the
  data model keys should be chosen to be functional descriptions of their use/content, and the kicad symbol
  attribute names should reflect that choice"); JMRI drivers need no address and are keyed by object class and
  served device, a Turnout's command and feedback symbols are one driver, a drawn `Address` overrides at info;
  every Mast is a device row; `anchors` are drawn instances and a FieldUnit reaches its code line's transport through
  the code line (0009 §3.12's check redefined); `Columns` derived. ADR 0009 §3.10 already carries `INDUSTRY`
  (record entry 2026-10-24). The glossary delta is applied in FieldUnit on branch `docs/glossary-seams-2026-10-24`
  (`f9c0e4d`, pushed, not merged).
- **Reviews**: `docs/review/adr-0008-rev4-review-2026-10-23.md` (27 findings, all dispositioned);
  `docs/review/naming-audit-2026-10-22.md`; `docs/review/glossary-delta-2026-10-23.md` (applied).

## The work, in order

The seven semantics items (the owner's list of 2026-10-25) and ADR 0010's C1, C2 and C3 are one sequence. The
trackplan semantics piece and the geometry piece read the same symbols and ship in one schema version; the readers
of C2 can be built against the ratified geometry fragment while the semantics shape is still being proposed, so 3
can run beside 2 if the session prefers, but 3.1.0 ships once.

0. **The netlist rule in the tooling.** `tests/test_layout_compiler.py` and `make_spcoast_layout.py` export a fresh
   netlist through `KicadCliNetlistExporter` into a temp location and delete it after use when `kicad-cli` is
   present; `SPCOAST_NETLIST` and the positional argument stay as explicit overrides for a machine without KiCad,
   with the warning that an override is the caller's cache. First, because every later gate compiles the project.
1. **ADR 0009 amendments** (0008 C11 lists them; the owner said amendments, not a new decision): §3.10 gains Kind
   `RAILROAD`, the macro rule, model board lamps as PANEL devices of Style `board` without a `Column` pin, `Name` on
   every keyed symbol and `Value` never read, `Kind` on an encoded driver and `Kind.name` as its key, a Mast as a
   device with a row, `anchors` as drawn instances with §3.12's check redefined; §3.5 the bit numbering base (1)
   and direction from pin type; §3.12's head row "`IND` wire to a Mast device"; §3.2 IC `CMRI` versus `CMRInet`.
   `INDUSTRY` is already in §3.10. One rev of 0009, record entry, no new ask beyond "amend as C11 says". Propose;
   the owner approves; then edit.
2. **The trackplan piece: `appliances` and `track`.** Read first: the view
   (`docs/review/layout-model-view-2026-10-16.md`) §3.1, §4.2 and §6; ADR 0003 (D1 direction normalisation, D8
   dependent derails, D9 mast letters); ADR 0009 §3.10 (Roles APPLIANCE, TRACK, POLICY, STRUCTURE and their Kinds)
   and §3.7; ADR 0010 §4.1 (membership by Role; the wire rule), §4.5, §4.6 and C6; `AGENTS.md` "Plant schematics";
   the memory `spcoast-kicad-vocabulary-and-unify-decisions`. Then, as a proposed change to 0008 (a minor version is
   a schema change, C8: never a quiet edit), the shape of:
   - `appliances{name}`: switches (gang id = `Name` minus its trailing letter; one gang, several symbols), derails
     (dependent on a gang by `<id>D`, NORMAL derailing), masts (heads by letter with Style from the trackplan head;
     the head devices already join by `serves` and `head`), track circuits (`Name` authoritative; the OS circuit of
     a switch defaults to `<switch>T1`, `TC` overrides), contacts, auxiliaries, maintainer calls (already joined to
     houses). Each appliance's `controlPoint` is **derived** from the signals (`IRJ-Signal` carries `CP`; ADR 0009
     and the unify decisions: "CP on IRJ-Signal only"), never stated per appliance; that derivation is what lets the
     Trackplan `CP` field retire (item 6). A switch's ports are named `N`, `R` and `C` as geometry already names
     them in `to:` references (ADR 0010 §4.6); one vocabulary for both pieces.
   - `track{}`: circuits and their joints (`IRJ`, `IRJ_Diag`, `IRJ-Signal`), `END_CTC`, `NextCP`, `Milepost`,
     `Bumper`, `Industry`; the policies (`Rule105`, `Rule251` left/right, `Rule261`, `Rule93 Yard Limits`) with
     `Direction` where drawn. Track nets need labels except OS legs, dark track and derail nets (`AGENTS.md`).
     ADR 0010 C6 binds the two pieces: `track` describes joints, ends and signs as facts of the circuits they bound,
     by circuit name, so geometry's `markers[]` joins to it without a key of its own; if this piece gives those
     things names instead, `markers[]` becomes a map by those names in the same version.
   - What stays out (the view §6: a computer derives it): signals' aspects, routes, limits, OS circuits as logic.
     They belong to the evaluated model and the FieldUnit generators (milestone E), not the Layout Data Model File.
   The same Role test picks the symbols this piece reads and the symbols C2 places; a `DEVICE`, an `IODRIVER`, the
   processor and the `Interlocking` declaration on the trackplan sheet belong to neither.
   Gates: the relation table grows rows for each trackplan relation (wire, fallback, check), tested on the SPCoast
   project; the example regenerated and byte-stable; `test_drawing_has_no_errors` stays green; the counts in 0008 §6
   updated by reading them off the Layout Data Model File.
3. **ADR 0010 C1, schema `layout-model/v3.1.0`**: one version adds `$defs/geometry` as `docs/adr/0010/geometry.schema.json`
   states it (lifted, not retyped), `layout.glyphs{}`, and the `appliances` and `track` shapes of item 2; one example
   regenerated; one migration note (ADR 0008 C8); ADR 0008 §4.1's "named by key and version, never copied" amended:
   the glyphs a layout draws with are copied once into `layout.glyphs{}`, the libraries and the reference data stay
   named. ADR 0008 C4's open objects close. DoD4 is checked here: every key of the fragment names its view in 0010 §4.
4. **ADR 0010 C2, the compiler piece**: a placement reader over the `.kicad_sch` files through `tools/kicad_services`
   (`SchematicPlacementReader` reads symbols today; wires and junctions are added beside it) and a glyph reader over
   the symbol libraries beside `SymbolLibraryReader` (pins, pin lines, polylines, circles, three-point arcs,
   rectangles, fixed text, stroke and fill); the generic part is a kicad-primitives ticket under ADR 0007. The
   compiler scopes placements to an interlocking by sheet (ADR 0004 D12), normalises per 0010 §4.2 and §4.3 (origin
   at the bottom-left pin: least y, then least x, in the library frame; the library is untouched, C8), joins runs to
   circuits through the netlist and never the reverse, and reports a run that ends at no port as an error (0010 §7,
   rev 2). Tests: DoD2 (translate a trackplan sheet, byte-identical), DoD3 (placement reader off, byte-identical
   outside `geometry`), the per-pin transform assertion the picture script already makes, and a 90-degree rotated
   fixture (the project draws rotations and mirrors; prove each case the library has). The example regenerated.
5. **ADR 0010 C3, the first view**: `tools/render_plant_picture.py` reading the Layout Data Model File (no KiCad
   schematic, no netlist, no symbol library, no archived drawing) as the model board and the route finder, the first
   gate (DoD1); the thinline second. `tools/plant_graph` retires behind it under ADR 0008 C6's "then go in one
   commit". The documentation packet and the route overlay follow as readers; the picture script of
   `docs/adr/0010/` becomes a reader too or is retired in that commit.
6. **The Trackplan `CP` field retirement**, a Railroad script with a gate whose oracle is the derived membership of
   item 2 (every `CP` field value equals the derived control point, else the drawing or the derivation is wrong).
   Deferred on 2026-10-23 for exactly this reason; gated on the derivation, never before it.
7. **`CP Name` on the 11 AAR-line columns** (Christopher 8 to 10, Corporal 11 and 12, Gilroy Caltrain 1 and 2,
   Gilroy Interchange 3 and 4, Sargent 13, Watsonville 14): an owner edit or a script; then `columns{}` names houses
   throughout and `column.cp_name` goes to 0. Ask the owner which house each column names where an interlocking has
   two (Christopher North and South, Gilroy North and South).
8. **Reference data as encountered** (ADR 0008 §4.7; milestone rule "reference data as encountered"): the two tables
   the compiler carries as constants (`TRANSPORT_OF_ENCODING`, `ENCODING_OF_IC`, dated in `REFERENCE_DATA`) and
   the boards and driver ICs the generators will need, each in its own small document when first needed. Settle
   `CMRI` versus `CMRInet` as the IC and Kind token there (0009 §3.2, C11). The symbol libraries stay reference data
   named by key and version; only their glyphs are copied (item 3).
9. **The three-copy experiment** (ADR 0009 C7): the all-explicit and all-implicit copies of the project, compiled to
   the same Layout Data Model File as the "both" copy. Milestone D's acceptance. Needs two scripted derivations of
   the drawing, not hand copies; with geometry in the Layout Data Model File, the derivations must move no symbol, or DoD2 says why a
   move is harmless.
10. **The boundary to milestone E**: the reader library (ADR 0008 C2) reads the Layout Data Model File, evaluates in
    memory, reports absences as info; FieldUnit's generators consume the reader's result. The four views of ADR 0010
    are readers in this sense, and the first of them (item 5) is this segment's gate; the library itself is **not
    this segment's work; do not start it without the owner.**

## Rules this session must keep

- Order of authority: the relay model and AAR practice; FieldUnit `src/`; KiCad-derived models; legacy sketches and
  harvests as evidence only. Never rewrite a principle to match weaker code.
- Vocabulary: FieldUnit `docs/GLOSSARY.md` (the seam vocabulary is on branch `docs/glossary-seams-2026-10-24`) and
  ADR 0009 §3.11. Three files are in play and each is named every time: the KiCad schematic, the netlist, and the
  Layout Data Model File (or "the JSON"); "the Layout Data Model" is the model. Never the unqualified word "file".
  CMRInet is the protocol's name.
- Facts, not symbols (ADR 0001 D15): a rule that reads "is there a symbol on this sheet" stands for a fact that
  lives elsewhere. Every key is a functionally named attribute carrying `${Value}`; the compiler never reads
  `Value`, and a new symbol it must name gets the attribute in the library and on its instances by script. What is
  on the trackplan is decided by Role, never by library, symbol name or position (ADR 0010 §4.1).
- Geometry is read for geometry only (ADR 0010 R2, DoD3; `AGENTS.md` C5): no connectivity, no membership and no name
  comes from a coordinate. The geometry fragment is ratified; change it only by an amendment to ADR 0010 with a
  record entry, never by a quiet edit to the schema or the reader.
- Proposals are ADRs with the asks first and defaults; one ask per ADR; a question gets an answer and discussion,
  and no ADR, library or memory edit until the owner says a point is settled; decisions in plain text, never choice
  cards; one consolidated list of pending decisions, not a narrative. Cleanup of the source data is preferred over
  code or schema complexity.
- Netlist and ERC are ground truth. Netlists are a cache of the KiCad project's state: never use a stale one; export
  a fresh one with `KicadCliNetlistExporter` into a temp location, use it, delete it. Drawing edits are dated scripts
  in Railroad `SPCoast/edits/` with a `--check` gate (netlist diff against the committed baseline, exact field
  deltas, ERC no new type and no count grown); baseline the owner's uncommitted edits first; check for `~*.lck` and a
  running KiCad before touching a `.kicad_sch`; `kicad-cli sch export netlist --format kicadsexpr` and `sch erc
  --format json --severity-all`; derived files go in `SPCoast/production/` (gitignored), and a netlist kept there is
  a cache under the rule above (each edit keeps `<edit>-after.net` and `.erc.json` as its record). Never refresh a
  cached symbol whose library pins moved. Library edits never reach placed instances. Run
  `tools/contract/lint_symbol_fields.py` after any library edit.
- Reuse `tools/kicad_services` (`SchematicPlacementReader`, `SymbolLibraryReader`, `KicadCliNetlistExporter`, jBOM's
  loader underneath); write no new s-expression parser. The picture script's reading is evidence of what the readers
  must do, to be moved, not copied.
- Compiler errors are fact inconsistencies only; no Layout Data Model File is written while one stands. Absence is
  information. Nothing in the Layout Data Model File names a sheet, net, reference, lib id or KiCad symbol unit,
  except the glyph key, which is the library's own name for a drawing (ADR 0010 R3, §4.9).
- Run Python as `uv run python`; `kicad-cli` at `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`;
  `PYTHONDONTWRITEBYTECODE=1` for the tests.
- Commit finished work every turn with Conventional Commits and a "Verified:" section; never push unless the owner
  asks; the owner merges. Goldens change in their own commit; prefer behavioural gates.
- Adversarial review by a fresh agent, anchored on the sources of truth and not on the writer's reasoning, before
  asking the owner to ratify anything; save the report verbatim under `docs/review/`.
