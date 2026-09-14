# FieldUnit-Subdivision

Operating session runtime and virtual railroad simulator for the [FieldUnit](https://github.com/plocher/FieldUnit) ecosystem.

`FieldUnit-Subdivision` connects multiple Control Points (CPs) into a complete operating territory with live track circuits, block progression, autonomous NPC trains, mobile web cabs, and live overhead model board displays, driven by physical or virtual cTc machines over MQTT.

## Architecture

- **`runtime/plant_host/`**: Headless native C++ virtual bungalow daemon executing authentic FieldUnit vital interlocking logic for all stations on the subdivision.
- **`runtime/graph/`**: Track topology and block progression managing train shunts, clearance fouling points, and sectional release.
- **`runtime/traffic/`**: Train entity model and autonomous NPC autopilot rulebook followers (*Daylight*, *Beet Turn*).
- **`runtime/web/`**: FastAPI/WebSocket server hosting the 2D SVG overhead model board display and responsive mobile crew cabs.
- **`profiles/`**: Layout-specific configuration profiles containing station JSON schemas, topology connections, and timetables.
- **`tools/`**: Harvesting utilities, validation tests, and documentation generators.

## Profiles

- **`spcoast_south`**: Southern Pacific Coast Line from Gilroy Caltrain (MP 77) through Watsonville staging (MP 97), controlled by the 14-column US&S Model 503 `spcoast_ctc` machine.
