# Driver types: commands, attributes, notifications (2026-10-09, rev 1)

- Status: a view for discussion. It fills the per-type pattern the owner asked for. Nothing here is decided.
- Governs: `driver-architecture-foundation.md`. Companion: `environment-view-2026-10-09.md` (what an instance is given).
- A driver type is a class. The pattern below is what the class owns.

## 1. The pattern

Every driver type is described by the same seven fields.

| Field | Meaning |
|---|---|
| Serves | the appliance type, or the office or fascia function, the type serves |
| Signature | its function pins, each with its pin contract |
| Commands | what the unit may ask it to do, in the appliance's vocabulary |
| Attributes | what the unit may read from it, raw, with no judgement |
| Notifications | what it reports without being asked, to the unit or the fault sink |
| Settings | the registry names it reads |
| Mechanism state | the only state it keeps |

Three rules hold across every type.

1. A command vocabulary covers every state the hardware can show, so that a lamp test, a maintainer exercise or a bench check is an ordinary command and not a mode.
2. Attributes are raw. A switch machine reports two contacts; it never reports "out of correspondence". That judgement is the vital logic's, per the relay model.
3. A notification is a fact the driver observed, never a decision.

Three families share the pattern. Device types (§2) talk to the unit in appliance vocabulary. Encoder types (§3) have no commands: the unit never addresses them. I/O types (§4) talk in pin vocabulary.

## 2. Device types

The types the SPCoast drawings need today. Each pin has one native capability: BI = binary in, BO = binary out, PO = position out. A device pin never names a domain; when it lands on a pin of another capability, the generator inserts a transformer (environment view §4.2).

### 2.1 Switch machine

| Field | |
|---|---|
| Serves | a powered switch (`Switch_Powered`) |
| Signature | `M` [BO]; `N`, `R` [BI] as packaging; `OCC` [BI] as packaging |
| Commands | `drive(NORMAL)`, `drive(REVERSE)` |
| Attributes | `contactN`, `contactR`, `occupied`, each when wired |
| Notifications | `contactsChanged` |
| Settings | `motor.normal_is` |
| Mechanism state | last value written |

One type for a stall motor, a PWM-driven motor and a servo. `M` is a binary demand; on a PWM pin the two-point transformer carries `M.low` and `M.high`, and on a servo pin the two-angle transformer carries `M.low_deg`, `M.high_deg` and `M.speed`. A simulated machine is not a driver type: the field unit simulates an appliance, and the driver renders what it is told.

### 2.2 Retired

The servo switch machine of rev 1 is §2.1 with a transformer.

### 2.3 Electric lock (to confirm)

| Field | |
|---|---|
| Serves | an electrically locked hand-throw switch (`Switch_Lock`) |
| Signature | `UNLOCK` [BO]; `N`, `R` [BI] as packaging; `OCC` [BI] as packaging |
| Commands | `lock()`, `unlock()` |
| Attributes | `contactN`, `contactR` when wired |
| Notifications | `contactsChanged` |
| Settings | `lock.unlocked_is` |
| Mechanism state | last value written |

The crew's lever, key and lamps are fascia types (§2.8, §2.9), bound to the same appliance as local clients. This type is the open item from the environment view §6: it either exists as its own symbol and class, as here, or the powered switch type serves a lock with its wires reinterpreted. This view takes the first position because the commands differ, and the command vocabulary is what makes a type.

### 2.4 Detector

| Field | |
|---|---|
| Serves | a track circuit |
| Signature | `OCC` [BI] |
| Commands | none |
| Attributes | `occupied`, `quality` |
| Notifications | `changed` |
| Settings | `detector.hold_ms` (zero for a current detector) |
| Mechanism state | hold timer |

Whether the release hold is the detector's or the track circuit's is a vital-logic question, listed in the foundation. This view keeps it here because an optical detector's hold is a property of the sensor, not of the circuit.

### 2.5 Colour-light head

| Field | |
|---|---|
| Serves | a head of a signal mast (`Signal Head - CL`) |
| Signature | `R`, `Y`, `G` [BO]; `L` [BO] as packaging |
| Commands | `show(lamps)`, where `lamps` is the lit set, already resolved for flashing by the unit; `show(ALL)` and `show(NONE)` are members |
| Attributes | `shown` |
| Notifications | `lampOut` when the hardware can tell |
| Settings | none |
| Mechanism state | none |

The translation from a signal indication to a head's lamps is not in this type. The unit does it, with the rulebook and the head's identity, and hands the type a lit set. Brightness, gamma and fade are the two-point transformer's settings on each lamp pin when it lands on a PWM pin.

A one-lamp colour head, an LED searchlight or a NeoPixel, is a signature variant: one `LAMP` pin, natively colour out, and the command `show(colour)`. It is not a three-lamp head through an encoder, because its colour is dynamic. Whether it is a variant of this Kind or its own Kind is open; the name "searchlight" is reserved for the prototype head with a vane.

### 2.6 Semaphore head

| Field | |
|---|---|
| Serves | a head of a signal mast (`Signal Head - SemaphoreU2`, `SemaphoreU3`) |
| Signature | `ARM` [PO]; `LAMP` [BO] |
| Commands | `show(position, lampLit)` with position HORIZONTAL, DIAGONAL or VERTICAL; a two-position head refuses DIAGONAL at compile time |
| Attributes | `position`, `moving` |
| Notifications | `arrived` |
| Settings | `semaphore.stop_deg`, `semaphore.approach_deg`, `semaphore.clear_deg`, `servo.speed` |
| Mechanism state | current angle, target angle |

