# The Layout Data Model: a view for review (2026-10-16, rev 1)

- Status: a view, written top-down for discussion, under the decisions of 2026-10-16 (§8). Decided items cite the checkpoint (`io-design-checkpoint-2026-10-10.md`, E = explicit, I = implicit), the ADRs, or the owner's answers of this date (O1 to O16, §8). The rest is the shape filled in and open to the owner.
- Governs: `handoff-compiler-io-2026-10-16.md` step 7, "the model schema". Companions: `environment-view-2026-10-09.md` §5 (what the drawing gives the model), `driver-types-view-2026-10-09.md` §6 (what the types need from it), `docs/design/layout-model.md` rev 8 (the earlier shape of the plant, office and code line sections, carried over here with its terms corrected).
- Scope: the model and the chain of tools around it. Not the schema text, not the serialisation, not the generators' options.

## 1. Intent

The Layout Data Model describes one model railroad's signalling territory as its designer stated it: the operational structure under the railroad's rulebooks and the designer's explicit constraints. It holds the track and appliances, the office and its machine, the code lines, the I/O that realises each appliance, the processors that host it, the drawing, the settings, and where every fact came from. It records what a person states and nothing a computer can compute from it. It is the only interface between the editors that produce it and the tools that consume it (O1, `goals.md`).

Three properties follow (O2, O3).

- **Source-independent.** Nothing in it says KiCad, sheet, net, reference or unit. A KiCad project, a Studio document and a hand-written file are three sources of the same model.
- **Target-independent.** Nothing in it says MQTT only, ESP32 only, or which program hosts which interlocking. Those are a generator's options.
- **Hand-authorable.** A small model written in a text editor is a valid input. That is how the emulator and the test harness get fixtures without KiCad (O3, "functional gates over fixtures").

Scope. In: plant, office, code line, realization, deployment, geometry, settings, provenance, the producer's diagnostics. Out: vital logic, driver code, run-time state, the content of the FieldUnit index, generator policy and targets, trains and operating sessions. Trains and sessions get reserved section names so a simulator can extend the model without a redesign.

## 2. The chain

```
.kicad_sch ──kicad2layout──▶                                                          ┌─▶ field unit application
Studio     ──(native)──────▶  Layout Data Model ──evaluate──▶ evaluated ──generators──┼─▶ CTC machine application
hand-written fixture ──────▶                        ▲         model                   ├─▶ doc package, pictures
                                                    │                                 └─▶ emulator, simulator
                                             FieldUnit index
```

Two activities, two results (O4). The **compiler** turns a source into the model; the KiCad compiler is the first one and is replaceable. The **evaluator** turns the model plus the FieldUnit index into the evaluated model: everything that follows from the design. Generators read both. The compiler and the evaluator are services that return data structures, in the manner of jBOM's KiCad services; a serialised form of either result is a later choice and not a design input (O5). The model is never changed by evaluation. An evaluated model names the model it was computed from by hash.

What is invented and what is not, in compiler terms:

| Term | Here | Invented here |
|---|---|---|
| source | `.kicad_sch`, a Studio document, a hand-written model | no |
| parse tree | KiCad's netlist; Studio's internals | no |
| intermediate representation | the Layout Data Model | yes, the one that matters |
| library interface | the FieldUnit index: types, signatures, casts, settings, factory defaults (I21) | yes, step 5 |
| analysis output | the evaluated model | yes |
| object files and a linker | none: the territory is one compilation unit, and names across interlockings resolve in the evaluator | no |
| link map and listing | the evaluated model, rendered by the doc package | no |
| executable | the generated applications, one per target | no |

The index is the truth for types. The symbol libraries conform to it, and the lint checks them against it (step 5). The model names a type by its key and never copies the index (I21, O7).

## 3. Sargent, worked

Sargent as drawn on 2026-10-16: one interlocking, one control point, one field sheet, one desk column. Qualified names throughout: `Sargent:835` is switch 835 at Sargent, `Sargent:836NB` is head B of mast `836NAB` (I12), `SPCoast South:13` is column 13 of the machine (O2). The sketches below are illustrative, not the schema.

