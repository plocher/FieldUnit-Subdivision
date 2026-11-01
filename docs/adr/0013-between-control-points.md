# 0013. Between control points: station-to-station blocks, automatic signals and line signals

- Status: **proposed** 2026-10-31. Decisions 1 to 4 and 6 to 10 were ruled by the owner on 2026-10-30 and 2026-10-31,
  worked through on a POC drawing. The ask: rule on decisions 5 and 11.[^rev1]
- Amends: ADR 0009 §3.10 (a mast states Kind; TRACK Kind `IRJ_SIGNALS`; track circuit Style `boundary`; done in the
  same change), ADR 0009 §3.12's row "track leaves an interlocking" (interlocking track only;
  merged in #58), ADR 0012 §5 (the blocks library's scope) and §5.5 (the proxy retires, §16).
- Builds on: `docs/review/abs-apb-research-2026-10-30.md` with the owner's answers of 2026-10-30, and
  `docs/review/traffic-locking-research-2026-10-31.md` (first-party sources on traffic locking and line circuits).
  The POC drawing: Railroad `2a1696e` (Corporal and Sargent sheets of the SPCoast project).

## Decisions

Ruled decisions are stated as rules. The two open ones have a default.

1. **A station-to-station block** is a piece of the track graph cut at every controlled signal joint that holds no
   switch or derail and lies under a block signal rule (`RULE_251` or `RULE_261`). It belongs to the layout, not to
   an interlocking, and is computed on demand (§4). Ruled.
2. **A mast states what it is:** `Kind` `CONTROLLED`, `ABSOLUTE` or `PERMISSIVE`. A mast with none is missing.
   Grade and restricting plates are POLICY symbols on the mast's net (§5). Ruled.
3. **A joint with a mast on each side** is the `IRJ-Signals` symbol: pins A, B, `SIGNAL_A` (its mast governs into A)
   and `SIGNAL_B` (into B). Nothing is read from rotation (§6). Ruled.
4. **Block track is drawn,** from one control point to the next, and replaces NEXT_CP inside CTC. The block's one
   indication is a virtual track circuit whose members are the block's circuits (§7). Ruled.
5. **A `RULE_251` sign's `LEFT` or `RIGHT` is the lever direction of the signals that govern with the current of
   traffic** (§8). Default: yes.
