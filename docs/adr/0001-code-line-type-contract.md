# 0001. The code line type contract

- Status: accepted
- Date: 2026-10-01

Replaces the spike S2 note (`docs/review/codeline-type-contract.md`, removed). Terms follow FieldUnit
`docs/GLOSSARY.md` (rewritten 2026-10-01).

## Context

### The question

A code line type defines how the CTC machine reaches a field unit. The glossary lists four parts:
addressing, capacity, encoding and timing. This ADR states the contract for addressing, capacity and
encoding, and the phase of the tool chain that owns each fact.

### The test cases

- US&S 506 time code [US&S 506 code line]. 16 steps: 1 conditioning, 7 station selection, 7
  function, 1 delivery. 7 controls and 7 office indications for each field station. 35 field stations
  on one code line. Each step is long or short.
  - Switch control on two steps (N, R). Neither asserted means "do not move".
  - Signal office indication, from one hearsay step list: two steps (L, R). Both long means "time
    release running". So three tokens (`NGK`, `SGK`, `TEK`) ride on two steps. A token is not a step.
  - Step lists are illustrative. The layout owner states the assignment.
- AAR tokens over MQTT. One field station for each field unit. No capacity limit from the type. The
  token is sent as written.
- A future type, invented or from another era.

### Luchessa

The interlocking model has switches 783, 795 and 799, dependent derail 795D, signal 784 (five masts),
and nine track circuits. It has three `MAIN HOUSE` symbols. The `CP` field on each appliance assigns
it to one of them (drawn values, from the model golden):

| Control point (`MAIN HOUSE` Value) | Appliances assigned by the `CP` field | Desk column |
|---|---|---|
| CP Luchessa | 783, 783T1, 1SA, mast 784EAB | 5 (levers 783, 784) |
| CP Gilroy | 795, 795D, 795T1, 2NAA, 2SA, masts 784EC, 784WA | 6 (lever 795, MC1) |
| CP Carnadero | 799, 799T1, 1NA, 2NA, 3NA, masts 784WBC, 784WD | 7 (lever 799, CODE) |

- The CTC machine has one CODE button for the three columns.
- Luchessa is one interlocking with three control points (owner, 2026-10-01). Each `MAIN HOUSE` symbol
  declares one control point and its bungalow. The `CP` field assigns an appliance to a control point.
- Spike S3 (`docs/review/spike-cp-membership.md`) found that the signals alone give the interlocking
  limits (one piece for Luchessa), not the control points. The assignment to control points is a drawn
  fact. Two drawn values disagree with the track graph (784WA, 1NA). The desk lamp for 1NA
  is in column 6 (CP Gilroy) while its `CP` field says CP Carnadero.
- The owner's plan: reduce Luchessa to one control point (one `MAIN HOUSE`) later.

### What the code does today

- One encoding exists twice. The virtual field processor (`spcoast_virtual_plant.cpp`,
  `setupCodec()`) builds its token list from the interlocking model: all nine track circuits, in model
  order, with maintainer calls hard-coded by station name. The CTC machine (`cTcMachine.h`,
  `CtcStation::buildCodec()`) builds its list from desk columns: lamped track circuits only, in column
  order. `AarTextCodec` decodes by position, so the two Luchessa lists differ when read alone. Whether
  the running pair works was not tested (unverified).
- `CtcStation` holds one codec for each interlocking. The glossary says it is the office-side record
  of one field station. The two agree only for MQTT.
- `BitPackedCodec` maps one token to one bit. It cannot carry "both long = `TEK`".
- `AarTextCodec` rejects `SGK` with `NGK`. It accepts `TEK` with either. The encoder does not check.
- Size limits: `MAX_MAP_ENTRIES` = 32 entries per codec, `MAX_APPLIANCES` = 16, `MqttCodeLine`
  buffer 512 bytes. Luchessa uses 14 entries.
- No capacity check exists in `tools/controller_graph/` or `tools/link/`.

## Decision

### D1. A code line type has two axes: encoding and transport

| Axis | States | Examples |
|---|---|---|
| encoding | addressing, capacity, encoding rules, code chart defaults | AAR tokens; US&S 506 (7 + 7); a larger invented encoding |
| transport | how the encoded code is moved, and its parameters | MQTT (`Broker`, `Topic`); LocoNet; serial; a custom relay box; in-process |

