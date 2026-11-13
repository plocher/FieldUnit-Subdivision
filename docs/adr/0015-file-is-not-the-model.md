# 0015. The file is not the model: writers compile, the file carries three parts, consumers read only the file

- Status: **proposed** 2026-11-13. The ask: ratify the eight decisions below.
- Amends: ADR 0011 §1 and §3 (the Layout Data Model File is the saved output of a writer, not the model itself; the
  stamp names the layout part's hash); ADR 0012 §5.1 (a domain library's results are written into the file's derived
  part at save), §6 (the file carries the reference rows it uses, not a path to the tables); the owner's ruling 10 of
  2026-11-13 (station packets are written at save, not only computed on demand).
- Builds on: ADR 0011 (given, relations, derived; writer and reader policies; what lasts and what is transient),
  ADR 0012 (derivation rules, domain libraries, reference data), the owner's discussion of 2026-11-13 in the Compiler
  Orchestration session (routes delivery, the DRY concern for Studio, the lifecycle of the parts), and the netlist
  rule of `AGENTS.md` (a cache of a source is volatile).

## Decisions requested

1. **The model has parts; the file carries them.** The layout's data model is three parts: reference data, layout
   data (stated) and derived data. Run-time state is a fourth kind of data and is never in the model. The Layout Data
   Model File is a writer's saved output that carries the three parts; it is not the same thing as the model.
   *Default: yes.*
2. **Only writers compile.** A writer (the KiCad importer now, Studio later) knows the reference data and how the
   layout selects from it. It compiles with the shared library: `derive` and the domain libraries. Studio compiles
   continuously, as a REPL that gives feedback, prompts and completion; the importer compiles as one discrete step.
   *Default: yes.*
3. **Save writes all three parts.** Every save identifies the reference content the layout selects, writes the
   reference part, writes the layout part, and computes and writes the derived part, including the domain libraries'
   results (routes now; blocks, ceilings and station packets as they land). *Default: yes.*
4. **The reference part holds only what is used.** For each table the layout uses: the rows it selects, the table's
   `version`, `schemaVersion` and provenance. Not whole tables, and not a path to them. *Default: yes (the owner,
   2026-11-13: "only what is needed").*
5. **Consumers read only the file.** Nothing outside the writers needs the library to derive or to find routes. A
   consumer in any language reads the three parts as JSON. *Default: yes.*
6. **The stamp makes staleness detectable without the library.** `provenance` names the library version, each
   reference table's version, and a hash of the layout part. A consumer that finds a hash that does not match the
   layout part rejects the file as edited outside a writer. *Default: yes.*
7. **Derived data is a function of reference data applied to layout data.** derived = `derive(reference, layout)`
   for a given library version. The library exposes it with the reference data as an explicit argument: the shipped
   tables are the default, and a writer, a test or a tool may pass another set. *Default: yes.*
8. **Layout data never copies reference data.** The layout states only its selection (`Railroad`, `Era`,
   `Rulebook`, an entity's own `Style` or `Kind`) and the designer's explicit overrides beside the item. A copied
   value would override the reference data and stop a change to it from reaching the layout. This is why a library
   symbol's override fields (`IndicationCeiling`, `Indications`, a train order board's `Rest`) are blank: only the
   designer fills them. *Default: yes.*

## 1. Problem

ADR 0011 made the file and the model the same thing: one JSON file, every entity with `given`, `relations` and
`derived`. Two questions of 2026-11-13 showed the cost of that equivalence.

- **Where do routes live?** ADR 0012 §5.1 said a domain library writes nothing into the file and every consumer calls
  the library. That made FieldUnit, a C++ project, depend on a Python library to read routes, and it put the same
  computation in every consumer.
- **Is `derived` a second copy?** The regime markers on the trackplan are the signs the crew sees; `derived.regime`
  restates their effect along the track. If the file is the model, Studio holds two copies of one truth and must keep
  them in sync.

Both questions have one answer. The rule of ADR 0012 §5.1 stands: routes are derived from the model, and the model
does not state them. What changes is that the file is no longer only the model.

## 2. The parts

| Part | What it is | Who writes it | When it changes | Where it lives |
|---|---|---|---|---|
| **Reference data** | railroad, era and rulebook tables: regimes (GCOR 6.13, Yard Limits: RESTRICTING), `policies`, head models, code line token forms, JMRI aspect names, train order words | the project, through ADRs | rarely; each table versioned | its source in the shared home; the rows a layout uses copied into its file |
| **Layout data** (stated) | `given` and `relations` of every entity: what the designer drew or typed, including the regime markers, the selection (`Railroad`, `Era`, `Rulebook`) and overrides beside the item | a writer | each edit | the layout's source (the KiCad project now, Studio's document later); carried in the file |
| **Derived data** | `derived` of every entity, the domain libraries' results | a writer, by the shared library | each compile; never by hand | the file |
| *Run-time state* | occupancy, lever and switch positions, signal indications, direction of traffic | FieldUnit | continuously | FieldUnit only |

