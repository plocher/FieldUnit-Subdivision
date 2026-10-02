# Ontology: one concept, many eras

Status: draft for review (2026-10-01, rev 4). A **delta against FieldUnit
`docs/GLOSSARY.md`**, which stays the source of truth for vocabulary. This document does not
invent a second vocabulary. The FieldUnit-Studio design spec is deliberately not used as an
authority: its limitations are why the project pivoted to KiCad schematics as truth.

Rev 3 (2026-10-01) incorporates the US&S 506A codeline detail in §1 and settles §9.
Rev 2 replaced rev 1's central claim: rev 1 argued that Control Point and Controlled Point
(Line Station) are two different concepts. They are not. **A "Control Point" is the name of
the location that contains a "controlled point"**, and in the early era the location, its
bungalow and its single addressable unit were one thing because the technology made them one.

## 1. What a control point is

A control point is a place on the railroad where the movement of trains can be controlled.
By definition that is a track switch. Because bare switches are bad for business, safety
appliances accumulated around them.

The first control points were exactly one thing, the end of a siding off a main track, and
needed exactly:

- a track switch, Normal and Reverse;
- a two-head mast facing traffic on the main heading into the points;
- a one-head mast facing traffic on the main heading against the frog;
- a one-head dwarf facing traffic on the siding heading against the frog;
- a track circuit protecting the switch itself;
- track circuits for the three tracks leading into the switch;
- a maintainer call, for the telephone in the trackside bungalow, because radio did not exist.
- a call-on feature for exceptional circumstances

The Union Switch & Signal (US&S) 506A Centralized Traffic Control (CTC) machine utilized a 16-step timecode cycle to transmit controls from the dispatcher's office to a field station (and to receive status indications in return). [1, 2, 3] 
The system was capable of handling up to 35 unique field locations, allocating 7 control functions and 7 indication functions per station. [1] 
The 16 steps making up the machine's codeline sequence are structured as follows: [1] 

### The 16-Step Codeline Structure

   1. Step 1: Conditioning Step (1 step) – A single long pulse used for line check, locking purposes, and preparing the field stations for an incoming transmission. [3] 
   2. Steps 2 to 8: Station Selection (7 steps) – These 7 steps uniquely identify the targeted field station using a distinct combination of long and short pulses (typically 3 long and 4 short pulses). Up to 35 stations were supported by a single system. [3] 
   3. Steps 9 to 15: Function Controls (7 steps) – The core 7 functions supported by the machine. Each of these 7 steps can be either long or short, carrying the specific binary operational commands to the equipment at the selected station. [3] 
   4. Step 16: Delivery Step (1 step) – An extra-long final pulse used to execute ("deliver") the commands to the magnetic stick relays (KP relays) and reset the line apparatus for the next cycle. [1, 3] 


### The 7 Function Controls (Steps 9–15)
While the function steps are generic binary placeholders on the line circuit, a standard US&S 500-series setup assigned these 7 codelines to the following prototypical field commands: [4] 

* Switch Control (Normal / Reverse): Typically takes up two steps to govern the physical alignment of the turnout points. [4] 
* Signal Control (Left / Right / Stop): Typically takes up two or three steps to clear signals for leftward movements, rightward movements, or to drop them all back to a "Stop" (Normal) state. [4, 5] 
* Maintainer Call: A dedicated toggle step used to light a lamp or sound a horn at the field bungalow to flag down a trackside worker. [4, 6] 
* Call-On / Override Function: Used to allow a train to enter an occupied block under a restrictive aspect in special switching or emergency circumstances. [4] 

