B)# Appliance driver subsystem: survey and summary (2026-10-08)

Read-only survey by a Fable sub-agent, briefed with the order of authority, the glossary, the owner's R0 (FieldUnit `docs/adr/0004-driver-seam.md`), the three-seam / A-B-C deployment model and the Matter/Zigbee cluster vocabulary. No files edited. Paths: `FU/` = `~/Dropbox/Arduino/libraries/FieldUnit`, `Sub/` = `~/Dropbox/workspace/FieldUnit-Subdivision`, `Sym/` = `~/Dropbox/KiCad/InterlockingPlant/symbols`.

**Order of authority (governs this report):** (1) the relay model and AAR practice, `FU/docs/GLOSSARY.md` §10.6; (2) `FU/src/`, defective where it differs from (1); (3) KiCad-derived models (symbol libraries, drawings); (4) legacy sketches and harvested profiles, evidence only. Watsonville is not cited. Vocabulary per the glossary: *head appearance* (`head1()`…), *aspect* = whole signal, *signal indication*, *appliance*, *field unit*, *office unit*; `FU/docs/GLOSSARY.md:321` already records that `Aspect` mixes head appearances and aspects.

**Owner's latest word:** R0 and his notes on R1–R9 in `FU/docs/adr/0004-driver-seam.md:12-71` (commit `2b911f7`). Everything below "## Context" in that file is the bottom-up draft under re-examination.

## 1. Inventory of hard-coded drivers (`FU/src/drivers/`)

| Class | Serves | Reads | Writes | Attach surface | Hard-codes | Reads beyond own appliance |
|---|---|---|---|---|---|---|
| `SwitchDriver` (`SwitchDriver.h:12-64`) | one `Switch` | `commandedPosition()`; 2 `InputBit` contacts | `writeBit(motor, cmd==NORMAL)`; `sw->updateFeedback(N/R/OOC/MOVING)` | ctor `(Switch*, OutputBit, InputBit, InputBit)` | motor polarity = "Normal is true" (no `NormalIs`); contact classification: both closed → `OUT_OF_CORRESPONDENCE`, neither → `MOVING` (`:38-48`), a vital judgment made in the driver | no |
| `TrackCircuitDriver` (`:9-28`) | one `TrackCircuit` | 1 `InputBit` | `tc->update(occ, Quality::GOOD, now)` | ctor `(TrackCircuit*, InputBit)` | quality always `GOOD`; no hold (the optical release hold lives in `TrackCircuit::dropoutDelayMs_`, `TrackCircuit.h:12,60-87`) | no |
| `SignalMastDriver` (`:17-92`) | one `SignalMast`, up to 3 heads | `mast_->head1/2/3()` | `writeBit` R/Y/G/L per head | `ctor(SignalMast*)` + `addHead(R,Y,G,L)` | max 3 heads (`:24`); 1 Hz flash `nowMs%1000<500` (`:32`); per-head `switch` on `Aspect` that also lists whole-mast values `RED_OVER_GREEN`… (`:43-81`); fixed 4-colour pin set | no |
| `SemaphoreDriver` (`:19-69`) | one `SignalMast`, up to 3 arms | `head1/2/3()` | `writeAngle(device, channel, deg)` | `ctor(SignalMast*)` + `addArm(dev, ch, 0, 45, 90)` | angles default 0/45/90; colour→angle collapse (flashing folded into steady, lunar→stop, `:46-61`); no lamp, no daylight, no motion | no |
| `CplMastDriver` (`:36-118`) | one `SignalMast` (one head + 6 markers) | `head1()`, `markers()` | `writeBit` ×10 | `ctor(SignalMast*)`, `setDiskPins`, `setMarkerPins` | 1 Hz flash (`:55`); marker bit→pin map | no |
| `MockSwitchDriver` (`DriverPolicy.h:33-70`) | one `Switch` | `reportedPosition()` vs `commandedPosition()` | `updateFeedback(commanded)` after `travelTimeMs` | `ApplianceDriver::setAppliance(void*)` | travel 2000 ms; no IOBus at all | no |

