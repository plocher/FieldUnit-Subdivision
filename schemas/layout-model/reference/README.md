# Reference data

General facts, not layout data (ADR 0012 §6): one JSON file per table, the source and not an output (the owner,
2026-11-13). The reference derivation resolves them per entity into `derived`, so a consumer of a Layout Data Model
File reads the resolved words from the file. A consumer that needs a table itself reads it here, at the path the
file's `provenance.referenceData.<table>.file` names (relative to `schemas/`). Nothing here imports Python.

## A file

| Key | Meaning |
|---|---|
| `table` | the table's name, the file's stem; `provenance.referenceData` names it |
| `schemaVersion` | the version of `<table>.schema.json` the file is written to; 0 until the KiCad importer and FieldUnit work end to end, with no bump rules before then |
| `version` | the table's provenance date, `.n` when revised again that day; a layout file names it |
| `provenance` | where the rows come from: the owner's ruling, the document and date, or the standard opened |
| `rows` | the table, keyed as its schema says |

A table may hold its own constants beside `rows` (`regimes`: `ctc`, `currentOfTraffic`). The schema beside each file is
the contract; `tests/test_reference_data.py` validates every file against it.

## The tables

| Table | Rows keyed by | A row |
|---|---|---|
| `encodingTransportPairing` | encoding Kind | the transport Kind it rides |
| `driverEncodings` | driver IC | the encoding Kind it needs on its processor |
| `indicationTokens` | encoding Kind or `default` | appliance class → token templates (`{name}K`) |
| `stations` | encoding Kind or `default` | `house` or `interlocking` |
| `codeLineCapacity` | code line type | stations, controls, indications in steps; `options` or `steps` forms; `source` |
| `codeLineSteps` | code line type, appliance class | controls and indications in steps |
| `trainOrderInputs` | rulebook or `default` | `inputs`, a list ranked from the most restrictive, each `{input, indication}`; `rest`. Resolved onto a face keyed by rank |
| `regimes` | GCOR Rule marker Kind | the chapter or rule title |
| `aspectNames` | JMRI signal system, indication | the aspect name, or a map by mast Kind |
| `headModels` | head Style | `source`; `words`: head word → outputs (`lamp`, `arm`) |
| `policies` | rulebook, head count, mast indication | the head word of each position top down (no row shipped yet, #62) |

## Selection and overrides

The layout selects: `layout.given.Railroad`, `Era` and `Rulebook` choose the row of every layout-keyed table
(`trainOrderInputs`, `policies`), and `layout.derived.reference` names the row each resolved to. An entity's own
fields choose the rest: a head's `Style`, a driver's `JMRI.SignalSystem` (over its encoding's), a code line's `Kind`.
An explicit override is a stated field beside the item: a train order board's `Rest` and `Shows.<input>`, a mast's
`Indications`. The user's own tables layer over these (`derive(model, reference_data=...)`, keyed by table name); a key
with no row resolves to nothing, never a guess.
