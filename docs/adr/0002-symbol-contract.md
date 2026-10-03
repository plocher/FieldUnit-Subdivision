# 0002. The symbol contract: what each KiCad symbol records

- Status: proposed
- Date: 2026-10-02

Not committed. No library, schematic or code is changed by this ADR.

Terms: FieldUnit `docs/GLOSSARY.md`; ADR 0001 (D1–D16, amended 2026-10-02); `docs/review/vocabulary-review.md`
iterations 9–11; `ontology.md` rev 5; `layout-model.md` rev 8; `desk-codeline-kicad-pattern.md`.
The class of a control (the `Vital` field) is the subject of FieldUnit `docs/adr/0002-control-transaction-classes.md`
(accepted 2026-10-02). That ADR names the classes: vital and non-vital. The field is `Vital`.

"(unverified)" marks a statement that no opened source supports.

## Decisions requested

Ordered by what blocks the migration first. Answer each in one line. The default is the proposal in
"Decision".

Already decided by the owner (2026-10-02), so not asked:

- The `Rulebook` field was replaced on purpose by the Kind/Role mechanism. The policy markers lose `Rulebook`.
  The compiler must be updated to match.
- A plant project with no `MAIN HOUSE` symbol is a compiler error that states the uncertainty.

Asked:

1. Interlocking name: which symbol or field names the interlocking? Options: 
   A. an `INTERLOCKING` symbol;
   B. a field on `MAIN HOUSE`
   C. the title block. 
   Default: A.

   RESPONSE: Agreed: A
   B fails when there are multiple MAIN HOUSE symbols
   C fails becaus title blocks are not authorative parts of the schematic/data model

2. Read `Role` and `Kind` from the library by `lib_id`, and only warn on instance copies that differ? Options:
   yes, no. Default: yes.

   RESPONSE: Agreed: warn when symbols don't match library Kind and Role.
   Disagreement means someone was trying to do something different, and we need to understand their problem better...

   Tied to this: making a new symbol with an existing KIND/ROLE and the same pin naming/count shoul dbe transparent to the compiler.  Saying another way, the names of the symbols should not be special/hardcoded into the compiler.

3. Policy marker `Kind` names: by meaning (`SIGNALED_ONE_DIRECTION`, `SIGNALED_BOTH_DIRECTIONS`,
   `YARD_LIMITS`, `NOT_SIGNALED`) or by one rulebook (which)? Default: by meaning.

   RESPONSE: Is this a reference to the direction of traffic?
   NEED MORE INFO TO RESPOND

4. Where does the `Vital` field (the control class) live? Options: on the plant `AUXILIARY` symbol (moved from the panel
   symbols), or stay on the panel symbols. Default: on `AUXILIARY`. The class names (vital, non-vital) and the field `Vital` come
   from FieldUnit ADR 0002 (control transaction classes).

   RESPONSE: These can only apply to **controls**, which makes them panel appliance attributes and not hardware I/O attributes.  
   This implies that PanelAuxiliary is the correct symbol, not the AUXILIARY lamp...
   Further, the attribute does not apply to signal and switch levers; only to auxiliary functions such as MCall and PanelAuxiliary...

   I hear a distinction between "plant" and "panel" symbols that should not exist - these symbols will merge into one library soon, and their names should not matter...

5. Lamp entries: office indication names (`795T1K`, `MC1K`) or appliance names (`795T1`, `MC1`)?
   
   Default: office indication names.

   RESPONSE:  The attribute `IndicationToken` exists for exactly this purpose.  It is a comma separated list of tokens...
   The lamp appliances don't generally have VALUES that are unique...
   
6. Addresses on `CODELINE`: one field per field station (`Address Gilroy`) or one list field (`Addresses`)?
   Default: one field per field station.

   RESPONSE: See new transport/encoding symbology in South-cTc

7. Encoding and transport symbols: once per code line on the root sheet (global label), or on every sheet?
   Default: once per code line on the root sheet.

      RESPONSE: See new transport/encoding symbology in South-cTc

8. `NextCP` Value: the neighbor interlocking or the neighbor control point? Default: the neighbor interlocking.

   RESPONSE: neighbor interlocking

9.  Rename `NextCP` / `NEXT_CP` to `NextInterlocking` / `NEXT_INTERLOCKING`: yes or no? Default: yes (optional).

   RESPONSE: I'll change the library, but allow both unless we kick off a task to modify the existing schematics...

10. `MAIN HOUSE` `Milepost`: keep as the geographic order of control points, or remove? Default: keep.

   RESPONSE: Keep

11. Remove the unread `Route` symbol: yes or no? Default: yes.

   RESPONSE: Deleted

12. Does a lock lever carry `NWK` and `RWK` as well as `WLS` and `WLK`? Default: `WLS` and `WLK` only until
    FieldUnit confirms (unverified).

   RESPONSE: Currently, locks and switches carry the SAME AAR tokens (both control and indication) for simplicity - the prototypical crew/dispatcher/field coordination is ignored.

   In order to "do" electric locks correctly, we need more structure and vocabulary, which is a large scoped task that I'm not sure we're ready for in this session.  I've captured it in `docs/review/ElectricLockProcedure.md` for reference.


12.  Spelling of the SPCoast panel style value (for example `LEVER`)? Default: `LEVER`.
    
     RESPONSE:  LEVER

13.  GilroyCalTrain switch 771 has `TC` = `771T1, 773T1, 775T1`: one shared OS circuit, or three? Default: none;
    the drawing owner knows.

   RESPONSE: All three switches are in one logical detection block.  If the layout uses detectors on each, they need to be aggregated.

14.  Is a hand-throw switch an appliance with a `CP` (Corporal 1 has `INDUSTRY`)? Default: none; the drawing
    owner knows.

   RESPONSE: The industry switches are not ctc/dispatcher controlled, though they may well (will) be electrically operated devices with local fascia mounted controls that need to be integrated into the field unit's I/O connections.

## Decided since the proposal (owner, 2026-10-02)