Framework: `ApplianceDriver` (`DriverPolicy.h:21-27`) is `setAppliance(void*)`, `sample(now)`, `drive(now)`: type-erased, no IOBus or context parameter. `DriverPolicy` (`:76-81`) is plant-wide `sampleAll/driveAll`; `IoBitDriverPolicy` (`:164-232`) holds fixed arrays of 32 `TrackCircuitDriver`, `SwitchDriver`, `SignalMastDriver` only (no Semaphore/CPL slot) and calls `io_->flush()` after masts. `InterlockingPlant::overrideDriver(name, driver)` (`:105-123`) resolves the name against Switch→TrackCircuit→SignalMast. Tick order `sampleInputs → evaluateVitalRules → driveOutputs` (`FU/src/InterlockingPlant.h:504-516`).

`MqttApplianceBus` (`MqttApplianceBus.h:34-323`) is not an `IOBus`: it binds `TrackCircuit*`/`Switch*`/`SignalMast*` directly, includes `InterlockingPlant.h` (`:13`) and `bind(InterlockingPlant&)` walks every appliance (`:121-131`). Ingress writes `tc->update` and `sw->updateFeedback` (`:144-159`); egress publishes `commandedPosition()` as CLOSED/THROWN and a JMRI aspect name derived from the *Indication* (`:190-200, 208-246`). It is the one "driver" that sees the whole plant.

Office side has a second, unrelated seam: `PanelHardware::read(column, PanelInput)/write(column, PanelOutput, bool)` (`FU/src/cTcMachine.h:100-109`), lamps written from the `IndicationVector` in `PanelColumn::applyIndications` (`:224-258`), enumerated by function (`SW_NORMAL_LAMP`, `TRACK_LAMP_1..6`), not by token. The desk sketch's `PanelIO` (`FU/examples/spcoast_ctc/IO-I2C.h:35-52`) hard-codes `colToDev = col-1` and input mask `0x1EC4`; its only "flash" is a 120 ms code-pulse blink (`spcoast_ctc.ino:454`). The `WLQK` blink ruled in Sub ADR 0004 D4/D5 has no home on either seam today.

## 2. The IOBus family

`IOBus` (`IOBus.h:9-16`): `readBit(InputBit)`, `writeBit(OutputBit, bool)`, `writeAngle(device, channel, deg)` (default no-op), `flush()`. Nothing else.

- **Addressing/polarity/direction:** `IOBit{device, offset, bitIndex, Polarity}` (`IOBit.h:20-35`); direction is a compile-time type (`InputBit`/`OutputBit`, `:39-49`). Polarity is inverted in software inside every bus (`IOBus.h:41,48`; `I2CexpanderIOBus.h:31,39`; `CmriIOBus.h:34,44`). No bus configures expander direction, pull-ups, or chip inversion; `I2CexpanderIOBus` takes a pre-configured `I2Cexpander[]` (`:17`). ADR 0003 D6/D8 (asserted-low norm, pull-up where an active-low input is attached) is unimplemented.
- **Missing for other domains:** no duty write (PWM lamps/heads), no frequency/drive-mode config, no pixel write (chain, index, colour), no servo speed, no `begin/end`, no capability query or refusal, no fault/quality return path, no shared flash phase.
- **CMRI vs I2C:** `CmriIOBus` ignores `device`, treats `offset` as byte index into IB/OB arrays (`:29-30, 39-40`); same bit semantics, no angle. It is a SEAM-2 adapter with a SEAM-1 vocabulary.
- **MQTT:** not an IOBus; its vocabulary is already appliance-level (sensor/turnout/signalmast topics), so the "translation" there is near-identity and the appliance objects themselves are the surface.
- **Mock:** `MockIOBus` holds bits and angles, `setPinState` for tests (`IOBus.h:19-93`).

## 3. Indication → appearance path

`Route` → `SignalMast::setIndication(ind)` (`FU/src/SignalMast.h:102-109`) → `AspectResolver policy_(ind, headCount, isDwarf)` (`SignalAspectPolicy.h:24`) → `MastAspects{head1, head2, head3, markers}` → drivers read `head1()…`, `markers()`. `compositeAspect()` (`SignalMast.h:81-99`) recombines heads into a whole-mast `Aspect` for MQTT only. `MastType` is ONE/TWO/THREE/DWARF (`:9-14`); `headCount` is derived from it, not from the drawing's heads.

