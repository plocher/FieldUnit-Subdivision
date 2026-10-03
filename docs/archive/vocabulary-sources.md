# Vocabulary review: sources table

Status: draft for the glossary rewrite (spike S6). Date: 2026-10-01.

This file checks 15 "recall" claims from `vocabulary-review.md` against sources that were opened.

## Rules for this table

- "Opened" means the page or file was fetched and its text was read in this session.
- A search-result snippet is a **lead, not read**. Leads are named as leads. They never support a verdict.
- Where a quote is marked "(fetch tool)", a web fetch tool returned the sentence. The page was not read raw. Check it before you copy it into the glossary.
- Where a quote is marked "(text)", the text was extracted from the PDF or HTML file with `pdftotext` or `sed`.
- Verdicts: **Confirmed**, **Contradicted**, **Partly**, **Not found**. "Not found" means no opened source says it. It does not mean the claim is false.
- Failed fetches: jmri.org (403), ctcparts.com (TLS), forum.trains.com and cs.trains.com (403 or DNS), trains.com PDF (403), arema.org MP PDFs (404), `Union_Bull_148_CTC_gen.pdf` (opened, no usable text), NORAC 9th edition (opened only as a saved PDF, read with `pdftotext`), Cornell 49 CFR 236.0 and 236.703 (opened, no definition of the terms asked), research.nprha.org (404), cs.trains.com/t/30761 (DNS failure).

## Table

