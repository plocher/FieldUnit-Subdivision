# 0017. Seam symbols do not know where they are used

- Status: **accepted by the owner 2026-11-14**. The ask was: rule on the eight decisions below and on the aggregate
  question under decision 5.
- Amends (as follow-up changes; not edited in this ADR's PR): ADR 0009 §3.10 (Role `PANEL` on the office side) and
  the paragraph after the relation table (a lamp's scope); ADR 0008 C11 and its 2026-10-23 ruling (model board
  lamps as PANEL devices); the symbol lint's E72 and its PANEL rules. §5 lists the text.
- Builds on: the owner's point of 2026-11-14 (drivers, devices and panel items are seam entities and do not care
  where they are used; the `Local-*` and `Panel*` pairs are a DRY failure); FieldUnit `docs/GLOSSARY.md` "seam";
  ADR 0004 D5 and its lock table; ADR 0009 §3; ADR 0013 §4; ADR 0016 decision 4; `AGENTS.md`, Design rules.

## Decisions requested (all ruled 2026-11-14)

1. **A seam symbol states what it is, never where it is used.** Its function (`Appliance`, `Style`), its pins and
   its settings. Not office or field, not desk or fascia. *Ratified 2026-11-14.*
2. **Desk or field comes from the processor the bindings reach.** A device bound to an office unit's processor is
   that office unit's; one bound to a field unit's processor is that field unit's interlocking's. A device with no
   binding falls back to its `Column` pin (a column is the desk's), then to its sheet. A binding that contradicts the
   sheet is reported; bindings that reach both sides are an error. *Ratified 2026-11-14.*
3. **A demand goes through the vital logic of the interlocking that owns its appliance.** A demand over a code line
   is a control; a demand a field unit reads from any I/O (a lever, a key, any sensor, over any transport) is a local
   demand, and where its sensor is wired is free. Every demand is an input to the logic of the interlocking that owns
   the appliance, and only that logic drives the appliance: nothing goes behind the code line's back. The check is on
   outputs: an appliance's output (a switch machine, a head) bound to a processor that does not run its interlocking
   is an error; a demand bound anywhere is never an error by itself. The stations of one interlocking (Luchessa's
   three houses on a 506 line) share demands freely, and what one interlocking learns from another is ADR 0013's
   seam, not a demand.
   *Ratified 2026-11-14 in this wording.*[^demand]
4. **Column membership comes from a wired `Column` pin, not from Role.** A desk device with no `Column` pin is in no
   column. A `Column` pin on a device bound to a field unit is an error. *Ratified 2026-11-14.*
5. **A device symbol can be used with office and field hardware, unchanged.** Where two symbols today state one
   function only to mark desk or field, they become one: `PanelSwitch`, `Local-Switch` and `Local-Derail`;
   `ModelLamp-*` and `Device-Lamp` (the colour a setting). *Ratified 2026-11-14 in this wording.*
   - **Aggregates stay one symbol, and are desirable.** `PanelSignal` is an aggregate: unit 1 has the `Column` pin
     and three contacts (`NGS`, `HS`, `SGS`), unit 2 three lamps (pins 5 to 7; Railroad `9905c8e`: `SGK`, `NGK`,
     `TEK`; the owner's working copy renames pin 7 to `STOP`, uncommitted). `PanelSwitch`, `PanelLock` and
     `PanelMCall` are aggregates of contacts and lamps in one unit. An aggregate is not composed of primitive device
     symbols; it is location-independent like every device symbol. *Ruled 2026-11-14 (the owner: aggregated symbols
     "are not only OK, they are desirable").*
6. **The lock plates are not a pair and stay two symbols.** The desk plate sends the release (`WLS`); the fascia
   plate sends the crew's request (`WLQ`). These are two functions. Each is named for its function.
   *Ratified 2026-11-14.*
7. **Role `PANEL` retires; its symbols become `DEVICE`.** It states nothing that a pin, a binding or the function
   does not state (§3.4). The device symbols move to one library. *Ratified 2026-11-14.*
8. **Migration in two steps, no bridges.** Decisions 2 to 4 are an importer change and land first; they fix
   Watsonville and change no symbol. Decisions 5 to 7 land after the MVP, by our lock-gated edit tooling, in one pass
   over libraries, embedded copies and placed instances, with a field diff before the owner commits.
   *Ratified 2026-11-14.*

[^demand]: Vocabulary, agreed by the owner 2026-11-14 ("the earlier change lost the nuance"): demand is the parent
    term. A control is a demand over a code line; a local demand is one the field unit reads at the location. FieldUnit
    `docs/GLOSSARY.md` §11 retired "demand (for a control)" as a synonym of control (line 757); the glossary gains
    entries for demand and local demand and drops that row, a FieldUnit change (branch `docs/glossary-demand`).

## 1. Problem

The importer decides the side of a device by its Role (`tools/layout_compiler/seams.py` `_devices`, line 829 on):

- Role `PANEL`: the single office unit (lines 841 and 854). Its column comes from its `Column` net (lines 837 to
  845).
- Any other `DEVICE`: the interlocking of its sheet, by `_unit_of_sheet` (lines 469 to 472, called at line 856).

The derivation then reads the side from where the device is filed: a desk lever is an office unit device, a field
lever an interlocking device (`tools/layout_model/derive.py` `control_sources`, lines 1506 to 1534). So the Role
decides whether a lever is the dispatcher's or the crew's.

**Watsonville is wrong today.** `PanelSelector` is in `Railroad-Office` but carries Role `DEVICE`. The two knobs are
drawn on `Watsonville-Panel.kicad_sch`, a child sheet of `Watsonville.kicad_sch`. In
`schemas/layout-model/examples/spcoast.layout.json` both selectors (`Arrival`, `Departure`) are filed under
`interlockings.Watsonville.devices`, but their bindings are `SouthCTC/0x50` and `SouthCTC/0x51` (`VALUE`, `BUTTON`).
`SouthCTC` is the processor of the office unit `SouthCTC`; Watsonville's processor is `Watsonville`. A milestone E
field unit generator that reads `interlockings.Watsonville.devices` would put the desk knobs into the Watsonville
field sketch. The derivation already allows a selector "on the desk or in the field" (`derive.py` line 1393); only
the filing is wrong.

**The Tutorial is right only because of Role.** `Railroad/Tutorial/Tutorial.kicad_sch` draws the desk and the field
on one sheet. Compiled 2026-11-14 with `tools/compile_layout.py`: every office unit device is bound to
`ExampleDesk/0x40` (the office unit's processor) and every bound interlocking device to `ExampleField/0x21` (the
interlocking's processor). Role and bindings agree, so either rule gives this result.

**The binding rule reproduces every other filing.** In the SPCoast example all 72 office unit devices are bound, all
to `SouthCTC`. No interlocking device other than the two selectors is bound to `SouthCTC`. Decision 2 moves the two
selectors and nothing else.

## 2. Architecture

### 2.1 Cited rules

| # | Rule | Tag | Source |
|---|---|---|---|
| R1 | Seam 2 is hardware I/O, local or remote, on the panel side and on the field side. | model | GLOSSARY "seam" |
| R2 | Each fact has one source. | model | `AGENTS.md`, Design rules |
| R3 | Abstraction and DRY violations in existing code are debt, not precedent. | representation | `AGENTS.md`, Design rules |
| R4 | A driver finds its bus by declaration and scope; attachments carry only their own address. | representation | ADR 0005 |
| R5 | A processor runs logic and anchors connections; remote I/O is an attachment, not a processor. | model | ADR 0009 §3 |
| R6 | The crew's throw of the points by `Local-Switch` sends nothing on the code line. The crew's request (`WLQ`) is a local input; the field unit sends `WLQK` up. | operating | ADR 0004, lock table and D5 |
| R7 | A `local` switch is driven by the field unit from a fascia lever alone, with no desk lever. | operating | ADR 0013 §4 |
| R8 | `Control.<pin>` and `Indication.<pin>` bind a pin to a function word. | representation | ADR 0016 decision 4 |
| R9 | No fallbacks where an explicit form exists. | model | ADR 0012 §4 |

### 2.2 What follows

The side of a device is already a fact of the drawing: the bus its pins land on belongs to a processor, and the
processor runs an office unit or a field unit (`relations.processor` on each). The Role restates that fact, and the
restatement can disagree with it (Watsonville). By R2 the binding is the source. By R9 the sheet is a fallback only
where no binding is drawn: a device whose hardware is not drawn yet, or a head or mast whose I/O is reached through
an encoder (the importer writes no binding for those today).

Control or local demand (decision 3) needs no new fact. A desk device's demands are controls: they go to the
station of its column, or for a selector the station that owns its ladder's switches (`derive.py` lines 150 to
157). A field device's demands are local demands (R6, R7), whichever field unit's I/O reads them. The owner (2026-11-14)
widened the first wording, which made a field device's demand on another interlocking's appliance an error: a
designer may wire a sensor on one interlocking's hardware for another's appliance, over CMRInet, JMRI-MQTT or a
custom transport, and Luchessa's three houses on a 506 line share demands in one processor. What the rule protects
is the vital logic: "you can't change my vital behavior by going behind the code line's back". So the check moves
to outputs, where a bypass would show: an appliance driven by a processor that does not run its interlocking.

## 3. Evidence

### 3.1 The symbol pairs (libraries read 2026-11-14, Railroad `9905c8e`)

| Pair | Same | Different |
|---|---|---|
| `PanelSwitch` (Office, PANEL) / `Local-Switch` (Field, DEVICE) | `Appliance lever`, `Style switch`, `Name ${Value}`, `Pin.NWS`, `Pin.RWS`, `Pin.NWK`, `Pin.RWK` all `binary`; the four pins and their electrical types | `PanelSwitch` has the `Column` pin (pin 1, so the others are numbered 2 to 5, not 1 to 4) and the four `Control.*`/`Indication.*` fields; the Description |
| `Local-Derail` / `Local-Switch` (both Field, DEVICE) | every field, pin and number | the Description only. `Local-Derail` carries `Style switch` |
| `ModelLamp-AMBER`, `-BLUE`, `-GREEN`, `-RED`, `-YELLOW` (Office, PANEL) | among themselves, all but `Color` and the placeholder `Value` | five symbols for one setting |
| `ModelLamp-*` / `Device-Lamp` (Field, DEVICE) | `Appliance lamp`, `Name ${Value}`, `Pin.LAMP binary`, one `~{LAMP}` input | `ModelLamp` has `Style board`, `Color` and the whole-symbol `Indication` expression; `Device-Lamp` has `Address` (a pixel bus); pin number 2 against 1 |
| `PanelLock` (Office, PANEL) / `Local-Lock` (Field, DEVICE) | `Appliance lever`, `Style lock`, `WLQK`, `WLK` | not one function: `PanelLock` sends `WLS` (the release) and has `UNUSED` (the N contact) and the `Column` pin; `Local-Lock` sends `WLQ` (the crew's request). The lit-while-dropped `WLK` lamp is stated two ways: `Indication.WLK = !${Value}WLK` against `Invert = WLK` |

No pair: `Local-TrainOrder` (field only); `PanelSignal`, `PanelMCall`, `PanelCode`, `PanelAuxiliary` (desk only
today); `PanelSelector` (one symbol, already Role `DEVICE`, used on the desk).

Under ADR 0016 decision 4 (R8) the `Control.*`/`Indication.*` fields bind pins to function words
(`Control.RWS = REVERSE`). A desk switch lever and a fascia switch lever then carry the same fields; the only real
difference left between `PanelSwitch` and `Local-Switch` is the `Column` pin, which is a wire, and so a fact of use.

### 3.2 Lamps that read as heads

`Device-Lamp-RGB` (Field) carries `Appliance head`, `Style Generic`, pins `IND` and `APP`: a colour lamp classed as a
signal head. Watsonville's knob colour does not use it: `Watsonville-Panel.kicad_sch` draws two `Encoder-RGB`
(Description "Encoder for a signal head") and two `Driver-I2C-KnobEncoderRGB`, and the selector's `COLOR` pin has no
binding in the model. A colour lamp is the lamp of decision 5 with a colour word set (ADR 0016 decision 7, `color`),
not a head.

### 3.3 What the libraries enforce by place

`tools/contract/lint_symbol_fields.py`: PANEL needs a `Column` pin or `Style board` (lines 310 to 313); DEVICE may
not have a `Column` pin (line 315, E72); `Control.*`/`Indication.*` are checked only on PANEL (line 340). Each rule
reads a place from the Role.

### 3.4 What Role PANEL states, and where else it is stated

| Role PANEL is read for | Stated also by |
|---|---|
| the side (office unit) | the bindings (decision 2) |
| the column | the `Column` pin (decision 4) |
| a model board device in no column | `Style board`, and the absence of a `Column` pin |
| where `Control.*`/`Indication.*` may appear | the pins they name (R8 applies to a fascia lever too) |
| a function that exists only on a CTC machine (the code button, `Style code`) | the function: a `Style code` device bound to a field unit is an error |

Nothing is left that only the Role states.

## 4. Consequences

- The importer: `_devices` files by binding (decision 2), with the new reports below; `_unit_of_sheet` stays as the
  fallback.
- New import diagnostics (registered in `tools/layout_compiler/diagnostics.json` with the change): the side by
  binding disagrees with the sheet (warning); bindings reach both sides (error); a `Column` pin on a device bound to a
  field unit (error). A rule check in `derive.py`: an appliance's output bound to a processor that does not run
  its interlocking (error; decision 3). `device.office` retires with Role `PANEL`.
- A processor that runs the field units of two interlockings (GLOSSARY "field processor"; `SPCoastApp` runs
  `GCaltrain` today) names the side but not the interlocking; the served appliance's interlocking, then the sheet,
  decides.
- A binding through remote I/O (a CMRInet Node on a line, a JMRI encoding) reaches the processor that anchors the
  line or the transport (R5).
- `derive.py` `control_sources` is unchanged: it reads the side from the containment, which is now right.

## 5. Text this amends (record; not edited here)

| Where | Text now | Change (follow-up) |
|---|---|---|
| ADR 0009 §3.10, Role list | "`OFFICE_UNIT`, `COLUMN`, `PANEL`, ... on the office side; `DEVICE` in the field" | `DEVICE` on both sides; the side by binding |
| ADR 0009, after the relation table | "A model board lamp never uses a column: its scope is the interlocking of the panel sheet it is drawn on" | its scope is the processor it is bound to; a row in the relation table for "device to its side" |
| ADR 0008 C11, ruling of 2026-10-23 | "model board lamps as PANEL devices of Style `board` without a `Column` pin" | lamp devices, Style `board`, no `Column` pin |
| ADR 0002 | symbol contract by library and Role (frozen) | input to its rewrite after #30 |
| ADR 0004 D5, lock table | names `Local-Lock`, `Local-Switch` | the function names of decisions 5 and 6 |
| ADR 0011, ADR 0012 | no text on the side of a device (searched for `PANEL`) | no change |
| ADR 0013 §4 | "a Local-Switch alone" | the switch lever bound to the field unit |
| FieldUnit `docs/GLOSSARY.md` | "panel column" names KiCad `PanelColumn`; no entry for desk or fascia device | a note under "seam": a seam device's side is its binding; "demand" as the parent term (decision 3, footnote), which §11 now retires |
| Code | `seams.py` `_devices` (lines 829 to 883) and line 702; `lint_symbol_fields.py` lines 51, 67 to 72, 114, 310 to 315, 340; `derive.py` and `grammar.py` docstrings and messages that name `Local-Switch`, `Local-Lock`, `Local-Derail` (`derive.py` lines 1508 to 1562, `grammar.py` line 135) | as §4; messages name functions, not symbols |
| Features and tests | `schemas/layout-model/rules/features/logical/trackplan/appliance_switch_control.feature`, `appliance_derail.feature`, `ladder.feature`, `steps/model_steps.py`; `tools/layout_compiler/features/field/device_train_order.feature`, `driver_encoded.feature`, `trackplan/appliance_derail.feature`; `tests/test_layout_compiler.py`, `test_derive.py`, `test_trackplan.py`, `test_symbol_units.py`, `test_kicad_library_overview.py` | a scenario for a desk selector on an interlocking's sheet; symbol names follow decision 5 |
| Railroad | `Railroad-Office.kicad_sym`, `Railroad-Field.kicad_sym`, every sheet that places the pairs, `symbols/manual.html` | decisions 5 to 7, after the MVP |

## 6. Record

### 6.1 Options considered (decision 2)

| Option | For | Against |
|---|---|---|
| **The side from the bindings, the sheet as fallback** (chosen) | one source; fixes Watsonville; the Tutorial is unchanged; no symbol edit | a device with no binding still needs the fallback |
| Keep Role; make `PanelSelector` Role `PANEL` | one field changed | the place stays in the symbol; a field selector needs a second symbol, one more pair |
| The side from the sheet: panel sheets marked as desk | no binding needed | a sheet is a drawing artifact, not a fact; the Tutorial draws both sides on one sheet |

### 6.2 Not verified

- That the FieldUnit office unit sketch generator (FieldUnit `a9070ae`) and a future field unit generator read the
  devices from `officeUnits` and `interlockings` as filed `(unverified)`.
- How the importer would follow an encoder to the processor for heads and masts; today the sheet decides for them.
- Whether an office unit and a field unit can share one processor. No drawing does it; if one does, decision 2
  names no side and the sheet decides.
