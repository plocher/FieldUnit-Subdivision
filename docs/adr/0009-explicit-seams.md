# ADR 0009. Explicit seams: the nets, symbols and pins the compiler reads

Accepted by the owner 2026-10-23 (rev 2, after the owner's review). Rev 1 asked: ratify §3 and the relation table.

Terms (2026-10-26, after ADR 0011): "compiler" in this record means what ADR 0011 splits into the KiCad importer,
which reads the drawing, and the reference derivation, which computes `derived`; "seam reader" is the first piece of
the KiCad importer. The record is not reworded. See FieldUnit `docs/GLOSSARY.md` §2.6.

This records the design settled between 2026-10-21 and 2026-10-23 while the SPCoast project was redrawn so
that every relation the compiler needs is a wire, and names the implicit fallback for each. It amends
ADRs 0001, 0004, 0005 and 0008 where it overturns them (§6). The drawing it describes is the Railroad
project at commit `ab119e3` on `feat/deployment-cases`, reached by the dated scripts in
`SPCoast/edits/2026-10-2*.py` and the owner's edits between them (§5).

## 1. Problem

The compiler's inputs were a mix of wires, fields, sheet scope and name joins, chosen one at a time. Nobody could say, for a given relation, whether the explicit form and the implicit form resolved to the same thing,
because for several relations only one form existed and for one, the host of a unit, neither did: it was invented by the compiler. ADR 0008 §4.9 and its example described hosts and nodes the drawing did not contain.

Prove there is an explicit way to draw every relation, check it against
the two-seam architecture and its vocabulary, then make three copies of the project, all explicit, all implicit, and both, that must compile to the same Data Model.

## 2. Rules in play

- R1 and R2 of ADR 0008: the Data Model carries every fact the drawing states, losslessly, and nothing of KiCad.
- FieldUnit ADR 0005, defines the cTc interface layers, and is the definitive architecture for this effort.
  - Seam 1 is the code line between office and field logic;
  - Seam 2 is hardware I/O, local or remote; 
  - a transport catalog is bindable to either seam. 
- One source per fact
  - facts, not symbols (ADR 0001 D15); 
  - symbols are keyed by fields, never by name (AGENTS.md); 
  - a net's name is never a fact.
- The order of authority for vocabulary: FieldUnit `docs/GLOSSARY.md`, then FieldUnit ADR 0005, then the
  ADRs here. The audit in `docs/review/naming-audit-2026-10-22.md` was run against it.
- The owner's rulings of this period, quoted where they decide a point.

## 3. Architecture

### 3.1 Four kinds of net

Every wire in the seam drawing is one of four kinds, and a pin's name says which net it lands on:

| Net | Provided by | What lands on it |
|---|---|---|
| **Transport** | a `Transport-*` symbol: the mechanism (a broker; a serial port and baud; DC pulses) | an encoding's `Transport` pin; a CMRInet node's `Transport` pin |
| **Codeline** | a code line encoding (`Encoding-AAR`, `Encoding-US&S-506`, `Encoding-Bits`) through its `Codeline` pin | an Interlocking's `Codeline` pin, and its houses' |
| **IOBus** | a `Processor` through its `IOBus` pin, or a CMRInet node through its `IOBus` pin | every driver's `IOBus` pin |
| **Processor** | Home of the "logic" that implements the office or field unit | one or more interlockings and the transport's that become part of that logic. |

### 3.2 Symbols: what each ingests and provides

| Symbol | Ingests | Provides | Fixed facts |
|---|---|---|---|
| `Transport-`<BR>[`MQTT, TimeCode, CMRInet, LocoNet`] | `Processor`: the processor that runs the code to interact with the bus | `Transport` | Role `TRANSPORT`<br>Kind;<br>`Broker`, or `Port and Baud` |
| `Encoding-AAR`, `-US&S-506`, `-Bits` | `Transport` | `Codeline` | Role `CODELINE_ENCODING`<br>Kind;<br>AAR carries the topic root and Railroad |
| `Encoding-JMRI`, `-CMRInet` | `Transport` | nothing: a fact about the transport instance it rides | Role `IO_ENCODING`<br>Kind;<br>JMRI carries its topic root and `JMRI.SignalSystem` (§3.4)[^signal-system] |
| `Processor` | `Processor`: units, machines, transports | `IOBus` | Role `STRUCTURE`<br>Kind `PROCESSOR`;<br>Board |
| `Interlocking` | `Processor`; `Codeline` | nothing | `Name` (§3.9) |
| `House` | `Codeline`, with its unit;<br>`MC`, the maintainer call | nothing | `CP Name` (§3.9) |
| `OfficeUnit` | `Processor` | nothing | Role `OFFICE_UNIT`;<br>Style `US&S`;<br>Columns, Railroad |
| `Driver-*` (I2C, GPIO, JMRI, CMRInet bits) | `IOBus` | the device pins | Role `IODRIVER`;<br>`IC` names the chip or the encoding kind;<br>a CMRInet bit: IC `CMRI`, Kind `IB` or `OB`, Bit |
| `Driver-CMRInet-Node` | `Transport` | `IOBus` | Role `IODRIVER`,<br>IC `CMRI`, Kind `NODE`;<br>NodeType, Address (the UA),<br>InputBytes, OutputBytes[^cmri-kind] |
| `Device-Head-*` | `IND` from a position pin (A, B, C) of its field mast device; `APP` to its encoders | nothing | Role `DEVICE`, Appliance `head`;<br>Style the head model, fixed per symbol; no Name, no Head letter (§3.7)[^heads] |
| `PanelColumn`, panel devices, `Driver-I2C-MAX7313` | `IOBus` on the panel bus | | |

Every unit sheet potentially exposes four ports to the Office Sheet at the top level: 
 1. `Codeline` (its line), 
 2. `Processor` (where its logic runs),
 3. `IOBus` (its field bus, only when that bus leaves the sheet), and 
 4. `PanelIOBus` (its panel column's bus). 
The office unit needs to connect to:
 - each interlocking through a codeline
 - a processor (local or virtual) that runs its logic,
 - the per-interlocking office panel devices and drivers.
 In addition, a "Virtual" processor or Application can be defined that hosts the logic for interlockings that are themselves either virtual (emulated) or only use distributed I/O devices (via, for example, CMRInet, LocoNet, LCC, MQTT-JMRI,...)

### 3.3 The processor

A processor runs the Office- or Field-Unit's logic and anchors its communication connections.  Processors can be distributed compute units (ESP32/RasPi with IO pins and I2C) or virtual (a desktop application using MQTT or CMRInet).
 - A unit's logic runs on exactly one processor. 
 - The `Processor` net logically connects the Units and transport instances it connects to; 
 - A Processor's `IOBus` net connects to the Drivers it manages.  Drivers are connected to Devices that represent the various railroad appliances managed by an Interlocking.
   - Appliances can connect directly to a processor's GPIO pins, or to pins on I2C expanders and PWM drivers.  Addressable NeoPixel Lamps can be driven from a processor's GPIO pins.
   - Appliances can also reference remote I/O on CMRInet Nodes and JMRI-MQTT IoT devices using a matching encoding on a transport instance on the same processor (§3.4).

### 3.4 Transports are mechanisms; encodings ride them

A transport symbol represents the mechanism - a network connection, a serial port, a twisted pair of wires. An encoding defines the content on that transport and how it is represented (a serializer/deserializer, or encoder/decoder, if you will).  Encodings either define a `Codeline` net  or a `remote I/O` protocol.

A transport instance is connected to a processor through its `Processor` pin, and a given transport may be placed once per processor that connects to it (§3.8).
An I/O encoding's processor defines an instance, and if multiple instances are on a processor, each instance must have different controlling attributes (address, MQTT topic root, ...).

Example:  On the SPCoast example that uses an AAR encoded MQTT codeline, the MQTT Transport is used in two places:  On the OfficeUnit with an AAR Token encoder and on the Gilroy Interchange sheet with a `MQTT-JMRI` encoder to support the remote IoT appliances used by that interlocking.  All the interlockings are connected through codelines that lead back to the OfficeUnit, so all support MQTT and the Codeline encoding; the Gilroy Interchange ALSO supports JMRI-MQTT encoding to talk to JMRI IoT appliances through the same MQTT broker, but on different topics.

#### 3.4.1 A device may aggregate several appliances

A device symbol stands for the hardware at one place. When that hardware packages several appliances, one device
serves them all, and its pins say which function each serves. `Device-Switch-OS` (Railroad-Field) is one device,
named for its switch, that serves the switch motor (pin `M`, the binary demand), the points (the contacts `~{N}` and
`~{R}`) and the OS track circuit's detector (`~{OCC}`). The device is matched to the trackplan switch by Name; the
circuit its `OCC` pin reports is the switch's OS circuit, and deriving that circuit from the pin is still open (PR
121).[^aggregate]

#### 3.4.2 The encoded driver's key

A driver on an I/O encoding (a JMRI object, IC `MQTT-JMRI`) is an encoded driver: it carries no address of its own.
Its key is `Kind.served[.functions]`, from its Kind, the object class, and what its wires state (FieldUnit ADR 0005
S4 and R11), as `seams._encoded_address` computes it.[^encoded-key]

- `served` is the Name of the one device the driver's function pins reach (`_served`). A nameless device, a head or a
  train order lever, serves under its mast's Name and the mast pin its `IND` wire reaches (`_anonymous_served`):
  `Gilroy.E`.
- The functions come from the pin names alone. A driver pin named like the device pin it lands on serves that
  function by its own definition and adds no suffix: a Turnout's `M`, `N` and `R` on the switch's `M`, `N` and `R`
  keep `TURNOUT.777`. A driver pin named otherwise reads the device pin's function as a suffix: a Sensor's `S` on
  `Device-Switch-OS`'s `OCC` is `SENSOR.777.OCC`, on a track circuit detector's `OCC` is `SENSOR.01T.OCC`, on the
  lock lever's `WLQK` is `SENSOR.777.WLQK`, on the train order lever's `STOP` is `SENSOR.Gilroy.E.STOP`; a Light's
  `ON` on a lamp's `LAMP` is `LIGHT.MC1.LAMP`. Several suffixes sort shortest first.
- A SignalMast driver on a mast, a train order mast or a head stands in for positions instead: it carries the
  positions its net reaches unless that is every one of the mast's (`_function_pins`, the library's `Pin.*` contract):
  `SIGNALMAST.778NAB.A` on one pin of a double mast, `SIGNALMAST.778NAB` on both, `SIGNALMAST.Gilroy.E` on a face's
  head.
