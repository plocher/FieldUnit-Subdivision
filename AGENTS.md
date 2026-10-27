# AGENTS.md

Guidance for agentic coders working in FieldUnit-Subdivision. Read `README.md`
first; this file adds what an agent needs that the README does not say.

## What this repo owns

FieldUnit-Subdivision is the operating-subdivision layer (SPCoast South: 7
interlockings, one 14-column desk: the SPCoast CTC machine, US&S style). It owns:

- **KiCad → data tooling**: reading plant and desk schematics and emitting the
  portable model, FieldUnit interlocking model JSON, board pictures, and (planned) desk
  firmware.
- **Subdivision runtime**: virtual plants, train progression, board and crew views.

It does **not** own vital logic. Plants run FieldUnit's interlocking logic (`InterlockingPlant`);
never copy or reimplement interlocking rules here.

## Related repos and sources of truth

| Path | Role | Truth it owns |
| --- | --- | --- |
| `~/Dropbox/KiCad/Railroad/SPCoast/` | the unified KiCad project (git; hand-maintained since the 2026-10-07 cutover) | Plant topology, desk and field wiring as drawn |
| `~/Dropbox/KiCad/Railroad/Archive/SPCoast/<Project>/` | the per-project drawings as of 2026-10-07 (read-only) | Reference for checking the unified project |
| `~/Dropbox/KiCad/Railroad/symbols/` | `Railroad-Trackplan`, `Railroad-Office`, `Railroad-Field`, `Railroad-HardwareIO.kicad_sym` | Symbol and field contracts, hand-maintained in KiCad since 2026-10-11; gate `tools/contract/lint_symbol_fields.py`, render check `tools/contract/symbol_contact_sheet.py`. Symbols are keyed by fields (Role, Appliance, Style, `IC`, `Pin.*`, `Invert`), never by name. The old `Railroad`, `RailroadPanel`, `RailroadField` libraries in `~/Dropbox/KiCad/InterlockingPlant/symbols/` stay registered only for sheets not yet migrated. |
| `~/Dropbox/Arduino/libraries/FieldUnit` | Header-only C++17 library (git) | Interlocking logic, codecs, `PlantSerializer`, `cTcMachine`, and the `examples/spcoast_ctc` desk sketch |
| this repo | Tooling and runtime | Everything derived from the above |

The symbol libraries are registered globally in
`~/Library/Preferences/kicad/10.0/sym-lib-table` by absolute path. KiCad 10 is required.

## Commands

```zsh
uv sync                                        # once per checkout: .venv with Python 3.14, jbom (the PyPI release) and sexpdata
uv run python -m unittest discover -s tests -q # 303 tests; the SPCoast gates export a fresh netlist with kicad-cli and skip without it
uv run tools/run_plant_graph_smoke.sh          # Luchessa end-to-end; needs kicad-cli. Fails today: the old compiler reports 5 known diagnostics on the archived drawing (#15)
```

- Python is managed per repo with `uv` (`pyproject.toml`, `.python-version`, `uv.lock`; `.venv` is gitignored). Never rely on the system `python3`: a Homebrew or macOS update replaced it with 3.15 without the dependencies (2026-10-16). Run every script as `uv run python <script>`, or `uv run --project ~/Dropbox/workspace/FieldUnit-Subdivision python <script>` from another repo (the Railroad `edits/` scripts import `tools/kicad_services` this way).

- `kicad-cli` is not on PATH. Tools find it through `KICAD_CLI` or the app bundle
  (`/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`); it exports the SPCoast netlist in about 2 s (2026-10-27).
  Without KiCad, pass a saved netlist; `tools/kicad_services/snapshot.py` then refuses it when the Railroad repo has
  uncommitted drawing or library changes, or a commit to them newer than the netlist file (the importer reads the
  sheets and libraries live, so the netlist must be the same snapshot).
- **Netlists are a cached version of the KiCad project's state.** They become invalid whenever the KiCad
  project is modified. Agents and the KiCad importer may use netlists as part of their
  activities and follow these rules (owner, 2026-10-24): (A) never use a stale cached netlist; (B) treat
  generated netlists as volatile artifacts, created in a temp location and deleted when their immediate
  use is complete (`KicadCliNetlistExporter` exports one; the old rule, prefer the `.net` and refresh it
  with `make netlist`, had agents reading a stale copy for several turns before noticing).
