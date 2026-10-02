# Layout Data Model — draft for review (2026-09-30, rev 7)

Status: draft under review. Nothing else in the repo changes until this is
agreed. Supersedes the "fragment + link" shape of PR #12 and §6 of
`desk-codeline-kicad-pattern.md`; §5a (field hardware sheet) stands. Rev 7
applies the sixth-round review (log in §8). Vocabulary follows FieldUnit
`docs/GLOSSARY.md`.

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
- Nothing below the compiler front end knows the word KiCad. Every fact is
  stated in railroad / signalling / hardware vocabulary, and is
  self-documenting: no ordinals, no status flags, no codes that need a
  decoder ring. Provenance lives only in `sources` and in a diagnostic's
  `sourceRef`.
- **Missing data is discovered, not flagged.** A generator joins and walks
  the model; whatever it needs and does not find is its finding to report.
  The compiler records what the sources said and its own diagnostics, nothing
  else.

## 1. Entities and relations

Normalized: entities are keyed by railroad name; relations are explicit and
generators join them. Every foreign key resolves to an entity, even if that
entity is empty (an interlocking a desk names but no plant defines is a row
with empty sections).

```
layout
├── identity              { name: "SPCoast", railroad, division, era, revision, date, schemaVersion: "layout-model/1.0" }
├── compiler              { name, version }                                   git describe --dirty --always of the tooling repo
│
├── interlockings{name}   Interlocking Plant (Glossary): the vital unit      ─── ecosystem A: plant
│     controlledPoints[]  its CPs, in geographic order
│     signals{name}       { controlledPoint,                                 derived: the CP whose column holds the lever; null without a controller
│                           masts{ name: { controlledPoint, direction, kind, heads[] } } }   authored house allocation of each mast
│     routes[]            { name, signal, mast, alignments[], clearTrackCircuits[], bestIndication, entrance, approaching, … }
│     topology, terminals                                                 as interlocking-plant/v1 today
│
├── controlledPoints{name}  Controlled Point (Glossary): the unit of dispatcher authority
│     interlocking        FK
│     switches{}          { kind: POWERED | LOCK, osTrackCircuit, … }     a lock is a switch under different operating rules
│     derails{}           { controlMode, controllingSwitch, trackCircuit }
│     trackCircuits{}     including the derived OS circuit of each switch (783T1 belongs to 783's CP)
│     maintainerCalls{}   non-vital { controlToken: MC1S, indicationToken: MC1K, vital: false }
│     auxiliaries{}       non-vital { kind, controlToken, vital }         switch heater, bungalow door, …
│
├── fieldUnits{name}      Field Unit (Glossary): the hardware behind one interlocking   ─── ecosystem A: field I/O (§5a)
│     interlocking        FK
│     station             FK: the one station this unit answers on          derived when the interlocking has exactly one station, else null (§5)
│     hardware            ESP32 | RELAY | …                               (no row at all when nothing is authored)
│     drivers[]           { id, busKind, address }
│     proxies[]           { appliance: "<CP>/<name>", functions{ <fn>: { driver, bit } } }   fn: DRIVE_N, DETECT_R, OCCUPANCY, HEAD_A, …
│
├── controllers{name}     CTC machine, tower desk, software console       ─── ecosystem B: controller + I/O
│     machine             { type: "US&S506", columns: 14, era }
│     columns[]           ordered { number, controlledPoint }             column IS a CP
│     appliances[]        { kind, name, controlledPoint, color, vital, indicationTokens[], controlTokens[],
│                           functions{ <fn>: { driver, bit } } }         fn: NWS, RWS, NWK, RWK, NGS, HS, SGS, NGK, SGK, TEK, LAMP, CODE, SW
│     drivers[]           { id, busKind, address }
│
├── codelines[]           derived instances                              ─── ecosystem C
│     { id, transport, params }                                          id is functional: "MQTT@mqtt.local", "CMRInet@/dev/tty…"; there is no VIRTUAL instance
│
├── attachments[]         controller × interlocking (relation)
│     { controller, interlocking, columns[], codeline: null | id, station: null | "<name>" }   codeline null ⇒ in-process (nothing drawn)
│
├── stations[]            interlocking × codeline   (derived from attachments that name a codeline)
│     { codeline, interlocking, controlledPoint: null | "<CP>", name, key }
│
├── diagnostics[]         { severity, code, about: {entity refs}, message, sourceRef? }
└── sources[]             { name, role: plant | controller, frontEnd: "kicad", path, sha256, version, generatedAt }   version = git describe --dirty --always of the source repo
```

Key rules:

- **An interlocking is the vital unit** (Glossary: Interlocking Plant). It
  aggregates one or more controlled points; a single-CP interlocking is the
  degenerate case. It owns what spans CPs: signals and their routes,
  topology and terminals.
- **A controlled point is the unit of dispatcher authority.** It owns its
  switches (powered or lock), derails, track circuits (including the derived
  OS circuit of each of its switches) and its non-vital appliances.
