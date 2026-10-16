# Handoff: from the symbol libraries to the compiler's I/O section (2026-10-16)

- For: the orchestrator session that takes the next segment. Read this file first, then the
  record it points at. It is written to be the only thing that session needs beyond the repo's
  `AGENTS.md` and the memory directory it inherits.
- From: the session that ran the library segment (2026-10-09 to 16), `digest-io-baseline`.
- Status: the libraries segment is closed. Every SPCoast sheet is on the four Railroad libraries,
  Sargent is redrawn on the new symbols with every I/O pin bound, ERC is clean across the project
  (Railroad PR #11), and the I/O design checkpoint is at rev 14 with step 6's drawing half closed.

## 1. What this segment produced

- Four symbol libraries in `~/Dropbox/KiCad/Railroad/symbols/`: `Railroad-Trackplan` (38 plant
  symbols), `Railroad-Office` (20: the CTC machine's plates, column, machine, code line),
  `Railroad-Field` (16: device symbols and the `Local-*` plates), `Railroad-HardwareIO` (8: I2C
  chips, GPIO pins, `Setting`). 82 symbols, hand-maintained in the KiCad Symbol Editor since the
  2026-10-11 cutover. The gate is `tools/contract/lint_symbol_fields.py` (0 errors), the render
  check `tools/contract/symbol_contact_sheet.py`, the documentation page
  `tools/kicad_library_overview.py` (writes `symbols/production/overview/library-overview.html`).
- Every symbol is keyed by fields, never by name: `Role`; `Appliance` and `Style` on plant and
  device symbols; `IC` on I/O symbols; one `Pin.<base>` word per function pin, the base of
  `~{OCC}` being `OCC`; `Invert` as a list of pin names; settings as `lower_snake_case` fields.
  The capability words carry no direction: `binary`, `level`, `position`, `color`, `pixel`,
  `message`; direction is the KiCad electrical type, and a binding is valid when the words match
  and the types are complementary (checkpoint E66).
- A symbol whose pins mix word or type is multi-unit, one unit per capability, body graphics in
  unit 0, Value fixed, units not interchangeable, so the units mesh on a sheet and show one name
  (E56). `Terminal` and the adapter idea are gone (E56, E71).
- The SPCoast project, `~/Dropbox/KiCad/Railroad/SPCoast/`, migrated by text with
  `SPCoast/edits/2026-10-12-migrate-libraries.py` (re-runnable; carries post-migration renames)
  and checked by `tools/contract/netlist_diff.py`, the connectivity gate. Sargent's field sheet
  is the first real I/O drawing: three track circuit detectors, the manual switch and its OS
  switch device, the 835 lock plates, two CPL encoder heads, one CL head (836SA, RGB legs), one
  RGB semaphore head (836SB) on a second PCA9685 as servo, two lamps, an MCP23017 and a
  PCA9685-PWM. Device references are by kind: `DevHead`, `DevLamp`, `DevSW`, `DevLock`, `DevTC`,
  `DevContact` (E73). Always name a symbol to the owner by Value and symbol name, never by
  reference.
- Python is per repo with uv (`pyproject.toml`, Python 3.14, `jbom>=7.10.2` from PyPI,
  `sexpdata`; `uv sync`, `uv run ...`). The system `python3` is 3.15 without the dependencies.

## 2. The record, in reading order

1. `docs/review/io-design-checkpoint-2026-10-10.md`, rev 14. THE record: eleven learned points,
   E1 to E73 owner decisions, I1 to I34 implicit decisions, §4.1 symbols by Role, Appliance and
   Style, §4.2 registries, §5 tasks and next steps. Nothing below contradicts it; where a view
   and the checkpoint differ, the checkpoint wins.
2. `docs/review/driver-architecture-foundation.md`. The governing text for the driver
   architecture; the checkpoint records decisions taken under it.
3. `docs/review/environment-view-2026-10-09.md`, rev 10. The driver environment: identity,
   bindings, settings, services, construction; §5 is the model's shape, the input to the schema.
4. `docs/review/driver-types-view-2026-10-09.md`, rev 4. The device and I/O types, their
   signatures, commands, attributes, settings. Its `binary in` and `binary out` read as the word
   plus the pin type (E66).
5. `docs/review/symbol-library-triage-2026-10-10.md`, rev 4. How the libraries were made and
   migrated; closed.
6. `docs/review/kicad-services-survey-2026-10-12.md`. The KiCad services across the owner's
   repos, with fifteen pending decisions; the owner is still reviewing it, and the
   `kicad-primitives` package is a separate project at `~/Dropbox/KiCad/kicad-primitives` of
   which this repo is a late-stage consumer. Do not start that work here.
7. FieldUnit: `docs/GLOSSARY.md` (vocabulary, the source of truth), `docs/AAR_SIGNALING_PRIMER.md`
   §17 and §18 (semaphores and eras, the electric lock step by step), `docs/adr/0006-dual-control-switch.md`
   (proposed).

## 3. What the next segment delivers, in order

The checkpoint's next steps 7, 5, 8 and 9. Step 7 first, because it reads Sargent.

1. **Step 7: the compiler's I/O section and the model schema.** Read the netlist of the SPCoast
   project (`kicad-cli sch export netlist --format kicadsexpr`, into `SPCoast/production/`, never
   beside the schematics) and the four libraries, and produce, per interlocking, the bindings:
   for every device and plate function pin, the I/O pin it lands on, the chip from `IC`, the
   capability at each end, the cast path and its settings, the `Address` on bus devices, the
   `Invert` lists, the processor that owns the expander and therefore consumes the device (E43,
   E44, I27), column membership on the desk (E41), lamp joins by Value or token list (E42),
   tokens derived as Value plus pin (I28). The shape is the environment view §5; the schema is
   new and goes where the unify plan put schemas, beside `schemas/interlocking-plant/v1.json`,
   with the owner's say on its name. Diagnostics follow E49: unconsumed and unbound are
   informational; contradiction is an error. `IndicationCeiling` is the field; read
   `Indications` as a fallback until every sheet carries the new name. The compiler must not
   depend on symbol names (learned 9) or references.
2. **Step 5: the indexers.** Casts, their settings and factory defaults, and the driver types'
   signatures come from the FieldUnit source tree, published as one indexed document
   (`fieldunit-index/v1`, I21), read by the compiler beside the libraries; and a symbol
   requirements report from the libraries. Their form inside FieldUnit is the first question to
   put to the owner; it is an ADR, not a guess.
3. **Step 8: glossary.** The foundation's amendments plus the new terms: capability, cast,
   binding, setting scope, chip setting, `Invert`; adapter is not a term. FieldUnit PR.
4. **Step 9: the alternatives ADR for Part 2** (proposals #1, #2, #3 in the foundation), once
   Part 1 is stable, in `docs/adr/` here, opening with the decisions requested, one line each,
   with a default.

## 4. Gates

- Functional gates over fixtures (owner). For step 7: the compiler resolves every binding on
  Sargent's field sheet and the desk's Sargent column with no error-level diagnostic, and reports
  the informational ones the drawing earns (unconsumed `835UNUSED`, I33). The earlier spike,
  `binding_pass.py` and `binding_pass2.py` in the gitignored `~/Dropbox/KiCad/Railroad/Scratch/tools/`,
  resolved 17 bindings on the Scratch sheet with two true diagnostics; it read the old fields and
  is evidence of the rules, not code to keep. Archive the two scripts under `docs/archive/` first
  (survey decision 11), then write the real thing.
- The existing suite stays green under `uv run python -m unittest discover -s tests -q` (147).
  `tools/run_plant_graph_smoke.sh` fails today with five known diagnostics from the old
  proof-of-concept compiler against the archived Luchessa drawing (#15); do not fix that by
  teaching the old compiler new symbols.
- The virtual plant host self-test (`spcoast_virtual_plant --test`, built per `AGENTS.md`) must
  still pass when anything under `runtime/` or `profiles/` changes.
- A golden changes only in its own commit; the desk fixture `South-cTc.net` is known stale (#23).
- Before any edit to a `.kicad_sch` or `.kicad_sym`: check for `~*.lck`; the owner usually has
  KiCad open. Prefer reading the netlist. If a text edit is needed, use `kicad_services.sch_text`
  and run the connectivity gate before and after.

## 5. Standing rules, as the owner stated them this segment

- Order of authority: the relay model and AAR practice; FieldUnit `src/` (defective where it
  differs); KiCad-derived models; legacy sketches and harvested profiles as evidence only.
- A question gets an answer and discussion before anything changes. No doc, memory or library
  edit until the owner says it is settled. Decisions are asked in plain text, one consolidated
  list, each with a default; never as choice cards.
- Proposals are ADRs in `docs/adr/`. Review material lives in `docs/review/`; superseded
  material is committed, pushed, then removed.
- Feature branches and PRs with Conventional Commits and a "Verified:" section; the owner merges.
  After a merge, return the checkout to main and delete the branch.
- Unconsumed and unbound items are informational, never refusals: layouts are under construction.
- Watsonville is not evidence for rules, but it is migrated like every sheet.
- Settings are `lower_snake_case` on symbols; the compiler normalises before use.

## 6. Settled, do not re-derive

| Topic | Where |
|---|---|
| Capability words without direction; binding validity by word and complementary type | E66 |
| Multi-unit symbols, unit 0 rule, Terminal retired | E56 |
| Adapters withdrawn; three wires is a device signature; casts stay one wire to one wire | E71 |
| Head Styles CL, CPL, LQ, UQ; the six head devices; the semaphore lamp as a colour point | E65, E71 |
| Switch Styles powered, manual, manual_sensed, lock, derail, dual | E63 |
| Field layout closed; Local plates are devices; PANEL if and only if Column | E68, E72 |
| `WLK` asserted means released, fail-safe; `WLQK` the request | E55, primer §18 |
| Searchlight is CL; the aspect set is an era fact, never a link error | E47, E48 |
| Style selects the handler; the index is open to user source | E52 |
| `Invert` as the logical complement; `~{}` stays electrical | E53 |
| Four libraries by the sheet they serve | E67 |
| Reference prefixes by kind; references decide nothing | E73 |

## 7. Decisions still open, one line each

1. The schema's name and home for the bindings model (step 7). Default: `schemas/layout/v1.json`
   in this repo until FieldUnit claims it (unify plan: schema in FieldUnit).
2. The form of the FieldUnit index (`fieldunit-index/v1`) and what generates it (step 5).
   Default: a script in FieldUnit `tools/` reading its `src/`, committed output in `docs/`.
3. The Style word lists for contact (`lock_request`, `button`, `door`), mast and lamp.
   Default: as listed in I8 and I23 until a drawing needs another.
4. Where the era indication tables live in FieldUnit (E48). Default: an ADR when step 5 reaches
   them.
5. The layout anchor symbol on the root sheet and the field processor symbol (I31). Default: the
   anchor on the root sheet when the first layout-scope setting is drawn; no processor symbol
   while the `MAIN HOUSE` identifies it.
6. The survey's fifteen pending decisions: the owner is reviewing; 2 was done as "PyPI release,
   checkout as an opt-in source", 12 and 15 are done. Default: leave the rest to the owner and
   the `kicad-primitives` project.
7. Whether the compiler keeps requiring `Rulebook` on the direction markers (AGENTS.md says it is
   behind). Default: read the symbol's Role and Style, accept `Rulebook` as a fallback, report
   its absence as informational.

## 8. Debts and issues that touch this work

- #15 plant compiler classification by Role and fields; #23 the stale desk fixture; #30 the
  cleanup pass over the legacy drawings; #26 the epic for the model, link and generate layer;
  #16 controlled points optional; #19 the linker's control point check.
- `tools/plant_graph` and `tools/controller_graph` are proofs of concept kept to check the new
  project against the archive; the new compiler is written from scratch (unify plan).
- Two Watsonville `AUXILIARY` markers replaced the retired traffic markers by the owner's hand;
  the compiler produces fleet indications itself.
- The glossary retires "desk" for "CTC machine"; the library name `Railroad-Office` follows it.