6. **Three layers:** operations (a railroad's rules and era), the model (railroad-neutral) and the layout (the
   owner's hardware). Prototype practice is evidence for the model's shape, never a wiring mandate (§9). Ruled.
7. **Line signals:** between neighbouring signal locations, one line signal per direction, carrying two values, E
   (energized) and P (proceed). They chain from one control point to the other (§10). Ruled.
8. **The rules that produce line signals,** one for a signal location and one for a control point (§10.3, §10.4).
   Ruled.
9. **Names by signal location:** automatic masts and the circuits between them are numbered for their signal
   location (§11). Ruled.
10. **A boundary track circuit** (Style `boundary`) is a detector at a joint whose occupancy counts toward the circuits
    on both sides (§12). Ruled.
11. **A line signal that must cross between processors and has no drawn transport is an error.** Relaying it through
    the office is allowed only where drawn, never as a fallback (§10.6). Default: yes.

## 1. Problem

The Layout Data Model File describes each interlocking well and the track between them hardly at all:

- No entity holds the track between two control points. A NEXT_CP names a neighbour, but nothing says which circuits
  lie between or which signals govern them.
- Nothing says which signals are automatic.
- A double location, two masts back to back at one joint, is an import error (`joint.masts`).
- Traffic locking and the tumble-down need facts from the far end of the block. The code line carries controls and
  indications between the office and the stations. It cannot carry facts from one field unit to the next.

## 2. Picture and example

![Corporal to Sargent: signal locations and line signals](0013/line-signals.svg)

The POC between Corporal and Sargent shows every case in too little track. It is an example, not a plan for real
signal placement:

| Signal location | Masts | Circuits |
|---|---|---|
| Corporal (control point) | 830SAB and 828SA leave toward Sargent; the 830 home faces the block | 832T on the block side |
| 832 (`IRJ-Signals` B11007) | 832SA toward Sargent, 832NA toward Corporal, both `PERMISSIVE` | 832T, 834T; boundary 833T at the joint |
| 834 (`IRJ-Signals` B1) | 834SA, 834NA, both `PERMISSIVE` | 834T, 836T |
| Sargent (control point) | 836NAB leaves toward Corporal; the 836 home faces the block | 836T |

834T runs from Corporal's sheet to Sargent's through the hierarchical label `ToSargentMT`. The model board shows the
block as `Corporal:831T`, a virtual circuit with members 832T, 834T and 836T.

## 3. Rules in play

Tags: **model**, **representation** (how KiCad draws it), **operating** (a railroad's rule), **layout** (the owner's
hardware).

| # | Rule | Source | Tag |
|---|---|---|---|
| R1 | Subdivision owns no vital logic. Field units run FieldUnit's interlocking logic. This ADR states what passes between them, and FieldUnit implements it. | AGENTS.md | model |
| R2 | A rule that reads a symbol stands for a fact that lives elsewhere. Find the fact. | ADR 0001 D15 | model |
| R3 | Each fact has one source. | AGENTS.md | model |
| R4 | Where a relationship has an explicit form, it is stated or it is missing. | ADR 0012 §4 | model |
| R5 | Domain libraries write nothing into the file. | ADR 0012 §5 | model |
| R6 | A control point is a place with controlled absolute signals. Interlocking limits are the track between opposing home signals: cut the track graph at every controlled signal, and each piece with a switch or derail is an interlocking. | GLOSSARY §4 | model |
| R7 | A block is one or more track circuits treated as one occupancy for one purpose. | GLOSSARY §7 | model |
| R8 | A station-to-station block reaches the office as one indication. | owner 2026-10-30 | model |
| R9 | On SP CTC the signal levers set the direction of traffic. There is no traffic lever. | owner 2026-10-30, [RS1942] | operating |
| R10 | Automatic signals give no authority. On SP they are clear in both directions while the block is idle. Clearing a leaving signal tumbles the opposing ones down to stop. | owner 2026-10-31 | operating |
| R11 | SP practice was not uniform. The model derives the general case, and the drawing states exceptions. | owner 2026-10-30 | model |
| R12 | A token goes on the code line only when something consumes it. | owner 2026-10-27 | model |
| R13 | Identity never comes from a binding. Which processor runs a thing comes from its wiring. | owner 2026-10-16 to 18 | model |
| R14 | Desk and field I/O are asserted low. | owner 2026-10-07 | layout |
| R15 | Selective compression: the model may leave out prototype protections the layout does not need. | owner 2026-10-31 | model |

## 4. The station-to-station block (decision 1)

Cut the track graph at every controlled signal joint (R6). Each piece that holds no switch or derail and carries a
`RULE_251` or `RULE_261` policy sign is one station-to-station block. It holds:

- its track circuits, in order,
- its signal locations and their masts, in order,
- at each end, the control point's leaving signals into it and its home signal facing it,
- its rule and, under `RULE_251`, its current of traffic (§8).

A piece under `RULE_105` or `RULE_93` alone is a siding or station track. A piece that reaches an END_CTC leads to
unsignalled track. Neither is a station-to-station block.

The block belongs to no interlocking. The blocks library computes it on demand (R5). Its track is drawn across sheets
(§7.1), so no pairing is needed.

**ABS or APB is derived, never stated.** It is a property of the block, read from facts already drawn: the masts'
Kinds, the policy sign, and what ends the block.

| Ends | Intermediate masts | Sign | The block is |
|---|---|---|---|
| `CONTROLLED` | `PERMISSIVE` | `RULE_261` | CTC with automatic intermediate signals and traffic locking (Corporal to Sargent) |
| `ABSOLUTE` head blocks | `PERMISSIVE` | `RULE_261` | APB |
| any | all `PERMISSIVE` | `RULE_251` | ABS, one current of traffic |

## 5. What a mast is (decision 2)

A mast states `Kind`:

| Kind | Meaning | What the crew does at its most restrictive aspect |
|---|---|---|
| `CONTROLLED` | The dispatcher controls it. It belongs in a control point. | Stop |
| `ABSOLUTE` | Automatic and absolute (an APB head block) | Stop |
| `PERMISSIVE` | Automatic and permissive, with a number plate | Stop, then proceed at restricted speed |

Kind never changes what the signal displays. Every mast shows the same red at its most restrictive, and the field
unit's logic is the same for all three. The number plate is a fixed part of the aspect, and the rulebook gives that
aspect a different indication: Stop and Proceed instead of Stop. Only the crew's behaviour changes. A semaphore could
show only clear, approach and stop, so a plated stop meant stop, then go slow.

- **Representation.** The library has symbols whose Kind is fixed, with graphics that suggest it: Signal Mast Single
  `CONTROLLED`, `ABSOLUTE` and `PERMISSIVE`, and Signal Mast Double and Dwarf `CONTROLLED`. A fixed Kind is part of
  the symbol's identity, like `Rule251-Left`'s Direction, not a per-instance default. A mast with no Kind is missing.
- **Plates.** The number plate symbol is gone: `PERMISSIVE` means the plate. `Plate-G` (Kind `RULE_290_G`, heavy
  freight only) and `Plate-R` (Kind `RULE_290_R`, all trains) are POLICY symbols. Their pin `To` sits on the mast's
  `SIGNAL` net, and each requires a `PERMISSIVE` mast. No Milepost field: the milepost is already in the mast's name.
- **Check, never a source.** A mast that is not `CONTROLLED` whose route passes a switch is reported at warning. SP's
  spring switches in ABS and APB territory are the exception. The check sets nothing. It belongs with the rule checks
  in `tools/layout_model`.
- **CP Name** is the operations level only: which control point a controlled mast belongs to. Automatic masts state
  none. Which processor drives a mast's lamps comes from the wiring (R13).

Rejected: "a signal is controlled exactly when it states a CP Name". That decided control by inference from a field
that already does another job.

## 6. A joint with a mast on each side (decision 3)

`IRJ-Signals` is Role `TRACK`, Kind `IRJ_SIGNALS`, with pins A (1), B (2), `SIGNAL_A` (3) and `SIGNAL_B` (4). The
mast on `SIGNAL_A` governs into side A. The mast on `SIGNAL_B` governs into side B.

- Masts are drawn on the engineer's side of the approaching train, to the right of the track. On a schematic that is
  plain by inspection, and nothing is inferred from rotation or from which mast is "first". There is no side field.
- `IRJ-Signal` keeps its one `SIGNAL` pin. ADR 0012 §8's `approach` and `governed` sides stand for it unchanged.
- For a double joint, each mast's `approach` and `governed` sides are derived from its pin. The approach and
  governed names are relative to a mast, not to the joint.

## 7. Block track and the block's indication (decision 4)

### 7.1 Drawn, not paired

The block's track is drawn from one control point to the next, across sheets where needed. A hierarchical label
continues the run. Pairing comes from netlist connectivity. Inside CTC a NEXT_CP is no longer needed. It stays for an
interlocking whose neighbour is not drawn.

Consequence for ADR 0009 §3.12's row "track leaves an interlocking only at a NEXT_CP or an END_CTC" (merged in #58): it
covers interlocking track only. Block track belongs to the layout. Dark track beyond an END_CTC is outside both.

### 7.2 The block's one indication

R8: the block reaches the office as one indication. It is a virtual track circuit (`Track Circuit_Virtual`, Style
`virtual`) whose `Members` are the block's circuits: `831T` = [832T, 834T, 836T]. A consumer qualifies it with the
station that sends it, `Corporal:831T` on the model board. By R12 that consumer makes Corporal send `831TK`. Check:
the qualifying station is at one end of the block.

A layout without a model board lamp for the block sends nothing for it.

## 8. Direction of the current of traffic under `RULE_251` (decision 5, open)

| Sign | Kind | `Direction` |
|---|---|---|
| `Rule251-DoT-Left`, `Rule251-DoT-Right` | `RULE_251` | `LEFT`, `RIGHT` |
| `Rule261-DoT-BiDirectional` | `RULE_261` | `BOTH` |
| `Rule105-RestrictedSpeed`, `Rule93-Yard Limits` | `RULE_105`, `RULE_93` | `BOTH` |

`BOTH` adds nothing to its Kind. The 251 sign's `LEFT` or `RIGHT` needs a meaning; as drawn it is an arrow on the
sheet. LEFT and RIGHT are the directions of a signal lever and of a route (GLOSSARY §7). Proposed: the 251 sign's
direction is the lever direction of the signals that govern with the current of traffic. SPCoast agrees:
`Christopher:1NAT` and `Corporal:1SAT` both state `RIGHT`, and trains with the current arrive at a RIGHT signal at
Corporal. The blocks library checks that the signs of one block agree with each other and with its masts.

| Option | For | Against |
|---|---|---|
| **A. The lever direction of the signals that govern with the current** | No drawing change. Checkable against the masts. | Rests on the mast's direction letter (ADR 0003 D1, frozen). |
| B. The far end named | Independent of names. | Fails for a block whose two ends are one interlocking (Watsonville). A library edit. |
| C. Derived from the automatic masts, which face one way under 251 | No statement. | Needs automatic masts drawn on every 251 block. |

Recommendation: A. Under `RULE_261` the direction is set at run time by the line signals (§10). It is not a model fact.

**A `RULE_251` sign inside interlocking limits** states the current of traffic on that track, and nothing more
(owner, 2026-10-31). Watsonville's arrival and departure tracks are switch 837's two legs, between the home joints of
838NCD and 838NAB and the switch. Each leg carries a 251 sign with its direction of travel (Railroad `31954c5`). Such
a sign makes no block, because its piece holds a switch (§4), and it marks neither a block limit nor the end of CTC.
The same agreement check applies: the sign's direction against the signals that govern on that track.

## 9. Three layers (decision 6)

| Layer | What it holds | Who chooses |
|---|---|---|
| Operations | The rule (251, 261); whether following moves may fleet; whether an idle block keeps its last direction (CB&Q) or has none (SP); whether the tumble-down starts when a leaving signal clears (CTC) or when a train passes a head block (APB); whether intermediates are clear at rest | The layout owner, by railroad and era |
| Model | Station-to-station blocks, signal locations, line signals and the rules that produce them; which field unit produces and which consumes each line signal | Railroad-neutral, derived |
| Layout | How a line signal gets from one processor to another: no transport, wires, a field bus, MQTT topics | The layout owner's hardware, drawn |

SP and CB&Q practice from the research shows the model has the right shape. It is not something a layout must copy:
SP did not use microcontrollers or CMRInet. The rules in §10 give SP's behaviour (R10). The operations settings and
where they live are a gap (§14).

## 10. Line signals (decisions 7, 8 and 11)

### 10.1 What a line signal is

A **signal location** is a block boundary: one joint with its pair of masts (the `IRJ-Signals` symbol), the track
circuits on each side, and a line signal in and out on each side. A control point is a signal location with one side
toward the block.

Between neighbouring signal locations there is one line signal for each direction. **A line signal is named for a
mast, and goes to the previous signal in that mast's direction of travel.** It tells that previous signal how far it
may let the next train go, so following traffic does not run into the train ahead. In the picture, `834NA` goes to
Sargent's 836NAB, and `836SA` (Sargent's home) goes to 834SA. It carries two values:

