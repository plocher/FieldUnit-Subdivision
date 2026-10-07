# 0004. The crew's unlock request, head appliances, milepost anchors, and the field I/O review

- Status: proposed. D1–D13 record the owner's rulings of 2026-10-07; only R5 is asked.
- Date: 2026-10-07
- Amends: FieldUnit `docs/adr/0003-field-io-symbols.md` (frozen), closing its O1 and O3.
- Order of authority: the relay model and AAR practice (FieldUnit `docs/GLOSSARY.md` §10.6), then FieldUnit `src/`.

## Decisions requested

- R5. The local switch lever while locked and at unlock: while `HAND_LOCKED`, the field unit ignores the lever and its N/R lamps show the points, so a moved lever is visibly out of correspondence. After an unlock, or after a relock has driven the points to N, the lever's demand is honoured only once the lever has been seen in correspondence with the points (no movement on release). Default: yes.

Answered 2026-10-07: R1 (stick rule) and R4 (desk display) accepted; R2 and R3 replaced by D10.

## Rulings recorded (owner, 2026-10-07)

### The crew's unlock request (closes ADR 0003 O1)

- D1. The crew's request is the non-vital indication `WLQK` (switch lock, request, indication), e.g. `835WLQK`. `WLR` is not used as a prefix: it is FieldUnit's switch-lock relay (`Switch::WLR()`).
- D2. The lock keeps the electric-lock tokens `WLS` (release, control) and `WLK` (released, indication). `RWS`/`RWK` are not used for a lock: on a switch lock they would collide with the switch's own tokens (`835RWK` is "switch 835 reversed").
- D3. The sequence:

  | Step | Who | Token | Vital |
  |---|---|---|---|
  | Crew turns the key or moves the local lock lever N to R | fascia `Local-Lock` | `835WLQK` up | no |
  | Desk 835 N lamp blinks | desk `PanelLock` | `WLQK` | no |
  | Dispatcher moves the lock lever to R and codes it | desk to field | `835WLS` | yes: released only with every governing signal at STOP and no time locking running |
  | Field unit releases the lock (removes `HAND_LOCKED`); approval means unlocked | field to desk | `835WLK` up; desk R lamp lit | yes |
  | Crew operates the points (hand, or `Local-Switch`) | fascia | none on the code line | the field unit uses the sensed position in all route logic; the dispatcher never sees it |
  | Crew returns the key or lever to N | fascia | `WLQK` down | no |
  | Field unit drives the points to N, relocks once they are normal and in correspondence (D10), and drops the release: a new unlock needs `WLS` to N and back to R (D11) | field to desk | `835WLK` down | yes |
  | Desk lock lever is at R with its R lamp dark: out of correspondence until the dispatcher restores it, as `SGK` drops for a signal knocked down by a train (D11); no extra blink | desk | | |

- D4. Desk `PanelLock` (Kind `LOCK_LEVER_2LAMP_2CONTACT`): pins unchanged (N contact `WLS`, R contact `~{WLS}`, R lamp `~{WLK}`, N lamp `WLK`). The N lamp blinking on `WLQK` belongs to the Kind's logic block, not to a pin.
- D5. Fascia `Local-Lock` (Kind `LOCK_LEVER`; ADR 0003's `Local-Lock-2Lamp`, the one-lamp plate dropped). Its two lamps are two concepts, not complements:

  | Pin | Lamp | Shows |
  |---|---|---|
  | `~{WLQ}` | (key or lever) | the crew's request, replacing `~{WLS}` (the dispatcher's control, drawn there by mistake in the first pass) |
  | `~{WLQK}` | amber, UNLCK | off; blinking while the request waits (out of correspondence); steady once the field unit has unlocked (`WLK`) |
  | `WLK` (unbarred) | green, LOCK | lit while locked (`WLK` down) |

  The blink-then-steady behaviour belongs to the `LOCK_LEVER` logic block.

- D10. A `SWITCH_LOCK` has a motor: the field unit controls the points and can always restore them, so a crew relock drives them to N first. A `SWITCH_LOCK` whose device has no motor (`SWITCH_SENSE` alone) is an error. An electrically locked hand-thrown switch (points feedback interlocked with a mechanical points lock, its own rulebook process) is not supported yet. This amends ADR 0003 D4 and its worked example for Sargent 835 (`Device-Switch-Sense` alone).
- D11. An unlock is used up (stick rule; was R1), and the desk shows the knocked-down lock lever by its dark R lamp (was R4).

