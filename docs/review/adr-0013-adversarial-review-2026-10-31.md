# ADR 0013: adjudication of the adversarial review (2026-10-31)

Adjudication of the review the owner pasted on 2026-10-31 against `docs/adr/0013-between-control-points.md`
(branch `docs/adr-0013-blocks`, PR #59). Nothing in the ADR was edited. Order of authority as in AGENTS.md:
(1) the relay model and AAR practice from primary documents, (2) FieldUnit `src/`, (3) KiCad-derived models,
(4) legacy sketches. Hobbyist sources (C/MRI) illustrate, never validate. Owner rulings of 2026-10-30/31 are
settled unless a trace shows a safety or logic defect.

Vocabulary: GLOSSARY §10.5/§10.6 (`HR`, `DR`, `HSR`, `ASR`, directional stick `ESR`/`WSR`), §2.3 (a lever is the
dispatcher's intent at the office; the field holds the accepted control), §8 (signal indication, aspect).

## 1. Verdict table

| Item | Claim | Verdict | Consequence |
|---|---|---|---|
| OA-1 | ADR = "exact logical model" of the AAR two-wire polarized HD line circuit (Dwg 8000, 8002, 8027, 8044) | partly valid | E/P match H/D in meaning; E also carries the opposing-control, time and stick terms of an either-direction (traffic-locked) line circuit (CB&Q 1946), which Dwg 8000/8002 (one direction) do not. Drawing numbers not verified: AARTC71 is not local. |
| OA-2 | Kind as a mast property matches Rules 291/292 | valid | AAR56 pp. 51, 53-54 read. |
| OA-3 | "SP APB under Rule 505, CTC under the 760 series" | unverifiable | Comes from the owner's own answers (ABSAPB §5 items 3-4), which are not period documents; no SP rulebook opened. Nothing in the ADR rests on it. |
| 1A | APB is not `RULE_261` | valid | §4 table row 2 is wrong in principle; owner decision on what an APB block states. |
| 1B | Passed-memory race on opposing moves | partly valid | No race in the ADR's own CTC trace (the accepted control releases E before the train enters). Real under the APB operations setting of §9 (no control) and for any mast whose E has not dropped first. Primary sources use the ADR's form (track relay down while HR up), not the reviewer's approach-circuit form. |
| 1C | Cross-processor blind spot for 834SA's memory | valid, serious | §10.3's rule is not computable on Corporal's processor (836T never travels, §10.1); the obvious proxy (E from Sargent dropped) is unsafe: traced to both leaving signals cleared at once. Owner decision; default: add the approach-circuit term, which also closes 1B. |
| 1D | `Corporal:831T = [832T, 834T, 836T]` not computable at Corporal | valid | §7.2 contradicts §10.1 with the POC wiring. Gap 4 (derive from the two line signals) is answered negatively by the trace: Corporal sees E and P asserted with T1 in 836T. Owner decision. |
| 1E | P must not be asserted for Restricting / Stop and Proceed | valid | GLOSSARY §10.6: `DR` is fed over the next signal's `HR` front; `HR` is down at Restricting. Fix within rulings. |
| 2.1 | Switches inside a block; APB cut points | valid | SP hand-throw switches with electric locks read block vacancy from the line circuits [RS1942, RS1945 via research note]; §4 excludes them. §4 cuts only at controlled signals, so the APB rows of its own table are unreachable. Owner decision (touches R6/GLOSSARY §4). |
| 2.2 | Zero intermediates | valid, minor | Fix within rulings. |
| 2.3 | "levers 830 and 828 indicated" is office vocabulary | partly valid | The vocabulary point stands (GLOSSARY §2.3). The reviewer's semantics (`HSR` dropped) contradict the owner's release ruling and CB&Q p. 616; reject them. Fix the wording to "the accepted signal controls for 830 and 828 are STOP". |
| 2.4 | `RULE_290_G`/`_R` misname the rule | partly valid | AAR56 p. 53: Rule 290 *is* used "on automatic block signals for movements of trains by such signals without stopping"; p. 54: the grade marker modifies a Stop and Proceed signal. A note suffices; renaming is optional. |
| W1 | §12 wording (beam, dropout delay, make-before-break) | partly valid | The dropout delay is layout/FieldUnit (§15); do not add. The make-before-break sentence is true and useful. |
| W2 | §10.1/§10.3 "anything but stop" → "Approach or better" | valid | Same as 1E. |
| W3 | §10.4 wording | partly valid | Same as 2.3; use the field term, not `HSR`. |
| X1 (missed) | §10.5 row 3 "832 → 834 E asserted once 834T clears" | defect in the ADR | Holds only after the dispatcher has returned lever 830 to STOP; with the accepted control still toward the block it stays released. Row 2's "following train" needs a new control (stick). Fix within rulings. |
| X2 (missed) | §14 gap 2 (CB&Q feed vs passed memory) | answerable now | CBQ1946 pp. 614-616 read: the same-direction stick feeds the line rearward (= §10.3), and in addition each signal's control passes over back contacts of the same-location opposing `HR` and `SR`. The ADR has the first, lacks the second; no safety difference in the traced scenarios. |
| X3 (missed) | R10 says SP (cleared signal starts the tumble-down); §10.4 drops E on the accepted control, before the signal clears | note | That is CB&Q's trigger (`4RFR` from `RGZ`), not SP's. Both are §9 operations settings; the ADR should say which it implements. |

## 2. Per-item analysis

### OA-1. "Exact logical model of the two-wire polarized HD line circuit"

The HD line of AAR Dwg 8000/8002 (as the ABS/APB note reads them, lines 27-34) carries: no current = block
occupied or line broken; polarity = next signal at stop or proceeding. E/P keep that meaning (§10.2). But the ADR's E
also requires, at a control point, "accepted controls not toward the block AND no time running" (§10.4), and at an
intermediate the stick term (§10.3). Those are the terms of a traffic-locked, either-direction line circuit, which
CB&Q describes [CBQ1946 pp. 614-615, read] and which Dwg 8044's note restricts to "where manual control establishes
direction ... supplemented by traffic locking" (note line 128, second-hand). So: the shape is the CB&Q/SP
either-direction circuit, not the plain HD line. "Exact" overstates it: the ADR models a per-segment conjunction, with
no line relay, pole change or slow-release repeater (R15). The drawing numbers could not be checked: AARTC71 is not in
`docs/reference/`, and the 1946 nomenclature PDF there has no text layer.

### OA-3. Rule 505 and the 760 series

These numbers appear in the ADR's own evidence trail only as the owner's answers (`Answers-abs-apb.txt`, "Did SP have
a 261-type rule"), which the ABS/APB note §5 marks as "not all from period documents". No SP rulebook of 1942-1985 was
opened by anyone in the trail (note line 192, "Not found: SP rule numbers for APB or CTC"). The ADR does not use them
(§6.2 of that note keeps Standard Code numbers in the Kinds), so nothing turns on them. Unverifiable; do not cite them
as fact in the ADR.

### 1A. APB is not `RULE_261`

GLOSSARY §9 quotes Rule 261 [PRR56]: signals "supersede the superiority of trains for both opposing and following
movements". That is authority by signal indication in both directions. R10 (owner): automatic signals give no
authority. An APB block (ABSOLUTE automatic head blocks, no operator) therefore cannot be under a 261-type rule: its
head block signal cannot authorize an opposing move; trains hold timetable or train-order authority. The owner's own
answer agrees (APB "without direct dispatcher intervention"; the Oxnard-Montalvo special rules are cited as the
exception where SP let APB signals authorize moves, which proves the rule). The research note's APB/CTC contrast
(§2a: "in APB direction is established by the train", "in CTC by the control") says the same.

So §4's row `ABSOLUTE head blocks | PERMISSIVE | RULE_261 | APB` states an operating rule the block cannot have. The
model fact ("this block is APB") is correctly derived from the masts' Kinds alone; the sign is a separate operating
fact (authority). What an APB block's sign should be is an owner decision: the existing POLICY Kinds (251 L/R, 261
BOTH, 105, 93) have no "ABS, no current of traffic, authority elsewhere" member, and §4 makes a block exist only under
a 251 or 261 sign.

Note on the reviewer's wording: "APB operated under Rule 505" is OA-3; the argument stands without it.

### 1B. Passed-memory race on opposing moves

The ADR's rule (§10.3): memory of M is set when "the circuits beyond M become occupied while M shows proceed";
released when E from W is asserted again.

**Primary sources on the pick-up.** The 1927 US&S/C&NW/C&O circuits [RS1927Spray, OCR of pp. 269-270]: "As train N
starts past signal 7, relay 7TR becomes shunted and hence closes the pick-up circuit of relay 7S which will 'pick up'
before contact 7H opens and will then 'stick up' through back contact 7TR and afterward through back contact of
slow-acting relay 7HR" (p. 269). C&NW: the stick "will only pick up when the track relay is de-energized at the time
the signal arm is moving from 90 deg. to the stop position. The latter condition will only obtain for following train
movements" (p. 270). CB&Q 1946 (p. 615, OCR): when 502TR drops "a circuit is completed, momentarily before the 502HR
relay has a chance to drop, to pick up the 502SR stick relay ... over a front contact of the 502HR relay, back contacts
of the 502TR and 501SR relays". Held by 502HR back + own front; released when 502HR picks up again.

So the ADR's rule is the prototype's form: governed track relay down while the signal's own `HR` is still up. None of
the three circuits read uses an approach-circuit term; the reviewer's "fix per AAR/US&S [RS1927Spray]" is not what
that article shows (the US&S variant on p. 269 does use approach-side floating relays `ASTR`/`A4TR` in 3S's pick-up,
but I could not reconstruct that circuit from the OCR; mark it unverified). CB&Q adds one term the ADR lacks: the
same-location opposing stick down (501SR back).

**Why the prototype does not false-pick.** An opposing train entering M's governed stretch from the far end has
already broken M's line from ahead (its own earlier section, or the departure control at a CP), so M's `HR` is down
before the track relay nearest M drops. CB&Q makes this explicit: 501's line passes over 3TP and 4RATR before 4RBTR,
so an eastbound entering 4RAT drops 501HR before 4RBT (501's pick-up section) is reached. The guard is the chain, not an
approach term.

**Trace of the reviewer's counter-scenario in the ADR's CTC rules.** Southbound from Corporal into 832T; M = 832NA,
W = Corporal, "beyond 832NA" = 832T.

1. Dispatcher sets 830 toward the block. §10.4: E out (`830NAB`, read by 832NA) = 832T clear AND accepted controls
   not toward the block AND no time running → **released**. §10.2: 832NA shows stop.
2. 830SAB clears (E in from 832 asserted). Train enters 832T. 832NA is at stop, so "while M shows proceed" is false:
   **no memory set**. The reviewer's premise ("while idle 832NA shows proceed; when the southbound enters 832T ... 832NA
   still shows proceed") skips step 1.

The second counter-scenario ("in CTC with a southbound train in 836T, Corporal re-asserts E out so 832NA clears while
the train is still in 836T"): true only after the dispatcher has returned lever 830 to STOP (X1). Then 832NA shows
approach (P from Corporal = 830NAB not at stop; 830NAB is a home into Corporal, normally at stop) over 832T, which T1
has left. A northward train can reach 832T only through 836NAB, and 834 → Sargent E is released while T1 is in 836T
(§10.5 row 3, verified: 836T occupied). No hazard. CB&Q behaves the same: "When the train clears the track section
between 501-502 and 401-402 the 502HR relay ... again picks up, controlling signal 502 to Approach" (p. 616); 501 stays
at stop only because the line from the east is still broken by the train, i.e. through track occupancy, as here.

**Where the race is real.**
- §9 lists an operations setting "the tumble-down starts ... when a train passes a head block (APB)" and §4 derives
  APB blocks. Under that setting there is no accepted control to release E first. A train leaving a siding past an
  ABSOLUTE head block enters 832T while 832NA shows clear (R10: clear in both directions at rest): memory sets
  falsely; 832 → 834 E = 834T clear AND (E from Corporal OR 832NA memory) → asserted; 834NA shows approach toward a
  train coming at it. That is the opposing-protection failure the reviewer describes, in APB mode. The ADR has no
  §10.4-equivalent rule for a head block location at all, so APB operation is not specified, only classified.
- Any wiring where the control-point rule's E drop reaches 832NA later than the train does (a transport with latency,
  §10.6) reopens it. On the POC both are on one processor.

Verdict: partly valid. The ADR's CTC trace is sound; the rule is the prototype's; the hazard exists in APB mode, which
the ADR half-admits into scope (§4 table, §9 setting) without a rule. Decide: scope APB operation out of §10
explicitly, or add the guard. The approach-circuit term (1C) is one guard that works for both; the CB&Q guard
(same-location opposing stick down in the pick-up) does not cover this case.

### 1C. 834SA's memory cannot be computed on Corporal's processor

POC wiring (§10.6): 834, 834T on Corporal's processor; 836T on Sargent's. 834SA's "circuits beyond" is 836T. §10.1:
"Track circuits never travel one by one. Only what each line signal says travels." So Corporal's processor cannot
evaluate "836T becomes occupied while 834SA shows proceed" (the footnote `[^segment]` handles the E *output* by
letting Sargent AND 836T in; nothing handles the memory). The reviewer is right that the only remote observable is E on
`836SA`, which drops for three causes: 836T occupied, 836NAB's accepted control toward the block, 836NAB running time.

**Trace of the proxy "E from Sargent dropped while 834SA showed proceed".** Corporal's levers at STOP; block idle.
1. Sargent sets 836 toward the block. 834 → Sargent E = 836T clear AND (E from 832 asserted OR 834NA memory); E from
   832 = 834T clear AND (E from Corporal asserted OR ...) = asserted. 836NAB clears legitimately.
2. `836SA` E drops (control toward the block). 834SA goes to stop, and under the proxy sets its memory.
3. 834 → 832 E = 834T clear AND (E from Sargent OR 834SA memory) = **asserted**; P released (834SA at stop). 832SA
   shows approach. 832 → Corporal E = 832T clear AND E from 834 = asserted, P asserted.
4. 830SAB's E in is asserted; the dispatcher clears 830SAB. Two leaving signals into one single-track block are
   clear until Corporal's E-out drop walks the chain back (832NA, 834NA, 836NAB) and tumbles 836NAB down. A train
   that has accepted 836NAB is past help.

Under the ADR's literal rule (836T itself) step 2 sets nothing, so the ADR is sound but not implementable as written
on this wiring. An implementer who reaches for the proxy produces a head-on. Valid and serious.

**The reviewer's fix, traced.** Memory set when M shows proceed AND M's approach circuit (834T) is occupied AND E from
W is released. In step 2 834T is clear → no set. Can Sargent clear 836NAB while a southbound is in 834T under
834SA at proceed? 834 → Sargent E needs E from 832 = 834T clear → released; 834NA memory is not set (no northward
move) → Sargent cannot. So with 834T occupied, an E drop from Sargent can only mean 836T occupied, which is the
train passing. The term is sound on this topology, and the approach circuit is always local: §10.3 already needs the
location's own circuits for its other output. With the boundary circuit (§12) ORed into both sides, "approach occupied
at the instant the governed side becomes occupied" holds even for cars that only the joint detector sees.

Cost: it departs from the CB&Q/C&NW pick-up (which has no approach term) and is a change to a ruled rule (decision 8),
so it is an owner decision. Alternatives: (i) rule that a mast's memory is computed where its governed circuit is read
(here Sargent), with the result travelling as a third value on the line signal; (ii) forbid wiring where a signal
location's two sides are on different processors (then nothing crosses mid-location, and the 834-836 crossing is at
the CP boundary, where Sargent's rule needs only 836T and the accepted control). (ii) is what the POC nearly is: only
836T is on the "wrong" side. Default: the approach term; it also closes 1B's APB case.

### 1D. `Corporal:831T` with members on two processors

§7.2: `831T = [832T, 834T, 836T]`, sent by Corporal (`831TK`), check: "the qualifying station is at one end of the
block". Corporal does not read 836T. With T1 in 836T the office lamp would show the block clear from Corporal's
knowledge. The reviewer is right. §14 gap 4 asks whether the two line signals could replace the members; the trace of
§10.5 row 3 answers no for E/P as defined: at Corporal, 832 → Corporal is E asserted (832SA's memory, then E from 834
via 834SA's memory) and P asserted (832SA at approach) with T1 in 836T. SP's whole-block detection "from the two line
circuits" [RS1947 p. 92] therefore used a different circuit (perhaps the line in the other direction, read at its
receiving end, Sargent); the ADR's model has no such read at Corporal. Owner decision. Default: the derivation reports
an error when a virtual circuit's member is not read on the processor that sends it; the owner either reads 836T on
Corporal's processor or draws one virtual circuit per end and lets the board lamp consume both tokens (`Corporal:831T`,
`Sargent:831T`), the office ORing them. That matches R12 (nothing travels that nothing consumes) and the research
note's "each station reported its portion" reading of the desk lamps.

### 1E. P and Restricting

GLOSSARY §10.6 (authority 1 for the model): `DR: ──[ 2HR front ]──[ advance TR front ]──[ next signal HR front ]──( 2DR )`.
"Next signal HR front" means the next signal shows at least Approach; a call-on/Restricting is displayed with `HR`
down. AAR56 p. 53 (read): Rule 290 "may be used to admit a train to a main track or other route that is occupied". The
signal in rear of a Restricting must show Approach. The ADR's "P: the producer's mast indicates anything but stop"
(§10.1, §10.3, §10.4 "830NAB does not indicate stop") asserts P for Restricting and so clears 834SA behind Sargent's
home at call-on. Stop and Proceed is the red aspect and already releases P. Valid; a definition fix inside the
two-value ruling. Note for §15: with two values the signal in rear of a diverging aspect also gets "clear"; that is
selective compression (R15) and should be said once.

### 2.1. Switches inside a station-to-station block; APB cut points

Two defects.
- SP CTC blocks held hand-throw switches with electric locks whose release read block vacancy from the line circuits
  [RS1942, RS1945, research note §2e; not opened by me]. §4 ("holds no switch or derail") makes such a main track not
  a block, and R6/GLOSSARY §4 ("each piece with a switch or derail is an interlocking") makes it an interlocking with
  no controlled signal, which §5's check then reports on every PERMISSIVE mast whose route "passes a switch". The §5
  spring-switch exception shows the ADR knows the case and leaves the block rule unchanged.
- §4 cuts "at every controlled signal joint". An APB stretch between two CPs (CP, siding, siding, CP) is then one
  piece holding the siding switches: not a block. The §4 table's APB and ABS rows are unreachable from its own cut
  rule unless ABSOLUTE joints cut too.

Owner decision, since R6 is GLOSSARY text. Default: cut at CONTROLLED and ABSOLUTE joints; a piece is a block when it
holds no *powered* switch (one with a machine or a CP Name); hand-throw, spring and electrically locked hand-throw
switches may lie in a block (their lock reading the block is a later rule); a powered switch outside interlocking
limits is an error.

### 2.2. Zero intermediates

A CTC block from home to home with no automatic signal is ordinary. §4's table columns "Intermediate masts:
PERMISSIVE" / "all PERMISSIVE" read as requiring at least one. Fix: "none, or all PERMISSIVE".

### 2.3 and W3. "levers 830 and 828 indicated not toward the block"

GLOSSARY §2.3: a CTC lever's position is "the intent of the dispatcher only"; the field unit holds the accepted
control. So "levers ... indicated" is office vocabulary for a field term. The reviewer's replacement, "not controlled
toward the block (HSR dropped)", changes the meaning: `HSR` drops at knockdown when the train enters the entrance
circuit (GLOSSARY §10.5), which would re-energize the opposing line the moment the train is past 832T. That contradicts
the owner's release ruling ("doesn't reset until the initiating signal lever is ack'd at STOP AND the entire block is
cleared") and CB&Q: `4RFR` "released with the restoration of C.T.C. machine levers to normal" (p. 616, read), AAR 8059
"providing signal lever 4 is not still turned to the right" (research note). SP's field, which knew only the stick
control, is the one that differs; the ruling picked the CB&Q/AAR release, which R11 allows. Keep the semantics, fix the
word: "the accepted signal controls for 830 and 828 are STOP (neither toward the block)". FieldUnit note: `HSR()` today
conflates the accepted direction with the stick; the rule needs the accepted direction itself.

### 2.4. `RULE_290_G`, `RULE_290_R`

AAR56 p. 53 (read): the Rule 290 indication "is used at interlockings for routes where restricted speed is required
and on automatic block signals for movements of trains by such signals without stopping". p. 54: the grade signal
"permit[s] heavy tonnage freight trains ... to proceed at restricted speed by a signal displaying Stop and Proceed
without stopping ... on some roads all freight trains ... on other roads all trains". Rule 291's own note: "Railroads
desiring to avoid stopping trains may arrange accordingly." So the plate is a modifier of the Rule 291 signal, and the
resulting indication is Rule 290's. The Kind names the resulting indication, which is defensible; the ADR should say so
in one line. The symbols exist (`Signal Mast Plate-G`, Kind `RULE_290_G`; `Plate-R`, `RULE_290_R` in
`Railroad-Trackplan.kicad_sym`), so renaming is a library edit and not worth it. "Plate-R, all trains" is the owner's
convention; AAR56 names no R plate (yellow G disc, short arm, yellow arm). Not a model fact.

### W1. §12 wording

"Car bodies hold the beam broken (with a short dropout delay bridging coupler gaps)": the detector technology and its
debounce are the layout's and FieldUnit's (§12 "The model reads only the Style"; §15). Do not add. The second sentence
("because the boundary circuit is ORed into both sides, it also guarantees make-before-break when a train passes the
signal") is correct and worth one line; it is why the approach term of 1C is reliable at the joint.

### X1 (missed by the reviewer). §10.5 rows 2 and 3 against §10.4

Row 3: "832 → 834 E asserted once 834T clears". By §10.3 that E = 834T clear AND (E from Corporal asserted OR 832NA
memory). 832NA's memory is not set (no northward move). E from Corporal (§10.4) needs the accepted controls for 830
and 828 at STOP. Under the owner's release ruling the dispatcher has not necessarily done that; while 830's accepted
control is still toward the block, the E stays released and 834NA stays at stop (the CB&Q behaviour: "Signal 501 is
retained at Stop"). The row should say "once 834T clears and 830's control is back at STOP". Row 2: "Corporal can
clear 830SAB to approach for a following train" needs a new control under stick operation (lever to STOP, then toward
the block again); during the STOP moment E out asserts and 832NA may show approach over the empty 832T, harmless.

### X2. §14 gap 2, from the circuit description

CBQ1946 pp. 614-616: at a double location the line circuit controlling each signal "extend[s] through back contacts
of the HR and SR stick relays for the opposing direction" (p. 613); the same-direction stick re-feeds the line toward
the signal in rear: "With the 502SR relay up energy is prepared to be fed westward on the line circuit over front
contacts of the 502SR relay" (p. 615). So CB&Q has both the ADR's OR (same-direction memory) and a cut (opposing `HR`
and `SR` at the same location) in each signal's own control. The ADR has only the OR; a mast's own conditions (§10.2)
do not mention the same-location opposing mast. Effect: 832NA may clear while 832SA's memory is set (after the lever
is restored), where CB&Q's 501 waits for 502HR to re-pick. No safety difference in the traced scenarios (nothing can
be northbound there); a fidelity difference. Optional one-line addition to §10.2: "and the same location's opposing
mast at stop with its memory released". Gap 2 can be closed either way.