- **E, energized:** the producer's conditions for permission are all true (§10.3, §10.4).
- **P, proceed:** the producer's mast in that direction indicates anything but stop. It is read only while E is
  asserted.

Track circuits never travel one by one. Only what each line signal says travels. On the prototype this is the
line circuit, a chain of two-wire sections fed again at each location [CBQ1946 pp. 613-615], [RS1947 p. 92]. The
model keeps its meaning, not its wiring (decision 6).

### 10.2 A mast reads the line signal from the location it governs toward

| E | P | The mast may show |
|---|---|---|
| released | ignored | stop |
| asserted | released | approach |
| asserted | asserted | clear |

Each indication is further limited by the mast's own conditions (its route and its passed memory).

### 10.3 What a signal location produces

At a signal location L between neighbours U and W, take the mast M at L that governs toward W. Its line signal goes
to U, where the previous signal in M's direction of travel stands:

- **E** is asserted when the circuits between U and L are clear, AND either E from W is asserted or M's passed memory
  is set.
- **P** is asserted when M does not indicate stop.
- **M's passed memory** is set when a train passes M (the circuits beyond M become occupied while M shows proceed).
  It is released when E from W is asserted again. The prototype's form is the directional stick relay
  [CBQ1946 p. 615], [RS1927Spray]. It is FieldUnit state, never stored in the file.

