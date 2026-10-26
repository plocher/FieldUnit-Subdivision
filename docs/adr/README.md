# Decision records

One list of what is decided and what waits for the owner. Each proposed ADR opens with a
"Decisions requested" section.

## Waiting for a decision

| ADR | Subject | Asked of the owner |
|---|---|---|
| [0011](0011-given-relations-derived.md) | What the Layout Data Model File states: `given`, `relations` and `derived` on every entity and row; the writer and reader policies; one definition of the computation (rules, conformance suite, reference derivation); incomplete is not in error, and saving a file in error is each writer's policy; geometry always. Amends 0008, 0009 §3.12, 0010. | Six decisions, each with a default (proposed 2026-10-26). |
| [0002](0002-symbol-contract.md) | What each KiCad symbol records | Frozen 2026-10-03: too complicated to approve as-is. Rewritten to rules after the cleanup pass (#30), then approved. |
| [0003](0003-name-grammar.md) | One grammar for the names of appliances, signals and track circuits | Frozen 2026-10-03, same reason; the owner's in-progress edits are committed as they stood. Rewritten to rules after #30. |

## Accepted

| ADR | Subject | Date |
|---|---|---|
| [0010](0010-geometry-and-views.md) | Geometry: the drawing as a design fact. Per interlocking a placement for every named thing by name, each drawn run of track as a row with its circuit and switch ports, unnamed track symbols as rows joined by circuit; what is on the trackplan decided by Role; the interlocking's own frame in millimetres with every `at` the glyph's bottom-left pin; the glyphs written once in `layout.glyphs{}` keyed by library and symbol, with KiCad's stroke and fill where not default; polylines as strings under the canonical form; order along the subdivision derived from mileposts and NextCP; the office unit's geometry empty until a desk or board is drawn; the four views (thinline, model board, route finder, documentation packet) as gates. Worked Sargent example and two pictures in `0010/`, generated. Schema 3.1.0 shared with the trackplan semantics piece. | 2026-10-24 |
| [0008](0008-layout-data-model-file.md) | The Layout Data Model File, the public interface milestone D writes and milestone E reads. Problem, three rules (fidelity, the KiCad boundary, reusable), a definition of done (lossless round trip, coverage, schema), the architecture with its alternatives run down, and the schema `schemas/layout-model/v3.0.0.json` with the example compiled from the SPCoast project by the seam reader, never typed. On ADR 0009: transports anchored per processor, encodings on the instance they ride, CMRInet Nodes under their line by UA, processors with drivers by address, bindings as routes, stations derived and absent, the `Railroad` symbol's layout facts, macros expanded by the compiler, `Name` as identity on every keyed symbol and `Value` never read, JMRI drivers keyed by object class and served device, every Mast a row. Pictures in `0008/`. | 2026-10-24 |
| [0009](0009-explicit-seams.md) | Explicit seams: the four net kinds, every symbol's ingested and provided pins, processors as what runs logic and anchors connections, transports as mechanisms and encodings riding them, the CMRInet node as a driver on the line, head devices with fixed styles, derived stations, the one-entity-many-sheets rule, the vocabulary rulings, and the relation table (explicit wire, implicit fallback, check) that is the compiler's test. Amends 0001, 0004, 0005, 0008. | 2026-10-23 |
| [0007](0007-kicad-services-ownership-split.md) | KiCad services ownership: shared development moves to kicad-primitives now, no intermediate service layer here; Subdivision keeps Railroad field ownership rules, mast and head interpretation, dated rulings, the `production/` conventions, urgent consumer workflows and temporary migration adapters. The Caltrain edit runs as a dated script with a gate that proves the expected delta. Records both passes of the kicad-primitives orchestrator's adversarial review, all findings accepted. | 2026-10-19 |
| [0006](0006-kicad-edit-services.md) | KiCad services evidence: what a service is in jBOM's and the package's terms, the inventory of code, process and ten learnings from the SPCoast edits, defects in what we have, donor-side defects found. Input to kicad-primitives tickets #4, #8, #9, #12. | 2026-10-19 |
| [0005](0005-bus-binding-and-containers.md) | How a driver finds its bus: the rules in play, tagged model, representation or operating, and the binding rule derived from them. A bus is declared once and attachments carry only their own address; scopes are wire, sheet, layout, innermost first; a KiCad group is not a scope; nothing reads a driver's Value. Eleven consequences, thirteen recipes, three pictures in `0005/`. | 2026-10-19 |
| [0004](0004-lock-request-heads-mileposts.md) | The crew's unlock request (`WLQK`) and the lock sequence, the local lever rule, head appliances, milepost anchors, the field I/O review, the unified project hierarchy and field units | 2026-10-07 |
| FieldUnit `docs/adr/0002-control-transaction-classes.md` | A malformed transaction is ignored as a whole; an unsafe one voids every vital control; classes are vital and non-vital | 2026-10-02 |
| [0001](0001-code-line-type-contract.md) | The code line type contract: encoding on transport, one code chart for each field station, authored addresses, data-file definitions, first target AAR tokens over MQTT | 2026-10-01, amended 2026-10-02 |
| FieldUnit `docs/adr/0001-mqtt-aar-codeline-interface-a.md` | MQTT broker and AAR tokens for the code line interface | 2026-09-12 |

## Design documents to read (no decision asked; rewritten on 2026-10-01 and 2026-10-02)

| Document | What changed |
|---|---|
| FieldUnit `docs/GLOSSARY.md` | Rewritten. Source of truth for terms. |
| `docs/design/ontology.md` (rev 5) | Rewritten by facet. |
| `docs/design/layout-model.md` (rev 8), `layout-model-plan.md` (rev 3) | Aligned with ADR 0001. Key names `controlPoints`, `fieldStations` are proposals. |
| `docs/design/desk-codeline-kicad-pattern.md` | Aligned with ADR 0001. |

## Records (not for decision)

- `docs/archive/vocabulary-review.md`: findings, eleven iterations of decisions, the plan, the code backlog.
- `docs/archive/vocabulary-sources.md`: what is and is not sourced.
- `docs/archive/spike-cp-membership.md`: the interlocking limits can be derived from signals; control points are declared.

## Not yet written

- Local fascia-mounted devices and maintainer service modes (the tower operator and maintainer roles).
- A US&S 506 code line.