### X3. Which railroad's trigger §10.4 implements

R10 and §9 say SP starts the tumble-down when the leaving signal *clears*. §10.4 releases E out when the accepted
control turns toward the block, before the signal clears (the signal cannot clear until E in returns). That is CB&Q's
order (`4RFR` picks "over a front contact of the eastward signal control code application relay RGZ", p. 614; the
round trip "requires about 6 sec.", p. 615), and it is the safer one (the far end is locked before anything is
displayed). Say so in §10.4; it is an operations choice under §9, and R10's wording should not claim it is SP's.

## 3. Proposed ADR changes

### Fixes within existing rulings

1. §10.1 and §10.3 P: "the producer's mast in that direction indicates anything but stop" → "the producer's mast in
   that direction indicates Approach or better (its `HR` is up: not Stop, Stop and Proceed or Restricting)". §10.4
   "P out: Corporal's home, 830NAB, does not indicate stop" → "... indicates Approach or better". Add to §15: a
   diverging aspect ahead still yields clear in rear (two values, R15).
2. §10.4 E out: "levers 830 and 828 indicated not toward the block" → "the accepted signal controls for 830 and 828
   are STOP (neither toward the block)". Add one line that this is the accepted control, not `HSR`, and that it is
   the CB&Q/AAR 8059 release (lever back to normal), chosen under R11 (X3).
