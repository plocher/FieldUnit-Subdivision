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
| `Encoding-JMRI`, `-CMRInet` | `Transport` | nothing: a fact about the transport instance it rides | Role `IO_ENCODING`<br>Kind;<br>JMRI carries its topic root |
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

### 3.7 Head devices[^heads]

Signals, masts, heads, indications and head words. The OfficeUnit controls only whether a signal is at `STOP` or is
allowed to indicate safe travel to the `LEFT` or to the `RIGHT`. The FieldUnit determines the allowed indications for
every route the signal governs from switch positions, track occupancy and the other vital concerns, and maps each
indication to what the mast's heads show through lookup tables. The chain and its seams are the signal symbols
worklist's (`docs/review/signal-symbols-worklist.md`, "The chain and its seams", 2026-11-04):

    trackplan Mast ──indication──▶ field Mast device ──pin A/B/C──▶ anonymous Head ──head word──▶ Encoder ──pins──▶ Driver

- The trackplan mast (`Appliance mast`) has one `SIGNAL` pin and no heads. Its Name's letters count its head
  positions (ADR 0003 rule 7): the k-th letter is the k-th position top down, so `774NC` is signal 774N's head C on a
  one-position mast. Its `Indications` is empty by rule; filled, it is only an explicit list of indication words
  replacing the derived demand (the owner, 2026-11-04). The demand itself is derived with #62.
- The field mast device (`Appliance mast`, Name the trackplan mast's) has one passive pin per head position, `A`,
  `B`, `C` top down (`Device-Mast-Single`, `-Double`, `-Triple`, the dwarf forms).
- A head device (`Appliance head`) is anonymous: no Name, no Head letter. Its `IND` wire to a mast pin is its
  position (`relations.mast`, `relations.position`; a head on a train order mast's face pin states `relations.face`
  instead). Its Style is its model and the index into the head model table, reference data
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
  which lands with #62. A head wired beyond the last position the Name letters count is `mast.heads` at error.

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
  - `Kind`: the sub-class where a Role alone does not say what the symbol is: `STRUCTURE` is `INTERLOCKING`, `CONTROL_POINT` or `PROCESSOR`; `TRACK` is `IRJ`, `IRJ_SIGNAL`, `IRJ_SIGNALS` (a joint with a mast on each side, ADR 0013), `END_CTC`, `MILEPOST`, `NEXT_CP`, `BUMPER` (the track ends) or `INDUSTRY` (track exists past this point, but is not drawn; added 2026-10-24); `POLICY` is the rule number; a `TRANSPORT` is `MQTT`, `CMRI`, `TIMECODE` or `LOCONET`; an encoding is `AAR`, `USS506`, `BITS`, `JMRI` or `CMRI`. An encoding's Kind must pair with its transport's Kind (reference data). Roles that classify by `Appliance` and `Style` instead (`APPLIANCE`, `DEVICE`, `PANEL`) carry no Kind, with one exception: a mast states `CONTROLLED`, `ABSOLUTE` or `PERMISSIVE`, what the signal is, and a mast with none is missing.[^mast-kind]
  - `Style`: the variant within an appliance, and the one key two symbols must agree on: a head's style (`CL`, `CPL`, `UQ`, `LQ`) on the trackplan head and fixed in the head device; a mast's (`single`, `double`, `dwarf`); a switch's (`powered`, `manual`, `manual_sensed`, `lock`, `dual`, `derail`); a track circuit's (`virtual`, `boundary`); a lamp's or lever's on the panel; the OfficeUnit's (`US&S`).
  - `Topic` on MQTT Encodings
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
| Head device to its position | its `IND` wire to a position pin (A, B, C) of the field mast device named for the trackplan mast[^heads] | none | the Name's letters count the positions; demand ⊆ presents (§3.7) |
| Panel column to its control point | `CP Name` on the column, naming its interlocking or one of its houses[^cpname] | an empty `CP Name`: the column's interlocking | names resolve |
| Track leaves an interlocking | a `NEXT_CP` (to the next interlocking), a plain `IRJ` beyond which the track carries another regime's `GCOR Rule` marker (ADR 0013 §7.1), or an end (`INDUSTRY`, `BUMPER`)[^track][^regime] | none | a switch port or track row related to another interlocking's is an error (`reference.track`); another interlocking is reached only through its indications |

A panel appliance's indication lamps (a switch's, a signal's, a maintainer call's) belong to its lever and so to the
lever's column. A model board lamp never uses a column: its scope is the interlocking of the panel sheet it is drawn on.

The first and second columns must resolve to the same thing in the "both" copy of the project, or the
compiler reports the disagreement. The table is the test for the three copies.

## 4. Decision

Ratify §3 as the drawing contract the milestone D compiler reads, and §3.11 as its consistency checks.

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
- C6. The compiler's checks are the fourth column of §3.11 plus the head position match of §3.7 and the
  node byte check of §3.5.
- C7. The three-copy experiment (all explicit, all implicit, both) is the acceptance test for milestone D;
  the "both" copy is this project.

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

[^mast-kind]: Amended 2026-10-31 (owner, ADR 0013): a mast states `Kind` `CONTROLLED`, `ABSOLUTE` or `PERMISSIVE`; the TRACK Kind `IRJ_SIGNALS` and the track circuit Style `boundary` are added. Before, `APPLIANCE` carried no Kind without exception; the earlier text is at commit aa80e18.
