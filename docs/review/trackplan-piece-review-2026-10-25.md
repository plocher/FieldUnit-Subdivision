# Adversarial review: the trackplan piece (`appliances{}`, `track{}`, schema 3.1.0)

Reviewed 2026-10-25 on `feat/trackplan-semantics` (`12e8d76` plus the uncommitted proposal edit): the proposal
`docs/review/trackplan-piece-2026-10-25.md`, `tools/layout_compiler/trackplan.py` and its use in `geometry.py`,
`seams.resolve` and `emit.py`, `$defs` appliance / trackplan / trackSymbol / portRef of
`schemas/layout-model/v3.1.0.json`, `tests/test_trackplan.py`, and `schemas/layout-model/examples/spcoast.layout.json`.
I checked the claims against the sources of truth, not against the proposal's reasoning: ADR 0003, 0008, 0009 and 0010, the
FieldUnit glossary, `AGENTS.md`, the handoff item 2, the view, and `Railroad-Trackplan.kicad_sym`, which I read directly.
I read the drawing only through `from_netlist` on `~/Dropbox/KiCad/Railroad/SPCoast/production/SPCoast.net`, and checked
plausible drawings by running the scenario harness of `tests/test_trackplan.py` in memory. I edited no file except this
one. 220 tests pass with `SPCOAST_NETLIST` set.

**Source freshness.** At the start of the review the netlist was dated 22:25. Three sheets (`Corporal`, `South-cTc`,
`SPCoast`) had a 22:30 mtime, and `South-cTc.kicad_sch` had an uncommitted Railroad edit (IC `CMRInet` changed to `CMRI`).
During the review the owner re-exported the netlist (22:30:52), so it is now newer than every sheet (latest 22:30:35)
and than the library (20:32). Compiled from the new export, the example differs from the committed one in that one IC
value only. Every trackplan fact is identical. The proposal and the handoff still cite the 22:25 export.

## Findings

1. **Blocker. Claim attacked: "Left out, because a reader derives them: … a NextCP's destination (its circuit's
   interlocking prefix says it where it is a reference)."**
   *Evidence.* The drawing states the destination of every one of the 18 NextCPs, but it states it in `Value`:
   - Christopher CP9001/CP9002 `Sargent`, CP9003/CP9004 `Luchessa`
   - Corporal `Sargent`, `Christopher`, `Christopher`
   - Gilroy Caltrain `Lick`, `Gilroy Interchange`
   - Gilroy Interchange `Gilroy Caltrain`, `Luchessa`
   - Luchessa `Gilroy Interchange`, `Hollister`, `Christopher` ×2
   - Sargent `Corporal`, `Watsonville`
   - Watsonville `Sargent`

   Only one of the 18 (Sargent CP1, on `Corporal:2NAT`) is recoverable from a circuit prefix. No track net spans two
   interlockings (I checked every net). The library symbol `NextCP` says it "Identifies the next control point on this
   track", but it has no field except `Value`. ADR 0010 §4.7 says "`track` will carry each NextCP's destination", and the
   reader orders the subdivision by "join[ing] them end to end at their NextCP runs". The view §3.1 lists "the two NextCP
   references (Corporal, Watsonville)" as stated facts. As written, the subdivision strip and the cross-interlocking route
   join cannot be built from the file.

   Reading the destination would also have caught a likely drawing error. Christopher's two `Sargent` NextCPs contradict
   Sargent's own pair (`Corporal`, `Watsonville`) and Corporal's pair (`Christopher` ×2). Corporal lies between them.

   *Fix.* Give `NextCP` a key field, `Name = ${Value}` (or a functional name such as `To`), as was done for appliances and
   mileposts. Write it on the end row as a layout name. Check it in pairs: if A names B, then B has a NextCP naming A.
   A name that is not an interlocking (`Lick`, `Hollister`) is reported at info as off-layout.

