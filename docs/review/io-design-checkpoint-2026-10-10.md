# I/O design checkpoint (2026-10-10, rev 8)

- Status: a record of the design conversation of 2026-10-09 and 10, for the owner's confirmation. "Explicit" is what the owner said. "Implicit" is what followed from it in the drafts and the spike without being said; each one needs a yes or a no. Rev 2 applies the owner's review of rev 1; the changes are listed at the end.
- Governs: `driver-architecture-foundation.md`. Companions: `environment-view-2026-10-09.md` (rev 5), `driver-types-view-2026-10-09.md` (rev 2), and the spike in `~/Dropbox/KiCad/Railroad/Scratch/` (not git; generators and the binding pass in its `tools/`, reports in `production/`). The digest and survey that preceded this record are in git history only.
- Scope: Part 1, the drawing side: the user's workflow, the symbol libraries, the schematics, the KiCad compiler and the Layout Data Model. Part 2, what consumes the model, is set aside and appears here only where it constrained Part 1.

## 1. What we learned

1. **The netlist already carries everything.** Nets, each pin's electrical type, and every symbol field reach the compiler through the netlist export. Per-pin capabilities as symbol fields, settings as fields, addresses as fields: none of it needs a new reader. The spike proved it on one sheet.
2. **The symbol's pins are the function signature.** A device symbol says what its appliance's functions are, by pin name, and nothing about hardware. What the function lands on decides the hardware.
3. **One binding mechanism.** A symbol pin on a net with an I/O pin. Device symbols are the ergonomic form; the one-pin `Binding` symbol is the escape hatch; text labels are out. The label experiment failed on usability, not on data.
4. **Domains leave the names.** With the generator inserting casts between a function's native capability and the I/O pin's, no Kind, symbol or setting carries a domain word. Eighteen device Kinds become about eight, and three of those are signature variants of one head.
5. **A chain is a bus, and a bus is a net with addressed devices.** The same thing an I2C expander already is.
6. **The Encoder Role is gone.** A mux-coded head is a device whose signature is the code we drive; the decoding is field hardware on the far side, like a shift register on a head or an LED. A chain is a bus. Casts cover one wire to one wire. Nothing is left for an encoder symbol to do.
7. **Settings are symbols' fields.** After the standard fields are removed, every field on a symbol is one setting. A `Setting` symbol attaches settings to a net, and everything on that net inherits them.
8. **Hand-maintained registries are a liability.** The capability words, the casts and their settings, and the factory defaults all have one natural source, the FieldUnit source tree, and can be indexed from it. The symbol requirements have one natural source, the libraries, and can be reported from them. Nothing of this needs a file kept by hand.
9. **Symbol names decide nothing.** Every decision reads a field: Role on every symbol, Appliance and Style on the plant and device sides, `IC` on the I/O side. A symbol's name and shape are the drafter's choice. The spike pass broke this in three places (chip by part name, masts and heads by part name, the Terminal by Kind), and the plant compiler breaks it today with its part-name table; the real compiler copies none of them.
10. **The desk is the same mechanism.** A lever plate or lamp on an expander pin is a device pin on an I/O pin; the column backplane's coincident pins are membership; the join to the plant is the Value, or a token list for a lamp. The desk rules added for it (I27 to I31) ran over the real SPCoast desk, 137 bindings, with no diagnostics and no change to the drawing.
11. **The method that worked.** Top-down views, a conversation that pushes back, then a drawing in KiCad before anything is relied on. The bottom-up documents and the hand-written sketches were demoted to evidence at the start and nothing was lost.

## 2. Explicit decisions (owner)

Reading rules
- E1. The foundation document governs. ADR 0004 below its R-text, the rejected 0005 draft, the survey's inferences, the delivery classes in the (Role, Kind) table and `keys.toml` are evidence.
- E2. The legacy sketches are informative and expendable.
- E3. Netlists are generated on demand with kicad-cli.
- E4. Part 1 first. Part 2 is a mental check that the model suffices.

Proposals for the ADR
- E5. Three proposals stand aside for the ADR: #1 run-time interpretation, #2 code generation, #3 generated tables with a fixed engine. #2 uses classes and static objects; templates, RTTI and heap are out for firmware.