### 3.1 What the designer stated

The plant.

```
interlockings.Sargent
  controlPoints: { Sargent: { milepost: 83.5 } }
  appliances:
    "835":    { appliance: switch, style: lock, controlPoint: Sargent, osCircuit: 835T1 }
    "1":      { appliance: switch, style: manual_sensed, controlPoint: Sargent, indicationCeiling: "RESTRICTING/RESTRICTING" }
    1NAT, 1SAT, 2SAT: { appliance: track_circuit, controlPoint: Sargent }
    "Corporal:2NAT": a reference, not an appliance: a track circuit of another interlocking, used here
    836SA:   { appliance: mast, style: single, heads: { A: { style: CL } } }
    836SB:   { appliance: mast, style: dwarf,  heads: { B: { style: UQ } } }
    836NAB:  { appliance: mast, style: double, heads: { A: { style: CPL }, B: { style: CPL } } }
    MC1:     { appliance: lamp, style: maintainer_call }
    HBA:     { appliance: lamp, style: non_vital, controlPoint: Sargent }
  track: segments and their endpoints, insulated joints, the END CTC marker, the two NextCP references (Corporal, Watsonville)
  policies: [ { rule: 261, direction: BOTH, on: <track> }, { rule: 105, direction: BOTH, on: <track> }, ... ]
  geometry: the drawing (§4.7)
```

The deployment and the realization.

```
processors:
  Sargent:         { side: field, chips: { "0x20/MCP23017": { ic: MCP23017, address: "0x20" },
                                           "0x27/PCA9685":  { ic: PCA9685, use: pwm,   address: "0x27", settings: { frequency_hz: "" } },
                                           "0x20/PCA9685":  { ic: PCA9685, use: servo, address: "0x20", settings: { min_us: "", max_us: "" } } } }
  "SPCoast South": { side: office, chips: { "0x2C/MAX7313": { ic: MAX7313, address: "0x2C" } } }

fieldUnits:
  Sargent: { interlocking: Sargent, host: Sargent }

devices:                                                     one row per device instance, not per symbol
  { type: { appliance: track_circuit, signature: ["~{OCC}"] }, serves: "Sargent:1NAT", settings: { hold_ms: 1500 },
    bindings: [ { function: OCC, chip: "Sargent/0x20/MCP23017", pin: A4 } ] }
  { type: { appliance: switch, style: [powered, lock, dual], signature: [M, "~{N}", "~{R}", "~{OCC}"] }, serves: "Sargent:835",
    bindings: [ { function: M, chip: ..., pin: B1 }, { function: N, ... B2 }, { function: R, ... B3 }, { function: OCC, ... B4 } ] }
  { type: { appliance: lever, style: lock, signature: ["~{WLQ}"] }, serves: "Sargent:835",
    bindings: [ { function: WLQ, chip: "Sargent/0x20/MCP23017", pin: A3 } ] }                      the crew's key, from Local-Lock
  { type: { appliance: lamp, signature: ["~{LAMP}"] }, shows: ["Sargent:835WLK"], invert: true,
    bindings: [ { function: LAMP, chip: "Sargent/0x20/MCP23017", pin: A1 } ] }                      the green LOCK lamp, from Local-Lock
  { type: { appliance: head, style: CL, signature: ["~{R}", "~{G}", "~{B}"] }, serves: "Sargent:836SA",
    bindings: [ { function: R, chip: "Sargent/0x27/PCA9685", pin: A3 }, { function: G, ... A2 }, { function: B, ... A1 } ] }
  { type: { appliance: head, style: [LQ, UQ], signature: [ARM, "~{R}", "~{G}", "~{B}"] }, serves: "Sargent:836SB",
    settings: { stop_deg: "", approach_deg: "", clear_deg: "" },
    bindings: [ { function: ARM, chip: "Sargent/0x20/PCA9685", pin: A1 }, { function: R, chip: "Sargent/0x27/PCA9685", pin: B4 }, ... ] }
  { type: { appliance: lamp, signature: ["~{LAMP}"] }, serves: "Sargent:HBA", address: 1,
    bindings: [ { function: LAMP, chip: "Sargent/0x27/PCA9685", pin: B1 } ] }
  ... 1SAT, 2SAT, switch 1, the two CPL heads of 836NAB, MC1's lamp, the Local-Switch lever and its two lamps

  { type: { appliance: lever, style: lock, signature: ["~{WLS}", "~{UNUSED}"] }, serves: "Sargent:835", column: "SPCoast South:13",
    bindings: [ { function: WLS, chip: "SPCoast South/0x2C/MAX7313", pin: A7 }, { function: UNUSED, ... A8 } ] }
  { type: { appliance: lamp, signature: ["~{LAMP}"] }, shows: ["Sargent:835WLK"], invert: true, column: "SPCoast South:13",
    bindings: [ { function: LAMP, chip: "SPCoast South/0x2C/MAX7313", pin: A1 } ] }
  { type: { appliance: lamp, signature: ["~{LAMP}"] }, shows: ["Watsonville:837T1"], column: "SPCoast South:13", label: TRACK, color: red, ... }
  { type: { appliance: lever, style: code, signature: ["~{CODE}"] }, column: "SPCoast South:13", bindings: [ ... B5 ] }
  ... the OS and HBD lamps, the MC lamp, the MC1 lever
```

