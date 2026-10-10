# The driver environment: a view for review (2026-10-09, rev 4)

- Status: a view, written top-down for discussion. Rev 4 replaces capability lists with native capabilities plus generator-inserted transformers. Decided items are marked **(owner)**. Changes are listed at the end.
- Governs: `driver-architecture-foundation.md`. The foundation says a driver "runs in an environment that supplies context" and that the environment "contains contextual data, utility functions and lifecycle support" (§2 principle 5, §3.5). This view gives that sentence a structure.
- The per-type pattern of commands, attributes and notifications is in `driver-types-view-2026-10-09.md`.

## 1. Two things called "driver"

- A **driver class** is source code. It owns: its signature, which is the set of function pins it exposes, each with one native capability (§4.2); its commands, attributes and notifications (the driver types view); the settings it reads, by name; the rules that validate a command and a configuration; the transform itself; and helper functions that encapsulate the transform's context checks, such as `isCommandedNormal()`.
- A **driver instance** is a runtime object. It owns its identity, its bindings, its resolved settings, and its mechanism state: where a searchlight wheel is, how far a fade has gone, the last sampled contact. It owns no decision state. It is constructed complete; it never discovers anything.

The environment is what the instance is given. The class is what reads it.

## 2. The problem the environment solves

A driver transforms one appliance's vocabulary into the vocabulary of the I/O pins it is wired to, and back. To do that transform an instance needs four things it does not own:

1. Who it serves.
2. What it is wired to, and what each wire carries.
3. The settings that parameterise the transform, authored at several scopes.
4. Shared, changing facts: time and the store.

Plus one thing done to it, not by it: construction and release, computed by the generator and executed by the unit.

## 3. An example before the structure

A powered switch, say `783` at Luchessa, with a device whose signature is `M`, `OCC`, `N`, `R`. No such device is drawn yet. The only drawn switch device, at `835` in Sargent, serves an electric lock and is the test case in §6.

| What the instance needs | Where it comes from | Example |
|---|---|---|
| Who it serves | derived from the Value `783` and the plant sheet | switch 783, powered, dispatcher-controlled |
| `M` is wired to | derived from the net | expander 0x20, pin B1 |
| What that pin natively is | the I/O symbol's `Pin.B1` property, as configured | binary out |
| What `M` natively is | the device symbol's `Pin.M` property | binary out |
| The transformer, if the two differ | the generator's table; none here | direct |
| Which binary value means NORMAL | setting `motor.normal_is`, through the scopes | HIGH |
| If `M` had landed on a PWM pin instead | the two-point transformer's `M.low`, `M.high`, through the scopes | 400, 3700 |
| Now, in ms | service | |
| The last commanded position, restored at power-up | the store, keyed by `783` | REVERSE |
| Construction with all of the above | generated setup code | |

The driver class's helper `isCommandedNormal()` hides the scope lookup. The class's `M` code writes a binary value and nothing else. Whether that value becomes a pin level, a PWM duty or a servo angle is the transformer's business, inserted by the generator. The instance never knows what chip the pin is on, and never knows which scope answered.

## 4. The structure: five parts

### 4.1 Identity

What the instance serves. Derived by the compiler, never typed.

- The appliance name as the vital logic knows it (`783`, `836NAB`, `1NAT`), and the part when the appliance has parts: head `B` of `836NAB`, column 6 of the machine for a desk lamp.
- The place a library call may need (R7): which head from the top, dwarf or high, the head's display type.

Identity is readable. A driver may put it in a fault or a debug message, and may pass it to a library call such as the one that turns a signal indication into what head `B` shows. The rule is: no driver needs identity to do its transform.

Identity holds no state. Stored state is a service (§4.4).

### 4.2 Bindings

What the instance is wired to, one binding per function pin. Derived from the netlist.

- The I/O pin: which I/O symbol instance and which of its pins (`0x20.B1`).
- The transformer on the wire, if the two ends differ, with its settings.

