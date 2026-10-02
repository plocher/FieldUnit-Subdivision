# Symbol contract: what each KiCad symbol records

- Status: proposal for owner review (2026-10-02). Not committed. No library, schematic or code is changed.
- Terms: FieldUnit `docs/GLOSSARY.md`; ADR 0001 (D1–D16, amended 2026-10-02); `vocabulary-review.md`
  iterations 9–11; `ontology.md` rev 5; `layout-model.md` rev 8; `desk-codeline-kicad-pattern.md`.
- Evidence: the two libraries (read with `SymbolLibraryReader`) and the netlists of Luchessa, Sargent,
  GilroyInterchange, Christopher, Corporal, GilroyCalTrain and South-cTc (read with `NetlistReader`).
  The Watsonville project and the Watsonville sheet of South-cTc are excluded. Christopher, Corporal
  and GilroyCalTrain have components but no nets, so they give field values only.
- "(unverified)" marks a statement that no opened source supports.

## 1. Purpose and storyline

1. Draw each interlocking and the CTC machine in KiCad.
2. The compiler and linker read the drawings and make one model.
3. The generator reads the model and emits one interlocking application for each interlocking and one CTC machine application.
4. The applications run on field processors and on the CTC machine: first virtual, then AAR tokens over MQTT.
5. This document states, for each symbol, the facts that step 2 must read so that step 3 can emit step 4. Everything else leaves the symbol.

## 2. Principles for a field

| # | Principle | Test |
|---|---|---|
| P1 | One fact, one place. | If two fields (or a field and a pin connection, a sheet name or a title block) record one fact, one of them goes. |
| P2 | A phase reads it. | The compiler, the linker or the generator reads the field. If no phase reads it, it goes, or it becomes documentation in the symbol description. |
| P3 | Names, not policy. | A field records a drawn fact (a name, a membership, an authored address). It does not record what the generator must do (a topic pattern, a token spelling, a target). The generator owns policy (ADR D6). |
| P4 | Library facts stay in the library. | A fact that is the same for every instance of a symbol (`Role`, `Kind`, `Color`, `BusKind`, `Direction` on a one-direction marker) is read from the library by `lib_id`. The copy that KiCad puts in each instance is not read. A copy that differs from the library is a warning ("update symbol from library"). |
| P5 | Instance facts have an empty default. | A name, a membership or an address has an empty library default, so a missing value is found. Placeholders (`XX`, `FIXME`, `COLUMN#`, `79.0`, `S`, `Luchessa`) go. |
| P6 | Connections are pins. | A membership that can be drawn as a pin connection is read from the netlist, not from a name field (AGENTS.md). |
| P7 | Code names versus prose terms. | A field name, a Role or a Kind is a code name. It keeps its spelling when the prose term differs, unless its meaning changed or it uses a retired term. Names in values have no `CP ` or `CP_` prefix (D12). A name used in a topic or a key has each space replaced by `-`; that is the only normalization. |

Finding behind P4. Instance copies of `Role` and `Kind` already disagree with the library in 15 symbols:
Sargent 1, GilroyInterchange 2, Christopher 4, Corporal 2, GilroyCalTrain 5, South-cTc 1. Examples:
`Mast_Double` with `Kind` = `MAST_DWARF` (GilroyInterchange S3, S4); `Switch_HandThrow` with `Kind` =
`SWITCH_POWERED` (Sargent SW3, Corporal SW901); `PanelLock` 795 with `Kind` = `SWITCH_LEVER` (South-cTc
SW796). The controller compiler reads the instance `Kind`, so it treats lock lever 795 as a switch lever
today. The plant compiler reads neither; it classifies by symbol name (`_PART_KIND`).

## 3. Plant library (`Railroad.kicad_sym`)

29 symbols, 114 field slots, 11 field names (`CP`, `Direction`, `Head`, `Indication`, `Kind`,
`Milepost`, `Name`, `Role`, `Signal`, `TC`, `Value`). Instances also carry `Rulebook` (Luchessa, 5),
`Indications` (none drawn; the compiler reads it) and stray `Direction`/`Name` (GilroyInterchange, 27
and 29).

Readers today: `plant_graph/compiler.py` (C), `plant_graph/model.py` (M), `plant_graph/routes.py` (R),
`plant_graph/indications.py` (I), `plant_graph/picture.py` (P), `link/linker.py` (L).

### 3.1 Fields common to every plant symbol

| Field | Today | Proposed | Fact | Phase |
|---|---|---|---|---|
| `Role` | library value on all 29; no plant reader (C classifies by symbol name) | keep; read from the library (P4). Rename value `CONTROLLED_POINT` → `CONTROL_POINT` (retired term) | what the compiler does with the Value and pins | compiler |
| `Kind` | library value on 27; no plant reader | keep; read from the library; the compiler classifies by `Kind`, and `_PART_KIND` goes | the FieldUnit class, or the variant that changes derivation | compiler |
| `Value` | per symbol; read by C | keep; meaning per family below; library default empty (P5) | the railroad name | compiler |

