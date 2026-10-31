# ABS, APB, home and distant signals: prototype research (2026-10-30)

Research note for a future ADR. It records prototype facts only. It designs nothing.

## 1. Scope and order of authority

- Scope: what happens between control points (CPs). The questions are automatic block signals (ABS), absolute permissive block (APB), direction of traffic on one and several tracks, the seam with interlockings and CTC CPs, Southern Pacific (SP) practice 1942 to 1985, and home and distant signals (section G).
- Order of authority used to weigh every source:
  1. The relay model and AAR practice: AAR Signal Section texts and typical circuits, period trade press (*Railway Signal Engineer*, *Railway Signaling*), US&S and GRS material. This is the design principle.
  2. Railroad rulebooks, for terms and rules. Each rule is given with its book and year. Rule numbers differ by road and year.
  3. Modern and hobby sources (Lundsten, Trains, forums, Wikipedia, 49 CFR 236 as it reads today). Pointers only, or marked "unverified".
- Marks: "(paraphrase)" = wording came through a web fetch or OCR and is not checked letter by letter. "(unverified)" = no primary source was opened. "(inference)" = my reading of a primary source, not its words.
- Most period articles were read from the OCR text layer of the jonroma.net scans. OCR has errors; quotes were kept short and checked against context. AAR56 was read from its page images.

## 2. Findings

### A. ABS on single and double track

Track circuits and blocks

- A block is "a length of track of defined limits" governed by block signals [PRR56 Definitions; CFR236 §236.708]. ABS is "a series of consecutive blocks" governed by automatic block signals [UCOR62].
- An automatic signal's block is one or more track circuits. A long block is split into cut sections with their own track relays [AARTC71 Dwg 8003, 8004 "relayed cut section"].
- On SP CTC, the main track opposite a siding is cut into two track circuits, and so is the siding [RS1942; RS1945; RS1950].

Line circuits and the H, D, HD relays

- The aspect of an automatic signal depends on the block ahead and on the next signal. The dependency is carried back over a line circuit, a pair of line wires from the next signal location, broken through the track relays of the block [AARTC71 Dwg 8000, 8002].
- The AAR typical circuits name the line relay HD (or HDR). It is polarized: current in one direction means "next signal at stop" and the other direction means "next signal proceeding"; no current means the block is occupied or the line is broken [AARTC71 Dwg 8000, 8002; RSC1967] (inference from the circuit notes and the 1967 walk-through).
- "Pole changing" is the reversal of the line polarity when the next signal changes. A "retained neutral polarized line relay" does not open its neutral contacts during the reversal [AARTC71 Dwg 8000 note] (paraphrase).
- Alternative: an ordinary polarized relay plus a slow-release neutral repeater (HPR) that bridges the pole change [AARTC71 Dwg 8002 note; RSC1967].
- Other AAR variants use separate relays: a neutral H line relay (block clear) and a biased neutral D line relay (next signal clear) [AARTC71 Dwg 8001, 8044]. The glossary already records that the AAR letter D means "proceed indication", not "distant" [AARLIST].
- Double break: the HD line circuit is broken on both wires by track relay contacts [AARTC71 Dwg 8000 note]. SP CTC line circuits are "checking, double-break, through track relays" [RS1947] (paraphrase).
- Energy for the HD line is taken through a front contact of the track relay ahead of the signal, to stop a false clear flash when a short train leaves the block [AARTC71 Dwg 8000 note] (paraphrase).
- Three aspects follow from H and D: block occupied = stop (or stop and proceed); block clear, next signal at stop = approach; block clear, next signal proceeding = clear [RSC1967; AARTC71 Dwg 8000 "Code Rules 281-285-291"].
- Four-aspect signals add a slow-release D or AD relay, for advance approach [AARTC71 index "Four aspect"].
- Where signals are closer than stopping distance, "three-block indication" is used; a train receiving Proceed has three clear blocks [AAR56 p. 52] (paraphrase).

Coded track circuits

- Coded track circuits replace the line wires: the code rate in the rails carries the next signal's state back to the signal in the rear [AARTC71 index "coded track circuits without line wires"; RS1944].
- SP did not use them on the Colton–Alhambra CTC because crossings cut the track circuits up too much; it used d-c neutral track circuits with line circuits [RS1950] (paraphrase).

Approach lighting

- Signals are often lit only when a train approaches. AAR circuits do it with an AER relay in series with the HD line circuit, slow release to bridge pole changes [AARTC71 Dwg 8000 note].
- 1923 methods: a relay in series with the track battery, a back contact of the track relay, a relay in series with the line battery, and on single track the opposing signal's circuit controller [RS1923 (Trout answer)].

Permissive and absolute aspects

- Standard Code names [AAR56 pp. 52-54]: Rule 290 "proceed at restricted speed"; Rule 291 "stop and proceed"; Rule 292 "stop".
- Rule 292 aspects are used at interlockings and block stations "where it is desired to hold trains" [AAR56 p. 54]. Rule 291 aspects are used on automatic block signals where stop and stay is not required [AAR56 p. 54] (paraphrase).
- Number plates: "On some roads automatic block signals are equipped with number plates" [AAR56 p. 54]. Some roads put the plate only on stop-and-proceed signals [AAR56 p. 54].
- Absolute signals are designated "by the absence of a number plate" [RS1941; also PRR on APB, RS1929 per search snippet] (paraphrase).
- SP 1960: automatic block signals bear number plates; absolute and interlocking signals bear none, but may carry an "A" or "SA" plate [SP1960 "Fixed Signals"].
- Grade signals: a marker (G disc, short arm) lets tonnage trains pass a stop-and-proceed signal without stopping [AAR56 p. 54; PRR56 Rule 291 note].
- Illinois Central let trains pass stop-and-proceed signals without stopping at 15 mph, multiple track 1930 and APB single track 1933 [RS1941] (paraphrase).
- Rule numbers for the stop rule vary: Standard Code 292 [AAR56]; SP 1960 Rule 290 is "Stop", home signal red [SP1960]. SP's own numbering differs from the Code.

