# 0011. Given, relations, derived: what the Layout Data Model File states, and how it is written and read

- Status: **accepted by the owner 2026-10-26** (rev 3, with the owner's wording of decision 3; rev 2: incomplete is not
  in error; rev 3: what lasts and what is transient). The ask was: ratify the six decisions below. ADR 0008, 0009 and
  0010, the schema and the KiCad importer change to follow them (§9).
- Amended 2026-10-27 (the owner's rulings on `docs/review/three-maps-mapping-2026-10-27.md`): a track pin's wire is a
  stated relation, `relations.<pin>`, not `derived` (D5), and so are a run's ends; membership implied only by the sheet
  hierarchy is written by the KiCad importer as `relations.interlocking`, not resolved into `derived` (D6). §2 is read
  with these.
- Amended 2026-10-27 (the owner, on cross-interlocking references): a reference to another interlocking's thing is a
  one-sided consumer of a codeline indication, never a general link to the thing. The only real-time state one
  FieldUnit or OfficeUnit has of another station is what that station sends over its codeline as indications. By the
  AAR nomenclature behind every codeline, controls end in `S` and indications in `K`. So a drawn `Corporal:2NAT` names
  the indication token `Corporal:2NATK`; the drawing is not edited, and a writer may add the `K` at ingest. The
  reference is a typed relation to that token (`relations.indication`). It resolves against the indications the named
  station sends: an error when the station is in the file but sends no such indication, a warning when the station is
  not in the file. The same rule applies to an OfficeUnit's `IndicationToken`.
- Amends: ADR 0008 §4.4 (named relations), §4.5 (`settings`), §4.6 and §4.7 (incomplete and in error), §4.8 (canonical
  form covers the stamp) and the schema; ADR 0009 §3.12 (the relation table becomes normative rules with a conformance suite); ADR 0010
  §4.10 and C2 (geometry optional).
- Builds on: the owner's discussion of 2026-10-26, which began at a field the KiCad compiler dropped (`Milepost` on an
  appliance) and ended at what Studio would need if this file were its native format; ADR 0008 R2 and R3 (the Studio
  test, the file as a future source); the control point rulings of 2026-10-26
  (`docs/review/trackplan-piece-2026-10-25.md`), which made "stated" and "inherited" a distinction the file must keep.

## Decisions requested (all ratified 2026-10-26)

Each line has a default; the sections below argue it. All six are about what lasts, the data model and its rules;
the KiCad compiler is a transient writer of it (§1).

1. **Three maps.** Every entity and every row holds `given` (what was stated, as fields), `relations` (what was stated
   as connections) and `derived` (what the rules compute). Default: yes (§2).
2. **Writer policy** as in §3: `given` and `relations` exactly as stated; `derived` holds everything the rules can
   derive from them, by a conforming derivation, stamped with its rules version; any edit re-derives it. Default: yes.
3. **Reader policy** as in §4: for meaning, `derived` then `relations` then `given`, first hit wins; `derived` is effectively a
   cache that may need to be rebuilt; unknown keys skipped and reported. Default: yes.
4. **One definition of the computation**: normative rules, a conformance suite as data, a reference derivation, one
   version for the three (§5). Default: they live in this repo beside the schema and move to FieldUnit with it (view
   O15).
5. **Incomplete is not in error.** A missing fact leaves its derived facts absent and the file is written; how loudly
   to say so is each writer's choice. Facts that contradict each other are an error, and whether a writer saves a file
   in error is its own policy: the KiCad importer does not; Studio may, as work in progress (§6). Default: yes.
6. **Geometry always.** Every file carries geometry; the KiCad importer's `--geometry` flag goes. Default: yes (§7).

Two limits are recorded, not decided (§8): KiCad is the one source until Studio exists, and the flow from KiCad is
one way.

## 1. Problem

