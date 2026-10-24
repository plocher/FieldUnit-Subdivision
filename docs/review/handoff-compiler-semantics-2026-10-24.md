# Handoff: the semantic compiler, after ADR 0008 rev 4

Written 2026-10-24 at the close of the ADR 0008 rev 4 segment, for the session that continues the milestone D
compiler: the trackplan's meaning, the open objects of the schema, and the loose ends the rulings left. It runs in
parallel with `handoff-0010-geometry-2026-10-24.md`; the two meet at `appliances` and `track` (the same symbols,
read for meaning here and for placement there) and at the schema's next minor version. Agree the order of the two
3.1.0 changes with that session, or ship one 3.1.0 together.

## Where things stand

- **ADR 0008 rev 4** is accepted (2026-10-24, Subdivision `a3f1e35`); `schemas/layout-model/v3.0.0.json` is the
  public interface, `tools/layout_model` validates and writes canonically, `tools/layout_compiler/` (the seam
  reader: `source.py`, `seams.py`, `emit.py`; CLI `tools/compile_layout.py NETLIST -o OUT [--log] [--quiet]`) writes
  `schemas/layout-model/examples/spcoast.layout.json` from the Railroad production netlist
  (`schemas/layout-model/examples/make_spcoast_layout.py`). Two compiles are byte-identical. 184 tests
  (`uv run python -m unittest discover -s tests -q`); `tests/test_layout_compiler.py` proves ADR 0009 §3.12 on the
  SPCoast netlist when present (`SPCOAST_NETLIST`, default `~/Dropbox/KiCad/Railroad/SPCoast/production/SPCoast.net`)
  and the rules on in-memory sources (`plant()`, `jmri_plant()` builders).
- **What the compiler resolves today** (ADR 0009 §3.12, every relation by wire and by fallback, disagreement an
  error): the Railroad symbol's layout facts; processors; office units and their columns (house by `CP Name`, else
  interlocking by folder); transports (anchors = drawn instances) and the encodings riding them; interlockings and
  houses (milepost, maintainer call); CMRInet Nodes by UA with their bits; drivers on buses (chips by `Address`,
  bits by `IB.n`/`OB.n`, JMRI objects by `Kind.servedDevice`); devices, one row each, masts included, with bindings
  as routes and `Invert` as `invert`; heads to trackplan heads (§3.7 vocabulary). Macros `<ROLE:KIND:Field>` are
  expanded. Reports on SPCoast: 66 info (`*.explicit_only`, `transport.reach`), 11 missing (`column.cp_name`), 0
  errors, 0 `identity.value`.
- **What it does not read yet**: the trackplan's meaning. `interlocking.appliances` and `interlocking.track` are
  open objects (schema; ADR 0008 §4.3, C4: fixing them is a minor version). `_heads` already walks the trackplan
  for head Style and mast names, and `_houses` for maintainer calls; nothing else of `Railroad-Trackplan` is read.
  The old proof-of-concept compiler `tools/plant_graph/compiler.py` (`_PART_KIND`, routes, indications) knows the
  conventions and is evidence of them, never the reference (`AGENTS.md`; order of authority).
