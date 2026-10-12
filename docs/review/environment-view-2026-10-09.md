# The driver environment: a view for review (2026-10-09, rev 7)

- Status: a view, written top-down for discussion, revised in rev 6 to match the design checkpoint (`io-design-checkpoint-2026-10-10.md`, rev 9). Decided items cite the checkpoint (E = explicit, I = implicit). Changes are listed at the end.
- Governs: `driver-architecture-foundation.md`. The foundation says a driver "runs in an environment that supplies context" and that the environment "contains contextual data, utility functions and lifecycle support" (§2 principle 5, §3.5). This view gives that sentence a structure.
- The per-type pattern of commands, attributes and notifications is in `driver-types-view-2026-10-09.md`.

## 1. Two things called "driver"

- A **driver class** is source code, keyed by Role, Appliance, Style and pin set (I9): a symbol is one logic block. It owns: its signature, which is the set of function pins it exposes, each with one native capability and its polarity (§4.2); its commands, attributes and notifications (the driver types view); the settings it reads, by name, each with a factory default (I15); the rules that validate a command and a configuration; the transform itself; and helper functions that encapsulate the transform's context checks.
- A **driver instance** is a runtime object. It owns its identity, its bindings, its resolved settings, and its mechanism state: where a searchlight wheel is, how far a fade has gone, the last sampled contact. It owns no decision state. It is constructed complete; it never discovers anything (E20).

The environment is what the instance is given. The class is what reads it.

## 2. The problem the environment solves

A driver transforms one appliance's vocabulary into the vocabulary of the I/O pins it is wired to, and back. To do that transform an instance needs four things it does not own:

1. Who it serves.
2. What it is wired to, and what each wire carries.
3. The settings that parameterise the transform, authored at several scopes.
4. Shared, changing facts: time and the store.

Plus one thing done to it, not by it: construction and release, computed by the generator and executed by the unit.

## 3. An example before the structure

A powered switch, `783` on the Scratch sheet, with `Device-Switch` abutted on an MCP23017: signature `M`, `~{N}`, `~{R}`, `~{OCC}`.

| What the instance needs | Where it comes from | Example |
|---|---|---|
| Who it serves | the device symbol's Value, joined to the plant symbol of equal Appliance and Style in the same interlocking hierarchy (E34, I9, I13) | `Switch_Powered 783` |
| `M` is wired to | the net | expander `0x20`, pin `B1` |
| What that pin natively is | the I/O symbol's `IC` and its library `Pin.*` properties; a bidirectional chip pin is configured by what lands on it (E36, I5) | binary out |
| What `M` natively is | the device symbol's library `Pin.M` property (I5) | binary out |
| Which level means REVERSE | the pin name: `M` asserted is REVERSE; a device wired the other way is drawn with `~{M}` (I7) | asserted high |
| The cast, if the two ends differ | the cast index (E13, I2); none here | direct |
| If `M` had landed on a PWM pin instead | the two-point cast's `low`, `high`, `fade_ms`, through the scopes | `low = 400`, `high = 3700`, as the `Setting` on that net says |
| Now, in ms | service | |
| The last commanded position, restored at power-up | the store, keyed by `783` (E17) | REVERSE |
| Which processor runs it | the one `MAIN HOUSE` in the sheet's scope, or `Processor` on the I/O symbol when there are several (E44) | field unit Scratch |
| Construction with all of the above | generated setup code (E20) | |

The class's `M` code writes a binary value and nothing else. Whether that value becomes a pin level, a PWM duty or a servo angle is the cast's business, inserted by the generator. The instance never knows what chip the pin is on, never inverts (I7), and never knows which scope answered.

## 4. The structure: five parts

### 4.1 Identity

What the instance serves. Derived by the compiler, never typed beyond the Value.

- The appliance name as the vital logic knows it (`783`, `836NAB`, `1NAT`), and the part when the appliance has parts: head `B` of `836NAB` is `836NB` (I12); column 6 of the machine for a desk lamp (E41).
- The place a library call may need: which head from the top, dwarf or high, the head's Style.
- The processor that owns it, which is the consumer of what it observes (E43, E44).

Identity is readable. A driver may put it in a fault or a debug message, and may pass it to a library call such as the one that turns a signal indication into what head `B` shows. The rule is: no driver needs identity to do its transform (E21).

