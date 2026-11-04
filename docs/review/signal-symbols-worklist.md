# Signal symbols: the settled shape, take 3 (worklist, 2026-11-04)

Working direction agreed 2026-11-03/04, to be recorded in an ADR once the POC compiles. Supersedes the take 2 version
of this file (Railroad PR #17 pass 2). Railroad `5eda8ab` regenerates `Railroad-Field-Signals` to this shape.

## The chain and its seams

```
trackplan Mast ──indication──▶ field Mast device ──pin A/B/C (indication)──▶ anonymous Head ──head word──▶ Encoder ──pins / pixels──▶ Driver
```

| seam | between | vocabulary | owner of the list |
| --- | --- | --- | --- |
| indication | trackplan mast → field mast device → head, per position pin | Stop, Approach, Clear, … | the indication list (`reference.py` today, FieldUnit `enum Indication`) |
| head word | head → encoder | a subset of the indication list, plus DARK | the same list; a head's model table says which |
| device interface | encoder → driver | binary, position, a pixel index | the pin-kind vocabulary |

No appearance vocabulary (no colours, no blade positions) crosses a seam. Colours and positions appear only on the
right-hand side of a head model's table, which is the encoder's instruction. Never "aspect" for an indication, never
a colour for a word.

## Functions, one fact each

| function | where | states | derived from it |
| --- | --- | --- | --- |
| demand | derived: the routes the mast governs and the block beyond (Stop always; every other word earned by a governed route's ceiling or block spacing; profile = Railroad/Era/Rulebook, ADR 0013 R11; lands with #62) | what this signal must be able to say | match against the heads |
| demand exception | trackplan mast, `Indications` field, EMPTY by rule | filled: ONLY an explicit comma-separated list of the profile's indication words, replacing the derived set; the difference is reported. No named subsets, no classes | |
| policy table | reference data, per rulebook | mast indication → one head word per head position | the aspect a mast shows |
| field mast device | field sheet, Name = the trackplan mast's Name (246AB), pins A/B/C | the binding: which heads this mast has and in which position | head position = the pin the head's IND is wired to |
| head | field device, Style = manufacturer model, anonymous | which model sits at that position | `presents` = the keys of its model table |
| head model table | reference data, per model | head word → the output the encoder makes (R, Y flashing, horizontal, none) | absence = cannot present |
| encoder | field symbol between head and driver | its pins / pixel addresses | reads the table of the head it serves |
| driver | HardwareIO, unchanged | the chip or chain that owns the pins | |
| match | derived | demand ⊆ what the heads present through the policy table | missing (no devices yet) / error (cannot present) |

A head alone shows no aspect (Glossary). A head has no identity of its own: it is a position on a mast, keyed by the
mast's Name plus the pin it is wired to (A, B, C top down: 830SAB, 784EAB, Glossary head1..head3). Nothing is written
per instance except the mast's Name, an encoder's Address and settings.

## Symbols

### Railroad-Trackplan-Signals (owner-maintained; the generator does not touch it)

`Signal Mast Single`, `Signal Mast Single ABSOLUTE`, `Signal Mast Single PERMISSIVE`, `Signal Mast Double`,
`Signal Mast Triple`, `Signal Mast Dwarf`, `Stop`; Role APPLIANCE, Appliance mast, Name=${Value}, Kind
CONTROLLED/ABSOLUTE/PERMISSIVE, `Indications=` empty by rule (the exception above), one pin SIGNAL. Head glyphs are
picture; the trackplan mast has no head devices.

### Railroad-Field-Signals: field mast devices (generated)

Role DEVICE, Appliance mast, Reference DevMast, Name=${Value}; one output pin per head position, named A, B, C top
down and numbered 1..3, `Pin.<letter>=indication`; no Style, no Kind, no Indications (the pin set is the head count).
Picture: the Field library's box with `MAST ${VALUE}`.

| symbol | pins |
| --- | --- |
| Device-Mast-Single | A |
| Device-Mast-Double | A, B |
| Device-Mast-Triple | A, B, C |

### Railroad-Field-Signals: heads (generated, anonymous)

Role DEVICE, Appliance head, Reference Cast, Style the model, **no Name property** (Value stays as KiCad's required
empty property; the box shows the Style alone); pins `IND` (input, Pin.IND=indication) and `APP` (output,
Pin.APP=indication); no other pins, no settings, no Head field.

| symbol | Style | Description |
| --- | --- | --- |
| Device-Head-TypeD | TypeD | GRS Type D colour-light head. Presents what its model table lists; the encoder it is wired to makes the lamps. |
| Device-Head-SA | SA | GRS SA searchlight head. |
| Device-Head-H2 | H2 | US&S H-2 searchlight head. |
| Device-Head-Semaphore-UQ | UQ | Upper-quadrant semaphore head, three positions. |
| Device-Head-Semaphore-LQ | LQ | Lower-quadrant semaphore head, two positions. |

### Railroad-Field-Signals: encoders (generated, unchanged since take 2)

Role ENCODER, Kind per symbol, Name=${Value}, no Appliance; exactly one input pin `APP` (Pin.APP=indication);
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

Retired: Railroad-Field:Mast and Device-Head-CL-RGB, -CL-Pixel, -CPL, -CPL-Encoded, -CPL-Pixel (old library, after
the sheets migrate); the first-cut Device-Head-TypeD-Encoded, -TypeD-Pixel, -SA-RGB, -SA-Pixel, -H2-RGB, -H2-Pixel;
the trackplan head symbols.

## Contract changes (Subdivision)

- No new pin kind: the head → encoder seam carries an indication word, so `APP` is kind indication, direction output.
- Role `ENCODER`: no Appliance; Kind required; exactly one input pin of kind indication; `Pin.*` per pin;
  `Address.<pin or colour>` and `Code` are contract fields; settings snake.
- Head device (take 2): exactly one input of kind indication and exactly one output of kind indication, nothing else.
- Anonymous head (take 3, `lint_symbol_fields.py`): a DEVICE/head with an indication output carries no `Name`
  (error: "a head has no name; it is keyed by the mast pin it is wired to"). Old-shape Railroad-Field heads untouched.
- Field mast (take 3): DEVICE/mast with lettered pins: all outputs of kind indication, named A, B, C in number
  order from A with no gap, one to three; `Pin.<letter>=indication`; no Style, Kind or Indications (error: the pin
  set states the head count). Railroad-Field:Mast (one IND output) has no lettered pin and keeps the plain DEVICE rules.
- "Name=${Value} on every keyed symbol" (the overview's G2, `identity_field`) exempts exactly the anonymous head.
- ADR 0009's Role table gains ENCODER; the Glossary's "encoding" widens to the verb (owner, FieldUnit repo).

## Reference data (behind `reference.py` functions until files exist)

- `head_model(style)` → the model table, head word → output. Seed: TypeD {STOP R, APPROACH Y, ADVANCE_APPROACH Y
  flashing, CLEAR G, DARK none}; SA and H2 the same table; UQ {STOP horizontal, APPROACH diagonal, CLEAR vertical};
  LQ {STOP horizontal, CLEAR dropped}. Lunar and other variants are new rows when a drawing needs them.
- `policy(rulebook)` → mast indication → head word per position (seeded with #62). No named subsets of the
  indication list: the profile's words, the derived demand, and an explicit `Indications` list are the only sets.
- `code(name)` → the two-bit table; `palette()` → colour mixes for Encoder-RGB.

## Model step (after the symbols)

- Head position from the pin on the `head.mast` relation: `seams.py:164` (`Device.mast`) already reads the head's
  IND wire to its mast; the pin letter it lands on is the position. The field mast device binds to the trackplan
  mast by Name.
- Demand derivation lands with #62 (routes, blocks, ceilings): Stop always, the rest earned; an explicit
  `Indications` list replaces it with the difference reported.
- Match: demand ⊆ presents, through the policy table per position; diagnostics missing / error.
- `derived.presents` per head position; FieldUnit's `Aspect` composites become derived (a FieldUnit defect against
  the shared list, by the order of authority); schema additive change; the ADR line moving "head casts with Head
  letter" to the field sheet becomes "head position = mast pin".

## Migration (SPCoast sheets, later)

Today: 47 head devices placed (35 CPL-Encoded, 6 CL-Pixel, 3 CPL, 2 CL-RGB, 1 Semaphore-UQ) and 38
`Railroad-Field:Mast` placements across 7 sheets (Christopher 4, Corporal 4, GilroyCalTrain 5, GilroyInterchange 8,
Luchessa 5, Sargent 3, Watsonville 9). Each Mast becomes a Device-Mast-* sized to its heads; each head becomes an
anonymous head device on a lettered pin plus one encoder; the pixel casts' `Address` moves to the encoder; the head
Names (784A) are dropped. Scripted, lock-gated, with a compile diff.

## Rulings 2026-11-04

- Heads are anonymous: a head is a position on its mast, keyed by the mast's Name plus the pin (A, B, C). The
  2026-10-16 ruling "identity never from a binding" holds for named devices only.
- A trackplan mast's `Indications` is empty by rule; the demand is derived. Filled, it is only an explicit list of
  the profile's words replacing the derived set, with the difference reported. There are no named subsets or classes.
- Kind (CONTROLLED/ABSOLUTE/PERMISSIVE) changes no demand word: a permissive mast demands STOP like any other; the
  number plate changes the crew's rule after stopping.
- Only Stop is universal; every other word is earned by a governed route's ceiling or block spacing.
