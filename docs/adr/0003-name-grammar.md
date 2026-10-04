# 0003. One grammar for the names of appliances, signals and track circuits

- Status: proposed; frozen 2026-10-03 until the cleanup pass (issue #30) rewrites this ADR to rules. The owner's review: too complicated and unfocused to approve as-is.
- Date: 2026-10-02 (responses), 2026-10-03 (final form)

Reshaped from spike S5 of `vocabulary-review.md` (F16). Nothing is renamed until the owner accepts this
ADR. No code, schematic or profile is changed by it.

"Q n" is question n of the earlier proposal (Appendix A; the evidence in Appendix B uses the same
numbers). "D n" is decision n below. "(unverified)" marks a statement that no opened source supports.

## Decisions

The owner answered every question on 2026-10-02 (Appendix A). Q1, Q3 and Q4 were decided first; the
others follow the RESPONSE text.

- D1. Direction letter (Q1). Panels and code conventions use L and R; they do not depend on railroad,
  geography or era. A schematic track diagram uses N/S, E/W or L/R as local policy decides, with one
  fixed mapping: Left = North and West; Right = South and East. Mast names drawn with compass letters
  stay valid; the compiler maps them to L and R.
- D2. Tokens and displays (Q2). Local era, railroad, geography and policy dictate the drawing, the
  tokens and the panel displays (W/E, N/S, L/R). The code uses L and R internally and keeps the style
  the user gave. FieldUnit `NGS`, `SGS`, `NGK`, `SGK` (N = LEFT, S = RIGHT) are one such style and are
  not renamed.
- D3. OS track circuit (Q3). An OS track circuit generated from the switch number is `<switch>T1`. This
  keeps it distinct from other circuits that end in `T`: `833T` and `833T1` can both exist. The AAR56
  `<number>T` form is not used for OS circuits.
- D4. Track circuit names (Q4). A track circuit name ends in `T` or `T<digit>`. When the drawing gives a
  name (`1SAT`), the tooling uses it. When no name is given, the AAR56 rule is authoritative for the
  generated name, except for the OS form of D3. Luchessa's circuits are renamed in the schematic
  (`1SA` → `1SAT`, `2NAA` → `2NAAT`, and so on).
- D5. Circuits with no switch and no signal; specialized tokens (Q9, second round 2026-10-03). The AAR
  scheme is part of the layout designer documentation, although these South-cTc plans do not use it.
  Where AAR has defined terminology, it is documented and used; specialized tokens carry minimal
  semantic value.
  - Arbitrary numbers that start with the digit zero, `0<n>T` (`01T`), name tracks with no interlocked
    switches that govern no signal: isolated or auxiliary track segments (the owner's examples: plain
    stretch blocks, specialized detector circuits, crossing approaches, storage tracks, some yard tracks,
    isolated sidings). The prefix is the digit zero, not the letter O (owner, V4).
  - Single digits (`1T` to `9T`) serve the same purpose in a plant whose dispatcher-visible and
    cross-interlocking items use milepost-based numbers (owner, V4; D11).
  - The hot box token is `HBA` (hot box alarm), not `HBD`. The owner changed Sargent.
  - The traffic indicators are `EFLK`/`WFLK` or `SFLK`/`NFLK`: direction letter, `F` (traffic), `LK`
    (traffic locking indicator). They replace `TL` and `TR`, which also collided with `TR` (track relay).
    The owner updated the schematics.
  - None of these is a track circuit. The pasted ATCS and F-token material (Appendix A, second round) is
    a lead: a summary with no checked source. The AAR status of `HBA`, `[NSEW]FLK` and the zero prefix is
    unverified until the 1946 document is checked (V2, V3, V4).
- D6. Section letter placement (Q5, V5). Open. The owner answered "The former: 784LAT" (letter after
  the signal number, before T). The same round's statement of the AAR rule gives the letter as a
  prefix: "A10T, B10T, and C10T" for successive circuits governing signal 10. The two answers conflict;
  the owner picks one. It matters only when the tooling must generate an approach name (D4).
- D7. Crossover ends (Q6). Base plus letter. A simple crossover is `815`, `815A`; a double crossover is
  `815`, `815A`, `815B`, `815C`. D8 gives the general gang rule.
- D8. Gangs and derails (owner, 2026-10-03; replaces the earlier D8, "keep `<switch>D`; `D` reserved").
  Dependence and ganging are decided by the symbol kind and the name relation, not by the letter D.
  - Names are unique. The full Value of an appliance is unique within an interlocking across switches,
    locks and derails. A duplicate is a compiler error; the kind does not disambiguate it. Example: a
    derail `815A` beside a switch `815A` is an error.
  - A name is `<id>[<letter>]`, letter A to Z. The gang id of a Value is the Value with its trailing
    letter removed (`815A` → `815`; `815` → `815`), so the rule holds when a gang has no bare member
    (`815A`, `815B` only).
  - Ganged switches: `APPLIANCE`/`SWITCH` or `APPLIANCE`/`LOCK` symbols whose Values share one gang id
    are one gang, worked by one lever: `815`, `815A`; a double to `815C`.
  - Dependent derail: an `APPLIANCE`/`DERAIL` symbol whose gang id matches a switch or lock gang in the
    same interlocking is dependent on that gang. Example: a derail `815D` beside switches `815A` and
    `815B`.
  - Independent derail: an `APPLIANCE`/`DERAIL` symbol whose gang id matches no switch or lock gang.
  - The letter D is the convention, not the mechanism: a dependent derail is named `<id>D` (`795D`, as
    kept by the Q7 response); an independent derail has no letter or D. D is not reserved: a switch
    may be named `815D` when no other appliance has that name.
- D9. Head letters (Q8). Do not limit them. Every single letter A–Z is usable.
- D10. One-head signal (Q11). Always a letter, also on a signal with one head.
- D11. Local items (Q10). Items that only local crews see or control, such as a hand-throw switch, do
  not take milepost names. They take arbitrary numbers, with or without a zero prefix (`0<n>T`, or
  `[1..9]T`). Corporal SW901 and Sargent SW3 keep `1`.
- D12. Maintainer call (Q13, V1). `MC` is the AAR abbreviation for the maintainer call, per the owner:
  AAR Signal Manual Part 33 (circuit nomenclature) and Part 91 (lamp abbreviations), with control token
  `MCS` and indication `MCK`; a Conrail CS-4000 (1981) lamp list also has `MC` (Maintainer's call). The
  1946 document in `docs/reference` is likely Part 33 itself; to verify there (V1). FieldUnit
  `MC<n>S`/`MC<n>K` adds an instance number, so one interlocking can have several calls. Keep `MC<n>`.
- D13. Watsonville staging yards (Q12). Withdrawn by the owner; model-layout yards are supported by the
  tooling later. The Watsonville schematic was updated on 2026-10-02 and can be re-checked.
- D14. Prefixes and normalization. ADR 0001 D12 (amended) decides them: a KiCad name has no `CP_` or
  `CP ` prefix, a model board may add `CP ` for display, and a space becomes `-` in a topic or key. This
  ADR adds no prefix rule and no normalization.

- D15. AAR naming as the owner reads it (V6, 2026-10-03).
  - Inside interlocking limits a track circuit that encloses switch 11 is `11T`; the OS circuit of
    switch 11 is `11T1`. So `833T` and `833T1` are different circuits (D3).
  - Outside interlocking limits a track circuit is numbered from the signal that governs over it
    (`10T`); successive circuits that govern one signal get progressive letters (placement: D6).
  - Tracks with no interlocked switches that govern no signal get arbitrary numbers that start with
    zero (D5).
  - The directional coded-track form is track number, direction, T (`1WT`, `1ET`: track 1, west or
    east side of the insulated joint). It is the source of `1SAT` ("track 1, southbound approach") and
    the like.

Open:

- O1 (D6). Section letter: after the signal number (`784LAT`, the owner's answer) or before it
  (`A10T`, the owner's statement of the AAR rule). Needed: the owner's pick; V5 may settle it.
- O2 (D2). Where a layout records its style (W/E, N/S or L/R) for tokens and panel displays, so that
  the generator reads one source. Today FieldUnit `WireCodec.h` writes N and S for LEFT and RIGHT, and
  Luchessa mixes axes (masts E/W, circuits N/S; Appendix B, B1.4 item 6). Not answered in the second
  round. Needed: the owner's choice of source.
- O3 (D5). Which symbol and `Kind` carry `HBA` and `[NSEW]FLK`. Not answered in the second round.
  Needed: the owner's choice. A candidate is `AUXILIARY` with `Functions` = `INDICATION` (ADR 0002).

### The grammar that follows

EBNF:

```ebnf
digit1       = "1" | … | "9" ;
number       = digit1 , [ digit ] , [ digit ] , [ digit ] ;   (* 1–9999 *)
lever        = [ "0" ] , number ;                (* 783 (milepost); 1 or 01 (local, D11) *)
side         = "L" | "R"                         (* code and panel *)
             | "N" | "S" | "E" | "W" ;           (* drawn style; N, W = L; S, E = R (D1) *)
letter       = "A" | … | "Z" ;

id           = lever ;
name         = id , [ letter ] ;                 (* gang id = name without its trailing letter (D8) *)
switch       = name ;                            (* SWITCH or LOCK kind; 783; gang 815, 815A, 815B... (D7, D8) *)
derail       = name ;                            (* DERAIL kind; dependent when its gang id names a switch
                                                    or lock gang: 795D; else independent: 5, 5D (D8) *)
(* every name is unique in the interlocking across switches, locks and derails (D8) *)
signal       = lever , side ;                    (* lever position: 784L, 784R; drawn 784E, 784W *)
head         = signal , letter ;                 (* 784LB; the KiCad head Value is the letter only (D9, D10) *)
mast         = signal , letter , { letter } ;    (* 784LBC: the letters of its heads, top to bottom, ascending *)

track_circuit = drawn_tc | os_tc | local_tc ;
drawn_tc     = { letter | digit } , "T" , [ digit ] ;   (* as drawn: 1SAT, 2NAAT (D4) *)
os_tc        = ( switch | derail ) , "T1" ;      (* generated: 783T1, 815AT1 (D3) *)
local_tc     = [ "0" ] , number , [ letter ] , "T" ;    (* 01T; 1T; cut sections 01AT, 01BT (D5, D11) *)

maintainer_call = "MC" , number ;                (* MC1 (D12) *)
reference    = interlocking , ":" , name ;       (* Corporal:1NAT; cross-plant reference only *)

token        = lever , ( "NWS" | "RWS" | "NWK" | "RWK" | "WLS" | "WLK" )   (* switch lever *)
             | lever , ( "NGS" | "SGS" | "HS" | "NGK" | "SGK" | "TEK" )   (* signal lever; letters in the local style (D2) *)
             | track_circuit , "K"                                        (* 783T1K *)
             | maintainer_call , ( "S" | "K" ) ;                          (* MC1S, MC1K *)
```

Regular expressions (compared case-insensitively; case preserved when produced):

| Kind | Regex | Examples |
|---|---|---|
| lever | `^0?[1-9]\d{0,3}$` | `783`, `1`, `01` |
| switch, lock, derail (name) | `^(0?[1-9]\d{0,3})([A-Z]?)$`; group 1 is the gang id | `783`, `815A`, `795D`, `5` |
| mast | `^(0?[1-9]\d{0,3})([LRNSEW])([A-Z]+)$`, letters ascending | `784LBC`, `784EAB`, `774NE` |
| head (KiCad Value) | `^[A-Z]$` | `B` |
| track circuit | `^[0-9A-Z]*T[0-9]?$` | `783T1`, `1SAT`, `01T`, `01AT` |
| maintainer call | `^MC[1-9]\d{0,3}$` | `MC1` |

Rules:

1. Every name of a switch, derail, signal, head or mast starts with a lever number. The number is the
   railroad name. KiCad references (`SW783`, `S784E1`) are never names. Track circuit names follow
   rules 8 to 10.
2. A symbol that another sheet uses or the dispatcher sees uses milepost numbering (Principle). On
   SPCoast the lever number is the milepost in tenths of the appliance (`783` at MP 78.3). Two
   appliances closer than 0.1 mile take adjacent numbers. Odd for switches and even for signals is a
   project habit. The compiler may warn on it. It is not an error (`vocabulary-review.md` F25 and §6). A local item takes
   an arbitrary short number, with or without a zero prefix (D11).
3. Switches and locks whose Values share a gang id are one gang on one lever (D8). A crossover is one
   gang: `815`, `815A`; a double crossover runs to `815C` (D7).
4. A switch, lock or derail Value is unique in the interlocking; a duplicate is an error (D8). A
   derail is dependent when its gang id is the id of a switch or lock gang in the same interlocking,
   and independent otherwise. The symbol kind, not the letter, makes it a derail. Convention: a
   dependent derail ends in D (`795D`); an independent derail has no letter or D (D8).
5. A signal is a lever position: lever number plus a side letter. The code uses L and R. A drawing,
   a token and a panel display use the local style, mapped by D1.
6. A head is a signal plus one letter, any of A–Z (D9). A head always has a letter (D10). Letters are
   unique within one signal, across all its masts. On one mast they run top to bottom in alphabetical
   order. The KiCad head Value is the letter alone.
7. A mast name is its signal plus the letters of its heads. A one-head mast and its head have the
   same full name. AAR56 names no masts; the mast name is derived and is checked against the
   attached heads.
8. A track circuit name ends in `T` or `T<digit>` (D4). A drawn name is used as drawn. A generated OS
   name is the switch or derail name plus `T1` (D3). When one circuit holds several switches and its
   name is generated, it takes the number of a movable-point frog first, then a switch, then a derail;
   among equals, the lowest number (AAR56 p. 31). A `TC` field that lists several circuits names a
   block, not one circuit (ADR 0002 D16).
9. A track circuit outside the switches keeps its drawn name. A generated name follows the AAR56 rule:
   the signal that governs over it, a section letter (placement open, O1) and T.
10. A track circuit with no switch and no governing signal takes a zero prefix, a number unique in the
    interlocking, and T (`01T`). Cut sections of one block add a section letter (`01AT`, `01BT`;
    glossary "cut section").
11. A token is a lever, track circuit or maintainer call plus a function. The function letters are
    listed in the table below and in the glossary §10.3.
12. Names are case-preserved when produced and compared case-insensitively (AGENTS.md).

Meaning of each letter:

| Letter | Position | Meaning | Source |
|---|---|---|---|
| A–Z | after a switch, lock or derail id | gang member letter; a crossover uses A, B, C; the base number is the first end | AAR56 p. 34; D7, D8 |
| D | after an id, on a derail | dependent derail by convention; not reserved | project (D8); AAR56 p. 32 gives D other meanings |
| L, R | after a lever | signal lever position left, right (code and panel) | AAR56 p. 34, Figs. 18, 22; D1 |
| N, S, E, W | after a lever | drawn side in the local style: N, W = L; S, E = R | D1 |
| A–Z | after the side letter, last letters of a head or mast | signal function (head) | AAR56 p. 34, Fig. 26; D9 |
| A–Z | before T in a generated or local name | section letter | AAR56 p. 31 ("progressive alphabetical") |
| T | last letter of a track circuit, or before a final digit | track section | AAR56 p. 34; D4 |
| T1 | after a switch or derail name | generated OS track circuit | project (D3); no source |
| 0 | first digit of a track circuit | arbitrary section, no switch, no signal | D5; AAR56 p. 31 prints `O1T` (letter or digit unverified) |
| MC | prefix | maintainer call | AAR Signal Manual Parts 33 and 91 per the owner; to verify in AAR46 (D12, V1) |
| F | traffic, in `EFLK`, `WFLK`, `NFLK`, `SFLK` | traffic direction; `FLK` traffic indicator | owner (D5); unverified (V3) |
| NW, RW | token | normal, reverse of the switch | AAR56 p. 35 |
| WL | token | electric switch lock | AAR56 p. 35 |
| G | token | signal mechanism | AAR56 p. 32 |
| N, S in NGS, SGS, NGK, SGK | token | LEFT, RIGHT (FieldUnit `WireCodec.h`); the local style (D2) | FieldUnit; AAR56 reads N as Normal and S as South or Stick |
| HS | token | hold the signal at stop | FieldUnit; AAR56 p. 37: HS = control of the home stick relay |
| TE | token | time element | AAR56 p. 38; TEK is not in AAR56 |
| K | last letter of a token | indication | AAR56 p. 32 ("Indicator") |
| S | last letter of a control token | control | FieldUnit; AAR56 has no control suffix |

## Principle (owner, 2026-10-02)

- A symbol that is local to one drawing uses a short number and a tag: switch `1`, signal `2`, circuit `1SAT`, or follows the AAR56 rules for arbitrary numbers with a zero prefix (`0<n>T`)
- A symbol that is not local, because another sheet uses it or the dispatcher sees it, uses milepost
  numbering, so that the reference is explicit: switch `783`, signal `784`, circuit `783T1`.
- A track circuit name ends in `T` or `T<digit>`. A name given on the drawing is used as drawn. A
  generated name follows the AAR56 rule.

## Context

Terms follow the settled vocabulary and the FieldUnit glossary (`docs/GLOSSARY.md`): control point (declared by one `MAIN HOUSE` symbol), interlocking (Luchessa is one interlocking with three control points), field station, OS section, track circuit, approach track circuit, control, indication. "Block" is not used for a track circuit. "Island" is not used.

Four name schemes coexist for the same kinds of appliance:

- the compass-letter masts and approach circuits of the KiCad plants (`784EAB`, `1SA`);
- the `T1` OS form (`783T1`) and mnemonic names (`IND`, `TK1`, `HBD`);
- the machine-order lever numbers of the legacy profiles and FieldUnit examples (`1`, `3`, `5`; `2NAB`);
- the milepost-tenths numbers of the Luchessa plant (`783`, `784`).

Sources, with the printed page numbers (in both PDFs the PDF page is the printed page plus 2):

- `AAR56` = *American Railway Signaling Principles and Practices*, Chapter II, AAR Signal Section, revised June 1956.
- `TT52` = Southern Pacific Coast Division Timetable 162, 1952-09-28.
- `AAR46` = AAR Signal Section, *Circuit nomenclature, written circuits, and graphical symbols*, 1946-10
  (`FieldUnit/docs/reference/`). A scan with no text layer; not read. The owner checks it visually.

What AAR56 settles:

- Lever positions are L and R (p. 34).
- A, B, C name functions of a lever or lever position (p. 34; Fig. 26, p. 33).
- A track circuit is a number plus T. The number is that of a switch in it, else of the signal that governs over it, else arbitrary (`O1T`) (p. 31).
- TK is the track indication. NWK and RWK are the switch indications (pp. 34-36).

What TT52 supports: on the SP Coast Line the timetable direction is east/west, and signal numbers equal
the milepost in tenths (the timetable's Rule 105 entry, which bounds sidings by automatic signal numbers;
p. 28).

Drawing conventions today (owner, 2026-10-03): the track diagrams and code line charts the owner has
use several conventions over several eras. The South-cTc schematics do not follow the AAR forms; they
follow ATCS-inspired forms that may be layman-derived (for example the directional , D15). This
is context, not a rule.

What neither settles: mast names, head order, the form of control tokens, `T1`, dependent derail names, odd/even numbering, and whether milepost numbers apply to switches and CTC signals. For longevity, most railroads used milepost-based IDs for switches and signals used by the dispatcher.

Appendix B, B1, lists the evidence and the points where the references allow two readings.

## Consequences

### Names that change under the Decisions

Derived from the rows of Appendix B, B2.1 (plant netlists of 2026-10-01), not re-read from the
netlists. A name fails when a track circuit does not end in `T` or `T<digit>`, a Value is empty, or a
name is not a track circuit but sits on a `Track Circuit` symbol. Compass-letter masts, `T1` OS names,
`815`/`815A` crossover ends and the local switch `1` now fit.

| Plant | Failing names | Count |
|---|---|---|
| Luchessa | `1SA`, `2SA`, `1NA`, `2NA`, `3NA`, `2NAA` (renamed in the schematic, D4); MC1 `~` | 7 |
| Christopher | `1SA`, `2SA`, `1NA`, `2NA`; `IND`; 2 empty mast Values; 5 empty head Values | 12 |
| Corporal | `IND` | 1 |
| GilroyCalTrain | `1SA`, `1NA`; `TK1`, `TK2`, `TK3` | 5 |
| GilroyInterchange | `1SA`; `INTER`; `TK1` | 3 |
| Sargent | `1SA`, `2SA`, `1NA`; `HBD` (not a track circuit; now `HBA`, changed by the owner on 2026-10-03, to be re-checked; D5, O3); `Corporal:2NA` (no final T, and Corporal has no `2NA`) | 5 |
| Total | | 33 |

Watsonville is excluded (as of 2026-10-01, changed by the owner on 2026-10-02, to be re-checked).
GilroyCalTrain (as of 2026-10-01, changed by the owner on 2026-10-02, to be re-checked): switch 771's
`TC` list is a block under ADR 0002 D16 and fits.

Desk netlist (`South-cTc.net`, B2.5): the 14 OS names in `T1` form fit. 10 track circuit names fail:
the 6 approach names (`1SA`, `1NA`, `2SA`, `2NA`, `2NAA`, `SA1`), `TK1`–`TK3` and `XNA`. `SDT`, `ART`,
`ALT` and `SAT` fit the syntax. `HBD`, `TL` and `TR` are not track circuits; the owner renamed them
`HBA` and `[NSEW]FLK` on 2026-10-03 (D5, O3; to be re-checked in a new netlist).

Profiles, FieldUnit examples and FieldUnit docs are not recounted. The same test applies: approach
names without a final T (`1SA`, `1WA`, `1EA`), mnemonics (`IND`, `TK1`, `EA1`, `INTER`) and `HBD`,
`TL`, `TR` (now `HBA`, `[NSEW]FLK`). Mixed-case masts (`2Nab`) fit, because names are compared case-insensitively. The counts
under the earlier proposal are kept in Appendix B, B2.

Also affected, not counted: FieldUnit-Subdivision tests and fixtures hard-code Luchessa names (`tests/test_kicad_plant_graph.py`, `tests/test_controller_graph.py`, `tests/fixtures/kicad/Luchessa.plant-model.json`, `tools/run_plant_graph_smoke.sh`, `runtime/plant_host/spcoast_virtual_plant.cpp`). Per AGENTS.md they change in a separate step.

Order of authority: the relay model and AAR practice first, then FieldUnit `src/`, then KiCad-derived models. Legacy sketches and XML-harvested profiles are evidence only. Names found only in legacy sketches or in legacy `CP_*.json` profiles do not weigh on the decision. Their counts are kept in Appendix B as facts.

### Cost on the built CTC machine and on verified tokens

- OS names do not change (D3). Tokens verified in the `T1` form (`783T1K`) stay.
- Approach circuit names gain a final T in the plants and on the desk together (`1SA` → `1SAT`, so
  `1SAK` → `1SATK`): the desk `IndicationToken` fields, `configureDesk()` in `spcoast_ctc` and the
  token lists of the virtual plant. The desk linker pairs by normalized name, so the names must change
  in the plants and the desk together.
- FieldUnit `WireCodec.h` appends `K` to a track name unless the name already ends in K. With every
  track circuit ending in `T` or `T<digit>`, that special case can go.
- Signal tokens (`NGS`, `SGK`) are not renamed (D2).
- Two pairing faults exist whatever the grammar (see Appendix B, B2.5).

### What changes in the compiler

`tools/plant_graph/compiler.py` and `tools/plant_graph/routes.py`:

| Item | Today | Change |
|---|---|---|
| `_MAST_VALUE_RE` | `^(\d+)([NSEW])([A-E]+)$`, defined twice (compiler.py:114, routes.py:29) | `^(0?[1-9]\d{0,3})([LRNSEW])([A-Z]+)$`, one definition imported by both. Add: letters ascending; a letter used once per signal across masts. |
| `_DEFAULT_MAST_DIRECTION_MAP`, `mast_direction_map` parameter, `PlantGraph.mast_direction_map` | N/W → LEFT, S/E → RIGHT | One fixed map (D1): L, N, W → LEFT; R, S, E → RIGHT. The parameter goes, because the mapping is fixed. |
| `bad_mast_value` message | says `<signal><N\|S><heads>` while the regex accepts NSEW | Message follows the regex. |
| `_derive_os_circuits` default | `f"{name}T1"` | No change (D3). Validate each `TC` entry against the track circuit rule (D4). A list in one `TC` field names a block (ADR 0002 D16); it is not an error. |
| Switch Value | any non-empty string | See the next row. Diagnostic `bad_switch_value`. |
| Switch, lock and derail Values | compiler.py:907 `(\d+)(D)?`; `_check_dependent_derail_allocations` (compiler.py:1461) keys on `endswith("D")`; `_derail_models` (model.py:516, 528, 533) sets dependence and `controllingSwitch` from a trailing D; the crossover group (model.py:540-555) keys on a trailing `B` | `^(0?[1-9]\d{0,3})([A-Z]?)$` (D8). Error on a Value used twice across switches, locks and derails. Gang = switches and locks with one gang id. A derail is dependent when its gang id matches a gang; `controllingSwitch` names that gang. Nothing keys on the letter D or B. |
| Head Value | `^[A-E]$` | `^[A-Z]$` (D9). Empty `~` heads already fail (D10). |
| Track Circuit Value | any non-empty string | Ends in `T` or `T<digit>` (D4), a warning first. Accept `<Interlocking>:` references. The proposed side-letter check is dropped: drawn names are used as drawn. |
| MaintainerCall Value | not checked | `^MC[1-9]\d{0,3}$` (D12). |
| Lever parity | not checked | Optional warning: switch even or signal odd. Not an error (§6, F25). |
| `_PART_KIND` | 25 parts | Goes (ADR 0002 D2). Observed in the netlists and missing from the map today: `Switch_HandThrow`, `Switch_Powered_NO_TC`, `Track Circuit_Yellow`, `Rule6.13-Yard Limits`. These raise `unknown_symbol` today. The kind for `HBA` and `[NSEW]FLK` is O3. |

Outside the plant compiler: the desk `IndicationToken` fields and `configureDesk()` change with the plants. The desk linker pairs by normalized name.

### Outside the plant compiler (D8)

The derail and gang rule (D8) also touches:

- FieldUnit `InterlockingPlant::addDerail` (`src/InterlockingPlant.h`): it parses a trailing D, takes
  the rest as the base switch, and refuses a `*D` name with no base. It changes to take dependence from
  the model (an explicit base, as the portable model's `controllingSwitch` already carries). FieldUnit
  `PlantSerializer.h` (derails "dependent *D", lines 346 and 598) follows. An issue is to be filed.
- FieldUnit `docs/how-to/05_derails_and_os_binding.md` section 2 ("`D` is reserved for derails. The
  suffix `D` must not name a crossover end."). Listed here; not edited.
- The glossary entries "dependent derail", "independent derail", "crossover" and §10.2, and the
  AGENTS.md line on the dependent derail Value: updated with this ADR.

### To check in the 1946 AAR document

One sitting with `FieldUnit/docs/reference/AAR. Signal Section. Circuit nomenclature, written circuits,
and graphical symbols. 1946-10.pdf` (AAR46; likely AAR Signal Manual Part 33, per the owner). For each
item, note the page and the exact form. The owner's second-round answers (Appendix A) give the
expected result; the check confirms it in the document.

- V1. `MC`: listed as maintainer call, with `MCS` and `MCK` (owner: Parts 33 and 91)? (D12)
- V2. `HBA` (hot box alarm): listed in AAR46? The owner's source is ATCS 250 material, a later
  standard. (D5)
- V3. `F` (traffic) and `FLK` (traffic indicator) with a direction letter (`EFLK`, `WFLK`, `NFLK`,
  `SFLK`): listed in AAR46? (D5)
- V4. Zero prefix: the owner answers the digit zero. Confirm the AAR46 form (`01T`; AAR56 p. 31 reads
  `O1T` in our copy) and the scope of the rule. (D5)
- V5. Section letter: which form does AAR46 show, `784LAT` or `A10T`? This can settle D6.
- V6. Optional. The track circuit rule (number plus T; frog, switch, derail preference) and the reading
  of a trailing digit as a wire's contact count (AAR56 p. 32), which bears on `T1` (D3, D15).

## Appendix A: the questions and the owner's responses, verbatim

The questions as asked on 2026-10-02, with the owner's responses unchanged. "Recommended" and
"the proposal" in the text below mean the earlier proposal, kept in Appendix B, B3.

Answer each item with one line. The recommended default is the first option. "Q" numbers are the question numbers of the earlier proposal; the appendices use them. The items are ordered by the number of names each one renames.

1. Q1. Signal direction letter: DECIDED (owner, 2026-10-02). Panels and code conventions use L and R;
   they do not depend on railroad, geography or era. A schematic track diagram can use N/S, E/W or
   L/R as local policy decides. The fixed mapping is Left = North and West; Right = South and East.
   Mast names drawn with compass letters therefore stay valid; the compiler maps them to L and R.
2. Q3. OS track circuit suffix: DECIDED (owner, 2026-10-02). An OS track circuit generated from the
   switch number is `<switch>T1`. This keeps it distinct from other circuits that end in `T`; `833T`
   and `833T1` can both exist. The AAR56 `<number>T` form is not used for OS circuits.
3. Q4. Approach track circuit names: DECIDED (owner, 2026-10-02). A track circuit name ends in `T` or
   `T<digit>`. When the drawing gives a name (`1SAT`), the tooling uses it. When no name is given, the
   AAR56 rule is authoritative for the generated name. Luchessa's circuits are renamed in the
   schematic (`1SA`→`1SAT`, `2NAA`→`2NAAT`, and so on).

4. Q9. Circuits with no switch and no signal: AAR `O<n>T` (`O1T`), or mnemonics (`IND`, `TK1`)? And do `HBD`, `TL`, `TR`, which are not track circuits, get their own kinds? Recommended: `O<n>T`, and own kinds.

   RESPONSE: While not used in these South-cTc plans, the AAR scheme should be part of the layout designer documentation.  As with other specialized tokens, the semantic value associated with them should be minimal.  Where AAR has defined terminology, it should be documented and used.  The ones you mention were takeen from forum threads and may not be AAR...
   HBD - hot box detector
   TL/TR - left and right traffic indications

   Arbitrary numbers with a zero prefix (0<n>T) are explicitly assigned to isolated or auxiliary track segments—such as plain stretch blocks, specialized detector circuits, or crossing approaches—where no switch points exist and no governing signal is directly attached

5. Q5. Section letter: after the side (`784LAT`) or as a true prefix (`A784LT`)? Recommended: after the side.

    RESPONSE: Not sure what is meant here.  Is it related to `/Users/jplocher/Dropbox/Arduino/libraries/FieldUnit/docs/reference/AAR. Signal Section. Circuit nomenclature, written circuits, and graphical symbols. 1946-10.pdf`?

6. Q6. Crossover ends: both lettered (`815A`, `815B`) or base plus letter (`815`, `815A`)? Recommended: both lettered.

    RESPONSE: For simple crossovers, base plus letter: (`815`, `815A`) and for doubles, (`815`, `815A`, `815B`, `815C`)
    (`815D`) is used as a DERAIL reference, though with recent changes, I don't believe the "D" is still special

7. Q10. Name of a hand-throw (non-interlocked) switch: milepost number like any switch? Recommended: milepost number. Corporal `SW901` and Sargent `SW3` now carry `1`.
   
   RESPONSE: Local non-dispatcher seen/controlled items usually don't have milepost names, but instead have arbitrary numbers with or without a zero prefix (0<n>T) or ([1..9]T)

8. Q2. Signal tokens: keep `NGS/SGS/NGK/SGK` as FieldUnit wire names with a glossary note, or move to `LGS/RGS/LGK/RGK`? Recommended: decide separately; it is a code line API change.

    RESPONSE: local era/railroad/geography/policy dictates drawing, token and panel displays (W/E, N/S, L/R), our code uses L/R internally but keeps user-provided style.

9.  Q7. Dependent derail: keep `<switch>D` (`795D`)? Recommended: keep.
    RESPONSE: keep

10. Q8. Are head letters A-E enough? Recommended: yes (the maximum in use is E, at GilroyCalTrain).
    
    RESPONSE: don't limit them.  All single letters should be usable.

11. Q11. May a one-head signal omit its letter (`10R`, as AAR56 allows)? Recommended: no; always a letter.

    RESPONSE: always a letter

12. Q13. Keep maintainer call `MC<n>`, which has no period source? Recommended: keep, marked as FieldUnit.

    RESPONSE:

The Association of American Railroads (AAR) establishes standard technical guidelines, circuit nomenclature, and specifications for Maintainer Call (MC) systems used across North American railroads. [1, 2] 
In standard AAR signal manuals and standard railroad plans (such as Conrail or ATSF design catalogs), the specific designation token for these systems is MC. [1, 3] 
Here is how the AAR standards govern the levers, switches, and lamps for these systems:
### 1. The AAR Token & Lamp Specifications (MC)

* Nomenclature: On a signal circuit drawing or control board layout, a lamp designated as MC explicitly stands for Maintainer's Call.
* AAR Bulb Standards: The AAR Signal Manual (specifically Part 91) categorizes bulbs by manufacturing dimensions, base styles, and filaments (such as those detailed under AAR drawings 1541, 1542, and 1543). 
* Physical Lamp Purpose: When a dispatcher activates the MC system, it lights a steady white or clear bulb inside a weatherproof housing mounted on the exterior wall of a wayside signal bungalow or relay house at an interlocking. 

### 2. Control Machine Levers and Toggles
On vintage Union Switch & Signal (US&S) or General Railway Signal (GRS) Centralized Traffic Control (CTC) machines, the maintainer call function is assigned a control interface directly beneath the track model board: 

* The Toggle Switch: Because maintainer calls do not require mechanical safety interlocking logic (they don't change track switches or clear trains), they do not use the large "Armstrong" or heavy rotary levers. Instead, they use small two-position toggle switches or push-buttons located on the console panel. [4, 5, 6] 
* Operation Sequence: To signal a maintainer, the train dispatcher flips the field station's MC toggle switch to "ON" and hits the Code Start button to send a pneumatic or electronic code out to that field location. 

### 3. Indication Lamps on the Console

* The Repeater Lamp: Right next to or directly below the field code buttons on the dispatcher's console, there is a small panel indication lamp. 
* AAR Classification: This is an AAR-standardized LL (Lever Light) or IND (Indication) lamp. It illuminates on the dispatcher's board to confirm that the code successfully went out and that the field MC light is actively burning on the wayside bungalow. 

### Historic Context
Before the widespread adoption of two-way locomotive and trackside radios, the Maintainer Call system was vital. While called a "Maintainer" call, railroad operating rulebooks typically mandated that any railroad employee (including conductors or engineers) who spotted a lit MC lamp on a wayside building had to immediately stop at the nearest wayside telephone box to contact the dispatcher. 



Questions not asked:

- Q12 (staging yards of the Watsonville schematic) was withdrawn by the owner. Model-layout yards will be supported by the tooling later. 
  
  RESPONSE: The Watsonville schematic has been updated and can now be rechecked.
  
- ADR 0001 D12 (as amended) answers any question about a `CP_` or `CP ` prefix and about normalizing names. A KiCad name has no prefix, a model board may add `CP ` for display, and a space becomes `-` in a topic or key. This ADR adds no prefix rule and no normalization.


### Second round (2026-10-03)

The owner typed these into the first final-review form. They are kept unchanged.

Inline edit of D5 (Q9):

- D5. Circuits with no switch and no signal; specialized tokens (Q9). The AAR scheme is part of the
  layout designer documentation, although these South-cTc plans do not use it. Where AAR has defined
  terminology, it is documented and used; specialized tokens carry minimal semantic value.
  - Arbitrary numbers with a zero prefix, `0<n>T` (`01T`), name isolated or auxiliary track segments
    where no switch points exist and no governing signal is directly attached (the owner's examples:
    plain stretch blocks, specialized detector circuits, crossing approaches).
  - `HBD` (NOW HBA - Hot Box Alarm) is a hot box detector. `TL` and `TR` (now [N,S,E,W]FLK) are left and right traffic indications. None of them is
    a track circuit. They came from forum threads and may not be AAR.
      - The AAR status of `HBD`, `TL`/`TR` and the zero prefix is unverified until the 1946 AAR nomenclature
        document is checked (see Consequences, "To check in the 1946 AAR document").

Responses under the 1946 check list:

### To check in the 1946 AAR document

One sitting with `FieldUnit/docs/reference/AAR. Signal Section. Circuit nomenclature, written circuits,
and graphical symbols. 1946-10.pdf` (AAR46). For each item, note the page and the exact form.

- V1. `MC`. Is `MC` listed, and as what: maintainer call, a lamp, a control, a relay? The owner's
  summary (Appendix A, Q13) cites this document as its source [2] and also claims the AAR lamp classes
  "LL (Lever Light)" and "IND (Indication)". Check each claim (D12).

RESPONSE:
The reference is Part 33 Circuit Nomenclature.
AAR Maintainer Call (MC) tokens and abbreviations are defined in the Association of American Railroads (AAR) Signal Manual, specifically under Part 33 (Circuit Nomenclature and Written Circuits) and Part 91 (Lamp Use and Abbreviations).

* AAR Signal Manual Part 33 (Circuit Nomenclature): Dictates the standard alphabetic term sequencing and prefix rules used to define electrically operated railroad signal units, wire labels, and relays.
* AAR Signal Manual Part 91: Defines standard material categories, design drawings (e.g., drawings 1541, 1542, 1543), and operational abbreviations. Under this section, MC is designated as the abbreviation for a Maintainer's Call indicator lamp or feature.
* Conrail's CS-4000 standard (1981) for electric lamps defines lamp abbreviations:
CGA - crossing gate arm
CTI - Chart Track Indicator
ESL - Electric Switch Lock
HCD - High Car Detector
HBR - Hot Box Recorder
IND - Indication
LL  - Lever Light
MC  - Maintainer's call
PT  - Pole Target
SL  - Switch Lamp
TO  - Train Order

* Control Token: MCS, ECS or MCR (Maintainer Call Relay) — This represents the control code sent from the dispatcher's machine to the field location to activate the maintainer's call light or horn.
* Indication Token: MCK (Maintainer Call Indication / "Keep" light) or ECK — This represents the return indication code sent back from the field to the dispatcher's console, illuminating the indication lamp to confirm that the maintainer call is actively operating in the field

- V2. `HBD`. Is `HBD` listed as hot box detector (D5)?
HBA seems to be the proper name.  I changed Sargent's use.

Defined in the ATCS series of communication standards

The AAR (Association of American Railroads) standardizes wayside defect data and Centralized Traffic Control (CTC) codeline commands through the Advanced Train Control System (ATCS) Specification 200 series (specifically ATCS 250). 
In ATCS network protocol formatting, data fields are designated as tokens or byte flags that represent specific control actions and indication telemetry sent between the central office (CAD system) and the wayside equipment shelter. 

Indication Tokens (Wayside-to-Office)
Indication bytes pass telemetry back to the dispatcher's office or network management server when a train transitions over a detector:

* HBA (Hot Box Alarm): A high-level boolean token indicating that at least one journal bearing has exceeded the critical temperature threshold. 
* HWA (Hot Wheel Alarm): Triggered when a dragging brake or locked wheel causes a wheel rim to overheat. 
* DED (Dragging Equipment Detector): Flags that a dragging object has broken or struck the trackside structural plates.
* AXLE_CNT (Axle Count): On digital codelines, a numeric token providing the total integer count of passing axles used to verify train integrity and pinpoint defect positions.
* DET_SYS_OK / FLT: A health status token verifying system calibration and functionality, or indicating a localized hardware failure. 

Control Tokens (Office-to-Wayside)
Control bytes allow the dispatcher or centralized management system to interact directly with the field installation: 

* ALM_RST (Alarm Reset): Remotely resets the wayside visual indicator lamps, alarm stick relays, or talker sub-systems after an inspection is completed.
* SYS_EN / SYS_DIS (System Enable/Disable): Toggles the operational state of the monitoring site or forces an override state.
* DIAG_REQ (Diagnostics Request): Prompts the field microprocessor to run self-calibration routines and transmit back DET_SYS_OK and an event log. 


- V3. `TL`, `TR`. Are they listed as left and right traffic indications (D5)? AAR56 p. 34 uses `TR` for
  the track relay (glossary `TR`). Note whether AAR46 gives `TR` both meanings, and how position
  separates them.

  RESPONSE: These should be EFLK/WFLK or SFLK/NFLK.  I updated the schematics.

==========
  In the Association of American Railroads (AAR) standard signal nomenclature for Centralized Traffic Control (CTC) and codeline transmission, the primary letter token designated for Traffic Direction is F.
To control and indicate the directional flow of traffic across a codeline circuit, F is paired with geographical direction prefixes and functional suffixes:

**Geographical Direction Prefixes**  
These tokens are placed before F to specify the direction of train movement being authorized or indicated:

* E – East / Eastward
* W – West / Westward
* N – North / Northward
* S – South / Southward

**Standard Codeline Control & Indication Tokens**  
These mnemonic combinations are mapped directly to specific bits in the codeline byte structure to control and read back traffic status:

| Token | Meaning & System Role |
|---|---|
| FR | Traffic Relay – The basic unit or bit state defining traffic direction authority. |
| FSR | Traffic Stick Relay – Used to lock and hold the requested traffic direction until a block clears. |
| EFSR / WFSR | East / West Traffic Stick Relay – Specific directional stick controls/indications transmitted via the codeline. |
| EFR / WFR | Eastward / Westward Traffic Relay – Active bits representing established traffic direction (or NFR / SFR for North/South lines). |
| FLR | Traffic Locking Relay – Ensures a traffic direction request cannot be reversed while a route is lined or a block is occupied. |
| FLK | Traffic Indicator – The indication code sent back to the dispatcher's office to illuminate the panel status. |

==========

- V4. Zero prefix. Is the arbitrary track circuit number written with the digit zero (`01T`) or the
  letter O (`O1T`, as AAR56 p. 31 reads in our copy)? Does the rule cover "isolated or auxiliary"
  segments (plain stretch, detector circuits, crossing approaches), or only circuits "in which there
  are no interlocked switches and which do not govern signals" (AAR56 wording) (D5)?

  RESPONSE:  the number ZERO (0).  In addition single digits serve the same purpose in a plant where dispatcher- and cross-interlocking items use milepost-based numbers.

- V5. Section letter (Q5, O1). Is there an example of "progressive alphabetical prefixes" that shows
  where the letter goes (`784LAT` or `A784LT`)?

      RESPONSE: The latter: A784LT which conflicts with the practice used in these schematics.  The failure case in the schematics is the slight ambiguity with head letters.

- V6. Optional. Does AAR46 state the track circuit rule as AAR56 p. 31 does (number plus T; frog,
  switch, derail preference), and does it read a trailing digit as a wire's contact count (AAR56 p. 32),
  which bears on `T1` (D3)?

    RESPONSE:   The track diagrams and codeline charts I have use several conventions over several eras; the South-cTc schematics DO NOT correctly follow the AAR forms, but do follow ATCS-inspired forms that may be layman derived and thus misinformed.

    my understanding is that 
    - Within Interlocking Limits (switches and derails) a track circuit enclosing Switch #11 is named 11T, or if the TC is the OS circuit, 11T1
    - Outside Interlocking Limits (signals), a TC should be numbered based on the roadway signal governing over it,
       - If multiple sequential track circuits govern a single signal, progressive alphabetical letters are added to differentiate the sections.
           - Example: The primary track circuit directly ahead of Signal 10 is named 10T.
           - Example: If there are three successive track circuits approaching or governing Signal 10, they are prefixed sequentially as A10T, B10T, and C10T
    - For tracks that feature no interlocked switches and do not govern any active block signals (such as storage tracks, specific yard tracks, or isolated sidings), arbitrary sequential numbers starting with zero are assigned
    - Directional Coded Track (e.g., 1WT / 1ET): In modern Coded Track Circuit territory, a circuit may combine the track number, direction, and the letter T (e.g., Track 1, West side of the insulated joint = 1WT).  This is where "1SAT" and friends come from - 1SAT -> southbound approach...

Rule change given in chat (owner, 2026-10-03), as relayed: "dependence and ganging are decided by the
symbol kind and the name relation, not by the letter D"; a name is `<id>[<letter>]`; the full Value is
unique within an interlocking across switches, locks and derails, and a derail `815A` beside a switch
`815A` is a name collision and a compiler error; gang id = Value minus its trailing letter; a DERAIL
whose gang id matches a switch or lock gang is dependent on it, otherwise independent; the letter D is
the convention, not the mechanism. This replaces the earlier D8.

## Appendix B: evidence and inventory

### B1. Evidence from the 1956 chapter and the 1952 timetable

#### B1.1 AAR 1956, Chapter II

| Point | What the document shows | Page |
|---|---|---|
| Structure of a name | "a designation made up of two parts": a numerical prefix ("the number of the principal lever, signal, track circuit, or other device") and an alphabetic term. "The last letter … designates the general kind of unit, while the first letter or letters … describe specifically the operated unit." Example `10HR`: 10 is the signal, R a relay, H the home function. | 31 |
| One letter, several meanings | "N" is Normal, Negative and North; the meaning follows from position "with respect to numerals and other letters". | 31 |
| Letter table | A Approach. D Proceed indication, Detector, Decoding, Dragging. E East. G Signal (operating mechanism). H Home, approach indication. K Indicator. L Left, Lever, Lock. N Normal, North. R Right, Reverse, Relay, Stop indication. S South, Stick, Storage. T Track, Time. W Switch, West. Z special. | 32 |
| Lever position L/R | "In order to distinguish between right and left position of three-position levers, use R (right) or L (left) after the lever number, as 10R, 10L." | 34 |
| Lever with several functions | "When one lever controls two or more functions, use letters A, B, C, etc., after the lever numbers: for example, 10A, 10B, 10C." Three-position lever with several functions in each position: "10RA, 10LA". | 34 |
| Lever positions drawn | Levers with the middle position as normal have positions L (reverse to left), N (normal), R (reverse to right). | Fig. 18 p. 23; Fig. 22 p. 27 |
| A/B/C on the plan | Fig. 26: `2RA`, `2RB` and `2RC` are three signals on three different tracks (`2RB` is a dwarf). `2L` is one mast with two arms marked A and B; relay names `2LAHR`, `2LBLR` use them. Automatic signals are `108` and `110`. | 33 |
| Track circuit | "A track circuit is designated by the letter T preceded by a number." Inside interlocking limits it takes the number of a movable-point frog, switch or derail inside it, "the preference being in the order named". Otherwise "it is numbered from a signal governing over the track circuit. Progressive alphabetical prefixes are used in the case of a plurality of track sections that govern one signal." "Arbitrary numbers, as O1T, O2T, O3T, etc., are given track circuits in which there are no interlocked switches and which do not govern signals." | 31 |
| Track names in Fig. 26 | `1T`, `3T` (switch numbers); `108T`, `110T` (signal numbers). | 33 |
| Track units | T track section; TR track relay; TK "indicator, indicating condition of a track circuit". | 34 |
| Switch units | NWK, RWK "indicator indicating the normal (reverse) position of a switch"; WK; WL switch lock; NW, RW normal and reverse control wires. | 35–36 |
| Signal units | RGK, HGK, DGK indicators of the signal mechanism at stop, approach, proceed. HS "positive control of HSR" (home stick relay). | 36–37 |
| Compass letters | Used as a first letter on directional units: "ESR — East stick relay, likewise north, south and west"; EB, EC, EAX, ETOHR. Not used on signal names. | 34, 37, 39 |
| Wire names | A trailing number is "the number of circuit controlling contacts in the circuit between the wire and unit" (`2LAH1`, `3TP1`). | 32–33 |
| Appliance numbers | Fig. 6 numbers appliances 1–12: crossover 2 (both ends marked 2), derail 3, slip switches 4 and 5, movable-point frog 6, dual-control switch 12. Switch-type appliances carry even numbers. | 9 |

AAR56 is silent on: a name for a mast; head order top to bottom; milepost numbers; an odd/even
rule for switches and signals; CTC codes (`NWS`, `NGS`, `SGK`, `TEK`, `MC`); the term "OS";
the form `T1`; the name of a dependent derail.

On A/B/C: the letter names a function of a lever position. Fig. 26 uses it for separate
signals on separate tracks (`2RA`, `2RB`, `2RC`) and for two arms on one mast (`2LA`, `2LB`). The
letter does not say whether functions share a mast. In color-light terms one function is one head.
Fig. 26 does not state which arm of `2L` is the top arm.

#### B1.2 SP Coast Division Timetable 162 (1952)

| Point | What the document shows | Page |
|---|---|---|
| Timetable direction | Schedules are EASTWARD and WESTWARD. Eastward runs San Francisco → San Jose → Watsonville Jct., in increasing milepost. | 2, 14 |
| Signal numbers | Salinas Subdivision Rule 105: "No. 1 siding at Salinas extends from Signal 1164 to crossover just west of Signal 1178. No. 2 siding extends from crossover just east of Signal 1178 to crossover just west of Signal 1186." Salinas is MP 118.2. The numbers equal the milepost in tenths. | 28, 18 |
| Gilroy Subdivision | Automatic block signals, double track Lick–Coyote, Gilroy–Corporal, Logan–Aromas. Gilroy MP 80.7, Carnadero 83.2, Corporal 86.4, Sargent 87.1. No Luchessa or Christopher station. | 14–17 |
| CTC | Only Santa Margarita–San Luis Obispo is marked Centralized Traffic Control. | 22–23 |

TT52 is silent on: switch and lever numbers; track circuit names; mast and head letters; signal
direction letters; odd/even. It states no numbering rule; the milepost reading is an inference from
three numbers. It gives no example of a milepost number on a CTC or interlocked signal.

#### B1.3 Where the references allow two readings

"Proposed" in this table marks the earlier proposal. The Decisions settle R1 (D1, D2: L and R in the
code, the local style on drawings), R3 (D3: `<switch>T1`), R4 and R5 (D4, D6: drawn names are kept;
the generated form waits for O1) and R7 (D8: dependence by symbol kind and gang id; `D` by convention). R6 follows the Principle: milepost numbers
for non-local items, arbitrary numbers for local ones (D11). R2 stands as evidence.

| # | Question | Reading 1 | Reading 2 | Cost of the proposal |
|---|---|---|---|---|
| R1 | Direction letter on a signal | L/R, the lever position (AAR56 p. 34). Proposed. Matches FieldUnit `LEFT`/`RIGHT`. Removes `_DEFAULT_MAST_DIRECTION_MAP`. | E/W, the timetable direction (TT52 p. 2, 14), in the AAR56 style of compass first letters (ESR). | L/R renames all 25 named masts, including Luchessa's E/W ones. E/W renames 20 and keeps a translation map. Status quo N/S matches no timetable direction on the Coast Line. |
| R2 | A, B on a signal: masts or heads | One reading only: functions of a lever position, either way (Fig. 26). | — | None. Luchessa already uses it (`784WA`, `784WBC`, `784WD`). |
| R3 | OS name | `<switch>T` (AAR56 p. 31). Proposed. Token `783TK` is the AAR TK. | `<switch>T1` (project). No source. AAR56 p. 32 reads a trailing digit as a wire's contact count. | Every OS name changes: plants, profiles, desk tokens, tests, compiler default. |
| R4 | Number of an approach track circuit | The plant signal that governs over it (AAR56 p. 31): `784LAT`. Proposed. Needs nothing outside the plant. | The automatic signal that governs over it, numbered by milepost (TT52 p. 28; AAR56 Fig. 26 `108T`): `780T`. The handoff alias `2NAA → 797T` already uses this form. | Reading 2 needs a milepost for each section and signals that may not exist on the layout. It gives subdivision-unique names and no side letter. |
| R5 | "Progressive alphabetical prefixes" | A letter before T: `784LAT`. Proposed. | A letter before the number: `A784LT`. | The text does not show an example. Reading 2 breaks rule 1 (names start with the lever number). |
| R6 | Lever numbers | Milepost tenths (TT52 p. 28, for automatic signals only). Proposed for SPCoast. | Machine lever order 1…n (AAR56 Figs. 6, 26; legacy `CP_*.json`). | Reading 2 repeats numbers in every plant (`1` everywhere) and needs a plant qualifier in every reference. |
| R7 | Dependent derail | `<switch>D` (project, already in compiler and FieldUnit). Proposed. | A function letter of the switch lever (`795B`), as AAR56 p. 34 would give. | Reading 2 makes the switch itself `795A` and collides with crossover end letters. |

#### B1.4 Contradictions with `vocabulary-review.md`

1. F16 counts one scheme as two. It sets `2R/2LA/2LB` ("A and B are separate masts") against
   `2NAB` ("A and B are heads on one mast"). AAR56 Fig. 26 (p. 33) uses one rule for both: the
   letter is a function of a lever position, on one mast or on several. The schemes differ only
   in the direction letter (L/R or compass) and in whether the mast name lists all its letters.
2. F16 says track circuit names "have no rule". The project has none. AAR56 p. 31 has one,
   and the proposal uses it.
3. F25 is rated "recall". AAR56 Fig. 6 (p. 9) numbers a crossover 2, slip switches 4, a
   movable-point frog 6 and 8, and a dual-control switch 12. The AAR does not reserve odd numbers
   for switches. F25 can be rated "checked".
4. F9 is confirmed. AAR56 p. 32: G is Signal; S is South, Stick, Storage, Southward. No source
   reserves S for Signal.
5. F12 ("1NA is an approach circuit by name and an Exit Block in Tutorial 1"). Both uses are
   correct for opposite directions: `1NA` is the approach track circuit for leftward moves and
   the exit for rightward moves. The proposed names record the governing signal and side, not
   "approach", so the conflict leaves the name.
6. One letter set, two axes. The review does not note that Luchessa mixes axes: masts use E/W
   (`784EAB`), track circuits use N/S (`1SA`). FieldUnit tokens use N/S for LEFT/RIGHT
   (`WireCodec.h`; Primer §10 "2SGS … South/Right"). Any choice in R1 leaves either the names or
   the tokens on a different letter set until Q2 is decided.
7. Model mileposts are not the 1952 mileposts. TT52 puts Corporal at MP 86.4 and Sargent at
   87.1 (p. 14). The layout numbers them 829–832 and 835–836. This extends F28; it does not block
   the grammar.

### B2. Every name that fails the grammar as first proposed, by source, with the corrected name

A dated record. The corrections below follow the earlier proposal; under the Decisions most of these
names stay (compass-letter masts, `T1` OS names, `815`/`815A`, the local switch `1`). Consequences,
"Names that change under the Decisions", gives what still fails.

Counts under the earlier proposal (distinct failing names; the sections below list each name and its
correction):

| Source | Failing names |
|---|---|
| Plant netlists (6 valid) | 79 without Watsonville (Luchessa 15, Christopher 22, Corporal 12, GilroyCalTrain 11, GilroyInterchange 9, Sargent 10). Watsonville was excluded (was 144 with its 65; as of 2026-10-01, changed by the owner on 2026-10-02, to be re-checked). |
| Profiles | 62 (legacy 37 including the legacy `CP_Watsonville.json` 5, `generated/Luchessa.json` 14, sidecar 11) |
| FieldUnit examples | 55 |
| FieldUnit docs | 84 |
| Desk netlist (extra) | 31 |

Corrections use the proposal (L/R, `T`, plant-signal approach names). "Side" mapping: the current
letter names the direction of the approaching train (`1SA` is the entrance for RIGHT routes in
`generated/Luchessa.json`), so S/E approach circuits lie on the left and become `<signal>L…T`,
N/W approach circuits lie on the right and become `<signal>R…T`. Section letters are a first
assignment for the owner to confirm. "?" means the correction needs a fact not in the source.

Counts are distinct names per file. Names that fail only the SPCoast milepost rule (legacy `1`,
`3`, `5`, `2`) are noted per file and not counted.

#### B2.1 Plant netlists, `~/Dropbox/KiCad/Railroad/SPCoast/<Project>/<Project>.net`

All seven netlists were newer than their schematics at read time.

Luchessa.net (15)

| Ref | Kind | Now | Proposed |
|---|---|---|---|
| S784E1 | mast | `784EAB` | `784RAB` |
| S784E2 | mast | `784EC` | `784RC` |
| S784W1 | mast | `784WA` | `784LA` |
| S784W2 | mast | `784WBC` | `784LBC` |
| S784W3 | mast | `784WD` | `784LD` |
| TC6 | approach | `1SA` | `784LAT` |
| TC5 | approach | `2SA` | `784LBT` |
| TC3 | approach | `1NA` | `784RAT` |
| TC2 | approach | `2NA` | `784RBT` |
| TC1 | approach | `3NA` | `784RCT` |
| TC4 | interior, no switch | `2NAA` | `O1T` (R4 reading 2: `797T`) |
| SW783 | TC field | `783T1` | `783T` (or drop the field; it equals the default) |
| SW795 | TC field | `795T1` | `795T` |
| SW799 | TC field | `799T1` | `799T` |
| MC1 | maintainer call | `~` (empty) | `MC1` |

Fit: switches `783`, `795`, `799`; derail `795D`; heads A–D.

Christopher.net (22)

| Ref | Kind | Now | Proposed |
|---|---|---|---|
| S4 | mast | `816SAB` | `816RAB` |
| S5 | mast | `816SC` | `816RC` |
| S6 | mast | `816NAB` | `816LAB` |
| S3 | mast | `816NC` | `816LC` |
| S1, S2 | dwarf mast | `~` (empty, 2) | `816L?` / `816R?` |
| H1, H2, H5, H6, H8 | head | `~` (empty, 5) | a letter A–E |
| SW815 | crossover end | `815` | `815A` |
| SW900 | crossover end | `815A` | `815B` |
| SW813, SW815, SW900, SW817 | TC field | `813T1`, `815T1`, `815AT1`, `817T1` (4) | `813T`, `815AT`, `815BT`, `817T` |
| TC3 | approach | `1SA` | `816LAT` |
| TC4 | approach | `2SA` | `816LBT` |
| TC1 | approach | `1NA` | `816RAT` |
| TC2 | approach | `2NA` | `816RBT` |
| TC5 | other | `IND` | `O1T` |

Corporal.net (12)

| Ref | Kind | Now | Proposed |
|---|---|---|---|
| S4 | mast | `830NAB` | `830LAB` |
| S2 | mast | `830SAB` | `830RAB` |
| S1 | dwarf | `832NA` | `832LA` |
| S3 | mast | `832SA` | `832RA` |
| TC3 | approach | `1SAT` | `830LAT` (assumes signal 830) |
| TC4 | approach | `2SAT` | `830LBT` |
| TC1 | approach | `1NAT` | `830RAT` |
| TC2 | approach | `2NAT` | `830RBT` |
| TC5 | other | `IND` | `O1T` |
| SW829, SW831 | TC field | `829T1`, `831T1` (2) | `829T`, `831T` |
| SW901 | hand-throw switch | `1` | `?` (milepost number; see Q10) |

Fit: derail `829D`, switches `829`, `831`.

GilroyCalTrain.net (11)

| Ref | Kind | Now | Proposed |
|---|---|---|---|
| S5 | mast | `774NAB` | `774LAB` |
| S1 | mast | `774SAB` | `774RAB` |
| S2, S3, S4 | dwarf | `774NC`, `774ND`, `774NE` (3) | `774LC`, `774LD`, `774LE` |
| TC1 | approach | `1SA` | `774LAT` |
| TC5 | approach | `1NA` | `774RAT` |
| TC2, TC3, TC4 | yard track | `TK1`, `TK2`, `TK3` (3) | `O1T`, `O2T`, `O3T` |
| SW771 | TC field | `771T1, 773T1, 775T1` (as of 2026-10-01, changed by the owner on 2026-10-02, to be re-checked) | `771T` (one circuit, one name). Under ADR 0002 D16 the list names a block and stays |

GilroyInterchange.net (9)

| Ref | Kind | Now | Proposed |
|---|---|---|---|
| S4 | mast | `778NAB` | `778LAB` |
| S3 | mast | `778SAB` | `778RAB` |
| S1 | dwarf | `778NC` | `778LC` |
| S2 | dwarf | `778SC` | `778RC` |
| TC1 | approach | `1SA` | `778LAT` |
| TC3 | other | `INTER` | `O1T` |
| TC2 | other | `TK1` | `O2T` |
| SW777, SW781 | TC field | `777T1`, `781T1` (2) | `777T`, `781T` |

Sargent.net (10)

| Ref | Kind | Now | Proposed |
|---|---|---|---|
| S1 | mast | `836NAB` | `836LAB` |
| S2 | mast | `836SA` | `836RA` |
| S3 | dwarf | `836SB` | `836RB` |
| TC1 | approach | `1SA` | `836LAT` |
| TC2 | approach | `2SA` | `836LBT` |
| TC5 | approach | `1NA` | `836RAT` |
| TC3 | detector on a Track Circuit symbol | `HBD` | `O1T`, or a detector kind (Q9) |
| TC4 | cross-plant reference | `Corporal:2NA` | `Corporal:830RBT`. Corporal has no `2NA` today; the reference is already broken. |
| SW835 | TC field | `835T1` | `835T` |
| SW3 | hand-throw switch | `1` | `?` (Q10) |


Watsonville.net (65): excluded because the schematic was incomplete and not valid evidence (owner; as of 2026-10-01, changed by the owner on 2026-10-02, to be re-checked). The table is kept as a dated record and drives no proposal.

| Ref | Kind | Now | Proposed |
|---|---|---|---|
| SW3…SW25 | switch | `FIXME 3` … `FIXME 25` (12) | excluded |
| SW837 | TC field | `837T1` | excluded |
| SW3, 5, 7, 9, 11, 13 | TC field | `DLT` (6) | excluded |
| SW15…SW23 | TC field | `ALT` (5) | excluded |
| SW25 | TC field | `FIXME 25T1` | excluded |
| TC1–TC32 | staging sections | `AT`, `SAT`, `SDT`, `1BT`…`1ET`, `2AT`…`2ET`, `3BT`…`7ET` (32) | excluded |
| MC1–MC8 | maintainer call | `K0`…`K7` (8) | excluded |

#### B2.2 Profiles, `profiles/spcoast_south/cps/`

Legacy files are renamed at cutover (AGENTS.md). Their switch and signal levers (`1`, `3`, `5`,
`2`) fit the syntax and fail the milepost rule; they are not counted.

| File | Failing names | Proposed | Count |
|---|---|---|---|
| `CP_Christopher.json` | `1T1`, `3T1`, `3BT1`, `5T1`; `1WA`, `2WA`, `1EA`, `2EA`; masts `2Nab`, `2Sab` | `1T`, `3T`, `3BT`, `5T`; `2RAT`, `2RBT`, `2LAT`, `2LBT`; `2LAB`, `2RAB` | 10 |
| `CP_Corporal.json` | `1T1`, `3T1`; `1EA`; `SDT`, `TL`, `TR`; masts `2NAB`, `2SA` | `1T`, `3T`; `2LAT`; `O1T`, and TL/TR are traffic, not track circuits (Q9); `2LAB`, `2RA` | 8 |
| `CP_GilroyCaltrain.json` | `1T1`, `EA1`, `TK1`, `TK2`, `TK3` | `1T`, `O1T`…`O4T` | 5 |
| `CP_GilroyInterchange.json` | `1T1`, `3T1`, `TK1` | `1T`, `3T`, `O1T` | 3 |
| `CP_Luchessa.json` | `1T1`, `3T1`; masts `2SAB`, `2NAB` | `1T`, `3T`; `2RAB`, `2LAB` | 4 |
| `CP_Sargent.json` | `1T1`, `HBD` | `1T`, `O1T` or detector (Q9) | 2 |
| `CP_Watsonville.json` (legacy harvest, not the Watsonville schematic; kept) | `ALT`, `EAT`, `SAT`; masts `2NA`, `2SA` | `O1T`…`O3T`; `2LA`, `2RA` | 5 |
| `generated/Luchessa.json` | the 9 track circuits and 5 masts of Luchessa.net | as Luchessa.net | 14 |
| `generated/Luchessa.projectionDeferred.json` | the same 6 track circuits and 5 masts, as references | regenerated | 11 |

Fit: `795D`, switches `783`, `795`, `799`, signal lever `784`.

#### B2.3 FieldUnit examples, `~/Dropbox/Arduino/libraries/FieldUnit/examples/` (bench excluded)

| File | Failing names | Proposed | Count |
|---|---|---|---|
| `CP_Christopher/CP_Christopher.ino` | `1T1`, `3T1`, `3BT1`, `5T1`; `1SA`, `2SA`, `1NA`, `2NA`; `IND`; crossover `addCrossover("3", "3", "3B")` base end `3`; masts `2Nab`, `2Sab`, `2Nc` | `1T`, `3T`, `3BT`, `5T`; `2LAT`, `2LBT`, `2RAT`, `2RBT`; `O1T`; ends `3A`, `3B`; `2LAB`, `2RAB`, `2LC` | 13 |
| `CP_Corporal/CP_Corporal.ino` | `1T1`, `3T1`, `5T1`; `1NAT`, `2NAT`, `1SAT`, `2SAT`; masts `2NAB`, `2SA`, `4NA`, `4SA` | `1T`, `3T`, `5T`; `2RAT`, `2RBT`, `2LAT`, `2LBT`; `2LAB`, `2RA`, `4LA`, `4RA` | 11 |
| `spcoast_ctc/spcoast_ctc.ino` `configureDesk()` | track lamps: GilroyCaltrain `1T1`, `EA1`, `TK1`–`TK3`; GilroyInterchange `1T1`, `3T1`, `TK1`; Luchessa `783T1`, `795T1`; Christopher `1T1`, `1WA`, `2WA`, `3T1`, `3BT1`, `5T1`, `1EA`, `2EA`; Corporal `1EA`, `1T1`, `3T1`, `SDT`, `TL`, `TR`; Sargent `1T1`, `HBD`; Watsonville `ALT`, `EAT`, `SAT` | as the profiles above | 29 |
| `Universal_FieldUnit/Universal_FieldUnit.ino` | `1T1`, `2T1` | `1T`, `O1T` (2T1 contains no switch 2) | 2 |
| `FieldUnit_Tracer/*` | tokens only (`1NWS`, `2NGS`, `2NGK`) | see Q2 | 0 |

Fit: `2LA` in `Universal_FieldUnit.ino`.

#### B2.4 FieldUnit docs, `~/Dropbox/Arduino/libraries/FieldUnit/docs/` and `README.md`

The example plant in the primer and tutorials has switches 1, 3, 5 and signals 2, 4.
Relay names (`1TR`, `2HSR`, `1NWCR`) are not in scope.

| File | Failing names | Proposed | Count |
|---|---|---|---|
| `GLOSSARY.md` | `1T1K` | `1TK` | 1 |
| `AAR_SIGNALING_PRIMER.md` | `1T1`, `3T1`, `5T1`, `1T1K`; `1SA`, `1SAK`, `1SATR`, `1NAT`, `2NAT`, `1SAT`, `2SAT`; `2nab`, `2sa`, `4na`, `4sa` | `1T`, `3T`, `5T`, `1TK`; `2LAT`, `2LATK`, `2LATR`, `2RAT`, `2RBT`, `2LAT`, `2LBT`; `2LAB`, `2RA`, `4LA`, `4RA` | 15 |
| `tutorials/01_drawing_your_signaling_track_plan.md` | `1T1`; `1SA`, `1NA`, `2NA`; mast `2R` (two heads) | `1T`; `2LAT`, `2RAT`, `2RBT`; `2RAB` | 5 |
| `tutorials/02_building_your_first_cp.md` | `1T1`, `3T1`, `5T1`; `1NAT`, `2NAT`, `1SAT`, `2SAT`; `2NAB`, `2SA`, `4NA`, `4SA`; `S2NAB`, `S2SA`, `S4NA`, `S4SA` | `1T`, `3T`, `5T`; `2RAT`, `2RBT`, `2LAT`, `2LBT`; `2LAB`, `2RA`, `4LA`, `4RA`; drop the `S` (it is a KiCad reference prefix) | 15 |
| `tutorials/03_Signal_Operation.md` | `1T1`, `3T1`; `1NAT`, `2NAT`, `1SAT`, `2SAT`; `2NAB`, `2SA`, `4NA`, `4SA` | as tutorial 02 | 10 |
| `how-to/01_data_collection_and_aar_bits.md` | `1T1`, `3T1`, `5T1`, `7T1`, `1T1K`; `1SA`, `2SA`, `1NA`, `2NA`; `2Nab`, `2Sab` | `1T`, `3T`, `5T`, `7T`, `1TK`; `2LAT`, `2LBT`, `2RAT`, `2RBT`; `2LAB`, `2RAB` | 11 |
| `how-to/02_jmri_and_cmri_integration.md` | `1T1`, `1T1K` | `1T`, `1TK` | 2 |
| `how-to/05_derails_and_os_binding.md` | `1T1`, `3T1`, `5T1`, `1DT1`; crossover rule "`1A`, `1B`, `1C` ganged with `1`" | `1T`, `3T`, `5T`, `1DT`; ends `1A`, `1B`, `1C`, lever `1` | 5 |
| `CONTROL_POINT_ARCHITECTURE.md` | `1T1`, `3T1`, `5T1`, `1DT1`; the same crossover rule | as how-to 05 | 5 |
| `CTC_SUBDIVISION_AND_PLANT_DESIGN.md` | `783T1`, `795T1`, `799T1`; `1SA`, `2NA`, `3NA`, `2NAA`; `784SAB`, `784S`; `780SA` | `783T`, `795T`, `799T`; `784LAT`, `784RBT`, `784RCT`, `O1T`; `784RAB`, `784R`; `780T` (R4 reading 2) | 10 |
| `README.md` | `1T1`, `3T1`, `1T1K`; `2NA`; mast `2S` | `1T`, `3T`, `1TK`; `2RBT`; `2RA?` | 5 |

Fit: `2LA`, `2LB` (tutorial 01, how-to 04), `782R`, `782L` and `2R` used as lever positions.
`CHANGELOG.md` and the ADR mention `1T1K`; they are history and are not counted.

#### B2.5 Desk netlist (not in the requested list; names must pair with the plants)

`South-cTc.net` `IndicationToken` fields hold 31 distinct failing names: 14 OS names in `T1` form
(`773T1`, `777T1`, `781T1`, `783T1`, `795T1`, `799T1`, `813T1`, `815T1`, `817T1`, `829T1`,
`831T1`, `835T1`, `3BT1`, `1T1`), 6 approach names (`1SA`, `1NA`, `2SA`, `2NA`, `2NAA`, `SA1`),
and 11 others (`TK1`–`TK3`, `XNA`, `SDT`, `ART`, `ALT`, `SAT`, `HBD`, `TL`, `TR`). Two pairing
faults are independent of the grammar:

- `PanelSignal` `838` has no plant signal of that number. Sargent's masts are `836…`.
- `773T1` has no plant circuit of its own. GilroyCalTrain lists it inside switch 771's `TC` field (as
  of 2026-10-01, changed by the owner on 2026-10-02, to be re-checked). Under ADR 0002 D16 that list
  names a block whose members are track circuits, so `773T1` is a member circuit; whether the desk lamp
  then resolves is to be re-checked.

### B3. The grammar as first proposed

A record of the proposal of 2026-10-02. The grammar below used the recommended answer to each question
in Appendix A. The Decisions supersede it where they differ: L/R only (D1), `<switch>T` (D3), `O<n>T`
(D5), both crossover ends lettered (D7), heads A–E (D9), milepost numbers for local items (D11), and
the generated approach names. Its rule 12 and the regex heading ("upper case on output") disagreed
with AGENTS.md (case preserved); the decided grammar follows AGENTS.md.

#### EBNF

```ebnf
digit1       = "1" | … | "9" ;
number       = digit1 , [ digit ] , [ digit ] , [ digit ] ;   (* 1–9999 *)
side         = "L" | "R" ;
end          = "A" | "B" | "C" ;
func         = "A" | … | "E" ;
seq          = "A" | … | "Z" ;

lever        = number ;                          (* 783, 784; the desk lever and the token stem *)
switch       = lever , [ end ] ;                 (* 783; crossover ends 815A, 815B *)
derail       = lever                             (* independent derail with its own lever *)
             | switch , "D" ;                    (* dependent derail: 795D *)
signal       = lever , side ;                    (* lever position: 784L, 784R *)
head         = signal , func ;                   (* 784LB; the KiCad head Value is func only: "B" *)
mast         = signal , func , { func } ;        (* 784LBC: the letters of its heads, top to bottom, ascending *)

os_tc        = ( switch | derail ) , "T" ;       (* 783T, 815AT *)
signal_tc    = signal , seq , "T" ;              (* 784LAT: section A governed over by 784L *)
other_tc     = "O" , number , "T" ;              (* O1T *)
track_circuit = os_tc | signal_tc | other_tc ;

maintainer_call = "MC" , digit1 ;                (* MC1 *)
reference    = interlocking , ":" , name ;       (* Corporal:830RBT; cross-plant reference only *)

token        = lever , ( "NWS" | "RWS" | "NWK" | "RWK" | "WLS" | "WLK" )   (* switch lever *)
             | lever , ( "NGS" | "SGS" | "HS" | "NGK" | "SGK" | "TEK" )   (* signal lever; see Q2 *)
             | track_circuit , "K"                                        (* 783TK *)
             | maintainer_call , ( "S" | "K" ) ;                          (* MC1S, MC1K *)
```

#### Regular expressions (case-insensitive on input, upper case on output)

| Kind | Regex | Examples |
|---|---|---|
| lever | `^[1-9]\d{0,3}$` | `783`, `784` |
| switch | `^[1-9]\d{0,3}[A-C]?$` | `783`, `815A` |
| derail | `^[1-9]\d{0,3}([A-C]?D)?$` | `5`, `795D` |
| mast | `^([1-9]\d{0,3})([LR])([A-E]+)$`, letters ascending | `784LBC`, `784RA` |
| head (KiCad Value) | `^[A-E]$` | `B` |
| track circuit | `^([1-9]\d{0,3}[A-C]?D?T\|[1-9]\d{0,3}[LR][A-Z]T\|O[1-9]\d?T)$` | `783T`, `784LAT`, `O1T` |
| maintainer call | `^MC[1-9]$` | `MC1` |

The three track circuit forms cannot be confused: `os_tc` never contains L or R; `signal_tc`
always does; `other_tc` starts with O.

#### Rules

1. Every name of a field appliance starts with a lever number. The number is the railroad name.
   KiCad references (`SW783`, `S784E1`) are never names.
2. On SPCoast the lever number is the milepost in tenths of the appliance (`783` at MP 78.3).
   Two appliances closer than 0.1 mile take adjacent numbers. Odd for switches and even for signals
   is a project habit. The compiler may warn on it. It is not an error (see F25 and §6).
3. A crossover is one lever. Its ends are the lever number plus A, B, C (AAR56 p. 34). The lever
   number alone names the lever, not an end.
4. An independent derail has its own lever number. A dependent derail is its switch name plus D.
5. A signal is a lever position: lever number plus L or R. L and R are the directions on the
   plant drawing and the desk, which are drawn in the same orientation.
6. A head is a signal plus one letter A–E. Letters are unique within one signal, across all its
   masts. On one mast they run top to bottom in alphabetical order. The KiCad head Value is the
   letter alone.
7. A mast name is its signal plus the letters of its heads. A one-head mast and its head have the
   same full name. AAR56 names no masts; the mast name is derived and is checked against the
   attached heads.
8. An OS track circuit is the name of a switch or derail in it plus T (AAR56 p. 31). When one
   circuit holds several switches, it takes one name: a movable-point frog first, then a switch,
   then a derail; among equals, the lowest number.
9. A track circuit outside the switches, entered from the plant, takes the signal that governs
   over it, a section letter and T. The section letter runs A, B, C outward and across tracks, in
   the order the designer sets. The side letter names the plant signal that governs moves into
   the section, which is also the side of the plant it lies on.
10. A track circuit with no switch and no governing plant signal takes O, a number unique in the
    interlocking, and T.
11. A token is a lever, track circuit or maintainer call plus a function. The function letters
    are listed in §2.4.
12. Names are produced in upper case and compared case-insensitively (AGENTS.md).

#### Meaning of each letter

| Letter | Position | Meaning | Source |
|---|---|---|---|
| A, B, C | after a switch lever | crossover end (function of the lever) | AAR56 p. 34 |
| D | after a switch name | dependent derail | project; AAR56 p. 32 gives D other meanings |
| L, R | after a lever | signal lever position left, right | AAR56 p. 34, Figs. 18, 22 |
| A–E | after L/R, last letters of a head or mast | signal function (head) | AAR56 p. 34, Fig. 26 |
| A–Z | after L/R, before T | section letter | AAR56 p. 31 ("progressive alphabetical") |
| T | last letter of a track circuit | track section | AAR56 p. 34 |
| O | first letter of a track circuit | arbitrary section, no switch, no signal | AAR56 p. 31 |
| MC | prefix | maintainer call | project; no source |
| NW, RW | token | normal, reverse of the switch | AAR56 p. 35 |
| WL | token | electric switch lock | AAR56 p. 35 |
| G | token | signal mechanism | AAR56 p. 32 |
| N, S in NGS, SGS, NGK, SGK | token | LEFT, RIGHT (FieldUnit `WireCodec.h`) | FieldUnit; AAR56 reads N as Normal and S as South or Stick |
| HS | token | hold the signal at stop | FieldUnit; AAR56 p. 37: HS = control of the home stick relay |
| TE | token | time element | AAR56 p. 38; TEK is not in AAR56 |
| K | last letter of a token | indication | AAR56 p. 32 ("Indicator") |
| S | last letter of a control token | control | FieldUnit; AAR56 has no control suffix |

#### Consequences as first proposed

##### Cost on the built CTC machine and on verified tokens

- Every OS name changes under Q3, so the desk `IndicationToken` fields, `configureDesk()` in `spcoast_ctc` and the token lists of the virtual plant change with the plants. The desk linker pairs by normalized name, so the names must change in the plants and the desk together.
- Tokens that were verified with the `T1` form (`783T1K`) change to `783TK`. FieldUnit `WireCodec.h` appends `K` to a track name unless the name already ends in K. With every track circuit ending in T, that special case can go.
- Signal tokens (`NGS`, `SGK`) are not renamed unless Q2 is decided that way.
- Two pairing faults exist whatever the owner decides (see B2.5).

##### What changes in the compiler

`tools/plant_graph/compiler.py` and `tools/plant_graph/routes.py`:

| Item | Today | Change |
|---|---|---|
| `_MAST_VALUE_RE` | `^(\d+)([NSEW])([A-E]+)$`, defined twice (compiler.py:114, routes.py:29) | `^([1-9]\d{0,3})([LR])([A-E]+)$`, one definition imported by both. Add: letters ascending; a letter used once per signal across masts. |
| `_DEFAULT_MAST_DIRECTION_MAP`, `mast_direction_map` parameter, `PlantGraph.mast_direction_map` | N/W → LEFT, S/E → RIGHT | Remove. L → LEFT and R → RIGHT need no map. With reading R1-2 (E/W) the map stays, as E/W only. |
| `bad_mast_value` message | says `<signal><N\|S><heads>` while the regex accepts NSEW | Message follows the regex. |
| `_derive_os_circuits` default | `f"{name}T1"` | `f"{name}T"`. Validate the `TC` field against the track circuit regex. Reject a list of names in one `TC` field (GilroyCalTrain 771). |
| Switch Value | any non-empty string | `^[1-9]\d{0,3}[A-C]?$`. Diagnostic `bad_switch_value`. |
| Derail Value | `(\d+)(D)?` after `upper()` | `^[1-9]\d{0,3}([A-C]?D)?$`. Dependent-derail lookup strips `D` as today. |
| Head Value | `^[A-E]$` | No change. Empty `~` heads already fail. |
| Track Circuit Value | any non-empty string | Track circuit regex, warning first. Optional check: the side letter of a `signal_tc` matches the side of the plant where the section lies (topology from the netlist, not coordinates). Accept `<Interlocking>:` references. |
| MaintainerCall Value | not checked | `^MC[1-9]$`. |
| Lever parity | not checked | Optional warning: switch even or signal odd. Not an error (§6, F25). |
| `_PART_KIND` | 25 parts | No change for the grammar. Observed in the netlists and missing from the map: `Switch_HandThrow`, `Switch_Powered_NO_TC`, `Track Circuit_Yellow`, `Rule6.13-Yard Limits`. These raise `unknown_symbol` today. A detector kind for `HBD` would add one part (Q9). |

Outside the plant compiler: the desk `IndicationToken` fields and `configureDesk()` change with the plants. The desk linker pairs by normalized name.