Identity holds no state. Stored state is a service (§4.4).

### 4.2 Bindings

What the instance is wired to, one binding per function pin. Derived from the netlist (learned 1).

- The I/O pin: which I/O symbol instance and which of its pins (`0x20.B1`), and the chip it is, from the symbol's `IC` (E36).
- The cast on the wire, if the two ends differ, with its settings.
- On a bus, the device's slot: its `Address` (E14, E30).

**One binding mechanism** (learned 3). A device symbol pin on a net with an I/O pin. Abutting the pins is the ergonomic form; a wire is the same binding. A device whose pins want different chips is a multi-unit symbol, one unit per capability, each unit placed beside its chip, on any sheet of the hierarchy; KiCad joins the units by reference, enforces one Value, and reports a unit never placed through ERC, and the netlist shows one component with every unit's pins (E56). The `Terminal` symbol that reached across sheets is retired (E56). Text labels are out (E11).

**Capabilities.** Every pin on a device symbol and every pin on an I/O symbol has one **native capability**, from one vocabulary, direction inside, stated from the unit's point of view on both sides (E8, E9). The vocabulary today: binary in, binary out, level in, level out, position out, color out, pixel out, message in, message out (I1). It is not a file: it is the set of words in the libraries' `Pin.*` fields and in the casts' from and to declarations, and the lint reports a word that appears in one and not the other. A device pin's native capability is the natural type of its function; an I/O pin's is what the chip does on that pin; a chip whose pin can do two things is drawn as one symbol per use (I3, I22).

| Pin | Native capability |
|---|---|
| `IC` MCP23017 or MAX7313 pin | binary in, or binary out, configured by what lands on it |
| `IC` PCA9685, `-PWM` symbol | level out, chip setting `frequency_hz` |
| `IC` PCA9685, `-Servo` symbol | position out, 50 Hz fixed, settings `min_us`, `max_us` |
| `Driver-GPIO-Digital` `D` | binary in or binary out, configured by what lands on it |
| `Driver-GPIO-Analog` `D` | level in |
| `Driver-GPIO-PWM` `D` | level out |
| `Driver-GPIO-Servo` `D` | position out |
| `Driver-GPIO-Pixel` `D` | pixel out, a bus |
| switch machine `M` | binary out |
| switch machine `~{OCC}`, `~{N}`, `~{R}` | binary in, asserted low |
| colour-light head `~{R}`, `~{Y}`, `~{G}` | binary out |
| one-lamp colour head `RGB`, searchlight `RGB` | color out |
| semaphore `ARM` | position out |
| desk lever contact, desk lamp | binary in, binary out, asserted low |

**Polarity** is in the pin name: `~{OCC}` is an asserted-low contact, `~{LAMP}` an asserted-low lamp (E27, I7). It is an electrical fact of the device. The generator turns it into I/O-pin configuration, inversion in the chip's register where the chip has one, in the I/O driver otherwise, and a pull-up where an asserted-low input lands on a programmable pin. No device driver inverts. `~{}` means asserted low and nothing else: a plate with two contacts or two lamps names them as two functions (E45).

**`Invert`** is a different thing: a logical complement, not an electrical one (E53). It is a field listing pin names, accepted on every symbol as a general mechanism, contacts included (I32). A lamp pin listed is lit while its token is deasserted. The unit applies it when it computes what to write; the generator's pin configuration and the drivers never see it. Library default on the symbol, overridable per instance like every field. The lock plates need it because `WLK` asserted means released, the fail-safe reading, while the green lamp shows locked (E54, E55).

**Casts.** When the two ends of a net have the same native capability the binding is direct. When they differ the generator inserts a **cast** from a bounded index, one per pin, with its own settings resolved through the scopes (E9, E13). Casts are one to one (E12); they may chain, the generator finds the path, and two paths is an error the author resolves with a `cast` setting on the net (I2). When the index has no path, the net is an error. The index is not a file: it is what the FieldUnit source tree declares, published as the index document (§5).

