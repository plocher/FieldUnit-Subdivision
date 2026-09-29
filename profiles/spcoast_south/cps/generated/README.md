# KiCad-projected plant JSON

FieldUnit runtime payloads generated from KiCad. One file per **interlocking**
(e.g. `Luchessa`), not per controlled point (`CP Luchessa`, `CP Gilroy`,
`CP Carnadero` are its members; see the sidecar's `controlledPoints`).

```zsh
python3 tools/parse_kicad_plant.py \
  --library "$KICAD_RAILROAD_LIB" \
  --schematic "$KICAD_LUCHESSA_SCH" \
  --format fieldunit-json \
  --plant-name Luchessa \
  --plant-id spcoast.Luchessa \
  --output /tmp/Luchessa.json
```

Then move `projectionDeferred` into the `.projectionDeferred.json` sidecar. The
plant name is already the interlocking name, which is also the CodeLine (MQTT)
station key, so no manual rename is needed.

The same output is produced by `make json` in
`~/Dropbox/KiCad/Railroad/SPCoast/Luchessa/` (as `Luchessa-field.json`).

Legacy harvest files remain one directory up until each station is cut over.