Double track

- Double-track signalling "pre-supposes" one direction per track; a train accepting a clear signal may expect the block clear [RSE1921] (paraphrase).
- On double track a signal controls only to the next signal; on single track the same scheme does not protect against opposing trains [RSE1921].

### B. APB

Origin

- GRS developed APB. It was first put in service in 1911, Kinnear to Vinemount, Ontario, Toronto Hamilton & Buffalo [RS1954].
- GRS showed a scheme for interurban lines at the Railway Appliances Association exhibit, March 1911, then adapted it for steam roads within a year [RSE1920 (Fugina)] (paraphrase).
- "Hoyt" or "Cox" as inventor: not found. A 1911 GRS paper is credited to W. K. Howe (search snippet only) (unverified). See open questions.
- A 1911 *Signal Dictionary* already described APB schemes with "normal danger" head-block signals [RS1940] (paraphrase).

Principle

- APB gives permissive indications for following trains and absolute stop for opposing trains between sidings [RS1923].
- Requirements stated by its developers: full overlap protection for opposing moves, double-track protection for following moves, reliable distant signals [RSE1921].
- The extent of a signal's control is variable and "depend[s] upon the direction of traffic" [RSE1921]. The means is a stick relay [RSE1921].
- Layout: the block for opposing moves runs siding to siding; the signals entering it show stop when an opposing train occupies it [RSC1967] (paraphrase of AAR Ch. XV summary).
- Leaving signals at the end of a passing track are "positive" (absolute) signals with square-end blade and marker light; signals between are permissive [RSE1920 (Fugina)]. Lake Shore 1912 used the same scheme: pointed blades between stations, square-end absolute blades beyond the leaving end of sidings [RS1912].
- SP CTC terms: "station-leaving" semi-automatic signals bound a "station-to-station block"; signals between are "intermediate signals" [RS1942; RS1945; RS1947].
- "Head block": the period phrase is "station-leaving, head-block signals" [RS1940; RS1941]. Claus 1949 writes "station-leaving head-block signals" [RS1949]. LA&SL 1923 calls it the "starting signal" [RS1923].

The tumble-down (relay level)

- When a train passes the starting signal, its track relay drops, which opens the control wire of the first opposing signal's H relay. That H relay opens the next one, and so on to the far siding [RS1923]. The PRR 1927 explanation calls this "cascading the home control relays" [RS1927b].
- The last signal in the chain, on going to stop, pole-changes the line so the opposing signal at the far siding shows caution [RS1923] (paraphrase).
- "Tumble-down" as a word: a 1920s patent writes "tumble down circuits" (search snippet only) (unverified). Lundsten uses "tumble-down" [LUNDSTEN] (modern).
- Following moves: the directional stick relay. It picks up through a back contact of the first track circuit and a signal contact (signal clear), and holds through its own front contact and a back contact of the signal control relay [RSE1921]. With it up, the signal behind the train clears to approach as soon as the train is far enough [RSE1921; RS1923 (STK relay)].
- AAR names: "directional stick relay" [AARTC71 Dwg 8027 sheet 6, 8029]; relay SR, e.g. 12SR, with polar HDR and slow-release HPR, three-wire HD control [RSC1967].
- Traffic cannot reverse until the stick relays restore to normal [RSE1921].
- Self-check: if two opposing trains pass opposing signals at once, a "locked-up condition" holds all signals at stop until a maintainer clears it, leaving "a tell-tale" [RSE1921] (paraphrase).
- A train that changes direction keeps the direction it set: "Whenever a train passes a signal at clear, it establishes its direction" [RSE1920 (Fugina)] (paraphrase).

Overlaps and spacing

- If sidings are too close for twice stopping distance between opposing intermediates, opposing trains could both get clear and meet red intermediates [RS1949].
- Remedies: manually controlled directional overlap, and automatically timed overlap using a speed-measuring section [RS1949].
- Where two opposing operators can clear head blocks independently, APB alone lets both clear at once; "check locking" (each head-block control broken through the other at stop) is the fix [RS1939Q] (paraphrase).

### C. Direction of traffic on several tracks

Current of traffic

- "Current of traffic": movement on a main track in one direction "as specified on the time-table" [PRR56 Definitions]. UCOR 1962 and CFR use the same idea [UCOR62; CFR236 §236.734].
- PRR 1956 D-151: on two main tracks, trains keep right unless the time-table says otherwise [PRR56] (already in the glossary).
- Standard Code double-track rules, quoted 1925: D-251 runs trains "with the current of traffic by block signals"; D-261 runs them "against the current of traffic by block signals", on portions specified in the time-table [RS1925] (paraphrase).
- SP 1960 D-251 covers following movements only: trains run "with reference to other trains in the same direction by block signals" on tracks specified in the timetable [SP1960]. The SP 1960 excerpt has no 261 text.
- UCOR 1962: where two tracks are each signalled both ways, the timetable names them (North Track, South Track) and "there is no specified current of traffic" [UCOR62] (Canadian code).

