# Adversarial review: ADR 0009 rev 3 amendments (proposal of 2026-10-25)

Reviewed 2026-10-25 on `feat/trackplan-semantics`. Subject: `docs/review/adr-0009-rev3-amendments-2026-10-25.md`
(the proposal), against ADR 0008 C11 and §8 (2026-10-23 to 2026-10-25), ADR 0009, FieldUnit `docs/GLOSSARY.md`,
the four `~/Dropbox/KiCad/Railroad/symbols/*.kicad_sym` libraries (parsed directly), `tools/layout_compiler/seams.py`
at `18640e8` and in the working tree, and `SPCoast/production/SPCoast.net` (22:09) read with `source.from_netlist`
under `uv run python`. kicad-cli was not run. No file other than this report was edited.

Verified as stated: one `Railroad` symbol (RAILROAD1, sheet `/`, Name SPCoast); 0 `identity.value`, with and without
the geometry reader; 38 Mast rows (of 268 rows), matching 38 `"appliance": "mast"` in the example; six
`transport.reach` infos; 14 JMRI drivers keyed `Kind.name`, the two Turnouts merged from command and feedback;
ModelLamp-AMBER/-BLUE/-GREEN/-RED/-YELLOW are PANEL, Appliance `lamp`, Style `board`, sole pin `~{LAMP}`; IB bits 1
to 14 (InputBytes 2), OB bits 1 to 20 (OutputBytes 3), direction from the `D` pin type (`input` on
Driver-CMRInet-IB, `output` on -OB); Transport-CMRInet and Encoding-CMRInet Kind `CMRI`; Driver-CMRInet-Node, -IB,
-OB IC `CMRI` in the library; RIO1 (sheet `/South-cTc/`) IC `CMRInet`, its 34 bits IC `CMRI`, the example writes
`"ic": "CMRInet"` once (`schemas/layout-model/examples/spcoast.layout.json:3733`). The `18640e8` compiler and the
uncommitted working tree give identical diagnostics on this netlist.

## Findings

