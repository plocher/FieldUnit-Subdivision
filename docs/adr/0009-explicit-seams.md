# ADR 0009. Explicit seams: the nets, symbols and pins the compiler reads

Proposed, 2026-10-23. Asked of the owner: ratify §3 and the relation table in §3.11.

This records the design settled between 2026-10-21 and 2026-10-23 while the SPCoast project was redrawn so
that every relation the compiler needs is a wire, and names the implicit fallback for each. It amends
ADRs 0001, 0004, 0005 and 0008 where it overturns them (§6). The drawing it describes is the Railroad
project at commit `ab119e3` on `feat/deployment-cases`, reached by the dated scripts in
`SPCoast/edits/2026-10-2*.py` and the owner's edits between them (§5).

## 1. Problem

The compiler's inputs were a mix of wires, fields, sheet scope and name joins, chosen one at a time. Nobody
could say, for a given relation, whether the explicit form and the implicit form resolved to the same thing,
because for several relations only one form existed and for one, the host of a unit, neither did: it was
invented by the compiler. ADR 0008 §4.9 and its example described hosts and nodes the drawing did not
contain.

The owner's program (2026-10-21): prove there is an explicit way to draw every relation, check it against
the two-seam architecture and its vocabulary, then make three copies of the project, all explicit, all
implicit, and both, that must compile to the same file.

## 2. Rules in play

- R1 and R2 of ADR 0008: the file carries every fact the drawing states, losslessly, and nothing of KiCad.
- FieldUnit ADR 0005, the cTc interface layers: Seam 1 is the code line between office and field logic;
  Seam 2 is hardware I/O, local or remote; a transport catalog is bindable to either seam. The definitive
  architecture for this effort (owner, 2026-10-20).
- One source per fact (AGENTS.md design rules); facts, not symbols (ADR 0001 D15); symbols are keyed by
  fields, never by name (AGENTS.md); a net's name is never a fact.
- The order of authority for vocabulary: FieldUnit `docs/GLOSSARY.md`, then FieldUnit ADR 0005, then the
  ADRs here. The audit in `docs/review/naming-audit-2026-10-22.md` was run against it.
- The owner's rulings of this period, quoted where they decide a point.

## 3. Architecture

### 3.1 Three kinds of net

Every wire in the seam drawing is one of three kinds, and a pin's name says which net it lands on:

| Net | Provided by | What lands on it |
|---|---|---|
| **Transport** | a `Transport-*` symbol: the mechanism (a broker; a serial port and baud; DC pulses) | an encoding's `Transport` pin; a CMRInet node's `Transport` pin |
| **Codeline** | a code line encoding (`Encoding-AAR`, `Encoding-US&S-506`, `Encoding-Bits`) through its `Codeline` pin | an Interlocking's `Codeline` pin, and its houses' |
| **IOBus** | a `Processor` through its `IOBus` pin, or a CMRInet node through its `IOBus` pin | every driver's `IOBus` pin |

A fourth name, **Processor**, is the net of a processor: an Interlocking's, an OfficeUnit's or a transport's
`Processor` pin lands on a `Processor` symbol's `Processor` pin and nowhere else. "A `Processor` wire always
ends on a processor" (owner, 2026-10-22).

### 3.2 Symbols: what each ingests and provides

| Symbol | Ingests | Provides | Fixed facts |
|---|---|---|---|
| `Transport-MQTT`, `-TimeCode`, `-CMRInet`, `-LocoNet` | `Processor`: the processor that runs the mechanism (the master of a line; a client of a broker) | `Transport` | Role `TRANSPORT`, Kind; Broker, or Port and Baud |
| `Encoding-AAR`, `-US&S-506`, `-Bits` | `Transport` | `Codeline` | Role `CODELINE_ENCODING`, Kind; AAR carries the topic root and Railroad |
| `Encoding-JMRI`, `-CMRInet` | `Transport` | nothing: a fact about the transport instance it rides | Role `IO_ENCODING`, Kind; JMRI carries its topic root |
| `Processor` | `Processor`: units, machines, transports | `IOBus` | Role `STRUCTURE`, Kind `PROCESSOR`; Board |
| `Interlocking` | `Processor`; `Codeline` | nothing | `Name` (§3.9) |
| `House` | `Codeline`, with its unit; `MC`, the maintainer call | nothing | `CP Name` (§3.9) |
| `OfficeUnit` | `Processor` | nothing | Role `MACHINE`; Style `US&S`; Columns, Railroad |
| `Driver-*` (I2C, GPIO, JMRI, CMRInet bits) | `IOBus` | the device pins | Role `IODRIVER`; `IC` names the chip or the encoding kind |
| `Driver-CMRInet-Node` | `Transport` | `IOBus` | Role `IODRIVER`, IC `CMRI`; NodeType, Address (the UA), InputBytes, OutputBytes |
| `Device-Head-*` | its device pins from a driver; `IND` from its mast | nothing | Role `CAST`; Style fixed per symbol (§3.6) |
| `PanelColumn`, panel devices, `Driver-I2C-MAX7313` | `IOBus` on the panel bus | | |

