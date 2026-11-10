# Recipe: switch 1 as a local switch, and the I/O expander moves (Sargent, Corporal)

Owner request, 2026-11-09, after the Sargent wiring audit. Facts below come from a fresh netlist and ERC of the
SPCoast project as drawn that day (KiCad open, working tree uncommitted). Every edit is the owner's, in KiCad.

## Facts

| Sheet | What is drawn | What it should say |
| --- | --- | --- |
| Sargent | Switch `1` is `Switch_Manual_Sensed`; its `Device-Switch 1` has `M` on the servo driver 0x27 A2, `N`/`R` on MCP23017 0x20 B4/B5 | a motor the field unit drives with no dispatcher: regime `local` |
| Corporal | Switch `1` is `Switch_Manual_Sensed`; its `Device-Switch 1` has `M` on MCP23017 0x22 B6, `N`/`R` on 0x22 B7/B8 | the same |
| Sargent | `1NAT`, `836T`, `2SAT` optical track circuits put their `OCC` outputs on PCA9685-PWM 0x26 B5, B6, B7 | ERC: Output to Output, three errors; the library calls 0x26 a lamp driver |
| Sargent | MCP23017 0x20 has one free pin (B6); PCA9685-Servo 0x27 has A3 to B8 free | not enough input pins for the moves below |
| Corporal | MCP23017 0x22 has A4, A5, A7, A8, B1 to B5 free | enough for the moves below |
| Corporal | track circuit marker `833T` has no `Device-TrackCircuit-*` | a device, or the marker goes |
| Corporal | `Device-Lamp` named `MC1`; the maintainer call appliance is `1MC` (`${Value}MC`) | rename to `1MC` (done on Sargent) |
| Sargent | `1MC` lamp pin shares the pixel data net with the pixel encoder's CHAIN and GPIO-Pixel D2 | a pixel encoder for a binary word (new symbol, with Address) between lamp and chain |

A `local` switch is worked from its `Local-Switch` lever alone (owner ruling 2026-11-09; ADR 0013 §4 as amended in PR 107).
Until the lever is drawn the model reports `switch.lever` at missing on that switch, which is the drawing's truth.

## Sargent

1. Trackplan: replace `Switch_Manual_Sensed 1` with `Switch_Local 1` (Style `local`). Its `TC` keeps the library default
   `${VALUE}T1`: a local switch has an `Indication` like every other and `<switch>T1` is the pattern (owner, 2026-11-09).
2. Field: place `Railroad-Field:Local-Switch` with Value `1` (Style `switch`; pins `NWS`, `RWS`, `NWK`, `RWK`). Keep
   `Device-Switch 1` as it is (M on 0x27 A2, N/R on 0x20 B4/B5).
3. Add a second input-capable expander: `Driver-I2C-MCP23017` at `0x21` on Sargent's `IOBus`. Then:
   - move `1NAT.OCC`, `836T.OCC`, `2SAT.OCC` from 0x26 B5/B6/B7 to 0x21 A1/A2/A3 (ERC errors go away; 0x26 B5 to B8 become free);
   - wire `Local-Switch 1` `NWS`, `RWS`, `NWK`, `RWK` to 0x21 A4/A5/A6/A7 (the same order as `Local-Switch 835` on 0x20 A4 to A7).
   Addresses are per processor bus, so 0x21 is free on Sargent even though Corporal uses it.
4. Maintainer call lamp as a pixel (owner, 2026-11-09): a lamp needs no encoder. A `Device-Lamp` on a pixel data net is
   its own pixel: its `Address` is the slot on the chain and its `Color` (trial attribute) the colour it shows. Only mast
   indications go through an encoder. The drawing stands; the pin-kind rule (gap 4 below) must allow a `binary` lamp pin
   with an `Address` on a `color` net.
5. Save, ERC: expect 0 errors on Sargent apart from HBA's intentionally unconnected sensor pin.

## Corporal

1. Trackplan: `Switch_Manual_Sensed 1` becomes `Switch_Local 1`, TC decided as above.
2. Field: place `Local-Switch` Value `1`; wire `NWS`, `RWS`, `NWK`, `RWK` to 0x22 A4/A5/A7/A8 (A6 is the `1MC` lamp). Keep
   `Device-Switch 1` on 0x22 B6/B7/B8.
3. `833T`: place `Device-TrackCircuit-Optical` Value `833T` with `OCC` on 0x22 B1, or remove the marker if that track has
   no detection.
4. Rename `Device-Lamp MC1` to `1MC`.
5. Remove the orphan `Device-TrackCircuit-Optical 2NAT` if not already done.
6. Save, ERC: expect 0 errors on Corporal.

## After both

- Fresh compile (`uv run python tools/compile_layout.py SPCoast.kicad_sch -o <scratch>`): expect no `reference.*` or
  `unit.*` findings; `switch.lever` gone on both `1` switches once the levers are wired; the remaining missings are #80's
  heads.
- Commit the Railroad repo (`SPCoast/*.kicad_sch`, by name; `Panels/` stays untracked).

## Compiler gaps this exposed (tickets to file on map #94, owner's go pending)

1. ERC as a gate: run `kicad-cli sch erc` in the SPCoast gate and as an importer primitive; errors fail the gate.
2. Device against appliance both ways: a field device named for no appliance; an appliance with no device, including
   track circuit markers against track circuit devices (a dependent derail needs none; it moves with its switch).
3. Regime against the field device: `manual_sensed`/`manual` with a drive pin wired; `powered`/`dual`/`local` with none.
4. Pin-kind agreement on a net (`binary` against `color`/`indication`/`level`), the functional form of the lamp-on-chain case.
5. Encoder fan-out from one head is allowed; differing capability subsets are informational (#80, recorded 2026-11-09).
