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

- 2026-11-06: Railroad PR 20 merged `Railroad-Trackplan-Signals` into `Railroad-Trackplan` and `Railroad-Field-Signals` into
  `Railroad-Field` (four libraries, 117 symbols); the headings below name the libraries as they were when written.

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
- Train order boards (Time Table and Train Order territory, never CTC). Ruled 2026-11-05, reworked 2026-11-08 from the
  owner's worked example in Gilroy Interchange (the 2026-11-05 form, faces as named units of one field device, is in
  commit e48eec0 and was not drawn): the shape is the signal mast's.
  1. Trackplan: `Train Order Mast Single` and `Train Order Mast Double`, Appliance `train_order`, Style `single` or
     `double`, Name and Station, no pins. A single board faces the way its glyph is turned (unturned LEFT, a half
     turn RIGHT, mirror swaps), `relations.facing`; the importer reads the same facing from every signal mast and
     warns when it disagrees with the Name letter (`mast.facing`).
  2. Field mast: `Device-TrainOrder-Mast-Single` and `-Double`, Appliance `train_order_mast`, Name matching the
     board; one passive pin per face, `Pin.X: indication`; a double mast's pins are named for the directions, E and
     W or N and S; a single mast's one pin carries no direction. A face exists when something is wired to its pin.
  3. Head: a `Device-Head-*` whose IND is on a face pin's net is that face's head, as a head on a signal mast; a
     three-position head (UQ, or an LQ three-position symbol still to draw) for a face that shows STOP, APPROACH and
     CLEAR. No Head letter: the face names it.
  4. Lever: `Local-TrainOrder`, Appliance `lever`, Style `train_order` (the `Local-` family: Appliance says what the
     device is, Style what it works). Its IND is on the face pin's net beside the head, so the wire says which face
     it serves and no name is typed twice; outputs STOP and SLOW, asserted low, to any driver. No CALLON: CALLON is
     the block signal's indication, used with the board to bring a train stopped at the block boundary up to the
     station; not a train order control (owner, 2026-11-08).
  5. Words: nothing asserted CLEAR, SLOW APPROACH, STOP STOP, in reference data (`reference.TRAIN_ORDER_INPUTS`,
     dated), never in code; the run-time precedence (STOP over SLOW) is FieldUnit's (its issue #44).
  6. Findings: board with no field mast, or a mast with no face wired, `train_order.device` missing; face with no
     lever `train_order.lever` missing; lever on no face `lever.face` missing, on two faces `lever.faces` error; a
     double board's face pin naming no direction, a single board turned a quarter or with two faces wired, or a face
     two levers serve, `train_order.face` error.
  The fascia control is local, no code line. A nameless head or lever serves under its mast's name, so a JMRI object
  wired to one is keyed by the mast (`SIGNALMAST.Gilroy`, `SENSOR.Gilroy`); per-face or per-pin JMRI names are the
  JMRI naming item, not this one.
- AUXILIARY and Contact: the `MC` pin was copied from MaintainerCall by mistake; it becomes an optional `TRACK` pin.
  Wired to a track net, the importer writes the circuit as the appliance's relation and the derivation checks it is
  a circuit of the same interlocking; wired elsewhere is an import error; unwired, Milepost and CP Name place it.
  A switch heater attaches to the switch's N pin like track. NFL/SFL at Luchessa and Watsonville are fleeting
  (traffic flow direction) lamps, not fouling. Grade crossings are an appliance of their own: issue #74.
- Driver-CMRInet-Node: the `Transport` field is deleted (owner); the `Transport` pin's wire is the binding.

## Rules as features (structure settled 2026-11-05)

Derivation rules are Gherkin features (ADR 0012). A registry code's `feature` is null until a scenario names it.
Two roots (owner, 2026-11-05; the check is "what would Studio do", whose native file is the model):

- **Model features**, `schemas/layout-model/rules/features/`: start from facts of the file, end at `derived` or a rule
  check. Every writer passes them. Inside: `logical/` (what the facts mean on the railroad: trackplan, office, code
  line, policy and demand tables; rules answer "is this correct", cite rulebook and history) and `physical/` (how a
  logical fact is realised: field devices, encoders, drivers, transports; rules answer "are these equivalent", one
  scenario outline per logical fact with an Examples row per realisation).
- **Import features**, `tools/layout_compiler/features/`: start from a drawing (symbols, pins, nets), end at the facts
  written or an import diagnostic. The importer's "a wire means" rules live here, with the import registry, and
  retire with the importer. Nothing KiCad is in the model root.

