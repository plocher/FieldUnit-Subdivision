# 0008. The Layout Data Model File

- Status: proposed, rev 2, 2026-10-20.
- Decision requested: **ratify**, the architecture of the on-disk representation. 
- Builds on: 
   - `docs/review/layout-model-view-2026-10-16.md` (the Data Model's content: sections, O1 to O16), 
   - ADR 0001 (encoding on transport, authored addresses), 
   - ADR 0004 (the project hierarchy), 
   - ADR 0005 (declarations, attachments, scopes), 
   - `docs/review/processor-cases-2026-10-16.md`, 
   - the glossary §2.
- Overview: `0008/shape.svg`.

## 1. Problem

The abstract actors and relationships captured in the KiCad schematic artifact represent a Layout Data Model. Milestone D compiles that model into a defined structure saved to the filesystem for interchange to various consumers: code generators, documentation producers, validators, simulators and emulators. This on-disk structure is currently undefined.

The Data Model itself is defined above, with names and relationships. What is undefined is the structure that carries it between the compiler and its consumers.

## 2. Rules

- **R1. Fidelity.** The structure must robustly capture the existing Data Model, with all its nuances, decisions and constraints.
- **R2. Boundary.** The KiCad compiler reads KiCad (tokens...) and creates a Data Model (grammer and parse tree), which it then saves to a filesystem representation. This constructed Data Model may not expose KiCad implementation details. The test for any entry: would Studio (a TBD replacement for KiCad-as-editor) need it?
- **R3. Reusable.** The structure must be usable as "the source file" for a future Studio layout design editor, and as-yet undefined tools must be able to consume it.  This representation and its schema become a stable public interface.

### ToC for Data Model content:

| Content | Defined in |
|---|---|
| Sections and entities: layout, interlockings, machines, control points, appliances, track, columns, processors, chips, devices, bindings, geometry | view 2026-10-16 §3, §4 |
| Code lines, transports, encodings, authored addresses | ADR 0001 D1, D4, D13, D15 |
| Interlocking membership and hierarchy, field units, mileposts, heads | ADR 0004 D12, D13, D7, D6 |
| Bus declarations, attachments, scopes, addresses; a node is a processor | ADR 0005 S1 to S7, C1 to C11 |
| Identity by qualified railroad name; relations by name, not containment; errors as inconsistent facts, absence as information | view O2, O9, O13; glossary §2 |
| Processors, field units and control points as independent entities | processor-cases §1, §5 |

## 3. Definition of done

- **DoD1. Lossless round trip.** KiCad schematic → **[Data Model] → compiler output → on-disk representation → reader input → [Data Model]** → generators. The two bracketed models are equal. Proven by: compile SPCoast, write, read, compare the models; then write again and compare the bytes. The first leg, schematic → model, drops source-isms on purpose (R2) and is not part of the round trip.
- **DoD2. Coverage.** The Data Model in the file captures the relationships, actors and dependencies articulated in the ADRs. Proven by: every recipe of ADR 0005 §7 and every section of the view §4 is readable from the compiled SPCoast file, with Sargent, Gilroy Caltrain, Gilroy Interchange, Watsonville and the desk present; a replica KiCad project that contains only the Sargent Interlocking (R3) evaluates to the same structure as the Sargent Interlocking from the SPCoast layout project.
- **DoD3. Schema.** The on-disk representation has a schema that defines its intended structure.  The compiler output validates correctly against it. Proven by: Validate the SPCoast project's compiled output, adversarial review of the schema and the validation mechanism.

## 4. Architecture

Each subsection names the rule that drives it, weighs the alternatives, and states the choice. Together they define the on-disk representation.

### 4.1 One file holds the entire layout

R3 asks for the file a Studio user opens, carries and backs up. A directory of files, one per scope, was weighed and withdrawn: its benefits are multi-writer safety and per-file diffs, and neither exists here: KiCad can't support multiple writers, and we don't construct KiCad schematics **from** this data model; its cost is a manifest and a filesystem layer the user can not treat atomically. 

### 4.2 JSON, defined by a JSON Schema

DoD3 asks for a schema; R3 demands a well defined, simple format and R2 forbids using a KiCad-shaped format.

| Option | For | Against |
|---|---|---|
| **JSON with JSON Schema** (chosen) | one schema document validates and documents the structure; every language, the microcontroller and the Mac already parse it; the existing POC plant schema and both readers are JSON | no comments; punctuation-heavy for a hand-written file |
| YAML | comments and less punctuation for hand authoring, parsers available, can be added on top od JSON without touching the model | indentation errors are silent |
| XML with XSD | a mature schema language, parsers available | twice the size of JSON  |
| s-expressions | the KiCad habit | the format itself is a KiCad implementation detail (R2) |

### 4.3 Facts nested by scope

R1 says the scope that declares a bus is a fact of the model (ADR 0005 S5: an attachment finds its declaration by wire, sheet, layout), and R3 says a one-interlocking file must be a natural thing to write.

```
schema, layout{settings, transports{}, codelines{}}, interlockings{name}, machines{name}, provenance, diagnostics[]
```

The top level is the layout and the file's own head. Each interlocking or machine dictionary holds what its scope declares: `settings`; the appliances and track (interlocking) or the columns (machine); `codelines[]`, the encoding instances with their authored address (ADR 0001 D4); `processors{}` declared in that scope, a CMRInet node being a processor with `transport` and `address` (ADR 0005 S2); `fieldUnit` or `officeUnit` naming its host; `devices[]` with their bindings; `geometry`.

| Option | For | Against |
|---|---|---|
| **Nested by scope** (chosen) | the declaring scope is a file fact; a one-interlocking file is one dictionary (R3); a diff names the interlocking | a reader that wants every device walks the scopes; a processor serving two interlockings is declared in one and named from the other |
| Flat sections (`processors{}`, `fieldUnits{}`, `devices[]`) | every device in one list | DRY issues: the declaring scope must be written on every row as a `scope` field; each interlocking is scattered over five sections |

### 4.4 The compiler resolves scopes to names

R2 draws the boundary. The sheets and netlist in a KiCad project are how the drawing says "which bus"; Studio's canvas will say it another way. The KiCad compiler internally resolves each relation by wire, sheet and layout (ADR 0005 S5) and writes the named relation: a chip's `processor`, a node's `transport`, a consumer's chain, a binding's chip and pin. An override field on a symbol yields the same relation plus an `info` diagnostic (ADR 0005 C8).

The Data Model holds names only.

| Option | For | Against |
|---|---|---|
| **Resolve in the compiler** (chosen) | the model stays relations-by-name (view O9); relations are recorded once; the scope ladder is coded once | a sub-sheet drawn only to separate two nodes leaves no trace in the Data Model |
| Persist the containers and let readers resolve | the data model shows the designer's grouping | a sub-sheet shows up in the model as a KiCad implementation detail (R2); every reader of every source must carry every source's container semantics |

### 4.5 Names and references

R1 says identity is the qualified railroad name only (view O2): no UUIDs, no ordinals or index IDs, case preserved and compared case-folded. The Data Model encodes it so:

- A dictionary key is the entity's own name within its scope. Its qualified name is the scope's name, a colon, and the key: `Sargent:835`, `SPCoast South:13`. Entities of the layout scope (interlockings, machines, transports, code lines) have no prefix: `Sargent`, `CMRInet`. A name may not contain a colon.
- Processors are named layout-wide (processor-cases §1) and declared in the scope that drew them. A chip is `processor/address`, or `processor/address/use` where one address serves two uses (the PCA9685 as PWM and as servo, view I3).
- **A reference is always the qualified name, in every scope**, including from inside the scope that declares the entity: a Sargent device serves `Sargent:835`, not `835`.
- A device row has no identity (view §7 item 2). Nothing references a row. A diagnostic locates one by its scope, its index in that scope's list and its natural key (`serves` or `shows`, the type, `column` where present); the index locates within one file and is never an identity across files.

| Option | For | Against |
|---|---|---|
| **Always qualified** (chosen) | one form, so a reader needs no scope context and `grep` finds every reference; a diagnostic quotes a name without saying where it found it; a machine's devices, which have no interlocking scope, need no special rule | a few bytes per row; renaming an interlocking touches every reference to it, which is a tool's job anyway |
| Bare within the declaring scope, qualified across scopes (withdrawn 2026-10-19) | terser; a rename touches less | every reader carries a resolver that depends on where a field sits; the canonical form needs a shortening rule; machine devices need a rule of their own |
| Row ids for devices | a diagnostic can point at a row | an id that is not a name is an identity the model forbids (O2), and a device has no name |

### 4.6 The file's head: schema, provenance, diagnostics

DoD3 asks the file to say which schema it follows; R1 asks it to say which versions of the libraries and reference data it was compiled against (view I21), since it names those by key and never copies them; R2 limits what it may say about where it came from.

- `schema`: the string `layout-model/v2.0.0`. The schema file is semantically versioned `schemas/layout-model/v2.0.0.json` in this repo until the chain moves into FieldUnit as its own PR (view O15), when the old `schemas/interlocking-plant/v1.json` is retired (O16).
- `provenance`: a property of the layout. 
   - The string `source-type/KiCad`; 
   - the compiler's name and version; 
   - the source (KiCad project, with its path, hash and `git describe`)
   - each symbol library and its version; 
   - each reference data set and its version.
- `diagnostics[]`: the compiler's Data-Model findings, each with a level (`error`: inconsistent facts; `info`: absence), text and the qualified names it concerns (view §4.9). The compiler emits parse errors and warnings as part of its forensics, sheet and reference included, to its own log.  A source document with compiler errors never generates a Data Model File representation.

### 4.7 Incompleteness and reference data

R1 says absence is information, not an error (view O13), incomplete models are allowed, their gaps are found by the readers and stubbed where useful by the emulator's mocks, and reference data is created in its simpleton form as the compiler first needs it.

- A field that is absent is absent (view §4): a device without a binding, an interlocking without a field unit, a processor without a board are valid files with `info` diagnostics.
- Reference data (chip definitions by IC, aspect and indication tables by rulebook, driver type keys, encodings) is named by key in the file and by version in `provenance`; no row is copied. Each set lives in its own place with its own small document, not in this file.

The alternative, copying the referenced rows into the file so it reads stand-alone, was rejected: it makes the file a second source of every table (the one-source rule of `AGENTS.md`), and a version in `provenance` gives a reader the same guarantee.

### 4.8 Canonical serialisation

DoD1 asks for a byte-identical rewrite, and a git diff of the file should show railroad changes only. So the writer, in the compiler and in the reader library, must sort things in the same way: natural-sorted alpha-numerical case folded, whitespace deduplicated  This includes keys, dictionaries by name, lists, etc.

## 5. The shape, drawn

![The file's shape](0008/shape.svg)

## 6. Sargent and the Caltrain node, excerpted

Illustrative, not the schema. Names and values are the drawing's as of 2026-10-19; the device rows follow the view §3.1.

```json
{
  "schema": "layout-model/1",
  "layout": {
    "name": "SPCoast", "railroad": "SPCoast", "division": "South",
    "settings": { "era": "", "rulebook": "" },
    "transports": {
      "CMRInet": { "kind": "CMRI", "params": { "port": "/dev/cu.modemXXXX", "baud": "28800" }, "host": "" },
      "MQTT":    { "kind": "MQTT", "params": { "broker": "192.168.1.21:1883", "topic": "ctc/SPCoast/codeline/" }, "host": "" }
    },
    "codelines": { "AAR Tokens@MQTT": { "encoding": "AAR", "transport": "MQTT" } }
  },
  "interlockings": {
    "Sargent": {
      "controlPoints": { "Sargent": { "milepost": 83.5 } },
      "appliances": {
        "835":    { "appliance": "switch", "style": "lock", "controlPoint": "Sargent:Sargent", "osCircuit": "Sargent:835T1" },
        "836NAB": { "appliance": "mast", "style": "double", "heads": { "A": { "style": "CPL" }, "B": { "style": "CPL" } } }
      },
      "codelines": [ { "codeline": "AAR Tokens@MQTT" } ],
      "processors": { "Sargent": { "side": "field", "chips": { "0x20": { "ic": "MCP23017" }, "0x27": { "ic": "PCA9685", "use": "pwm" } } } },
      "fieldUnit": { "host": "Sargent" },
      "devices": [
        { "type": { "appliance": "switch", "style": ["powered", "lock", "dual"] }, "serves": "Sargent:835",
          "bindings": [ { "function": "M", "chip": "Sargent/0x20", "pin": "B1" }, { "function": "N", "chip": "Sargent/0x20", "pin": "B2" } ] },
        { "type": { "appliance": "lamp" }, "serves": "Sargent:HBA", "address": "1",
          "bindings": [ { "function": "LAMP", "chip": "Sargent/0x27", "pin": "B1" } ] }
      ]
    },
    "Gilroy Caltrain": {
      "processors": { "Caltrain": { "side": "field", "board": "cpNode", "transport": "CMRInet", "address": "30",
                                    "chips": { "CMRI": { "ic": "CMRI" } } } },
      "devices": [
        { "type": { "appliance": "lamp" }, "serves": "Gilroy Caltrain:…", "bindings": [ { "function": "LAMP", "chip": "Caltrain/CMRI", "pin": "OUT.7" } ] }
      ]
    }
  },
  "machines": {
    "SPCoast South": {
      "panelStyle": "US&S 506 lever panel",
      "columns": { "13": { "interlocking": "Sargent" } },
      "attachments": [ { "interlocking": "Sargent", "columns": [13], "codeline": "AAR Tokens@MQTT" } ],
      "processors": { "SPCoast South": { "side": "office", "chips": { "0x2C": { "ic": "MAX7313" } } } },
      "officeUnit": { "host": "SPCoast South" },
      "devices": [
        { "type": { "appliance": "lever", "style": "lock" }, "serves": "Sargent:835", "column": "SPCoast South:13",
          "bindings": [ { "function": "WLS", "chip": "SPCoast South/0x2C", "pin": "A7" } ] }
      ]
    }
  },
  "provenance": { "compiler": "kicad2layout 0.1", "source": { "path": "SPCoast/SPCoast.kicad_pro", "sha256": "…", "describe": "…" },
                  "libraries": { "Railroad-HardwareIO": "…" }, "referenceData": { "chips": "…" } },
  "diagnostics": [ { "level": "info", "text": "Sargent: HBA carries Address 1 on a wire-capability pin", "about": ["Sargent:HBA"] } ]
}
```

Read off the excerpt: the Caltrain node is a processor that attaches to the layout's CMRInet transport by its address and declares the bits its drivers use; no driver row names the transport or the UA (ADR 0005 S1). Every reference is a qualified name, whether it stays in its scope (`Sargent:835` from a Sargent device) or crosses one (the lever in `SPCoast South:13` serves `Sargent:835`); the layout's own entities carry no prefix (§4.5). Nothing says sheet, net, reference or unit (R2).

## 7. Decision

Ratify §4 as the on-disk representation of the Layout Data Model: one JSON file defined by `schemas/layout-model/v2.0.0.json`, facts nested by scope, scopes resolved to qualified names by the compiler, a head of schema, layout-level provenance and diagnostics, absence as information, reference data by key, canonical serialisation. Milestone D writes it; milestone E reads it; §3 gates both.

## 8. Record

How the choices were made, in order:

- 2026-10-16. The layout model view fixed the Data Model's content and deferred its serialised form (O5). The owner answered its sixteen questions.
- 2026-10-19. The owner set milestones D and E and their operating rules: FieldUnit is informational, the schema is ours to invent iteratively, reference data in simpleton form as encountered, incomplete models allowed, Watsonville in scope.
- 2026-10-19. One file versus a directory: argued both ways, the owner chose one file (§4.1).
- 2026-10-19. References bare within a scope, qualified across: the owner asked for the implications (ambiguity, whether qualified works everywhere, code complexity against terseness); always-qualified was recommended and agreed (§4.5). The CMRInet node as a processor with chip `CMRI` and pins `OUT.n`/`IN.n`: "worth trying; regroup if it adds complexity."
- 2026-10-19. Rev 1 carried a `source` entry per interlocking. The owner struck it: it exposes a KiCad sheet name in a generalised model, the source is a layout property since all interlockings come from the one project, and nothing can use it (§4.6).
- 2026-10-20. The author applied the same rule to the diagnostics' `sourceRef` and dropped it (§4.6).
- 2026-10-20. The owner reframed the ADR: a problem that names the undefined thing, three rules, a definition of done that connects to the problem, and the intermediate choices run down by the author so that one decision remains. Rev 2.

## 9. Consequences

- C1. Milestone D's compiler writes this file and nothing else; its contract is the schema plus §4.8. Its gates are §3.
- C2. The reader library reads the file, evaluates in memory (view O4) and reports; FieldUnit's generators and emulator consume the reader's result, not the file's text.
- C3. The scope resolver of ADR 0005 C11 lives in the compiler (§4.4). The duplicate-address and two-candidates rules of ADR 0005 C10 are compiler diagnostics where they need the source and reader diagnostics where the file alone shows them.
- C4. `schemas/layout-model/v1.json` is written on ratification, from §4 and the view §4, with `geometry` an open object until the picture generator fixes it (view §4.7).
- C5. The view §7 items 1 (section names) and 2 (row identity) close here: the names are those of §4.3 and §6, read against the glossary §2.4; rows have no identity.
- C6. The old compilers, `schemas/interlocking-plant/v1.json` and the generated Luchessa JSON stay as reference until §3 passes, then go in one commit (layout-model-plan §0).
- C7. The compiler keeps its own log for forensics (sheet, reference, unit); the file never carries them.

## 10. Out of scope

- The evaluated model's serialisation, still deferred (view O5); it is an in-memory result keyed to the file's hash.
- The reference data sets' own shape: each gets its simpleton version and document when the compiler first needs it.
- `geometry` in detail (view §4.7).
- Generator options, including which processor hosts what in the emulator (processor-cases case 6).
