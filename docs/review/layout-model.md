# Layout Data Model — draft for review (2026-10-02, rev 8)

Status: draft under review. Nothing else in the repo changes until this is
agreed. Supersedes the "fragment + link" shape of PR #12 and §6 of
`desk-codeline-kicad-pattern.md`; §5a (field hardware sheet) stands. Rev 7
applied the sixth-round review (log in §8). Rev 8 aligns the terms and the
code line with ADR 0001 and ontology rev 5. Vocabulary follows FieldUnit
`docs/GLOSSARY.md`.

## Revision (2026-10-02, rev 8)

Sources: `docs/adr/0001-code-line-type-contract.md` (accepted, D1–D16),
`docs/review/ontology.md` rev 5, `vocabulary-review.md` iterations 8–10.

- Terms. "Controlled point" becomes "control point". "Station" and "line
  station" become "field station". "Host" becomes "field processor".
  "Vital" and "non-vital" on code line functions become "interlocked" and
  "auxiliary". "CP" is no longer a common noun. "Desk" is kept.
- Proposed keys renamed: `controlledPoints` → `controlPoints`;
  `controlledPoint` → `controlPoint`; `stations[]` → `fieldStations[]`;
  `vital` → `interlocked`. Keys that exist in code today keep their spelling
  (§4).
- A control point is declared by one `MAIN HOUSE` symbol. The tooling never
  derives or counts control points (ontology §3.1).
- A panel column is not a control point. The column of a lever or lamp
  decides which field station carries that function. A difference between an
  appliance's `CP` field and that column is not an error (ADR D3).
- Field stations depend on the code line type: one per control point on a
  506-style encoding, one per interlocking on AAR tokens (ADR D3).
- A field unit answers at one or more field stations (1 : N). `fieldUnits[].station`
  becomes the derived set `fieldStations` (ADR 0001, consequences).
- A code line type is an encoding on a transport (D1). `machine.type: "US&S506"`
  moves from the CTC machine to the code line as its encoding.
- Field station addresses are authored on the `CODELINE` symbol (D13), which
  has an encoding pin and a transport pin (D15).
- Names carry no `CP ` or `CP_` prefix (D12). The wire key that removed
  whitespace is withdrawn.
- The generator phase is stated in §0, §2 and §5: it chooses the code line
  type target, builds the code charts and checks capacity and size limits for
  that target (D5, D6, D16).
- Removed (overridden): "column IS a CP"; "a signal's CP is derived from the
  lever's column"; "a unit serves one master: exactly one station"; "a
  controller's interlockings are the groups of columns sharing one CODE
  button"; the station `key` with whitespace removed; §7 "Open points: none".
- The review log (§8) keeps the words of earlier revisions.

## 0. The rule

```
sources (KiCad today)    →   KiCad2Model compiler    ↘
                                                    ONE layout model document  →  generators  →  final artifacts
sources (Studio future)  →   Studio2Model compiler   ↗
```

- A compiler reads every project in a membership folder and writes one
  document (`generated/SPCoast.json` today; name, location and format are a
  serialization choice). It is regenerated whenever any source changes; there
  is no per-project intermediate.
- Generators read that document, join the parts they need, and write final
  artifacts (`Luchessa.ino`, an emulator, a picture, a doc packet). They write
  no intermediate data files. Many "generators" are expected to be a few
  programs with settings.
- The phases are those of ADR 0001 D6: compiler and linker, generator, run
  time. The compiler and linker own the model. The generator owns policy: it
  chooses the code line type target (the drawn default or another, such as
  virtual or US&S 506), builds one code chart for each field station, checks
  capacity and size limits for that target, and emits the interlocking
  application and the CTC machine application from one set of chart tables.
  Run time encodes and decodes by the chart.
- Nothing below the compiler front end knows the word KiCad. Every fact is
  stated in railroad / signalling / hardware vocabulary, and is
  self-documenting: no ordinals, no status flags, no codes that need a
  decoder ring. Provenance lives only in `sources` and in a diagnostic's
  `sourceRef`.
