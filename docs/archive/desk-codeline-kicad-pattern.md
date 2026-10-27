# Desk, code line and field: KiCad authoring pattern and logical model

Status: draft for review (2026-09-28; amended 2026-09-29 with §1a, the
placeholder/stub/EMULATED decisions, and implementation status; revised
2026-10-02, see below). Supersedes the desk-binding parts of
`ctc-panel-hardware-binding.md` where they disagree.

Revision 2026-10-02. Terms follow FieldUnit `docs/GLOSSARY.md`. Decisions
follow ADR 0001 (`docs/adr/0001-code-line-type-contract.md`, accepted,
D1–D16) and `ontology.md` rev 5. Section numbers are unchanged.

2026-10-02 (iteration 11): proxy names, MAIN HOUSE required, machine type kept as panel style, operator roles, topic normalization

- Terms: "controlled point", "CP" as a common noun, "station" for a code
  line address, "cTc machine" in prose and "plant host" are replaced by
  control point, field station, CTC machine and virtual field processor.
  "Codeline" in prose is "code line". Code and KiCad names keep their
  spelling. "Desk" stays.
- §2 and §7a: "a column IS a CP", "a station is an interlocking's
  attachment to exactly one codeline", "one CODE per interlocking sheet (one
  station)" and "machine-type capacity per column" are replaced by ADR D2,
  D3, D5, D6 and D9. A panel column is not a control point and not a field
  station. The column of a lever or lamp decides which field station carries
  its function.
- §1, §7a, §10: names carry no `CP_` or `CP ` prefix (D12). The
  interlocking and one of its control points can share a name. The sources
  are not fixed yet.
- §1a, §2, §4, §5, §7: the `CODELINE` symbol gets two pins, one for an
  encoding symbol and one for a transport symbol (D15). Field station
  addresses are fields on the `CODELINE` symbol (D13). `Codeline-VIRTUAL`
  and the "really empty sheet defaults to VIRTUAL" rule are restated: a
  virtual target needs no drawn data. The compiler still has both today.
- §4, §5: `CtcMachine` `Type` = `US&S506` names an encoding. The encoding
  moves to the code line (ADR 0001, consequences). The machine keeps `Type`
  as its panel style (iteration 11).
- Roles (iteration 11): "controller" is not a term for a role. The
  dispatcher's CTC machine is the only role modelled. The tower operator and
  the maintainer are not yet covered. `tools/controller_graph`,
  `parse_kicad_controller.py` and `controllers{}` are code names and keep
  their spelling.
- §4, §7, §10: statements about library defaults and fields now match the
  library as it is today (`CP Name` empty, lamp `IndicationToken` = `S`,
  `Railroad` in place of `TopicRoot`, `Vital` field).
- §6: the three phases (compiler and linker, generator, run time) and the
  facts each owns (D6, D16).
- §8, §9: dated records are kept, with "since then" notes. §9 notes the
  carried-forward rule "behavioral gates, not frozen goldens".
- §10: "506 gives each CP its own station code, a per-column attribute" is
  replaced by D3 and D13. New open items from the ADR are listed.

## 1. Principles

- **The logical model is the only interface.** KiCad projects, via the compiler
  and linker, produce a logical model. Generators (desk sketch, virtual field
  processor, field firmware, software panels) read only that model, never
  `.kicad_sch` or `.net`.
- **Value is the name. References mean nothing.** KiCad re-annotates References
  freely (`SW784` may hold switch `783`). Never derive or check a name from a
  Reference.
- **Symbols declare their role in fields, not in their names.** The compiler
  classifies by the hidden `Role` / `Kind` fields fixed in the library, never by
  symbol or library names. A new implementation is a new symbol, with no
  compiler change.
- **Connectivity comes from the netlist, never from coordinates.** Membership and
  wiring are nets. Pin numbers carry meaning only on IODRIVER symbols (bits).
- **One source per fact.** A fact that can be derived is not authored twice.
  Shortcuts in existing code (`base + (col-1)`, fixed bit constants, hand-copied
  names) are debt, not conventions.
- **Names are case-preserved when produced and compared case-insensitively
  when consumed.** Case is folded. One more normalization: a name used in an
  MQTT topic or a key has each space replaced by `-` (ADR D12, amended).
- **A KiCad name has no `CP_` or `CP ` prefix (ADR D12).** A `MAIN HOUSE`
  Value is the bare name (`Gilroy`). A model board can add `CP ` for display.
  Each source is fixed once; no code adds or strips a prefix. After the fix, the
  interlocking `Luchessa` and its control point `Luchessa` share a name and
  differ by kind. Today the Values still carry the prefix (`CP Luchessa`), to
  be fixed. (This replaces "`Luchessa` and `CP Luchessa` stay distinct".)

Terminology (FieldUnit / CTC; the glossary defines all other terms):

| Term | Meaning | Example |
|---|---|---|
| signal | the dispatcher-controlled signal, one lever | `784` |
| mast | one physical signal location governed by that signal | `784EAB`, `784WD` |
| head | one lamp unit on a mast | `A`, `B` |

## 1a. Three ecosystems, partial inputs

The tooling deals with three ecosystems:
**(1) A Plant Model**: the interlocking's field unit and its physical I/O,
**(2) A CTC Machine Model**: the dispatcher's CTC machine and its physical
I/O (the tower operator's machine and the maintainer's mode are not yet
covered), and
**(3) A Code Line Model**: the code line between them.
A user may provide any or all of these.