- One JMRI Turnout is drawn as two symbols, `Driver-JMRI-Turnout` (the command, `M`) and `Driver-JMRI-Turnout-Feedback`
  (the feedback, `N` and `R`). Two symbols at one key are one object only when both are Kind `TURNOUT` on one
  encoding and their wires reach no common device pin (`_one_turnout`); this is the only merge, and their stated
  fields must agree (`entity.conflict`). Anything else at one key is `driver.duplicate`.
- A drawn `Address` never keys. It is written as a stated field and reported at info (`driver.address.override`);
  the derivation uses it only as the tail of a signal mast driver's published topic. A driver wired to no device is
  `driver.serves` at missing, to two devices `driver.serves.two` at error, with no Kind `driver.kind` at missing.

The feature is `tools/layout_compiler/features/field/driver_encoded.feature`; the schema states the rule on
`$defs/driver` (v3.1.0).

#### 3.4.3 `JMRI.SignalSystem`

A JMRI signal mast driver publishes a mast's indication as a JMRI aspect name. Which names is a fact about each
installation: the field `JMRI.SignalSystem` names the JMRI signal system, a JMRI identity, the folder under JMRI's
`xml/signals` (`SPTCO-1969`, `basic`). It is declared on the `Encoding-JMRI` instance, for every signal mast driver
on that encoding, and a `Driver-JMRI-SignalMast` may state its own, which overrides the encoding's.[^signal-system]