The file mixes two kinds of fact under one set of keys. Some keys hold what a person drew (`style`, `settings.Topic`);
some hold what the compiler concluded from it (`controlPoint`, a driver's bus owner, `osCircuit`). Which drawn fields
appear as typed keys, which under `settings`, and which not at all depended on which reader in the compiler happened
to consume them: `Milepost` on a house was a typed key, on an appliance it was dropped. A consumer had to know the
compiler's internals to find a fact.

The control point rulings of 2026-10-26 made the gap concrete. A switch's control point is stated on 815 and
inherited by 815A through its gang. A file that holds only the resolved answer shows both as stated, and an editor
that moves 815 to another house leaves 815A behind. The sparse-clue design survives editing only if the file says
what was stated.

ADR 0008 R3 asks the file to be usable as the source file of Studio. The test this ADR applies throughout is the
owner's: what would Studio need if this file were its native format?

### What lasts and what is transient

The KiCad-to-data-model compiler is needed now and not once Studio exists (the owner, 2026-10-26). What Studio and
every consumer need, and what this ADR is about, is what lasts:

- **Lasting:** the schema with its three maps (§2); the writer and reader policies (§3, §4); the derivation's rules,
  conformance suite and reference implementation (§5). These belong to the data model, not to any tool that writes it.
- **Transient:** the KiCad importer, what is called the compiler today. Under this ADR it reads the drawing, writes
  `given` and `relations`, and calls the shared derivation. It is one writer among others, with no standing the others
  lack; it retires when Studio exists, or stays as an import path.

The test for where a piece of code or a rule belongs: if Studio would need it, it is lasting and lives with the data
model; if only reading KiCad needs it (netlists, sheets, references, the sheet hierarchy, `Value`), it is the
importer's. Nothing lasting may live only in the importer.

## 2. Three maps

```json
"HBA": {
  "given":     {"Appliance": "lamp", "Style": "non_vital", "CP Name": "Sargent", "Milepost": "83.4"},
  "derived":   {"controlPoint": "Sargent:Sargent"}
},
"815A": {
  "given":     {"Appliance": "switch", "Style": "powered", "TC": "815AT1"},
  "derived":   {"controlPoint": "Christopher:Christopher North", "osCircuit": "Christopher:815AT1"}
},
"MC1": {
  "given":     {"Appliance": "lamp", "Style": "maintainer_call"},
  "relations": {"house": "Gilroy Interchange:Gilroy North"},
  "derived":   {"controlPoint": "Gilroy Interchange:Gilroy North"}
}
```

A track row, which has no name, is the same three maps:

```json
{"given": {"Kind": "END_CTC"},
 "derived": {"circuits": {"CTC": "Luchessa:02T"}, "ports": {"DARK": ["Luchessa:Gilroy Industry.EoT"]}}}
```

- **`given`** holds every field the person stated on the symbol, keyed as drawn, every value a string as KiCad states
  it. Left out: KiCad's own housekeeping (`Reference`, `Value`, `Footprint`, `Datasheet`, `Description`,
  `Sheetname`, `Sheetfile`, `ki_*`), which Studio would not need (ADR 0008 R2), and the key field, which is already the
  map key (`key_of`, ADR 0008 §4.5). Nothing else is left out, whether or not any reader consumes it. `settings` is
  gone: it was `given` less the fields some reader happened to read.
- **`relations`** holds every connection the person stated, each written as the name it reaches: the explicit forms
  of ADR 0009 §3.12 (a wire to a processor, a transport, a bus, a column, a house), and the trackplan's wires (a
  mast's signal joint, a head's mast). A relation the drawing implies only by sheet hierarchy is not stated: it is a
  KiCad container fact (ADR 0008 §4.4) and is resolved into `derived`.
