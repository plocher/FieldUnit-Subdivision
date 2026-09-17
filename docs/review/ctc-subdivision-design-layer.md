# CTC / Subdivision design layer (KiCad plant-graph spike)

Working design lock for `feature/kicad-plant-graph-parser` and follow-on plant harvest work.

This note is **Subdivision-local**: what the spike implements, what Luchessa proved, and what comes next. It does not replace the FieldUnit design layer.

## Related documents

| Document | Role |
| --- | --- |
| FieldUnit `docs/CTC_SUBDIVISION_AND_PLANT_DESIGN.md` (Arduino/libraries/FieldUnit) | Normative design layer: GCOR CTC frame, static vs dynamic clocks, faces, route ends, DoT placeholders, ABS/tumble-down, naming, indication solve sketch |
| FieldUnit `docs/AAR_SIGNALING_PRIMER.md` | Bungalow / vital logic (HR, DR, locking, CodeLine) |
| `docs/review/kicad-as-plant-design-editor.pdf` | Spike motivation: schematic as plant design editor |
| `docs/review/TBD-shared-kicad-python-api.md` | Later lift of `tools/kicad_services/` toward jBOM / shared KiCad API |

If this note and the FieldUnit CTC document disagree, **prefer the FieldUnit document** for domain rules, then fix this note.

## Purpose

Answer, for Subdivision tooling:

1. How structural routes are harvested from a KiCad plant schematic.  
2. What is product output vs internal proof.  
3. What is deliberately out of scope until a later slice.  
4. How CP-local harvest binds later to subdivision corridors without rewriting the plant enum.

FieldUnit remains the authority for **execution safety**.  
Schematic harvest remains the authority for **which static route equations exist**.

## Two clocks (do not mix)

### Static enumeration (design / harvest time)

**Inputs:** library pin contracts, netlist connectivity, Railroad symbol kinds, labeled nets.  
**Output:** structural routes per signal face (lined switch combinations, clear-track lists, ends).

A structural route does not know live occupancy. It states only the geometry equation for that face.

### Dynamic evaluation (run time)

**Inputs:** switch correspondence, track-circuit occupancy, opposing locks, downstream face state, dispatcher products.  
**Output:** indication each mast may show **now**.

FieldUnit (and later subdivision corridor logic) **solves** the equations. Harvest **writes** them.

Rejected conflations:

- Empty walk under one full switch plant ≠ “this mast is always Stop.”  
- Occupied clear-list TC or switch lined against a matched route ⇒ run-time Stop / non-match.  
- Routes that end inside the plant (industry stub) may still have non-Stop ceilings when the equation is satisfied.

## Signal faces

A **signal face** is one directional protecting unit: typically one mast (or head set) on a **Signal IRJ**, facing one direction of travel.

- Faces are **direction-sensitive**.  
  Example: Luchessa `784SC` protects moves **out of** Gilroy Industry only. It does **not** end routes that are **entering** the industry.  
- One Signal IRJ may carry **two** faces (back-to-back bi-di main, crossover hold). Luchessa often uses one face per Signal IRJ; the contract must allow two.  
- Mast Value carries the proper name (`784NAB`); Head Values are letters; Signal identity is the even number (`784`). Technical KiCad References stay editor IDs.

### Facing authority (mast Value, not IRJ pins)

**Facing / direction of travel for a face comes from the mast Value grammar** (`784N…` / `784S…`), not from IRJ track pin names and not from symbol rotation.

| Concern | Authority |
| --- | --- |
| Track sides of the joint | IRJ pins **A** and **B** only (geometry) |
| Where the mast attaches | **SIGNAL** pin(s) on IRJ-Signal / future dual-SIGNAL IRJ |
| Which way the face protects | **Mast Value** direction letter (N/S), DRY across copies |
| Approach vs plant track side | Topology inference (DoT/bumper vs switch) or rare instance override—not a global A→B law |

Do **not** rename A/B to IN/OUT or FRONT/BACK. Dual-face joints and mirrored symbols make those names lie.

