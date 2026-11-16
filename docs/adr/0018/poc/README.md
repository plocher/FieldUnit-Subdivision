# ADR 0018 spike: a train order face symbol with per-object JMRI addresses

Three throwaway schematics. Each has one embedded symbol `Spike:TOFace`, named `Gilroy.E`, with an
`IOBus` pin and three fields `Address.MAST`, `Address.STOP`, `Address.SLOW`. Open each `spike.kicad_sch`
in KiCad 10 to see how it looks and feels. Regenerate with `python3 make.py <variant> > <variant>/spike.kicad_sch`.

| Variant | Units | Pins |
|---|---|---|
| `pinless` | A MAST, B STOP, C SLOW | `IOBus` on A only |
| `pinned` | A MAST, B STOP, C SLOW | `IOBus` on A; `STOP` on B and `SLOW` on C, each with a no-connect flag |
| `single` | one | `IOBus`; all three Address fields shown on it |

In the multi-unit variants each unit has a value only in its own field: A has `Address.MAST` 101, B has
`Address.STOP` 202, C has `Address.SLOW` 303.

What `kicad-cli` 10.0.1 does (2026-11-15):

- **A unit with no pins is accepted.** ERC reports nothing about B or C (the 5 warnings are the spike's
  own: library not in the table, off-grid ends, the lone label). The units place and print as `TOF1B`, `TOF1C`.
- **The netlist has one component for `TOF1`, not one per unit, and one value for each field.** Its
  `fields` list took `Address.MAST` 101 from unit A; its `property` list took `Address.STOP` 202 from
  unit B; `Address.SLOW` 303 from unit C is in neither. A value set on only one unit can be lost.
- The `.kicad_sch` keeps each unit's own fields, so a reader of the sheet sees all three.
