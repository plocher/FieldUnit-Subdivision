# FieldUnit-Subdivision Part C: KiCad editor to Plant Data Model transition
## Purpose of the next session
Restate and continue Part C after the KiCad schematic-as-plant-editor pivot. The immediate task is to define the tool-neutral intermediate Plant Data Model/Plant Graph contract between a current KiCad authoring adapter and all downstream FieldUnit, cTc, field, documentation, display, simulation, and future-editor adapters.
## Read first
- Original Part C roadmap and source-model reset: Warp plan `eb965064-b08a-428c-a90b-659f1932db5a`.
- KiCad plant-graph spike report: PR #3, `https://github.com/plocher/FieldUnit-Subdivision/pull/3`.
- Spike design lock: PR #3 `docs/review/ctc-subdivision-design-layer.md`.
- Spike handoff: PR #3 `docs/review/SPIKE_HANDOFF_kicad-plant-graph.md`.
- FieldUnit normative companion: `~/Dropbox/Arduino/libraries/FieldUnit/docs/CTC_SUBDIVISION_AND_PLANT_DESIGN.md`.
- FieldUnit signaling/vital primer: `~/Dropbox/Arduino/libraries/FieldUnit/docs/AAR_SIGNALING_PRIMER.md`.
- Current local domain glossary: `CONTEXT.md`.
## Original A/B/C position
### Part A: plant reconstruction
Status: proof of concept complete.
- Seven SPCoast South reconstructed profile JSON candidates exist under `profiles/spcoast_south/cps/`.
- The candidates deserialize through FieldUnit but are not final plant truth.
- Historical ArduinoPoint XML/sketches and Graffle/PDF documents are informational evidence, not authority over FieldUnit vital/AAR behavior.
### Part B: virtual plants and physical desk
Status: working checkpoint complete.
- Native virtual plants and the physical SPCoast Model 503 cTc desk exchange MQTT controls/indications.
- FieldUnit remains the execution authority for vital locking, signals, and indications.
- This checkpoint must remain usable while the authoring model changes.
### Part C: operating overlay
The original intended progression remains valid but now has an explicit prerequisite:
1. Build verified static plant topology and route equations.
2. Bind verified plants into a dispatcher territory and deterministic train progression.
3. Render the live overhead model board from runtime state.
4. Add NPC traffic and later crew interaction.
The KiCad POC completes the first credible piece of Step 1 for Luchessa.
## Reframed architecture
```text
Current editor: KiCad schematic + shared Railroad symbol library
          │
          │ KiCad authoring adapter (others possible in TBD future)
          ▼
Tool-neutral Plant Data Model
  └── Plant Graph core, static route equations, policy, optional realizations
          │
          ├── FieldUnit vital-payload adapter
          ├── cTc machine/layout adapter
          ├── field-device/I/O adapter
          ├── documentation/model-board renderer
          ├── territory/topology adapter
          ├── live runtime evaluation adapter
          └── future Studio or other editor adapter
```
KiCad is the current editable source of plant design. The Plant Data Model is a semantic contract and representation, constructed on demand. It is intended to be a derived source of truth suitable for data interchange. While it is not intended to be human editable, it may be stored as a cached, read-only structured document that reflects an external source of truth.
If KiCad is replaced later, only the editor adapter changes. A replacement editor must produce the same Plant Data Model contract; existing consumers will continue to use this Plant Data Model and will not need to parse editor-specific files.
## Plant Data Model contract to define next
Keep the model normalized and tool-neutral, with all relationships made explicitly.  Don't expose editor-implementation details in the model.
### Structural Plant Graph
- Named Track Nets from the authoring source.
- Unnamed IRJ/Signal IRJ graph nodes identified by connected track nets and technical source locator only.
- Switch and Lock nodes with C/N/R conditional edges.
- Derived Switch OS Track Circuit `<SwitchName>T1` spanning C/N/R nets.
- Signal faces: directional Masts/Head sets attached to Signal IRJs.
- DoT/CP-limit terminals, bumpers, and next-face termini.
### Static plant policy and route equations
- Structural Signal Routes derived from the graph, never manually maintained route records.
- Per route: derived path, Switch alignments that define that route, OS and Track Circuits in that route, the signal, mast, heads and direction that protect that route, where the route ends, and (a place for future) "most favorable" indication ceiling.
- DoT/Rulebook policy at plant limits.
- This static enumeration of possible routes is separate from live evaluation of the routes' real time Indication state.
### Realization bindings (not explicitly represented in the current KiCad schematic)
- cTc realization: Controlled Point/Panel Column, `SWITCH` or `LOCK` presentation, lamp and CODE group mapping.
- field realization: appliance-port to field-node/device/I/O mapping.
- human/display realization: model-board geometry and documentation annotations.
Bindings reference Plant Graph entities as a single source of truth - they never restate topology or route behavior.
### Documentation and source annotations
- Human notes, historical artifact references, construction state, mileposts, bridges, crossings, and industry names can attach to named graph entities, rendering elements or the model as a whole.
- Historical input is informational evidence. It does not create a parallel behavior schema.
## KiCad POC semantics already established
- KiCad symbol types from a "Railroad" Symbol library supply railroad device and appliance type structure.
- KiCad Reference prefixes/suffixes are technical editor identifiers. Direct appliance names derive by removing the shared-library Reference prefix. Independently placed Mast/Head functional names use Values.
- Track Net labels are authoritative for track paths.
- `MT`, `MT1`, and `MT2` are operating designations, not Track Circuit names.
- Ordinary IRJ: A/B pins; Signal IRJ: A/B plus SIGNAL.
- IRJs need no user-facing canonical names. Milepost is optional display-spacing metadata, not identity.
- Power Switch and Lock are distinct first-class symbol types with C/N/R topology.
- Switch OS circuit is derived as `<SwitchName>T1`.
- Signal Mast attaches to Signal IRJ through SIGNAL; Heads attach to Mast Head pins.
- Mast Value carries signal/direction/head grammar; facing derives from that grammar, not IRJ A/B or graphical rotation.
- DoT is a CP-limit terminal on a single-plant sheet. It carries operating designation + Rulebook and is a placeholder for next-CP/ABS binding.
- DoT markers should have only one graph connection, with semantic direction of travel (Destination, Source, Bidirectional) explicitly called out in the Plant Data Model.  Any logic based on pin traversal order is flawed.
- Model-board 2-inch/1/2-inch grids are renderer constraints, not KiCad netlist constraints.
## PR #3 result: successful spike
PR #3 reports:
- Generic KiCad library/netlist readers under `tools/kicad_services/`.
- Railroad-specific compiler/routes/types under `tools/plant_graph/`.
- Read-only CLI `tools/parse_kicad_plant.py`.
- Luchessa: 10 structural routes, 8 `cp_limit` ends and 2 `dead_end` ends.
- Match to the historical 10-row table after historical-to-current name mapping.
- Static rows retain alignment, clear list, head, and end information needed by later evaluation.
- Unit tests and a smoke harness passed on the author’s environment.
PR #3 does not yet generate FieldUnit payloads/cTc layout, solve live indications, bind adjacent CPs, or implement ABS.
## Boundary locks
- Do not reintroduce v1 `plant.json` as the editor source by appending more design namespaces.
- Do not make the Plant Data Model a second editable source file.
- Do not derive live indication from static enumeration.
- Do not make DoT/corridor/ABS behavior more CP-local route rows.
- Do not use Graffle/XML/sketch history as direct authority over FieldUnit safety behavior.
- Do not expose internal combinatoric impossible pairs as dispatcher product output.
## Suggested next-session order
1. Review/merge or otherwise adopt PR #3 after running its smoke command with local KiCad paths.
2. Extract the stable public Plant Data Model interface from the current `tools/plant_graph/types.py`; distinguish tool-neutral fields from KiCad parsing details.
3. Define the first consumers of that interface:
   - static route/ceiling policy;
   - cTc Panel Column binding;
   - FieldUnit vital payload projection.