Moves against the current

- 1913 Ohio Central: double track, right-hand running, signals with the current; reverse moves by interlocking dwarf signals and manual block between towers. A traffic lever at one tower prevents clearing any opposing signal [RS1925].
- A second move against the current was not allowed until the first had cleared the far end [RS1925] (paraphrase).

Tracks signalled in both directions

- Missouri Pacific, 1925-27: each track signalled "in the same manner as a single track railroad" for either direction, by the overlap method [RS1927MP] (paraphrase).
- Erie, 1932, Hammond to Griffith: single-track ABS on each track plus "traffic direction locking". Normally set for right-hand running. To reverse, the far tower reverses its traffic lever first; then the near tower can reverse its lever if the track is unoccupied. Intermediates act as single-track signals [RS1932].
- The Erie traffic locking runs over a two-wire line circuit "carried through each track relay involved" [RS1932] (paraphrase).
- SP San Jose, 1939, College Park to Lick: three tracks, then double track, all signalled for movement either direction; "traffic-direction locking" is set by the signal levers, and the two levermen "must cooperate" to set direction [RS1939SJ] (paraphrase).
- Each track has its own traffic direction. One track can run one way while the next runs the other; the Erie and San Jose installations set direction per track by lever [RS1932; RS1939SJ] (inference).

Traffic locking: definitions and circuits

- Traffic locking: electric locking that prevents changing the direction of traffic on a section while it is occupied, or while a signal is cleared into it [CFR236 §236.769] (modern wording).
- AAR traffic-locking circuits exist for: relay type between attended offices; electric lever locking between attended offices; mechanical locking at an attended location with circuit locking at a coded or direct-wire remote location [AARTC71 Dwg 8026, 8035, 8064, 8065].
- AAR Dwg 8035: two-wire traffic control with electric locks on the traffic levers; levers normal for westward, both reversed for eastward; lights show block occupancy and direction; following moves into an occupied block are allowed [AARTC71 Dwg 8035 note] (paraphrase).
- AAR Dwg 8044 (two-wire polarized line, both directions): usable only where manual control establishes direction; if the two ends are under two operators, "supplemented by traffic locking" [AARTC71 Dwg 8044 note].
- In SP CTC, a cleared station-leaving signal cuts energy off the line circuits of all opposing signals in the station-to-station block, so "the established route and traffic direction is automatically retained" [RS1942; RS1945; RS1947] (paraphrase).
- Reversal after a signal is taken away waits for the approach-locking time release (DT-10 time relay); this meets ICC Item 412 [RS1942; RS1947] (paraphrase).
- So the release of direction is by an unoccupied block (track relays in the line circuit) or, if a signal was cleared and then taken away with a train approaching, by time [RS1942] (inference).

APB and multi-track

- No source opened says APB itself was applied per track on dispatcher-set double track. Erie 1932 used single-track ABS per track plus traffic levers [RS1932]. Treat "APB per track" as open.

### D. The seam with interlockings and CTC CPs

Where block limits and interlocking limits sit

- Interlocking limits: tracks between the outer opposing home signals [PRR56 Definitions; CFR236 §236.753].
- Interlocking home signals governing routes into a block also govern the block [PRR56 Rule 501].
- When an interlocking is in use in ABS territory, interlocking rules govern through it [UCOR62 Rule 506].

What the CP signal reads from the block beyond

- SP CTC leave-siding signals have three aspects. With a train in the block of automatic signal 8, signal 4 shows Approach (yellow); with the train beyond automatic signal 10, it shows Clear (green) [RS1942].
- So the CP's leaving signal is controlled by the same line circuits as an automatic signal: its aspect depends on the next automatic signal [RS1942; RS1945] (inference).
- SP station-entering signal 5 (CP home) shows green under red into an empty siding, yellow under red into an occupied one, red over red if the siding holds an opposing train or the far signal is cleared into it [RS1942].

What the block reads from the CP

- In SP CTC, clearing a station-leaving signal cuts off the line circuits of all opposing intermediates and the opposing station-leaving signal [RS1942; RS1945; RS1947]. The dispatcher's code sets direction; APB stick relays still clear intermediates for following trains [RS1942].
- That is APB with the head blocks controlled by the dispatcher (inference). The nearest period wording: a 1940 editorial proposes reviving "normal danger" head-block station-leaving signals with "manual remote control" so trains move "by signal indication without train orders" [RS1940] (paraphrase). No source opened says "CTC is APB with dispatcher-controlled head blocks" in those words.
- SP CTC signal controls are stick: a new code is needed to clear for a second train [RS1942].

CTC over former ABS or APB

- SP 1942: the line had automatic block signalling for years with hand-throw switches, timetable and train orders; CTC replaced the semaphores with searchlights and renewed the relays and line circuits [RS1942].
- SP Colton–Indio, 1945: the old signalling was two-position lower-quadrant ABS "controlled by overlap circuits"; it was removed and replaced [RS1945] (paraphrase).
- Santa Fe put CTC into service one siding at a time where an existing ABS was converted (search snippet) (unverified).

Code line content (SP 504-B, 1942)

- Controls per field station: switch normal, switch reverse, signal right, signal left, maintainer's call, two specials (call-on, stick/non-stick) [RS1942] (paraphrase).
- Indications: switch normal, switch reverse, signal right, signal left, OS track occupancy, power-off, one extra (fire, approach, etc.) [RS1942] (paraphrase).
- The track diagram lamps repeat OS occupancy at the switches [RS1942].