2. **Blocker. Claim attacked: "Its geometry marker has the same `kind` and the same `circuits`. That is the join ADR
   0010 C6 asks for, so `markers[]` needs no key."**
   *Evidence.* In the example, Corporal and Sargent each have two `INDUSTRY` rows whose kind and circuits are identical.
   Both are `{"kind": "INDUSTRY"}` in `track.ends` and in `geometry.markers`. The `track` rows differ only by `ports`
   (`Corporal:1.N` against `Corporal:1.R`, and likewise at Sargent), and geometry markers carry no `ports`. So a view
   cannot tell which glyph is which leg's Industry. ADR 0010 §4.5 itself names the collision case ("a loop that rejoins
   one circuit twice collides"). A passing siding with joints at both ends against the same two circuits would collide
   the same way.

   *Fix.* Write the same `ports` map on geometry markers. It is a netlist fact, just as `circuits` is. Add a gate test
   that every marker joins exactly one `track` row and every row joins exactly one marker. If that is not enough, take
   C6's alternative and name these symbols.

3. **Should-fix. Claim attacked: the track shape is lossless for route finding.**
   *Evidence.*
   - At Luchessa, END_CTC B11008's `DARK` pin and Industry B7010's `EoT` pin share one net (`Net-(B11008-DARK)`). The file
     writes `{"kind":"END_CTC","circuits":{"CTC":"Luchessa:02T"}}` and `{"kind":"INDUSTRY"}`, and the fact that they meet
     is gone. I reproduced this in memory: two track symbols that meet on dark track with no switch port between them
     leave no trace.
   - An open pin and a pin on dark track look the same (both are simply absent from `circuits` and `ports`).
   - `links` covers only switch ports that meet. A switch port alone on its net is dropped silently.

   Rows have no identity, so one row cannot reference another, and dark track has no name. That is a model gap, not a
   coding slip.

   *Fix.* This is a decision for the owner, not a default. Options:
   - (a) dark track between two non-switch track symbols must carry a marker, else it is reported missing;
   - (b) the dark-track meetings are written as rows of the pins that meet, which needs identity;
   - (c) C6's named-symbol alternative.

   At minimum, report an open track pin as missing.

4. **Should-fix. Claim attacked: "Two names on one circuit are an error."**
   *Evidence.* ADR 0003 rule 8 covers this case: "When one circuit holds several switches and its name is generated, it
   takes the number of a movable-point frog first, then a switch, then a derail; among equals, the lowest number." The
   library generates `TC = ${VALUE}T1` on Switch_Lock, Switch_Powered*, Switch_Dual and Derail_TC.

   I compiled a crossover in memory: `815` (TC 815T1) and `815A` (TC 815AT1) linked R to R with no joint between. It
   gives `circuit.names` ("a joint is missing or a TC is wrong") for a drawing rule 8 calls legal. A `Derail_TC` inside
   its switch's circuit hits the same error. Neither case occurs on SPCoast: Christopher's 815 and 815A have an IRJ
   between them.

   *Fix.* When every name in a circuit is in the generated `<name>T1` form, apply rule 8. Report an error only when a
   drawn marker or a hand-edited TC disagrees. Add a scenario for each.

5. **Should-fix. Claim attacked (decision 1 and the handoff status): "The signals determine membership for the OS
   circuits, the switches and derails in them."**
   *Evidence.* Signals do not determine five of Watsonville's OS switches (17, 19, 21, 23, 25) or Christopher's `815`.
   Their circuits are bounded only by plain IRJs between neighbouring OS circuits (`815T1` between `813T1`, `815AT1` and
   `817T1`; `15T1`…`25T1` chained by `IRJ_Diag`). The compile reports `appliance.control_point.implicit_only` for 10
   switches: those six, 783 and 815A (shared), and the two hand-thrown `1`s.

   So the derivation covers 22 switches and derails, 35 masts and 7 maintainer calls, and nothing else. Every one of the
   62 track circuits comes from the field. The proposal also says "41 memberships come from the wire only"; the compile
   gives 42 (35 masts and 7 maintainer calls).

   *Fix.* Either carry membership across a plain IRJ between two circuits that are both OS-named (each holds a switch),
   or correct decision 1 so the owner rules on the true scope. Correct the count either way.