- The `Vital` field is a property of a control. It lives on the panel auxiliary symbols (`PanelMCall`,
  `PanelAuxiliary`), never on a switch or signal lever (owner's response to request 4, 2026-10-02).
  The plant and panel libraries will merge; the split is not meaningful.
- A switch or signal marked non-vital on a drawing is a compiler **warning**: the attribute is
  ignored and the appliance is processed as vital. It is not an error.
- What a drawer means by a "non-vital switch" or "non-vital signal" has a model already: a switch
  the interlocking does not control is dark track; a signal that is not interlocked is an
  `AUXILIARY` lamp; relaxed checks for test or maintenance are the maintainer role, a run-time
  mode, not a drawn attribute.

## Prototype adopted (owner, 2026-10-02)

Final form (later on 2026-10-02): transports on the root sheet on the `CtcMachine` `Transports` pin,
global labels as the code line nets, field stations as encoding instances on the interlocking sheets,
`CODELINE` retired. See ADR 0001 D15. The `CtcMachine` symbol gains the pin `Transports`.


The owner drew the code line symbols on the South-cTc Luchessa sheet: `Codeline` (pin `Transports`),
`Codeline-Transport-MQTT` and `Codeline-Transport-TimeCode` (pins `Codeline`, `Encoding`),
`Codeline-Encoding-AAR` and `Codeline-Encoding-US&S-506` (pin `Encoding`). The netlist shows the
graph complete. ADR 0001 D13 and D15 are amended to this shape. Requests 6 and 7 are answered (ADR 0001 D13 as
amended a second time): a station-selecting encoding is drawn once for each field station, with
`Station` and `Address` fields on each instance; the symbols sit on the sheet of the interlocking. Open on the prototype: the Value "USS Type L Form 506" ("Type L" and
"Form 506" have no source) and the ATCS description on `Codeline-Encoding-AAR`.

## Context

### The storyline

1. Draw each interlocking and the CTC machine in KiCad.
2. The compiler and linker read the drawings and make one model.
3. The generator reads the model and emits one interlocking application for each interlocking and one CTC machine application.
4. The applications run on field processors and on the CTC machine: first virtual, then AAR tokens over MQTT.
5. This ADR states, for each symbol, the facts that step 2 must read so that step 3 can emit step 4.
   Everything else leaves the symbol.

### Why fields went stale

The definitions behind the symbol fields changed (vocabulary review, iteration 11). The symbols hold
facts of the older model, for example the `Station` field of `Codeline-MQTT`. Some fields are read by no
phase. Some facts are recorded twice. Placeholder defaults hide missing values. Some compilers still
classify by a hard-coded table.

### What was inventoried

- The two libraries, read with `SymbolLibraryReader`: the plant library `Railroad.kicad_sym` (29 symbols,
  114 field slots, 11 field names) and the panel library `RailroadPanel.kicad_sym` (14 symbols, 62 field
  slots, 21 field names).
- The netlists of Luchessa, Sargent, GilroyInterchange, Christopher, Corporal, GilroyCalTrain and
  South-cTc, read with `NetlistReader`. Christopher, Corporal and GilroyCalTrain have components but no
  nets, so they give field values only.
- Excluded as of 2026-10-01: the Watsonville project and the Watsonville sheet of South-cTc. The owner
  changed the Watsonville schematic on 2026-10-02; to be re-checked. No re-inventory was done.
- Instance copies of `Role` and `Kind` disagree with the library in 15 symbols: Sargent 1,
  GilroyInterchange 2, Christopher 4, Corporal 2, GilroyCalTrain 5, South-cTc 1.

## Decision

### Principles for a field

| # | Principle | Test |
|---|---|---|
| P1 | One fact, one place. | If two fields (or a field and a pin connection, a sheet name or a title block) record one fact, one of them goes. |
| P2 | A phase reads it. | The compiler, the linker or the generator reads the field. If no phase reads it, it goes, or it becomes documentation in the symbol description. |
| P3 | Names, not policy. | A field records a drawn fact (a name, a membership, an authored address). It does not record what the generator must do (a topic pattern, a token spelling, a target). The generator owns policy (ADR 0001 D6). |
| P4 | Library facts stay in the library. | A fact that is the same for every instance of a symbol (`Role`, `Kind`, `Color`, `BusKind`, `Direction` on a one-direction marker) is read from the library by `lib_id`. The copy that KiCad puts in each instance is not read. A copy that differs from the library is a warning ("update symbol from library"). |
| P5 | Instance facts have an empty default. | A name, a membership or an address has an empty library default, so a missing value is found. Placeholders (`XX`, `FIXME`, `COLUMN#`, `79.0`, `S`, `Luchessa`) go. |
| P6 | Connections are pins. | A membership that can be drawn as a pin connection is read from the netlist, not from a name field (AGENTS.md). |
| P7 | Code names versus prose terms. | A field name, a Role or a Kind is a code name. It keeps its spelling when the prose term differs, unless its meaning changed or it uses a retired term. Names in values have no `CP ` or `CP_` prefix (ADR 0001 D12). A name used in a topic or a key has each space replaced by `-`; that is the only normalization. |

Instance copies of `Role` and `Kind` disagree with the library (see Context). Examples: `Mast_Double`
with `Kind` = `MAST_DWARF` (GilroyInterchange S3, S4); `Switch_HandThrow` with `Kind` = `SWITCH_POWERED`
(Sargent SW3, Corporal SW901); `PanelLock` 795 with `Kind` = `SWITCH_LEVER` (South-cTc SW796). The
controller compiler reads the instance `Kind`, so it treats lock lever 795 as a switch lever today. The
plant compiler reads neither; it classifies by symbol name (`_PART_KIND`).

Operator roles: dispatcher, tower operator, maintainer. The machine keeps a type that means its panel style.

### Plant library: fields that change

Fields kept unchanged are in the appendix. "Phase" is the phase that reads the fact.

Common to every plant symbol:

| Symbol · field | Change | Fact recorded | Phase |
|---|---|---|---|
| all · `Role` | read from the library (P4). Value `CONTROLLED_POINT` → `CONTROL_POINT` (retired term) | what the compiler does with the Value and pins | compiler |
| all · `Kind` | read from the library; the compiler classifies by `Kind`, and `_PART_KIND` goes | the FieldUnit class, or the variant that changes derivation | compiler |
| all · `Value` | library default empty (P5) | the railroad name | compiler |

`MAIN HOUSE`:

| Field | Change | Fact | Phase |
|---|---|---|---|
| `Role` | rename value → `CONTROL_POINT` (P7) | none new | compiler |
| `Milepost` | default `79.0` → empty (Luchessa has `79.0` on all three, the default, never set; Sargent and Corporal have `FIXME`). The compiler reads it to put `controlPoints[]` in geographic order (`layout-model.md` §1) instead of the x coordinate (request 10) | the location of the control point | compiler |
| `Value` | no `MAIN HOUSE` in a plant project: error that states the uncertainty (decided) | the control point and its bungalow | compiler |

Switches (`Switch_Powered`, `Switch_Powered_Small`, `Switch_Powered_NO_TC`, `Switch_Lock`, `Switch_HandThrow`):

| Field | Change | Fact | Phase |
|---|---|---|---|
| `Indications` | add to the library as `IndicationCeiling`, default empty. Form `NORMAL/REVERSE`, e.g. `CLEAR/APPROACH`. Instances carry `Indications` today (none drawn; the compiler reads it) | the most favorable signal indication over the switch in each position (glossary "indication ceiling") | compiler (route `bestIndication`) |
| `TC` | exactly one name, or empty for no OS circuit. A list is not allowed (request 14) | the OS track circuit that detector-locks the switch | compiler, generator |

Derails (`Switch_Powered_Derail`, `Switch_Powered_Derail_TC`):

| Field | Change | Fact | Phase |
|---|---|---|---|
| `CP` | empty for a dependent derail: the compiler takes the switch's control point (P1). A value that differs is an error | control point of the derail | compiler |

Track circuits (`Track Circuit`, `Track Circuit_Yellow`):

| Field | Change | Fact | Phase |
|---|---|---|---|
| `CP` | empty for a proxy circuit: the circuit is not in this interlocking (Sargent TC4 has `Corporal`) | control point of the circuit | compiler |
| pin 1 name | rename `MC` → `T` (number stays 1; the compiler reads numbers) | none (the name misleads) | none |

Signals:

| Symbol · field | Change | Fact | Phase |
|---|---|---|---|
| Mast `CP` | add to the library, default empty (drawn today on 6 masts: GilroyInterchange 2, Christopher 4; not read). The compiler reads it (`layout-model.md` §1: "controlPoint: the mast's drawn CP field") | control point of the mast in the field | compiler |
| `IRJ-Signal` `CP` | remove after the mast `CP` is filled (P1). The IRJ is `TRACK`; it has no railroad name. Today it is the only source of a mast's control point (read by M and checked by C) | (moves to the mast) | none |

Track terminals:

| Symbol · field | Change | Fact | Phase |
|---|---|---|---|
| `IRJ`, `Bumper` | remove the stray instance `CP` (GilroyCalTrain bumpers 3) and `Direction`/`Name` (GilroyInterchange) | a track graph edge or end | compiler |
| `NextCP` `Value` | bare name of the neighbor interlocking (`Christopher`, not `CP Christopher`) (request 8). Rename `Kind` `NEXT_CP` → `NEXT_INTERLOCKING` and the symbol to match (request 9; optional; the term "CP" is not a common noun) | the neighbor across this plant edge | compiler; linker (subdivision topology); generator (proxy listening; train progression) |

Policy markers (`Rule251-DoT-Left`, `Rule251-DoT-Right`, `Rule261-DoT-BiDirectional`, `Rule6.13-Yard Limits`, `Rule6.28-OtherThanMain`):

| Field | Change | Fact | Phase |
|---|---|---|---|
| `Kind` | rename to the meaning, not a rule number: `SIGNALED_ONE_DIRECTION`, `SIGNALED_BOTH_DIRECTIONS`, `YARD_LIMITS`, `NOT_SIGNALED` (other than main track, dark). The compiler reads `Kind` (request 3) | the operating method of the track at the marker | compiler |
| `Rulebook` | remove from the instances (decided: the Kind/Role mechanism replaced it on purpose). The description may cite rule numbers as documentation | (in `Kind`) | none |
| `Name` | remove (P2). Prose goes in the description | none | none |
| `Direction` | keep on the one-direction markers only (library fact, P4). Remove from the others: `BOTH` is implied by `Kind` | the direction of traffic on one-direction track | compiler |
| `Value` | library default empty (P5); the defaults (`RULE 251`, `Rule 261`, `YARD`, `DARK`) are labels, not names | the track name | compiler |

`Route`: remove the symbol (request 11). `IndicationCeiling` on switches gives the authored input to
`bestIndication`. Keep it only if a route-level override is needed.

`MaintainerCall` and `AUXILIARY`:

| Symbol · field | Change | Fact | Phase |
|---|---|---|---|
| `MaintainerCall` `Value` | required: `MC<n>`, unique in the interlocking (Luchessa MC1 has `~`) | the call's name; functions `MC<n>S`, `MC<n>K` | compiler, linker, generator |
| `MaintainerCall` `CP` | do not add to the library. Read the control point from the pin connection to `MAIN HOUSE` pin `H` (P6) and do not also require a `CP` field. Remove the 4 existing instance fields (GilroyInterchange 2, Christopher 2) | the bungalow the maintainer is called to | compiler |
| `MaintainerCall` class | no field: a maintainer call is always a non-vital control (iteration 11) | (by `Kind`) | generator |
| `AUXILIARY` control point | pin connection to `MAIN HOUSE` pin `H` (P6); rename pin name `MC` → `H` | the bungalow of the appliance | compiler |
| `AUXILIARY` `Vital` field | add (bool). The class names (vital, non-vital) come from FieldUnit ADR 0002 (control transaction classes). The class moves here from the panel symbols (request 4) | how the field unit processes the control (vital: ignored as a group when one is unsafe; non-vital: processed anyway) | generator (interlocking application) |
| `AUXILIARY` `Functions` | add: `CONTROL`, `INDICATION`, or `CONTROL,INDICATION` (proposal) | which functions exist; their names are `<Value>S`, `<Value>K` | generator; linker (lever and lamp cross-check) |

The maintainer call connects by pin to `MAIN HOUSE` pin `H`. The drawing records the bungalow of every
connected call. This is verified in the Luchessa, Sargent and GilroyInterchange netlists. In
GilroyInterchange the `CP` field also exists and agrees (MC1, MC2). Christopher and Corporal are not
wired. Luchessa MC1 connects to `CP Luchessa`; its panel lever and lamp are in column 6 (`CP Gilroy`).
By ADR 0001 D3 this is not an error.

`Milepost` symbol: keep as documentation; default empty. No phase reads it.

Plant hardware sheet (planned, not designed here): `desk-codeline-kicad-pattern.md` §5a plans a second
top-level sheet with a field unit symbol, field I/O proxies and IODRIVER symbols. Head type (color
light, semaphore) belongs there, as field I/O. Not in scope.

### Panel library: fields that change

`CtcMachine`:

| Field | Change | Fact | Phase |
|---|---|---|---|
| `Value` | default `SPCoast South cTc` → empty (drawn `SPCoast South`) | machine name | compiler, generator |
| `Type` | rename → `PanelStyle`; value names the style, e.g. `LEVER` (a lever panel that is not NX; request 13). The encoding leaves the machine (see "Code line") | the panel style. It owns the lever rule (per column: at most one switch or lock lever, at most one signal lever, at least one) and the order of levers and lamps | compiler (lever rule), generator (order) |
| `Era` | remove (P2). Title block comment 6 already records the era | none | none |
| `Kind` | add: `DISPATCHER`. Place for the other operator roles (see "Operator roles") | the operator role the machine serves | compiler, generator |

`PanelColumn`:

| Field | Change | Fact | Phase |
|---|---|---|---|
| `Value` | default `COLUMN#` → empty | column number (known nowhere else) | compiler, generator |
| `CP Name` | rename → `CP` (same code name as the plant field; one meaning: a control point name). Bare name. Empty is allowed: the compiler warns; a generator for a 506-style target fails without it. A value that does not resolve to a `MAIN HOUSE` of the sheet's interlocking is an error | the control point (and so the 506-style field station) whose functions this column carries (ADR 0001 D3) | linker, generator |
| `Interlocking` | remove (P1: the sheet name records it). Default `Luchessa` | none | none |
| `Machine` | remove (P1: the one `CtcMachine` of the project). Default `SPCoast South` | none | none |
| `Column` | remove (P1: copy of Value). Default `${VALUE}` | none | none |

`PanelColumn-MAX7313`: library default `8` for `Value` goes (empty default, P5).

`PanelLock`: change pins from `Column`, `NWS`, `RWS`, `RWK`, `NWK` to `Column`, `WLS`, `WLK`, `NWK`, `RWK`.
FieldUnit encodes an electric lock as `WLS` (control) and `WLK` (office indication) (`WireCodec.h`).
Whether the field unit also sends `NWK`/`RWK` for a lock switch is unverified (request 12).

Lamps:

| Field | Change | Fact | Phase |
|---|---|---|---|
| `IndicationToken` | rename → `OfficeIndications`; default empty (the `S` default goes). One form for every entry: office indication names (`795T1K,2NAAK,799T1K`, `MC1K`). Today the entries mix circuit names (`795T1`) and tokens (`MC1K`). Proxy form `<interlocking>:<name>` for a foreign function. Form open (request 5) | the office indications OR'd onto this lamp | linker (resolve), generator |

Maintainer call and auxiliary levers:

| Symbol · field | Change | Fact | Phase |
|---|---|---|---|
| `PanelMCall` `Value` | default `MC1` → empty | which call this lever sends | linker, generator |
| `PanelMCall` `ControlToken` | remove (P1, P3: the function name follows from the Value) | none | none |
| `PanelMCall` `Vital` | remove: the class of a maintainer call is fixed | none | none |
| `PanelAuxiliary` `ControlToken` | remove (P1, P3) | none | none |
| `PanelAuxiliary` `Vital` | move to the plant `AUXILIARY` as the `Vital` field (request 4) | none on the panel | none |

Why the class moves. The class says how the field unit processes a control (iteration 11). The
interlocking application must know it with no CTC machine drawn, for example for a tower operator or a
virtual target. One fact, one place: the plant symbol. The CTC machine does not need it. FieldUnit
ADR 0002 (control transaction classes) names the classes: vital and non-vital.

### Code line

`CODELINE`, an encoding symbol and a transport symbol replace `Codeline-MQTT` and `Codeline-CMRInet`
(ADR 0001 D13, D15).

Three symbols for one code line:

| Symbol | Role | Pins | Value | Fields | Phase |
|---|---|---|---|---|---|
| `CODELINE` | `CODELINE` | 1 `ENCODING`, 2 `TRANSPORT` | empty (label) | `Address <field station>`, one per field station that has an authored address (e.g. `Address Luchessa`, `Address Gilroy`). Form open (request 6) | compiler records the addresses and checks them for duplicates; generator uses them, and fails for a target that needs one and does not find it |
| `Encoding` | `ENCODING` | 1 | the name of the encoding definition (`AAR-TOKENS`, `USS-506`; spelling unverified) | none. The definition file in the SPCoast KiCad repo holds the rules (ADR 0001 D10, D11) | compiler (resolves the name), generator |
| `Transport-MQTT` | `TRANSPORT` | 1 | `MQTT` (the transport definition) | `Broker`, `TopicRoot` (`ctc/SPCoast/codeline`) | compiler, generator |
| `Transport-CMRInet` | `TRANSPORT` | 1 | `CMRInet` | `Port`, `Baud`. The node UA is an address: it goes on `CODELINE` | compiler, generator |

Field by field from today:

| Today | Proposed | Reason |
|---|---|---|
| `Value` = transport | the transport symbol's Value | ADR 0001 D1, D15 |
| `Station` = `${SHEETNAME}` | remove | P1: on AAR tokens the field station is the interlocking; on a 506-style encoding it is the `MAIN HOUSE` Value. The generator derives it |
| `Station` = node UA (CMRInet) | `Address <field station>` on `CODELINE` | it is an authored address (ADR 0001 D4, D13) |
| `Topic` | remove | P3: the topic form is transport policy; the MQTT definition builds it from `TopicRoot` and the field station name (spaces to `-`) |
| `Railroad` | remove | P2: only `Topic` used it; title block comment 4 records the railroad |
| `Broker` | keep, on the transport symbol | transport parameter |
| `Port`, `Baud` | keep, on the transport symbol | transport parameters |

Placement (proposal). One `CODELINE` on each interlocking sheet of the CTC machine project, as today.
One encoding symbol and one transport symbol for each code line, on the root sheet, joined to every
`CODELINE` pin by a global label. The net then names the code line instance; `Broker` is written once
(P1). Today's rule ("same transport and same `Broker` = one instance") becomes a check. The alternative
is one encoding and one transport symbol on every sheet, with the instance derived as today (request 7).

A virtual target needs nothing drawn. A sheet with no `CODELINE` is valid. The `VIRTUAL` default in the
controller compiler goes.

### Operator roles

- Dispatcher: `CtcMachine`, `Kind` = `DISPATCHER`. The only role drawn.
- Tower operator: reserved as Role `MACHINE`, `Kind` = `TOWER_OPERATOR` (direct to a locking bed, no
  code line). Where it is drawn (plant project or its own project) is not designed.
- Maintainer: reserved `Kind` = `MAINTAINER` (maintenance or debug mode, without the interlocking). Not
  designed. Fascia devices and service modes have their own ADR (ADR 0001, still open item 4).

### What names the interlocking

Today: `--plant-name` on the command line, else the file stem; the folder name for membership; the
sheet name on the CTC machine side. The sources disagree. The linker pairs plant and desk sheet today by
removing whitespace, a rule that ADR 0001 D12 (amended) withdraws.

| Option | What is drawn | Cost |
|---|---|---|
| A. `INTERLOCKING` symbol | One symbol, Role `INTERLOCKING`, no pins, in each plant project. Value = the name; it may display `${TITLE}` | A new library symbol; 6 placements. Exactly one per plant project, else an error. Symmetric with `MAIN HOUSE`. Works for one or several control points. The name is free of file system limits. The desk sheet name must equal it (case folded) |
| B. Field on `MAIN HOUSE` | `Interlocking` = name on every `MAIN HOUSE`, or a flag on one | No new symbol; a script can add the field. On every house: N copies of one fact (P1), all must agree. On one house: moving or deleting that house loses the name. With one control point the field repeats or differs from the Value for no reason |
| C. Title block | The compiler reads `title` (already parsed into `document.title`) | No drawing change except fixing titles. A title is prose for print (`Gilroy Caltrain Station`), not a name, and it is not visible as a model fact. Close to what the owner rejected for `MAIN HOUSE` |

Recommendation: A. Under all options the desk side keeps the sheet name as the join, and the linker
compares names with case folded and spaces replaced by `-` only.

## Consequences

### Counts per project

Watsonville excluded as of 2026-10-01; the owner changed the Watsonville schematic on 2026-10-02; to be
re-checked.

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
| `NextCP` Value: bare interlocking name | 4 | 2 (`~`: hand) | 1 (`Gilroy Caltrain`: hand; as of 2026-10-01, to be re-checked) | 0 | 0 | 1 (`CP_Lick`) | mostly |
| `MaintainerCall`: set Value; remove `CP` | 1 (Value `MC1`) | 0 | 2 (`CP`) | 2 (`CP`) | 0 | 0 | yes |
| `MaintainerCall`: connect pin to `MAIN HOUSE` where not wired | 0 | 0 | 0 | 2 (hand) | 1 (hand) | 0 | hand |
| Dependent derail `CP` emptied | 1 | 0 | 0 | 0 | 1 | 0 | yes |
| Proxy track circuit `CP` emptied | 0 | 1 | 0 | 0 | 0 | 0 | yes |
| Stray fields removed (`Direction`, `Name`, `CP` on IRJ/Bumper) | 0 | 0 | 56 | 0 | 0 | 3 | yes |
| `TC` list to one name | 0 | 0 | 0 | 0 | 0 | 1 | no (request 14) |
| Empty Values on masts or heads | 0 | 0 | 0 | 7 | 0 | 0 | no |
| `Milepost` set (default or `FIXME`) | 3 | 1 | 0 | 0 | 2 | 0 | no |
| Interlocking name (option A) | 1 | 1 | 1 | 1 | 1 | 1 | placement yes |

South-cTc (Watsonville sheet excluded as of 2026-10-01; the owner changed it on 2026-10-02; to be re-checked):

| Change | Count | Script? |
|---|---|---|
| `PanelColumn`: remove `Interlocking`, `Machine`, `Column` | 13 × 3 | yes |
| `PanelColumn`: `CP Name` → `CP`; strip `CP ` (3); `FIXME` → empty (10) | 13 | yes; the 10 values by hand later |
| Lamps: `IndicationToken` → `OfficeIndications`; entry form | 39 | yes for the 30 that resolve; 9 `FIXME` entries by hand |
| `PanelMCall`: remove `ControlToken`, `Vital` | 8 | yes |
| `PanelLock`: new pins, re-wire to driver bits; reset `Kind` on 795 | 7 | no (re-wire by hand) |
| `Codeline-MQTT` → `CODELINE` + encoding + transport | 6 sheets | no (placement and wiring); field values yes |
| `CtcMachine`: `Type` → `PanelStyle`, remove `Era`, add `Kind` | 1 | yes |
| Sheet names equal the interlocking names (`Gilroy CalTrain`, `Gilroy Interchange`; as of 2026-10-01, to be re-checked) | 2 | no (owner picks the spelling) |

A script edits `.kicad_sch` files only when no `~*.lck` exists and KiCad is closed (AGENTS.md). It uses
the existing s-expression helpers; it writes no new parser. `tools/legacy_import/` already edits
properties this way (unverified that it fits).

### Compiler and linker changes

Plant compiler:

1. Classify by library `Role`/`Kind` through `lib_id`; drop `_PART_KIND`. Warn when an instance copy
   differs. This admits `Switch_HandThrow`, `Switch_Powered_NO_TC`, `Switch_Powered_Small`,
   `Track Circuit_Yellow`, `Rule6.13-Yard Limits`, the semaphore heads and `AUXILIARY`.
2. Error when a plant project has no `MAIN HOUSE`; the message states the uncertainty. Warn on a `CP ` or
   `CP_` prefix in any name (a check, not normalization).
3. Read the mast `CP`; during the transition fall back to the IRJ `CP` with a warning.
4. Read policy `Kind` and `Direction`; find dark track by `Kind`; stop requiring `Rulebook`. The compiler
   is behind the library here: the owner replaced `Rulebook` by Kind/Role on purpose.
5. Put maintainer calls and auxiliaries in the model, with the control point from the pin net to
   `MAIN HOUSE`. Then `setupCodec()` loses its hard-coded calls (FieldUnit-Subdivision runtime).
6. Read `IndicationCeiling` (fallback `Indications`).
7. Take the dependent derail's control point from its switch.
8. Recognize the proxy form `<interlocking>:<name>` as a foreign reference.
9. Take the interlocking name from the chosen option; `--plant-name` goes.
10. Read `MAIN HOUSE` `Milepost` for control point order (if request 10 is yes).

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

### Migration order

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
8. Watsonville follows when its schematic is fixed (the owner changed the schematic on 2026-10-02; to be
   re-checked).

### Cost

- A library change in 14 panel and 29 plant symbols, with new symbols (`INTERLOCKING` if option A,
  `CODELINE`, encoding, two transports).
- One script run per project, then hand work (list in step 5).
- Compiler, controller compiler and linker changes above, with a transition period of fallbacks.
- Test and golden updates in their own commit.

## Findings in today's drawings and compilers

These are facts from the inventory, not proposals. Watsonville was excluded as of 2026-10-01 and the
owner changed it on 2026-10-02; to be re-checked.

- Instance copies of `Role` and `Kind` disagree with the library in 15 symbols (Sargent 1,
  GilroyInterchange 2, Christopher 4, Corporal 2, GilroyCalTrain 5, South-cTc 1). Examples are in
  "Principles for a field".
- The controller compiler reads the instance `Kind`, so it treats lock lever 795 as a switch lever. The
  plant compiler reads neither and classifies by symbol name (`_PART_KIND`).
- Compiler defect: policy markers fail outside Luchessa. The compiler requires `Rulebook`
  (`missing_policy_rulebook`), which the library does not carry on purpose (the owner replaced it by
  Kind/Role). Only the five Luchessa instances have `Rulebook` (`251`, `261`, `Rule 6.28`); the other five
  projects fail. The compiler finds dark track by `Rulebook` starting with `6.28`.
- The `Kind` names of policy markers mix Standard Code rule numbers (251, 261) with GCOR-style numbers
  (6.13, 6.28).
- The compiler rejects symbols that are not in `_PART_KIND`: `Switch_Powered_Small`,
  `Switch_Powered_NO_TC`, `Switch_HandThrow` (GilroyCalTrain 2, Sargent 1, Corporal 1), `Track Circuit_Yellow`
  (GilroyCalTrain 3), `Rule6.13-Yard Limits`, `Switch_Powered_Derail_TC`, the semaphore heads and
  `AUXILIARY`. `Switch_Powered_Derail_TC`, the semaphore heads and `AUXILIARY` are not drawn.
- The `Milepost` default `79.0` was never set in Luchessa (all three). Sargent and Corporal have `FIXME`.
- Instances carry `Rulebook` (Luchessa, 5), `Indications` (none drawn; the compiler reads it) and stray
  `Direction`/`Name` (GilroyInterchange, 27 and 29).
- The `Route` symbol and `Milepost` entities are read by no phase. `Route` is not drawn.
- Mast `CP` is drawn on 6 masts (GilroyInterchange 2, Christopher 4) and not read. The IRJ `CP` is today
  the only source of a mast's control point.
- Sargent TC4 is a proxy circuit with `CP` = `Corporal`.
- GilroyCalTrain 771 has `TC` = `771T1, 773T1, 775T1`.
- Luchessa MC1 has Value `~`. Today `MaintainerCall` is in `_PART_KIND` but no phase puts it in the model
  (known gap; `setupCodec()` hard-codes the calls).
- Pin 1 of `Track Circuit` and of `MaintainerCall` and `AUXILIARY` is named `MC`, which misleads.
- `Codeline-MQTT` has `Value` `MQTT`, `Railroad` `SPCoast`, `Broker`, `Topic`
  `ctc/${Railroad}/codeline/${Station}` and `Station` `${SHEETNAME}`. The controller compiler reads
  `Station`, `Broker` and `Topic`, and also looks for `TopicRoot`, which no symbol has. `Codeline-CMRInet`
  has `Station` (`Node UA`), `Port`, `Baud`. Neither has pins.
- No phase reads `Era`, `Interlocking`, `Machine`, `Column`, `Color`, `Vital` or `Railroad` on the panel
  side.
- Lamp `IndicationToken` entries mix circuit names (`795T1`) and tokens (`MC1K`). The `S` default and
  `COLUMN#` default are placeholders.
- `PanelLock` has the same pins as `PanelSwitch`; locks are not in the plant model, so the linker cannot
  check them. `PanelMCall` Value is reported as unchecked.
- `PanelColumn` `CP Name` holds `FIXME` in 10 of 13 columns.
- Spellings of the same interlocking differ between sources, as of 2026-10-01; the owner changed these on
  2026-10-02; to be re-checked. GilroyCalTrain has four spellings: folder `GilroyCalTrain`, title `Gilroy
  Caltrain Station`, desk sheet `Gilroy CalTrain`, and `NextCP` in GilroyInterchange `Gilroy Caltrain`.
  GilroyInterchange: folder and title `GilroyInterchange`, desk sheet `Gilroy Interchange`.
- The linker pairs plant and desk sheet by removing whitespace, a rule that ADR 0001 D12 (amended)
  withdraws.
- `NextCP` Values: GilroyCalTrain `CP_Lick`, Sargent `~` (2), GilroyInterchange `Gilroy Caltrain`.
- Christopher and GilroyCalTrain have no nets in the netlist (components only), so connectivity there is
  not verified. Mast and head Values are empty in Christopher (7).
- The library `Railroad.kicad_sym` changed on 2026-10-02, after every netlist. South-cTc sheets are newer
  than its netlist (2026-09-30 16:12), so its counts can be stale (unverified).

## Appendix: full inventory

Readers today (plant): `plant_graph/compiler.py` (C), `plant_graph/model.py` (M), `plant_graph/routes.py`
(R), `plant_graph/indications.py` (I), `plant_graph/picture.py` (P), `link/linker.py` (L).
Readers today (panel): `controller_graph/compiler.py` (CC) and `link/linker.py` (L). CC reads `Role`,
`Kind`, `Columns`, `Type`, `CP Name`, `Station`, `Broker`, `TopicRoot`, `Topic`, `Port`, `Baud`, `BusKind`,
`IndicationToken`, `ControlToken` and `Value`. No phase reads `Era`, `Interlocking`, `Machine`, `Column`,
`Color`, `Vital` or `Railroad`.

In the tables below, "request n" refers to "Decisions requested" above.

### A1. Plant library (`Railroad.kicad_sym`)

29 symbols, 114 field slots, 11 field names (`CP`, `Direction`, `Head`, `Indication`, `Kind`,
`Milepost`, `Name`, `Role`, `Signal`, `TC`, `Value`). Instances also carry `Rulebook` (Luchessa, 5),
`Indications` (none drawn; the compiler reads it) and stray `Direction`/`Name` (GilroyInterchange, 27
and 29).

#### A1.1 Fields common to every plant symbol

| Field | Today | Proposed | Fact | Phase |
|---|---|---|---|---|
| `Role` | library value on all 29; no plant reader (C classifies by symbol name) | keep; read from the library (P4). Rename value `CONTROLLED_POINT` → `CONTROL_POINT` (retired term) | what the compiler does with the Value and pins | compiler |
| `Kind` | library value on 27; no plant reader | keep; read from the library; the compiler classifies by `Kind`, and `_PART_KIND` goes | the FieldUnit class, or the variant that changes derivation | compiler |
| `Value` | per symbol; read by C | keep; meaning per family below; library default empty (P5) | the railroad name | compiler |

#### A1.2 `MAIN HOUSE`

Pins: 1 `H`. In Luchessa, Sargent and GilroyInterchange pin `H` connects to the `MaintainerCall` pin.

| Field | Today: default · reader | Proposed | Fact | Phase |
|---|---|---|---|---|
| `Value` | empty · C, M (control point list, board order) | keep. Bare name (`Luchessa`, `Gilroy`, `Carnadero`). May display a title block variable (`${COMMENTx}`). No `MAIN HOUSE` in a plant project: error that states the uncertainty (decided) | the control point and its bungalow; on a 506-style encoding also the field station name | compiler, generator |
| `Role` | `CONTROLLED_POINT` · none | rename value → `CONTROL_POINT` | (P7) | compiler |
| `Milepost` | `79.0` · none. Luchessa has `79.0` on all three (the default, never set); Sargent, Corporal `FIXME` | keep, default empty; the compiler reads it to put `controlPoints[]` in geographic order (`layout-model.md` §1) instead of the x coordinate. Owner to confirm (request 10) | the location of the control point | compiler |

#### A1.3 Switches: `Switch_Powered`, `Switch_Powered_Small`, `Switch_Powered_NO_TC`, `Switch_Lock`, `Switch_HandThrow`

Pins: 1 `C`, 2 `N`, 3 `R`. `Kind`: `SWITCH_POWERED` (three symbols), `SWITCH_LOCK`, `SWITCH_MANUAL`.
`Switch_Powered_Small`, `Switch_Powered_NO_TC` and `Switch_HandThrow` are not in `_PART_KIND`; the
compiler rejects them today (GilroyCalTrain 2, Sargent 1, Corporal 1).

| Field | Today: default · reader | Proposed | Fact | Phase |
|---|---|---|---|---|
| `Value` | empty · C | keep: switch number (`783`) | switch name; lever and tokens match it | compiler, linker, generator |
| `CP` | empty · C (checks), M (members), C (board section) | keep. Bare control point name | control point of the switch in the field (control point limits) | compiler; generator (model board; later the hardware sheet) |
| `TC` | `${VALUE}T1` (empty on `NO_TC`, `HandThrow`) · C, R | keep. Exactly one name, or empty for no OS circuit. A list is not allowed (GilroyCalTrain 771 has `771T1, 773T1, 775T1`; request 14) | the OS track circuit that detector-locks the switch | compiler, generator |
| `Indications` | not in library; none drawn · C, I | add to the library as `IndicationCeiling`, default empty. Form `NORMAL/REVERSE`, e.g. `CLEAR/APPROACH` | the most favorable signal indication over the switch in each position (glossary "indication ceiling") | compiler (route `bestIndication`) |

Variants that differ only in a field default or in graphics keep one `Kind`. Removing them is optional.

#### A1.4 Derails: `Switch_Powered_Derail`, `Switch_Powered_Derail_TC`

Pins: 1 `C`, 2 `R` (through path = REVERSE; verified in the library). `Kind` = `DERAIL` on both.
`Switch_Powered_Derail_TC` is not in `_PART_KIND` and is not drawn.

| Field | Today: default · reader | Proposed | Fact | Phase |
|---|---|---|---|---|
| `Value` | empty · C | keep: `<switch>D` (dependent) or its own number (independent) | derail name; dependency on its switch | compiler |
| `CP` | empty · C (mismatch warning) | keep for an independent derail. Empty for a dependent derail: the compiler takes the switch's control point (P1). A value that differs is an error | control point of the derail | compiler |
| `TC` | empty / `${VALUE}T1` · C | keep; same rule as switches | own track circuit, if any | compiler |

`Switch_Powered_Derail_TC` only changes the `TC` default. Remove it, or keep it as a convenience (optional).

#### A1.5 Track circuits: `Track Circuit`, `Track Circuit_Yellow`

Pins: 1 named `MC`. `Kind` = `TRACK_CIRCUIT` on both. `Track Circuit_Yellow` is not in `_PART_KIND`
(GilroyCalTrain uses it 3 times). The difference between the two is graphics only (unverified).

| Field | Today: default · reader | Proposed | Fact | Phase |
|---|---|---|---|---|
| `Value` | empty · C | keep: circuit name (`1NA`), the authoritative name. A foreign circuit uses the proxy form `<interlocking>:<name>` (Sargent `Corporal:2NA`) | track circuit; or a reference to a circuit of another interlocking | compiler; generator (a foreign interlocking: listen on the code line; the same interlocking: local) |
| `CP` | empty · C, M | keep. Empty for a proxy: the circuit is not in this interlocking (Sargent TC4 has `Corporal`) | control point of the circuit | compiler |
| pin 1 name | `MC` | rename the pin name to `T` (number stays 1; the compiler reads numbers) | none (the name misleads) | none |

#### A1.6 Signals: `Mast_Single`, `Mast_Double`, `Mast_Dwarf`, `Signal Head - CL`, `Signal Head - SemaphoreU2`, `Signal Head - SemaphoreU3`, `IRJ-Signal`

Pins: masts 1 `SIGNAL` plus head pins (`H` or `H1`, `H2`); heads 1 `M`; `IRJ-Signal` 1 `A`, 2 `B`, 3
`SIGNAL`. The two semaphore heads are not in `_PART_KIND` and are not drawn.

| Symbol · field | Today: default · reader | Proposed | Fact | Phase |
|---|---|---|---|---|
| Mast `Value` | empty · C, R | keep: `^\d+[NSEW][A-E]+$` (`784EAB`) | mast name; signal number; direction (N/W = LEFT, S/E = RIGHT); its heads | compiler |
| Mast `CP` | not in library. Drawn on 6 masts (GilroyInterchange 2, Christopher 4); not read | add to the library, default empty; the compiler reads it (`layout-model.md` §1: "controlPoint: the mast's drawn CP field") | control point of the mast in the field | compiler |
| `IRJ-Signal` `CP` | empty · M (the only source of a mast's control point today), C (check) | remove after the mast `CP` is filled (P1). The IRJ is `TRACK`; it has no railroad name | (moves to the mast) | none |
| Head `Value` | empty · C | keep: one letter A–E. The compiler checks that the letters of the heads on a mast equal the letters in the mast Value (unverified that it checks today) | head letter | compiler |

#### A1.7 Track terminals: `IRJ`, `Bumper`, `NextCP`

| Symbol · field | Today: default · reader | Proposed | Fact | Phase |
|---|---|---|---|---|
| `IRJ`, `Bumper` | `Value`, `Role`, `Kind` only · C (by reference) | keep; no instance fields. Remove the stray instance `CP` (GilroyCalTrain bumpers 3) and `Direction`/`Name` (GilroyInterchange) | a track graph edge or end | compiler |
| `NextCP` `Value` | empty · R (terminal designation) | keep. Bare name of the neighbor interlocking (`Christopher`, not `CP Christopher`). Owner to confirm interlocking versus control point (request 8). Rename `Kind` `NEXT_CP` → `NEXT_INTERLOCKING` and the symbol to match (request 9; optional; the term "CP" is not a common noun) | the neighbor across this plant edge | compiler; linker (subdivision topology); generator (proxy listening; train progression) |

#### A1.8 Policy markers: `Rule251-DoT-Left`, `Rule251-DoT-Right`, `Rule261-DoT-BiDirectional`, `Rule6.13-Yard Limits`, `Rule6.28-OtherThanMain`

Today the `Kind` names mix Standard Code rule numbers (251, 261) with GCOR-style numbers (6.13, 6.28).
The compiler reads `Rulebook` (not in the library) and `Direction`. It finds dark track by `Rulebook`
starting with `6.28`. Only Luchessa instances have `Rulebook`, so the other five projects fail
`missing_policy_rulebook` today. This is a compiler defect: the owner replaced `Rulebook` by the Kind/Role
mechanism on purpose (2026-10-02), and the compiler must be updated. `Rule6.13-Yard Limits` is not in
`_PART_KIND`.

| Field | Today: default · reader | Proposed | Fact | Phase |
|---|---|---|---|---|
| `Kind` | `RULE_251`, `RULE_261`, `RULE_6.13`, `RULE_6.28` · none | rename to the meaning, not a rule number: `SIGNALED_ONE_DIRECTION`, `SIGNALED_BOTH_DIRECTIONS`, `YARD_LIMITS`, `NOT_SIGNALED` (other than main track, dark). The compiler reads `Kind` (request 3) | the operating method of the track at the marker | compiler |
| `Rulebook` | instance only (Luchessa 5: `251`, `261`, `Rule 6.28`) · C, R, P | remove (decided; P1: `Kind` records it). The description may cite rule numbers as documentation | (in `Kind`) | none |
| `Name` | prose (`Track Signaled in One Direction`); on Left, 6.13, 6.28, not Right · none | remove (P2). Prose goes in the description | none | none |
| `Direction` | `LEFT`, `RIGHT`, `BOTH` · C (required on every marker) | keep on the one-direction markers only (library fact, P4). Remove from the others: `BOTH` is implied by `Kind` | the direction of traffic on one-direction track | compiler |
| `Value` | `RULE 251`, `Rule 261`, `YARD`, `DARK` · C ("track-name Value") | keep: the track name (`MT1`, `Branch`). Library default empty (P5); the defaults are labels, not names | the track name | compiler |

#### A1.9 `Route`

Fields `Signal`, `Head`, `Indication` (`CLEAR`), `Kind` = `ROUTE_INDICATION`. No reader. Not drawn.
Proposed: remove the symbol. `IndicationCeiling` on switches (A1.3) gives the authored input to
`bestIndication`. Keep it only if a route-level override is needed (request 11).

#### A1.10 `MaintainerCall` and `AUXILIARY`

Pins: 1 named `MC` on both. Today `MaintainerCall` is in `_PART_KIND` but no phase puts it in the model
(known gap; `setupCodec()` hard-codes the calls). `AUXILIARY` is not in `_PART_KIND` and is not drawn.

| Symbol · field | Today: default · reader | Proposed | Fact | Phase |
|---|---|---|---|---|
| `MaintainerCall` `Value` | empty · C (name only) | keep: `MC<n>`, unique in the interlocking. Required (Luchessa MC1 has `~`) | the call's name; functions `MC<n>S`, `MC<n>K` | compiler, linker, generator |
| `MaintainerCall` `CP` | not in library; drawn on 4 (GilroyInterchange 2, Christopher 2) · none | do not add. The control point is the `MAIN HOUSE` its pin connects to (P6); do not also require a `CP` field. Remove the 4 instance fields | the bungalow the maintainer is called to | compiler |
| `MaintainerCall` class | none | no field: a maintainer call is always a non-vital control (iteration 11) | (by `Kind`) | generator |
| `AUXILIARY` `Value` | empty · none | keep: the appliance name (switch heater, bungalow door) | auxiliary appliance name | compiler, linker, generator |
| `AUXILIARY` control point | none | pin connection to `MAIN HOUSE` pin `H` (P6); rename pin name `MC` → `H` | the bungalow of the appliance | compiler |
| `AUXILIARY` `Vital` field | none (the class is on the panel symbols today) | add (bool). Class names: FieldUnit ADR 0002 (control transaction classes). See A2.7 for why it moves here (request 4) | how the field unit processes the control: vital (ignored as a group when one is unsafe) or non-vital (processed anyway) | generator (interlocking application) |
| `AUXILIARY` `Functions` | none | add: `CONTROL`, `INDICATION`, or `CONTROL,INDICATION` (proposal) | which functions exist; their names are `<Value>S`, `<Value>K` | generator; linker (lever and lamp cross-check) |

The drawn pin connection records the bungalow of every connected call. It is verified in the Luchessa,
Sargent and GilroyInterchange netlists; in GilroyInterchange the `CP` field also exists and agrees
(MC1, MC2). Christopher and Corporal are not wired. Luchessa MC1 connects to `CP Luchessa`; its panel
lever and lamp are in column 6 (`CP Gilroy`). By ADR 0001 D3 this is not an error.

#### A1.11 `Milepost`

`Value` = `##.#`, `Role` = `ANNOTATION`. Entity made by C; no reader. Keep as documentation; default
empty. No phase reads it.

#### A1.12 Plant hardware sheet (planned, not designed here)

`desk-codeline-kicad-pattern.md` §5a plans a second top-level sheet with a field unit symbol, field
I/O proxies and IODRIVER symbols. Head type (color light, semaphore) belongs there, as field I/O. Not in
scope.

### A2. Panel library (`RailroadPanel.kicad_sym`)

14 symbols, 62 field slots, 21 field names.

#### A2.1 `CtcMachine` (Role `MACHINE`)

| Field | Today: default · reader | Proposed | Fact | Phase |
|---|---|---|---|---|
| `Value` | `SPCoast South cTc` (drawn `SPCoast South`) · CC | keep; default empty | machine name | compiler, generator |
| `Type` | `US&S506` · CC | rename → `PanelStyle`; value names the style, e.g. `LEVER` (a lever panel that is not NX; spelling request 13). The encoding leaves the machine (A2.8) | the panel style. It owns the lever rule (per column: at most one switch or lock lever, at most one signal lever, at least one) and the order of levers and lamps | compiler (lever rule), generator (order) |
| `Columns` | `14` · CC | keep | number of physical columns | compiler, generator |
| `Era` | empty · none | remove (P2). Title block comment 6 already records the era | none | none |
| `Kind` | none | add: `DISPATCHER`. Place for the other operator roles (A2.9) | the operator role the machine serves | compiler, generator |

#### A2.2 `PanelColumn` (Role `COLUMN`)

Pins 1–8 `Column` (all equal; membership only).

| Field | Today: default · reader | Proposed | Fact | Phase |
|---|---|---|---|---|
| `Value` | `COLUMN#` · CC | keep: column number; default empty | column number (known nowhere else) | compiler, generator |
| `CP Name` | empty · CC, L | rename → `CP` (same code name as the plant field; one meaning: a control point name). Bare name. Empty is allowed: the compiler warns; a generator for a 506-style target fails without it. A value that does not resolve to a `MAIN HOUSE` of the sheet's interlocking is an error | the control point (and so the 506-style field station) whose functions this column carries (ADR 0001 D3) | linker, generator |
| `Interlocking` | `Luchessa` · none | remove (P1: the sheet name records it) | none | none |
| `Machine` | `SPCoast South` · none | remove (P1: the one `CtcMachine` of the project) | none | none |
| `Column` | `${VALUE}` · none | remove (P1: copy of Value) | none | none |

#### A2.3 `PanelColumn-MAX7313` (Role `IODRIVER`)

Pins `bit0`–`bit15`. Keep `Value` (bus address, default empty; the library default `8` goes) and
`BusKind` (library fact, P4). Read by CC; used by the generator for the CTC machine application.

#### A2.4 Levers: `PanelSwitch`, `PanelLock`, `PanelSignal` (Role `APPLIANCE`)

| Symbol | Value | Pins today | Proposed |
|---|---|---|---|
| `PanelSwitch` (`SWITCH_LEVER`) | switch name; L matches plant switches | `Column`, `NWS`, `RWS`, `RWK`, `NWK` | keep |
| `PanelLock` (`LOCK_LEVER`) | switch name; L cannot check it (locks not in the model) | `Column`, `NWS`, `RWS`, `RWK`, `NWK` | change pins to `Column`, `WLS`, `WLK`, `NWK`, `RWK`. FieldUnit encodes an electric lock as `WLS` (control) and `WLK` (office indication) (`WireCodec.h`). Whether the field unit also sends `NWK`/`RWK` for a lock switch is unverified (request 12) |
| `PanelSignal` (`SIGNAL_LEVER`) | signal number; L matches plant signals | `Column`, `NGS`, `HS`, `SGS`, `SGK`, `NGK`, `TEK` | keep |

Levers have no fields beyond `Value`, `Role`, `Kind`. Pin names are function names; the generator
reads them through the drive bindings.

#### A2.5 Lamps: `PanelLamp-RED`, `PanelLamp-YELLOW`, `PanelLamp-BLUE` (Kind `LAMP`)

| Field | Today: default · reader | Proposed | Fact | Phase |
|---|---|---|---|---|
| `Value` | `OS` / `TRACK` · none | keep as a free label (KiCad requires a Value); no phase reads it | none | none |
| `Color` | per symbol · none | keep; library fact (P4). `layout-model.md` has `color` on lamps | lamp color | generator (CTC machine screen, simulator) |
| `IndicationToken` | `S` · CC, L | rename → `OfficeIndications`; default empty (the `S` default goes). One form for every entry: office indication names (`795T1K,2NAAK,799T1K`, `MC1K`). Today the entries mix circuit names (`795T1`) and tokens (`MC1K`). Proxy form `<interlocking>:<name>` for a foreign function. Form open (request 5) | the office indications OR'd onto this lamp | linker (resolve), generator |

#### A2.6 `PanelCode` (Kind `CODE`)

`Value` = `CODE` (label). Pins `Column`, `CODE`. Keep. Which field stations one button serves is the
ADR 0001 D9 question; it is not a symbol field.

#### A2.7 `PanelMCall` and `PanelAuxiliary` (Role `APPLIANCE`)

| Symbol · field | Today: default · reader | Proposed | Fact | Phase |
|---|---|---|---|---|
| `PanelMCall` `Value` | `MC1` · L (reported as unchecked) | keep: names the plant `MaintainerCall`; default empty | which call this lever sends | linker, generator |
| `PanelMCall` `ControlToken` | `${VALUE}S` · CC | remove (P1, P3: the function name follows from the Value) | none | none |
| `PanelMCall` `Vital` | `NO` · none | remove: the class of a maintainer call is fixed | none | none |
| `PanelAuxiliary` `Value` | empty · none | keep: names the plant `AUXILIARY` | which auxiliary this lever sends | linker, generator |
| `PanelAuxiliary` `ControlToken` | `${VALUE}S` · CC | remove (P1, P3) | none | none |
| `PanelAuxiliary` `Vital` | `NO` · none | move to the plant `AUXILIARY` as the `Vital` field (A1.10; request 4) | none on the panel | none |

Why the class moves. The class says how the field unit processes a control (iteration 11). The
interlocking application must know it with no CTC machine drawn, for example for a tower operator or a
virtual target. One fact, one place: the plant symbol. The CTC machine does not need it. The class names
(vital, non-vital) come from FieldUnit ADR 0002 (control transaction classes).

#### A2.8 Code line: `CODELINE`, encoding symbol, transport symbol (replace `Codeline-MQTT`, `Codeline-CMRInet`)

Today `Codeline-MQTT` has `Value` `MQTT` (the transport), `Railroad` `SPCoast`, `Broker`, `Topic`
`ctc/${Railroad}/codeline/${Station}` and `Station` `${SHEETNAME}`. CC reads `Station`, `Broker` and
`Topic`, and also looks for `TopicRoot`, which no symbol has. `Codeline-CMRInet` has `Station` (`Node
UA`), `Port`, `Baud`. Neither has pins.

Proposed drawing (ADR 0001 D13, D15). Three symbols for one code line:

| Symbol | Role | Pins | Value | Fields | Phase |
|---|---|---|---|---|---|
| `CODELINE` | `CODELINE` | 1 `ENCODING`, 2 `TRANSPORT` | empty (label) | `Address <field station>`, one per field station that has an authored address (e.g. `Address Luchessa`, `Address Gilroy`). Form open (request 6) | compiler records the addresses and checks them for duplicates; generator uses them, and fails for a target that needs one and does not find it |
| `Encoding` | `ENCODING` | 1 | the name of the encoding definition (`AAR-TOKENS`, `USS-506`; spelling unverified) | none. The definition file in the SPCoast KiCad repo holds the rules (ADR 0001 D10, D11) | compiler (resolves the name), generator |
| `Transport-MQTT` | `TRANSPORT` | 1 | `MQTT` (the transport definition) | `Broker`, `TopicRoot` (`ctc/SPCoast/codeline`) | compiler, generator |
| `Transport-CMRInet` | `TRANSPORT` | 1 | `CMRInet` | `Port`, `Baud`. The node UA is an address: it goes on `CODELINE` | compiler, generator |

Field by field from today:

| Today | Proposed | Reason |
|---|---|---|
| `Value` = transport | the transport symbol's Value | ADR 0001 D1, D15 |
| `Station` = `${SHEETNAME}` | remove | P1: on AAR tokens the field station is the interlocking; on a 506-style encoding it is the `MAIN HOUSE` Value. The generator derives it |
| `Station` = node UA (CMRInet) | `Address <field station>` on `CODELINE` | it is an authored address (ADR 0001 D4, D13) |
| `Topic` | remove | P3: the topic form is transport policy; the MQTT definition builds it from `TopicRoot` and the field station name (spaces to `-`) |
| `Railroad` | remove | P2: only `Topic` used it; title block comment 4 records the railroad |
| `Broker` | keep, on the transport symbol | transport parameter |
| `Port`, `Baud` | keep, on the transport symbol | transport parameters |

Placement (proposal). One `CODELINE` on each interlocking sheet of the CTC machine project, as today.
One encoding symbol and one transport symbol for each code line, on the root sheet, joined to every
`CODELINE` pin by a global label. The net then names the code line instance; `Broker` is written once
(P1). Today's rule ("same transport and same `Broker` = one instance") becomes a check. The alternative
is one encoding and one transport symbol on every sheet, with the instance derived as today (request 7).

A virtual target needs nothing drawn. A sheet with no `CODELINE` is valid. The `VIRTUAL` default in CC
goes.

#### A2.9 Place for the other operator roles

- Dispatcher: `CtcMachine`, `Kind` = `DISPATCHER`. The only role drawn.
- Tower operator: reserved as Role `MACHINE`, `Kind` = `TOWER_OPERATOR` (direct to a locking bed, no
  code line). Where it is drawn (plant project or its own project) is not designed.
- Maintainer: reserved `Kind` = `MAINTAINER` (maintenance or debug mode, without the interlocking). Not
  designed. Fascia devices and service modes have their own ADR (ADR 0001, still open item 4).

### A3. What names the interlocking

Today: `--plant-name` on the command line, else the file stem; the folder name for membership; the
sheet name on the CTC machine side. The sources disagree (as of 2026-10-01; the owner changed these on
2026-10-02; to be re-checked). GilroyCalTrain: folder `GilroyCalTrain`, title `Gilroy Caltrain Station`,
desk sheet `Gilroy CalTrain`, `NextCP` in GilroyInterchange `Gilroy Caltrain`. GilroyInterchange: folder
and title `GilroyInterchange`, desk sheet `Gilroy Interchange`. The linker pairs them today by removing
whitespace, a rule that ADR 0001 D12 (amended) withdraws.

The three options are in "Decision", "What names the interlocking". Recommendation: A.


## Decisions from the owner's responses (2026-10-02)

Requests 1, 2, 4 to 15 are decided as the RESPONSE text above states. In short: A, an `INTERLOCKING`
symbol (1); read `Role`/`Kind` from the library, warn on a differing instance copy, and never key the
compiler on a symbol name (2); `Vital` on the panel auxiliary symbols only (4); lamp entries are the
`IndicationToken` list of tokens, a bare circuit name meaning its `K` token (5); the drawn
transport/encoding structure of ADR 0001 D15 (6, 7); `NextCP` names the neighbor interlocking (8);
the library gains `NextInterlocking` and accepts both until the schematics move (9); keep `Milepost`
(10); `Route` deleted (11); locks share switch tokens for now, the electric lock procedure is deferred
to `docs/review/ElectricLockProcedure.md`, unverified (12); panel style `LEVER` (13); switch 771's `TC`
list is one logical detection block with aggregated detectors (14); industry switches are not
dispatcher controlled and belong with the fascia/local control scope (15).

Request 3 (decided 2026-10-03): the policy marker `Kind` uses Standard Code rule numbers, because the
markers name truths the Standard Code defines and SPCoast models a 1942-1985 SP railroad; the GCOR
equivalent goes in the description. `RULE_251`, `RULE_261`, `RULE_93` (yard limits; PRR 1956 text
confirmed; GCOR 6.13). `RULE_105` for movement on sidings and other than main track (GCOR 6.28): SP Coast Division Rules &
Regulations, effective 1943-02-15, "All movements on sidings must be made with caution" (later
editions: at restricted speed). That book is the reference for SPCoast. Standard Code numbering varied by road; the SP's own
rulebook is the final reference for SPCoast.

Request 14, corrected 2026-10-03 (the first reading was wrong): the `TC` list expresses a **logical
detection block**: several physical track circuits, each with its own detector, treated as one
occupancy for one purpose. The model gains a block entity with member track circuits; a block is
occupied when any member is occupied. The OS section of a switch is a block (usually of one circuit);
route clear lists may name blocks; a desk lamp's `IndicationToken` list is the same idea on the office
side. The code chart decides whether members or the block go on the code line. The general case
stays although the owner redrew this instance. It also serves mixed current and optical detection on
one section, and later ABS and APB blocks.
