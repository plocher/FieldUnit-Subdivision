# FieldUnit-Subdivision

The developer's map of this repo. `AGENTS.md` is the agent's file: commands, layout
and the working agreements. This file says where things are and why; it does not
repeat `AGENTS.md`.

## What this repo owns

FieldUnit-Subdivision is the operating-subdivision layer of the
[FieldUnit](https://github.com/plocher/FieldUnit) ecosystem, built for the owner's
SPCoast South (seven interlockings, one 14-column US&S style CTC desk). It owns:

- the tooling from the KiCad drawings to data: the KiCad importer, the Layout
  Data Model File with its schema and derivation rules, and the domain libraries
  that read it;
- the subdivision runtime: virtual plants, train progression, board and crew views.

It does not own:

- **vital logic**. Plants run FieldUnit's interlocking logic (`InterlockingPlant`,
  `~/Dropbox/Arduino/libraries/FieldUnit`). Nothing here copies or reimplements an
  interlocking rule (ADR 0012 §5.2);
- **the drawings**. The KiCad project and the four symbol libraries
  (`Railroad-Trackplan`, `Railroad-Office`, `Railroad-Field`, `Railroad-HardwareIO`)
  live in the Railroad repo, `~/Dropbox/KiCad/Railroad/`;
- **the second writer**. FieldUnit-Studio will write the same file. Until it exists
  the KiCad project is the one source and the flow is one way (ADR 0011 §8).

## The flow

```text
KiCad project + symbol libraries            ~/Dropbox/KiCad/Railroad/ (SPCoast/, symbols/)
        |
        v
KiCad importer (transient, ADR 0011)        tools/layout_compiler/   CLI: tools/compile_layout.py
   reads the drawing through tools/kicad_services/
   writes `given` and `relations`, reports import diagnostics
        |
        v
Layout Data Model File                      schemas/layout-model/    (v3.1.0.json, examples/)
   every entity and row: given, relations, derived
        |
        v
Reference derivation (pure function)        tools/layout_model/derive.py
   rules as Gherkin features                schemas/layout-model/rules/features/
   rule-check registry                      schemas/layout-model/rules/diagnostics.json
   grammar and reference data               tools/layout_model/grammar.py, reference.py
        |
        v
Domain libraries                            tools/railroad/ (codeline.py today)
        |
        v
Consumers: FieldUnit generators (planned), the virtual plant host
   runtime/plant_host/, pictures and documentation packets
```

The importer writes `given` and `relations`, calls `derive`, and writes the file.
`derive` needs the file and nothing else: no netlist, no KiCad.

## The three maps (ADR 0011)

Every entity and row in the file holds three maps (ADR 0011 §2):

- `given`: every field the person stated on the symbol, keyed as drawn;
- `relations`: every connection the person stated, each written as the name it
  reaches;
- `derived`: what the rules compute, including every resolved relation and every
  fact the drawing does not state.

A reader takes meaning from `derived`, then `relations`, then `given`, first hit
wins; `derived` is a cache that may need to be rebuilt (ADR 0011 §4). The same
ADR divides the code by what Studio would need:

| | What | Where |
|---|---|---|
| **Lasting** | the schema with its three maps; the writer and reader policies; the derivation rules, their conformance suite (the features) and the reference derivation | `schemas/layout-model/`, `tools/layout_model/` |
| **Transient** | the KiCad importer: netlists, sheets, references, the sheet hierarchy, `Value`. One writer among others; it retires when Studio exists or stays as an import path | `tools/layout_compiler/`, `tools/kicad_services/` |
| **Derived** | every `derived` map, recomputable from `given` and `relations` by any conforming derivation; never written by hand; a `derived` already in the file is ignored and rebuilt | `tools/layout_model/derive.py` |

Incomplete is not in error: a fact the rules cannot reach is absent and reported
at `missing`; facts that contradict each other are an error, and the importer
writes no file on an error (ADR 0011 §6, `tools/compile_layout.py`).

## Where each kind of fact lives

Symbols are keyed by their fields, never by their names. The keys the importer
reads are `Role`, `Kind`, `Appliance`, `Style`, `Name`, `CP Name`, `IC`, `Address`,
`Column`, `Pin.X`, `Control.X` and `Indication.X`; `Reference` and `Value` are
never read (ADR 0009 §3.10).

