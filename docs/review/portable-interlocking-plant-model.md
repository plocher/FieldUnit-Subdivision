# Portable Interlocking Plant Model
## Status
Candidate C.0 contract. This document defines what is portable, static, and editor-neutral. It is not yet a declaration that the first schema version is sufficient for runtime train progression or every FieldUnit execution feature.
## Purpose
An Interlocking Plant is designed in KiCad today, but must be consumed by FieldUnit, cTc realization, documentation, model-board rendering, territory binding, simulation, and a future Studio implementation without each consumer parsing KiCad files.

The portable model is an interchange contract. It is not:
- a replacement KiCad editor format;
- a FieldUnit `PlantSerializer` execution payload;
- a runtime state snapshot;
- a physical desk wiring map;
- an SVG/model-board layout file.
## Contract Layers
### KiCad Source Evidence
The KiCad adapter retains references, library IDs, raw nets, pins, placement, symbol fields, and source diagnostics. These facts support traceability and compiler diagnostics. They do not form public semantic identity.
### InterlockingPlantDefinition
The portable, versioned definition contains:
- plant identity;
- switches, derived OS circuit identities, and naming-derived ganged crossover groups;
- explicit track circuits;
- signal faces, mast/head facts, and direction;
- semantic topology segments and unnamed internal nodes;
- terminals and route-end kinds;
- structural route equations;
- switch alignments, route circuit roles, clear circuits, and static indication ceilings.

The current JSON schema is `schemas/interlocking-plant/v1.json`. The compiler emits it through:

```zsh path=null start=null
python3 tools/parse_kicad_plant.py \
  --library {{railroad_symbol_library}} \
  --schematic {{plant_schematic}} \
  --format plant-model-json \
  --plant-name "CP Luchessa" \
  --plant-id spcoast.luchessa \
  --output {{compiled_model_path}}
```

`--format json` remains a debug projection and is not a public API.
### Crossover Control Groups
Physical switches always remain independent topology appliances. A crossover is
not inferred merely because two switches join parallel tracks. The designer
declares ganging through standard naming:

```text
Independent switches: 783 ─── segment ─── 785
Ganged crossover:     783 ─── segment ─── 783B
```

The compiler derives `783` + `783B` into one `crossover` control group with
ganged commands and all-members correspondence proof. A pair named `783` and
`785` remains independently controlled. An orphan `783B` without `783` is a
semantic validation error.
### Realization Bindings
Separate artifacts reference definition identifiers but must not repeat plant topology or route equations:
- Controlled Point / Panel Column / CODE-group mapping;
- office control-regime profile and MQTT station address;
- field device, GPIO, sensor, and motor mapping;
- model-board physical geometry and lamp-hole realization;
- Studio canvas coordinates and annotations.
### Projections and Diagnostics
Renderer primitives, route-combinatoric proof, aliases, compiler diagnostics, and source provenance are downstream products. They are not required fields in the portable definition.
## Functional Model Overlay
A JSON definition alone is not the complete data model. The system has definition, state, commands, events, and views.
### Runtime Attributes
`PlantRuntimeState` is evaluated by the FieldUnit vital engine and includes:

| Appliance / Aggregate | Runtime attributes |
| --- | --- |
| Track Circuit | occupancy, quality, age, clearance timer |
| Switch | commanded position, reported position, correspondence, detector/route/time/hand locks |
| Signal Authority | commanded and active direction, fleeting, approach time lock |
| Signal Mast | rulebook indication, aspect, head aspects, markers |
| Route | idle/cleared/traversing state and sectional-release state |
| Auxiliary | maintainer call and other non-vital state |

Runtime attributes are not edited in KiCad and do not belong in the static definition export.
### Commands
Commands are constrained by the definition and vital safety rules:

| Command family | Typical producer | Vital authority |
| --- | --- | --- |
| Atomic `ControlTransaction` | cTc desk / dispatcher | FieldUnit verifies and applies or rejects |
| Field observation update | detector, switch contact, smart appliance | Field input driver |
| Simulation occupancy update | train progression runtime | Field input adapter |
| Auxiliary/non-vital control | maintainer, environment controller | FieldUnit applies without vital route authority |
| Lifecycle operation | load, explicit simulation reset, configuration activation | runtime host |

UI gestures, MQTT packets, CodeLine pulse displays, and KiCad edits are adapters into commands. They are not themselves the command vocabulary.
### Events
Event names must describe authoritative state transitions so consumers do not repeat vital evaluation:
- control transaction accepted, rejected, or ignored;
- switch movement started, correspondence lost, correspondence achieved;
- track circuit occupancy or quality changed;
- lock state changed;
- route cleared, knocked down, sectional release advanced, or released;
- signal authority, indication, or aspect changed;
- plant indication vector changed.

The overhead display, diagnostics, model board, cTc console, train simulation, and future crew applications subscribe to state snapshots or these events. They do not derive safety state from topology independently.
## Current V1 Invariants
- Appliance, terminal, switch, track-circuit, and topology endpoint references resolve within one definition.
- Static routes reference existing switches, circuits, and terminals.
- Derived switch OS circuits are distinct from human-authored Track Circuit markers.
- Operating track designations such as `MT`, `MT1`, and `MT2` are not automatically treated as Track Circuit identities.
- Unnamed IRJ and bumper nodes receive opaque compiler-generated IDs; their KiCad references remain source provenance only.
- Plant identity is compiler input (`--plant-name`, `--plant-id`), never inferred from `MAIN HOUSE` board sections.
## Known Gaps
- FieldUnit `PlantSerializer` cannot yet express all definition facts, especially route end kinds, circuit roles, topology segments, and terminal semantics. Projection to FieldUnit is intentionally lossy until that execution schema evolves.
- cTc Panel Column, Controlled Point, and CODE-group bindings are not yet a portable realization artifact.
- Territory links between `cp_limit` terminals are not yet defined.
- Runtime event serialization and state snapshots are not yet formalized.
- Existing model-board layout facts need a separate realization projection rather than inclusion in V1 core.
## Historical Office Systems
US&S and GRS history informs the capacity, role vocabulary, operator procedure, and realization constraints of office profiles. The current system transports controls/indications using modern MQTT and textual AAR tokens. It does not claim bit-perfect electrical emulation of historical coding systems.

NX is an operator route-selection method, not a step-code family. It belongs in office/control-regime realization behavior rather than static Interlocking Plant route equations.
