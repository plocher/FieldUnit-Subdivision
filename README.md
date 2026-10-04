# FieldUnit-Subdivision

Operating-session runtime and virtual railroad simulator for the
[FieldUnit](https://github.com/plocher/FieldUnit) ecosystem.

`FieldUnit-Subdivision` connects multiple FieldUnit interlocking plants into one
operating territory. It combines live track-circuit state, train progression,
optional NPC traffic, crew interfaces, and an overhead model board. The physical
dispatcher CTC machine remains the supervisory control source.

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
FieldUnit interlocking model projection
  tools/plant_graph/fieldunit_projection.py
        |
        +--> FieldUnit interlocking logic, `InterlockingPlant` (vital safety)
        |
        v
Subdivision runtime consumers
  plant_host / graph / traffic / web model board
```

| Layer | Owns | Does not own |
| --- | --- | --- |
| **KiCad + Railroad library** | Human interlocking plant design, topology drawing, title-block metadata | Runtime state, MQTT, desk wiring |
| **Plant graph compiler** | Source parse, diagnostics, route harvest, board picture inputs | FieldUnit execution payload |
| **Portable model** | Editor-neutral interlocking model and static route equations | KiCad refs, runtime occupancy, desk columns |
| **FieldUnit projection** | Map into the FieldUnit interlocking model JSON (switches, derails, OS, routes) plus deferred facts | Reinterpretation of routes at runtime |
| **Subdivision runtime** | Hosting plants, train progression, board/crew views | Vital safety rules (those stay in FieldUnit) |

Design detail lives in:

- `docs/design/portable-interlocking-plant-model.md`
- `docs/archive/legacy-xml-kicad-bootstrap.md`
- `docs/archive/ctc-subdivision-design-layer.md` (when present)

## Domain boundaries

- **Interlocking plant**: Field safety entity. Track junction, appliances, routes,
  and vital rules. Independent of the bungalow that holds the equipment.
- **Control point**: The place where signals are controlled.
- **Field station**: Addressable unit on the code line. Capacity follows the code
  line type (US&S 506 time code, GRS, NX, or electronic transports).
- **Panel Column**: Physical modular slice of the office console. On the SPCoast
  CTC machine (US&S style), one column is one code line address (US&S 506 time
  code: 16 steps; 7 controls and 7 indications per field station).
- **Naming**: an interlocking (`Luchessa`) and the `CP Luchessa` house (a MAIN
  HOUSE Value) may share a base name. Interlockings never carry the `CP`
  prefix; the three `CP <name>` houses (`CP Luchessa`, `CP Gilroy`,
  `CP Carnadero`) always do. Names are case-preserved when produced
  and compared case-insensitively when consumed. The MQTT code line is keyed by
  interlocking; its messages carry the tokens of all three `CP <name>` houses.

The runtime must remain a user of FieldUnit. It must not copy vital logic from
FieldUnit's interlocking logic (`InterlockingPlant`).

## KiCad symbol details

Attributes used:
- CONTROLLED_POINT: Value creates a CP entity. Other symbols point at it by name through their CP field.
- APPLIANCE: Value is a railroad name; the compiler creates an entity under a CP; that entity is in the CP's control/indication vocabulary, so desk levers and lamps match it by name and the codec cross-checks it; and a hardware-sheet proxy can name it to bind field I/O. Pins are track connectivity or attachment.
- COMPONENT: Value names a part of the appliance it is attached to, folded into that parent. It is never matched by name from outside. Its I/O binds through the parent's proxy.
- TRACK: no railroad name of its own. Pins are edges of the track graph; the compiler builds topology from them, and terminals carry a designation.
- POLICY: changes how derived facts are computed. Value is a label; fields carry parameters; a pin locates it on the track.
- ANNOTATION: documentation only, no effect on derivation.


## Developer workflow: interlocking plant artifacts

Default gold fixture is the Luchessa interlocking (the three `CP <name>` houses:
`CP Luchessa`, `CP Gilroy`, `CP Carnadero`). Override paths with env vars when needed:

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
  --plant-name Luchessa \
  --plant-id spcoast.Luchessa \
  --output /tmp/luchessa.plant.json
```

Plant identity comes from `--plant-name` / `--plant-id`. The compiler does not
infer identity from Main House board sections.

### 5. FieldUnit interlocking model JSON

```zsh
python3 tools/parse_kicad_plant.py \
  --library "$KICAD_RAILROAD_LIB" \
  --schematic "$KICAD_LUCHESSA_SCH" \
  --format fieldunit-json \
  --plant-name Luchessa \
  --plant-id spcoast.Luchessa \
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

`tools/validate_plants.cpp` loads interlocking model JSON through FieldUnit
`PlantSerializer`. Use it after you generate FieldUnit JSON and have a local
FieldUnit build available.

## Subdivision runtime layout

- **`runtime/plant_host/`**: Headless native C++ host (a field
  processor running seven field units). Runs FieldUnit's interlocking logic
  (`InterlockingPlant`) and bridges it to MQTT.
- **`runtime/graph/`**: Topology and block-progression primitives. These map
  train position into track-circuit shunts.
- **`runtime/traffic/`**: Train entities and optional NPC crew behavior.
- **`runtime/web/`**: FastAPI/WebSocket server for the 2D SVG model board and
  mobile crew cabs.
- **`profiles/`**: Layout-specific interlocking model JSON, topology links, roles, timetables.
- **`tools/`**: Harvest helpers, KiCad compiler, validators, picture renderers.
- **`schemas/`**: Versioned portable interlocking model contracts.

## Aspiration

Target: a playable, operationally credible model railroad subdivision.

- A physical or virtual CTC machine dispatches territory through the code line
  interface.
- Native virtual field units apply FieldUnit's interlocking logic and
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
  field units and talks to the physical SPCoast desk, a CTC machine (US&S
  style), over MQTT.
- Controls use `ctc/SPCoast/codeline/<station>/controls`.
- Verified indications use the matching `/indications` topic.
- The host models switch lock-dog withdrawal, point travel, and correspondence.
- Retained MQTT indications provide normal startup field truth.
  `--reset` / `--normative` is an explicit simulation reset only.

The physical desk owns office procedure (code line timing, display pulses, future
sound). The virtual field host must not simulate office-originated code line
delays.

### Completed: Luchessa desk cutover

- Hand-authored KiCad gold plant: Luchessa.
- Compiler emits portable model v1 and FieldUnit projection (native derails/OS).
- Generated Luchessa JSON (`profiles/spcoast_south/cps/generated/Luchessa.json`)
  loads in FieldUnit `PlantSerializer` / `InterlockingPlant` and drives both the
  virtual plant host and the physical desk sketch's `configureDesk()` field
  numbers (`783`/`795`/`799`/`784`) unchanged from the recovered, hardware-verified
  baseline (I2C driver, `OneShot`, OLED, code line stepping).
- Six-scenario `spcoast_virtual_plant --test` self-test passes against the
  Luchessa KiCad plant (route alignment, signal authority, knockdown).
- Six of the seven stations (all but Luchessa) remain on legacy XML-harvested
  profiles until each is cut over in turn. Next: Christopher, then Corporal.
- Legacy XML bootstrap stays later work. See
  `docs/archive/legacy-xml-kicad-bootstrap.md`.

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
profile code line definitions must conform to its fixed hardware allocation.

The runtime and Studio must report mismatches. They must not silently rewrite a
plant definition to fit a desk.

## Profiles

- **`spcoast_south`**: Southern Pacific Coast Line from Gilroy Caltrain (MP 77)
  through Watsonville staging (MP 97), controlled by the 14-column SPCoast CTC
  machine (US&S style), `spcoast_ctc`.

## Related work

- [Visual HTML/SVG Plant Documentation Packet Generator](https://github.com/plocher/FieldUnit-Subdivision/issues/1):
  offline visual plant/control-table docs for human review of profile JSON
  before Part C topology automation.
