# Traffic direction between CTC control points: prototype research (2026-10-31)

Research note. It records prototype facts only and designs nothing. It continues
`docs/review/abs-apb-research-2026-10-30.md` (cited below as [ABSAPB]) and does not repeat it.
Source keys from that note (RS1923, RSE1921, RS1932, RS1939SJ, AARTC71 and others) keep their meaning here.

Order of authority used: (1) the relay model and AAR practice from primary documents (AAR Signal Section
drawings and nomenclature, ICC and CFR text, period trade-press circuit descriptions written by railroad
signal engineers); (2) everything else. Marks: "(inference)" = my reading, not the source's words;
"(not found)" = no primary source was opened for the claim.

## 1. Verdicts on the working model

| # | Working-model claim | Verdict | Primary sources |
|---|---|---|---|
| 1 | One traffic direction relay per single-track block is part of every route equation into that track and of every intermediate signal's control. | **Corrected.** Some schemes have a per-block traffic relay, but where it sits depends on the scheme. It is in the control machine in AAR Dwg 8066, 8082 and 8059; at the departure CP (FR) on CB&Q 1946; and as traffic repeaters (FPR) at each signal location only in traffic-lever schemes (AAR 8064). SP CTC has no traffic relay at all. There, the cleared station-leaving signal, the line circuits through the track relays and the APB stick relays together *are* the direction. Intermediates carry no direction relay in SP or CB&Q practice: what they "know" of direction is which line circuit is fed, held by their own directional stick relay (SR). | AAR8066; AAR8082; AAR8059; AAR8064; CBQ1946; RS1942; RS1947 |
| 2 | It is SET when the exit signal lever's accepted indication (field confirmation) goes to the direction into the block, not by the dispatcher's control. | **Corrected; it depends on the scheme.** In the line-wire schemes the direction is set in the field *by the control*. On CB&Q 1946 the field traffic relay picks up from the control code, before the signal clears and before any indication. On SP it is set by the leaving signal clearing. Only in AAR 8059 (coded track, no line wires) is the office traffic stick relay picked by indications (block clear and signal clear). That matches the claim, but even there the far-end field traffic relay was set earlier, by an automatic control. Note also that "accept" in period sources is what a *train* does to a signal. | CBQ1946; RS1942; RS1945; AAR8059 |
| 3 | RELEASED only when the initiating lever is at STOP and every track circuit between the two CPs is vacant. | **Confirmed, with two refinements.** (a) A third condition: if a cleared signal was taken away with a train approaching, the direction stays locked until the time release (approach or time locking) runs out. (b) "Released" means "free to be reversed", not "reversed". On CB&Q the intermediates stay set for the direction last used; on SP, at rest, neither direction is set. The ICC (1939) also required that only a signal's own lever can restore it to stop. | CFR236 §236.405, §236.407, §236.769; ICC1939 items 382, 409, 412; CBQ1946; AAR8059; AAR8064; AAR8082; RS1942; RS1947 |
| 4 | While set: opposing exit signal locked at stop; opposing intermediates tumble down; following moves allowed (fleeting). | **Confirmed, except the term "fleeting".** The opposing leaving signal cannot clear "regardless" of the code sent [RS1947], and the opposing intermediates are "knocked down" to their most restrictive aspect [CBQ1946]. Following moves are allowed through the directional stick relays, but each following train needs a new control. Fleeting (the signal re-clearing by itself) is a separate control option, which SP had. In CTC the tumble-down starts when the signal is *cleared*; in APB (train-order territory) it starts when the train passes the head-block signal. | RS1947; CBQ1946; RS1942; SP1962; RS1923 |
| 5 | The "pole line" is the line circuit that carries this from one CP to the other through the intermediates. | **Corrected (term and topology).** The pole line is the physical pole line. It carries the code line, the signal line circuits, power and telephone. The circuit is the *line circuit* (SP: "signal line control circuits"; CB&Q: "two-wire either-direction line circuit"; N&W and Erie: "traffic locking line circuit"). It is a chain of two-wire segments, one per signal location to the next, and each intermediate relays (repeats) its segment to the next one. It is not one circuit spanning the block. Coded-track schemes have no line wires: the rails carry it. | RS1942; RS1945; RS1947; CBQ1946; NW1949; ERIE1942; AAR8059 |

