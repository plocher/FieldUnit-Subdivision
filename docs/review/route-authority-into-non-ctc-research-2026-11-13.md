# Route authority from CTC into non-CTC track (research, 2026-11-13)

Question: does a CTC signal indication that lines a route into track under another method
of operation (for example Yard Limits, or an industry or staging track) also authorize the
movement past the END CTC / BEGIN Yard Limits point, with no stop for further authority? And
what speed and indication then govern?

## Verdict: partly supported

- **Supported:** the crew does not stop at the change point to get more authority. But the
  rulebook does not say that the signal authorizes the movement beyond that point. The signal
  governs only to the end of the block system (GCOR 9.3, 9.11, 9.12.1, Block definition).
  Beyond it, the other territory's own rule is the authority. GCOR 6.13 authorizes trains to use
  main track in yard limits. GCOR 6.28 governs track that is not main track and has no block
  system. These rules need no new authority from the control operator. One exception:
  yard limits that overlap CTC (GCOR 6.13, "In CTC Territory").
- **Not supported as worded:** "the signal's authority continues past the sign." The nearest
  rule is GCOR 9.23.1 (signals suspended past a control point): a signal there authorizes
  movement only through the control point, not beyond it. That rule covers a special
  case, but it is the only text that addresses the point, and it goes against the claim.
- **Speed:** restricted speed in yard limits, except under a block signal more favourable
  than Approach (GCOR 6.13). On track that is not main track and has no block system, the
  speed must let the train stop in half the range of vision (GCOR 6.28). A signal
  requiring restricted speed binds only to the end of the block system (GCOR 9.11).
- **Indication ceiling: not settled by the sources opened.** The aspects and their names are
  in each railroad's special instructions (GCOR 9.1), and those were not opened. No GCOR text that
  I read requires a Restricting (or Diverging Restricting) aspect for a route into yard
  limits or non-signaled track. Rule 6.13 does assume a block signal may "require
  restricted speed due to yard limits". That is evidence for the practice, but it does not require it.

Source caveat: the local PDF is the **UPRR web edition of GCOR, Seventh Edition, effective
2025-09-23, updates to 2026-10-27** (title page). It is not the 8th edition named in the brief.
Rule numbers below are as printed there.

## Evidence

Each quote is under 15 words.

### Signal authority: how far it goes

- GCOR 9.3 (What Signals Govern): "Interlocking signals govern the use of interlocking routes."
- GCOR 9.3 (What Signals Govern): "Where a track is signaled beyond the interlocking limits … the interlocking signal is also a block signal."
  The converse is not stated. Where the track is not signaled beyond, the signal is only an interlocking signal.
- GCOR 9.3 (What Signals Govern): "All other rules, where required, remain in effect".
- GCOR Glossary, Block: "Between a block signal and the end of block system limits".
- GCOR Glossary, Block Signal: "governs trains entering and using that block."
- GCOR Glossary, Interlocking Limits: "The tracks between outer opposing absolute signals of an interlocking."
- GCOR Glossary, Centralized Traffic Control: "A block system that uses block signal indications to authorize train movements."
- GCOR 9.11 (Movement from Signal Requiring Restricted Speed): "until its leading wheels have passed the next governing signal or the end of the block system."
- GCOR 9.10 (Initiating Movement Between Signals): same limit, "the next governing signal or the end of the block system."
- GCOR 9.12.1 (CTC Territory), the operator's check before he authorizes a train past Stop: "to … the next absolute signal governing movement or the end of CTC".
  The rules expect a route whose protected extent ends at the end of CTC, not at a further signal.
- GCOR 9.23.1 (Guidelines While Block System Is Suspended): "signal indication will only authorize movement through the control point, not beyond it."
  This is the only text found that says how far a CP signal's authority goes when no block system follows.
- 49 CFR 236.806 (Signal, home): "at the entrance to a route or block to govern trains in entering and using" it.
  Source: law.cornell.edu.
- 49 CFR 236.828 (Traffic control system): "train movements are authorized by block signals". Source: law.cornell.edu.

### Leaving the main track through a lined route

- GCOR 9.16 (Stop and Proceed Indication) 2a: may pass at restricted speed to "Leave the main track when the switch is lined".
- GCOR 11.2 (Signal Indications with Absolute Block): "the train may leave the main track through a switch that is immediately after" the signal.
  Both rules treat leaving the main track over a lined switch as part of the movement the signal governs. Neither requires a stop at the switch.

### What governs past the change point

- GCOR 6.13 (Yard Limits): "trains or engines are authorized to use the main track not protecting against other trains".
- GCOR 6.13 (Yard Limits): "must be made at restricted speed unless operating under a block signal indication" (continued: more favourable than Approach).
- GCOR 6.13 (Yard Limits): "a block signal may require restricted speed due to yard limits".
- GCOR 6.13 (Yard Limits), In CTC Territory: "the control operator must authorize any movement on the main track."
  This applies where yard limits overlap CTC. There the CTC authority (the signal) still applies.
- GCOR Glossary, Yard Limits: "A portion of main track designated by yard limit signs".
  Yard limits are main track. Industry, yard and staging tracks are not; see 6.28.
- GCOR Glossary, Yard: "tracks, other than main tracks and sidings, used for making up trains".
- GCOR 6.28 (Movement on Other than Main Track): "Except when moving on a main track or on a track where a block system is in effect"
  The rule then sets the half-range-of-vision speed.
- GCOR Glossary, Other Controlled Track: "A segment of track (not main track or siding) between Control Points"
  The definition continues: governed by Chapter 10. A track that is not main track can be inside CTC if the timetable lists it.

### Entry into CTC (for contrast)

- GCOR 10.1 (Authority to Enter CTC Limits): "A train must not enter or occupy any track where CTC is in effect unless" (a proceed indication or operator authority).
  The rule covers entry only. Chapter 10 has no matching rule for leaving CTC.

## Open points

1. **Where the claim's step comes from.** No rule found says "the indication authorizes
   movement beyond END CTC". The practical outcome is the same: the crew does not stop. But
   the authority beyond the point comes from Rule 6.13 or 6.28, not from the signal. For the
   model, this means the regime boundary hands authority from one source to the next. The
   route does not carry its authority past the boundary.
2. **Indication ceiling for routes into yard limits or non-signaled track.** Not settled. The
   aspect tables are in railroad special instructions (GCOR 9.1). The SP timetable and special
   instructions were not opened (unverified). The AREMA C&S Manual was not opened (unverified).
3. **Yard limits overlaid on CTC** (GCOR 6.13, In CTC Territory) is a different case from yard
   limits that begin at END CTC. The model must know which case applies at each boundary.
4. **Edition.** Check the same rules in a non-UPRR GCOR 8th edition text if one is available.
   I opened only the UPRR web edition.
5. **NORAC and SP practice:** not opened (unverified).
