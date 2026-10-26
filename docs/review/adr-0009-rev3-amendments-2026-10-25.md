# ADR 0009 rev 3: the amendments of ADR 0008 C11, proposed

Proposed 2026-10-25, revised the same day after the adversarial review
(`adr-0009-rev3-amendments-review-2026-10-25.md`, 15 findings, each applied below or put to the owner as a
decision). `docs/adr/0009-explicit-seams.md` stays unchanged until the owner settles each point.

ADR 0008 C11 lists the amendments; the owner called them amendments, not a new decision. Each amended rule below is
labelled by its source: **C11** (listed there), **0008** (ratified in ADR 0008 §4.5 or §8 and repeated here so the
contract is whole), **code** (what `seams.py` does and the drawing obeys, recorded), or **xref** (a cross-reference
or vocabulary correction). Nothing below has an unlabelled source.

## Decisions requested

1. **The CMRInet IC token.** The owner typed IC `CMRInet` by hand twice: in the library and on the Caltrain
   instances (Railroad `3cb51fc`, 2026-10-22 19:55), and again on the node RIO1 (`54f3fa9`, 2026-10-23). A script
   replaced the library value with `CMRI` five minutes after the first of those edits (`203bab3`). Two equal
   options:
   - (a) IC `CMRInet` on `Driver-CMRInet-Node`, `-IB` and `-OB` in the library and on every instance. Kind stays
     `CMRI` on the transport and the encoding.
   - (b) IC `CMRI` everywhere. RIO1 changes back.

   The compiler checks no node IC, so either option costs nothing in code. Each is a dated Railroad edit, and
   either one changes one value (`ic`) in the example. Recommended: (a). It is the owner's own value, entered twice,
   and C11 reads "where the drawing and the vocabulary say `CMRInet`".
2. **The Value fallback.** `name_of` still reads `Value` when a symbol has no key attribute, and reports
   `identity.value` (none on SPCoast). Default: remove the fallback. A symbol without its key is reported `missing`
   and skipped. Today `_processors`, `_transports`, `_encodings` and `_office_units` would key it by `""`, and the
   default fixes that too. `tests/test_layout_compiler.py`'s `test_a_symbol_without_name_uses_value_and_says_so` is
   inverted. ADR 0008 §4.5 loses its sentence "Where a symbol still lacks the attribute the compiler reads the Value
   and reports `identity.value`", with its own ADR 0008 §8 entry. This is a compiler change and an edit to ratified
   0008 text.
3. **The key list.** Default: §3.10 lists the key for each symbol, as ADR 0008 §8 (2026-10-25) left it: "whether
   every key should be spelled `Name` is open". How KiCad fills the key is KiCad's business. Most libraries use
   `Name = ${Value}`. The House and the drivers use the reverse (`Value = ${CP Name}`, `Value = ${Address}`).
   The CMRInet bits have no key attribute: their key is `Bit` plus the array from the pin type. ADR 0008 §4.5's
   "every symbol the compiler names carries a functionally named attribute whose content is `${Value}`" is
   corrected the same way, with an ADR 0008 §8 entry.
4. **The head device's trackplan head.** It is resolved by a name join, with no wire: the Mast device's `Name`
   equals the trackplan mast's `Name`, and the head device's `Head` equals the trackplan head's `Name`. Default:
   keep it as a table entry of its own, with "by name" as its fallback and no explicit form. As a consequence, the
   all-explicit copy of C7 cannot draw this relation as a wire. Alternative: add a wire, a pin on the head device
   to the trackplan head. That is a library change.
5. **Two §3.2 table entries that C11 does not list, now false of the libraries.** The OfficeUnit's fixed facts
   "Columns, Railroad": the library OfficeUnit has Role, Name and Style only. `Columns` was struck on 2026-10-24,
   and the Railroad facts moved to the `Railroad` symbol. Encoding-AAR "carries the topic root and Railroad": it has
   `Topic` only. Default: correct both in this rev.
6. **Cross-references and §4.** The insertion of §3.6 shifted the numbering, and about a dozen references are now
   stale (listed under xref below). One of them is in the decision text itself: §4 reads "§3.11 as its consistency
   checks", which should say §3.12. Default: correct all of them, the decision's included.
7. **Three compiler checks, recorded as rules but not enforced.** `Bit` is an integer of 1 or more
   (`bit.number`; today a non-integer `Bit` crashes the byte check). The Railroad symbol is on the root sheet. A
   macro names a non-empty Kind. Default: add the checks after ratification, and say "from 1" in the two bit
   Descriptions in the library.
8. **The glossary.** FieldUnit `docs/GLOSSARY.md` (line 138 and §4 "control point") names a field station and a
   control point by "the Value of the KiCad `MAIN HOUSE` symbol". Default: a glossary delta, `CP Name` on the
   `House`, proposed beside this rev. The owner edits the glossary.

## Record entry (for §5)