| Kind of fact | Lives in | Written by | Read by | Gate |
|---|---|---|---|---|
| Symbol field or pin contract | Railroad `symbols/*.kicad_sym` | the owner, in KiCad | the importer, the manual generator | `tools/contract/lint_symbol_fields.py`, `tools/contract/symbol_contact_sheet.py` |
| KiCad reading and import diagnostics | `tools/layout_compiler/`, registry `tools/layout_compiler/diagnostics.json`, features `tools/layout_compiler/features/` | the importer's developer | `tools/compile_layout.py` | `tests/test_layout_compiler.py`, `tests/test_diagnostic_registries.py`, `tests/test_rule_features.py` |
| Derivation and rule checks | `tools/layout_model/derive.py`, registry `schemas/layout-model/rules/diagnostics.json` | the data model's developer | every writer of the file (the importer today) | the features, `tests/test_derive.py`, the registry gate |
| Reference data (encoding and transport pairing, token templates, stations, regimes, aspect names) | `tools/layout_model/reference.py`, a placeholder (ADR 0012 §6) | the owner, as encountered | the derivation and the domain libraries | `tests/test_reference_capacity.py` |
| Naming grammar and Style classes | `tools/layout_model/grammar.py` | the data model's developer | the derivation and the domain libraries | the features |
| Domain library (code line packets, later routes, blocks, ceilings) | `tools/railroad/` (ADR 0012 §5) | the library's developer | consumers, and the derivation for its checks | each library's gate over every SPCoast interlocking |
| Decision and its rule | `docs/adr/` | the owner ratifies; agents propose | everyone | review: an amended rule changes its feature in the same PR |
| Rule specification | `schemas/layout-model/rules/features/` (model), `tools/layout_compiler/features/` (import) | the rule's developer | `behave`, Studio later | `tests/test_rule_features.py`: every registry link resolves both ways |
| What a symbol field or pin commits to | Railroad `symbols/manual.html` (prose fragments) and the libraries' Descriptions | the owner | symbol authors | `tools/contract/symbol_manual.py` generates the page; `tests/test_symbol_manual.py` |

Import diagnostics are located in KiCad terms (sheet, reference, library symbol,
Name) and belong to the importer; rule checks name model entities and belong to
the data model (ADR 0012 §3.3). Each registry is checked against its raisers by
`tests/test_diagnostic_registries.py`.

## Commands

The commands, with their environment and caveats, are in the Commands block of
`AGENTS.md`. Run every script with `uv run python`. The entry points:

- `tools/compile_layout.py PROJECT.kicad_sch -o OUT`: the KiCad importer. Exports a
  fresh netlist with kicad-cli, writes the Layout Data Model File, logs diagnostics.
- `uv run python -m unittest discover -s tests -q`: the unit tests and gates,
  including both registry gates and the features.
- `uv run behave --tags='not @pending'` in `schemas/layout-model/rules/features/`
  or `tools/layout_compiler/features/`: the rules as features, one root at a time.
- `tools/doc_debt.py`: the documentation debt report of ADR 0014 (lands with PR 127).
- `tools/contract/lint_symbol_fields.py`: the symbol field lint.
- `tools/contract/symbol_contact_sheet.py`: renders every unit of every symbol; the
  render is also the parse check.
- `tools/contract/symbol_manual.py`: generates the symbols manual.
- `tools/contract/netlist_diff.py`: compares two netlists by connectivity, the
  gate for a KiCad edit.

The proof-of-concept compilers are kept only to check the unified project against
the archived per-project drawings, not to compile it: `tools/plant_graph/`,
`tools/controller_graph/`, `tools/link/`, `tools/parse_kicad_plant.py`,
`tools/parse_kicad_controller.py`, `tools/link_subdivision.py`,
`tools/render_plant_picture.py` and `tools/run_plant_graph_smoke.sh`, with the
portable model schema `schemas/interlocking-plant/v1.json`. Their conventions are in
`AGENTS.md` under "KiCad conventions the proof-of-concept compilers rely on".

## Decisions

The index is `docs/adr/README.md`: what is accepted, what waits for the owner, and
the records. Accepted, in one line each:

- 0001: the code line type contract; encoding on transport, one code chart per
  field station, authored addresses.