The office and the code line.

```
machines."SPCoast South": { panelStyle: "US&S 506 lever panel", columns: { 13: { interlocking: Sargent, controlPoint: null } }, ... }
codelines: { "AAR Tokens@MQTT": { encoding: AAR, transport: MQTT, params: { broker: "192.168.1.21:1883", topic: "ctc/SPCoast/codeline/" } } }
attachments: [ { machine: "SPCoast South", interlocking: Sargent, columns: [13], codeline: "AAR Tokens@MQTT" } ]
layout: { name: SPCoast, railroad: SPCoast, settings: { era: "", rulebook: "", ... } }
```

Note what is not there. No sheet, no net, no reference, no unit, no `Pin.*` field, no capability word, no cast, no token, no field station. `Local-Lock` and `PanelLock` are each three device rows, a lever and two lamps, because a plate is several device instances (driver types view §2.8). Every device names its type by key and lands each function on a chip pin. That is all a person states.

### 3.2 What the evaluator adds

```
evaluated.of: sha256 of the model above
interlockings.Sargent:
  limits, OS circuits (835T1), signals (836S: masts 836SA and 836SB; 836N: mast 836NAB), routes with their best indication,
  indications: the tokens this plant produces (1NATK ... 835NWK, 835RWK, 835WLK, 835WLQK, MC1K, HBAK, ...)
fieldStations: [ { codeline: "AAR Tokens@MQTT", interlocking: Sargent, name: Sargent, address: null, columns: [13] } ]
devices:                                                  one row per model device, same order
  835 / Device-Switch:
    consumer: fieldUnit Sargent, local I/O (the chip's processor is the host)
    driverType: "Device : switch : lock : M ~{N} ~{R} ~{OCC}"           from the index, selected by the appliance's Style (E52)
    bindings:
      M:   { device: binary out, io: binary bidirectional -> configured out, polarity: asserted high, cast: direct }
      N:   { device: binary in asserted low, io: configured in, pull-up, invert in register, cast: direct }
      ...
  836SA / Device-Head-CL:
    bindings: R, G, B: { device: binary out asserted low, io: level out, cast: [two-point], settings: { low: {value: 0, from: factory}, high: {...}, fade_ms: {...} } }
  836SB / Device-Head-Semaphore-RGB:
    bindings: ARM: { device: position, io: position, cast: direct, settings: { stop_deg: {from: factory, value: 0}, ... } }
  PanelLock 835 lever:  tokens: [835WLS, 835UNUSED]; consumer: machine "SPCoast South"; fieldStation: Sargent
  Local-Lock 835 lever: tokens: [835WLQK]; consumer: fieldUnit Sargent; not on the code line: no office device lists it
diagnostics:
  info  835 has no Device-Lock: the lock mechanism is simulated, quality SIMULATED (E49, E50, foundation principle 15)
  info  835UNUSED is produced by column 13 and consumed by nothing (I33)
  info  Sargent:HBA carries Address 1 on a wire-capability pin; the address is ignored (E14)
  info  Watsonville:837T1 is listed by a lamp in column 13 and Watsonville's plant does not produce it (Watsonville is not evidence)
  info  Corporal:2NAT is used by Sargent's routes and comes from the code line (ADR 0004 D13)
  info  three settings on 836SB are empty and take the factory default
```

