# Layout model — spike-first plan (draft for review, 2026-10-02, rev 3)

Status: draft under review. Companion to `layout-model.md` (rev 8, the data
model) and `desk-codeline-kicad-pattern.md` §4/§4a (the KiCad symbol
contracts). Rev 2 replaced the requirements-first plan with a spike and two
functional gates (level-set 2026-09-30) and kept the designer's §0 edits.
Rev 3 aligns the terms and the code line steps with ADR 0001 and ontology
rev 5.

## Revision (2026-10-02, rev 3)

Sources: `docs/adr/0001-code-line-type-contract.md` (accepted, D1–D16),
`docs/design/ontology.md` rev 5, `vocabulary-review.md` iterations 8–10.

2026-10-02 (iteration 11): proxy names, MAIN HOUSE required, machine type kept as panel style, operator roles, topic normalization

- Terms. "CP" as a common noun becomes "control point". "Station" becomes
  "field station". "Host program" becomes "simulated field processor". "Desk"
  is kept.
- §0: the order of authority is added, the three phases of ADR D6, and the scope of the code line work
  (first target AAR tokens over MQTT; US&S 506 not ruled out, D14).
- Step 2.1: control points come from `MAIN HOUSE` symbols and are never
  counted. One normalization: a space becomes `-` in a topic or key (D12,
  amended); no code adds or strips a `CP` prefix.
- Step 2.3: the control point of each mast comes from its `CP` field.
- Step 2.6: field stations are derived per code line type (D3). Addresses
  come from the `CODELINE` symbol (D13).
- Step 2.7: "signal CP from the lever's column" and "CODE grouping vs plant
  interlocking" are replaced: the column of a lever or lamp decides its field
  station, and a difference from the `CP` field is not an error (D3).
  Capacity and size-limit checks of the drawn default are added (D5, D16).
- Steps 4 and 5: the generator phase is stated between the model and run
  time (D6). The emulator target selects interlockings, not stations.
- Step 6: pattern doc §2 and §7a are added to the rewrite list (ADR 0001,
  consequences).
- Cross-repo items: encoding and transport definition files (D10), the
  two-pin `CODELINE` symbol (D15), the name fix (D12) and the move of
  the encoding `US&S506` out of `Type` are added. The machine keeps `Type` as
  its panel style.
- Removed (overridden): "signal CP from the lever's column" and "CODE
  grouping vs plant interlocking" as cross-checks (step 2.7, overridden by
  ADR D3).
- Roles (iteration 11). "Controller" is not a term for a role. Only the
  dispatcher's CTC machine is modelled; the tower operator and the maintainer
  are not yet covered. `controller_graph`, `controllers{}` and
  `parse_kicad_controller.py` are code names and keep their spelling.

## 0. Decisions this plan rests on

- **From first principles.** The current `plant_graph`, `controller_graph`,
  `link` packages, their CLIs, `schemas/interlocking-plant/v1.json` and the
  122 tests are a learning exercise: illustrative, not definitive. None of
  them is a requirement. They stay in the tree as reference until the spike
  passes its gates, then are deleted in one commit.
- **Order of authority** (vocabulary review, iteration 9): (1) the relay
  model of the interlocking logic (glossary §10.6); (2) `src/` in FieldUnit;
  (3) KiCad-derived interlocking models; (4) legacy sketches and
  XML-harvested profiles, as evidence only. Where FieldUnit differs from the
  relay model, the code has a defect.
- **Harvest knowledge, not code.** Track-net walking, OS circuits, canonical
  names, route and best-indication derivation, the Graphviz picture: copied
  in behind the new model types when the spike needs them, never imported.
- **Requirements live in Gherkin, implementation tests are ephemeral.**
  `features/` holds behave scenarios that capture purely functional requirements;
  if they fail, a contract with another entity has been broken.  These scenarios
  are created with a preference for minimization and must express a single functional
  requirement. As they capture committed relationships that impact other projects,
  scenarios evolve slowly, compatability forward; deletions and incompatable changes
  must align with an intentional contract change and be syncronized across all impacted
  parties.
  `tests/` holds unittest/pytest tests that MUST stay in sync with implementation evolution.
  Unit tests never duplicate or take the place of functional tests; they are never
  considered a requirement, as they exist only to validate implementation correctness.
