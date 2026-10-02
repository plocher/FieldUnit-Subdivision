# Legacy import (one-shot bootstrap)

Turns the historical ArduinoPoint XML definitions
(`~/Dropbox/workspace/ArduinoPoint/definitions/`) into drawn KiCad sources, so
the compiler has more than one interlocking to work on. The output is
**scaffolding, not truth**: it encodes legacy assumptions and every fact the
sources do not record is written as `FIXME`. Only the hand-finished result is
truth, at the fidelity of the hand-drawn Luchessa.

These scripts are expected to be deleted once the six interlockings are
finished. They are not part of the compiler.

```zsh
# close KiCad first: both scripts write .kicad_sch
python3 tools/legacy_import/import_desk_sheets.py     # South-cTc interlocking sheets
python3 tools/legacy_import/import_plant_projects.py  # peer-of-Luchessa plant projects
```

Both refuse to overwrite: a desk sheet that already holds symbols, or a plant
project whose schematic exists, is skipped. Luchessa is never touched.

## What each produces

`import_desk_sheets.py` fills the six empty `South-cTc` interlocking sheets
from `SouthCTC.xml`: one `PanelColumn` per desk column with its
`PanelColumn-MAX7313`, the lamps, levers, maintainer call and code button, and
one `Codeline-MQTT`. Placement is computed from the symbols' pin geometry, so
an appliance dropped on its column pin lands its function pins on the right
expander bits; the script fails loudly if any pin misses. Verified: 111
components export, every appliance resolves to exactly one column, every
function pin to a driver bit, the bit map matches the hand-written
`examples/spcoast_ctc/IO-I2C.h` convention, and ERC is clean.

`import_plant_projects.py` creates a plant project per interlocking holding
only the parts whose identity the legacy sources fix: one `MAIN HOUSE` per
desk column (a column IS a controlled point), every switch and lock AAR-named
from its desk lever and allocated to its column's house, every track circuit
that is not a switch's derived OS circuit, and the maintainer calls. It does
**not** invent the trackplan: topology, masts and heads are left to the
designer. Each sheet carries a FIXME recipe with the legacy ASCII diagram, the
local-to-AAR map, the signal inventory and the legacy route list.

A plant project will not compile until its trackplan is drawn; the plant
compiler needs track anchors and raises `The first anchor must be fixed at
zero` without them. That is expected.

## FIXME markers

| Marker | Meaning |
|---|---|
| `CP Name` = `FIXME` on a desk column | the controlled point's geographic name, recorded nowhere in the legacy sources |
| `MAIN HOUSE` Value = `FIXME CP <n>` | the same name, plant side; each switch's `CP` field already points here, so renaming the house is enough |
| `IndicationToken` = `FIXME <n>T1` | the OS circuit of a switch with no desk lever (a crossover slave) |
| `IndicationToken` = `FIXME TL` / `TR` | traffic lamps, not track circuits; expect `PanelAuxiliary` or a new indication kind |
| `IndicationToken` = `FIXME CP_Other:token` | the lamp shows another interlocking's indication; needs a model and compiler addition |
| Switch Value = `FIXME <local>` | a slaved crossover switch with no lever, so no AAR number |
| Track circuit `CP` = `FIXME` | the legacy sources do not say which controlled point owns a circuit |

## Things the import turned up

- **Expander addresses are computed** as `0x20 + column - 1`, the legacy
  convention baked into `IO-I2C.h`. Verify each against the built hardware.
- **Lever kinds in the legacy XML are suggestions.** It called Luchessa's 795
  a switch when it is a lock.
- **A swapped symbol keeps its old field values.** The drawn Luchessa desk
  sheet has `Kind=SWITCH_LEVER` on a `PanelLock` (795), which the compiler
  reads. Run Update Symbols from Library on that sheet. Both scripts take
  `Role` and `Kind` from the library, never from the template instance.
- **The legacy head list spans several masts.** Head names encode signal,
  direction and head letter, but the ASCII diagrams show, for example,
  Christopher's northbound signal as two masts (`2Nab` and `2Nc`), exactly as
  Luchessa splits 784 into `784EAB` and `784EC`. Mast grouping is not
  derivable from the XML.
- **The library has no three- or four-head mast symbol.** GilroyInterchange
  and Christopher need three heads, Watsonville four. The portable model
  already supports `THREE_HEAD`.
- **Watsonville shares one track circuit across many switches** (`DLT` on six,
  `ALT` on five), a yard ladder. Those switches carry an explicit `TC`.
- **The desk has 15 columns, the machine declares 14.** Column 15 is a
  Watsonville yard custom-code block, not a lever column, and is skipped.

## Traps in writing `.kicad_sch` (all cost a debugging session)

KiCad accepts a malformed sheet **silently**: `kicad-cli` exits 0, prints
nothing, and the netlist simply omits every symbol on that sheet.

- A **literal newline inside a quoted string** breaks the parse. Escape it as
  `\n` (`kicad_sexpr.q` does).
- A **cached `lib_symbols` entry** carries the library nickname on the outer
  name only; inner unit names (`PanelLamp-BLUE_1_1`) stay bare.
- A symbol used by the sheet but **absent from `lib_symbols`** takes the sheet
  down with it, so a symbol the template does not use (here `PanelLamp-BLUE`)
  must be converted in from the library.
- A hand-built `(text_box ...)` is easy to get wrong; a plain `(text ...)`
  is safe.
- A **reference must end in digits**: `SW3B` is an annotation error.
- Reference prefixes must match the library's (`HOUSE`, `SW`, `TC`, `MC`).
- Symbol `instances` paths are `/<root sheet uuid>/<sheet symbol uuid>` for a
  child sheet and `/<sheet uuid>` for a root sheet, and the `project` name
  must match.
- Property `(at ...)` positions are absolute and must be offset with the
  symbol.
- Unused `PanelColumn-MAX7313` bit pins need a `no_connect` or ERC fails;
  `PanelColumn` pins are `free` and do not.
