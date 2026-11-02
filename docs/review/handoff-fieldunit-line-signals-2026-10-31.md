# Handoff to FieldUnit: the interlocking–block seam, HD lines and traffic (ADR 0013 Parts 2 & 3)

- Date: 2026-10-31, revised 2026-11-02 (rev 4). From: the Subdivision ADR 0013 session. To: a FieldUnit session
  (`~/Dropbox/Arduino/libraries/FieldUnit`).
- Source: Subdivision `docs/adr/0013-between-control-points.md`, **Part 2** (between-interlockings prototype behavior,
  the functional interlocking–block seam in §13, safety invariants `I1`–`I4` in §14.1, and reference-data profiles in
  §14.2) and **Part 3** (deployment variations A–D, carrier vitality, and consumer context), on branch
  `docs/adr-0013-blocks` (accepted, rev 4).
- Prototype evidence: `docs/review/traffic-locking-research-2026-10-31.md` (`[TLRES]`),
  `docs/review/abs-apb-research-2026-10-30.md` (`[ABSAPB]`) and
  `docs/review/adr-0013-adversarial-review-2026-10-31.md`.
- Picture: `docs/adr/0013/line-signals.svg`.

## Order of authority

1. **The relay model of interlocking and block signaling and AAR/AREMA practice**, in two documents by scope:
   - **Inside an interlocking plant:** `FieldUnit/docs/GLOSSARY.md` §10.6.
   - **Between interlocking plants:** `FieldUnit-Subdivision/docs/adr/0013-between-control-points.md` Part 2.
   - **The boundary between them:** the functional **interlocking–block seam** (ADR 0013 §13). Neither document restates
     or reaches inside the other's scope.
2. **FieldUnit `src/`.** Where it differs from (1), the code has a defect. File it; never rewrite a principle to match
   weaker code.
3. **KiCad-derived models** (the Layout Data Model File; ADR 0013 Part 1).
4. **Legacy sketches and XML-harvested profiles:** evidence only, never a reference.

If the model is missing or misstating something, codegen cannot fix it (R17). Consumers use only Part 1 facts (the
traceability table, ADR 0013 §20) plus reference data, never invent, default or repair a model fact, and never read
KiCad.

## The functional seam contract (ADR 0013 §13)

At each end of a station-to-station block, the interlocking and the block exchange seven functional facts:

| Direction | Functional seam port | Meaning | Prototype relay realization |
|---|---|---|---|
| **Interlocking $\to$ Block** (outbound) | `requested` | A leaving signal at this end has an active direction request into the block | `RGZ` / `HSR` |
| **Interlocking $\to$ Block** (outbound) | `cleared` | A leaving signal at this end is cleared into the block (indicates Approach or better) | `HR` front / `!RGPR` |
| **Interlocking $\to$ Block** (outbound) | `in_time` | A leaving signal into the block is running approach or time locking | `ASR` back / `TER` |
| **Interlocking $\to$ Block** (outbound) | `home_proceed` | The home signal facing the block indicates Approach or better | `HR` front (`GLOSSARY.md` §10.6); `AGGPR` (`[CBQ1946 p. 615]`, opened) |
| **Block $\to$ Interlocking** (inbound) | `segment_clear` | The entrance circuit and ahead/stick conditions permit the leaving signal to show at least Approach | `H` (feeds leaving signal `HR`) |
| **Block $\to$ Interlocking** (inbound) | `next_proceed` | The next signal in the block indicates Approach or better, permitting the leaving signal to upgrade to Clear | `D` (feeds leaving signal `DR`) |
| **Block $\to$ Interlocking** (inbound) | `traffic_free` | The block and far end are free of opposing traffic (never bypassed by an intermediate directional stick) | `F` / `FR` / `FSR` (equals `segment_clear` under `SP_1942`) |

## Where to read in ADR 0013

| Topic | Section |
|---|---|
| The functional seam between an interlocking and a station-to-station block | §13 |
| Four railroad-independent safety invariants (`I1`–`I4`, Gherkin) and the 3-column `blockRules` profile table (`SP_1942`, `CBQ_1946`, `ERIE_NW_1942`) | §14 |
| The HD line (`segment_clear` / `H`, `next_proceed` / `D`), the directional stick `SR`, intermediate and seam rules, what `Kind` means to a crew | §15 |
| One train, traced across the seam | §16 |
| Selective compressions (two-value diverging compression, boundary make-before-break) | §17 |
| Four deployment variations (A: AAR codeline eavesdropping [`non_vital` R15], B: wired `H`/`D` [`vital`], C: unified processor [`vital`], D: US&S 506 1–2 circuit eavesdropping [`non_vital` R15]), what is drawn for each, and the POC 834–836 split | §18 |
| Boundary track circuit occupancy | §19 |
| Traceability of every consumer input to Part 1 | §20 |
| Gaps (`blockRules` in `reference.py`, `Device-HD-Out`/`Device-HD-In` graphics in `Railroad-Field.kicad_sym`) | §21 |
| Dated revision record | §24 |

## Known defect to file

- `src/WireCodec.h` writes and expects only `NGS`/`SGS` and `NGK`/`SGK` (lines 927-928, 1042-1043). The direction
  letters belong to the railroad and era: an E/W railroad sends `WGS`/`EGS` and `WGK`/`EGK`. The codec should accept
  either pair (N or W is LEFT, S or E is RIGHT, as ADR 0003 D1 reads mast names) (owner, 2026-11-01). Which letters a
  layout uses comes from its drawing: a per-railroad trackplan library (`Railroad-Trackplan-SP`,
  `Railroad-Trackplan-CBQ`) with the same symbol names, not a reference-data table.

## Open on the Subdivision side

ADR 0013 §21 gaps 2 and 3 (`blockRules` profiles in `tools/layout_model/reference.py`, and the library graphics for
`Device-HD-Out` / `Device-HD-In` in `Railroad-Field.kicad_sym`). Gaps 1, 4, and 5 (`reference.CODE_LINE_CAPACITY`,
`reference.CODE_LINE_STEPS`, and the `FieldUnit/docs/GLOSSARY.md` entries) are closed.

## Out of scope for this handoff

- The KiCad importer and `derive.py` changes (Subdivision's; ADR 0013 §23).
- A common hardware set for a signal location (connector, wiring, PCB): a layout reference design.

## Asked back (seam checklist)

One consolidated per-fact list for the seven seam ports of §13 (`requested`, `cleared`, `in_time`, `home_proceed`;
`segment_clear`, `next_proceed`, `traffic_free`) plus the invariants `I1`–`I4`:

1. For each seam port: what `FieldUnit/src/` exposes today, under what name, and whether it is available today,
   available but misnamed, or a code defect (such as missing `DR` / issue #18).
2. Any decisions `FieldUnit` needs from the owner to wire the seam ports and preserve `I1`–`I4`, one line each with a
   default.