- **The drawing**: Railroad `d51f78e` on `feat/deployment-cases` (pushed), ERC 0, lint
  `tools/contract/lint_symbol_fields.py` 0 errors on 99 symbols. Since 2026-10-24 every symbol the compiler names
  carries `Name` = `${Value}` (Processor, Transport-*, Interlocking, Railroad, OfficeUnit, Encoding-*, every DEVICE
  and PANEL, every Trackplan APPLIANCE; a trackplan head's `Name` is its letter). `Columns` is gone from the
  OfficeUnit. The five JMRI drivers carry `Kind` (TURNOUT, SENSOR, SIGNALMAST) and `Driver-JMRI-Light` (LIGHT)
  exists; Gilroy Interchange's MC1 and MC2 are Lights. The two Light bodies on that sheet overlap by one row
  (cosmetic; the owner nudges in KiCad).
- **Rulings of 2026-10-24 in force** (recorded in ADR 0008 §8 and C11): no key from `Value`, no exception ("the
  data model keys should be chosen to be functional descriptions of their use/content, and the kicad symbol
  attribute names should reflect that choice"); JMRI drivers need no address and are keyed by object class and
  served device, a Turnout's command and feedback symbols are one driver, a drawn `Address` overrides at info;
  every Mast is a device row; `anchors` are drawn instances and a FieldUnit reaches its code line's transport through
  the code line (0009 §3.12's check redefined); `Columns` derived. The glossary delta is applied in FieldUnit on
  branch `docs/glossary-seams-2026-10-24` (`f9c0e4d`, pushed, not merged).
- **Reviews**: `docs/review/adr-0008-rev4-review-2026-10-23.md` (27 findings, all dispositioned);
  `docs/review/naming-audit-2026-10-22.md`; `docs/review/glossary-delta-2026-10-23.md` (applied).

## The work, in order

1. **ADR 0009 amendments** (0008 C11 lists them; the owner said amendments, not a new decision): §3.10 gains Kind
   `RAILROAD`, the macro rule, model board lamps as PANEL devices of Style `board` without a `Column` pin, `Name` on
   every keyed symbol and `Value` never read, `Kind` on an encoded driver and `Kind.name` as its key, a Mast as a
   device with a row, `anchors` as drawn instances with §3.12's check redefined; §3.5 the bit numbering base (1)
   and direction from pin type; §3.12's head row "`IND` wire to a Mast device"; §3.2 IC `CMRI` versus `CMRInet`.
   One rev of 0009, record entry, no new ask beyond "amend as C11 says". Propose; the owner approves; then edit.
2. **The trackplan piece: `appliances` and `track`**, schema 3.1.0. Read first: the view
   (`docs/review/layout-model-view-2026-10-16.md`) §3.1, §4.2 and §6; ADR 0003 (D1 direction normalisation, D8
   dependent derails, D9 mast letters); ADR 0009 §3.10 (Roles APPLIANCE, TRACK, POLICY, STRUCTURE and their Kinds)
   and §3.7; `AGENTS.md` "Plant schematics"; the memory `spcoast-kicad-vocabulary-and-unify-decisions`. Then, as a
   proposed change to 0008 (a minor version is a schema change, C8: never a quiet edit), the shape of:
   - `appliances{name}`: switches (gang id = `Name` minus its trailing letter; one gang, several symbols), derails
     (dependent on a gang by `<id>D`, NORMAL derailing), masts (heads by letter with Style from the trackplan head;
     the head devices already join by `serves` and `head`), track circuits (`Name` authoritative; the OS circuit of
     a switch defaults to `<switch>T1`, `TC` overrides), contacts, auxiliaries, maintainer calls (already joined to
     houses). Each appliance's `controlPoint` is **derived** from the signals (`IRJ-Signal` carries `CP`; ADR 0009
     and the unify decisions: "CP on IRJ-Signal only"), never stated per appliance; that derivation is what lets the
     Trackplan `CP` field retire (deferred item below).
   - `track{}`: circuits and their joints (`IRJ`, `IRJ_Diag`, `IRJ-Signal`), `END_CTC`, `NextCP`, `Milepost`,
     `Bumper`; the policies (`Rule105`, `Rule251` left/right, `Rule261`, `Rule93 Yard Limits`) with `Direction` where
     drawn. Track nets need labels except OS legs, dark track and derail nets (`AGENTS.md`).
   - What stays out (the view §6: a computer derives it): signals' aspects, routes, limits, OS circuits as logic.
     They belong to the evaluated model and the FieldUnit generators (milestone E), not the file.
   Gates: the relation table grows rows for each trackplan relation (wire, fallback, check), tested on the SPCoast
   netlist; the example regenerated and byte-stable; `test_drawing_has_no_errors` stays green; the counts in 0008 §6
   updated by reading them off the file.
3. **The Trackplan `CP` field retirement**, a Railroad script with a gate whose oracle is the derived membership of
   step 2 (every `CP` field value equals the derived control point, else the drawing or the derivation is wrong).
   Deferred on 2026-10-23 for exactly this reason.
4. **`CP Name` on the 11 AAR-line columns** (Christopher 8 to 10, Corporal 11 and 12, Gilroy Caltrain 1 and 2,
   Gilroy Interchange 3 and 4, Sargent 13, Watsonville 14): an owner edit or a script; then `columns{}` names houses
   throughout and `column.cp_name` goes to 0. Ask the owner which house each column names where an interlocking has
   two (Christopher North and South, Gilroy North and South).
5. **Reference data as encountered** (ADR 0008 §4.7; milestone rule "reference data as encountered"): the two tables
   the compiler carries as constants (`TRANSPORT_OF_ENCODING`, `ENCODING_OF_IC`, dated in `REFERENCE_DATA`) and
   the boards and driver ICs the generators will need, each in its own small document when first needed. Settle
   `CMRI` versus `CMRInet` as the IC and Kind token there (0009 §3.2, C11).
6. **The three-copy experiment** (ADR 0009 C7): the all-explicit and all-implicit copies of the project, compiled to
   the same file as the "both" copy. Milestone D's acceptance. Needs two scripted derivations of the drawing, not
   hand copies.
7. **The boundary to milestone E**: the reader library (ADR 0008 C2) reads the file, evaluates in memory, reports
   absences as info; FieldUnit's generators consume the reader's result. Not this segment's work; do not start it
   without the owner.

## Rules this session must keep

- Order of authority: the relay model and AAR practice; FieldUnit `src/`; KiCad-derived models; legacy sketches and
  harvests as evidence only. Never rewrite a principle to match weaker code.
- Vocabulary: FieldUnit `docs/GLOSSARY.md` (the seam vocabulary is on branch `docs/glossary-seams-2026-10-24`) and
  ADR 0009 §3.11. Say "the Layout Data Model File" or "the JSON" for the artifact; "the Layout Data Model" for the
  model. CMRInet is the protocol's name.
- Facts, not symbols (ADR 0001 D15): a rule that reads "is there a symbol on this sheet" stands for a fact that
  lives elsewhere. Every key is a functionally named attribute carrying `${Value}`; the compiler never reads
  `Value`, and a new symbol it must name gets the attribute in the library and on its instances by script.
- Proposals are ADRs with the asks first and defaults; one ask per ADR; a question gets an answer and discussion,
  and no ADR, library or memory edit until the owner says a point is settled; decisions in plain text, never choice
  cards; one consolidated list of pending decisions, not a narrative. Cleanup of the source data is preferred over
  code or schema complexity.
- Netlist and ERC are ground truth. Drawing edits are dated scripts in Railroad `SPCoast/edits/` with a `--check`
  gate (netlist diff against the committed baseline, exact field deltas, ERC no new type and no count grown);
  baseline the owner's uncommitted edits first; check for `~*.lck` and a running KiCad before touching a
  `.kicad_sch`; `kicad-cli sch export netlist --format kicadsexpr` and `sch erc --format json --severity-all` into
  `SPCoast/production/` (gitignored; `SPCoast.net` is the current export, each edit also keeps `<edit>-after.net`
  and `.erc.json`). Never refresh a cached symbol whose library pins moved. Library edits never reach placed
  instances. Run `tools/contract/lint_symbol_fields.py` after any library edit.
- Compiler errors are fact inconsistencies only; no file is written while one stands. Absence is information.
  Nothing in the file names a sheet, net, reference, lib id or KiCad symbol unit.
- Run Python as `uv run python`; `kicad-cli` at `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`;
  `PYTHONDONTWRITEBYTECODE=1` for the tests.
- Commit finished work every turn with Conventional Commits and a "Verified:" section; never push unless the owner
  asks; the owner merges. Goldens change in their own commit; prefer behavioural gates.
- Adversarial review by a fresh agent, anchored on the sources of truth and not on the writer's reasoning, before
  asking the owner to ratify anything; save the report verbatim under `docs/review/`.