Every pin on a device symbol and every pin on an I/O symbol has one **native capability**, from one vocabulary, direction inside, stated from the unit's point of view on both sides **(owner)**. Nothing downstream does direction arithmetic. A device pin's native capability is the natural type of its function: a motor demand is binary, a lamp is binary, an arm is a position, a contact is binary in. An I/O pin's native capability is what the chip does on that pin; a chip whose pin can do two things gets one symbol variant per use.

| Pin | Native capability |
|---|---|
| MCP23017 pin | binary in, or binary out, per the configured direction |
| PCA9685 pin, PWM variant | level out |
| PCA9685 pin, servo variant | position out |
| processor ADC pin | level in |
| switch machine `M` | binary out |
| switch machine `OCC`, `N`, `R` | binary in |
| colour-light head lamp | binary out |
| semaphore arm | position out |

When the two ends of a net have the same native capability, the binding is direct. When they differ, the generator inserts a **transformer** from a bounded table **(owner)**, one per pin, with its own settings resolved through the scopes. When the table has no entry, the net is an error.

| From device pin | To I/O pin | Transformer | Settings, with factory defaults |
|---|---|---|---|
| binary out | level out | two-point | `low = 0%`, `high = 100%`; optional `fade_ms = 0` |
| binary out | position out | two-angle | `low_deg`, `high_deg`, `speed` |
| binary out | colour out | one-point | `color`, `brightness` |
| level out | level out | scale | `gamma`, `scale = 100%` |
| position out | level out | servo pulse | `min_us`, `max_us` (only if the servo variant is not used) |
| level in | binary in | threshold | `threshold = 60%`, `hysteresis = 0%` |
| binary in | binary in | direct | |
| level in | level in | direct | |
| any out | any in, or the reverse | none: error | |

Transformers are one-to-one and inserted by the generator. Anything that changes the number of wires, a 2-to-4 selector, a pixel chain, a shift register, is an encoder, drawn as a symbol by the designer. That is the boundary.

A servo on a PCA9685 needs no symbol variant: the device pin is position out, the chip pin is level out, and the servo-pulse transformer between them carries `min_us` and `max_us`. The chip's servo mode is that transformer's configuration on that pin.

Colour is a capability of its own, **colour out**: a lit state and a colour value, dynamic. A device whose lamp changes colour has a colour-out pin: a one-lamp LED head, a searchlight-style head, a multi-colour indicator. A plain lamp stays binary out, and lands on a colour-out pin through a one-point transformer whose `color` setting gives it its fixed colour. A pixel chain's data pin, on the I/O side, is **pixel out**; nothing reaches it except a drawn chain encoder, whose device-side pins are colour out, one per slot, the slot being the encoder pin's number and the chain the encoder instance. An RGBW chain is an encoder variant. This is a paper design: it must be drawn in KiCad, with the encoder symbol and the colour-out pins, and compiled through the netlist before it counts as usable **(owner)**.

The vocabulary is a registry, like the settings registry, extended by adding a word together with the I/O pins that offer it, the device or encoder pins that use it, and its transformer entries, if any. Things that are not appliance I/O, a GPS or NTP time source, an RFID reader, a fast-clock listener, are drivers of a third kind: service sources. They are drawn with the same symbol-and-pin pattern, their capability is a stream (**message in**, **message out**), and their consumer is the unit's services, not an appliance.

Consequences. A driver class is written for its native capabilities only; it adapts to nothing. The motor settings of the earlier example, `left_pwm` and `right_pwm`, are not the switch driver's: they are the two-point transformer's `low` and `high` on that one pin. A transformer's settings are addressed per instance pin, `M.high = 3700` as a field on the device instance, with layout and interlocking defaults above it.