1. **Blocker. Claim: "The key of every symbol the compiler names is a functionally named attribute whose content is
   `${Value}`" and "`${Value}` is the library default" (proposal §3.10, first bullet).** The libraries contradict
   it for four of the six keys listed:
   - `House`: `CP Name = ''`, `Value = '${CP Name}'` (the reverse direction);
   - `Driver-CMRInet-Node`: `Address = ''`, `Value = 'UA${Address}'`; `Driver-I2C-MCP23017`, `-MAX7311`, `-MAX7313`,
     `-PCA9685-*`: `Address = ''`, `Value = '${ADDRESS}'`; `Driver-GPIO-*`: `Value = '${Address}'`;
   - `PanelColumn`: `Column = '${VALUE}'` (upper case, KiCad's built-in, not the literal `${Value}`);
   - `Device-Head-CPL-Encoded`, `-Semaphore-LQ`, `-Semaphore-UQ`: `Head = ''`.
   - `Driver-CMRInet-IB`/`-OB` have no key attribute at all (no Name, no Address); the key is `Bit` plus pin type.

   ADR 0008 §4.5 carries the same over-statement; copying it into the drawing contract makes the contract false.
   Fix: "The key of every symbol the compiler names is a functionally named attribute (list). Its content is KiCad's
   business: `${Value}` on most, the reverse (`Value = ${Key}`) on the House and the drivers." Raise the same
   correction for ADR 0008 §4.5.

2. **Should-fix. Claim: the per-symbol key list (§3.10 first bullet; Decision 3).** It is incomplete and too broad:
   - It omits the CMRInet bit (`Bit`, with the array taken from the `D` pin type; seams.py `_drivers`, lines 580-587).
   - It omits the Milepost: Role `TRACK`, not a trackplan appliance, `Name = ${Value}` since Railroad `a3642e4`, and
     read by `geometry.py` line 396 (`mileposts[name_of(s, report)]`).
   - "`Name` on ... a device" is too broad. A head device is keyed by `Head` and its `IND` wire. A panel lamp's key is
     `IndicationToken` (seams.py line 778). The code lever has no key (lines 803-804). The ModelLamp's `Name = ${Value}`
     copies a label: the library's Description says "Value is a free descriptive label (e.g. OS, TRACK ...) and is
     not used elsewhere".

   Fix: add `Bit` on a CMRInet bit and `Name` on a Milepost. Say that a lamp is keyed by what it shows and that its
   `Name` is a label.

3. **Should-fix. Claim: Decision 1's default is that RIO1's IC is "restored to the library's `CMRI`".** C11 reads "§3.2
   says IC `CMRI` where the drawing and the vocabulary say `CMRInet`", which reads most naturally as a defect in §3.2,
   not in the drawing. The Railroad history shows that `CMRInet` was the owner's hand-entered value twice and that
   `CMRI` came from a script:
   - `3cb51fc` (owner edits, 2026-10-22) added `(property "IC" "CMRInet"` to `Railroad-HardwareIO.kicad_sym` and to
     the Caltrain instances.
   - `203bab3` (script, five minutes later) replaced it with `CMRI`.
   - `54f3fa9` (owner edits, 2026-10-23) set RIO1 to `CMRInet` again.

   "Restored" therefore frames the owner's value as drift. The compiler checks no node IC: only the transport and
   encoding Kinds pair (`TRANSPORT_OF_ENCODING`, seams.py line 26), so either answer costs nothing in code. Fix: put
   the alternative beside the default as an equal option (the library node, and perhaps the bits, carry IC
   `CMRInet`, and Kind stays `CMRI`), and quote the history.

4. **Should-fix. Claim: the record entry says "The decision of §4 is unchanged: these record what the drawing and the
   compiler already do".** Under the proposal's own defaults this is false:
   - Decision 1 is a Railroad edit, and it changes a fact in the ratified example (`ic`).
   - Decision 2 is a compiler change, and it strikes a sentence from ADR 0008 §4.5, which is part of ADR 0008's
     ratified §4. That needs its own ADR 0008 §8 entry, not only an ADR 0009 rev.

   Decision 2 also leaves out what "left unnamed" does. `_processors`, `_transports`, `_encodings` and `_office_units`
   (seams.py lines 327, 365, 402, 505) would key an entity by `""`; only `_interlockings` skips. The test
   `tests/test_layout_compiler.py:126-131` (`test_a_symbol_without_name_uses_value_and_says_so`) asserts the fallback
   and would have to be inverted.

   The cited commits are incomplete. They omit `6882aa6` (Name on devices, office unit and encodings; Kind on the JMRI
   drivers), `a953197` and `1dce092` (ModelLamp), and `d52017c` and `21536f1` (the Railroad symbol and the macro).

   Fix: write "unchanged except as Decisions 1 and 2 settle", say what the compiler does with a symbol that has no
   key (skip and report `missing`), list the test, and cite the commits.

5. **Should-fix. Claim: "Every other amendment below is C11 as written, or a correction of a cross-reference."** These
   items are neither:
   - the §3.11 `MQTT-JMRI` line (a vocabulary correction);
   - "the machine's processor" becoming "the OfficeUnit's processor" in the transport row (a vocabulary correction, not
     flagged);
   - "A drawn `Address` overrides the key, reported at info" and "Two symbols with one key ... are one driver" (from
     ADR 0008 §4.5, not C11);
   - "every instance has one anchor" (a new Check);
   - "the trackplan draws that head on that mast" (a new Check);
   - "showing the indications named in its `IndicationToken`";
   - "A symbol the compiler must name and that lacks its attribute gets it in the library and on its instances by a
     dated script".

   Most of these record what the code does and can stay if they are labelled. The last is a new procedure. It also
   competes with §3.10's existing "The compiler's 'missing' report is the tutorial prompt". Fix: label each item as
   recorded from code or from ADR 0008, and drop the dated-script sentence or move it to the record.

6. **Should-fix. Claim: cross-reference corrections were made (only §3.6 to §3.7 in the head row).** Other stale
   references remain because the numbering shifted when §3.6 JMRI-MQTT was inserted:
   - §4 Decision, "§3.11 as its consistency checks", should be §3.12. This is decision text.
   - C6, "the fourth column of §3.11" should be §3.12, and "the head-vocabulary error of §3.6" should be §3.7.
   - §3.2, "`Name` (§3.9)" and "`CP Name` (§3.9)" should both be §3.10.
   - §3.4, "(§3.8)" should be §3.9.
   - C1, "superseded by ... §3.8" for C10 should be §3.9.
   - C2, "`CP Name` (§3.9)" should be §3.10, and "D13 ... by §3.7" should be §3.8 (stations).
   - The transport row the proposal rewrites still cites "(0005 S3)", which ADR 0009 C1 says is superseded by §3.4.

   Fix: correct all of them, or none. The §4 correction touches the decision's wording, so the owner should rule on it
   explicitly.

7. **Should-fix. Claim: "The old head row ... is withdrawn: the mast is found by wire only".** The relation is renamed
   from "Head device to its head" (the trackplan head) to "Head device to its mast" (the Mast device), and with that
   the device-to-trackplan relation leaves the table. That relation is still resolved by a name join with no wire.
   `_heads` (seams.py lines 818-834) keys the trackplan side by `(name_of(mast), name_of(head))` and the device side by
   `(d.serves.split(":")[1], d.head)`. The Mast device's `Name` must equal the trackplan Mast's `Name`, and the head
   device's `Head` must equal the trackplan head's `Name`. Separately, an Implicit fallback of "none" means the
   all-implicit copy (ADR 0009 C7; §3.12 "The table is the test for the three copies") cannot express this relation.
   Fix: keep a row "Head device to its trackplan head | none | Mast device `Name` and `Head` letter, by name | the
   trackplan draws that head (`head.plan`); vocabularies match (§3.7)". State the consequence for C7.

8. **Should-fix. Claim: "Library defaults for names, hosts and transports are empty (unchanged)".** This is false of
   the libraries, and the proposal re-ratifies it. Through `Name = ${Value}`, the library defaults give names
   `'MQTT'`, `'TimeCode'`, `'CMRInet'`, `'LocoNet'`, `'AAR Tokens'`, `'US&S 506'`, `'Bit Packing'`, `'JMRI'`. There
   are placeholders as well: PanelColumn `'COLUMN#'`, PanelSignal `'222'`, PanelSwitch `'111'`, PanelLock `'123'`,
   Milepost `'##.#'`, ModelLamp `'OS'`/`'TRACK'`. "Hosts" is a retired word (§3.11; GLOSSARY.md line 627). "(unchanged)"
   inside a list marked "rewritten" is also ambiguous: it does not say whether the original's rationale and its
   sentences "The compiler's 'missing' report is the tutorial prompt" and "Fixed facts ... keep their defaults"
   survive. Fix: state which defaults are empty today (processor, interlocking, office unit, house, driver address),
   say "processors" for "hosts", and carry the kept sentences verbatim.

9. **Should-fix. The amendments leave other ADR 0009 text, and the glossary, contradicting them.**
   - §3.8: "the house's desk column number (the `PanelColumn` Value ...)". This contradicts "Value is never read"; the
     compiler reads `Column` (seams.py line 694).
   - §3.4: "placed once per processor that connects to it". This contradicts anchors as "processors that run an
     encoding on it" (the glossary's "transport" entry, line 159).
   - The glossary, which outranks the ADRs (ADR 0009 §2), still names a field station and a control point by "the
     Value of the KiCad `MAIN HOUSE` symbol" (GLOSSARY.md line 138 and §4 "control point"). This contradicts "Value is
     never read", `House` and `CP Name`. It needs a glossary delta named in the rev.
   - Outside C11 but now false of the libraries: §3.2's OfficeUnit row ("Columns, Railroad"; the library OfficeUnit
     has only Role, Name and Style) and Encoding-AAR "carries the topic root and Railroad" (Railroad `c1d446b`; the
     library has `Topic` only).

   Fix: amend §3.8 and §3.4 in this rev. Name the glossary delta. Put the two §3.2 rows to the owner as a fourth
   decision ("C11 omitted them"), not silently.