- Environment overrides: `KICAD_RAILROAD_LIB`, `KICAD_LUCHESSA_SCH`.
- `render_plant_picture.py` needs Graphviz `dot`.
- Virtual plant host. The build command is not scripted yet; this is the known-good form:
  ```zsh
  clang++ -std=c++17 -I ~/Dropbox/Arduino/libraries/FieldUnit/src -DHAS_MOSQUITTO \
    runtime/plant_host/spcoast_virtual_plant.cpp -lmosquitto -o spcoast_virtual_plant
  ./spcoast_virtual_plant --test        # 6-scenario self-test
  ```
  It needs mosquitto on `localhost:1883` (`brew services start mosquitto`). The
  root `spcoast_virtual_plant` binary is a gitignored build artifact. Run it from
  the repo root, or pass `--profiles <dir>` (default `profiles/spcoast_south/cps`).
- Archived KiCad project outputs (netlist, plant JSON, SVG) are rebuilt with `make` in each
  `~/Dropbox/KiCad/Railroad/Archive/SPCoast/<Project>/` (shared rules in `Archive/SPCoast/kicad.mk`).
  The unified `SPCoast` project is maintained by hand in KiCad since the 2026-10-07 cutover; its
  migration script is retired in `docs/archive/unify/`. Derived files (netlists, ERC reports, JSON,
  SVG) go in `<project>/production/`, never beside the schematics; a netlist kept there is a cache
  under the netlist rule above. The proof-of-concept compilers (plant and controller) are
  kept to check the new project against the archive, not to compile it.
- Set `PYTHONDONTWRITEBYTECODE=1` or clean up `__pycache__`. Stale caches reference removed modules.
- `tools/kicad_services` imports `jbom` as an installed package, the PyPI release pinned in `pyproject.toml`; the old `sys.path` reach into the jBOM checkout is gone (KiCad services survey, decision 2). To test against the live checkout, uncomment the `[tool.uv.sources]` block in `pyproject.toml` and `uv sync`; do not commit that. jBOM's own command line is a `uv tool install jbom`, separate from this venv.

## Layout

- `tools/kicad_services/`: generic KiCad readers (netlist with its sheet files and a fresh-export context manager, schematic placements with wires and junctions, symbol library pin contracts and graphics, the `sym-lib-table`). Reuse these; do not write new s-expression parsers.
- `tools/layout_compiler/`: the KiCad importer, transient (ADR 0011): it reads the drawing, writes `given` and `relations` and calls `tools/layout_model/derive.py` for `derived` (`seams.py` the relation table of ADR 0009; `trackplan.py` the appliances and track rows as drawn; `geometry.py` the placements, runs and glyphs of ADR 0010; `emit.py` the Layout Data Model File). CLI `tools/compile_layout.py PROJECT.kicad_sch -o OUT` (geometry always, ADR 0011 §7); schema in `schemas/layout-model/`. Only KiCad reading and diagnostics about the drawing as drawn stay here.
- `tools/layout_model/`: the Layout Data Model File's reader and canonical writer, and the reference derivation `derive.py`: a pure function from a file's `given` and `relations` to every `derived` map plus diagnostics, needing nothing but the file (circuits from the stated track adjacency, control points, links, indications, consumers, NextCP pairing, references, columns, devices); `derive.strip` removes every `derived`. Its codes and levels are in `schemas/layout-model/rules/diagnostics.json`; `reference.py` is the placeholder reference data (ADR 0012 §6), `report.py` the diagnostics every writer shares. Every entity and row holds `given`, `relations` and `derived`; readers take meaning from `derived`, then `relations`, then `given` (ADR 0011). Terms: FieldUnit `docs/GLOSSARY.md` §2.6.
- `tools/plant_graph/`: the proof-of-concept plant compiler (`compiler.py`), routes, indications, portable model, FieldUnit projection, layout and picture.
- `tools/controller_graph/`: the proof-of-concept controller compiler (columns are CPs, appliances, drive bits from IODRIVER pins, codelines with stub/empty-sheet handling, §7 diagnostics).
- `tools/link/`: subdivision linker (pairing by normalized name, placeholder stations, §7a cross-checks, codeline instances, source hashes, JSON model).
- `tools/parse_kicad_plant.py`, `tools/parse_kicad_controller.py`, `tools/link_subdivision.py`, `tools/render_plant_picture.py`: CLI front ends.
- `tests/fixtures/kicad/`: frozen goldens (`South-cTc.net`, `Luchessa.plant-model.json`) and the hand-written `minimal_controller.net` that negative tests mutate.
- `schemas/interlocking-plant/v1.json`: portable model schema.
- `profiles/spcoast_south/cps/`: station JSON. `CP_*.json` are legacy harvests; `generated/` holds KiCad-derived interlockings (only `Luchessa` so far). The plant host prefers `generated/<name>.json` over the legacy file.
- `runtime/plant_host/`: the only runtime code. `graph/`, `traffic/` and `web/*` are empty placeholders.
- `docs/archive/vocabulary-review.md` and FieldUnit `docs/GLOSSARY.md` (`~/Dropbox/Arduino/libraries/FieldUnit/docs/GLOSSARY.md`): the sources of truth for vocabulary. Use their terms in prose; code names keep their spelling.
- `docs/review/`: design notes and handoffs. `ctc-panel-hardware-binding.md` covers desk wiring.

