# Driver types: commands, attributes, notifications (2026-10-09, rev 2)

- Status: a view for discussion, revised in rev 2 to match the design checkpoint (`io-design-checkpoint-2026-10-10.md`, rev 8). Decided items cite the checkpoint (E = explicit, I = implicit); the rest is the pattern filled in and still open to the owner.
- Governs: `driver-architecture-foundation.md`. Companion: `environment-view-2026-10-09.md` (what an instance is given).
- A driver type is a class, keyed by Role, Appliance, Style and pin set (I9). The pattern below is what the class owns.

## 1. The pattern

Every driver type is described by the same seven fields (I17).

| Field | Meaning |
|---|---|
| Serves | the Appliance and Style the type serves; a type with no Style serves every Style of its Appliance |
| Signature | its function pins, each with one native capability and its polarity in the name |
| Commands | what the unit may ask it to do, in the appliance's vocabulary |
| Attributes | what the unit may read from it, raw, with no judgement |
| Notifications | what it reports without being asked, to the unit or the fault sink |
| Settings | the names it reads, each with a factory default declared in source |
| Mechanism state | the only state it keeps |

Three rules hold across every type.

1. A command vocabulary covers every state the hardware can show, so that a lamp test, a maintainer exercise or a bench check is an ordinary command and not a mode (E22).
2. Attributes are raw (I16). A contact is one of CLOSED or OPEN, after the I/O's inversion so that the word names the contact and not the wire, with its sample time and a quality of GOOD, STALE or LOST. Never a boolean, never a position, never a token. A switch machine reports two contacts; it never reports "out of correspondence". That judgement is the vital logic's, per the relay model.
3. A notification is a fact the driver observed, never a decision.

Two families share the pattern. Device types (§2) talk to the unit in appliance vocabulary. I/O types (§4) talk in pin vocabulary. Service sources (§5) feed the unit's services. Encoder types are retired (§3).

Capabilities below: BI = binary in, BO = binary out, PO = position out, CO = colour out. `~{}` in a pin name means asserted low (I7). A device pin never names a chip or a domain; when it lands on a pin of another capability, the generator inserts a cast (environment view §4.2).

## 2. Device types

The types the SPCoast drawings need today, one per device symbol in the checkpoint's §4.1.

### 2.1 Switch machine: `Device-Switch`

| Field | |
|---|---|
| Serves | switch, Styles `powered` and `lock` (the machine half of a locked switch, I25) |
| Signature | `M` [BO]; `~{N}`, `~{R}` [BI] as packaging; `~{OCC}` [BI] as packaging |
| Commands | `drive(NORMAL)`, `drive(REVERSE)` |
| Attributes | `contactN`, `contactR`, `occupied`, each when wired |
| Notifications | `contactsChanged` |
| Settings | none of its own; `M` asserted is REVERSE, and a machine wired the other way is drawn with `~{M}` |
| Mechanism state | last value written |

One type for a stall motor, a PWM-driven motor and a servo. `M` is a binary demand; on a `level out` pin the two-point cast carries `low`, `high` and `fade_ms`, and on a `position out` pin the two-angle cast carries `low_deg`, `high_deg` and `speed`. The earlier `motor.normal_is` setting is gone: polarity is in the pin name. A simulated machine is not a driver type (E23).

### 2.2 Manual switch with point sensing: `Device-Switch-ManualSensed`

| Field | |
|---|---|
| Serves | switch, Style `manual_sensed` |
| Signature | `~{N}`, `~{R}` [BI] |
| Commands | none |
| Attributes | `contactN`, `contactR` |
| Notifications | `contactsChanged` |
| Settings | none |
| Mechanism state | none |

### 2.3 Electric lock: `Device-Lock`

| Field | |
|---|---|
| Serves | switch, Style `lock` only |
| Signature | `UNLOCK` [BO]; `~{LOCKED}` [BI] if the hardware has a lock sense (open) |
| Commands | `lock()`, `unlock()` |
| Attributes | `locked` when wired |
| Notifications | `lockChanged` |
| Settings | none known |
| Mechanism state | last value written |

Its own logic block, by the owner's ruling: the lock's behaviour differs from the switch's even though they interact (E35, I18). It shares its Value with the `Device-Switch` of the same switch, and completeness is checked over both symbols' pins (I25). The crew's lever, key and lamps are lever and lamp devices (§2.8, §2.9) on the field expander, consumed by the field processor because that is the expander they land on (E43). The lock request contact is the local lever's `WLQ` pin (I23).

### 2.4 Track circuit: `Device-TrackCircuit`

| Field | |
|---|---|
| Serves | track_circuit |
| Signature | `~{OCC}` [BI] |
| Commands | none |
| Attributes | `occupied`, `quality` |
| Notifications | `changed` |
| Settings | `hold_ms`, type ms, factory default 0, interlocking and instance scopes (I19) |
| Mechanism state | hold timer |

While `hold_ms` is greater than zero the driver holds `occupied` for `hold_ms` after the contact last opened, so that an optical detector does not report a gap between cars as a clear track. The track circuit object keeps no hold of its own (I19, closing the question of rev 1).