Distant and approach signals at the seam: see section G.

### E. Southern Pacific, 1942-1985

- SP 1960 rulebook (Pacific Lines) [SP1960]:
  - D-251, D-253, D-254 (following movements by block signals, timetable designated tracks).
  - Automatic block signals carry number plates; a distant light signal's plate has prefix "D"; absolute and interlocking signals carry no number plate but may carry "A" or "SA".
  - Aspect rules 281 to 298 in SP numbering: 285 Approach (yellow), 286 Distant signal yellow (plate prefix D), 287 Grade signal red, 290 Stop (home signal red), 293 home signal red with triangular plate (inspect, then proceed), 297 dummy masts, 298 block indicators.
  - Train order Form Z examples refer to number plates "reversed, showing yellow" (meaning not explained in the excerpt).
  - The excerpt seen has no SP CTC rules and no SP stop-and-proceed rule for automatic signals.
- SP signal practice in CTC (Railway Signaling, 1942-1950):
  - Searchlight signals for semi-automatic (CP) and intermediate signals [RS1942; RS1945].
  - No red in a clear aspect: the lower unit is dark on a main-line clear [RS1942].
  - Triangular "P" plate on signals with detector (slide, fire) protection [RS1942].
  - Two separate two-wire normally-energized line circuits per station-to-station block, one per direction, polar DP14 or DP17 control relays [RS1942; RS1945; RS1947].
  - Intermediates are "double locations"; each signal's control checks the other at stop [RS1947; RS1950].
  - Hand-throw turnouts between CPs get a high dwarf signal and a telephone; the APB direction stick features let it clear behind a receding train [RS1942].
  - Motor-car indicators on separate line circuits [RS1942; RS1950].
  - US&S equipment, 504-B code [RS1942]; US&S multiple time code with coded carrier [RS1947].
- SP Coast line items found:
  - San Jose 1939: College Park to Lick, 4.5 miles, CTC-type machine at San Jose station plus a GRS Model 2 interlocking at College Park; traffic-direction locking; triangular marker plates at Lick [RS1939SJ].
  - The 1942 article does not name its location. Its facts (17 miles, 2.2% grades, summit tunnel, East a sub-division point with yard and helpers) fit San Luis Obispo to Santa Margarita (inference). A forum says SLO–Santa Margarita was SP's first CTC, in 1942 [RAILPIX] (unverified).
- SP in the 1920 APB debate: E. E. Worthing, signal engineer of the SP Atlantic System, gave one of the three papers [RSE1920]. His paper was not read.
- Not found: SP rule numbers for APB or CTC 1942-1985; the full SP 261 text; SP Coast Division APB history; when SP Coast intermediates were searchlights vs semaphores.

### F. Model-relevant prototype answers

1. Two masts at one block joint. Yes, normal. AAR typical circuits for track signalled both ways come as "opposite locations" (both directions at one joint) and "staggered locations" (offset) [AARTC71 Dwg 8027, 8029]. SP intermediates were "double locations" whose controls check each other at stop [RS1947; RS1950]. A double location at a siding end is also common ("approach lighting at a double location") [RS1923]. Pairing in the relay model is by the shared track circuits and by the check of the other signal at stop, not by a mast [RS1947] (inference).
2. Track circuits and neighbours. In the SP CTC examples, each field station's code reports only its own OS circuit and functions [RS1942]. The block between two stations is shared: both station-leaving signals read it through the two line circuits, which run through every track relay of the block [RS1942; RS1947]. Neither station "owns" the intermediate track circuits in the code sense; the line circuit does (inference). Other installations did show every track section on the machine (San Jose 1939, a small direct-control area) [RS1939SJ].
3. One signal standing in for another. A distant signal (or approach signal) gives advance information of a home signal at another location [PRR56 Definitions; CFR236 §236.803]. An automatic signal in the rear of a CP does the same job by its approach aspect (see G). The period name is distant signal; Standard Code era books also say approach signal [UCOR50; UCOR62]. "Repeater" is used for relays (e.g. HPR), not for these signals, in the sources read.
4. Physical vs rule facts.
   - Physical: track circuits and insulated joints, signal locations, number and letter plates, line circuits, traffic levers and locking [AARTC71; RS1942; SP1960].
   - Operating rule: which tracks are under 251-type or 261-type rules, current of traffic, CTC limits, ABS limits; all "designated" or "specified in the time-table" [PRR56; SP1960; UCOR62]. Signals can be taken out of service by train order [SP1960 Form Z].
   - Mixed: whether a signal is absolute or permissive is a circuit fact shown by a physical plate [AAR56 p. 54; SP1960].
5. Is a stand-in signal a distant for that home? Yes when its aspect is controlled by the home's state and it governs the approach to the home: the definitions call that a distant (or approach) signal [PRR56; CFR236 §236.803]. An automatic block signal in the rear of a CP home is functionally that signal's distant; SP used a separate "distant signal" with D-plate where needed [RS1942; SP1960] (inference for the general statement).

### G. Home and distant signals

Definitions and history

