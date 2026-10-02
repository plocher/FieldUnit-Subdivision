# Name grammar for levers, signals, masts, heads, switches, derails and track circuits

Status: spike S5 from `vocabulary-review.md` (F16). Proposal only. No code, schematic or profile is changed.
Date: 2026-10-01.

Terms follow the settled vocabulary: OS section, track circuit, approach track circuit, control,
indication, field station. "Block" is not used for a track circuit. "Island" is not used.

Page numbers are the printed page numbers. In both PDFs the PDF page is the printed page plus 2.

- `AAR56` = *American Railway Signaling Principles and Practices*, Chapter II, AAR Signal Section, revised June 1956.
- `TT52` = Southern Pacific Coast Division Timetable 162, 1952-09-28.

---

## 1. What the period references show

### 1.1 AAR 1956, Chapter II

| Point | What the document shows | Page |
|---|---|---|
| Structure of a name | "a designation made up of two parts": a **numerical prefix** ("the number of the principal lever, signal, track circuit, or other device") and an **alphabetic term**. "The last letter … designates the general kind of unit, while the first letter or letters … describe specifically the operated unit." Example `10HR`: 10 is the signal, R a relay, H the home function. | 31 |
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

**AAR56 is silent on:** a name for a mast; head order top to bottom; milepost numbers; an odd/even
rule for switches and signals; CTC codes (`NWS`, `NGS`, `SGK`, `TEK`, `MC`); the term "OS";
the form `T1`; the name of a dependent derail.

**On A/B/C:** the letter names a **function of a lever position**. Fig. 26 uses it for separate
signals on separate tracks (`2RA`, `2RB`, `2RC`) and for two arms on one mast (`2LA`, `2LB`). The
letter does not say whether functions share a mast. In color-light terms one function is one head.
Fig. 26 does not state which arm of `2L` is the top arm.

### 1.2 SP Coast Division Timetable 162 (1952)

| Point | What the document shows | Page |
|---|---|---|
| Timetable direction | Schedules are EASTWARD and WESTWARD. Eastward runs San Francisco → San Jose → Watsonville Jct., in increasing milepost. | 2, 14 |
| Signal numbers | Salinas Subdivision Rule 105: "No. 1 siding at Salinas extends from Signal 1164 to crossover just west of Signal 1178. No. 2 siding extends from crossover just east of Signal 1178 to crossover just west of Signal 1186." Salinas is MP 118.2. The numbers equal the milepost in tenths. | 28, 18 |
| Gilroy Subdivision | Automatic block signals, double track Lick–Coyote, Gilroy–Corporal, Logan–Aromas. Gilroy MP 80.7, Carnadero 83.2, Corporal 86.4, Sargent 87.1. No Luchessa or Christopher station. | 14–17 |
| CTC | Only Santa Margarita–San Luis Obispo is marked Centralized Traffic Control. | 22–23 |

**TT52 is silent on:** switch and lever numbers; track circuit names; mast and head letters; signal
direction letters; odd/even. It states no numbering rule; the milepost reading is an inference from
three numbers. It gives no example of a milepost number on a CTC or interlocked signal.

### 1.3 What this settles

- Settled by AAR56: lever positions are L and R; A, B, C name functions of a lever or lever
  position; a track circuit is number + T, numbered from its switch, else from its governing
  signal, else arbitrarily (`O1T`); TK is the track indication; NWK and RWK are the switch indications.
- Supported by TT52: on the SP Coast Line the timetable direction is east/west, and signal numbers
  are milepost tenths.
- Not settled: mast names, head order, the form of control tokens, `T1`, dependent derail names,
  odd/even, and whether milepost numbers apply to switches and CTC signals.

---

## 2. Proposed grammar

One grammar. The open choices are in §2.4 and §5.

### 2.1 EBNF

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

### 2.2 Regexes (case-insensitive on input, upper case on output)

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

### 2.3 Rules in sentences

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

### 2.4 Meaning of each letter

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

---

## 3. Where the references allow two readings