A code line type is one encoding on one transport. Examples: AAR tokens over MQTT; 506 over LocoNet;
506 over a custom relay box. The KiCad `CODELINE` Value today names a transport only. It must name both
axes, or two fields must.

### D2. The encoding is per field station

- The encoding axis supplies rules and defaults.
- Each field station has its own code chart: its name, its address, and the ordered steps with the
  encoding rule on each step. What a field station must carry decides its chart.
- For the AAR token encoding the chart is the identity: each function is sent as its token.

### D3. What is grouped, and into what

- Functions (controls and office indications of appliances) are grouped into field stations.
- On a 506-style encoding a field station is a control point: one `MAIN HOUSE` symbol.
  - The `MAIN HOUSE` must have a Value. The Value is the field station name.
  - Names are checked for duplicates. They are never invented. D12 gives the naming rule.
  - An interlocking model with no `MAIN HOUSE` symbol is an error (owner, 2026-10-02). The `MAIN HOUSE`
    symbol is the explicit source of the name. The tooling does not take it from the title block or
    the file name. The symbol can show a title block variable (`${DOCUMENT_NAME}`, `${COMMENTx}`).
- On the AAR token encoding a field unit answers at one field station, named by the interlocking
  (`Luchessa`).
- Two sources can assign an appliance to a control point:

  | Source | Covers | Drawn today |
  |---|---|---|
  | `CP` field on each plant appliance | every appliance with the field | yes (Luchessa: 15 values) |
  | lever column on the CTC machine schematic | switches and signals with a lever; lamps by placement | yes (783 in 5, 795 in 6, 799 in 7) |

  Decision (owner, 2026-10-01): the CTC machine is the source. A field station carries the functions
  of the levers and lamps in its panel column.

  - The dispatcher's control of a signal (left, stop, right) is one function of one lever. It belongs
    to the field station of that lever's column. Example: signal 784 has masts at all three control
    points and one lever in column 5, so `CP Luchessa` carries `784NGS`, `784HS`, `784SGS` and their
    office indications.
  - Routes, masts and the aspects on heads are not code line functions. They are the work of the
    interlocking in the field.
  - Inside one interlocking, an appliance of one control point can serve a function of another field
    station. This is normal. The interlocking makes it work behind the code line. Example: track
    circuit 1NA has `CP` = CP Carnadero, and its lamp is in column 6, so `CP Gilroy` carries `1NAK`.
  - A difference between the `CP` field of an appliance and the column of its lever or lamp is not
    an error. The `CP` field records the control point of the appliance in the field. The column
    records the address that the dispatcher sees.
  - Principle: a field station is the abstraction that the interlocking presents to the dispatcher.
    The interlocking keeps that abstraction true.

### D4. Addresses are authored

- The address of each field station is authored. The tooling never allocates one.
- Reason: an allocation that shifts when the model changes puts firmware images out of step with the
  wire encoding. That can stop the whole running layout.
- A generator that needs an address it does not find reports it and does not emit.

### D5. Capacity is permissive

- The check asks whether the chosen code line type can carry what is drawn. It never requires a
  number of field stations or control points (ontology §6a).
- The check counts steps after the code chart is applied. It never counts tokens or symbol pins.
- A code chart may drop a function (for example an unlamped track circuit). This is allowed. It is
  reported as info, or only under a verbose flag.

### D6. Three phases, and the facts each owns