- Home signal: "A fixed signal at the entrance to a route or block" [PRR56 Definitions] (paraphrase via fetch). CFR wording is the same [CFR236 §236.806].
- Distant signal: "A fixed signal used in connection with one or more signals to govern the approach thereto" [PRR56 Definitions]. CFR and UCOR call this an approach signal [CFR236 §236.803; UCOR62].
- 1909: the home signal "really gives the indication"; the distant forewarns of the home [LATIMER1909] (paraphrase). Home blades were square-ended, distant blades notched [LATIMER1909].
- AAR56: some roads used a fishtail blade "as approach or distance signals" outside ABS territory [AAR56 p. 41].
- Interlocking locking: distant levers lock their home levers reversed, so a distant clears only when its home is clear [LATIMER1909].
- PRR 1956 Rule 605: movements protected "by home signals and distant signals" [PRR56]. Rule 661: a train delayed between a clear distant and its home must approach the home prepared to stop [PRR56] (paraphrase).

From separate arms to aspects

- Two-position lower-quadrant signals "require two arms" for the three indications of one three-position arm [AAR56 p. 55]. So home and distant were separate arms.
- In England the distant for one home was often on the mast of the home in rear [LATIMER1909]. US automatic signals had "home and distant (on the same mast)" schemes, with separate home and distant line wires [SCOTT1908] (paraphrase).
- Three-position signals and colour lights give approach in one head. The AAR "approach" aspect is "necessary to govern the approach of a train to a signal indicating Stop" [AAR56 p. 53]. AAR56 names advance approach (Rule 282A) and approach (Rule 285) [AAR56 pp. 48, 52, Fig. 30].
- So the distant function is folded into the approach aspect of the signal in the rear, automatic or not (inference from AAR56 pp. 52-53).
- SP 1960 still names a "distant signal" with its own rule (286) and a D-prefix number plate [SP1960].

Place at interlockings and CPs

- The home signal is the absolute signal at the entrance to interlocking limits; interlocking limits run between opposing homes [PRR56; CFR236 §236.753].
- Lower arms or heads of a home signal select route and speed: medium-clear (Rule 283) and limited-clear (281C) are speed within interlocking limits [AAR56 pp. 44, 52].
- Is the distant a separate mast? Both occur. SP 1942 used a separate "distant signal 7" for station-entering signal 5, with an extra lower unit: yellow over green when 5 is set to an empty siding, yellow only when the siding is occupied [RS1942]. In other places the last intermediate gives the approach information (inference from RS1942 Fig. 2 and APB practice in RSE1921).
- In CTC the CP's station-entering signals are the homes [RS1942].

How the distant reads the home

- Semaphore era: separate home and distant line wires; the distant arm is clear only while the home arm is clear, enforced by a circuit breaker on the home semaphore [SCOTT1908] (paraphrase).
- Colour-light era: the home's state goes back on the HD line circuit, polarity = next signal at stop or proceeding [AARTC71 Dwg 8000]. A coded fourth aspect can be sent on a two-wire line to an approach signal [AARTC71 Dwg 8079 title].
- SP 1945 lists "RGPR controls which extend beyond C.T.C. limits" among line circuits [RS1945] (meaning of RGPR not stated; likely a signal repeater relay) (inference).

Direction and multi-track

- Each home has a distant on the approach side for its own direction and track [LATIMER1909; SCOTT1908] (inference from the general definition).
- On single-track APB, a distant for a siding signal was of "questionable value" under overlap schemes: an opposing train could put the home to stop after the train passed a clear distant [RSE1921]. APB was built to make distant indications reliable [RSE1921; RSE1920].

Intermediates as distants

- APB "provides a caution signal whenever it is necessary" to approach the next signal prepared to stop [RSE1921] (paraphrase). Fugina 1920 describes a "double caution indication" approaching a passing track [RSE1920] (paraphrase).
- In CTC the intermediate in the rear of a station-entering signal plays the distant (inference).

## 3. Terminology