Where the native capability lives. KiCad has no per-pin properties, so it is a symbol property in the library, one per pin, in the same way `Role` and `Kind` are symbol properties today: `Pin.M = binary out`. The library is the one source; the value reaches the compiler through the netlist's component fields, so no new reader is needed; the lint checks each property against the pin's electrical type, which stays for ERC only.

### 4.3 Settings

Named values that parameterise the transform. Static for the life of the unit.

- Each setting has a name, a type, a meaning and a factory default. One registry lists them, for field and desk alike. A driver class declares which settings it reads.
- Each setting is resolved through four scopes, most specific wins:

| Scope | Authored by | Drawn where | How |
|---|---|---|---|
| factory default | the driver's author | the registry | |
| layout | the layout designer, once | the root sheet | a setting symbol wired to the layout's anchor symbol |
| interlocking | the layout designer, per plant | the plant sheet | a setting symbol wired to the `Interlocking` symbol **(owner)** |
| symbol instance | the layout designer, per device | the device symbol | a field on the instance |

- A setting symbol has Value = the setting's name and a field for its value, so the setting is visible when the sheet is viewed or printed. The root sheet needs an anchor symbol for the layout scope; none exists today.
- A fifth source sits above the four scopes at run time: a **calibrated** value, written by the unit when a maintainer calibrates a device on the layout (a servo's end angles, a motor's PWM endpoints, a detector's threshold). It lives in the store (§4.4), keyed by identity, pin and setting, and wins over the drawing while present. How long it lives, across reboots and reflashes, is the generator's and the store's business and is not decided here. The maintainer's way of calibrating is one more interface to capture; it is listed in §7 and not designed here.
- A value in the drawing survives a reflash by construction: it is regenerated into the firmware. That is the test for what is a setting and what is state: a servo's calibration angle is a setting; its last angle is state.
- An instance gets one value per setting; it never sees the scopes. The compiler reports an instance field that no driver class reads, and a field that is not a registered setting.
- Not settings: inversion and blinking. Inversion is an I/O-pin configuration the compiler computes from the binding and the generator installs in the chip where the chip can do it, else in the I/O symbol's code; a device driver never inverts. Blinking is rendering logic above the driver **(owner)**: the generator resolves a flashing appearance to lit or dark per tick from the regime, and the lamp driver writes what it is given.

### 4.4 Services

Shared, changing facts and utilities. Owned by the unit, read by every instance, written by none except through the fault sink and the store.

- Time: now, in ms, and a clock service for time of day and daylight. Its source is a layout policy: the processor's real clock, a fast clock from the layout, or a fixed value for a bench.
- Flash regimes: named, synchronised flashers, each with a period and a pattern, defined at the layout scope. The unit's rendering logic reads them; a driver does not.
- A fault sink: an instance reports a lamp out, a stalled servo, a lost pin. The unit decides what to do with it.
- A store **(owner)**: state that must survive a reboot, keyed by identity. First use: each switch's last commanded position, restored before the first drive so that a switch under a parked train is not driven to a default at power-up. Rules: write on change only, never per tick; coalesce bursts; use the processor's wear-levelled store where one exists and a write budget where one does not. The store is unit-level; a driver instance reads its entry at construction and does not write it.

Operating modes are not a service to drivers. A lamp test is the unit issuing an ordinary command through the driver's command vocabulary; the driver types view requires every output type's vocabulary to cover every renderable state for that reason.

### 4.5 Construction and release

Not a lifecycle the driver runs. Setup is computed by the compiler and generator, which see every driver instance and every I/O symbol on the unit, and executed by the unit in generated code.

1. The generator aggregates every binding's chosen capability and every I/O symbol's configuration (direction, inversion, pull-up, PWM frequency) per chip. Conflicts, such as two PWM frequencies on one PCA9685, are compile-time errors.
2. The unit configures the I/O symbols from that aggregate.
3. The unit restores the store, then constructs each driver instance complete, with identity, bindings and resolved settings. An instance has no "initialise yourself" step.
4. Each tick the unit observes inputs through the instances and renders demands through them, in an order the unit owns.
5. On shutdown, or on a fault the unit cannot tolerate, the unit applies the layout's release policy, a layout-scope setting. Two regimes define the pattern **(owner)**: everything to the restrictive state; or "no dispatcher", unlocked switches and automatic signals, for running trains without an office.

## 5. What this asks of the drawing and the model

Everything above comes out of the Layout Data Model, directly or indirectly.

| Part | From the drawing | In the model |
|---|---|---|
| Identity | Values on appliance, part and device symbols; the plant sheet | derived, per device instance |
| Bindings | nets between device pins and I/O pins | derived, per function pin, with the transformer and its resolved settings |
| Native capabilities | `Pin.<name>` properties on library symbols | one copy per symbol and pin |
| Transformer table | nothing drawn; the generator's | nothing; the model names the transformer per binding |
| Settings | setting symbols on the root and plant sheets; fields on device instances; the registry | the raw scopes, and the resolved value per instance |
| Services | layout-scope settings: regimes, clock source, release policy | the layout scope |
| Store | nothing drawn; which appliances persist is implied by type | nothing; a generator fact |
| Construction | nothing drawn | generated from bindings and contracts |

Three things have no home today: the `Pin.<name>` properties, the setting symbol and the layout anchor symbol on the root sheet, and the registry's content, which exists as a file whose entries are evidence only.

## 6. Test case: the electric lock at Sargent

`835` is drawn with the right appliance symbol, `Railroad:Switch_Lock` **(owner)**. The device bound to it is `Device-Switch-StallMotor-Sensed-OS`, whose signature is a powered switch's: motor out, two point contacts in. At a lock the same four wires mean different things: the output is the lock release, and the two lamps show the request state and the lock state. The crew's lever and key on the same expander operate the switch when it is unlocked.

Under this view the question the case poses is: does one device class serve both appliances with the same wires and different commands, or does a lock get its own device symbol and class? The driver types view takes the second position and marks it for confirmation. Either way the compiler must check the device's signature against the appliance's type, and both facts are in the model.

## 7. Open after this revision

1. The lock device: its own symbol and class, or the powered switch's signature reinterpreted by appliance type. See the driver types view, type 3.
2. The layout anchor symbol on the root sheet: a `Layout` symbol in the `Railroad` library with one pin for setting symbols.
3. The capability vocabulary today: binary in, binary out, level in, level out, position out, colour out on both sides; pixel out on the I/O side only; message in and message out for service sources. A registry, extended as §4.2 says.
4. Per-pin instance settings are addressed `<pin>.<setting>` on the device instance (`M.high`, `LAMP.color`). To confirm.
5. Interfaces named here and not designed here, to be captured one by one: the maintainer's calibration interface; the store; the fault sink; the clock source.
6. The pixel chain and colour-out design must be proven in KiCad before it is relied on: an encoder symbol, a one-lamp colour head, a plain lamp through the one-point transformer, all on a chain, compiled through the netlist.

## Changes in rev 4

Capability lists replaced by one native capability per pin, with a bounded transformer table the generator applies one-to-one (owner's proposal). The two-match error disappears: a net either matches, transforms, or is an error. Drivers no longer adapt to domains; the motor PWM endpoints became transformer settings on the pin. The boundary between auto-inserted transformers and drawn encoders stated. The example and the model table updated.

## Changes in rev 3

Owner's answers applied: pin contracts with direction inside; exactly one match or an error, with symbol variants as the way to choose; PCA9685 contract reduced to [level out]; setting symbols wired to the `Interlocking` symbol; the store kept, with the switch-position case and the wear rules; two release regimes as the pattern; flashing resolved above the driver. The pin contract's home nailed down as `Pin.<name>` symbol properties. The 835 test case corrected: the appliance symbol is right, the question is the device. Questions replaced by three open items.
