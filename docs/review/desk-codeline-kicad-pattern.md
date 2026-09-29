# Desk, codeline and field: KiCad authoring pattern and logical model

Status: draft for review (2026-09-28; amended 2026-09-29 with §1a, the
placeholder/stub/EMULATED decisions, and implementation status). Supersedes
the desk-binding parts of `ctc-panel-hardware-binding.md` where they
disagree.

## 1. Principles

- **The logical model is the only interface.** KiCad projects, via the compiler
  and linker, produce a logical model. Generators (desk sketch, plant host, field
  firmware, software panels) read only that model, never `.kicad_sch` or `.net`.
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
  when consumed.** Only case is folded, so interlocking `Luchessa` and its
  controlled point `CP Luchessa` stay distinct.

Terminology (FieldUnit / cTc):

| Term | Meaning | Example |
|---|---|---|
| signal | the dispatcher-controlled signal, one lever | `784` |
| mast | one physical signal location governed by that signal | `784EAB`, `784WD` |
| head | one lamp unit on a mast | `A`, `B` |

## 1a. Three ecosystems, partial inputs

The tooling deals with three ecosystems:
**(1) A Plant Model**: the interlocking's field unit and its physical I/O,
**(2) A Controller Model**: the controller (desk, tower panel, software
panel) and its physical I/O, and
**(3) A Codeline Model**: the codeline between them.
A user may provide any or all of these.

We have chosen to leverage KiCad's schematic editor for these source
documents, producing a compiler that converts them into a generalized data
model. This insulates the downstream tooling from dependencies on esoteric
KiCad details, and allows us to replace KiCad with a better domain-aware
editing tool in the future.

- **KiCad schematics are the initial source of Truth.** The user creates
  KiCad schematic models of
  1. Plant trackplans, the appliances they use, the codeline it connects to
     and the physical I/O connecting it to the layout;
  2. Tower operator's / dispatcher cTc machine's lever panel layout and the
     physical I/O connecting it to the cTc machine.
- **The compiler generates per-project data models.** The output of the
  compiler is a data model representation of the project as depicted by the
  project's KiCad schematic source material. This model is self-consistent
  and representative of the ecosystems found in the project sources, even
  when those sources are incomplete. The compiler cross-checks the
  integrity of the sources and emits diagnostics as necessary.
- **The linker cross-checks between the three ecosystems.** A controller
  sheet with no plant model becomes a **placeholder station** (recorded
  status, like a weak symbol), not a failure. A plant with no controller
  sheet is info (M:N, or not on this machine).
- **The generated data model is a cached copy of the project's Truth.**
  It is never edited, only regenerated.
- **Generators use the data model to create artifacts.** The data model
  carries per-station status rich enough for generators to validate and
  use without any knowledge of KiCad. Generators consume the data model,
  validate its suitability for use, and create artifacts (e.g., fieldunit
  or cTc machine sketches, emulator and simulation applications,
  documentation sets, CMRInet host applications).

Framing use cases (GIVEN/WHEN/THEN):

- GIVEN source data for (**A**) plants only,
  WHEN the layout's data model is created,
  THEN the model will contain (**A**) the plants' field unit models
  AND the model will not contain (**B**) controller models
  AND the model will not contain (**C**) codeline models.
  Generators for interlockings will report "no controllers defined";
  generators for field units are limited to EMULATED; codelines are
  limited to the simple in-memory passing of data within a single app.
- GIVEN source data for a (**B**) controller only,
  WHEN the layout's data model is created,
  THEN the model will contain (**A**) incomplete plant field unit models
  (no trackplan, no field I/O bindings)
  AND the model will contain (**B**) controller models
  AND the model will contain (**C**) codeline models
  AND linker cross-checks will report *unchecked*.
  cTc machine/tower generators will be successful; generators for field
  units will be limited to EMULATED.
- GIVEN today's SPCoast South (one drawn plant, one drawn controller
  interlocking and six stubs),
  WHEN the layout's data model is created,
  THEN the model will contain (**A**) a plant field unit model for
  Luchessa only (others are undefined)
  AND the model will contain (**B**) a controller model for Luchessa only
  (others are placeholder stations)
  AND the model will contain (**C**) the codeline models as drawn
  (`Codeline-VIRTUAL` today); a really empty sheet defaults to VIRTUAL
  (§7).