| # | Claim | Verdict | Source URL(s) opened | Supporting quote | Note |
|---|---|---|---|---|---|
| 1 | "Control Point" (GCOR) and "Controlled Point" (49 CFR 236, NORAC) name the same thing | Partly | https://fobnr.org/wp-content/uploads/2021/06/GCOR-040710.pdf ; https://www.law.cornell.edu/cfr/text/49/236.782 ; https://rail.pgengler.net/NORAC_9th_Edition.pdf ; https://tc.canada.ca/en/rail-transportation/rules/2022-2023/canadian-rail-operating-rules/definitions ; https://utahrails.net/up/control-points.php | GCOR 6th ed. (text): "Control Point: The location of absolute signals controlled by a control operator." 49 CFR 236.782 (fetch tool): "A location where signals and/or other functions of a traffic control system are controlled from the control machine." NORAC 9th (text): "CONTROLLED POINT (CP): A station designated in the Timetable where signals are remotely controlled from the control station." | The names match the review. The definitions are close but not equal. See note 1. |
| 2 | "cTc" was the GRS styling; US&S sold "Union" CTC; "TCS" is regulatory | Partly | https://en.wikipedia.org/wiki/General_Railway_Signal ; https://www.jonroma.net/media/signaling/railway-signaling/1937/Ends%20of%20Double%20Track%20Controlled%20by%20CTC.pdf ; https://utahrails.net/pdf/Farrington_1949_Union-Switch-Signal.pdf ; https://jonroma.net/media/signaling/railway-signaling/1959/Pushbutton%20console%20for%20CTC.pdf | Wikipedia GRS (fetch tool): "First Centralized traffic control (cTc) machine, 1927." Railway Signaling, Oct 1937 (text): "The Union time-code C.T.C. system is designed to control switch and signal functions of any type of track layout". US&S history, 1949 (text): "Centralized traffic control is a system of train dispatching whereby the dispatcher seated at his C.T.C. control machine". | No trademark record was found. US&S wrote "C.T.C." in 1937 and 1949. See note 2. |
| 3 | US&S 500-series time code systems: 502, 504, 506, 508, 510, 514, 516; a "Model 503" | Partly | https://rrsignal.com/railroad/ctc/uss514.htm (and the already-checked uss506.htm) | rrsignal 514 page (fetch tool): the 514 "was capable of 35 field locations with a minimum of 7 controls and 7 indications at each station". It is "very similar to 506". | 506 and 514 are Confirmed. 502, 504, 508, 510, 516 are Not found in any opened source. "503" is Not found anywhere. See note 3. |
| 4 | First CTC: 1927, NYC, Stanley to Berwick, Ohio, GRS; one-wire control, not a coded two-wire line | Partly | https://ekeving.se/ctc/us/NYC_1927.html ; https://en.wikipedia.org/wiki/Centralized_traffic_control ; https://www.ekeving.se/ctc/ctc193x/Wh/Wh_J173.html | ekeving (fetch tool): "one wire was required between the dispatchers office and each switch (plus a common return wire)". Wikipedia (fetch tool): "first installation in 1927 was on a 40-mile stretch of the New York Central Railroad between Stanley, Toledo and Berwick, Ohio". | Year, road, endpoints, builder and wiring are Confirmed. "Toledo & Ohio Central" is Not found. US&S time code date is Not found. See note 4. |
| 5 | AAR letters: W switch, G signal, S stick, K indication, H home, D distant, T track, R relay, P repeater, N/R normal/reverse, L lock, TE time element | Partly | https://railroadsignals.us/basics/nomenclature.htm | (fetch tool) W: "Switch (operating mechanism), west, westward, white". G: "Green, signal (operating mechanism), ground". S: "South, stick, storage, southward". K: "Indicator". H: "Home, Approach indication of a signal". D: "Proceed indication of a signal, detector, decoding". TSR: "Track stick relay". | D is **not** "distant" on this list. TE is absent. Every other letter is listed with extra meanings. The page reproduces AAR abbreviations. It is not AREMA text. See note 5. |
| 6 | "OS" means "on sheet" (the dispatcher's train sheet) | Confirmed | https://www.bnsf.com/news-media/railtalk/heritage/abcs.html | (fetch tool) "The term OS stands for 'on-sheet;' it is a term used by train dispatchers to document reports of trains passing a specific location. OS is also used to describe the segment of track between opposing signals in a control point within Centralized Traffic Control." | The BNSF page is a modern railroad source. It also gives the OS-section meaning. No period source was opened. |
| 7 | A derail's NORMAL position is the derailing position | Partly | https://www.law.cornell.edu/cfr/text/49/218.109 ; https://fobnr.org/wp-content/uploads/2021/06/GCOR-040710.pdf | 49 CFR 218.109(b)(1) (fetch tool): "The normal position of fixed derails is in the derailing position except as provided in part 218, subpart B of this chapter, or the railroad's operating rules or special instructions." GCOR 8.20 (text): "Sidings having hand-thrown derails will have derail locked in non-derailing position, except when engines or cars are left unattended on siding." | Support exists for fixed (hand) derails. No source was found for power-operated, interlocked derails. GCOR 8.20 sets the opposite rest state for sidings. See note 7. |
| 8 | Standard Code rules 251, 261, 262, D-151, D-152; GCOR does not use these numbers | Partly | https://www.redoveryellow.com/position-light/PRR_Diagrams/PRR-1956-Rulebook/rulebook1956.html ; https://fobnr.org/wp-content/uploads/2021/06/GCOR-040710.pdf ; https://jonroma.net/media/signaling/railway-signaling/1960/Fourteen%20RRs%20adopt%20new%20operating%20code.pdf | PRR 1956 (text): "261. On portions of the railroad and on designated tracks so specified on the time-table, trains will be governed by block signals whose indications will supersede the superiority of trains for both opposing and following movements on the same track." "D-151. Where two main tracks are in service, trains must keep to the right unless otherwise provided on the time-table." | Texts are Confirmed, from one road (PRR, 1956/64). GCOR 6th ed. uses 1.1, 8.20 style numbers. The GCOR 1985 first edition was not opened. See note 8. |
| 9 | ERS is a named circuit; AREMA terms "track stick relay", "directional stick relay" | Partly | https://railroadsignals.us/basics/nomenclature.htm ; https://jonroma.net/media/signaling/railway-signaling/1927/Various%20Circuits%20for%20Directional%20Control%20of%20Single%20Track%20Signals.pdf ; https://jonroma.net/media/signaling/railway-signaling/1944/Coded%20Track%20Circuits%20for%20CTC%20and%20Cab%20Signaling.pdf | Nomenclature page (fetch tool): "TSR" is "Track stick relay". 1927 article (text): "the directional stick relay 35R". 1944 article (text): "R52S (eastward directional stick) relay". | "Engine return stick" was found only in search snippets (lead, not read). The AREMA manual PDFs returned 404. See note 9. |
| 10 | Maintainer call lamp on CTC: who it summoned | Partly | https://jonroma.net/media/signaling/railway-signaling/1959/Pushbutton%20console%20for%20CTC.pdf ; https://rail.pgengler.net/NORAC_9th_Edition.pdf | Railway Signaling, July 1959 (text): the auxiliary panel controls items such as "fleeting, maintainer's call, snow melters, carrier transfer"; "A power-off indication lamp and maintainers' call lamp are also located at these location points". | The name says the lamp calls a maintainer. No opened source says whether train crews also used it. See note 10. |
| 11 | "Island" is a highway grade-crossing term | Confirmed | https://patents.google.com/patent/US4868538 | Patent (fetch tool): "an island formed by one or more railroad tracks crossing a street or roadway at grade level". | The sense at crossings is Confirmed. "Only at crossings" is not proven. No source was found that uses "island" for a switch section. |
| 12 | Industry uses "application" for generic logic configured with one site's data | Partly | https://extranet.artc.com.au/docs/eng/signal/procedures/design/SCP23.pdf | ARTC SCP 23 (text): "reference should be made to the US&S Microlok II System Application Logic Programming Guide." "Microlok application data must not use Look-up tables without a specific design guideline". | The Microlok usage is Confirmed. The words "generic" and "specific application" from CENELEC EN 50129 were found only in search snippets (lead, not read). See note 12. |
| 13 | B&O color-position-light marker meanings | Partly | https://jonroma.net/media/signaling/railway-signaling/1925/B%26O%20Color-Position-Light%20Signals.pdf ; https://railroadsignals.us/signals/cpl/index.htm ; https://www.american-rails.com/cpl.html | 1925 proposal (text): "White upper and lower route markers for high speed and restricted speed routes respectively, indicate clearly which route is set". american-rails (fetch tool): markers below the head mean "medium-speed moves through the interlocking or crossover". | No opened source uses clock positions. None gives "limited" at 4 o'clock. See note 13. |
| 14 | Chubb's book title is *Railroader's C/MRI Applications Handbook* | Contradicted (in part) | https://www.jlcenterprises.net/pages/support | (text) "Railroader's C/MRI Application Handbook – Volume 1 Enhancements – Version 3.0" and "... Volume 2 Signaling – Version 3.0". | The title is singular "Application", not "Applications". Two volumes exist. The page is the publisher's own. |
| 15 | "Central instrument location (CIL)" is a real signalling term | Not found | https://cse.iitkgp.ac.in/~chitta/CRR/sigDocs/S1-basics.pdf (opened, searched for the term) | None. | Four searches returned no page that uses the term. It may exist in Indian or other practice. The glossary should not use it without a source. |

## Notes on nuanced claims

### Note 1. Control Point and Controlled Point

- GCOR defines "Control Point" as a location of absolute signals. It names a control operator.
- 49 CFR 236.782 defines "Controlled point" as a location where "signals and/or other functions" are controlled from the control machine. This covers more than signals.
- NORAC 9th edition (2008) defines it as "A station designated in the Timetable". It is a timetable station here.
- The Canadian rules (CROR, Transport Canada page) define only "controlled point". The text is "A signal location in CTC consisting of controlled signal(s) in one direction only." That is narrower than the other three.
- A Union Pacific 1979 bulletin, quoted on utahrails.net (fetch tool), uses "Controlled Point (CP)". The page's own text says "A location where signals and/or switches of a CTC System are controlled by train dispatcher or control operator."
- Summary: the two names do mean "a place with dispatcher-controlled signals". The sources do not show a structural distinction. NORAC adds "station designated in the Timetable". The review's regional reading (GCOR "Control Point", CFR and NORAC "Controlled Point") is supported by these texts.
- Review claim F3 says GCOR and the CFR name "the same thing". The texts differ in detail. The glossary can still treat them as synonyms. It should cite the GCOR definition for "Control Point".

### Note 2. cTc, US&S and TCS

- What is supported: Wikipedia writes "(cTc)" for GRS machines. A hobby site (rrsignal) writes "cTc" for US&S 514 machines.
- What is not found: any trademark record or GRS document that says "cTc" is a GRS styling.
- US&S wrote "C.T.C." in a 1937 article ("The Union time-code C.T.C. system") and in a 1949 company history ("his C.T.C. control machine").
- The 1959 Railway Signaling article names a US&S machine "TCC (traffic control center)". It does not say "TCS".
- "Union Centralized Traffic Control" as a product name: lead only. `Union_Bull_148_CTC_gen.pdf` was opened. It is a scanned image, and no text could be read.
- "TCS" as an ICC/FRA term is already checked (jbritton). 49 CFR 236 uses "traffic control system" (see the 236.782 definition above, which says "a traffic control system").
- Net effect: "US&S cTc" is not supported as a US&S term. "Union time-code C.T.C." is supported for 1937.

### Note 3. 500-series members and "Model 503"

- Confirmed: 506 and 514 are US&S time-code systems (rrsignal).
- Not found in any opened source: 502, 504, 508, 510, 516, and any "503".
- A 1937 article describes an earlier Union time code with "A control code consists of 14 impulses". It does not use a model number. So code length changed between systems. This does not contradict the 16-step 506 result. It shows that "15 or 14 steps" may come from an older Union code.
- The searches for "Model 503", "Style 503" and "Type 503" returned no page that contains the term.

### Note 4. First CTC installation

- Confirmed by ekeving (page title "1927: Dispatcher Control on the New York Central"): builder General Railway Signal, one wire to each switch plus a common return.
- Wikipedia (fetch tool) says: "initially, the communication was accomplished by dedicated wires or wire pairs". It adds: "later this was supplanted by pulse code systems".
- A 1954 GRS history in Railway Signaling and Communications has a scanned caption on the 1927 NYC installation. The OCR text is garbled, so it is not quoted.
- Not found: "Toledo & Ohio Central". Every source opened says "New York Central", Ohio Division.
- The F30 correction stands. The first installation was not a two-wire time code.
- US&S time code date: not found. The earliest opened dated source is the Railway Signaling issue of October 1937, which describes an installed "Union time-code C.T.C. system" with a "single series circuit of two wires".
- A 1949 US&S history (utahrails.net) says coded track circuits were first placed in service in "March, 1933". It also says coded carrier lets sections "be operated simultaneously over a two-wire line". These are not the same as the code line.
- A Westinghouse document of 1931 (ekeving, fetch tool) says: "The first coded installation of C.T.C. was placed in service on the Pere Marquette R.R. in U.S.A. in 1928." The page does not name the maker. Treat as a lead for the first coded installation.

### Note 5. Nomenclature letters

- Source: the "General AAR Abbreviations" list at railroadsignals.us. It is a railfan reproduction of the AAR list, not the AREMA manual.
- The list gives many meanings per letter. A relay name uses one of them.
- D reads "Proceed indication of a signal, detector, decoding". The review's "D = distant" is not on the list. "Distant" appears for a distant signal elsewhere in rulebooks (NORAC: "DISTANT SIGNAL"), not as the letter D.
- R reads "Right, red, reverse, relay, power operated controller or contactor, route, stop indication of a signal". N reads "Normal, north, northward, negative".
- P includes "repeating". L includes "lock". T includes "track" and "time".
- TE is not in the list. A "time element" source was not found.
- The glossary should cite this list as "AAR abbreviations, as reproduced". It should not say "AREMA" unless the AREMA manual is opened.

### Note 7. Derail normal position

- 49 CFR 218.109(b)(1) is about hand-operated fixed derails. Its purpose is worker protection and not signal control.
- GCOR 8.20 says hand-thrown derails on sidings are locked in the non-derailing position. On auxiliary tracks they are "always in derailing position".
- So the rule is by use. It is not a universal statement of NORMAL for interlocked derails.
- The F11 change follows the SPCoast prototype. No source opened says what the signal-circuit NORMAL of a power derail was on the SP Coast Line. The glossary should label it "Prototype convention", not "AAR".

### Note 8. Rules and GCOR numbering

- PRR 1956/64 text (effective October 28, 1956):
  - 251: "On portions of the railroad and on designated tracks so specified on the time-table, trains will run with reference to other trains in the same direction by block signals whose indications will supersede the superiority of trains."
  - 262: "A train for which the direction of traffic has been established must not move in the opposite direction without proper interlocking or manual block signal indication or train order."
  - D-152 (the heading in the file reads "152."): "When a train or engine crosses over to or obstructs a track where block signal system rules are in effect, the movement must be protected by the operator as provided by Rules 327 or 504, except where 605 is in effect. (Rev. 10-18-64)"
- This is one railroad's book. Another road's wording can differ. The SP and the SPCoast timetable text were not opened. The SP 1960 excerpt that was opened shows "D-251" and "D-254" in the SP numbering.
- A 1960 trade article (Railway Signaling and Communications) says fourteen western roads adopted a consolidated code with CTC rules "265-273". A 1962 Canadian code excerpt has "263" and "264" for CTC. So CTC rule numbers vary by code and year.
- NORAC 9th edition (2008) still says "Rule 251 main track". So the numbers did not stop with GCOR. They continue in NORAC.
- GCOR 6th edition (2010) uses chapter numbers such as 1.1 and 8.20. This supports "GCOR does not use 251 and 261". The 1985 first edition was not opened. A search snippet says "GCOR roads have used the General Code of Operating Rules since 1985" (lead, not read).
- Verdict on the review text: the claim that 251/261/D-151/D-152 are Standard Code numbers is supported for Standard Code descendants (PRR). The claim that GCOR does not use them is supported for the 2010 edition only.

### Note 9. ERS, track stick, directional stick

- "Track stick relay" (TSR) is on the AAR list.
- "Directional stick" appears in 1927 and 1944 Railway Signaling articles ("directional stick relay 35R", "R52S (eastward directional stick) relay").
- "Engine return stick": only a search snippet attributes it to AREMA Manual Part 16 ("Engine Return Stick Circuits at Interlockings and Controlled Points"). The PDFs gave 404. Lead, not read.
- The `ERS` letters are not on the AAR list. The review's reading, "a FieldUnit name for a function", stays valid.

### Note 10. Maintainer call

- Railway Signaling, July 1959, describes a pushbutton CTC machine. Its auxiliary panel has a "maintainer's call" control. A "maintainers' call lamp" sits at each location.
- This shows the control and the lamp existed. It does not say who answered. The label points to a signal maintainer.
- NORAC Rule 18 and the PRR 1956 book (text) have a horn signal "o o o o" with the meaning "Signal maintainer must call the Dispatcher or Operator" (NORAC) and "Call signal maintainer" (PRR). This is a train-to-interlocking signal. It is not the CTC lamp.
- GCOR (text) says the dispatcher must "call the signal maintainer" in a failure.
- No opened source supports a "call to train crews". The review's F22 doubt stands. A claim that the lamp called train crews is Not found.

### Note 12. "Application"

- ARTC SCP 23 shows the vendor's own manual title: "Microlok II System Application Logic Programming Guide". It also uses "application data" and "application logic" for the per-site part.
- The document does not say "generic".
- The EN 50129 and CLC/TR 50506-1 pages (iteh, ANSI preview) were opened and gave no definition text. The search snippet "applies to generic systems ... as well as to systems for specific applications" is a lead, not read.
- For the glossary, the Microlok usage can be cited. The CENELEC wording needs the standard itself.

### Note 13. B&O CPL markers

- A 1925 proposal (Railway Signaling, July 1925) says: "White marker light above two red lights in horizontal line, stop, then proceed; main route." It also says "White marker light below two red lights in horizontal line, stop, then proceed; restricted route." This is an early proposal. Later practice changed.
- Later practice, as returned by the fetch tool for railroadsignals.us: markers above are high speed. Markers below are medium speed. White on the left means expect medium at the next signal. Yellow on the right means expect slow. No marker means slow speed.
- Rule numbers seen: 283 (Medium Clear), 283A (Medium Approach Medium), 287A (Slow Clear), 288 (Slow Approach), 292 (Stop). These are fetch-tool extractions. The SP Coast rules differ.
- The FieldUnit how-to 04 lists "2 o'clock Medium, 4 o'clock Limited, 6 o'clock Slow, 10 o'clock Cab Speed". No opened source matches this layout. This supports F20.

## Verdict list

1. Control Point = Controlled Point: Partly.
2. cTc / Union CTC / TCS: Partly.
3. 500-series list and "Model 503": Partly (506 and 514 only); 503 Not found.
4. First CTC 1927: Partly (all but "Toledo & Ohio Central" and the US&S date).
5. AAR letters: Partly (D is not "distant"; TE absent).
6. OS = on sheet: Confirmed.
7. Derail normal = derailing: Partly.
8. Rules 251/261/262/D-151/D-152: Partly (texts Confirmed for PRR; GCOR 2010 only).
9. ERS and AREMA stick names: Partly.
10. Maintainer call: Partly.
11. Island: Confirmed (crossing sense).
12. Application: Partly.
13. B&O CPL markers: Partly.
14. Chubb title: Contradicted in part ("Application", not "Applications").
15. CIL: Not found.