3. §10.5 row 3 "asserted once 834T clears" → "asserted once 834T clears and 830's accepted control is back at STOP;
   released while it is still toward the block". Row 2: add "(a new control under stick operation)".
4. §4 table: intermediate masts "PERMISSIVE" → "none, or all PERMISSIVE" (2.2).
5. §5 Plates: add "The Kind names the resulting indication, Rule 290 (AAR56 p. 53); the plate itself modifies a Rule
   291 signal (p. 54)."
6. §12: add "Because the boundary circuit is ORed into both sides, a train passing the masts occupies the circuit
   ahead before it releases the one behind."
7. §14 gap 2: replace with the X2 finding (closed; optional cut).
8. §14 gap 4: replace with "Not derivable from E and P as defined: Corporal reads E and P asserted with T1 in 836T."
9. §10.6 table row `836SA`: E asserted when "836T clear AND 836NAB at stop and not running time" → "836T clear AND
   836NAB's accepted control at STOP and not running time" (same vocabulary fix).

### Owner decisions needed (one line each, with a default)

1. **APB sign (1A).** An APB block (ABSOLUTE head blocks) is not under a 261-type rule. Default: §4 derives APB from
   the Kinds alone; the sign states authority only; the APB row drops `RULE_261`; a 261 sign on ABSOLUTE ends is
   reported at warning (Oxnard-Montalvo would state it deliberately); a block with ABSOLUTE ends needs no sign.