The file carries the first three. The layout part is the source only in Studio; while KiCad is the source, the whole
file is an output of the importer, as it already is today.

## 3. The lifecycle

```
edit ──► compile ──► save
 │         │          ├─ identify the reference content the layout selects
 │         │          ├─ write the reference part (rows used, versions)
 │         │          ├─ write the layout part (given, relations)
 │         │          └─ compute and write the derived part (derive, routes, ...), stamp
 │         └─ Studio: continuous (REPL feedback, prompts, completion)
 │            KiCad importer: one discrete step
 └─ Studio: the designer edits stated data; the importer: the designer edits the drawing
```

The library (`derive` and the domain libraries) is the writers' dependency, and only theirs. It is the "middle home"
the owner agreed in principle on 2026-11-13: neither the importer nor FieldUnit owns it.

Studio's sync problem disappears because compile is part of save. The designer moves a regime marker; the next
compile recomputes every piece's regime and every route that passes it; the save writes them together. No copy is
ever edited apart from its source.

### 3.1 One function, two inputs

derived = `derive(reference, layout)`. The layout's selection chooses rows from whatever reference set is passed; the
designer's overrides win over the chosen rows; nothing else in the layout states a reference value (decision 8). Three
uses follow:

- **Writers** pass the shipped reference set (with the user's own layered over it, ADR 0012 §6).
- **Tests** cycle one layout over several reference sets: the same Corporal under two rulebooks or two eras, to show
  that a ceiling, a head word or a token form follows the table and not the drawing.
- **Tools** answer "what if": a designer previews the layout under another railroad's rules without editing it.

The reference part of the file (decision 4) is a record of the rows this compile used, so a consumer needs nothing
else. It is not layout data and overrides nothing: the next compile reads the reference set again and writes a new
record.

## 4. What a consumer does

A consumer reads the file. It reads meaning under ADR 0011 §4 (`derived`, then `relations`, then `given`), the resolved
reference words from `derived`, and the reference rows from the reference part when it needs a table row directly. It
checks the stamp: a hash that does not match the layout part means the file was edited outside a writer, and the
consumer rejects it. ADR 0011 §4.2 (a reader that holds other rules rebuilds `derived`) is retired for consumers; only a
writer rebuilds.

## 5. Where the domain libraries' results go

Each result is written beside the entity it belongs to, so every entity still holds `given`, `relations` and
`derived` (ADR 0011 §2):

- **routes:** `derived.routes` on the mast that displays them (a route belongs to its mast; the owner, 2026-11-13);
- **station packets:** `derived` on the code line station they belong to (ruling 10 changes from "computed on
  demand" to "written at save, computed by the same function");
- **blocks and ceilings:** placed by their tickets (#62) under the same rule.

## 6. Options considered

| Option | For | Against |
|---|---|---|
| **Writers compile; the file carries three parts** (chosen) | consumers need only JSON; one computation, run by writers; Studio has no sync step; staleness detectable by hash | the file is larger; a writer must run the library before each save |
| Derived computed on open by each consumer; the file holds only stated data | smallest file; nothing can be stale | every consumer needs the library, in its own language or through a bridge; FieldUnit depends on Python |
| As ADR 0011 and 0012 stand: `derived` stored, domain results computed by consumers | no change | two lifecycles for one kind of fact; consumers depend on the library for routes |

## 7. Consequences

- Tickets: the importer writes the reference part and the routes into `derived.routes` (the routes library of
  issue #139 is the function it calls); the stamp gains the layout hash; the schema gains the reference part and
  `derived.routes`. The schema change waits for nothing: versioning is idle until end to end (the owner,
  2026-11-13), and the contract freeze (#30, #98, #99) fixes the result.
- FieldUnit's layoutgen reads routes from the file, not from `tools/railroad`.
- `tools/layout_model/reference.py` loads the tables from one fixed folder today; `derive` and the domain libraries
  take the reference set as an argument instead (decision 7), with that folder as the default.
- A lint finds instance fields that repeat a reference value (decision 8), reported, not fatal.
- ADR 0011 §1 and §3, ADR 0012 §5.1 and §6, and the station-token feature are amended in place with a footnote when
  this ADR is accepted.
- No change for the MVP beyond the routes the first consumer needs anyway (FieldUnit's blocker B1).