Most important correction: there is no single, universal "traffic direction relay" in the vital field
circuits. In the SP (and CB&Q) practice nearest to SPCoast, direction is a **distributed state**. It is made of
(i) the departure CP's cleared signal (SP) or traffic relay (CB&Q), (ii) which end feeds each line-circuit segment,
which the track relays break, and (iii) the directional stick relays at the intermediate locations. A per-block
traffic relay does appear in AAR typical CTC *machine* circuits, and as field repeaters at each end in
some coded schemes. As a model abstraction it is defensible; as a description of the field it is not (inference).

## 2. Answers

### a. Relay names and circuits; APB versus CTC traffic locking

AAR names (Signal Section, *Circuit Nomenclature and Written Circuits*, 1943, approved Sept 1934 / Mar 1944,
in the Manual complete to Oct 1946) [AARNOM46 pp. 2-7]:

- Letter **F = Traffic**; **FC** = common traffic locking (energy wire).
- **FR** traffic relay; **FSR** traffic stick relay; **EFSR** east traffic stick relay (likewise N, S, W).
- **FL**: traffic lock preventing initial movement of a traffic lever from normal or reverse; **FLM**: traffic lock that also prevents its final (indicating) movement; **FLR**, **FLMR**: relays controlling FL and FLM; **FLK**: traffic lock indicator.
- **SR** stick relay; **ESR** east stick relay; **ASR** approach stick relay; **HSR** home stick relay.
- **HR, DR, HDR, HPR** as in [ABSAPB]. **BPR**: "block repeater relay, relay repeating the track circuits in a block"; **BK**: block indicator.
- **RGPR**: relay repeating the signal mechanism at stop. This answers [ABSAPB] open question 12: SP's "RGPR controls" carry a signal's at-stop state past the CTC limits (inference from the nomenclature).

Names used in the AAR typical CTC drawings [AARTC71]:

- **GZR**: field signal control relay (code-operated). **TFZR** (e.g. `6LTFZR`): field traffic control relay at the far end of a block, picked by an automatic control cycle [AAR8059 Sheet 6-8].
- **LFSR / RFSR** (e.g. `4-6RFSR`): office "left/right traffic relay"; "Once established it holds until block is clear in the field" [AAR8059 Sheet 8 nomenclature].
- **FR** per block in the machine (e.g. `1-3FR`, a magnetic polar stick relay; `4-8FR`) [AAR8066 Sheet 3; AAR8082].
- **FSR** at each end of a block in the field (e.g. `8LFSR`, `4RFSR`). These set which end feeds the line circuit and which end receives [AAR8082].
- **FPR**: traffic repeater "at each signal location", selecting the reversible two-wire signal control circuit [AAR8064].
- **RFR** at the end of siding (e.g. `3RFR`), slow pick-up, so that the directional stick relay at the approach signal is released when direction changes [AAR8066 Sheet 2].
- **BKR, TKR, RGKR**: office indication relays for block clear, track occupied and signal at stop. They appear in the traffic-locking checks [AAR8059; AAR8066].

Three families of practice:

1. **Traffic levers with electric traffic locking**, between attended towers. Each end has a traffic lever. Both levers must be in correspondence (both normal or both reversed). Electric locks (FL/FLM) or a relay line circuit (FR) enforce it [AAR8026; AAR8035; AAR8064; AAR8065; C&O1921; RS1932]. On the C&O in 1921, the entering signals lock the traffic levers reversed, and the home control of the first automatic signal is carried over the far tower's traffic lever normal contact [C&O1921 p. 130].
2. **APB-style line circuits, direction set by the CTC signal control.** No traffic lever. SP CTC: clearing a station-leaving signal cuts energy off the line circuits of all opposing signals, so "the established route and traffic direction is automatically retained" [RS1942; RS1945; RS1947]. CB&Q 1946: the eastward traffic relay `4RFR` picks up "over a front contact of the eastward signal control code application relay RGZ", which opens the opposing line circuit and knocks down the opposing intermediates in cascade [CBQ1946 p. 614].
3. **Control-machine traffic locking.** The AAR CTC drawings put a per-block traffic relay in the machine. It refuses a control for an opposing signal while a signal is being cleared, is cleared, or the block is occupied [AAR8066 Sheet 3; AAR8082; AAR8059]. Where there are no line wires, the office relays plus automatic control cycles to both ends do the job that line wires do elsewhere [AAR8059].

APB versus CTC (inference from RS1923, RSE1921, CBQ1946, RS1942):