- **A signal's CP is derived, not authored.** The controller column holding
  the signal lever names it; the compiler joins the two. With no controller
  the field is null, and nothing needs it. Each mast carries its own authored
  house allocation, which is a field-wiring fact.
- **Locks are switches.** `switches{}.kind` is `POWERED` or `LOCK`; the
  interlocking rules differ, the CTC view differs only in the plate name and
  the reverse-lamp colour.
- **Maintainer calls and auxiliaries are non-vital CP appliances** with
  their control and indication tokens and the `vital` flag the panel symbols
  carry, so lever, lamp and codec vocabulary cross-check.
- **A field unit row is authored hardware for one interlocking** (§5a
  hardware sheet). Its proxies name plant appliances by `<CP>/<name>`,
  exactly as desk levers name them, with each field function bound inline
  to a driver bit. No hardware sheet, no row. **A unit serves one master:**
  it answers on exactly one station. An interlocking that is a station on two
  codelines is two field unit instances; at most one of them is the drawn
  hardware, the rest are generated realizations (see §5).
- **A controller is an ordered list of CPs (columns).** Its interlockings are
  the groups of columns sharing one CODE button; the compiler checks that
  grouping against the CPs' own `interlocking` FK.
- **Appliances have no ids.** Nothing references an appliance, so bindings
  live inline as the appliance's `functions`. A lever is `{kind, name,
  controlledPoint}`; a board lamp is what it shows, `{kind: LAMP, color,
  indicationTokens}`. Two lamps on one CP showing the same tokens are two
  lamps (info at most). Column pins mean membership only; the compiler never
  reads a slot number, and a machine type's row order is the generator's
  business.
- **In-process is the absence of a codeline.** A controller sheet with no
  Codeline symbol reaches its interlocking in-process; nothing declares
  "VIRTUAL" because a virtual realization is a selection (§5), never a
  drawing. There is no VIRTUAL codeline instance and no VIRTUAL station.
- **Attachment = a controller's columns on an interlocking**, plus the
  codeline it reaches it over, which is a fact about the controller's sheet
  (that is where a Codeline symbol sits). Controller M:N codeline = two
  attachments on one interlocking naming the same codeline. A controller
  that only names an interlocking has an attachment with no columns and no
  codeline: an empty sheet needs no symbol and no default.
- **Station = interlocking × codeline instance, derived from attachments.**
  `controlledPoint` is null for per-interlocking codelines (MQTT); for US&S
  506 each CP is its own line station (Glossary) and it names the CP. `name`
  is the station name authored on the Codeline symbol, `key` the wire key
  (whitespace removed, case folded); attachments that disagree on the name
  for one interlocking on one codeline are a diagnostic.
- **Derived facts are in the model** (routes and their `bestIndication`, OS
  circuits, signal CPs, codeline instances, station keys, interlocking
  groupings), so generators never re-derive.
- **Two versions, both recorded.** `identity.schemaVersion` says what shape
  the document has; `compiler.version` and each source's `version` say what
  produced it, as `git describe --dirty --always` so a hash is always present
  and a tag appears once a milestone is tagged. The netlist sha256 and a
  timestamp are forensic extras. A generator can refuse a document whose
  schema it does not know or whose sources are dirty. This needs the symbol
  libraries in git, which is already expected.

## 2. Joins generators make

(Luchessa Interlocking Plant used as the example)

| Generator | Logical "table join" |
|---|---|
| field unit sketch for `Luchessa` | `fieldUnits(interlocking=Luchessa)` ⋈ `interlockings[Luchessa]` (signals, routes, topology) ⋈ `controlledPoints` ⋈ `stations(interlocking=Luchessa)` ⋈ `codelines` |
| emulator for a chosen set of interlockings | `interlockings[…]` ⋈ `controlledPoints` ⋈ `stations` ⋈ `codelines`; no `fieldUnits` needed |
| desk sketch for `SPCoast South` | `controllers[SPCoast South]` ⋈ `attachments` ⋈ `codelines` (null = in-process); lever and lamp names resolve via `controlledPoints` |
| model-board picture | `interlockings[X].topology` ⋈ `controlledPoints` (+ `controllers` for lamp placement) |
| doc packet | everything, plus `diagnostics` |

Today's SPCoast South instance:

| Table | Rows |
|---|---|
| interlockings | Luchessa (3 CPs, signal 784 with 5 masts, 10 routes); 6 named by the desk, empty |
| controlledPoints | CP Luchessa, CP Gilroy, CP Carnadero; others as named by the desk, empty |
| fieldUnits | none (no hardware sheet drawn yet) |
| controllers | SPCoast South (3 columns, 10 appliances with 24 bound functions, 3 drivers) |
| codelines | none |
| stations | none |
| attachments | 7, all in-process (Luchessa: columns 5,6,7; 6 with no columns) |

## 3. Framing cases (§1a) against this shape

- **A: plants only.** Interlockings and CPs defined (field units if drawn);
  controllers, codelines, stations, attachments empty; signal CPs null. A
  field-unit generator finds no station → in-memory only. ✓
- **B: controller only.** Interlockings and CPs named but empty; controllers
  and attachments filled, codelines and stations as drawn. Desk generator succeeds; a
  field generator walks into empty CPs and says so. ✓
- **C: today.** Table above. ✓
- **Transport change** touches `codelines` + `stations` only. **IODRIVER
  change** touches `controllers[].drivers` and the affected `functions` only.
  **Field hardware change** touches `fieldUnits` only. ✓
- **M:N controllers**: one station, two attachments. **506**: one station per
  CP. **Emulate everything in one process**, or **also simulate what is
  drawn for ESP32**: a generate-time selection (§5), no model change. ✓

## 4. Vocabulary purge (what leaks today)

| Today | Replace with |
|---|---|
| `Appliance.reference`, `DriveBinding.appliance` = designator (`LAMP5`) | no ids; bindings inline as `functions` |
| `Codeline-VIRTUAL` symbol, `Codeline.stub`, "really empty sheet", `sheet-empty-defaulted` | nothing: no symbol means in-process; an empty sheet is an interlocking the desk names with nothing drawn |
| `Station.status` linked / placeholder | nothing; empty entities are discovered by walking |
| `route.staticIndication` (v1) / `maxIndication` (FieldUnit payload) | `bestIndication` on both sides (FieldUnit changes too) |
| `controlledPoints[].members` (kind/id list) | the CP entity owning its appliances |
| masts under `appliances.masts[]` with a `signal` back-pointer | `signals{}.masts{}` on the interlocking |
| diagnostic codes `netlist-no-nets`, subjects = designators / sheet names | source-neutral codes (`source-no-connectivity`), `about` = entity refs, `sourceRef` for forensics |
| `sources[].kind` = controller-netlist / plant-model | `role` + `frontEnd` |
| plant `document` / `profile` (title block) | `layout.identity` |

## 5. Hosting: what the model records

The drawings say what exists: plants, per-plant field hardware (§5a),
controllers, and which codeline each controller reaches each interlocking
over. Hosting content recorded in the model is a default for generators: a
convenience that lets the layout designer capture everything about their
railroad in one source document. It does not preclude generator options
that change or override those defaults, for example to generate a virtual
or simulated version of the railroad, or to try out an alternate codeline
implementation ("both-and", 2026-09-30 review).

What the model carries, and what it does not:

- **`attachments[].codeline`** says which codeline a controller uses for an
  interlocking; null is in-process. **`stations`** are the distinct
  interlocking × codeline pairs that follow.
- **`fieldUnits`** rows exist only for drawn hardware (§5a), one per
  interlocking, each with its `station`: derived when the interlocking has
  exactly one station, null otherwise (with an info diagnostic). The
  controller sheets are the one source of codeline declarations; the
  hardware sheet never repeats them.
- **Nothing in the model groups interlockings into programs.** An emulator
  hosting seven interlockings, a C/MRI host behind a yard complex, or one
  ESP32 crossing an interlocking boundary by modeller's licence is a
  generator's choice made from the facts above. How a generator is told
  (its options, make rules, recorded provenance) is out of scope for this
  document.

## 6. Compiler and generator packaging (follows from §0)

```
tools/kicad/        front end: netlist, schematic, symbol readers + role/kind mapping   (only KiCad-aware code)
tools/compile/      phases: read projects → CPs/interlockings → field units → controllers → codelines/stations/attachments → cross-check → derive
tools/model/        types, JSON, draft schema `layout-model/v1` (frozen with the 2nd field unit)
tools/generate/     one package; targets are settings, not separate tools per artifact
compile_layout.py   folder in, model out
generate.py --target fieldunit|emulator|desk|picture|docs …
```

`plant_graph` and `controller_graph` dissolve into `compile/` phases;
`fieldunit_projection`, `picture`, `layout` move to `generate/`. One
`Diagnostic` type. `interlocking-plant/v1` is retired: its content is spread
over `interlockings` and `controlledPoints` inside `layout-model/v1`.

## 7. Open points

None. Resolved in the fifth and sixth rounds: hosting is both-and (§5); a
unit serves one master (`fieldUnits[].station`, derived or null, never
re-declared on the hardware sheet); `vital` stays on ad-hoc appliances;
`Codeline-VIRTUAL` removed; generator options are out of scope here.

Source and compiler ripple of removing `Codeline-VIRTUAL` (not a model
question, listed so it is not lost):
- `RailroadPanel.kicad_sym`: deleted the symbol; South-cTc: deleted it from
  the seven interlocking sheets. The `South-cTc.net` netlist file needs
  to be regenerated.
- Controller compile phase: "exactly one CODELINE per sheet" becomes "at
  most one"; stub recognition, the VIRTUAL transport and the
  `sheet-empty-defaulted` default go away; the 2026-09-29 decision
  "`Codeline-VIRTUAL` is the correct spelling" is superseded.

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