- 0002, 0003: the symbol contract and the name grammar; frozen 2026-10-03, to be
  rewritten as rules after the cleanup pass (#30).
- 0004: the crew's unlock request (`WLQK`), head appliances, milepost anchors, the
  unified project hierarchy.
- 0005: how a driver finds its bus; a bus is declared once, scopes are wire, sheet,
  layout.
- 0006, 0007: KiCad services, the evidence and the ownership split with
  kicad-primitives.
- 0008: the Layout Data Model File as the public interface, with its schema.
- 0009: explicit seams; the net kinds, every symbol's pins, the keys (§3.10) and the
  relation table (§3.12).
- 0010: geometry as a design fact; placements, runs and glyphs; the four views.
- 0011: given, relations, derived; the writer and reader policies; what lasts and
  what is transient.
- 0012: rules as features with a registry; no fallbacks; domain libraries; reference
  data; versioning.
- 0013: between control points; station-to-station blocks, the interlocking–block
  seam, the HD line and SR sticks.
- 0014: definition of done, the documentation debt report and this map (accepted
  2026-11-12, in PR 126).

## Definition of done and documentation debt

ADR 0014 decision 1: a change is complete when every artifact that states the fact
it changes is changed with it, in the same PR. A rule change amends its ADR section
in place and its feature file; a change to what a symbol field or pin commits to
touches the symbols manual fragment and the field lint; a new or renamed diagnostic
code is registered and cited; a file format change bumps the schema and regenerates
the example in its own commit; a change to how a developer works updates `AGENTS.md`
and this map. The PR body lists the artifacts under "Done means".

Decision 2 measures it: `docs/doc-debt-report.md` is a generated report, written by
`tools/doc_debt.py` from `docs/agents/doc-map.json`, with the date and commit it was
computed on. It lists, per merged PR, which trigger paths changed without their
mapped documents, and the registered codes and scenarios no ADR or manual cites.
Reported, not enforced. Both files land with PR 127.

## Three readers

Issue 122 asks for one documentation per reader of the kind table (the words a
drawing may use and what each commits to):

- **Project developer**: this README and `AGENTS.md`.
- **Symbol author**: the Railroad symbols manual, prose in `symbols/manual.html`,
  generated by `tools/contract/symbol_manual.py` to
  `symbols/production/manual/index.html`.
- **Layout designer**: does not exist yet. It will live under `docs/` beside the
  manual, written from the user's chair with the diagnostics they will meet. Issue
  122 stays open for it.

## Runtime and profiles

- `runtime/plant_host/spcoast_virtual_plant.cpp` is the only runtime code: a
  headless C++ host running FieldUnit's interlocking logic for the SPCoast South
  stations and bridging it to the physical desk over MQTT
  (`ctc/SPCoast/codeline/<station>/controls` and `/indications`). `runtime/graph/`,
  `runtime/traffic/` and `runtime/web/` are empty placeholders. The build and
  self-test are in `AGENTS.md`.
- `profiles/spcoast_south/cps/`: station JSON for the Southern Pacific Coast Line
  from Gilroy Caltrain (MP 77) to Watsonville staging (MP 97). `CP_*.json` are
  legacy XML harvests, evidence only; `generated/` holds the KiCad-derived
  interlockings (Luchessa so far), which the plant host prefers.

## Aspiration

Target: a playable, operationally credible model railroad subdivision.

Scope (owner, 2026-11-10). A railroad, layout or real, is track connected to track,
and every piece of it is governed by some set of rules in a rulebook. Which rules
govern which track depends on the era (the technology available), the operations
(the use made of the track) and the railroad itself. FieldUnit captures the
prototypical behaviour of a full CTC system: office, code line and field.
Subdivision fills in what grows beyond, before and after the interlockings CTC
manages: block track between control points, sidings and track that were never
under CTC, industry and branch track, and the regimes that governed them, from
timetable and train orders with train order signals, switch tenders and tower
operators, through CTC, to radio-era track warrants (TWC) and block allocation
(DTC). The data model carries every piece of track with the regime that governs
it, so that a layout can be designed for modern radio and DTC operation without a
lever-based CTC office machine. No part of the model treats the dispatcher's
horizon as the edge of the railroad; "dark" is a word for what the office does not
see, never for what is there (ADR 0013 §7.1).

Near-term display target is SVG/HTML, not a 3D world.
