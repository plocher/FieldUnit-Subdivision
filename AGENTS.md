# AGENTS.md

Guidance for agentic coders working in FieldUnit-Subdivision. Read `README.md`
first; this file adds what an agent needs that the README does not say.

## What this repo owns

FieldUnit-Subdivision is the operating-territory layer (SPCoast South: 7
controlled points, one 14-column US&S cTc desk). It owns:

- **KiCad → data tooling**: reading plant and desk schematics and emitting the
  portable model, FieldUnit plant JSON, board pictures, and (planned) desk
  firmware.
- **Subdivision runtime**: virtual plants, train progression, board and crew views.

It does **not** own vital logic. Plants run FieldUnit's `InterlockingPlant`;
never copy or reimplement interlocking rules here.

## Related repos and sources of truth

| Path | Role | Truth it owns |
| --- | --- | --- |
| `~/Dropbox/KiCad/Railroad/SPCoast/<Project>/` | KiCad projects (git) | Plant topology and desk wiring as drawn |
| `~/Dropbox/KiCad/InterlockingPlant/symbols/` | `Railroad.kicad_sym` (plant), `RailroadPanel.kicad_sym` (desk) | Symbol and field contracts. **Not in git.** Parked outside this repo while they evolve; expected to move into this repo. |
| `~/Dropbox/Arduino/libraries/FieldUnit` | Header-only C++17 library (git) | Vital engine, codecs, `PlantSerializer`, `cTcMachine`, and the `examples/spcoast_ctc` desk sketch |
| this repo | Tooling and runtime | Everything derived from the above |

The symbol libraries are registered globally in
`~/Library/Preferences/kicad/10.0/sym-lib-table` by absolute path. KiCad 10 is required.

## Commands

```zsh
python3 -m unittest discover -s tests -q      # 110 tests, Python 3.14
tools/run_plant_graph_smoke.sh               # Luchessa end-to-end; needs kicad-cli
```

- `kicad-cli` is not on PATH. Tools find it through `KICAD_CLI` or the app bundle
  (`/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`). Without KiCad, pass `--netlist <file.net>`.
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
- KiCad project outputs (netlist, plant JSON, SVG) are rebuilt with `make` in each
  `~/Dropbox/KiCad/Railroad/SPCoast/<Project>/`. The shared rules live in
  `SPCoast/kicad.mk` while they are experimental and are expected to move into
  this repo's `tools/`.
- Set `PYTHONDONTWRITEBYTECODE=1` or clean up `__pycache__`. Stale caches reference removed modules.

## Layout

- `tools/kicad_services/`: generic KiCad readers (netlist, schematic placement, symbol library pin contracts). Reuse these; do not write new s-expression parsers.
- `tools/plant_graph/`: plant compiler (`compiler.py`), routes, indications, portable model, FieldUnit projection, layout and picture.
- `tools/controller_graph/`: controller compiler (columns are CPs, appliances, drive bits from IODRIVER pins, codelines with stub/empty-sheet handling, §7 diagnostics).
- `tools/link/`: subdivision linker (pairing by normalized name, placeholder stations, §7a cross-checks, codeline instances, source hashes, JSON model).
- `tools/parse_kicad_plant.py`, `tools/parse_kicad_controller.py`, `tools/link_subdivision.py`, `tools/render_plant_picture.py`: CLI front ends.
- `tests/fixtures/kicad/`: frozen goldens (`South-cTc.net`, `Luchessa.plant-model.json`) and the hand-written `minimal_controller.net` that negative tests mutate.
- `schemas/interlocking-plant/v1.json`: portable model schema.
- `profiles/spcoast_south/cps/`: station JSON. `CP_*.json` are legacy harvests; `generated/` holds KiCad-derived interlockings (only `Luchessa` so far). The plant host prefers `generated/<name>.json` over the legacy file.
- `runtime/plant_host/`: the only runtime code. `graph/`, `traffic/` and `web/*` are empty placeholders.
- `docs/review/`: design notes and handoffs. `ctc-panel-hardware-binding.md` covers desk wiring.