10. **Should-fix. Claim (§3.10 anchors bullet): "each placed `Transport-*` symbol is wired to the processor that runs
    an encoding on it, and only those processors are anchors"; "the compiler derives that and reports it at info".**
    - The compiler does not check that an anchor runs an encoding (`_transports`, seams.py lines 360-380).
    - "Wired" is not required. The `Processor` field and the OfficeUnit fallback (lines 373-375) also anchor an
      instance. No `Transport-*` library symbol even has a `Processor` field, so that fallback is an instance-added
      field.
    - The reach info appears only when the FieldUnit's processor anchors no instance of that transport (line 683).
      Gilroy Interchange reaches MQTT through its code line and gets no info, because Gilroy anchors a JMRI instance.

    The drawing does satisfy the rule today. Fix: word it as the drawing rule plus what the compiler checks, or add
    the check. Say "when its processor anchors no instance of it" for the info.

11. **Nit. Claim: Kind `RAILROAD` is "the one symbol on the root sheet".** `_railroad` (seams.py lines 311-312) counts
    one per project and never checks the sheet. ADR 0008 §4.9 says both "on the root sheet" and "one per project".
    The drawing complies. Fix: say "one per project, placed on the root sheet", or check the sheet.

12. **Nit. Claim: "the macro and its two errors"; "none or two in scope is a compiler error".** There are three
    errors: `macro.field` (lines 279-281) when the field is absent. The pattern `MACRO` (line 21) also accepts an empty
    KIND (`<ROLE::Field>`). Fix: name the third error, and either reject an empty KIND or document it.