| Term | Meaning | Period / road | Source |
|---|---|---|---|
| block | track of defined limits governed by block signals | PRR 1956; CFR | PRR56; CFR236 |
| block limits | the ends of a block, at its block signals | general | PRR56 (inference) |
| ABS (automatic block signal system) | consecutive blocks governed by automatic block signals | UCOR 1962; CFR | UCOR62; CFR236 |
| APB (absolute permissive block) | single-track ABS: absolute between sidings for opposing moves, permissive for following | GRS 1911 on | RS1954; RS1923 |
| head block (head-block signal) | absolute station-leaving signal at a siding end, entering single track | 1940s trade press | RS1940; RS1941; RS1949 |
| starting signal | same function, LA&SL 1923 | LA&SL | RS1923 |
| station-leaving / leave-siding signal | absolute signal governing departure from a station into the station-to-station block | SP 1942-50 | RS1942; RS1947 |
| station-entering signal | CP home signal governing entry to a siding layout | SP 1942 | RS1942 |
| station-to-station block | the block between two passing tracks | SP 1942-50 | RS1942 |
| intermediate signal | automatic (permissive) signal between sidings or CPs | SP; AAR | RS1942; AARTC71 |
| semi-automatic signal | signal cleared by control and put to stop automatically by trains (SP CTC CP signals) | SP 1942 | RS1942 |
| absolute signal | signal whose most restrictive indication is stop (Rule 292) | Code | AAR56 p. 54; RS1941 |
| permissive signal | automatic signal whose most restrictive indication is stop and proceed (Rule 291) | Code | AAR56 p. 54; RS1941 |
| number plate | plate on an automatic signal; absent on absolute signals | SP 1960; AAR | SP1960; AAR56 |
| A / SA plate | plate on an absolute / semi-automatic signal | SP 1960 | SP1960 |
| P plate (triangle) | signal with detector protection | SP 1942 | RS1942 |
| tumble-down | opposing signals cascading to stop when a train enters single track | patent 1920s; modern | LUNDSTEN (unverified as period term) |
| cascading home relays | the relay action behind the tumble-down | PRR 1927 | RS1927b |
| directional stick relay (SR, STK) | stick relay that remembers direction so intermediates clear behind a train | AAR; 1921-67 | RSE1921; AARTC71; RSC1967 |
| opposing overlap | extending a signal's control past the next signal against opposing trains | 1921 | RSE1921 |
| H relay (HR) | home (signal control) relay: block clear | AAR | RSE1921; AARTC71 |
| D relay (DR) | line relay for "next signal proceeding"; D is not "distant" on the AAR list | AAR | AARTC71; AARLIST |
| HD relay (HDR) | polarized line relay combining H and D | AAR | AARTC71; RSC1967 |
| HPR | slow-release neutral repeater of HDR | AAR | AARTC71; RSC1967 |
| line circuit | two-wire circuit between signal locations, no common return | AAR; CFR | AARTC71; CFR236 §236.723 |
| polarized line circuit | line circuit whose polarity carries the next signal's state | AAR | AARTC71 |
| pole changing | reversal of line polarity | AAR | AARTC71 |
| coded track circuit | track circuit whose code replaces line wires | AAR | AARTC71; RS1944 |
| approach lighting | signal lit only on approach of a train | 1923 on | RS1923; AARTC71 |
| traffic lever | lever that sets direction of traffic on a track | 1913-1971 | RS1925; RS1932; AARTC71 |
| traffic (direction) locking | locking that stops a direction change while the section is occupied or a signal cleared into it | 1932; CFR | RS1932; RS1939SJ; CFR236 §236.769 |
| check locking | each opposing head-block control broken through the other at stop | 1939 | RS1939Q |
| current of traffic | movement on a main track in one direction set by the timetable | PRR 1956 | PRR56 |
| signalled in both directions | each track has signals for both directions | AAR | AARTC71; UCOR62 |
| either-direction signalling | same, 1932 term | Erie | RS1932 |
| home signal | fixed signal at the entrance to a route or block | PRR 1956; CFR | PRR56; CFR236 |
| distant signal | fixed signal governing the approach to another signal | PRR 1956; SP 1960 | PRR56; SP1960 |
| approach signal | the same function, later wording | UCOR 1950-62; CFR | UCOR50; CFR236 |
| distant arm | semaphore arm giving the distant indication, often on the same mast as a home | 1908-09 | SCOTT1908; LATIMER1909 |
| approach (aspect) | prepare to stop at next signal (Code Rule 285) | AAR 1956 | AAR56 |
| advance approach (aspect) | prepare to stop at second signal (Code Rule 282A) | AAR 1956 | AAR56 |
| entering signal | signal governing entry to a station or CTC territory | SP 1942 | RS1942 |
| leaving / departure signal | see station-leaving | SP 1942 | RS1942 |
| interlocking limits | tracks between outer opposing home signals | PRR 1956 | PRR56 |
| controlled point | location of signals controlled from the control machine | CFR | CFR236 (already in glossary) |
| CTC | movement by signals controlled from a point, no train orders, no superiority | ICC 1933 | RS1933 |

## 4. Sources

Keys already in the glossary and reused here: AAR56, AARLIST, CFR236 (extended), PRR56, RS1944, RS1960. Keys new in this note are listed below. "jonroma" = jonroma.net Railway Signaling archive (`/media/signaling/railway-signaling/<year>/<title>.pdf`).