### 3.2 `MAIN HOUSE`

Pins: 1 `H`. In Luchessa, Sargent and GilroyInterchange pin `H` connects to the `MaintainerCall` pin.

| Field | Today: default · reader | Proposed | Fact | Phase |
|---|---|---|---|---|
| `Value` | empty · C, M (control point list, board order) | keep. Bare name (`Luchessa`, `Gilroy`, `Carnadero`). May display a title block variable (`${COMMENTx}`). No `MAIN HOUSE` in a plant project: error | the control point and its bungalow; on a 506-style encoding also the field station name | compiler, generator |
| `Role` | `CONTROLLED_POINT` · none | rename value → `CONTROL_POINT` | (P7) | compiler |
| `Milepost` | `79.0` · none. Luchessa has `79.0` on all three (the default, never set); Sargent, Corporal `FIXME` | keep, default empty; the compiler reads it to put `controlPoints[]` in geographic order (`layout-model.md` §1) instead of the x coordinate. Owner to confirm (Q7) | the location of the control point | compiler |

### 3.3 Switches: `Switch_Powered`, `Switch_Powered_Small`, `Switch_Powered_NO_TC`, `Switch_Lock`, `Switch_HandThrow`

Pins: 1 `C`, 2 `N`, 3 `R`. `Kind`: `SWITCH_POWERED` (three symbols), `SWITCH_LOCK`, `SWITCH_MANUAL`.
`Switch_Powered_Small`, `Switch_Powered_NO_TC` and `Switch_HandThrow` are not in `_PART_KIND`; the
compiler rejects them today (GilroyCalTrain 2, Sargent 1, Corporal 1).

| Field | Today: default · reader | Proposed | Fact | Phase |
|---|---|---|---|---|
| `Value` | empty · C | keep: switch number (`783`) | switch name; lever and tokens match it | compiler, linker, generator |
| `CP` | empty · C (checks), M (members), C (board section) | keep. Bare control point name | control point of the switch in the field (control point limits) | compiler; generator (model board; later the hardware sheet) |
| `TC` | `${VALUE}T1` (empty on `NO_TC`, `HandThrow`) · C, R | keep. Exactly one name, or empty for no OS circuit. A list is not allowed (GilroyCalTrain 771 has `771T1, 773T1, 775T1`; Q13) | the OS track circuit that detector-locks the switch | compiler, generator |
| `Indications` | not in library; none drawn · C, I | add to the library as `IndicationCeiling`, default empty. Form `NORMAL/REVERSE`, e.g. `CLEAR/APPROACH` | the most favorable signal indication over the switch in each position (glossary "indication ceiling") | compiler (route `bestIndication`) |

Variants that differ only in a field default or in graphics keep one `Kind`. Removing them is optional.

### 3.4 Derails: `Switch_Powered_Derail`, `Switch_Powered_Derail_TC`

Pins: 1 `C`, 2 `R` (through path = REVERSE; verified in the library). `Kind` = `DERAIL` on both.
`Switch_Powered_Derail_TC` is not in `_PART_KIND` and is not drawn.

| Field | Today: default · reader | Proposed | Fact | Phase |
|---|---|---|---|---|
| `Value` | empty · C | keep: `<switch>D` (dependent) or its own number (independent) | derail name; dependency on its switch | compiler |
| `CP` | empty · C (mismatch warning) | keep for an independent derail. Empty for a dependent derail: the compiler takes the switch's control point (P1). A value that differs is an error | control point of the derail | compiler |
| `TC` | empty / `${VALUE}T1` · C | keep; same rule as switches | own track circuit, if any | compiler |

`Switch_Powered_Derail_TC` only changes the `TC` default. Remove it, or keep it as a convenience (optional).

### 3.5 Track circuits: `Track Circuit`, `Track Circuit_Yellow`

Pins: 1 named `MC`. `Kind` = `TRACK_CIRCUIT` on both. `Track Circuit_Yellow` is not in `_PART_KIND`
(GilroyCalTrain uses it 3 times). The difference between the two is graphics only (unverified).

| Field | Today: default · reader | Proposed | Fact | Phase |
|---|---|---|---|---|
| `Value` | empty · C | keep: circuit name (`1NA`), the authoritative name. A foreign circuit uses the proxy form `<interlocking>:<name>` (Sargent `Corporal:2NA`) | track circuit; or a reference to a circuit of another interlocking | compiler; generator (a foreign interlocking: listen on the code line; the same interlocking: local) |
| `CP` | empty · C, M | keep. Empty for a proxy: the circuit is not in this interlocking (Sargent TC4 has `Corporal`) | control point of the circuit | compiler |
| pin 1 name | `MC` | rename the pin name to `T` (number stays 1; the compiler reads numbers) | none (the name misleads) | none |