The derivation (`derive.jmri_masts`) writes it as `derived.jmriSignalSystem` on the driver (schema v3.1.0, the
version that added `derived` to a driver). Neither stated is `driver.jmri.signal_system` at missing; a system no
aspect-name table names is `driver.signal_system.unknown` at error (`schemas/layout-model/rules/diagnostics.json`).
The aspect-name tables are reference data keyed by signal system, indication and the mast's Kind
(`reference.ASPECT_NAMES`, `aspect_name`, `signal_systems`; the user's `aspectNames` table layers over the shipped
ones). Features: `physical/io/driver_jmri_mast.feature`, `physical/io/driver_jmri_aspect_names.feature`.

Both library symbols declare `JMRI.SignalSystem`, empty by default (Railroad `9a1899e`); the SPCoast drawing states
`SPTCO-1969` on Gilroy's `Encoding-JMRI`.

### 3.5 CMRInet

A CMRInet Node is accessed through its CMRInet Host, addressed by its UA, and provides a bus for its bits:
 - The Processor that will be the CMRInet Host defines a `CMRInet Transport` with the serial port and baud rate for the RS485 serial bus, and a `CMRInet v1.1 Encoding` for the protocol used on that bus.
 - The Field Hardware `IOBus` is anchored by a `Driver-CMRInet-Node` that connects to the `CMRInet Transport` and defines `Node Type 'C' UA:30` with its `IB[]` and `OB[]` arrays
 - `Driver-CMRInet-IB` and `-OB` represent individual bits in those `IB` and `OB` arrays. Each CMRInet driver states what it is in `Kind`: `NODE` for the node, `IB` or `OB` for a bit, which is also the bit's direction and the first part of its key (`IB.3`). `NodeType` is an ordinary node setting (its value, `C`), never the test for a node.
 - The compiler derives the bits in use and checks the byte sizes in the Node declaration, never invents it, and reports an undersized one. Spare
bytes may be used by another interlocking. A node's identity is transport plus UA.

#### 3.6 JMRI-MQTT

JMRI needs no node: its objects are an MQTT topic subscription / publish on the processor itself, and have no hardware between them and the broker, so JMRI drivers sit on the processor's own bus with the JMRI encoding as the fact.
"A symbol earns its place only by carrying a fact nothing else carries".

### 3.7 Head devices[^heads][^atoms]

Signals, masts, heads, indications and head words. The OfficeUnit controls only whether a signal is at `STOP` or is
allowed to indicate safe travel to the `LEFT` or to the `RIGHT`. The FieldUnit determines the allowed indications for
every route the signal governs from switch positions, track occupancy and the other vital concerns, and maps each
indication to what the mast's heads show through lookup tables. The chain and its seams are the signal symbols
worklist's (`docs/review/signal-symbols-worklist.md`, "The chain and its seams", 2026-11-04):

    trackplan Mast ──indication──▶ field Mast device ──pin A/B/C──▶ anonymous Head ──head word──▶ Encoder ──pins──▶ Driver

- The trackplan mast (`Appliance mast`) has one `SIGNAL` pin and no heads. Its Name is KiCad shorthand for three
  atoms (ADR 0003 rules 5 to 7), which the importer states and nothing downstream reads (the owner, 2026-11-12: the
  atoms are stated, the Name is a label composed of them; deriving from the Name would denormalize, since every Studio
  edit would touch many stored things): `given.signal`, the signal number (`784`); `relations.facing`, the side
  letter's direction (D1: N and W `LEFT`, S and E `RIGHT`; the glyph's turn must agree, `geometry.facing`);
  `given.heads`, the head letters top down as a comma list (`B,C` of `784WBC`). The k-th letter is the k-th position,
  so `774NC` is signal 774's head C on a one-position mast and `784WBC`'s pin A is head B. A Name that is not the
  grammar states none of them, `mast.name` at missing. Its `Indications` is empty by rule; filled, it is only an
  explicit list of indication words replacing the derived demand (the owner, 2026-11-04). The demand itself is derived
  with #62.
