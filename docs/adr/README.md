# Decision records

One list of what is decided and what waits for the owner. Each proposed ADR opens with a
"Decisions requested" section.

## Waiting for a decision

| ADR | Subject | Asked of the owner |
|---|---|---|
| FieldUnit `docs/adr/0002-control-transaction-classes.md` | How a field unit processes a control transaction: a malformed one is ignored as a whole; an unsafe one has every first-class control ignored together | Approve the two rules. Choose the class names: vital / non-vital, or interlocked / auxiliary. |
| [0002](0002-symbol-contract.md) | What each KiCad symbol records | The numbered list at the top of the ADR. First: what names the interlocking. |
| [0003](0003-name-grammar.md) | One grammar for the names of appliances, signals and track circuits | The numbered list at the top of the ADR. Nothing is renamed until it is accepted. |

## Accepted

| ADR | Subject | Date |
|---|---|---|
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
