# CTC Dispatcher Panel Hardware Binding — Checkpoint

Status: experimental data model proven on one station (CP Luchessa). Not yet
generalized or consumed by any compiler/runtime code.

## The gap this addresses

The KiCad → FieldUnit JSON pipeline (`tools/parse_kicad_plant.py`) captures the
*vital field plant*: switches, tracks, signals, routes. It captures nothing
about the *dispatcher desk*: which physical column a lever lives in, which
I2C/CMRI bit drives which lamp, which appliances the desk's CodeLine schema
must decode, or how several vital track circuits can share one physical
lamp. That knowledge currently lives only as hand-typed C++
(`configureDesk()` in `spcoast_ctc.ino`) and hand-tuned bit constants
(`examples/spcoast_ctc/IO-I2C.h`'s `PanelIO::read`/`write`), with nothing
checking the two agree. The Luchessa desk-cutover bug (office schema
declared 2 track lamps, field emitted 9) was a direct symptom of this gap.

Historical precedent exists: the legacy `ArduinoPoint` XML (e.g.
`SouthCTC.xml`) captured exactly this — per-column device index, explicit
lamp position, physical faceplate label vs. internal appliance name, LED
color — but that information was never carried forward into the KiCad/JSON
pipeline.

## What was built

**New symbol library**: `~/Dropbox/KiCad/InterlockingPlant/symbols/RailroadPanel.kicad_sym`
(registered in the global `sym-lib-table` alongside `Railroad`). Eight symbols:

- `CtcMachine` — one per physical desk. Protocol/vocabulary facts (`Type` =
  `US&S506`, `Era`, `Columns`). Analogous to the plant library's `MAIN HOUSE`.
- `PanelColumn` — one per physical column. Pure documentation (no pins,
  no netlist participation): `Value` = column number, `Interlocking`,
  `Machine` (cross-references `CtcMachine.Value` by string, not a wire).
- `PanelColumn-MAX7313` — one physical IO expander instance bound to a
  column. Real numbered pins (`bit0`..`bit15`) with function labels
  (`SW N`, `LED MB1`, etc.) silkscreened on the body. `Value` = I2C address.
- `PanelSwitch` / `PanelLock` — lever plates for dispatcher-controlled
  switches/locks. Pins are the literal AAR wire suffixes (`NWS`, `RWS`,
  `NWK`, `RWK`) — mandatory, type-fixed vocabulary, so no explicit token
  field is needed; the token is `{Value}NWS` etc.
- `PanelSignal` — lever plate for signals. Pins `SGS`/`NGS`/`HS` (control),
  `SGK`/`NGK`/`TEK` (indication) — matches FieldUnit's real wire vocabulary.
- `PanelAuxiliary` — generic 1-bit **control-only** appliance (Maintainer
  Call, switch heater, bungalow door, ...). One `SW` pin. Unlike
  Switch/Signal, its vocabulary isn't type-fixed, so it carries an explicit
  `ControlToken` field. `Vital` field (default `NO`) documents whether it
  participates in vital safety logic (none do today).
- `PanelLamp-RED` / `PanelLamp-YELLOW` — generic **indication-only** lamp.
  `Value` is a category label for the legend (`OS`/`TRACK`/`MC`);
  `IndicationToken` is the actual token(s) this lamp displays, comma-separated
  when one physical lamp aggregates several track circuits (see below).
  Used for both the maintainer-call indication (yellow, decoupled from
  `PanelAuxiliary`'s control-only pin) and all track-diagram lamps.
- `PanelCode` — station CODE pushbutton, one per multi-column station.

**Example project**: `~/Dropbox/KiCad/Railroad/SPCoast/South-cTc/` —
`South-cTc.kicad_pro`/`.kicad_sch`. Models Luchessa's real columns 5–7:
switches 783/795/799, signal 784, maintainer call MC1, code button, and two
real panel lamps (783T1; and an aggregate covering 795T1+2NAA+799T1). Pin
connections are made by **exact coincident coordinates** between appliance
pins and expander bits (no drawn wires) — the same technique the existing
`Railroad` library already relies on throughout.

## Ontology decisions worth remembering

- **Cross-reference mechanism differs by relationship type.** Appliance
  symbol ↔ plant appliance, and column ↔ desk: plain `Value`-string match
  (no real KiCad connectivity — there's no electrical circuit between a
  physical field bungalow and the dispatcher desk; they only talk over
  CodeLine/MQTT). Lever/lamp ↔ IO expander bit, within one desk: **real
  pin-to-pin coincidence**, because that genuinely is a physical wire on the
  same board.
- **Control vs. indication vocabulary is asymmetric.** Switch/Signal tokens
  are mandatory and mechanically derived from `Value` (`{V}NWS`, `{V}T1`,
  etc.) — no stored token needed. Generic 1-bit appliances have no fixed
  formula, so they carry explicit `ControlToken`/`IndicationToken` fields.
- **A lamp is a display device, not a wire-schema decision.** All of a
  plant's track circuits are unconditionally on the CodeLine wire (matching
  `cp_.trackCircuitCount()` today) — there is no "internal-only, not on the
  wire" track circuit. What's optional is whether a given circuit has a
  *physical model-board lamp*, and whether several circuits' occupancy gets
  OR'd onto one shared lamp (real example: `795T1`/`2NAA`/`799T1` share one
  lamp because the two turnouts are ~6 inches apart on the prototype). The
  OR happens on the office side, after decode — it does not shrink the wire
  schema. Not every track circuit needs a lamp at all (five of Luchessa's
  six interior/approach blocks have none, and that's fine — FieldUnit's
  `InterlockingPlant` already has a real precedent for "exists on the wire,
  no panel representation" in `Switch::appearsOnCodeLine()`).
- **Missing panel binding for a CodeLine-citizen appliance is an error, not
  an absence.** A non-dependent-derail switch/signal/MC with no `PanelSwitch`
  /`PanelSignal`/`PanelAuxiliary` anywhere is a configuration gap (mirrors
  the existing `missing_cp_allocation` diagnostic pattern), since every such
  appliance is unconditionally a CodeLine citizen by type.
- **Instance moves don't need to touch symbol definitions.** Fixing pin
  alignment is a rigid-body translation of a placed instance's `(at X Y)` —
  it cannot distort graphics, because library-local pin/graphic coordinates
  never change relative to each other. No project setting governs Y-axis
  direction in the Symbol Editor; it is a fixed, Y-down system throughout
  (confirmed: no such toggle exists in `eeschema.json`/`symbol_editor.json`,
  unlike the PCB/Footprint editors' `origin_invert_y_axis` display-only
  preference, which is unrelated).

## Verification status (as of this checkpoint)

**Netlist-confirmed correct.** `South-cTc.net` (KiCad's own exported
netlist — the authoritative source, not coordinate math) shows all 24
intended appliance-pin ↔ expander-bit pairs correctly matched to the
`IO-I2C.h` bit assignments (e.g. `SW783.NWS`↔`U1.bit7`/`SW_NORMAL`,
`SIG784.TEK`↔`U1.bit15`/`SIG_STOP_LAMP`, `AUX1.SW`↔`U2.bit2`
/`MAINTAINER_CALL_SW`), for all three columns. All 24 genuinely-unused
expander bits are correctly marked `no_connect`. ERC is clean (0
errors/warnings).

Getting to this point took an extended, partly-wrong debugging detour into
manual coordinate arithmetic (chasing a phantom Y-axis transform bug that
didn't actually exist). **Lesson for next time: trust KiCad's own
netlist/ERC output as ground truth immediately; don't reverse-engineer
connectivity from raw `.kicad_sch` coordinates.**

## Open items / next steps

1. **This is Luchessa-only.** The other six SPCoast South stations
   (Christopher, Corporal, Sargent, Watsonville, GilroyCaltrain,
   GilroyInterchange) have no panel-binding data yet.
2. **Nothing consumes this data yet.** No compiler script reads
   `RailroadPanel` symbols to generate or validate `configureDesk()` or
   `IO-I2C.h`; today's C++ is still hand-typed and hand-synced.
3. **FieldUnit library gap**: `cTcMachine.h`'s `PanelColumn`/`CtcStation`
   currently conflates "codec-decoded track" with "physical lamp slot" in
   one array. Supporting N decoded wire facts feeding M physical lamps
   (with an OR in between) needs a real change there, not just data
   modeling.
4. **`PanelAuxiliary`/lamp generalization is untested beyond MC.** Switch
   heaters, bungalow door locks, etc. have no FieldUnit vital-engine home
   yet (only `maintainerCall[]`, a fixed positional bool array, exists
   today).
5. **Desk-project structure decision**: `South-cTc` currently holds only
   Luchessa's columns. As other stations get KiCad-native cutovers, decide
   whether they become additional hierarchical child sheets in this same
   project (matching the legacy `SouthCTC.xml`'s `<depends>` structure) or
   something else.
6. **XML bootstrap**: auto-converting the remaining legacy `ArduinoPoint`
   XML into rough panel-binding candidates (needing human cleanup) is
   planned but not started.
