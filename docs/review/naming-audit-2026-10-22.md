# Naming audit, 2026-10-22

An independent, adversarial audit of the names in the KiCad symbol libraries, the SPCoast sheet ports and net
labels, and the layout-model schema, against the vocabulary sources of truth in their order of authority:
FieldUnit `docs/GLOSSARY.md`, FieldUnit ADR 0005 (cTc interface layers), then this repository's ADRs 0001, 0004,
0005, 0008 and `docs/archive/vocabulary-review.md`. The auditor was given the drawing's design facts as settled
(transports serve either seam; Host wires end on processors, Codeline wires on a transport net; the four unit
ports; remote I/O is an attachment, not a processor; node / topic / station are address vocabularies) and asked
to audit the names only, as one list, no narrative. The report is reproduced verbatim below; the architect's
assessment of each finding is in the session record and will land in the ADRs the owner ratifies.

Railroad project state audited: branch `feat/deployment-cases` at `6f22a0f`.

---

## 1. FINDINGS (most severe first)

Paths: GL = `~/Dropbox/Arduino/libraries/FieldUnit/docs/GLOSSARY.md`; SYM = `~/Dropbox/KiCad/Railroad/symbols/`; SCH = `~/Dropbox/KiCad/Railroad/SPCoast/`; SCHEMA = `FieldUnit-Subdivision/schemas/layout-model/v2.0.0.json`; EX = `.../examples/spcoast-excerpt.json`.