The same rule runs for the other mast and the other direction. At location 832, with M = 832SA:

| Output | E asserted when | P asserted when |
|---|---|---|
| to Corporal (read by 830SAB, 828SA) | 832T clear AND (E from 834 asserted OR 832SA's memory set) | 832SA not at stop |
| to 834 (read by 834NA) | 834T clear AND (E from Corporal asserted OR 832NA's memory set) | 832NA not at stop |

The first part, "E from beyond", chains: a break passes from location to location. That is the tumble-down. The
second part, the passed memory, keeps following moves possible: it masks a break caused by a train moving away.

### 10.4 What a control point produces

Toward its block, at Corporal:

| | Rule |
|---|---|
| **E out** (line signal `830NAB`, to 832NA) | 832T clear AND levers 830 and 828 indicated not toward the block AND neither leaving signal running time |
| **P out** | Corporal's home, 830NAB, does not indicate stop |
| **E in** (from 832) | Required by the route equations of 830SAB and 828SA |
| **P in** | Selects approach or clear for 830SAB and 828SA |

E in stands for every remote term in a leaving signal's route equation:

```
Corporal:830SAB = (831) 831T1 832T 830(RIGHT) 828(STOP) E_in
```

No term for Sargent's lever and no block-clear term is needed. E in is asserted only when no opposing lever is set,
no opposing time is running and no opposing train is in the block. The traffic direction relay is not stated: once
Corporal's train enters, the line back to Sargent stays broken until the train has left the whole block.

### 10.5 One train, traced

T1 leaves Corporal for Sargent:

| T1 in | 832 → 834 E | 834 → Sargent E | 832 → Corporal E | Effect |
|---|---|---|---|---|
| 832T | released (E from Corporal released, no 832NA memory) | released | released (832T occupied) | Tumble-down: 834NA stops; 836NAB locked |
| 834T | released (834T occupied) | released | asserted (832SA's memory set), P released | Corporal can clear 830SAB to approach for a following train; Sargent stays locked |
| 836T | asserted once 834T clears | released (836T occupied) | asserted | Sargent stays locked until T1 arrives |

The research checks this against the prototype's form, with one difference to settle: CB&Q describes the
intermediate's feed as passing over back contacts of the opposing control and stick relays [CBQ1946], where §10.3
uses the same direction's memory. The scenarios above hold either way. The circuit drawing is to be read before the
rule is implemented (§14).

### 10.6 Transport (decision 11, open)

Electrical form, for wired line signals (layout):

- Each value is one wire. Asserted is the producer pulling the line to 0 V (open-drain). Released is the producer
  driving nothing, with a pull-up at the consumer holding the line at +V. A common ground joins the two.
- Released is always the restrictive meaning: a broken wire, an unpowered producer or a processor in reset reads as
  stop. This is R14's asserted-low rule.
- A producer stuck at 0 V reads as permissive. The model does not guard against it (R15). A pulsed signal, like coded
  track, is a possible layout option.
- On I2C expander pins, one line signal each way across a segment is four wires plus ground.
- On MQTT each line signal is one topic, named for its mast: `<root>/linesignal/<mast>`, for example
  `ctc/SPCoast/linesignal/834NA`. E and P travel in one message, so they never disagree: `E P`, `E (P)` or `(E)`
  (P means nothing while E is released). The message is retained, so a consumer that restarts reads the current value.
  The producer's last will is `(E)`, so the broker releases E when the producer drops off: the pull-up's job. The root
  is layout data, as the code line's is. Mast names that govern into a block are unique on the layout, because the
  dispatcher or a tower operator sees them and they take milepost numbers (ADR 0003), so the topic needs no
  qualifier. On multiple track the mast letter tells the tracks apart (834SA and 834SB).

The derivation knows which processor runs each signal location (R13) and lists every line signal whose producer and
consumer are on different processors. With the POC wiring (832T, 834T, 830, 832 and 834 on Corporal's processor; 836T
and 836 on Sargent's), only the 834–836 segment crosses:

| Line signal (topic) | Produced by | Goes to | E asserted when | P asserted when |
|---|---|---|---|---|
| `836SA`, southbound | Sargent | 834SA, on Corporal's processor | 836T clear AND 836NAB at stop and not running time | 836SA not at stop |
| `834NA`, northbound | location 834, on Corporal's processor | Sargent's 836NAB | 836T clear AND (E from 832 asserted OR 834NA's memory set)[^segment] | 834NA not at stop |

Proposed: a crossing line signal with no transport drawn is an error, and relaying through the office host (one
station's indication forwarded to another as a control) is allowed only where drawn. Relaying puts field safety on
the office being up.

| Option | For | Against |
|---|---|---|
| **A. Error; office relay only where drawn** | No hidden dependency on the office. Every crossing is visible in the drawing. | The owner draws a transport for every split. |
| B. Office relay as the fallback | Works with only a code line. | The tumble-down and traffic locking then fail when the office is down. |
| C. Constrain wiring so nothing crosses | No transport. | Both control points need the end circuits, so it works only when both interlockings run on one processor. Every interlocking has neighbours, so it ends as one processor for all. |

Recommendation: A. The code line itself is no transport for line signals: it carries the office's controls and the
stations' indications.

Where the central-application pattern holds (one program runs all the logic; CMRInet, JMRI MQTT, LocoNet or LCC
nodes carry the wiring), nothing crosses: every line signal is local. The distributed pattern (an office unit and
field units on one code line, US&S 506 or AAR MQTT) is the one that needs a transport.

## 11. Names by signal location (decision 9)

- An automatic mast is numbered for its signal location, the milepost in tenths, with its direction letter and head
  letter as for any mast (`grammar.MAST_NAME`): 832SA and 832NA at location 832. No CP Name.
- A circuit between two signal locations is named for the location at its higher-milepost end, whose mast governs
  over it: 832T between 830 and 832. ADR 0003 already numbers a circuit outside interlocking limits for the signal
  that governs over it. No CP Name: block track belongs to the layout.
- A virtual circuit for a block (`831T`) takes any number not used by a signal location.

Milepost numbers are unique on the layout, so none of these names needs an interlocking qualifier. The names do not
change when the hardware is split differently.

## 12. Boundary track circuits (decision 10)

Current detection does not see cars with plastic wheels. A detector at the joint, an IR beam for example, keeps the
block a train is leaving occupied until the last car has passed the masts. (MSS, the Modular Signal System, places
its detectors at block boundaries for the same reason.)

- The symbol `Track Circuit IR Boundary` is `Appliance track_circuit`, Style `boundary`, with pins A and B on the two
  nets at a joint. Its name says the technology. The model reads only the Style.
- It has one detected output, wired to a driver pin like any track circuit. The derivation ORs its occupancy into
  each circuit on its pins. It never splits a circuit or ends a block.
- A detector wired straight into the two circuits' inputs in the field is not drawn at all.
- It is named like any circuit (833T in the POC). Its input belongs on the processor that runs its signal location,
  which reads it for both of that location's outputs.

## 13. Derived, and where each result lives

| Result | Where |
|---|---|
| A mast's Kind | `given`, stated |
| ABS, APB or CTC for a block | blocks library, on demand |
| Station-to-station blocks, their circuits, signal locations, rule and current | blocks library, on demand |
| Line signals: producer, consumer, and the processors each runs on | blocks library, on demand |
| A circuit's occupancy inputs, including boundary circuits | derivation, from the pins |
| Next and approach signals, home and leaving roles | routes library, on demand (ADR 0012 §5.3) |
| A virtual circuit's token on the code line | code line library, by R12 |

## 14. Gaps

1. The operations settings of §9: their names and where they live (the rulebook reference table of ADR 0012 §6 is
   the likely home).
2. CB&Q's intermediate feed against §10.3's passed memory (§10.5): to be read from the circuit drawing.
3. How a line signal transport is drawn: wires between processors' driver pins, a field bus, MQTT topics. A symbol
   or seam for it, like the code line's.
4. Whether the board's `831T` could be derived from the two line signals instead of its members. SP used the two line
   circuits to detect the block as a whole [RS1947 p. 92].
5. The glossary has no entries for automatic signal, signal location, line signal, station-to-station block,
   boundary circuit, current and direction of traffic.
6. Luchessa's and Watsonville's `NFLK` and `SFLK` (board `TRAFFIC` lamps): whether they become a block's direction
   indication.
7. Off-layout ends (Lick, Hollister): a block with one end on the layout is reported at info.

## 15. Out of scope

- FieldUnit's implementation of §10 (R1): the relay model, approach lighting, time release, aspects.
- The contents of the rulebook reference table.
- Train order conditions: the reversed number plate, Form Z.
- How a US&S 506 code chart assigns the block indication to a step.
- A common hardware set for a signal location (connector, wiring, PCB carrying the line signals, detector inputs and
  mast outputs): a layout reference design, not a model fact.

## 16. Consequences

- ADR 0009 §3.10: a mast states Kind; TRACK Kind `IRJ_SIGNALS`; track circuit Style `boundary` (this change), and the
  symbol-field lint accepts a mast's Kind and requires it.
- ADR 0009 §3.12 (merged in #58): the track rule covers interlocking track only, amended in place when this ADR is ruled.
- ADR 0012 §5: the blocks library covers the track between control points, and serves line signals. §5.5: the proxy
  and its TBD retire, since a signal never stands in for another; the approach signal of a home is derived.
- The KiCad importer: a hierarchical label continues a track run (`geometry.run_end` fires on one today);
  `IRJ-Signals` with per-mast sides; `joint.masts` retires for two masts on opposite sides; Style `boundary` (today
  the boundary symbol, with no `TC` pin, is skipped without a word).
- `derive.py`: the mast checks of §5; boundary occupancy; NEXT_CP pairing retires inside CTC.
- The schema: a double joint's masts with their sides; a mast's Kind.
- FieldUnit: implements §10's rules and line signal transports.

[^rev1]: Rewritten 2026-10-31 from the owner's rulings. The first draft (commit 96d3765) asked six decisions:
    decision 2 there (controlled exactly when a CP Name is stated) was rejected; decision 4 (the policy sign names the
    block and pairs NEXT_CPs) became drawn block track and a virtual circuit; decision 6 (each end's indications
    include the far end's part) was replaced by line signals.

[^segment]: 836T is read on Sargent's processor, so with this wiring Sargent ANDs 836T into the value it reads, and
    location 834 sends the rest. Each end of a segment ANDs the part of the segment's occupancy it reads.
