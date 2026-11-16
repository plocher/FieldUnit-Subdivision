# 0018. Devices serve an appliance by Name; outputs fan out, inputs have one source

- Status: **proposed 2026-11-14, rewritten 2026-11-15**. The ask: rule on the nine decisions below. Each has a
  default. Decisions 1 to 3 are the design; 4 to 9 apply it.
- Amends (as follow-up changes in the recipe, §9; not edited in this ADR's PR): `tools/layout_model/derive.py`, the
  mast paragraph (lines 70 to 91) and the train order paragraph (lines 92 to 108); ADR 0009 §3 (field mast devices,
  train order mast devices, their position and face pins); ADR 0003 (the names of a head and of a face); the
  2026-11-04 and 2026-11-08 rulings that a head and a train order lever have no name of their own (§2.3 says what
  stays true); the 2026-11-05 ruling that several devices may consume one mast by Name (§5 restates it by direction).
- Builds on: the owner's brainstorm of 2026-11-14 (this ADR records it); ADR 0016 (function words); ADR 0017
  decision 1 (a seam symbol states what it is), decision 3 (a demand goes through the vital logic of the interlocking
  that owns its appliance) and decision 5 (aggregates are desirable); the JMRI mast proxy
  `Railroad-HardwareIO:Device-Mast-JMRI` (Railroad `e8929e1`, Subdivision PR 156); FieldUnit
  `tools/layoutgen/layoutgen.py`.

## Decisions requested

The design:

1. **A device serves an appliance by Name, never by a wire to a tap.** A device that serves a whole appliance carries
   the appliance's Name (`778NAB`, `Gilroy`). A device that serves one part of it carries `<appliance>.<part>`
   (`778NAB.A`, `Gilroy.E`). The importer splits at the last dot and matches the appliance exactly. *Default: yes.*
2. **The appliance says what its parts are.** A signal mast's parts are its heads, and its Name states their letters
   (`778NAB` has heads A and B). A train order board's parts are its faces, and a face exists when a device names it.
   A part Name that the appliance does not allow is an error. *Default: yes.*
3. **Every function a device carries has one direction, seen from the logic, and the direction sets the sharing
   rule.** A function the logic drives (an output) can have any number of consumers. A function the logic reads (an
   input, a demand) has exactly one source for each part, function word and origin (§5). *Default: yes.*

Applied:

4. **The taps retire, for signals and train orders alike.** `Device-Mast-Single`, `-Double`, `-Triple`, `-Dwarf`,
   `-Dwarf-Double` and `Device-TrainOrder-Mast-Single`, `-Double` go. The pins that existed only to reach a tap go
   with them: `IND` on each `Device-Head-*` and on `Local-TrainOrder`. *Default: yes.* The alternative that is also
   consistent: keep taps for both, and make `Device-Mast-JMRI` hang on one too (§6.2).
5. **A head is named for the head it is.** `778SC.C`, not "position A of the mast device". Its position top down is
   derived from the order of the letters in the mast's Name, as the derivation does today from the pin. The derived
   `positions` of a mast keep their shape, so FieldUnit's mast reader does not change. *Default: yes.*
6. **A train order face's suffix is a required label.** `.E`, `.EAST`, `.W` and `.oldstation` are all valid; it must
   be different from the other faces of its board. *Default: yes.*
7. **A fact is in the model only when something reads it.** A signal mast's facing stays: the mast rules read it
   (`mast.letters`) and so do the regime rules. A train order face's direction goes: nothing reads it (§4.3). The
   `train_order.face` direction checks retire. *Default: yes.*
8. **A JMRI proxy is a device like any other.** `Device-Mast-JMRI` serves a whole signal mast (bare Name). A JMRI
   train order face is one symbol in three units, serving one face (`Gilroy.E`): unit A the mast (an output, the only
   unit with an `IOBus` pin), unit B the `STOP` sensor and unit C the `SLOW` sensor (inputs). *Default: yes.*
9. **Migration is one orchestrated pass with no bridges** (§9). Signals and train orders move together, because a
   rule that holds for one and not the other is the bridge. *Default: yes.*

## 1. Problem

Signals and train orders are drawn the same way today, in three layers:

| Layer | Signal mast | Train order board |
|---|---|---|
| trackplan appliance | `Signal Mast Double` `778NAB` | `Train Order Mast Double` `Gilroy` |
| tap, named for the appliance | `Device-Mast-Double` `778NAB`, passive pins `A`, `B` (positions top down) | `Device-TrainOrder-Mast-Double` `Gilroy`, passive pins `E`, `W` (faces) |
| consumers, anonymous | a `Device-Head-*` whose `IND` reaches a position pin | a `Local-TrainOrder` lever and a head whose `IND` reaches a face pin |

The tap exists so that an anonymous consumer can say which part it serves: the derivation reads `relations.mast` and
`relations.position` (or `relations.face`) from the pin the consumer's `IND` reaches (`derive.py` lines 77 and 99).

Three things show that this structure states too much:

- **The JMRI mast proxy has no tap.** `Device-Mast-JMRI` (PR 156) serves its mast by Name alone. It is the first
  consumer tied by Name. It works because it serves the whole mast. Today a consumer of a part cannot do the same.
- **The parts already have names.** The importer keys JMRI objects `SIGNALMAST.Gilroy.E` and `SENSOR.Gilroy.E.STOP`
  (the owner, 2026-11-10). FieldUnit's generator names a train order mast `<board>.<face pin>`, and notes: "The model
  gives the mast no name of its own." A signal mast's Name already lists its head letters (ADR 0003 rule 7).
- **The tap's pins and the head letters are two names for one thing.** The dwarf `778SC` has one head, letter C, but
  it hangs on pin `A` of `Device-Mast-Dwarf`. The derivation maps "the k-th letter is the k-th position" (`derive.py`
  line 72). The tap adds a second name and a mapping.

Train orders add one more: on Gilroy (Railroad `e8929e1`) each face is a tap pin, a lever, a head, a mast driver and
two sensor drivers. That is eleven symbols for one board. In that installation JMRI shows the semaphore and JMRI's
panel is the operator's lever, so the head and the lever are there only to carry wires.

## 2. The design

### 2.1 Three rules

| Rule | Says | Tag |
|---|---|---|
| R1 | A device serves an appliance by Name: the appliance's Name for the whole, `<appliance>.<part>` for a part. | representation |
| R2 | The appliance says which parts exist. | model |
| R3 | A function's direction, seen from the logic, sets how many devices may carry it. | model |

### 2.2 What each kind of appliance has

| Appliance | Parts | Part names | Where the parts come from |
|---|---|---|---|
| signal mast | heads | the head letters of its Name: `778NAB.A`, `778NAB.B`, `778SC.C` | the appliance Name (ADR 0003 rule 7) |
| train order board | faces | a label: `Gilroy.E`, `Gilroy.W` | the devices that name them |
| any other (switch, lock, track circuit) | none today | — | — |

A signal mast's parts are fixed by its Name, so a head device that names a letter the mast does not have is an error.
A train order board's parts are open, so each new label is a new face. Its Style `single` or `double` is only a
picture.

### 2.3 What stays true from the "no name of its own" rulings

The 2026-11-04 and 2026-11-08 rulings say that a head and a train order lever have no name of their own. That stays
true: `778NAB.A` is not the head's own name. It is the name of the part the head serves. The device has no identity
apart from that part. Two heads that serve `778NAB.A` (a fascia head and a model board repeater) are two consumers of
one part.

### 2.4 The names

| Device serves | Name | Split |
|---|---|---|
| the whole signal mast | `778NAB` | appliance `778NAB` |
| head A of it | `778NAB.A` | appliance `778NAB`, part `A` |
| the whole train order board | `Gilroy` | appliance `Gilroy` |
| its east face | `Gilroy.E` | appliance `Gilroy`, part `E` |
| a face of a board whose Name has a dot | `St.Louis.W` | appliance `St.Louis`, part `W` (the last dot) |

- The match on the appliance part is exact, so `Gilroy`, `GilroyYard` and `GilroyEast` never collide.
- The importer states the parts (`appliance`, `part`). Nothing downstream parses a Name (the owner, 2026-11-12).
- In KiCad the Name is typed text. A field cannot refer to another symbol's field except by a reference designator,
  which we do not use. The importer checks every Name against the appliances.

## 3. Applied to signals

### 3.1 Before and after

| | Today | After |
|---|---|---|
| a head | `Device-Head-TypeD`, no Name, `IND` wired to pin A of `Device-Mast-Double` `778NAB` | `Device-Head-TypeD` Name `778NAB.A`, no `IND` pin |
| its output | `APP` to an encoder, the encoder to an IO driver | unchanged |
| the mast's positions | from the tap pins its heads reach | from the letters of the Name, in order |
| a whole-mast JMRI consumer | `Device-Mast-JMRI` `778NAB` (since PR 156) | unchanged |
| the Gilroy fascia repeaters | a second tap per mast, H2 heads on its pins | H2 heads named `778NAB.A` and so on, no tap |

### 3.2 What the head loses and what replaces it

- **The `IND` pin.** It carried the logic's word to the head as a wire. Nothing reads that wire's direction (PR 156
  skips it), and its only use is to reach the tap. After this ADR the Name says which part the head serves.
- **ERC on that wire.** KiCad's ERC no longer checks that a head is wired to a mast. The importer checks instead: a
  head Name that names no mast or no letter of it is an error; a head letter that no device serves is reported as
  today (`mast.heads`).
- **The position pins.** `PINS` (`derive.py` line 1915) and the "k-th letter is the k-th position" mapping become one
  rule: the position of a letter is its place in the Name.

### 3.3 What does not change for signals

The trackplan mast symbols; the Name grammar of a mast; its facing and every rule that reads it; the encoders and IO
drivers; the head's `APP` pin and what it reaches; the derived `positions` and `presents` (FieldUnit's
`layoutgen.py` reads `derived.positions`, line 161).