- **Contracts do not exist yet, so scenarios wait for the gates.** No
  behave, no pytest, no golden document during the spike. KiCad projects
  make poor fixtures (invisible preconditions, heavy to maintain: the jBOM
  lesson), and a snapshot taken before a consumer exists is the compiler's
  own opinion. The gates are: (1) a doc package that recreates the pictures
  and tables from the KiCad sources, reviewed by the designer; (2) a
  FieldUnit emulation that decodes and runs the plant from the model. The
  contracts established there (model ↔ FieldUnit, model ↔ generators) are
  what the first scenarios capture, using jBOM's pattern: table-based steps
  that build a model document directly, a generic baseline every scenario
  can assume, sandboxes for preconditions, no KiCad in the step layer.
- **The spike is v0.2 and may be thrown away.** v1.0 is whatever survives
  the gates. `layout-model.md` stays the spec and is revised as the gates
  reveal gaps.
- **Three phases** (ADR 0001 D6): compiler and linker (the model), generator
  (chooses the code line type target, builds the code charts, emits the
  interlocking application and the CTC machine application from one set of
  chart tables), run time (encodes and decodes by the chart). Each phase
  checks the capacity and size limits it can see (D5, D16).
- **Code line scope** (ADR D14): the first working target is AAR tokens
  over MQTT. Nothing in the model or the code may rule out US&S 506. A
  virtual target needs no added data and is always available (D13).
- **Sources are ready**
  - repo: ~/Dropbox/Arduino/libraries/FieldUnit/
  - repo: ~/Dropbox/workspace/FieldUnit-Subdivision/
  - repo: ~/Dropbox/KiCad/Railroad/
  - Symbol libraries: ~/Dropbox/KiCad/InterlockingPlant/symbols/[Railroad, RailroadPanel] (not in git yet)
- **FieldUnit evolves with the model** rather than being shimmed. Where the
  model needs FieldUnit to change (`bestIndication`, decoding the model's
  plant, I/O from the model, one generic codec that runs a code chart), the
  change is made there.
- **Design guidance**
  - Simple solutions are preferred over complexity
  - Avoid tech debt - loose ends, little things, uncommitted files, code changes without test and doc refreshes
  - No backwards compatability shims - as above, this spike is driving towards a 1.0 MVP toolchain, harvesting knowledge from existing code.  It is always OK to rewrite the functionality and/or change that code.

## 1. Repo shape after the spike

```
tools/
  kicad/            front end: readers (today's kicad_services), Role/Kind classification, project discovery, source versions
  compile/          one compiler, phases
  model/            types, JSON, versioning (schema written when v1.0 is declared, not before)
  generate/         one package; targets are settings: report, emulator, desk, picture …; the code line type target is one setting
  compile_layout.py folder in, model out
  generate.py       model in, artifact out
generated/          SPCoast.json and generated artifacts (gitignored until v1.0)
features/           added at step 6, jBOM pattern (environment.py sandbox rule, recipe, table-based steps)
tests/              implementation tests, in sync with the implementation, never requirements
docs/review/        layout-model.md, this plan, pattern doc
```

Encoding and transport definitions are not in this repo. They are data
files in the SPCoast KiCad repo (ADR D10).

## 2. Steps

One branch, `feature/layout-model-spike`; commits per step; PRs at the two
gates. Nothing old is deleted until step 6. Uncommitted files, loose ends
and stale docs are debt (§0), so each step ends with its docs refreshed.

### Step 1. Model and front end

- `tools/model/`: dataclasses mirroring `layout-model.md` §1 exactly, JSON
  emission with stable key order, `identity.schemaVersion`, `compiler` and
  per-source `version` (`git describe --dirty --always`, netlist sha256,
  timestamp). No schema file yet.
- `tools/kicad/`: today's `kicad_services` readers moved unchanged;
  project discovery (folder = membership; MAIN HOUSE ⇒ plant, MACHINE ⇒
  CTC machine; a plant project with no MAIN HOUSE is an error); Role/Kind classification with `unknown-role` / `unknown-kind`
  diagnostics; sheet paths; source versions.
- One `Diagnostic` type: severity, code, `about` (entity refs), message,
  optional `sourceRef`.