### 2.5 Colour-light head: `Device-Head-CL-3Lamp`, `-RGB`, `-Mux2`

Three signatures of one head Style, `CL`, each its own type because a symbol is one logic block (I9).

| Field | `-3Lamp` | `-RGB` | `-Mux2` |
|---|---|---|---|
| Serves | head, Style `CL` | head, Style `CL` | head, Style `CL` |
| Signature | `~{R}`, `~{Y}`, `~{G}` [BO]; `~{L}` [BO] as packaging | `RGB` [CO] | `S0`, `S1` [BO], a select code with no asserted state |
| Commands | `show(lamps)`, the lit set; `show(ALL)` and `show(NONE)` are members | `show(colour)`, including off | `show(code)`, covering every code |
| Attributes | `shown` | `shown` | `shown` |
| Notifications | `lampOut` when the hardware can tell | none | none |
| Settings | none | none | none |
| Mechanism state | none | none | none |

The translation from a signal indication to what a head shows is not in these types. The unit does it, with the rulebook and the head's identity, and hands the type a lit set, a colour or a code, already resolved for flashing (E19). Brightness, gamma and fade are the two-point cast's settings on each lamp pin when it lands on a `level out` pin. The `-RGB` head's colour is dynamic, which is why it is a colour-out pin and not three lamps through anything; on a pixel chain it lands on its slot directly, with an `Address` (E30). The `-Mux2` head is our side of a serialise-and-decode pattern; the decoder on the head is field hardware and out of scope (E28).

### 2.6 Semaphore and searchlight heads: `Device-Head-Semaphore`, `Device-Head-Searchlight`

| Field | Semaphore | Searchlight |
|---|---|---|
| Serves | head, Style `semaphore` | head, Style `searchlight` |
| Signature | `ARM` [PO]; `~{LAMP}` [BO] | `VANE` [PO]; `~{LAMP}` [BO] |
| Commands | `show(position, lampLit)`, position HORIZONTAL, DIAGONAL or VERTICAL | `show(position, lampLit)`, one position per roundel |
| Attributes | `position`, `moving` | `position`, `moving` |
| Notifications | `arrived` | `arrived` |
| Settings | `stop_deg`, `approach_deg`, `clear_deg`, `speed` | one angle per position, `speed` |
| Mechanism state | current angle, target angle | current angle, target angle |

Whether the lamp is lit by daylight is the unit's decision from the clock service; the type receives `lampLit`. Whether a two-position semaphore is a Style, a setting or a third signature is open (checkpoint task 2).

### 2.7 Lamp: `Device-Lamp`