| # | Where | Current | Vocabulary says | Problem | Proposed | Sev |
|---|---|---|---|---|---|---|
| 1 | SYM Trackplan `Interlocking` pin, Office `OfficeUnit` pin, HardwareIO `Processor` pin, `Codeline-Transport-*` pin+field; SCH port `Host`; SCHEMA `unit.host`, `transport.host`; EX processors `CMRI Host`, `JMRI Host`, `Plant Host` | `Host` | GL §11: "host, plant host, node (for a computer that runs field units) → field processor"; `docs/archive/vocabulary-review.md` §"Field unit, plant, and field processor": "'Host' is rejected: C/MRI and JMRI already use it with other meanings" | A retired, explicitly rejected word is the main port of every unit, a transport field, three schema keys and three processor names | pin/port `Processor`; schema `fieldUnit.processor`, `transport.processor` (or `poller`) | blocker |
| 2 | SYM HardwareIO `Remote-IO-*` descriptions ("one node"), SCHEMA `processor` ("when it is a node"), ADR 0008 §4.9/§5, EX `processors.Caltrain/JMRI` | node = a processor | GL §11 retires "node"; brief's design fact: remote I/O is an attachment, not a processor; ADR 0005 A8 says the opposite ("a CMRInet node is a processor that hosts nothing") | Library (`REMOTE_IO`) and schema (`processors{}` with `transport`+`address`) disagree on what a remote I/O is; schema has no key for it | SCHEMA `layout.remoteIO{}` (kind, transport, address, nodeType, bytes); drop `processor.transport/address/side` | blocker |
| 3 | SYM `OfficeUnit` (Reference/Role `MACHINE`, description "dispatcher cTc machine"); SCHEMA `machines{}.officeUnit`, `$unit` ("office unit of a machine") | `OfficeUnit` / `officeUnit` | GL §3 CTC machine: "`OfficeUnit` [is an alias]. Prose uses 'CTC machine'"; GL §2.4: "That application on a processor is a CTC machine" | "office unit" is undefined; the glossary's noun for the running office application is the CTC machine itself, so `machine` and `officeUnit` name one thing twice | symbol `CTC-Machine`; schema `machines{}.processor` (no `officeUnit`) | should-fix |
| 4 | SCHEMA `$codelineInstance`, `interlocking.codelines[]` (EX `address: "Corporal"`) | `codelines[]` | GL §3 field station: "One address on a code line"; ADR 0001 D13 "Field stations are drawn as encoding instances" | The glossary's own term is hidden behind "codeline instance" | `interlocking.fieldStations[]` {codeline, address} | should-fix |
| 5 | SCHEMA `machine.attachments[]` vs ADR 0005 S1 ("A thing on the bus is an attachment") and `Remote-IO-*` | `attachments` | ADR 0005 S1 | Overload: a machine–interlocking–codeline triple and a device-on-a-bus share one word | machine `fieldStations[]`/`served[]`; keep "attachment" for Seam 2 | should-fix |
| 6 | SYM `Codeline-Transport-*`: pin `Host` AND field `Host`; `Remote-IO-*`: pin `Transport` AND field `Transport`; SCH all instances field empty | pin + field | ADR 0005 S3 "`Host` is a field of the transport"; A1 one source | One fact, two sources; which wins is undefined | wire only; delete the fields | should-fix |
| 7 | SYM `MAIN HOUSE` Value `CP ${CP Name}` (Luchessa) vs `${CP Name}` (Watsonville); EX controlPoints `CP Luchessa` vs `Sargent` | `CP ` prefix | ADR 0001 D12 "A KiCad name never contains `CP_` or `CP `"; GL §11 "CP (as a common noun) → control point" | Prefix survives on three of seven sheets and in the example; field is named `CP Name` | field `Control Point`; Values bare | should-fix |
| 8 | SYM `Processor` pin `IO_Bus` vs every driver pin `IOBus`, Panel sheet pin `IOBus`, unit port `OfficeIOBus` | `IO_Bus` | GL §3 device interface: code names `IOBus` | Same bus, three spellings; the panel column's bus is `OfficeIOBus` outside the Panel sheet and `IOBus` inside | `IOBus` everywhere; `PanelIOBus` for the office side (FieldUnit ADR 0005 SVG: "PANEL I/O") | should-fix |
| 9 | SYM `Codeline-Transport-Loconet` pin `Encoding`; all other transports pin `Transport` | `Encoding` | ADR 0001 D15 (old name) | Stale asymmetry; also "Loconet" vs ADR 0005 "LocoNet" | `Transport`, `LocoNet` | should-fix |
| 10 | SYM `OfficeUnit` field `Type` = `US&S506`; SCHEMA `machine.panelStyle` ("US&S 506 lever panel") | `Type`/`US&S506` | GL §11: "Model 506, Type 506 machine, US&S506 machine → the SPCoast CTC machine (US&S style)" | Retired term as a default value; symbol field and schema key differ | field `Style` = `US&S`; schema `style` | should-fix |
| 11 | SYM `Remote-IO-CMRInet` field `Board` = `C` vs `Processor` field `Board` = `cpNode-Xiao` | `Board` | ADR 0008 §4.7 board = reference-data key | Overload: node-type letter vs board key | `NodeType` | should-fix |
| 12 | JMRI naming: Kind `MQTT-JMRI`, Reference/label `JMRI_MQTT`, Value `JMRI`, driver `IC`=`MQTT`, EX chip `JMRI/MQTT` ic `JMRI` | five spellings | FieldUnit ADR 0005 SVG: transport `MQTT`, remote I/O adapter per transport | One attachment kind, five names | Kind `JMRI`, transport `MQTT` (the topic root distinguishes lines) | should-fix |
| 13 | SYM drivers field `IC` = `CMRI`, `MQTT`, `GPIO`; SCHEMA `chip.ic` "CMRI (a node's bits)" | `IC` | FieldUnit ADR 0003 D10: Kind = chip | A transport is not an integrated circuit | `Kind` | should-fix |
| 14 | SYM `Codeline-Transport-MQTT` Topic `ctc/${Railroad}/codeline/` vs FieldUnit ADR 0001 `/layout/<layoutname>/codeline/` | topic root | FieldUnit ADR 0001 | Library default and rank-2 source disagree; `Railroad` is also on `OfficeUnit` (ADR 0001 open item 5) | one source | should-fix |
| 15 | SYM `Interlocking` Value `${TITLE}`, `Name` `${Value}`; Reference `Plant` | title-block name | GL §3 field station: tooling "does not take it from the title block"; §11 "plant (alone)" retired | Hidden source via KiCad variable; retired reference prefix | Value typed; Reference `IXL` | should-fix |
| 16 | SYM `MAIN HOUSE` pins `H`, `Codeline` | `H`, `Codeline` | ADR 0001 D15: stations are encoding instances; GL §11 house → bungalow | `H` undefined; a second code line attach point on a control point symbol; retired word in symbol name | `Bungalow`, pin `Track`; drop `Codeline` | should-fix |
| 17 | SCH labels `MQTT`, `TIMECODE`, `CMRInet`, `JMRI_MQTT`; Values `MQTT`, `Time Coded`, `CMRInet`; Kinds `MQTT`, `TIMECODE`, `CMRI`; symbol `TimeCode` | four spellings of time code; two of CMRI | GL §6 "US&S 506 time code" | Label, Value, Kind and symbol spell one transport four ways | `TimeCode` / `CMRInet` throughout | nit |
| 18 | SYM/EX board keys `MacOS`, `macOS app`, `cpNode-Xiao`, `cpNode Xiao`, `cpNode` | — | ADR 0008 §4.7 reference keys | Inconsistent keys for one board | one key form | nit |
| 19 | EX `codelines` key `AAR Tokens@MQTT`; chip keys `0x40/pwm`, `Caltrain/CMRI` | `@`, `/` composites | ADR 0008 §4.5: name = scope `:` key | Invented separators; code line name rule undefined | document or name lines (`MQTT line`) | nit |
| 20 | SYM Field `Mast`, `Local-*`, `Cast-*` vs `Device-*` | `Mast` | — | Device symbols not uniformly prefixed; `Local-Switch` description copied from `PanelSwitch` ("dispatcher-controlled", "plant sheet") | `Device-Mast`, fix text | nit |
| 21 | SYM Office `Driver-I2C-MAX7313-SPCoastcTc`; SCH `South-cTc`; `OfficeUnit` description "cTc" | `cTc` | GL §11 "cTc → CTC" | Retired spelling in names | `CTC` | nit |
| 22 | SYM `Codeline-Encoding-Bits` field `Station`; SCH Processor `JohnCTC`, `Gilroy` (Interchange's processor) vs control point `Gilroy` in Luchessa | — | GL §11 "station → field station" | Retired word; personal and colliding processor names | `FieldStation`; `Gilroy Interchange` | nit |
| 23 | SCH `South-cTc` sheet pin `Codeline` is `input` on one sheet, `bidirectional` on six; `Setting` pin `net` | — | ADR 0005 A3 | KiCad electrical-type and net-vocabulary leaks | bidirectional; `Scope` | nit |

## 2. UNDEFINED TERMS (absent from GLOSSARY)

host (retired, in use), processor (generic; only "field processor" is defined), transport, attachment, node (retired, in use), port, bus, chip, driver, cast, column (only "panel column"), machine (only "CTC machine"), office unit, remote I/O, local I/O, adapter, board, seam, "Codeline" as a pin word (GL §11 retires `CodeLine` in prose in favor of "code line"), `OFFICE_IO` (named in the brief; found nowhere in SCH).

## 3. STORYLINE CHECK

I draw an interlocking plant on its own sheet and name it with the Interlocking symbol. I place one bungalow per control point and give it the control point name. I attach the interlocking to a code line by wiring its code line port to the transport that carries that line, and on a 506 line I add one field station per control point with its authored address. I say where its logic runs by wiring it to a field processor. I put its field I/O on that processor's device interface, or on a remote I/O attachment to a transport. I put its panel column on the CTC machine's panel I/O. I give the CTC machine its code lines and its processor.

Differences the user sees: "interlocking plant" → `Interlocking` (Reference `Plant`, Value `${TITLE}`); "bungalow"/"control point" → `MAIN HOUSE` / `CP Name`; "code line" → `Codeline`; "field station" → `Codeline-Encoding-*` with `Station`/`Address`, schema `codelines[]`; "field processor" → `Processor` reached by `Host`; "device interface" → `IOBus`/`IO_Bus`; "remote I/O attachment" → `Remote-IO-*` (schema: a processor); "CTC machine" → `OfficeUnit`/`MACHINE`/`SPCoast South`; "panel I/O" → `OfficeIOBus`.

## 4. SPELLING/STYLE CONVENTIONS

- Role/Kind: UPPER_SNAKE (`CONTROL_POINT`, `CODELINE_TRANSPORT`); exceptions `MQTT-JMRI`, `USS506`.
- Style: lower_snake (`manual_sensed`, `non_vital`); exceptions head styles UPPER (`CL`, `CPL`, `LQ`, `UQ`).
- Pins: CamelCase (`Codeline`, `Host`, `IOBus`, `Transport`, `Column`), tokens UPPER with `~{X}`; exceptions `IO_Bus`, `net`, `H`, `EoT`.
- Fields: CamelCase (`InputBytes`, `IndicationToken`); settings lower_snake (`settle_ms`, `frequency_hz`); one with a space (`CP Name`); Value templates mix `${VALUE}`, `${Value}`, `${ADDRESS}`, `${Address}`.
- Symbol names: `Family-Variant` hyphens (Office, Field, HardwareIO) vs `Family_Variant` underscores and spaces (Trackplan: `Switch_Powered`, `MAIN HOUSE`, `Track Circuit`, `Signal Head - CL`, `IRJ-END_CTC`).
- Labels: UPPER (`MQTT`, `TIMECODE`), product case (`CMRInet`), snake (`JMRI_MQTT`).
- Schema: camelCase keys; values with spaces (`CMRI Host`, `cpNode Xiao`); composite keys with `@`, `/`, `:`.
