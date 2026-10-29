# 0012. Derivation rules and domain libraries: what the model states, how the rules are written, and what consumers share

- Status: **accepted by the owner 2026-10-26** (rev 2: §4 says what "no fallbacks" retires and what it keeps, after the
  owner's question). The ask was: ratify the eight decisions below.
- Amends: ADR 0009 §3.12 (the relation table's implicit fallbacks retire; its rows become features, §4); ADR 0011 §5
  (the conformance suite is a set of features, not data files; the version is semantic, not a date, §3 and §7).
- Builds on: ADR 0011 (given, relations, derived; what lasts and what is transient); the owner's discussion of
  2026-10-26 on the form of the rules, scopes, routes and indications; the route spike of the same day (§9);
  FieldUnit `docs/CTC_SUBDIVISION_AND_PLANT_DESIGN.md` §2 and §6.1 (structural routes and the indication ceiling
  heuristics, worked out earlier).

## Decisions requested (all ratified 2026-10-26)

Each line has a default; the sections below argue it. Everything defined here is version 1.0 and is expected to
evolve (§7).

1. **The functional model** is the rules' only vocabulary: entities, attributes, typed relationships with
   cardinalities, namespaces, derived facts. KiCad's mechanisms (symbols, wires, sheets, labels) appear only in the
   KiCad importer (§2). Default: yes.
2. **Rules are executable features.** Each rule is a Gherkin feature whose description states the principle and whose
   scenarios are the rule; together they are the normative conformance suite (§3). Default: yes; `behave` runs them
   here.
3. **A registry of rule-check codes**, as data: syntax, level, lifecycle, the rule that raises each (§3.3). Default:
   yes, `schemas/layout-model/rules/diagnostics.json`.
4. **No fallbacks.** Where a relationship has an explicit form, it is stated or it is missing: the implicit
   alternatives of ADR 0009 §3.12 retire. Every derivation stays (§4). Default: yes.
5. **Domain libraries**: routes, blocks between interlockings and indication ceilings first, each with its own semantic
   version, its own features, and a sufficiency gate over SPCoast; a fact a library needs and does not find is
   reported at `missing` (§5). Default: yes, in `tools/railroad/`, moving to FieldUnit with the schema (view O15).
6. **Reference data** (rulebooks and their policies) is a placeholder package delivered with FieldUnit, reached by one
   lookup by railroad, era and rulebook, with the user's own data layered over the shipped defaults (§6). Default:
   yes; contents TBD.
7. **Semantic versioning** for the rules, the registry and each library, with a lifecycle that states backward
   compatibility and forward evolution (§7). Default: yes, the first release 1.0.0.
8. **A signal joint's sides are named for what they do**, `approach` and `governed`, not KiCad's pin names `B` and `A`
   (§8). Default: yes, in ADR 0011's reshape of the schema.

## 1. Problem

ADR 0011 settled what lasts: the schema with its three maps, the writer and reader policies, and one definition of
the computation (rules, conformance suite, reference derivation). It left open what the rules are written in, what
they may talk about, how they change, and what else consumers must share. Four things showed up while answering that:

- The relation table of ADR 0009 §3.12 is written in KiCad's terms ("the one Processor on the sheet", "by layout when
  one exists"). Studio has no sheets. Rules written that way would make Studio reimplement KiCad.
- A rule written as structured prose is a test written longhand.
- Consumers need more than `derived`. A code generator needs routes; the importer needs to know whether a layout is
  complete enough to generate; Studio needs routes to show; doc packets need all three. Each would otherwise write its
  own route finder.
- Ceilings and aspects depend on the railroad, the era and the rulebook, which are reference data, not layout data.

### Primitives, not an executive[^checks]

Everything this ADR defines (the reference derivation, the rule checks, the domain libraries) and the KiCad services
beside them are primitives: functions a client calls, each returning a result. It should be possible to build an
executive using these primitives, but these primitives are not that executive. When to derive, check, export a netlist
or run ERC, in what order, and what to do with a result are the client's decisions: the KiCad importer's, a code
generator's, Studio's.

## 2. The functional model

What the model states, with nothing about how a drawing states it:

1. **Entities**, each with an identity: a name unique in its namespace. A thing exists once in the model however many
   times a drawing or a view shows it.
2. **Attributes**: facts stated about one entity (`Broker`, `Milepost`, `Style`). These are `given` (ADR 0011).
3. **Typed relationships**: a named link from one entity to another, by qualified name (`Christopher:815A`). An
   appliance belongs to an interlocking; an interlocking runs on a processor; an encoding rides a transport for a
   processor; a driver sits on a bus; a circuit adjoins a circuit. Any entity may reference any other. These are
   `relations` when stated and `derived` when computed.
4. **Cardinalities and constraints** per relationship type, in the form of the glossary's §2.5: an appliance is in
   exactly one interlocking; a FieldUnit runs on exactly one processor. A violation is a diagnostic.
5. **Namespaces**: the layout, each interlocking, the OfficeUnit. A name is unique in its namespace; a reference to
   another namespace is qualified. A namespace has no parent, child or sibling: visibility and exposure are drawing
   concerns, not model ones.
6. **Derived facts**: what the rules compute from 1 to 5 (`controlPoint` by propagation, circuits, a switch's legs).

The KiCad importer maps the drawing onto this, and its own tests check the mapping: symbol instances become entities,
merged by identity (the MQTT transport placed on South-cTc and on Gilroy Interchange is one transport related to two
processors, as a switch placed on several sheets is one switch); wires, nets and hierarchical labels become
relationships; sheets become namespaces. Studio is free to represent any of it its own way.

## 3. Rules are executable features

### 3.1 Form

A rule is a Gherkin feature. Its description states the principle in a sentence or two; its scenarios are the rule.
Steps are written in the model's terms only:

```gherkin
Feature: Gang inheritance
  An appliance in a gang that states no control point takes its leader's.

  Scenario: 815A inherits from 815
    Given interlocking "Christopher" with house "Christopher North"
    And switch "815" states CP "Christopher North"
    And switch "815A" states no CP
    When the layout is derived
    Then "815A" has controlPoint "Christopher:Christopher North"
    And there are no diagnostics

  Scenario: a gang split across houses
    Given switch "815" states CP "Christopher North"
    And switch "815A" states CP "Christopher South"
    When the layout is derived
    Then there is a warning "control_point.gang" on "815A"
```

Any implementation conforms by running the same feature files against its own step definitions: the reference
derivation in Python here, Studio in whatever language it is written in. Gherkin has runners in most languages.
`behave` is added to this repo's development dependencies.

### 3.2 Where KiCad appears

Only in structural features, and there as one paragraph: "in KiCad, a namespace is a sheet". A rule such as gang
inheritance has nothing to do with KiCad and says nothing about it. The importer's own tests check that a drawing
yields the `Given` facts.

### 3.3 The rule-check registry[^checks]

A rule check is a model-integrity check: a function from a model to a list of findings. Each finding has a code, a level,
and names every entity it is about by model identity: one for a fact wrong in itself, every party for a relationship
(the consumer and the interlocking it fails to resolve against, both pins of a shorted symbol). Calling it, and what to
do with each level, are the client's (§1).

The scenarios name the codes; the registry says what each code is:

```json
"control_point.gang": {
  "level": "warning",
  "lifecycle": "active",
  "since": "1.0.0",
  "feature": "control_point/gang_inheritance.feature",
  "replacedBy": null
}
```

- Syntax: `<family>.<condition>`, lower snake case; the family is the feature's directory (`control_point`, `next_cp`,
  `identity`, `track`, `route`).
- Levels, most severe first: error, warning, info, missing.
- Lifecycle: proposed, active, deprecated (with `replacedBy`), retired. A code retires only at a MAJOR version (§7).
- A gate checks that every code a scenario names is in the registry and every active code is named by a scenario.
- Import diagnostics are not rule checks. They are problems translating a drawing into a model, located in the
  drawing's terms (project, sheet, reference, Name), and mean nothing to a code generator or to Studio, which imports
  nothing. They belong to the KiCad importer, with their own registry in `tools/layout_compiler`. The importer may also
  locate a rule check's entities in the drawing for its user; that is the importer's work, not the finding's.

## 4. No fallbacks

What retires is narrow: a second, implicit way to state a relationship that the drawing now states explicitly. Where
ADR 0009 §3.12 gives a relation both an explicit form and an implicit fallback, the explicit form is the only one, and
without it the relationship is missing. The fallbacks that retire:

- a FieldUnit's processor: "the one Processor on the sheet";
- an OfficeUnit's processor: "the one Processor on its sheet";
- a unit's code line: "an encoding instance in the unit's folder; by layout when one line exists";
- a driver's bus: "the one Processor on the sheet; `Processor` field when two";
- a transport's anchor: "the `Processor` field; the machine's processor for a code line transport";
- an encoding's transport: "the `Transport` field; by layout when one transport of its kind exists";
- a CMRInet bit's node: "the one CMRInet Node on the sheet".

They stay in ADR 0009 as a record.

What stays is everything derived: facts computed from stated facts, which have no explicit form to compete with.

- Control point by propagation (the rulings of 2026-10-26): one house on a sheet, gangs, switch to OS circuit, mast
  and signal joint, plain IRJs, virtual circuits, maintainer calls; a stated `CP` still wins.
- Circuits and their names, a switch's OS circuit and its `TC` override, ports, links, named ends, NextCP pairing, a
  mast's heads.
- The §3.12 rows whose only form is derived: the 506 station address from the column number, an OfficeUnit's columns
  from its interlockings, a head device to its head by name, a panel column to its house by `CP Name`.
- Identity by name (§2): a thing placed several times is one entity.

Evidence: the KiCad importer over SPCoast resolves every relation by wire and none by fallback alone, with no
disagreement: 48 drivers on a bus, 7 interlockings on a code line, 2 on a processor, 2 transport anchors, 1 encoding on
a transport. The code line already carries the encodings and the code line processor into each interlocking's
namespace. The importer's fallback code and its `*.explicit_only` and `*.implicit_only` info diagnostics go in the
implementation step.

## 5. Domain libraries

### 5.1 What they are

Railroad operations over the model, shared by every consumer: the KiCad importer (is the layout complete enough to
generate?), Studio (visualisation), code generators, doc packets. They read the file under ADR 0011's reader policy and
write nothing into it: routes are derived from the model, not stored in `derived`. The model's obligation is to be
sufficient for them.

| Library | Answers | Reads |
|---|---|---|
| routes | the structural routes of each signal: entrance, end, switch alignment, circuits passed | switch legs and their neighbours, signal joints and the direction each governs, circuit adjacency, ends |
| blocks | the track between two interlockings: the pair of NextCPs, its method of operation, the signals that protect it from each end | NextCP pairs, policies (Rule 251, Rule 261), routes |
| ceilings | the indication ceiling of each route | routes, `IndicationCeiling` where stated, reference data (§6) |
| codeline[^libs] | per station, the controls it receives, the indications it must send, and the appliance that reports each token | desk columns, the levers' `Control.X`, the consumers' `Indication`, the appliances; which appliance reports a token is an interim lookup that reads the reference templates backwards |

What a processor needs (its transports and the encodings riding them there) is a query in the same family, a join of
facts the model holds; it is not stored.

### 5.2 The vital boundary

The libraries find static facts: what FieldUnit's interlocking model takes as `routes[]` with `displays: {mast,
maxIndication}`. The signal indication shown at run time (all routes at a signal but one at Stop; the one aligned
route's indication computed from the interlocking's state) and the aspect the heads display (FieldUnit's
`AspectResolver`) are FieldUnit's. No library implements locking of any kind.

### 5.3 The route rule

A route runs from a signal, in the direction it governs, until it reaches the next signal governing the same
direction, or a limit (a NextCP, END_CTC or bumper). Opposing signals are passed: a route can leave a protected siding
whose points end is protected against traffic the other way. At a switch entered at C the route takes N or R; entered
at N or R it leaves by C. A derail has legs C and R only. A route's identity is its entrance, its end and its
alignment: two routes may share an entrance and an end (Christopher, 816NC to 816SAB).

### 5.4 Indication ceilings

The heuristics of FieldUnit `docs/CTC_SUBDIVISION_AND_PLANT_DESIGN.md` §6.1 carry over as the ceiling library's
version 1.0 scenarios: a switch normal gives Clear; reversed gives Approach; passed reversed trailing, Approach; a
route into dark track, Restricting, or Diverging Restricting through a reversed switch facing. `IndicationCeiling`
stated on an appliance (795D: `STOP/RESTRICTING`) overrides them where the user wants control. The proof-of-concept
`tools/plant_graph/indications.py` is evidence, not a reference. The indication each heuristic yields is reference
data, so a railroad or era can change it.

### 5.5 Sufficiency and incompleteness

Each library has a gate: it runs over every interlocking in SPCoast. A result it cannot finish for want of a fact is
reported at `missing`, never at error (ADR 0011 §6). Example: Watsonville has no southbound signal into 837T1, an
intentional TBD (the owner, 2026-10-26: on the single track from Corporal, Corporal's 830S and the automatic block
between are the proxy). The routes library reports a facing switch at a limit with no entering signal at `missing`.

## 6. Reference data

Rulebooks and their policies (which `AspectResolver` applies, the indication each ceiling heuristic yields, later a
speed rating's limit) are reference data, not layout data. There are too many railroads, eras and rulebooks to ship
them all.

- A placeholder package, delivered with FieldUnit beside the libraries and tools that read it.
- One lookup by railroad, era and rulebook (the layout's `railroad`, `era` and `rulebook`). No consumer hard-codes a
  table.
- The user's own reference data layers over the shipped defaults; the user's wins.
- Contents TBD. Only the interface and the override order are fixed now.

## 7. Versioning

The rules with the registry, and each library, carry a semantic version. Dates live in changelogs and git tags
(`rules-v1.0.0`). `provenance.rules` (ADR 0011 §3) carries the rules version.

| Change | Bump |
|---|---|
| A `derived` key removed or changing meaning; a code retired; a level raised (a clean file now has an error); a library result changing for an unchanged file | MAJOR |
| A rule, a `derived` key, an optional attribute or a code added; a code deprecated; a level lowered | MINOR |
| An implementation fixed to match its scenarios; a message reworded | PATCH |

- **Backward compatibility.** A reader holding rules X.Y uses a file stamped X.Z as it is and skips keys it does not
  know. A different MAJOR means rebuild `derived`. A library states the MAJOR of the rules it reads.
- **Forward evolution.** A new fact arrives as an optional attribute with a stated behaviour when it is absent.
  Deprecation comes before retirement; retirement only at a MAJOR.

Worked example, the turnout speed rating (the owner, 2026-10-26: turnouts will need one):

1. The schema and the rules gain an optional switch attribute (name and values to decide; Slow, Medium, Limited). A
   file without it stays valid: MINOR.
2. The ceiling library uses it when present, through reference data that maps a speed to the best diverging
   indication for the railroad and era. Without it, the 1.0 heuristic applies, so every existing file keeps its
   ceilings: MINOR, not MAJOR.
3. The reference data gains a speed table, with placeholder defaults a user may override.
4. The switch symbols gain the field (an owner library edit) and the KiCad importer reads it.
5. New scenarios cover "with a speed rating"; the 1.0 scenarios pass unchanged, which is the proof of compatibility.

## 8. Signal joints, named for what they do

The file says which way a signal governs only through the pin names of the KiCad symbol: the signal governs movement
from `B` into `A` (`joint.reversed` checks it). That is a KiCad convention leaking into the model. A signal joint's
circuits are named `approach` and `governed`; other joints keep neutral sides. The change lands in ADR 0011's reshape
of the schema, not as a separate version.

## 9. Evidence: the route spike of 2026-10-26

A throwaway route search read only the SPCoast Layout Data Model File (KiCad importer output, Railroad `96c6b4e`) and
applied §5.3:

| Interlocking | Switches | Signals | Routes |
|---|---|---|---|
| Christopher | 4 | 4 | 8 |
| Corporal | 4 | 4 | 6 |
| Gilroy Caltrain | 3 | 5 | 8 |
| Gilroy Interchange | 2 | 4 | 6 |
| Luchessa | 4 | 5 | 10 |
| Sargent | 2 | 3 | 4 |
| Watsonville | 13 | 10 | 16 |

- Every switch leg, plain circuit and signal is connected; no circuit has more than two boundaries.
- Luchessa's ten routes match the ten structural routes of FieldUnit's design document §8.1, including the industry
  routes through 795 reversed with 795D clear.
- Every NextCP states its method of operation (Rule 251 on the double track Luchessa to Corporal, Rule 261 on the
  single track elsewhere) except Watsonville's, the TBD of §5.5. The single track Corporal to Sargent is one circuit,
  `Corporal:2NAT`, named from both sides.
- The only model gap found is §8.

## 10. Where things live (defaults)

| What | Where |
|---|---|
| Features, by family | `schemas/layout-model/rules/features/<family>/*.feature` |
| Rule-check registry and changelog | `schemas/layout-model/rules/diagnostics.json`, `schemas/layout-model/rules/CHANGELOG.md` |
| Import diagnostic registry | `tools/layout_compiler/`, retired with the importer |
| Reference derivation | `tools/layout_model/derive.py` (ADR 0011 §5) |
| Domain libraries | `tools/railroad/` (`routes.py`, `blocks.py`, `ceilings.py`, `codeline.py`), each with its version and its features |
| Naming grammar and Style classes, shared by the reference derivation and the domain libraries | `tools/layout_model/grammar.py`[^libs] |
| Reference data | FieldUnit, path TBD |

All move to FieldUnit with the schema (view O15).

## 11. Out of scope

- The signal indication at run time and the aspect a mast displays: FieldUnit.
- The contents of the reference data.
- How Studio represents namespaces, identity or relationships.
- The ADR 0003 discussion held on 2026-10-26: rule 8 crossovers, `TC` detection blocks, the OS circuit default.

## 12. Consequences

- ADR 0009 §3.12: the implicit fallbacks listed in §4 retire; the relation rows, and the derived rows, become features.
- ADR 0011 §5: the conformance suite is the features; the version is semantic.
- The implementation step (after this ADR and ADR 0011's reshape): the features and registry, `derive.py` with the
  importer calling it, the fallbacks removed, the joint sides renamed, then the routes, blocks and ceilings libraries
  with their gates.
- `AGENTS.md` gains the libraries and the reference data in its Layout and Direction sections once this is ruled.
- The vocabulary gate covers this repository only; FieldUnit's design documents still use the proof-of-concept names
  (`Indications`, `Rulebook`, `dark_exit`, the compiler). Extending the gate to FieldUnit is a separate step.

[^libs]: Rewritten in place on 2026-10-28: §5.1 gains the codeline library and §10 gains `codeline.py` and
    `grammar.py`, both built in step 2. The earlier wording is at commit `f18e009`.

[^checks]: Rewritten in place on 2026-10-29 (the owner): the package is primitives, not an executive (§1); §3.3
    registers rule checks, which name every entity they are about, and import diagnostics move to the importer. The
    earlier wording is at commit `2bf4bb1`.
