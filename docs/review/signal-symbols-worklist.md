# Signal symbols: the settled shape, take 3 (worklist, 2026-11-04)

Working direction agreed 2026-11-03/04, to be recorded in an ADR once the POC compiles. Supersedes the take 2 version
of this file (Railroad PR #17 pass 2). Both Signals libraries are hand-maintained by the owner in KiCad; the generator
`edits/make_signal_libraries.py` is retired at Railroad `b45950a`. The library is the truth; where the lint
disagrees, the lint is fixed.

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
| head model table | reference data, per model | head word → one column per encoder Kind (lamps R/Y/G, blade angle, the lamp behind a semaphore roundel: DARK = lamp out, blade unchanged) | absence = cannot present |
| encoder | field symbol between head and driver, anonymous (keyed by the head it serves) | Kind, its pins / pixel addresses | reads its Kind's column of the served head's table; one APP net may feed two encoders (Servo for the blade, Lamp for the lamp) |
| driver | HardwareIO, unchanged | the chip or chain that owns the pins | |
| match | derived | demand ⊆ what the heads present through the policy table | missing (no devices yet) / error (cannot present) |

A head alone shows no aspect (Glossary). A head has no identity of its own: it is a position on a mast, keyed by the
mast's Name plus the pin it is wired to (A, B, C top down: 830SAB, 784EAB, Glossary head1..head3). Nothing is written
per instance except the mast's Name, an encoder's Address and settings. Value is informative and never read.

## Symbols

### Railroad-Trackplan-Signals (hand-maintained)

`Signal Mast Single`, `Signal Mast Single ABSOLUTE`, `Signal Mast Single PERMISSIVE`, `Signal Mast Double`,
`Signal Mast Triple`, `Signal Mast Dwarf`, `Stop`; Role APPLIANCE, Appliance mast, Name=${Value}, Kind
CONTROLLED/ABSOLUTE/PERMISSIVE, `Indications=` empty by rule (the exception above), one pin SIGNAL. Head glyphs are
picture; the trackplan mast has no head devices.

### Railroad-Field-Signals: field mast devices (hand-maintained)

Role DEVICE, Appliance mast, Reference DevMast, Name=${Value}; one output pin per head position, named A, B, C top
down and numbered 1..3, `Pin.<letter>=indication`; no Style, no Kind, no Indications (the pin set is the head count).
Picture: the Field library's box with `MAST ${VALUE}`.

| symbol | pins |
| --- | --- |
| Device-Mast-Single | A |
| Device-Mast-Double | A, B |
| Device-Mast-Triple | A, B, C |

### Railroad-Field-Signals: heads (hand-maintained, anonymous)

Role DEVICE, Appliance head, Reference `Head`, Value `${Style}` (informative, never read), Style the model, **no Name
property**; pins `IND` (input, Pin.IND=indication) and `APP` (output, Pin.APP=indication); no other pins, no
settings, no Head field.

| symbol | Style |
| --- | --- |
| Device-Head-TypeD | TypeD |
| Device-Head-SA | SA |
| Device-Head-H2 | H2 |
| Device-Head-Semaphore-UQ | UQ |
| Device-Head-Semaphore-LQ | LQ |

### Railroad-Field-Signals: encoders (hand-maintained, anonymous)

Role ENCODER, Kind per symbol (any word: a reference-data key), **no Name** (keyed by the head it serves), Value
informative (`${Kind}`, or a literal such as PIXEL / PIXELS; never read), no Appliance; exactly one input pin `APP`
(Pin.APP=indication); every hardware-side function pin is an **input** of kind binary or position, driven by a
driver's output pin (as Device-Lamp and the old CPL-Encoded S0/S1 were); `Pin.*` per pin; `CHAIN` a passive
membership pin without `Pin.*`; `Address` / `Address.<colour>` contract fields; no `Code` field; settings
lower_snake_case. An encoder states only its hardware side; the mapping head word → output is its Kind's column of
the served head's model table, read through the wire.

| symbol | Kind | hardware pins (inputs) | fields |
| --- | --- | --- | --- |
| Encoder-RYG | RYG | ~{R} ~{Y} ~{G} binary | |
| Encoder-RGB | RGB | ~{R} ~{G} ~{B} binary | |
| Encoder-3MUX2A | 3MUX2A | S0 S1 binary | (truth table G=00, Y=01, R=10, DARK=11 is reference data keyed by Kind; owner's decoder board, 2026-11-04) |
| Encoder-Lamp | LAMP | ~{LAMP} binary | |
| Encoder-Pixel-RYG | PIXEL_RYG | CHAIN | Address.R= Address.Y= Address.G= |
| Encoder-Pixel-RGB | PIXEL_RGB | CHAIN | Address= |
| Encoder-Servo | SERVO | ARM position | stop_deg= approach_deg= clear_deg= |

Retired: Railroad-Field:Mast and Device-Head-CL-RGB, -CL-Pixel, -CPL, -CPL-Encoded, -CPL-Pixel (old library, after
the sheets migrate); the first-cut Device-Head-TypeD-Encoded, -TypeD-Pixel, -SA-RGB, -SA-Pixel, -H2-RGB, -H2-Pixel;
the trackplan head symbols.

## Contract changes (Subdivision)

- No new pin kind: the head → encoder seam carries an indication word, so `APP` is kind indication, direction output.
- Role `ENCODER`: no Appliance; Kind required; no `Name` (error: "an encoder is keyed by the head it serves; it has no
  name"); exactly one input pin of kind indication; every other function pin an input of kind binary or position
  (an output is an error: "encoder hardware pins are inputs, driven by the driver"); `Pin.*` per pin; `Address` and
  `Address.<colour>` contract fields; `Code` gone (a plain non-snake setting now, so flagged); settings snake.
- Head device (take 2): exactly one input of kind indication and exactly one output of kind indication, nothing else.
- Anonymous head (take 3, `lint_symbol_fields.py`): a DEVICE/head with an indication output carries no `Name`
  (error: "a head has no name; it is keyed by the mast pin it is wired to"). Old-shape Railroad-Field heads untouched.
- Field mast (take 3): DEVICE/mast with lettered pins: all outputs of kind indication, named A, B, C in number
  order from A with no gap, one to three; `Pin.<letter>=indication`; no Style, Kind or Indications (error: the pin
  set states the head count). Railroad-Field:Mast (one IND output) has no lettered pin and keeps the plain DEVICE rules.
- "Name=${Value} on every keyed symbol" (the overview's G2, `identity_field`) exempts the anonymous head and Role
  ENCODER, nothing else.
- ADR 0009's Role table gains ENCODER; the Glossary's "encoding" widens to the verb (owner, FieldUnit repo).

## Reference data (behind `reference.py` functions until files exist)

- `head_model(style)` → the model table, head word → one column per encoder Kind. Seed: TypeD {STOP R, APPROACH Y,
  ADVANCE_APPROACH Y flashing, CLEAR G, DARK none}; SA and H2 the same table; UQ {STOP horizontal, APPROACH diagonal,
  CLEAR vertical} plus a lamp column {every word lamp on, DARK lamp out}; LQ {STOP horizontal, CLEAR dropped} plus
  the same lamp column. Lunar and other variants are new rows when a drawing needs them.
- `policy(rulebook)` → mast indication → head word per position (seeded with #62). No named subsets of the
  indication list: the profile's words, the derived demand, and an explicit `Indications` list are the only sets.
- `encoder_table(kind)` → keyed by Kind: 3MUX2A {G 00, Y 01, R 10, DARK 11} (owner's decoder board, 2026-11-04);
  `palette()` → colour mixes for RGB.

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
- Encoders are anonymous: keyed by the head they serve.
- Value is informative and never read (heads `${Style}`, encoders `${Kind}` or a literal).
- A device pin meeting a driver pin is an input: encoder hardware pins are inputs, driven by the driver's output.
- The lamp behind a semaphore roundel is a head output column (DARK = lamp out, blade unchanged): the UQ and LQ model
  tables gain a lamp column, and a head's one APP net may feed two encoders (Servo for the blade, Lamp for the
  lamp), each reading only its Kind's column.

## Rulings 2026-11-05 (manual review, items 1 to 4)

- IndicationCeiling: on every switch, empty by default; the route derivation's heuristics set each route's ceiling.
  Filled, it is an override, two indication words NORMAL/REVERSE ("a route through this appliance in this position
  can never show better than X"). The hand-switch library default RESTRICTING/RESTRICTING is removed (owner's edit);
  its rule moves to reference data for the heuristics. A derail keeps STOP/RESTRICTING: NORMAL is derailing.
- Train order boards (Time Table and Train Order territory, never CTC): one trackplan `Train Order Mast` with Station
  and no head pin; a field `Device-TrainOrder`, one unit per face (N/W, S/E), inputs STOP, SLOW, CALLON from any
  driver, output IND to an anonymous head; nothing asserted = CLEAR, SLOW = APPROACH (orders on the fly), CALLON =
  RESTRICTING, the most restrictive asserted input wins. The fascia control is local, no code line. A one-faced
  board places one unit.
- AUXILIARY and Contact: the `MC` pin was copied from MaintainerCall by mistake; it becomes an optional `TRACK` pin.
  Wired to a track net, the importer writes the circuit as the appliance's relation and the derivation checks it is
  a circuit of the same interlocking; wired elsewhere is an import error; unwired, Milepost and CP Name place it.
  A switch heater attaches to the switch's N pin like track. NFL/SFL at Luchessa and Watsonville are fleeting
  (traffic flow direction) lamps, not fouling. Grade crossings are an appliance of their own: issue #74.
- Driver-CMRInet-Node: the `Transport` field is deleted (owner); the `Transport` pin's wire is the binding.

## Rules as features (structure settled 2026-11-05)

Derivation rules are Gherkin features (ADR 0012), none written yet; every registry code has `feature: None`.
Structure: `logical/` (what the drawing means on the railroad: trackplan, office, code line, policy and demand
tables; rules answer "is this correct", cite rulebook and history) and `physical/` (how a logical fact is realised:
field devices, encoders, drivers, transports; rules answer "are these equivalent", one scenario outline per logical
fact with an Examples row per realisation; the importer's "a wire means" rules live here too). Inside each: seam
(ADR 0009's table) then Role, or Role plus Appliance where Role is too wide. A scenario is one route through the
logic, named in the user's words; its diagnostic code is a tag; the registry key is `file#scenario`. The field
device is the one place both halves meet. Symbols a feature touches are computed from library fields by the manual
generator, never written in the feature. First features: the four rulings above and the take 3 head positions.

## Documentation decisions (owner, 2026-11-04/05)

- The symbols manual is generated HTML, not markdown (owner: markdown "isn't suitable for user documentation"). Facts
  come from the six libraries through the contact-sheet tooling: Description, fields and pins per symbol, who sets
  each field (an empty library value = the user fills it; a literal or `${...}` = fixed), per-unit SVGs from
  kicad-cli. Only a usage paragraph per group is hand-written. Each pin or field links to the rule feature that binds
  it; the symbols a feature touches are computed from library fields. `symbols/README.symbols.md` is the interim draft
  and retires when the page lands. Open: prose as HTML fragments in `symbols/manual/` with output in `production/`
  (default) or one page with marked regions.
- Examples in use are a curated KiCad project `Railroad/Examples` (branch feat/examples-project): one page per
  compiler pattern, bands TRACKPLAN / FIELD / OFFICE, each page its own Interlocking and House, a sidecar `.md` with
  the intent paragraph and the facts the compiler must derive, `TODO:` text wherever the script guessed. Drafted by
  `tools/examples/build_examples.py` from SPCoast patterns, tidied by the owner in KiCad. Consumers: the manual
  (render), functional tests (fresh netlist, compile), talks. Project scaffolding (Railroad, OfficeUnit, processors,
  transports, encodings) sits once on the root sheet, so a page does not compile alone (recorded, not fixed). Order:
  01 track circuit, 02 powered switch, 03 single mast (drafted d92f385), 04 double mast 3MUX2A + siding dwarf,
  05 semaphore servo+lamp, 06 pixel chain, 07 control point complete, 08 desk column, 09 code line three ways,
  10 AUXILIARY/Contact/MaintainerCall, 11 hand switch + derail (empty office band), 12 train order board + station,
  13 ABS/APB + END_CTC + HD line (with #62). The talk outline is a quarry of ideas; its history figures are slides.

## Blocks, direction of traffic and lamps (owner, 2026-11-05; feeds #62 and ADR 0013 pending item 6)

Settled in discussion:
- Library renames (owner): Contact is `Sensor` (pin SENSOR), new `Actuator` (pin ACTUATOR) and `Lamp` (pin LAMP);
  AUXILIARY is gone. The importer keys the optional track pin on Role and Appliance, never a pin name. No migration
  bridges: migrate completely, then change the tools.
- A trackplan `Lamp` is a physical lamp on the layout on the field processor; it never appears on the office board.
  An office `ModelLamp` is the board's lamp. Lamp and Actuator state no `Indication`. A `Sensor` states
  `Indication = ${Name}K` and is the source a board lamp consumes: Sargent's `HBA` Lamp was a local repeater with no
  source and becomes a Sensor with its field device an input.
- One level, not two. A block ends at every controlled or absolute signal joint (ADR 0013 §4): Corporal to Sargent and
  Sargent to Watsonville are two independent station-to-station blocks in a row; nothing real corresponds to their
  union. They are never combined into one indication: each block has its own lamps.
- A block's identity is a name symbol placed on its track. The block exposes its "in use" indication (the virtual
  circuit of §7.2, members derived), its direction of traffic, and its place on the board (X from the track, Y from
  the swimlane the trackplan capture gives).
- Direction of traffic is a property of the whole block including both end interlockings: an agreement, never one
  end's decision. One of the pair or neither is lit; lettered N/S or E/W by railroad and era.
- Either end station may send a block's indications; demand = a consumer exists, then it is in every packet. Each end
  sends the other all of its block circuits. Under AAR MQTT eavesdropping the signal and time indications are already
  in the packet; with H and D wired, direction is explicit.
- The `NFL` and `SFL` Lamp placements (Luchessa, Watsonville) are proxies for this logic and go once blocks expose
  direction. A `Rule261-DoT` marker only delineates one end of a section; it is not the fact and gives no place.

Open for ADR 0013:
1. Closed (owner, 2026-11-05): direction of traffic is a held fact, found in the signal lever position accepted by the
   plant: the seam's outbound port `requested` (§13, "a leaving signal at this end has an active direction request into
   the block"). A block's direction is which end has its lever accepted into it; each end knows its own directly and
   the other's from that end's signal lever indications (already in the packet under eavesdropping) or the wires; one
   or neither, never both. Which lever sets direction is the profile's: western roads with long runs and light traffic
   used the signal lever (SP, `hd_chain`); eastern high-traffic lines often had a separate traffic lever working with
   fleeting (`traffic_line`, `field_fr`). ADR 0013 states this as the definition of the indication. (An earlier reading here looked
   only at `cleared`, which drops behind the train, and wrongly concluded neither end holds direction.)
2. Extent of the approach section of a home signal facing a block. With an intermediate interlocking's signal lined
   through, a train leaving the far end on Clear has accepted an indication that depended on it through the D chain:
   the tumble-down continues to the next control point and the signal and switch must be held (restoring needs time).
   The section must cover every block circuit whose signals its proceed upgraded. Not stated in the ADR.