## 4. Applied to train orders

### 4.1 Before and after

| | Today | After |
|---|---|---|
| the faces | the pins of `Device-TrainOrder-Mast-Double` `Gilroy` | the labels that devices name: `Gilroy.E`, `Gilroy.W` |
| a local face | a `Local-TrainOrder` lever and a head, `IND` on the face pin | the same symbols, Name `Gilroy.E`, no `IND` pin |
| a JMRI face | the head's `APP` to `Driver-JMRI-SignalMast`, the lever's `~{STOP}`, `~{SLOW}` to two `Driver-JMRI-Sensor-Feedback` | one JMRI train order face symbol, Name `Gilroy.E`, on Gilroy's `IOBus` |

### 4.2 The JMRI train order face

| Unit | Is | Direction | Pin | Fields |
|---|---|---|---|---|
| A | the JMRI mast: the face's indication (CLEAR, APPROACH, STOP from `trainOrderInputs`) | output | `IOBus`, passive | `Address` |
| B | the `STOP` sensor | input (a local demand) | none | `Address` |
| C | the `SLOW` sensor | input (a local demand) | none | `Address` |

- It is the train order counterpart of `Device-Mast-JMRI`: a proxy device, tied by Name, with one `IOBus` route.
- One placement is the one operator station for its face. A second placement brings a second `STOP` and `SLOW`,
  which R3 rejects. A repeater is an output-only device with the same Name.