[1] [https://rrsignal.com](http://rrsignal.com/railroad/ctc/uss506.htm)
[2] [https://position-light.blogspot.com](http://position-light.blogspot.com/2020/10/videos-us-ctc-machine-operation-in.html)
[3] [https://groups.io](https://groups.io/g/CMRI-Users/topic/dead_time_on_a_code_line/75489030)
[4] [https://ctcparts.com](http://ctcparts.com/?page_id=322)
[5] [https://position-light.blogspot.com](http://position-light.blogspot.com/2020/10/videos-us-ctc-machine-operation-in.html)
[6] [https://www.jmri.org](https://www.jmri.org/help/en/html/tools/uss/index.shtml)


The Field Station was also called a Control Point or simply a Station interchangeably, and it was usually experienced as
a pile of batteries, relays, spiders and rattlesnakes in a concrete bungalow out in the middle of nowhere.

**In the early twentieth century there was no conflation to resolve.** The bungalow was the
main house, was the station, was the controlled point. They were one thing because the
technology made them one thing.

## 2. How the terms came apart

| Change | Consequence |
|---|---|
| anything more complex than a siding | needed a TowerMaster with switch tenders, levermen and clerks, and a mechanical interlocking machine wired to the points through pipe and wire runs |
| **a control point needing more than 7 functions** | **they added a new control point next to it** |
| running out of 35 station addresses | replace the whole system with one carrying 18 to 35 functions, for many more dollars |
| mechanical to electrical | relays replace linkages |
| staffed towers to remote dispatchers | the operator leaves the site |
| slot-based codelines to digital | the step budget disappears |

The second row is the one that matters here. **Splitting a control point into several
adjacent control points was a capacity workaround, not a fact about the railroad.** It is the
historical mechanism behind #16.

## 3. One location, era-dependent addressing

Control Point and Station name the same thing. "Station" is the *addressable realization* of
a control point under a given era's codeline technology, and only the projection changes:

| Era / codeline | Budget per station | Effect on a control point |
|---|---|---|
| US&S 506A | 7 control steps + 7 indication steps, 35 stations per system | a location needing more is split; another controlled point is added beside it |
| later relay systems | 18 to 35 functions | fewer splits |
| MQTT / digital | unbounded | no splits; one station per interlocking suffices |

**The budget is not approximately the end-of-siding control point. It is exactly it.**
Costing the §1 list, where a signal control is **always three** steps:

| Appliance | Control steps | Indication steps |
|---|---|---|
| switch, Normal / Reverse | 2 | 2 |
| signal, Left / Right / Stop | **3** | 3 |
| maintainer call | 1 | 1 |
| call-on / override | 1 | 1 |
| **total** | **7 of 7** | **7 of 7** |

A signal's control is always three because the three steps are permissions, not positions:
*you must be at stop*, *you may be left*, *you may be right*. The indication side carries what
was actually commanded, modified by time locking and the other locks.

So the 506A's seven control and seven indication steps were sized for precisely one
end-of-siding control point, with nothing spare. That is the arithmetic behind "when a control
point needed more than 7 functions, they added a new one next to it".

**The panel symbol set already encodes this budget**, which is a useful cross-check that the
ontology is right:

| Symbol | Control pins | Indication pins |
|---|---|---|
| `PanelSwitch`, `PanelLock` | `NWS`, `RWS` | `NWK`, `RWK` |
| `PanelSignal` | `NGS`, `HS`, `SGS` | `NGK`, `SGK`, `TEK` |
| `PanelMCall` | `SW` | the `MCnK` lamp token |
| call-on | **no symbol exists** | **none** |

Six of seven steps each way are already drawn; **call-on is the only missing appliance**, and
`PanelCode` is the code button rather than a function step.

**The canonical multi-point case is a passing siding.** Both ends are handled as two control
points, one per end. Each end is one switch plus one signal set, so each exactly fills a
station. This matters for reading a drawing: multiple control points arise both from geography
(two ends, genuinely separate places) and from overflow at one place (a junction needing more
than seven steps), and **the drawing alone cannot tell you which**. Luchessa is the geographic
kind, since Carnadero is miles from Gilroy (§8).

So the location is durable and the addressing is era-dependent. A model that spans eras must
keep them apart; a model of 1950 alone need not, which is why the sources read as they do.

## 3a. Consolidation: two causes, one outcome

**Control points grow geometrically with track geometry.** One per switch, so a passing siding
is two, one per end. The same holds for crossovers and the other common design blocks: each
adds its own controlled points because each adds a place where movement is controlled.

**Railroads then consolidated, because that growth was expensive.** Maintaining two
independent codeline stations for one passing siding cost real money, so whenever a newer and
lighter era allowed older and heavier practice to be condensed, railroads condensed it:

- ABS / APB across long stretches with no control points at all;
- one field unit serving several related stations, which is exactly the Luchessa shape;
- and eventually digital high-frequency track overlays, radio and GPS, which removed the
  codeline step budget entirely.

**The terminology and the drawings lag the technology, sometimes by decades.** CalTrain issued
early-2000s drawings to current AREMA and AAR standards while still using semaphore icons. So
a drawing's vocabulary is evidence of drafting convention, not of implementation.

### Why this gives Luchessa legitimacy

Selective compression on a model railroad and technological consolidation on a real one
**produce the same structure**: several formerly independent control points served by one field
unit and one codeline station. Miles becoming three inches has the same outcome as "we have
radios and a digital codeline".

So Luchessa's three control points under one field unit are **not a modelling compromise and
not a 506-era artifact to be unwound**. They are what consolidation looks like on a real
railroad, and they are prototypically correct.

### Two consequences for the compiler

1. **Consolidation is expressed by what the field unit spans, not by deleting control points.**
   The control points stay as drawn and named; the field unit and the station are what collapse.
   This is the concrete reason `fieldUnits` needs `codeline` plus derived `stations[]` (§7)
   rather than a single station.
2. **Never infer the implementation from the iconography.** A drawing may legitimately carry an
   older era's symbols and names for newer-era equipment. This is the same rule as the
   permissive validation in §6a, arriving from the other direction: the drawing states what
   exists, and the codeline states what carries it.

**On 15 versus 16 steps: both are right.** The cycle is 16 steps, of which the conditioning
step carries no data, so counting data-bearing steps gives 15. The glossary's "15, 20 or 32"
and the 506A sources' 16-step cycle are the same fact counted differently. Either way the
enforceable number is **7 control functions**, not the cycle length, so the glossary delta is a
clarification rather than a correction.

**The glossary already says both halves**, in two entries that sound the same:

- §1.2 **Control Point (CP)**: "the logical unit of dispatcher authority. A named geographic
  location... containing wayside signals governing train movement."
- §1.1 **Controlled Point (Line Station)**: "the addressable supervisory unit on the
  CodeLine. Bounded by the stepping capacity (15, 20 or 32 steps)."

Read as one concept and it is era projection, those stop competing. Read as two concepts, and they collide. The glossary needs to disambiguate them.

## 4. MAIN HOUSE is the bungalow, and that is correct

**`MAIN HOUSE` and Bungalow are synonyms** (decided 2026-10-01). The symbol is the physical
enclosure, and its Description saying "the Control Point Maintainer Bungalow" is correct, not
a conflation to fix. It is also where the maintainer-call light and telephone are, which is
what makes more than one call imply more than one bungalow.

The **Field Unit is not a synonym**: it is the computer, relays and magic pixie dust *inside*
the bungalow, matching the glossary's "the local compute and I/O controller... inside the
bungalow". It needs its own symbol (§5a), and one field unit can answer for several stations.

So what is actually wrong is narrower than rev 1 claimed. `MAIN HOUSE` is the right symbol for
the right thing; the error is **downstream interpretation**: the compiler reads it as the
addressable controlled point and treats a desk column as identical to it. That only breaks
because SPCoast South is a 506-era *machine* on an MQTT *codeline*, so the model has to span
two eras at once.

## 5. Three sources already model it this way

**The glossary**: a panel column maps 1:1 with a controlled point "**in 15-step systems**",
and "multiple columns are consolidated under a single CODE button". The 1:1 was always scoped
to the hardware; the tooling generalised it into an identity.

**The FieldUnit runtime**: `CtcStation` holds N `PanelColumn`s and builds one codec per
station (`src/cTcMachine.h:283,120`). A column is not a station.

**The legacy ArduinoPoint model**: one `<controlpoint>` per station with N columns and a
single node address (GCaltrain 0x77, GInterchange 0x78, Christopher 0x81, Corporal 0x83,
Sargent 0x84, Watsonville 0x97).

The KiCad compiler is the only place that equates a column with a control point.

## 6. Cardinalities

```
Territory / Subdivision ─1:N─ Control Point        a named location on the railroad
Interlocking Plant      ─1:N─ Control Point        a plant may span several locations
Control Point           ─1:N─ controlled point     the addressable unit(s) AT that location
                                                   N>1 only under a step budget (506A: 7 control steps)
Control Point           ─1:1─ Bungalow / MAIN HOUSE   synonyms; the enclosure at the location
Bungalow                ─0:1─ Maintainer Call      the call telephone and light are AT the bungalow
Bungalow                ─1:1─ Field Unit           the computer INSIDE the bungalow; not a synonym for it
Field Unit              ─1:N─ Station              one controller answers for every station on its codeline
CodeLine                ─1:N─ Station
Station                 ─1:N─ Panel Column         1:1 only when the step budget forces one appliance set per station
```

## 6a. Validation direction: permissive, never prescriptive

Era is recorded in the sources (`CtcMachine` has an `Era` field, title blocks say
`Era: 1942 until 1985` and `cTc: US&S 506`) but it is **unreliable as an input** and should
not drive anything. The codeline symbol already states the technology, so the constraint
comes from there.

The direction of inference matters, and only one direction is acceptable
(decided 2026-10-01):

- **Not prescriptive.** The compiler never demands structure to satisfy a configuration:
  *"you placed a `Codeline-USS506`, therefore you must have N control points"* is wrong. The
  drawing is the truth.
- **Permissive.** The compiler checks whether the chosen codeline can carry what is drawn:
  *"you placed one control point carrying 9 functions, so choosing `Codeline-USS506` is an
  error"* is right. Either split the point or choose a codeline that can carry it.

So the check is a **capacity check, not a count check**. That is the same shape as the open
machine-capacity item in `desk-codeline-kicad-pattern.md` §7a, and the two budgets are
siblings:

| Budget | Owner | Unit |
|---|---|---|
| levers and lamps per column | the machine type (`US&S506`) | one console column |
| control functions per station | the codeline (506A = 7 control + 7 indication steps) | one addressable controlled point |

A codeline symbol therefore has to carry its budget, the way `PanelColumn-MAX7313` carries
the implication of 16 bits. There is no `Codeline-USS506` symbol yet; when one is drawn, the
budget is a field on it or implied by the symbol, never a number in the compiler.

**Era then needs no model field.** It is documentation in the title block, and the enforceable
facts come from the codeline and machine symbols.


## 7. What this settles

**The maintainer-call rule has a mechanism.** The call telephone is at the bungalow, so that
relation is 1:1, and more than one call means more than one bungalow. The converse fails, and
the drawn sources agree: the call count is at most the house count everywhere (Luchessa 1 of
3, GilroyInterchange 2 of 2, Christopher 2 of 3, Corporal 1 of 2, Sargent 1 of 1).

**`fieldUnits[].station` in `layout-model.md` rev 7 is wrong.** It says a unit answers on
exactly one station. Under a step budget one controller in one bungalow answers for every
station of its control point. The intended rule was that a unit cannot serve two *masters*,
where a master is a **codeline**, so it becomes a `codeline` foreign key with `stations[]`
derived.

**The `CP` field on plant appliances is the wrong mechanism** (#16). An appliance belongs to a
control point by geography, and writing it on every appliance is a second place for the same
fact. It has already drifted: 66 appliances across four stations name a house Value that does
not exist.

## 8. Luchessa, answered

Carnadero is the junction to the Hollister branch and sits miles from south Gilroy's
industrial park. On the prototype they would never have been aggregated into one interlocking.
Selective compression turned those miles into three inches of layout.

Earlier revisions of this document treated that compression as a distortion to be unwound,
leaving Luchessa with one main house. **That was wrong, and §3a says why.** Compression on a
model railroad produces the same structure as consolidation on a real one: several control
points served by one field unit and one codeline station. Luchessa is therefore a faithful
representation of a consolidated prototype, not an artifact.

**So Luchessa keeps its three control points, permanently, and not merely as a 506 test
fixture.** What is era-dependent is how many stations and field units serve them: three
stations on a 506 codeline, one on MQTT, with one field unit either way.

Two things that follow:

- The earlier plan to "simplify Luchessa after #15" is withdrawn. There is nothing to simplify.
  The regression-reference tension disappears with it, though the carried-forward point about
  better tests stands on its own merits (§10).
- **Other stations may legitimately have several control points too**, wherever geometry gives
  them several: both ends of a passing siding, a crossover, any other design block. What the
  bootstrap generator got wrong was manufacturing one house *per desk column*, which is the
  506-era column identity, not one per place where movement is controlled.

## 9. Resolved

1. **Is a bungalow its own symbol?** No new symbol needed. **`MAIN HOUSE` and Bungalow are
   synonyms.** The Field Unit is the computer inside it and gets its own symbol (§5a).
2. **Glossary wording.** "Control Point" is the name of the **location** that contains a
   "controlled point". The glossary should say that plainly instead of leaving two entries that
   sound alike. Also reconcile the step count (§3 note).
3. **Luchessa's three houses.** Keep permanently: they are prototypically correct, being what
   consolidation looks like (§3a, §8). Nothing to simplify.

## 10. Carried forward

- **"Find a better way to regression and feature test these things."** Today the only
  regression reference is one hand-drawn station. This no longer blocks anything, since
  Luchessa is not being simplified, but it remains the right criticism: the gates should be
  behavioural, not a frozen document, per the functional-gates principle.
- **Crossovers and other design blocks each grow their own control points** (§3a). Worth
  capturing as reusable KiCad design blocks in the existing `SPCoast.kicad_blocks` library, so
  the pattern is drawn once rather than copied.
- A `Codeline-USS506` symbol does not exist. When drawn, it carries its own budget (7 control
  functions), the way `PanelColumn-MAX7313` implies 16 bits, so the capacity check in §6a has
  something to read.
- `fieldUnits[].station` in `layout-model.md` becomes a `codeline` foreign key with `stations[]`
  derived (§7).
- The `CP` field on plant appliances is retired in favour of derived membership (#16).

