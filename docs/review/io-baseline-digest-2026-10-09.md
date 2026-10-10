# I/O baseline digest (2026-10-09)

- Status: a digest of facts for the owner's line-by-line check. It proposes nothing. The alternatives ADR comes after this check.
- Reading rule (owner, 2026-10-09): `driver-architecture-foundation.md` governs where it clarifies or contradicts any other document. FieldUnit ADR 0004 below its R-text, the rejected ADR 0005 draft, the survey report's own inferences, and the delivery classes in the (Role, Kind) table are evidence, not direction. The legacy sketches (`CP_Christopher`, `CP_Corporal`, `spcoast_ctc`) are informative and expendable.
- Paths: `FU/` = `~/Dropbox/Arduino/libraries/FieldUnit`, `Sub/` = this repo, `KiCad/` = `~/Dropbox/KiCad/Railroad/SPCoast`, `Sym/` = `~/Dropbox/KiCad/InterlockingPlant/symbols`.
- Netlist: generated on demand today with kicad-cli 10.0.1 from `KiCad/SPCoast.kicad_sch` into the session scratchpad. Every pairing in §2 was read from that netlist, not from coordinates. Watsonville is not cited.

## 1. The picture

Two flows. The interlocking half of each flow exists. The I/O half does not.

```
                  flow 1: compile                          flow 2: generate or load
KiCad drawings ─────────────────▶ Layout Data Model ─────────────────────────▶ unit (field or office)
 plant sheets        exists        interlocking plant      exists (PlantSerializer)   vital logic, data-driven
 field I/O (Sargent) missing       I/O: nothing            missing                    I/O layer: hand-typed per sketch
 desk Panel sheets   exists        desk bindings, a fragment   nothing reads it        desk I/O: hand-typed PanelIO
```

| Half | Flow 1: drawing to model | Flow 2: model to unit |
|---|---|---|
| Interlocking plant | `Sub/tools/plant_graph` emits `interlocking-plant/v1` | `FU/src/PlantSerializer.h` builds the plant from JSON |
| Field I/O | Nothing. The plant compiler reports every DEVICE and IODRIVER symbol as `unknown_symbol` (`compiler.py:46-70, 847-856`) | Nothing. Each sketch types expanders, bits and drivers by hand |
| Desk I/O | `Sub/tools/controller_graph` emits `DriveBinding` rows (address, bus kind, bit, active-low) | Nothing reads them. `PanelIO` in the sketch holds the bits |

The session's motivation is the two missing cells: the I/O part of the model, and the FieldUnit layer that consumes it.

## 2. What the drawings represent today

Hierarchy: `SPCoast.kicad_sch` → `South-cTc.kicad_sch` → `<plant>.kicad_sch` → `<plant>-Panel.kicad_sch`. The desk columns live in the per-plant Panel sheets. `South-cTc` holds the CtcMachine, four code line transports and one encoding, and no columns.

### 2.1 Field side (one sheet: Sargent)

Field I/O is drawn on `Sargent.kicad_sch` only, on the plant sheet among the appliances. No other plant sheet has a DEVICE or IODRIVER symbol.

| Fact | How it is drawn | Netlist check |
|---|---|---|
| Bus instance | One IODRIVER symbol per chip. Kind `I2C-MCP23017` (0x20, 0x21) and `I2C-PCA9685` (0x27). Value is the address | 3 instances, 12 unit placements |
| Channel | Library pin names `A1..A8`, `B1..B8` | Present as pin functions |
| Part to channel | A device pin placed on an expander pin. No wires, no labels | 26 nets, each with exactly two nodes |
| Direction | The device pin's electrical type: `input` (lamp, motor, servo, head), `output` (contact, detector). Expander pins `bidirectional` (MCP23017) or `output` (PCA9685) | The netlist carries `pintype` on every node |
| Polarity | Pin name `~{X}` on the library symbol | Pin functions show `~{OCC}`, `~{N}`, `~{R}`, `~{OUT}`, `~{WLQ}` |
| Device to appliance | The device Value equals an appliance Value on the same sheet: `835`, `1`, `1NAT`, `1SAT`, `2SAT`, `MC1`, `HBA`, `836SA`, `836SB` | Not a net. A string match |
| Head devices | `836NA`, `836NB` have no literal appliance. The plant has `Mast_Double` `836NAB` with heads `A` and `B` | Composite name `<mast><letter>`, by implication |
| Appliance settings | `Hold_ms=1500` on each detector, `NormalIs=HIGH` on 835, the semaphore angles on 836SB left empty, `Chain=A Index=1` on HBA | Symbol properties |
| Fascia controls | `Local-Switch 835` and `Local-Lock 835`, Role PANEL, on the field expander 0x20 A1 to A8 | 7 nets |
| NeoPixel lamp HBA | `Device-Lamp-NeoPixel` has no pins. Nothing models the chain | Absent from the netlist |
| Unused expander pins | No-connect flags, 22 on Sargent | |

