# Handoff to FieldUnit: line signals between control points (ADR 0013)

- Date: 2026-10-31. From: the Subdivision ADR 0013 session. To: a FieldUnit session
  (`~/Dropbox/Arduino/libraries/FieldUnit`).
- Source of the rules: Subdivision `docs/adr/0013-between-control-points.md` (branch `docs/adr-0013-blocks`, commit
  `b40f238`; proposed, decisions 5 and 11 open). Prototype evidence: `docs/review/traffic-locking-research-2026-10-31.md`
  and `docs/review/abs-apb-research-2026-10-30.md`.
- Picture: `docs/adr/0013/line-signals.svg`.

## Order of authority

1. The relay model of interlocking logic and AAR practice (FieldUnit `docs/GLOSSARY.md` §10.6).
2. FieldUnit `src/`. Where it differs from (1), the code has a defect. File it; never rewrite a principle to match
   weaker code.
3. KiCad-derived models (the Layout Data Model File).
4. Legacy sketches and XML-harvested profiles: evidence only, never a reference.

ADR 0013 states what passes between field units and what it means. FieldUnit implements it (Subdivision owns no
vital logic). Prototype practice (SP, CB&Q) is evidence for the shape of the model, not a wiring mandate: layouts may
compress (ADR 0013 §9).

## What FieldUnit implements

| # | Item | ADR 0013 |
|---|---|---|
| 1 | **The line signal** as a type: two values, E (energized) and P (proceed; read only while E is asserted), with a producer and a consumer. One per direction between neighbouring signal locations. A line signal is named for a mast and goes to the previous signal in that mast's direction of travel. | §10.1 |
| 2 | **A mast reads E/P** from the location it governs toward: E released → stop; E without P → approach; E and P → clear, further limited by its own route and passed memory. The same for every mast Kind: Kind changes the crew's rule (a plated red is Stop and Proceed), never the aspect or the logic. | §10.2, §5 |
| 3 | **The signal location** (one joint, its mast pair, the circuits each side): for mast M governing toward W, the line signal named M goes to U with E = circuits U–L clear AND (E from W OR M's passed memory); P = M not at stop. The passed memory is set when a train passes M and released when E from W is asserted again (the prototype's directional stick relay). | §10.3 |
| 4 | **The control point** toward its block: E out = first block circuit clear AND its leaving levers indicated not toward the block AND no time running; P out = its home facing the block not at stop. E in replaces every remote term in a leaving signal's route equation (`830SAB = (831) 831T1 832T 830(RIGHT) 828(STOP) E_in`); the traffic direction relay is not stated, it falls out of the chain. | §10.4 |
| 5 | **Transports** for a line signal whose producer and consumer run on different processors: local (same processor, nothing travels); digital pins (asserted = producer pulls to 0 V, open-drain; released = consumer's pull-up; a broken wire reads restrictive); MQTT (one retained topic per line signal, `<root>/linesignal/<mast>`, payload `E P`, `E (P)` or `(E)`, last will `(E)`). The code line is never a transport for line signals. | §10.6 |
| 6 | **Boundary track circuits** (Style `boundary`): a detector at a joint with its own input; its occupancy ORs into each circuit on its two pins; it never splits a circuit or ends a block. | §12 |
| 7 | **The block's virtual circuit** (`831T` = [832T, 834T, 836T]): sent as an indication only when a consumer, such as a model board lamp, asks for it. | §7.2 |
| 8 | **Operations settings** chosen per railroad and era: fleeting, whether an idle block keeps its last direction (CB&Q) or none (SP), whether the tumble-down starts when a leaving signal clears (CTC) or when a train passes a head block (APB), intermediates clear at rest (SP). The rules of items 3 and 4 give SP's behaviour. Where the settings live is open. | §9, §14 gap 1 |
| 9 | **GLOSSARY terms** (FieldUnit owns the glossary): automatic signal, signal location, line signal, station-to-station block, boundary circuit, current and direction of traffic, passed memory. | §14 gap 5 |

The worked example is ADR 0013 §10.5 (one train traced through the chain) and the POC crossing pair in §10.6
(`836SA` to 834SA, `834NA` to 836NAB).

## First step, before any code

Map E and P onto the relay model in GLOSSARY §10.6. Our reading, to be checked, not assumed: E is the line that feeds
a signal's `HR` from the location ahead; P is what `DR` reads (the next signal not at stop); the passed memory is the
directional stick relay. Settle there:

- **CB&Q's intermediate feed.** The research reads CB&Q (1946, pp. 613-615) as feeding the next section over back
  contacts of the opposing `HR` and `SR`. ADR 0013 §10.3 uses the same direction's passed memory instead. The traced
  scenarios hold either way. Read the circuit drawing and say which the relay model requires (ADR 0013 §14 gap 2).
- **Where the relay model and `src/` differ,** list each difference as a code defect.

## Open on the Subdivision side

- ADR 0013 decision 5: what a `RULE_251` sign's `LEFT` or `RIGHT` means (default: the lever direction of the signals
  that govern with the current of traffic).
- ADR 0013 decision 11: a line signal that must cross processors with no drawn transport is an error; relaying through
  the office only where drawn (default: yes).
- How a line signal transport is drawn in KiCad (ADR 0013 §14 gap 3).

## Out of scope for this handoff

- The KiCad importer and `derive.py` changes (Subdivision's; ADR 0013 §16).
- A common hardware set for a signal location (connector, wiring, PCB): a layout reference design.

## Asked back

One consolidated list, not a narrative:

1. The E/P to relay model mapping, confirmed or corrected, with GLOSSARY section references.
2. The answer to the CB&Q feed question.
3. Each difference between the relay model and `src/`, as a defect.
4. The decisions FieldUnit needs from the owner, one line each with a default.
