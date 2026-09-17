# Handoff: KiCad plant-graph spike

Branch: `feature/kicad-plant-graph-parser`

## What this spike is

Read-only harvest from a Railroad KiCad library + interlocking schematic into an
in-memory **Plant Graph** and **structural route equations** suitable for later
dynamic indication evaluation (FieldUnit) and subdivision binding.

It does **not** emit FieldUnit vital payloads, cTc code, or ABS tumble-down.

## How to run

```bash
# Unit + Luchessa integration (paths overridable)
./tools/run_plant_graph_smoke.sh

# Or pieces:
python3 -m unittest tests.test_kicad_plant_graph -q
python3 tools/parse_kicad_plant.py \
  --library "$HOME/Dropbox/KiCad/InterlockingPlant/symbols/Railroad.kicad_sym" \
  --schematic "$HOME/Dropbox/KiCad/Railroad/SPCoast/CP_Luchessa/CP_Luchessa.kicad_sch"
```

Optional name legend:

```bash
python3 tools/parse_kicad_plant.py ... --aliases /path/to/aliases.json
# aliases.json: { "2NAA": "797T", ... }
```

Requires: Python 3.10+, `sexpdata`, local jBOM at `~/Dropbox/KiCad/jBOM/src`
(or installed), and `kicad-cli` for schematic→netlist (or pass `--netlist`).

## Design locks

- Normative domain: FieldUnit `docs/CTC_SUBDIVISION_AND_PLANT_DESIGN.md`
- Spike map: `docs/review/ctc-subdivision-design-layer.md`
- Static enum ≠ dynamic eval. Routes are equations; occupancy/switches solve them later.
- Route ends: `dead_end` | `cp_limit` (DoT stub for next CP) | `next_face` (same direction of travel).
- Faces are direction-sensitive (e.g. industry dwarf ends outbound only).
- **Facing from mast Value grammar** (`784N`/`784S`), not IRJ A/B. A/B are track sides only. Drafting: mast on engineer’s right-hand-seat side of the track; base at IRJ, heads away from the approaching engineer—human sheet rule, not netlist law.
- Clear list = OS `<switch>T1` + labeled path nets. Local vs MP names via aliases later.
- Combinatoric “impossible” pairs are internal proof only, not product.

## Luchessa checkpoint

- 10 structural routes; end kinds: 8 `cp_limit`, 2 `dead_end`.
- Matches historical 10-row table after name map (`2`→`784`, `1/3/5`→`783/795/799`).
- Diagnostics clean on the accepted drawing.
- Eval-ready fields on each route: alignments, clears, heads, end_kind, exit_face_*.

## Code map

| Path | Role |
| --- | --- |
| `tools/kicad_services/` | Library + netlist readers, kicad-cli export |
| `tools/plant_graph/` | Compiler, routes, types |
| `tools/parse_kicad_plant.py` | CLI |
| `tools/run_plant_graph_smoke.sh` | Regression smoke |
| `tests/test_kicad_plant_graph.py` | Seams + next-face fixture |

## Non-goals (do not start on this spike)

- Indication ceilings / cascade / least-restrictive **solver** (but static rows must stay rich enough to feed one)
- Subdivision DoT→neighbor CP binding / ABS tumble-down
- Schematic MP renames / legend authoring as product
- Dual-SIGNAL IRJ symbol library changes (unless a sheet requires it)
- FieldUnit vital payload / cTc compile
- jBOM upstream package publish

## Suggested next owner slices

1. Indication ceiling policy on structural routes (still static ceilings on the table).
2. Subdivision binding of `cp_limit` ends to neighbor entry + corridor ABS.
3. Shared KiCad Python API lift (`TBD-shared-kicad-python-api.md`).