- In APB (timetable and train-order territory), direction is established by the **train**. When it passes the head-block (starting) signal, its track relay drops and the opposing H controls cascade to stop [RS1923; RSE1921 in ABSAPB].
- In CTC, direction is established by the **control**: the leaving signal's control opens the opposing line before the train arrives, and the leaving signal clears only when energy comes back from the far end. On CB&Q that round trip "requires about 6 sec." [CBQ1946 p. 615].
- Both use the same directional stick relays (SR) at intermediates for following moves [RS1942; CBQ1946]. SP calls its CTC line circuits "the conventional arrangement of absolute permissive block stick relays", which also give "absolute control of opposing station-leaving signals" [RS1942].

### b. What sets and what releases

Set:

- **SP**: the cleared station-leaving signal. The opposing leaving signal "cannot be cleared, regardless of whether a control code is sent" [RS1947 p. 92; RS1945].
- **CB&Q 1946**: the traffic relay picks up on receipt of the control (RGZ), before the signal clears [CBQ1946 p. 614].
- **AAR 8082 (machine)**: the office `4-8FR` is reversed only over "a circuit which checks the block unoccupied and opposing signals at stop and not in time". The code then carries a traffic step that sets the field FSRs at both ends [AAR8082 Sheet 4-5].
- **AAR 8059 (coded track, no line wires)**: the control picks `4RGZR`, and an automatic control cycle picks `6LTFZR` at the far end, which starts code back through the rails. When the code reaches the leaving signal, that signal clears. The indication (block clear, signal clear) then picks the office `4-6RFSR` "to establish and maintain the direction of traffic" [AAR8059 Sheet 7-8]. This is the one primary source where the indication sets a direction relay.
- **Train entering, APB**: [RS1923; RSE1921] (see ABSAPB).

Held:

- While the signal is clear: by the signal or traffic relay itself [RS1947; AAR8059 "stuck up as long as 4R signal is clear"].
- Once the train is in the block: by the track relays in the line circuit and by the SR stick relays [CBQ1946; AAR8059 "stuck up ... by LRBKR down"].

Released, in the order the sources give:

