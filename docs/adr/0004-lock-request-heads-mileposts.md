# 0004. The crew's unlock request, head appliances, milepost anchors, and the field I/O review

- Status: proposed. D1–D9 record the owner's rulings of 2026-10-07; only the decisions below are asked.
- Date: 2026-10-07
- Amends: FieldUnit `docs/adr/0003-field-io-symbols.md` (frozen), closing its O1 and O3.
- Order of authority: the relay model and AAR practice (FieldUnit `docs/GLOSSARY.md` §10.6), then FieldUnit `src/`.

## Decisions requested

- R1. An unlock is used up: after the crew relocks, a new unlock needs `WLS` to go to N and back to R (a stick rule, as for a signal knocked down by a train). Default: yes.
- R2. A crew relock with the points reversed: the lock does not re-engage, `WLK` stays up, and the switch reports out of correspondence until the points are normal. Default: yes.
- R3. A crew relock on a switch with a motor drives the points to N first, then relocks. Default: yes.
- R4. The desk shows the knocked-down lock lever by its R lamp going dark while the lever stays at R (as `SGK` drops for a signal); no extra blink. Default: yes.

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
  | Field unit relocks (R2, R3), drops the release (R1) | field to desk | `835WLK` down | yes |
  | Desk lock lever is at R with its R lamp dark: out of correspondence until the dispatcher restores it (R4) | desk | | |

- D4. Desk `PanelLock` (Kind `LOCK_LEVER_2LAMP_2CONTACT`): pins unchanged (N contact `WLS`, R contact `~{WLS}`, R lamp `~{WLK}`, N lamp `WLK`). The N lamp blinking on `WLQK` belongs to the Kind's logic block, not to a pin.
- D5. Fascia `Local-Lock`: the lever or key pin is the request, `~{WLQ}`, replacing `~{WLS}` (the dispatcher's control, drawn there by mistake in the first pass). R lamp `~{WLK}`; the N lamp, where drawn, mirrors the desk (steady locked, blinking while the request waits). A crew "now unlock" lever is a later variant: until then approval means unlocked. Variants are separate symbols with Kinds of one family (`LOCK_*`), as ADR 0003 D7 requires.

### Heads

- D6. Head symbols are appliances: Role `APPLIANCE`, Kind by what the head can display, not how it is built: `Signal Head - CL` `HEAD_COLOR_LIGHT`, `Signal Head - SemaphoreU2` `HEAD_SEMAPHORE_2POS`, `Signal Head - SemaphoreU3` `HEAD_SEMAPHORE_3POS` (was `COMPONENT`/`HEAD`). The mast stays the signal. The generator checks that a head device can render its head's Kind. Head devices are heads, not lamps, because they need indication-to-aspect logic: `Device-Head-1LED-NeoPixel`, `Device-Head-1LED-PWM` sit beside `Device-Lamp-NeoPixel`.

### Mileposts

- D7. `Milepost` is a `TRACK` marker with one pin on a track net; its Value is the milepost. It anchors that net's position; every other position is derived through the track topology, never typed on each symbol. Two anchors give an interlocking its direction (cross-checked against mast letters); across interlockings they order the subdivision for lateral alignment. Open: the symbol's look (keep the track diagram uncluttered), a line name for branch milepost series, and what becomes of the MAIN HOUSE `Milepost` field.

### Field I/O review (amends ADR 0003, applied in InterlockingPlant `e10c0da`)

- D8. Driver symbols have no direction or polarity of their own: pins are bidirectional and take both from what is wired to them; the generator enables a pull-up where an active-low input is attached (no `Pullups` attribute; amends D6). One convention: Kind `I2C-<chip>` (`I2C-MCP23017`, `I2C-PCA9685`, `I2C-MAX7313`), pins `A1..A8`, `B1..B8`, pin N is chip bit N-1 (amends D10). `PanelColumn-MAX7313` is `Driver-I2C-MAX7313`.
- D9. Asserted-low `~{X}` is the norm for field inputs and outputs and for every desk lever and lamp pin; families are checked for exceptions. `Device-Head-3LED-Mux2` `S0`, `S1` are plain (a select code has no asserted state). `PanelAuxiliary` takes Role `PANEL` with the other desk symbols.

## Consequences

- FieldUnit: `WLQK` in `WireCodec` and the glossary; the stick rule on `WLS`; relock on the crew's return with R2/R3; the N-lamp blink in the desk's lock logic.
- InterlockingPlant: `Local-Lock`/`-2Lamp` pins to `~{WLQ}`; head symbols to Role `APPLIANCE` and the Kinds above; `Milepost` gains its track pin (owner's symbol design).
- Compiler (#30 step 3): head Kinds into `_PART_KIND` and the `(Role, Kind)` table; milepost anchors and derived positions.