- 2026-10-25. Rev 3: the amendments of ADR 0008 C11, which the seam reader and the adversarial review of ADR 0008
  rev 4 made necessary (`docs/review/adr-0008-rev4-review-2026-10-23.md`; the owner's rulings of 2026-10-23 and
  2026-10-24, ADR 0008 §8). §3.10 states the key of each symbol with `Value` never read, Kind `RAILROAD`, the macro
  rule, model board lamps, `Kind` on an encoded driver, a Mast as a device with a row, and `anchors` as drawn
  instances. §3.5 states the bit numbering and the bit's direction. §3.12 redefines its transport entry and splits
  its head entry in two. §3.2 states the CMRInet IC token. §3.4 and §3.8 follow. The cross-references are
  corrected. The decision of §4 is unchanged except for its cross-reference and as Decisions 1 and 2 settle: one
  token in the drawing, and one fallback leaving the compiler. Railroad `6882aa6`, `d51f78e` (Name on devices,
  the office unit and the encodings; Kind on the JMRI drivers), `a953197`, `1dce092` (ModelLamp), `d52017c`,
  `21536f1` (the Railroad symbol and the macro), `b309d9a`, `a3642e4`.

## The amended rules

### §3.2, symbols

- `Driver-CMRInet-Node` entry, fixed facts (**C11**; the token per Decision 1): "Role `IODRIVER`, IC `CMRInet`
  (option a) or `CMRI` (option b); NodeType, Address (the UA), InputBytes, OutputBytes."
- `OfficeUnit` entry, fixed facts (**Decision 5**): "Role `OFFICE_UNIT`; Style `US&S`; Name."
- `Encoding-AAR` entry (**Decision 5**): "AAR carries the topic root (`Topic`)."
- "`Name` (§3.9)" and "`CP Name` (§3.9)" become "(§3.10)" (**xref**).

### §3.4, transports

"A transport instance is connected to a processor through its `Processor` pin, and a given transport may be placed
once per processor that runs an encoding on it (§3.9)" (**0008** §4.5, §4.9; was "that connects to it (§3.8)").

### §3.5, CMRInet: added after "`Driver-CMRInet-IB` and `-OB` represent individual bits"

> A bit's position is its `Bit` field, numbered from 1 within its array. Its array is read from the type of the bit
> symbol's `D` pin: an input pin is an `IB` bit, an output pin an `OB` bit. A bit is written `IB.n` or `OB.n`.
> (**C11**; the check is Decision 7)

### §3.8, stations

"one per house on a US&S 506 line, addressed by the house's desk column number (the `PanelColumn`'s `Column`,
whose `CP Name` names its house)" (**C11**, `Value` never read; was "the `PanelColumn` Value").

### §3.10, keys the compiler reads

Rewritten as one list. Each entry is labelled.

> - **The key of each symbol the compiler names** (**C11**, **0008**; Decision 3):
>   - `Name` on the Railroad symbol, an Interlocking, a processor, a transport, an encoding, an OfficeUnit, a
>     Milepost, and every device and trackplan appliance that has a railroad name;
>   - `CP Name` on a House, and `Column` on a PanelColumn;
>   - `Address` on a driver or a CMRInet Node;
>   - `Bit` and the pin type on a CMRInet bit;
>   - `Head` on a head device, beside the Mast it is wired to.
>
>   A panel lamp is keyed by what it shows (`IndicationToken`), and its `Name` is a label. The code lever has no key.
>   How KiCad fills a key is KiCad's business: `Name = ${Value}` on most symbols, the reverse
>   (`Value = ${CP Name}`, `Value = ${Address}`) on the House and the drivers. `Reference` and `Value` are never read.
> - `IC` on a driver or a CMRInet Node (unchanged).
> - **An encoded driver** (a JMRI object) has no address (**C11**). `Kind` is its object class (`TURNOUT`,
>   `SENSOR`, `SIGNALMAST`, `LIGHT`), and its key is `<Kind>.<served device's Name>` (`TURNOUT.777`). Two symbols
>   with one key are one driver: a Turnout's command and its feedback. A drawn `Address` overrides the key, and the
>   compiler reports it at info (**0008** §4.5).
> - `Role`: the list is unchanged. Under it (**C11**): `PANEL` covers the model board lamps. A `ModelLamp-*` is a
>   PANEL device of Style `board` with no `Column` pin. It is in no column and shows the indications its
>   `IndicationToken` names (**code**).
> - `Kind`: the list is unchanged, plus `RAILROAD` under `STRUCTURE` (**C11**). That is one symbol per project,
>   placed on the root sheet (the check is Decision 7), carrying the layout's `Name`, `Railroad`, `Region`, `Era`
>   and `Rulebook`. Roles that classify by `Appliance` and `Style` carry no Kind. An encoded `IODRIVER` carries one
>   (above).
> - **The macro** `<ROLE:KIND:Field>` (**C11**). A field may name another symbol's field this way. The compiler
>   expands it against the one symbol of that Role and Kind in scope (on the sheet or an ancestor). No such symbol,
>   two of them, or a missing field is a compiler error (`macro.scope`, `macro.field`). The Layout Data Model File
>   carries the expanded value.
> - **A Mast is a device** (**C11**). Every `DEVICE` symbol of Appliance `mast` is a device row, with its `IND`
>   binding when a driver takes the whole mast.
> - **`anchors` are the drawn instances** (**C11**). Each placed `Transport-*` symbol names the processor that runs
>   an encoding on it, by its `Processor` wire, or else its `Processor` field, or else, for a code line transport,
>   the OfficeUnit's processor. Those processors are the transport's anchors, and no others. The compiler does not
>   check that an anchor runs an encoding. When a FieldUnit's processor anchors no instance of its code line's
>   transport, the FieldUnit reaches that transport through the code line, and the compiler reports the
>   reach at info.
> - `Style` and `Topic`: unchanged.
> - Library defaults (**code**): the names of processors, interlockings, office units and houses, and the
>   addresses of drivers, are empty by default, so the compiler's `missing` report is the tutorial prompt.
>   Transports and encodings default to their kind's name (`MQTT`, `AAR Tokens`). Some panel and track symbols
>   carry placeholders (`COLUMN#`, `##.#`), which the owner replaces when placing them. Fixed facts (Role, Kind,
>   Style, a topic template) keep their defaults. (Was "Library defaults for names, hosts and transports are empty",
>   which is false of the libraries.)