2. **Passed memory set condition (1B, 1C).** Default: "set when M shows Approach or better, M's approach circuit is
   occupied, and E from W is released"; released when E from W is asserted again. Computable without far-side
   circuits; also guards the APB case. Alternative: keep the prototype form and forbid a signal location's two sides
   on different processors.
3. **APB operation in §10 (1B).** Default: out of scope for §10 (CTC rules only); §9 keeps the setting as a named
   future; §4 keeps the classification.
4. **Virtual circuit members on another processor (1D).** Default: error from the derivation when a member is not read
   on the sending station's processor; the owner reads 836T at Corporal or draws one virtual circuit per end and the
   board consumer ORs the two tokens.
5. **Switches inside a block and the cut rule (2.1).** Default: cut at CONTROLLED and ABSOLUTE joints; a block may hold
   hand-throw, spring and electrically locked hand-throw switches; a powered switch in a block is an error; amend R6
   (GLOSSARY §4) to "powered switch".
6. **Same-location opposing cut (X2).** Default: not added (no safety difference); recorded as a fidelity option.

## 4. Sources opened

Primary, read in full or in the cited pages:
- RS1927Spray: *Railway Signaling* v20 n7, July 1927, pp. 269-270, "Various Circuits for Directional Control of
  Single Track Signals" (US&S, C&O, IC, C&NW circuits). Fetched from jonroma.net, text recovered with `pdftotext`
  from the scan's OCR layer. Used for the stick relay pick-up (1B).