The rejected draft's worked decomposition, which was inferred from Values without a netlist, matches the netlist on every bit except the semaphore: the drawing has `ARM` on 0x27 A5 and `LAMP` on A6, not A4 and A5.

### 2.2 Desk side (per-plant Panel sheets)

| Fact | How it is drawn |
|---|---|
| Column | `PanelColumn`, Value = column number, properties `Interlocking`, `CP Name`, `Machine` (a string, not a wire). Eight `free` pins |
| Column membership | A lever's or lamp's pin 1 placed on a PanelColumn pin. No wires |
| Bus instance | `Driver-I2C-MAX7313`, Value = address, one per column |
| Lever or lamp to channel | Pin placed on an expander pin. Sargent-Panel: 10 nets, each with two nodes |
| Lever identity | Value only (`783`, `784`, `795`, `799`, `835`). No token property on `PanelSwitch`, `PanelSignal`, `PanelLock` |
| Lamp identity | `IndicationToken`, a comma list (`795T1,01T,799T1`), sometimes cross-plant (`Luchessa:NFLK`, `Watsonville:837T1`). Value is a legend label (`TRACK`, `OS`, `MC`) |
| Control identity | `ControlToken` on `PanelMCall` and `PanelAuxiliary`, default `${VALUE}S` |
| Direction and polarity | As on the field side: pin electrical type and `~{X}` |
| Code line | Encodings on the Panel sheet, transports on `South-cTc`, joined by global labels |

### 2.3 Libraries

| Library | Symbols | Notes |
|---|---|---|
| `RailroadField` | 18 DEVICE, 6 `Local-*` (Role PANEL), 2 IODRIVER | No MAX7313, no encoder, no chain driver, no GPIO. `Device-Head-3LED-Mux2` is a DEVICE Kind. The two NeoPixel symbols have no pins. PCA9685 default `Address` is 0x20. Field drivers' Value is `${ADDRESS}` while the property is `Address` |
| `RailroadPanel` | `PanelColumn`, `Driver-I2C-MAX7313`, five `PanelLamp-<colour>`, `PanelSwitch`, `PanelSignal`, `PanelLock`, `PanelAuxiliary`, `PanelMCall`, `PanelCode`, `CtcMachine`, 3 encodings, 4 transports | `CtcMachine` and `PanelColumn` have no Kind |

Not drawn anywhere: a flash regime, the field unit or processor that hosts a device, a pull-up (derived from an asserted-low input on a programmable pin), a GPIO pin, a remote I/O node.

## 3. What the Layout Data Model carries today