| # | Question | Reading 1 | Reading 2 | Cost of the proposal |
|---|---|---|---|---|
| R1 | Direction letter on a signal | **L/R, the lever position** (AAR56 p. 34). Proposed. Matches FieldUnit `LEFT`/`RIGHT`. Removes `_DEFAULT_MAST_DIRECTION_MAP`. | E/W, the timetable direction (TT52 p. 2, 14), in the AAR56 style of compass first letters (ESR). | L/R renames all 25 named masts, including Luchessa's E/W ones. E/W renames 20 and keeps a translation map. Status quo N/S matches no timetable direction on the Coast Line. |
| R2 | A, B on a signal: masts or heads | One reading only: functions of a lever position, either way (Fig. 26). | — | None. Luchessa already uses it (`784WA`, `784WBC`, `784WD`). |
| R3 | OS name | **`<switch>T`** (AAR56 p. 31). Proposed. Token `783TK` is the AAR TK. | `<switch>T1` (project). No source. AAR56 p. 32 reads a trailing digit as a wire's contact count. | Every OS name changes: plants, profiles, desk tokens, tests, compiler default. |
| R4 | Number of an approach track circuit | **The plant signal that governs over it** (AAR56 p. 31): `784LAT`. Proposed. Needs nothing outside the plant. | The automatic signal that governs over it, numbered by milepost (TT52 p. 28; AAR56 Fig. 26 `108T`): `780T`. The handoff alias `2NAA → 797T` already uses this form. | Reading 2 needs a milepost for each section and signals that may not exist on the layout. It gives subdivision-unique names and no side letter. |
| R5 | "Progressive alphabetical prefixes" | A letter before T: `784LAT`. Proposed. | A letter before the number: `A784LT`. | The text does not show an example. Reading 2 breaks rule 1 (names start with the lever number). |
| R6 | Lever numbers | **Milepost tenths** (TT52 p. 28, for automatic signals only). Proposed for SPCoast. | Machine lever order 1…n (AAR56 Figs. 6, 26; legacy `CP_*.json`). | Reading 2 repeats numbers in every plant (`1` everywhere) and needs a plant qualifier in every reference. |
| R7 | Dependent derail | **`<switch>D`** (project, already in compiler and FieldUnit). Proposed. | A function letter of the switch lever (`795B`), as AAR56 p. 34 would give. | Reading 2 makes the switch itself `795A` and collides with crossover end letters. |

---

## 4. Names that fail the grammar

Corrections use the proposal (L/R, `T`, plant-signal approach names). "Side" mapping: the current
letter names the direction of the approaching train (`1SA` is the entrance for RIGHT routes in
`generated/Luchessa.json`), so S/E approach circuits lie on the left and become `<signal>L…T`,
N/W approach circuits lie on the right and become `<signal>R…T`. Section letters are a first
assignment for the owner to confirm. "?" means the correction needs a fact not in the source.

Counts are distinct names per file. Names that fail only the SPCoast milepost rule (legacy `1`,
`3`, `5`, `2`) are noted per file and not counted.

### 4.1 Plant netlists, `~/Dropbox/KiCad/Railroad/SPCoast/<Project>/<Project>.net`

All seven netlists were newer than their schematics at read time.

**Luchessa.net (15)**

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

**Christopher.net (22)**

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

**Corporal.net (12)**

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

**GilroyCalTrain.net (11)**

| Ref | Kind | Now | Proposed |
|---|---|---|---|
| S5 | mast | `774NAB` | `774LAB` |
| S1 | mast | `774SAB` | `774RAB` |
| S2, S3, S4 | dwarf | `774NC`, `774ND`, `774NE` (3) | `774LC`, `774LD`, `774LE` |
| TC1 | approach | `1SA` | `774LAT` |
| TC5 | approach | `1NA` | `774RAT` |
| TC2, TC3, TC4 | yard track | `TK1`, `TK2`, `TK3` (3) | `O1T`, `O2T`, `O3T` |
| SW771 | TC field | `771T1, 773T1, 775T1` | `771T` (one circuit, one name) |

**GilroyInterchange.net (9)**

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