### §3.11, vocabulary

"IC `MQTT-JMRI` on JMRI drivers, with `Kind` their object class (§3.10)" (**xref**; was "Kind `MQTT-JMRI` on JMRI
drivers IC").

### §3.12, the relation table

| Relation | Explicit | Implicit fallback | Check |
|---|---|---|---|
| Transport anchored on | Transport `Processor` to a Processor | the `Processor` field; the OfficeUnit's processor for a code line transport (§3.4) | each instance has one anchor; a FieldUnit whose processor anchors no instance of its code line's transport reaches it through the code line (info) |
| Head device to its mast | its `IND` wire to a Mast device | none | one Mast on the `IND` net |
| Head device to its trackplan head | none (Decision 4) | the Mast device's `Name` and the `Head` letter, by name, to the trackplan mast's `Name` and its head's `Name` | the trackplan draws that head (`head.plan`); the vocabularies match (§3.7) |

Sources: the transport entry is **C11**, with **xref** "(0005 S3)" changed to "(§3.4)" and "the machine's processor"
changed to "the OfficeUnit's processor". The two head entries are **C11** "`IND` wire to a Mast device" and
**code** for the name join, which replaces "mast Value and `Head` letter, by name | same | vocabularies match
(§3.6)". The checks are what `_transports`, `_reach`, `_devices` and `_heads` do.

### Cross-references (**xref**, Decision 6)

- §4: "§3.11 as its consistency checks" becomes §3.12.
- C6: "the fourth column of §3.11" becomes §3.12, and "the head-vocabulary error of §3.6" becomes §3.7.
- C1: "superseded by §3.5, §3.4 and §3.8" becomes "§3.5, §3.4 and §3.9".
- C2: "`CP Name` (§3.9)" becomes §3.10, and "D13 … by §3.7" becomes §3.8.
- §3.4: "(§3.8)" becomes §3.9.
- §3.12, the head entry: "(§3.6)" becomes §3.7.

## What was checked

Against the drawing at Railroad `7ecb9d9` (the netlist exported by the owner 2026-10-25 22:25, newer than every
sheet and library) and `tools/layout_compiler/seams.py` on Subdivision `feat/trackplan-semantics`. The review
checked the same facts at `a3642e4`, and none of them depends on the Watsonville mast renamed between the two.

- One Railroad symbol, RAILROAD1 on `/`. The macro reports `macro.scope` or `macro.field`.
- `ModelLamp-AMBER`, `-BLUE`, `-GREEN`, `-RED` and `-YELLOW` are PANEL, Style `board`, and have one pin `~{LAMP}`.
  `_devices` asks for no column.
- Keys: 0 `identity.value` on the project. The key direction per library is as listed in Decision 3.
- 14 JMRI drivers are keyed `<Kind>.<name>`, with the two Turnouts merged from command and feedback.
- 38 Mast rows of 268 rows. Six `transport.reach` infos.
- IB bits run 1 to 14 (InputBytes 2) and OB bits 1 to 20 (OutputBytes 3). The direction comes from the `D` pin
  type.
- CMRInet: Transport-CMRInet and Encoding-CMRInet carry Kind `CMRI`, and the node and bit libraries carry IC
  `CMRI`. RIO1 on `/South-cTc/` carries IC `CMRInet`, and its 34 bits carry `CMRI`. The example writes
  `"ic": "CMRInet"` once.