| Source | I/O content |
|---|---|
| `Sub/schemas/interlocking-plant/v1.json` | None. `additionalProperties: false`. Its description says realization bindings are separate contracts |
| `Sub/profiles/spcoast_south/cps/generated/Luchessa.json` and its `projectionDeferred` sidecar | None |
| `Sub/tools/plant_graph` | None. Part kinds are keyed by symbol name (`compiler.py:46-70`), not by `(Role, Kind)`. DEVICE and IODRIVER symbols raise `unknown_symbol` |
| `Sub/tools/controller_graph` | `DriveBinding(appliance, function, driver address, bus_kind, bit, active_low)` from the net walk (`compiler.py:356-421`, `types.py:83-92`). Bit from `A1..B8` (`:44-55`), polarity from `~{X}` (`:68-74`). No direction field. Diagnostics for shared bits and unbound functions. Nothing consumes it |
| `Sub/docs/design/layout-model.md` rev 8 | §5 says `fieldUnits` rows exist only for drawn hardware and cites a "§5a field hardware sheet". No §5a exists in rev 8 |
| `Sub/schemas/symbols/role-kind.toml` | 68 rows on branch `feat/role-kind-table`. DEVICE rows name delivery classes that do not exist in FieldUnit (`Head3LedPwmDriver`, `LampNeoPixelDriver`, `Pca9685IOBus`, …). The foundation (§4) lists the Kind-as-product shape as in dispute, so these rows are a lint target, not a decision |
| `Sub/schemas/context/keys.toml` | 8 namespaces, 14 keys. `timing.flash_ms` says "one shared phase per field unit", which the owner's flash ruling supersedes |

## 4. What FieldUnit has today

The vital objects are data-driven: `PlantSerializer::deserialize` (`FU/src/PlantSerializer.h:506`) builds circuits, switches, derails, crossovers, signal controls, masts (`type` = head count), detector locks and routes from JSON, and skips keys it does not know (`:258`). No hardware fact is in that JSON.

The device interface, as evidence:

| Element | Shape today | Source |
|---|---|---|
| `IOBus` | `readBit(InputBit)`, `writeBit(OutputBit, bool)`, `writeAngle(device, channel, deg)`, `flush()`. No begin, configure, direction, pull-up, duty or pixel | `FU/src/drivers/IOBus.h:9-16` |
| `IOBit` | `{device, offset, bitIndex, Polarity}`; direction is the C++ type `InputBit` or `OutputBit` | `IOBit.h:20-49` |
| Polarity | Inverted in software in every bus | `IOBus.h:41,48`, `I2CexpanderIOBus.h:31,39`, `CmriIOBus.h:34,44` |
| Expander direction | Set outside the bus by the sketch, `I2Cexpander::init(addr, type, mask)`; MCP23017 pull-ups follow the input mask | `I2CexpanderIOBus.h:17`, `I2Cexpander.cpp:433-470` |
| Drivers | One class per appliance type, with the pins in the constructor: `SwitchDriver` (motor bit, two contacts; classifies MOVING and OUT_OF_CORRESPONDENCE itself), `TrackCircuitDriver`, `SignalMastDriver` (up to three heads of R/Y/G/L bits, 1 Hz flash inline, a `switch` over `Aspect`), `SemaphoreDriver`, `CplMastDriver`, `MockSwitchDriver` | `FU/src/drivers/*.h` |
| Attachment | `ApplianceDriver::setAppliance(void*)`; `IoBitDriverPolicy` holds fixed arrays of three driver types; `overrideDriver(name, driver)` resolves the name as switch, then circuit, then mast | `DriverPolicy.h:21-27, 105-123, 164-232` |
| MQTT | `MqttApplianceBus` binds the whole plant by name convention, the one derived binding | `MqttApplianceBus.h:121-131` |
| Desk | `PanelHardware::read(column, function)` and `write(column, function, bool)`; the column-to-bit map lives in the sketch | `FU/src/cTcMachine.h:100-109` |
| Tick | `sampleInputs → evaluateVitalRules → driveOutputs` | `FU/src/InterlockingPlant.h:504-516` |

Sketches, evidence only: `CP_Christopher` and `CP_Corporal` build plant, expanders, bit literals and drivers by hand and call the drivers from the loop; `Universal_FieldUnit` loads JSON and has no I/O at all; `spcoast_ctc` holds the desk bits in `IO-I2C.h` and `IO-CMRI.h` with `col-1` arithmetic. The plant host (`Sub/runtime/plant_host`) has no bus and uses `overrideDriver` with a simulated switch driver. Defects seen in passing, recorded for evidence and not for the design: both field sketches initialise their expanders with every pin as an input; the two desk headers disagree on which bit is the normal contact; `CmriIOBus` ignores `device`.

## 5. The I/O fact ledger