6. **Should-fix. Claim attacked: the relation-table rows, where "Explicit: the signal joints of one control point on
   the circuit's `A` sides", and the decision 1 default.**
   *Evidence.*
   - In ADR 0009 §3.12, "explicit" is always a wire. Here it is the joint's `CP` field (a field) carried over topology:
     two hops, no wire to the appliance. The table's first row likewise puts a field ("`CP` on the IRJ-Signal") in the
     Explicit column. Retiring the appliance `CP` field (item 6) replaces one field with another field plus an inference.
   - The glossary (`GLOSSARY.md`, "control point", FieldUnit sub-bullet) says "The `CP` field of an appliance assigns it
     to a control point". The view §4.2 calls `controlPoint` "membership, not a boundary". Both outrank the handoff's
     "derived … never stated per appliance".

   Decision 1 does not mention this conflict. It is the real decision.

   *Fix.* Relabel the rows (stated field against inferred check), cite the glossary and the view, and put the conflict
   to the owner. Two options:
   - (a) the field stays the statement and the signals become its check (this matches the glossary);
   - (b) the glossary changes and the field retires where the inference covers it.

7. **Should-fix. Claim attacked: the `A` pin is the inside on all 35 joints (decision 3), and `joint.inside` guards the
   convention.**
   *Evidence.* On SPCoast the convention holds. I checked every one: all 35 `A` sides are TC-named OS circuits, and no `B`
   side holds a switch. The check is weak, though:
   - It looks only for a switch on `A` (`trackplan.py` l.192). A joint with switches on both sides passes.
   - In memory I swapped J1's A and B in `ONE_SWITCH`. The result was one info. The derivation silently moved to the
     approach circuit (`1NAT` came out "derived") and away from switch 835 (which fell back to its field). With one house
     nothing disagrees, so nothing surfaces.
   - The glossary says "A control point can have no switch". A signal-only control point therefore draws a false
     `joint.inside`.

   *Fix.* Check that `A` is the side whose circuit holds a switch or is OS-named, and that `B` is not. When they
   contradict, report it. Also record the convention in the library description, as decision 3 proposes.

8. **Should-fix. Claim attacked: decision 2, "Two-house OS circuits … the `CP` field decides … info."**
   *Evidence.*
   - At Luchessa, the joint with `CP=Gilroy` has `A=783T1` and `B=1NAT`. The switch `783` states `CP=Luchessa`, and `1NAT`
     states `Carnadero`. Decision 1's example (1NAT) and decision 2's case (783) are the same joint, but the proposal
     presents them separately.
   - At Christopher, `815AT1` is entered by a South joint (`B=2NAT`) and a North joint (`B=2SAT`), while `815A` states
     North.

   These cases could be prototypical: in a 506 station split, the house is the code station, not the signals' owner. Or
   they could be drawing errors. Reporting them at info treats them as settled.

   *Fix.* Present both cases to the owner with the joint, the switch and the approach circuit side by side. Until the
   owner rules, report at a level the drawing gate shows. The default of letting the field decide is fine once the owner
   confirms the arrangement is real.

9. **Should-fix. Claim attacked: "errors are fact inconsistencies"; the piece reports the inconsistencies it can see.**
   *Evidence.* Each of these I either reproduced in memory or read off the code:
   - A switch with no port nets: no report, yet `osCircuit: X:9T1` is written for a circuit no track carries (l.146
     skips naming; l.232 still writes `osCircuit`).
   - A joint whose `A` and `B` lie on one circuit: no report. (The circuit loops around the joint, so a joint elsewhere is
     missing.)
   - `END_CTC` with a circuit on `DARK`, or with dark track on `CTC`: no report.
   - A signal joint with two masts on its `SIGNAL` net: the joint's `mast` is silently dropped (l.268), and each mast
     still finds one joint.
   - A virtual circuit's `members` are not checked against this interlocking's circuits.
   - A reference such as `Corporal:2NAT` is not checked to name an appliance of Corporal, and its `CP` field is skipped
     unchecked (l.212).
   - Sargent and Corporal both draw a `RULE_261 BOTH` on `Corporal:2NAT`, so one sign is written twice with no
     agreement check.

   *Fix.* Add each one as a check, with a scenario.