### Heads

- D6. Head symbols are appliances: Role `APPLIANCE`, Kind by what the head can display, not how it is built: `Signal Head - CL` `HEAD_COLOR_LIGHT`, `Signal Head - SemaphoreU2` `HEAD_SEMAPHORE_2POS`, `Signal Head - SemaphoreU3` `HEAD_SEMAPHORE_3POS` (was `COMPONENT`/`HEAD`). The mast stays the signal. The generator checks that a head device can render its head's Kind. Head devices are heads, not lamps, because they need indication-to-aspect logic: `Device-Head-1LED-NeoPixel`, `Device-Head-1LED-PWM` sit beside `Device-Lamp-NeoPixel`.

### Mileposts

- D7. `Milepost` is a `TRACK` marker with one pin on a track net; its Value is the milepost. It anchors that net's position; every other position is derived through the track topology, never typed on each symbol. Two anchors give an interlocking its direction (cross-checked against mast letters); across interlockings they order the subdivision for lateral alignment. Open: the symbol's look (keep the track diagram uncluttered), a line name for branch milepost series, and what becomes of the MAIN HOUSE `Milepost` field.

### Field I/O review (amends ADR 0003, applied in InterlockingPlant `e10c0da`)

- D8. Driver symbols have no direction or polarity of their own: pins are bidirectional and take both from what is wired to them; the generator enables a pull-up where an active-low input is attached (no `Pullups` attribute; amends D6). One convention: Kind `I2C-<chip>` (`I2C-MCP23017`, `I2C-PCA9685`, `I2C-MAX7313`), pins `A1..A8`, `B1..B8`, pin N is chip bit N-1 (amends D10). `PanelColumn-MAX7313` is `Driver-I2C-MAX7313`.
- D9. Asserted-low `~{X}` is the norm for field inputs and outputs and for every desk lever and lamp pin; families are checked for exceptions. `Device-Head-3LED-Mux2` `S0`, `S1` are plain (a select code has no asserted state). `PanelAuxiliary` takes Role `PANEL` with the other desk symbols.

### The unified project (owner, 2026-10-07)

- D12. Hierarchy. Layout 1:M machines 1:M plants; no plant is under two machines. A symbol belongs to the `INTERLOCKING` on its own sheet or, failing that, the nearest ancestor sheet that has one; likewise for `MACHINE`. At most one of each per sheet, and a plant's `INTERLOCKING` sits on its machine's sheet or below it. Nothing else in the hierarchy carries meaning: Trackplan, Panel and Field I/O sheets, and how many there are, are drafting conventions; a plant may be one sheet holding all of them. Symbols are classified by Role, and a net that mixes kinds is an error (track nets join only `TRACK`/`APPLIANCE`/`POLICY` pins; `DEVICE` and `PANEL` pins join only `IODRIVER` pins, plus `PANEL` Column pins to `COLUMN`). Wiring between plants is deferred; `NextCP` names stay.
- D13. Field units. With no `FIELD_UNIT` symbol, a plant has one field unit, named after the interlocking, hosting every house and driver (the common case). One field unit per MAIN HOUSE is the other form: a `FIELD_UNIT` symbol on the trackplan, its pin wired to that house, and each driver names its field unit in a `FieldUnit` attribute. The forms are not mixed in one plant; every house belongs to exactly one field unit. A device must be on the field unit that hosts its appliance; a field unit may still consume another unit's indications from the code line (remote track circuits, e.g. Watsonville `1SAT`), which needs no device.

## Consequences

- FieldUnit: `WLQK` in `WireCodec` and the glossary; the stick rule on `WLS`; relock on the crew's return (drive to N, then lock); the local lever rule (R5); the N-lamp blink in the desk's lock logic.
- InterlockingPlant: `Local-Lock`/`-2Lamp` pins to `~{WLQ}`; head symbols to Role `APPLIANCE` and the Kinds above; `Milepost` gains its track pin (owner's symbol design).
- Compiler (#30 step 3): head Kinds into `_PART_KIND` and the `(Role, Kind)` table; milepost anchors and derived positions.