Every fact a unit needs to bind an appliance to hardware, with where it lives today.

| Fact | In the drawing | In the model | In the unit | Foundation or ruling |
|---|---|---|---|---|
| Bus instance: kind, address | IODRIVER symbol Kind and Value | Desk: yes. Field: no | Sketch constant | Brainstorm B: IODRIVER symbols are the bus instances |
| Channel index on a bus | Library pin name `A1..B8` | Desk: bit 0..15. Field: no | Bit literal | Sub 0004 D8: pin N is bit N-1 |
| Part to channel | Two-node net | Desk: yes. Field: no | Constructor argument | Principle 9: from the netlist |
| Direction | Device pin electrical type; netlist `pintype` | No (desk infers from the function name) | C++ type | Principle 12, R6 |
| Polarity | `~{X}` pin name | Desk: `active_low`. Field: no | `Polarity` enum, software inversion | Principle 7 (an attribute); asserted-low norm |
| Pull-up | Not drawn; derivable | No | Follows the input mask | Memory 2026-10-07: derived, never on the driver symbol |
| Device to appliance | Value string match on one sheet | No | `findSwitch("835")` by hand | Principle 10 |
| Head identity (mast, letter, order, dwarf, display Kind) | Mast and head symbols on the plant sheet; device Value `836NA` | Heads: `headLetters` in v1. Device link: no | `head1()..head3()` by position | R7: an opaque handle; D6 heads are appliances |
| Device Kind to logic block | Role and Kind on the library symbol | No | Class chosen by hand | §4: the Kind-as-product shape is in dispute |
| Appliance settings | Symbol properties (`Hold_ms`, `NormalIs`, angles, `Fade_ms`, `Color`, `Chain`, `Index`) | No | Constants or absent | R2 appliance context; KEYS 7-10 |
| Layout context (era, rulebook, timing, colour, light, clock, mode) | Not drawn | `keys.toml` registry only | Inline (1 Hz flash, 2000 ms travel) | R9; flash ruling: several regimes per unit |
| Token binding of a lamp or control | `IndicationToken`, `ControlToken` | Desk: yes | `configureDesk()` by hand | Principle 10 |
| Column membership | PanelColumn pins | Desk: yes | `col-1` arithmetic | Membership pin, RK 21 |
| Encoder (mux, chain) | `Device-Head-3LED-Mux2` Kind; NeoPixel `Chain`/`Index` with no pins | No | `CplMastDriver` marker map | Ruling: encoders are their own symbols between device and expander; §3.5: an encoder is a driver |
| Field unit that hosts a device | The sheet the device sits on | No | The sketch is the unit | Sub 0004 D13 |
| Remote I/O node (CMRI, MQTT) | Not drawn | No | `CmriIOBus`, `MqttApplianceBus` | Seam 2 remote I/O; transport catalog |
| Maintainer and lamp-test access by part name | Not drawn | No | None | Brainstorm: `2NA.Y` addressable without the interlocking |

## 6. Discrepancies

The reading rule settles the first group. The second group is open because the foundation's own text is silent or says two things.

### Settled by the foundation

| Topic | Foundation | Other source | Effect |
|---|---|---|---|
| Seam numbering | Seam 1 code line, Seam 2 hardware I/O, local or remote, panel and field | ADR 0004 and the draft: SEAM-0 code line, SEAM-1 hardware, SEAM-2 remote link | The table's and lint's comments cite the old numbering |
| Encoder | A driver, drawn as a symbol between device and expander | Draft 0005: a new Role `ENCODER`, a "pure transform" distinct from drivers | No new Role is ruled |
| 74HC595 on a head | An encoder (owner ruling) | Draft 0005 D15: an IODRIVER row | |
| Flash | Several synchronized regimes per unit (owner ruling) | `keys.toml timing.flash_ms`: one phase per unit; draft D10: one flasher | The key's meaning is stale |
| Appliance | GCOR text; MC is an appliance and not vital | G 115 "a device the field unit operates or reads"; draft: "a vital object" | Glossary amendment pending |
| Era | A layout context input (R9) | `ontology.md:17`: not a model input | |
| Delivery classes per Kind | Kind = appliance × domain product is in dispute (§4) | `role-kind.toml` DEVICE rows name one class per product Kind | Rows are lint targets, not decisions |
| Stall motor | Binary, held against a stop; not a Position (owner correction) | `SWITCH_SERVO_*` rows treat position as the general case | |