Inside each: seam then Role, or Role plus Appliance where Role is too wide. A scenario is one route through the
logic, named in the user's words; its diagnostic code is a tag; the registry key is `file#scenario`, relative to the
registry's own root. A ruling with both parts is two files of the same name. `@pending` marks a rule stated before
its implementation; its code is `proposed`. The field device is the one place both halves of the model root meet.
Symbols a feature touches are computed from library fields by the manual generator, never written in the feature.
First features: the four rulings above and the take 3 head positions (`tests/test_rule_features.py` is the gate).

## Documentation decisions (owner, 2026-11-04/05)

- The symbols manual is generated HTML, not markdown (owner: markdown "isn't suitable for user documentation"). Facts
  come from the six libraries through the contact-sheet tooling: Description, fields and pins per symbol, who sets
  each field (an empty library value = the user fills it; a literal or `${...}` = fixed), per-unit SVGs from
  kicad-cli. Only a usage paragraph per group is hand-written. Each pin or field links to the rule feature that binds
  it; the symbols a feature touches are computed from library fields. The hand-written text is one file, Railroad
  `symbols/manual.html`: HTML fragments between `<!-- GROUP: title | selector -->` and `<!-- END GROUP -->` markers
  (owner, 2026-11-05: markdown is too weak, a file per fragment is hard to edit). The selector over library fields
  says which symbols a group holds. The page is `symbols/production/manual/index.html` and repeats the markers, so
  prose edited in the page is copied back with `symbol_manual.py --harvest`. `symbols/README.symbols.md` was the
  interim draft, retired when the page landed.
- Examples in use are root sheets in the KiCad project `Railroad/Tutorial` (owner, 2026-11-06): a story that starts
  simple and builds to more complex arrangements, each sheet a building block for functional tests, documentation
  and tutorials. Every sheet is a top-level sheet and a complete small system (Railroad, OfficeUnit, processors,
  transport, encoding, trackplan, field and office wiring), so no sheet depends on another; a tutorial that needs a
  hierarchy has its own. Sheet 1 teaches with text beside the drawing (a controlled siding); sheet 2 is the same
  drawing without the text, the template for the next ones. Sheet-local nets use hierarchical labels, which are
  easy to see; the ERC complaint about a hierarchical label on a root sheet is excluded. The owner draws the sheets
  in KiCad. This replaces the `Railroad/Examples` project and its generator `tools/examples/build_examples.py`
  (one root sheet of shared scaffolding, 13 planned pages that did not compile alone), removed 2026-11-06; the old
  text and the page order are in commit 84f508b. The talk outline is a quarry of ideas; its history figures are slides.

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

## JMRI-style MQTT masts (owner, 2026-11-05)

Settled in conversation; nothing below is implemented in the importer yet (it belongs with the model step, #80).

- **One way to draw a mast.** A field mast device's position pins A, B, C are passive. What is wired to a pin says
  what it takes: a head takes that position's head word; a whole-mast consumer (`Driver-JMRI-SignalMast`) takes the
  mast's indication, and the pins on its net are the positions it stands in for. Mixed wiring (A and B to a JMRI mast,
  C to a local head) is allowed. Lint requires passive (d26bf09).
- **One device per consumer.** Position pins tied together are one net, so a second consumer that needs the positions
  apart (anonymous heads) gets its own mast device with the same Name. Gilroy Interchange is drawn this way: per
  signal, one mast device to the JMRI driver and one to H2 heads, `Encoder-Pixel-RGB` and the D2 pixel chain
  (addresses 1 to 6).
- **We publish; JMRI does not run.** The field unit stands where JMRI would and the appliance subscribes, so JMRI's
  system name and mast model do not enter the model. The mast model is the appliance's own business.
- **The seam** (JMRI `java/src/jmri/jmrix/mqtt/MqttSignalMast.java`, opened): topic = prefix (JMRI default
  `track/signalmast/`) + the mast's ordinal or name, which is the driver's `Address`; payload =
  `<"aspect name">; Lit; Unheld`. Lit and Held are constants for now.
- **Translation table**, keyed (signal system, indication, mast Kind) -> JMRI "aspect name". Kind is in the key
  because SP's names fold the plate in (STOP is "Home Signal Red" on an absolute or controlled mast, "Stop and
  Proceed" on a permissive one); our indication vocabulary does not change. A word with no row is not presentable in
  that system (a rule check). The tables are ours and editable; JMRI's `xml/signals/<system>/aspects.xml` is a source
  for names, not an authority. JMRI's appearance files and `aspectMappings` are not adopted (they are our head tables
  and our derivation, multiplied out); the appearance files may serve later as a check on our head tables.