Every unit sheet exposes four ports to South-cTc: `Codeline` (its line), `Processor` (where its logic runs),
`IOBus` (its field bus, only when that bus leaves the sheet), `PanelIOBus` (its panel column's bus). The
root wires each to a transport net, a processor or the desk processor's bus, and no-connects what stays
local. "The pattern is the point" (owner, 2026-10-21).

### 3.3 The processor

A processor runs logic and anchors connections. Its `Processor` net carries the units and machines it runs
and the transport instances it connects to; its `IOBus` carries the chips it owns. A virtual host
(`SPCoastApp`, Board `MacOS`) is a `Processor` like any other. A unit's logic runs on exactly one
processor: "the logic for an interlocking is being split between two processors, which we agreed wouldn't
happen" (owner, 2026-10-22). A driver on a processor's bus whose IC is not native to the processor's
board needs an encoding of that kind on a transport instance the processor anchors (§3.4); which kinds a
board provides natively (cpNode-Xiao: I2C, GPIO, Pixel) is reference data.

### 3.4 Transports are mechanisms; encodings ride them

A transport symbol holds the mechanism's facts only. What rides it is an encoding, and what an encoding
provides decides its seam: a code line encoding provides a `Codeline` net for units; an I/O encoding provides
nothing but the fact that this processor's bus reaches that kind of remote I/O.

A transport instance is anchored on a processor through its `Processor` pin, and a transport may be placed
once per processor that connects to it (§3.8): MQTT is placed on South-cTc beside JohnCTC and SPCoastApp and
on the Gilroy Interchange sheet beside `Gilroy`. The AAR encoding rides the office instance; the JMRI
encoding rides `Gilroy`'s. "A code line encoding's field ends are derived through the Interlocking symbols'
Processor wires" (owner, 2026-10-22); an I/O encoding's processor is the anchor of the instance it rides.
The MQTT topic root is a fact of the encoding, not of the broker.

### 3.5 The CMRInet node

A node is on the line, addressed by its UA, and provides a bus for its bits: `Driver-CMRInet-Node` ingests
`Transport` and provides `IOBus`; `Driver-CMRInet-IB` and `-OB` are drivers on that bus like any other. The
node declares NodeType (the spec's letter: C, M, N), its UA and its IB and OB byte counts; the compiler
derives the bits in use and checks the declaration, never invents it, and reports an undersized one. Spare
bytes may be used by another interlocking. A node's identity is transport plus UA; its Value is display.
JMRI needs no node: its objects have no hardware between them and the broker, so JMRI drivers sit on the
processor's own bus with the JMRI encoding as the fact. "A symbol earns its place only by carrying a fact
nothing else carries" (owner, 2026-10-22).

### 3.6 Head devices

Two tables, two owners. Indication to aspect belongs to the trackplan head (`Signal Head - CL`, `- CPL`,
`- Semaphore-UQ`, `- Semaphore-LQ`). Aspect to I/O belongs to the head device, and a device symbol embodies
one aspect vocabulary on one hardware: `Device-Head-CL-Pixel`, `-CL-RGB`, `-CPL`, `-CPL-Encoded`,
`-CPL-Pixel`, `-Semaphore-UQ`, `-Semaphore-LQ`, each with its Style fixed and hidden. Symbol names are the
railroad's head types, not the implementation (owner, 2026-10-23). A lamp vocabulary serves any head with a
lamp: a UQ semaphore is a `-Semaphore-UQ` arm plus a `-CL-RGB` spectacle lamp. The head's vocabulary and the
device's must match, or:

    ERROR: the trackplan draws 778SAB as a CPL head, but its device is Device-Head-CL-Pixel.
    Fix: change the trackplan head, or bind a CPL device.

### 3.7 Stations, lines and the machine

A unit attaches to one line through its `Codeline` pin; its houses sit on the same net. Stations are derived:
one per interlocking on an AAR line, addressed by name; one per house on a US&S 506 line, addressed by the
house's desk column number (the `PanelColumn` Value, which names its house in `CP Name`). Nothing is typed
per station. The machine's lines are derived from its columns; the OfficeUnit has a `Processor` pin and
nothing else. The drawing is the deployment: no generator re-targets a line or re-hosts a unit.

### 3.8 One entity, several sheets

A layout-scope entity (a processor, a transport, a node) may be placed on more than one sheet; instances with
one identity are one entity. At least one instance declares; every instance that declares must agree; an
empty field says nothing. This is also the rule for a wire and a field that both speak. ADR 0005 C10's
duplicate-declaration error narrows to conflicting declarations.

### 3.9 Keys the compiler reads

`CP Name` on a house, `Name` on an Interlocking, `Address` on a chip or node, `Value` on a PanelColumn.
A Value that is a display macro (`${CP Name}`, `${TITLE}`, `UA${Address}`) is never read; how a key is
derived in KiCad is KiCad's business (owner, 2026-10-22). Library defaults for names, hosts and transports
are empty: a placeholder that looks like a name becomes a name, and the compiler's "missing" report is the
tutorial prompt. Fixed facts (Role, Kind, Style, a topic template) keep their defaults.

### 3.10 Vocabulary

From the audit and the owner's rulings: `Processor` not `Host` (a retired glossary word) except that
`Host` survives nowhere; `IOBus` and `PanelIOBus`; `House` (instrument house; `Case` reserved); `Style` not
`Type` on the machine; `TimeCode`, `LocoNet`, `CMRInet`; `NodeType`; Kind `MQTT-JMRI` on JMRI drivers'
IC; no `cTc`; head devices, not casts, in prose. Pins carry the relation's name; a provided pin is named for
what it provides. Captions drawn in symbol bodies follow pin renames (`edits/2026-10-22-pin-captions.py`).

### 3.11 The relation table

| Relation | Explicit | Implicit fallback | Check |
|---|---|---|---|
| Unit on its line | Interlocking `Codeline` on an encoding's Codeline net | an encoding instance in the unit's folder; by layout when one line exists | both name one line |
| House is a station | house on the unit's Codeline net | house in the folder | same |
| 506 station address | none | the house's column number via `CP Name` | columns unique per machine |
| Unit runs on | Interlocking `Processor` to a Processor | the one Processor in the folder; none means reported | one processor per unit |
| Machine runs on | OfficeUnit `Processor` to a Processor | the one Processor on its sheet | |
| Machine's lines | none | its columns' interlockings' lines | |
| Chip on a bus | `IOBus` to a Processor or node | the one Processor on the sheet; `Processor` field when two | IC native or encoded (§3.3) |
| Transport anchored on | Transport `Processor` to a Processor | the `Processor` field; the machine's processor for a code line transport (0005 S3) | an anchor per connecting processor |
| Encoding rides | `Transport` to a transport net | the `Transport` field; by layout when one transport of its kind exists | kind pairs with the transport's kind (reference data) |
| Node on its line | node `Transport` to a transport net | the `Transport` field | UA unique per line |
| Bit on its node | bit `IOBus` on the node's bus | the one node on the sheet; `Node` field when two | bytes declared cover bits used |
| Head device to its head | mast Value and `Head` letter, by name | same | vocabularies match (§3.6) |
| Panel column to its house | `CP Name` on the column, by name | same | names resolve |

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
- C6. The compiler's checks are the fourth column of §3.11 plus the head-vocabulary error of §3.6 and the
  node byte check of §3.5.
- C7. The three-copy experiment (all explicit, all implicit, both) is the acceptance test for milestone D;
  the "both" copy is this project.

## 7. Out of scope

A picture and words for the hosting variations the owner listed (a field processor polling its own CMRInet
nodes; a local processor as MQTT client, which Interchange now is); KiCad units for a node's bits; LCC and
other transports; Studio's own notation.