- The JMRI keys stay derived: `SIGNALMAST.Gilroy.E`, `SENSOR.Gilroy.E.STOP`, `SENSOR.Gilroy.E.SLOW`.
- A JMRI sensor has no wire, so it has no sense.
- To verify in KiCad before the symbol is drawn: that a unit with no pins is supported, and that a field such as
  `Address` is kept for each placed unit and not shared by all units of one reference.

### 4.3 Why the face's direction goes

The derivation checks that a double board's face pins name N, S, E or W, and takes a single board's direction from
the glyph's turn (`derive.py` lines 101 to 102). It says that "no mast rule, lever rule or code line token reads it".
FieldUnit copies `direction` into its row (`layoutgen.py` line 276) and uses it for nothing else. The board glyph's
turn still gives the picture. A signal's facing is different: `mast.letters` reads it (one letter on two masts of one
signal facing one way, `derive.py` line 74), and so does the regime rule for masts facing both ways (line 56). So it
stays (decision 7).

## 5. Outputs fan out, inputs have one source

### 5.1 The rule

| Direction | Devices that carry the function | Bound by |
|---|---|---|
| output: the logic drives it (an indication, a head, a lamp, a switch machine) | any number; each is a consumer | ADR 0017 decision 3: every consumer is bound to a processor that runs the owning interlocking (a desk lamp: the office unit) |
| input: the logic reads it (a demand: `STOP`, `SLOW`, a lever's `RWS`, a track circuit's `OCC`) | exactly one source for each key below | — |

The direction comes from what the device states: the electrical type of its pin at the device-to-driver boundary
(PR 156), or the unit (decision 8) where there is no pin.

### 5.2 The key for "one source"

One source for each **(appliance or part, function word, origin)**:

