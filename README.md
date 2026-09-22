# FieldUnit-Subdivision

Operating-session runtime and virtual railroad simulator for the
[FieldUnit](https://github.com/plocher/FieldUnit) ecosystem.

`FieldUnit-Subdivision` connects multiple FieldUnit Interlocking Plants into one
operating territory. It combines live track-circuit state, train progression,
optional NPC traffic, crew interfaces, and an overhead model board. The physical
dispatcher cTc machine remains the supervisory control source.

## Ecosystem map

Plant design and runtime sit in separate layers. Each layer has one job.

```text
KiCad schematic + Railroad symbol library
        |
        v
Plant graph compiler (tools/parse_kicad_plant.py)
        |
        +--> debug inventory (--format text|json)
        |
        v
Portable InterlockingPlantModel
  schemas/interlocking-plant/v1.json
        |
        v
FieldUnit plant JSON projection
  tools/plant_graph/fieldunit_projection.py
        |
        +--> FieldUnit ControlPoint (vital safety)
        |
        v
Subdivision runtime consumers
  plant_host / graph / traffic / web model board
```

| Layer | Owns | Does not own |
| --- | --- | --- |
| **KiCad + Railroad library** | Human plant design, topology drawing, title-block metadata | Runtime state, MQTT, desk wiring |
| **Plant graph compiler** | Source parse, diagnostics, route harvest, board picture inputs | FieldUnit execution payload |
| **Portable model** | Editor-neutral plant definition and static route equations | KiCad refs, runtime occupancy, desk columns |
| **FieldUnit projection** | Map into FieldUnit plant JSON (switches, derails, OS, routes) plus deferred facts | Reinterpretation of routes at runtime |
| **Subdivision runtime** | Hosting plants, train progression, board/crew views | Vital safety rules (those stay in FieldUnit) |

Design detail lives in:

- `docs/review/portable-interlocking-plant-model.md`
- `docs/review/legacy-xml-kicad-bootstrap.md`
- `docs/review/ctc-subdivision-design-layer.md` (when present)

## Domain boundaries

- **Interlocking Plant**: Field safety entity. Track junction, appliances, routes,
  and vital rules. Independent of the shelter that holds the equipment.
- **Controlled Point / Line Station**: Addressable supervisory unit on the
  CodeLine. Capacity follows the coding system (US&S step codes, GRS, NX, or
  electronic transports).
- **Panel Column**: Physical modular slice of the office console. On the SPCoast
  US&S Model 503, one column is one 15-step controlled point.

The runtime must remain a user of FieldUnit. It must not copy vital logic from
`ControlPoint` / the interlocking engine.

## Developer workflow: plant artifacts

Default gold fixture is CP Luchessa. Override paths with env vars when needed:

- `KICAD_RAILROAD_LIB` — Railroad symbol library (`.kicad_sym`)
- `KICAD_LUCHESSA_SCH` — Luchessa schematic (`.kicad_sch`)

### 1. Unit tests

```zsh
python3 -m unittest discover -s tests -q
```

### 2. Full smoke (graph, portable model, FieldUnit, route board)

```zsh
tools/run_plant_graph_smoke.sh
```

If the library or schematic path is missing, the script runs unit tests and
skips Luchessa integration.

### 3. Plant graph inventory (debug)

```zsh
python3 tools/parse_kicad_plant.py \
  --library "$KICAD_RAILROAD_LIB" \
  --schematic "$KICAD_LUCHESSA_SCH" \
  --format text
```

`--format json` is a debug projection. It is not a public API.

### 4. Portable InterlockingPlantModel

```zsh
python3 tools/parse_kicad_plant.py \
  --library "$KICAD_RAILROAD_LIB" \
  --schematic "$KICAD_LUCHESSA_SCH" \
  --format plant-model-json \
  --plant-name "CP Luchessa" \
  --plant-id spcoast.luchessa \
  --output /tmp/luchessa.plant.json
```

Plant identity comes from `--plant-name` / `--plant-id`. The compiler does not
infer identity from Main House board sections.

### 5. FieldUnit plant JSON

```zsh
python3 tools/parse_kicad_plant.py \
  --library "$KICAD_RAILROAD_LIB" \
  --schematic "$KICAD_LUCHESSA_SCH" \
  --format fieldunit-json \
  --plant-name "CP Luchessa" \
  --plant-id spcoast.luchessa \
  --output /tmp/luchessa.fieldunit.json
```

Native FieldUnit facts include switches with optional `os`, `derails[]`
(dependent `*D` after the base switch), and route aligns that name the master
only for dependent derails. Remaining portable facts (CP allocation, topology,
terminals) stay under `projectionDeferred`. Unsupported indications fail the
projection instead of silent degradation to `STOP`.

### 6. Model board SVG

```zsh
python3 tools/render_plant_picture.py \
  --library "$KICAD_RAILROAD_LIB" \
  --schematic "$KICAD_LUCHESSA_SCH" \
  --format route-board-svg \
  --output /tmp/luchessa.board.svg
```

### 7. Validate FieldUnit JSON (optional C++ check)

`tools/validate_plants.cpp` loads plant JSON through FieldUnit
`PlantSerializer`. Use it after you generate FieldUnit JSON and have a local
FieldUnit build available.

## Subdivision runtime layout

- **`runtime/plant_host/`**: Headless native C++ host. Runs FieldUnit
  `ControlPoint` logic and bridges it to MQTT.
- **`runtime/graph/`**: Topology and block-progression primitives. These map
  train position into track-circuit shunts.
- **`runtime/traffic/`**: Train entities and optional NPC crew behavior.
- **`runtime/web/`**: FastAPI/WebSocket server for the 2D SVG model board and
  mobile crew cabs.
- **`profiles/`**: Layout-specific plant JSON, topology links, roles, timetables.
- **`tools/`**: Harvest helpers, KiCad compiler, validators, picture renderers.
- **`schemas/`**: Versioned portable plant contracts.

## Aspiration

Target: a playable, operationally credible model railroad subdivision.

- A physical or virtual cTc machine dispatches territory through the CodeLine
  interface.
- Native virtual Interlocking Plants apply FieldUnit vital safety rules and
  publish verified indications.
- A simulation overlay moves trains through topology and shunts real plant track
  circuits. It does not reproduce vital rules.
- An overhead 2D schematic serves crews, dispatchers, diagnostics, and demos.
- NPC traffic supports solo sessions. Human crews can later claim trains through
  mobile cab interfaces.

Near-term display target is SVG/HTML, not a 3D world.

## Current checkpoint

### Completed: Part A — Plant reconstruction

- `tools/harvest_spcoast_cps.py` converts legacy SPCoast XML/wiki material into
  profile JSON candidates.
- `tools/validate_plants.cpp` loads generated schemas through FieldUnit
  `PlantSerializer`.
- Seven SPCoast South plant profiles exist under `profiles/spcoast_south/cps/`.

These schemas are valid FieldUnit inputs but remain reconstructed candidates.
Review route and topology assumptions before automated train movement uses them.

### Completed: Part B — Virtual plant / physical desk

- `runtime/plant_host/spcoast_virtual_plant.cpp` hosts seven native virtual
  plants and talks to the physical SPCoast Model 503 desk over MQTT.
- Controls use `ctc/SPCoast/codeline/<station>/controls`.
- Verified indications use the matching `/indications` topic.
- The host models switch lock-dog withdrawal, point travel, and correspondence.
- Retained MQTT indications provide normal startup field truth.
  `--reset` / `--normative` is an explicit simulation reset only.

The physical desk owns office procedure (CodeLine timing, display pulses, future
sound). The virtual field host must not simulate office-originated CodeLine
delays.

### In progress: portable design source path

- Hand-authored KiCad gold plant: Luchessa.
- Compiler emits portable model v1 and FieldUnit projection (native derails/OS).
- Generated Luchessa JSON loads in FieldUnit `PlantSerializer` / `ControlPoint`.
- Desk cutover is next: host profile + `configureDesk()` field numbers (`783` /
  `784`), not a new faceplate image.
- After Luchessa desk acceptance: Christopher, then Corporal.
- Legacy XML bootstrap stays later work. See
  `docs/review/legacy-xml-kicad-bootstrap.md`.

### Part C: Virtual operating session overlay

#### C.1 — Topology and train progression

Define a profile-level topology contract for plant boundaries, corridor
segments, blocks, route-dependent paths, and industry branches. Start with a
two-plant vertical slice. Extend the Gilroy-to-Watsonville corridor only after
that slice is repeatable.

#### C.2 — Overhead 2D model board

Render runtime state in a browser SVG/HTML schematic. The display observes
runtime state. It does not replace FieldUnit safety state.

#### C.3 — Crews and NPC traffic

Add a simple autonomous through passenger train as an end-to-end scenario.
Later add mobile crew ownership and work such as the Corporal Beet Turn with
Engine Return Stick (`ERS`) behavior.

## Source-of-truth lifecycle

During Studio design, a serialized design artifact can be the fluid source of
truth. After physical panel columns, wiring, faceplates, and model-board
graphics exist, that constructed desk becomes a lifecycle interlock. Compatible
profile CodeLine definitions must conform to its fixed hardware allocation.

The runtime and Studio must report mismatches. They must not silently rewrite a
plant definition to fit a desk.

## Profiles

- **`spcoast_south`**: Southern Pacific Coast Line from Gilroy Caltrain (MP 77)
  through Watsonville staging (MP 97), controlled by the 14-column US&S Model 503
  `spcoast_ctc` machine.

## Related work

- [Visual HTML/SVG Plant Documentation Packet Generator](https://github.com/plocher/FieldUnit-Subdivision/issues/1):
  offline visual plant/control-table docs for human review of profile JSON
  before Part C topology automation.