**Sargent.net (10)**

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

**Watsonville.net (65)**

| Ref | Kind | Now | Proposed |
|---|---|---|---|
| SW3…SW25 | switch | `FIXME 3` … `FIXME 25` (12) | milepost lever numbers `?` |
| SW837 | TC field | `837T1` | `837T` |
| SW3, 5, 7, 9, 11, 13 | TC field | `DLT` (6) | one OS name: lowest switch + `T` |
| SW15…SW23 | TC field | `ALT` (5) | one OS name: lowest switch + `T` |
| SW25 | TC field | `FIXME 25T1` | `<lever>T` |
| TC1–TC32 | staging sections | `AT`, `SAT`, `SDT`, `1BT`…`1ET`, `2AT`…`2ET`, `3BT`…`7ET` (32) | `O1T`…`O32T`, or a staging form (Q12). The leading digit is a track number, not a lever. |
| MC1–MC8 | maintainer call | `K0`…`K7` (8) | `MC1`…`MC8` |

### 4.2 Profiles, `profiles/spcoast_south/cps/`

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
| `CP_Watsonville.json` | `ALT`, `EAT`, `SAT`; masts `2NA`, `2SA` | `O1T`…`O3T`; `2LA`, `2RA` | 5 |
| `generated/Luchessa.json` | the 9 track circuits and 5 masts of Luchessa.net | as Luchessa.net | 14 |
| `generated/Luchessa.projectionDeferred.json` | the same 6 track circuits and 5 masts, as references | regenerated | 11 |

Fit: `795D`, switches `783`, `795`, `799`, signal lever `784`.

### 4.3 FieldUnit examples, `~/Dropbox/Arduino/libraries/FieldUnit/examples/` (bench excluded)

| File | Failing names | Proposed | Count |
|---|---|---|---|
| `CP_Christopher/CP_Christopher.ino` | `1T1`, `3T1`, `3BT1`, `5T1`; `1SA`, `2SA`, `1NA`, `2NA`; `IND`; crossover `addCrossover("3", "3", "3B")` base end `3`; masts `2Nab`, `2Sab`, `2Nc` | `1T`, `3T`, `3BT`, `5T`; `2LAT`, `2LBT`, `2RAT`, `2RBT`; `O1T`; ends `3A`, `3B`; `2LAB`, `2RAB`, `2LC` | 13 |
| `CP_Corporal/CP_Corporal.ino` | `1T1`, `3T1`, `5T1`; `1NAT`, `2NAT`, `1SAT`, `2SAT`; masts `2NAB`, `2SA`, `4NA`, `4SA` | `1T`, `3T`, `5T`; `2RAT`, `2RBT`, `2LAT`, `2LBT`; `2LAB`, `2RA`, `4LA`, `4RA` | 11 |
| `spcoast_ctc/spcoast_ctc.ino` `configureDesk()` | track lamps: GilroyCaltrain `1T1`, `EA1`, `TK1`–`TK3`; GilroyInterchange `1T1`, `3T1`, `TK1`; Luchessa `783T1`, `795T1`; Christopher `1T1`, `1WA`, `2WA`, `3T1`, `3BT1`, `5T1`, `1EA`, `2EA`; Corporal `1EA`, `1T1`, `3T1`, `SDT`, `TL`, `TR`; Sargent `1T1`, `HBD`; Watsonville `ALT`, `EAT`, `SAT` | as the profiles above | 29 |
| `Universal_FieldUnit/Universal_FieldUnit.ino` | `1T1`, `2T1` | `1T`, `O1T` (2T1 contains no switch 2) | 2 |
| `FieldUnit_Tracer/*` | tokens only (`1NWS`, `2NGS`, `2NGK`) | see Q2 | 0 |

Fit: `2LA` in `Universal_FieldUnit.ino`.

### 4.4 FieldUnit docs, `~/Dropbox/Arduino/libraries/FieldUnit/docs/` and `README.md`

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

### 4.5 Desk netlist (not in the requested list; names must pair with the plants)