- **Lever at stop.** CB&Q: `4RFR` is "released with the restoration of C.T.C. machine levers to normal" [CBQ1946 p. 616]. AAR 8059: release only "providing signal lever 4 is not still turned to the right" [AAR8059 Sheet 8]. AAR 8066: the machine traffic locking "is dependent on leaving the switch and signal control levers in the position called for until the indications have been received". ICC 1939 Item 412: a cleared signal must not be restorable to stop "by the operation of any lever other than its controlling lever" [ICC1939]. SP satisfied Item 412 with its line circuits alone [RS1942; RS1947].
- **Whole block vacant**, from opposing signal to opposing signal at the adjacent CPs. CFR §236.405: occupancy of that track "shall prevent changing the direction of traffic". ICC 1939 Item 382 tests that traffic-changing levers cannot be worked "with any part of the section occupied". CB&Q: "Traffic direction is maintained until the eastbound train is by signal 6LA or 6LB" (the far CP's opposing signal) [CBQ1946 p. 616]. AAR 8059 releases when the train "proceeds entirely out of the block (passed 6L signal)". AAR 8064: only when the track is unoccupied can the traffic lever be restored.
- **Approach or time locking expired.** SP: if a proceed aspect "is taken away" with the approach occupied, the opposing line control is not closed until the time release (DT-10 relay) expires [RS1942; RS1945; RS1947]. CFR §236.407 requires approach or time locking "where route or direction of traffic can be changed". AAR 8082 checks the opposing signals "not in time"; AAR 8066 Sheet 2 has the approach stick relays.
- **Directional stick relays released.** AAR 8066: `3RFR` is slow pick-up so that the approach signal's directional stick relay is released when traffic changes [AAR8066 Sheet 2]. AAR 8059 warns that cancelling an unlock too early can leave "an APB directional stick" up in the field.

Exception (modern text only): CFR §236.405 lets an aspect not exceeding restricted speed be shown into the occupied block when a train nears the next CP to switch there. I did not find whether the ICC rules of the 1950s had this text (not found).

### c. One circuit or relays in correspondence; what travels on the line wires

- **Neither one circuit nor two end relays.** In the line-wire CTC schemes it is a chain. Each signal location feeds the next segment only through its own relays (HR, SR, track relays), so the direction propagates location by location. CB&Q describes the segments, each re-fed at the double intermediate locations over back contacts of the opposing HR and SR [CBQ1946 pp. 613-615]. The AAR HD line circuits are the same, broken through track relays and re-fed at each location [AARTC71 Dwg 8000, 8044; ABSAPB].
- **End relays kept in correspondence** occur in traffic-lever and coded schemes. Examples: the two traffic levers and their FR/FL [AAR8026; AAR8035; AAR8064]; field `FSR` at both block ends set by code [AAR8082]; and the office `FSR` with field `TFZR` at both ends [AAR8059]. A two-wire traffic locking line circuit links the ends on N&W 1949 and Erie 1942; it "checks the opposing signals in the stop aspect" [NW1949 p. 433].
- **SP specifically**: two separate two-wire, normally energized line circuits per station-to-station block, one per direction, each "checking, double-break, through track relays" [RS1947 p. 92; RS1942; RS1945].

On the wires (SP and CB&Q, inference from the descriptions):

- *energized* = every track circuit of that segment is clear, and the opposing signals behind are at stop;
- *polarity* (polar DP-14/DP-17 relays on SP; a biased-neutral DR on CB&Q) = the next signal clear or at stop;
- *which end feeds* = the direction;
- SP also used the same wires for approach locking and for releasing hand-throw switch electric locks. The two line circuits "detect track occupancy of the station-to-station block as a whole" [RS1947 p. 92]. SP's turnout signal reads relays 4LPR and 2RPR. They are up only if no leaving signal is cleared and no track circuit in the block is occupied [RS1942].

Individual track circuits of the block do **not** travel as separate facts; only their conjunction per segment does
(inference). The code line reported OS circuits, switches and signals [RS1942; ABSAPB]. Some machines also showed
block occupancy (`BK` lamps) and a direction-of-traffic lamp: Burlington 1951 lights it "when the dispatcher sends
out a control to clear a signal" [CBQ1951]; UP used pink and green direction lamps and B&O lamps in open arrows above the track diagram [RS1951TDI]; AAR 8059 has the `4-6RFE` lamp.

Coded track alternative: there are no line wires. The rails carry the code, and the feed end is reversed to set
the direction ("set up to feed ... in the direction opposite to the train movement") [NW1949 p. 433; AAR8059].

### d. What each location needs

Intermediate signal location (double location on SP and CB&Q):

- the track relays of its block ahead (in the line circuit);
- the next signal's state (line polarity, or the D/DR relay);
- the opposing signal's HR and SR at the same location, so that each signal's control checks the other at stop [RS1947 "Signals Check Each Other"; CBQ1946];
- its own directional stick relay SR. It picks up as a train passes the signal (track relay drops before HR drops) and sticks until the HR picks up again [CBQ1946 p. 615; RS1927Spray].

No traffic relay is needed at the intermediate in these schemes. Traffic-lever schemes add an FPR repeater [AAR8064].

Control point (station-leaving signal), from the far end:

- energy back on the line circuit, which proves that the opposing leaving signal is at stop and not in time, that every track circuit of the block is clear, and that no opposing SR is up [CBQ1946; RS1942; RS1947];
- the line polarity, which selects approach versus clear [RS1942 in ABSAPB].

On CB&Q the leaving signal's mechanism is fed only over a front contact of its own `4RFR` with that returning
energy [CBQ1946 p. 615]. This is the relay form of "direction is part of the route equation" (inference).

### e. Southern Pacific

Primary SP evidence (trade-press articles on SP installations, written with SP signal forces; no SP rulebook or
signal instruction on traffic locking was found):

- **No traffic levers.** Direction follows the signal levers. A cleared station-leaving signal locks out the opposing one in the field "regardless" of the code sent [RS1942 (1942 article, location not named); RS1945 Colton-Indio; RS1947 Lucin-Bridge]. Earlier, San Jose 1939 set "traffic-direction locking" by the signal levers, with two levermen cooperating [RS1939SJ in ABSAPB].
- **Two normally energized two-wire line circuits per station-to-station block, one per direction.** As a result, at rest *no* direction is established: both directions' line circuits are energized while no leaving signal is clear and the block is empty [RS1942; RS1945]. CB&Q differs: it keeps the direction last used [CBQ1946].
- **Approach locking by DT-10 time relay** in the opposing line control. SP cites it as its means of complying with Item 412 [RS1942; RS1945; RS1947].
- **Signal controls are stick**, with a non-stick (fleet) special on the code [RS1942 in ABSAPB]. SP machines had fleeting controls, later reused for automatic operation [SP1962].
- **Hand-throw switch electric locks and turnout signals** read block vacancy from the same line circuits. The APB directional stick features let a turnout signal clear behind a receding train [RS1942; RS1945].
- **SP 1959-62 "automatic CTC"** (El Paso-Yuma): circuits clear signals ahead of trains and make meets. The dispatcher "will, of course, suffer the penalty of time locking if he attempts to change a route after the automatic system has established it" [SP1962].
- Not found: SP rulebook CTC or traffic rules and their numbers; SP signal department instructions on traffic locking; any SP Coast Division traffic-locking description after 1939.

## 3. Open points

1. The AAR *American Railway Signaling Principles and Practices* chapters on CTC and on traffic locking were not found online. The AAR content above comes from the *Typical Circuits* addenda and the nomenclature, not from the Principles text.
2. Not opened: the AREMA C&S Manual (paywalled), GRS *Elements of Railway Signaling* (1979; the IRSE NL page describes it but hosts no scan), and US&S CTC bulletins.
3. Pre-1984 wording of the rule now in CFR §236.405, including its restricted-speed exception (ICC rules of the 1950s), was not found. The 1939 ICC text has only Item 409 ("means shall be provided for establishing, maintaining, and changing direction of traffic").
4. The addendum dates of the AAR drawings cited were not read reliably from the scans. They are cited by drawing and sheet, in the 1971 compilation.

## 4. Sources

| Key | Citation | URL | Used for |
|---|---|---|---|
| AARNOM46 | AAR Signal Section, *Circuit Nomenclature, Written Circuits and Graphical Symbols* (Manual Part 33, 1943; approved Sept 1934, Mar 1944; as in Manual complete to Oct 1946), pp. 2-9 | local: `~/Dropbox/Arduino/libraries/FieldUnit/docs/reference/AAR. Signal Section. Circuit nomenclature, written circuits, and graphical symbols. 1946-10.pdf` | F = traffic; FR, FSR, EFSR, FL, FLM, FLR, FLK, FC; BPR, RGPR, SR, ASR |
| AARTC71 | AAR Communication & Signal Section, *Typical Circuits Representing Current Practice for Railway Signaling*, compiled 1971 (424 pp.) | https://jonroma.net/media/signaling/standards/na/aar/AAR.%20Typical%20circuits%20representing%20current%20practice%20for%20railway%20signaling.%201971.pdf | index, Dwg 8000/8044 (via ABSAPB) |
| AAR8026 | same, Addendum to Dwg 8026A, "Typical Traffic Circuits Between Attended Offices" (relay type) | as AARTC71 | traffic levers both normal / both reversed; FR; following moves |
| AAR8035 | same, Addendum 8035A, "Typical Traffic Locking Circuits Between Attended Offices Using Electric Lever Locking" | as AARTC71 | electric locks on traffic levers |
| AAR8059 | same, Addendum 8059A, "Typical Normally De-energized Coded Track Circuits and Traffic Control Without Line Wires", Sheets 1-8 | as AARTC71 | GZR, TFZR, LFSR/RFSR, set by indication, release on lever + block clear, tumble-down on overrun |
| AAR8064 | same, Addendum 8064A, traffic control between attended and direct-wire remote interlockings | as AARTC71 | 1FR, FPR at each signal location; reverse only with signals at stop and track unoccupied |
| AAR8065 | same, Addendum 8065A, traffic control between attended and coded remote interlockings | as AARTC71 | FR, FPR, RFSR; operator coordination |
| AAR8066 | same, Addendum 8066A, "Typical Traffic Control Circuits Using 2-Wire HD Line Control", Sheets 1-3 | as AARTC71 | per-block magnetic polar stick FR in machine; 3RFR; levers left until indications received |
| AAR8082 | same, Addendum 8082A, "Circuits for Modified Traffic Control System Using Two-Wire Line Control and Spring-Power Ends of Siding", Sheets 4-5 | as AARTC71 | office 4-8FR; field FSR feed/receive ends; "not in time" |
| ICC1939 | "I.C.C. Issues Rules, Standards and Instructions for Signaling", *Railway Signaling*, 1939 (order of May 25, 1939), items 382, 401-414 | https://www.jonroma.net/media/signaling/railway-signaling/1939/ICC%20Issues%20Rules%2C%20Standards%20and%20Instructions%20for%20Signaling.pdf | traffic locking test; Item 409 direction of traffic; Item 412 |
| CFR236 | 49 CFR Part 236, §§236.381, 236.404, 236.405, 236.407, 236.760, 236.769 (eCFR, text as of 2025-01-01; Subpart D wording from 49 FR 3386, Jan. 26, 1984) | https://www.ecfr.gov/current/title-49/subtitle-B/chapter-II/part-236 | regulatory cross-check |
| CBQ1946 | Zane, W. F. (Signal Engineer, CB&Q), "New Signal Control Line Circuits in Centralized Traffic Control Territory on the Burlington", *Railway Signaling*, Sept. 1946, pp. 612-616 (second of two; first Aug. 1946 p. 528) | https://www.jonroma.net/media/signaling/railway-signaling/1946/New%20Signal%20Control%20Line%20Circuits%20in%20Centralized%20Traffic%20Control%20Territory%20on%20the%20Burlington.pdf | FR from RGZ, cascade knock-down, SR, release, direction last used, 6 s cycle |
| CBQ1951 | "Burlington Simplifies CTC for Light-Traffic Single Track", *Railway Signaling*, Nov. 1951, pp. 774-780 | https://www.jonroma.net/media/signaling/railway-signaling/1951/Burlington%20Simplifies%20CTC%20for%20Light-Traffic%20Single%20Track.pdf | direction lamp lit on control |
| RS1942 | "C.T.C. Saves Train Time on a Section of the Southern Pacific", *Railway Signaling*, Oct. 1942, pp. 538-545 | https://www.jonroma.net/media/signaling/railway-signaling/1942/CTC%20Saves%20Train%20Time%20on%20a%20Section%20of%20the%20Southern%20Pacific.pdf | SP line circuits, direction retained, Item 412, turnout LPR/RPR |
| RS1945 | "Southern Pacific Installs CTC on 72 Miles of Single Track", *Railway Signaling*, Feb. 1945, pp. 94-99 | https://www.jonroma.net/media/signaling/railway-signaling/1945/Southern%20Pacific%20Installs%20CTC%20on%2072%20Miles%20of%20Single%20Track.pdf | normally energized line circuits, DT-10, electric lock |
| RS1947 | "Southern Pacific Installs C.T.C.", *Railway Signaling*, Feb. 1947 (p. 92 for line circuits) | https://www.jonroma.net/media/signaling/railway-signaling/1947/Southern%20Pacific%20Installs%20CTC.pdf | "regardless" of code; block as a whole; signals check each other |
| SP1962 | "SP Has 500 Miles of Automatic CTC", *Railway Signaling and Communications*, 1962, p. 22 | https://www.jonroma.net/media/signaling/railway-signaling/1962/SP%20Has%20500%20Miles%20of%20Automatic%20CTC.pdf | SP fleeting controls; time locking penalty |
| NW1949 | "Either-Direction Running on Two Tracks on the Norfolk & Western", *Railway Signaling*, July 1949, pp. 432-437 | https://www.jonroma.net/media/signaling/railway-signaling/1949/Either-Direction%20Running%20on%20Two%20Tracks%20on%20the%20Norfolk%20%26%20Western.pdf | traffic-direction locking line circuit; coded track reversal |
| ERIE1942 | "Centralized Traffic Control on the Erie", *Railway Signaling*, April 1942, pp. 189-191 | https://www.jonroma.net/media/signaling/railway-signaling/1942/Centralized%20Traffic%20Control%20on%20the%20Erie.pdf | normally de-energized two-wire traffic locking circuit |
| C&O1921 | Johnson, H. E., "A New Idea in Traffic Locking on the C. & O.", *Railway Signal Engineer* v14 n4, April 1921, pp. 130-131 | https://www.jonroma.net/media/signaling/railway-signaling/1921/A%20New%20Idea%20in%20Traffic%20Locking%20On%20the%20C%26O.pdf | traffic levers with APB; entering signals lock traffic levers |
| RS1927Spray | Spray, L. E. (Circuit Engineer, US&S) and others, "Various Circuits for Directional Control of Single Track Signals", *Railway Signaling* v20 n7, July 1927, pp. 269-270 | https://www.jonroma.net/media/signaling/railway-signaling/1927/Various%20Circuits%20for%20Directional%20Control%20of%20Single%20Track%20Signals.pdf | US&S APB directional stick relays; Hall-Kendall selector (IC) |
| RS1951TDI | "Traffic Direction Indication" (Kinks / What's the Answer), *Railway Signaling and Communications*, Aug. 1951, p. 558 | https://www.jonroma.net/media/signaling/railway-signaling/1951/Traffic%20Direction%20Indication.pdf | UP and B&O direction lamps on CTC machines |
| ABSAPB | `docs/review/abs-apb-research-2026-10-30.md` | this repo | RS1923, RSE1921, RS1932, RS1939SJ, AARTC71 Dwg 8000/8044, SP code content |