## KiCad conventions the compiler relies on

**Plant schematics (Railroad lib).** The compiler maps parts through `_PART_KIND` in
`tools/plant_graph/compiler.py`; any other part raises `unknown_symbol`.

- The Value is the railroad name for every named part (switch `783`, mast `784EAB`, circuit `1NA`). References (`SW1`, `S7`) are KiCad annotation artifacts. Use them only as netlist identities, never to derive or check names.
- Dependent derail Value is `<switch>D`, e.g. `795D`.
- Mast Value matches `^\d+[NSEW][A-E]+$`, e.g. `784EAB`. N/W normalise to LEFT, S/E to RIGHT.
- Head Value is one letter, A–E. The Track Circuit marker's Value is the authoritative circuit name.
- A switch's OS circuit defaults to `<switch>T1`; a `TC` field overrides it.
- `CP` must equal a MAIN HOUSE Value.
- Direction and policy markers need `Rulebook`, and `Direction` where applicable.
- Track nets need labels, except OS legs, dark track and derail nets.

**Desk schematics (RailroadPanel lib).** Compiled by `tools/controller_graph/` (CLI `parse_kicad_controller.py`) and cross-checked against plants by `tools/link_subdivision.py`.

- `PanelColumn` Value is the desk column number.
- `PanelColumn-MAX7313` Value is the expander's address or index on its bus. Pin N is bit N-1. Take expander, bit and direction from the schematic; never compute them from column numbers.
- Panel appliance Values must match plant names. `PanelLamp` lists its circuits in `IndicationToken` (comma-separated); `PanelAuxiliary` uses `ControlToken`.
- Connections are made by coincident pins and read from the netlist.
- **Use KiCad's netlist and ERC as ground truth. Never infer connectivity from coordinates.**

## Station cutover checklist (legacy → KiCad-derived)

1. Draw the interlocking in `~/Dropbox/KiCad/Railroad/SPCoast/<Interlocking>/`, add a two-line `Makefile` (`KIND := plant` / `include ../kicad.mk`), and run `make all`.
2. Run `parse_kicad_plant.py --format fieldunit-json --plant-name <Interlocking> --plant-id spcoast.<Interlocking>` into `profiles/spcoast_south/cps/generated/<Interlocking>.json`, then split `projectionDeferred` into a sidecar (see `generated/README.md`).
3. Update `loadStations()` and the self-test in `spcoast_virtual_plant.cpp`.
4. Update the desk names in FieldUnit `examples/spcoast_ctc` (`configureDesk()`) and in `tools/test_ctc_desk.py`.
5. Verify with unittest, the smoke script, `--test`, and an `arduino-cli compile` of the sketch.

Tests and the smoke script hard-code Luchessa facts. When a change to them is intended, make it in a separate step.

## Direction (in progress)

Target: a Makefile plus tool that takes the desk and plant `.kicad_sch` files and
generates a complete desk sketch, compiles it with arduino-cli and uploads it.
FieldUnit `examples/spcoast_ctc` is a working placeholder and a possible
template, not a constraint. The output form (runtime JSON, generated header, or
full sketch) is still open. Propose options; do not pick one on your own.

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
  - Controlled point: `CP Luchessa` (MAIN HOUSE Value; one desk column each).
  - Plant id: `spcoast.<Interlocking>`.
  - Names are case-preserved when produced and compared case-insensitively when consumed. Only case is folded, so `Luchessa` and `CP Luchessa` stay distinct.
  - Legacy stations still named `CP_<X>` are renamed when each is cut over, after checking whether it is an interlocking or a single CP.
- `secrets.h` is gitignored everywhere. Never commit credentials.
- **Before editing any `.kicad_sch`/`.kicad_pro`**, check for `~*.lck` or a running KiCad; the user often has it open. Prefer reading the `.net`, and refresh it with `make netlist`, which rebuilds it when the `.kicad_sch` is newer.