### Step 2. Compiler v0.2, phase by phase

Dependency order; each phase is run on the live `SPCoast/` folder as it
lands and its output read, nothing frozen.

1. **Control points and interlockings.** One plant project is one
   interlocking. Each `MAIN HOUSE` symbol (Role `CONTROLLED_POINT` today, a
   code name to review) declares one control point; its Value is the name.
   The compiler never derives or counts control points. A plant project with no
   `MAIN HOUSE` symbol is an error: the symbol is the explicit source of the
   name, and it can display a title block variable. It checks that each
   Value is present and unique, and that each `CP` field resolves to a
   `MAIN HOUSE` Value of the same project. A space becomes `-` in a topic or
   key (D12); no code adds or strips `CP`.
   Appliances by Kind (`SWITCH_POWERED`, `SWITCH_LOCK`, `DERAIL`,
   `TRACK_CIRCUIT`, `MAINTAINER_CALL`, `AUXILIARY`), assigned to a control
   point by their `CP` field. Harvest canonical-name and allocation rules
   from `plant_graph/compiler.py`.
2. **Topology** from `TRACK` symbols and nets: segments, nodes, terminals,
   OS circuits. Harvest net walking, IRJ handling, OS derivation.
3. **Signals, masts, heads**: masts grouped by number; `COMPONENT` heads
   folded into masts; the control point of each mast from its `CP` field
   (on `IRJ_SIGNAL` today; some projects write it on the mast, so read
   both, ontology §6).
4. **Routes and best indication** with `POLICY` symbols. Harvest
   `routes.py` and `indications.py`; the ten Luchessa routes compared
   against today's output and against the drawing.
5. **CTC machines**: machine (with its panel style, `Type`), ordered columns, appliances with inline
   `functions` from IODRIVER bits, column membership from column pins.
   Harvest `controller_graph` net logic. Bindings compared against
   `IO-I2C.h`, the one binding fact validated on the real desk.
6. **Attachments, codelines, field stations**: at most one Codeline symbol
   per sheet; null = in-process; instances by transport + Broker/Port;
   `Railroad` replaces `TopicRoot`. Field stations derived per code line
   type (ADR D3): one per control point on a 506-style encoding, one per
   interlocking on AAR tokens. Addresses read from the `CODELINE` symbol
   (D13), never allocated (D4). Today `Codeline-MQTT` names the transport
   only; the encoding is AAR tokens by implication until the two-pin
   `CODELINE` symbol exists (D15).
7. **Cross-checks** re-derived from the model, only what a generator
   needs: column `CP Name` ↔ `MAIN HOUSE` Value of that sheet's
   interlocking; lever ↔ switch kind; the lever rule of the panel style (an error for the
   lever panel); lamp tokens; the field station of each
   function from the column of its lever or lamp (D3). A difference between
   an appliance's `CP` field and that column is not an error. Capacity of
   the drawn default, counting steps after the code chart (D5), and size
   limits the compiler can see (D16).
8. **Field units**: the phase exists with no rows until §5a symbols exist
   (step 7).

`compile_layout.py` writes `generated/SPCoast.json`.

### Step 3. Gate 1: the doc package

`generate.py --target report`: a Markdown package from the model alone
that recreates what the KiCad sources show: the plant picture (harvest the
Graphviz renderer behind the new model), the desk column, appliance and
binding tables, appliance tables for each control point (by `CP` field),
signal, mast and route tables with best indications, code line and field
station tables (with addresses where authored), diagnostics. The designer
compares it with the schematics. Every discrepancy is a compiler bug or a
model gap; model gaps go back into `layout-model.md` as a revision.
**PR 1** when the package is judged faithful. Tag the Railroad repo then.

### Step 4. FieldUnit decodes the model

In the FieldUnit repo: `PlantSerializer` (or a successor) accepts the
model's interlocking and control point content directly, with
`bestIndication` replacing `maxIndication`. The generator stands between
the model and run time (D6): it builds the code chart of each field station
for the chosen target (for AAR tokens the chart is the identity) and emits
it with the plant. The generic-JSON knowledge in `fieldunit_projection.py`
becomes the `emulator` target's embedded payload, never a file on disk.
This is the first contract with another entity in the §0 sense.