Primitives, functions, capabilities
- E6. Level is the analog primitive, 0 to 100%, the one that meets PWM and DAC. Light was moved out of the primitive list; a lamp is a conglomerate.
- E7. A device pin declares a function (`M`, `OCC`, `N`, `R`), not a primitive. The hardware comes from what it is wired to.
- E8. One capability vocabulary, direction inside, on every pin.
- E9. One native capability per pin; the generator inserts a cast from a bounded table when the two ends differ. (The earlier "more than one match is an error" became moot.)
- E10. The order rule for several expander pins on one net is rejected. Every function pin lands on its own expander pin, explicitly.
- E11. Typing labels is poor UX. Device symbols stay as the drag-and-drop form.
- E12. Casts are one to one. One-to-many casts are a usability problem and are out.
- E13. The cast table is the index of the transform functions found in the source tree, not a file kept by hand.
- E14. A bus-capability pin admits many addressed device pins on its net; a wire-capability pin admits one.

Settings
- E15. One pattern for every setting: settings are fields on symbols. A `Setting` symbol attaches them to a net, and whatever is on that net inherits them: the `Interlocking` symbol's net for a plant, a function's net for one binding, the layout anchor's net for the layout. Its Value is the human reason. A symbol's own fields are its own settings.
- E16. Factory settings need a stated home and a stated way to change them.

Environment and drivers
- E17. The store exists: a switch's last position matters when a train is parked on it; persistence must be wear-aware.
- E18. Two release regimes, restrictive and "no dispatcher", are the pattern for more.
- E19. Flashing is resolved above the driver by the generator.
- E20. A driver has no "initialise yourself" step; construction is computed by the generator and executed by the unit.
- E21. Identity is readable by a driver but never required for its transform.
- E22. Maintainer and lamp-test modes are not driver concerns; they are commands in the per-type vocabulary.
- E23. Simulated travel is the field unit's, not a driver's.
- E24. Whether a calibrated value survives a reflash is not to be codified.
- E25. The maintainer's calibration interface, the store, the fault sink and the clock source are interfaces to capture, not designed now.

Naming, symbols, polarity
- E26. `835` is drawn with the right appliance symbol, `Switch_Lock`. The device bound to it is of the wrong Kind, which calls for a Kind namespace review.
- E27. The `~{X}` pin-name form is useful and informative and stays. It was wrongly parked.
- E28. A 74HC595 on a head is a field actuator, no different from an LED, and out of scope. The 3-to-2 mux is our side of that serialise-and-decode pattern.
- E29. The symbol requirements, roles, kinds, device types, pins and fields, belong in tables, not in prose.

Chains and buses
- E30. A pixel chain is a net; devices on it carry an `Address` for their position; the chain encoder symbol is withdrawn.
- E31. Gaps on a chain are tolerated; the generator writes "off".
- E32. CMRInet nodes are remote expanders, to be proven on an interlocking later.

