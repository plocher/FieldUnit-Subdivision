# FieldUnit-Subdivision

Operating-session runtime and virtual railroad simulator for the [FieldUnit](https://github.com/plocher/FieldUnit) ecosystem.

`FieldUnit-Subdivision` connects multiple FieldUnit Interlocking Plants into a bounded dispatcher territory. It will combine live track-circuit state, train progression, autonomous traffic, crew interfaces, and an overhead model board while preserving the physical dispatcher cTc machine as the supervisory control source. It does not claim to model the complete geographic subdivision beyond that territory.

## Aspiration

The target is a playable, operationally credible dispatcher territory:
- A physical or virtual cTc Machine dispatches a territory through the CodeLine Interface.
- Native virtual Interlocking Plants apply FieldUnit vital safety rules and publish verified indications.
- A simulation overlay moves trains through the defined topology, shunting real plant track circuits rather than reproducing vital rules.
- An overhead 2D schematic serves crews, dispatchers, diagnostics, and demonstrations.
- NPC traffic supports solo sessions; human crews can later claim trains through mobile cab interfaces.

The near-term target is an SVG/HTML operational overview, not a 3D world. A more elaborate game or Unreal Engine presentation remains a future possibility, not a prerequisite.

## Domain Boundaries

- **Interlocking Plant**: The field safety entity. It models the track junction, appliances, routes, and vital safety rules. It is independent of the physical shelter that contains its equipment.
- **Controlled Point / Line Station**: An addressable supervisory unit on the CodeLine, constrained by the selected coding system (for example US&S 15-, 20-, or 32-step; GRS Type K / Class M; NX; or electronic transports).
- **Panel Column**: A physical modular slice of the office console. On the SPCoast US&S Model 503, one column represents a 15-step controlled point. Multiple columns can share a physical CODE button while belonging to the same Interlocking Plant.

The runtime must remain a user of FieldUnit. It must not duplicate the vital logic implemented by `InterlockingPlant`.

## Architecture

- **`runtime/plant_host/`**: Headless native C++ host that executes FieldUnit `InterlockingPlant` logic for the active profile and bridges it to MQTT.
- **`runtime/graph/`**: Generic topology and block-progression primitives. These translate train position into track-circuit shunts.
- **`runtime/traffic/`**: Train entities and optional NPC crew behavior, including future through-passenger and beet-turn roles.
- **`runtime/web/`**: FastAPI/WebSocket server hosting the 2D SVG overhead model board display and responsive mobile crew cabs.
- **`profiles/`**: Layout-specific configuration profiles containing Interlocking Plant JSON schemas, topology connections, operational roles, and timetables.
- **`tools/`**: Harvesting utilities, validation tests, and documentation generators.
## Current Checkpoint

### Completed: Part A — Plant Reconstruction

- `tools/harvest_spcoast_cps.py` converts legacy SPCoast XML/wiki source material into profile JSON candidates.
- `tools/validate_plants.cpp` loads each generated schema through FieldUnit `PlantSerializer`.
- Seven SPCoast South plant profiles exist under `profiles/spcoast_south/cps/`.

The generated schemas are valid FieldUnit inputs but remain reconstructed candidates. Before automated train movement uses them, route and topology assumptions must be reviewed against the legacy XML, ASCII plans, physical desk layout, and operator knowledge.

### Completed: Part B — Virtual Plant / Physical Desk Integration

- `runtime/plant_host/spcoast_virtual_plant.cpp` hosts seven native virtual Interlocking Plants and communicates with the physical SPCoast Model 503 desk by MQTT.
- Controls use `ctc/SPCoast/codeline/<station>/controls`; verified indications use the matching `/indications` topic.
- The host models switch lock-dog withdrawal, point travel, and correspondence.
- Retained MQTT indications provide normal startup field truth. `--reset` / `--normative` is an explicit simulation reset only; it establishes normal switch alignment, Stop signals, vacant tracks, and inactive maintainer calls.

The physical desk owns office procedure such as CodeLine timing, display pulses, and future sound effects. The virtual field host must not simulate office-originated CodeLine delays.

## Part C: Virtual Operating Session Overlay

### C.1 — Topology and Train Progression

Define a profile-level topology contract for named plant boundaries, corridor segments, blocks, route-dependent paths, and industry/yard branches. Start with a deterministic two-plant vertical slice: a dispatcher clears a route, a simulated train enters and clears its circuits, FieldUnit produces knockdown and locking behavior, and the physical desk receives the resulting indications.

Extend to the full Gilroy-to-Watsonville corridor only after that slice is repeatable.

### C.2 — Overhead 2D Model Board

Render runtime state in a browser-visible SVG/HTML schematic. Display train identity, location, heading, speed, occupancy, switch correspondence, and signal condition. The display observes runtime state; it does not derive or replace FieldUnit safety state.

### C.3 — Crews and NPC Traffic

Add a simple autonomous through passenger train as an end-to-end operating and regression scenario. Later, add mobile crew ownership and more complex work such as the Corporal Beet Turn with Engine Return Stick (`ERS`) behavior.

## Source-of-Truth Lifecycle

During Studio design, a serialized design artifact can be the fluid source of truth. Once physical panel columns, wiring, faceplates, and model-board graphics exist, that constructed desk becomes a lifecycle interlock: compatible profile CodeLine definitions must conform to its fixed hardware allocation.

The runtime and Studio should validate mismatches explicitly. They must not silently rewrite a plant definition to fit a desk or imply that an already constructed desk can be reconfigured as cheaply as virtual layout data.

## Profiles

- **`spcoast_south`**: Southern Pacific Coast Line from Gilroy Caltrain (MP 77) through Watsonville staging (MP 97), controlled by the 14-column US&S Model 503 `spcoast_ctc` machine.

## Related Work

- [Visual HTML/SVG Plant Documentation Packet Generator](https://github.com/plocher/FieldUnit-Subdivision/issues/1): Generate offline visual plant/control-table documentation to support human review of profile JSON before Part C topology automation.