10. **Should-fix. Claim attacked: "one source per fact"; nothing derived is written.**
    *Evidence.*
    - A mast's `controlPoint` is exactly the `controlPoint` of the joint row that carries `mast` (written twice).
    - `osCircuit` repeats the circuit already named on the joint, link or end rows at that switch's ports. Its meaning is
      "the TC field", not "the switch's circuit": a switch in a circuit named by a marker gets no `osCircuit`.
    - A joint's `controlPoint` is written from the one-house fallback, while the schema says "the CP field, the one place
      it is stated".
    - `track.mileposts` repeats the keys of `geometry.mileposts`. A Milepost has no pin (no nets, according to the
      netlist), so it says nothing about track.

    *Fix.*
    - Drop the mast's `controlPoint`; the joint states it.
    - Either define `osCircuit` as "the circuit of the switch's ports", written for every switch on a named circuit, or
      drop it.
    - Write the joint's `controlPoint` only when it is stated, or correct the description.
    - Drop `track.mileposts`, or give it a reason geometry does not cover.

11. **Should-fix. Claim attacked: the Watsonville `838NAB` error class is closed by `appliance.duplicate`.**
    *Evidence.* ADR 0003 rule 6 says letters are unique within one signal across all its masts. Rule 7 says a mast name
    is its signal plus its heads' letters, "checked against the attached heads". The piece checks neither (`_heads` only
    checks for duplicates within one mast). Had the second mast been named anything other than `838NAB` while keeping
    heads A and B, nothing would have fired. Both rules hold on SPCoast today (I checked).

    *Fix.* Check rules 6 and 7 per interlocking, with scenarios.

12. **Should-fix. Claim attacked: `switch.tc_block` is an error.**
    *Evidence.* ADR 0003 rule 8 and ADR 0002 D16 make a TC that lists several circuits a legal statement (a block). The
    error reports a gap in the schema, not an inconsistency in the drawing. No case on SPCoast.

    *Fix.* Name it as an open schema item in the proposal's decisions. Keep refusing to write until the owner gives the
    form, but say why.

13. **Should-fix. Claim attacked: the scenarios "set up context with tables and check with tables".**
    *Evidence.* The Given side is tables throughout. The Then side is mixed:
    - `assertIn(code, codes(...))` in `test_one_circuit_named_by_marker…`, `test_two_markers…`, `…no_house…` and
      `…duplicate…`;
    - a count in `…bounded_by_two_control_points…`;
    - the `by` lambda, which parses diagnostic message text (`d.text.split(": ")[1].split(" in ")[0]`), so rewording a
      message breaks the test;
    - ends compared through `sorted(map(str, …))`.

    No scenario covers:
    - a maintainer call joined to its house by `MC`;
    - a mast on no joint or on two joints;
    - a joint with two masts;
    - `head.duplicate`, `switch.tc_block`, `appliance.on_track`, `joint.inside` and `track.kind`;
    - a joint on a multi-house interlocking with no `CP` (`joint.control_point.missing`);
    - a three-port link, a policy with ports, mileposts;
    - rule 8 crossovers and `Derail_TC`;
    - the C6 join (marker to row);
    - "the example equals the compile of the named netlist". `test_layout_model_file` only round-trips the committed file,
      which is how the CMRI drift above went unseen.

    *Fix.* Write every Then as a table of rows (`code`, `subject`) built from structured diagnostic fields, not message
    text. Add the scenarios listed.