- **`derived`** holds what the rules compute: every resolved relation, whether it came from a wire, a field or a
  chain (`controlPoint`, a driver's `owner`, a column's `house`, `osCircuit`), and every fact the drawing does not
  state (`circuits`, `ports`, a mast's `heads`). It holds no copy of a stated value under another form: a reader that
  wants `Milepost` as a number parses `given.Milepost`, which the schema checks is numeric text.

The three maps capture different facts, so one subject may appear in two of them with two names and two meanings:
`given.CP` is the person's statement, `derived.controlPoint` is the answer, present also where nothing was stated.

| Option | For | Against |
|---|---|---|
| **Three maps** (chosen) | an editor keeps intent; no drawn name can collide with a computed one; whether a reader consumes a field is invisible | every entity grows a level |
| One flat map, typed keys beside drawn fields (today) | short | which map a fact lands in depends on the compiler's readers; a drawn field can collide with a computed key |
| `given` and `derived` only | simpler | a wire is a stated fact that is not a field, and it would land in `derived` beside inherited facts, losing the distinction editing needs |
| One `model` map plus an optional `source` map | consumers read one place | the editor's truth becomes the optional part; the model would need to forbid drawn names that collide with computed ones, and a data model can't forbid names in a library |

## 3. Writer policy

1. `given` and `relations` hold exactly what was stated. A writer never writes an inherited fact into either.
2. `derived` holds everything the rules can derive from `given` and `relations`, by a derivation that passes the
   conformance suite (§5). A fact the rules cannot reach for want of a stated fact is absent; so is a fact whose
   evidence contradicts itself. `derived` is never written by hand, and never holds less than the rules derive.
3. `derived` is stamped: `provenance.rules` names the rules version that produced it, present exactly when `derived`
   is.
4. Any change to `given` or `relations` makes `derived` stale. The writer re-derives it before it saves. A file never
   carries a `derived` that does not match its facts.
5. The canonical form of ADR 0008 §4.8 covers all three maps and the stamp, so two conforming writers given the same
   facts write the same bytes.

## 4. Reader policy

1. For the meaning of a name, a reader looks in `derived`, then `relations`, then `given`; the first hit wins. A
   reader with a specific purpose (a diagnostic, an editor) may read one map directly.
2. `derived` is effectively a cache. Where it is stamped with rules the reader does not hold, a reader that needs meaning
   rebuilds it with a conforming derivation.
3. A file may be incomplete. Each consumer decides whether it holds enough for its own work, as a capability gate: the
   documentation views may draw a layout no code generator can yet build a sketch for. What a consumer does short of
   what it needs is its own stance (the code generator's is out of scope here).
4. A key the reader does not know is skipped and reported at info (ADR 0008 C8, strict writer and lenient reader).

## 5. One definition of the computation

Every writer must produce the same `derived` from the same facts: the KiCad importer today, Studio later, whatever
language Studio is written in. Three parts, one version:

- **Normative rules.** The relation table of ADR 0009 §3.12 and the derivations it does not yet hold (circuits and
  their names, control point propagation, ports and links, a mast's heads), written as rules and versioned by date.
  This is a text change to ADR 0009 that waits for this ADR.
- **A conformance suite, as data.** Each case is a file: `given` and `relations` in; the expected `derived` and the
  expected diagnostics (by code and symbol) out. The scenario tables in `tests/test_trackplan.py` and
  `tests/test_layout_compiler.py` become its first cases. Diagnostics are part of the suite so that every writer
  reports one problem with one code.
- **A reference derivation.** `tools/layout_model/derive.py`, beside the schema's reader and writer: it takes the
  three maps and returns `derived` and the diagnostics. Today that logic lives inside the KiCad compiler (§9 lists
  it); it moves out, and the importer calls it.

Default location: `schemas/layout-model/rules/` (the rules' version and changelog) and
`schemas/layout-model/conformance/` (the cases), beside the schema, moving to FieldUnit with it (view O15).

## 6. Incomplete is not in error

Two different conditions, which ADR 0008 §4.7 already separates (absence is information, view O13):

- **Incomplete.** A fact is not stated: a layout with no `CP Name` on any house, a device with no binding. The rules
  derive what they can; whatever depends on the missing fact is absent from `derived`. The file is written, with no
  promise that every consumer can do useful work with it (§4, item 3). How much to say about the gaps is the writer's
  choice: the KiCad importer reports each at `missing`, as today.
- **In error.** Stated facts contradict each other: a `CP` naming no house, two names on one circuit, two houses
  reaching an appliance that states none. The model must be fixed. The facts in conflict derive nothing; the rest
  derives as usual.

Whether a writer saves a file in error is its own policy, not the file's:

- **The KiCad importer is picky.** Its output feeds generators while KiCad is the source: a drawing in error writes
  no file (ADR 0008 §4.6 kept), and the diagnostics go to its log.
- **Studio is not a compiler.** It is an editor that saves work in progress. It may save a layout in error, read it
  back and keep improving it, treating completeness and correctness as a lifecycle gate rather than a refusal to
  save. Its diagnostics are its own display (out of scope).

The conformance suite (§5) fixes what `derived` holds in every case, incomplete and in error included, so two writers
given the same facts write the same `derived`, whatever each chooses to say about it.

## 7. Geometry always

ADR 0010 made the placement reader optional (`--geometry`, C2). Studio needs geometry and so does every expected
consumer (the four views). Default: every file carries it, the flag goes, and the KiCad importer always reads the
sheets and libraries beside the netlist. Geometry's own rows take the same three maps: a placement is `given`; a run's
`circuit` and `from`/`to` ports are `derived`.

## 8. Limits (recorded, not decided)

- **KiCad is the one source until Studio exists.** Nothing generates KiCad from this file, so the file cannot be a
  source: it is the importer's output, and an edit to it is lost at the next import. When Studio exists, this rule is
  revisited (ADR 0008 §4.6's single source).
- **The flow from KiCad is one way.** The importer drops references, `Value`, KiCad's housekeeping fields and the
  sheet hierarchy, and writes each wire as a named relation. A round trip back to KiCad is neither needed nor exact.

## 9. Consequences

- The schema is reshaped in place. It is a working schema with no consumer: no version bump until a release, which
  will be 2.x over the published 1.x (the owner, 2026-10-26). Every entity changes shape, the 3.0.0 ones included:
  transports, encodings, processors, CMRInet Nodes, drivers, houses, columns, devices, appliances, track rows,
  geometry.
- **The derivation moves out of the compiler.** Most of what `tools/layout_compiler` holds is lasting and moves to
  the reference derivation (§5): the relation table's resolution of explicit form against fallback (`seams.py`);
  circuits and their names, control point propagation, ports, links, named ends and NextCP pairing (`trackplan.py`);
  a run's circuit and ports (`geometry.py`). What stays is the importer: reading the netlist, the sheets and the
  libraries, `key_of`'s table of key fields, wires turned into named `relations`, and the macro expansion of ADR 0008
  §4.4. `CONSUMED`, `NOT_SETTINGS` and `settings_of` go.
- The example is regenerated in its own commit; the tests become the conformance suite plus the importer's own.
- `tools/contract/lint_symbol_fields.py` is unaffected: it checks the library, not the file.

## 10. Out of scope

- The code generator's stance on a file short of what it needs.
- Studio itself, its editor and its diagnostics display.
- Recording how a derived fact was reached (`controlPointBy: stated | chain | house`), until a consumer asks.
- ADR 0003 rule 8 crossovers and detection blocks in `TC`, held for a separate discussion (the owner, 2026-10-26).
