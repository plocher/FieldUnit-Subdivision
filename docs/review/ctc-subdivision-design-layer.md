# CTC / Subdivision design layer

Working understanding from the KiCad plant-graph spike and related design talk.

**Normative companion (FieldUnit book material):**  
[`FieldUnit/docs/CTC_SUBDIVISION_AND_PLANT_DESIGN.md`](../../../../Arduino/libraries/FieldUnit/docs/CTC_SUBDIVISION_AND_PLANT_DESIGN.md)

**Bungalow / vital primer:**  
[`FieldUnit/docs/AAR_SIGNALING_PRIMER.md`](../../../../Arduino/libraries/FieldUnit/docs/AAR_SIGNALING_PRIMER.md)

## Spike status (this branch)

- Read-only KiCad library + netlist → plant inventory and **structural routes** (static equations).  
- Route table line: mast, switch alignment, lever face, clear TCs (OS + path nets).  
- Combinatorics stay **internal completeness** only.  
- Indication solve, next-face ends beyond DoT/bumper, subdivision tumble-down binding, and name aliases are **not** finished product on this branch.

## Design rules locked for authors

1. Static route enum ≠ dynamic indication eval.  
2. Signal faces are direction-sensitive.  
3. Structural route ends at next same-direction protection, dead end, or CP-limit DoT (placeholder for next CP / ABS).  
4. Local net names and MP appliance names may coexist; alias layer later.  
5. GCOR CTC chapters frame authority; FieldUnit executes plant vital truth.