- GIVEN a topology,
  WHEN an interlocking plant's codeline transport changes,
  THEN the logical column/appliance model remains unchanged; only the
  controller/interlocking codeline details change.
- GIVEN a topology,
  WHEN an IODRIVER implementation changes,
  THEN only the impacted I/O bindings change.

## 2. Topology

```
Controller (desk, tower panel, software panel)  [M:N]  CodeLine  [N:F]  FieldUnit
```

- A **controller** has columns; each column is one **controlled point (CP)**.
- An **interlocking** owns one or more CPs uniquely. A CP that is its own
  interlocking is the degenerate case.
- A **station** is an interlocking's attachment to exactly one codeline.
  Its control and indication messages carry the tokens of all of its CPs.
- **The codeline transport and the field-unit implementation are independent:**

  | CODELINE | FIELDUNIT.HARDWARE | Meaning |
  |---|---|---|
  | VIRTUAL | EMULATED | in-memory codeline to an emulated plant in-process |
  | MQTT | EMULATED | MQTT to an emulated plant in another process (today's `spcoast_virtual_plant`) |
  | MQTT | ESP32 | MQTT to a physical FieldUnit on the layout |
  | CMRInet | … | C/MRI node on an RS485 bus |

  `FIELDUNIT.HARDWARE` is not designed yet (see §5a). Today's desk hard-codes
  MQTT + EMULATED; this pattern unwinds that.

## 3. Project layout and roles

```
Railroad/SPCoast/                  folder = membership (no manifest)
  Luchessa/Luchessa.kicad_pro      plant project  (contains MAIN HOUSE symbols)
  South-cTc/South-cTc.kicad_pro    controller project (contains a MACHINE symbol)
    South-cTc.kicad_sch            root sheet: MACHINE
    Luchessa.kicad_sch             one hierarchical sheet per interlocking
    Christopher.kicad_sch …
```

- **A project's role comes from its content, not its name:** MAIN HOUSE means
  an interlocking plant; MACHINE means a controller.
- **The sheet name is the interlocking name.** It links by name to the plant
  project of the same name.
- **MACHINE appears only in controller projects,** once per machine.

## 4. Controller symbols (`RailroadPanel.kicad_sym`)

| Role | Symbol(s) | Value | Key fields / pins |
|---|---|---|---|
| `MACHINE` | CtcMachine | machine name | `Type` (e.g. `US&S506`), `Columns`, `Era` |
| `COLUMN` | PanelColumn | **column number** (known nowhere else) | `CP Name` (the CP this column is); column pins (all equivalent) |
| `APPLIANCE` | PanelSwitch, PanelLock, PanelSignal, PanelMCall, PanelLamp-*, PanelCode, PanelAuxiliary | appliance name (plant name, or label for lamps) | `Kind`; one `Column` pin; function pins (NWS/RWS/NWK/RWK, NGS/HS/SGS/NGK/SGK/TEK, LAMP, CODE, SW) |
| `IODRIVER` | PanelColumn-MAX7313 (implementation-specific) | bus address (e.g. `0x24`) | `BusKind` (e.g. `I2C-MAX7313`); pins `bitN` |
| `CODELINE` | Codeline-VIRTUAL, Codeline-MQTT, Codeline-CMRInet | **transport type** | `Station`; transport parameters (below) |

Appliance `Kind` values: `SWITCH_LEVER`, `LOCK_LEVER`, `SIGNAL_LEVER`, `LAMP`,
`CODE`, `MAINTAINER_CALL`, `AUXILIARY`.

Lamps: Value is a descriptive label only (OS, TRACK, MC) and nothing reads it.
`IndicationToken` is the comma-separated list of indications OR'd onto the lamp
(`795T1,2NAA,799T1`, `MC1K`). The library default is empty, so a lamp with no
token is diagnosed rather than silently getting a default.

Maintainer calls use `PanelMCall` (`Kind=MAINTAINER_CALL`, `ControlToken=${VALUE}S`, e.g. `MC1S`). `PanelAuxiliary` is for other one-bit appliances (switch heater, bungalow door …). Its `Kind` says which, and it never means a maintainer call.

`PanelColumn-MAX7313` states one implementation choice: this desk dedicates one
16-bit expander per column. Other machines define their own IODRIVER symbols
(e.g. a neopixel lamp driver). The model has no column–driver relationship.

Codeline transport fields:

| Value | Station means | Parameters |
|---|---|---|
| `VIRTUAL` | station key | none |
| `MQTT` | topic station level | `Broker`, `TopicRoot`, `Topic` (e.g. `ctc/${TopicRoot}/codeline/${Station}`) |
| `CMRInet` | node UA (0–127) | `Port`, `Baud` |

The netlist exports field values already resolved, including `${Station}`,
`${TopicRoot}` and `${SHEETNAME}`, so the compiler never interprets `${…}`.

## 5. Relationships and how each is derived

| Relationship | Source | Rule |
|---|---|---|
| appliance ∈ column | net between the appliance `Column` pin and a COLUMN pin | exactly one column per appliance |
| appliance function → drive bit | net between an appliance function pin and an IODRIVER `bitN` pin | the driver is identified by Value and `BusKind`; the bit comes from the pin |
| column ∈ interlocking | the sheet the column is on | an interlocking has exactly one CODE |
| column = CP | identity: the column is the CP, named by its `CP Name` field | ≤1 switch/lock lever, ≤1 signal lever, ≥1 of them; `CP Name` is a plant CP (MAIN HOUSE) of the interlocking |
| interlocking → codeline | the single CODELINE symbol on the interlocking's sheet | exactly one per sheet |
| codeline instance | **derived**: same Value + same `Broker` (MQTT) or `Port` (C/MRI) | multiple brokers or buses are allowed |
| machine → columns | the controller project | vertical lamp and lever order comes from the machine `Type` (manufacturer standard), not from the schematic |
| panel appliance ↔ plant appliance | by name (Value) | e.g. panel switch `783` ↔ plant switch `783` |

Station keys on the wire: remove whitespace (`Gilroy CalTrain` becomes
`GilroyCalTrain`) and compare case-insensitively. Keys must be unique within a
codeline instance after this normalisation.

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
  Luchessa.kicad_sch            topology sheet (as today): track, switches, masts, CPs
  Luchessa-hardware.kicad_sch   hardware sheet: FIELDUNIT, IODRIVERs, field I/O proxies
```

- **The topology sheet stays hardware-free.** The portable plant model
  (`schemas/interlocking-plant/v1.json`) is still compiled from it alone.
- **The hardware sheet mirrors the desk pattern:**
  - **FIELDUNIT symbol** (`Role=FIELDUNIT`): `HARDWARE` = `EMULATED`, `ESP32`,
    `RELAY` …. With `EMULATED`, the hardware sheet may contain nothing else.
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
- **The codeline is not repeated on the field side.** The interlocking's
  codeline and Station come from the controller project's sheet for that
  interlocking (§5). The linker gives the field unit its codeline. A field unit
  reachable from several controllers (M:N) gets its codeline from the matched
  instance.
- **Diagnostics mirror the desk's:**
  - plant appliance with no proxy (when `HARDWARE` ≠ `EMULATED`);
  - proxy naming no plant appliance;
  - proxy function pin not on a driver bit;
  - driver bit used twice.

A plant project with **no hardware sheet implies `HARDWARE = EMULATED`**.
Existing plants stay valid and virtual-plant generation just works; a
physical build requires source data from that sheet.

## 6. Pipeline

```
make netlist   (per project: kicad-cli sch export netlist, rebuilt when a sheet is newer)
   ↓
compile        (per project → fragment: plant or controller)
   ↓
link           (Railroad/SPCoast/*: resolve names, match columns to plant CPs, derive codeline instances, diagnose)
   ↓
logical model  (JSON; the only input to generators)
   ↓
generators     (desk sketch → arduino-cli compile → upload; plant host; …)
```

The netlist reader must keep each component's sheet path; the current
`kicad_services.NetlistReader` drops it.

## 7. Diagnostics

Errors:
- **Netlist with components but zero nets.** The hierarchy is broken: instance
  paths don't match the root sheet UUID. KiCad's ERC does not catch this.
- Appliance with no column, or with more than one column.
- Appliance function pin not on any IODRIVER bit.
- Column with more than one switch/lock lever or signal lever, or with none of them; interlocking sheet without exactly one CODE.
- Column `CP Name` empty, still the library placeholder, or not a plant CP of the interlocking.
- Panel appliance whose name matches no plant appliance.
- Interlocking sheet with no, or more than one, CODELINE symbol.
- Unknown CODELINE Value; C/MRI Station that isn't a UA from 0 to 127.
- MQTT Station containing `/`, `+` or `#`.
- Duplicate station key within a codeline instance, after normalisation.
- Inconsistent `Baud` on one C/MRI port.
- Symbol with no `Role`; unknown `Role` or `Kind`.
- A required field still holding its library placeholder (e.g. `CP Name` = `CP NAME`). Library defaults for identity fields should be empty.
- Lamp with an empty `IndicationToken`.

Warnings:
- Multiple `TopicRoot` values on one broker. This is allowed, but usually
  unintended.
- Station key changed by normalisation — **forensic context only**: emitted
  when the normalisation caused an associated finding (e.g. two stations
  that collide only after whitespace removal and case folding), never as a
  routine notice on multi-word stations, and not for literal copy-paste
  duplicates.

Stub sheets:
- A sheet holding **exactly one CODELINE** and nothing else is a recognized
  **stub**: a declared placeholder for an interlocking not yet drawn on
  this panel. It is exempt from the one-CODE and lever rules and still
  contributes its codeline parameters. Anything in between is still
  validated and can generate warnings and errors.
- A **really empty sheet** — no codeline symbol at all — still names an
  interlocking: the compiler fills in the blank with a defaulted `VIRTUAL`
  codeline (Station = sheet name, marked `defaulted`, info diagnostic).
  Without any other data it is useless for anything but a doc packet that
  says "TBD".

## 7a. Cross-project consistency: plant project ↔ controller sheet

A plant project (`Luchessa/Luchessa.kicad_pro`) and the controller sheet for
that interlocking (`South-cTc/Luchessa.kicad_sch`) are authored separately and
linked only by name. The **linker** owns keeping them consistent. Each project
first compiles clean on its own (plant compiler and desk compiler
diagnostics); the linker then cross-checks the two fragments.

**Pairing:**
- Each controller interlocking sheet matches exactly one plant project, by
  name after normalisation, and the plant's identity name agrees. A sheet
  with no plant becomes a **placeholder station**: recorded status,
  cross-checks reported as unchecked, never fatal at link time. It is an
  error only when a generator that needs the pairing (field firmware, a
  verified desk build) is asked to produce that station.
- A plant with no controller sheet is **info**: it may be controlled by another
  controller (M:N), or not yet be on this machine.

**CPs and columns: a column IS a CP.** This is identity, not derivation.
- The column's `CP Name` field names the CP. It must match a plant CP (MAIN HOUSE
  Value) of the same interlocking. If it's empty, still holds the library
  placeholder, or matches nothing, that's an **error**.
- A column/CP has **at most one** switch or lock lever, **at most one** signal
  lever, and **at least one** of them. This is a rule about **panel levers**.
  It does not constrain how the plant allocates masts, heads or other field
  equipment to MAIN HOUSEs. A signal's masts can sit in several houses:
  Luchessa's signal 784 does. Routes and signals span CPs, which is exactly why
  several CPs form one interlocking whose logic interlocks them.
- An interlocking is the set of its CPs/columns, with **exactly one** CODE
  button.
- Two columns naming the same CP is an **error**. A plant CP with no column is
  a **warning** (not dispatcher-controlled from this machine).

**Appliances:**
- Every panel appliance names a plant appliance **of this interlocking**, and
  the kinds must match:
  - `SWITCH_LEVER` ↔ powered switch
  - `LOCK_LEVER` ↔ switch lock
  - `SIGNAL_LEVER` ↔ signal control
  - `MAINTAINER_CALL` ↔ maintainer call
- Every dispatcher-controlled plant appliance has a lever. Dependent derails
  (`795D`) are exempt.
- A lamp's `IndicationToken` entries resolve **per interlocking**: to track
  circuits (including derived OS circuits such as `783T1`) or maintainer-call
  indications. Which column or driver a lamp is wired to is a hardware or
  model-board choice and carries no CP meaning.
- A plant track circuit that no lamp shows is **info**.

**Station:**
- One CODE per interlocking sheet (one station).
- The station's control and indication vocabulary, as computed from the plant
  (the same tokens the codec uses), must be covered by the sheet's levers and
  lamps. The model reports any gaps.
- Machine-type capacity (e.g. US&S 506 functions per column) is checked
  against the column's appliances.

**Staying in sync:**
- Make dependencies do this: each netlist depends on its project's sheets, and
  the linked model depends on every netlist under `SPCoast/`. Editing either
  side rebuilds the model and re-runs the cross-checks.
- The model records the source netlists it was built from (path and content
  hash), so a generator can refuse a stale model.

**Known gap:**
- **Maintainer calls are not in the portable plant model today.** The plant
  schematic has MC symbols, but the model drops them. So the desk's
  `MC1S`/`MC1K` cannot be cross-checked, and the plant host hard-codes
  maintainer calls per station (debt). The plant model must carry them.

**Prototype check against Luchessa (2026-09-28):**
- **Lever counts:** columns 5/6/7 each have one switch lever (783/795/799);
  column 5 also has signal lever 784. All satisfy the lever rule.
- **`CP Name`:** still the library placeholder `CP NAME` on all three columns,
  so it is flagged as unset.
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
- **Codelines:** all 7 sheets carry one codeline (currently VIRTUAL). Nested
  field references export resolved: `Topic` exports as
  `ctc/SPCoast/codeline/Luchessa`.
- **ERC:** 0 violations after the root-UUID repair and the symbol clean-ups.

**Implemented 2026-09-29** (`tools/controller_graph/`, `tools/link/`,
`parse_kicad_controller.py`, `link_subdivision.py`; 50 new tests): the
reader keeps sheetpaths and design-section sheet lists; controller
compiler with §7 diagnostics, stub recognition and empty-sheet
defaulting; linker with §7a cross-checks, placeholder stations, codeline
instances, source hashes and JSON emission. Golden test: generated
bindings match hand-written `examples/spcoast_ctc/IO-I2C.h` exactly.
Negative fixtures cover §7 (incl. zero-nets) and §7a. Still open:
station vocabulary coverage and machine-type capacity checks (§7a), the
second-implementation fixture (§9), field side (§5a).

## 9. Test plan

- **Golden:** from the Luchessa sheet plus the Luchessa plant, generate the
  column/appliance/bit bindings and check them against today's hand-written
  `configureDesk()` / `IO-I2C.h`.
- **Generality:** include a second, different controller implementation as a
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
- **US&S 506 codeline:** it gives each CP its own station code. That becomes a
  per-column attribute when a 506 codeline exists.
- **M:N controllers:** a tower panel and the dispatcher sharing a codeline. Each
  controller project carries its own codeline symbols; the linker matches them
  into one instance.
- **Library clean-ups:**
  - `PanelColumn` defaults carry SPCoast values (`Interlocking`, `Machine`), and
    its `Column` field (`${VALUE}`) repeats Value. `Interlocking` and `Machine`
    are derivable from the sheet and project.
  - Codeline defaults carry SPCoast values (`Broker`, `TopicRoot`, `Port`).
  - `PanelColumn` `CP Name` defaults to the placeholder `CP NAME`. An empty default (like the lamp `IndicationToken`) makes "unset" unambiguous.
- **Plant compiler:** it still maps library part names to kinds (`_PART_KIND`
  in `tools/plant_graph/compiler.py`). It should move to `Role` / `Kind` fields
  like the panel library.
- **FieldUnit `cTcMachine`:** it conflates codec track circuits with lamp slots
  (`withTrackLamps`). An `IndicationToken` list can drive one lamp from several
  circuits.