| Key | Citation | URL | Used for |
|---|---|---|---|
| AAR56 | AAR Signal Section, *American Railway Signaling Principles and Practices*, Ch. II, rev. June 1956 | FieldUnit `docs/reference/Chapter-02-...1956.pdf` | aspects 281-292, number plates, approach, semaphore arms, fishtail distant (pp. 41, 52-55, 58) |
| AARTC71 | AAR Communication & Signal Section, *Typical Circuits Representing Current Practice for Railway Signaling*, index 1967, compiled 1971 | jonroma.net/media/signaling/standards/na/aar/ (title as above) | HD/H/D relays, polarized line, coded track, both-direction circuits, traffic locking (Dwg 8000-8079) |
| RSC1967 | *Railway Signaling and Communications*, April 1967, "Block signal systems" (summary of AAR Ch. XV) | jonroma 1967/Block signal systems.pdf | APB relay walk-through: HDR, HPR, SR |
| RSE1920 | *Railway Signal Engineer*, 1920 (month OCR "-ember"), "What Scheme of Signaling is Most Desirable?" (Fugina, L&N; McKeen, UP; Worthing, SP) | jonroma 1920/What Scheme of Signaling is Most Desirable?.pdf | APB origin, positive leaving signals, direction rule |
| RSE1921 | Dunham, C. A., "Absolute Permissive Block Signal System", *Railway Signal Engineer* v14 n11, Nov 1921, pp. 439-440 | jonroma 1921/Absolute Permissive Block Signal System.pdf | APB principles, stick relay, overlaps, distants |
| RS1912 | "New Single Track Signals on the Lake Shore", 1912 | jonroma 1912/New Single Track Signals on the Lake Shore.pdf | absolute vs permissive blades, 1912 |
| RS1923 | *Railway Signaling* v16 n10, Oct 1923, pp. 426-427, "Permissive Block Signal Circuits" (Bremiller) and "Approach Lighting Circuits" (Trout) | jonroma 1923/Permissive Block Signal Circuits.pdf | tumble-down, STK relay, approach lighting |
| RS1925 | Schwendt, B. J., "Traffic Reversal on Double Track by Signal Indication", *Railway Signaling* v18 n6, 1925 | jonroma 1925/Traffic Reversal on Double Track by Signal Indication.pdf | D-251, D-261, traffic lever |
| RS1927b | "Another APB Circuit Explanation", *Railway Signaling*, Aug 1927, p. 311 | jonroma 1927/Another APB Circuit Explanation.pdf | cascading home relays |
| RS1927MP | "Missouri Pacific Operates Trains in Either Direction on Both Tracks", *Railway Signaling* v20 n2, Feb 1927 | jonroma 1927/(title).pdf | each track signalled as single track |
| RS1929 | "Pennsylvania Installs APB Signaling on 86 Miles", *Railway Signaling*, 1929 | jonroma 1929/(title).pdf | absolute = no number plate (search snippet only) |
| RS1932 | "The Erie Installs Either-Direction Signaling", *Railway Signaling* v25 n3, March 1932 | jonroma 1932/(title).pdf | traffic direction locking procedure |
| RS1933 | Editorial, "Centralized Traffic Control and Remote Control", *Railway Signaling*, 1933, p. 306 | jonroma 1933/(title).pdf | ICC definition of CTC |
| RS1939Q | "Operation by Signal Indication on Single Track" (Q&A), *Railway Signaling*, Jan 1939, p. 44 | jonroma 1939/(title).pdf | check locking |
| RS1939SJ | "Trains Directed by Signal Indication at San Jose, California", *Railway Signaling*, Sept 1939, pp. 490-492 | jonroma 1939/(title).pdf | SP Coast line traffic-direction locking |
| RS1940 | Editorial "Single-Track Signaling", *Railway Signaling*, Feb 1940, pp. 103-104 | jonroma 1940/Single-Track Signaling.pdf | head-block signals under remote control |
| RS1941 | "Non-Stop Permissive Signals", *Railway Signaling*, May 1941 | jonroma 1941/Non-Stop Permissive Signals.pdf | Code 290/291/292, head-block, IC rule |
| RS1942 | "C.T.C. Saves Train Time on a Section of the Southern Pacific", *Railway Signaling*, Oct 1942, pp. 538-545 | jonroma 1942/(title).pdf | SP CTC over ABS: line circuits, aspects, distant, code |
| RS1945 | "Southern Pacific Installs CTC on 72 Miles of Single Track", *Railway Signaling*, Feb 1945, pp. 94-99 | jonroma 1945/(title).pdf | SP Colton-Indio; overlap ABS replaced |
| RS1947 | "Southern Pacific Installs C.T.C.", *Railway Signaling*, Feb 1947 | jonroma 1947/Southern Pacific Installs CTC.pdf | double locations, line circuits, Item 412 |
| RS1949 | Claus, W. H., "Controlled Overlaps for Single-Track APB Signaling", *Railway Signaling*, 1949 | jonroma 1949/(title).pdf | overlaps, head-block |
| RS1950 | "CTC on Sunset Route", *Railway Signaling*, 1950 | jonroma 1950/CTC on Sunset Route.pdf | SP line circuits, no coded track |
| RS1954 | "General Railway Signal Company Enters Fiftieth Year", *Railway Signaling*, 1954 | jonroma 1954/(title).pdf | APB first installed 1911 TH&B |
| SP1960 | Southern Pacific (Pacific Lines), *Rules and Regulations of the Transportation Department*, eff. July 1, 1960 (excerpts) | jonroma.net/media/rail/opdocs/na/sp/ (title) | D-251, plates, SP aspect rules |
| UCOR50 | *Uniform Code of Operating Rules*, eff. May 1, 1950 (MoPac, RI, MKT, SSW and others; excerpts) | jonroma.net/media/rail/opdocs/na/uniformcode/ | approach signal note, Rules 281-292A |
| UCOR62 | *Uniform Code of Operating Rules*, Canada, rev. 1962 (signal portions, transcription by R. Milhaupt) | railroadsignals.us/rulebooks/UCOR62/UCOR1962SignalRules.pdf | definitions, 251-263, 505-509 (Canadian) |
| LATIMER1909 | Latimer, J. B., *Railway Signaling in Theory and Practice*, Mackenzie-Klink, 1909 | distantreader.org uc2 ark 13960/t78s4m60s | home vs distant, same-mast distants, locking |
| SCOTT1908 | Scott, R., *Automatic Block Signals and Signal Circuits*, McGraw, 1908 | distantreader.org uc2 ark 13960/t1qf8kj9n | home and distant on same mast circuits |
| CFR236 | 49 CFR 236 Subpart G definitions (current text) | ecfr.gov | modern definitions (block, home, approach, traffic locking, current of traffic) |
| LUNDSTEN | Lundsten, C., "North American Signaling: ABS/APB" | lundsten.dk/us_signaling/abs_apb/ | modern pointer, "tumble-down" |
| RAILPIX | RailPictures.net forum, photo 740533 | forums.railpictures.net/photo/740533 | SLO-Santa Margarita first SP CTC (unverified) |
| OWNER | The owner's answers to the open questions, 2026-10-30, `docs/review/Answers-abs-apb.txt` | this repository | section 5; accepted as good enough for this research |

Sources counted: 31 keys in the table above (including reused AAR56 and CFR236), plus PRR56, AARLIST, RS1944 reused from the glossary.