## KiCad conventions the proof-of-concept compilers rely on

These are the rules of `tools/plant_graph` and `tools/controller_graph`, not of the KiCad importer, which follows
ADR 0009 (`Name` is the identity; `Value` is never read). This section is rewritten against ADR 0009 to 0011 with the
ADR 0003 discussion.

**Plant schematics (Railroad lib).** The plant compiler maps parts through `_PART_KIND` in
`tools/plant_graph/compiler.py`; any other part raises `unknown_symbol`.

- The Value is the railroad name for every named part (switch `783`, mast `784EAB`, circuit `1NA`). References (`SW1`, `S7`) are KiCad annotation artifacts. Use them only as netlist identities, never to derive or check names.
- Switch, lock and derail Values are unique in an interlocking. Gang id = Value minus its trailing letter (A–Z); switches and locks with one gang id are one gang (`815`, `815A`). A derail whose gang id matches a gang is dependent on it, by convention `<id>D` (e.g. `795D`); the letter D is not the mechanism (ADR 0003 D8, proposed). A dependent derail takes the same position as its switch. Derail NORMAL is derailing; REVERSE is clear. The derail symbol's through pin is `R` (pin 2).
- Mast Value matches `^\d+[NSEW][A-E]+$` in the plant compiler today, e.g. `784EAB`; ADR 0003 D9 allows any letter A to Z. N/W normalise to LEFT, S/E to RIGHT (ADR 0003 D1).
- Head Value is one letter, A–E. The Track Circuit marker's Value is the authoritative circuit name.
- A switch's OS circuit defaults to `<switch>T1`; a `TC` field overrides it.
- `CP` must equal a MAIN HOUSE Value.
- Direction and policy markers: the symbol's Kind/Role records the rule. It replaces the `Rulebook` field. The plant compiler still requires `Rulebook`. `Direction` where applicable.
- Track nets need labels, except OS legs, dark track and derail nets.
- An interlocking's trackplan is one sheet, and its placements are read for geometry only (ADR 0010 C5). What is
  on the trackplan is decided by Role: `APPLIANCE`, `TRACK`, `POLICY`, plus the house (`STRUCTURE` with Kind
  `CONTROL_POINT`); never by library, symbol name or position on the sheet. A `DEVICE`, an `IODRIVER`, the
  processor and the `Interlocking` declaration on the same sheet are not geometry. A wire is track when it ends
  on a pin of a trackplan symbol; which circuit it is comes from the netlist, never from coordinates.

**Desk schematics (RailroadPanel lib).** Compiled by `tools/controller_graph/` (CLI `parse_kicad_controller.py`) and cross-checked against plants by `tools/link_subdivision.py`.

- `PanelColumn` Value is the desk column number.
- `PanelColumn-MAX7313` Value is the expander's address or index on its bus. Pin N is bit N-1. Take expander, bit and direction from the schematic; never compute them from column numbers.
- Panel appliance Values must match plant names. `PanelLamp` lists its circuits in `IndicationToken` (comma-separated); `PanelAuxiliary` uses `ControlToken`.
- Connections are made by coincident pins and read from the netlist.
- **Use KiCad's netlist and ERC as ground truth. Never infer connectivity from coordinates.**

## Station cutover checklist (legacy → KiCad-derived)

Superseded by the unification (2026-10-07); kept for the archived per-project flow.

1. Draw the interlocking in `~/Dropbox/KiCad/Railroad/Archive/SPCoast/<Interlocking>/`, add a two-line `Makefile` (`KIND := plant` / `include ../kicad.mk`), and run `make all`.
2. Run `parse_kicad_plant.py --format fieldunit-json --plant-name <Interlocking> --plant-id spcoast.<Interlocking>` into `profiles/spcoast_south/cps/generated/<Interlocking>.json`, then split `projectionDeferred` into a sidecar (see `generated/README.md`).
3. Update `loadStations()` and the self-test in `spcoast_virtual_plant.cpp`.
4. Update the desk names in FieldUnit `examples/spcoast_ctc` (`configureDesk()`) and in `tools/test_ctc_desk.py`.
5. Verify with unittest, the smoke script, `--test`, and an `arduino-cli compile` of the sketch.
6. Update FieldUnit docs that quote the station. Corporal: primer Act V and Tutorial 2 quote the legacy `CP_Corporal.ino`.

