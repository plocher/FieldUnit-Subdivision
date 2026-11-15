# 0018. Train order faces are named appliances; outputs fan out, inputs have one source

- Status: **proposed 2026-11-14**. The ask: rule on the eight decisions below. Each has a default.
- Amends (as follow-up changes in the recipe, §6; not edited in this ADR's PR): the train order paragraph of
  `tools/layout_model/derive.py` (lines 92 to 108) and `train_orders`; ADR 0009 §3 (the train order mast device and
  its face pins); ADR 0003 (the name of a train order face); the 2026-11-05 ruling that several devices may consume
  one mast by Name (§3.3 restates it by direction).
- Builds on: the owner's brainstorm of 2026-11-14 (this ADR records it); ADR 0016 (function words); ADR 0017
  decision 3 (a demand goes through the vital logic of the interlocking that owns its appliance) and decision 5
  (aggregates are desirable); the JMRI mast proxy `Railroad-HardwareIO:Device-Mast-JMRI` (Railroad `e8929e1`,
  Subdivision PR 156); FieldUnit `tools/layoutgen/layoutgen.py` `gather_train_order`.

## Decisions requested

1. **A train order face is a named appliance.** Each face has a Name, `<board>.<suffix>`. The board on the trackplan
   keeps its bare Name (`Gilroy`). A device that serves a face carries the face's Name (`Gilroy.E`). The importer
   splits a face Name at its last dot and matches the board part exactly. *Default: yes.*
2. **The suffix is required, and it is a label.** A face Name without a suffix is an error, as a signal mast Name
   without a facing is. The suffix must be different from the other faces of the same board. `.E`, `.EAST`, `.W` and
   `.oldstation` are all valid. Nothing reads a direction from the suffix. *Default: yes.*
3. **A face's direction is not a model fact.** No rule, lever, code line token or generator reads it. The board
   glyph's turn on the sheet still gives the picture. The `train_order.face` direction checks retire.
   *Default: yes.*
4. **Outputs fan out; inputs have one source.** Several devices can carry one Name. Each function the logic drives
   (an indication, a lamp, a switch machine) can have any number of consumers. Each function the logic reads (a
   demand: `STOP`, `SLOW`, a lever's `RWS`) must have exactly one source. Two sources for one input is an error.
   This rule applies to every appliance, not only to train orders. *Default: yes.*
5. **The train order mast device and its face pins retire.** `Device-TrainOrder-Mast-Single` and
   `Device-TrainOrder-Mast-Double` go. A local face's lever (`Local-TrainOrder`) and its output (a head, a lamp)
   carry the face Name and need no tap. *Default: yes.*
6. **A JMRI train order face is one symbol in three units.** Unit A is the JMRI mast (the face's indication, driven
   by the logic). Unit B is the `STOP` sensor and unit C the `SLOW` sensor (local demands, read by the logic). Only
   unit A has an `IOBus` pin. Each unit has its own `Address`, for JMRI's identifier (deferred, §7). The units share
   the face Name. *Default: yes.*
7. **Signal masts change only by decision 4.** `Device-Mast-JMRI` is the case with no suffix: its Name is the mast's
   Name. The field mast devices (`Device-Mast-*`), their position pins and the anonymous heads on them do not change
   in this ADR. *Default: yes.*
8. **Migration is one orchestrated pass with no bridges** (§6). *Default: yes.*

## 1. Problem

Today a train order board is three layers (`derive.py` lines 92 to 108, `train_orders`):

| Layer | Symbol | What it states |
|---|---|---|
| trackplan | `Train Order Mast Double` (Name `Gilroy`, Style `double`) | the board, its station |
| tap | `Device-TrainOrder-Mast-Double` (Name `Gilroy`, passive pins `E`, `W`) | the faces, as pin names |
| consumers | `Local-TrainOrder` lever and a head, their `IND` on a face pin | which face each one serves |

On Gilroy (Railroad `e8929e1`) each face also has its head's `APP` wired to a `Driver-JMRI-SignalMast`, and the
lever's `~{STOP}` and `~{SLOW}` wired to two `Driver-JMRI-Sensor-Feedback`. That is eleven symbols for one board. In
that installation JMRI shows the semaphore and JMRI's panel is the operator's lever, so the head and the lever are
present only to carry the wires.

Three facts show that the layers state too much:

- **The face already has a name.** The importer keys the JMRI objects `SIGNALMAST.Gilroy.E` and
  `SENSOR.Gilroy.E.STOP` (the owner, 2026-11-10), and FieldUnit's generator names the mast `<board>.<face pin>`. It
  notes: "The model gives the mast no name of its own."
- **Nothing reads the direction.** The derivation checks that a double board's face pins name a direction, and it
  takes a single board's direction from the glyph's turn. It says itself that "no mast rule, lever rule or code line
  token reads it." FieldUnit copies `direction` into its row and uses it for nothing else.
- **"Double" means nothing.** A double board is two faces on one mast. Each face has its own lever, its own
  indication and its own JMRI objects. Nothing belongs to the pair.

## 2. Face names

| Thing | Name | Parts |
|---|---|---|
| signal mast | `778NAB` | signal 778, facing N, heads A and B |
| train order board (trackplan) | `Gilroy` | the board |
| train order face (device) | `Gilroy.E`, `Gilroy.W`, `GilroyYard.oldstation` | the board, a suffix |

- A signal mast Name never omits its facing (`778` alone is not a mast). A face Name never omits its suffix.
- The split is at the last dot, so a board Name can contain a dot. The match on the board part is exact, so the
  boards `Gilroy`, `GilroyYard` and `GilroyEast` never collide.
- The importer states the parts (`board`, `suffix`). Nothing downstream parses the Name (the owner, 2026-11-12).
- A board with one face is a board whose devices carry one suffix. Style `single` or `double` on the trackplan
  symbol is only a picture.
- In KiCad the face Name is typed text: a field cannot refer to another symbol's field except by a reference
  designator, which we do not use. The importer checks the name.

## 3. Outputs fan out; inputs have one source

### 3.1 The rule

| Direction of the function | Devices with the same Name | Example |
|---|---|---|
| the logic drives it (output) | any number: each is a consumer | a JMRI mast and a fascia repeater for `778NAB` |
| the logic reads it (input, a demand) | exactly one source | one `STOP` for `Gilroy.E` |

The direction comes from what the device states: a pin's electrical type at the device-to-driver boundary (PR 156),
or for a unit with no pin, the unit (decision 6).

### 3.2 Why

Two sources for one demand give the logic two answers for one function. The importer would have to pick one or
combine them, and either choice hides a drawing error. ADR 0017 decision 3 puts every demand through the owning
interlocking's logic; this rule makes sure that each demand comes from one place.

### 3.3 What it replaces

- The 2026-11-05 ruling ("several field devices may consume one trackplan mast by Name on purpose") becomes the
  output half of the rule. The Gilroy Interchange placements (a JMRI consumer and a fascia repeater for each 778
  mast) stay valid.
- `train_order.face` "a face two levers serve" becomes a case of the input half, for every appliance.

## 4. The JMRI train order face

| Unit | Is | Logic | Pin | Fields |
|---|---|---|---|---|
| A | the JMRI mast | drives it (the face's indication: CLEAR, APPROACH, STOP from `trainOrderInputs`) | `IOBus`, passive | `Address` |
| B | the `STOP` sensor | reads it (local demand) | none | `Address` |
| C | the `SLOW` sensor | reads it (local demand) | none | `Address` |

- One placement of the symbol is the one operator station for the face. A second placement brings a second `STOP`
  and `SLOW`, which decision 4 rejects. A repeater is an output-only symbol with the same Name.
- The binding is unit A's `IOBus` route. The JMRI keys stay derived: `SIGNALMAST.Gilroy.E`, `SENSOR.Gilroy.E.STOP`,
  `SENSOR.Gilroy.E.SLOW`.
- A JMRI sensor has no wire, so it has no sense.
- To verify in KiCad before the symbol is drawn: that a unit with no pins is supported, and that a field such as
  `Address` is kept for each placed unit and not shared by all units of one reference.

## 5. Blast radius

Counts from the Railroad working copy and Subdivision `main` on 2026-11-14.

| Area | Items |
|---|---|
| Library | new: the JMRI train order face symbol; retire: `Device-TrainOrder-Mast-Single`, `Device-TrainOrder-Mast-Double`; change: `Local-TrainOrder` (its `Name`, empty today, carries the face; its `IND` pin loses the tap it reached) |
| SPCoast | Gilroy: 1 train order tap, 2 `Local-TrainOrder`, 2 `Device-Head-Semaphore-UQ3`, 2 `Driver-JMRI-SignalMast`, 4 of the 23 `Driver-JMRI-Sensor-Feedback` |
| Testbeds | `testbed-jmri` (Gilroy), with the 778 masts still in the old JMRI form |
| Tutorial | no train order |
| Importer | `seams.py`: `_mast_on_ind`, the face handling in `_file_field` (lines 950 to 961), the JMRI key collision (lines 693 to 715), the `SIGNALMAST` key (line 781) |
| Derivation | `derive.py` train order paragraph and `train_orders`; a new rule check for decision 4 |
| Features | model: `appliance_train_order`, `device_train_order`, `device_output`, `driver_jmri_mast`; importer: `device_train_order`, `appliance_train_order`, `device_binding` |
| Registries | retire `train_order.face` (direction cases), `train_order.device` (rewritten for the tap's absence); new: an input with two sources |
| Schema | a minor version: a face device's `relations.board` and `relations.suffix` in place of `relations.mast` and `relations.face` |
| Tests | `test_trackplan`, `test_layout_compiler`, `test_derive` (train order cases) |
| FieldUnit | `layoutgen.py` `gather_train_order` reads faces by Name; `Gilroy_trainorder.h` regenerates |

## 6. Recipe

Each step lands complete, with its gate. No step leaves the old and the new form both accepted (the owner's "no
migration bridges").

1. **Ratify this ADR.** Gate: the owner's ruling on decisions 1 to 8.
2. **Library (the owner in KiCad, or our lock-gated edit tooling on the owner's word).** Draw the JMRI train order
   face symbol (decision 6). Decide what `Local-TrainOrder`'s `IND` pin does with no tap to reach (it carried the face). Leave the retired symbols in place until step 5.
   Gate: `tools/contract/lint_symbol_fields.py` clean for the new symbols, the two KiCad checks in §4 done.
3. **Importer and derivation (one Subdivision PR, a worktree subagent).** Face Names (§2), the rule of §3 with its
   registry entry, the JMRI face (§4), the tap retired, the schema minor version. Test with netlist-fragment
   scenarios; the pinned corpus still has the old drawing, so the PR states the expected corpus diagnostics and does
   not refreeze. Gate: unittest, both behave suites, the registry gate.
4. **Drawing (the owner in KiCad).** Gilroy in `SPCoast`: replace each face's tap, lever, head, mast driver and two
   sensor drivers with one JMRI face symbol named `Gilroy.E` or `Gilroy.W`, on Gilroy's `IOBus`. Gate: a fresh
   netlist, the field diff against Railroad `HEAD`, the step 3 importer on the live drawing with no train order
   findings; then the owner commits.
5. **Retire and refreeze (one Subdivision PR).** Remove the retired symbols from the library (after a search of every
   sheet for placements). Move the corpus pin to the step 4 commit and rebuild `spcoast.layout.json`; update the
   gates in their own commit. Convert `testbed-jmri` in the same pass. Gate: unittest and behave on the new corpus.
6. **FieldUnit (FieldUnit Orchestration, in lockstep with step 5).** `gather_train_order` finds a face's devices by
   Name; `Gilroy_trainorder.h` regenerates with the same faces. Gate: the generated header has the same faces,
   inputs and rest words as before.
7. **Amend the ADRs in place** (0003, 0009, the 2026-11-05 ruling's records), with a footnote that gives the old
   commit.

Steps 3 and 4 can run at the same time. Step 5 waits for both. Step 6 merges with step 5.

## 7. Not decided here

- **JMRI's identifiers.** JMRI's MQTT address is a number (the owner, 2026-11-14), so a default derived from our Name
  does not work. Each unit has an `Address` field; what goes in it, and what the model does with it, waits for the
  MVP.
- **Named heads on signal masts.** A signal mast's heads are anonymous and hang on the mast device's position pins.
  Whether a head should instead carry a name (`778NAB.A`), as a face now does, is open.
- **Library names and division.** Office and field hardware are interchangeable (ADR 0017 decision 5), JMRI symbols
  are in two libraries, and name prefixes do the work of libraries. The owner noted this on 2026-11-14 ("we can't
  ignore this"); it is a later item.
- **The other JMRI drivers.** Turnout, Light and Sensor follow the energy rule and stay drivers until one of them
  does not fit.