Step 4, the owner's verdict on the drawing (2026-10-10)
- E34. The appliance name is the join. The plant symbol, the desk symbol, the local lever symbols and each field device symbol carry the same Value (835 is `Switch_Lock` on the plant, `PanelLock` on the desk, `Local-Switch` and `Local-Lock` in the field); the lint checks them. Wires between sheets are cumbersome in KiCad and break the compiler's assumptions, so no other join is wanted.
- E35. The lock is its own logic block: its behaviour differs from the switch's even though they interact. Device side: `Device-Switch` plus `Device-Lock`, one Value. An appliance may be served by several device symbols.
- E36. Symbol names have no place in any decision. The I/O symbols carry an `IC` attribute so that every shape of one chip is handled the same way (the 4-pin-per-unit shape mirrors the owner's boards and stays the default; a 16-pin unit or a 1-pin-per-unit shape may be added if they earn it). Wires across units are an ordinary binding.
- E37. The `Setting` symbol's Value is short, because it is displayed; `Description` carries the reason.
- E38. The `Terminal` is normal in both uses: reach across sheets and awkward geometry or arity on one sheet.
- E39. Terminal pairs are merged into one net by Value by the compiler.
- E40. Chain addresses are typed per device. Implications are to be learned from use. `Address` is one attribute name resolved in its context: a column on the desk, a pin on an IC, a slot on a chain; the grouping makes the meaning obvious.

The desk and fascia spike (owner, 2026-10-10)
- E41. Column membership stays as drawn: a `Column` pin on each desk appliance meeting the column symbol's backplane pins. The column matters for rendering the model and the panel boards. A machine with another arrangement forks the expander symbol; the `IC` is unchanged.
- E42. Desk lamp join. The Value is a human note like a setting. If the Value alone resolves to an indication, it is the join. If the Value does not resolve and `IndicationToken` is set, the token list is the join. Both resolving and different is a compiler error, "ambiguous symbol". An unprefixed token is scoped to the column's interlocking; `<interlocking>:<token>` names another's.
- E43. The consumer of a device is the processor that owns the I/O pin it lands on. With "nothing on the panel references it: not on the code line" and the open item "local logic for local hardware", this covers the crew's local levers without a sheet rule or a symbol saying "local".
- E44. Processor ownership of an I/O symbol is implied by the sheet context: the one MACHINE or MAIN HOUSE in scope. The attribute `Processor` (Value of that symbol) is required on each I/O symbol only when the context holds more than one; the compiler never guesses between two. On the field side the processor is a CP, declared by its `MAIN HOUSE`. Luchessa, three houses in one interlocking, either puts each CP's I/O on its own sub-sheet or types `Processor` on every I/O symbol.
- E45. `PanelLock` is redone under the three planes: Appliance `lever`, Style `lock`, four distinct functions instead of `WLS`/`~{WLS}` and `WLK`/`~{WLK}`, since `~{}` means asserted low and nothing else. `PanelMCall`'s pin is renamed `S` so that every lever token derives as Value plus pin name.

Spike
- E33. The spike lives in `~/Dropbox/KiCad/Railroad/Scratch/`, not under git. The owner completed the trackplan; the I/O side was rebuilt around it.

## 3. Implicit decisions (to confirm)

Capabilities and casts
- I1. The vocabulary today: binary in, binary out, level in, level out, position out, colour out, pixel out, message in, message out. No "sides": a word is a word; which pins use it is a fact of the libraries. The vocabulary is not a file: it is the set of words that appear in `Pin.*` fields across the libraries and in the from/to declarations of the casts, and the lint reports a word that appears in one place and not the other.
- I2. The cast index. Each cast is one class in FieldUnit that declares its from-word, its to-word and its settings with factory defaults, in a form the indexer reads. Today's expected entries: binary out to level out (two-point: `low`, `high`, `fade_ms`); binary out to position out (two-angle: `low_deg`, `high_deg`, `speed`); binary out to colour out (one-point: `color`, `brightness`); level out to level out (scale: `gamma`, `scale`); level in to binary in (threshold: `threshold`, `hysteresis`). A binary `M` on a servo board is the two-angle cast onto a position-out pin. Casts may chain; the generator finds the path; two paths is an error the author resolves with a `cast` setting on the net.
- I3. Servo, PWM and duty, codified. A "level out" I/O pin is a PWM waveform; brightness is duty at any frequency. A hobby servo is a pulse of 500 to 2500 µs every 20 ms, which is duty at 50 Hz. A PCA9685 owns one frequency for all sixteen pins, so one chip is either a lamp driver or a servo driver, never both. That is drawn, not configured: two I/O symbols, `Driver-I2C-PCA9685-PWM` with pins level out and `Driver-I2C-PCA9685-Servo` with pins position out, and the I/O driver type for the servo variant owns the 50 Hz and the pulse mapping (`min_us`, `max_us` as its settings). A lamp on the servo variant is a capability mismatch the compiler refuses. The servo-pulse cast of rev 1 is withdrawn.
- I4. A chip-wide setting, where a chip has one, lives as a field on the I/O symbol instance. A device's requirement on it comes from the cast or the I/O type, and conflicts are compile errors.

Symbols and names
- I5. The native capability lives in a `Pin.<name>` symbol property, one per pin, because KiCad has no per-pin fields. The lint checks it against the pin's electrical type.
- I6. The KiCad electrical type stays as "what the symbol does to its wire", for ERC only.
- I7. Polarity stays in the pin name: `~{OCC}` is an asserted-low contact, `~{LAMP}` an asserted-low lamp. It is an electrical fact of the device. The generator turns it into I/O-pin configuration, inversion in the chip's register where the chip has one, in the I/O driver otherwise, and a pull-up where an asserted-low input lands on a programmable pin. No device driver inverts.
- I8. `Kind` and `Serves` are retired as fields. Three facts in three planes replace them. **Appliance** is what sort of thing: `switch`, `head`, `mast`, `track_circuit`, `lamp`, `lever`, `maintainer_call`. **Style** is the prototype variant within it, how the railroad built it: switch `powered`, `manual`, `manual_sensed`, `lock`, `derail`; head `semaphore`, `CL`, `searchlight`, `PL`, `CPL`, `PCL`, `ball`, `vane`; mast `single`, `double`, `dwarf`. **Signature** is how the model realises it: the device symbol's pin set, not a field. `Role` stays. An appliance symbol carries Appliance and Style; a device symbol carries the same two plus its pins.
- I9. A device binds to an appliance of equal Appliance and Style. A device with no Style serves every Style of its Appliance (`Device-Lamp` serves `lamp`/`maintainer_call` and `lamp`/`auxiliary`). `835` fails because `switch`/`powered` is not `switch`/`lock`. The symbol name documents the signature: `Device-Head-CL-3Lamp`, `Device-Head-CL-RGB`, `Device-Head-CL-Mux2`, `Device-Switch-Powered`, `Device-Switch-Lock`, `Device-TrackCircuit`. The driver class is keyed by Role, Appliance, Style and pin set; "a Kind is one logic block" becomes "a symbol is one logic block".
- I10. `Terminal` (the symbol; "binding" is the relation) is a reference by name to a device symbol's pin. The compiler resolves `1NAT.OCC` by finding the device symbols of `1NAT`'s Appliance and Style that have an `OCC` pin and takes that pin's capability and polarity. Lint rule: device symbols of one Appliance and Style that share a pin name must agree on that pin's capability and polarity, so the answer is one. `Device-Lamp`, `PanelMCall` and the rest remain the normal form; `Binding` is the duplicate for the odd wire.
- I11. `Setting`: Role `SETTING`, one passive pin. `Address` is a binding field, excluded from the settings list with Reference, Value, Footprint, Datasheet, Description, Role, Appliance, Style, `Pin.*` and KiCad's own fields.
- I12. Head parts are named mast number and direction plus head letter: `2NA` is head A of `2NAB`.
- I13. A device binds to its appliance by Value within the same interlocking hierarchy: the plant sheet and its child sheets. A large interlocking puts its I/O on a child sheet, the way the Panel already is one. No wire crosses a sheet; the Value does the join; the compiler scopes by sheet path.
- I14. Plant symbols and I/O symbols may share a sheet; the compiler splits them by Role.

Environment and types
- I15. Setting scopes, most specific wins: factory (FieldUnit source: the driver or cast class that reads the setting declares its default; changed by a code change and a release), layout (a `Setting` symbol on the layout anchor's net on the root sheet), interlocking (a `Setting` symbol on the `Interlocking` symbol's net), binding (a `Setting` symbol on a function's net), instance (fields on the device symbol), calibrated (the store, at run time).
- I16. "Raw" attributes means sampled contact states: for each contact, a state from the enumeration CLOSED or OPEN, after the I/O's inversion so that the enumeration names the contact and not the wire, the sample time, and a quality of GOOD, STALE or LOST. No boolean, so no ambiguity about what true means. Not a position, not a token. The vital logic derives `NWCR`, `RWCR` and `KR` from them, per the relay model.
- I21. How the derived registries fit the model. The capability words, the casts with their settings, and the factory defaults are facts of the toolchain, not of the layout. They are published by FieldUnit as one indexed document with its own schema (`fieldunit-index/v1`: casts with from, to, settings, defaults, chip requirements; driver types with Serves, signature, settings). The compiler reads it as an input beside the libraries. In the Layout Data Model they appear twice: as first-class provenance, the index version and the library versions the model was compiled against; and as second-class derived relations on each binding, the capability found at each end, the cast path chosen, and the settings resolved for it. The model never copies the index. A model compiled against a later index is recompiled, not patched.
- I17. The driver type pattern, seven fields per type: Serves, Signature (function pins with capabilities and polarity), Commands (what the unit may ask, in the appliance's vocabulary, covering every renderable state so a test is an ordinary command), Attributes (raw observations), Notifications (facts observed, never decisions), Settings (the names it reads, with factory defaults), Mechanism state (the only state it keeps). Two families with the pattern, device types and I/O types, plus service sources. Encoder types are retired.
- I18. An electric lock has its own device symbol and driver class: `Device-Switch-Lock`, Appliance `switch`, Style `lock`; signature `UNLOCK` (binary out), optional `~{N}`, `~{R}`, `~{OCC}` (binary in); commands `lock()`, `unlock()`.
- I19. Precisely: the `Device-TrackCircuit` driver class (Appliance `track_circuit`) has a `hold_ms` setting, type ms, factory default 0, interlocking and instance scopes allowed. While `hold_ms` is greater than zero the driver holds `occupied` true for `hold_ms` after the contact last opened, so that an optical detector does not report a gap between cars as a clear track. The track circuit object keeps no hold of its own.
- I20. Simulated appliances are the field unit's; no "sim" device symbol exists.
- I22. GPIO. A processor pin is one of five I/O symbols by use, `Driver-GPIO-Digital`, `-Analog`, `-PWM`, `-Servo`, `-Pixel`, with the capability on `Pin.D` in the library so that every I/O pin on every chip is read by one rule. The Value is the physical pin name as the board's core spells it (`GPIO5`, `A0`); the generator passes it through as an identifier; a misspelling fails the C++ build; an invalid pin or an invalid use is the designer's responsibility. Logical channel names were rejected because the designer wires specific wires to specific pins; a board profile with validation was judged too much complexity for now and stays available later.
- I24. Terminal rules. A Terminal is placed in pairs, one on the device pin and one on the I/O pin, same Value; the compiler merges the two nets by Value (E39). The part must be a device symbol placed in the same interlocking hierarchy and the function must be in its pin set; resolution and the Value join use the sheet path, never the whole project. A Terminal with no device end, and a device pin with no I/O end, are each one error, which is how a missed pin is caught. `Address` is never on a Terminal; a chain device's slot lives on the device symbol.
- I25. Several device symbols per appliance (E35): completeness is checked over the union of their pins and a function bound twice is an error. A device symbol may list more than one Style (`Device-Switch` serves powered and lock; `Device-Lock` serves lock only) so that the switch half of a locked switch is the ordinary switch device.
- I26. Chain addresses (E40), to watch: a duplicate address on one chain is an error, a gap is off, the chain length is the highest address plus one, an address past the physical strip is silent at runtime.
- I27. Addresses are scoped by processor (Scratch has an expander at `0x20` on the desk and another in the field); that is why E44 requires one unambiguous processor per I/O symbol.
- I28. Tokens derive as Value plus function pin for every lever (`783NWS`, `MC1S` after E45); no `ControlToken` field is needed. A lamp's join is its token list or Value (E42); a code button has no join.
- I29. Indication facts are a product of the plant compiler for each interlocking (circuits, switch and signal K tokens, fleet and traffic indications); token validation is a link-time check against them. The spike validated against a toy set and could not know `NFLK`.
- I30. A signal lever's Value names its masts by number: `784` joins every mast whose Value starts `784`.
- I31. The field-side processor symbol: the house declares the processor (E44). Whether a house without hardware (emulated) is drawn differently is open; the design note's `FIELDUNIT`/`HARDWARE` proposal is the candidate.
- I23. The `contact` appliance. Who consumes a contact is its Style plus its Value: Style `lock_request` with Value `835` is the crew's unlock key for switch 835, consumed by the lock sequence; Style `auxiliary` or `button` with its own Value is consumed by no local logic. The Style selects the handler class in the generator. Whether a contact reaches the office is exposure by demand (owner, 2026-10-05): it is on the code line only because a desk symbol lists its token. No field says "local" or "code line". Open: whether the compiler refuses a contact that no handler and no desk symbol consumes, as a drawn input that goes nowhere.

## 4. Tables

### 4.1 Symbols by Role, Appliance and Style (the plant Roles TRACK, POLICY, STRUCTURE and the desk Roles unchanged in form)

Appliance symbols (Role APPLIANCE), today's Kinds mapped:

| Symbol | Appliance | Style | Was |
|---|---|---|---|
| `Switch_Powered` and variants | switch | powered | SWITCH_REMOTE |
| `Switch_Lock` | switch | lock | SWITCH_LOCK |
| `Switch_Manual_Sensed` | switch | manual_sensed | SWITCH_MANUAL_SENSED |
| `Switch_Manual` | switch | manual | SWITCH_MANUAL |
| `Derail` (was `Switch_Powered_Derail`) | switch | derail | DERAIL |
| `Track Circuit` | track_circuit | | TRACK_CIRCUIT |
| `Mast_Single`, `_Double`, `_Dwarf` | mast | single, double, dwarf | MAST_* |
| `Signal Head - CL` | head | CL | HEAD_COLOR_LIGHT |
| `Signal Head - SemaphoreU2`, `U3` | head | semaphore | HEAD_SEMAPHORE_2POS, _3POS (positions become a setting or a signature) |
| `MaintainerCall` | lamp | maintainer_call | MAINTAINER_CALL |
| `AUXILIARY` | lamp | auxiliary | AUXILIARY |
| `Contact` (new) | contact | auxiliary, button, door, … | the generic non-vital input, the complement of `AUXILIARY`; its office indication is `<Value>K` (was DEVICE/INPUT_BIT with no appliance) |

`lamp` and `contact` are the two generic non-vital appliances: one output the office commands, one input the office sees.

Device symbols (Role DEVICE). A device binds to an appliance of equal Appliance and Style; no Style means every Style.

| Symbol | Appliance | Style | Signature (capability; `~{}` = asserted low) |
|---|---|---|---|
| `Device-Switch` | switch | powered, lock | `M` binary out; `~{N}`, `~{R}` binary in; `~{OCC}` binary in (packaging) |
| `Device-Switch-ManualSensed` | switch | manual_sensed | `~{N}`, `~{R}` binary in |
| `Device-Lock` | switch | lock | the lock mechanism: `UNLOCK` binary out, a lock sense `~{LOCKED}` binary in if the hardware has one (to confirm against FieldUnit's lock driver); one Value with its `Device-Switch` (E35, I25). Today's `Local-Switch` and `Local-Lock` on the Sargent sheet are not this: they are the crew's local lever and lamps, Role PANEL on a field sheet, the "local client" of task 4 |
| `Device-TrackCircuit` | track_circuit | | `~{OCC}` binary in; setting `hold_ms` |
| `Device-Head-CL-3Lamp` | head | CL | `~{R}`, `~{Y}`, `~{G}` binary out; `~{L}` (packaging) |
| `Device-Head-CL-RGB` | head | CL | `RGB` colour out |
| `Device-Head-CL-Mux2` | head | CL | `S0`, `S1` binary out (a select code: no asserted state) |
| `Device-Head-Semaphore` | head | semaphore | `ARM` position out; `~{LAMP}` binary out |
| `Device-Head-Searchlight` | head | searchlight | `VANE` position out; `~{LAMP}` binary out (not drawn yet) |
| `Device-Lamp` | lamp | | `~{LAMP}` binary out |
| `Device-Contact` | contact | | `~{IN}` binary in |
| `Terminal` (was `Binding`) | any | any | one pin; Value `<part>.<function>`, the tag on the terminal; placed in pairs, merged by Value (E39, I24) |

"Binding" stays as the name of the relation in the model, a function bound to an I/O pin. The symbol is named for the domain: a terminal on the bungalow's terminal board carries a tag naming the wire that lands on it, and `Terminal` with Value `1NAT.OCC` is exactly that. `Wire` or `Lead` would also do; `Pin` and `Connection` collide with KiCad's own words.

Desk and fascia symbols (Role PANEL) are devices in their own right, Appliance `lever` or `lamp`, Style `switch`, `signal`, `lock`, `code`, `maintainer_call`, `indication`, bound by pin abutment like every device, joined by Value (levers), by Value or token list (lamps, E42), with the `Column` pin for membership (E41). `PanelLock` is redone and `PanelMCall`'s pin becomes `S` (E45). The spike copies are in `ScratchPanel.kicad_sym`.

I/O symbols (Role IODRIVER) and the setting symbol. A pin has one capability, so a processor pin that can be several things is several symbols, one per use, Value = the pin. Every I/O symbol carries `IC`, the chip it stands for; the symbol's name and its unit partition are free (E36), so a 4-pins-per-unit `MCP23017` and a 16-pin one are the same chip to the compiler:

| Symbol | `IC` | Pins (capability) | Fields |
|---|---|---|---|
| `Driver-I2C-MCP23017` | `MCP23017` | `A1..B8` binary in or binary out, each pin configured by what lands on it | `Address` |
| `Driver-I2C-MAX7313` | `MAX7313` | `A1..B8` binary in or binary out, each pin configured by what lands on it | `Address` (per-port intensity and blink unverified) |
| `Driver-I2C-PCA9685-PWM` | `PCA9685` | `A1..B8` level out | `Address`, chip setting `frequency_hz` |
| `Driver-I2C-PCA9685-Servo` | `PCA9685` | `A1..B8` position out; 50 Hz fixed | `Address`, settings `min_us`, `max_us` |
| `Driver-GPIO-Digital` | `GPIO` | `D` binary in or binary out, configured by what lands on it | Value = the physical pin name (`GPIO5`, `D4`) |
| `Driver-GPIO-Analog` | `GPIO` | `D` level in (ADC) | Value = the physical pin name (`A0`) |
| `Driver-GPIO-PWM` | `GPIO` | `D` level out | Value = the physical pin name, `frequency_hz` |
| `Driver-GPIO-Servo` | `GPIO` | `D` position out | Value = the physical pin name, `min_us`, `max_us` |
| `Driver-GPIO-Pixel` | `GPIO` | `D` pixel out (bus) | Value = the physical pin name |
| `Setting` (Role SETTING) | | `net` passive | Value = a short name (displayed); `Description` = the reason; every other field = one setting (E37) |

The GPIO Value is passed through to the generated code as the board core's identifier; the C++ build is the check (I22). A board profile is a possible later addition, not drawn and not required.

Every symbol in the libraries today is expendable: they exist to prove the ideas, not to encode requirements (owner).

### 4.2 Where each registry comes from

| Registry | Source | Kept by hand? | Checked by |
|---|---|---|---|
| Capability words | `Pin.*` fields in the libraries; from/to of the casts | no | lint: a word used on a pin with no cast or match |
| Casts and their settings | cast classes in FieldUnit, indexed | the code, yes; the table, no | generator: a binding with no path |
| Settings and factory defaults | driver and cast classes in FieldUnit, indexed | the code, yes; the table, no | compiler: a field that is not a declared setting |
| Symbol requirements (Role, Kind, Serves, pins, polarity) | the libraries, reported | the libraries, yes; the table, no | lint: electrical type versus capability; Serves names an existing appliance Kind |
| Layout, interlocking, binding, instance settings | the drawings | yes, by the layout designer | compiler: scope and name |

## 5. What is left

Part 1 task list, with status

| # | Item | Status |
|---|---|---|
| 1 | Primitives on pins | Resolved as functions and capabilities (E6 to E9, I1 to I3). |
| 2 | Kind grammar | Replaced: Appliance, Style and signature in three planes (I8, I9, §4.1). Open: the Style word lists, and whether a semaphore's two or three positions are a Style, a setting or a signature. |
| 3 | Encoder symbols | Retired (learned 6, E28, I17). |
| 4 | Binding rules | Field side proven in the spike and passed the owner's usability verdict (E34 to E40). Desk and fascia side proven on the Scratch Panel sheet and on the real SPCoast desk (E41 to E45, I27 to I31): column membership, token lists on lamps, the local lever by processor ownership. |
| 5 | Direction, polarity, complement | Direction inside the capability; polarity in the pin name (E27, I7); complement is never `~{}` (E45, `PanelLock`). To be written once in the environment view. |
| 6 | What is never drawn | Settled. Missing symbols: the layout anchor on the root sheet. |
| 7 | The model section | Shape in the environment view §5: nodes, nets, binds with the cast path per binding, settings by scope, addresses, chip settings. Not yet a schema. |

Next steps, in order
1. Done: step 3, the binding pass over `Scratch.net` (17 bindings resolved, two true diagnostics) and over the real `SPCoast.net` (field side resolves; `836SB.ARM` exposes the missing `Pin.*` fields; the desk side needs its own rules). Done: step 4, the owner's verdict (E34 to E40).
2. Done: the desk and fascia spike, `ScratchPanel.kicad_sch` and `binding_pass2.py`; the real desk reads clean under the rules.
3. Done: the two views revised to match (environment view rev 5, driver types view rev 2).
4. The real libraries: `Appliance` and `Style` fields in place of `Kind`, `IC` on the I/O symbols, `Pin.*` fields, `~{}` names where missing, the `Setting`, `Terminal` and layout anchor symbols, the two PCA9685 symbols, `Device-Switch` plus `Device-Lock`, the lint updated. In a branch, after the owner's symbol review.
5. The indexers: casts and settings from FieldUnit source; the symbol requirements report from the libraries. Their form in FieldUnit is the first Part 2 question that Part 1 depends on.
6. Sargent redrawn under the new rules as the first real sheet, compiled, diagnostics read.
7. The compiler's I/O section and the model schema.
8. Glossary amendments the foundation lists, plus the new terms: capability, cast, binding, setting scope, chip setting.
9. The alternatives ADR for Part 2, with proposals #1, #2 and #3, once Part 1 is stable.

## Changes in rev 8

The desk and fascia spike, discussed first and applied on the owner's answers: column membership kept (E41); the lamp join compromise and token scope (E42, I28, I29); consumer by processor ownership (E43); processor implied by sheet context with `Processor` as the explicit fallback, the house as the field processor (E44, I27, I31); `PanelLock` redone and `PanelMCall` pin `S` (E45); the signal lever join (I30); learned 10; task 4 and 5 statuses; next steps.

## Changes in rev 7

Step 4, the owner's usability verdict on the Scratch drawing, discussed first and applied on "4 is closed": the name as the join (E34); the lock as its own block and several device symbols per appliance (E35, I25, §4.1); symbol names decide nothing and the `IC` attribute (learned 9, E36, §4.1); `Setting` Value short (E37); `Terminal` in both uses, in pairs, merged by Value (E38, E39, I24); chain addresses typed and `Address` resolved by context (E40, I26); next steps renumbered.

## Changes in rev 6

Owner's fifth review, discussed first and applied on "go": GPIO settled as five symbols with the physical pin name as Value and the C++ build as the check (I22, §4.1); `Terminal` kept over Token and Label (§4.1); I18 and I19 reworded into Appliance and Style form; the `contact` appliance's consumer and code-line rules stated, with the refusal question left open (I23).

## Changes in rev 5

Owner's fourth review: `Derail` as the symbol name; the generic non-vital input `Contact` added as the complement of `AUXILIARY`, with `Device-Contact`; the `Binding` symbol renamed `Terminal`, with "binding" kept for the relation; `Driver-GPIO-*` as one symbol per use with a board profile check named (§4.1).

## Changes in rev 4

Owner's third review: `Kind` and `Serves` retired; `Appliance`, `Style` and the pin set replace them in three planes (I8 to I11); the symbol tables rewritten in that form with today's Kinds mapped (§4.1); the lint rule for `Binding` resolution added (I10); the symbols declared expendable (owner).

## Changes in rev 3

Owner's second review: the derived registries placed in the model as a FieldUnit index document, provenance first-class and per-binding results derived (I21); the PCA9685 split into PWM and Servo symbols and the servo-pulse cast withdrawn (I3, I4, §4.1); contact state as an enumeration (I16); Kind and Serves kept as two facts, with the reason (§4.1); the MCP23017 and MAX7313 rows made identical, MAX7313 extras marked unverified.

## Changes in rev 2

Owner's review applied: settings unified into one pattern (E15); factory settings given a home (I15); casts indexed from source (E13, I2); servo, PWM and duty codified as chip settings plus cast requirements (I3, I4); "sides" dropped from the vocabulary and the registries made derived (I1, §4.2); Encoder retired and the 74HC595 ruled out of scope (E28, learned 6); `Binding` defined as a reference to a device pin, with the normal symbols kept (I10); the sheet rule widened to the interlocking hierarchy (I13); polarity restored (E27, I7); "raw" defined (I16); the driver pattern stated (I17); the lock and the detector hold made precise (I18, I19); the Kind table and the registry table added (§4).