`South-cTc.net` `IndicationToken` fields hold 31 distinct failing names: 14 OS names in `T1` form
(`773T1`, `777T1`, `781T1`, `783T1`, `795T1`, `799T1`, `813T1`, `815T1`, `817T1`, `829T1`,
`831T1`, `835T1`, `3BT1`, `1T1`), 6 approach names (`1SA`, `1NA`, `2SA`, `2NA`, `2NAA`, `SA1`),
and 11 others (`TK1`–`TK3`, `XNA`, `SDT`, `ART`, `ALT`, `SAT`, `HBD`, `TL`, `TR`). Two pairing
faults are independent of the grammar:

- `PanelSignal` `838` has no plant signal of that number. Sargent's masts are `836…`.
- `773T1` has no plant circuit of its own. GilroyCalTrain lists it inside switch 771's `TC` field.

### 4.6 Count summary

| Source | Failing names |
|---|---|
| Plant netlists (7) | 144 (Luchessa 15, Christopher 22, Corporal 12, GilroyCalTrain 11, GilroyInterchange 9, Sargent 10, Watsonville 65) |
| Profiles | 62 (legacy 37, `generated/Luchessa.json` 14, sidecar 11) |
| FieldUnit examples | 55 |
| FieldUnit docs | 84 |
| Desk netlist (extra) | 31 |

Also affected, not counted: FieldUnit-Subdivision tests and fixtures hard-code Luchessa names
(`tests/test_kicad_plant_graph.py`, `tests/test_controller_graph.py`,
`tests/fixtures/kicad/Luchessa.plant-model.json`, `tools/run_plant_graph_smoke.sh`,
`runtime/plant_host/spcoast_virtual_plant.cpp`). Per AGENTS.md they change in a separate step.

---

## 5. What changes in the compiler

`tools/plant_graph/compiler.py` and `tools/plant_graph/routes.py`:

| Item | Today | Change |
|---|---|---|
| `_MAST_VALUE_RE` | `^(\d+)([NSEW])([A-E]+)$`, defined twice (compiler.py:114, routes.py:29) | `^([1-9]\d{0,3})([LR])([A-E]+)$`, one definition imported by both. Add: letters ascending; a letter used once per signal across masts. |
| `_DEFAULT_MAST_DIRECTION_MAP`, `mast_direction_map` parameter, `PlantGraph.mast_direction_map` | N/W → LEFT, S/E → RIGHT | Remove. L → LEFT and R → RIGHT need no map. With reading R1-2 (E/W) the map stays, as E/W only. |
| `bad_mast_value` message | says `<signal><N\|S><heads>` while the regex accepts NSEW | Message follows the regex. |
| `_derive_os_circuits` default | `f"{name}T1"` | `f"{name}T"`. Validate the `TC` field against the track circuit regex. Reject a list of names in one `TC` field (GilroyCalTrain 771). |
| Switch Value | any non-empty string (`FIXME 11` passes) | `^[1-9]\d{0,3}[A-C]?$`. Diagnostic `bad_switch_value`. |
| Derail Value | `(\d+)(D)?` after `upper()` | `^[1-9]\d{0,3}([A-C]?D)?$`. Dependent-derail lookup strips `D` as today. |
| Head Value | `^[A-E]$` | No change. Empty `~` heads already fail. |
| Track Circuit Value | any non-empty string | Track circuit regex, warning first. Optional check: the side letter of a `signal_tc` matches the side of the plant where the section lies (topology from the netlist, not coordinates). Accept `<Interlocking>:` references. |
| MaintainerCall Value | not checked | `^MC[1-9]$`. |
| Lever parity | not checked | Optional warning: switch even or signal odd. Not an error (§6, F25). |
| `_PART_KIND` | 25 parts | No change for the grammar. Observed in the netlists and missing from the map: `Switch_HandThrow`, `Switch_Powered_NO_TC`, `Track Circuit_Yellow`, `Rule6.13-Yard Limits`. These raise `unknown_symbol` today. A detector kind for `HBD` would add one part (Q9). |

