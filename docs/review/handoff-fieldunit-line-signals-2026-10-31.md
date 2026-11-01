# Handoff to FieldUnit: HD lines and traffic between control points (ADR 0013 Part 2)

- Date: 2026-10-31, revised 2026-11-01. From: the Subdivision ADR 0013 session. To: a FieldUnit session
  (`~/Dropbox/Arduino/libraries/FieldUnit`).
- Source of the rules: Subdivision `docs/adr/0013-between-control-points.md`, **Part 2** (branch
  `docs/adr-0013-blocks`, the 2026-11-01 rewrite; proposed, open decisions A to F). Part 2 is what FieldUnit
  implements. This note does not restate it.
- Prototype evidence: `docs/review/traffic-locking-research-2026-10-31.md`,
  `docs/review/abs-apb-research-2026-10-30.md` and `docs/review/adr-0013-adversarial-review-2026-10-31.md` (the
  second pass governs).
- Picture: `docs/adr/0013/line-signals.svg`.

## Order of authority

1. The relay model of interlocking logic and AAR practice (FieldUnit `docs/GLOSSARY.md` §10.6).
2. FieldUnit `src/`. Where it differs from (1), the code has a defect. File it; never rewrite a principle to match
   weaker code.
3. KiCad-derived models (the Layout Data Model File).
4. Legacy sketches and XML-harvested profiles: evidence only, never a reference.

ADR 0013 Part 1 states the model facts. Part 2 states how FieldUnit codegen and runtime interpret them. The joining
rule: if the model is missing or misstating something, codegen can't fix it. Codegen uses only Part 1 facts (the
traceability table, ADR 0013 §20), never invents, defaults or repairs one, and never reads KiCad.

## Where to read in ADR 0013

| Topic | Section |
|---|---|
| The joining rule; run-time state is FieldUnit's | §13 |
| Operations settings | §14 |
| The HD line: H, D, the SR, the signal location and control point rules | §15 |
| Traffic: why the chain is not enough; the office check (a); the traffic-locking line (b); release | §16 |
| One train, traced | §17 |
| The carrier per block and per code line; electrical and topic forms; codegen errors | §18 |
| What Kind means to a crew; boundary occupancy | §19 |
| Traceability of every Part 2 input to Part 1 | §20 |
| Gaps, including those that block codegen | §21 |

## First step, before any code

Map H, D, the SR, `FR` and `FSR` onto the relay model in GLOSSARY §10.6 and §10.5. Note that GLOSSARY §10.5 uses
`FSR` for FieldUnit's fleet stick relay; the AAR uses it for the traffic stick relay (ADR 0013 gap 6). Where the
relay model and `src/` differ, list each difference as a code defect.

## Open on the Subdivision side

ADR 0013's open decisions A to F, and its gaps 1 to 5 (indication budget, operations settings, how line wires are
drawn, tokens to bits, mixed code lines).

## Out of scope for this handoff

- The KiCad importer and `derive.py` changes (Subdivision's; ADR 0013 §23).
- A common hardware set for a signal location (connector, wiring, PCB): a layout reference design.

## Asked back

One consolidated list, not a narrative:

1. The H/D to relay model mapping, confirmed or corrected, with GLOSSARY section references.
2. The answer to the CB&Q feed question (the same-location opposing cut, ADR 0013 open decision E).
3. Each difference between the relay model and `src/`, as a defect.
4. The decisions FieldUnit needs from the owner, one line each with a default.