- **First two maps**, to exercise the railroad and era tags:
  - `basic`: CLEAR Clear; APPROACH Approach; STOP Stop; DIVERGING_CLEAR Diverging Clear; DIVERGING_APPROACH Diverging
    Approach; plus our own row RESTRICTING Restricting (not in JMRI's `basic`).
  - `SPTCO-1969`: CLEAR Block Signal Green; APPROACH Approach Signal Yellow; RESTRICTING Restricting; STOP Home Signal
    Red (CONTROLLED, ABSOLUTE) or Stop and Proceed (PERMISSIVE); DIVERGING_CLEAR Block Signal Green for Diverging
    Route; APPROACH_DIVERGING Block Signal Yellow over Green; APPROACH_MEDIUM Approach Medium - Flashing Yellow;
    DIVERGING_APPROACH Home Signal Yellow for Diverging Route; DIVERGING_RESTRICTING Home Signal Red over Lunar (red
    over yellow in later eras, when lunar was dropped: an edit to the row). ADVANCE_APPROACH and the speed-signalling
    words have no row; the owner expects them absent on western roads.
- **Where the signal system is stated.** Eras never end, they only start (owner): SP ran old and new signals side by
  side through each transition. So the signal system is a fact about each installation, never a mode of the layout.
  `Encoding-JMRI` names the usual one; a `Driver-JMRI-SignalMast` states its own when its appliance is of another
  era. (My reading of the owner's remark; the field names are not chosen yet.)
- **Follow-on:** FieldUnit `src/drivers/MqttApplianceBus.h` `aspectName()` hard-codes names; it should take them from
  this table. Four SPCoast drawing gates fail on the take 3 sheets until the model step lands.

## Rulings 2026-11-09 (derails, local control, heads on one pin)

Owner, in conversation while reviewing the Sargent edge cases. Supersedes the 2026-11-05 line "A derail keeps
STOP/RESTRICTING". The Subdivision code change is #105 on map #94; the FieldUnit side is plocher/FieldUnit#45.

1. **Heads on one mast pin.** A mast demands a set of indications, I[mast]. Each head wired to a mast pin presents a
   subset, I[head], from the head table keyed by its Style; a demanded word outside that subset is the table's
   business (its indication filter), never a model finding. Any number of heads may share a pin, and the model does
   not tell a head on the mast from a fascia repeater. Two heads on one pin with I[H1] ≠ I[H2] is an informational
   finding naming the pin, both heads and the difference: a normal configuration (a head upgrade with both in
   service; a cheap fascia repeater of a mast hidden from the aisle). No error, no warning, no head-count rule.
   Semaphore Styles name the arm positions: `LQ2`, `LQ3`, `UQ3`. Recorded on #80.
2. **"Powered" is ADR 0013 §4's seam word**, not "has a motor": a powered switch or derail is an interlocking
   appliance whose position the field unit knows and may move. A CP Name makes nothing powered (ADR 0013 §4);
   `grammar.is_powered` still reads one on an independent derail and loses that reading.
3. **A derail is a switch with the word `derail` in its Style**, ports C and R, and the switch vocabulary names every
   regime; dependency is the one extra and comes from the name (gang id names a switch, ADR 0003 D8):

   | Trackplan symbol | Style | Control source stated by |
   | --- | --- | --- |
   | Switch_Powered (+ Diag, Small, NO_TC) | `powered` | a desk lever on its column |
   | Switch_Dual | `dual` | the desk lever; the crew releases and throws with Local-Lock + Local-Switch |
   | Switch_Local (new) | `local` (new word) | a Local-Switch alone; no desk lever, no lock |
   | Switch_Lock | `lock` | the desk lock lever; in the field a Local-Lock asking the release and a Local-Switch throwing the points, the switch device reporting NWK/RWK, and its TC (owner, 2026-11-09: "a fascia pair of lock/switch lever/lamps and a remote switch with point feedback and a TC"; Christopher 813 and 817 are the reference) |
   | Switch_Manual_Sensed | `manual_sensed` | hand; a contact reports the position |
   | Switch_Manual | `manual` | hand; nothing reported |
   | Derail | `derail,powered` | its switch's lever when the gang id names a switch; else a desk lever |
   | Derail Dual (new) | `derail,dual` | as Switch_Dual |
   | Derail Local (new) | `derail,local` | as Switch_Local |
   | Derail Manual Sensed (new) | `derail,manual_sensed` | as Switch_Manual_Sensed |
   | Derail Manual | `derail,manual` | as Switch_Manual |

   `dual` is the glossary's dual-control switch: hand operation only under a release, never both sources at once.
   `local` differs from `manual_sensed` in having a machine: the field unit drives it from the local lever
   (NWS/RWS out) and reads NWK/RWK back; a sensed manual one it can only read. A dependent derail takes its switch's
   regime whatever its own word; a dependent derail drawn `local` or `manual` is a finding. A powered appliance with
   no lever of either kind named for it is `missing` (no control source), and so is a `lock` one with no Local-Switch;
   a `local` one with a desk lever, or a `dual` or `lock` one with no Local-Lock, is a finding.
4. **Lever devices are unchanged.** A lever's Style names its token set, the same word on the desk and in the field:
   `switch` (NWS/RWS out, NWK/RWK in: PanelSwitch, Local-Switch, Local-Derail), `lock` (WLQ out, WLK/WLQK in:
   PanelLock, Local-Lock), `train_order`. Local-Switch with Local-Lock is the crew's release-and-throw pair of a
   dual-control switch; alone it is the control of a `local` one. The appliance a lever serves comes from its Name;
   a derail lever is a `switch` lever named for the derail. No `derail` lever word.
5. **A derail owns no OS circuit.** The OS circuit (`<switch>T1`, `TC` overriding) is a switch idea: where a train is
   "at", and detector locking of the points. A derail lies in the circuit of the net its ports are on, as Sensor,
   Lamp and Actuator do (`relations.circuit` from the track net on the pin, PR #100); a Track Circuit marker on that
   track names it when detection is wanted. `Derail TC` is removed from the library, and the `TC` and `Indication`
   fields leave the derail symbols. An independent derail still reports its position to the field unit: it figures
   in routes and other field logic whether or not the dispatcher controls it.
6. **IndicationCeiling on derails is empty** like every other switch; the derail rule (NORMAL is derailing) lives in
   reference data for the route heuristics (#81).

Subdivision code (one ticket): `grammar.is_powered` (drop the CP Name reading; `local` joins the powered words;
`derail` matched by word, as the two `== "derail"` port readings in `derive.py` and `trackplan.py` must be), the
lever function in `grammar.py` ("a derail has no lever" becomes "a derail has whatever lever device is named for
it"), no OS default and no `TC` reading for a derail, the lever-consistency findings above, and one scenario per
table row. FieldUnit: the local control source (a lever that is not on the code line asserts NWS/RWS), the release
flow of `dual` (ADR 0006, proposed) applied to a derail, `manual_sensed` as a read-only position, derail dependence
taken from the model (FieldUnit #29), and the glossary's powered-switch and derail entries.

## Queued: encoder Value cleanup (owner, 2026-11-09)

An encoder is anonymous (no `Name`; keyed by `Kind` and the net on its `APP` pin), so nothing reads its `Value`.
The libraries now carry `Value` empty and `Kind` literal on every encoder, and every placed encoder has a literal
`Kind` (checked 2026-11-09 after the Sargent hand edits). Fifty placements still carry text in `Value`: `3MUX2A` on
40 (all six 3MUX2A sheets), `PIXEL` on 7 (GilroyInterchange, Sargent), `RYG` on 3 (GilroyCalTrain). Blank them in
one scripted, lock-gated pass with a field diff before the commit (the field-reset incidents of 2026-10-17/18),
not through Update Symbols, which the owner does not want touching `Value`. Railroad repo edit, separate commit.

## Rulings 2026-11-10: regime markers (owner; ADR 0013 §7.1, decision 3; ADR 0009 §3.12)

- Every piece of track is in the model with the regime that governs it; CTC is one regime among several. "Dark" is
  the office's view, never a kind of track (README "Aspiration", PR 111).
- Regimes are `GCOR Rule NN` POLICY symbols, Kind `GCOR_RULE_N` shared by the BEGIN and END glyphs, one passive pin
  `To`, no Name. The GCOR prefix scopes the vocabulary; Studio will present the era's set. GCOR has no Rule 261: the
  nine `Rule261` signs are removed, signalled-both-ways is read from the masts. `Rule251` -> 9.14 (Direction kept),
  `Rule93` -> 6.13, `Rule105` -> 6.28, `IRJ-END_CTC` -> plain `IRJ` plus a marker each side. Railroad `0ddd395`.
- Extent is derived (joint-bounded pieces; marker, interlocking membership, inheritance; conflicts are errors); sign
  faces are rendered from the two adjacent regimes. Sources opened: GCOR 8th edition (10.1, 14, 16.1, 6.13, 6.14,
  6.28, 9.14, glossary "Interlocking Limits"); the 1980 Coast Line track chart
  (`docs/review/coast-line-track-chart-1980-notes.md`).
- Compiler pass (ticket on map #94): `trackplan.py` ENDS and `derive.py` read the new Kinds; `policy_sign.feature`
  loses the 261 scenario; the old symbols and Kinds are deleted in the same change, no bridge.
- Queued after it: the JMRI binding collision at Gilroy (two anonymous Local-TrainOrder levers and two UQ3 heads on one
  appliance route to one JMRI name; distinguishing facts are face E/W and pin STOP/SLOW; with #85/#99).