Outside the plant compiler: FieldUnit `WireCodec.h` appends `K` to a track name unless the name
already ends in K. With every track circuit ending in T, that special case can go. The desk linker
pairs by normalized name, so the desk `IndicationToken` fields and `configureDesk()` change with
the plants.

---

## 6. Contradictions with `vocabulary-review.md`

1. **F16 counts one scheme as two.** It sets `2R/2LA/2LB` ("A and B are separate masts") against
   `2NAB` ("A and B are heads on one mast"). AAR56 Fig. 26 (p. 33) uses one rule for both: the
   letter is a function of a lever position, on one mast or on several. The schemes differ only
   in the direction letter (L/R or compass) and in whether the mast name lists all its letters.
2. **F16 says track circuit names "have no rule".** The project has none. AAR56 p. 31 has one,
   and the proposal uses it.
3. **F25 is rated "recall".** AAR56 Fig. 6 (p. 9) numbers a crossover 2, slip switches 4, a
   movable-point frog 6 and 8, and a dual-control switch 12. The AAR does not reserve odd numbers
   for switches. F25 can be rated "checked".
4. **F9 is confirmed.** AAR56 p. 32: G is Signal; S is South, Stick, Storage, Southward. No source
   reserves S for Signal.
5. **F12 ("1NA is an approach circuit by name and an Exit Block in Tutorial 1").** Both uses are
   correct for opposite directions: `1NA` is the approach track circuit for leftward moves and
   the exit for rightward moves. The proposed names record the governing signal and side, not
   "approach", so the conflict leaves the name.
6. **One letter set, two axes.** The review does not note that Luchessa mixes axes: masts use E/W
   (`784EAB`), track circuits use N/S (`1SA`). FieldUnit tokens use N/S for LEFT/RIGHT
   (`WireCodec.h`; Primer §10 "2SGS … South/Right"). Any choice in R1 leaves either the names or
   the tokens on a different letter set until Q2 is decided.
7. **Model mileposts are not the 1952 mileposts.** TT52 puts Corporal at MP 86.4 and Sargent at
   87.1 (p. 14). The layout numbers them 829–832 and 835–836. This extends F28; it does not block
   the grammar.

---

## 7. Open questions for the owner

| # | Question | Proposal |
|---|---|---|
| Q1 | Signal direction letter: L/R (lever), E/W (timetable) or N/S (status quo)? | L/R |
| Q2 | Signal tokens: keep `NGS/SGS/NGK/SGK` as FieldUnit wire names with a glossary note, or move to `LGS/RGS/LGK/RGK`? AAR56 p. 36 already uses `RGK` for "signal mechanism at stop", and reads `NGK` as "normal" (at stop). | Separate decision; a code-line API change |
| Q3 | OS suffix `T` or keep `T1`? Is there an SP or US&S drawing that shows `1T1`? | `T` unless a source shows `T1` |
| Q4 | Approach track circuit number: plant signal (`784LAT`) or milepost of the governing automatic signal (`780T`)? | Plant signal |
| Q5 | Section letter after the side (`784LAT`) or as a true prefix (`A784LT`)? | After the side |
| Q6 | Crossover ends: both lettered (`815A`, `815B`) or base plus letter (`815`, `815A`)? | Both lettered |
| Q7 | Dependent derail: keep `<switch>D`? | Keep |
| Q8 | Are head letters A–E enough? | Yes for all current plants (max E at GilroyCalTrain) |
| Q9 | Circuits with no switch and no signal: AAR `O<n>T`, or mnemonics (`IND`, `TK1`)? `HBD`, `TL`, `TR` are not track circuits; do they get their own kinds? | `O<n>T`; own kinds |
| Q10 | Name of a hand-throw (non-interlocked) switch: milepost number like any switch? | Milepost number |
| Q11 | May a one-head signal omit its letter (`10R`, as AAR56 allows)? | No; always a letter |
| Q12 | Staging yard sections (Watsonville `1BT`…`7ET`): `O<n>T`, or a staging form? | Owner's choice |
| Q13 | Maintainer call `MC<n>` has no source. Keep it? | Keep, marked FieldUnit |
