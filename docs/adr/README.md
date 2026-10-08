# Decision records

One list of what is decided and what waits for the owner. Each proposed ADR opens with a
"Decisions requested" section.

## Waiting for a decision

| ADR | Subject | Asked of the owner |
|---|---|---|
| [0002](0002-symbol-contract.md) | What each KiCad symbol records | Frozen 2026-10-03: too complicated to approve as-is. Rewritten to rules after the cleanup pass (#30), then approved. |
| [0003](0003-name-grammar.md) | One grammar for the names of appliances, signals and track circuits | Frozen 2026-10-03, same reason; the owner's in-progress edits are committed as they stood. Rewritten to rules after #30. |
| [0004](0004-lock-request-heads-mileposts.md) | The crew's unlock request (`WLQK`), head appliances, milepost anchors, field I/O review | R5: the local switch lever while locked and at unlock. D1–D13 record the 2026-10-07 rulings, including the unified project hierarchy and field units. |

## Accepted

| ADR | Subject | Date |
|---|---|---|
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
