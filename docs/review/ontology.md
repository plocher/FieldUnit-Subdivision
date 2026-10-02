# Ontology: facets of one place

Status: draft for review (2026-10-01, rev 5). Replaces rev 4.

## 1. Status and scope

- This document is a delta on FieldUnit `docs/GLOSSARY.md` (here: "the glossary").
- The glossary defines the terms. This document does not define them again. It cites them by glossary section.
- This document adds what the tooling needs: entities, relations and cardinalities. For each fact it states what is drawn, what is derived, what is checked, and which phase does it.
- The phases are those of ADR 0001 D6: compiler and linker, generator, run time.
- Decisions come from the glossary, `docs/adr/0001-code-line-type-contract.md` (D1 to D16), and `vocabulary-review.md` iterations 9 and 10.
- Order of authority (vocabulary review, iteration 9):
  1. the relay model of the interlocking logic (glossary §10.6);
  2. `src/` in FieldUnit;
  3. KiCad-derived interlocking models;
  4. legacy sketches and harvested profiles, as evidence only.
- Era is not a model input. Era text in a title block or in a `CtcMachine` field is documentation.
- Validation is permissive. A check asks whether a target can carry what is drawn. No check requires a structure.
- "(unverified)" marks a statement that no opened source supports.

### 1.1 Changes from rev 4

- The structure follows the facets of glossary §2.2. Rev 4 followed eras.
- A `MAIN HOUSE` symbol declares a control point. The tooling does not derive control points or count them.
- The signal graph cut (spike S3, Rule A) derives interlocking limits. It does not derive control points.
- "Field station" replaces "controlled point", "station" and "line station". A field station depends on the code line type.
- The `CP` field stays. It is the drawn assignment of an appliance to a control point. Rev 4 §7 retired it.
- Luchessa has three control points by a design decision of the layout. Rev 4 argued this from history. That argument is withdrawn.
- US&S 506 facts come from glossary §6. Rev 4's pasted source list is removed.
- KiCad names have no `CP ` or `CP_` prefix (ADR D12).
- Withdrawn from rev 4, with no replacement:
  - "a control point is by definition a track switch";
  - "control points grow geometrically", "one per switch";
  - the "exactly 7 of 7" costing table and "a signal control is always three steps";
  - "the panel symbol set already encodes this budget";
  - "15 versus 16 steps: both are right";
  - "TowerMaster";
  - the chronology that puts towers and ABS/APB after CTC;
  - "Luchessa is prototypically correct" and "keep three control points permanently";
  - "Field Unit 1:1 Bungalow";
  - "Control Point 1:N controlled point".

## 2. Roles and the seam

Glossary §2.1 states the three roles and the seam. Glossary §2.3 states the tower and CTC difference.