**What `Aspect` conflates** (`FU/src/types.h:118-142`): (a) a head appearance (`RED`, `FLASHING_YELLOW`); (b) a whole-signal aspect (`RED_OVER_GREEN`); (c) a technology-neutral colour that other technologies borrow: position-light rows are wired to colour pins (`FU/docs/how-to/04…md:135-139`), the semaphore driver maps colour→angle, CPL markers are a separate bitmask. The policy signature has no head identity, head technology, era, or mast name.

**Policies present:** `defaultRoute`, `sp1969` (= defaultRoute), `sp1985` (flashing-red Restricting), `gcorSpeed` (= sp1985), `nycSpeed` (3-head), `prrPositionLight`, `upperQuadrantSemaphore` (= defaultRoute), `boCpl` (markers). All keyed by `(headCount, isDwarf)` only.

**A per-head, per-technology appearance function would need:** the signal indication; the head's identity (which head of which signal: `836NA` = head A of 836N, dwarf or high); the head's *display* Kind from the plant (`HEAD_COLOR_LIGHT`, `HEAD_SEMAPHORE_2POS/3POS`, Sub ADR 0004 D6); the device technology (3-lamp, 1-lamp pixel, searchlight, semaphore servo, CPL disk/markers); the rulebook/era from layout context; and it should return a technology-specific vocabulary (lamp set + flash; angle + lamp lit; wheel colour) plus allow a static "every indication this signal's routes can produce is renderable by every head" check (draft R8; Sub ADR 0004 D6 "the generator checks that a head device can render its head's Kind").

## 4. The Subdivision side

`Sub/schemas/symbols/role-kind.toml` (68 rows), `Sub/schemas/context/keys.toml` (8 namespaces, 14 keys), `Sub/tools/contract/lint_libraries.py`.

**Asserted today:** DEVICE rows carry `delivery = {class, family, implements="ApplianceDriver"}`; the lint derives *family* as `kind.split("_")[0]` (`lint_libraries.py:95`) → SWITCH, DETECTOR, HEAD, LAMP, INPUT. Pin types BIT/LEVEL/DUTY/ANGLE with direction in/out/bidir = "what the symbol does to its wire" (`:42-43`); LEVEL rides on BIT. IODRIVER rows name the chip (`I2C-MCP23017` BIT bidir, `I2C-PCA9685` DUTY|ANGLE out, `I2C-MAX7313`) with `implements="IOBus"`. Attributes declare `context = appliance|binding|model`; only `appliance` may link to a layout key (`default_from`, `lookup`, `:110-118`). PANEL rows deliver `{tokens=…}`; PANEL/LAMP lists both `RailroadPanel:PanelLamp-*` and `RailroadField:Local-Lamp` on one row; `LAMP_PWM`/`LAMP_NEOPIXEL` proposed as separate Kinds "because D1 says different logic block". Every DEVICE Kind names its own class (`Head3LedDriver`, `Head3LedMux2Driver`, `Head3LedPwmDriver`, `Head1LedPwmDriver`, `Head1LedNeoPixelDriver`, `SemaphoreHeadDriver`, `LampBitDriver`, `LampPwmDriver`, `LampNeoPixelDriver`, `ServoSwitchDriver`…); none exist in FieldUnit, which has per-mast drivers only.

Lint run today: 9 errors (`Railroad` head symbols still `COMPONENT/HEAD` vs table `APPLIANCE/HEAD_*`; `Milepost` Role `ANNOTATION`, no pin; `Local-Lamp-PWM/-NeoPixel` still `PANEL/LAMP`; `CtcMachine`, `PanelColumn` no Kind), one note (`Local-Lock` `WLK` asserted-high by design, Sub ADR 0004 D5).

