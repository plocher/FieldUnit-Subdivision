# Signal symbols: the settled shape (worklist, 2026-11-04)

Working direction agreed 2026-11-03/04, to be recorded in an ADR once the POC compiles. Supersedes the 2026-11-03
version of this file (Railroad PR #17 generated the first cut from it; the owner then edited both libraries by hand).

## The chain and its seams

```
Mast ──indication──▶ Head ──head word──▶ Encoder ──pins / pixels──▶ Driver (owns the hardware)
```

| seam | between | vocabulary | owner of the list |
| --- | --- | --- | --- |
| indication | mast → head | Stop, Approach, Clear, … | the indication list (`reference.py` today, FieldUnit `enum Indication`) |
| head word | head → encoder | a SUBSET of the indication list, plus DARK | the same list; a head's model table says which |
| device interface | encoder → driver | binary, position, a pixel index | the pin-kind vocabulary |

No appearance vocabulary (no colours, no blade positions) crosses a seam. Colours and positions appear only on the
right-hand side of a head model's table, which is the encoder's instruction.

## Functions, one fact each

| function | where | states | derived from it |
| --- | --- | --- | --- |
| demand | trackplan mast, `Indications` field, rulebook words | what this signal must be able to say | match against the heads |
| policy table | reference data, per rulebook | mast indication → one head word per head letter | the aspect a mast shows |
| head | field device, Style = manufacturer model, Name = mast + letter (784A) | which model it is | `presents` = the keys of its model table |
| head model table | reference data, per model | head word → the output the encoder makes (R, Y flashing, horizontal, none) | absence = cannot present |
| encoder | field symbol between head and driver | its pins / pixel addresses | reads the table of the head it serves |
| driver | HardwareIO, unchanged | the chip or chain that owns the pins | |
| match | derived | every word the policy hands head A is a key in A's table; every demanded indication has a policy row the heads can present | missing (no devices yet) / error (cannot present) |

A head alone shows no aspect (Glossary). Nothing is written per instance except Name, Address and settings.

## Symbols

### Railroad-Trackplan-Signals (owner-maintained; the generator no longer touches it)

As edited by the owner 2026-11-04: `Signal Mast Single`, `Signal Mast Single PERMISSIVE`, `Signal Mast Double`,
`Stop`; Role APPLIANCE, Appliance mast, Name=${Value}, Style single|double|stop_sign, Kind per instance
(CONTROLLED default, PERMISSIVE fixed on that symbol, ABSOLUTE on the Stop), `Indications=` (Stop fixed on the Stop
sign), one pin SIGNAL. Head glyphs are picture.

### Railroad-Field-Signals: heads (generated)

Every head device: Role DEVICE, Appliance head, Name=${Value}, Style the model; pins `IND` (input, Pin.IND=indication)
and `APP` (output, Pin.APP=indication); no other pins, no settings, no Head field. The picture is a box with the model
name.

| symbol | Style | Description |
| --- | --- | --- |
| Device-Head-TypeD | TypeD | GRS Type D colour-light head. Presents what its model table lists; the encoder it is wired to makes the lamps. |
| Device-Head-SA | SA | GRS SA searchlight head. |
| Device-Head-H2 | H2 | US&S H-2 searchlight head. |
| Device-Head-Semaphore-UQ | UQ | Upper-quadrant semaphore head, three positions. |
| Device-Head-Semaphore-LQ | LQ | Lower-quadrant semaphore head, two positions. |

### Railroad-Field-Signals: encoders (generated)

Role ENCODER (new), Kind per symbol, Name=${Value}, no Appliance; exactly one input pin `APP` (Pin.APP=indication);
outputs as listed, `Pin.*` per pin; settings lower_snake_case. An encoder states only its hardware side; the mapping
head word → output is the served head's model table, read through the wire.

| symbol | Kind | outputs | fields | Description |
| --- | --- | --- | --- | --- |
| Encoder-RYG | RYG | ~{R} ~{Y} ~{G} binary | | Three lamp lines for a three-lamp head, to any driver's pins. |
| Encoder-RGB | RGB | ~{R} ~{G} ~{B} binary | | Three legs of one tricolour LED (a searchlight); the palette mixes yellow. |
| Encoder-2bit | TWO_BIT | S0 S1 binary | Code= | Two-bit select for the decoder on the mast; Code names the table. 35 placements on SPCoast today. |
| Encoder-Pixel | PIXEL | CHAIN (chain attachment) | Address.R= Address.Y= Address.G= | Three pixels on a chain, one per lamp colour; no span, nothing positional. |
| Encoder-Pixel-RGB | PIXEL_RGB | CHAIN | Address= | One pixel showing the head's colour. |
| Encoder-Servo | SERVO | ARM position | stop_deg= approach_deg= clear_deg= | A blade's angles, moved here from the semaphore head devices. |

Retired: Device-Head-CL-RGB, -CL-Pixel, -CPL, -CPL-Encoded, -CPL-Pixel (old library, after the sheets migrate);
the first-cut Device-Head-TypeD-Encoded, -TypeD-Pixel, -SA-RGB, -SA-Pixel, -H2-RGB, -H2-Pixel; the trackplan head
symbols.

## Contract changes (Subdivision)

- No new pin kind: the head → encoder seam carries an indication word, so `APP` is kind indication, direction output.
- Role `ENCODER`: no Appliance; Kind required; exactly one input pin of kind indication; `Pin.*` per pin;
  `Address.<pin or colour>` is a contract field (names a lamp colour of the served head, not a pin); settings snake.
- Head device: exactly one input of kind indication and exactly one output of kind indication (direction tells them apart), nothing else.
- ADR 0009's Role table gains ENCODER; the Glossary's "encoding" widens to the verb (owner, FieldUnit repo).

## Reference data (behind `reference.py` functions until files exist)

- `head_model(style)` → the model table, head word → output. Seed: TypeD {STOP R, APPROACH Y, ADVANCE_APPROACH Y
  flashing, CLEAR G, DARK none}; SA and H2 the same table; UQ {STOP horizontal, APPROACH diagonal, CLEAR vertical};
  LQ {STOP horizontal, CLEAR dropped}. Lunar and other variants are new rows when a drawing needs them.
- `policy(rulebook)` → mast indication → head word per letter (seeded with #62).
- `code(name)` → the two-bit table; `palette()` → colour mixes for Encoder-RGB.

## Model step (after the symbols)

`Indications` as a mast given; heads derived from the devices bound by Name; `derived.presents` per head;
the match with its diagnostics; FieldUnit's `Aspect` composites become derived (a FieldUnit defect against the
shared list, by the order of authority); schema additive change; the ADR line moving "head casts with Head letter"
to the field sheet.

## Migration (SPCoast sheets, later)

47 head devices placed today: 35 CPL-Encoded, 6 CL-Pixel, 3 CPL, 2 CL-RGB, 1 Semaphore-UQ. Each becomes a head device
plus one encoder; the pixel casts' `Address` moves to the encoder. Scripted, lock-gated, with a compile diff.