4. Implement the next vertical slice: static indication-ceiling policy on harvested route equations. Keep live solve out of harvest.
5. After Luchessa static policy is accepted, bind `cp_limit` ends to neighboring plants and begin the territory-level topology/trains work.
  - Since additional use case examples are needed to validate the expressiveness of a proposed data model and to exercise the connectivity between plant models, consider exporting the other SPCoast CP info as rough/incomplete KiCad schematics, having the user update them to reflect correct semantic and visual correctness, and ingesting them as additional test articles.

## Open questions for the next session
- Is the proposed schema extensible for future evolution, is it minimalist, human-verifiable and complete?
- A well-designed data model schema for data interchange uses platform-independent structures, clear naming rules, and strict validation to let different software systems share information without errors.
- Which Plant Data Model fields are genuinely editor-neutral and therefore part of the public contract?
- How do cTc Panel Column and field I/O bindings enter the Plant Data Model without making KiCad PCB realization the functional authority?
- What is the exact static indication-ceiling policy/rulebook adapter for the first Luchessa routes?
- Does a second real consumer justify lifting `tools/kicad_services/` into jBOM or a shared KiCad API?
- When a real plant needs it, what is the correct dual-SIGNAL IRJ symbol and corresponding Plant Graph relationship?

## - Core Schema Design Principles:
  - Platform Independence: The schema should act as a neutral blueprint that works across different technologies
  - Consistent Naming: Use simple, uniform names for fields and tables 
  - Standard Data Types: Assign exact types—like text, integers, or timestamps—to every attribute to prevent translation errors during the transfer. 
  - Defined Relationships: Clearly state how separate data pieces connect to each other to preserve the context of the information.  
  - Flexibility and Extensibility: Allow for evolution through extra fields or semi-structured formats so the schema can grow without breaking older integrations.             
  - Strict Validation Rules: Apply constraints to block bad data before it enters another system.                                                             
  - Clear Documentation: Maintain updated guides and use version numbers 

## Working-tree and source locations
- This conversation’s local branch was `feature/part-c-a-ontology` and contains earlier unmerged v1-schema/reconciliation work. Do not assume it is clean or that it is the same branch as PR #3.
- PR #3 branch: `feature/kicad-plant-graph-parser`.
- KiCad sources are outside this repository:
  - `~/Dropbox/KiCad/InterlockingPlant/symbols/Railroad.kicad_sym`
  - `~/Dropbox/KiCad/Railroad/SPCoast/CP_Luchessa/CP_Luchessa.kicad_sch`
Treat current KiCad authoring files as user-owned. Do not edit them unless the user explicitly requests it.
## Suggested skills
- `domain-modeling`: formalize the public Plant Data Model terms and keep source/editor/runtime concepts distinct.
- `codebase-design`: make Plant Data Model a deep, stable module with editor and consumer adapters at clean seams.
- `tdd`: lock Plant Data Model behavior with fixture-based parser/compiler/consumer tests.
- `design-doc-template`: revise the Part C design around the tool-neutral model before implementing dynamic evaluation.
- `implement`: execute approved vertical slices after the interface is agreed.