- **Part.** `Gilroy.E` `STOP` and `Gilroy.W` `STOP` are two keys. A key without the part would flag every double
  board.
- **Function word** (ADR 0016). A switch's `RWS` and `NWS` are two keys.
- **Origin.** A control comes over a code line from the desk; a local demand comes from the field (ADR 0017 decision
  3). A dual-control switch has a desk lever and a fascia lever for one function word: two origins, one source each.
  Which origin the logic obeys is the switch's control regime (the 2026-11-09 ruling: powered, dual, local), not this
  rule.
- **What the function belongs to.** A desk column's `CODE` button belongs to its column's station, not to an
  appliance named `CODE`. Seven `CODE` buttons on SouthCTC are seven keys.

Several readers of one source are fine: the rule counts sources, not readers.

### 5.3 What the corpus says

The rule was checked against `schemas/layout-model/examples/spcoast.layout.json` on 2026-11-15. It has 241 input
functions. A first count keyed by appliance and function word alone found four keys with two or more sources: the
train order board's `APP`, `STOP` and `SLOW` (the two faces) and SouthCTC's `CODE` (seven columns). All four are
correct drawings, and the key of §5.2 separates them. With that key the corpus has no input with two sources. No
function has both a desk and a field source today.

### 5.4 What it replaces

- The 2026-11-05 ruling ("several field devices may consume one trackplan mast by Name on purpose") becomes the
  output half. The Gilroy Interchange placements (a JMRI consumer and a fascia repeater for each 778 mast) stay valid.
- `train_order.face` "a face two levers serve" becomes a case of the input half, for every appliance. It is a new
  rule check (`derive.py`), at error.

### 5.5 What a consumer of the model must do

An output with several consumers has several bindings. A generator drives each of them. Whether every FieldUnit generator reader
takes all the bindings of a function is (unverified); step 6 of §9 checks each one.

## 6. What this design rules out, and the alternative

### 6.1 Ruled out

- A tap as the identity of a part. A wire from a consumer to a tap pin no longer says anything.
- A JMRI driver standing in for a consumer: the proxy devices are devices (decision 8).
- Two sources for one input key, anywhere.

### 6.2 The other consistent design

Keep the taps, for both kinds: heads and faces keep their `IND` pins, `Device-Mast-JMRI` gets an `IND` pin and hangs on
a tap, and the JMRI train order face hangs on a face pin. This keeps ERC on every consumer and changes no library
symbol except the proxies. It costs a tap for every appliance with a consumer, it keeps the tap pins as a second name
for the head letters, and the JMRI proxies come back to the "filler" that the owner removed on 2026-11-14. The default
is R1, with no taps.

## 7. Blast radius

Counts from the Railroad working copy and Subdivision `main` on 2026-11-14 and 15.

| Area | Signals | Train orders |
|---|---|---|
| Library: retire | `Device-Mast-Single`, `-Double`, `-Triple`, `-Dwarf`, `-Dwarf-Double` | `Device-TrainOrder-Mast-Single`, `-Double` |
| Library: change | the six `Device-Head-*` lose `IND` and gain a used `Name` | `Local-TrainOrder` loses `IND`; its `Name` (empty today) carries the face |
| Library: new | — | the JMRI train order face symbol |
| SPCoast placements | 42 taps (11 single, 14 double, 1 triple, 16 dwarf); 60 heads (49 TypeD, 8 H2, 3 UQ3) get Names | Gilroy: 1 tap, 2 levers, 2 UQ3 heads, 2 `Driver-JMRI-SignalMast`, 4 `Driver-JMRI-Sensor-Feedback` become 2 JMRI face symbols |
| Tutorial | 6 taps, 8 heads | none |
| Testbeds | each testbed's masts | `testbed-jmri` (Gilroy) |
| Importer (`seams.py`) | `_mast_on_ind`, `_file_field` (lines 950 to 961), the head and lever `IND` skip | the face handling, the JMRI key collision (lines 693 to 715), the `SIGNALMAST` key (line 781) |
| Derivation (`derive.py`) | the mast paragraph, `positions` from letters, `PINS` | the train order paragraph, `train_orders`; the new R3 rule check |
| Features | model: `device_mast_head`, `device_output`, `driver_jmri_mast`; importer: `device_mast_head`, `driver_encoded`, `device_binding` | model: `appliance_train_order`, `device_train_order`; importer: `device_train_order`, `appliance_train_order` |
| Registries | `mast.device`, `mast.heads` (rewritten for names) | `train_order.face`, `train_order.device` (rewritten); new: an input with two sources |
| Schema | a minor version: a part device's `relations.appliance` and `relations.part` in place of `relations.mast`, `relations.position` and `relations.face` | |
| Tests | `test_trackplan`, `test_layout_compiler`, `test_derive`, `test_fieldunit_projection` | the same |
| FieldUnit `layoutgen.py` | no change if `derived.positions` keeps its shape (decision 5) | `gather_train_order` (line 256) finds a face's devices by Name; `Gilroy_trainorder.h` regenerates |

