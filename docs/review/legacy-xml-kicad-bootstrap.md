# Legacy XML to KiCad Bootstrap
## Purpose
Historical ArduinoPoint XML is useful evidence and inventory. It is not authority for interlocking topology, route safety, or FieldUnit execution behavior.

After the portable model contract is accepted, a migration helper may create a sparse import draft from XML. The draft helps a human start a KiCad schematic; it must not claim that its resulting topology is valid.
## Pipeline
```text
legacy XML
  -> LegacyPlantImport draft
  -> KiCad draft projection
  -> human topology and policy completion
  -> KiCad compiler
  -> validated InterlockingPlantDefinition
```
## LegacyPlantImport Draft
The import draft may contain:
- source path and content digest;
- control point name and descriptive text;
- switches, track-circuit names, signals, heads, maintainer calls;
- legacy route/aspect rows as non-authoritative evidence;
- slave/invert annotations;
- unresolved facts and migration diagnostics.

The draft must not claim:
- C/N/R track wiring;
- IRJ inventory or type;
- signal-IRJ or mast-head attachment;
- switch mirror/rotation;
- terminal/CP-limit location;
- route authority, clear circuits, or indication ceiling;
- field I/O or physical desk binding;
- a valid FieldUnit execution payload.
## KiCad Draft Projection
The first migration helper should generate:
- a sandbox project and schematic skeleton;
- Railroad library symbols for appliance inventory;
- named draft placement lanes;
- preserved XML prose/ASCII drawing as notes;
- `BOOTSTRAP_MANIFEST.json`;
- `HUMAN_TODO.md`.

The v1 interface must refuse automatic wire generation (`--connect none` only), stamp the sheet as `BOOTSTRAP DRAFT — NOT PLANT AUTHORITY`, and refuse overwriting a hand-authored gold plant without an explicit override.
## Fixture Order
1. Luchessa remains the hand-authored gold schematic.
2. `CP_Christopher.xml` is the first recommended bootstrap target.
3. `CP_Corporal.xml` follows after Christopher validates the workflow.

The migration helper remains an isolated candidate for future promotion into a jBOM-oriented KiCad services library. It is not part of the core Interlocking Plant compiler.