| Phase | Reads | Owns | Does not do |
|---|---|---|---|
| Compiler and linker | KiCad sources, type definitions | The model: interlocking models, CTC machine models, control points and their names, authored addresses, the drawn code line (the layout's default). Checks: names present, normalized and unique; addresses unique; references resolve; capacity of the drawn default; size limits of the drawn default. | choose a target |
| Generator | the model, type definitions, a target selection | Policy: chooses the code line type (the drawn default, or another target such as virtual or 506); builds each code chart from the type's defaults and the authored overrides, or checks an authored chart; checks capacity and size limits for that target; emits the interlocking application and the CTC machine application with one set of chart tables. | change the model |
| Run time | the emitted applications (or a JSON model loaded by FieldUnit, `PlantSerializer`) | Encoding and decoding by the chart; the `TEK` check (D8); optional size checks when a JSON model is loaded | allocate, group or choose |

- A drawn `Codeline-MQTT` does not limit generation. From the same interlocking model the generator
  can emit a virtual version or a 506 version. The code line type is a generation target. The drawn
  symbol states the layout's default.
- The CTC machine and the field unit read one chart. Neither end builds its own (one source per fact).

### D7. Size limits are checked before run time

`MAX_MAP_ENTRIES`, `MAX_APPLIANCES` and buffer sizes are checked by the compiler or the generator.
FieldUnit can also load a JSON model at run time (`PlantSerializer`), so a run-time check is possible.
It is not required.

### D8. `TEK` with `NGK` or `SGK` is an error

- A field unit never validly asserts `TEK` together with `NGK` or `SGK`. If it happens, it is a logic
  failure or data corruption.
- So the encoding rule "L, R; both long = `TEK`" needs no collapse rule.
- The check:
  - Field unit, before encoding: `timeLocked` with `activeAuthority` LEFT or RIGHT is an internal fault.
    The field unit does not send that office indication and reports the fault (telemetry).
  - CTC machine, on decoding an encoding that can carry the combination (AAR tokens): reject the
    office indication, as `AarTextCodec` rejects `SGK` with `NGK` today.
  - On a 506-style two-step rule the combination cannot be encoded, so a decoder cannot see it. The
    field unit check before encoding is then the only check.

### D9. CODE button on Luchessa: two workarounds, not picked

A true 506 CTC machine has a code button in every column. The SPCoast CTC machine has one CODE button
for Luchessa's three columns, so Luchessa as built is not a true 506 installation. Two workarounds sit
on the encoding axis:

| Workaround | What happens | Effect |
|---|---|---|
| (a) sequence | One CODE press sends one code cycle to each field station of that button, in sequence. | Keeps 506 (7 + 7). Three field stations: CP Luchessa, CP Gilroy, CP Carnadero. The glossary's "code button sends the controls of one field station" gets an exception. |
| (b) larger encoding | One field station with more function steps than 506. | Luchessa needs 10 controls and 18 office indications in one field station (see the worked example). Fits the plan to reduce Luchessa to one control point. Not a prototype type. |

### D10. Type definitions live in the SPCoast KiCad repo

The definitions of encodings and transports live in `~/Dropbox/KiCad/Railroad/SPCoast/`, next to the
South-cTc project. They are layout sources, read by the compiler and the generator.

### D11. Encoding rules are data (truth tables)

The rules of an encoding are tables in its definition file, not named rules in the codec. A table is
less fixed than code, and names in code go stale. Design patterns for common cases can come later.
This choice is provisional: build one worked example, and change it if tables are the wrong form.

### D12. Names: no `CP` prefix in the sources, and no normalization code

- A KiCad name never contains `CP_` or `CP `. A `MAIN HOUSE` Value is the bare name: `Gilroy`, not `CP Gilroy`.
- A model board can put `CP ` in front of a name for display, to match the signs on the railroad.
- Fix every source once. Write no code that adds or strips a prefix.
- Amended 2026-10-02: one normalization is allowed. A name used in an MQTT topic or a key has each
  space replaced by `-`. A space in a topic name is legal but not wanted.
- Consequence to check when the sources are fixed: the interlocking `Luchessa` and its control point
  `Luchessa` then have the same name. They differ by kind only. Today the two are kept apart by the
  prefix (AGENTS.md "Naming"; FieldUnit test `testStationLookupFoldsCaseOnly`).

### D13. Field stations are drawn as encoding instances; the address is a field on each (amended 2026-10-02, second time)

- An encoding that selects stations (US&S 506) is drawn once for each field station. Each instance
  is wired to the `Encoding` pin of its transport. The instance carries:
  - `Station`: the field station name. On a 506-style encoding it equals the control point name,
    the `MAIN HOUSE` Value (bare, D12). The linker joins by this name; a station that names no
    control point is an error.
  - `Address`: the authored address (D4). Required when the encoding's definition has station selection.
- An encoding with no station selection (AAR tokens) is drawn once. Its one field station is the
  interlocking; the transport carries the name (`Transport-MQTT` `Station` = `${SHEETNAME}`) and the
  topic is the address. A space in a name becomes `-` in the topic.
- Adding a field station is placing one more encoding instance. The capacity check (D5) runs for
  each instance.
- Prototype: South-cTc, Luchessa sheet, 2026-10-02: `Encoding2`, `Encoding3`, `Encoding4`
  (`Station` = `Luchessa`, `Gilroy Industry`, `Carnadero`) on `Transport-TimeCode`; `Encoding1`
  (AAR) on `Transport-MQTT`. The `Address` field is not drawn yet. `Gilroy Industry` does not join
  the plant's `CP Gilroy` until the names agree.
- Both earlier forms (fields on `CODELINE`; one field for each station on one encoding instance)
  are withdrawn.

### D14. Scope now: AAR tokens over MQTT

- The first working target is AAR tokens over MQTT.
- A US&S 506 code line is left for later. Nothing in the model or the code may rule it out.
- The CODE button workaround for Luchessa (D9) is not chosen now.

### D15. The `CODELINE` symbol, transports and encodings (amended 2026-10-02 from the owner's prototype)

- One `CODELINE` symbol on a sheet is the interlocking's code line attachment. It has one pin, `Transports`.
- Each transport is a symbol with two pins: `Codeline`, wired to the `CODELINE` symbol, and `Encoding`.
- Each encoding is a symbol with one pin, wired to the `Encoding` pin of one transport.
- One transport with its encoding is one code line type (D1). Several transports on one `CODELINE`
  are several targets for the same interlocking (D6).
- Roles: `CODELINE`, `CODELINE_TRANSPORT`, `CODELINE_ENCODING`. `Kind` names the type definition
  (`MQTT`, `TIMECODE`; `AAR`, `USS506`).
- Prototype: South-cTc, Luchessa sheet: `CODELINE1` with `Transport-MQTT` + `Encoding-AAR` and
  `Transport-TimeCode` + `Encoding-US&S-506`. Verified in the netlist on 2026-10-02.
- The earlier form (one `CODELINE` with one encoding pin and one transport pin) is withdrawn.

### D16. Size limits: each phase checks what it can see

The compiler checks what it can. The generator checks what it can. They see different facts, so their
checks differ. When something breaks, fix it and add a check.

### Worked example: Luchessa

Grouping by panel column (D3). Illustrative chart. Review the track circuit rows against the lamp
columns of the CTC machine schematic: this table was first built from the `CP` field, and 1NA moves
to CP Gilroy. Steps C1–C7 and I1–I7 are cycle steps 9–15.

| Field station | Controls | Steps | Office indications | Steps |
|---|---|---|---|---|
| CP Luchessa | C1 `783NWS`, C2 `783RWS`, C3 `784NGS`, C4 `784HS`, C5 `784SGS` | 5 of 7 | I1 `783NWK`, I2 `783T1K`, I3 `783RWK`, I4 `1SAK`, I5 and I7 signal 784 (L, R: `NGK`, `SGK`, `TEK`), I6 unassigned | 6 of 7 |
| CP Gilroy | C1 `795NWS`, C2 `795RWS`, C3 `MC1S` | 3 of 7 | I1 `795NWK`, I2 `795T1K`, I3 `795RWK`, I4 `2NAAK`, I5 `2SAK`, I6 `MC1K` | 6 of 7 |
| CP Carnadero | C1 `799NWS`, C2 `799RWS` | 2 of 7 | I1 `799NWK`, I2 `799T1K`, I3 `799RWK`, I4 `1NAK`, I5 `2NAK`, I6 `3NAK` | 6 of 7 |
| One control point, 506 | all | 10 of 7: fails | all | 18 of 7: fails |
| AAR over MQTT: `Luchessa` | all, as tokens | no limit | all, as tokens | no limit |

- 795D has no function on the code line.
- The `CP` field of MC1 is not in the model (known gap). Column 6 places it in CP Gilroy.

### Decided by the answers, and still to choose

Decided: D1 to D16.

The form of the type definition is still to choose. The three options of the spike note, re-evaluated:

| Option | Before the answers | What the answers rule out | What remains |
|---|---|---|---|
| A. Data files | Type file in this repo; chart file with field stations listed by control point | The location (D10: SPCoast repo). Listing field stations and membership in the chart file (D3: field stations are `MAIN HOUSE` symbols; membership comes from the `CP` field or lever column). A chart file as the only path: a generation target that was not drawn still needs defaults (D6). | Encoding and transport definition files in the SPCoast repo. Per-field-station overrides and authored addresses in data, keyed by `MAIN HOUSE` name. The generator builds charts from defaults plus overrides. |
| B. Drawn in KiCad | `FieldStation-USS506` symbols with step pins on the CTC machine sheet; encoder symbols | `FieldStation` symbols: they name field stations a second time beside `MAIN HOUSE` (D3). A chart that exists only as nets: it covers the drawn default and not other targets (D6). | Authored addresses and per-station overrides as fields on `MAIN HOUSE` or on the `CODELINE` symbol. Encoder symbols are not needed if rules are data. |
| C. C++ classes in FieldUnit | Type is code; grouping by a field on `PanelColumn`; closed set of rules | Type definitions in FieldUnit (D10). Grouping by desk column as a new field (D3), D3 uses the existing lever column and adds no field. | A generic FieldUnit codec that runs chart tables (all options need it). Encoding rules as named code, if they are not data. |

Decision (owner, 2026-10-01): A, with authored addresses as fields on the `CODELINE` symbol (D13), because the answers
move every fact to a layout source that the generator reads for any target, and A is the only option
that needs no second drawing of field stations.

## Consequences

### For the model and documents

- `desk-codeline-kicad-pattern.md` §2 and §7a ("a station is an interlocking's attachment to exactly
  one codeline"; "one CODE per interlocking sheet (one station)"; "machine-type capacity per column")
  are replaced by D2, D3, D5 and D6.
- `desk-codeline-kicad-pattern.md` §10 and `layout-model.md` `stations[].controlledPoint` ("506 gives
  each CP its own station") are prescriptive. They are replaced by D3 and D5.
- `layout-model.md` `fieldUnits[].station` becomes a list (field unit to field station is 1 : N).
- The `CtcMachine` symbol field `Type` = `US&S506` names a code line encoding as a machine type (F8).
  The encoding moves to the code line. The machine keeps a type of its own (amended 2026-10-02): the
  style of its panel, for example a lever panel that is not NX. The panel style owns the lever rule
  (at most one switch or lock, at most one signal, at least one, for each column) and the order of
  levers and lamps. Another style, such as a glass-panel track plan, can have other rules.
- `PanelColumn` stays a CTC machine fact. By D3 the panel column of a lever or lamp decides which
  field station carries its function.
- A `MAIN HOUSE` without a Value becomes a compile error when a 506-style encoding is the default or a target.

### For the code (not changed by this ADR)

- One generic step codec in FieldUnit runs a code chart at both ends. `BitPackedCodec` cannot do this as is.
- `CtcStation` becomes one per field station. A CODE button can serve several (workaround a).
- The virtual field processor and the CTC machine take their token lists from the emitted chart. The
  hard-coded maintainer calls in `setupCodec()` go.
- `AarTextCodec`: comments call each token a "step"; the header says "any order" while decoding is
  positional; `vitalValid` and `vitalConflictCount_` use "vital" for code line functions (F6). Add the
  D8 check to the encoder and decoder.
- `controller_graph/compiler.py` still has the VIRTUAL transport and empty-sheet default
  (`layout-model.md` rev 7 removed them). The `Codeline-MQTT` symbol has `Railroad`; the compiler
  reads `TopicRoot`.

### Cost

- New definition files for encodings and transports in the SPCoast repo, and a schema for them.
- A generator phase that does not exist yet as a program.
- Authored addresses for every field station of every 506-style target.

### Still open

1. (Closed: the owner approved this ADR on 2026-10-01. Option A, data files, is the decision.)
2. A worked example for D11 (truth tables).
3. The source fix for D12: `MAIN HOUSE` Values, `CP` fields, generated JSON, tests and documents.
4. Local fascia-mounted devices and maintainer service modes: own ADR, later.

### Not verified

- The 506 step lists (hearsay), the station selection pattern, and one code button for each field
  station on the prototype (recall).
- Whether the desk sketch and the virtual field processor agree on the Luchessa token order today.
- The `CP` field of MC1 on the plant side.