- **Missing data is discovered, not flagged.** A generator joins and walks
  the model; whatever it needs and does not find is its finding to report.
  Example: a US&S 506 target needs authored addresses; without them the
  generator fails for that target (ADR D13). The compiler records what the
  sources said and its own diagnostics, nothing else. Its diagnostics include
  the checks it can see: names present and unique, addresses unique, capacity
  and size limits of the drawn default (ADR D6, D16).

## 1. Entities and relations

Normalized: entities are keyed by railroad name; relations are explicit and
generators join them. Every foreign key resolves to an entity, even if that
entity is empty (an interlocking a desk names but no plant defines is a row
with empty sections).

```
layout
├── identity              { name: "SPCoast", railroad, division, era, revision, date, schemaVersion: "layout-model/1.0" }   era is documentation, not a model input
├── compiler              { name, version }                                   git describe --dirty --always of the tooling repo
│
├── interlockings{name}   interlocking plant (glossary §3): one field unit solves it   ─── ecosystem A: plant
│     controlPoints[]     its control points (one per MAIN HOUSE), in geographic order
│     signals{name}       { masts{ name: { controlPoint, direction, kind, heads[] } } }   controlPoint: the mast's drawn CP field
│     routes[]            { name, signal, mast, alignments[], clearTrackCircuits[], bestIndication, entrance, approaching, … }
│     topology, terminals                                                 as interlocking-plant/v1 today
│
├── controlPoints{name}   control point (glossary §4): declared by one MAIN HOUSE; its Value is the name
│     interlocking        FK
│     switches{}          { kind: POWERED | LOCK, osTrackCircuit, … }     a lock is a switch under different operating rules
│     derails{}           { controlMode, controllingSwitch, trackCircuit }
│     trackCircuits{}     including the derived OS circuit of each switch (783T1 belongs to the control point of 783)
│     maintainerCalls{}   auxiliary function { controlToken: MC1S, indicationToken: MC1K, interlocked: false }
│     auxiliaries{}       { kind, controlToken, interlocked }              switch heater, bungalow door, …
│
├── fieldUnits{name}      field unit (glossary §3): the interlocking application of one interlocking on a field processor   ─── ecosystem A: field I/O (§5a)
│     interlocking        FK
│     fieldStations       derived set: the field stations of this interlocking on its code line (§5)
│     hardware            ESP32 | RELAY | …                               (no row at all when nothing is authored)
│     drivers[]           { id, busKind, address }
│     proxies[]           { appliance: "<interlocking>/<name>", functions{ <fn>: { driver, bit } } }   fn: DRIVE_N, DETECT_R, OCCUPANCY, HEAD_A, …
│
├── controllers{name}     CTC machine (any implementation: panel, screen, simulator) ─── ecosystem B: controller + I/O
│     machine             { columns: 14, era }                            era is documentation; the code line type is on codelines[]
│     columns[]           ordered { number, controlPoint }                controlPoint: the column's CP Name field; a column is not a control point
│     appliances[]        { kind, name, column, color, interlocked, indicationTokens[], controlTokens[],
│                           functions{ <fn>: { driver, bit } } }         fn: NWS, RWS, NWK, RWK, NGS, HS, SGS, NGK, SGK, TEK, LAMP, CODE, SW
│     drivers[]           { id, busKind, address }
│
├── codelines[]           derived instances                              ─── ecosystem C
│     { id, encoding, transport, params }                                id is functional: "MQTT@mqtt.local", "CMRInet@/dev/tty…"; there is no VIRTUAL instance
│
├── attachments[]         controller × interlocking (relation)
│     { controller, interlocking, columns[], codeline: null | id }       codeline null ⇒ in-process (nothing drawn)
│
├── fieldStations[]       per code line type   (derived from attachments that name a codeline, and the encoding)
│     { codeline, interlocking, name, address: null | "<authored>", controlPoint: null | "<name>", columns[] }
│
├── diagnostics[]         { severity, code, about: {entity refs}, message, sourceRef? }
└── sources[]             { name, role: plant | controller, frontEnd: "kicad", path, sha256, version, generatedAt }   version = git describe --dirty --always of the source repo
```

