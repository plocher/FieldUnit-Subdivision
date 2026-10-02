# Vocabulary review: historical correctness and STE style

Status: iterated seven times with the owner and closed (2026-10-01, rev 7). Findings, decisions and the plan.
The derail change (F11) is made and uncommitted in both repos. No other source document is changed.

Scope read in full:

- FieldUnit: `docs/GLOSSARY.md` (including the uncommitted §1.4), `docs/AAR_SIGNALING_PRIMER.md`,
  `docs/CTC_SUBDIVISION_AND_PLANT_DESIGN.md`, `docs/how-to/01`–`05`, `docs/tutorials/01`–`03`, `README.md`.
- FieldUnit-Subdivision: `docs/review/ontology.md` (rev 4), `README.md`.

Not read: `CONTROL_POINT_ARCHITECTURE.md`, `FIELDUNIT_STUDIO_DESIGN_SPEC.md`, the ADR, the two reference PDFs.

## How to read the ratings

- **Severity**: S1 = wrong model (a designer builds the wrong structure), S2 = wrong fact or wrong
  word (a reader learns something false), S3 = style or consistency.
- **Blast radius**: B1 = code API, schema, symbol names or repo names; B2 = several documents;
  B3 = one document.
- **Confidence**: how sure the reviewer is of the historical claim. "Checked" means checked against
  a source in this session. "Recall" means reviewer knowledge that still needs a primary source.
  Occurrence counts are case-insensitive line counts over `.md/.h/.cpp/.ino/.py/.json`.

One source was checked: rrsignal.com `uss506.htm` states that the US&S 506 code has "16 steps
(1 conditioning, 7 station selects, 7 functions, and 1 delivery step)", 35 field locations, and
"7 controls and 7 indications at each station" for 506/506A (506C: 7 controls, 35 indications).
The page says "field station" and "field location". It does not say "control point".

---

## Tier 1: model-level disconnects (settle these first)

### F1. Three incompatible descriptions of the code line (S1, B2, checked)

| Document | Claim |
|---|---|
| Glossary §1.1, Primer §9.5/§9.6, Subdivision README | 15 steps (Form 504/506), 20 steps (506-A/508), 32 steps (Type L Form 510) |
| Primer §9.5.1 | 15 steps: 1 sync, 4 address, 2 switch, 3 signal, 3 track, 1 MC, 1 execute |
| Ontology §1, §3 | 16 steps: 1 conditioning, 7 station, 7 function, 1 delivery; 506A |

- The source supports the ontology. It contradicts the glossary: 506 and 506A are both 16-step.
- "Form 508", "Form 510", "Type L" and the 20/32-step figures have no source. Treat them as
  unverified until one is found. The same applies to "GRS Type K2 Class M".
- Primer §9.5.1 is the SPCoast desk's display rhythm. It is a model design, placed in a prototype
  primer, and its 4-bit address plus track steps look like a prototype fact.
- Ontology §3a "15 versus 16: both are right" is a reconciliation of a glossary error, not a fact.
  Delete it when the glossary is corrected.
- Ramification: the capacity check in ontology §6a needs one true budget. Today three exist.

### F2. The 7+7 budget arithmetic omits track indications (S1, B3 now, B1 once coded; checked + logic)

Ontology §3 costs the end-of-siding point at 7 indications: switch 2, signal 3, maintainer call 1,
call-on 1. Ontology §1 says the same point has four track circuits (OS and three approaches). The
table has no track step. An office with no OS indication cannot work.

- The claim "the budget is exactly the end-of-siding control point" does not hold on the indication side.
- The control side depends on two unverified items: that a signal always takes three control steps,
  and that call-on was a standard function at a siding end. The source list in ontology §1 reads as a
  pasted search summary (it calls the function steps "7 codelines"). It is not a primary source.
- 506C (7 controls, 35 indications) shows that the real pressure was on indications.
- Ramification: the "panel symbol set already encodes this budget" cross-check and the planned
  `Codeline-USS506` budget field both inherit the error.

### F3. "Control Point" and "Controlled Point" carry a distinction that history does not (S1, B1, recall)

- Recall: GCOR and western practice say "Control Point". 49 CFR 236 and NORAC say "Controlled Point".
  They are regional and regulatory names for the same thing: a location of dispatcher-controlled signals.
- The glossary uses the two spellings for two concepts (location; addressable code-line unit).
- Ontology rev 2 says they are one concept, then §6 models `Control Point 1:N controlled point`,
  plus `Field Unit 1:N Station` and `Station 1:N Panel Column`. Three nouns remain. It is not stated
  whether "controlled point" and "Station" are the same thing.
- The era source (rrsignal, US&S) says "field station" for the addressable unit.
- STE: two terms that differ by two letters cannot carry a structural distinction.
- "Station" also has a rulebook meaning (a place named in the timetable). "Field station" or
  "code station" avoids that collision.
- Counts: "controlled point" FU 12, SUB 41; "control point" FU 79, SUB 39; "line station" FU 3, SUB 7.
  The KiCad attribute is `CONTROLLED_POINT` and plant appliances carry a `CP` field.

### F4. "A control point is by definition a track switch" (S1, B2, recall)

Ontology §1 and §3a ("one per switch").

- A control point is defined by controlled absolute signals, not by a switch. Hold signals, drawbridges
  and crossings at grade are control points with no switch.