| Role | Drawn in | Model entity |
|---|---|---|
| CTC machine | CTC machine project (`South-cTc`): `CtcMachine`, `PanelColumn`, panel appliances, IODRIVER symbols | CTC machine model |
| code line | `CODELINE` symbol on each interlocking sheet of the CTC machine project | code line (the layout's default) |
| field unit | plant project (topology sheet); a hardware sheet is planned (`desk-codeline-kicad-pattern.md` §5a) | interlocking model; field unit only for drawn hardware |

- The model records the facts of each role. A generator chooses an implementation for each role (ADR D6).
- The seam carries controls and office indications as named functions. The names are the same for every code line type.
- Below the seam, each code line type defines its own step, code cycle, address, field station, capacity, encoding and timing.
- Vital logic is in the field unit only. A code line function is interlocked or auxiliary (glossary §5). The model does not mark a code line function as vital.
- A generated CTC machine application lets the operator state an unsafe intent (glossary §2.3). It does not copy locking to the office.
- Relations between the control points of one interlocking are behind the seam. The code line does not carry them.

## 3. Facets

Glossary §2.2 lists the facets. Each section below gives the tooling view of one facet.

### 3.1 Function: control point

Glossary §4, "control point".

- The designer declares each control point. One `MAIN HOUSE` symbol declares one control point. Its Value is the name.
- The tooling never derives a control point. Switches, signals and panel columns do not count control points.
- An interlocking contains one or more control points.
- The `CP` field of an appliance assigns the appliance to one control point in the field.
- The `CP Name` field of a `PanelColumn` names the control point of that column.

| Fact | Drawn or derived | Phase | Check |
|---|---|---|---|
| a control point and its name | drawn: `MAIN HOUSE` Value | compiler | Value present; not a library placeholder; unique in the interlocking (case folded) |
| appliance to control point | drawn: `CP` field | compiler | value equals a `MAIN HOUSE` Value of the same plant project |
| panel column to control point | drawn: `PanelColumn` `CP Name` | linker | value equals a `MAIN HOUSE` Value of the interlocking of that sheet |
| number of control points | not derived | none | no check requires a number (ADR D5) |

- A difference between the `CP` field of an appliance and the column of its lever or lamp is not an error (ADR D3). Example: track circuit 1NA has `CP` = CP Carnadero. Its lamp is in column 6, which names CP Gilroy.
- Name rule (ADR D12): a KiCad name contains no `CP_` and no `CP `. A model board can add `CP ` for display.
- Names today, to be fixed:
  - Luchessa `MAIN HOUSE` Values: `CP Luchessa`, `CP Gilroy`, `CP Carnadero`.
  - Luchessa `CP` fields and column `CP Name` fields: the same three values.
  - `CP Name` on the other interlocking sheets: `CP_<Name>` forms or `FIXME` (Watsonville excluded; its schematic is not valid evidence).
  - `CP` fields at Christopher: `CP Christopher North` and others, while the `MAIN HOUSE` Values are bare.
- After the fix, the interlocking `Luchessa` and the control point `Luchessa` have the same name. They differ by kind only.
- Luchessa is one interlocking with three control points. This is a design decision of the layout (selective compression).
- The owner plans to reduce Luchessa to one control point later. The tooling treats both shapes the same way.

### 3.2 Mechanism: interlocking

Glossary §4, "interlocking"; glossary §2.4 for the interlocking logic.

- One plant project draws one interlocking plant. Its interlocking model is one entity, keyed by the interlocking name.
- The interlocking name is the plant project name. It is also the sheet name in the CTC machine project (`desk-codeline-kicad-pattern.md` §3).
- The interlocking logic enforces safety for all control points of one interlocking together.
- Signals, routes and topology belong to the interlocking. They do not belong to one control point. Example: signal 784 has masts at all three Luchessa control points.

| Fact | Drawn or derived | Phase |
|---|---|---|
| track, switches, derails, masts, heads, track circuits, policy markers | drawn | compiler |
| signals (masts that share a number) | derived | compiler |
| routes and their best indication | derived | compiler |
| OS track circuit of a switch (`<switch>T1`, or the `TC` field) | derived | compiler |
| dependent derail and its switch (`<switch>D`) | derived | compiler |
| locking, aspects, office indications | not in the model | run time (interlocking logic) |

- The compiler checks the conventions in `AGENTS.md`, "KiCad conventions the compiler relies on".
- The model copies no interlocking rule. The relay model is the design principle of the logic (glossary §10.6).

### 3.3 Extent: limits

Glossary §4, "interlocking limits", "control point limits", "CTC limits".

| Limits | How they are known | Phase | Status |
|---|---|---|---|
| interlocking limits | derived: cut the track graph at every controlled signal; each piece that contains a switch or derail is one interlocking (spike S3, Rule A) | compiler | spike code only; not in `tools/` |
| control point limits | drawn: the `CP` field | compiler | in the model; the compiler reads `CP` on the signal IRJ only, not on the mast (spike S3) |
| CTC limits | not drawn | none | not modeled |

- Spike S3 results: Luchessa gives one piece. GilroyInterchange gives one. Sargent gives one, plus one circuit of the next plant.
- Corporal, Christopher and GilroyCalTrain have no nets. Rule A did not run on them.
- Control point limits are not derived. Rule B (house allocation from switch anchors) disagrees with two drawn Luchessa values (784WA, 1NA). These are drawn facts. They are not errors.

### 3.4 Addressing: field station and code line type

Glossary §3, "field station", "code line type"; glossary §6; ADR 0001.

Code line type:

- A code line type is one encoding on one transport (ADR D1). Example: AAR tokens over MQTT.
- Drawn form, planned: one `CODELINE` symbol with two pins. One pin takes an encoding symbol. The other takes a transport symbol (D15).
- Drawn form, today: `Codeline-MQTT`. Its Value names the transport only.
- The drawn code line is the layout's default. The generator can emit another target from the same model, for example virtual or US&S 506 (D6).
- Type definitions are data files in the SPCoast KiCad repo (D10; option A). Encoding rules are truth tables (D11, provisional).
- First target: AAR tokens over MQTT. Nothing in the model or the code may rule out US&S 506 (D14).

Field station:

| Encoding | Field stations | Name | Functions carried |
|---|---|---|---|
| US&S 506-style | one for each control point | the `MAIN HOUSE` Value | the levers and lamps of the panel column whose `CP Name` is that control point |
| AAR tokens | one for each interlocking | the interlocking name | the levers and lamps of all columns of that interlocking sheet |

- A field station is the abstraction that the interlocking presents to the dispatcher (ADR D3). The interlocking keeps it true.
- A signal control (left, stop, right) is one function of one lever. It goes to the field station of that lever.
- Routes, masts and aspects are not code line functions.
- An appliance of one control point can serve a function of another field station of the same interlocking. This is normal.
- An interlocking model with no `MAIN HOUSE` symbol cannot use a 506-style encoding. A `MAIN HOUSE` with no Value is an error when a 506-style encoding is the default or a target (ADR 0001, consequences).
- ADR D3 says "its panel column". It does not name the field that joins a column to a field station. This document reads it as `CP Name` (unverified).

Code chart, address and capacity:

| Fact | Source | Phase |
|---|---|---|
| code chart, one for each field station | the encoding's defaults plus authored overrides; or an authored chart, checked (D2) | generator |
| address of a field station | authored as a field of the `CODELINE` symbol (D13); never allocated (D4) | compiler records it; the generator fails for a target that needs it and does not find it |
| capacity | counts steps after the chart is applied; never tokens or symbol pins (D5) | compiler for the drawn default; generator for each target |
| dropped function | allowed; reported as info or under a verbose flag (D5) | generator |
| size limits (`MAX_MAP_ENTRIES`, `MAX_APPLIANCES`, buffers) | each phase checks what it sees (D7, D16) | compiler, generator; run time optional |
| encoding and decoding; `TEK` with `NGK` or `SGK` | the chart; D8 | run time |

- For AAR tokens the chart is the identity. The type sets no capacity limit.
- For US&S 506, glossary §6 gives the facts: 16 steps (1 + 7 + 7 + 1), 7 controls and 7 office indications for each field station, 35 field stations on one code line.
- Step assignments are illustrative only. The layout owner states the assignment.
- The capacity check never requires a number of field stations or control points. A failure says that the drawn content does not fit the target.
- ADR 0001 has the Luchessa worked example: three field stations fit 7 + 7 each; one field station does not fit.
- Luchessa has one CODE button for three columns. ADR D9 gives two workarounds. Neither is chosen (D14).

### 3.5 Logic: six terms and the field unit

Glossary §2.4 (six terms) and §2.5 (cardinality). This table adds the phase that produces each thing.

| # | Term | Produced by | Phase | Today |
|---|---|---|---|---|
| 0 | interlocking plant | the layout | none | on the layout |
| 1 | interlocking logic | FieldUnit `src/`; class `InterlockingPlant`, rename to `Interlocking` planned | not generated | yes |
| 2 | interlocking model | plant schematic to `generated/<Interlocking>.json` and the portable model | compiler | Luchessa only |
| 3 | interlocking application | logic plus model plus chart tables | generator | not a file; `spcoast_virtual_plant` builds it at start |
| 4 | field processor | deployment; hardware sheet planned | none | simulator only |
| 5 | field unit | (3) running on (4) | run time | virtual only |
| 6 | field station | §3.4 | compiler (names), generator (charts) | AAR tokens over MQTT only |

- One field unit solves one interlocking plant in one deployment.
- A field unit answers at every field station of its interlocking on its code line. Luchessa: three on a 506-style encoding; one on AAR tokens.
- The CTC machine application and the interlocking application read one set of chart tables. Neither end builds its own list (D6).
- Today each end builds its own list (ADR 0001, "What the code does today"). This is debt.

### 3.6 Enclosure: bungalow and `MAIN HOUSE`

Glossary §3, "bungalow".

- The `MAIN HOUSE` symbol declares a control point and its bungalow. One symbol carries both facets.
- No separate bungalow symbol is needed.
- A field unit is not a bungalow. A field unit is an application that runs. A bungalow is an enclosure.
- An interlocking with several bungalows has one field unit. The model does not record which bungalow holds the field processor. This is a deployment fact.
- The maintainer call is at a bungalow. See §5.3.

## 4. Cardinalities

| Relation | Cardinality | Known by | Source |
|---|---|---|---|
| subdivision to interlocking | 1 : N | folder membership | `layout-model.md` §0 |
| interlocking plant to control point | 1 : N | drawn (`MAIN HOUSE`) | glossary §2.5 |
| control point to bungalow | 1 : 1 | the same symbol | glossary §3 |
| appliance with a `CP` field to control point | N : 1 | drawn (`CP` field) | glossary §4 |
| interlocking to interlocking limits | 1 : 1 | derived (Rule A) | spike S3 |
| control point to field station | 1 : 1 on a 506-style encoding; N : 1 on AAR tokens | code line type | glossary §2.5 |
| control point to panel column, on one CTC machine | 1 : 0..1 | drawn (`CP Name`); linker check | `desk-codeline-kicad-pattern.md` §7a |
| field station to panel column | 1 : 1 on a 506-style encoding (unverified); 1 : N on AAR tokens | code line type | ADR D3; `MAX_COLUMNS_PER_STATION` = 4 today |
| field station to code chart | 1 : 1 | generator | ADR D2 |
| field station to address | 1 : 1 | authored | ADR D4, D13 |
| code line to field station | 1 : N (US&S 506: N up to 35) | code line type | glossary §6 |
| CTC machine to code line | M : N | drawn | `layout-model.md` §1 |
| interlocking plant to field unit | 1 : 1 in one deployment | none | glossary §2.5 |
| field unit to field station | 1 : N | code line type | glossary §2.5 |
| field processor to field unit | 1 : N | deployment | glossary §2.5 |
| CODE button to field station | 1 : 1 on a 506 machine (unverified); 1 : 3 at Luchessa | drawn | ADR D9 |

## 5. What this settles in the tooling

### 5.1 The `CP` field (issue #16)

- Meaning: the drawn assignment of an appliance to a control point in the field. It gives the control point limits.
- It does not group functions into field stations. The panel column does (ADR D3).
- It cannot be derived from signals. Rule A gives interlocking limits. Rule B needs one anchor for each switch, and it disagrees with two drawn Luchessa values.
- Rev 4 §7 ("retire the `CP` field") is reversed.
- Issue #16 says that control points are optional and that the decomposition is a 506 requirement. Rev 5 does not adopt this. Control points are declared layout facts. One field station for each control point is a property of the 506-style encoding.
- Proposed scope for #16 (owner to decide): keep the field; check that it resolves; fix the drift and the names (D12).
- Drift today. Method: each symbol with a `CP` field whose value is not a `MAIN HOUSE` Value of the same `.kicad_sch` (empty values included), read 2026-10-01. Issue #16 used another method and reports 66. That total includes Watsonville; not valid. Without Watsonville this method gives 39 of 88 (21 + 10 + 0 + 4 + 0 + 4 = 39 unresolved; 21 + 13 + 16 + 13 + 15 + 10 = 88 symbols). Watsonville excluded.

| Project | Unresolved of all | Values seen |
|---|---|---|
| Christopher | 21 of 21 | `CP Christopher North`, `CP Christopher South`, `CP Christopher`, empty |
| Corporal | 10 of 13 | `FIXME`, empty, `INDUSTRY` |
| GilroyCalTrain | 0 of 16 | |
| GilroyInterchange | 4 of 13 | empty |
| Luchessa | 0 of 15 | |
| Sargent | 4 of 10 | empty, `Corporal` |
| Watsonville | excluded: the Watsonville schematic is incomplete and not valid evidence (owner, 2026-10-02) | |

### 5.2 `fieldUnits[].station` in `layout-model.md`

- It becomes a list. Field unit to field station is 1 : N (glossary §2.5; ADR 0001, consequences).
- Proposed form: `fieldUnits[].codeline`, with the field stations derived from the encoding (§3.4).
- Whether one field unit can serve two code lines is open.
- `stations[]` there becomes field stations. On a 506-style encoding the name is the `MAIN HOUSE` Value. On AAR tokens it is the interlocking name.

### 5.3 Maintainer call

Re-derived under the rev 5 model:

- A maintainer call is an auxiliary function (glossary §5). It calls the maintainer to a bungalow.
- Its control point is given by its `CP` field, as for any appliance.
- Its control and office indication go to the field station of the column that holds its lever and lamp (ADR D3). Luchessa: `MC1` is in column 6, so a 506-style encoding puts it in field station CP Gilroy.
- Rev 4 said: "call count is at most the house count everywhere". The drawn symbols today (`MaintainerCall` symbols and `MAIN HOUSE` symbols, read 2026-10-01):

| Project | Calls | Bungalows |
|---|---|---|
| Christopher | 2 | 3 |
| Corporal | 1 | 2 |
| GilroyCalTrain | 0 | 3 |
| GilroyInterchange | 2 | 2 |
| Luchessa | 1 | 3 |
| Sargent | 1 | 1 |
| Watsonville | excluded: the Watsonville schematic is incomplete and not valid evidence (owner, 2026-10-02) | |

- The observation holds in all six other projects: calls never exceed bungalows (2 of 3, 1 of 2, 0 of 3, 2 of 2, 1 of 3, 1 of 1). Watsonville is excluded: its schematic is incomplete and not valid evidence (owner, 2026-10-02). Issue #16's reading of its symbols as yard selectors is not used. Model-layout yards will be supported by the tooling later.
- "At most one maintainer call for each bungalow" is a candidate check. It is not a rule now (owner to decide).
- The check cannot run today. Christopher's calls name `CP` values that match no `MAIN HOUSE`. The calls at Corporal, Sargent and Luchessa have no `CP` field. The Luchessa call has an empty Value; `MC1` is its Reference.
- A maintainer call does not create a control point. "More than one call forces more than one control point" (rev 4 §4, issue #16) is withdrawn.
- The plant model must carry maintainer calls (`desk-codeline-kicad-pattern.md` §7a, known gap). The hard-coded calls in `setupCodec()` then go (ADR 0001, consequences).

### 5.4 `CtcStation`

- The glossary defines `CtcStation` as the office-side record of one field station.
- Today the SPCoast desk has one `CtcStation` for each interlocking, with up to four panel columns and one codec. That agrees with AAR tokens.
- On a 506-style encoding there is one `CtcStation` for each control point. A CODE button can serve several (ADR D9, workaround a).
- Its token list comes from the emitted chart (D6). Today `CtcStation::buildCodec()` builds it from the columns.
- The header comment at `cTcMachine.h:278` says "Control Point Spanning 1 to N Columns". It uses the wrong term. This is code debt; it is not changed here.

### 5.5 Panel column

- A panel column is a CTC machine fact (glossary §3). It names one control point by `CP Name`.
- A panel column is not a control point. "A column IS a CP" is replaced by §3.1 and §3.4.

## 6. Open and carried forward

Open:

- Fix the names in the sources (D12): `MAIN HOUSE` Values, `CP` fields, `CP Name`, generated JSON, tests, documents.
- Confirm `CP Name` as the join from panel column to field station (§3.4).
- Decide whether "one plant project gives one Rule A piece" is a compiler check.
- Decide whether "at most one maintainer call for each bungalow" is a check (§5.3).
- Decide whether one field unit can serve two code lines (§5.2).
- Draw the two-pin `CODELINE` symbol and the encoding and transport symbols (D15).
- Build the worked example for truth tables (D11).
- Choose the Luchessa CODE button workaround when a 506 target is built (D9).
- Move `Type` = `US&S506` from `CtcMachine` to the code line (ADR 0001, consequences).
- Reduce Luchessa to one control point: owner's plan, no date.
- Fascia devices and maintainer service modes: own ADR.

Carried forward:

- Use behavioral gates for regression, not frozen goldens (rev 4 §10).
- Capture common track arrangements as KiCad design blocks in `SPCoast.kicad_blocks`. A block does not set a number of control points (rev 4 §10, corrected).
- Connect the nets in Corporal, Christopher and GilroyCalTrain.
- Move the plant compiler from `_PART_KIND` to `Role`/`Kind`. Review the Role name `CONTROLLED_POINT` against the retired term.
- Read the `CP` field on masts, not only on the signal IRJ (spike S3).
- Fix `make all` for six plant projects (`tools/plant_graph/layout.py:65`).

## 7. Rev 4 section map

Other documents cite rev 4 sections: ADR 0001 D5 cites §6a; `spike-cp-membership.md` cites §7 and §8. Rev 4 cited "§5a" for `desk-codeline-kicad-pattern.md` §5a.

| Rev 4 | Topic | Rev 5 |
|---|---|---|
| §1 | what a control point is; 506 detail | §3.1; 506 facts in glossary §6 and §3.4 |
| §2 | how the terms came apart | withdrawn |
| §3 | era-dependent addressing; budget | §3.4 |
| §3a | consolidation; Luchessa | withdrawn; Luchessa in §3.1 |
| §4 | `MAIN HOUSE` is the bungalow | §3.6 |
| §5 | three sources model it this way | §5.4, §5.5 |
| §6 | cardinalities | §4 |
| §6a | permissive validation | §1, §3.4 |
| §7 | what this settles | §5 |
| §8 | Luchessa | §3.1 |
| §9 | resolved | §1.1, §3.6 |
| §10 | carried forward | §6 |