| From device pin | To I/O pin | Cast | Settings, with factory defaults |
|---|---|---|---|
| binary out | level out | two-point | `low = 0%`, `high = 100%`, `fade_ms = 0` |
| binary out | position out | two-angle | `low_deg`, `high_deg`, `speed` |
| binary out | color out | one-point | `color`, `brightness` |
| level out | level out | scale | `gamma`, `scale = 100%` |
| level in | binary in | threshold | `threshold = 60%`, `hysteresis = 0%` |
| same word | same word | direct | |
| any out | any in, or the reverse | none: error | |

There is no servo-pulse cast: a servo is drawn on the `-Servo` symbol or the `Driver-GPIO-Servo` symbol, whose pins are position out, and the I/O type owns the pulse mapping (I3).

**Bus and wire** (E14). A wire-capability pin admits one device pin on its net; a bus-capability pin admits many, each carrying an `Address` for its slot. A pixel chain is a net on a `pixel out` pin (E30): a bus pin offers `color out` to each slot, so a one-lamp colour head's `RGB` pin lands on it directly and a plain lamp's `~{LAMP}` lands on it through the one-point cast with its `color`. Gaps in the addresses are tolerated and the generator writes "off" (E31). An I2C expander is the same thing with its own `Address` on the bus; a CMRInet node is a remote expander (E32). Addresses are typed, never inferred from drawing order (E10, E40), and are scoped by the processor that owns the bus (I27).

**No encoders** (learned 6, E28). A mux-coded head is a device whose signature is the code we drive (`S0`, `S1`); the decoding, like a shift register on a head, is field hardware on the far side and out of scope. Casts cover one wire to one wire. Nothing is left for an encoder symbol to do.

**Several device symbols per appliance** (E35, I25). The lock mechanism is `Device-Lock` beside `Device-Switch`, one Value; the crew's local lever and lamps are desk-style devices on the field expander. Completeness is checked over the union of their pins; a function bound twice is an error. A device symbol may list more than one Style: `Device-Switch` serves `powered` and `lock`.

**Absence is information, contradiction is an error** (E49). The compiler refuses only what it cannot resolve: two valid joins, a function bound twice, a capability with no cast, two processors in scope. An appliance with no device, a device with an unbound pin, a contact or token nothing consumes, each gets one informational line and the generator stubs it, because a layout under construction is full of them. A `Device-Lock` with no sense pin is the worked case: the type simulates the sense and reports it with quality SIMULATED (E50).

**Service sources.** Things that are not appliance I/O, a GPS or NTP time source, an RFID reader, a fast-clock listener, are drivers of a third kind. They are drawn with the same symbol-and-pin pattern, their capability is a stream (message in, message out), and their consumer is the unit's services, not an appliance.

**Where it lives.** KiCad has no per-pin properties, so a native capability is a symbol property in the library, one per pin, `Pin.M = binary out` (I5). The library is the one source; the value reaches the compiler through the netlist's component fields, so no new reader is needed; the lint checks each property against the pin's electrical type, which stays for ERC only (I6). Nothing reads a symbol's name (learned 9, E36).

### 4.3 Settings

Named values that parameterise the transform. Static for the life of the unit.