- The field mast device (`Appliance mast`, Name the trackplan mast's) has one passive pin per head position, `A`,
  `B`, `C` top down (`Device-Mast-Single`, `-Double`, `-Triple`, the dwarf forms).
- A head device (`Appliance head`) is anonymous: no Name, no Head letter. Its `IND` wire to a mast pin is its
  position (`relations.mast`, `relations.position`; a head on a train order mast's face pin states `relations.face`
  instead); its railroad letter, the mast's letter for that pin, is derived (`derived.letter`), never stated on the
  head. The mast's `derived.positions` is keyed by the pin and carries each pin's `letter` and what it `presents`: the
  pin is the physical fact every seam uses, the letter the name, and keyed by the pin A never means pin A on one mast
  and head A on another. Its Style is its model and the index into the head model table, reference data
  (`tools/layout_model/reference.py`, `head_model`): `derived.presents` is the table's head words, the subset of the
  indication list plus DARK the head can show. The right-hand side of the table (lamps, arm positions) is the encoder's
  instruction; no colour or position word crosses a seam. A Style with no row is `head.model` at missing.
- Any number of heads may share a position (the owner, 2026-11-09): a fascia repeater, a head upgrade with both in
  service. The position presents what any of them presents; two heads on one pin presenting different words are
  `head.position` at info, never an error. The same one seam down: a head's `APP` may feed any number of encoders,
  each presenting what its Kind can (#81); the importer refuses none.
- The match: a mast's demand is within what its positions present. A mast with no field mast device, or whose device
  has no head wired, is `mast.device` at missing. On a one-position mast a demanded word the position does not present
  is `mast.presents` at info; a mast with several positions is matched through the policy table (`reference.policy`),
  which lands with #62. A head wired beyond the last position the stated heads count is `mast.heads` at error; one
  letter on two masts of one signal facing one way is `mast.letters` at error (ADR 0003 rule 6).
- A desk signal lever works the masts of its signal number (ADR 0003 rule 5): it serves the number in its interlocking
  and derives `masts`, every mast there whose `given.signal` is that number; a number no mast states is `lever.serves`
  at error. A `CONTROLLED` mast whose signal number no desk signal lever serves is `mast.lever` at missing, as a powered
  switch with no lever is `switch.lever` (the owner, 2026-11-12: Sargent's 836NAB, 836SA and 836SB); an `ABSOLUTE` or
  `PERMISSIVE` mast is automatic and has none.

The rules are `schemas/layout-model/rules/features/physical/field/device_mast_head.feature` and the importer's
`tools/layout_compiler/features/field/device_mast_head.feature`.

### 3.8 Stations, columns and the machine

A FieldUnit attaches to one codeline through its `Codeline` pin; its houses sit on the same net, and represent the bungalow(s) and instrument cases found in the field.  Historically (e.g., with US&S type 506 Traffic Controllers) a single station could only control a limited number of appliances, so complex interlockings required multiple stations, each one with its own unique station address.  Modern era "digital codelines" (like the MQTT AAR Encoding) don't have those limits, and so have a one-to-one relationship between Interlocking and Stations.

Stations are derived:
 - one per interlocking on an AAR line, addressed by name;
 - one per house on a US&S 506 line, addressed by the house's desk column number (the `PanelColumn` Value, which names its house in `CP Name`) 
Nothing is typed per station, as the stations are mapped to the OfficeUnit's columns as station addresses; the OfficeUnit symbol has a `Processor` pin that connects to its processor, and that processor has an IOBus pin that connects to the panel appliances.

### 3.9 One entity, several sheets

Since we are using KiCad as a layout editor, we can use its hierarchical sheet rules to abstract and isolate each interlocking. Sheets at the top of the hierarchy can define things that are used on their child sheets, while child sheets must explicitly espose/export labels for use elsewhere.
A layout-scope entity (a processor, a transport, a node) may be placed on more than one sheet; instances with
one identity (same name and attributes (always excluding KiCad's REFDES)) are one entity. At least one instance declares; every instance that declares values for attributes must agree ; an empty attribute says nothing. This is also the rule for a wire and a field that both speak. ADR 0005 C10's duplicate-declaration error narrows to conflicting declarations.

A sheet's interlocking is only the default scope for the symbols on it that state no `CP Name`[^cpname]. Explicit
statements (`CP Name`, wires, references) override it, so several interlockings drawn on one sheet are unambiguous when
each is stated, and that is not an error.

A trackplan symbol (Role `TRACK`, `APPLIANCE` or `POLICY`) belongs to one interlocking, placed in this order
(`trackplan.placements`, computed once per drawing):[^placement]

1. by its `CP Name` when it names an interlocking or one of its houses, compared case-insensitively as the desk side
   compares them, even on another interlocking's sheet;
2. else by its sheet, the nearest interlocking at or above it (ADR 0004 D12);
3. else, drawn under no interlocking's sheet, by its track net: when the nets on its track pins reach the track pins
   of exactly one interlocking's placed symbols it is that interlocking's (a NextCP on the parent sheet wired to a
   hierarchical net), repeated to a fixpoint so a chain of such symbols is placed from its one placed end;
4. else it belongs to none: the importer reports `trackplan.unit` at missing (`tools/layout_compiler/diagnostics.json`)
   and writes no row for it. It is never dropped in silence.

The feature is `tools/layout_compiler/features/trackplan/trackplan_placement.feature`. Geometry reads the
interlocking's own sheet for its frame (ADR 0010 C5), so a row placed from another sheet has no marker there.

### 3.10 Keys the compiler reads

Symbol attribute names that are used by the compiler:
  - `CP Name` on a house, 
  - `Name` on an Interlocking, 
  - `IC` and `Address` on a chip or node,
  - `Column` on a PanelColumn.
  - `Role`: the symbol's class, what the compiler does with it. In the libraries today: 
      - `APPLIANCE`, `TRACK`, `POLICY` and `STRUCTURE` on the trackplan;
      - `OFFICE_UNIT`, `COLUMN`, `PANEL`, `TRANSPORT`, `CODELINE_ENCODING` and `IO_ENCODING` on the office side; 
      - `DEVICE` in the field, with Appliance `head` on the head devices; 
      - `IODRIVER` and `SETTING` in hardware I/O. 
    - A symbol with no Role is drawing only. `CAST` and `MACHINE` were implementation words and are gone from the libraries and sheets (Railroad `edits/2026-10-23-roles.py`); the symbol-field lint follows (`tools/contract/lint_symbol_fields.py`).
  - `Kind`: the sub-class where a Role alone does not say what the symbol is: `STRUCTURE` is `INTERLOCKING`, `CONTROL_POINT` or `PROCESSOR`; `TRACK` is `IRJ`, `IRJ_SIGNAL`, `IRJ_SIGNALS` (a joint with a mast on each side, ADR 0013), `END_CTC`, `MILEPOST`, `NEXT_CP`, `BUMPER` (the track ends) or `INDUSTRY` (track exists past this point, but is not drawn; added 2026-10-24); `POLICY` is the rule number (a GCOR Rule regime, the current-of-traffic sign `GCOR_RULE_9_14`, a plate `RULE_290_G` or `RULE_290_R`) or `LADDER`, a ladder marker, whose `Name` names its ladder and makes its row a named row; any other `POLICY` Kind is written as drawn and is the derivation's `policy.kind` at warning, which holds its piece to no regime (ADR 0013 §7.1);[^policy-kind] a `TRANSPORT` is `MQTT`, `CMRI`, `TIMECODE` or `LOCONET`; an encoding is `AAR`, `USS506`, `BITS`, `JMRI` or `CMRI`. An encoding's Kind must pair with its transport's Kind (reference data). Roles that classify by `Appliance` and `Style` instead (`APPLIANCE`, `DEVICE`, `PANEL`) carry no Kind, with one exception: a mast states `CONTROLLED`, `ABSOLUTE` or `PERMISSIVE`, what the signal is, and a mast with none is missing.[^mast-kind]
  - `Style`: the variant within an appliance, and the one key two symbols must agree on: a head's style (`CL`, `CPL`, `UQ`, `LQ`) on the trackplan head and fixed in the head device; a mast's (`single`, `double`, `dwarf`); a switch's (`powered`, `manual`, `manual_sensed`, `lock`, `dual`, `derail`); a track circuit's (`virtual`, `boundary`); a lamp's or lever's on the panel; the OfficeUnit's (`US&S`).
  - `Topic` on MQTT Encodings
  - `JMRI.SignalSystem` on `Encoding-JMRI` and, as an override, on `Driver-JMRI-SignalMast` (§3.4.3)[^signal-system]
  - `Reference` and `Value` are never used.  How a key is derived in KiCad is KiCad's business (e.g., the Address attribute may have `${Value}` as its content, that is OK.). Library defaults for names, hosts and transports are empty: we've chosen to NOT use placeholders because inadvertant "update all symbols from Library" with the wrong checkboxes is a disaster. The compiler's "missing" report is the tutorial prompt. Fixed facts (Role, Kind, Style, a topic template) keep their defaults.

### 3.11 Vocabulary

`Processor` not `Host` (a retired glossary word) except that
`Host` survives in some Descriptions that need to be updated; 
`IOBus` and `PanelIOBus`; 
`House` (instrument house; `Case` reserved); 
`Style` not `Type` on the OfficeUnit; `
`OfficeUnit` not `machine`
`FieldUnit` not `unit`
`KiCad Symbol Units` not `units`
`CMRInet Node` not `node`
`CMRInet Host` not `host`
`columns` not `lines`
`Driver` not `chip`
`TimeCode`, `LocoNet`, `CMRInet`; `NodeType`; Kind `NODE`, `IB`, `OB` on CMRInet drivers;
Kind `MQTT-JMRI` on JMRI drivers IC; 
`head devices`, not `casts`, in prose.
Pins carry the relation's name; a provided pin is named for what it provides. 
Captions drawn in symbol bodies follow pin renames.

### 3.12 The relation table

| Relation | Explicit | Implicit fallback | Check |
|---|---|---|---|
| Unit on its line | Interlocking `Codeline` on an encoding's Codeline net | an encoding instance in the unit's folder; by layout when one line exists | both name one line |
| House is a station | house on the unit's Codeline net | house in the folder | same |
| 506 station address | none | the house's column number via `CP Name` | columns unique per OfficeUnit |
| FieldUnit runs on | Interlocking `Processor` to a Processor | the one Processor on the sheet; none means reported | one processor per FieldUnit |
| OfficeUnit runs on | OfficeUnit `Processor` to a Processor | the one Processor on its sheet | |
| OfficeUnit's columns | none | its interlockings' columns | |
| Driver on a bus | `IOBus` to a Processor or CMRInet Node | the one Processor on the sheet; `Processor` field when two | IC native or encoded (§3.3) |
| Transport anchored on | Transport `Processor` to a Processor | the `Processor` field; the machine's processor for a code line transport (0005 S3) | an anchor per connecting processor |
| Encoding rides | `Transport` to a transport net | the `Transport` field; by layout when one transport of its kind exists | kind pairs with the transport's kind (reference data) |
| CMRInet Node on its line | `Driver-CMRInet-Node` connects a processor's `Transport` to an `IOBus` | the `Transport` field | UA unique per line |
| Bit on its CMRInet Node | a `Driver-CMRInet-IB/OB` connects to an `IOBus` that originates at a `Driver-CMRInet-Node` | the one CMRInet Node on the sheet; the bit's `Node` field (the UA) when a sheet holds two, added to the library 2026-10-23 (Railroad `edits/2026-10-23-descriptions.py`), empty by default | bytes declared cover bits used |
| Head device to its position | its `IND` wire to a position pin (A, B, C) of the field mast device named for the trackplan mast[^heads] | none | the mast's stated `heads` count the positions (`mast.heads`); demand ⊆ presents (§3.7)[^atoms] |
| Signal lever to its masts | the lever's number is the masts' stated `signal` in the lever's interlocking (§3.7)[^atoms] | none | `lever.serves`; a CONTROLLED mast with no lever is `mast.lever` |
| Track shared by two interlockings' switches | none: a wire joining switch ports of two interlockings with no joint between | none | none when neither port is dispatcher-controlled: two crew-worked switches on one spur, which no interlocking claims (ADR 0013 §7.1 accepts plain block track); a dispatcher-controlled port there is `reference.track`[^atoms][^localswitches] |
| Derail to its switch | stated: the importer reads the drawn Name's gang id once (ADR 0003 D8) and writes `relations.switch`, the switch or lock of the derail's interlocking it follows; the switch derives `derails`[^derail] | none: a derail that states no switch is independent | `derail.switch` at error: a stated switch that is no switch or lock of the interlocking |
| Panel column to its control point | `CP Name` on the column, naming its interlocking or one of its houses[^cpname] | an empty `CP Name`: the column's interlocking | names resolve |
| Track leaves an interlocking | a `NEXT_CP` (to the next interlocking), a plain `IRJ` beyond which the track carries another regime's `GCOR Rule` marker (ADR 0013 §7.1), or an end (`INDUSTRY`, `BUMPER`)[^track][^regime] | none | a switch port or track row related to another interlocking's is an error (`reference.track`); another interlocking is reached only through its indications |
| Trackplan symbol in its interlocking | `CP Name` naming the interlocking or one of its houses (§3.9) | its sheet's interlocking; else the one interlocking its track net reaches | none of these is `trackplan.unit` at missing, no row written[^placement] |
| Encoded driver's key | its wires: `Kind.served[.functions]` (§3.4.2) | none; `Address` never keys | two symbols at one key are one Turnout's command and feedback, else `driver.duplicate`[^encoded-key] |
| Signal mast driver's signal system | `JMRI.SignalSystem` on the driver (§3.4.3) | the `JMRI.SignalSystem` of its `Encoding-JMRI` | neither is `driver.jmri.signal_system`; a system no table names is `driver.signal_system.unknown`[^signal-system] |

A panel appliance's indication lamps (a switch's, a signal's, a maintainer call's) belong to its lever and so to the
lever's column. A model board lamp never uses a column: its scope is the interlocking of the panel sheet it is drawn on.

The first and second columns must resolve to the same thing in the "both" copy of the project, or the
compiler reports the disagreement. The table is the test for the three copies.

## 4. Decision

Ratify §3 as the drawing contract the milestone D compiler reads, and §3.12 as its consistency checks.[^s4]

## 5. Record

- 2026-10-21. Owner's mockup of explicit wiring on Luchessa (Railroad `5288025`); the pattern applied to
  every sheet (`3129076`); uniform ports (`48e86ff`, `2965e7e`); local units and panels on the desk bus
  (`379b30b`); appliances and local I/O on every unit in Sargent's forms (`3bcab3d`).
- 2026-10-22. Watsonville's yard (`a5bceb8`); Interchange hosted by its own processor (`6f22a0f`); the
  naming audit and its rulings (`8938528`, `096201e`, `d7ca97d`); the node as a driver and the JMRI
  attachment retired (`6846d43`); head pictograms restored (`a2a5efc`); transports as mechanisms and
  encodings with provided nets (`203bab3`); the owner's instance-per-anchor MQTT, node fields, IC on the
  node, OfficeUnit reduced to its processor (`3e21882`, `97bba77`, `a055ce3`, `d93d778`, `3cb51fc`,
  `f204f45`).
- 2026-10-23. Head devices renamed with fixed styles, LQ semaphore, CPL-Pixel, Interchange heads CL
  (`54f3fa9`); definitions refreshed and local buses local (`ab119e3`). The node's pin ruled `Transport`.
- 2026-10-24. `INDUSTRY` added to the TRACK Kinds (§3.10) with the owner's Industry symbol (Railroad `37a0dcd`),
  which replaced the wires drawn into dark track at Sargent, Corporal and Luchessa. A reader keys by Kind, never
  by symbol name, so "track ends" and "track continues, not drawn" need two Kinds. Raised in ADR 0010.
- Two slips recorded for the method: a script reset discarded the owner's uncommitted edits once, recovered
  from KiCad's backup archive (`e477212`); a commit was gated on the wrong check once and reset.
- 2026-11-10 to 11-12. The owner's rulings on encoded drivers, placement and the signal system landed in code and
  features in that week (PRs 116, 121, 123, 124, 125) and are written into §3.4.1 to §3.4.3, §3.9 and §3.12 on
  2026-11-12 as the first application of ADR 0014 decision 1: a nameless head or train order lever serves under the
  mast pin its `IND` reaches (`6fcd375`); the key's functions come from the pin names, on every device (`3010cd6`,
  `5b1f750`); a Turnout's command and feedback are the one merge (`6fcd375`); a trackplan symbol is placed by
  `CP Name`, sheet or track net, else reported (`2d79796`); the aspect-name table is named by `JMRI.SignalSystem`
  (`82b8262`, renamed from `SignalSystem` in `d6b052c`); the SPCoast drawing states it on Gilroy's `Encoding-JMRI`
  (Railroad `0b39d49`).

## 6. Consequences

- C1. ADR 0005 A8 ("a CMRInet node is a processor that hosts nothing"), S3 and C3 (`Host` as a transport
  field) and the strict form of C10 are superseded by §3.5, §3.4 and §3.8.
- C2. ADR 0001 D12 (the bare-name rule) is superseded by `CP Name` (§3.9); D13 (stations as encoding
  instances with Station and Address) by §3.7; the "drawn default" sentence after its phase table by
  "the drawing is the deployment".
- C3. ADR 0004 D13's field units follow §3.3; `MAIN HOUSE` is `House`.
- C4. ADR 0008 §4.5, §4.9, §5 and §6 are rewritten on this model in its rev 4; the schema gets a new major
  with transports, encodings, processors, nodes and buses as entities and bindings as routes; the example is
  derived from the project by a reader, never typed.
- C5. The FieldUnit glossary lacks processor, transport, encoding, attachment, bus, chip, driver, node, port,
  seam, remote and local I/O: a delta is proposed in `docs/review/glossary-delta-2026-10-23.md`.
- C6. The compiler's checks are the fourth column of §3.12 plus the head position match of §3.7, the
  node byte check of §3.5, the encoded-driver checks of §3.4.2 (`driver.duplicate`, `driver.serves`,
  `driver.serves.two`, `driver.kind`, `driver.address.override`), the placement check of §3.9 (`trackplan.unit`) and
  the signal-system checks of §3.4.3 (`driver.jmri.signal_system`, `driver.signal_system.unknown`).[^c6]
- C7. The three-copy experiment (all explicit, all implicit, both) is the acceptance test for milestone D;
  the "both" copy is this project.
- C8. The symbols manual (Railroad `symbols/manual.html`) states what §3.4.1 to §3.4.3 commit a field or pin to:
  the fragments for `Device-Switch-OS`, the JMRI drivers, `Encoding-JMRI` and `Local-Lock` are changed with this
  text (ADR 0014 decision 1). Both library symbols declare `JMRI.SignalSystem` (§3.4.3).[^c6]

## 7. Out of scope

A picture and words for the hosting variations the owner listed (a field processor polling its own CMRInet
nodes; a local processor as MQTT client, which Interchange now is); KiCad units for a node's bits; LCC and
other transports; Studio's own notation.

[^cmri-kind]: Amended 2026-10-30 (owner): CMRInet drivers state `Kind` `NODE`, `IB` or `OB` (Railroad 2ecf8a4). Before, the node was the driver with `NodeType` and a bit's direction came from its D pin's electrical type; the earlier text is at commit c3edd3c.

[^cpname]: Rewritten in place on 2026-10-29 (the owner, 2026-10-28): a column's `CP Name` names its interlocking or one
    of its houses and defaults to the interlocking; a sheet's interlocking is only a default scope; model board lamps
    never use columns, while an appliance's indication lamps follow its lever's column. The earlier wording is at
    commit `c3edd3c`.

[^track]: Added 2026-10-29 (the owner, 2026-10-28 and 2026-10-29). Two track pins of one symbol on one wire
    (`track.shorted`) is an import diagnostic, the KiCad importer's, not a rule here (ADR 0012 §3.3).

[^regime]: Amended 2026-11-10 (owner; ADR 0013 §7.1 and decision 3). Until commit `9516aa0` this read "or an `END_CTC` (to
    dark territory: an industry complex, a branch line)". The track beyond the boundary is in the model under its own
    regime; "dark" is the office's view, not a kind of track; the Kind `END_CTC` and `IRJ-END_CTC` are retired.

[^heads]: Rewritten in place on 2026-11-12 (issue #80; the owner, 2026-11-04 and 2026-11-09, `docs/review/signal-symbols-worklist.md`).
    Until commit `260596c` §3.7 read heads as named devices (`Device-Head-CL-Pixel`, `-CPL-Encoded`, `-Semaphore-UQ`, each
    one aspect vocabulary on one hardware) bound to a trackplan head by the mast's Value and a `Head` letter, with the
    vocabularies matched (`head.vocabulary`); the relation table row read "Head device to its head | mast Value and
    `Head` letter, by name | same | vocabularies match (§3.6)". The trackplan head symbols and the head Name and letter
    are retired; a head is a position on its field mast device.

[^atoms]: Rewritten in place on 2026-11-12 (the owner, on the first consumer's findings of 2026-11-12; schema 3.3.0,
    `schemas/layout-model/v3.3.0-migration.md`). Until commit `da2a765` §3.7 read the positions off the Name's letters
    in the derivation (`mast.grammar`, `mast.facing`, `lever_of`), `derived.positions` was keyed by the pin letter
    alone, a desk lever found its masts by cutting the letters off, and a track wire shared by two interlockings'
    switches was not reported. The grammar is now read once, in the importer (`grammar.mast_atoms`).

[^localswitches]: Rewritten in place on 2026-11-13 (the owner: Corporal's and Sargent's switch 1 are two distinct
    crew-worked switches, and the Beet Loader spur between them raises no conflict). Until commit `17764dd` the row
    reported such a wire as `reference.switches` at warning, one piece of track claimed by two interlockings; the code
    is retired.

[^derail]: Added 2026-11-13 (issue #133; the owner's ruling of 2026-11-13 that the importer states every atom and
    nothing downstream parses a Name). Until commit `662e9b8` the derivation paired a derail with its switch by its
    Name (`grammar.depends_on` read the gang id); the relation is now stated by the writer, as a mast's atoms are[^atoms].

[^mast-kind]: Amended 2026-10-31 (owner, ADR 0013): a mast states `Kind` `CONTROLLED`, `ABSOLUTE` or `PERMISSIVE`; the TRACK Kind `IRJ_SIGNALS` and the track circuit Style `boundary` are added. Before, `APPLIANCE` carried no Kind without exception; the earlier text is at commit aa80e18.

[^aggregate]: Added 2026-11-12 (ADR 0014 decision 1, the backlog of 2026-11-05 to 11-12). The rule landed in the
    feature `field/driver_encoded.feature` ("a driver pin named like the device pin serves that function and adds
    nothing") in commit `5b1f750`; the symbol `Device-Switch-OS` is Railroad-Field's. The §3.4 text it follows is at
    commits `2cf4105` and `cc370f4`.

[^encoded-key]: Added 2026-11-12 (ADR 0014 decision 1). The key `Kind.served[.functions]` and the Turnout merge landed in
    `6fcd375` (the owner, 2026-11-10); the matching-pin rule on every device in `3010cd6` and `5b1f750` (the owner,
    2026-11-11), which retired `6fcd375`'s carve-out for named devices. Before this text, §3.6 said only that JMRI
    drivers sit on the processor's own bus; the §3.4 text this follows is at commits `2cf4105` and `cc370f4`.

[^signal-system]: Added 2026-11-12 (ADR 0014 decision 1). The field landed as `SignalSystem` in `82b8262` (the owner,
    2026-11-10) and was renamed `JMRI.SignalSystem`, a JMRI identity, in `d6b052c` (the owner, 2026-11-11), with the
    derived key `jmriSignalSystem` and the code `driver.jmri.signal_system`. The §3.2 table row and the §3.10 list this
    amends are at commit `cc370f4`.

[^placement]: Added 2026-11-12 (ADR 0014 decision 1). The order landed in `2d79796` (the owner, 2026-11-11), which
    replaced placement by sheet alone, under which a symbol under no interlocking sheet was dropped in silence. The
    §3.9 text this follows is at commits `2cf4105` and `33d26ee`.

[^s4]: Amended 2026-11-12 (ADR 0014 decision 1): the relation table is §3.12 since rev 2 moved it; the ratified
    sentence said §3.11, the same slip C6 had. A section number is not a decision. The earlier text is at commit `cc370f4`.

[^c6]: Amended 2026-11-12 (ADR 0014 decision 1): C6 names the checks of §3.4.2, §3.4.3 and §3.9, and its references
    to the relation table and the head-vocabulary error now read §3.12 and §3.7, the sections that hold them since
    rev 2; C8 is new. The earlier C6 is at commit `cc370f4`.

[^policy-kind]: Amended in place on 2026-11-13 (issue #145, the owner): `LADDER` is added, a named `POLICY` row is
    allowed, and an unknown `POLICY` Kind is reported (`policy.kind`). Before, the text was "`POLICY` is the rule
    number"; the earlier text is at commit `1a733ef`. Amended again the same day: `policy.kind` is the
    derivation's rule check, not the importer's, and holds its piece to no regime; the earlier text is at `785b056`.