We have chosen to leverage KiCad's schematic editor for these source
documents, producing a compiler that converts them into a generalized data
model. This insulates the downstream tooling from dependencies on esoteric
KiCad details, and allows us to replace KiCad with a better domain-aware
editing tool in the future.

- **KiCad schematics are the initial source of Truth.** The user creates
  KiCad schematic models of
  1. Plant trackplans, the appliances they use, the code line it connects to
     and the physical I/O connecting it to the layout;
  2. The lever panel layout of a dispatcher's CTC machine, and the physical
     I/O connecting it to that machine.
- **The compiler generates per-project data models.** The output of the
  compiler is a data model representation of the project as depicted by the
  project's KiCad schematic source material. This model is self-consistent
  and representative of the ecosystems found in the project sources, even
  when those sources are incomplete. The compiler cross-checks the
  integrity of the sources and emits diagnostics as necessary.
- **The linker cross-checks between the three ecosystems.** A CTC machine
  sheet with no interlocking model becomes a **placeholder** (recorded
  status, like a weak symbol), not a failure. An interlocking model with no
  CTC machine sheet is info (M:N, or not on this machine).
- **The generated data model is a cached copy of the project's Truth.**
  It is never edited, only regenerated.
- **Generators use the data model to create artifacts.** The data model
  carries per-interlocking status rich enough for generators to validate and
  use without any knowledge of KiCad. Generators consume the data model,
  validate its suitability for use, and create artifacts (e.g., field unit
  or CTC machine sketches, emulator and simulation applications,
  documentation sets, CMRInet host applications).

Framing use cases (GIVEN/WHEN/THEN):

- GIVEN source data for (**A**) plants only,
  WHEN the layout's data model is created,
  THEN the model will contain (**A**) the plants' field unit models
  AND the model will not contain (**B**) CTC machine models
  AND the model will not contain (**C**) code line models.
  Generators for interlockings will report "no CTC machines defined";
  generators for field units are limited to EMULATED; code lines are
  limited to the virtual target: in-memory passing of data within a single
  app. The virtual target needs no drawn data (ADR D13).
- GIVEN source data for a (**B**) CTC machine only,
  WHEN the layout's data model is created,
  THEN the model will contain (**A**) incomplete plant field unit models
  (no trackplan, no field I/O bindings)
  AND the model will contain (**B**) CTC machine models
  AND the model will contain (**C**) code line models
  AND linker cross-checks will report *unchecked*.
  CTC machine and tower generators will be successful; generators for field
  units will be limited to EMULATED.
- GIVEN SPCoast South as in the frozen netlist
  (`tests/fixtures/kicad/South-cTc.net`, 2026-09-29: one drawn plant, one
  drawn CTC machine interlocking and six stubs),
  WHEN the layout's data model is created,
  THEN the model will contain (**A**) a plant field unit model for
  Luchessa only (others are undefined)
  AND the model will contain (**B**) a CTC machine model for Luchessa only
  (others are placeholders)
  AND the model will contain (**C**) the code line models as drawn.
  The frozen netlist draws `Codeline-VIRTUAL` on every sheet. The live
  South-cTc now draws `Codeline-MQTT` and panel columns on all seven
  sheets. A sheet with no `CODELINE` symbol has no drawn code line; the
  virtual target is still available, because it needs no drawn data
  (ADR D13; §7).
- GIVEN a topology,
  WHEN an interlocking plant's code line type (encoding or transport)
  changes,
  THEN the logical column/appliance model remains unchanged; only the
  CTC machine/interlocking code line details change, and the generator
  builds new code charts (ADR D6).
- GIVEN a topology,
  WHEN an IODRIVER implementation changes,
  THEN only the impacted I/O bindings change.

## 2. Topology

Partly replaced by ADR 0001 (D2, D3, D6). The ADR replaces "each column is
one CP" and "a station is an interlocking's attachment to exactly one
codeline". What stands is kept below.

```
CTC machine (the dispatcher's)  [M:N]  CodeLine  [N:F]  FieldUnit
```

- A **CTC machine** has **panel columns**. A panel column holds levers, lamps
  and code buttons. A panel column is not a control point and not a field
  station.
- An **interlocking** contains one or more **control points**. One `MAIN
  HOUSE` symbol on the plant schematic declares one control point. The
  tooling never derives or counts control points. An interlocking with one
  control point is the simple case.
- A **field station** is one address on a code line, and the controls and
  office indications carried under it. The code line type decides the field
  stations (ADR D3):
  - on a 506-style encoding, each control point is one field station, with
    the same name;
  - on the AAR token encoding, the field unit answers at one field station,
    named for the interlocking.
- **The column of a lever or lamp decides which field station carries its
  function** (ADR D3). A field station is the abstraction that the
  interlocking presents to the dispatcher. Relations between control points
  inside one interlocking are the interlocking's business. The code line
  does not carry them.
- **A code line type is one encoding on one transport** (ADR D1). The drawn
  code line is the layout's default. The generator can emit another target
  from the same model, for example virtual or US&S 506 (ADR D6). The first
  target is AAR tokens over MQTT; nothing may rule out US&S 506 (ADR D14).