| Field | |
|---|---|
| Serves | lamp, every Style (`maintainer_call`, `auxiliary`, and the desk's `indication`) |
| Signature | `~{LAMP}` [BO] |
| Commands | `set(LIT)`, `set(DARK)` |
| Attributes | `shown` |
| Notifications | none |
| Settings | none; brightness is the two-point cast's, colour on a chain is the one-point cast's `color` |
| Mechanism state | none |

One type for office and field. On a pixel chain the lamp carries an `Address` and the one-point cast gives it its fixed colour (E30). Which indications light a desk lamp is a join fact, Value or token list (E42), that the unit uses and the type never sees.

### 2.8 Lever: `PanelSwitch`, `PanelSignal`, `PanelLock`, `PanelCode`, `PanelMCall`, `Local-Switch`, `Local-Lock`

| Field | |
|---|---|
| Serves | lever, Styles `switch`, `signal`, `lock`, `code`, `maintainer_call` |
| Signature | one to three contacts, each [BI], named for their AAR suffix: `~{NWS}`, `~{RWS}`; `~{NGS}`, `~{HS}`, `~{SGS}`; `~{S}` (E45) |
| Commands | none |
| Attributes | `position`: one of the contact set's named positions |
| Notifications | `moved` |
| Settings | `debounce_ms` |
| Mechanism state | debounce timers |

A code button's one-shot is office logic, not a lever property. A plate with lamps on it (a switch lever's `~{NWK}`, `~{RWK}`; a signal lever's `~{NGK}`, `~{SGK}`, `~{TEK}`) is one lever instance plus one lamp instance per lamp, bound to the same appliance: [BI] pins are the lever, [BO] pins are lamps. The symbol is one; the driver instances are several. Tokens derive as Value plus pin name, `783NWS`, `MC1S`, so no token field is typed (I28). The consumer is the processor that owns the expander the plate lands on: the CTC machine for a desk plate, the field unit for a local one (E43). `PanelLock` is being redone so that its two contacts and two lamps are four distinct names, since `~{}` is reserved for asserted low (E45).

### 2.9 Local lock plate: `Local-Lock`

Not a type. `Local-Lock` compiles to one lever (`WLQ`, the crew's key or request) and two lamps (`WLQK`, `WLK`) under §2.7 and §2.8, on the field processor. The blink of `WLQK` while a request waits is unit rendering, like every other blink (E19). Listed here so that the composite is explicit.

### 2.10 Contact: `Device-Contact`

| Field | |
|---|---|
| Serves | contact, the generic non-vital input (I23) |
| Signature | `~{IN}` [BI] |
| Commands | none |
| Attributes | `state` |
| Notifications | `changed` |
| Settings | `debounce_ms` |
| Mechanism state | debounce timer |

The complement of the auxiliary lamp. Who consumes it is its Style plus its Value; whether an unconsumed contact is refused is open (I23).

## 3. Encoder types: retired

Rev 1 had encoders for a 2-to-4 selector, a pixel chain and a shift register. All three are gone (learned 6, E28, E30): the selector is the `-Mux2` head's own signature, the chain is a bus with addressed devices, and the shift register is field hardware beyond our side of the wire. A cast is one wire to one wire and the generator inserts it; nothing changes the wire count on our side.

## 4. I/O types

An I/O type serves no appliance. It serves pins. It is keyed by the symbol's `IC`, never by the symbol's name or shape (E36).

| Field | Meaning |
|---|---|
| Serves | one chip, one processor pin use, or one transport node |
| Signature | its pins, each with one native capability from the library's `Pin.*` properties |
| Commands | `write(pin, value)`, `read(pin)`; `configure(pin, capability, inversion, pullup)` at construction only |
| Attributes | `health` |
| Notifications | `lostComms`, `configurationRefused` at construction |
| Settings | `Address` on a bus; chip-wide values, which the generator checks for conflict (I4); `Processor` when the sheet's scope holds more than one (E44) |
| Mechanism state | the output latch and input image between `flush` and `sample` |

| Type (`IC`) | Pins | Notes |
|---|---|---|
| MCP23017 | `A1..B8` BI or BO, configured by what lands | 4-pins-per-unit shape mirrors the owner's boards; other shapes are the same `IC` (E36) |
| MAX7313 | `A1..B8` BI or BO | per-port intensity and blink unverified |
| PCA9685, `-PWM` symbol | `A1..B8` level out | `frequency_hz` chip setting |
| PCA9685, `-Servo` symbol | `A1..B8` position out | 50 Hz fixed; `min_us`, `max_us`; a lamp on it is refused (I3) |
| GPIO, five symbols by use | `D` BI/BO, level in, level out, position out, pixel out | Value = the board core's pin name, checked by the C++ build (I22) |
| pixel chain data pin | one bus pin offering colour out per slot | addresses typed; gaps off; past the strip silent (E31, I26) |
| CMRInet node | a remote expander | to be proven later (E32) |
| mock | any | for the bench and the virtual plant |

## 5. Service sources

Drivers of a third kind, for things that are not appliance I/O: a GPS or NTP time source, an RFID reader, a fast-clock listener. Same symbol-and-pin pattern; capability `message in` or `message out`; consumer the unit's services. Their pattern is the I/O type's with `read` replaced by a stream.

## 6. What the drawing and the model need for this

- A device symbol per device type, carrying `Appliance` and `Style` and one `Pin.<name>` native capability per pin, polarity in the pin name, and nothing that is a command, an attribute or a setting of another scope (I5, I7, I8).
- An appliance symbol per plant appliance carrying the same `Appliance` and `Style`, so the compiler joins a device to its appliance by Value and refuses a mismatch (I9).
- `IC` on every I/O symbol, `Address` on bus devices and expanders, `Processor` on an I/O symbol when its sheet's scope holds several (E36, E40, E44).
- For a plate symbol that compiles to several instances, the rule that says which pins form the lever and which form lamps: [BI] pins are the lever, [BO] pins are lamps.
- The type signatures, their settings and factory defaults, published by FieldUnit in the index document the compiler reads (I21).
- Nothing about commands, attributes or notifications. They are code, and the model carries only what instantiates them.

## 7. Open

1. `Device-Lock`'s `~{LOCKED}` sense: does the hardware have one.
2. Whether `lampOut` is worth a notification before any hardware can report it.
3. The semaphore's two or three positions: Style, setting or signature.
4. The Style word lists, and refusal of an unconsumed `contact` (I23).
5. The four names for `PanelLock`'s two contacts and two lamps (E45).

## Changes in rev 2

Aligned with the checkpoint rev 8. Types renamed to the device symbols of its §4.1 and keyed by Appliance, Style and pin set; polarity written into every signature and `motor.normal_is` dropped (I7); the lock made its own block with the `Device-Switch` beside it (E35, I18, I25); the manual sensed switch and the contact added (I23); the three colour-light signatures made three types and the encoders retired (I9, E28, E30); the searchlight added; raw attributes made the CLOSED/OPEN enumeration with quality (I16); levers given derived tokens, the consumer rule and the `PanelLock` redo (E43, E45, I28); I/O types keyed by `IC` with the two PCA9685 symbols, the five GPIO symbols and the chain as a bus (E36, I3, I22); service sources given their own section; the detector hold closed (I19); the model needs and open items rewritten.