**Where this strains against R0:**
1. **Kind = appliance × domain × packaging product.** `HEAD_3LED_PWM` fuses appliance family (Head), lamp count (packaging), and domain (PWM). R0 says a driver is *one appliance shape × one domain shape*; a product-named Kind with a class per row gives N×M classes and N×M table rows, and `family` is recovered by string-splitting.
2. **Same shape, different rows and delivery forms.** `PANEL/LAMP` (tokens) and `DEVICE/LAMP_BIT` (class) are one Lamp shape on one digital domain; the office lamp additionally carries the token binding (`IndicationToken`) and, per Sub ADR 0004 D4/D5, flash behaviour (`WLQK`). The draft seam's `T` for LAMP ("off, on, flashing; request lamp: off, waiting, steady") already says they are one shape.
3. **Head technology in two places.** The plant head Kind states what the head can display (D6); the DEVICE Kind states how it is built. Both are needed by the appearance function, and nothing checks them against each other. At Sargent (`Railroad/SPCoast/Sargent.kicad_sch`) all four plant heads are `Signal Head - CL` while device `836SB` is `Device-Head-Semaphore-Servo` and `836SA` is `HEAD_3LED_PWM` on a PCA9685 at 0x27 (instance Role/Kind on the heads are still `COMPONENT/HEAD`). Not verified from the netlist which head symbol nets to `836SB`; the mismatch is the exact case D6 wants caught.
4. **Domain encodings leak into Kinds.** `HEAD_3LED_MUX2` (2-bit select code), `LAMP_NEOPIXEL` (no pins, addressed by `Chain`/`Index`, so the "a net joins pins of one family" rule cannot check it), `INPUT_BIT` (family "INPUT" is a domain primitive, not an appliance).
5. **`delivery.family` chooses `Transition<T>`**, but T is a per-appliance-shape fact, not a per-row fact; the table repeats it.
6. **Pin direction and polarity** are now settled in the table/lint (D6, D8, R6) but have no counterpart in `IOBus`.

## 5. First mapping onto Matter/Zigbee clusters

*Owner stated* (R0): clusters = attributes + commands + notifications; endpoints compose clusters; a device type is a required cluster set; the two Lamp examples (digital: on/off/flicker(level)/flash(rate), `isOn`/`Flicker`/`FlashRate`, Fault; PWM adds fade_on/fade_off/brightness, `currentBrightness`). Everything else below is *the sub-agent's inference*.

**Appliance-side clusters (what the field/office unit talks to):**
- **Lamp**: as the owner stated. Flash should take a shared phase from the environment (`timing.flash_ms`) rather than own a clock.
- **Head**: `show(appearance)` where *appearance* is typed by the head's display Kind (colour-light lamp set; semaphore position; CPL disk + markers); attributes current/previous appearance, since; notifications Fault (lamp-out), Moving (blade in motion). Internally a Head endpoint may compose Lamp clusters (3 lamps) or a Position cluster (arm) plus a Lamp.
- **Switch machine**: `throw(N|R)`; attributes commanded, contacts `{N, R}` as raw samples; notifications ContactsChanged, Fault. Classification of `{N,R}` into MOVING/OUT_OF_CORRESPONDENCE belongs to `Switch` (relay model: `NWCR`/`RWCR`/`KR`), not to the driver, so today's `SwitchDriver.h:38-48` is a defect under authority (2).
- **Detector** (feeds one `TR`): attribute occupied, quality; config hold; notification Changed. Quality should be real (`LOST_COMMS`) for remote domains.
- **Lever** (PANEL input): attribute position (N/R; L/S/R; key in/out); notification Moved; a Code button is a one-shot Lever.
- **Indicator** (PANEL output): Lamp + token binding; a Lock plate = Lever(WLQ) + Indicator(WLQK, blink/steady) + Indicator(WLK).

**Domain-side clusters (what the driver uses):** DigitalOut (bit, polarity, sink/source), DigitalIn (bit, polarity, pull-up, debounce), PwmOut (duty, frequency, invert, fade), ServoOut (angle, speed, limits), PixelOut (chain, index, colour, brightness), RemoteBit (CMRI IB/OB over SEAM-2), RemoteAppliance (MQTT: an already appliance-shaped domain). Each IODRIVER Kind declares which it offers; `IOBus` today offers DigitalIn/DigitalOut and a stub ServoOut.