- Each setting has a name, a type, a meaning and a factory default, declared by the driver or cast class that reads it, in FieldUnit source (E16, I15). A class declares which settings it reads.
- One pattern for every setting (E15): settings are fields on symbols. After the standard fields are removed (Reference, Value, Footprint, Datasheet, Description, Role, Appliance, Style, `IC`, `Pin.*`, `Address`, `Invert`, `IndicationToken`, `Processor`, and KiCad's own), every field on a symbol is one setting (learned 7, I11). A `Setting` symbol (Role `SETTING`, one passive pin) attaches settings to a net, and whatever is on that net inherits them; its Value is a short displayed name and its `Description` is the reason (E37).
- Each setting is resolved through the scopes, most specific wins (I15):

| Scope | Authored by | Drawn where |
|---|---|---|
| factory | the driver's or cast's author | FieldUnit source, published in the index document |
| layout | the layout designer, once | a `Setting` symbol on the layout anchor's net, root sheet |
| interlocking | the layout designer, per plant | a `Setting` symbol on the `Interlocking` symbol's net |
| binding | the layout designer, per function | a `Setting` symbol on that function's net |
| instance | the layout designer, per device | fields on the device symbol |
| calibrated | the unit, at run time | the store (§4.4) |

- A **calibrated** value is written by the unit when a maintainer calibrates a device on the layout (a servo's end angles, a motor's PWM endpoints, a detector's threshold). It lives in the store, keyed by identity, pin and setting, and wins over the drawing while present. Whether it survives a reflash is not to be codified (E24). The maintainer's way of calibrating is an interface to capture, not designed here (E25).
- A value in the drawing is regenerated into the firmware. That is the test for what is a setting and what is state: a servo's calibration angle is a setting; its last angle is state.
- An instance gets one value per setting; it never sees the scopes. The compiler reports an instance field that no class reads, and a setting name the index does not know.
- Chip-wide settings, where a chip has one (`frequency_hz` on a PCA9685), are fields on the I/O symbol instance; a requirement on them from a cast or an I/O type that conflicts is a compile error (I4).
- Not settings: inversion, `Invert` and blinking. Inversion is the pin name's polarity, installed by the generator (I7); `Invert` is a join fact the unit applies (E53). Blinking is rendering logic above the driver (E19): the generator resolves a flashing appearance to lit or dark per tick from the regime, and the lamp driver writes what it is given.

### 4.4 Services

Shared, changing facts and utilities. Owned by the processor, read by every instance it owns, written by none except through the fault sink and the store.

- Time: now, in ms, and a clock service for time of day and daylight. Its source is a layout policy: the processor's real clock, a fast clock from the layout, or a fixed value for a bench.
- Flash regimes: named, synchronised flashers, each with a period and a pattern, defined at the layout scope. The unit's rendering logic reads them; a driver does not.
- A fault sink: an instance reports a lamp out, a stalled servo, a lost pin. The unit decides what to do with it.
- A store (E17): state that must survive a reboot, keyed by identity. First use: each switch's last commanded position, restored before the first drive so that a switch under a parked train is not driven to a default at power-up. Rules: write on change only, never per tick; coalesce bursts; use the processor's wear-levelled store where one exists and a write budget where one does not. The store is unit-level; a driver instance reads its entry at construction and does not write it.

Operating modes are not a service to drivers. A lamp test is the unit issuing an ordinary command through the driver's command vocabulary (E22); the driver types view requires every output type's vocabulary to cover every renderable state for that reason. Simulated travel is the field unit's, not a driver's (E23).

### 4.5 Construction and release

Not a lifecycle the driver runs (E20). Setup is computed by the compiler and generator, which see every driver instance and every I/O symbol a processor owns, and executed by the unit in generated code.

1. The generator aggregates every binding's chosen capability and every I/O symbol's configuration (direction, inversion, pull-up, chip settings) per chip. Conflicts, such as a lamp on a `-Servo` symbol, are compile-time errors.
2. The unit configures the I/O symbols from that aggregate.
3. The unit restores the store, then constructs each driver instance complete, with identity, bindings and resolved settings. An instance has no "initialise yourself" step.
4. Each tick the unit observes inputs through the instances and renders demands through them, in an order the unit owns.
5. On shutdown, or on a fault the unit cannot tolerate, the unit applies the layout's release policy, a layout-scope setting. Two regimes define the pattern (E18): everything to the restrictive state; or "no dispatcher", unlocked switches and automatic signals, for running trains without an office.

## 5. What this asks of the drawing and the model

Everything above comes out of the Layout Data Model, directly or indirectly.

| Part | From the drawing | In the model |
|---|---|---|
| Identity | Values on appliance, device, desk and local symbols, joined by Value within the interlocking hierarchy; head letters; `Column` membership on the desk; the `MAIN HOUSE` or `CtcMachine` in scope, or `Processor` | derived, per device instance, with its processor |
| Bindings | nets between device pins and I/O pins, each unit of a multi-unit device beside its chip; `Address` on bus devices; `Invert` lists on plates | derived, per function pin, with the capability at each end, the cast path and its resolved settings |
| Native capabilities, polarity | `Pin.<name>` properties and `~{}` pin names on library symbols; `IC` on I/O symbols | provenance: the library versions compiled against |
| Cast index, factory defaults, type signatures | nothing drawn; FieldUnit publishes `fieldunit-index/v1` (I21) | provenance: the index version; per binding, the derived results only; never a copy |
| Settings | `Setting` symbols on the layout anchor's, the `Interlocking` symbol's and a function's net; fields on device and I/O instances | the raw scopes, and the resolved value per instance |
| Services | layout-scope settings: regimes, clock source, release policy | the layout scope |
| Store | nothing drawn; which appliances persist is implied by type | nothing; a generator fact |
| Construction | nothing drawn | generated from bindings and the index |

In the libraries since checkpoint step 4: the `Pin.*` properties, `Appliance`, `Style` and `IC`, the `Setting` symbol, the multi-unit devices and plates (E56). Still without a home: the layout anchor on the root sheet and the field-side processor symbol (I31). The index document is the first Part 2 question Part 1 depends on.

## 6. Test case: the electric lock at Sargent

Resolved by the checkpoint. `835` is drawn with the right appliance symbol, `Switch_Lock` (E26). The device bound to it today has a powered switch's signature and the wrong Style, which is why the Kind namespace was reviewed and replaced (I8). Under the three planes the drawing becomes: `Device-Switch` for the machine and its contacts, `Device-Lock` for the lock mechanism, one Value, two logic blocks (E35, I18, I25); and the crew's `Local-Switch` and `Local-Lock` as lever and lamp devices on the Sargent expander, consumed by the Sargent processor because that is the expander they land on (E43). The binding pass read all 26 of Sargent's bindings that way from the unchanged drawing, with the local levers on no column and the desk's `PanelLock` for 835 on column 13.

## 7. Open after this revision

1. The layout anchor symbol on the root sheet, and the field-side processor symbol: whether a house without hardware is drawn differently (I31).
2. The Style word lists; the form of the era indication tables in FieldUnit that carry a route's aspect set (E48).
3. Interfaces named here and not designed here (E25): the maintainer's calibration interface, which also owns every hardware fault (E51); the store; the fault sink; the clock source. Local logic for local hardware (E43).
4. Chain address implications, to be learned from use (I26). MAX7313 per-port intensity and blink, unverified.

Closed in rev 6: the lock sense (E50), the semaphore's positions (E48), the unconsumed contact (E49).

## Changes in rev 7

`Terminal` retired for multi-unit symbols (checkpoint E56): the binding paragraph, the §5 table and the library status.

## Changes in rev 6

The owner's review of the driver types view rev 2 (checkpoint E46 to E55): `Invert` as the logical complement beside `~{}` polarity, on every symbol (E53, I32); absence informational and contradiction an error, with the simulated lock sense as the worked case (E49, E50); the searchlight's pin made color out (E47); the standard-field list completed; the open items reduced.

## Changes in rev 5

Aligned with the checkpoint rev 8. Transformers renamed casts and the servo-pulse cast withdrawn in favour of the two PCA9685 symbols and the five GPIO symbols (I3, I22); `~{}` polarity restored and `motor.normal_is` dropped for it (E27, I7); encoders retired and the pixel chain made a bus with typed addresses (E14, E28, E30, E31); `Terminal` pairs merged by Value (E38, E39, I24); several device symbols per appliance and the lock as its own block (E35, I25); `IC` and the rule that symbol names decide nothing (E36); settings as fields with the six scopes and the `Setting` symbol's short Value (E15, E37, I11, I15); the index document as provenance plus derived results (I21); processor ownership as the consumer (E43, E44, I27); the 835 case resolved (§6); the model table and open items rewritten.

## Changes in rev 4

Capability lists replaced by one native capability per pin, with a bounded transformer table the generator applies one-to-one (owner's proposal). The two-match error disappears: a net either matches, transforms, or is an error. Drivers no longer adapt to domains; the motor PWM endpoints became transformer settings on the pin. The boundary between auto-inserted transformers and drawn encoders stated. The example and the model table updated.

## Changes in rev 3

Owner's answers applied: pin contracts with direction inside; exactly one match or an error, with symbol variants as the way to choose; PCA9685 contract reduced to [level out]; setting symbols wired to the `Interlocking` symbol; the store kept, with the switch-position case and the wear rules; two release regimes as the pattern; flashing resolved above the driver. The pin contract's home nailed down as `Pin.<name>` symbol properties. The 835 test case corrected: the appliance symbol is right, the question is the device. Questions replaced by three open items.