### 3.6 Signals: `Mast_Single`, `Mast_Double`, `Mast_Dwarf`, `Signal Head - CL`, `Signal Head - SemaphoreU2`, `Signal Head - SemaphoreU3`, `IRJ-Signal`

Pins: masts 1 `SIGNAL` plus head pins (`H` or `H1`, `H2`); heads 1 `M`; `IRJ-Signal` 1 `A`, 2 `B`, 3
`SIGNAL`. The two semaphore heads are not in `_PART_KIND` and are not drawn.

| Symbol · field | Today: default · reader | Proposed | Fact | Phase |
|---|---|---|---|---|
| Mast `Value` | empty · C, R | keep: `^\d+[NSEW][A-E]+$` (`784EAB`) | mast name; signal number; direction (N/W = LEFT, S/E = RIGHT); its heads | compiler |
| Mast `CP` | not in library. Drawn on 6 masts (GilroyInterchange 2, Christopher 4); not read | add to the library, default empty; the compiler reads it (`layout-model.md` §1: "controlPoint: the mast's drawn CP field") | control point of the mast in the field | compiler |
| `IRJ-Signal` `CP` | empty · M (the only source of a mast's control point today), C (check) | remove after the mast `CP` is filled (P1). The IRJ is `TRACK`; it has no railroad name | (moves to the mast) | none |
| Head `Value` | empty · C | keep: one letter A–E. The compiler checks that the letters of the heads on a mast equal the letters in the mast Value (unverified that it checks today) | head letter | compiler |

### 3.7 Track terminals: `IRJ`, `Bumper`, `NextCP`

| Symbol · field | Today: default · reader | Proposed | Fact | Phase |
|---|---|---|---|---|
| `IRJ`, `Bumper` | `Value`, `Role`, `Kind` only · C (by reference) | keep; no instance fields. Remove the stray instance `CP` (GilroyCalTrain bumpers 3) and `Direction`/`Name` (GilroyInterchange) | a track graph edge or end | compiler |
| `NextCP` `Value` | empty · R (terminal designation) | keep. Bare name of the neighbor interlocking (`Christopher`, not `CP Christopher`). Owner to confirm interlocking versus control point (Q9). Rename `Kind` `NEXT_CP` → `NEXT_INTERLOCKING` and the symbol to match (optional; the term "CP" is not a common noun) | the neighbor across this plant edge | compiler; linker (subdivision topology); generator (proxy listening; train progression) |

### 3.8 Policy markers: `Rule251-DoT-Left`, `Rule251-DoT-Right`, `Rule261-DoT-BiDirectional`, `Rule6.13-Yard Limits`, `Rule6.28-OtherThanMain`

Today the `Kind` names mix Standard Code rule numbers (251, 261) with GCOR-style numbers (6.13, 6.28).
The compiler reads `Rulebook` (not in the library) and `Direction`. It finds dark track by
`Rulebook` starting with `6.28`. Only Luchessa instances have `Rulebook`, so the other five projects
fail `missing_policy_rulebook` today. `Rule6.13-Yard Limits` is not in `_PART_KIND`.

| Field | Today: default · reader | Proposed | Fact | Phase |
|---|---|---|---|---|
| `Kind` | `RULE_251`, `RULE_261`, `RULE_6.13`, `RULE_6.28` · none | rename to the meaning, not a rule number: `SIGNALED_ONE_DIRECTION`, `SIGNALED_BOTH_DIRECTIONS`, `YARD_LIMITS`, `NOT_SIGNALED` (other than main track, dark). The compiler reads `Kind` (Q12) | the operating method of the track at the marker | compiler |
| `Rulebook` | instance only (Luchessa 5: `251`, `261`, `Rule 6.28`) · C, R, P | remove (P1: `Kind` records it). The description may cite rule numbers as documentation | (in `Kind`) | none |
| `Name` | prose (`Track Signaled in One Direction`); on Left, 6.13, 6.28, not Right · none | remove (P2). Prose goes in the description | none | none |
| `Direction` | `LEFT`, `RIGHT`, `BOTH` · C (required on every marker) | keep on the one-direction markers only (library fact, P4). Remove from the others: `BOTH` is implied by `Kind` | the direction of traffic on one-direction track | compiler |
| `Value` | `RULE 251`, `Rule 261`, `YARD`, `DARK` · C ("track-name Value") | keep: the track name (`MT1`, `Branch`). Library default empty (P5); the defaults are labels, not names | the track name | compiler |

### 3.9 `Route`

Fields `Signal`, `Head`, `Indication` (`CLEAR`), `Kind` = `ROUTE_INDICATION`. No reader. Not drawn.
Proposed: remove the symbol. `IndicationCeiling` on switches (§3.3) gives the authored input to
`bestIndication`. Keep it only if a route-level override is needed (Q8).

### 3.10 `MaintainerCall` and `AUXILIARY`

Pins: 1 named `MC` on both. Today `MaintainerCall` is in `_PART_KIND` but no phase puts it in the model
(known gap; `setupCodec()` hard-codes the calls). `AUXILIARY` is not in `_PART_KIND` and is not drawn.

| Symbol · field | Today: default · reader | Proposed | Fact | Phase |
|---|---|---|---|---|
| `MaintainerCall` `Value` | empty · C (name only) | keep: `MC<n>`, unique in the interlocking. Required (Luchessa MC1 has `~`) | the call's name; functions `MC<n>S`, `MC<n>K` | compiler, linker, generator |
| `MaintainerCall` `CP` | not in library; drawn on 4 (GilroyInterchange 2, Christopher 2) · none | do not add. The control point is the `MAIN HOUSE` its pin connects to (P6). Remove the 4 instance fields | the bungalow the maintainer is called to | compiler |
| `MaintainerCall` class | none | no field: a maintainer call is always a second-class control (iteration 11) | (by `Kind`) | generator |
| `AUXILIARY` `Value` | empty · none | keep: the appliance name (switch heater, bungalow door) | auxiliary appliance name | compiler, linker, generator |
| `AUXILIARY` control point | none | pin connection to `MAIN HOUSE` pin `H` (P6); rename pin name `MC` → `H` | the bungalow of the appliance | compiler |
| `AUXILIARY` `<ControlClass>` | none (the class is on the panel symbols today) | add, placeholder name `ControlClass`; values open: `INTERLOCKED`/`AUXILIARY` or `VITAL`/`NON_VITAL` (Q2). See §4.7 for why it moves here (Q3) | how the field unit processes the control: first class (rejected as a group when one is unsafe) or second class (processed anyway) | generator (interlocking application) |
| `AUXILIARY` `Functions` | none | add: `CONTROL`, `INDICATION`, or `CONTROL,INDICATION` (proposal) | which functions exist; their names are `<Value>S`, `<Value>K` | generator; linker (lever and lamp cross-check) |

Finding: the drawn pin connection already records the bungalow of every connected call, and it agrees
with the instance `CP` where both exist (GilroyInterchange MC1, MC2). Luchessa MC1 connects to `CP
Luchessa`; its panel lever and lamp are in column 6 (`CP Gilroy`). By D3 this is not an error.

### 3.11 `Milepost`

`Value` = `##.#`, `Role` = `ANNOTATION`. Entity made by C; no reader. Keep as documentation; default
empty. No phase reads it.

### 3.12 Plant hardware sheet (planned, not designed here)

`desk-codeline-kicad-pattern.md` §5a plans a second top-level sheet with a field unit symbol, field
I/O proxies and IODRIVER symbols. Head type (color light, semaphore) belongs there, as field I/O. Not in
scope.

## 4. Panel library (`RailroadPanel.kicad_sym`)

14 symbols, 62 field slots, 21 field names. Readers today: `controller_graph/compiler.py` (CC) and
`link/linker.py` (L). CC reads `Role`, `Kind`, `Columns`, `Type`, `CP Name`, `Station`, `Broker`,
`TopicRoot`, `Topic`, `Port`, `Baud`, `BusKind`, `IndicationToken`, `ControlToken` and `Value`. No
phase reads `Era`, `Interlocking`, `Machine`, `Column`, `Color`, `Vital` or `Railroad`.

### 4.1 `CtcMachine` (Role `MACHINE`)

| Field | Today: default · reader | Proposed | Fact | Phase |
|---|---|---|---|---|
| `Value` | `SPCoast South cTc` (drawn `SPCoast South`) · CC | keep; default empty | machine name | compiler, generator |
| `Type` | `US&S506` · CC | rename → `PanelStyle`; value names the style, e.g. `LEVER` (a lever panel that is not NX; spelling Q11). The encoding leaves the machine (§4.8) | the panel style. It owns the lever rule (per column: at most one switch or lock lever, at most one signal lever, at least one) and the order of levers and lamps | compiler (lever rule), generator (order) |
| `Columns` | `14` · CC | keep | number of physical columns | compiler, generator |
| `Era` | empty · none | remove (P2). Title block comment 6 already records the era | none | none |
| `Kind` | none | add: `DISPATCHER`. Place for the other operator roles (§4.9) | the operator role the machine serves | compiler, generator |

### 4.2 `PanelColumn` (Role `COLUMN`)

Pins 1–8 `Column` (all equal; membership only).

| Field | Today: default · reader | Proposed | Fact | Phase |
|---|---|---|---|---|
| `Value` | `COLUMN#` · CC | keep: column number; default empty | column number (known nowhere else) | compiler, generator |
| `CP Name` | empty · CC, L | rename → `CP` (same code name as the plant field; one meaning: a control point name). Bare name. Empty is allowed: the compiler warns; a generator for a 506-style target fails without it. A value that does not resolve to a `MAIN HOUSE` of the sheet's interlocking is an error | the control point (and so the 506-style field station) whose functions this column carries (D3) | linker, generator |
| `Interlocking` | `Luchessa` · none | remove (P1: the sheet name records it) | none | none |
| `Machine` | `SPCoast South` · none | remove (P1: the one `CtcMachine` of the project) | none | none |
| `Column` | `${VALUE}` · none | remove (P1: copy of Value) | none | none |

### 4.3 `PanelColumn-MAX7313` (Role `IODRIVER`)

Pins `bit0`–`bit15`. Keep `Value` (bus address, default empty; the library default `8` goes) and
`BusKind` (library fact, P4). Read by CC; used by the generator for the CTC machine application.

### 4.4 Levers: `PanelSwitch`, `PanelLock`, `PanelSignal` (Role `APPLIANCE`)

| Symbol | Value | Pins today | Proposed |
|---|---|---|---|
| `PanelSwitch` (`SWITCH_LEVER`) | switch name; L matches plant switches | `Column`, `NWS`, `RWS`, `RWK`, `NWK` | keep |
| `PanelLock` (`LOCK_LEVER`) | switch name; L cannot check it (locks not in the model) | `Column`, `NWS`, `RWS`, `RWK`, `NWK` | change pins to `Column`, `WLS`, `WLK`, `NWK`, `RWK`. FieldUnit encodes an electric lock as `WLS` (control) and `WLK` (office indication) (`WireCodec.h`). Whether the field unit also sends `NWK`/`RWK` for a lock switch is unverified (Q10) |
| `PanelSignal` (`SIGNAL_LEVER`) | signal number; L matches plant signals | `Column`, `NGS`, `HS`, `SGS`, `SGK`, `NGK`, `TEK` | keep |

Levers have no fields beyond `Value`, `Role`, `Kind`. Pin names are function names; the generator
reads them through the drive bindings.

### 4.5 Lamps: `PanelLamp-RED`, `PanelLamp-YELLOW`, `PanelLamp-BLUE` (Kind `LAMP`)

| Field | Today: default · reader | Proposed | Fact | Phase |
|---|---|---|---|---|
| `Value` | `OS` / `TRACK` · none | keep as a free label (KiCad requires a Value); no phase reads it | none | none |
| `Color` | per symbol · none | keep; library fact (P4). `layout-model.md` has `color` on lamps | lamp color | generator (CTC machine screen, simulator) |
| `IndicationToken` | `S` · CC, L | rename → `OfficeIndications`; default empty (the `S` default goes). One form for every entry: office indication names (`795T1K,2NAAK,799T1K`, `MC1K`). Today the entries mix circuit names (`795T1`) and tokens (`MC1K`). Proxy form `<interlocking>:<name>` for a foreign function. Form open (Q4) | the office indications OR'd onto this lamp | linker (resolve), generator |

### 4.6 `PanelCode` (Kind `CODE`)

`Value` = `CODE` (label). Pins `Column`, `CODE`. Keep. Which field stations one button serves is the
D9 question; it is not a symbol field.

### 4.7 `PanelMCall` and `PanelAuxiliary` (Role `APPLIANCE`)

| Symbol · field | Today: default · reader | Proposed | Fact | Phase |
|---|---|---|---|---|
| `PanelMCall` `Value` | `MC1` · L (reported as unchecked) | keep: names the plant `MaintainerCall`; default empty | which call this lever sends | linker, generator |
| `PanelMCall` `ControlToken` | `${VALUE}S` · CC | remove (P1, P3: the function name follows from the Value) | none | none |
| `PanelMCall` `Vital` | `NO` · none | remove: the class of a maintainer call is fixed | none | none |
| `PanelAuxiliary` `Value` | empty · none | keep: names the plant `AUXILIARY` | which auxiliary this lever sends | linker, generator |
| `PanelAuxiliary` `ControlToken` | `${VALUE}S` · CC | remove (P1, P3) | none | none |
| `PanelAuxiliary` `Vital` | `NO` · none | move to the plant `AUXILIARY` as `<ControlClass>` (§3.10; Q3) | none on the panel | none |

Why the class moves. The class says how the field unit processes a control (iteration 11). The
interlocking application must know it with no CTC machine drawn, for example for a tower operator or a
virtual target. One fact, one place: the plant symbol. The CTC machine does not need it.

### 4.8 Code line: `CODELINE`, encoding symbol, transport symbol (replace `Codeline-MQTT`, `Codeline-CMRInet`)

Today `Codeline-MQTT` has `Value` `MQTT` (the transport), `Railroad` `SPCoast`, `Broker`, `Topic`
`ctc/${Railroad}/codeline/${Station}` and `Station` `${SHEETNAME}`. CC reads `Station`, `Broker` and
`Topic`, and also looks for `TopicRoot`, which no symbol has. `Codeline-CMRInet` has `Station` (`Node
UA`), `Port`, `Baud`. Neither has pins.

Proposed drawing (D13, D15). Three symbols for one code line:

| Symbol | Role | Pins | Value | Fields | Phase |
|---|---|---|---|---|---|
| `CODELINE` | `CODELINE` | 1 `ENCODING`, 2 `TRANSPORT` | empty (label) | `Address <field station>`, one per field station that has an authored address (e.g. `Address Luchessa`, `Address Gilroy`). Form open (Q5) | compiler records the addresses and checks them for duplicates; generator uses them, and fails for a target that needs one and does not find it |
| `Encoding` | `ENCODING` | 1 | the name of the encoding definition (`AAR-TOKENS`, `USS-506`; spelling unverified) | none. The definition file in the SPCoast KiCad repo holds the rules (D10, D11) | compiler (resolves the name), generator |
| `Transport-MQTT` | `TRANSPORT` | 1 | `MQTT` (the transport definition) | `Broker`, `TopicRoot` (`ctc/SPCoast/codeline`) | compiler, generator |
| `Transport-CMRInet` | `TRANSPORT` | 1 | `CMRInet` | `Port`, `Baud`. The node UA is an address: it goes on `CODELINE` | compiler, generator |

Field by field from today:

| Today | Proposed | Reason |
|---|---|---|
| `Value` = transport | the transport symbol's Value | D1, D15 |
| `Station` = `${SHEETNAME}` | remove | P1: on AAR tokens the field station is the interlocking; on a 506-style encoding it is the `MAIN HOUSE` Value. The generator derives it |
| `Station` = node UA (CMRInet) | `Address <field station>` on `CODELINE` | it is an authored address (D4, D13) |
| `Topic` | remove | P3: the topic form is transport policy; the MQTT definition builds it from `TopicRoot` and the field station name (spaces to `-`) |
| `Railroad` | remove | P2: only `Topic` used it; title block comment 4 records the railroad |
| `Broker` | keep, on the transport symbol | transport parameter |
| `Port`, `Baud` | keep, on the transport symbol | transport parameters |

Placement (proposal). One `CODELINE` on each interlocking sheet of the CTC machine project, as today.
One encoding symbol and one transport symbol for each code line, on the root sheet, joined to every
`CODELINE` pin by a global label. The net then names the code line instance; `Broker` is written once
(P1). Today's rule ("same transport and same `Broker` = one instance") becomes a check. The alternative
is one encoding and one transport symbol on every sheet, with the instance derived as today (Q6).

A virtual target needs nothing drawn. A sheet with no `CODELINE` is valid. The `VIRTUAL` default in CC
goes.

### 4.9 Place for the other operator roles

- Dispatcher: `CtcMachine`, `Kind` = `DISPATCHER`. The only role drawn.
- Tower operator: reserved as Role `MACHINE`, `Kind` = `TOWER_OPERATOR` (direct to a locking bed, no
  code line). Where it is drawn (plant project or its own project) is not designed.
- Maintainer: reserved `Kind` = `MAINTAINER` (maintenance or debug mode, without the interlocking). Not
  designed. Fascia devices and service modes have their own ADR (ADR 0001, still open item 4).

## 5. What names the interlocking

Today: `--plant-name` on the command line, else the file stem; the folder name for membership; the
sheet name on the CTC machine side. The sources disagree. GilroyCalTrain: folder `GilroyCalTrain`,
title `Gilroy Caltrain Station`, desk sheet `Gilroy CalTrain`, `NextCP` in GilroyInterchange `Gilroy
Caltrain`. GilroyInterchange: folder and title `GilroyInterchange`, desk sheet `Gilroy Interchange`. The
linker pairs them today by removing whitespace, a rule that D12 (amended) withdraws.

| Option | What is drawn | Cost |
|---|---|---|
| A. `INTERLOCKING` symbol | One symbol, Role `INTERLOCKING`, no pins, in each plant project. Value = the name; it may display `${TITLE}` | A new library symbol; 6 placements. Exactly one per plant project, else an error. Symmetric with `MAIN HOUSE`. Works for one or several control points. The name is free of file system limits. The desk sheet name must equal it (case folded) |
| B. Field on `MAIN HOUSE` | `Interlocking` = name on every `MAIN HOUSE`, or a flag on one | No new symbol; a script can add the field. On every house: N copies of one fact (P1), all must agree. On one house: moving or deleting that house loses the name. With one control point the field repeats or differs from the Value for no reason |
| C. Title block | The compiler reads `title` (already parsed into `document.title`) | No drawing change except fixing titles. A title is prose for print (`Gilroy Caltrain Station`), not a name, and it is not visible as a model fact. Close to what the owner rejected for `MAIN HOUSE` |

Recommendation: A. Under all options the desk side keeps the sheet name as the join, and the linker
compares names with case folded and spaces replaced by `-` only.

## 6. Migration

### 6.1 Counts per project (Watsonville excluded)

Read from the netlists (2026-10-01 for plants; 2026-09-30 16:12 for South-cTc, whose sheets are newer,
so its counts can be stale (unverified)). The library `Railroad.kicad_sym` changed on 2026-10-02, after
every netlist.

| Change | Luchessa | Sargent | GilroyInterchange | Christopher | Corporal | GilroyCalTrain | Script? |
|---|---|---|---|---|---|---|---|
| `MAIN HOUSE` Value: strip `CP ` | 3 | 0 | 0 | 0 | 0 | 0 | yes |
| `CP` values: strip `CP ` | 15 | 0 | 0 | 15 | 0 | 0 | yes |
| `CP` values that resolve to no `MAIN HOUSE` after the strip (empty IRJ `CP` included; those fields go) | 0 | 4 (3 IRJ, 1 proxy) | 4 (IRJ) | 6 (IRJ) | 10 (4 IRJ, 5 `FIXME`, 1 `INDUSTRY`) | 0 | no for `FIXME`, `INDUSTRY` |
| Role `CONTROLLED_POINT` → `CONTROL_POINT` | 3 | 1 | 2 | 3 | 2 | 3 | yes |
| Instance `Role`/`Kind` reset to library | 0 | 1 | 2 | 4 | 2 | 5 | yes |
| Mast `CP` from the IRJ on its `SIGNAL` net, then IRJ `CP` removed | 5 | 3 (IRJ empty: hand) | 4 (2 set on the mast; 2 by hand) | 6 (no nets: hand) | 4 (no nets, IRJ empty: hand) | 5 (no nets: hand) | Luchessa yes; others hand |
| Policy markers: `Kind` rename; remove `Rulebook`, `Name`, `Direction` where implied | 5 | 4 | 2 | 4 | 4 | 5 | yes |
| `NextCP` Value: bare interlocking name | 4 | 2 (`~`: hand) | 1 (`Gilroy Caltrain`: hand) | 0 | 0 | 1 (`CP_Lick`) | mostly |
| `MaintainerCall`: set Value; remove `CP`; connect pin to `MAIN HOUSE` | 1 (Value `MC1`) | 0 | 2 (`CP`) | 2 (`CP`, pin: hand) | 1 (pin: hand) | 0 | Value and field yes; pins hand |
| Dependent derail `CP` emptied | 1 | 0 | 0 | 0 | 1 | 0 | yes |
| Proxy track circuit `CP` emptied | 0 | 1 | 0 | 0 | 0 | 0 | yes |
| Stray fields removed (`Direction`, `Name`, `CP` on IRJ/Bumper) | 0 | 0 | 56 | 0 | 0 | 3 | yes |
| `TC` list to one name | 0 | 0 | 0 | 0 | 0 | 1 | no (Q13) |
| Empty Values on masts or heads | 0 | 0 | 0 | 7 | 0 | 0 | no |
| `Milepost` set (default or `FIXME`) | 3 | 1 | 0 | 0 | 2 | 0 | no |
| Interlocking name (option A) | 1 | 1 | 1 | 1 | 1 | 1 | placement yes |

South-cTc (Watsonville sheet excluded):

| Change | Count | Script? |
|---|---|---|
| `PanelColumn`: remove `Interlocking`, `Machine`, `Column` | 13 × 3 | yes |
| `PanelColumn`: `CP Name` → `CP`; strip `CP ` (3); `FIXME` → empty (10) | 13 | yes; the 10 values by hand later |
| Lamps: `IndicationToken` → `OfficeIndications`; entry form | 39 | yes for the 30 that resolve; 9 `FIXME` entries by hand |
| `PanelMCall`: remove `ControlToken`, `Vital` | 8 | yes |
| `PanelLock`: new pins, re-wire to driver bits; reset `Kind` on 795 | 7 | no (re-wire by hand) |
| `Codeline-MQTT` → `CODELINE` + encoding + transport | 6 sheets | no (placement and wiring); field values yes |
| `CtcMachine`: `Type` → `PanelStyle`, remove `Era`, add `Kind` | 1 | yes |
| Sheet names equal the interlocking names (`Gilroy CalTrain`, `Gilroy Interchange`) | 2 | no (owner picks the spelling) |

A script edits `.kicad_sch` files only when no `~*.lck` exists and KiCad is closed (AGENTS.md). It uses
the existing s-expression helpers; it writes no new parser. `tools/legacy_import/` already edits
properties this way (unverified that it fits).

### 6.2 Compiler and linker changes

Plant compiler:

1. Classify by library `Role`/`Kind` through `lib_id`; drop `_PART_KIND`. Warn when an instance copy
   differs. This admits `Switch_HandThrow`, `Switch_Powered_NO_TC`, `Switch_Powered_Small`,
   `Track Circuit_Yellow`, `Rule6.13-Yard Limits`, the semaphore heads and `AUXILIARY`.
2. Error when a plant project has no `MAIN HOUSE`. Warn on a `CP ` or `CP_` prefix in any name (a
   check, not normalization).
3. Read the mast `CP`; during the transition fall back to the IRJ `CP` with a warning.
4. Read policy `Kind` and `Direction`; find dark track by `Kind`; stop requiring `Rulebook`.
5. Put maintainer calls and auxiliaries in the model, with the control point from the pin net to
   `MAIN HOUSE`. Then `setupCodec()` loses its hard-coded calls (FieldUnit-Subdivision runtime).
6. Read `IndicationCeiling` (fallback `Indications`).
7. Take the dependent derail's control point from its switch.
8. Recognize the proxy form `<interlocking>:<name>` as a foreign reference.
9. Take the interlocking name from the chosen option (§5); `--plant-name` goes.
10. Read `MAIN HOUSE` `Milepost` for control point order (if Q7 is yes).

Controller compiler:

1. Read `CP` (fallback `CP Name`); empty is a warning, not the error `cp-name-unset`.
2. Read `OfficeIndications` (fallback `IndicationToken`).
3. Read `CODELINE`, encoding and transport symbols through their pin nets; read `Address <name>`
   fields. Allow zero `CODELINE` on a sheet. Remove `_TRANSPORTS`, the `VIRTUAL` default and the
   reads of `Station` and `Topic`.
4. Read `PanelStyle` and `Kind` from `CtcMachine`; key the lever rule to the panel style.
5. Accept `PanelLock` pins `WLS`, `WLK`.

Linker:

1. Pair plant and sheet by interlocking name: case folded, spaces to `-`. `station_key()` (whitespace
   removed) goes.
2. Cross-check `PanelColumn` `CP`, maintainer calls and auxiliaries (now in the model). Locks stay a
   known gap until the plant model has them.
3. Check that addresses are unique on one code line instance, and that two attachments agree.

### 6.3 Order of steps

Each step leaves the drawings and the tools in agreement. Goldens and tests that hard-code Luchessa
facts change in their own step (AGENTS.md).

1. Put both libraries under git (in this repo, as AGENTS.md expects) before the first change.
2. Compilers read new and old names (the fallbacks above). Tests pass on today's drawings.
3. Change the library: renames, removals, empty defaults, new fields, new symbols, pin changes.
4. Run the script per project, with KiCad closed. Rebuild netlists (`make netlist`). Run the compilers.
   Compare the models before and after by behavior gates, not by goldens.
5. Hand work: `FIXME` values, unresolved `CP` values, mast `CP` where nets are missing, `PanelLock`
   wiring, the `CODELINE` trio, the interlocking name symbols, maintainer call pins.
6. Update FieldUnit `examples/spcoast_ctc` `configureDesk()` and `tools/test_ctc_desk.py` for the bare
   names; update goldens and tests in their own commit.
7. Remove the fallbacks. Instance copy warnings become errors where the owner wants it.
8. Watsonville follows when its schematic is fixed.

## 7. Open questions for the owner

1. Interlocking name: option A (symbol), B (`MAIN HOUSE` field) or C (title block)?
2. Class names: `INTERLOCKED`/`AUXILIARY` or `VITAL`/`NON_VITAL`, and the field name (placeholder `ControlClass`)?
3. Move the class field from the panel symbols to the plant `AUXILIARY` symbol: yes or no?
4. Lamp entries: office indication names (`795T1K`, `MC1K`) or appliance names (`795T1`, `MC1`)?
5. Addresses: one field per field station (`Address Gilroy`) or one list field (`Addresses`)?
6. Encoding and transport symbols: once per code line on the root sheet (global label), or on every sheet?
7. `MAIN HOUSE` `Milepost`: keep as the geographic order of control points, or remove?
8. Remove the unread `Route` symbol: yes or no?
9. `NextCP` Value: the neighbor interlocking or the neighbor control point?
10. Does a lock lever carry `NWK`/`RWK` as well as `WLS`/`WLK`?
11. Spelling of the SPCoast panel style value (e.g. `LEVER`)?
12. Policy `Kind`: names by meaning (`SIGNALED_ONE_DIRECTION`), or by one rulebook (which)?
13. GilroyCalTrain 771 `TC` = `771T1, 773T1, 775T1`: one shared OS circuit, or three?
14. Read `Role`/`Kind` from the library and only warn on instance copies: yes or no?
15. Is a hand-throw switch an appliance with a `CP` (Corporal 1 has `INDUSTRY`)?
16. Rename `NextCP`/`NEXT_CP` to `NextInterlocking`/`NEXT_INTERLOCKING`: yes or no?
