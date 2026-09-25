# KiCad-projected plant JSON

FieldUnit runtime payloads generated from KiCad via:

```zsh
python3 tools/parse_kicad_plant.py \
  --library "$KICAD_RAILROAD_LIB" \
  --schematic "$KICAD_LUCHESSA_SCH" \
  --format fieldunit-json \
  --plant-name "CP Luchessa" \
  --plant-id spcoast.luchessa \
  --output profiles/spcoast_south/cps/generated/CP_Luchessa.json
```

Then strip `projectionDeferred` (or keep a `.projectionDeferred.json` sidecar) and set
`"name"` to the CodeLine station id (`CP_Luchessa`).

Legacy harvest files remain one directory up until each station is cut over.