Two things to notice. The evaluator never had to know the source: the same rows come out of a hand-written model. And the consumer of each device fell out of two facts, the chip's processor and the field unit's host (O9), with no "local" word anywhere.

## 4. The model, section by section

Conventions. Entities are keyed by qualified railroad name; names are case-preserved and compared case-folded; nothing else is an identity (O2). A relation is a name in a field, never containment, unless the thing cannot exist alone (a head on its mast, a column on its machine). A field that is absent is absent: no status flags, no "declared by" (`layout-model.md` §0).

### 4.1 `layout`

The territory: `name`, `railroad`, `division`, and `settings`, the layout scope of the setting mechanism (E15, I15). Era and rulebook are layout settings (O11), as are the flash regimes, the clock source and the release policy (environment view §4.4, E18). Reserved for later sections: `trains`, `sessions`.

### 4.2 `interlockings{name}`

One per interlocking plant (glossary §2.4). Holds `controlPoints{name}` (one per `MAIN HOUSE`, with its milepost; ADR 0004 D7), `appliances{name}` with `appliance`, `style`, the optional `controlPoint` relation (O6; "membership, not a boundary", ontology §3.3), and the appliance's own facts: a switch's OS circuit and indication ceiling, a mast's heads by letter with each head's Style, a derail's controlling switch. `track` is the topology as drawn: segments, their endpoints, joints and markers. `policies` are the direction and speed markers with the rule they carry (the Role and Style of the marker, not `Rulebook`; handoff decision 7). `settings` is the interlocking scope. A name of the form `<other>:<name>` in any of these is a reference to another interlocking and is resolved by the evaluator.

Carried over from `layout-model.md` rev 8 with two changes: appliances sit under the interlocking, not under the control point, and signals, routes, limits and OS circuits leave the model for the evaluated model, because a computer derives them.

### 4.3 `machines{name}`

One per CTC machine (the term; `controllers` was a code name). `panelStyle`, the lever rule it implies, `columns{number}` each naming its interlocking and, optionally, its control point (the `CP Name` field; ontology §3.4), and `attachments[]`: machine × interlocking with the columns and the code line, `codeline` null for in-process (`layout-model.md` §1). Carried over unchanged in substance.

### 4.4 `codelines{id}`

One per drawn code line type: `encoding`, `transport`, `params`, and `addresses{}` authored per field station where the encoding needs them (ADR 0001 D1, D4, D13). On the SPCoast root sheet today: four transports on the machine's bus and an encoding per interlocking sheet joined to one of them by label.

### 4.5 `processors{name}` and `fieldUnits{name}`

The deployment facet (O9). A **processor** is a field processor or the office's: `side`, an optional `board`, and `chips{name}`: each with `ic`, `use` where one chip is drawn as several symbols (the PCA9685 as PWM or servo, I3), `address` on a bus, and `settings`, the chip-wide values (I4). A chip's name is local to its processor, so two expanders at `0x20` on two processors are two chips (I27).

A **field unit** is one per interlocking per deployment (glossary §2.5) and names its `host` processor. The office unit is the machine and its host is the office processor.

Processor, field unit and control point are three independent entities. A processor runs zero or more units; one that runs none is a pure I/O node, which is what a CMRInet node is (E32). One interlocking may have chips on several processors; the unit still runs in one place. The field station is a code line fact and is orthogonal to both (glossary §2.2). What the KiCad compiler does when nothing is drawn: one processor per interlocking, named after it, hosting its field unit and every chip in its hierarchy; one per machine; the `Processor` field on a chip names another (E44). Whether a processor symbol exists on the sheet is the open I31 question, now a drawing question only.