Future two-signal IRJ: keep A/B for track; add two SIGNAL attachments (e.g. SIGNAL_N / SIGNAL_S or two SIGNAL pins each bound to a mast whose Value carries facing).

### Drafting rule (human sheet, not netlist law)

Place the mast on the side of the track where the engineer in the **right-hand seat** will see it. Mast base at the IRJ; mast/heads extend **away** from the approaching engineer’s viewpoint. That is drawing discipline for legibility. The compiler must not require coordinates to recover facing—Value grammar remains the machine-readable facing source.

## Structural route shape

### Start

The face that protects movement from its approach onto plant geometry—commonly protecting the first switch **C** in the move, or the absolute face at the CP limit for that approach.

### End

End at the **next protection in the direction of travel**, or at a **dead end**:

| End kind | Meaning | Spike status |
| --- | --- | --- |
| Next same-direction signal face | Opens a new route set ahead; this face’s structural routes cover steel only up to that face | Implemented (same mast-Value direction; end at other face **approach** pin) |
| Dead end | Bumper, stub, industry end with no further same-direction protecting face | Implemented (bumper terminal) |
| CP-limit placeholder | DoT + named exit net standing in for the **next CP entry signal** and ABS chain toward it | Implemented as DoT terminal |

Chain **2 → 4 → 6** in one direction of travel:

- Structural routes for **2** cover steel **only to 4**.  
- Structural routes for **4** cover steel **only to 6**.  
- Indication on 2 accounts for 4 (and 4 for 6) through evaluation cascade (distant / advance), not one static route from 2 through 6.

### Identity fields (product table)

Scannable line shape:

```text
route-name   mast   switch-alignment   signal(lever)   clear-TCs   [indication ceiling]
```

Example (Luchessa harvest):

```text
MT-Hollister Branch   784SAB   (783)795(799)   784S(RIGHT)   783T1 795T1 799T1 1SA 2NAA 3NA   —
```

Conventions:

- Alignment: bare name = Normal; `(name)` = Reverse.  
- Lever: mast geographic face → office Left/Right for this desk (`N`→LEFT, `S`→RIGHT on Luchessa-style harvest; document per machine if different).  
- Clear list: derived OS `<switch>T1` plus **labeled path nets** on the route.  
- Indication ceiling: design-time max when the equation is fully satisfied; run time may be stricter. Spike still prints `—` until policy is wired.

Combinatoric exploration of all switch plants is an **internal completeness proof** only. Impossible entry/exit pairs are not product tables. CLI warns only if harvest and proof disagree.

## KiCad drawing rules used by the spike

### Appliances

- **Switch:** C/N/R pins 1/2/3; never short C/N/R; OS name `<SwitchName>T1`.  
- **IRJ / IRJ-Signal:** A/B track; Signal IRJ adds SIGNAL. Joint is crossable for movement; circuits stay separate.  
- **Mast / Head:** SIGNAL to Signal IRJ; heads only on mast head pins.  
- **DoT:** CP-local **limit terminal** (one live track pin; other intentional NC). Value = designation; Rulebook = 251/261/…. Not an interior series edge for ordinary CP design.  
- **Bumper:** dead-end terminal.

### Net classes (harvest)

| Class | Role | Needs user label? |
| --- | --- | --- |
| `track` | Path nets between non-switch track ports | Yes |
| `switch_os` | Nets touching switch C/N/R | No (covered by `<sw>T1`) |
| `signal_attachment` | IRJ SIGNAL ↔ mast SIGNAL | No |
| `head_attachment` | Mast head ↔ head | No |
| `unconnected` | NC / dangling | No |

### Names (two layers, one drawing)

| Pattern | Use | Examples |
| --- | --- | --- |
| Milepost / system | Mainline switches, signals, corridor identity | `783`, `784`, later `780SA` |
| Plant-local | Internal nets/circuits | `1SA`, `2NA`, `2NAA` |

