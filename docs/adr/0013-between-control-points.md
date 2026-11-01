# 0013. Between control points: blocks, automatic signals, the HD line and traffic

- Status: **proposed** 2026-10-31, rewritten 2026-11-01 as one ADR in two parts.[^rev] The owner ruled the decisions
  in the list "Ruled" on 2026-10-30, 2026-10-31 and 2026-11-01. The ask: rule on open decisions A to F.
- Amends: ADR 0009 §3.10 (a mast states Kind; TRACK Kind `IRJ_SIGNALS`; track circuit Style `boundary`; done in the
  same change), ADR 0009 §3.12's row "track leaves an interlocking" (interlocking track only; merged in #58), ADR 0012
  §5 (the blocks library's scope) and §5.5 (the proxy retires, §23).
- Builds on: `docs/review/abs-apb-research-2026-10-30.md` with the owner's answers of 2026-10-30,
  `docs/review/traffic-locking-research-2026-10-31.md` (first-party sources on traffic locking and line circuits) and
  `docs/review/adr-0013-adversarial-review-2026-10-31.md` (both passes; the second governs). The POC drawing: Railroad
  `2a1696e` (Corporal and Sargent sheets of the SPCoast project).

## Decisions requested

Open. Each has a default.

- **A.** Where a mast's governed circuit is read for its SR. Default: on the processor that runs the mast's signal
  location; otherwise an error. Rulings 9 and 10 may make it moot on AAR MQTT (§15.3, §18).
- **B.** APB is derived from `ABSOLUTE` ends alone; a `RULE_261` sign on `ABSOLUTE` ends is reported at warning.
  Default: yes (§4).
- **C.** The block is cut at `CONTROLLED` and `ABSOLUTE` joints; a block may hold switches that are not powered; R6
  reads "powered switch". Default: yes (§4).
- **D.** The tumble-down starts on the accepted control (CB&Q) or on the cleared signal (SP). Default: the accepted
  control (§15.4).
- **E.** The same-location opposing cut (CB&Q) is not added. Default: yes; it is fidelity only (§15.3).
- **F.** A `RULE_251` sign's `LEFT` or `RIGHT` is the lever direction of the signals that govern with the current of
  traffic. Default: yes, as is (§8).

Ruled. Stated as rules.

1. **Two parts, one ADR.** Part 1 states the model facts. Part 2 states how consumers interpret them. Part 2 uses only
   facts that Part 1 states. If the model is missing or misstating something, codegen can't fix it (§13).
2. **A station-to-station block** is a piece of the track graph between control points, cut at signal joints, that
   holds no powered switch and lies under a block signal rule (cut and switches: open C). It belongs to the layout, not to an
   interlocking. A domain library computes it on demand (§4).
3. **A mast states what it is:** `Kind` `CONTROLLED`, `ABSOLUTE` or `PERMISSIVE`. A mast with none is missing. Grade
   and restricting plates are POLICY symbols on the mast's net (§5).
4. **A joint with a mast on each side** is the `IRJ-Signals` symbol: pins A, B, `SIGNAL_A` (its mast governs into A)
   and `SIGNAL_B` (into B). Nothing is read from rotation (§6).
5. **Block track is drawn** from one control point to the next. It replaces NEXT_CP inside CTC. The block's one
   indication is a virtual track circuit whose members are the block's circuits (§7).
6. **Three layers:** operations (a railroad's rules and era), the model (railroad-neutral) and the layout (the
   owner's hardware). Prototype practice is evidence for the model's shape, never a wiring mandate (§14).
7. **Prototype names.** Between neighbouring signal locations, one **HD line** per direction carries two values: H
   feeds the signal's `HR`, D feeds its `DR` (AAR Dwg 8066, "Two-Wire HD Line Control"; AAR nomenclature, 1946). The
   passed memory is the **SR** (stick relay). The direction of a block is its **traffic** (`FR` traffic relay, `FSR`
   traffic stick relay) (§15, §16).
8. **The rules that produce H and D,** one for a signal location and one for a control point (§15.3, §15.4).
9. **Traffic is explicit.** The HD chain alone does not lock a block's traffic. One of two means locks it: the office
   check (AAR Dwg 8082) or a traffic-locking line between the end control points (Erie 1942, N&W 1949). Traffic is
   never inferred in the field from H and D. It releases only when the initiating lever is back at STOP and the whole
   block is clear (§16).
10. **The carrier is codegen's choice, per block.** On AAR MQTT, block circuits go to the office as indications. On
    US&S 506, a block-clear indication bit from one end control point, else a traffic-locking line. A block with
    neither is a codegen error (§18).
11. **Where things live.** Generators decide transports and carriers (ADR 0012's split). `derive.py` raises no
    transport errors (§18.5).
12. **Facts the model carries for Part 2:** blocks with their ends, signal locations, members and the processor that
    reads each circuit; each station's code line kind; each station's indication budget; the indications already
    used; drawn line wires (§11).
13. **Names by signal location:** automatic masts and the circuits between them are numbered for their signal
    location (§9).
14. **A boundary track circuit** (Style `boundary`) is a detector at a joint. The model states which circuits it
    counts toward (§10). Consumers OR its occupancy into them (§19.2).
15. **A `RULE_251` sign inside interlocking limits** states the current of traffic on that track, and nothing more
    (§8).

# Part 1. Model facts

What comes from KiCad or Studio into the Layout Data Model File, as `given`, `relations` or `derived` (ADR 0011), and
what the domain libraries compute from it on demand (ADR 0012 §5).

## 1. Problem

The Layout Data Model File describes each interlocking well and the track between them hardly at all:

- No entity holds the track between two control points. A NEXT_CP names a neighbour, but nothing says which circuits
  lie between or which signals govern them.
- Nothing says which signals are automatic.
- A double location, two masts back to back at one joint, is an import error (`joint.masts`).
- Traffic locking and the tumble-down need facts from the far end of the block. The model does not say which
  processor has those facts, or how a consumer can get them.

## 2. Picture and example

![Corporal to Sargent: signal locations, HD lines and traffic](0013/line-signals.svg)

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
| R1 | Subdivision owns no vital logic. Field units run FieldUnit's interlocking logic. This ADR states the facts and what passes between units. FieldUnit implements it. | AGENTS.md | model |
| R2 | A rule that reads a symbol stands for a fact that lives elsewhere. Find the fact. | ADR 0001 D15 | model |
| R3 | Each fact has one source. | AGENTS.md | model |
| R4 | Where a relationship has an explicit form, it is stated or it is missing. | ADR 0012 §4 | model |
| R5 | Domain libraries write nothing into the file. | ADR 0012 §5 | model |
| R6 | A control point is a place with controlled absolute signals. Interlocking limits are the track between opposing home signals: cut the track graph at every controlled signal, and each piece with a switch or derail is an interlocking. Open C reads "powered switch". | GLOSSARY §4 | model |
| R7 | A block is one or more track circuits treated as one occupancy for one purpose. | GLOSSARY §7 | model |
| R8 | A station-to-station block reaches the office as one indication. | owner 2026-10-30 | model |
| R9 | On SP CTC the signal levers set the traffic. There is no traffic lever. | owner 2026-10-30, [RS1942] | operating |
| R10 | Automatic signals give no authority. On SP they are clear in both directions while the block is idle, and clearing a leaving signal tumbles the opposing ones down to stop. Other railroads differ (§14). | owner 2026-10-31, [CBQ1946] | operating |
| R11 | SP practice was not uniform. The model derives the general case, and the drawing states exceptions. | owner 2026-10-30 | model |
| R12 | A token goes on the code line only when something consumes it. | owner 2026-10-27 | model |
| R13 | Identity never comes from a binding. Which processor runs a thing comes from its wiring. | owner 2026-10-16 to 18 | model |
| R14 | Desk and field I/O are asserted low. | owner 2026-10-07 | layout |
| R15 | Selective compression: the model may leave out prototype protections the layout does not need. | owner 2026-10-31 | model |
| R16 | Occupancy of the block, or an opposing cleared signal, prevents a change of traffic. | CFR §236.405; ICC 1939 Item 382 | operating |
| R17 | If the model is missing or misstating something, codegen can't fix it. | owner 2026-11-01 | model |

## 4. The station-to-station block (ruled 2; open B, C)

Cut the track graph at every `CONTROLLED` and `ABSOLUTE` signal joint (open C). Each piece that holds no powered
switch and lies under a block signal rule is one station-to-station block. A powered switch has a machine or a CP
Name. A hand-throw switch, a spring switch and an electrically locked hand-throw switch may lie in a block (open C).
A block holds:

- its track circuits, in order;
- its signal locations and their masts, in order;
- at each end, the control point's leaving signals into it and its home signal facing it;
- its rule and, under `RULE_251`, its current of traffic (§8).

A piece under `RULE_105` or `RULE_93` alone is a siding or station track. A piece that reaches an END_CTC leads to
unsignalled track. Neither is a station-to-station block.

The block belongs to no interlocking. The blocks library computes it on demand (R5). Its track is drawn across sheets
(§7.1), so no pairing is needed.

**ABS, APB or CTC is derived, never stated.** It is a property of the block, read from facts already drawn: the
masts' Kinds at its ends and between, and its sign.

| Ends | Intermediate masts | Sign | The block is |
|---|---|---|---|
| `CONTROLLED` | none, or all `PERMISSIVE` | `RULE_261` | CTC, with automatic intermediate signals where drawn (Corporal to Sargent) |
| `ABSOLUTE` head blocks | none, or all `PERMISSIVE` | any, or none (open B) | APB |
| any | all `PERMISSIVE` | `RULE_251` | ABS, one current of traffic |

Open B: the APB row is derived from the `ABSOLUTE` ends alone. The sign states authority, not the method. Rule 261
gives signal indication authority in both directions, and an automatic signal gives none (R10), so a `RULE_261` sign
on `ABSOLUTE` ends is reported at warning. A railroad that let APB signals authorize moves (SP's Oxnard to Montalvo
special rules) states it on purpose.

## 5. What a mast is (ruled 3)

A mast states `Kind`: `CONTROLLED` (the dispatcher controls it; it belongs in a control point), `ABSOLUTE` (automatic
and absolute, an APB head block) or `PERMISSIVE` (automatic and permissive, with a number plate). Kind is a fact.
What it means to a crew is Part 2's (§19.1).

- **Representation.** The library has symbols whose Kind is fixed, with graphics that suggest it: Signal Mast Single
  `CONTROLLED`, `ABSOLUTE` and `PERMISSIVE`, and Signal Mast Double and Dwarf `CONTROLLED`. A fixed Kind is part of
  the symbol's identity, like `Rule251-Left`'s Direction, not a per-instance default. A mast with no Kind is missing.
- **Plates.** The number plate symbol is gone: `PERMISSIVE` means the plate. `Plate-G` (Kind `RULE_290_G`, heavy
  freight only) and `Plate-R` (Kind `RULE_290_R`, all trains) are POLICY symbols. Their pin `To` sits on the mast's
  `SIGNAL` net, and each requires a `PERMISSIVE` mast. The Kind names the resulting indication, Rule 290 [AAR56
  p. 53]; the plate itself modifies a Rule 291 signal [AAR56 p. 54]. No Milepost field: the milepost is already in
  the mast's name.
- **Check, never a source.** A mast that is not `CONTROLLED` whose route passes a powered switch (open C) is reported
  at warning. SP's spring switches in ABS and APB territory are not powered. The check sets nothing. It belongs with the rule checks in `tools/layout_model`.
- **CP Name** is the operations level only: which control point a controlled mast belongs to. Automatic masts state
  none. Which processor drives a mast's lamps comes from the wiring (R13).

Rejected: "a signal is controlled exactly when it states a CP Name". That decided control by inference from a field
that already does another job.

## 6. A joint with a mast on each side (ruled 4)

`IRJ-Signals` is Role `TRACK`, Kind `IRJ_SIGNALS`, with pins A (1), B (2), `SIGNAL_A` (3) and `SIGNAL_B` (4). The
mast on `SIGNAL_A` governs into side A. The mast on `SIGNAL_B` governs into side B.

- Masts are drawn on the engineer's side of the approaching train, to the right of the track. On a schematic that is
  plain by inspection, and nothing is inferred from rotation or from which mast is "first". There is no side field.
- `IRJ-Signal` keeps its one `SIGNAL` pin. ADR 0012 §8's `approach` and `governed` sides stand for it unchanged.
- For a double joint, each mast's `approach` and `governed` sides are derived from its pin. The approach and
  governed names are relative to a mast, not to the joint.

A **signal location** is a block boundary: one joint with its masts, and the track circuits on each side. A control
point is a signal location with one side toward the block.

## 7. Block track and the block's indication (ruled 5)

### 7.1 Drawn, not paired

The block's track is drawn from one control point to the next, across sheets where needed. A hierarchical label
continues the run. Pairing comes from netlist connectivity. Inside CTC a NEXT_CP is no longer needed. It stays for an
interlocking whose neighbour is not drawn.

Consequence for ADR 0009 §3.12's row "track leaves an interlocking only at a NEXT_CP or an END_CTC" (merged in #58): it
covers interlocking track only. Block track belongs to the layout. Dark track beyond an END_CTC is outside both.

### 7.2 The block's one indication

R8: the block reaches the office as one indication. It is a virtual track circuit (`Track Circuit_Virtual`, Style
`virtual`) whose `Members` are the block's circuits: `831T` = [832T, 834T, 836T]. A consumer qualifies it with the
station that sends it, `Corporal:831T` on the model board. By R12 that consumer makes Corporal send `831TK`. The
model states the members and the station named. Whether that station can compute the token is Part 2's (§18.2).
Check: the qualifying station is at one end of the block.

The block's virtual circuit is also the block-clear indication that the office check reads (§16.2). A layout with no
consumer for it sends nothing for it.

The token is not derivable from the H and D a control point receives. With T1 in 836T, Corporal reads H and D
asserted from 832 (832SA's SR, then 834SA's).

## 8. The current of traffic under `RULE_251` (open F)

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

Recommendation: A. Under `RULE_261` the traffic is set at run time (§16). It is not a model fact.

**A `RULE_251` sign inside interlocking limits** states the current of traffic on that track, and nothing more
(owner, 2026-10-31). Watsonville's arrival and departure tracks are switch 837's two legs, between the home joints of
838NCD and 838NAB and the switch. Each leg carries a 251 sign with its direction of travel (Railroad `31954c5`). Such
a sign makes no block, because its piece holds a powered switch (§4), and it marks neither a block limit nor the end
of CTC. The same agreement check applies: the sign's direction against the signals that govern on that track.

## 9. Names by signal location (ruled 13)

- An automatic mast is numbered for its signal location, the milepost in tenths, with its direction letter and head
  letter as for any mast (`grammar.MAST_NAME`): 832SA and 832NA at location 832. No CP Name.
- A circuit between two signal locations is named for the location at its higher-milepost end, whose mast governs
  over it: 832T between 830 and 832. ADR 0003 already numbers a circuit outside interlocking limits for the signal
  that governs over it. No CP Name: block track belongs to the layout.
- A virtual circuit for a block (`831T`) takes any number not used by a signal location. It is the block's name in
  every consumer. A block with no virtual circuit drawn has no name.
- A controlled mast's lever is the number in its name, and its lever direction comes from its direction letter
  (ADR 0003 D1).

Milepost numbers are unique on the layout, so none of these names needs an interlocking qualifier. The names do not
change when the hardware is split differently.

## 10. Boundary track circuits (ruled 14)

Current detection does not see cars with plastic wheels. A detector at the joint, an IR beam for example, keeps the
block a train is leaving occupied until the last car has passed the masts. (MSS, the Modular Signal System, places
its detectors at block boundaries for the same reason.)

- The symbol `Track Circuit IR Boundary` is `Appliance track_circuit`, Style `boundary`, with pins A and B on the two
  nets at a joint. Its name says the technology. The model reads only the Style.
- It has one detected output, wired to a driver pin like any track circuit.
- The derivation states which circuits it counts toward: the circuit on each of its pins. It never splits a circuit
  or ends a block.
- A detector wired straight into the two circuits' inputs in the field is not drawn at all.
- It is named like any circuit (833T in the POC). Its input belongs on the processor that runs its signal location.

## 11. Facts the model carries for Part 2 (ruled 12)

| Fact | Form | Source |
|---|---|---|
| A block's end control points, signal locations in order, member circuits in order | derived, on demand | blocks library (§4) |
| The processor that reads each circuit | relation | the circuit's binding route `processor/address/pin` (ADR 0008), joined on demand |
| The processor that runs each signal location | relation | the bindings of its masts' heads (R13), joined on demand |
| Each station's code line kind | given and relation | the code line's `Kind`; the interlocking's `codeline` (`codeline.encoding`) |
| What a station is (house or interlocking) | reference data | `reference.STATION` |
| Each station's indication budget: free indication bits per code | reference data, with the bus kinds (ADR 0012 §6) | **not present**: `reference.py` has no budget (gap 1) |
| The indications a station already sends | computed on demand | `tools/railroad/codeline.py` (`stations`) |
| Drawn line wires: H, D, traffic-locking | relation | **how they are drawn is open** (gap 3) |
| The transports each processor reaches | given and relation | ADR 0008 (`anchors`; a code line's transport) |

## 12. Derived, and where each result lives

| Result | Where |
|---|---|
| A mast's Kind | `given`, stated |
| ABS, APB or CTC for a block | blocks library, on demand |
| Station-to-station blocks, their circuits, signal locations, rule and current | blocks library, on demand |
| HD lines: producer, consumer, and the processor each runs on | blocks library, on demand |
| The circuits a boundary circuit counts toward | derivation, from the pins |
| Next and approach signals, home and leaving roles | routes library, on demand (ADR 0012 §5.3) |
| A virtual circuit's token on the code line | code line library, by R12 |

# Part 2. Interpretation by consumers

FieldUnit codegen and the FieldUnit runtime.

## 13. The joining rule

If the model is missing or misstating something, codegen can't fix it (R17). Part 2 uses only facts that Part 1
states (§20). It never invents, defaults or repairs a fact, and it never reads KiCad. A fact Part 2 needs and Part 1
does not state is a gap in Part 1 (§21), not a codegen default.

Run-time state is FieldUnit's and is not a model fact: accepted controls, what a mast shows, SRs, `FR` and `FSR`,
timers.

The HD line and traffic rules below are for CTC blocks. APB operation (traffic set by the train at a head block) is
classified (§4) but not specified here.

## 14. Three layers and the operations settings (ruled 6)

| Layer | What it holds | Who chooses |
|---|---|---|
| Operations | The rule (251, 261); the settings below | The layout owner, by railroad and era |
| Model | Blocks, signal locations, HD lines and the rules that produce them; which field unit produces and which consumes each | Railroad-neutral, derived (Part 1) |
| Layout | How H, D and traffic get from one processor to another: no carrier, wires, MQTT topics, the code line | The layout owner's hardware, drawn; chosen by codegen (§18) |

The operations settings:

- whether following moves may fleet (SP had fleeting controls [SP1962]);
- whether an idle block keeps its last traffic (CB&Q) or has none (SP);
- whether the tumble-down starts on the accepted control (CB&Q) or on the cleared signal (SP) (open D);
- whether intermediates are clear at rest (SP).

SP and CB&Q practice from the research shows the model has the right shape. It is not something a layout must copy:
SP did not use microcontrollers or CMRInet. The settings' names and where they live are gap 2.

## 15. The HD line (ruled 7, 8)

### 15.1 What it is

Between neighbouring signal locations there is one HD line for each direction. **An HD line is named for a mast, and
goes to the previous signal in that mast's direction of travel.** It tells that previous signal how far it may let
the next train go, so following traffic does not run into the train ahead. In the picture, `834NA` goes to Sargent's
836NAB, and `836SA` (Sargent's home) goes to 834SA. It carries two values [AAR Dwg 8066]:

- **H** feeds the receiving signal's `HR`: the producer's conditions for permission are all true (§15.3, §15.4).
- **D** feeds the receiving signal's `DR`: the producer's mast in that direction indicates something more favorable
  than Stop or Restricting, so its `HR` is up [CBQ1946 p. 615, `6RAGGPR`; GLOSSARY §10.6]. Stop and Proceed and
  Restricting release D. D is read only while H is asserted.

Track circuits never travel one by one on an HD line. Only what each HD line says travels. On the prototype this is
the line circuit, a chain of two-wire sections fed again at each location [CBQ1946 pp. 613-615], [RS1947 p. 92]. The
model keeps its meaning, not its wiring (§14).

### 15.2 A mast reads the HD line from the location it governs toward

| H | D | The mast may show |
|---|---|---|
| released | ignored | stop |
| asserted | released | approach |
| asserted | asserted | clear |

Each indication is further limited by the mast's own conditions (its route and its SR). With two values, the signal
in rear of a diverging aspect also shows clear (R15).

### 15.3 What a signal location produces

At a signal location L between neighbours U and W, take the mast M at L that governs toward W. Its HD line goes to U,
where the previous signal in M's direction of travel stands:

- **H** is asserted when the circuits between U and L are clear, AND either H from W is asserted or M's SR is set.
- **D** is asserted when M indicates something more favorable than Stop or Restricting.
- **M's SR** (stick relay) is set when a train passes M: the circuits beyond M become occupied while M shows proceed.
  It is released when H from W is asserted again [CBQ1946 pp. 615-616], [RS1927Spray]. Open A: M's governed circuit
  is read on the processor that runs L.

The same rule runs for the other mast and the other direction. At location 832, with M = 832SA:

| Output | H asserted when | D asserted when |
|---|---|---|
| to Corporal (read by 830SAB, 828SA) | 832T clear AND (H from 834 asserted OR 832SA's SR set) | 832SA more favorable than Stop or Restricting |
| to 834 (read by 834NA) | 834T clear AND (H from Corporal asserted OR 832NA's SR set) | 832NA more favorable than Stop or Restricting |

The first part, "H from beyond", chains: a break passes from location to location. That is the tumble-down. The
second part, the SR, keeps following moves possible: it masks a break caused by a train moving away. The SR does not
lock traffic, and it can be stale (§16.1).

Open E: CB&Q also passes each signal's control over back contacts of the same location's opposing `HR` and `SR`
[CBQ1946 p. 613]. This rule does not. No traced scenario shows a safety difference.

### 15.4 What a control point produces

Toward its block, at Corporal:

| | Rule |
|---|---|
| **H out** (HD line `830NAB`, to 832NA) | 832T clear AND the accepted signal controls for 830 and 828 are STOP (neither toward the block) AND neither leaving signal is running time |
| **D out** | Corporal's home, 830NAB, indicates something more favorable than Stop or Restricting |
| **H in** (from 832) | Required by the route equations of 830SAB and 828SA |
| **D in** | Selects approach or clear for 830SAB and 828SA |

The term is the accepted control, not `HSR`: `HSR` drops at knockdown, and the release needs the lever back at STOP
[CBQ1946 p. 616], [AAR8059]. H out releases when the accepted control turns toward the block, before the leaving
signal clears. That is CB&Q's trigger (`4RFR` picked from `RGZ`, CBQ1946 p. 614), and the safer one: the far end is
locked before anything is displayed. SP started it on the cleared signal (open D).

A leaving signal's route equation holds H in and the block's traffic (§16):

```
Corporal:830SAB = (831) 831T1 832T 830(RIGHT) 828(STOP) H_in TRAFFIC(Corporal)
```

`TRAFFIC(Corporal)` is true when the block's traffic is Corporal's, by the means §16.2 or §16.3.

## 16. Traffic (ruled 9)

### 16.1 Why the chain is not enough

The HD chain, with its SRs, does not lock traffic. A stale SR lets two leaving signals clear into one block. Trace
with the rules of §15 alone, POC block Corporal-832-834-Sargent, T0 northward arriving at Corporal:

1. T0 passes 832NA northward. 832NA's SR sets (832T occupied while 832NA showed proceed). Correct.
2. While T0 is still in 832T, the dispatcher lines 830 southward for the next move. H out from Corporal is released,
   and it stays released after T0 clears 832T, because the accepted control is toward the block.
3. 832NA's SR releases only when H from Corporal is asserted again. It never is. The SR is stale.
4. 832 → 834 H = 834T clear AND (H from Corporal OR 832NA's SR): asserted through the stale SR. 834 → Sargent H =
   836T clear AND (H from 832 OR 834NA's SR): asserted. 836NAB's H in is asserted.
5. 830SAB's H in is asserted (Sargent idle), so 830SAB clears southward.
6. Sargent lines 836 northward. 836NAB clears, since its H in is asserted. Two leaving signals are clear into one
   single-track block.

This violates R16 and the release rule. The cause is structural: the SR's OR path bypasses the far control point's
accepted control. Every prototype scheme in the research has a traffic term that no SR bypasses: `FR` in the machine
(AAR Dwg 8066, 8082), field `FSR` at both ends (8082), CB&Q's `4RFR` in the mechanism feed (CBQ1946 pp. 614-616), the
traffic-locking line (Erie 1942, N&W 1949).

### 16.2 Means (a): the office check

As in AAR Dwg 8082. The office holds one traffic relay `FR` for each block. It sets `FR` toward an end control point
only when:

- the block is unoccupied, by the block-clear indication (§7.2, §18);
- the opposing leaving signals at the other end are at stop (no `NGK` or `SGK` for their levers); and
- they are not in time (no `TEK`).

The office sends a control that clears a leaving signal into the block only while `FR` is toward that end. `FR`
releases when the initiating lever is back at STOP and the block-clear indication shows the block clear. Either end
control point may send the block-clear indication; one is enough. When the office is down, no control is sent, and no
traffic is set.

### 16.3 Means (b): a traffic-locking line

As on the Erie (1942) and the N&W (1949). A traffic-locking line runs between the two end control points. It checks
the opposing signals at stop [NW1949 p. 433]. Each signal location between relays it unchanged: never ORed with an
SR.

- An end control point energizes the line toward the far end only when its accepted signal controls toward the block
  are STOP, its leaving signals into the block are at stop and not running time, and it does not hold the traffic.
- A leaving signal into the block requires the line from the far end energized.
- The end that clears a leaving signal holds the traffic in its `FSR` (traffic stick relay). The `FSR` picks when
  its control toward the block is accepted with the line from the far end energized. It releases when its accepted
  controls are back at STOP and the whole block is clear.
- If both ends accept a control at once, neither line is energized and neither signal clears. That is safe. It ends
  when one lever returns to STOP.

The whole-block-clear term at an end comes from the member circuits its processor reads. A member read on another
processor reaches it only over a drawn line, never inferred from H and D (§7.2). How that is drawn is gap 3.

### 16.4 What traffic is not

- Traffic is never a field-to-field inference from H and D.
- Traffic releases only when the initiating lever is back at STOP AND the whole block is clear (owner; [CBQ1946
  p. 616]: "Traffic direction is maintained until the eastbound train is by signal 6LA or 6LB").
- Under the release rule, a lever put to STOP for a following move does not release traffic while the block is
  occupied.

## 17. One train, traced

T1 leaves Corporal for Sargent. The traffic is set by either means. The trigger is the accepted control (open D,
default).

| T1 | 832 → 834 H | 834 → Sargent H | 832 → Corporal H | Effect |
|---|---|---|---|---|
| at Corporal; 830's control toward the block accepted | released (H from Corporal released; no 832NA SR) | released | asserted | Tumble-down: 832NA, 834NA, 836NAB at stop. Traffic Corporal's. 830SAB clears. |
| in 832T | released | released | released (832T occupied) | 836NAB locked by H in and by traffic |
| in 834T | released (834T occupied) | released | asserted (832SA's SR set), D released | A following train: Corporal can clear 830SAB to approach on a new control (lever to STOP, then RIGHT; stick operation). In the STOP moment H out may assert and 832NA may show approach over the empty 832T; harmless. Traffic stays Corporal's. |
| in 836T | asserted once 834T clears and 830's accepted control is back at STOP; released while it is still toward the block | released (836T occupied) | asserted | Sargent stays locked: traffic stays Corporal's until T1 has left the block |
| clear of 836T, 830 at STOP | asserted | asserted | asserted | Traffic released. Intermediates clear both ways at rest (SP setting). |

## 18. The carrier, per block (ruled 10, 11)

### 18.1 What codegen chooses

For each block, codegen chooses the traffic means and the carrier for H, D and the block-clear indication. It chooses
only from Part 1 facts (§11).

### 18.2 AAR MQTT code line

- Traffic: means (a). The block circuits go to the office as indications, each from the station whose processor
  reads it. The office computes block clear from them. The block's virtual circuit token may serve instead when its
  sending station's processor reads every member.
- H and D between processors: an HD line topic, or the intermediates' H and D may follow circuit indications
  broadcast on the code line, where those state every term.

### 18.3 US&S 506 code line

- Traffic: means (a) when either end control point has a free indication bit (one bit per block, from one end; a
  control point may have none, since bits are sparse). The bit is the block's virtual circuit token, so the virtual
  circuit is drawn and the sending end's processor reads every member. Otherwise means (b), a drawn traffic-locking
  line.
- H and D: drawn wires carry the tumble-down to the intermediates.

### 18.4 Electrical and topic forms

Wired H and D (layout):

- Each value is one wire. Asserted is the producer pulling the line to 0 V (open-drain). Released is the producer
  driving nothing, with a pull-up at the consumer holding the line at +V. A common ground joins the two.
- Released is always the restrictive meaning: a broken wire, an unpowered producer or a processor in reset reads as
  stop. This is R14's asserted-low rule.
- A producer stuck at 0 V reads as permissive. The model does not guard against it (R15). A pulsed signal, like coded
  track, is a possible layout option.
- On I2C expander pins, one HD line each way across a segment is four wires plus ground.

HD line topic (MQTT): one topic per HD line, named for its mast: `<root>/hdline/<mast>`, for example
`ctc/SPCoast/hdline/834NA`. The root is the AAR encoding's `Topic` (ADR 0009 §3.10). H and D travel in one message, so
they never disagree: `H D`, `H (D)` or `(H)` (D means nothing while H is released). The message is retained, so a
consumer that restarts reads the current value. The producer's last will is `(H)`, so the broker releases H when the
producer drops off: the pull-up's job. Mast names that govern into a block are unique on the layout (§9), so the
topic needs no qualifier. On multiple track the mast letter tells the tracks apart (834SA and 834SB). Both processors
reach one MQTT transport (§11).

### 18.5 Codegen errors

- A block with no traffic means codegen can build from Part 1 facts.
- An HD line whose producer and consumer run on different processors, with no carrier codegen can name from Part 1
  facts.
- A block-clear indication whose sending station's processor does not read every member.

These are codegen errors. `derive.py` raises none of them (ADR 0012's split).

Where one program runs all the logic (CMRInet, JMRI MQTT, LocoNet or LCC nodes carry the wiring), nothing crosses:
every HD line is local. The distributed pattern (an office unit and field units on one code line, US&S 506 or AAR
MQTT) is the one that needs carriers.

### 18.6 The POC crossing

The blocks library knows which processor runs each signal location (R13) and lists every HD line whose producer and
consumer are on different processors. With the POC wiring (832T, 834T, 830, 832 and 834 on Corporal's processor; 836T
and 836 on Sargent's), only the 834–836 segment crosses:

| HD line (topic) | Produced by | Goes to | H asserted when | D asserted when |
|---|---|---|---|---|
| `836SA`, southbound | Sargent | 834SA, on Corporal's processor | 836T clear AND 836NAB's accepted control at STOP and not running time | 836SA more favorable than Stop or Restricting |
| `834NA`, northbound | location 834, on Corporal's processor | Sargent's 836NAB | 836T clear AND (H from 832 asserted OR 834NA's SR set)[^segment] | 834NA more favorable than Stop or Restricting |

Under open A's default, this wiring is an error: 834SA's governed circuit, 836T, is read on Sargent's processor, not
on the processor that runs location 834.

## 19. Other interpretations

### 19.1 What Kind means to a crew

| Kind | What the crew does at its most restrictive aspect |
|---|---|
| `CONTROLLED` | Stop |
| `ABSOLUTE` | Stop |
| `PERMISSIVE` | Stop, then proceed at restricted speed |

Kind never changes what the signal displays. Every mast shows the same red at its most restrictive [AAR56 p. 51], and
the field unit's logic per mast is the same for all three. The number plate is a fixed part of the aspect, and the
rulebook gives that aspect a different indication: Stop and Proceed instead of Stop. Kind does decide where a block
ends (§4).

### 19.2 Boundary occupancy

The runtime ORs a boundary circuit's occupancy into each circuit that §10 says it counts toward. The processor that
runs its signal location reads it for both of that location's outputs. Because it is ORed into both sides, a train
passing the masts occupies the circuit ahead before it releases the one behind.

## 20. Traceability

Each Part 2 input, the Part 1 section that states it, and its form.

| Part 2 input | Used in | Part 1 | Form |
|---|---|---|---|
| Blocks: end control points, signal locations and member circuits in order | §15, §16, §18 | §4, §11 | derived (blocks library) |
| ABS, APB or CTC for a block | §13 | §4 | derived (blocks library) |
| A mast's Kind | §19.1 | §5 | given |
| A mast's approach and governed sides; the direction it governs | §15 | §6 | derived (from the pins) |
| A control point's leaving signals into the block and home facing it | §15.4, §16 | §4, §12 | derived (routes library) |
| A leaving signal's lever and lever direction | §16.2 | §9 | derived (from the name, ADR 0003) |
| The block's virtual circuit: name and members | §16.2, §18 | §7.2, §9 | given |
| The circuits a boundary circuit counts toward | §19.2 | §10 | derived |
| The processor that reads each circuit | §15.3, §16.3, §18 | §11 | relation |
| The processor that runs each signal location | §18.6 | §11 | relation |
| Each station's code line kind | §18 | §11 | given and relation |
| What a station is (house or interlocking) | §18.3 | §11 | reference data |
| A station's indication budget | §18.3 | §11 | reference data: **gap 1** |
| The indications a station already sends | §18.3 | §11 | computed on demand (`codeline.py`) |
| The indication bits those tokens take (steps per token) | §18.3 | none | **gap 4** |
| Indication tokens for levers (`NGK`, `SGK`, `TEK`) and circuits (`K`) | §16.2 | §11 | reference data (`reference.INDICATION_TOKENS`) |
| Drawn line wires: H, D, traffic-locking, block clear | §16.3, §18 | §11 | relation: **gap 3** |
| The transports each processor reaches | §18.4 | §11 | given and relation |
| The MQTT topic root | §18.4 | ADR 0009 §3.10 | given (AAR encoding `Topic`) |
| The rule and the current of traffic | §14 | §8 | given (sign Kind, Direction); derived per block |
| The operations settings | §14, §15.4, §17 | none | reference data: **gap 2** |
| The layout's railroad, era and rulebook (the key for gap 2) | §14 | ADR 0008 | given |

## 21. Gaps

1. **Indication budget.** Free indication bits per code, by code line kind, are not in the reference data
   (`tools/layout_model/reference.py` has none). GLOSSARY §6 gives 7 indications for 506 and 506A and 35 for 506C;
   AAR MQTT has no limit. To be added with the bus kinds (ADR 0012 §6).
2. **Operations settings** (§14): their names and where they live. The rulebook reference data of ADR 0012 §6 is the
   likely home. Its contents are TBD.
3. **How line wires are drawn:** H and D between processors' driver pins, a traffic-locking line, a block-clear line
   for a member read on another processor. A symbol or seam for them, like the code line's.
4. **Tokens to bits.** `codeline.py` computes tokens; a 506 budget counts steps. The code chart that maps tokens to
   steps is not in the model (GLOSSARY §6: "A token is not a step").
5. **Mixed code lines.** A block whose two end control points are on code lines of different kinds has no carrier
   rule in §18.
6. **Glossary.** No entries for automatic signal, signal location, HD line, station-to-station block, boundary
   circuit, current of traffic, traffic, `SR` as the directional stick, traffic-locking line. `FSR` collides: the
   GLOSSARY (§10.5) uses it for FieldUnit's fleet stick relay; the AAR uses it for the traffic stick relay.
7. Luchessa's and Watsonville's `NFLK` and `SFLK` (board `TRAFFIC` lamps): whether they become the block's traffic
   indication (the office `FR`).
8. Off-layout ends (Lick, Hollister): a block with one end on the layout is reported at info.

## 22. Out of scope

- FieldUnit's implementation of Part 2 (R1): the relay model, approach lighting, time release, aspects.
- The contents of the rulebook reference data.
- APB operation (§13).
- Train order conditions: the reversed number plate, Form Z.
- How a US&S 506 code chart assigns the block-clear bit to a step.
- A common hardware set for a signal location (connector, wiring, PCB carrying the HD lines, detector inputs and mast
  outputs): a layout reference design, not a model fact.

## 23. Consequences

- ADR 0009 §3.10: a mast states Kind; TRACK Kind `IRJ_SIGNALS`; track circuit Style `boundary` (this change), and the
  symbol-field lint accepts a mast's Kind and requires it.
- ADR 0009 §3.12 (merged in #58): the track rule covers interlocking track only, amended in place when this ADR is
  ruled.
- ADR 0012 §5: the blocks library covers the track between control points and serves HD lines. §5.5: the proxy and
  its TBD retire, since a signal never stands in for another; the approach signal of a home is derived.
- GLOSSARY §4 (FieldUnit's): "powered switch" in the interlocking limits entry, if open C is ruled.
- The KiCad importer: a hierarchical label continues a track run (`geometry.run_end` fires on one today);
  `IRJ-Signals` with per-mast sides; `joint.masts` retires for two masts on opposite sides; Style `boundary` (today
  the boundary symbol, with no `TC` pin, is skipped without a word).
- `derive.py`: the mast checks of §5; the circuits a boundary circuit counts toward; NEXT_CP pairing retires inside
  CTC. No transport or carrier checks.
- The schema: a double joint's masts with their sides; a mast's Kind.
- Reference data: the indication budget (gap 1) and the operations settings (gap 2).
- FieldUnit: implements Part 2, including the office `FR` and codegen's carrier choice.

[^rev]: Rewritten 2026-11-01 from the owner's rulings of that day and the second pass of the adversarial review. The
    text before this rewrite is commit `2a456d4`. It named the line signal's values E and P and the passed memory
    "passed memory", let the chain alone set the direction of traffic, and made the code line no transport for line
    signals; each is reversed here. An earlier draft (commit `96d3765`) asked six decisions, since replaced.

[^segment]: 836T is read on Sargent's processor, so with this wiring Sargent ANDs 836T into the value it reads, and
    location 834 sends the rest. Each end of a segment ANDs the part of the segment's occupancy it reads.