### Step 5. Gate 2: the emulation

`generate.py --target emulator --interlockings …`: a simulated field
processor program that runs the field units of a selected set of
interlockings, realized `EMULATED`, plant definitions embedded. The
generator takes the code line type from the model's drawn default: AAR
tokens over MQTT for Luchessa (D14). It builds the code charts and checks
capacity and size limits for that target (D5, D16). The maintainer calls
come from the model, not from code (ontology §5.3). It must pass the six
scenarios that `spcoast_virtual_plant --test` runs today, then be driven by
the current desk sketch over MQTT. The desk sketch builds its own token
list today (ADR 0001, "What the code does today"), so gate 2 also shows
whether the two lists agree. When FieldUnit runs Luchessa from the model
with no hand-written plant data, the model is proven sufficient for its
hardest consumer. **PR 2.** Selection syntax is decided here, not in the
model.

### Step 6. Declare v1.0, delete the old, write the contracts

- `schemas/layout-model/1.0.json`; `generated/SPCoast.json` committed as a
  regression snapshot (a change detector, never a requirement).
- Delete `plant_graph`, `controller_graph`, `link`, the three CLIs,
  `schemas/interlocking-plant/`, old tests and fixtures, the smoke script,
  `profiles/spcoast_south/cps/generated/`, `runtime/plant_host/`.
- `features/` per §0: the model ↔ FieldUnit contract (what the emulator
  target must embed) and the model ↔ report contract, from table-built
  model documents; then the desk. Implementation tests only where they
  earn their keep, kept in sync.
- `AGENTS.md`, `README.md`, pattern doc §2/§6/§7a/§8/§10 rewritten (§2,
  §7a and §10 are replaced by ADR 0001 D2, D3, D5 and D6).

### Step 7. Next targets

- `desk`: the SPCoast South sketch replacing `examples/spcoast_ctc`,
  compiled with `arduino-cli` (`esp32:esp32:XIAO_ESP32C6`), uploaded;
  `cTcMachine` lamp-slot conflation fixed in FieldUnit when this needs it.
  The CTC machine application takes its token lists from the same code
  charts as the interlocking application (D6). `CtcStation` becomes one per
  field station.
- Field side: §5a symbol design (FIELDUNIT, I/O proxies, field IODRIVERs),
  Luchessa hardware sheet, compiler phase 8, `fieldunit` target, FieldUnit
  taking I/O from the model instead of `IO-xxx.h`.
- US&S 506 is not a target of this plan. It needs authored addresses (D13)
  and a choice of the Luchessa CODE button workaround (D9).

### Cross-repo items

- FieldUnit: step 4; later the desk and field-side items above; one generic
  codec that runs a code chart at both ends.
- Railroad: commit the eight modified sheets; tag at gate 1; `kicad.mk`
  gains `compile`/`generate` rules calling this repo's CLIs.
- Railroad (SPCoast): encoding and transport definition files and their
  schema (D10, D11); the source fix for names (D12: `MAIN HOUSE` Values,
  `CP` fields, `CP Name`); the encoding `US&S506` moved from `CtcMachine` `Type` to
  the code line (the machine keeps `Type` as its panel style).
- Symbol libraries: the two-pin `CODELINE` symbol and the one-pin encoding
  and transport symbols (D15).
- Symbol libraries into git (own repo or under Railroad: decide) so source
  versions are complete.

## 3. Verification

- Steps 1–2: `compile_layout.py` on the live `SPCoast/` folder, zero
  error-severity findings on Luchessa, output read by the designer.
- Gate 1: the report package judged faithful to the schematics.
- Gate 2: the emulator passes the six scenarios and runs under the current
  desk sketch over MQTT.
- Desk bindings equal `IO-I2C.h` throughout.
- Conventional Commits with "Verified:"; two PRs, at the gates; no
  uncommitted leftovers between steps.

## 4. Decisions for this review

1. **Gate 2 ownership across repos**: the emulator program (a simulated
   field processor) is generated into this repo and FieldUnit gains only the
   decoder, or the emulator becomes a FieldUnit example?
2. **Symbol libraries' git home**: own repo, or under Railroad?
3. **`generated/SPCoast.json`**: gitignored during the spike (proposed),
   committed as a snapshot at v1.0.