- Graph identity = strings as drawn.  
- Optional **alias / legend** (local → MP) later; do not require MP on every net for parse.  
- Historical ordinal tables (`1/3/5`, signal `2`) are migration evidence only.

## Between CPs: DoT as placeholder

On a single-plant sheet, DoT + named exit (e.g. Hollister Branch) is:

1. Operating designation + rulebook at that limit, and  
2. A **stub** for the next CP’s entry signal and the ABS chain on single track between CPs.

Subdivision binding later resolves the stub. ABS tumble-down (opposing intermediates red when the corridor is claimed; following still occupancy-based) is **territory evaluation**, not more rows in one CP’s switch enum.

Do not remove CP-local DoT ends because “the real end is Hollister.” Keep both scopes.

## Indication solve (eval sketch only)

When several structural routes could apply to one face under current plant:

1. Keep routes whose switch alignments match verified correspondence.  
2. Per route: most restrictive result from clears, locks, policy ceiling, **downstream face indication**.  
3. Face shows the **least restrictive** among those results, or Stop if none survive.

Not implemented in the spike CLI beyond the empty indication column.

## Spike implementation map

| Path | Responsibility |
| --- | --- |
| `tools/kicad_services/` | Generic KiCad reads: symbol library, netlist parse, kicad-cli export |
| `tools/plant_graph/compiler.py` | Railroad typing, net class, diagnostics, OS derive, invoke route harvest |
| `tools/plant_graph/routes.py` | Terminals, faces, structural route walk, presentation helpers, internal proof |
| `tools/plant_graph/types.py` | Plant graph domain types |
| `tools/parse_kicad_plant.py` | Read-only CLI inventory + route table |
| `tests/test_kicad_plant_graph.py` | Seam tests + minimal route fixture |

### Luchessa checkpoint (this branch)

- Library + schematic → clean diagnostics for the accepted drawing.  
- **10** structural routes; matches historical 10-row table after name map (`2`→`784`, `1/3/5`→`783/795/799`, mast `2SAB`→`784SAB`, …).  
- FieldUnit v1 `routes` in profile JSON remain a **lossy** ordinal projection, not the full design table.  
- Ends: **DoT (`cp_limit`)**, **bumper (`dead_end`)**, **next same-direction face (`next_face`)** via mast Value direction + approach-pin end. Luchessa: 8 limit + 2 dead-end.  
- Eval-ready route fields: alignments, clears, head letters, end_kind, exit_face_*.  
- Optional `--aliases` JSON for local→display/MP names (identity stays as drawn).

## Gaps / next owner slices (after this spike)

1. **Indication ceiling** policy (head grammar + clear/cascade hooks); static rows already carry the inputs.  
2. **Subdivision binding** of DoT ends to neighbor entry + ABS tumble-down.  
3. **Dual SIGNAL ports** on one IRJ when a real sheet needs it (facing still from mast Value).  
4. **Shared KiCad Python API** lift (`TBD-shared-kicad-python-api.md`).  
5. Approach-side **instance override** if topology inference is ever ambiguous (no A/B rename).

## Author checklist (single CP)

1. Switches with C/N/R; OS names derived; no list-index identity.  
2. IRJs / Signal IRJs; masts on SIGNAL only; face direction honest.  
3. Enumerate structural routes: face → next same-direction face | dead end | CP-limit DoT.  
4. Clear lists = OS + path labels as drawn.  
5. DoT designation + rulebook at limits; treat as neighbor placeholders.  
6. Local vs MP names; legend if both appear.  
7. Hand equations to FieldUnit-style evaluation; do not bake live occupancy into the drawing.

## Summary

- **Write routes as static equations; solve indications at run time.**  
- **End at next same-direction protection, dead end, or CP-limit DoT stub.**  
- **Faces are direction-sensitive; industry dwarfs do not end inbound moves.**  
- **DoT on a plant sheet is limit policy + next-CP placeholder—not interior topology and not the whole subdivision graph.**  
- **This spike harvests CP-local equations from KiCad; FieldUnit executes plant vital truth; subdivision later binds limits and ABS.**
