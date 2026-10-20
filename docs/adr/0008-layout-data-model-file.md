# 0008. The Layout Data Model File

- Status: proposed, rev 3, 2026-10-20. The schema and a validated example exist (§6) and are part of what is ratified.
- Decision requested: **ratify**, the architecture of the on-disk representation: §4 and the schema `schemas/layout-model/v2.0.0.json` it describes.
- Builds on: 
   - `docs/review/layout-model-view-2026-10-16.md` (the Data Model's content: sections, O1 to O16), 
   - ADR 0001 (encoding on transport, authored addresses), 
   - ADR 0004 (the project hierarchy), 
   - ADR 0005 (declarations, attachments, scopes), 
   - `docs/review/processor-cases-2026-10-16.md`, 
   - the glossary §2,
   - FieldUnit `docs/adr/0005-appliance-driver-architecture.md` and its picture `0005-ctc-interface-layers.svg`: the two seams and the transport catalog, the definitive architecture this file is shaped on.
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
| The interface layers: Seam 1 Codeline between office and field logic; Seam 2 Hardware I/O on the panel side and the field side, local or remote; the transport catalog, any transport bindable to any seam | FieldUnit ADR 0005, `0005-ctc-interface-layers.svg` |

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
schema, layout{settings, transports{}, codelines{}, processors{}}, interlockings{name}, machines{name}, provenance
```

The top level is the layout and the file's own head. The layout scope holds the entities whose names are layout-wide: the transports, the code lines and the processors, a Remote I/O node (the Caltrain CMRInet node) being a processor with `transport` and `address` (ADR 0005 S2). Each interlocking or machine dictionary holds only railroad things: `settings`; the appliances and track (interlocking) or the columns (machine); `codelines[]`, the encoding instances with their authored address (ADR 0001 D4); `fieldUnit` or `officeUnit` naming the processor that runs it; `devices[]`, one row per device instance, with its bindings; `geometry`.

| Option | For | Against |
|---|---|---|
| **Nested by scope** (chosen) | the declaring scope is a file fact; a one-interlocking file is one dictionary (R3); a diff names the interlocking | a reader that wants every device walks the scopes |
| Flat sections (`processors{}`, `fieldUnits{}`, `devices[]`) | every device in one list | DRY issues: the declaring scope must be written on every row as a `scope` field; each interlocking is scattered over five sections |

The shape is the cTc interface layers of FieldUnit ADR 0005, which is why it needs no other section:

| FieldUnit ADR 0005 artifact | In the file |
|---|---|
| Transport catalog (DC pulses, MQTT, LocoNet, CMRInet, virtual/in-process) | `layout.transports{}`: this layout's instances, each of a kind in the reference data, declared once and bound by name |
| Seam 1, Codeline: controls down, indications up | `layout.codelines{}`: an encoding on a transport. Office end: the machine's `attachments[]`. Field end: the interlocking's `codelines[]` entry, the station with its authored address |
| Seam 2, Hardware I/O, panel side and field side: Local I/O (GPIO, I2C, SPI) | chips on the unit's host processor, `layout.processors{}.chips` |
| Seam 2: Remote I/O node, with its adapter, one per transport | a processor with `transport` and `address` that hosts no unit (Caltrain); the adapter is the transport kind, reference data |
| Office logic, the cTc code machine | `machines{}` with `officeUnit.host` |
| Panel devices: levers, buttons, lamps | the machine's `devices[]` rows |
| Field logic, one per location: codeline handler, safety logic | `interlockings{}` with `fieldUnit.host` |
| Field devices: motors, LEDs, detectors | the interlocking's `devices[]` rows |
| Codeline adapters, I/O managers | runtime parts of a unit, not facts a person states: no key |

Which seam a transport serves is not written either: a transport a code line names serves Seam 1, one a node names serves Seam 2, and one transport may do both. The reader derives it (R1).

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
- A processor is a layout-scope entity: one namespace for the whole layout, because one processor can serve several interlockings (processor-cases §1). Its name is the Value of its `Processor` symbol; when an interlocking draws none, the compiler declares one named after the interlocking, and likewise one per machine. So Luchessa's cpNode Xiao is the processor `Luchessa`, Corporal's is `Corporal`, the drawn Caltrain node is `Caltrain`, and the desk's is `SPCoast South`. Each entity kind has its own dictionary, so the interlocking `Luchessa` and the processor `Luchessa` coexist; a reference is typed by the field it sits in (`fieldUnit.host` names a processor). Two `Processor` symbols with one Value anywhere in the layout is a duplicate declaration, an error (ADR 0005 C10).
- A chip is `processor/address`: `Luchessa/0x20` and `Corporal/0x20` are two MCP23017s at the same I2C address on two processors, and no collision exists because the chip key carries the processor. Where one address serves two uses the key is `processor/address/use` (`Sargent/0x40/pwm` and `Sargent/0x40/servo`, the PCA9685 as both, view I3).
- A **row** is one element of a `devices[]` list: one device instance (view §3.1). The word names the list element and nothing else.
- **A reference is always the qualified name, in every scope**, including from inside the scope that declares the entity: a Sargent device serves `Sargent:835`, not `835`.
- A row has no identity (view §7 item 2). Nothing references a row, so no `id` key exists and the schema rejects one. A reader that reports on a row names it by its scope and its natural key (`serves` or `shows`, the type, `column` where present).

| Option | For | Against |
|---|---|---|
| **Always qualified** (chosen) | one form, so a reader needs no scope context and `grep` finds every reference; a diagnostic quotes a name without saying where it found it; a machine's devices, which have no interlocking scope, need no special rule | a few bytes per row; renaming an interlocking touches every reference to it, which is a tool's job anyway |
| Bare within the declaring scope, qualified across scopes (withdrawn 2026-10-19) | terser; a rename touches less | every reader carries a resolver that depends on where a field sits; the canonical form needs a shortening rule; machine devices need a rule of their own |
| Row ids for devices | a report can point at a row | an id that is not a name is an identity the model forbids (O2), and a device has no name |
| Processors declared under the interlocking that drew them (rev 2) | the file shows which sheet holds the symbol | that is a KiCad fact (R2); the name is layout-wide, so the dictionary must be too |

### 4.6 The file's head: schema and provenance

DoD3 asks the file to say which schema it follows; R1 asks it to say which versions of the libraries and reference data it was compiled against (view I21), since it names those by key and never copies them; R2 limits what it may say about where it came from.

- `schema`: the string `layout-model/v2.0.0`. The schema file is semantically versioned `schemas/layout-model/v2.0.0.json` in this repo until the chain moves into FieldUnit as its own PR (view O15), when the old `schemas/interlocking-plant/v1.json` is retired (O16).
- `provenance`: a property of the layout. 
   - The string `source-type/KiCad`; 
   - the compiler's name and version; 
   - the source (KiCad project, with its path, hash and `git describe`)
   - each symbol library and its version; 
   - each reference data set and its version.
- No `diagnostics[]`. A source document with compiler errors never generates a Data Model File. The compiler's observations about the drawing (an override field used, a sub-sheet that separated two nodes, a symbol it ignored) are forensics about the source, which R2 keeps out; the compiler prints them, sheet and reference included, to its own log.

### 4.7 Incompleteness and reference data

R1 says absence is information, not an error (view O13), incomplete models are allowed, their gaps are found by the readers and stubbed where useful by the emulator's mocks, and reference data is created in its simpleton form as the compiler first needs it.

- A field that is absent is absent (view §4): a device without a binding, an interlocking without a field unit, a processor without a board are valid - but incomplete - files. The reader reports each absence as `info` when it evaluates (§4.6); the file does not.
- Reference data (chip definitions by IC, aspect and indication tables by rulebook, driver type keys, encodings) is named by key in the file and by version in `provenance`; no row is copied. Each set lives in its own place with its own small document, not in this file.

The alternative, copying the referenced rows into the file so it reads stand-alone, was rejected: it makes the file a second source of every table (the one-source rule of `AGENTS.md`), and a version in `provenance` gives a reader the same guarantee.

### 4.8 Canonical serialisation

DoD1 asks for a byte-identical rewrite, and a git diff of the file should show railroad changes only. The writer used by the compiler and the reader library, must sort things in the same way: natural-sorted alpha-numerical case folded, whitespace deduplicated. This includes keys, dictionaries by name, lists, etc. In addition, the json file rendering needs to be the same: Two-space indent, UTF-8 unescaped, one trailing newline.

Sorting every list means that no list's order carries meaning. That is deliberate: implicit ordering is not deterministic, so every ordering needs to be explicit; we use an `address`. `name` or a token as a key. 

Tested via a writer (`tools/layout_model.dumps` and a script (`tests/test_layout_model_file.py`) to prove that a shuffled model writes the same bytes.

## 5. The Data Model shape

![The Data Model shape](0008/shape.svg)

One json file, a collection of facts organized by scope, relations linked by name, drawn on the cTc interface layers of FieldUnit ADR 0005: the office band is a machine, the field band holds the interlockings, Seam 1 is the code lines between them, Seam 2 is each band's I/O row, and the transport catalog stands beside them. Yellow is a declaration; white is an artifact that attaches via a relationship. Box titles are file paths.

- **Red dashed**: a reference by qualified name, a fact written in the file. A row's `serves`, a unit's `host`, a binding's chip, a code line's `transport` (the Seam 1 binding), a node's `transport` (the Seam 2 binding). The lever's `serves Sargent:835` runs from the office band to the field band in the same form it has anywhere.
- **Blue**: code line membership, the two facts the control path from a lever to its appliance is derived from: the machine's `attachments[]` entry (office end) and the interlocking's `codelines[]` entry (field end). The file never writes that path.

A processor has one name for the whole layout, so `Luchessa/0x20` and `Corporal/0x20` are two chips at one I2C address. A Remote I/O node (Caltrain) attaches by transport and address and hosts no unit. Which seam a transport serves is derived from what binds to it.

What is not in the file: sheets, nets, references, units (source-isms); diagnostics (an error means no file; absence is read from the file); routes, signals, tokens, casts, resolved settings, the seam a transport serves and the control path from a lever to its appliance (the evaluator derives them in memory); the libraries and the reference data (named by key and version, never copied); any order in a list (every intended order is an explicit address or key).

## 6. The example, validated

`schemas/layout-model/examples/spcoast-excerpt.json`, reproduced in full. It is generated by the script beside it, validates against `schemas/layout-model/v2.0.0.json`, and is in canonical form; `tests/test_layout_model_file.py` proves all three on every run. Railroad names are the drawing's as of 2026-10-19; the Luchessa and Corporal processors and their chips are the intended design, since neither sheet has field I/O drawn yet; `provenance` values are placeholders of valid form.

```json
{
  "interlockings": {
    "Corporal": {
      "codelines": [
        {
          "address": "Corporal",
          "codeline": "AAR Tokens@MQTT"
        }
      ],
      "fieldUnit": {
        "host": "Corporal"
      }
    },
    "Gilroy Caltrain": {
      "appliances": {
        "773": {
          "appliance": "switch",
          "controlPoint": "Gilroy Caltrain:Gilroy Caltrain",
          "style": "powered"
        },
        "774NAB": {
          "appliance": "mast",
          "heads": {
            "A": {
              "style": "CPL"
            },
            "B": {
              "style": "CPL"
            }
          },
          "style": "double"
        }
      },
      "controlPoints": {
        "Gilroy Caltrain": {}
      },
      "devices": [
        {
          "bindings": [
            {
              "chip": "Caltrain/CMRI",
              "function": "LAMP",
              "pin": "OUT.7"
            }
          ],
          "serves": "Gilroy Caltrain:774NAB",
          "type": {
            "appliance": "head"
          }
        },
        {
          "bindings": [
            {
              "chip": "Caltrain/CMRI",
              "function": "N",
              "pin": "OUT.1"
            },
            {
              "chip": "Caltrain/CMRI",
              "function": "NWK",
              "pin": "IN.1"
            }
          ],
          "serves": "Gilroy Caltrain:773",
          "type": {
            "appliance": "switch",
            "style": "powered"
          }
        }
      ],
      "fieldUnit": {
        "host": "Caltrain"
      }
    },
    "Luchessa": {
      "codelines": [
        {
          "address": "Luchessa",
          "codeline": "AAR Tokens@MQTT"
        }
      ],
      "controlPoints": {
        "CP Carnadero": {},
        "CP Gilroy": {},
        "CP Luchessa": {}
      },
      "fieldUnit": {
        "host": "Luchessa"
      }
    },
    "Sargent": {
      "appliances": {
        "835": {
          "appliance": "switch",
          "controlPoint": "Sargent:Sargent",
          "osCircuit": "Sargent:835T1",
          "style": "lock"
        },
        "836NAB": {
          "appliance": "mast",
          "heads": {
            "A": {
              "style": "CPL"
            },
            "B": {
              "style": "CPL"
            }
          },
          "style": "double"
        }
      },
      "codelines": [
        {
          "address": "Sargent",
          "codeline": "AAR Tokens@MQTT"
        }
      ],
      "controlPoints": {
        "Sargent": {
          "milepost": 83.5
        }
      },
      "devices": [
        {
          "address": "1",
          "bindings": [
            {
              "chip": "Sargent/0x40/pwm",
              "function": "LAMP",
              "pin": "B1"
            }
          ],
          "serves": "Sargent:836NAB",
          "type": {
            "appliance": "head"
          }
        },
        {
          "bindings": [
            {
              "chip": "Sargent/0x20",
              "function": "M",
              "pin": "B1"
            },
            {
              "chip": "Sargent/0x20",
              "function": "N",
              "pin": "B2"
            }
          ],
          "serves": "Sargent:835",
          "type": {
            "appliance": "switch",
            "style": [
              "dual",
              "lock",
              "powered"
            ]
          }
        }
      ],
      "fieldUnit": {
        "host": "Sargent"
      }
    }
  },
  "layout": {
    "codelines": {
      "AAR Tokens@MQTT": {
        "encoding": "AAR",
        "transport": "MQTT"
      }
    },
    "division": "South",
    "name": "SPCoast",
    "processors": {
      "Caltrain": {
        "address": "30",
        "board": "cpNode",
        "chips": {
          "CMRI": {
            "ic": "CMRI"
          }
        },
        "side": "field",
        "transport": "CMRInet"
      },
      "Corporal": {
        "board": "cpNode Xiao",
        "chips": {
          "0x20": {
            "ic": "MCP23017"
          }
        },
        "side": "field"
      },
      "Luchessa": {
        "board": "cpNode Xiao",
        "chips": {
          "0x20": {
            "ic": "MCP23017"
          },
          "0x21": {
            "ic": "MCP23017"
          }
        },
        "side": "field"
      },
      "Sargent": {
        "board": "cpNode Xiao",
        "chips": {
          "0x20": {
            "ic": "MCP23017"
          },
          "0x40/pwm": {
            "ic": "PCA9685"
          },
          "0x40/servo": {
            "ic": "PCA9685"
          }
        },
        "side": "field"
      },
      "SPCoast South": {
        "board": "ESP32",
        "chips": {
          "0x2C": {
            "ic": "MAX7313"
          }
        },
        "side": "office"
      }
    },
    "railroad": "SPCoast",
    "settings": {
      "era": "1970s",
      "rulebook": "SP 1969"
    },
    "transports": {
      "CMRInet": {
        "host": "SPCoast South",
        "kind": "CMRI",
        "params": {
          "baud": "28800",
          "port": "/dev/cu.usbserial-CMRI"
        }
      },
      "MQTT": {
        "kind": "MQTT",
        "params": {
          "broker": "192.168.1.21:1883",
          "topic": "ctc/SPCoast/codeline/"
        }
      }
    }
  },
  "machines": {
    "SPCoast South": {
      "attachments": [
        {
          "codeline": "AAR Tokens@MQTT",
          "columns": [
            "13"
          ],
          "interlocking": "Sargent"
        }
      ],
      "columns": {
        "13": {
          "interlocking": "Sargent"
        }
      },
      "devices": [
        {
          "bindings": [
            {
              "chip": "SPCoast South/0x2C",
              "function": "WLS",
              "pin": "A7"
            }
          ],
          "column": "SPCoast South:13",
          "serves": "Sargent:835",
          "type": {
            "appliance": "lever",
            "style": "lock"
          }
        }
      ],
      "officeUnit": {
        "host": "SPCoast South"
      },
      "panelStyle": "US&S 506 lever panel"
    }
  },
  "provenance": {
    "compiler": {
      "name": "kicad2layout",
      "version": "0.0.0-example"
    },
    "libraries": {
      "Railroad-Field": "example",
      "Railroad-HardwareIO": "example",
      "Railroad-Office": "example",
      "Railroad-Trackplan": "example"
    },
    "referenceData": {
      "boards": "example",
      "chips": "example",
      "encodings": "example"
    },
    "source": {
      "describe": "example",
      "path": "SPCoast/SPCoast.kicad_pro",
      "sha256": "50d858e0985ecc7f60418aaf0cc5ab587f42c2570a884095a9e8ccacd0f6545c"
    },
    "sourceType": "KiCad"
  },
  "schema": "layout-model/v2.0.0"
}
```

Read off the example: the Caltrain node is a processor that attaches to the layout's CMRInet transport by its address and declares the bits its devices use; no row names the transport or the UA (ADR 0005 S1). `Luchessa/0x20` and `Corporal/0x20` are different chips at one I2C address (§4.5). Every reference is a qualified name, whether it stays in its scope (`Sargent:835` from a Sargent row) or crosses one (the lever in `SPCoast South:13` serves `Sargent:835`); the layout's own entities carry no prefix. Nothing says sheet, net, reference or unit (R2). The canonical order puts `interlockings` before `layout` and `schema` last: the rule is one rule, with no exception for the head.

## 7. Decision

Ratify §4 and the schema `schemas/layout-model/v2.0.0.json` as the on-disk representation of the Layout Data Model, the public interface: one JSON file, facts nested by scope with processors at the layout, scopes resolved to qualified names by the compiler, rows without identity, a head of schema and layout-level provenance, no diagnostics, absence as information, reference data by key, canonical serialisation. Milestone D writes it; milestone E reads it; §3 gates both.

## 8. Record

How the choices were made, in order:

- 2026-10-16. The layout model view fixed the Data Model's content and deferred its serialised form (O5). The owner answered its sixteen questions.
- 2026-10-19. The owner set milestones D and E and their operating rules: FieldUnit is informational, the schema is ours to invent iteratively, reference data in simpleton form as encountered, incomplete models allowed, Watsonville in scope.
- 2026-10-19. One file versus a directory: argued both ways, the owner chose one file (§4.1).
- 2026-10-19. References bare within a scope, qualified across: the owner asked for the implications (ambiguity, whether qualified works everywhere, code complexity against terseness); always-qualified was recommended and agreed (§4.5). The CMRInet node as a processor with chip `CMRI` and pins `OUT.n`/`IN.n`: "worth trying; regroup if it adds complexity."
- 2026-10-19. Rev 1 carried a `source` entry per interlocking. The owner struck it: it exposes a KiCad sheet name in a generalised model, the source is a layout property since all interlockings come from the one project, and nothing can use it (§4.6).
- 2026-10-20. The author applied the same rule to the diagnostics' `sourceRef` and dropped it (§4.6).
- 2026-10-20. The owner reframed the ADR: a problem that names the undefined thing, three rules, a definition of done that connects to the problem, and the intermediate choices run down by the author so that one decision remains. Rev 2. The owner's edits: R2 in compiler terms (tokens, grammar, parse tree), R3 as a stable public interface, DoD2 proven by a replica project, DoD3 by adversarial review, the schema semantically versioned as `v2.0.0`, provenance with a source type, an error produces no file.
- 2026-10-20. The owner's clarifications on rev 2, folded in as rev 3: processors are layout-scope entities with a worked Luchessa and Corporal example, since "declared in the scope that drew them" was a KiCad fact and the namespace was unexplained (§4.3, §4.5); "row" is kept and defined as one element of `devices[]`, rather than a new generic word (§4.5); `diagnostics[]` is dropped, since an error produces no file and absence is readable from the file (§4.6); the example is the real file, generated and validated under test, because an example that does not show the schema is no use for evaluating it (§6). Sorted lists carry no order on purpose: intended order is always explicit, as the pixel chains taught (§4.8).
- 2026-10-20. The owner: the picture showed code lines and transports as siblings with no binding between them, and FieldUnit ADR 0005's interface layers (two seams, a transport catalog) are the definitive architecture. The picture is redrawn on those layers with both seam bindings drawn, the artifact-to-file mapping table is in §4.3, and the prose uses Local I/O and Remote I/O node. No key changed.

## 9. Consequences

- C1. Milestone D's compiler writes this file and nothing else; its contract is the schema plus §4.8. Its gates are §3.
- C2. The reader library reads the file, evaluates in memory (view O4) and reports; FieldUnit's generators and emulator consume the reader's result, not the file's text.
- C3. The scope resolver of ADR 0005 C11 lives in the compiler (§4.4). The duplicate-address and two-candidates rules of ADR 0005 C10 are compiler errors: no file is written. The reader reports absences as `info` from the file alone.
- C4. `schemas/layout-model/v2.0.0.json`, `tools/layout_model` (validate, canonical write) and the gates exist now and are ratified with this ADR. `track` and `geometry` are open objects until the compiler fixes them (view §4.7); fixing them is a minor version.
- C5. The view §7 items 1 (section names) and 2 (row identity) close here: the names are those of §4.3 and §6, read against the glossary §2.4; rows have no identity.
- C6. The old compilers, `schemas/interlocking-plant/v1.json` and the generated Luchessa JSON stay as reference until §3 passes, then go in one commit (layout-model-plan §0).
- C7. The compiler keeps its own log for errors and forensics (sheet, reference, unit); the file never carries them.
- C8. The schema is the public interface (R3): a change to the Data Model that changes the file is a schema version, with a migration for files already written, never a quiet edit.

## 10. Out of scope

- The evaluated model's serialisation, still deferred (view O5); it is an in-memory result keyed to the file's hash.
- The reference data sets' own shape: each gets its simpleton version and document when the compiler first needs it.
- `geometry` in detail (view §4.7).
- Generator options, including which processor hosts what in the emulator (processor-cases case 6).