## 8. Risks

- **A typed Name can be wrong.** A wire is checked by ERC; a Name is checked only by the importer. A head named
  `778NAB.C` on a two-head mast is an error the importer must catch (R2).
- **A large field edit.** About 70 heads change their Name and 48 taps go. The 2026-10-17 and 10-18 field resets show
  the risk; the field diff before each commit is the gate.
- **Two readers at once.** Until FieldUnit's readers move (step 6), the model and the generator disagree on where a
  face's devices are. Steps 5 and 6 land together for that reason.

## 9. Recipe

Each step lands complete, with its gate. No step leaves the old and the new form both accepted (the owner's "no
migration bridges").

1. **Ratify this ADR.** Gate: the owner's ruling on decisions 1 to 9, and on §6.2.
2. **Library: draw the new and changed symbols** (the owner in KiCad, or our lock-gated edit tooling on the owner's
   word). The JMRI train order face symbol; `Device-Head-*` and `Local-TrainOrder` without `IND`. The retired taps
   stay in the library until step 5. Gate: `tools/contract/lint_symbol_fields.py` clean; the two KiCad checks of
   §4.2 done.
3. **Importer and derivation (one Subdivision PR, a worktree subagent).** R1 to R3; heads and faces by Name; the R3
   rule check and its registry entry; the JMRI face; the taps no longer read; the schema minor version. Netlist
   fragment scenarios for each rule. The pinned corpus still has the old drawing, so the PR states the expected
   corpus diagnostics and does not refreeze. Gate: unittest, both behave suites, the registry gate.
4. **Drawing (a scripted pass, then the owner in KiCad).** A lock-gated edit script: for each head whose `IND` reaches
   a tap pin, set its Name to `<mast>.<letter>`, the letter from the tap pin's place in the mast's Name; then remove
   the wire and the tap. Gilroy's train order faces are redrawn by hand (one JMRI face symbol for each face). The same
   script runs on the Tutorial and the testbeds. Gate: a fresh netlist; the field diff against Railroad `HEAD`, which
   must show only the Name changes and the removed taps and wires; the step 3 importer on the live drawing with no
   new findings; then the owner commits.
5. **Retire and refreeze (one Subdivision PR).** Remove the retired symbols from the library after a search of every
   sheet. Move the corpus pin to the step 4 commit and rebuild `spcoast.layout.json`; update the gates in their own
   commit. Gate: unittest and behave on the new corpus.
6. **FieldUnit (FieldUnit Orchestration, in lockstep with step 5).** `gather_train_order` finds faces by Name; each
   reader that takes one binding for a function takes every binding of an output (§5.5). Gate: the generated headers
   have the same masts, faces, inputs and rest words as before.
7. **Amend the ADRs in place** (0003, 0009, and the records of the 2026-11-04, 11-05 and 11-08 rulings), with a
   footnote that gives the old commit.

Steps 3 and 4 can run at the same time. Step 5 waits for both. Step 6 merges with step 5.

## 10. Not decided here

- **JMRI's identifiers.** JMRI's MQTT address is a number (the owner, 2026-11-14), so a default derived from our Name
  does not work. Each proxy unit has an `Address` field; what goes in it, and what the model does with it, waits for
  the MVP.
- **Parts of other appliances.** A switch's points and its lock, or a lock's plates, could be parts in the same way.
  Nothing needs that yet.
- **Library names and division.** Office and field hardware are interchangeable (ADR 0017 decision 5), JMRI symbols
  are in two libraries, and name prefixes do the work of libraries. The owner noted this on 2026-11-14 ("we can't
  ignore this"); it is a later item, but step 2 is a natural time to do it.
- **The other JMRI drivers.** Turnout, Light and Sensor follow the energy rule and stay drivers until one of them
  does not fit.