Key rules:

- **An interlocking is the vital unit** (glossary: interlocking plant). One
  plant project draws one interlocking plant. It aggregates one or more
  control points; an interlocking with one control point is the degenerate
  case. It owns what spans control points: signals and their routes,
  topology and terminals. Its limits can be derived by cutting the track
  graph at every controlled signal (spike S3, Rule A; spike code only).
  Whether "one plant project gives one Rule A piece" is a compiler check is
  open (ontology §6).
- **A control point is declared, never derived.** One `MAIN HOUSE` symbol
  declares one control point and its bungalow; its Value is the name. The
  tooling does not count control points, and no check requires a number of
  them (ADR D5). A control point owns the appliances that its `CP` field
  assigns to it: switches (powered or lock), derails, track circuits
  (including the derived OS circuit of each of its switches), and its
  auxiliary appliances. Luchessa is one interlocking with three control
  points. This is a design decision of the layout; the owner plans to reduce
  it to one later. The model treats both shapes the same way.
- **A signal belongs to the interlocking, not to one control point.** Signal
  784 has masts at all three Luchessa control points. Each mast carries the
  control point from its own `CP` field, which is a field-wiring fact. The
  column of the signal lever is a CTC machine fact (`controllers[].appliances`).
  It decides which field station carries the signal's control (ADR D3).
- **Locks are switches.** `switches{}.kind` is `POWERED` or `LOCK`; the
  interlocking rules differ, the CTC view differs only in the plate name and
  the reverse-lamp colour.
- **Maintainer calls and auxiliaries are control point appliances** with
  their control and indication tokens and the `interlocked` flag, so lever,
  lamp and codec vocabulary cross-check. A maintainer call is always an
  auxiliary function (`interlocked: false`). An ad hoc auxiliary states the
  flag. The panel symbols carry it today as the field `Vital` (code name).
- **A field unit row is authored hardware for one interlocking** (§5a
  hardware sheet). Its proxies name plant appliances by
  `<interlocking>/<name>`, exactly as desk levers and lamps name them, with
  each field function bound inline to a driver bit. No hardware sheet, no
  row. A field unit answers at every field station of its interlocking on its
  code line (field unit to field station is 1 : N). Luchessa: three field
  stations on a 506-style encoding, one on AAR tokens. Whether one field unit
  can serve two code lines is open (ontology §5.2). Until it is decided, an
  interlocking on two code lines is two field unit instances; at most one of
  them is the drawn hardware, the rest are generated realizations (see §5).
- **A controller is an ordered list of panel columns.** Each column sits on
  one interlocking sheet, which names its interlocking. Its `CP Name` field
  names one control point of that interlocking; the linker checks that it
  resolves to a `MAIN HOUSE` Value (ontology §3.1). A panel column is not a
  control point. CODE buttons do not define interlockings: on a 506 machine
  each field station has its own CODE button (unverified), and at Luchessa
  one CODE button serves three columns (ADR D9).