### 4.6 `devices[]`

The realization: one row per device instance, which is the unit the driver environment is built for (environment view §1). A row holds:

- `type`: the driver type key as the index spells it, `appliance`, `style` (a word or a list, the Styles the type serves; I9, E63) and `signature`, the function pins with their polarity in the name (E46, I7).
- the join: `serves`, a qualified appliance name, for everything but a lamp; `shows`, a list of qualified indication names, for a lamp (E42). A code button has neither (I28).
- `column`, present exactly when the device is in a machine column (E41, E72). `label` and `color`, the plate's face, when drawn.
- `invert`, the logical complement (E53); `address`, the slot on a bus (E14, E40); `settings`, the instance scope.
- `bindings[]`: one per bound function: `function` (the pin's base name), `chip` (processor-qualified), `pin`, and `settings`, the binding scope (I15). An unbound function is simply absent (E49).

A device row never carries a capability, a cast, a token, a consumer or a resolved setting. Those are evaluated.

What the KiCad compiler reads for this section: every Role DEVICE or PANEL symbol, split into one row per instance the type rule gives (binary-input pins form the lever, binary-output pins form one lamp each; driver types view §2.8); the type key from the library symbol by `lib_id` (O8); the join from the Value, or the token list by the E42 compromise, with "both resolve and differ" an error; the nets to IODRIVER pins; the Column net to the column symbol; fields after the standard ones as settings (learned 7, I11).

### 4.7 `geometry`

The drawing is a design fact (O12): the trackplan sheet is drawn to look like the railroad, and Studio's canvas will be drawn the same way. Per interlocking, the compiler records placements of track, appliance and marker symbols (position, rotation, mirror) and the track segments as polylines, in a normalised frame, and never uses them for connectivity (AGENTS.md). The model board, the thinline diagram and the doc package derive their styles from it, with the milepost anchors ordering interlockings along the subdivision (ADR 0004 D7). The section's detail is written against the existing picture generator as its first consumer (O12) and is open until that worked example exists.

### 4.8 `settings`

Not a section: the setting mechanism appears at four places, `layout.settings`, `interlockings{}.settings`, `devices[].settings` and `devices[].bindings[].settings`, the four authored scopes (I15). The factory scope lives in the index and the calibrated scope in the store (E24); neither is in the model. The evaluator resolves each setting per device and records the value and the scope that answered.

### 4.9 `provenance` and `diagnostics`

`provenance`: the compiler's name and version, each source with its path, hash and `git describe`, the libraries and their versions, the index version compiled against (`layout-model.md` §1, "two versions, both recorded"; I21). `diagnostics[]`: the compiler's own findings, two levels, `error` and `info` (E49, O13), each with `about`, the entities it concerns, and a `sourceRef` for forensics. A missing join, an unbound pin and an unconsumed token are `info`. Two valid joins, a function bound twice and a net mixing Roles are `error`.

## 5. The evaluated model

Everything a computer derives, keyed to the model's hash, one section per model section plus `diagnostics` of its own.

| Section | Holds | From |
|---|---|---|
| `interlockings{}` | limits, OS circuits, signals and their masts, routes with best indication, the indications the plant produces | track, appliances, policies (the plant compiler of today, rebuilt as an evaluator pass) |
| `fieldStations[]` | per code line type: name, control point or null, columns, address | attachments, code lines, control points (ADR 0001 D3) |
| `devices[]` | the driver type selected, the consumer and whether its I/O is local or remote, tokens, and per binding the capability at each end, the pin configuration (direction, inversion, pull-up), the cast path and every setting with its value and scope | the device rows, the index, the processors |
| `diagnostics[]` | contradictions and absences found by evaluation | all of the above |

The evaluated model copies nothing from the index: the cast path names the cast, the resolved settings are values (I21). A model evaluated against a later index is evaluated again, not patched.

## 6. What the KiCad compiler resolves and what it does not

The compiler resolves KiCad-isms and nothing railroad. The test: would Studio ask the user for it? If yes, the compiler writes it into the model; if a computer derives it, the evaluator does.

| KiCad fact | Becomes | Rule |
|---|---|---|
| sheet hierarchy | the interlocking or machine a symbol belongs to | nearest `INTERLOCKING` or `MACHINE` on the sheet or an ancestor (ADR 0004 D12) |
| a net joining a device pin to an IODRIVER pin | a binding | one mechanism (learned 3) |
| a net joining a Column pin to a COLUMN symbol | `column` on the device | membership (E41) |
| a symbol's units | nothing: one component with every unit's pins | the netlist already merges them (E56) |
| references | nothing | annotation artifacts (AGENTS.md, E73) |
| `lib_id` and the library's owned fields | the type key, Role, Appliance, Style, IC | from the library, never the instance; a disagreeing instance is a diagnostic (O8) |
| `Pin.*` fields | nothing in the model | the library's copy of the index's signature, for the lint |
| Value | the name, the join, or a lamp's label | by Role and the E42 compromise |
| fields after the standard set | settings | learned 7, I11 |
| `Setting` symbol on a net | settings at the scope the net implies | E15, E37 |
| symbol placement and track wires | geometry | never connectivity |

## 7. Open after this revision

1. The names of the sections, as written here (`machines`, `processors`, `fieldUnits`, `devices`, `attachments`), to be read against the glossary once more before the schema fixes them.
2. The device row's own identity. Nothing references a device, so rows have no id. The evaluated model needs a stable way to name a row in a diagnostic: `serves` plus the type key, or `shows` plus the column, is the candidate.
3. Geometry's detail, against the picture generator (§4.7).
4. A device Style narrowed on the instance below the library's list (`836SB` said `UQ` where the device serves `LQ, UQ`). This view treats Style as library-owned and synced; the sheets were synced on 2026-10-16 (Railroad PR #12). If an instance may narrow it, the rule changes.
5. `Address` on a device whose function lands on a wire-capability pin (`HBA`, Address 1 on a PCA9685 pin): informational, as written, or an error.
6. The index's shape (`fieldunit-index/v1`), step 5, which fixes the spelling of the type key.
7. The processor symbol on the sheet (I31), now a drawing question.

## 8. The owner's answers of 2026-10-16

- O1. Scope and intent as in §1, with the correction that the model describes the operational structure under the rulebooks and the designer's explicit constraints.
- O2. Identity is the qualified railroad name only. No UUIDs, no ordinals. Renaming is renaming.
- O3. The model is hand-authorable and is a valid fixture form.
- O4. Compiling and evaluating are two serial activities; the evaluator consumes the model whatever its source. "Two strata in one document" was withdrawn.
- O5. The compiler and the evaluator are services that return data structures, in the manner of the jBOM KiCad services. A serialised form is deferred and not a design input.
- O6. Appliances live under the interlocking; the control point is a nullable relation.
- O7. The libraries are not the model. The compiler knows them; the model names types by key.
- O8. Library-owned fields are read from the library by `lib_id`; an instance that disagrees is a diagnostic. The drift on the sheets was fixed by script.
- O9. Processor, field unit and control point are three independent entities. Chips name their processor; field units name their host. Whether one processor serves one or several control points is the designer's choice.
- O10. The control point is a 506 address; on MQTT the interlocking is the address. Unchanged from the glossary.
- O11. Era and rulebook are layout-scope settings.
- O12. Geometry is a design section, written against the Sargent picture as its first consumer.
- O13. Diagnostics have two levels, error and info.
- O14. Order of work: the full top-level shape now, `devices` and `processors` in detail first, the plant and office sections carried over in a second pass.
- O15. The schema and the chain move into FieldUnit after Sargent runs end to end, as its own PR. This repo is a playground whose job then ends.
- O16. FieldUnit's current serializer schema is obsolete and will be replaced by this model.

## Changes in rev 1

First revision.