14. **Nit. Schema consistency.**
    - The `portRef` pattern (`^[^:/\s][^:/]*:[^:/\s][^:/]*\.(C|N|R)$`) is looser than `qualifiedName`: it allows a trailing
      space before `:` or `.`, and tabs and line breaks inside.
    - `osCircuit` wraps its `$ref` in a one-element `allOf`, while `controlPoint` uses `$ref` directly.
    - `appliances.*.style` is a string, while `devices[].type.style` is always a list (ADR 0008 rev 4, finding 19). One key
      name has two types.
    - `trackSymbol.kind` is not constrained per list (an `IRJ` validates under `policies`).
    - `circuits` and `ports` have no `propertyNames`.
    - `mileposts` items have no pattern.
    - `trackSymbol` has no `settings`, so a field someone adds to a track or policy symbol is silently dropped, against
      "every stated field written as drawn" (ADR 0008 rev 4, finding 2). No such field exists on SPCoast.

    The example validates and is sorted (§4.8); I found no ordering issue.

15. **Nit. Text accuracy.**
    - The proposal says "the library's default is `${Value}T1`"; the library has `${VALUE}T1`.
    - `AGENTS.md` says "A switch's OS circuit defaults to `<switch>T1`; a `TC` field overrides it". The piece applies no
      default when `TC` is empty, and relies on the library's field (`Switch_Manual`, `Switch_Powered_NO_TC` and `Derail`
      ship `TC ""`). That matches the library but not the `AGENTS.md` text; say so, or correct `AGENTS.md`.
    - The "41" in finding 5.
    - The 22:25 export in the header note.

16. **Nit. One Role test, two scope rules.** `trackplan.read` assigns a symbol to the nearest interlocking (`_unit_of`,
    ADR 0004 D12). `geometry.read` takes every symbol whose sheet starts with the interlocking's sheet (l.252). With
    nested interlockings the two pieces would read different symbol sets. They are identical on SPCoast.

17. **Nit. Decisions 3 and 4 are sound.** Both are real decisions with sensible defaults. For decision 4, `HBA`'s `MC`
    pin on 1SAT is a pin used for the wrong relation (meant for a house, wired to track). It is fine to leave it at info
    until the owner rules. The check covers only lamps and contacts; a head's `M` or a mast's `SIGNAL` on a track net is
    not looked for.

## Claims I would not accept

- That a NextCP's destination is derived. It is stated in `Value` on all 18, recoverable from a prefix for one, and ADR
  0010 §4.7 promises it in `track` (1).
- That `markers[]` joins `track` by kind and circuits with no key. It fails at Corporal and Sargent today (2).
- That `track` is lossless for route finding. Adjacency on dark track (Luchessa's END CTC to its Industry) and open
  pins are lost (3).
- That two TC names on one circuit are always an error. ADR 0003 rule 8 names the circuit (4).
- That the signals determine membership for the OS circuits. Six OS switches are not covered, and the count is 42, not
  41 (5).
- That signal-derived membership is the "explicit" form, and that the handoff's "never stated per appliance" stands
  against the glossary's "the `CP` field of an appliance assigns it" without an owner ruling (6).
- That `joint.inside` guards the `A`-inside convention. A reversed joint moves membership silently (7).
- That 783 and 815A are settled as "shared" at info. They need an owner ruling, and 1NAT is the same joint (8).
- That every fact inconsistency the piece can see is reported. Open switch ports, a joint inside one circuit, a reversed
  END CTC, two masts on a joint, unchecked members and references, and a duplicated policy are not (9).
- That nothing derived or duplicated is written. Mast `controlPoint`, `osCircuit`, the joint's fallback
  `controlPoint` and `track.mileposts` are (10).
- That `appliance.duplicate` closes the 838NAB class. ADR 0003 rules 6 and 7 are unchecked (11).
- That the scenarios check with tables. Several assert membership, counts, or parsed message text, and the C6 join and
  "example equals compile" gates are missing (13).