Whether the lamp is lit by daylight is the unit's decision from the clock service; the type receives `lampLit`.

### 2.7 Lamp

| Field | |
|---|---|
| Serves | a desk lamp (`PanelLamp-*`), a fascia lamp (`Local-Lamp`), a field lamp (maintainer call, auxiliary) |
| Signature | `LAMP` [BO] |
| Commands | `set(LIT)`, `set(DARK)` |
| Attributes | `shown` |
| Notifications | none |
| Settings | none; brightness is the transformer's, colour is the pixel encoder's |
| Mechanism state | none |

One type for office and field. Which tokens light a desk lamp is a binding fact the unit uses, not a property of the type.

### 2.8 Lever

| Field | |
|---|---|
| Serves | a desk or fascia lever: switch (`PanelSwitch`, `Local-Switch`), signal (`PanelSignal`), lock (`PanelLock`), key (`Local-Lock`), code button (`PanelCode`), maintainer call button (`PanelMCall`), auxiliary (`PanelAuxiliary`) |
| Signature | one to three contacts, each [BI] |
| Commands | none |
| Attributes | `position`: one of the contact set's named positions (N, R; L, N, R; IN, OUT; DOWN, UP) |
| Notifications | `moved` |
| Settings | `lever.debounce_ms` |
| Mechanism state | debounce timers |

A code button's one-shot is office logic, not a lever property. A plate with lamps on it (a switch lever's `NWK`, `RWK`; a lock plate's `WLQK`, `WLK`) is one lever instance plus one lamp instance per lamp, bound to the same appliance. The symbol is one; the driver instances are several.

### 2.9 Lock plate, fascia (composite, to confirm)

Not a type. `Local-Lock` compiles to one lever (`WLQ`, a key) and two lamps (`WLQK`, `WLK`) under §2.7 and §2.8. The blink of `WLQK` while a request waits is unit rendering, like every other blink. Listed here so that the composite is explicit.

## 3. Encoder types

An encoder sits on a net between a device pin and an I/O pin and transforms one set of wires into another. The unit never addresses it, so it has no commands and no attributes. Its pattern is smaller.

| Field | Meaning |
|---|---|
| Serves | nothing; it is transparent |
| Signature | device-side pins with contracts, and I/O-side pins with contracts |
| Transform | the truth table or mapping, in the symbol's documentation |
| Notifications | none |
| Settings | per encoder, if any |
| Mechanism state | the last device-side values, when the transform needs them together |

Two needed today: a 2-to-4 selector (device side three or four [BO] lamps, I/O side two [BO]); and a pixel chain (device side N slots, each colour out, I/O side one pixel-out data pin). A plain lamp reaches a slot through the one-point transformer with its `color` setting; a colour-out device pin reaches it directly. The 74HC595 on a head is a third (device side eight [BO], I/O side a serial pair). None exists as a symbol yet, and the chain must be drawn and compiled before it is relied on. The boundary with transformers: a transformer is one wire to one wire and the generator inserts it; an encoder changes the wire count and the designer draws it.

## 4. I/O types

An I/O type serves no appliance. It serves pins.

| Field | Meaning |
|---|---|
| Serves | one chip or one transport node |
| Signature | its pins, each with a contract |
| Commands | `write(pin, value)`, `read(pin)`; `configure(pin, capability, inversion, pullup, frequency)` at construction only |
| Attributes | `health` |
| Notifications | `lostComms`, `configurationRefused` at construction |
| Settings | address; chip-wide values such as PWM frequency, which the generator checks for conflict |
| Mechanism state | the output latch and input image between `flush` and `sample` |

Types needed today: MCP23017, MAX7313, PCA9685. Needed next: processor GPIO, a NeoPixel chain data pin, a CMRI node, an MQTT bit node, a mock for the bench and the virtual plant.

## 5. What the drawing and the model need for this

- A device symbol per device type, with one `Pin.<name>` native capability per pin, and nothing in the symbol that is a command, an attribute or a setting of another scope.
- A DEVICE Kind named for the appliance family it serves, plus a variant word only when the signature differs: `SWITCH_MACHINE`, `SWITCH_SENSE`, `SWITCH_LOCK`, `DETECTOR`, `HEAD_COLOR_LIGHT`, `HEAD_SEMAPHORE`, `LAMP`, `LEVER`. Eight, from eighteen today. Domains, chips and packaging never appear in a Kind. The appliance Kinds must use the same family words so the compiler can match them.
- The appliance type each device type serves, so the compiler can refuse a mismatch (a powered switch device on a `Switch_Lock`).
- For a plate symbol that compiles to several instances, the rule that says which pins form the lever and which form lamps. The pin contract says it: [BI] pins are the lever, [BO] pins are lamps.
- Nothing about commands, attributes or notifications. They are code, and the model carries only what instantiates them.

## 6. Open

1. The electric lock type (§2.3): own symbol and class, or the powered switch's wires reinterpreted.
2. The detector hold (§2.4): driver or track circuit.
3. Whether `lampOut` is worth a notification before any hardware can report it.
4. The name of the capability for a pixel chain's data pin.