## 5. Owner's answers (2026-10-30)

The owner answered the open questions in `Answers-abs-apb.txt` beside this note and ruled them good enough for the
purpose of this research [OWNER]. They are not all from period documents. Where one conflicts with a source above,
the conflict is noted; the owner's answer governs the ADR.

1. APB inventor: Sedgwick N. Wight, GRS, about 1911; patent filed 1913.
2. AAR Ch. XV terms: head block (the absolute signal at a siding end entering the block; a train passing it puts the opposing head block to stop), intermediate (the signals between, for following moves), tumble-down (opposing intermediates and head block fall to stop back to the next siding).
3. SP stop-and-proceed on automatic signals: Rule 509 until GCOR (October 25, 1985), then 291. Conflicts with the SP 1960 aspect numbering read above (Rule 290 Stop) [SP1960].
4. SP CTC rules: the 760 series (760 to 778); Rule 760 is SP's functional equivalent of a 261-type rule; ABS under 505. SP had a literal 261 only under GCOR from 1985.
5. SP number plate "reversed, showing yellow": a train may pass the signal at stop without stopping, with caution, as a grade signal or special instruction.
6. The unnamed 1942 article: possibly San Luis Obispo to Santa Margarita; not needed for this work.
7. APB on the Coast Division: SLO to Santa Margarita was the first CTC (1942); APB stayed between CTC islands, North Salinas to South Santa Margarita and South San Luis Obispo to Ellwood, and a short piece Oxnard to Montalvo. The conversions are after SPCoast's era.
8. SP double track near San Jose: College Park to Santa Clara either-direction under tower interlocking rules; San Jose to Lick an extended interlocking worked by the San Jose operator, by signal indication either way (CTC in the 1980s); the Peninsula north of Santa Clara D-251 current of traffic.
9. APB per track on double track: never on SP. Each track was single-track ABS with traffic locking between controlled interlockings or towers; the traffic lock holds the opposing signals at stop, so no tumble-down is needed.
10. What the SP CTC dispatcher saw: each OS circuit individually, and each station-to-station block as one combined occupancy indication, not its intermediate track circuits; code line capacity was the reason. Later electronic CTC showed intermediate blocks.
11. SP distant signals with a D plate: only on the approach from unsignalled territory to CTC or interlocking limits. Within signalled territory the preceding automatic signal (standard number plate) is the approach signal. Conflicts with the separate distant signal 7 of [RS1942].
12. RGPR: the relay repeating a signal mechanism at stop (red repeater).
13. Lick's triangular plate: a signal worked by a protective device; at the end of double track, probably a spring switch.
14. The 1925 D-251/D-261 wording: the same in the Code editions SP used.
15. Direction on SP CTC, one or two tracks: set by the signal levers (with the switch levers) and the code button; no separate traffic lever. The field logic checks the block vacant and sets the directional locking.
16. The relay reporting a whole station-to-station block clear: BPR, block repeater relay; with TR/TPR (track) and FR/FSR (traffic, traffic stick).

Consequences for the facts above:
- F2 holds and sharpens: a CP knows its own OS circuits; the block between two stations reaches the office as one indication (a block repeater), not as its track circuits.
- F5 and G: inside signalled territory, the automatic signal in the rear of a CP home is that home's approach signal; a separate D-plate distant marks the approach from unsignalled territory.
- C: on SP CTC the signal levers set direction; traffic levers belong to the tower-era either-direction installations.

## 6. Discrepancies resolved (owner, 2026-10-30)

SP was frugal and its practice was not uniform: a rule says what it names, never that every location followed it
[OWNER]. Read "only" and "always" above in that light.

1. Distant signals (answer 11 against [RS1942]). No conflict. [RS1942] calls signal 7 "distant" for its job; by
   the SP rulebook a Distant Signal (D plate) is one outside a block system, so signal 7 is an automatic signal with
   a number plate doing the approach job. For the model: the approach signal of a home is derived (the signal in the
   rear of the home along the track, in the direction of travel), never drawn; a D-plate distant is drawn only where
   unsignalled track enters CTC or interlocking limits; extra heads that repeat route information are an aspect
   matter of the signal's heads, not a kind of signal.
2. Rule numbers (answers 3 and 4 against [SP1960]). No conflict: SP's aspect rules (281 to 298) define aspects,
   Rule 509 the crew's action at an automatic signal at stop, the 760 series CTC; the numbering is SP's own. For the
   model: rule numbers belong to a rulebook and era and stay out of the drawing and the data model; the policy Kinds
   keep the Standard Code numbers (`RULE_251`, `RULE_261`, `RULE_105`, `RULE_93`); a road's own numbers come from a
   rulebook reference table, built when something needs it.
3. Relay names (answers 12 and 16). No conflict: BPR, RGPR, FR/FSR and TR/TPR are SP/US&S plan names consistent
   with AAR letter naming. For the model: relay names never appear; the model states that a station-to-station
   block is occupied and that it reaches the office as one indication. The names go to the glossary relay table,
   marked as SP/US&S usage per the owner. The block indication's token name is for the ADR.
4. Reversed number plate (answer 5). No conflict; the answer supplies the meaning [SP1960] lacked. It is an
   operating condition set by a Form Z train order, kept out of the model; the drawn facts it rests on (an
   automatic signal with a number plate) are already there.
5. History (answers 1 and 7). Taken as answered: APB's inventor is Sedgwick N. Wight (GRS); the Coast Division APB
   conversions fall after SPCoast's era. Neither affects the model.
