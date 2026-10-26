# The trackplan piece: `appliances{}` and `track{}`, proposed for schema 3.1.0

Proposed 2026-10-25 (semantics handoff item 2) as a change to ADR 0008 by minor version (C4, C8). The compiler
piece is `tools/layout_compiler/trackplan.py`, the shapes are `$defs/appliance`, `$defs/trackplan`,
`$defs/trackSymbol` and `$defs/portRef` of `schemas/layout-model/v3.1.0.json`, and the scenarios are
`tests/test_trackplan.py`. Nothing in ADR 0008, 0009 or 0010 is edited until the owner settles the points below.

## Decisions requested

1. **What `controlPoint` means outside the limits.** The signals determine membership for the OS circuits, the
   switches and derails in them, and the masts. They do not determine it for approach and yard circuits, for lamps
   (`HBA`, `NFLK`, `SFLK`), or for hand-thrown switches in dark track; there the `CP` field is the only statement
   (77 appliances on SPCoast), and at Luchessa it records which house reports the circuit (1NAT is bounded by a
   Gilroy signal and states Carnadero). Default: `controlPoint` carries the `CP` field there as drawn, and item 6
   (the field's retirement) is limited to what the signals derive. Item 6 can retire the field only where the
   signals cover it; the rest needs a new relation (a wire from the lamp or the circuit to its house) or stays a
   field.
2. **Two-house OS circuits.** Christopher's 815A and Luchessa's 783 lie in circuits whose signal joints name two
   houses. Default: the `CP` field decides, and the compiler reports `control_point.shared` at info.
3. **The `A` pin of `IRJ-Signal` is the side inside the limits.** True of all 35 signal joints on SPCoast, stated
   nowhere. Default: record it in the library's description of the symbol and in ADR 0009 §3.10. The compiler
   reports `joint.inside` at info for a joint with no switch on its `A` side.
4. **An appliance pin on a track net.** Sargent's `HBA` (AUXILIARY) has its `MC` pin on 1SAT's net. Default: not
   written, reported at info (`appliance.on_track`); the owner says whether the hot box detector stands on 1SAT
   (then it is a fact to carry) or the pin touches the line by accident.

## The shapes

Per interlocking, beside `houses` and `devices`:

```
appliances{Name}: appliance (switch | mast | track_circuit | lamp | contact), style, controlPoint,
                  osCircuit (switch: its TC), indicationCeiling, heads{letter: {style}} (mast),
                  members[] (virtual circuit: its IndicationToken), settings
track: joints[]   IRJ, IRJ_SIGNAL: kind, circuits{pin}, ports{pin: [port]}, mast, controlPoint (signal joint)
       ends[]     END_CTC, NEXT_CP, BUMPER, INDUSTRY: kind, circuits{pin}, ports{pin}
       policies[] RULE_105, RULE_251, RULE_261, RULE_93: kind, circuits{pin}, direction
       links[]    switch ports that meet with no symbol between: ports[], circuit
       mileposts[] the anchors' names
```

Sargent's east signal joint, as written:

```json
{"kind": "IRJ_SIGNAL", "circuits": {"A": "Sargent:835T1", "B": "Sargent:1NAT"},
 "ports": {"A": ["Sargent:835.C"]}, "mast": "Sargent:836NAB", "controlPoint": "Sargent:Sargent"}
```

Its geometry marker has the same `kind` and the same `circuits`. That is the join ADR 0010 C6 asks for, so
`markers[]` needs no key. `ports` is what the route finder needs where a joint touches a switch port with no run
between them (all of Sargent). It names the port with geometry's `to:` vocabulary.

How the shapes were chosen:

- **A circuit** is the nets joined through a switch's ports (C to N, C to R) and a derail's (C to R), split at every
  joint and end. It is named by the track circuit marker on it, or else by a switch's `TC`. Two names on one circuit
  are an error. Neither name means dark track. One `circuit_of_net` serves both pieces, so geometry now writes
  `835T1` on Sargent's three signal joints and on Luchessa's three port runs (handoff finding b).
- **Membership** follows the relation-table pattern. Explicit: the signal joints of one control point on the
  circuit's `A` sides, the joint under a mast's `SIGNAL` pin, the house on a maintainer call's `MC` net. Fallback:
  the appliance's `CP` field. Both present and different is an error. A signal joint's own `CP` is the stated fact,
  with the interlocking's one house as its fallback. Every `CP` must name a house of its interlocking.
- **Left out, because a reader derives them:** a switch's gang and a derail's dependence (ADR 0003 D8, from the
  names), signals, routes, limits and OS logic (the view §6), and a NextCP's destination (its circuit's interlocking
  prefix says it where it is a reference). A reference drawn here (`Corporal:2NAT` at Sargent) names track, but it
  is not an appliance of this interlocking, so geometry places it and `appliances` does not hold it.
- **Rows have no identity** (ADR 0008 §4.5). Every list is sorted (§4.8). A port is `<interlocking>:<switch>.<C|N|R>`.

## Relation table rows (for ADR 0009 §3.12, after the decisions)

| Relation | Explicit | Implicit fallback | Check |
|---|---|---|---|
| Signal joint's control point | `CP` on the IRJ-Signal | the interlocking's one house | names a house |
| Mast's control point | `SIGNAL` wire to an IRJ-Signal | none | one joint per mast |
| Appliance's control point | its circuit's signal joints, all of one control point | the appliance's `CP` field | agree; names a house |
| Maintainer call's house | `MC` wire to a House | none | |
| Circuit of a track net | the track circuit marker on the circuit | a switch's `TC` (its OS circuit) | one name per circuit |
| Trackplan head to its mast | `M` wire to a mast's `H` pin | none | one letter per mast |

## On SPCoast (Railroad `a3642e4`)

- No error except one, found by this piece. Watsonville drew two masts named `838NAB` (signal 838N on 837's N and R
  legs). The geometry reader had been silently writing one over the other. The owner renamed one `838NCD` on
  2026-10-25. Its heads are still lettered A and B.
- No circuit carries two names. No derived membership disagrees with a `CP` field. `control_point.shared` is
  reported twice (783, 815A). 41 memberships come from the wire only (masts, maintainer calls), and 77 from the
  field only (decision 1).