**Device types (required clusters) for existing DEVICE Kinds:** `SWITCH_STALL_SENSED` = Switch machine ⟵ DigitalOut(M) + DigitalIn(N,R); `SWITCH_STALL_SIM` = Switch machine ⟵ DigitalOut + simulated contacts; `SWITCH_SERVO_*` = Switch machine ⟵ ServoOut [+ DigitalIn]; `SWITCH_SENSE` = Switch machine (contacts only) ⟵ DigitalIn; `DETECTOR_*` = Detector ⟵ DigitalIn (+hold); `HEAD_3LED` = Head(colour-light) ⟵ 3×DigitalOut; `HEAD_3LED_PWM` = Head ⟵ 3×PwmOut; `HEAD_3LED_MUX2` = Head ⟵ 2×DigitalOut (an encoding); `HEAD_1LED_*` = Head ⟵ PixelOut | PwmOut; `HEAD_SEMAPHORE_SERVO` = Head(semaphore) ⟵ ServoOut + PwmOut; `LAMP_*` = Lamp ⟵ DigitalOut | PwmOut | PixelOut; `INPUT_BIT` = Lever ⟵ DigitalIn; PANEL lamps = Indicator ⟵ DigitalOut (MAX7313); PANEL levers = Lever ⟵ DigitalIn.

## 6. Consolidated decisions for the owner (default in italics)

**R0 questions, proposed answers**
1. *Role/Kind fit:* keep `(Role, Kind)` 1:1 with a logic block, but make a DEVICE row's Kind name the **appliance shape** (`HEAD`, `LAMP`, `SWITCH_MACHINE`, `DETECTOR`, `LEVER`) and move the **domain shape** to a second axis supplied by the IODRIVER pins it is wired to (BIT/DUTY/ANGLE/PIXEL). Packaging (`3LED`, `MUX2`, `-OS`) becomes an attribute or pin set, never a Kind part. *Default: yes; the table gains a `shape` and the driver registry is keyed (shape, domain).*
2. *Symbol naming fit:* symbol names may keep `Device-Head-3LED-PWM` as a human packaging hint (axiom 3 already allows suffixes); the Kind behind it changes. *Default: keep symbol names, change Kinds in one scripted pass.*
3. *Shape names:* appliance shapes Lamp, Head, SwitchMachine, Detector, Lever, Indicator(=Lamp+token), LockPlate(composite); domain shapes DigitalIn, DigitalOut, PwmOut, ServoOut, PixelOut, RemoteBit, RemoteAppliance. *Default: these, pending glossary entries.*
4. *Rename now?* *Default: no renames in libraries until the architecture ADR is accepted; record the mapping in the ADR first.*

**Other decisions needed**
5. Split `Aspect` into `HeadAppearance` (per technology) and signal aspect; rename `AspectResolver` policies to rulebook data behind a `getHeadAppearance(indication, headIdentity, displayKind, layout)`. *Default: yes.*
6. Where contact-state classification lives (driver vs `Switch`). *Default: `Switch`, per the relay model.*
7. Is the optical hold a Detector attribute or `TrackCircuit` behaviour? *Default: driver/Detector (`Hold_ms`), remove `dropoutDelayMs` from the vital object.*
8. Office and field lamps: one Indicator shape for `PanelLamp`, `Local-Lamp`, `Device-Lamp`, with the token binding as data? *Default: yes; `PanelHardware` is retired in favour of the same driver seam.*
9. Does `MqttApplianceBus` survive as a RemoteAppliance domain, or become a code-line/emulation concern? *Default: RemoteAppliance domain, but it must stop including `InterlockingPlant.h` and binding the whole plant.*
10. `IOBus` scope: add configuration (direction, pull-up, invert, frequency), duty, pixel, capability refusal, shared flash phase. *Default: yes, one capability-declaring interface per domain cluster rather than one fat `IOBus`.*
11. Heads: per-head drivers (one per head device) replace per-mast `addHead/addArm`; `MastType` derived from the drawing's heads. *Default: yes.*
12. Plant head Kind vs device Kind compatibility check location (compiler vs `begin()`). *Default: compiler, statically.*
13. Lamp-test/maintainer modes: layout context or vital-consent parameters (draft O3). *Default: parameters gated by the field unit.*
14. Flash: one phase per field unit from `timing.flash_ms`, or per-lamp rate command as in the owner's Lamp example (`flash(rate)`). *Default: per-lamp rate requested, phase supplied by the environment.*

**Could not verify:** the Sargent netlist (did not run `make netlist`; `.net` may be stale), so head-symbol ↔ device pairing is inferred from Values only; whether `FieldUnit` has an `I2Cexpander` configuration path outside the library (it does not in `src/`).

---

# Owner's brainstorm on the survey (2026-10-08)