- **Appliances have no ids.** Nothing references an appliance, so bindings
  live inline as the appliance's `functions`. A lever is `{kind, name,
  column}`; a board lamp is what it shows, `{kind: LAMP, color,
  indicationTokens}`. Two lamps in one column showing the same tokens are two
  lamps (info at most). Column pins mean membership only; the compiler never
  reads a slot number, and a code line type's step order is the generator's
  business.
- **A function goes to the field station of its column** (ADR D3). A field
  station carries the functions of the levers and lamps in its panel column.
  A signal control (left, stop, right) is one function of one lever. Routes,
  masts and aspects are not code line functions. An appliance of one control
  point can serve a function of another field station of the same
  interlocking. Example: track circuit 1NA has `CP` = Carnadero and its lamp
  is in column 6 (`CP Name` = Gilroy), so a 506-style field station Gilroy
  carries `1NAK`. This is not an error.
- **In-process is the absence of a codeline.** A controller sheet with no
  Codeline symbol reaches its interlocking in-process; nothing declares
  "VIRTUAL" because a virtual realization is a selection (§5), never a
  drawing. A virtual target needs no added data and is always available
  (ADR D13). There is no VIRTUAL codeline instance and no VIRTUAL field
  station.
- **A code line type is one encoding on one transport** (ADR D1). The drawn
  code line is the layout's default; the generator can emit another target
  from the same model (D6). Planned drawing: one `CODELINE` symbol with two
  pins, one for an encoding symbol and one for a transport symbol (D15).
  Today `Codeline-MQTT` names the transport only, and the encoding is AAR
  tokens by implication. Encoding and transport definitions are data files in
  the SPCoast KiCad repo (D10).
- **Attachment = a controller's columns on an interlocking**, plus the
  codeline it reaches it over, which is a fact about the controller's sheet
  (that is where a Codeline symbol sits). Controller M:N codeline = two
  attachments on one interlocking naming the same codeline. A controller
  that only names an interlocking has an attachment with no columns and no
  codeline: an empty sheet needs no symbol and no default.
- **Field stations are derived from attachments and the encoding.** On a
  506-style encoding there is one field station for each control point: its
  `name` is the `MAIN HOUSE` Value, `controlPoint` names it, and `columns`
  are the columns whose `CP Name` is that control point. On AAR tokens there
  is one field station for each interlocking: its `name` is the interlocking
  name, `controlPoint` is null, and `columns` are all columns of that sheet.
  An interlocking model with no `MAIN HOUSE` symbol cannot use a 506-style
  encoding. The model holds the field stations of the drawn default; a
  generator derives them again for another target.
- **Addresses are authored, never allocated** (ADR D4, D13). The address of
  each field station is a field of the `CODELINE` symbol of its code line.
  Attachments that disagree on an address for one field station on one code
  line are a diagnostic. Names are not normalized (D12): they are compared
  with case folded only, and a duplicate is an error.
- **Derived facts are in the model** (routes and their `bestIndication`, OS
  circuits, codeline instances, the field stations of the drawn default),
  so generators never re-derive them for the drawn default. Code charts are
  built by the generator for each target (ADR D2, D6).
- **Two versions, both recorded.** `identity.schemaVersion` says what shape
  the document has; `compiler.version` and each source's `version` say what
  produced it, as `git describe --dirty --always` so a hash is always present
  and a tag appears once a milestone is tagged. The netlist sha256 and a
  timestamp are forensic extras. A generator can refuse a document whose
  schema it does not know or whose sources are dirty. This needs the symbol
  libraries in git, which is already expected.

## 2. Joins generators make

(Luchessa interlocking plant used as the example)

Each generator that crosses the code line first chooses its code line type
target and builds the code chart of each field station (ADR D6).

| Generator | Logical "table join" |
|---|---|
| interlocking application (field unit sketch) for `Luchessa` | `fieldUnits(interlocking=Luchessa)` ⋈ `interlockings[Luchessa]` (signals, routes, topology) ⋈ `controlPoints` ⋈ `fieldStations(interlocking=Luchessa)` ⋈ `codelines`, then the code charts for the chosen target |
| emulator for a chosen set of interlockings | `interlockings[…]` ⋈ `controlPoints` ⋈ `fieldStations` ⋈ `codelines`; no `fieldUnits` needed |
| desk sketch (CTC machine application) for `SPCoast South` | `controllers[SPCoast South]` ⋈ `attachments` ⋈ `codelines` (null = in-process) ⋈ `fieldStations`, then the same code charts; lever and lamp names resolve within the interlocking of their sheet |
| model-board picture | `interlockings[X].topology` ⋈ `controlPoints` (+ `controllers` for lamp placement) |
| doc packet | everything, plus `diagnostics` |

Today's SPCoast South instance (as of rev 7, 2026-09-30; to be refreshed by a
compile, see §7, "Source ripple of ADR 0001"):

| Table | Rows |
|---|---|
| interlockings | Luchessa (3 control points, signal 784 with 5 masts, 10 routes); 6 named by the desk, empty |
| controlPoints | Luchessa, Gilroy, Carnadero (drawn today as `CP Luchessa`, `CP Gilroy`, `CP Carnadero`; to be fixed, ADR D12); others as named by the desk, empty |
| fieldUnits | none (no hardware sheet drawn yet) |
| controllers | SPCoast South (3 columns, 10 appliances with 24 bound functions, 3 drivers) |
| codelines | none |
| fieldStations | none |
| attachments | 7, all in-process (Luchessa: columns 5,6,7; 6 with no columns) |

## 3. Framing cases (§1a) against this shape

- **A: plants only.** Interlockings and control points defined (field units
  if drawn); controllers, codelines, field stations, attachments empty. A
  generator finds no code line → virtual (in-process) only, which needs no
  added data. ✓
- **B: controller only.** Interlockings and control points named but empty;
  controllers and attachments filled, codelines and field stations as drawn.
  Desk generator succeeds; a field generator walks into empty control points
  and says so. ✓
- **C: today.** Table above. ✓
- **Code line type change** (encoding or transport) touches `codelines` and
  `fieldStations` only. A different generation target changes neither: it is
  a generator setting (ADR D6). **IODRIVER change** touches
  `controllers[].drivers` and the affected `functions` only. **Field
  hardware change** touches `fieldUnits` only. ✓
- **M:N controllers**: one field station, two attachments. **506-style
  encoding**: one field station per control point. **Emulate everything in
  one process**, or **also simulate what is drawn for ESP32**: a
  generate-time selection (§5), no model change. ✓

## 4. Vocabulary purge (what leaks today)

| Today | Replace with |
|---|---|
| `Appliance.reference`, `DriveBinding.appliance` = designator (`LAMP5`) | no ids; bindings inline as `functions` |
| `Codeline-VIRTUAL` symbol, `Codeline.stub`, "really empty sheet", `sheet-empty-defaulted` | nothing: no symbol means in-process; an empty sheet is an interlocking the desk names with nothing drawn |
| `Station.status` linked / placeholder | nothing; empty entities are discovered by walking |
| `Station` (link model), "station" for a code line address | `fieldStations[]`, derived per code line type |
| `station_key()` / `stationKey` (whitespace removed, case folded) | nothing: names are compared with case folded only, and addresses are authored (ADR D12, D13) |
| `route.staticIndication` (v1) / `maxIndication` (FieldUnit payload) | `bestIndication` on both sides (FieldUnit changes too) |
| `controlledPoints[]` (plant JSON key) and its `members` (kind/id list) | `controlPoints`: the control point entity owning its appliances |
| `Column` docstring "A column IS a controlled point"; `cp_name` | a column names a control point by its `CP Name` field; `columns[].controlPoint` |
| `Machine.machine_type` from the `CtcMachine` field `Type` = `US&S506` | `codelines[].encoding`: a code line encoding, not a machine type (ADR 0001, consequences) |
| panel symbol field `Vital` = `NO` | `interlocked: false` (glossary §5: a code line function is interlocked or auxiliary) |
| masts under `appliances.masts[]` with a `signal` back-pointer | `signals{}.masts{}` on the interlocking |
| diagnostic codes `netlist-no-nets`, subjects = designators / sheet names | source-neutral codes (`source-no-connectivity`), `about` = entity refs, `sourceRef` for forensics |
| `sources[].kind` = controller-netlist / plant-model | `role` + `frontEnd` |
| plant `document` / `profile` (title block) | `layout.identity` |

Code names that stay until a rename: the KiCad Role `CONTROLLED_POINT` of
`MAIN HOUSE` (to review against the retired term, ontology §6), the
`PanelColumn` field `CP Name`, and the appliance field `CP`.

## 5. Deployment: what the model records

(Rev 7 title: "Hosting".)

The drawings say what exists: plants, per-plant field hardware (§5a),
controllers, and which codeline each controller reaches each interlocking
over. Deployment content recorded in the model is a default for generators: a
convenience that lets the layout designer capture everything about their
railroad in one source document. It does not preclude generator options
that change or override those defaults, for example to generate a virtual
or simulated version of the railroad, or to try out an alternate code line
type ("both-and", 2026-09-30 review; ADR D6).

What the model carries, and what it does not:

- **`attachments[].codeline`** says which codeline a controller uses for an
  interlocking; null is in-process. **`fieldStations`** follow from each
  interlocking × codeline pair and the code line's encoding (§1).
- **`fieldUnits`** rows exist only for drawn hardware (§5a), one per
  interlocking, each with its `fieldStations`: the derived set of field
  stations of its interlocking on its code line. The controller sheets are
  the one source of codeline declarations and addresses; the hardware sheet
  never repeats them.
- **The code line type in the model is the layout's default.** The generator
  chooses the target: the drawn default, virtual, or another type such as
  US&S 506 (ADR D6). For that target it builds the code charts (D2), checks
  capacity by counting steps after the chart (D5) and size limits (D16), and
  fails when it lacks facts it needs, such as addresses (D13). The first
  target is AAR tokens over MQTT. Nothing in the model may rule out US&S 506
  (D14).
- **Nothing in the model groups interlockings into programs.** A simulator
  that runs seven field units on one field processor, a C/MRI field processor
  for several interlockings, or one ESP32 crossing an interlocking boundary
  by modeller's licence is a generator's choice made from the facts above
  (field processor to field unit is 1 : N). How a generator is told (its
  options, make rules, recorded provenance) is out of scope for this
  document.

## 6. Compiler and generator packaging (follows from §0)

```
tools/kicad/        front end: netlist, schematic, symbol readers + role/kind mapping   (only KiCad-aware code)
tools/compile/      phases: read projects → control points/interlockings → field units → controllers → codelines/field stations/attachments → cross-check (incl. capacity and size limits of the drawn default) → derive
tools/model/        types, JSON, draft schema `layout-model/v1` (frozen with the 2nd field unit)
tools/generate/     one package; targets are settings, not separate tools per artifact; the code line type target is one setting
compile_layout.py   folder in, model out
generate.py --target fieldunit|emulator|desk|picture|docs …
```

`plant_graph` and `controller_graph` dissolve into `compile/` phases;
`fieldunit_projection`, `picture`, `layout` move to `generate/`. One
`Diagnostic` type. `interlocking-plant/v1` is retired: its content is spread
over `interlockings` and `controlPoints` inside `layout-model/v1`. Encoding
and transport definitions are not in this repo; they are data files in the
SPCoast KiCad repo, read by the compiler and the generator (ADR D10).

## 7. Open points

Resolved in the fifth and sixth rounds and still standing: deployment
defaults are both-and (§5); the field unit's field stations are derived, never
re-declared on the hardware sheet; the flag stays on ad hoc appliances (now
`interlocked`); `Codeline-VIRTUAL` removed; generator options are out of
scope here.

Withdrawn in rev 8: "a unit serves one master" as "exactly one station"
(overridden by field unit to field station 1 : N, glossary §2.5).

Open after rev 8 (from ADR 0001 and ontology rev 5 §6):

- Whether one field unit can serve two code lines (ontology §5.2).
- Confirm `CP Name` as the join from panel column to field station
  (ontology §3.4).
- Where an interlocking with no `MAIN HOUSE` keeps its appliances in this
  shape (§1 puts every appliance under a control point).
- The form of the encoding and transport definitions and their schema (ADR
  D10, D11), and the two-pin `CODELINE` symbol (D15).
- The source fix for names (D12): `MAIN HOUSE` Values, `CP` fields, `CP Name`,
  generated JSON, tests, documents.
- The Luchessa CODE button workaround, when a 506 target is built (D9).

Source and compiler ripple of removing `Codeline-VIRTUAL` (not a model
question, listed so it is not lost):
- `RailroadPanel.kicad_sym`: deleted the symbol; South-cTc: deleted it from
  the seven interlocking sheets. The `South-cTc.net` netlist file needs
  to be regenerated.
- Controller compile phase: "exactly one CODELINE per sheet" becomes "at
  most one"; stub recognition, the VIRTUAL transport and the
  `sheet-empty-defaulted` default go away; the 2026-09-29 decision
  "`Codeline-VIRTUAL` is the correct spelling" is superseded.

Source ripple of ADR 0001 (listed so it is not lost):
- The §2 instance table predates the current drawing. South-cTc now has
  `Codeline-MQTT` on all seven interlocking sheets (read 2026-10-02), so a
  compile gives seven code line attachments, not seven in-process ones.
- `CtcMachine` field `Type` = `US&S506` moves to the code line.
- `Codeline-MQTT` becomes a transport symbol on the two-pin `CODELINE`
  symbol, with an AAR token encoding symbol beside it (D15).
- The plant model must carry maintainer calls (ontology §5.3). The
  hard-coded calls in `setupCodec()` of the virtual field processor
  (`spcoast_virtual_plant.cpp`) then go.

## 8. Review log

- **Rev 1 → 2 (2026-09-29):** CPs made first-class; appliances and track
  circuits moved onto the CP; panel positions made functional; controllers
  modelled as an ordered CP list; document metadata moved to
  `layout.identity`; codeline ids kept functional; per-project cache dropped;
  `fieldUnits` split out.
- **Rev 2 → 3 (2026-09-29):** interlocking described as the vital unit;
  status enums replaced by provenance lists; signals moved onto the CP;
  `staticIndication` → `bestIndication`; locks folded into switches;
  positional appliance identity dropped; field-unit projects proposed.
- **Rev 3 → 4 (2026-09-30):** signal's CP made a derived field (from the
  lever's column), signals back on the interlocking with masts and their
  house allocation; `definedBy` / `declaredBy` dropped ("missing data is
  discovered, not flagged"); auxiliaries added as non-vital CP appliances
  with `vital`; appliance ids and the bindings table removed, bindings inline
  as `functions`; duplicate lamps allowed; field-unit projects and
  `fieldUnitAttachments` withdrawn, §5a hardware sheet stands, hosting made
  a selection (§5); `bestIndication` adopted on the FieldUnit side too.
- **Rev 4 → 5 (2026-09-30):** hosting made "both-and": drawn hardware is
  the default, any selection overrides, selection unit is station +
  realization, artifacts record their selection; a field unit serves
  exactly one station (`fieldUnits[].station`, derived when unambiguous);
  `vital` kept on maintainer calls and auxiliaries because they are ad hoc.
  Follow-up: §5 reworded as "recorded as a default, overridable by
  selection"; the hardware-sheet Codeline symbol withdrawn (DRY: the
  controller sheets already declare the codelines), `station` derived or
  null.
- **Rev 5 → 6 (2026-09-30):** `Codeline-VIRTUAL` removed as unnecessary:
  in-process is the absence of a codeline; attachments become controller ×
  interlocking carrying `codeline | null`; stations derived from attachments
  that name a codeline; no VIRTUAL instance, station, stub or default.
- **2026-09-30, versioning:** `identity.schemaVersion`, `compiler`, and
  per-source `version` (git describe) added. FieldUnit is a consumer we
  improve, not shim: it will take field I/O from the model, which needs the
  §5a symbols and a Luchessa hardware sheet first.
- **Rev 6 → 7 (2026-09-30):** §5 reduced to what the model records;
  selection units, precedence, artifact provenance and CLI syntax removed as
  generator policy, out of scope for the data model.
- **Rev 7 → 8 (2026-10-02):** aligned with ADR 0001 (accepted) and ontology
  rev 5; see "Revision" at the top. The rev 4 derived signal CP and the rev 5
  "one station" rule are withdrawn.
