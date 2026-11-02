# 0013. Between control points: blocks, automatic signals, the HD line and traffic

- Status: **accepted by the owner 2026-11-01** (rev 3: three-part structure separating Part 1 normative model facts, Part 2 prototype behavior, and Part 3 non-normative suggestions and context for FieldUnit).[^rev]
- Amends: ADR 0009 §3.10 (a mast states Kind; TRACK Kind `IRJ_SIGNALS`; track circuit Style `boundary`; done in the
  same change), ADR 0009 §3.12's row "track leaves an interlocking" (interlocking track only; merged in #58), ADR 0012
  §5 (the blocks library's scope) and §5.5 (the proxy retires, §23), FieldUnit `docs/GLOSSARY.md` §4 ("powered switch or derail").
- Builds on: `docs/review/abs-apb-research-2026-10-30.md` with the owner's answers of 2026-10-30,
  `docs/review/traffic-locking-research-2026-10-31.md` (first-party sources on traffic locking and line circuits) and
  `docs/review/adr-0013-adversarial-review-2026-10-31.md`. The POC drawing: Railroad
  `2a1696e` (Corporal and Sargent sheets of the SPCoast project).

## Decisions (all ratified 2026-11-01)

1. **Three parts, one ADR.** Part 1 states the normative model facts and domain-library derivations owned by Subdivision.
   Part 2 states the prototype behavior and relay principles (the reference authority). Part 3 records non-normative
   suggestions, context, and selective compressions for FieldUnit when reducing Part 2 to practice from Part 1 facts.
   If the model is missing or misstating something, codegen cannot fix it (§13).
2. **A station-to-station block** is a piece of the track graph cut at every `CONTROLLED` and `ABSOLUTE` signal joint
   that holds no powered switch or derail and lies under a block signal rule (`RULE_251`, `RULE_261`, or `ABSOLUTE`
   ends). Hand-throw, spring, and electrically locked hand-throw switches may lie in a block. It belongs to the layout,
   not to an interlocking, and the `blocks` library computes it on demand (§4).
3. **ABS, APB or CTC is derived, never stated.** APB is derived from `ABSOLUTE` ends alone; a `RULE_261` sign on
   `ABSOLUTE` ends is reported at warning (§4).
4. **A mast states what it is:** `Kind` `CONTROLLED`, `ABSOLUTE` or `PERMISSIVE`. A mast with none is missing. Grade
   and restricting plates are POLICY symbols on the mast's net (§5).
5. **A joint with a mast on each side** is the `IRJ-Signals` symbol: pins A, B, `SIGNAL_A` (its mast governs into A)
   and `SIGNAL_B` (into B). Nothing is read from rotation (§6).
6. **Block track is drawn** from one control point to the next and replaces NEXT_CP inside CTC. The block's one office
   indication is a virtual track circuit whose members are the block's circuits (§7).
7. **A `RULE_251` sign's `LEFT` or `RIGHT`** is the lever direction of the signals that govern with the current of
   traffic. A `RULE_251` sign inside interlocking limits states the current of traffic on that track, and nothing more
   (§8).
8. **Names by signal location:** automatic masts and the circuits between them are numbered for their signal
   location (§9).
9. **A boundary track circuit** (Style `boundary`) is a detector at a joint. The model states which circuits it
   counts toward (§10), and consumers OR its occupancy into them (§19.1).
10. **Facts the model carries for consumers:** blocks with their ends, signal locations, member circuits, and the
    processor that reads each circuit; the processor that runs each signal location; each station's code line kind,
    capacity in steps (reference data), and indications already used; drawn line wires; and the transports each
    processor reaches (§11). Where things live follows ADR 0012's split: `derive.py` raises no transport or carrier
    errors (§12).
11. **Three layers:** operations (a railroad's rules and era), the model (railroad-neutral, Part 1) and the layout (the
    owner's hardware). Prototype practice (Part 2) is the authority for behavior, never a hardware wiring mandate (§14).
12. **Prototype HD line and traffic locking (Part 2):** between neighbouring signal locations, one **HD line** per
    direction carries two values: `H` feeds the receiving signal's `HR`, and `D` feeds its `DR` (AAR Dwg 8000, 8066; AAR
    nomenclature, 1946). The directional stick relay is `SR`. Because the `OfficeUnit` is non-vital and never blocks
    controls (GLOSSARY §2.3) while the vital `FieldUnit` rejects any unsafe control transaction (FieldUnit ADR 0002
    Rule 2), the `HD` chain locks traffic in the field without an office gate (§15, §16).

# Part 1. Model facts (normative)

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
| R1 | Subdivision owns no vital logic. Field units run FieldUnit's interlocking logic. Part 1 states the model facts; Part 2 states the prototype behavior; Part 3 gives non-normative context for FieldUnit. | AGENTS.md | model |
| R2 | A rule that reads a symbol stands for a fact that lives elsewhere. Find the fact. | ADR 0001 D15 | model |
| R3 | Each fact has one source. | AGENTS.md | model |
| R4 | Where a relationship has an explicit form, it is stated or it is missing. | ADR 0012 §4 | model |
| R5 | Domain libraries write nothing into the file. | ADR 0012 §5 | model |
| R6 | A control point is a place with controlled absolute signals. Interlocking limits are the track between opposing home signals: cut the track graph at every controlled signal, and each piece with a powered switch or derail is an interlocking. | GLOSSARY §4 | model |
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
| R17 | If the model is missing or misstating something, codegen cannot fix it. | owner 2026-11-01 | model |
| R18 | The OfficeUnit is non-vital and never blocks a control; the FieldUnit is vital and ignores every vital control in an unsafe transaction. | GLOSSARY §2.3; FieldUnit ADR 0002 | model |

## 4. The station-to-station block (decisions 2, 3)

Cut the track graph at every `CONTROLLED` and `ABSOLUTE` signal joint. Each piece that holds no powered switch or
derail and lies under a block signal rule (`RULE_251`, `RULE_261`, or `ABSOLUTE` ends) is one station-to-station block.
A powered switch has a machine (`Style` `powered` or `dual`) or a `CP Name`. A hand-throw switch (`manual`,
`manual_sensed`), a spring switch, and an electrically locked hand-throw switch (`lock`) may lie in a block. A block
holds:

- its track circuits, in order;
- its signal locations and their masts, in order;
- at each end, the control point's leaving signals into it (or `ABSOLUTE` head-block signals) and its home signal facing it;
- its rule and, under `RULE_251`, its current of traffic (§8).

A piece under `RULE_105` or `RULE_93` alone is a siding or station track. A piece that reaches an END_CTC leads to
unsignalled track. Neither is a station-to-station block.

The block belongs to no interlocking. The `blocks` library computes it on demand (R5). Its track is drawn across sheets
(§7.1), so no pairing is needed.

**ABS, APB or CTC is derived, never stated.** It is a property of the block, read from facts already drawn: the
masts' Kinds at its ends and between, and its sign.

| Ends | Intermediate masts | Sign | The block is |
|---|---|---|---|
| `CONTROLLED` | none, or all `PERMISSIVE` | `RULE_261` | CTC, with automatic intermediate signals where drawn (Corporal to Sargent) |
| `ABSOLUTE` head blocks | none, or all `PERMISSIVE` | none (or any; `RULE_261` warns) | APB |
| any | none, or all `PERMISSIVE` | `RULE_251` | ABS, one current of traffic |

The APB row is derived from the `ABSOLUTE` ends alone. The policy sign states movement authority, not the signal
circuit method. Standard Code Rule 261 gives signal-indication authority in both directions, whereas an automatic
signal gives no authority (R10). Therefore, a `RULE_261` sign on `ABSOLUTE` ends is reported at warning (allowing a
deliberate prototype exception such as SP's Oxnard to Montalvo special rules without rejecting the file).

## 5. What a mast is (decision 4)

A mast states `Kind`: `CONTROLLED` (the dispatcher controls it; it belongs in a control point), `ABSOLUTE` (automatic
and absolute, an APB head block) or `PERMISSIVE` (automatic and permissive, with a number plate). Kind is a model fact.
What it means to a crew is in Part 2 (§15.5).

- **Representation.** The library has symbols whose Kind is fixed, with graphics that suggest it: Signal Mast Single
  `CONTROLLED`, `ABSOLUTE` and `PERMISSIVE`, and Signal Mast Double and Dwarf `CONTROLLED`. A fixed Kind is part of
  the symbol's identity, like `Rule251-Left`'s Direction, not a per-instance default. A mast with no Kind is missing.
- **Plates.** The number plate symbol is gone: `PERMISSIVE` means the plate. `Plate-G` (Kind `RULE_290_G`, heavy
  freight only) and `Plate-R` (Kind `RULE_290_R`, all trains) are POLICY symbols. Their pin `To` sits on the mast's
  `SIGNAL` net, and each requires a `PERMISSIVE` mast. The Kind names the resulting indication, Rule 290 [AAR56
  p. 53]; the plate itself modifies a Rule 291 signal [AAR56 p. 54]. No Milepost field: the milepost is already in
  the mast's name.
- **Check, never a source.** A mast that is not `CONTROLLED` whose route passes a powered switch or derail is reported
  at warning. SP's spring switches and hand-throw switches in ABS and APB territory are not powered. The check sets
  nothing. It belongs with the rule checks in `tools/layout_model`.
- **CP Name** is the operations level only: which control point a controlled mast belongs to. Automatic masts state
  none. Which processor drives a mast's lamps comes from the wiring (R13).

Rejected: "a signal is controlled exactly when it states a CP Name". That decided control by inference from a field
that already does another job.

## 6. A joint with a mast on each side (decision 5)

`IRJ-Signals` is Role `TRACK`, Kind `IRJ_SIGNALS`, with pins A (1), B (2), `SIGNAL_A` (3) and `SIGNAL_B` (4). The
mast on `SIGNAL_A` governs into side A. The mast on `SIGNAL_B` governs into side B.

- Masts are drawn on the engineer's side of the approaching train, to the right of the track. On a schematic that is
  plain by inspection, and nothing is inferred from rotation or from which mast is "first". There is no side field.
- `IRJ-Signal` keeps its one `SIGNAL` pin. ADR 0012 §8's `approach` and `governed` sides stand for it unchanged.
- For a double joint, each mast's `approach` and `governed` sides are derived from its pin. The approach and
  governed names are relative to a mast, not to the joint.

A **signal location** is a block boundary: one joint with its masts, and the track circuits on each side. A control
point is a signal location with one side toward the block.

## 7. Block track and the block's indication (decision 6)

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
model states the members and the station named. Check: the qualifying station is at one end of the block. A layout
without a consumer for the block's virtual circuit sends nothing for it.

When a member of `Corporal:831T` (`836T`) is wired to the neighbouring interlocking's processor (Sargent), `831T` is a
cross-interlocking consumer of `Sargent:836TK` (ADR 0011). By R12, that causes Sargent to include `836TK` in its
codeline indications (where the code line has capacity, §18.1), so Corporal can compute `831TK` without inferring
occupancy from `H` and `D` (which `834SA`'s `SR` masks while a southbound train occupies `836T`).

## 8. The current of traffic under `RULE_251` (decision 7)

| Sign | Kind | `Direction` |
|---|---|---|
| `Rule251-DoT-Left`, `Rule251-DoT-Right` | `RULE_251` | `LEFT`, `RIGHT` |
| `Rule261-DoT-BiDirectional` | `RULE_261` | `BOTH` |
| `Rule105-RestrictedSpeed`, `Rule93-Yard Limits` | `RULE_105`, `RULE_93` | `BOTH` |

`BOTH` adds nothing to its Kind. The 251 sign's `LEFT` or `RIGHT` is the lever direction of the signals that govern
with the current of traffic (GLOSSARY §7; ADR 0003 D1 maps `N`/`W` to `LEFT` and `S`/`E` to `RIGHT`). SPCoast agrees:
`Christopher:1NAT` and `Corporal:1SAT` both state `RIGHT`, and trains with the current arrive at a `RIGHT` signal at
Corporal. The `blocks` library checks that the signs of one block agree with each other and with its masts. Under
`RULE_261` the direction of traffic is set at run time (§16) and is not a static model fact.

**A `RULE_251` sign inside interlocking limits** states the current of traffic on that track, and nothing more
(owner, 2026-10-31). Watsonville's arrival and departure tracks are switch 837's two legs, between the home joints of
838NCD and 838NAB and the switch. Each leg carries a 251 sign with its direction of travel (Railroad `31954c5`). Such
a sign makes no block, because its piece holds a powered switch (§4), and it marks neither a block limit nor the end
of CTC. The same agreement check applies: the sign's direction against the signals that govern on that track.

## 9. Names by signal location (decision 8)

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

## 10. Boundary track circuits (decision 9)

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

## 11. Facts the model carries for consumers (decision 10)

| Fact | Form | Source |
|---|---|---|
| A block's end control points, signal locations in order, member circuits in order | derived, on demand | `blocks` library (§4) |
| The processor that reads each circuit | relation | the circuit's binding route `processor/address/pin` (ADR 0008), joined on demand |
| The processor that runs each signal location | relation | the bindings of its masts' heads (R13), joined on demand |
| Each station's code line kind | given and relation | the code line's `Kind`; the interlocking's `codeline` (`codeline.encoding`) |
| What a station is (house or interlocking) | reference data | `reference.STATION` |
| Each station's capacity: controls and office indications per field station, in steps | reference data | `reference.CODE_LINE_CAPACITY` (by code line type; set by the physical machine) |
| Steps a station already uses | computed on demand | its appliances (`tools/railroad/codeline.py`) times their steps (`reference.CODE_LINE_STEPS`) |
| The indications a station already sends | computed on demand | `tools/railroad/codeline.py` (`stations`) |
| Drawn line wires: H, D, traffic-locking | relation | **how they are drawn is open** (gap 3) |
| The transports each processor reaches | given and relation | ADR 0008 (`anchors`; a code line's transport) |

## 12. Derived, and where each result lives

| Result | Where |
|---|---|
| A mast's Kind | `given`, stated |
| ABS, APB or CTC for a block | `blocks` library, on demand |
| Station-to-station blocks, their circuits, signal locations, rule and current | `blocks` library, on demand |
| HD lines: producer, consumer, and the processor each runs on | `blocks` library, on demand |
| The circuits a boundary circuit counts toward | derivation, from the pins |
| Next and approach signals, home and leaving roles | `routes` library, on demand (ADR 0012 §5.3) |
| A virtual circuit's token on the code line | `codeline` library, by R12 |

# Part 2. Prototype behavior and relay principles (reference authority)

Order of authority #1 (`AGENTS.md`): how the prototype relay circuits and operating rules work between control points.
Part 2 states the behavioral truth that `FieldUnit` models.

## 13. The seam between the data model and `FieldUnit`

If the model is missing or misstating something, codegen cannot fix it (R17). Consumers read only facts that Part 1
states (§20) plus reference data; they never read KiCad or invent missing topology.

Run-time state belongs to `FieldUnit` and is never stored in the Layout Data Model File: accepted controls (`HSR`),
what a mast displays (`HR`, `DR`), directional stick relays (`SR`), and approach/time locking timers (`ASR`).

## 14. Three layers and the operations settings (decision 11)

| Layer | What it holds | Who chooses |
|---|---|---|
| Operations | The rule (251, 261); the railroad and era settings below | The layout owner, by railroad and era |
| Model | Blocks, signal locations, directed HD links, and which processor reads or drives each | Railroad-neutral, derived (Part 1) |
| Layout | How H, D and occupancy get from one processor to another: in-memory, wires, MQTT topics, or the code line | The layout owner's hardware and `FieldUnit` codegen (Part 3) |

Prototype railroads differed in four operations settings:

- whether following moves may fleet (SP had fleeting controls [SP1962]);
- whether an idle single-track block keeps its last direction of traffic (CB&Q [CBQ1946]) or has none at rest (SP [RS1942]);
- whether the opposing tumble-down starts when the leaving signal control is accepted (CB&Q [CBQ1946 p. 614]) or when the leaving signal clears (SP [RS1942]);
- whether intermediate signals stand clear in both directions at rest (SP) or only in the established direction.

## 15. The HD line and the directional stick relay (`SR`) (decision 12)

### 15.1 What an HD line carries

Between neighbouring signal locations there is one **HD line** for each direction. **An HD line is named for a mast,
and goes to the previous signal in that mast's direction of travel.** It tells that previous signal how far it may let
the next train go, so following traffic does not run into the train ahead. In the picture (§2), `834NA` goes to
Sargent's `836NAB`, and `836SA` (Sargent's home) goes to `834SA`. On the prototype this is a chain of two-wire
polarized line circuits fed again at each signal location [AAR Dwg 8000, 8066; CBQ1946 pp. 613-615; RS1947 p. 92].
Logically it carries two values:

- **`H`** feeds the receiving signal's home relay (`HR`): the producer's conditions for permission into the segment
  are all true (§15.3, §15.4).
- **`D`** feeds the receiving signal's proceed-indication relay (`DR`): the producer's mast in that direction
  indicates Approach or better (something more favorable than Stop, Stop and Proceed, or Restricting, so its own `HR`
  is picked up) [CBQ1946 p. 615, `6RAGGPR`; GLOSSARY §10.6]. `D` is read only while `H` is asserted.

### 15.2 How a mast reads the HD line from the location ahead

| `H` | `D` | The mast may show |
|---|---|---|
| released | ignored | Stop (or Stop and Proceed on a `PERMISSIVE` mast) |
| asserted | released | Approach |
| asserted | asserted | Clear |

Each indication is further limited by the mast's own route conditions (`GLOSSARY.md` §10.6).

### 15.3 What an intermediate signal location produces

At a signal location `L` between neighbours `U` and `W`, take the mast `M` at `L` that governs toward `W`. Its HD line
goes back to `U`, where the previous signal in `M`'s direction of travel stands:

- **`H`** is asserted when the track circuits between `U` and `L` are clear, AND either `H` from `W` is asserted or
  `M`'s directional stick relay (`SR`) is picked up.
- **`D`** is asserted when `M` indicates Approach or better (more favorable than Stop, Stop and Proceed, or Restricting).
- **`M`'s `SR` (directional stick relay)** picks up when a train passes `M` in `M`'s governing direction (the circuit
  beyond `M` becomes occupied while `M` is cleared to proceed, before `M`'s slow-release `HR` drops) and sticks
  through its own front contact and `M`'s `HR` back contact until `H` from `W` is asserted again [CBQ1946 pp. 615-616;
  RS1927Spray pp. 269-270].

The same rule runs symmetrically for the opposing mast at `L`. At location 832, with `M` = `832SA`:

| Output | `H` asserted when | `D` asserted when |
|---|---|---|
| to Corporal (read by `830SAB`, `828SA`) | `832T` clear AND (`H` from 834 asserted OR `832SA`'s `SR` set) | `832SA` Approach or better |
| to 834 (read by `834NA`) | `834T` clear AND (`H` from Corporal asserted OR `832NA`'s `SR` set) | `832NA` Approach or better |

The first term (`H` from ahead) chains: a break passes from location to location from one end of the block to the
other. That is the **tumble-down**. The second term (`M`'s `SR`) enables following moves: it masks the break ahead
when that break was caused by a train moving away in `M`'s direction.

### 15.4 What a control point produces toward its block

Toward its block, at Corporal:

| Port | Prototype rule |
|---|---|
| **`H` out** (HD line `830NAB`, to `832NA`) | `832T` clear AND neither `830` nor `828` is controlled toward the block AND neither leaving signal is running time (`ASR` up) |
| **`D` out** | Corporal's home facing the block (`830NAB`) indicates Approach or better |
| **`H` in** (from `832SA`) | Required in the `HR` route equations of leaving signals `830SAB` and `828SA` |
| **`D` in** (from `832SA`) | Feeds `DR` to select Approach versus Clear for `830SAB` and `828SA` |

### 15.5 What a mast's `Kind` means to a crew

| Kind | Most restrictive rulebook indication | What the crew does at its most restrictive aspect |
|---|---|---|
| `CONTROLLED` | Stop (Rule 292) | Stop and stay |
| `ABSOLUTE` | Stop (Rule 292) | Stop and stay |
| `PERMISSIVE` | Stop and Proceed (Rule 291; Rule 290 with `Plate-G` or `Plate-R`) | Stop, then proceed at restricted speed (or proceed at restricted speed without stopping under a grade/restricting plate) |

`Kind` never changes what lamps or blade positions the signal displays at its most restrictive aspect [AAR56 p. 51].
The number plate is a physical marker on the mast that changes the rulebook indication of the red aspect from Rule 292
to Rule 291.

## 16. How the vital field and the HD chain enforce traffic locking (decision 12)

### 16.1 Why the non-vital office and the vital field work together without a stale `SR`

Two foundational rules of the architecture (`GLOSSARY.md` §2.3 and `FieldUnit` ADR 0002 Rule 2; R18) govern how a
control point interacts with the `HD` chain:

1. **The `OfficeUnit` is non-vital.** Levers on the CTC machine move freely. When the dispatcher presses `CODE`, the
   office sends the control transaction unconditionally; it never blocks or filters controls from its own copy of
   field state.
2. **The `FieldUnit` is vital.** When a control transaction arrives at a field unit, the field unit checks whether the
   requested route is safe (`OS` clear, block entrance circuit `832T` clear, switches in correspondence, opposing
   signals at stop, and `H in` from the block asserted). If any safety condition is false, the field unit **ignores
   every vital control in the transaction**. Its accepted control state does not change.

Because the field unit rejects unsafe controls, an opposing `SR` can never become stale:

- For `832NA`'s `SR` to pick up when a northbound train `T0` enters `832T`, `832NA` must have been at Proceed, which
  requires Corporal's `H out` to have been asserted (meaning Corporal had no active southward control and no time
  running when `T0` entered `832T`).
- While `T0` approaches in `834T` or occupies `832T`, Corporal's `H in` or `832T` is de-energized, so Corporal's vital
  field unit **rejects** any southward control transaction coded by the dispatcher. Corporal's southward control stays
  at `STOP`.
- The moment `T0` clears `832T` into Corporal's `OS` (`831T1`), `832T` is clear and Corporal's southward control is
  still at `STOP`, so Corporal's `H out` immediately re-asserts and releases `832NA`'s `SR`.

Therefore, on SP-style two-wire `HD` line circuits ([RS1942], [RS1947]), **the `HD` chain alone locks traffic in the
field**:
```
Corporal:830SAB = (831) 831T1 832T 830(RIGHT) 828(STOP) H_in
```
No office gate and no separate traffic-locking wire are required where the `HD` chain runs end to end. Other prototype
families (such as Erie 1942 and N&W 1949 on multi-track, or AAR Dwg 8059/8082 on coded track without line wires) used
a dedicated traffic-locking line or field `FSR` relays set by code steps; see Part 3 (§18).

### 16.2 One train, traced

Southbound train `T1` leaves Corporal for Sargent:

| `T1` position | `832 → 834 H` | `834 → Sargent H` | `832 → Corporal H` | Operational effect |
|---|---|---|---|---|
| At Corporal; `830` southward control accepted | released (`H` from Corporal released; no `832NA` `SR`) | released | asserted | Tumble-down: `832NA`, `834NA` go to Stop; Sargent's `836NAB` is locked out (`H in` released); `830SAB` clears. |
| In `832T` (`830SAB` knocks down to Stop) | released (`832T` occupied) | released | released (`832T` occupied) | `830SAB` is at Stop; Sargent's `836NAB` stays locked out. |
| In `834T` (`832T` clear) | released (`834T` occupied) | released | asserted (`832SA`'s `SR` picked up), `D` released | Corporal can clear `830SAB` to Approach for a following move; Sargent's `836NAB` stays locked out (`834 → Sargent H` released). |
| In `836T` (`834T` clear) | asserted (once Corporal's southward control is at `STOP`) | released (`836T` occupied) | asserted (`834SA`'s `SR` picked up), `D` asserted | `832SA` clears to Clear; Sargent's `836NAB` stays locked out by `836T` occupancy until `T1` clears `836T`. |
| Clear of `836T` (into Sargent) | asserted | asserted | asserted | Block idle; intermediates clear both ways at rest (SP setting), and either CP may clear a leaving signal. |

# Part 3. Suggestions and context for `FieldUnit` (non-normative)

Engineering context, selective compressions (R15), and implementation options that `FieldUnit` and its code generators
may use when reducing Part 2 to practice from Part 1's data model. Nothing in Part 3 constrains the Layout Data Model
File or `derive.py`.

## 17. Relay model options and selective compressions for `FieldUnit`

1. **When a leaving signal control releases `H out` (`HSR` knockdown vs. sticky lever direction):**
   - Under `GLOSSARY.md` §10.5, a signal's `HSR` picks up when the field unit accepts a `LEFT` or `RIGHT` control and
     drops automatically when the train enters the route (`knockdown()`), unless fleeting (`FSR`) is active.
   - If `FieldUnit` drives `H out` from `!HSR` (plus `832T` clear and `ASR` up), traffic unlocks automatically as soon
     as the train clears the last circuit of the block (`836T` in §16.2), without requiring the dispatcher to press
     `CODE` at the departure CP to send a redundant `HS` control after a passed train.
   - If a railroad's operations setting (§14) requires the dispatcher to explicitly code `STOP` (`HS`) before traffic
     can reverse (CB&Q [CBQ1946 p. 616]), `FieldUnit` can hold a separate accepted-direction latch that resets on
     `HS`.
2. **Tumble-down trigger (accepted control vs. cleared signal):**
   - Dropping `H out` as soon as the leaving control is accepted (CB&Q `RGZ` trigger) locks the far end before the
     leaving signal displays Proceed. Dropping `H out` when the leaving signal clears (`HR` up, SP trigger) behaves
     identically whenever the block is initially idle.
3. **Same-location opposing cut (CB&Q fidelity):**
   - CB&Q [CBQ1946 p. 613] also passes each intermediate mast's control over back contacts of the opposing mast's `HR`
     and `SR` at the same double location (`832NA` held at Stop while `832SA`'s `SR` is up). It changes no safety
     outcome in the traced scenarios, only whether an opposing intermediate behind a receding train clears to Approach
     before or after the train clears the next section.
4. **Two-value `HD` compression on diverging routes (R15):**
   - With two values (`H` and `D`), a home signal showing `DIVERGING_CLEAR` or `DIVERGING_APPROACH` asserts `D`, so the
     approach signal in rear shows `CLEAR` rather than `APPROACH_MEDIUM`. That matches standard three-aspect signaling
     and avoids a third line value unless four-aspect coding is needed later.

## 18. Four deployment variations, what is drawn, and the POC 834–836 split

### 18.1 Four deployment variations and what is drawn for each

Across all four variations, **the trackplan drawing is identical**: the block track is drawn from one control point to
the next (with a hierarchical label where it crosses sheets, §7.1), with its `IRJ-Signals` / `IRJ-Signal` joints, its
`PERMISSIVE` (or `ABSOLUTE`) masts and heads, its track circuits (`832T`, `834T`, `836T`), any `boundary` detector
(`833T`), its `RULE_251` or `RULE_261` sign, and the block's `virtual` track circuit (`831T`) where the model board
displays the block.

Only the hardware / processor / codeline bindings differ:

| Variation | What is drawn on the sheets | How `FieldUnit` exchanges state across the block |
|---|---|---|
| **A. AAR codeline only between distributed `FieldUnit`s (preferred distributed form)** | Each interlocking connects to the shared AAR `Codeline` encoding and to its own field `Processor`. Each block track circuit and intermediate head device connects to a driver on whichever field `Processor` physically serves it. **No extra `HD` line symbols, topics, or cross-processor wires are drawn.** | **Codeline indication eavesdropping.** Each `FieldUnit` subscribes to the neighbouring station's codeline `Indication` messages on the shared code line. Because the far station's leaving/home signal indications (`NGK`, `SGK`, `TEK`) and remote block circuit indications (`TK`, included automatically by R12 when consumed by the neighbour's block or virtual circuit) are broadcast as codeline indications, each processor has every fact needed to evaluate its `HD` chain, `SR` sticks, and virtual block circuit (`831T`) locally—negating any separate `HD` lineset or `<root>/hdline/<mast>` topic. |
| **B. Physical `H`/`D` wire pairs between distributed `FieldUnit`s** | Each interlocking has its own field `Processor`. At the segment that crosses between two processors, four I/O driver pins (two open-drain outputs and two pull-up inputs on each processor: `H` and `D` each way, active-low per R14) are wired between the two processors' drivers (gap 3). Each mast's governed track circuit is wired to the processor that runs that mast's signal location. | **Wired `HD` cascade.** Each processor evaluates its local `HD` segments and drives the physical `H` and `D` wires across the boundary. A broken wire, unpowered producer, or processor in reset reads as released (`Stop`). |
| **C. Unified field logic system (CMRInet Host, JMRI, or `spcoast_virtual_plant`)** | Every interlocking's `Processor` pin connects to the **same** `Processor` entity (e.g., the CMRInet Host), and all field I/O drivers (`Driver-CMRInet-Node` `IB`/`OB`, JMRI drivers) attach to that processor's bus. **No cross-processor wires or extra topics are drawn.** | **In-memory.** The `blocks` library (§11) resolves every circuit and signal location in the block to the same processor, so `FieldUnit` evaluates every `HD` link, `SR` stick, and virtual circuit (`831T`) directly in memory. |
| **D. US&S 506 code line with a 1- or 2-circuit ABS/APB link** | Both interlockings connect to a `USS506` (7 indication steps per station) or `USS506C` (35 steps) `Codeline` encoding. Track circuits and head devices connect to their local field `Processor`'s drivers. | **Codeline eavesdropping up to step capacity; wired `HD` beyond it.** A standard 1-switch, 1-signal, 1-OS, 1-MC station uses 6 of its 7 indication steps, leaving 1 free step (`reference.CODE_LINE_CAPACITY`, `CODE_LINE_STEPS`). For a **1-circuit block** (one station sends its `TK` in its free step) or a **2-circuit block** (each end station sends its side's `TK` in its 1 free step), each `FieldUnit` eavesdrops on the other station's 506 indication code (`NGK`, `SGK`, `TEK`, `TK`) on the two-wire code line with **no extra field wires** (same mechanism as Variation A). Only when a block has more circuits than the two stations' free 506 indication steps must intermediate segments use Variation B (wired `H`/`D`) or an MQTT `HD` topic. |

### 18.2 How codeline indication eavesdropping works on the POC 834–836 split (Variations A and D)

In the POC between Corporal and Sargent (`832T`, `834T`, and locations `830`, `832`, `834` on Corporal's processor;
`836T` and location `836` on Sargent's processor), the boundary between processors falls between location `834` and
circuit `836T`:

| Direction | Needed by consumer | Provided by codeline eavesdropping (Variations A & D) | Provided by wired `HD` / topic (Variation B) |
|---|---|---|---|
| Sargent $\to$ Corporal | `834SA` (needs `836SA`'s `H`, `D`, and `836T` for `834SA`'s `SR`) and `Corporal:831T` (needs `836T`) | Sargent's codeline indications `836NGK` (leaving `836NAB`), `836SGK` (home `836SA`), `836TEK` (time), and `836TK` (circuit `836T`). Corporal computes `836SA` `H` = `!836TK && !836NGK && !836TEK`, `D` = `836SGK`, sets `834SA`'s `SR` directly from `836TK`, and computes `831TK` = `832T || 834T || 836TK`. | `836SA` `H` and `D` on two wires (or `<root>/hdline/836SA`); `834SA`'s `SR` uses the local `834T` approach-circuit guard (§18.3 item 1). |
| Corporal $\to$ Sargent | Sargent's leaving signal `836NAB` (needs `834NA`'s `H` and `D`) | Corporal's codeline indications `830SGK`, `830TEK`, `828SGK`, `828TEK`, `830NGK`, `832TK`, and `834TK`. Sargent has the complete occupancy progression (`832TK`, `834TK`, `836T`) and Corporal's signal state to evaluate `834NA`'s `H` and `D` locally. | `834NA` `H` and `D` on two wires (or `<root>/hdline/834NA`), with Sargent ANDing its local `836T` into `H`. |

### 18.3 Four implementation details `FieldUnit` codegen should watch

1. **Picking up `834SA`'s `SR` across a processor boundary:**
   - Under **Variations A, C, and D (1–2 circuits)**, Corporal's processor has `836T` occupancy directly (in memory or
     via `Sargent:836TK` on the code line), so `834SA`'s `SR` picks up by the standard §15.3 rule (`836T` occupied while
     `834SA` shows Proceed).
   - Under **Variation B** (where only `H` and `D` cross on wires and `836T` is not on Corporal's processor), Corporal
     cannot set `834SA`'s `SR` from "`836SA` `H` dropped while `834SA` showed Proceed" alone, because `836SA` `H` also
     drops when Sargent clears `836NAB` into an idle block. There, `FieldUnit` can either require each mast's governed
     circuit to be wired to its location's processor, or use the **approach-circuit guard (R15 compression)**: set `M`'s
     `SR` when `M` shows Proceed, **`M`'s local approach circuit (`834T`) is occupied**, and `H` from ahead (`836SA`)
     drops (which also guards pure APB mode).
2. **Computing the virtual block circuit (`Corporal:831T = [832T, 834T, 836T]`):**
   - Under **Variations A, C, and D**, Corporal has `836TK` from Sargent's codeline indications (or in memory) and sends
     `831TK` directly.
   - When a 506 station has no free step for a multi-circuit block, either all members of `831T` are wired to the
     sending station's processor, or the model board lamp consumes each station's local portion (`Corporal:831T` +
     `Sargent:836T`).
3. **Electrical and dedicated-topic carrier forms (when codeline eavesdropping is not used):**
   - **Wired `H` and `D` (Variation B, active-low per R14):** Each value is one open-drain wire pulled to 0 V when
     asserted and held at +V by a consumer pull-up when released (four wires plus common ground for a bidirectional
     segment on I2C expander pins).
   - **Dedicated MQTT `HD` topic (optional alternative to Variation A):** One retained topic per `HD` line,
     `<root>/hdline/<mast>` (for example `ctc/SPCoast/hdline/834NA`, where `<root>` is the AAR encoding's `Topic`),
     carrying `H D`, `H (D)`, or `(H)` in a single payload with a last-will message of `(H)`.
4. **Settle the `HD` chain before evaluating controls:**
   - When a train clears the last circuit of a block (`836T` at Sargent), the receding-direction stick (`834SA`'s `SR`)
     releases only when `836SA`'s `H out` re-asserts (`836T` clear and `836NAB` not controlled toward the block).
   - On relays, `836T` picking up re-asserts `836SA` `H out` and drops `834SA`'s `SR` in milliseconds (AAR Dwg 8066
     Sheet 2 also makes `3RFR` slow pick-up so the approach signal's `SR` releases before traffic reverses).
   - In a software scan loop, if `836T` clearing and a queued northward control for `836NAB` land in the same scan and
     the control is evaluated first, `836SA` `H out` stays released (switching directly from held-low-by-`836T` to
     held-low-by-`836NAB`) and `834SA`'s `SR` never sees the release pulse. After any circuit or `H in` change,
     `FieldUnit` should settle the `HD` chain before evaluating a control transaction.

## 19. Other consumer notes

### 19.1 Boundary track circuit occupancy (decision 9)

A consumer ORs a boundary circuit's occupancy into each circuit that Part 1 (§10) says it counts toward. Because the
boundary circuit (`833T`) is ORed into the circuits on both sides of the joint (`832T` and `834T`), a train passing the
masts occupies the circuit ahead before it releases the circuit behind (make-before-break).

## 20. Traceability

Each consumer input, the Part 1 section that states it, and its form:

| Consumer input | Used in | Part 1 | Form |
|---|---|---|---|
| Blocks: end control points, signal locations and member circuits in order | §15, §16, §18 | §4, §11 | derived (`blocks` library) |
| ABS, APB or CTC for a block | §13, §14 | §4 | derived (`blocks` library) |
| A mast's Kind | §15.5 | §5 | given |
| A mast's approach and governed sides; the direction it governs | §15 | §6 | derived (from the pins) |
| A control point's leaving signals into the block and home facing it | §15.4, §16 | §4, §12 | derived (`routes` library) |
| A leaving signal's lever and lever direction | §15.4 | §9 | derived (from the name, ADR 0003) |
| The block's virtual circuit: name and members | §7.2, §18.1, §18.3 | §7.2, §9 | given |
| The circuits a boundary circuit counts toward | §19.1 | §10 | derived |
| The processor that reads each circuit | §18 | §11 | relation |
| The processor that runs each signal location | §18 | §11 | relation |
| Each station's code line kind, capacity, and steps | §11, §18.1 | §11 | given, relation, and reference data |
| Drawn line wires | §18.1 | §11 | relation: **gap 3** |
| The transports each processor reaches | §18.1 | §11 | given and relation |
| The MQTT topic root | §18.3 | ADR 0009 §3.10 | given (AAR encoding `Topic`) |
| The rule and the current of traffic | §14 | §8 | given (sign Kind, Direction); derived per block |
| The operations settings | §14, §17 | none | reference data: **gap 2** |
| The layout's railroad, era and rulebook (the key for gap 2) | §14 | ADR 0008 | given |

## 21. Gaps

1. Closed 2026-11-01: capacity by code line type is reference data (`reference.CODE_LINE_CAPACITY`). A station's
   free steps are its capacity less the steps its appliances use (§11).
2. **Operations settings** (§14): their names and where they live. The rulebook reference data of ADR 0012 §6 is the
   likely home. Its contents are TBD.
3. **How line wires are drawn:** `H` and `D` between processors' driver pins, a traffic-locking line, or a block-clear
   line for a member read on another processor. A symbol or seam for them, like the code line's.
4. Closed 2026-11-01: a token is symbolic and a step is a pulse on the line (FieldUnit GLOSSARY §6). The code line
   type maps each appliance class to steps (`reference.CODE_LINE_STEPS`). On US&S 506 a switch takes two steps each
   way; a signal lever three controls (`NGS`, `SGS`, `HS`: the explicit stop has its own step) and three indications;
   a circuit or a maintainer call one; an electric lock one control (a two-position lever) and two indications. The
   token meanings are FieldUnit's (`docs/AAR_SIGNALING_PRIMER.md`, GLOSSARY §10.3).
5. Closed 2026-11-01: **Glossary.** Added entries in `FieldUnit/docs/GLOSSARY.md` for `automatic signal`, `signal
   location`, `HD line`, `station-to-station block`, `boundary track circuit`, `current of traffic`, `traffic` /
   `direction of traffic`, `SR` (directional stick), `BPR`, `FR`/`FSR` (traffic), and `RGPR`, plus "powered switch or
   derail" in `interlocking limits` (§4) and retired synonyms `line signal` and `passed memory` (§11). `FSR` is not a
   collision: AAR names are not unique across domains (owner, 2026-11-01); the GLOSSARY (§10.5) uses `FSR` for
   FieldUnit's fleet stick relay, while traffic-lever schemes use it for the traffic stick relay.
6. Luchessa's and Watsonville's `NFLK` and `SFLK` (board `TRAFFIC` lamps): whether they become a block's direction-of-traffic
   indication.
7. Off-layout ends (Lick, Hollister): a block with one end on the layout is reported at info.
8. **Hold signals.** An intermediate signal the dispatcher can hold at stop to divide an established block. A held
   signal location takes a control, so it is a code line station. Not modeled yet.

## 22. Out of scope

- FieldUnit's implementation of Parts 2 and 3 (R1): the relay model, approach lighting, time release, aspects, and
  carrier selection.
- The contents of the rulebook reference data.
- Detailed APB head-block circuit equations (§13, §18.2).
- Train order conditions: the reversed number plate, Form Z.
- How a US&S 506 code chart assigns the block-clear bit to a step.
- A common hardware set for a signal location (connector, wiring, PCB carrying the HD lines, detector inputs and mast
  outputs): a layout reference design, not a model fact.

## 23. Consequences

- ADR 0009 §3.10: a mast states Kind; TRACK Kind `IRJ_SIGNALS`; track circuit Style `boundary` (this change), and the
  symbol-field lint accepts a mast's Kind and requires it.
- ADR 0009 §3.12 (merged in #58): the track rule covers interlocking track only, amended in place.
- ADR 0012 §5: the `blocks` library covers the track between control points and serves directed `HD` links. §5.5: the
  proxy and its TBD retire, since a signal never stands in for another; the approach signal of a home is derived.
- FieldUnit `docs/GLOSSARY.md` §4, §7, §8, §9, §10.3, §10.5, §11, §12: "powered switch or derail" in `interlocking
  limits` and the ADR 0013 glossary entries (done).
- The KiCad importer: a hierarchical label continues a track run (`geometry.run_end` fires on one today);
  `IRJ-Signals` with per-mast sides; `joint.masts` retires for two masts on opposite sides; Style `boundary` (today
  the boundary symbol, with no `TC` pin, is skipped without a word).
- `derive.py`: the mast checks of §5; the circuits a boundary circuit counts toward; NEXT_CP pairing retires inside
  CTC. No transport or carrier checks.
- The schema: a double joint's masts with their sides; a mast's Kind.
- Reference data: code line capacity and steps (`reference.CODE_LINE_CAPACITY`, `CODE_LINE_STEPS`) and the operations
  settings (gap 2).
- FieldUnit: uses Part 2 (prototype behavior) and Part 3 (suggestions and context) when implementing `HD` lines and
  inter-CP blocks.

[^rev]: Rewritten 2026-11-01 (rev 3) into three parts: Part 1 normative model facts, Part 2 prototype behavior, and
    Part 3 non-normative suggestions and context for FieldUnit. Decisions B, C, and F are ratified; open items A, D,
    and E move to Part 3 as FieldUnit implementation context; the earlier §16 "stale `SR`" trace and office-gating `FR`
    are removed because a vital FieldUnit rejects unsafe controls (FieldUnit ADR 0002 Rule 2) while the non-vital
    OfficeUnit never gates controls (GLOSSARY §2.3). Commit `a3a35d7` holds the prior two-part draft; commit `2a456d4`
    holds the earlier E/P line-signal draft; commit `96d3765` holds the first six-decision draft.