### Open in the foundation's own text

| Topic | What the text says | Why it matters |
|---|---|---|
| Primitive set | §3.5 lists Toggle (on/off), Level (0 to 100%), Position, Contact, numbered 2 to 5, with Lamp as a conglomerate (Toggle + Level + blinking). The brainstorm (§4 Composition, memory) lists Light, Level (binary held, a stall motor), Position, Contact | "Level" means an analog ratio in one list and a held binary in the other. A stall motor is a Toggle under §3.5. Item 1 of the §3.5 list is missing |
| Device | "a Symbol that represents one physical electromechanical sensor that is wired to a host" | Actuators (motor, lamp, servo) are devices too. Sensor only is narrower than the symbol set |
| IODRIVER symbol | §3.5: a driver is a logic function represented by a symbol, and an encoder is a driver. Gaps: "driver: the R0 software translator versus the IODRIVER symbol" | Whether the expander symbol is a third driver family (channel vocabulary to chip) or something else |
| Head device name | `836NA` binds head A of `836NAB` by implied composite name. AGENTS: a head Value is one letter | A naming rule is needed for the device to head join. ADR 0003 (name grammar) is frozen |
| Sargent 836SB | Plant head drawn `Signal Head - CL`, device `Device-Head-Semaphore-Servo` | Either a deliberate test case for the compatibility check or a drawing slip |
| Flash regime | Term undefined; where a regime is declared (per light, per head Kind, per unit) is unsaid | Ruled behaviour with no home in the drawing or the context registry |
| Scope edge | Out: the generators. In: the model the compiler emits and "(looking ahead)" the generator that consumes it | This session's motivation needs the I/O content of the model and the consuming contract in FieldUnit, not the generator itself |

## 7. Memory entries reviewed

| Memory | Verdict |
|---|---|
| `spcoast-driver-architecture-direction` | Owner rulings are consistent with the foundation. Its plan line ("a fresh ADR 0005") is stale: that draft was rejected. Updated to point at the foundation and this digest |
| `spcoast-io-polarity-decisions` | Owner rulings of 2026-10-07. Consistent with principle 12 and the netlist. Kept |
| `feedback-architecture-adr-method` | Method, not design. Kept |
| `spcoast-logical-model-principles`, `spcoast-three-ecosystems-partial-compile` | One compiler, one model, generators consume parts. Consistent with `goals.md`. Kept |

No memory entry encodes the seam numbering, the Kind-as-product rows, or the one-flasher rule.

## 8. Questions for the owner

One list. Each has a default in italics that this session will assume if unanswered.

1. Primitives: Toggle, Level (0 to 100%), Position, Contact per §3.5, with Light and Lamp as conglomerates and a stall motor as a Toggle? *Default: §3.5 governs; the brainstorm's "Level" was the binary case and is renamed.*
2. Is the IODRIVER (expander, bus) symbol a driver in the §3.5 sense, making three driver families: device, encoder, bus? *Default: yes.*
3. Device definition: sensors and actuators? *Default: both.*
4. Head device to head join: accept `<mast><letter>` as the rule? *Default: yes, as a drawn Value, checked by the compiler.*
5. Sargent 836SB: a test case for the head compatibility check? *Default: yes; it stays as drawn.*
6. Scope for this session: define the I/O section of the layout model and the FieldUnit contract that consumes it; leave the generator's output form open per AGENTS "Direction"? *Default: yes.*
7. Flash regime: a named term and a declaration point? *Default: a layout-context namespace of named regimes; each light names its regime through its device Kind's row.*

## 9. Could not verify

- `I2Cexpander::init` for MAX7313 (pull-ups on the desk chips).
- Whether `${ADDRESS}` resolves against the property `Address` in KiCad (case).
- `spcoast_ctc_bench` and `FieldUnit_Tracer` were not read.