Tests and the smoke script hard-code Luchessa facts. When a change to them is intended, make it in a separate step.

## Direction (in progress)

Target: a Makefile plus tool that takes the desk and plant `.kicad_sch` files and
generates a complete desk sketch, compiles it with arduino-cli and uploads it.
FieldUnit `examples/spcoast_ctc` is a working placeholder and a possible
template, not a constraint. The output form (runtime JSON, generated header, or
full sketch) is still open. Propose options; do not pick one on your own.

What lasts is the Layout Data Model File: its schema, the writer and reader policies, and the derivation rules
with their conformance suite and reference derivation (ADR 0011). The KiCad importer is one writer of it and Studio
will be another. Until Studio exists, the KiCad project is the one source and the flow from it is one way. Code goes
with the data model if Studio would need it, with the importer if only reading KiCad needs it.

## Working agreements (owner, 2026-10-01 to 03)

- **Order of authority.** (1) The relay model of the interlocking logic and AAR practice: the design
  principle (`FieldUnit/docs/GLOSSARY.md` section 10.6). (2) FieldUnit `src/`: where it differs from
  (1), the code has a defect. (3) KiCad-derived interlocking models. (4) Legacy sketches and
  XML-harvested profiles: evidence only, never a reference. Never rewrite a principle to match weaker
  code; file the difference as a code defect.
- **Vocabulary.** `FieldUnit/docs/GLOSSARY.md` is the source of truth. Use its terms exactly. Its
  section 11 lists retired terms. Decisions live in `docs/adr/`; `docs/adr/README.md` is the index.
- **Facts, not symbols.** A rule that reads "is there a symbol on this sheet" is a placeholder for a
  fact that lives elsewhere. Find the fact (ADR 0001 D15).
- **Proposals are ADRs.** Anything that needs the owner's decision goes in `docs/adr/` as a proposed
  ADR that opens with the decisions requested, one line each, with a default. Keep records and
  spikes out of `docs/review/`; they go to `docs/archive/` when superseded.
- **Baseline before editing.** The owner's design drafts are in scope and collaborative. Commit the
  current version before changing one, so the change is an auditable diff.
- **Watsonville.** Its schematic was incomplete until 2026-10-02. Re-check before citing a count or a
  rule derived from it.
- **Briefing agents.** State the order of authority. Do not say "document what the code does" for
  interlocking logic. Do not name a legacy sketch as the reference. Exclude evidence the owner has
  ruled out. Ask for one consolidated list of pending decisions back, not a narrative.
- **Goldens.** A frozen golden encodes facts that go stale (the desk fixture, title blocks, the
  `0x25` lookup). Prefer behavioural gates; when a golden must change, change it in its own commit.

## Design rules

- Abstraction and DRY violations in existing code are debt, not precedent. Do not copy them into new code or treat them as conventions. Examples today:
  - hand-copied names across repos
  - `base + (col-1)` addressing and fixed bit constants in `spcoast_ctc`
  - per-station maintainer-call special cases in the plant host's `setupCodec()`
- Each fact has one source. When a fact exists both in a schematic and in code, generate or validate the code from the schematic.

## Conventions

- Conventional Commits with scopes, e.g. `feat(plant-graph)`, `feat(kicad)`, `fix(plant_host)`, `docs:`. Bodies include a "Verified:" section. Use feature branches and PRs.
- Naming:
  - AAR tokens: `783NWS`, `784SGK`, `1SA`.
  - Interlocking: `Luchessa` (no `CP`); this is the plant name and the MQTT station key.
  - The three `CP <name>` houses: `CP Luchessa`, `CP Gilroy`, `CP Carnadero` (MAIN HOUSE Values; one desk column each). Each is a control point: a `MAIN HOUSE` symbol declares it and its bungalow. On a 506-style code line each is one field station with the same name. The interlocking `Luchessa` contains all three.
  - Plant id: `spcoast.<Interlocking>`.
  - Names are case-preserved when produced and compared case-insensitively when consumed. Only case is folded, so `Luchessa` and `CP Luchessa` stay distinct.
  - Legacy stations still named `CP_<X>` are renamed when each is cut over, after checking whether it is an interlocking or a single CP.
- `secrets.h` is gitignored everywhere. Never commit credentials.
- **Before editing any `.kicad_sch`/`.kicad_pro`**, check for `~*.lck` or a running KiCad; the user often has it open. Prefer reading the drawing through a netlist, under the netlist rule in Commands.