- **The code line type and the field-unit implementation are independent:**

  | Code line type (target) | FIELDUNIT.HARDWARE | Meaning |
  |---|---|---|
  | virtual (in-process; needs no drawn data) | EMULATED | in-memory code line to an emulated interlocking in-process |
  | AAR tokens over MQTT | EMULATED | MQTT to an emulated interlocking in another process (today's `spcoast_virtual_plant`) |
  | AAR tokens over MQTT | ESP32 | MQTT to a physical FieldUnit on the layout |
  | … over CMRInet | … | C/MRI node on an RS485 bus |

  `FIELDUNIT.HARDWARE` is not designed yet (see §5a). Today's desk hard-codes
  MQTT + EMULATED; this pattern unwinds that.

## 3. Project layout and roles

```
Railroad/SPCoast/                  folder = membership (no manifest)
  Luchessa/Luchessa.kicad_pro      plant project  (contains MAIN HOUSE symbols)
  South-cTc/South-cTc.kicad_pro    CTC machine project (contains a MACHINE symbol)
    South-cTc.kicad_sch            root sheet: MACHINE
    Luchessa.kicad_sch             one hierarchical sheet per interlocking
    Christopher.kicad_sch …
```

- **A project's role comes from its content, not its name:** MAIN HOUSE means
  an interlocking plant; MACHINE means a CTC machine. A plant
  project with no `MAIN HOUSE` symbol is an error (owner, 2026-10-02). The
  symbol is the explicit source of the name, not the title block and not the
  file name. It can display a title block variable (`${DOCUMENT_NAME}`,
  `${COMMENTx}`).
- **The sheet name is the interlocking name.** It links by name to the plant
  project of the same name.
- **MACHINE appears only in CTC machine projects,** once per machine.

## 4. CTC machine symbols (`RailroadPanel.kicad_sym`)

| Role | Symbol(s) | Value | Key fields / pins |
|---|---|---|---|
| `MACHINE` | CtcMachine | machine name | `Type` (panel style; today's value `US&S506` names an encoding and is to be revised), `Columns`, `Era` |
| `COLUMN` | PanelColumn | **column number** (known nowhere else) | `CP Name` (the control point this column names; see §5); column pins (all equivalent) |
| `APPLIANCE` | PanelSwitch, PanelLock, PanelSignal, PanelMCall, PanelLamp-*, PanelCode, PanelAuxiliary | appliance name (the name in the interlocking model, or a label for lamps) | `Kind`; one `Column` pin; function pins (NWS/RWS/NWK/RWK, NGS/HS/SGS/NGK/SGK/TEK, LAMP, CODE, SW) |
| `IODRIVER` | PanelColumn-MAX7313 (implementation-specific) | bus address (e.g. `0x24`) | `BusKind` (e.g. `I2C-MAX7313`); pins `bitN` |
| `CODELINE` | today: Codeline-MQTT, Codeline-CMRInet | today: **transport type** | `Station`; transport parameters (below) |

- `CtcMachine` `Type` is the panel style of the machine (ADR D3 amendment,
  iteration 11). A lever panel that is not NX is the only style captured now.
  Today's value `US&S506` names an encoding. The encoding moves to the code
  line (ADR 0001, consequences). The `Type` value for the panel style is to
  be chosen. The panel style owns the lever rule (§5, §7a) and the order of
  levers and lamps (§5). A glass-panel track plan can have other rules. `Era`
  is documentation, not a model input (ontology §1).
- `CODELINE`, planned (ADR D15): the `CODELINE` symbol has two pins. One pin
  takes an encoding symbol. The other takes a transport symbol. Each
  encoding and each transport is a one-pin symbol with its own fields. The
  designer connects one of each. Today's `CODELINE` symbols have no pins, and
  their Value names the transport only.
- Authored field station addresses are fields on the `CODELINE` symbol for
  that code line, on that sheet (ADR D13). They are not a per-column
  attribute. The field names are not designed yet.
- Encoding and transport definitions are data files in the SPCoast KiCad
  repo, next to South-cTc (ADR D10, option A). Encoding rules are truth
  tables (ADR D11, provisional).
- `Codeline-VIRTUAL` is removed from the library (2026-09-30,
  `layout-model.md` rev 6). The frozen netlist still has it. A virtual target
  needs no drawn data and is always available (ADR D13). No symbol declares
  it.

Appliance `Kind` values: `SWITCH_LEVER`, `LOCK_LEVER`, `SIGNAL_LEVER`, `LAMP`,
`CODE`, `MAINTAINER_CALL`, `AUXILIARY`.

Lamps: Value is a descriptive label only (OS, TRACK, MC) and nothing reads it.
`IndicationToken` is the comma-separated list of indications OR'd onto the lamp
(`795T1,2NAA,799T1`, `MC1K`). The library default should be empty, so a lamp
with no token is diagnosed rather than silently getting a default. Today the
default on all three `PanelLamp-*` symbols is `S` (to be fixed).

Maintainer calls use `PanelMCall` (`Kind=MAINTAINER_CALL`, `ControlToken=${VALUE}S`, e.g. `MC1S`). `PanelAuxiliary` is for other one-bit appliances (switch heater, bungalow door …). Its `Kind` says which, and it never means a maintainer call.

Both symbols carry a `Vital` field (`NO`). The field states the class of the
control (glossary §5: vital control, non-vital control). The code line is not
vital. A maintainer call is a non-vital control. The field name is settled
(FieldUnit ADR 0002).

`PanelColumn-MAX7313` states one implementation choice: this desk dedicates one
16-bit expander per column. Other machines define their own IODRIVER symbols
(e.g. a neopixel lamp driver). The model has no column–driver relationship.

Code line transport fields (today's symbols):

| Value | `Station` means | Parameters |
|---|---|---|
| `MQTT` | topic level of the field station | `Broker`, `Railroad`, `Topic` (library: `ctc/${Railroad}/codeline/${Station}`); `Station` defaults to `${SHEETNAME}` |
| `CMRInet` | node UA (0–127) | `Port`, `Baud` |

- The `VIRTUAL` row is removed with `Codeline-VIRTUAL` (above).
- `Station` holds one field station name. On AAR tokens over MQTT the field
  unit answers at one field station, named for the interlocking, so
  `Station` is the interlocking name. A 506-style target needs one authored
  address for each field station (ADR D4, D13).
- The library field is `Railroad`. The compiler reads `TopicRoot` (ADR 0001,
  consequences), so it does not see the value today.

The netlist exports field values already resolved, including `${Station}`,
`${Railroad}` and `${SHEETNAME}`, so the compiler never interprets `${…}`.

## 4a. Plant symbols (`Railroad.kicad_sym`): Role and Kind

Agreed 2026-09-30 for the layout-model compiler (`layout-model.md`); the
plant library gets the same hidden `Role` / `Kind` fields as the panel
library, and the compiler stops classifying by symbol name.

**Role answers: what does the compiler do with this symbol's Value and
pins?** A Role is a set of compiler behaviours; that is the test for
choosing one.

| Role | Value | What it enables |
|---|---|---|
| `CONTROLLED_POINT` | control point name | declares the control point (and its bungalow) that `CP` fields point at |
| `APPLIANCE` | railroad name | assigned to a control point by its `CP` field; its functions go to the field station of the panel column that holds its lever or lamp (ADR D3); desk levers and lamps match it by name, the codec cross-checks it; a hardware-sheet proxy can name it to bind field I/O; pins are track connectivity or attachment |
| `COMPONENT` | part label | folded into the appliance it attaches to; never matched by name from outside; I/O binds through the parent's proxy |
| `TRACK` | none (terminals: designation) | pins are edges of the track graph |
| `POLICY` | label | changes how derived facts are computed; fields carry parameters; a pin locates it |
| `ANNOTATION` | label | documentation only |

The Role name `CONTROLLED_POINT` uses a retired term. It is a code name and
stays until it is reviewed (ontology §6).

Masts are appliances (named, assigned to a control point by the `CP` field,
FieldUnit class of their own, I/O via proxy); heads are components. The
signal itself has no symbol: it is derived from masts sharing a number.

**Kind answers: which class does the interlocking logic (FieldUnit
vocabulary) know this as, and which variant changes what the compiler
derives?** A
variant earns a suffix only when it changes derivation. Mechanism and
implementation (powered vs hand-throw, colour-light vs searchlight) stay in
the symbol name and description, so a new implementation is a new symbol
with the same Kind and no compiler change. Kind is empty where variants do
not change derivation (as the panel library does for MACHINE and COLUMN).

| Symbol | Role | Kind |
|---|---|---|
| MAIN HOUSE | `CONTROLLED_POINT` | (empty) |
| Switch_Powered | `APPLIANCE` | `SWITCH_POWERED` |
| Switch_Lock | `APPLIANCE` | `SWITCH_LOCK` |
| Switch_Powered_Derail, Switch_Powered_Derail_TC | `APPLIANCE` | `DERAIL` (the `TC` field says whether it has its own circuit; clear the plain symbol's default) |
| Track Circuit | `APPLIANCE` | `TRACK_CIRCUIT` |
| MaintainerCall | `APPLIANCE` | `MAINTAINER_CALL` |
| Auxiliary (to add: `CP`, `Vital` (name to review, glossary §5), `ControlToken`) | `APPLIANCE` | `AUXILIARY` |
| Mast_Single / Mast_Double / Mast_Dwarf | `APPLIANCE` | `MAST_SINGLE` / `MAST_DOUBLE` / `MAST_DWARF` (head count and dwarf change the FieldUnit mast type) |
| Signal Head - CL | `COMPONENT` | `HEAD` |
| IRJ / IRJ-Signal / Bumper / NextCP | `TRACK` | `IRJ` / `IRJ_SIGNAL` / `BUMPER` / `NEXT_CP` |
| Rule251-DoT-Left, Rule251-DoT-Right | `POLICY` | `RULE_251` (`Direction` distinguishes) |
| Rule261-DoT-BiDirectional | `POLICY` | `RULE_261` |
| Rule6.28-OtherThanMain | `POLICY` | `RULE_6.28` |
| Route | `POLICY` | `ROUTE_INDICATION` (authored override of the derived best indication) |
| Milepost | `ANNOTATION` | (empty) |

Identity placeholders (`CP` = "controlling cp", Value = "XX" / "?" /
"Block Name" / "Neighboring CP?") should default to empty, as for the panel
`CP Name`. The `Type` field on MAIN HOUSE is redundant with Role.

## 5. Relationships and how each is derived

| Relationship | Source | Rule |
|---|---|---|
| appliance ∈ column | net between the appliance `Column` pin and a COLUMN pin | exactly one column per appliance |
| appliance function → drive bit | net between an appliance function pin and an IODRIVER `bitN` pin | the driver is identified by Value and `BusKind`; the bit comes from the pin |
| column ∈ interlocking | the sheet the column is on | code buttons: see §7a (ADR D9) |
| panel column → control point | the column's `CP Name` field | lever rule of the panel style (lever panel, not NX; an error): ≤1 switch/lock lever, ≤1 signal lever, ≥1 of them; `CP Name` is a control point (`MAIN HOUSE` Value) of the interlocking. The column is not the control point. |
| function → field station | the panel column of its lever or lamp (ADR D3) | 506-style encoding: the field station of the control point that the column names (ontology §3.4; unverified); AAR tokens: the one field station of the interlocking |
| interlocking → code line | the CODELINE symbol on the interlocking's sheet | at most one per sheet; it states the layout's default (ADR D6). None: no drawn default; the virtual target is still available (ADR D13) |
| code line instance | **derived**: same Value + same `Broker` (MQTT) or `Port` (C/MRI) | multiple brokers or buses are allowed |
| machine → columns | the CTC machine project | vertical lamp and lever order is a manufacturer standard, not drawn in the schematic. It comes from the machine symbol: the machine `Type`, its panel style (iteration 11). Only the code line encoding leaves the machine. |
| panel appliance ↔ appliance in the interlocking model | by name (Value) | e.g. panel switch `783` ↔ plant switch `783` |

Field station keys on the wire: replace each space with `-` (`Gilroy CalTrain`
becomes `Gilroy-CalTrain`) and compare case-insensitively. Keys must be unique
within a code line instance after this replacement. (ADR D12, amended
2026-10-02: `station_key()` changes from removing whitespace to replacing each
space with `-`. No code adds or strips a `CP` prefix.)

## 5a. Field side: binding plants to hardware (to do)

Plant projects need the same hardware binding the desk now has. Today, field
I/O is hand-coded in each FieldUnit sketch (e.g. `examples/CP_Corporal`:
MCP23017 expanders, `InputBit` / `OutputBit` constants), which is the same debt
the desk had.

**Proposed shape:** a **second top-level sheet** in the plant project. KiCad 10
supports several top-level sheets (`top_level_sheets` in `.kicad_pro`), which
keeps topology and hardware apart:

```
Luchessa/Luchessa.kicad_pro
  Luchessa.kicad_sch            topology sheet (as today): track, switches, masts, control points
  Luchessa-hardware.kicad_sch   hardware sheet: FIELDUNIT, IODRIVERs, field I/O proxies
```

- **The topology sheet stays hardware-free.** The portable plant model
  (`schemas/interlocking-plant/v1.json`) is still compiled from it alone.
- **The hardware sheet mirrors the desk pattern:**
  - **FIELDUNIT symbol** (`Role=FIELDUNIT`): `HARDWARE` = `EMULATED`, `ESP32`,
    `RELAY` …; it names the field processor (glossary §2.4). With `EMULATED`,
    the hardware sheet may contain nothing else.
  - **Field I/O proxies** (`Role=APPLIANCE`): their Value names the plant
    appliance, linked by name exactly as panel levers link to plant switches.
    Their function pins are that appliance's field I/O, for example:
    - switch machine: drive N/R, point detection N/R;
    - track circuit: occupancy;
    - mast/head: head lamps or aspect channels;
    - derail and lock inputs.

    Proxies keep I/O pins off the topology symbols, whose pins (C/N/R, SIGNAL …)
    are track connectivity.
  - **IODRIVER symbols** (expanders, GPIO banks, servo or PWM drivers, C/MRI
    cards), each implementation-specific like `PanelColumn-MAX7313`. Proxy
    function pins connect to driver bits, and the drive binding is read from
    the netlist.
- **The code line is not repeated on the field side.** The interlocking's
  code line and field station addresses come from the CTC machine project's
  sheet for that interlocking (§5). The linker gives the field unit its code
  line. A field unit reachable from several CTC machines (M:N) gets its code
  line from the matched instance.
- **Diagnostics mirror the desk's:**
  - appliance with no proxy (when `HARDWARE` ≠ `EMULATED`);
  - proxy naming no appliance of the interlocking model;
  - proxy function pin not on a driver bit;
  - driver bit used twice.

A plant project with **no hardware sheet implies `HARDWARE = EMULATED`**.
Existing plants stay valid and virtual field unit generation just works; a
physical build requires source data from that sheet.

## 6. Pipeline

```
make netlist   (per project: kicad-cli sch export netlist, rebuilt when a sheet is newer)
   ↓
compile        (per project → fragment: plant or CTC machine)
   ↓
link           (Railroad/SPCoast/*: resolve names, match panel columns to control points, derive code line instances, diagnose)
   ↓
logical model  (JSON; the only input to generators)
   ↓
generators     (desk sketch → arduino-cli compile → upload; virtual field processor; …)
```

The netlist reader must keep each component's sheet path. `kicad_services.NetlistReader`
does so since 2026-09-29 (§8).

Three phases own different facts (ADR D6, D16):

| Phase | Owns | Does not do |
|---|---|---|
| compiler and linker | the model: interlocking models, CTC machine models, control points and their names, authored addresses, the drawn code line (the layout's default); checks on names, addresses, references, and the capacity and size limits of the drawn default | choose a target |
| generator | the target code line type (the drawn default or another, e.g. virtual or US&S 506); one code chart for each field station, from the type's defaults and authored overrides; capacity and size limits for that target; one set of chart tables for both the CTC machine application and the interlocking application | change the model |
| run time | encoding and decoding by the chart; the `TEK` check (ADR D8) | allocate, group or choose |

Each phase checks the size limits it can see (ADR D16). The generator phase
does not exist yet as a program.

`layout-model.md` rev 7 (draft) proposes to replace the per-project fragment
and link shape of this pipeline with one compiler that writes one model.

## 7. Diagnostics

Errors:
- **Netlist with components but zero nets.** The hierarchy is broken: instance
  paths don't match the root sheet UUID. KiCad's ERC does not catch this.
- Appliance with no column, or with more than one column.
- Appliance function pin not on any IODRIVER bit.
- Panel column with more than one switch/lock lever or signal lever, or with none of them.
- Code buttons: today the compiler requires exactly one CODE on each interlocking sheet (`sheet-code-count`). This fits AAR tokens over MQTT, the first target. The rule for a 506-style target is open (ADR D9, D14; §7a).
- Column `CP Name` empty, still the library placeholder, or not a control point (`MAIN HOUSE` Value) of the interlocking.
- Panel appliance whose name matches no appliance of the interlocking model.
- Interlocking sheet with more than one CODELINE symbol. A sheet with none is not an error: it has no drawn default, and the virtual target needs no drawn data (ADR D13). Today the compiler still reports a sheet with columns and no CODELINE (`sheet-codeline-count`).
- Unknown CODELINE Value; C/MRI `Station` that isn't a UA from 0 to 127.
- MQTT `Station` containing `/`, `+` or `#`.
- Duplicate field station key within a code line instance, after the space replacement.
- Duplicate authored field station address within a code line instance (ADR D6; not implemented).
- Inconsistent `Baud` on one C/MRI port.
- Symbol with no `Role`; unknown `Role` or `Kind`.
- A required field still holding its library placeholder (e.g. `CP Name` = `CP NAME` on older placements; `FIXME`). Library defaults for identity fields should be empty.
- Lamp with an empty `IndicationToken`.

Generator errors (ADR D4, D13): a target that needs a fact the model does
not have fails for that target and emits nothing. Example: a US&S 506 target
with no authored field station addresses. A missing symbol is not itself the
fault.

Warnings:
- Multiple `TopicRoot` values on one broker. This is allowed, but usually
  unintended. (The library field is `Railroad`; see §4.)
- Field station key changed by the space replacement — **forensic context
  only**: emitted when the replacement caused an associated finding (e.g. two
  field stations that collide only after space replacement and case
  folding), never as a routine notice on multi-word names, and not for
  literal copy-paste duplicates.

Stub sheets:
- A sheet holding **exactly one CODELINE** and nothing else is a recognized
  **stub**: a declared placeholder for an interlocking not yet drawn on
  this panel. It is exempt from the CODE and lever rules and still
  contributes its code line parameters. Anything in between is still
  validated and can generate warnings and errors. (`layout-model.md` rev 7,
  a draft, proposes to drop `Codeline.stub`; not decided here.)
- A **really empty sheet** — no CODELINE symbol at all — still names an
  interlocking. It has no drawn code line. Nothing is filled in: the virtual
  target needs no drawn data and is always available (ADR D13). A target
  that needs facts the sheet does not have fails in the generator. Without
  any other data the sheet is useless for anything but a doc packet that
  says "TBD". (This replaces "the compiler fills in a defaulted `VIRTUAL`
  codeline". The compiler still does that today: `sheet-empty-defaulted`,
  info. To be removed.)

## 7a. Cross-project consistency: plant project ↔ CTC machine sheet

Partly replaced by ADR 0001 (D2, D3, D5, D6, D9). The ADR replaces "a column
IS a CP", "one CODE per interlocking sheet (one station)" and "machine-type
capacity per column". Pairing, appliances and staying in sync stand.

A plant project (`Luchessa/Luchessa.kicad_pro`) and the CTC machine sheet for
that interlocking (`South-cTc/Luchessa.kicad_sch`) are authored separately and
linked only by name. The **linker** owns keeping them consistent. Each project
first compiles clean on its own (plant compiler and desk compiler
diagnostics); the linker then cross-checks the two fragments.

**Pairing:**
- Each CTC machine interlocking sheet matches exactly one plant project, by
  name (case folded), and the plant's identity name agrees. A sheet
  with no interlocking model becomes a **placeholder**: recorded status,
  cross-checks reported as unchecked, never fatal at link time. It is an
  error only when a generator that needs the pairing (field firmware, a
  verified desk build) is asked to produce that interlocking.
- An interlocking model with no CTC machine sheet is **info**: it may be
  controlled by another CTC machine (M:N), or not yet be on this machine.

**Control points and panel columns.** A panel column is not a control point
(replaces "a column IS a CP"; ADR D3, ontology §5.5).
- A control point is declared by one `MAIN HOUSE` symbol on the plant
  schematic. It is never derived from columns or counted.
- The column's `CP Name` field names one control point. It must match a
  control point (`MAIN HOUSE` Value) of the same interlocking. If it's empty,
  still holds the library placeholder, or matches nothing, that's an
  **error**.
- A panel column has **at most one** switch or lock lever, **at most one**
  signal lever, and **at least one** of them. This is the lever rule of the
  machine's panel style (a lever panel that is not NX). It stays an error for
  this style. It is a rule about **panel levers**. It does not constrain how the plant assigns masts, heads or other
  field equipment to control points. A signal's masts can sit at several
  control points: Luchessa's signal 784 does. Routes and signals span control
  points; the interlocking logic handles them for all control points of the
  interlocking together.
- The column of a lever or lamp decides which field station carries its
  function (ADR D3). A difference between an appliance's `CP` field and the
  column of its lever or lamp is **not an error**. Example: track circuit 1NA
  has `CP` = `CP Carnadero` (to be fixed: `Carnadero`); its lamp is in column
  6, whose `CP Name` is `CP Gilroy`.
- Code buttons (replaces "an interlocking ... with **exactly one** CODE
  button"): a true 506 machine has a code button in every column. The SPCoast
  CTC machine has one CODE button for Luchessa's three columns, so it is not
  a true 506 machine. ADR D9 gives two workarounds for a 506-style target;
  neither is chosen (ADR D14). The compiler's "exactly one CODE per
  interlocking sheet" (§7) fits AAR tokens over MQTT.
- Two columns naming the same control point is an **error**. A control point
  with no column is a **warning** (not dispatcher-controlled from this
  machine).

**Appliances:**
- Every panel appliance names an appliance of the interlocking model **of
  this interlocking**, and the kinds must match:
  - `SWITCH_LEVER` ↔ powered switch
  - `LOCK_LEVER` ↔ switch lock
  - `SIGNAL_LEVER` ↔ signal control
  - `MAINTAINER_CALL` ↔ maintainer call
- Every dispatcher-controlled appliance has a lever. Dependent derails
  (`795D`) are exempt.
- A lamp's `IndicationToken` entries resolve **per interlocking**: to track
  circuits (including derived OS circuits such as `783T1`) or maintainer-call
  indications. Which driver a lamp is wired to is a hardware or model-board
  choice. The column that holds the lamp decides which field station carries
  its office indications (ADR D3). It does not assign the track circuit to a
  control point; the `CP` field does that. (This replaces "which column a
  lamp is wired to carries no CP meaning".)
- A track circuit that no lamp shows is **info**. A code chart may drop a
  function; that is allowed and reported as info (ADR D5).

**Field stations** (replaces **Station**; ADR D2, D3, D5, D6):
- "One CODE per interlocking sheet (one station)" is replaced. The code line
  type decides the field stations (§2). Code buttons: see above.
- The functions of the interlocking, as computed from the interlocking model
  (the same tokens the codec uses), are compared with the levers and lamps
  on its sheet. The model reports any gaps.
- Capacity is permissive. The check asks whether the chosen code line type
  can carry what is drawn. It never requires a number of field stations or
  control points. It counts steps after the code chart is applied, never
  tokens or symbol pins. It belongs to the encoding, for each field station
  (ADR D5). The compiler checks the drawn default; the generator checks each
  target (ADR D6). The AAR token encoding has no capacity limit. (This
  replaces "machine-type capacity, e.g. US&S 506 functions per column, is
  checked against the column's appliances".)

**Staying in sync:**
- Make dependencies do this: each netlist depends on its project's sheets, and
  the linked model depends on every netlist under `SPCoast/`. Editing either
  side rebuilds the model and re-runs the cross-checks.
- The model records the source netlists it was built from (path and content
  hash), so a generator can refuse a stale model.

**Known gap:**
- **Maintainer calls are not in the portable plant model today.** The plant
  schematic has MC symbols, but the model drops them. So the desk's
  `MC1S`/`MC1K` cannot be cross-checked, and the virtual field processor
  (`setupCodec()`) hard-codes maintainer calls by interlocking name (debt).
  The plant model must carry them. The hard-coded calls go when both ends
  read the emitted code chart (ADR 0001, consequences).

**Prototype check against Luchessa (2026-09-28):**
- **Lever counts:** columns 5/6/7 each have one switch lever (783/795/799);
  column 5 also has signal lever 784. All satisfy the lever rule.
- **`CP Name`:** still the library placeholder `CP NAME` on all three columns,
  so it is flagged as unset. Since then: the columns name `CP Luchessa`,
  `CP Gilroy`, `CP Carnadero` (to be fixed to bare names, ADR D12); the other
  sheets of the live South-cTc hold `FIXME`.
- **Switches:** every plant switch has a lever; 795D is exempt as a dependent
  derail.
- **Lamp tokens:** all resolve within the interlocking.
- **Unlamped track circuits (info):** 1SA, 2NA, 2SA, 3NA.

## 8. Verified by playtest (2026-09-28, throwaway prototype)

Run against the South-cTc netlist (Luchessa sheet), with no input other than
the netlist:

- **Column membership:** all 10 appliances resolve to exactly one column.
- **Drive bits:** all resolve, and match the hand-written
  `examples/spcoast_ctc/IO-I2C.h`:
  - switch NWS/RWS/NWK/RWK on bits 7/6/0/1;
  - signal NGS/HS/SGS on 9/10/11 and NGK/SGK/TEK on 13/14/15;
  - track lamps on 3/4, MC lamp on 8, MC switch on 2, CODE on 12.
- **Code lines:** all 7 sheets carry one code line (currently VIRTUAL). Nested
  field references export resolved: `Topic` exports as
  `ctc/SPCoast/codeline/Luchessa`. (Since then the library has no
  `Codeline-VIRTUAL`, and the live South-cTc draws `Codeline-MQTT` on all
  seven sheets. The frozen netlist is unchanged.)
- **ERC:** 0 violations after the root-UUID repair and the symbol clean-ups.

**Implemented 2026-09-29** (`tools/controller_graph/`, `tools/link/`,
`parse_kicad_controller.py`, `link_subdivision.py`; 50 new tests): the
reader keeps sheetpaths and design-section sheet lists; controller
compiler with §7 diagnostics, stub recognition and empty-sheet
defaulting; linker with §7a cross-checks, placeholders, code line
instances, source hashes and JSON emission. Golden test: generated
bindings match hand-written `examples/spcoast_ctc/IO-I2C.h` exactly.
Negative fixtures cover §7 (incl. zero-nets) and §7a. Still open:
function coverage and capacity checks (§7a; capacity as ADR D5 states it),
the second-implementation fixture (§9), field side (§5a). The compiler
still implements "a column IS a CP" in its comments and types, the VIRTUAL
transport, stubs and the empty-sheet default (§7).

## 9. Test plan

Ontology rev 5 §6 carries forward "use behavioral gates for regression, not
frozen goldens". The golden below exists; new checks should be behavioral
gates.

- **Golden:** from the Luchessa sheet plus the Luchessa plant, generate the
  column/appliance/bit bindings and check them against today's hand-written
  `configureDesk()` / `IO-I2C.h`.
- **Generality:** include a second, different CTC machine implementation as a
  test fixture, e.g. lamps on a neopixel IODRIVER and levers on another
  expander type. It must compile to the same logical column/appliance model.
- **Negative fixtures:** one for each error in §7, including the broken-root-UUID
  netlist.

## 10. Open items and known debt

- **Field hardware binding (§5a):**
  - design the FIELDUNIT symbol (`HARDWARE` = EMULATED / ESP32 / relay …);
  - design the field I/O proxy symbols;
  - add a hardware top-level sheet to Luchessa;
  - golden-test the result against a hand-written field sketch's I/O.
- **US&S 506 code line** (replaced; ADR D3, D4, D5, D13, D14): on a
  506-style encoding each control point is one field station, with the same
  name. Its address is authored as a field on the `CODELINE` symbol, not as
  a per-column attribute. The first target is AAR tokens over MQTT; nothing
  may rule out US&S 506. (This replaces "it gives each CP its own station
  code; that becomes a per-column attribute".)
- **Code line types** (ADR D1, D10, D11, D15): draw the two-pin `CODELINE`
  symbol and the encoding and transport symbols; write the definition files
  and their schema in the SPCoast KiCad repo; build the truth-table worked
  example.
- **CODE button at Luchessa** (ADR D9, D14): choose a workaround when a 506
  target is built.
- **Names** (ADR D12): fix `MAIN HOUSE` Values, `CP` fields and `CP Name`
  (`CP Luchessa`, `CP Gilroy`, `CP Carnadero`; `FIXME` on the other sheets),
  the generated JSON, tests and documents. The linker's `cp-unmatched` then
  compares bare names.
- **CTC machine compiler** (`tools/controller_graph`; ADR 0001, consequences): remove the VIRTUAL
  transport and the empty-sheet default; accept a sheet with no CODELINE;
  read the MQTT field the library has (`Railroad`, not `TopicRoot`); treat
  `FIXME` as a placeholder.
- **M:N CTC machines:** two CTC machines sharing a code line. Each CTC
  machine project carries its own code line symbols; the linker
  matches them into one instance.
- **Library clean-ups:**
  - `PanelColumn` defaults carry SPCoast values (`Interlocking`, `Machine`), and
    its `Column` field (`${VALUE}`) repeats Value. `Interlocking` and `Machine`
    are derivable from the sheet and project.
  - Code line defaults carry SPCoast values (`Broker`, `Railroad`, `Port`).
  - `PanelColumn` `CP Name` now defaults to empty (done).
  - `PanelLamp-*` `IndicationToken` defaults to `S`, not empty (to fix).
  - `CtcMachine` `Type` = `US&S506` names an encoding. The encoding moves to
    the code line (ADR 0001, consequences). `Type` stays as the panel style.
  - `PanelMCall` and `PanelAuxiliary` carry `Vital` = `NO`. The field states
    the class of the control: vital or non-vital (glossary §5). The code line is
    not vital.
  - `PanelLock` function pins are `NWS`/`RWS`/`NWK`/`RWK`. The glossary's
    electric lock tokens are `WLS`/`WLK`. Review.
- **Plant compiler:** it still maps library part names to kinds (`_PART_KIND`
  in `tools/plant_graph/compiler.py`). It should move to `Role` / `Kind` fields
  like the panel library. Review the Role name `CONTROLLED_POINT` against the
  retired term (ontology §6).
- **FieldUnit `cTcMachine`:** it conflates codec track circuits with lamp slots
  (`withTrackLamps`). An `IndicationToken` list can drive one lamp from several
  circuits.
- **Two diagnostic types:** `plant_graph` (enum severities) and
  `controller_graph` (string severities) each define their own Diagnostic,
  so printers and filters cannot be shared across the plant and controller
  pipelines. Unify when the plant compiler moves to `Role`/`Kind` fields.
- **Locks are not in the portable plant model** (like maintainer calls):
  a `LOCK_LEVER` is reported `lock-uncheckable` (info) until they land.