A train of thought, not a review of the report's items. Rulings are marked; everything else is direction.

**A. The mast gets its heads.** A signal mast driver should be passed its heads rather than ignoring the mast's role. The mast → head → domain relationships are already in the drawing (mast `H1`/`H2` pins to head symbols; device bound to head by Value; device pins on expander pins whose Kind is the domain), so a notation like

```
2NAB => SignalMast(CplHead(2NA <Light:DigitalIO>), CplHead(2NB <Light:DigitalIO>))
```

is derivable from the netlist and can be emitted by the codegen as a report; it need not be drawn. A head can span domains (semaphore: arm on a servo, lamp on PWM).

**B. IOBus.** Needs serious work: today the field codegen has intimate knowledge of the expanders and sets up the IOBus for its drivers. Direction: IODRIVER symbols are the bus instances; each device pin resolves to (bus, channel) with its configuration as data; drivers ask the bus for a configured channel.

**C. Two axes: appliance-kind × deploy-domain-kind.** Are dozens of Kinds × dozens of domain mappings overcomplicating it? Switches and signals deconstruct into digital lever inputs and light outputs; the heavy lifting (indication → aspect → head appearance) is all symbolic (percent brightness, angles, PWM frequency, colours, booleans) until the last hardware step. So the maintained mapping is *primitives × domains*, not appliances × domains.

**Primitives** (corrected: a stall motor is binary, stalled against one stop or the other, with no middle and no feedback of its own; it is not a Position):

| Primitive | State | Domains |
|---|---|---|
| Light | on/off, brightness, colour, flash, flicker | bit, PWM, pixel |
| Level | binary, held (stall motor) | bit |
| Position | target angle, speed (servo) | servo |
| Contact | sampled (lever, point contact, detector) | bit in |

Appliances are compositions above this line: switch machine = Level + 2 Contacts, or Position + 2 Contacts, or Position alone (sim); head = Lights (and/or Position + Light); lock plate = Contact + Lights; a PANEL lamp and a field lamp are the same Light with a token binding above.

**Naming one level deeper.** Parts take the appliance name plus the device pin name, so the tree names itself:

```
2NAB
 ├─ 2NA  [CPL head]  ─ Lights  2NA.R  2NA.Y  2NA.G   ─ channels  0x20.A1  0x20.A2  0x20.A3
 └─ 2NB  [CPL head]  ─ Lights  2NB.R  2NB.Y  2NB.G   ─ [2:4 MUX] ─ 2NB.S0  2NB.S1  ─ 0x20.B1  0x20.B2
```

Every primitive is addressable by a stable name (`2NA.Y`: maintainer lamp test, diagnostics, test harnesses, with no interlocking involved), and the head-compatibility check becomes a walk over named parts.

**Encoders** are a node type between named lights and named channels: a pure transform in the symbolic realm (2:4 mux; 74HC595 shift-register chains by index; NeoPixel chains by chain+index+colour; charlieplexing). What `HEAD_3LED_MUX2` and `LAMP_NEOPIXEL` were encoding as Kinds. The domain adapter underneath stays channel-level.

**Ruling (owner):** encoders become their own symbols, wired between the device and the expander, because that simplifies the symbol set. Reimagining the hardware-mapping symbols is a small price for a regular, simple, structured architecture.

**Three layers this suggests:** (1) the vital objects (`Switch`, `SignalMast`, `TrackCircuit`), unchanged; (2) symbolic rendering built from the drawing's composition tree, indication → head appearance → primitive values, with mechanism state only (searchlight wheel, blade in motion) and no decision state, testable with no hardware; (3) primitives × domain adapters, a thin layer tested against a mock bus.

**Rulings on the rejected ADR 0005 draft (owner, 2026-10-09):**
- A 74HC595 on a signal head is an actuator that sits on the head, like an RGB LED or a motor: an encoder (serial in, lights out), not a bus. It does not daisy-chain in this use, so it is not a bus the way a NeoPixel chain is. The architecture may still admit a shift-register bus if one is ever wanted.
- Flash: FieldUnit needs several flash-rate regimes (signal heads, crossing gates, staccato or asymmetric patterns). All lamps in a regime use one synchronized flasher source. Limiting a unit to a single source is wrong.