13. **Nit. Claim: bits are "numbered from 1".** Only the byte check implies this: `max(used) > declared * 8`
    (line 632). Nothing rejects `Bit` 0. A non-integer `Bit` raises an uncaught `ValueError` at
    `int(a.split(".")[1])` (line 631). The library says only "Bit = the bit number" (Railroad-HardwareIO.kicad_sym
    lines 61 and 541). Fix: add a `bit.number` check (an integer of 1 or more) and say "from 1" in the two
    Descriptions. The proposal's "two sentences added" are three.

14. **Nit. Vocabulary (ADR 0009 §3.11, glossary).**
    - "chip" (proposal lines 55, 59): §3.11 says "`Driver` not `chip`", and ADR 0008 §4.5 says "on a driver or a
      CMRInet Node".
    - Bare "node" (lines 10, 59, 114): §3.11 says "`CMRInet Node` not `node`".
    - "hosts" (line 79): see finding 8.
    - "head row" and "transport row" use "row", which ADR 0008 §4.5 reserves for an element of `devices[]`; say
      "table entry".
    - `Kind.name`: say `<Kind>.<served device's Name>`.
    - "38 rows in the example": say "38 Mast rows of 268".
    - "File" is qualified everywhere ("The Layout Data Model File"): no finding.

15. **Nit. Claim: "netlist ... newer than every sheet and library"; the drawing "at Railroad `a3642e4`".** At 22:22:31
    the owner saved every sheet, and `SPCoast/Watsonville.kicad_sch` now differs from `a3642e4`: Mast_Double S15001
    `Value` changed from `838NAB` to `838NCD` (uncommitted, with `SPCoast.kicad_pro`). The Subdivision working tree
    also has uncommitted `seams.py`, `emit.py`, `geometry.py` and a new `trackplan.py`. No claim in the proposal
    depends on that Mast's name. Fix: re-export and re-run before the owner ratifies, and name the exact Railroad state.

## Claims I would not accept

- That every key's content is `${Value}` and that `${Value}` is the library default (finding 1).
- That `Name` is the key on "a device" without exception, and that the key list is complete without `Bit` and the
  Milepost (finding 2).
- That RIO1's `CMRInet` is drift to be "restored" to `CMRI` (finding 3).
- That rev 3 only records what the drawing and compiler already do, and that §4 is untouched, given Decisions 1 and 2
  and the ADR 0008 §4.5 strike (finding 4).
- That the record entry's "§3.2 and §3.11 say which token names CMRInet" is true: the §3.11 amendment says nothing
  about CMRInet (finding 3).
- That every other amendment is C11 or a cross-reference correction (finding 5).
- That the cross-references are corrected (finding 6).
- That the head device reaches its trackplan head "by wire only" (finding 7).
- That library defaults for names are empty (finding 8).
- That `anchors` are enforced as "only processors that run an encoding" and that every reach is reported (finding 10).
- That the 22:09 netlist is newer than every sheet at the time of ratification (finding 15).
