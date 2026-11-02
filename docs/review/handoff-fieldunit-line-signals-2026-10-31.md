# Handoff to FieldUnit: HD lines and traffic between control points (ADR 0013 Parts 2 & 3)

- Date: 2026-10-31, revised 2026-11-01 (rev 3). From: the Subdivision ADR 0013 session. To: a FieldUnit session
  (`~/Dropbox/Arduino/libraries/FieldUnit`).
- Source: Subdivision `docs/adr/0013-between-control-points.md`, **Part 2** (prototype behavior and relay principles,
  the reference authority) and **Part 3** (suggestions, implementation options, and context for FieldUnit), on branch
  `docs/adr-0013-blocks` (accepted 2026-11-01, rev 3). Part 2 is the behavior to model; Part 3 gives the options and
  the scan-order note. This note does not restate them.
- Prototype evidence: `docs/review/traffic-locking-research-2026-10-31.md`,
  `docs/review/abs-apb-research-2026-10-30.md` and `docs/review/adr-0013-adversarial-review-2026-10-31.md`.
- Picture: `docs/adr/0013/line-signals.svg`.

## Order of authority

1. The relay model of interlocking logic and AAR practice (FieldUnit `docs/GLOSSARY.md` §10.6; ADR 0013 Part 2).
2. FieldUnit `src/`. Where it differs from (1), the code has a defect. File it; never rewrite a principle to match
   weaker code.
3. KiCad-derived models (the Layout Data Model File; ADR 0013 Part 1).
4. Legacy sketches and XML-harvested profiles: evidence only, never a reference.

ADR 0013 Part 1 states the normative model facts. Part 2 states the prototype behavior. Part 3 gives non-normative
suggestions, selective compressions (R15), and implementation options for FieldUnit codegen and runtime. The joining
rule: if the model is missing or misstating something, codegen cannot fix it (R17). Codegen uses only Part 1 facts (the
traceability table, ADR 0013 §20) plus reference data, never invents, defaults or repairs a model fact, and never reads
KiCad.

## Where to read in ADR 0013

| Topic | Section |
|---|---|
| The seam between the data model and FieldUnit; run-time state is FieldUnit's | §13 |
| Three layers and the operations settings | §14 |
| The HD line: `H`, `D`, the directional stick `SR`, the signal location and control point rules, what `Kind` means to a crew | §15 |
| How the vital field and the HD chain enforce traffic locking (`R18`: non-vital office never gates controls; vital field rejects unsafe transactions); one train, traced | §16 |
| Relay model options and selective compressions for FieldUnit (`HSR` knockdown vs. sticky direction, tumble-down trigger, CB&Q same-location opposing cut, two-value diverging compression) | §17 |
| Cross-processor carriers, the POC 834–836 split, and the four things codegen should watch (including settling the `HD` chain before evaluating controls) | §18 |
| Boundary track circuit occupancy (make-before-break) | §19 |
| Traceability of every consumer input to Part 1 | §20 |
| Gaps (operations settings in reference data, how line wires are drawn) | §21 |

## First step, before any code

1. Map `H`, `D`, and `SR` onto the relay model in GLOSSARY §10.6 and §10.5. Note that GLOSSARY §10.5 uses `FSR` for
   FieldUnit's fleet stick relay while traffic-lever schemes use `FSR` for the traffic stick relay (ADR 0013 §21 gap 5:
   AAR names are not unique across domains). Where the relay model and `src/` differ, list each difference as a code
   defect.
2. Address the discrete scan-order requirement in ADR 0013 §18.2 item 4: after any track circuit or `H in` change,
   settle the `HD` chain before evaluating a control transaction, so a receding direction's `SR` always sees the release
   pulse when the last circuit of a block clears.

## Known defect to file

- `src/WireCodec.h` writes and expects only `NGS`/`SGS` and `NGK`/`SGK` (lines 927-928, 1042-1043). The direction
  letters belong to the railroad and era: an E/W railroad sends `WGS`/`EGS` and `WGK`/`EGK`. The codec should accept
  either pair (N or W is LEFT, S or E is RIGHT, as ADR 0003 D1 reads mast names) (owner, 2026-11-01). Which letters a
  layout uses comes from its drawing: a per-railroad trackplan library (`Railroad-Trackplan-SP`,
  `Railroad-Trackplan-CBQ`) with the same symbol names, not a reference-data table.

## Open on the Subdivision side

ADR 0013 §21 gaps 2 and 3 (the operations settings in reference data, and how line wires between processors are drawn).
Gaps 1, 4, and 5 (`reference.CODE_LINE_CAPACITY`, `reference.CODE_LINE_STEPS`, and the `FieldUnit/docs/GLOSSARY.md`
entries) are closed.

## Out of scope for this handoff

- The KiCad importer and `derive.py` changes (Subdivision's; ADR 0013 §23).
- A common hardware set for a signal location (connector, wiring, PCB): a layout reference design.

## Asked back

One consolidated list, not a narrative:

1. The `H`/`D`/`SR` to relay model mapping (including scan-order settling of the `HD` chain before controls), confirmed
   or corrected, with GLOSSARY section references.
2. Each difference between the relay model and `src/`, as a defect.
3. The decisions FieldUnit needs from the owner (such as which §17 and §18.2 options to adopt), one line each with a
   default.