- A crossover has two switches, one lever and one control point. "One per switch" then over-counts.
- "Control points grow geometrically" means "with track geometry". "Geometrically" reads as "exponentially".
- Ramification: derived CP membership (#16) and the design-block idea in ontology §10 need the right
  unit. The unit is the set of appliances between opposing controlled signals, not the switch.

### F5. Chronology in ontology §1–§3a is reversed in three places (S2, B3, recall)

- §2 lists the mechanical interlocking tower as a change that came after the control point. Towers
  date from the 1870s. CTC dates from 1927.
- §3a lists ABS/APB as a later, lighter-era consolidation. ABS and APB came before CTC. CTC was
  laid over them.
- "Control point" is used for the 1930s. The era term was "field station" or "controlled location".
- "TowerMaster" is not a railroad title. Use "operator", "towerman" or "leverman".
- "High-frequency track overlays, radio and GPS" mixes detection, code-line transport and PTC.
- Ramification: §3a's argument that Luchessa is "prototypically correct" rests on this history.
  The conclusion (keep three CPs, one field unit) can stand as a design decision. It should not be
  labelled as proven by prototype history. §8 already says the prototype would not have done it.

### F6. Code-line controls and indications are labelled "VITAL" (S1, B1, recall + README)

Glossary §1.1 "Vital Circuit / Command", Primer §10 tables.

- On the prototype the code line is non-vital. All vital logic is in the field. The FieldUnit README
  says the same: the office sends a request and the field decides.
- The docs mean "subject to interlocking checks" versus "not checked". That is a different property.
- `1NWK` is "VITAL" and `1OOK` is "NON-VITAL" although one is derived from the other.
- Ramification: a designer can read the tables as a requirement for integrity on the transport.
  Proposed terms: "interlocked function" and "auxiliary function". Counts for `VITAL`: FU 217, SUB 48
  (most are the legitimate sense; the code-line sense needs a targeted search).

### F7. "Interlocking Plant" spans locations; "Interlocking Limits" forbids it (S1, B1, logic)

- Glossary §1.2: interlocking limits are bounded by the opposing home signals of a control point.
- Ontology §6: `Interlocking Plant 1:N Control Point`, "a plant may span several locations".
- Glossary §1.1 defines Interlocking Plant three ways in one entry: a vital engine, the physical
  track, and a C++ class. §1.2 defines "Plant" again as physical hardware only.
- Recall: in rule terms a CTC control point is not an "interlocking" (49 CFR 236 and the rulebooks
  treat interlocking and traffic control as separate systems), although the field circuits are the same kind.
- Ramification: `InterlockingPlant` is the class name, the schema name and the MQTT key. The project
  needs a stated project meaning ("the set of control points one field unit solves together") that
  is marked as a FieldUnit term, not a prototype term.

---

## Tier 2: wrong facts or wrong words with wide reach

### F8. Model and form numbers name the wrong things (S2, B2, checked in part)

One desk is called "Model 503", "Type 506", "Form 506", "506A", "US&S506" and "US&S cTc". 504/506/514
are code systems, not consoles. No source in the repos supports "Model 503" as a machine. Ontology §6a
assigns the column budget to "the machine type (`US&S506`)" and the function budget to "the codeline
(506A)", so one number names two owners. Counts: "Model 503" FU 9, SUB 4.

### F9. Etymologies that are wrong, and one that inverts the meaning (S2, B2, recall)

- "`S` was reserved for Signal" (Glossary §2.1, Primer §3). In the docs' own tokens the signal letter
  is `G` (`NGS`, `SGK`). `S` is Stick.
- "`S` suffix = Send" (How-to 01). The glossary says `NWSR` is the Normal Switch Stick Relay. The `S` is Stick.
- "`K` = Kontrol" (How-to 01). `K` is the indication letter. The gloss attaches the word "control" to
  the indication side.
- "In railroad telegraphy" has no support.
- "OS = On-Sheet / Occupied Section" (Tutorial 1). OS is "on sheet". "Occupied Section" is a backronym.

### F10. `HS` means two opposite things (S2, B1, logic)

Glossary §3.3: `HSR` picks up when the dispatcher grants authority. Primer §10.1: control `2HS` is
"Force Signal 2 Stop". Ontology §3: `HS` is "you must be at stop". The same letters mean authority
in the field and stop on the line.

### F11. Derail NORMAL is defined as the non-derailing position (S2, B1, recall)

Glossary §1.3, Primer §5, How-to 05 "locked". On the prototype the normal position of a derail is the
derailing position. The glossary's own "fail-safe rest is REVERSE" shows the inversion. How-to 05 §7
calls the prototype polarity a legacy mistake. This is a decision to keep or reverse, and it reaches
the API, the plant JSON and the compiler.

### F12. "Block", "island" and "track circuit" are used as one word (S2, B2, recall)

- A block is track between signals. A track circuit is a detection section. The docs say "Approach
  Block 1SA", "Exit Block", "detection block".
- "Island" is the grade-crossing term. The switch section is the OS section or detector section.
  "island" FU 41.
- `1NA` is an "approach" circuit by name and an "Exit Block" in Tutorial 1.
- `Route::approaching(tc)` takes the block in advance of the signal. Approach and advance are
  opposites. `approaching(` FU 21.

### F13. "Indication" and "aspect" (S2, B1, logic)

- "Indication" is both the rulebook meaning of a signal and a field-to-office code. Both uses are
  correct. The glossary must give them two entries with qualifiers ("signal indication", "office indication").
- Glossary §1.3 defines aspect as the appearance of a head. §4 defines it as the appearance of a
  signal. The second is right. Code uses `Aspect::GREEN` per head (FU 214).
- "Aspect Ceiling" is defined as an indication. The design doc says "indication ceiling".

### F14. Correspondence relays (S2, B1, recall)

- `NWCR`/`RWCR` are defined as point detection (the prototype's switch repeater). Correspondence
  means position agrees with the control.
- `KR` is "NWCR or RWCR" in Glossary §3.2 and "(command and position)" in Primer §8.2.
- `ERS` has no cited source, and by the docs' own formula it would be `ERSR`.
- Option: keep the names and mark them as FieldUnit dialect in the glossary. `NWCR|RWCR` FU 37.

### F15. Rule numbers are attributed to the wrong book and era (S2, B2, recall)

251/261 and D-151/D-152 are Standard Code numbers. The design doc presents them under GCOR, which
dates from 1985. The SPCoast title block says 1942–1985. The glossary's Rule 262 and D-152 texts are
unverified. The rules sit unformatted under "Geographic and Physical Terms".

### F16. Signal and mast names follow four schemes (S2, B1, logic)

`2R/2LA/2LB` (A and B are separate masts), `2NAB` (A and B are heads on one mast), `784EAB`, and
`2Nab`/`S2NAB`. The compiler regex `^\d+[NSEW][A-E]+$` fixes one. The glossary defines none.
Track circuit names (`1SA`, `1NAT`, `2NAA`, `780SA`) have no rule either.

### F17. "cTc" on a US&S machine (S3 or S2, B1, low confidence)

Recall: "cTc" was the GRS styling; US&S sold "Union" C.T.C. Hobby sources (rrsignal) also write
"506 cTc". 419 occurrences including `cTcMachine.h`. Check one US&S primary document before any action.

---

## Tier 3: local errors

| ID | Where | Finding | Conf. |
|---|---|---|---|
| F18 | Primer §9.1 | The narrative sets switch 1 Normal and signal 2 Right. The packet shows `(1NWS)`, `(1RWS)`, `(2SGS)`, `(2NGS)`, all unasserted. "Both unasserted = leave alone" is not how a lever position is sent. | logic |
| F19 | How-to 03, README | Title says dual-control. Content is hand-throw with electric lock. They are different appliances. `WLR` is the motor lock relay in the glossary and the lock solenoid here. `WAK` is undefined. A door contact is declared with `addTrackCircuit`. | logic |
| F20 | How-to 04 §4 | B&O CPL marker meanings are wrong (2 o'clock medium, 4 o'clock limited, 6 o'clock slow). "Rule 290A" and "Cab Speed 281A" are unverified. "NORAC" is listed as a railroad. | recall |
| F21 | Tutorial 3 §5 | NYC Slow Approach and Restricting have the same aspect. | logic |
| F22 | Primer §14 | A quoted "operating rule" for the maintainer call has no source. The lamp is described as a call to train crews. | recall |
| F23 | Primer §7 | ASR "drops when approach is occupied" contradicts Glossary §3.4 "drops when a signal clears". Timer is 180 s, "3–5 m" and "5 minutes" in three places. Time locking is shown as a phase of approach locking. | logic |
| F24 | Primer §9.6 | "Later-era electronic control desks" describes relay machines. Code cycle is "1.8–2.2 s" here and "4 s" in §9.8. | logic |
| F25 | Glossary §2.1, Primer §3 | "Switches are ALWAYS odd… even in complex terminal interlockings" overstates a US&S CTC panel habit. | recall |
| F26 | Glossary §2.2 | Front contact is called a "neutral contact". Back contact "evaluates to `!true`". | recall |
| F27 | Glossary §1.2, §4 | "Territory / Subdivision" as synonyms. "Slotting" is British usage. | recall |
| F28 | Tutorial 1, README, Glossary | Christopher is MP 77.8 and MP 81. Gilroy is MP 77. | logic |
| F29 | Primer Act VI | Book title: Chubb's is the *Railroader's C/MRI Applications Handbook*. `DOOR`/`POR` reused for I2C faults. | recall |
| F30 | FU README | 1927 "two-wire CodeLine": the first installation was not a two-wire time code; that came later (US&S). | checked in part |
| F31 | Tutorials, How-to 01–04 | Code samples use `ControlPoint` and `CodeLineCodec.map…`. `src/` has `InterlockingPlant` only. | checked |
| F32 | Glossary §1.4 (uncommitted) | Reads as a pasted summary: "Type 506 machine", "TOLs", "on the layout". No sources. | logic |

---

## STE findings (ASD-STE100)

The FieldUnit README says only `CONTROL_POINT_ARCHITECTURE.md` is in STE. The other documents are not.

1. **One word, one meaning** is the main failure, and it is the same failure as Tiers 1–2.
   Synonym sets found:
   - bungalow, house, MAIN HOUSE, instrument case, relay house, shelter
   - office, desk, machine, console, panel, cTc machine
   - control, command, demand, request
   - token, mnemonic, bit, step, function
   - station, line station, field station, controlled point, control point, CP, plant, interlocking, junction
   - Field Unit, field unit, FieldUnit, field controller, Control Point Engine
   - mast, signal, face, head
   - territory, subdivision, corridor, layout
   Homonyms: indication, plant, station, clear, normal, approach, lock.
2. **One definition, one place.** The glossary defines Bungalow, Aspect, Indication, OS, CodeLine
   Interface and Device Interface twice each, with different words.
3. **Structure.** "Three-Tier Taxonomy" has eight entries. The README says four tiers. Tutorial 3 has
   a different "four-tier model".
4. **Register.** The primer is narrative ("slams down", "nightmare", "Secret 1", "citizens"). The
   ontology has "magic pixie dust" and "spiders and rattlesnakes". The design doc has "steel" and "toys".
   STE does not allow these. Decision needed: STE for glossary, ontology and design doc; a looser
   teaching register for primer and tutorials, with glossary terms used exactly.
5. **Prototype and model mixed.** Definitions join a prototype fact and a model workaround in one
   sentence (Fouling Point with optical sensors; Bungalow with "field computers"). Mark each entry
   Prototype, FieldUnit, or Both.
6. **Sentence form.** Long noun clusters ("addressable supervisory unit on the CodeLine"), slash
   compounds as terms ("Territory / Subdivision", "Vital Circuit / Command"), bold used for emphasis
   in most paragraphs of the ontology.

---

## Iteration 1 (2026-10-01): decisions and refinements

### Settled

| ID | Decision |
|---|---|
| F1 | rrsignal is correct. 506/506A: 16 steps (1+7+7+1), 7 controls, 7 indications, 35 stations. The glossary's 15/20/32 and the 4-bit address come from the model, not from history. |
| F3 | **Control Point**: the location of controlled signals. **Field station**: the addressable unit on a code line. **Controlled point**: retired as a concept; one synonym line under Control Point. Ontology §6 is wrong where it has `Control Point 1:N controlled point` and a separate "Station". |
| F4 | A control point is defined by its controlled signals. Signals control movement; a switch cannot tell a train anything. |
| F5 | Ontology chronology is reversed. Correct it. |
| F6 | "Vital" is a property of a function inside the field unit. It is not a property of a code-line control or indication. Remove the label from the code-line tables. |
| F8–F13, F16 | Agreed as written (see F8 refinement below). |
| F15 | Do not mix GCOR with the Standard Code era. |
| STE | Glossary, ontology and design doc are held to STE: no opinion, no decoration. Primer, tutorials and how-tos must be correct and use glossary terms exactly; they keep a teaching voice. |

### Refined

**F2: the total is settled; the step assignment is not.**

- The two summaries supplied in iteration disagree with each other and with the ontology:
  - Controls summary: the switch takes **one** step (long = Reverse, short = Normal). Ontology §3
    and the `PanelSwitch` symbol (`NWS`, `RWS`) say two.
  - Indications summary: switch 2 and signal 3 leave two steps. Its example gives both to approach
    sections. That leaves no step for the OS section or the maintainer call.
- Neither summary could be confirmed. rrsignal gives totals only. The jbritton page has no step
  content. ctcparts.com could not be reached. The GRS Type K manuals do not cover it.
- What stands: 7 + 7, and track indications compete for the seven. This explains why 506 model
  boards showed little except OS lamps.
- Ramifications:
  1. **A token is not a step.** FieldUnit sends `NWS` and `RWS`. A 506 line may send one step. The
     capacity check must count steps through a mapping. It cannot count tokens or symbol pins.
  2. **The step assignment is data for each field station** (a code chart). It is not a constant
     for each appliance type. "A signal is always three" becomes a default in the code-line
     definition.
  3. The ontology's "exactly 7 of 7" table and the "panel symbols already encode the budget"
     cross-check are withdrawn until a chart is found.
  4. Track lamps on a desk column are bounded by the indication steps that remain. That is a second
     capacity check.

**F8: two numbers, two owners.** The jbritton page states that the US&S desktop machines were the
"500 series". So "503" can be a machine model and "506" is the code system. Proposed terms:
"US&S 500-series machine" for the desk, "506 time code" for the line. "Type 506 machine" and
"`US&S506` machine type" are wrong. "Model 503" needs one source.

**F14: `ERS`.** Per the iteration note, AREMA practice calls this a track stick relay (TSR) or a
directional stick relay (SR, ESR, WSR). So ERS is a FieldUnit name for a function, and the glossary
already has a separate `ESR`/`WSR` entry that describes it as APB only. Proposed: one entry, "Engine
return stick (FieldUnit name); AREMA: track stick or directional stick relay", with the manual part
cited. No code rename.

**F17: naming the system.** Three statements are now on the table:

- GRS developed the system (confirmed) and styled it "cTc" (recall).
- "Traffic Control System (TCS)" is the ICC/FRA regulatory term; the jbritton page says the PRR's
  CTC "qualified as a TCS system per ICC and FRA regulations". It is not shown to be a US&S product name.
- US&S marketed "Union" Centralized Traffic Control (search result, not read at source).

All three agree on one point: "US&S cTc" joins one maker's styling to the other maker's machine.

### Still open

1. **F17**: write "CTC machine" (generic) in prose and keep `cTcMachine` as a code name with a
   glossary note, or rename the class (295 lines in FieldUnit, 124 here)?
2. **F7**: add Interlocking, Interlocking Limits, Control Point limits, CTC limits and Yard Limits
   as separate entries. Then state what `InterlockingPlant` means in the project. Proposed: "the set
   of control points that one field unit solves together; a FieldUnit term".
3. **F11**: derail polarity. The finding is agreed. Is the reversal wanted, or is the current
   polarity kept and marked as a FieldUnit convention?
4. **F2**: who finds the code chart, and where (SP or US&S drawings, a 506 service manual)?

---

## Iteration 2 (2026-10-01): decisions and refinements

### Settled

| ID | Decision |
|---|---|
| F2 | Stop looking for a code chart. The ontology states 7 + 7 as fact and shows step lists as **illustrative**, with their source and its standing (first-hand, hearsay, summary). "Exactly" and "always" are removed. Spike S1 is dropped. |
| F8 | No "503". US&S 500-series code systems carry even numbers. "Model 503" is removed from both repos (FU 9 lines, SUB 4). |
| F11 | Reverse the derail polarity now. See the change list below. |
| F17 | Prose says "CTC machine". `cTcMachine` stays as a code name with a glossary note. Glossary: "cTc" is the GRS trademark; "TCS" is the generic and regulatory name; "CTC" is the common word. |
| F7 | Definitions below. |

### F2 refined: are tokens steps?

Switch controls: two steps, one each for Normal and Reverse; neither asserted means "do not move".
This agrees with `NWS`/`RWS`, and with Primer §9.1 (which makes F18 smaller: the packet is legal, but
it still does not match the lever positions in its own narrative).

The indication list supplied in iteration (JMRI developers list, hearsay) is:

| Step | Function |
|---|---|
| 1 | line check and lockout |
| 2–8 | station selection |
| 9, 11 | switch Normal, Reverse; both short = not in correspondence |
| 10 | OS track |
| 12 | approach track |
| 13, 15 | signal Left, Right; both short = Stop; **both long = time release running** |
| 14 | commercial power |
| 16 | delivery |

Three consequences:

1. **On the indication side a token is not a step.** FieldUnit has three signal indication tokens
   (`NGK`, `SGK`, `TEK`) and `PanelSignal` has three indication pins. This list has two steps, and
   `TEK` is the combination "both long". So the code-line definition needs an encoding, not only a count.
2. This list has no maintainer-call indication and no call-on. The ontology table had both. It has
   power-off, which the ontology table did not.
3. One OS and one approach track are all that fit. This supports the statement that 506 model boards
   showed little except OS lamps.

So spike S2 stays, with a smaller question: where does the encoding from tokens to steps live, and
what does the capacity check count?

### F8 refined: what to call the desk and the line

The series list supplied in iteration names 502, 504, 506, 510 and 516. rrsignal has a page for
514. The glossary's "Form 508" stays unsourced. Proposed wording until a source says otherwise:

- the desk: "the SPCoast CTC machine (US&S style)"; no model number;
- the line: "US&S 506 time code";
- the family: "US&S 500-series time code systems"; no list of members in the glossary.

### F7 settled: interlocking terms

- **Interlocking**: the arrangement that forces switch and signal movements to follow each other in
  a safe sequence. First a mechanical machine (levers, locking bed, pipe and wire). Later relays.
- **Interlocking limits**: the track between the opposing home signals of an interlocking.
- **Interlocking plant**: all the control points and appliances inside one set of interlocking limits.
- **CTC (traffic control system)**: adds to interlocking the code line, field stations, the field
  unit, controls and indications, and a remote dispatcher.
- **Analogy to state once in the glossary**: the CTC machine is to the field unit as the tower
  operator is to the interlocking frame.
- Also add: Control Point limits, CTC limits, Yard Limits.
- Note: the iteration text said "controlled points within its limits". Under F3 this reads
  "control points".
- Still to state: one field unit for each interlocking plant (assumed from ontology §6).

### F11 refined: the reversal removes the inversion

Prototype polarity: derail NORMAL = derailing (on the rail). Derail REVERSE = clear.

Then a dependent derail is in the **same** position as its switch: switch Normal with derail Normal,
switch Reverse with derail Reverse. "Inverse-slaved" was a product of the wrong vocabulary. The
dependent derail becomes a ganged end, the same shape as a crossover end, and every appliance rests
in NORMAL.

Change list (found by search, not yet changed):

| Where | Change |
|---|---|
| FieldUnit `src/Switch.h` | `configureAsDerail()` rests in NORMAL. Remove `inversePosition` from `pairDependentDerail`, `inCorrespondence` and the throw path. Fix the header comment. `DEPENDENT_DERAIL` may reduce to the crossover pairing rule. |
| FieldUnit `src/InterlockingPlant.h` | `addDerail` comments. |
| FieldUnit `tests/test_derail.cpp` (198 lines), `tests/test_corporal_sketch.cpp` | Expected positions. |
| FieldUnit `examples/CP_Corporal/CP_Corporal.ino` | Already has prototype polarity in a comment ("NORMAL: derail is derailing") and still uses `addSwitch("5")` with a demand rewrite. Move to `addDerail`; routes through derail 5 require REVERSE (they already say `SW5=R`). |
| FieldUnit `examples/spcoast_ctc` | Comment only (795D has no lever). |
| FieldUnit docs | Glossary, primer §5, how-to 05 (§1, §3 table, §7), `CONTROL_POINT_ARCHITECTURE.md`, AGENTS, CHANGELOG. How-to 05 §7 now says the opposite of what is true. |
| Subdivision `tools/plant_graph/routes.py` | The derail's through path uses pin `N` (lines 963–967, 1018–1022). The route requirement for an independent derail becomes REVERSE. |
| `Railroad.kicad_sym` (`Switch_Powered_Derail`, `_TC`) | The through pin is named `N`. Rename it, or keep the pin and change the compiler's reading. The library is not in git; schematics that place the symbol follow the pin name. |
| Subdivision projection, plant host, schema, fixtures | `fieldunit_projection.py` names only the master for dependents, so it is likely unchanged. `Luchessa.json` and the frozen goldens need a regenerate-and-diff. The `--test` self-test asserts on 795D. |
| Desk | An independent derail's lever and lamps swap meaning. No independent derail is on the SPCoast desk today except Corporal's 5 (legacy profile). |

Wire tokens (`5NWS`, `5RWK`) keep their names. Their meaning for a derail flips. Any saved or
retained MQTT indication for a derail is stale after the change.

### Still open

1. F11: the symbol pin. Rename `N` on the derail symbols, or keep it and reinterpret?
2. F7: confirm one field unit for each interlocking plant.

---

## Iteration 3 (2026-10-01): roles, facets, and the derail change

### The model has three roles and one seam

The step, the station address, the budget and the token-to-step encoding are all properties of
**one code line type** (US&S 506). Another code line type (another era, another maker, a model
invention, MQTT) has its own. The two step lists supplied in iterations 1 and 2 can both be
well-intentioned and still rest on different practices.

So the vocabulary has two layers:

| Layer | Terms | Stable across code line types |
|---|---|---|
| Roles | **CTC machine** (office), **code line**, **field unit** | yes |
| Interface on the seam | **control**, **indication**, as named functions (AAR tokens) | yes |
| Code line type | step, cycle, station address, **field station**, capacity, encoding, timing | no; each type defines its own |

- A glass dispatcher display, a vintage 506 machine, a rebuilt desk with an ESP32, and a simulator
  with automated crews are all the CTC machine role.
- A layout picks one implementation for each role. The compiler must accept that choice and must
  not assume a 506.
- **Field station is a term of the code line type.** On a 506 line a plant can answer as several
  field stations. On an MQTT line it answers as one.
- Spike S2 becomes: define the contract of a code line type (addressing, capacity, encoding). The
  capacity check is a method of the type. The MQTT type has no limit.
- Glossary consequence: every 506 fact carries the scope tag "US&S 506 code line". It does not sit
  in a general entry.

### "Control point" is a functional term

A control point is a place where control can be asserted over a train. The words describe the
function. They are not, first, a proper name for a place on a map. ("CP Luchessa" is the name of
one instance.)

With functional terms, the questions "is a control point an interlocking?" and "is an interlocking a
control point?" do not arise, because the terms answer different questions about the same place:

| Facet | Question | Term |
|---|---|---|
| Function | What is done here? | control point |
| Mechanism | How is safety enforced? | interlocking |
| Extent | Where does it start and stop? | interlocking limits, CTC limits |
| Addressing | How does the office reach it? | field station (per code line type) |
| Logic | What solves it? | field unit |
| Enclosure | Where is the equipment? | bungalow |

Proposal: the ontology rewrite uses this table as its structure, one section for each facet. This
replaces the era narrative as the organizing idea. The era material becomes notes under Addressing.

The same facets for a tower interlocking and for a dispatcher-controlled point (iteration 4):

Rev 2 of the table (iteration 5). The rows marked ► carry the difference in behavior.

| Facet | Tower interlocking | CTC control point |
|---|---|---|
| Function | control of train movement by signal | the same |
| Who gives the intent | tower operator, at the site | dispatcher, at a distance |
| Where the intent is given | the levers of the interlocking machine | the levers of the CTC machine |
| ► What an unsafe lever does | It does not move. The locking bed holds it. | It moves freely. Nothing at the office holds it. |
| ► When the intent takes effect | when the lever moves | when the dispatcher presses CODE and the field unit accepts the control |
| ► How a refusal is known | at once, in the hand: the lever is locked | later, by its absence: no indication arrives that agrees with the lever |
| ► What a lever position means | the state of the plant (the lever could not be there otherwise) | the intent of the dispatcher only |
| ► What tells the truth | the lever, then lamps and the window | the indication only |
| What enforces safety | the locking of the machine (mechanical bed, later relays) | the field unit (relay or software logic) |
| Where safety is enforced | in the tower, under the operator's hands | in the field, away from the operator |
| Link to the appliances | pipe and wire, or direct wires | code line, then local wires |
| Addressing | none; one machine, one plant | field station (per code line type) |
| Extent | interlocking limits | control point limits inside CTC limits |
| Enclosure | tower | bungalow |

**The one-sentence form.** The code line, the field station and the field unit together stand in
for the mechanical locking bed: they do at a distance, and after the fact, what the bed does in the
operator's hand.

What follows from the ► rows:

- **Control and indication are two terms because the lever stopped telling the truth.** In a tower
  one object (the lever) holds intent and state together. CTC separates them, so it needs one word
  for each. This is the origin of "controls as demands, indications as truth".
- **Correspondence is a CTC concept at the office.** "Out of correspondence" means the lever and
  the indication disagree. A mechanical frame has no such state at the lever. (Correspondence
  between a switch machine and its control exists in both; that is the field meaning. The glossary
  must keep the two meanings apart: office correspondence and switch correspondence. See F14.)
- **The field unit refuses by doing nothing.** There is no refusal message, because the locking bed
  it replaces sent none. The lever that will not move becomes the indication that does not change.
- **The CODE button has no tower equivalent.** It exists because the lever is free. It marks the
  moment when intent becomes a request.
- **A CTC machine must never send on power-up** (Primer §9.4) for the same reason: a free lever
  that was moved while the machine was dark is intent that nobody has confirmed.
- **Requirement (accepted in iteration 5):** any implementation of the CTC machine role must let the
  operator state an unsafe intent. Dispatchers do this every day; the field refuses. A CTC machine that blocks the lever from its own copy of the plant state has moved
  the locking bed to the office, where it is not vital.

The analogy stays: the CTC machine is to the field unit as the tower operator is to the
interlocking frame. History agrees with it: the first CTC machine was an interlocking frame cut in
two, with one half moved away. The FieldUnit README already uses this picture. It stays; only its
"two-wire telegraph line" detail needs the F30 correction.

Accepted in iteration 5: the table, the facet structure for the ontology, and the requirement above.
"Host" was rejected in iteration 6; the term is "field processor".

**Field unit and field station.**

- **Field unit**: the logic that solves one interlocking plant. It reads the appliances, enforces
  the locking, drives the switches and signals, and answers the code line. It has behavior.
- **Field station**: one address on a code line, and the set of controls and indications carried
  under that address. It has no behavior. It is how one code line type lets the office reach a field unit.
- The difference shows when a plant needs more functions than one address carries. On a 506 line
  the plant then answers at several field stations (Luchessa: three), and one field unit is behind
  all of them. On an MQTT line one topic carries everything, so there is one field station.
- Prototype note: on a 506 installation each field station was also a physical line coding unit.
  In this project it is an address only.

Whether the lower-case phrase "controlled point" stays as plain English ("a point that is
controlled") is a style choice. As a defined term it stays retired (F3).

### Field unit, plant, and field processor

(Rewritten in iteration 6. "Host" is rejected: C/MRI and JMRI already use it with other meanings.
"Node" is rejected for the same reason. The term is **field processor**.)

| Term | What it is | Exists when |
|---|---|---|
| **interlocking plant** | The thing that is controlled: track, appliances, routes, limits. A design. | It is drawn. No computer is needed. |
| **field unit** | A running copy of the logic for one plant. | A field processor runs it. |
| **field station** | An address at which a field unit answers on a code line. | A code line type assigns it. |
| **field processor** | The microcontroller, computer or process that runs field units. | It is installed or started. |

Why plant and field unit are two terms although they are 1 : 1 in one deployment: the plant is the
design and the field unit is a running copy of it. One plant can have more than one running copy
at different times or places: the unit in the bungalow, and a virtual copy in a simulator that
tests a CTC machine. The KiCad drawing and the plant JSON describe the plant. `InterlockingPlant`
in C++ is a field unit loaded with that description, which is why the two feel like one.

| Relation | Cardinality | Depends on |
|---|---|---|
| interlocking plant to field unit | 1 : 1 in one deployment | nothing |
| field unit to field station | 1 : N | the code line type (506: N can exceed 1; MQTT: N = 1) |
| field processor to field unit | 1 : N | deployment only |

One picture, nested (the owner's form, iteration 6):

```text
CTC machine
   |
   |  code line   (type: US&S 506, MQTT, ...)
   v
field processor                                   runs 1..N field units
  +-- field unit  --solves-->  interlocking plant "Luchessa"
        |
        +-- answers at field station(s)
        |       506 line:   Luchessa, Gilroy, Carnadero   (one for each control point)
        |       MQTT line:  Luchessa
        |
        +-- device interface --> IOBus (C/MRI, I2C, ...) --> devices (the appliances of the plant)
```

- The field processor is not "for" a plant. It runs field units, and each field unit is for one plant.
- A microcontroller in a bungalow is a field processor with one field unit. The virtual plant
  simulator is a field processor with seven.
- Replacement list addition: `runtime/plant_host`, "plant host" and "Centralized Hosts" become
  "field processor".

### Six terms from plant to field unit (iteration 7, accepted)

This table replaces the four-term table above where they differ. "Interlocking plant" now means
only the real thing. Its description is the "interlocking model".

| # | Thing | Term | Luchessa example | Exists today |
|---|---|---|---|---|
| 0 | The real track, switches and signals | **interlocking plant** | Luchessa: SP Coast Line, about MP 78.3 to 79.9 (switches 783, 795, 799; signal 784) | on the layout |
| 1 | The generalized relay / AAR / AREMA logic | **interlocking logic** | C++ class `Interlocking` | yes, named `InterlockingPlant` |
| 2 | The data that describes one plant | **interlocking model** | `Luchessa.kicad_sch` compiled to `generated/Luchessa.json`, id `spcoast.Luchessa` | yes |
| 3 | The logic combined with one model | **interlocking application** | `Luchessa.ino` (generated sketch) or a native build | not as a file; the virtual plant program builds it at start |
| 4 | A computer that can execute (3) | **field processor** | a cpNode or ESP32 in the Luchessa bungalow; the Mac that runs the simulator | simulator only |
| 5 | (3) running on (4) | **field unit** | the unit that answers at `ctc/SPCoast/codeline/Luchessa/...` | virtual only |

field unit = (interlocking logic + interlocking model) on a field processor
= interlocking application on a field processor

- "Application" is the signalling industry's word for generic logic configured with the data of one
  site (recall; needs one citation, spike S6).
- The tooling goal reads: schematics to interlocking model, model to interlocking application,
  application loaded on a field processor gives a field unit.
- The office side has the same shape: desk logic (`cTcMachine`) with a desk model is a desk
  application; that application on a processor is a CTC machine.
- **Planned rename** (own PR, after the glossary rewrite): class `InterlockingPlant` to
  `Interlocking`. The same PR finishes the earlier rename (17 lines still say `ControlPoint`; the
  instance variable is still `cp` in about 540 lines). No compatibility alias.
- The schema name `InterlockingPlantModel` stays: it is a model of a plant.
- Where the example column says "Luchessa" six times, the name is the same on purpose. One name
  runs from the plant to the field unit; only the term in front of it changes.

### F11 done: derail polarity follows the prototype

Changed on branch `fix/derail-prototype-polarity` in both repos. Nothing is committed.

| Repo | Change | Verified |
|---|---|---|
| FieldUnit | `Switch.h`: derails rest in NORMAL; a dependent derail takes its switch's position; `inversePosition` removed. `InterlockingPlant.h` comments. `test_derail.cpp` expectations. Glossary, primer §5, how-to 05, architecture spec, AGENTS, CHANGELOG. | all 16 native tests pass |
| Subdivision | `routes.py`, `model.py`, `compiler.py`: the derail's through port is `R`; a route through a derail requires REVERSE. One new unit test. Derail lines in the Luchessa model golden and the deferred sidecar. `portable-interlocking-plant-model.md` line 110. | 123 unit tests, smoke script, `spcoast_virtual_plant --test` (6 scenarios) pass |

Findings from the change:

- `CP_Corporal.ino` already had prototype polarity (derail 5 follows switch 1). It did not change,
  except one comment. How-to 05 §7 had called that polarity a mistake; that text is corrected.
- The runtime file `generated/Luchessa.json` did not change. The projection names only the master
  switch for a dependent derail.
- A regenerated model golden differs from the frozen one in title-block fields too (company, date,
  era, railroad are empty in the golden). Only the derail lines were updated. The drift is a
  separate item.
- No unit test compared the route alignment of a derail before this change. The golden was not a gate.

Done in iteration 4:

- **KiCad pin rename** (`N` to `R` on pin 2 of `Switch_Powered_Derail` and `_TC`): 2 pins in
  `Railroad.kicad_sym`, 1 in each of the 7 SPCoast plant schematics. `.history` copies were not
  touched. `make all` passes for Luchessa; smoke script and 123 unit tests pass.
- `make all` fails for the other six plant projects at `<Project>-field.json` with
  `ValueError: The final anchor must equal the layout width` (`tools/plant_graph/layout.py:65`).
  The compiler on `main` fails the same way on Corporal, so this is not from the derail change. It
  is a separate defect.

Not done (derail commits are on hold):

- `arduino-cli compile` of the two example sketches.
- Portable model schema version: port id `derail:<id>:N` became `derail:<id>:R` and the alignment
  position changed, with the schema still at v1.

---

## What to do next (order matters)

Changes from the provisional plan: S1 is dropped, S4 is replaced by the F11 change (step 1a, first),
and "Model 503" joins the replacement table as a removal.

### Step 1a. Derail polarity (code change, two PRs)

Code and tests are changed on branch `fix/derail-prototype-polarity` in both repos (iteration 3).
Remaining:

1. Close KiCad, run the pin rename with `--write`, then `make all` in each SPCoast project.
2. `arduino-cli compile` of `CP_Corporal` and `spcoast_ctc`.
3. Commit. In Subdivision the golden and sidecar changes go in their own commit, per AGENTS.md.
4. Decide whether the port and position change needs a portable model schema version.

### Steps 0 to 6

### Step 0. Freeze

- Do not commit Glossary §1.4 as pasted. Rewrite it from sources in step 2.
- Mark ontology rev 4 "superseded by vocabulary review" at the top.

### Step 1. Spikes (answer a question; change no shipped file)

| Spike | Question | Output | Blocks |
|---|---|---|---|
| S1 code chart | Dropped in iteration 2. Step lists are illustrative. | | |
| S2 code line type | What is the contract of a code line type: addressing (field stations), capacity, and the encoding from named functions to steps? The 506 type and the MQTT type are the two cases. | A short design note with two or three options. Not picked without review. | linker capacity check, `Codeline-USS506` symbol |
| S3 membership by signal | Can the plant compiler derive control point membership from opposing controlled signals (F4), which would retire the `CP` field (#16)? | Result on Luchessa and one legacy station | #16 |
| S4 derail polarity | Replaced by step 1a. The change list is in iteration 2. | | |
| S5 names | One grammar for mast, signal and track circuit names (F16), checked against `docs/reference/Chapter-02…1956.pdf` and the 1952 timetable | Grammar plus the list of names in both repos that fail it | glossary §2, compiler regex |
| S6 sources | One primary or first-hand source for each of: Model 503, US&S product name, ERS in the AREMA manual, rule 262 and D-152 text, maintainer-call use | A sources table for the glossary | glossary rewrite |

### Step 2. Rewrite the glossary first (STE)

It is the declared source of truth, so everything else follows it.

- One entry for each term, one place, alphabetical inside each section.
- Each entry carries a scope tag: Prototype, FieldUnit, or Both. Era where it matters.
- Synonyms appear as "See" lines only.
- Split the homonyms: signal indication / office indication; block / track circuit / OS section;
  plant (physical) / `InterlockingPlant` (project).
- Remove: 15/20/32 steps, Form 508/510, "Kontrol", "Send", "S reserved for Signal", "Occupied
  Section", vital code-line commands.
- Add: field station, code line, code chart, step, function, conditioning step, delivery step,
  the limits entries from F7, a sources section.

### Step 3. Rewrite the ontology as a delta on the new glossary (STE)

- Structure: one section for each facet (function, mechanism, extent, addressing, logic, enclosure),
  then roles and the seam, then cardinalities including field processor (iteration 6).
- §1: control point defined by signals. §2 and §3a: chronology corrected, or cut to what the model needs.
- §3: budget stated as 7 + 7 with the assignment marked open (S1).
- §6: cardinalities use Control Point, field station, field unit, code line, panel column only.
- §3a and §8: Luchessa stated as a design decision.
- Remove the pasted source list; cite rrsignal directly.

### Step 4. Replacements (after step 2 fixes the target words)

Mechanical, reviewed as one diff for each row:

| From | To | Where | Note |
|---|---|---|---|
| "Controlled Point", "Line Station", "controlled point" | "field station" or "Control Point" | docs in both repos (about 60 lines) | Not mechanical: each use must be read to choose. |
| `CONTROLLED_POINT` attribute | decided in S3 | Subdivision README, compiler | After S3. |
| "15-step" | "16-step" or removed | glossary, primer, READMEs, AGENTS | Primer §9.5.1 becomes "SPCoast desk display", marked as a model design. |
| "Model 503", "Type 506 machine", "Model 506", "`US&S506` machine" | "the SPCoast CTC machine (US&S style)" / "US&S 506 time code" | both repos | "503" is removed everywhere. |
| "cTc machine", "US&S cTc" in prose | "CTC machine" | docs in both repos | `cTcMachine` and other code names stay. |
| "Island Block", "island" | "OS section" | FieldUnit docs (41 lines) | Code comments too. |
| "Approach Block", "Exit Block", "detection block" | "approach track circuit", etc. | tutorials, how-tos | |
| "Aspect Ceiling" | "indication ceiling" | glossary | |
| "Kontrol", "Send", "On-Sheet / Occupied Section" | corrected text | how-to 01, tutorial 1 | |
| VITAL / NON-VITAL columns in code-line tables | "interlocked" / "auxiliary" | primer §10, glossary | Code untouched. |
| "GCOR" as the frame for 251/261 | Standard Code for the era; GCOR named as the modern equivalent | design doc §1, glossary | |

Code names (`approaching()`, `NWCR`, `Aspect::`, `cTcMachine`, derail polarity) are **not** in this
table. Each is an API change and needs its own decision, a deprecation path and a PR.

### Step 4a. Class rename (own PR in FieldUnit, then Subdivision)

`InterlockingPlant` to `Interlocking`; finish `ControlPoint` and `cp`; `runtime/plant_host` to the
field processor name. No compatibility alias. Gate: all native tests, unit tests, smoke script,
simulator self-test, `arduino-cli compile`.

### Step 5. Correctness pass on the teaching documents

Primer, tutorials, how-tos, FieldUnit README: fix F18–F31, use glossary terms exactly, keep the voice.
Tutorial and how-to code samples must compile against `InterlockingPlant` (F31); that is a functional gate.

### Step 5a. Defects found during the review (separate from vocabulary)

- `make all` fails for six plant projects in `tools/plant_graph/layout.py:65` (also on `main`).
- The frozen Luchessa model golden has empty title-block fields that the compiler now fills.
- The six plant project folders other than Luchessa are untracked in the SPCoast KiCad repo.

### Step 6. Guard

A term lint (script, run in CI for both repos) that fails on retired terms in the STE documents and
warns in the teaching documents. The retired list comes from the glossary's "See" lines, so the
list has one source.

---

## Spike results (2026-10-01)

Reports: `vocabulary-sources.md` (S6), `../adr/0001-code-line-type-contract.md` (S2), `spike-cp-membership.md` (S3).
`../adr/0003-name-grammar.md` (S5) is pending.

### Corrections to this review from the sources spike

| Finding | Correction |
|---|---|
| F29 | Chubb's title is *Railroader's C/MRI Application Handbook* (singular). The review had "Applications". |
| F9 | On the AAR abbreviation list `D` is not "distant". Do not gloss it so in the glossary. `TE` is not on the list. |
| F3 | The names are regional, but the definitions differ: GCOR "the location of absolute signals controlled by a control operator"; 49 CFR 236.782 "a location where signals and/or other functions of a traffic control system are controlled from the control machine"; NORAC "a station designated in the Timetable where signals are remotely controlled". |
| F11 | "Derail NORMAL = derailing" has a regulatory source for fixed hand derails only (49 CFR 218.109). No source was found for power derails. Label it "prototype convention (recall)" until one is found. The code change stands on the owner's decision. |
| F15 | "GCOR does not use 251/261" is supported for the 2010 edition only. NORAC still says "Rule 251". The PRR 1956/64 book gives the full text of 251, 261, 262, D-151, D-152 for one road. |
| F17 | No source found for "cTc" as a GRS trademark. US&S's own texts (1937, 1949) write "C.T.C.". No source for "TCS" as a US&S product name. The decision (write "CTC machine") is unaffected. |
| F8 | 506 and 514 are sourced. 502, 504, 508, 510, 516 and "503" are not. |
| F30 | First CTC: NYC, Stanley to Berwick, GRS, one-wire control are confirmed. "Toledo & Ohio Central" was not found in a source. |
| F22 | A 1959 article describes a "maintainer's call" control and lamp. Nothing found says train crews used it. |
| Iteration 6 | "Central instrument location (CIL)" was not found in any source. Do not put it in the glossary. |
| Iteration 7 | "Application" is sourced for Microlok II ("Application Logic Programming Guide"). The CENELEC wording is unconfirmed. |

### Open decision from the membership spike (closed by iteration 9)

By the F4 definition the drawn Luchessa is one control point with three houses, not three control
points. See `spike-cp-membership.md`. The owner decides: one control point with three field
stations, or three control points with signals still to be drawn.

---

## Orchestration status (2026-10-01, end of session)

Everything below is uncommitted on branch `fix/derail-prototype-polarity` in each repo.

| Plan step | State |
|---|---|
| 1a derail polarity | Code, tests, docs, KiCad pin rename done. `spcoast_ctc` and all four example sketches compile for ESP32 after forward declarations were added to `CP_Corporal`, `CP_Christopher` and `FieldUnit_Tracer`. Commit is on hold. |
| 1 spikes | S2 `../adr/0001-code-line-type-contract.md`, S3 `spike-cp-membership.md`, S5 `../adr/0003-name-grammar.md`, S6 `vocabulary-sources.md`. All four are proposals or reports. None is applied. |
| 2 glossary | Rewritten in STE (`FieldUnit/docs/GLOSSARY.md`). Reviewed; three corrections applied. |
| 3 ontology | Rev 5 written after iteration 10 (by facet). Awaiting the owner's review. |
| 4 replacements | Done in Subdivision `README.md`, `AGENTS.md`, `generated/README.md`. "desk" not replaced (not confirmed). |
| 4a class rename | **Not started.** Needs the derail change committed first. |
| 5 teaching documents | Primer, FieldUnit README, three tutorials, five how-tos corrected. Every tutorial and how-to code sample compiles (`-fsyntax-only`) against `src/`. `CTC_SUBDIVISION_AND_PLANT_DESIGN.md` rewritten in STE. |
| 6 term lint | **Not started.** The glossary section 11 table is its input. |

Correction to F31: only `ControlPoint` is gone. `CodeLineCodec` exists (an alias of `BitPackedCodec`) with its `map…` functions.

### Decisions waiting for the owner

1. Luchessa: one control point with three field stations, or three control points.
2. Is "desk" retired in favour of "CTC machine"?
3. The 13 questions in `../adr/0003-name-grammar.md` (applying it renames about 375 names).
4. The three owner questions in `../adr/0001-code-line-type-contract.md`.
5. Lift the commit hold, so the class rename can start.
6. Milepost of Christopher (77.8 or 81) and Corporal (83, or 86.4 per the 1952 timetable).
7. "7 controlled points" in AGENTS.md was changed to "7 interlockings". Confirm.

### Code findings from the agents (not vocabulary; not verified by the orchestrating session)

Safety logic:

- `Route::approaching()` has two jobs. It decides whether a cancelled signal starts time locking, and it
  lowers CLEAR to APPROACH when the circuit is occupied. Sketches pass it a circuit named "advance".
  If the entrance circuit is passed, an approaching train lowers its own signal.
- A route with no `approaching()` circuit has no time locking: a cancelled signal releases its switches at once.
- `evaluateEngineReturn` shows RESTRICTING with no check of the signal control or of time locking.
- Route evaluation does not check `HAND_LOCKED`. A signal can clear over a switch whose electric lock is released.
- A lock control does not check the switch position. With `BitPackedCodec`, a 0 bit means LOCK in every packet.
- `nycSpeed` gives SLOW_APPROACH and RESTRICTING the same aspect.

Code line:

- The simulator builds its token list from the interlocking model (all track circuits). `CtcStation::buildCodec()`
  builds its list from panel columns (lamped circuits only). Decode is positional. Whether the running pair agrees was not tested.
- The `WireCodec.h` header says decode accepts any order. The code is positional.
- `CtcStation` assumes one field station for each interlocking. The CTC machine has no output for `TEK`.
- `BitPackedCodec` maps one token to one bit and cannot express "both long = TEK".

Tooling:

- `routes.py:583` writes `<switch>T1` on the clear list and ignores the `TC` field.
- `make all` fails for six plant projects in `tools/plant_graph/layout.py:65`. Three of them (Corporal,
  Christopher, GilroyCalTrain) have no nets at all.
- Four parts used in the netlists are missing from `_PART_KIND`.
- `model.py` reads `CP` from the signal IRJ only. GilroyInterchange and Christopher write it on the mast.
- `RouteSignalingPolicy.evaluate` is a second run-time evaluator next to FieldUnit's.
- The mast regex is defined twice (`compiler.py:114`, `routes.py:29`).

Drawings:

- The CTC machine schematic has `PanelSignal 838`; Sargent's masts are 836.
- Sargent's `Corporal:2NA` names a circuit that Corporal does not have (`2NAT`).
- Lamp `773T1` has no interlocking-plant circuit of its own.
- The symbol library mixes Standard Code (251, 261) and GCOR-style (6.28, 6.13) rule numbers.

Naming in code (for the rename PR): "island" and "block" for track circuits, `aspectCeiling()`, "vital" on
code line decode, tokens called "steps" in `WireCodec.h`, three compass readings of LEFT/RIGHT, "AAR" comments
on FieldUnit names, `SignalIndication` struct name, `CtcMachine`/`OfficeUnit` aliases.

---

## Iteration 8 (2026-10-01): owner's answers after the orchestration

### Field station and Luchessa (closes the open decision from the membership spike)

- A field station is a concept of a 506-style code line. On such a line one field station is one
  bungalow: one `MAIN HOUSE` symbol. Its name is the `MAIN HOUSE` Value.
- Names are normalized (pattern to be picked, for example `CP <Name>`) and checked for duplicates. They are never invented.
- An interlocking model with no `MAIN HOUSE` symbol cannot use that code line style.
- Luchessa today has three main houses, each a 506-capable unit. The plan is to reduce it to one house later.
- So `CP Luchessa`, `CP Gilroy`, `CP Carnadero` are bungalows and field stations. By the F4 rule
  (controlled signals) the drawn Luchessa is one control point. To confirm with the owner: that the
  count "one control point" is accepted.
- The `CP` field on an appliance assigns it to a house. It is the grouping of functions into field stations.
- Field station is added to the six-term table as row 6 (glossary section 2.4).

### Code line type (now an ADR: `docs/adr/0001-code-line-type-contract.md`, status proposed)

| Question | Answer |
|---|---|
| One axis or two | Two: encoding and carrier. AAR tokens over MQTT; 506 over LocoNet; 506 over a relay box. |
| Encoding scope | For each field station on a code line (a code chart), not only for the type. |
| Drawn symbol | States the default. The generator must also produce a virtual or a 506 version from the same model. |
| Missing phase | The generator: it reads the model, executes policy, and emits the applications. |
| CODE button | The SPCoast CTC machine has one CODE for three columns, so it is not a true 506 machine. Options: emit each column in sequence, or use a larger encoding. Not picked. |
| Dropped function | Allowed. Info, or shown only with a verbose flag. |
| Addresses | Authored. Never allocated: a shifted allocation would put firmware out of step with the wire encoding. |
| `TEK` with `NGK` or `SGK` | Never valid. The codec treats it as an error. |
| Implementation limits | Checked by the KiCad compiler or the sketch generator. A run-time check is possible because FieldUnit can load a JSON model. |
| Where type definitions live | The `~/Dropbox/KiCad/Railroad/SPCoast` repo. |
| Still open | Option A, B or C. |

New scope, not yet discussed: local fascia-mounted devices and maintainer service modes (local
control of things that are not CTC-controlled but need a processor and I/O).

### Documents

- "Lever frame" wording in the README: accepted.
- Odd switch, even signal: a common convention that goes back to lever-and-pipe plants. Not "borrowed from US&S panels". Owner's knowledge; unverified.
- GRS names: code systems Type F, H, J, K; brands SyncroStep, SyncroScan; consoles NX, Traffic Master. Model 5 (5A to 5H) is the GRS switch machine family. Owner's knowledge; added to the primer.
- First CTC wiring: the "one wire to each switch" statement comes from one secondary account (ekeving.se). The README and glossary now say "one account describes".
- Time-locking lamp and out-of-correspondence alarm: these capabilities must not be lost. The primer describes them and marks them "planned in FieldUnit". Backlog: `cTcMachine` needs a `TEK` lamp output and an out-of-office-correspondence output.
- Christopher is about MP 81. MP 77.x is Gilroy (GilroyCalTrain, GilroyInterchange). Closed.
- Debt: the primer Act V and Tutorial 2 quote the legacy `CP_Corporal.ino`. When Corporal is cut over to KiCad they must be updated. Added as step 6 of the station cutover checklist in AGENTS.md.
- `Route::approaching()`: acknowledged; stays in the code backlog.

---

## Iteration 9 (2026-10-01): two corrections from the owner

### Control point: the definition was muddied in iteration 8

Owner: Luchessa is one interlocking. It has three `MAIN HOUSE` symbols, so it includes three control
points within its limits.

What went wrong: spike S3 turned F4 ("signals make a control point, a switch does not") into a
derivation rule (cut the track graph at signals) and called each piece a control point. Each piece is
an **interlocking**: the track between opposing controlled signals is the interlocking limits. The
orchestrating session then recorded "Luchessa is one control point" from that. That was an error.

Corrected model:

| Term | How it is known | Luchessa |
|---|---|---|
| interlocking | derived: the track between opposing controlled signals (spike Rule A) | one |
| control point | declared: one `MAIN HOUSE` symbol; its Value is the name | three: `CP Luchessa`, `CP Gilroy`, `CP Carnadero` |
| bungalow | the enclosure of one control point (the same symbol) | three |
| field station | per code line type: one for each control point on a 506-style encoding; one for each interlocking on AAR tokens | three, or one |
| control point of an appliance | drawn: the `CP` field | 15 values |

- F4 stands as a statement of function: controlled signals make a place a control point. It is not a rule for counting.
- The facet table holds: at `CP Gilroy` the function is control point, the enclosure is bungalow, the address is field station.
- Luchessa suits the virtual, MQTT and US&S 506 code lines, the last only with a workaround, because
  the CTC machine has one CODE button for three columns.
- Corrected in: glossary (control point, control point limits, interlocking limits, bungalow, field
  station, cardinality), design doc §5.1, ADR 0001 (context, D3), AGENTS.md, `spike-cp-membership.md`.
- This is the model the owner stated on 2026-09-28. Iteration 8's "MAIN HOUSE does not define a control point" is withdrawn.

### Authority: relay principles first, code second, legacy sketches last

Owner: FieldUnit was built from AAR first principles and relay logic. That work must not be lost by
treating old `.ino` sketches as a reference.

What went wrong: the agent briefs said "document what the code does" and "CP_Corporal.ino is the
reference for Act V". The glossary and primer rewrites then replaced relay circuits (HR/DR, ASR, ERS)
with descriptions of today's code, where the code is the weaker thing.

Order of authority from now on:

1. The relay model of the interlocking logic (the design principle).
2. `src/` in FieldUnit. Where it differs from 1, the code has a defect.
3. KiCad-derived interlocking models.
4. Legacy sketches and XML-harvested profiles. These are evidence only. They are not a reference.

Done: the `ERS` stick circuit is restored in primer §8.7 with a note on what the code does today. The
glossary has a new section 10.6, "Relay model of the interlocking logic (design principle)", with the
HR/DR, ASR and ERS circuits and the known code differences. "ERS" is no longer on the retired list.

Consequences:

- The items listed as "safety logic" in the code backlog are defects against the relay model:
  no `DR` (next signal not read), `ASR` does not drop on clear, no time locking without an
  `approaching()` circuit, engine return without a stick, electric lock not checked in route evaluation.
- Primer Act V and Tutorial 2 still quote `CP_Corporal.ino`. They are marked as debt until the
  KiCad-derived Corporal exists. This is one reason to draw the remaining interlocking schematics.
- Still to check against the relay model, not done in this session: the rest of primer §8 and the
  tutorials, for other places where a circuit was replaced by a description of the code.

### Iteration 9, continued: grouping of functions into field stations (ADR 0001, D3)

- The CTC machine is the source. A field station carries the functions of the levers and lamps in its panel column.
- A signal's control (left, stop, right) is one function of one lever. It goes with that lever's
  column. Routes, masts and aspects are not code line functions; they are the interlocking's work in the field.
- Inside one interlocking, relations between control points are normal and are handled behind the
  code line. A difference between an appliance's `CP` field and the column of its lever or lamp is not an error.
- Principle: a field station is the abstraction that the interlocking presents to the dispatcher.
- `TEK` with `NGK`/`SGK`: a decoder can flag it only on an encoding that can carry it (AAR tokens).
  On a 506-style two-step rule it cannot be encoded; the field unit check before encoding is the only check.
- Fascia devices and maintainer service modes: own ADR, later.

### Iteration 10 (2026-10-01): remaining ADR 0001 items, settled by the owner

| Item | Decision |
|---|---|
| Encoding rules | Truth tables as data (D11). Provisional until a worked example is built. |
| Names | No `CP_` or `CP ` in any KiCad name. `MAIN HOUSE` Values are bare names. A model board can add `CP ` for display. Fix the sources once; no normalization code (D12). |
| Addresses | Fields on the `CODELINE` symbol of that code line. No matching symbol: the generator fails (D13). |
| Scope | First target is AAR tokens over MQTT. Do not rule out US&S 506. The CODE button workaround is not chosen now (D14). |
| Two axes on the symbol | `CODELINE` has two pins; one-pin symbols give the encoding and the transport (D15). The second axis is named "transport" in the ADR, not "carrier". |
| Size limits | The compiler and the generator each check what they can see (D16). |

D12 reverses the naming rule in AGENTS.md ("controlled points always carry the `CP` prefix"). After the
fix the interlocking `Luchessa` and its control point `Luchessa` share a name and differ by kind only.

---

## Iteration 11 (2026-10-02): owner's answers on the aligned design documents

| Topic | Decision |
|---|---|
| Watsonville note in AGENTS.md | Removed. The schematic will be fixed soon, so it is not a lasting instruction. The exclusion stays in the review documents. |
| Proxy names | `<interlocking>:<tokenname>` (the older pattern, still in the XML and some KiCad). When `<interlocking>` is not the local one, the generator must listen on the code line for the office indications of that field station and take the value, usually for route equations. When it names a control point inside the same interlocking limits, the generator handles it locally. The data model supplies the facts. It does not set the policy. |
| Symbol fields | The definitions behind the symbol fields changed. The symbols must be refactored to hold the facts the model now needs (for example the `Station` field of `Codeline-MQTT`). A proposal is in work: `docs/adr/0002-symbol-contract.md`. |
| No `MAIN HOUSE` | An error. The `MAIN HOUSE` symbol is the explicit source of the name; not the title block and not the file name. The symbol can display a title block variable. This replaces "cannot use a 506-style encoding" in ADR D3. |
| Field unit and two code lines | Covered by the six terms: a field processor runs one or more interlocking applications. The "two instances" rule stands. |
| Lever rule | Still an error for a CTC machine with a lever panel that is not NX. This is the only style captured now. The rule belongs to the choice of machine. A glass-panel track plan can have other rules. |
| Lever and lamp order | From the machine symbol. The machine keeps a type (its panel style). Only the code line encoding leaves the machine. This corrects "Type moves to the code line". |
| "Controller" | Not a term. Name the operator role: **dispatcher** (code line and the distributed handshake), **tower operator** (direct to a locking bed, real or virtual), **maintainer** (maintenance or debug mode, without the interlocking). The work so far covers the dispatcher. The tower operator is covered a little. The maintainer is not covered. |
| Name normalization | D12 was too strict. A name used in a topic or key has each space replaced by `-`. |

### The two classes of control (the purpose of the `vital` tag)

A field unit handles a control transaction in three steps:

1. It checks that the transaction is complete. An incomplete or malformed transaction is ignored as a
   whole. The only response is an office indication of the current, unchanged state.
2. It checks the transaction against the safety rules. If a control is unsafe or not allowed (for
   example a switch control while its OS track circuit is occupied), **all** the controls of the
   first class are ignored. The controls of the second class (maintainer call and the like) are processed.
3. It acts.

The tag separates the two classes. Open: the names of the classes. The glossary says "interlocked
function" and "auxiliary function". The owner says "vital" and "non-vital". The tag describes how the
field unit processes a control. It does not describe the code line. To check: whether the code
ignores all first-class controls together, as stated here.

### The top-level storyline (restated, because the detail work lost sight of it)

1. Draw each interlocking and the CTC machine in KiCad.
2. The compiler and linker read the drawings and make one model.
3. The generator reads the model and emits an interlocking application for each interlocking and a
   CTC machine application.
4. The applications run on field processors and on the CTC machine. The first target is virtual,
   then AAR tokens over MQTT.

The vocabulary, the ontology and ADR 0001 exist so that step 2's model is unambiguous. They are not
the goal. Three operator roles use the result: dispatcher, tower operator, maintainer.

---

## Iteration 12 (2026-10-02): the control transaction rule, restated by the owner

Recorded as FieldUnit `docs/adr/0002-control-transaction-classes.md` (proposed).

- A malformed transaction (incomplete, unknown or corrupted data, failed structural check) is ignored
  as a whole, like a UDP packet with a bad checksum. Error counters are updated.
- A valid transaction is reliable. If acting on it would violate a safety protection, every control
  that can affect safety is ignored. All other controls are honored. The maintainer call is one.
- The code line control is a transactional demand. This gives the protection of the lever frame: no
  partial control escapes.
- `applyControlTransaction` predates this work. It is illustrative and not authoritative. It has two
  defects against the rule (maintainer call applied on a malformed transaction; only the unsafe
  control skipped) and it knows only one second-class control.
- If a dispatcher needs several routes active at once, the interlocking must be designed for it.

Other answers:

- No `MAIN HOUSE`: the compiler stops with an error that states the uncertainty.
- The `Rulebook` field was replaced on purpose by the Kind/Role mechanism. The compiler is behind.
  AGENTS.md is corrected.
- The owner updated the Watsonville schematic and fixed the GilroyCalTrain spellings on 2026-10-02.
  The exclusions and counts in the documents are dated 2026-10-01 and must be re-checked.
- Maintainer call and `MAIN HOUSE`: verified in the netlists. The call symbol connects by pin to
  `MAIN HOUSE` pin H in Luchessa, Sargent and GilroyInterchange. It is not a defect. The proposal is
  only to read the pin and not also require a `CP` field.
- Proposals that need a decision moved into the ADR structure: `docs/adr/0002-symbol-contract.md`,
  `docs/adr/0003-name-grammar.md`. `docs/adr/README.md` lists what waits for the owner.

## Iteration 13 (2026-10-02)

- FieldUnit ADR 0002 accepted: the two transaction rules; the classes are **vital** and **non-vital**.
  The class describes field-unit processing; the code line is not vital. The glossary, primer §10,
  the layout model and the symbol ADR revert "interlocked / auxiliary" to these names.
- Name grammar Q1 decided: L/R on panels and in code; schematics may use N/S, E/W or L/R by local
  policy; Left = N and W, Right = S and E.
- Name grammar Q3 decided: OS track circuits are `<switch>T1`; `833T` and `833T1` are distinct.
- Name grammar Q4 was misread: it asks only what NUMBER an approach track circuit's name carries
  (today `1SA`), not which circuit is the approach. Restated to the owner.
