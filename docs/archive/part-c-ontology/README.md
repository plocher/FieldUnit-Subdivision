# Part C ontology checkpoint (2026-09-16) and the desk-cutover plan note (2026-09-24)

Records, not guidance. Salvaged from two branches that were never merged, `feature/part-c-a-ontology`
(one checkpoint commit, no PR) and `feature/luchessa-desk-cutover` (PR #9, closed as superseded by
FieldUnit PR #15 and Subdivision PR #11). Both branches are preserved as tags `archive/feature/part-c-a-ontology`
and `archive/feature/luchessa-desk-cutover`; the rest of their content (schemas of the old `CP_*.json`
shape, legacy profile edits, the forked desk sketch) stays in the tags only.

## Read with the vocabulary of the time

These files predate the 2026-10-01..03 vocabulary review. They use terms the glossary has since retired:
Controlled Point and Line Station (now control point and field station), cTc Machine (CTC machine),
Interlocking Plant for the logic (interlocking logic), Model Detection Block (track circuit or logical
detection block), aspect ceiling (indication ceiling). `CP_*.json` as "the complete source document" is
superseded: the KiCad drawings are the source and the compiler emits the model.

## What carried forward, and where

| Idea in these files | Where it lives now |
|---|---|
| Five authority domains: plant source, runtime vital model, operating topology, track diagram, operations | the first two are the compiler → model → FieldUnit chain; **operating topology and operations have no home on `main` yet** (the Subdivision runtime's train-progression work) |
| Source → vital payload is lossy and one-way; the runtime never writes the source | practice since the portable model; not yet stated in a design document |
| `InterlockingPlant`, `ControlledPoint`, `PanelColumn` are distinct entities | ADR 0001 (control point, field station, column) |
| A physical desk allocation validates against the code line definition; neither is rewritten silently | the linker's §7a cross-checks; ADR 0001 D3 |
| A `physical` namespace for field-node and I/O facts beside the vital model | FieldUnit ADR 0003: the generator's separate hardware-binding output |
| Evidence ledger with dispositions `accepted / provisional / rejected / incomplete` | done by hand as "(unverified)" marks in ADR 0003 (names) and the glossary; FieldUnit #26 is the open verification list |
| A tool-neutral track-diagram document, Studio as a later importer (the branch's ADR 0001, numbered before the current 0001 existed) | the same stance taken on 2026-10-05: panel tooling and the KiCad replacement are deferred to Studio (#13) |
| `TrainRoute` distinct from `SignalRoute`; `TransitSegment`, `PrototypeRedaction` | not yet used; candidates for the runtime vocabulary |

## The documentation packet generator

`generate_plant_docs.py` and its tests render an offline HTML packet for one plant (diagram, route table,
detector locks, panel columns) and a reconciliation view against the historical XML. It reads the old
`CP_*.json` shape and will not run against today's portable model without rework. It is kept because the
requirement it served is still open: **generate a documentation set (print, web, review) from the data
model**. See `docs/design/goals.md` and issue #31.

## Files

| File | Origin |
|---|---|
| `PART_C_ONTOLOGY.md` | `docs/ontology/PART_C_ONTOLOGY.md` on the ontology branch |
| `PART_C_REFERENCE_MODELS.md` | `docs/research/` on the ontology branch: JMRI PanelPro, OperationsPro, CATS as vocabulary references |
| `CONTEXT-glossary.md` | the branch's `CONTEXT.md` glossary (retired terms) |
| `adr-track-diagram-pathfinder-contract.md` | the branch's ADR, renumbered out of the sequence |
| `generate_plant_docs.py`, `test_generate_plant_docs.py` | the packet generator and its tests, as checkpointed |
| `DraftPlans-2026-09-24.md` | the desk-cutover branch's reset note: the long-, medium- and short-term goals as first written |
