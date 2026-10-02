# Layout model — spike-first plan (draft for review, 2026-09-30, rev 2)

Status: draft under review. Companion to `layout-model.md` (rev 7, the data
model) and `desk-codeline-kicad-pattern.md` §4/§4a (the KiCad symbol
contracts). Rev 2 replaces the requirements-first plan with a spike and two
functional gates (level-set 2026-09-30) and keeps the designer's §0 edits.

## 0. Decisions this plan rests on

- **From first principles.** The current `plant_graph`, `controller_graph`,
  `link` packages, their CLIs, `schemas/interlocking-plant/v1.json` and the
  122 tests are a learning exercise: illustrative, not definitive. None of
  them is a requirement. They stay in the tree as reference until the spike
  passes its gates, then are deleted in one commit.
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
- **Sources are ready**
  - repo: ~/Dropbox/Arduino/libraries/FieldUnit/
  - repo: ~/Dropbox/workspace/FieldUnit-Subdivision/
  - repo: ~/Dropbox/KiCad/Railroad/
  - Symbol libraries: ~/Dropbox/KiCad/InterlockingPlant/symbols/[Railroad, RailroadPanel] (not in git yet)
- **FieldUnit evolves with the model** rather than being shimmed. Where the
  model needs FieldUnit to change (`bestIndication`, decoding the model's
  plant, I/O from the model), the change is made there.
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
  generate/         one package; targets are settings: report, emulator, desk, picture …
  compile_layout.py folder in, model out
  generate.py       model in, artifact out
generated/          SPCoast.json and generated artifacts (gitignored until v1.0)
features/           added at step 6, jBOM pattern (environment.py sandbox rule, recipe, table-based steps)
tests/              implementation tests, in sync with the implementation, never requirements
docs/review/        layout-model.md, this plan, pattern doc
```

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
  controller); Role/Kind classification with `unknown-role` / `unknown-kind`
  diagnostics; sheet paths; source versions.
- One `Diagnostic` type: severity, code, `about` (entity refs), message,
  optional `sourceRef`.

### Step 2. Compiler v0.2, phase by phase

Dependency order; each phase is run on the live `SPCoast/` folder as it
lands and its output read, nothing frozen.

1. **CPs and interlockings** from `CONTROLLED_POINT` symbols and `CP`
   fields; appliances by Kind (`SWITCH_POWERED`, `SWITCH_LOCK`, `DERAIL`,
   `TRACK_CIRCUIT`, `MAINTAINER_CALL`, `AUXILIARY`). Harvest canonical-name
   and allocation rules from `plant_graph/compiler.py`.
2. **Topology** from `TRACK` symbols and nets: segments, nodes, terminals,
   OS circuits. Harvest net walking, IRJ handling, OS derivation.
3. **Signals, masts, heads**: masts grouped by number; `COMPONENT` heads
   folded into masts; house allocation from `IRJ_SIGNAL`'s `CP`.
4. **Routes and best indication** with `POLICY` symbols. Harvest
   `routes.py` and `indications.py`; the ten Luchessa routes compared
   against today's output and against the drawing.
5. **Controllers**: machine, ordered columns, appliances with inline
   `functions` from IODRIVER bits, column membership from column pins.
   Harvest `controller_graph` net logic. Bindings compared against
   `IO-I2C.h`, the one binding fact validated on the real desk.
6. **Attachments, codelines, stations**: at most one Codeline symbol per
   sheet; null = in-process; instances by transport + Broker/Port;
   stations derived; `Railroad` replaces `TopicRoot`.
7. **Cross-checks** re-derived from the model, only what a generator
   needs: signal CP from the lever's column; column ↔ CP; lever ↔ switch
   kind; lamp tokens; CODE grouping vs plant interlocking.
8. **Field units**: the phase exists with no rows until §5a symbols exist
   (step 7).

`compile_layout.py` writes `generated/SPCoast.json`.

### Step 3. Gate 1: the doc package

`generate.py --target report`: a Markdown package from the model alone
that recreates what the KiCad sources show: the plant picture (harvest the
Graphviz renderer behind the new model), the desk column, appliance and
binding tables, per-CP appliance tables, signal, mast and route tables with
best indications, codeline and station tables, diagnostics. The designer
compares it with the schematics. Every discrepancy is a compiler bug or a
model gap; model gaps go back into `layout-model.md` as a revision.
**PR 1** when the package is judged faithful. Tag the Railroad repo then.

### Step 4. FieldUnit decodes the model

In the FieldUnit repo: `PlantSerializer` (or a successor) accepts the
model's interlocking and CP content directly, with `bestIndication`
replacing `maxIndication`. The generic-JSON knowledge in
`fieldunit_projection.py` becomes the `emulator` target's embedded payload,
never a file on disk. This is the first contract with another entity in
the §0 sense.

### Step 5. Gate 2: the emulation

`generate.py --target emulator --stations …`: a host program for a selected
set of stations, realized `EMULATED`, plant definitions embedded, codeline
per the model (MQTT for Luchessa). It must pass the six scenarios that
`spcoast_virtual_plant --test` runs today, then be driven by the current
desk sketch over MQTT. When FieldUnit runs Luchessa from the model with no
hand-written plant data, the model is proven sufficient for its hardest
consumer. **PR 2.** Selection syntax is decided here, not in the model.

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
- `AGENTS.md`, `README.md`, pattern doc §6/§8/§10 rewritten.

### Step 7. Next targets

- `desk`: the SPCoast South sketch replacing `examples/spcoast_ctc`,
  compiled with `arduino-cli` (`esp32:esp32:XIAO_ESP32C6`), uploaded;
  `cTcMachine` lamp-slot conflation fixed in FieldUnit when this needs it.
- Field side: §5a symbol design (FIELDUNIT, I/O proxies, field IODRIVERs),
  Luchessa hardware sheet, compiler phase 8, `fieldunit` target, FieldUnit
  taking I/O from the model instead of `IO-xxx.h`.

### Cross-repo items

- FieldUnit: step 4; later the desk and field-side items above.
- Railroad: commit the eight modified sheets; tag at gate 1; `kicad.mk`
  gains `compile`/`generate` rules calling this repo's CLIs.
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

1. **Gate 2 ownership across repos**: the emulator host program is
   generated into this repo and FieldUnit gains only the decoder, or the
   emulator becomes a FieldUnit example?
2. **Symbol libraries' git home**: own repo, or under Railroad?
3. **`generated/SPCoast.json`**: gitignored during the spike (proposed),
   committed as a snapshot at v1.0.