- CBQ1946: *Railway Signaling*, Sept. 1946, pp. 612-616, Zane, "New Signal Control Line Circuits in Centralized
  Traffic Control Territory on the Burlington". Same method. Used for the SR pick-up and hold, the line re-feed over
  opposing HR/SR back contacts, the `4RFR` set (RGZ) and release (levers to normal), "retained at Stop" (1B, 2.3, X2,
  X3).
- AAR56: `FieldUnit/docs/reference/Chapter-02-Symbols-Aspects-and-Indications-1956.pdf`, printed pp. 50-54 (PDF
  pages 52-56), read as page images: Rules 289-292, number plates, grade signals (OA-2, 1E, 2.4).
- FieldUnit `docs/GLOSSARY.md` §2.3, §4, §8, §9, §10.5, §10.6, §11 headings (vocabulary, `DR` circuit, Rule 261 text).

Secondary and project documents:
- `docs/adr/0013-between-control-points.md` and `docs/adr/0013/line-signals.svg` (full).
- `docs/review/traffic-locking-research-2026-10-31.md` (full), `docs/review/abs-apb-research-2026-10-30.md` (grep and
  §5-§6), `docs/review/Answers-abs-apb.txt` (full; the owner's answers are not period documents).
- `docs/adr/0003-name-grammar.md` (D1, D9, circuit numbering), `docs/adr/0009-explicit-seams.md` §3.10,
  `docs/adr/0012-derivation-rules-and-domain-libraries.md` §5.5, §8.
- `~/Dropbox/KiCad/Railroad/symbols/Railroad-Trackplan.kicad_sym` (mast Kinds, `Plate-G`/`Plate-R` Kinds).

Not verifiable here:
- AAR Typical Circuits (AARTC71) Dwg 8000, 8002, 8027, 8044, 8059, 8064, 8066, 8082: not in `docs/reference/`; known
  only through the research notes' readings.
- The AAR 1946 nomenclature PDF in `docs/reference/` is a scan without a text layer; its SR/D definitions are taken
  from the research note.
- SP rulebooks 1942-1985 (Rule 505, the 760 series): not opened by anyone in the trail.
- RS1942, RS1945, RS1947 (SP line circuits, hand-throw switch locks): cited through the research notes, not opened.
- Bruce Chubb's C/MRI texts: not opened; hobbyist, not an authority here.

## Second pass: rulings audited against the order of authority (2026-11-01)

Correction to the first pass. Lines 6-7 above treated the owner's rulings as settled unless a trace failed. That
was wrong: AGENTS.md ranks (1) the relay model and AAR practice above everything; the rulings are design proposals
and a ruling that disagrees with (1) is wrong whether or not a trace fails. Bruce Chubb's signaling analysis counts as
serious analysis of prototype practice, with model compressions marked as such. None of his texts is on this machine
(`C/MRI User's Manual`, *Railroader's C/MRI Application Handbook* Vol. 2, *How to Operate Your Model Railroad*);
what is attributed to him below is from memory and marked "(Chubb, not opened)". The local C/MRI program
`~/Dropbox/workspace/C-MRI Code V.1-44/RR1-44.txt` is Martin Nile's Southern California Railway CTC, not Chubb's,
and ranks as (4), evidence only.

New primary reading for this pass: CBQ1946 p. 614 (west-end line feed), p. 615 (`6RAGGPR` and the pole change,
`502SR` pick-up and feed), p. 616 (release on levers to normal, "traffic direction is maintained until the eastbound
train is by signal 6LA or 6LB"); RS1927Spray pp. 269-270 as before.

### Trace that changes two verdicts: a stale passed memory

ADR rules as written, POC block Corporal-832-834-Sargent, T0 northward arriving at Corporal.

1. T0 passes 832NA northward: 832NA's memory sets (832T occupied while 832NA showed proceed). Correct.
2. While T0 is still in 832T the dispatcher lines 830 southward for the next move (ordinary practice). §10.4: E out
   from Corporal = 832T clear AND accepted controls at STOP AND no time → released, and it stays released after T0
   clears 832T because the control is toward the block.
3. 832NA's memory releases only "when E from W is asserted again" (§10.3); W = Corporal; it never is. The memory is
   stale.
4. 832 → 834 E = 834T clear AND (E from Corporal OR 832NA memory) → **asserted** through the stale memory.
   834 → Sargent E = 836T clear AND (E from 832 OR 834NA memory) → **asserted**. 836NAB's E in is asserted.
5. 830SAB's E in = 832T clear AND (834 → 832 E OR 832SA memory); 834 → 832 E = 834T clear AND (E from Sargent OR
   834SA memory); E from Sargent asserted (Sargent idle) → 830SAB clears southward.
6. Sargent lines 836 northward and codes: 836NAB clears, since its E in is asserted (step 4). Two leaving signals
   are clear into one single-track block. Corporal's E out was already released, so nothing further tumbles 836NAB
   down; 830SAB drops only when Sargent's control releases E from Sargent, after 836NAB has already cleared, and
   with a train approaching it holds through time locking.

This violates CFR §236.405 / ICC 1939 Item 382 (occupancy and an opposing cleared signal must prevent changing the
direction of traffic) and the owner's own release ruling (reset only with the initiating lever at STOP). The cause is
structural: the stick OR-path lets a memory bypass the far control point's accepted control, and the chain carries
nothing that a stick cannot bypass. The prototype has that something:

- AAR Typical Circuits: a per-block traffic relay `FR` in the machine (Dwg 8066, 8082) or field `FSR` at both ends
  (8082), or `TFZR`/`RFSR` with coded track (8059) [research note §2a-b; drawings not opened].
- Erie 1942 and N&W 1949: a separate "traffic locking line circuit" that "checks the opposing signals in the stop
  aspect" [research note §2c; not opened].
- CB&Q: the leaving signal's mechanism is fed only over its own `4RFR`, which picks on the control and is released
  with the levers to normal [CBQ1946 pp. 614-616, read]; the article defers the `RGZ`/`4RFR` controls to its first
  part (Aug. 1946 p. 528, not read), and CB&Q also relied on the machine's lever locking.
- SP: the owner's answer 15, "the field logic checks the block vacant and sets the directional locking"; RS1942/1945/
  1947 "regardless of the code sent" [via research note; not opened]. SP's exact circuit is not in the trail.
- Chubb's CTC keeps an explicit per-block traffic-direction variable set by the signal lever and held until the block
  is vacant; his APB infers direction from the order in which adjacent blocks become occupied (a compression of the
  stick relays) (Chubb, not opened). Nile's program carries the far-end term in every leaving signal's equation:
  "nobody cleared in our direction from the west end" (`RR1-44.txt` lines 2106-2110, 2234) and infers direction of
  travel from adjacent occupancy (lines 1471-1475): the same shape, rank (4).

Revised verdicts: **2.3 release ruling: confirmed as a rule, but the chain as written does not give it** (the ADR
is wrong, not the ruling). **X2 stays fidelity**: the same-location opposing cut does not close this hole (traced:
with one intermediate the stale memory feeds Sargent's E directly). The owner's original route equation
`Sargent:836NAB = ... 830(LEFT|STOP)` had the right term; §10.4's "No term for Sargent's lever ... is needed" removed
it.

### The rulings, one by one

| # | Ruling (ADR §) | Verdict | Evidence and corrected rule |
|---|---|---|---|
| R-1 | Three layers: operations, model, layout (§9) | not a prototype question | Design choice. Consistent with AAR56 keeping rules (Ch. II) apart from circuits (Typical Circuits). |
| R-2 | Line signal of two values E, P; truth table E released = stop, E alone = approach, E and P = clear (§10.1-10.2) | confirmed, with one fix | GLOSSARY §10.6 `HR`/`DR`; CBQ1946 pp. 614-615: neutral `HR` and biased-neutral `DR` on one two-wire line, "only the 402HR relay will pick up for controlling signal 402 to Approach ... pole changes ... 402DR ... Clear". Fix (1E): P is asserted for an aspect "more favorable than Stop or Restricting" (`6RAGGPR`, p. 615), not "anything but stop". |
| R-3 | Signal-location rule: E to rear = circuits to the rear clear AND (E from ahead OR passed memory); P = own mast not at stop (§10.3) | confirmed in structure; one gap | CBQ1946 p. 615: rearward feed over own `HR` front (idle) or own `SR` front (following), broken through the segment's track relays; RS1927 p. 269. Gap: the prototype passes the chain through M's `HR`, which also checks the same-location opposing signal at stop and its stick down (p. 613: line circuits "extend through back contacts of the HR and SR stick relays for the opposing direction"); the ADR passes E from ahead raw. Fidelity only (see the stale trace: it does not close the hole). |
| R-4 | Passed memory sets when the circuits beyond M become occupied while M shows proceed (decision 1 in the brief; §10.3) | confirmed | RS1927 p. 269: 7S picks "before contact 7H opens" when 7TR is shunted; p. 270 (C&NW): "only pick up when the track relay is de-energized at the time the signal arm is moving from 90 deg. to the stop position"; CBQ1946 p. 615: 502SR over 502HR front, 502TR back, 501SR back. No approach-circuit term in any of them. The first-pass default for decision 2 (add the approach term) is withdrawn as a prototype rule; it remains a possible R15 compression. |
| R-5 | Passed memory releases when E from ahead is asserted again (§10.3) | confirmed | CBQ1946 p. 616: "The 502SR relay circuit also is opened when the 502HR relay again picks up"; RS1927 p. 269: "as long as relay 7HR remains down". `HR` re-pick = governed circuits clear and line from ahead energized = E from W. The stale case is a consequence the prototype also has at this relay; the prototype covers it with R-8, not here. |
| R-6 | Where the memory is computed (1C): 834SA's memory needs 836T, on Sargent's processor | wrong as a layout, not as a rule | Prototype: the stick's pick-up contact is the track relay at the signal location (502TR, 7TR), i.e. the governed circuit's relay sits at the signal that governs over it; AAR Dwg 8000 takes the line energy "through a front contact of the track relay ahead of the signal" [research note line 33]. Corrected rule: a mast's governed circuit is read on the processor that runs the mast's signal location; otherwise error. The POC wiring (836T on Sargent) is the departure. |
| R-7 | CP rule: E out = block-side circuit clear AND accepted controls at STOP AND no time; P out = home not at stop (§10.4) | confirmed, with the P fix | CBQ1946 p. 614 west-end feed: over the eastward leaving signal's red repeater `4RMR` front, `4RFR` (traffic, picked on the control) back, switch lock repeater, `3TP` and `4RATR` track relays. Time term: SP DT-10 [RS1942/45/47 via note]; CFR §236.407 [via note]. P out: `4LAGGPR`/`6RAGGPR`, Approach or better (p. 615). |
| R-8 | "E in stands for every remote term ... No term for Sargent's lever and no block-clear term is needed. The traffic direction relay is not stated" (§10.4) | **wrong** | Stale-memory trace above. Prototype: every scheme in the trail carries a far-end traffic term that no stick bypasses (AAR `FR`/`FSR`, Erie/N&W traffic-locking line, CB&Q `4RFR` in the mechanism feed, Chubb's per-block direction variable). Corrected rule: the block's direction state is explicit at each control point. Minimal form: a third line-signal value **F** (far end free), produced at a control point = accepted controls at STOP AND leaving signals at stop AND no time, relayed **unchanged** by every signal location (never ORed with a memory), consumed by the opposite control point's leaving signals: `830SAB = ... E_in F_in`. E keeps its chain and sticks for following moves. The owner's "reset only when the initiating lever is at STOP and the block is clear" then holds: F gives the lever, E the block. |
| R-9 | Release ruling: direction resets only when the initiating lever is indicated at STOP AND the whole block is clear (brief; 2.3) | confirmed as a rule; the ADR's chain does not deliver it | CBQ1946 p. 616: "if the 4RFR relay has been released with the restoration of C.T.C. machine levers to normal"; "Traffic direction is maintained until the eastbound train is by signal 6LA or 6LB"; AAR 8059 "providing signal lever 4 is not still turned to the right" and CFR §236.405 [via note]. The reviewer's `HSR`-dropped semantics stay rejected. Delivered only with R-8's F. |
| R-10 | Kind (CONTROLLED, ABSOLUTE, PERMISSIVE) changes the crew's rule, never the aspect or the field logic (§5) | confirmed for the aspect; qualified for the logic | AAR56 p. 51 (Rule 291 designated by number plate, marker light or pointed blade; same red), p. 54 ("Stop and proceed ... closely allied with the stop indication"). Qualification: Kind decides where a block ends (§4) and, in APB, which signal is a head block; RS1927 p. 270 puts stick relays at "the intermediate signal and also at the head-block signals", so per-mast logic is the same, block structure is not. |
| R-11 | SP intermediates clear in both directions at rest; clearing a leaving signal tumbles the opposing ones down (R10, §9) | confirmed as SP; operations elsewhere | RS1942/1945: two normally energized line circuits per block, one per direction, so at rest no direction is set [via note, not opened]. CB&Q keeps the last direction and the tumble-down starts on the control, not the cleared signal (CBQ1946 pp. 614-615, read). X3 stands: §10.4 implements CB&Q's trigger (control) while R10 names SP's (cleared signal); say which. |
| R-12 | Station-to-station block cut at controlled signal joints; no switch inside (§4) | wrong in two places | 2.1 of the first pass: SP electrically locked hand-throw switches read block vacancy from the line circuits [RS1942/45 via note]; APB blocks end at ABSOLUTE automatic head blocks (AAR Ch. XV terms, owner answer 2; RS1927 p. 270). Corrected: cut at CONTROLLED and ABSOLUTE joints; a block may hold non-powered switches. |
| R-13 | ABS/APB/CTC derived from Kinds and the sign; APB row under `RULE_261` (§4) | wrong (1A) | GLOSSARY §9 Rule 261 text; R10. APB is derived from ABSOLUTE ends alone; the sign states authority. |
| R-14 | A 251 sign's LEFT/RIGHT = lever direction of the signals that govern with the current (decision 5, §8) | not a prototype question | Representation. The current of traffic is a timetable designation (GLOSSARY §9 Rule 251 "designated tracks"); how the drawing states it is the owner's. |
| R-15 | A 251 sign inside interlocking limits states the current of traffic on that track (§8) | not a prototype question | Same. |
| R-16 | Boundary track circuit ORed into both neighbours (§12) | not a prototype question | Layout compression for undetected cars. Prototype analogue of the concern: Dwg 8000's note on the false clear flash when a short train leaves [via note]. |
| R-17 | Names by signal location (§11) | confirmed | ADR 0003 D-rules from AAR56 p. 31 (a circuit outside interlocking limits is numbered for the signal that governs over it); not re-opened. |
| R-18 | Transport: a crossing line signal with no drawn transport is an error (decision 11, §10.6) | not a prototype question | Layout. One prototype remark: the line circuit is vital and wired; an office relay (option B) is the AAR machine-`FR` family, which paired it with lever locking, not a fallback. |
| R-19 | Block indication = virtual circuit of the block's members, sent by one end (§7.2) | confirmed as the office fact; wrong as placed (1D) | Owner answer 10 and 16 (`BPR`); RS1947 p. 92 "detect track occupancy of the block as a whole" [via note]. The members must be read where the token is sent (R-6's rule), or each end sends its part. |

### Chubb, where he bears on this (not opened; verify before citing in the ADR)

- His APB: direction from the order of block occupancy, opposing signals held at stop to the next siding, following
  signals permissive; a compression of the `SR` relays, layer "operations/model", not prototype wiring.
- His CTC: per-block traffic direction set by the signal lever, locked while the block is occupied or the opposing
  signal is cleared; this is the explicit direction state R-8 restores.
- His aspect logic: the signal in rear of Restricting shows Approach; consistent with R-2's fix.

### Owner decisions that remain (one line each, with a default)

1. **Explicit direction state (R-8, replaces first-pass decision 2's framing).** Default: add line-signal value F
   (far end free), produced at a CP, relayed unchanged, required by the opposite CP's leaving signals; E and the
   passed memory stay as ruled.
2. **Where a mast's governed circuit is read (R-6, 1C).** Default: on the processor of the mast's signal location,
   checked by the derivation (error); the approach-circuit term is withdrawn as prototype and offered only as an R15
   compression if the owner wants 836T to stay on Sargent.
3. **APB sign (R-13, 1A).** Default: APB derived from ABSOLUTE ends; the sign states authority only; `RULE_261` on
   ABSOLUTE ends at warning.
4. **APB operation in §10 (1B).** Default: out of scope for §10; the classification stays.
5. **Block cut and switches (R-12, 2.1).** Default: cut at CONTROLLED and ABSOLUTE joints; non-powered switches may
   lie in a block; amend R6/GLOSSARY §4 to "powered switch".
6. **Block indication across processors (R-19, 1D).** Default: follows decision 2 (members read where the token is
   sent); else one virtual circuit per end, ORed by the board consumer.
7. **Tumble-down trigger (R-11, X3).** Default: on the accepted control (CB&Q, safer); reword R10 so SP's cleared-
   signal trigger is not claimed as what §10.4 implements.
8. **Same-location opposing cut (R-3, X2).** Default: not added; fidelity only.

Fixes within rulings from the first pass (§3) stand, with one change: the P definition's citation is now primary
(CBQ1946 p. 615 `GGPR`), and §10.5 row 3's correction (X1) is confirmed by CBQ1946 p. 616.
