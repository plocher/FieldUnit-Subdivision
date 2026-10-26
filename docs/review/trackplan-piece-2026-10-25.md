# The trackplan piece: `appliances{}` and `track{}`, proposed for schema 3.1.0

Proposed 2026-10-25 (semantics handoff item 2) as a change to ADR 0008 by minor version (C4, C8). The compiler
piece is `tools/layout_compiler/trackplan.py`, the shapes are `$defs/appliance`, `$defs/trackplan`,
`$defs/trackSymbol` and `$defs/portRef` of `schemas/layout-model/v3.1.0.json`, and the scenarios are
`tests/test_trackplan.py`. Nothing in ADR 0008, 0009 or 0010 is edited until the owner settles the points below.

## The owner's rulings (2026-10-25)

- Decision 1, membership outside the limits: **signals protect routes through an interlocking. Yard, dark and
  industry track is outside interlocking protection by definition. Approach blocks and the track between
  interlockings are TBD, for when the ABS and APB rules are added.** The compiler now writes `controlPoint` on a
  switch or a circuit only where signals protect it. On unprotected track the `CP` field is not written, and the
  compiler reports it at info (`control_point.unprotected`). A lamp keeps its field, because signals say nothing
  about lamps.
- Decision 3: **the `A` pin is "the 'protected by a signal' beginning of a route"**. It is recorded in the
  compiler, in the schema's description of `joints`, and in ADR 0009 §3.10 when rev 3 is applied.
- Decision 4: **HBA is not on 1SAT.** A hot box alarm is not a track circuit. It is associated with a milepost and
  the timetable, so crews know where it is and which train is being checked. Its `MC` pin touching 1SAT's net is a
  drawing slip for the owner. Until then the compiler reports it at info and writes nothing.
- The notation `interlocking:token` (`Corporal:2NAT` at Sargent) names a code line indication token from that
  interlocking. It is a placeholder for the ABS/APB work. The compiler names track by it and writes no appliance
  for it.
- Decision 2, the two-house circuits (783, 815A), is still open. The `CP` field decides there until the owner
  rules.

## After the adversarial review (`trackplan-piece-review-2026-10-25.md`, 17 findings)

Applied (`c9c3a5d`, `e53f236`):

- Protection crosses plain joints between switch circuits. A circuit with no switch that lies between two of them
  joins their group. Christopher's 815, Watsonville's ladder 15 to 25 and the circuits between them are inside.
  The yard tracks off the ladder are outside (finding 5).
- `osCircuit` is the circuit the switch's track carries. A switch with no track writes none and is reported
  (findings 9, 10).
- New errors: a signal joint turned around, a joint with one circuit on both sides, END CTC turned around, two
  masts on one joint, and ADR 0003 rules 6 and 7 for mast names and head letters (findings 7, 9, 11).
- Geometry takes its symbols by the same nearest-interlocking rule (finding 16). Scenarios read diagnostics as
  (code, symbol) tables (finding 13). `portRef` has the name rule of `qualifiedName` (finding 14).
- Counts are corrected below.

### Still open, for the owner

1. **A NextCP's destination (blocker, finding 1).** All 18 NextCPs state it, but only in `Value`, which is never
   read. A circuit prefix recovers it for one of them. ADR 0010 §4.7 promises it in `track`. Default: a key
   attribute on `NextCP` in the library and on its instances (a functional name, for example `To` or `Next`, with
   content `${Value}`, by a dated script). The compiler then writes it on the end row and checks it in pairs. A
   destination off the layout (`Lick`, `Hollister`) is reported at info. While reading this, the review found
   that Christopher's two NextCPs both say `Sargent`, yet Corporal lies between them.
2. **The geometry join (blocker, finding 2).** At Corporal and Sargent, two `INDUSTRY` rows have the same kind and
   circuits. They differ only by `ports`, which geometry markers do not carry. Default: geometry markers carry the
   same `ports` map, by an amendment to ADR 0010 (C6, the fragment is ratified), plus a gate that every marker
   joins exactly one `track` row.
3. **Dark-track adjacency (finding 3).** At Luchessa, END CTC's `DARK` pin meets the Industry on one net, and
   nothing records the meeting. An open pin and a pin on dark track look alike. Options: (a) report an open track
   pin as missing, and write which ends meet on dark track; (b) name these symbols (the alternative in C6).
   Default: (a).
4. **Two control points' signals on one circuit (findings 6 and 8).** The `CP` field decides, at info, pending a
   ruling. Christopher 815, 815A and 01T bound by North and South, field North. Gilroy Interchange 02T bound by
   North and South. Luchessa 783 bound by Luchessa (joint B7001) and Gilroy (B7003), field Luchessa. Luchessa 01T
   bound by all three houses, field Gilroy.
5. **ADR 0003 rule 8 crossovers (finding 4).** One circuit with two generated OS names, such as 815T1 and 815AT1
   with no joint between them, is an error today. Rule 8 names such a circuit. Default: apply rule 8 (a switch
   before a derail, then the lowest number) when every name in the circuit has the generated form, and report an
   error only when a drawn marker disagrees. This doesn't arise on SPCoast.
6. **The glossary (finding 6).** It says "the `CP` field of an appliance assigns it to a control point". The owner's
   ruling makes the signals assign it for track. Default: a glossary delta.
7. **What is written twice (finding 10).** A mast's `controlPoint` equals its joint's. `track.mileposts` equals
   geometry's keys. Default: keep both, the first as a relation the compiler resolves (like `fieldUnit.processor`)
   and the second because geometry is optional.
8. **A detection block in `TC` (finding 12).** ADR 0003 rule 8 and ADR 0002 D16 make a TC that lists several circuits
   legal. Schema 3.1.0 has no form for it, so the compiler refuses to write. None is drawn.
9. **`AGENTS.md` (finding 15).** It says the OS circuit "defaults to `<switch>T1`; a `TC` field overrides it". The
   library's TC default does that, and the compiler applies no default of its own. Default: correct the sentence.

Not done, and tracked here: checking a virtual circuit's members and a reference's appliance, Corporal:2NAT's
Rule 261 drawn at both Sargent and Corporal, a gate that the example equals a fresh compile, and the schema nits of
finding 14 (style as a string where devices write a list, Kind not constrained per list, no `propertyNames`, no
`settings` on a track symbol).

## Decisions requested (as proposed)

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

## On SPCoast (Railroad `27496ce`, the owner's export of 2026-10-25 22:30)

- No error. The one error this piece found at `a3642e4` is fixed: Watsonville drew two masts named `838NAB`
  (signal 838N on 837's N and R legs), and the geometry reader had been silently writing one over the other. The
  owner renamed the second mast `838NCD` and relettered its heads C and D (Railroad `7ecb9d9`).
- No circuit carries two names. No membership the signals give disagrees with a `CP` field.
  `control_point.shared` is reported six times (open decision 4). Membership after the rulings:
  - 35 masts and 7 maintainer calls by wire;
  - every switch and circuit inside the limits by its signals;
  - the shared cases and the lamps by their `CP` field;
  - 60 `CP` fields on unprotected track not written.
