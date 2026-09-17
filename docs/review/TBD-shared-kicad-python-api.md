# TBD: Lift generic KiCad services into a shared Python API

## Status
Open (POC tech debt).

## Context
`tools/kicad_services/` in FieldUnit-Subdivision follows the jBOM domain-service
pattern (`SymbolLibraryReader`, `NetlistReader`, `KicadCliNetlistExporter`).
It uses jBOM's `sexp_parser` via the local Dropbox checkout when jbom is not
installed.

These readers are railroad-agnostic. Railroad semantics live only in
`tools/plant_graph/`.

## Future work
1. Contribute equivalent services upstream to jBOM (or extract a small
   `SPCoast-KiCad-API` / shared KiCad Python package with jBOM peers).
2. Replace the FieldUnit local copies with the published package.
3. Keep plant-graph compilation in FieldUnit-Subdivision (or a railroad-domain
   package), consuming the generic readers only.

## Non-goals for the POC
- Publishing a package in this spike
- Geometric schematic connectivity (kicad-cli netlist is the authority)
