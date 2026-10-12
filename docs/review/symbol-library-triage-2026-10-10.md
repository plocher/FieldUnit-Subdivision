# Symbol library triage: the recipe for checkpoint step 4 (2026-10-10, rev 3)

- Status: rev 3, the plan as executed, plus the owner's `Terminal` question of 2026-10-11 (checkpoint E56, E57): `Terminal` retired for multi-unit symbols, and the libraries hand-maintained with the recipe as the regeneration path. The recipe is `tools/contract/apply_symbol_recipe.py` (its `--table` prints it), the gate is `tools/contract/lint_symbol_fields.py`, the contact sheet is `tools/contract/symbol_contact_sheet.py`, and the result is the Railroad repo's `symbols/` (PR #6). Section 6 records what ran and what is left.
- Governs: `io-design-checkpoint-2026-10-10.md` (rev 10) and its §4.1 symbol tables. Source inventory: the three libraries in `~/Dropbox/KiCad/InterlockingPlant/symbols/`, 83 symbols, at InterlockingPlant commit 96fc28f, read in place by the recipe and never edited; the copies first made in the Railroad repo were dropped (owner, 2026-10-11: obsolete files clutter the folder; the InterlockingPlant git holds them).
- Owner's rulings, 2026-10-10: the new libraries are written to `~/Dropbox/KiCad/Railroad/symbols/`, nothing edited in place; setting names are `lower_snake_case` and the compiler normalises before use; `SemaphoreU2` was meant as `LQ2` and `U3` as `UQ3`; the two detector symbols stay as convenience forks; graphic forks stay, they make compact drawings; Watsonville migrates like every sheet (its exclusion was about evidence, not scope); `Indications` becomes `IndicationCeiling`, the glossary's term; GPIO is `Digital` and `Pixel` only for now (YAGNI on level pins; the pixel pin is the first "protocol on a pin"); `Device-Head-1LED-PWM` retires, a single-colour PWM lamp is `Device-Lamp` through the two-point cast; the capability words for a pin that is in or out by what lands are `binary bidirectional` and `level bidirectional`.
- The `Pin.*` property is named for the pin's base name, `Pin.OCC` for pin `~{OCC}`: polarity is in the pin name, the capability belongs to the function.

## 1. Rules the recipe applies

What is mechanical in a `.kicad_sym` (text edits, geometry untouched): rename a symbol and its unit blocks; rename a pin; delete a pin; change a pin's electrical type; add, rename or remove a property; copy a symbol to another library; split a symbol into units by capability (below). What is hand work: add a pin, change a body, draw a new body, distribute a split symbol's graphics between its units.

Hand work survives regeneration: a symbol finished in the KiCad editor is named in the script's `HAND_FINISHED` list and carried over from the existing output byte for byte on every run (E57). The lint is the gate either way.

| Disposition | Meaning |
|---|---|
| keep | copied unchanged except for the library move |
| retag | copied; fields change as listed; pins and body unchanged |
| rename | copied under a new name; fields and pin names change as listed; body unchanged |
| copy | a new symbol made from an existing one by rename and retag, no drawing |
| hand | needs a pin added or a body drawn |
| split | made multi-unit by the script, one unit per capability (E56) |
| retire | not copied; the old library keeps it for the sheets that still reference it |

Field rules on every copied symbol:

- `Kind` is removed from every APPLIANCE, DEVICE, PANEL and IODRIVER symbol (I8). It stays on TRACK, POLICY, STRUCTURE, CODELINE and MACHINE symbols, whose form is unchanged (§4.1).
- `Appliance` and `Style` are added on APPLIANCE, DEVICE and PANEL symbols; `IC` on IODRIVER symbols (E36).
- One `Pin.<name>` property per function pin on DEVICE, PANEL and IODRIVER symbols, holding the native capability (I5). None on plant symbols: their pins are topology.
- Per-pin override slots (`OCC=`, `N=`, `LAMP=`, `NormalIs=`, `SW=`, the token-named blanks on plates) are removed (I7, I28). `ControlToken` and `Vital` are removed (I28). `IndicationToken` and `Color` stay on lamps (E42).
- Setting fields are renamed to `lower_snake_case`: `Hold_ms` to `hold_ms`, `Stop_deg` to `stop_deg`.
- `~{}` is added to every asserted-low pin that lacks it (I7). `Invert` is added where a lamp shows a token's complement (E53).
- `Description` is rewritten where the old text names a Kind or a hardware domain, and so are the body's graphic labels (`NeoPixel`, `I/O`, `12-bit PWM`): a `texts` action renames or deletes them.
- A DEVICE or PANEL symbol whose pins carry more than one capability is split into units, one per capability in order of first appearance, passive pins (`Column`) with the first (E56). The body graphics go to the shared unit 0 and the Value is fixed in place, so the units mesh on the sheet and show one name; the units are not interchangeable (`ki_locked`). The script puts the whole body in unit 0; the owner's hand pattern (`PanelLock`, `PanelSwitch`, `PanelSignal`) moves each half's drawing into its unit and keeps only the shared outline in unit 0.

Library cut, three libraries by where a symbol is used. Names are placeholders for the owner:

| New library | Holds | From |
|---|---|---|
| `RailroadPlant` | plant symbols: TRACK, POLICY, STRUCTURE, APPLIANCE, the layout anchor | `Railroad.kicad_sym` |
| `RailroadDevice` | every DEVICE and IODRIVER symbol, used on field and desk sheets alike; `Setting` | `RailroadField.kicad_sym`, plus `Driver-I2C-MAX7313` from the panel library |
| `RailroadDesk` | every PANEL symbol, desk and fascia; CODELINE, MACHINE, COLUMN | `RailroadPanel.kicad_sym`, plus the `Local-*` plates from the field library |

Capability words used below: `binary in`, `binary out`, `binary bidirectional` (an expander or GPIO pin that becomes in or out by what lands on it, I3), `level in`, `level out`, `level bidirectional` (in the vocabulary, on no symbol yet), `position out`, `color out`, `pixel out`; the Setting pin is passive and carries no capability.

## 2. Plant library (`Railroad.kicad_sym`, 36 symbols)

Topology, policy and structure, 20 symbols, all `keep`: `Bumper`, `IRJ`, `IRJ-END_CTC`, `IRJ-Signal`, `IRJ_Diag`, `Interlocking`, `MAIN HOUSE`, `NextCP`, `Rule105-RestrictedSpeed`, `Rule251-DoT-Left`, `Rule251-DoT-Right`, `Rule261-DoT-BiDirectional`, `Rule93-Yard Limits`, and `Milepost` (retagged Role TRACK per the 2026-10-07 ruling, "Milepost becomes a TRACK anchor"; otherwise unchanged).

| Symbol | Disposition | New name | Role | Appliance | Style | Fields | Notes |
|---|---|---|---|---|---|---|---|
| `AUXILIARY` | retag | same | APPLIANCE | lamp | non_vital | keep `CP`; drop `Kind` | Style word `non_vital`, the glossary's term (E58) |
| `AUXILIARY_TRAFFIC` | retire | | | | | | holds `NFLK`/`SFLK` on Watsonville: fleet indications the plant compiler produces itself (I29); the two instances are removed when Watsonville migrates |
| `MaintainerCall` | retag | same | APPLIANCE | lamp | maintainer_call | drop `Kind` | |
| `Mast_Single` | retag | same | APPLIANCE | mast | single | drop `Kind` | |
| `Mast_Double` | retag | same | APPLIANCE | mast | double | drop `Kind` | |
| `Mast_Dwarf` | retag | same | APPLIANCE | mast | dwarf | drop `Kind` | |
| `Signal Head - CL` | retag | same | APPLIANCE | head | CL | drop `Kind` | Role was COMPONENT; heads are appliances (ADR 0004 D6) |
| `Signal Head - CL` | copy | `Signal Head - Searchlight` | APPLIANCE | head | searchlight | drop `Kind` | the plant head the searchlight device binds to (E61) |
| `Signal Head - SemaphoreU2` | rename | `Signal Head - SemaphoreLQ2` | APPLIANCE | head | semaphore_lq | drop `Kind` | two positions, arm drops (E48) |
| `Signal Head - SemaphoreU3` | rename | `Signal Head - SemaphoreUQ3` | APPLIANCE | head | semaphore_uq | drop `Kind` | three positions, arm rises (E48) |
| `Switch_Powered`, `_Diag`, `_NO_TC`, `_Small` | retag | same | APPLIANCE | switch | powered | keep `CP`, `TC`; `Indications` to `IndicationCeiling`; drop `Kind` | four graphic forks kept |
| `Switch_Powered` | copy | `Switch_Dual` | APPLIANCE | switch | dual | as above | dual-control switch (E63) |
| `Switch_Lock` | retag | same | APPLIANCE | switch | lock | keep `CP`, `TC`, `Indications`; drop `Kind` | |
| `Switch_Manual` | retag | same | APPLIANCE | switch | manual | as above | |
| `Switch_Manual_Sensed` | retag | same | APPLIANCE | switch | manual_sensed | as above | |
| `Switch_Powered_Derail` | rename | `Derail` | APPLIANCE | switch | derail | as above | §4.1 |
| `Switch_Powered_Derail_TC` | rename | `Derail_TC` | APPLIANCE | switch | derail | as above | graphic fork kept |
| `Track Circuit`, `_RED`, `_Yellow` | retag | same | APPLIANCE | track_circuit | | keep `CP`; drop `Kind` | three graphic forks kept |
| `Virtual Indication` | rename | `Track Circuit_Virtual` | APPLIANCE | track_circuit | virtual | keep `CP`, `IndicationToken` (the circuits aggregated), `Display`; drop `Kind` | it is the virtual track circuit: Watsonville's `0100T` aggregates six circuits |
| `Contact` | copy of `AUXILIARY` | `Contact` | APPLIANCE | contact | | keep `CP` | the generic non-vital input (I23); pin as `AUXILIARY`'s |
| layout anchor | hand | name open | STRUCTURE | | | | one symbol on the root sheet for layout-scope settings (task 6) |

`Indications` is the indication ceiling, the most favourable signal indication over the switch in each position, `NORMAL/REVERSE`; the compiler validates it (`parse_switch_indications`) and route logic uses it as `bestIndication`. Drawn on three switches: Corporal derail 829D and Luchessa derail 795D `STOP/RESTRICTING`, Sargent hand switch 1 `RESTRICTING/RESTRICTING`. Renamed `IndicationCeiling`, the glossary's term, as ADR 0002 planned; the compiler reads both until the sheets migrate.

## 3. Device library (`RailroadField.kicad_sym` less the plates, plus the MAX7313)

| Symbol | Disposition | New name | Appliance | Style | Pins (old to new) and `Pin.*` | Fields | Notes |
|---|---|---|---|---|---|---|---|
| `Device-Detector-Current` | rename | `Device-TrackCircuit-Current` | track_circuit | | `~{OCC}`: binary in | drop `Kind`, `OCC` | convenience fork kept |
| `Device-Detector-Optical` | rename | `Device-TrackCircuit-Optical` | track_circuit | | `~{OCC}`: binary in | drop `Kind`, `OCC`; `Hold_ms` to `hold_ms` | convenience fork kept (I19) |
| `Device-Head-3LED` | rename | `Device-Head-CL-3Lamp` | head | CL | `~{R}`, `~{Y}`, `~{G}`: binary out | drop `Kind`, `R`, `Y`, `G` | the optional `~{L}` packaging pin is hand work, deferred until a head needs it |
| `Device-Head-3LED-Mux2` | rename | `Device-Head-CL-Mux2` | head | CL | `S0`, `S1`: binary out | drop `Kind` | a select code, no asserted state |
| `Device-Head-1LED-NeoPixel` | rename, pin added | `Device-Head-CL-RGB` | head | CL | add `RGB`: color out | drop `Kind`, `Chain`, `Index`; add `Address` (blank) | the only field symbol with no pin; the script adds one at the body's right edge, for the visual pass to tidy |
| `Device-Head-Searchlight` | copy of `Device-Head-CL-RGB` | `Device-Head-Searchlight` | head | searchlight | `RGB`: color out | `Address` (blank); `transition_ms` (blank) | after the RGB head exists (E47) |
| `Device-Head-1LED-PWM` | retire | | | | | | a single-colour PWM lamp is `Device-Lamp` on a level-out pin; lunar and position-light heads wait for their head types |
| `Device-Head-3LED-PWM` | retire | | | | | | the two-point cast on a `level out` pin replaces it |
| `Device-Head-Semaphore-Servo` | rename | `Device-Head-Semaphore` | head | semaphore_lq, semaphore_uq | `ARM`: position out; `LAMP` to `~{LAMP}`: binary out | drop `Kind`; `Stop_deg`, `Approach_deg`, `Clear_deg` to `stop_deg`, `approach_deg`, `clear_deg` | one symbol, two Styles (E48) |
| `Device-Input-Bit` | rename | `Device-Contact` | contact | | `~{IN}`: binary in | drop `Kind`, `IN` | |
| `Device-Lamp-Bit` | rename | `Device-Lamp` | lamp | | `~{OUT}` to `~{LAMP}`: binary out | drop `Kind`, `OUT`; add `Address` (blank) | one lamp type for every I/O; on a chain it carries `Address` (E30) |
| `Device-Lamp-NeoPixel` | retire | | | | | | `Device-Lamp` with `Address` on a pixel bus |
| `Device-Lamp-PWM` | retire | | | | | | `Device-Lamp` through the two-point cast |
| `Device-Switch-Sense` | rename | `Device-Switch-ManualSensed` | switch | manual_sensed | `~{N}`, `~{R}`: binary in | drop `Kind`, `N`, `R` | |
| `Device-Switch-StallMotor-Sensed` | rename | `Device-Switch` | switch | powered, lock, dual | `M`: binary out; `~{N}`, `~{R}`: binary in | drop `Kind`, `N`, `R`, `NormalIs` | one type for stall, PWM and servo machines; `~{M}` is a fork if a machine is wired the other way |
| `Device-Switch-StallMotor-Sensed-OS` | rename | `Device-Switch-OS` | switch | powered, lock, dual | as above plus `~{OCC}`: binary in | drop `Kind`, `N`, `R`, `OCC`, `NormalIs` | the 4-pin unit shape |
| `Device-Switch-Servo-Sensed` | retire | | | | | | `Device-Switch` through the two-angle cast |
| `Device-Switch-Servo-Sim`, `Device-Switch-StallMotor-Sim` | retire | | | | | | a simulated machine is not a driver type (E23) |
| `Device-Lock` | copy of `Device-Switch-Sense` | `Device-Lock` | switch | lock, dual | `~{N}` to `UNLOCK`: binary out, electrical output; `~{R}` to `~{LOCKED}`: binary in | `settle_ms` (blank) | the sense pin is optional on the sheet (E50) |
| `Driver-I2C-MCP23017` | retag | same | | | `A1..B8`: binary bidirectional | `IC=MCP23017`; keep `Address`; drop `Kind` | 4-pins-per-unit shape kept (E36) |
| `Driver-I2C-MAX7313` | retag, moved from the panel library | same | | | `A1..B8`: binary bidirectional | `IC=MAX7313`; keep `Address`; drop `Kind` | |
| `Driver-I2C-PCA9685` | copy | `Driver-I2C-PCA9685-PWM` | | | `A1..B8`: level out | `IC=PCA9685`; keep `Address`; `frequency_hz` (blank); drop `Kind` | I3 |
| `Driver-I2C-PCA9685` | copy | `Driver-I2C-PCA9685-Servo` | | | `A1..B8`: position out | `IC=PCA9685`; keep `Address`; `min_us`, `max_us` (blank); drop `Kind` | I3; the old symbol is not copied under its own name |
| `Driver-GPIO-Digital` | copy of `Device-Lamp` | | | | `~{LAMP}` to `D`: binary bidirectional, electrical bidirectional | `IC=GPIO`; Role IODRIVER | Value = the core's pin name (I22) |
| `Driver-GPIO-Analog`, `-PWM`, `-Servo` | not made | | | | | | YAGNI (owner): copies of `Driver-GPIO-Digital` with another `Pin.D` when a layout needs one |
| `Driver-GPIO-Pixel` | copy of `Device-Lamp` | | | | `D`: pixel out | `IC=GPIO` | a bus (E30) |
| `Setting` | copy of `Device-Lamp` | `Setting` | | | one pin `net`, passive | Role SETTING; Value short; `Description` the reason (E37) | |
| field processor symbol | hand | open | | | | | I31: the house implies the processor today; a `FIELDUNIT` symbol only if the emulated case needs one |

The two GPIO symbols and the two one-pin symbols are copies of `Device-Lamp` because its body is a single pin on a small box; the body can be redrawn later without changing anything the compiler reads.

## 4. Desk library (`RailroadPanel.kicad_sym`, plus the `Local-*` plates)

Structure, 9 symbols, all `keep`: `Codeline-Encoding-AAR`, `-Bits`, `-US&S-506`, `Codeline-Transport-CMRInet`, `-Loconet`, `-MQTT`, `-TimeCode`, `CtcMachine`, `PanelColumn`. `Driver-I2C-MAX7313` moves to the device library.

| Symbol | Disposition | Appliance | Style | Pins (old to new) and `Pin.*` | Fields | Notes |
|---|---|---|---|---|---|---|
| `PanelSwitch` | retag | lever | switch | `~{NWS}`, `~{RWS}`: binary in; `~{NWK}`, `~{RWK}`: binary out | drop `Kind`, `NWS`, `RWS`, `RWK`, `NWK` | tokens derive as Value plus pin (I28) |
| `PanelSignal` | retag | lever | signal | `~{NGS}`, `~{HS}`, `~{SGS}`: binary in; `~{NGK}`, `~{SGK}`, `~{TEK}`: binary out | drop `Kind` and the six token blanks | |
| `PanelLock` | rename pins | lever | lock | `WLS` to `~{UNUSED}`: binary in; `~{WLS}`: binary in; `~{WLK}` to `~{WLQK}`: binary out; `WLK` to `~{WLK}`: binary out | drop `Kind`, `WLS`, `WLK`; add `Invert=WLK` | E54, E55. Check the plate's graphic text for the old names (visual pass) |
| `PanelCode` | retag | lever | code | `~{CODE}`: binary in | drop `Kind`, `CODE` | no join (I28) |
| `PanelMCall` | retag | lever | maintainer_call | `~{SW}` to `~{S}`: binary in | drop `Kind`, `Vital`, `ControlToken`, `SW` | E45 |
| `PanelAuxiliary` | retag | lever | non_vital | `~{SW}` to `~{S}`: binary in | drop `Kind`, `Vital`, `ControlToken`, `SW` | token `<Value>S` |
| `PanelLamp-RED`, `-YELLOW`, `-GREEN`, `-AMBER`, `-BLUE` | retag | lamp | indication | `~{LAMP}`: binary out | keep `Color`, `IndicationToken`; drop `Kind`, `LAMP` | five colour forks kept |
| `Local-Switch` | retag, moved from the field library | lever | switch | as `PanelSwitch` without `Column` | drop `Kind` and the four blanks | |
| `Local-Switch-NoLamp` | retag, moved | lever | switch | `~{NWS}`, `~{RWS}`: binary in | drop `Kind`, `NWS`, `RWS` | fork kept |
| `Local-Lock` | rename pins, moved | lever | lock | `~{WLQ}`: binary in; `~{WLQK}`: binary out; `WLK` to `~{WLK}`: binary out | drop `Kind`, `WLK`, `WLQ`, `WLQK`; add `Invert=WLK` | E54 |
| `Local-Lamp` | retag, moved | lamp | indication | `~{LAMP}`: binary out | keep `Color`, `IndicationToken`; drop `Kind`, `LAMP` | |
| `Local-Lamp-NeoPixel` | retire | | | | | `Local-Lamp` with `Address` on a pixel bus; it has no pin today |
| `Local-Lamp-PWM` | retire | | | | | `Local-Lamp` through the two-point cast |

`Column` pins carry no `Pin.*`: membership, not a function (E41).

## 5. Counts

| | Plant | Device | Desk | Total |
|---|---|---|---|---|
| keep | 14 | 0 | 9 | 23 |
| retag or rename, mechanical | 20 | 12 | 15 | 47 |
| copy, mechanical | 3 | 8 | 0 | 11 |
| made, with a pin added by the script | 0 | 2 | 0 | 2 |
| retire | 1 | 8 | 2 | 11 |
| output symbols | 38 | 20 | 24 | 82 |
| of which split into units (E56) | 0 | 4 | 5 | 9 |
| of which hand-finished and carried over (E57) | 0 | 2 | 3 | 5 |

Hand work left: the layout anchor body (task 6), the field processor symbol if I31 needs one, the optional `~{L}` pin on the three-lamp head when a head needs it, the visual pass over the RGB head's pin placement, and the graphics of the six script-split symbols. Everything else was the script.

## 5a. On the SPCoast sheets

The sheets place 62 distinct symbols. Instance counts from the `lib_id`s (multi-unit symbols counted once):

| On the sheets | Instances | Action when the sheet migrates |
|---|---|---|
| plant symbols kept or retagged (heads 48, IRJ 48, circuits 61, masts 35, houses 11, switches 30, rules 24, ...) | about 400 | remap `Railroad:` to `RailroadPlant:`, drop the instance's `Kind`, rename `Indications` on the three switches |
| `Switch_Powered_Derail` | 2 | remap and rename to `Derail` |
| `Virtual Indication` (Watsonville) | 2 | remap and rename to `Track Circuit_Virtual` |
| `AUXILIARY_TRAFFIC` (Watsonville) | 2 | remove: the compiler produces `NFLK`/`SFLK` |
| desk plates and lamps (`PanelLamp-*` 42, `PanelMCall` 8, `PanelSwitch` 7, `PanelLock` 7, `PanelCode` 7, `PanelSignal` 4) | 75 | remap `RailroadPanel:` to `RailroadDesk:`; pins keep their numbers so wires hold; drop the blanks and `ControlToken`, `Vital` on instances |
| `Driver-I2C-MAX7313` | 14 | remap to `RailroadDevice:` |
| `PanelColumn`, `CtcMachine`, codeline symbols | 23 | remap only |
| `Driver-I2C-MCP23017` (Sargent 2) | 2 | remap; `IC` arrives with the symbol |
| `Driver-I2C-PCA9685` (Sargent `0x27`) | 1 | **a real conflict**: it drives head 836SA's three lamps and head 836SB's servo arm and lamp on one chip, which I3 refuses. Sargent needs a second chip, or the lamps on the MCP23017. The drafter chooses `-PWM` or `-Servo` per chip. |
| `Device-Head-3LED-PWM` (836SA) | 1 | substitute `Device-Head-CL-3Lamp`; the cast replaces the symbol |
| `Device-Head-Semaphore-Servo` (836SB) | 1 | rename; `LAMP` keeps its number |
| `Device-Detector-Optical` | 3 | rename |
| `Device-Switch-StallMotor-Sensed-OS`, `Device-Switch-Sense`, `Device-Lamp-Bit` | 3 | rename |
| `Device-Lamp-NeoPixel` | 1 | substitute `Device-Lamp` with an `Address`; the old symbol had no pin, so this one is drawn |
| `Local-Switch`, `Local-Lock` | 2 | remap to `RailroadDesk:`; `Local-Lock`'s `WLK` pin becomes `~{WLK}` with `Invert` arriving on the symbol |

The gate for each sheet: a netlist exported before and after, compared by reference and pin number. Identical connectivity; only names and fields differ. Sargent first (checkpoint step 6).

## 6. Execution, as run (2026-10-10)

1. Done: the owner's markup, as the rulings above.
2. Done, then reversed: Railroad branch `feat/symbol-libraries`, baseline commit bdb0fd9 with the three source libraries byte-identical under `symbols/`; dropped again on 2026-10-11, the recipe reads InterlockingPlant directly.
3. Done: `tools/contract/apply_symbol_recipe.py` wrote the three new libraries; the second commit is the recipe applied.
4. Done by the script after all: `Device-Lock` and the GPIO symbols are copies with pins renamed; the RGB head and searchlight got their pin from the script. Left by hand: the layout anchor and, if needed, the processor symbol.
5. Done: `tools/contract/lint_symbol_fields.py`, 81 symbols, 0 errors; 80 after step 9.
6. Done: `kicad-cli sym export svg` renders every symbol; `tools/contract/symbol_contact_sheet.py` writes `symbols/production/contact-sheet.html`, each symbol baseline beside every unit of its output, retired ones last. Inspected: PanelLock, Device-Lock, GPIO, the RGB head, the split switch and semaphore.
7. Left to the owner: the global `sym-lib-table` entries `RailroadPlant`, `RailroadDevice`, `RailroadDesk` beside the old nicknames; the old libraries stay registered until the last sheet migrates. Railroad's AGENTS.md reversed in the PR.
8. Done (2026-10-11): the owner's `Terminal` question, discussed first. Singletons were the owner's expectation; the answer was multi-unit symbols, which retire `Terminal` outright (checkpoint E56). The owner drew `PanelLock`, `PanelSwitch` and `PanelSignal` as two-unit symbols in the editor (a paste had doubled every pin and some graphics; deduplicated by text, exact duplicate items within a unit) and gave the PCA9685 PWM and Servo symbols differentiation graphics.
9. Done: `Terminal` deleted; the recipe reads InterlockingPlant, splits the other six symbols by capability, carries the five hand-finished symbols over (`HAND_FINISHED`), writes symbols in KiCad's sorted order so the editor's saves diff small; the lint checks one capability per unit, `ki_locked` and the fixed Value, and the shared parser reports units. 80 symbols, 0 errors; the owner's five symbols byte-identical through a regeneration.
10. Done: the vocabulary check before the cutover (E58 to E61): `non_vital` for `auxiliary`, `color out`, `Signal Head - Searchlight`, the head Styles defined in the glossary (FieldUnit branch `docs/head-styles`). 81 symbols, 0 errors.
11. Done: switch Styles settled (E63): `manual` kept, `Switch_Dual` added, `dual` on the switch and lock device Style lists; the switch terms in the glossary and FieldUnit ADR 0006 proposed. 82 symbols, 0 errors.

## 7. Open after the run

1. The visual pass in KiCad, from the contact sheet: the RGB head's pin position; any label the `texts` action did not know about; the six script-split symbols, whose every unit carries the whole body until their graphics are distributed by hand (then add each to `HAND_FINISHED`).
2. Sargent's PCA9685 conflict (§5a), to resolve when Sargent is redrawn.
3. The layout anchor symbol and the field processor symbol (checkpoint task 6, I31).
4. `level bidirectional` is in the vocabulary and on no symbol; the GPIO level, servo and analog symbols wait for a need.
