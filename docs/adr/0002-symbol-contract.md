# 0002. The symbol contract: what each KiCad symbol records

- Status: proposed (final review)
- Date: 2026-10-02 (responses), 2026-10-03 (final form)

Not committed. This ADR changes no library, schematic or code by itself. The owner changed the
libraries while it was open (see Findings).

Terms: FieldUnit `docs/GLOSSARY.md`; ADR 0001 (D1–D16, amended 2026-10-02); `docs/archive/vocabulary-review.md`
iterations 9–11; `ontology.md` rev 5; `layout-model.md` rev 8; `desk-codeline-kicad-pattern.md`.
The class of a control (the `Vital` field) is the subject of FieldUnit `docs/adr/0002-control-transaction-classes.md`
(accepted 2026-10-02). That ADR names the classes: vital and non-vital. The field is `Vital`.

"(unverified)" marks a statement that no opened source supports. "Request n" is request n in
Appendix A. "D n" is decision n below.

## Decisions

The owner answered requests 1 to 15 on 2026-10-02 (Appendix A). Requests 3 and 14 were settled with
the owner on 2026-10-03. D4 and D5 were decided before the requests.

- D1. Interlocking name (request 1). An `INTERLOCKING` symbol names the interlocking: Role
   `INTERLOCKING`, no pins, exactly one in each plant project, the Value is the name (it may display
   `${TITLE}`). A field on `MAIN HOUSE` fails when there are several `MAIN HOUSE` symbols. The title
   block is not an authoritative part of the schematic or the data model.
- D2. `Role` and `Kind` (request 2). The compiler reads `Role` and `Kind` from the library by `lib_id`
   and warns when an instance copy differs: a difference means someone tried to do something different,
   and the tooling needs to understand that problem. The compiler never keys on a symbol name. A new
   symbol with an existing `Role`/`Kind` and the same pin names and count is transparent to the compiler.
- D3. Policy marker `Kind` (request 3, settled 2026-10-03). The `Kind` is the Standard Code rule
   number: `RULE_251` (signaled in one direction), `RULE_261` (signaled in both directions), `RULE_93`
   (yard limits; GCOR 6.13), `RULE_105` (movements on sidings and other than main track; GCOR 6.28). The
   GCOR equivalent goes in the symbol description. The reference for SPCoast is the SP Coast Division
   Rules & Regulations, effective 1943-02-15.
   - Reason: the markers name truths that the Standard Code defines, and SPCoast models a 1942–1985 SP
     railroad.
   - Rule 93: the PRR 1956 text is confirmed. Rule 105 in the SP 1943 book: "All movements on sidings
     must be made with caution" (later editions: at restricted speed).
   - Standard Code numbering varied by road. The SP's own rulebook is the final reference for SPCoast.
- D4. `Rulebook` (decided before the requests). The policy markers lose the `Rulebook` field. The
   Kind/Role mechanism replaced it on purpose. The compiler must be updated to match.
- D5. `MAIN HOUSE` required (decided before the requests). A plant project with no `MAIN HOUSE` symbol
   is a compiler error that states the uncertainty (ADR 0001 D3).
- D6. `Vital` (request 4). `Vital` applies only to controls, so it is a panel appliance attribute, not
   a hardware I/O attribute. It lives on the panel auxiliary symbols (`PanelMCall`, `PanelAuxiliary`),
   never on a switch or signal lever, and not on the `AUXILIARY` symbol. The class names are vital and
   non-vital (FieldUnit ADR 0002).
   - A switch or signal marked non-vital on a drawing is a compiler warning, not an error. The attribute
     is ignored and the appliance is processed as vital.
   - What a drawer means by a "non-vital switch" or "non-vital signal" has a model already: a switch the
     interlocking does not control is dark track; a signal that is not interlocked is an `AUXILIARY`
     lamp; relaxed checks for test or maintenance are the maintainer role, a run-time mode, not a drawn
     attribute.
   - No CTC machine drawn (O1, closed 2026-10-03). In the data model the class of every `AUXILIARY`
     appliance defaults to non-vital. Without a CTC machine there is no code line and no "code, then look
     for the indication" workflow, so the class has no meaning; the appliances are direct access points
     to the field unit. The model is complete only after both the compiler and the linker have run; the
     linker applies the `Vital` field of a drawn panel symbol. The owner names the real problem as the
     "in two places" KiCad setup, not the data model. This also closes ADR 0001 open item 6.
- D7. One library (request 4). The plant and panel libraries will merge into one library soon. The
   split between "plant" and "panel" symbols carries no meaning, and symbol names do not matter (D2).
   This ADR names the two files only to say where a symbol is today.
- D8. Lamp entries (request 5). A lamp lists its office indications in `IndicationToken`, a
   comma-separated list of tokens; the field exists for exactly this purpose. Lamp Values are generally
   not unique and name nothing. A bare track circuit name in the list stands for its `K` token; the
   rename to `OfficeIndications` is withdrawn.
- D9. Code line drawing (requests 6 and 7). Answered by the owner's transport and encoding symbols in
   South-cTc, recorded as ADR 0001 D13 and D15 (final form): transports on the root sheet on the
   `CtcMachine` `Transports` pin, global labels as the code line nets, field stations as encoding
   instances with `Station` and `Address` on the interlocking sheets, `CODELINE` retired. A target is
   available when its facts are present; rules that read the presence of a symbol are obsolete. See
   ADR 0001 D15. The owner changed the Value of the South-cTc Luchessa encoding symbols to "US&S 506
   time-coded DC pulses" (O3, 2026-10-03), replacing "USS Type L Form 506".
- D10. `NextCP` Value (request 8). The `NextCP` Value is the bare name of the neighbor interlocking
    (`Christopher`, not `CP Christopher`).
- D11. `NextCP` rename (request 9). The owner changes the library to `NextInterlocking` /
    `NEXT_INTERLOCKING`. The compiler accepts both names until a task changes the existing schematics.
- D12. `Milepost` (request 10). `MAIN HOUSE` keeps `Milepost`. The compiler reads it to put the control
    points in geographic order.
- D13. `Route` (request 11). The `Route` symbol is deleted. `IndicationCeiling` on switches gives the
    authored input to `bestIndication`.
- D14. Lock levers (request 12). Locks and switches carry the same AAR tokens, controls and
    indications, for simplicity; the prototype crew, dispatcher and field coordination is ignored.
    `PanelLock` keeps the switch pins. A correct electric lock needs more structure and vocabulary, a
    large task that is deferred; `docs/design/ElectricLockProcedure.md` is a lead, not a reference.
- D15. Panel style (request 13). The panel style value is `LEVER`.
- D16. Logical detection block (request 14, settled 2026-10-03). A `TC` field holds one track circuit
    name or a list; a list names a logical detection block. Each listed circuit is a track circuit with
    its own track relay (`TR`), and the block's occupancy is a track repeater (`TP`) over those `TR`s,
    picked up only when every circuit is clear. The owner's words: "All three switches are in one
    logical detection block. If the layout uses detectors on each, they need to be aggregated."
    - Several sensors wired in parallel to one input are one `TR`, inside one track circuit, and are not
      model objects (glossary "aggregation").
    - The OS section of a switch is a block, usually of one circuit. Route clear lists may name blocks.
      A lamp's `IndicationToken` list (D8) is the same idea on the office side. The code chart decides
      whether the office sees the circuits, the block, or both.
    - The model gains a block entity with member track circuits (FieldUnit-Subdivision issue #24).
    - The first reading (one OS circuit shared by 771, 773 and 775) was wrong. The general case stays
      although the owner redrew GilroyCalTrain (as of 2026-10-01, changed by the owner on 2026-10-02,
      to be re-checked). It also serves mixed current and optical detection on one section, and later
      ABS and APB blocks.
- D17. Hand-throw industry switches (request 15). Industry switches are not CTC or dispatcher
    controlled. They may well be (will be) electrically operated, with local fascia-mounted controls
    that must be integrated into the field unit's I/O. Local fascia control is a future scope item with
    its own ADR (ADR 0001, still open item 4).
    - `CP` (O2, closed 2026-10-03). An appliance that is not on the code line needs no dispatcher-visible
      control point name. The `CP` field is not required on it, and the compiler does not diagnose its
      absence or a value that resolves to no `MAIN HOUSE` (Corporal SW901 `INDUSTRY`). A local
      hand-thrown switch connects through the field's hardware mapping: in the model, device to I/O
      unit. Fascia-mounted lamps and levers are still to be designed.

- D18. Every field on a placed symbol is carried into the model with that symbol (owner, 2026-10-03).
    The compiler copies all fields of an instance into the model entity verbatim, keyed by field name,
    as `fields: {name: value}`, with the instance's sheet path, reference and `lib_id` beside them. It
    interprets the fields that the symbol contract names for that Role and Kind, and passes the others
    through untouched. A consumer (generator, model board, glass panel, linker) reads what it needs.
    Adding a field to a symbol needs no grammar, schema or compiler change. Removing or renaming a
    field is a contract change and gets an ADR.
    - Diagnostics: an unknown field is not an error. A contract field with a bad value is an error. A
      field that the contract has retired is a warning, so drift is reported instead of silently
      changing behaviour.
    - A field is not semantics. `Color` on a lamp passes through and the model board reads it; the
      compiler does not need to understand it. `Address` on `PanelColumn-MAX7313` passes through and
      the drive-bit code reads it.
    - The pass-through is not a licence to put facts in Values. A Value is an identifier (the railroad
      name) or a human label. Meaning comes from Role, Kind, pins and named fields. Where a Value's
      letters carry AAR meaning (direction, head letters, the gang letter), the compiler may read them to
      check against the drawn structure and report a difference, never as the only source; the gang id
      (ADR 0003 D8) is the one stated exception.
    - Changed by the owner on 2026-10-03 under this rule: `PanelColumn-MAX7313` gains `Address` (the
      expander address was in the Value) and its `BusKind` is renamed `Kind`, so the symbol follows the
      Role/Kind pattern; the compiler reads the field, not the Value. Lamp colour is the `Color` field,
      kept in the model for the model board and the glass panel; today no phase reads it, and the
      `PanelLamp-RED`/`-YELLOW` variants only preset it.
    - This supersedes P2 below where P2 says a field that no phase reads "goes": it is passed through.

Closed on 2026-10-03 by the owner's second responses (verbatim in Appendix A, "Second round"):
O1 (by D6), O2 (by D17), and the encoding Value of O3 (by D9).

Open:

- O3 (D9). The ATCS description on `Codeline-Encoding-AAR`. The second response covers only the
  US&S 506 encoding Value. Needed: the owner's text, or removal.

## Context

### The storyline

1. Draw each interlocking and the CTC machine in KiCad.
2. The compiler and linker read the drawings and make one model.
3. The generator reads the model and emits one interlocking application for each interlocking and one CTC machine application.
4. The applications run on field processors and on the CTC machine: first virtual, then AAR tokens over MQTT.
5. This ADR states, for each symbol, the facts that step 2 must read so that step 3 can emit step 4.
   Everything else leaves the symbol.

### Why fields went stale

The definitions behind the symbol fields changed (vocabulary review, iteration 11). The symbols hold
facts of the older model, for example the `Station` field of `Codeline-MQTT`. Some fields are read by no
phase. Some facts are recorded twice. Placeholder defaults hide missing values. Some compilers still
classify by a hard-coded table.

### What was inventoried

- The two libraries, read with `SymbolLibraryReader`: the plant library `Railroad.kicad_sym` (29 symbols,
  114 field slots, 11 field names) and the panel library `RailroadPanel.kicad_sym` (14 symbols, 62 field
  slots, 21 field names). Both changed after the inventory (see Findings).
- The netlists of Luchessa, Sargent, GilroyInterchange, Christopher, Corporal, GilroyCalTrain and
  South-cTc, read with `NetlistReader`. Christopher, Corporal and GilroyCalTrain have components but no
  nets, so they give field values only.
- Excluded: the Watsonville project and the Watsonville sheet of South-cTc (as of 2026-10-01, changed
  by the owner on 2026-10-02, to be re-checked). No re-inventory was done.
- Instance copies of `Role` and `Kind` disagree with the library in 15 symbols: Sargent 1,
  GilroyInterchange 2, Christopher 4, Corporal 2, GilroyCalTrain 5, South-cTc 1.

Appendix B holds the full inventory, symbol by symbol, with what each field records today.

## Consequences

### Principles for a field

The changes below follow these principles.

| # | Principle | Test |
|---|---|---|
| P1 | One fact, one place. | If two fields (or a field and a pin connection, a sheet name or a title block) record one fact, one of them goes. |
| P2 | A phase interprets the contract fields; every field is carried (D18). | The contract names the fields a phase interprets for each Role and Kind. A field no phase interprets is carried in `fields` and not removed. A field that duplicates another fact goes under P1, not P2. |
| P3 | Names, not policy. | A field records a drawn fact (a name, a membership, an authored address). It does not record what the generator must do (a topic pattern, a token spelling, a target). The generator owns policy (ADR 0001 D6). |
| P4 | Library facts stay in the library. | A fact that is the same for every instance of a symbol (`Role`, `Kind`, `Color`, `BusKind`, `Direction` on a one-direction marker) is read from the library by `lib_id`. The copy that KiCad puts in each instance is not read. A copy that differs from the library is a warning ("update symbol from library") (D2). |
| P5 | Instance facts have an empty default. | A name, a membership or an address has an empty library default, so a missing value is found. Placeholders (`XX`, `FIXME`, `COLUMN#`, `79.0`, `S`, `Luchessa`) go. |
| P6 | Connections are pins. | A membership that can be drawn as a pin connection is read from the netlist, not from a name field (AGENTS.md). |
| P7 | Code names versus prose terms. | A field name, a Role or a Kind is a code name. It keeps its spelling when the prose term differs, unless its meaning changed or it uses a retired term. Names in values have no `CP ` or `CP_` prefix (ADR 0001 D12). A name used in a topic or a key has each space replaced by `-`; that is the only normalization. |

Instance copies of `Role` and `Kind` disagree with the library (see Context). Examples: `Mast_Double`
with `Kind` = `MAST_DWARF` (GilroyInterchange S3, S4); `Switch_HandThrow` with `Kind` = `SWITCH_POWERED`
(Sargent SW3, Corporal SW901); `PanelLock` 795 with `Kind` = `SWITCH_LEVER` (South-cTc SW796). The
controller compiler reads the instance `Kind`, so it treats lock lever 795 as a switch lever today. The
plant compiler reads neither; it classifies by symbol name (`_PART_KIND`).

Operator roles: dispatcher, tower operator, maintainer. The machine keeps a type that means its panel style.

### Field pass-through (D18)

| Place | Change |
|---|---|
| `schemas/interlocking-plant/v1.json` | each entity gets an open `fields` map (string values, `additionalProperties: true`) beside its interpreted properties, which stay closed |
| `tools/kicad_services/netlist_reader.py` | already exposes every field of a component as `fields`; no change |
| plant and desk compilers | copy the field map onto the entity first, then interpret the contract fields; stop dropping unknown fields |
| symbol contract | which fields a Role and Kind require, and their types, becomes data in the SPCoast repo (like the code line type definitions, D10), so a new Kind is a data change |
| `docs/design/layout-model.md` | every entity gains `fields` |
| test | compile Luchessa, pick any placed symbol, assert that every field in the netlist appears in the model entity's `fields`. This test fails today. |

### Plant library: fields that change

Fields kept unchanged are in Appendix B. "Phase" is the phase that reads the fact.

Common to every plant symbol:

| Symbol · field | Change | Fact recorded | Phase |
|---|---|---|---|
| all · `Role` | read from the library (P4, D2). Value `CONTROLLED_POINT` → `CONTROL_POINT` (retired term) | what the compiler does with the Value and pins | compiler |
| all · `Kind` | read from the library; the compiler classifies by `Role`/`Kind`, never by symbol name, and `_PART_KIND` goes (D2) | the FieldUnit class, or the variant that changes derivation | compiler |
| all · `Value` | library default empty (P5) | the railroad name | compiler |

`MAIN HOUSE`:

| Field | Change | Fact | Phase |
|---|---|---|---|
| `Role` | rename value → `CONTROL_POINT` (P7) | none new | compiler |
| `Milepost` | default `79.0` → empty (Luchessa has `79.0` on all three, the default, never set; Sargent and Corporal have `FIXME`). The compiler reads it to put `controlPoints[]` in geographic order (`layout-model.md` §1) instead of the x coordinate (D12) | the location of the control point | compiler |
| `Value` | no `MAIN HOUSE` in a plant project: error that states the uncertainty (D5) | the control point and its bungalow | compiler |

`INTERLOCKING` (new, D1): Role `INTERLOCKING`, no pins, Value = the interlocking name. Exactly one in
each plant project, else an error. The desk sheet name must equal it (case folded).

Switches (`Switch_Powered`, `Switch_Powered_Small`, `Switch_Powered_NO_TC`, `Switch_Lock`, `Switch_HandThrow`):

| Field | Change | Fact | Phase |
|---|---|---|---|
| `Indications` | add to the library as `IndicationCeiling`, default empty. Form `NORMAL/REVERSE`, e.g. `CLEAR/APPROACH`. Instances carry `Indications` today (none drawn; the compiler reads it) | the most favorable signal indication over the switch in each position (glossary "indication ceiling") | compiler (route `bestIndication`) |
| `TC` | one track circuit name, a list that names a logical detection block (D16), or empty for no OS circuit | the OS track circuit or block that detector-locks the switch | compiler, generator |

Derails (`Switch_Powered_Derail`, `Switch_Powered_Derail_TC`):

| Field | Change | Fact | Phase |
|---|---|---|---|
| `CP` | empty for a dependent derail: the compiler takes the switch's control point (P1). A value that differs is an error | control point of the derail | compiler |

Track circuits (`Track Circuit`, `Track Circuit_Yellow`):

| Field | Change | Fact | Phase |
|---|---|---|---|
| `CP` | empty for a proxy circuit: the circuit is not in this interlocking (Sargent TC4 has `Corporal`) | control point of the circuit | compiler |
| pin 1 name | rename `MC` → `T` (number stays 1; the compiler reads numbers) | none (the name misleads) | none |

Signals:

| Symbol · field | Change | Fact | Phase |
|---|---|---|---|
| Mast `CP` | add to the library, default empty (drawn today on 6 masts: GilroyInterchange 2, Christopher 4; not read). The compiler reads it (`layout-model.md` §1: "controlPoint: the mast's drawn CP field") | control point of the mast in the field | compiler |
| `IRJ-Signal` `CP` | remove after the mast `CP` is filled (P1). The IRJ is `TRACK`; it has no railroad name. Today it is the only source of a mast's control point (read by M and checked by C) | (moves to the mast) | none |

Track terminals:

| Symbol · field | Change | Fact | Phase |
|---|---|---|---|
| `IRJ`, `Bumper` | remove the stray instance `CP` (GilroyCalTrain bumpers 3) and `Direction`/`Name` (GilroyInterchange) | a track graph edge or end | compiler |
| `NextCP` `Value` | bare name of the neighbor interlocking (D10). The library gains `NextInterlocking` with `Kind` `NEXT_INTERLOCKING`; the compiler accepts both until the schematics move (D11) | the neighbor across this plant edge | compiler; linker (subdivision topology); generator (proxy listening; train progression) |

Policy markers (today `Rule251-DoT-Left`, `Rule251-DoT-Right`, `Rule261-DoT-BiDirectional`,
`Rule93-Yard Limits`, `Rule105-RestrictedSpeed`; inventoried as `Rule6.13-Yard Limits` and
`Rule6.28-OtherThanMain`):

| Field | Change | Fact | Phase |
|---|---|---|---|
| `Kind` | `RULE_251`, `RULE_261`, `RULE_93`, `RULE_105` (D3). The compiler reads `Kind`. Done in the library on 2026-10-03; drawn instances keep their old copy until updated from the library | the operating method of the track at the marker | compiler |
| `Rulebook` | remove from the instances (D4). The description cites the GCOR equivalent (D3) | (in `Kind`) | none |
| `Name` | remove (P2). Prose goes in the description | none | none |
| `Direction` | keep on the one-direction markers only (library fact, P4). Remove from the others: `BOTH` is implied by `Kind` | the direction of traffic on one-direction track | compiler |
| `Value` | library default empty (P5); the old defaults (`RULE 251`, `Rule 261`, `YARD`, `DARK`) are labels, not names | the track name | compiler |

`Route`: deleted (D13).

`MaintainerCall` and `AUXILIARY`:

| Symbol · field | Change | Fact | Phase |
|---|---|---|---|
| `MaintainerCall` `Value` | required: `MC<n>`, unique in the interlocking (Luchessa MC1 has `~`) | the call's name; functions `MC<n>S`, `MC<n>K` | compiler, linker, generator |
| `MaintainerCall` `CP` | do not add to the library. Read the control point from the pin connection to `MAIN HOUSE` pin `H` (P6) and do not also require a `CP` field. Remove the 4 existing instance fields (GilroyInterchange 2, Christopher 2) | the bungalow the maintainer is called to | compiler |
| `MaintainerCall` class | no field on this symbol. The class is on `PanelMCall` (D6). A maintainer call is a non-vital control (glossary) | (on the panel symbol) | linker, generator |
| `AUXILIARY` control point | pin connection to `MAIN HOUSE` pin `H` (P6); rename pin name `MC` → `H` | the bungalow of the appliance | compiler |
| `AUXILIARY` `Vital` | not added. The class is on `PanelAuxiliary` (D6) | (on the panel symbol) | none |
| `AUXILIARY` `Functions` | add: `CONTROL`, `INDICATION`, or `CONTROL,INDICATION` (proposal, not asked) | which functions exist; their names are `<Value>S`, `<Value>K` | generator; linker (lever and lamp cross-check) |

The maintainer call connects by pin to `MAIN HOUSE` pin `H`. The drawing records the bungalow of every
connected call. This is verified in the Luchessa, Sargent and GilroyInterchange netlists. In
GilroyInterchange the `CP` field also exists and agrees (MC1, MC2). Christopher and Corporal are not
wired. Luchessa MC1 connects to `CP Luchessa`; its panel lever and lamp are in column 6 (`CP Gilroy`).
By ADR 0001 D3 this is not an error.

`Milepost` symbol: keep as documentation; default empty. No phase reads it.

Plant hardware sheet (planned, not designed here): `desk-codeline-kicad-pattern.md` §5a plans a second
top-level sheet with a field unit symbol, field I/O proxies and IODRIVER symbols. Head type (color
light, semaphore) belongs there, as field I/O. Sensors that are wiring inside one track relay's circuit
are drawn there (glossary "aggregation"). Not in scope.

### Panel library: fields that change

`CtcMachine`:

| Field | Change | Fact | Phase |
|---|---|---|---|
| `Value` | default `SPCoast South cTc` → empty (drawn `SPCoast South`) | machine name | compiler, generator |
| `Type` | rename → `PanelStyle`; value `LEVER` (a lever panel that is not NX; D15). The encoding leaves the machine (D9) | the panel style. It owns the lever rule (per column: at most one switch or lock lever, at most one signal lever, at least one) and the order of levers and lamps | compiler (lever rule), generator (order) |
| `Era` | remove (P2). Title block comment 6 already records the era | none | none |
| `Kind` | add: `DISPATCHER`. Place for the other operator roles (see "Operator roles") | the operator role the machine serves | compiler, generator |
| pin `Transports` | add (D9; ADR 0001 D15) | the code lines of the machine | compiler |

`PanelColumn`:

| Field | Change | Fact | Phase |
|---|---|---|---|
| `Value` | default `COLUMN#` → empty | column number (known nowhere else) | compiler, generator |
| `CP Name` | rename → `CP` (same code name as the plant field; one meaning: a control point name). Bare name. Empty is allowed: the compiler warns, and a 506-style target is then not available for the interlocking (ADR 0001 D15). A value that does not resolve to a `MAIN HOUSE` of the sheet's interlocking is an error | the control point (and so the 506-style field station) whose functions this column carries (ADR 0001 D3) | linker, generator |
| `Interlocking` | remove (P1: the sheet name records it). Default `Luchessa` | none | none |
| `Machine` | remove (P1: the one `CtcMachine` of the project). Default `SPCoast South` | none | none |
| `Column` | remove (P1: copy of Value). Default `${VALUE}` | none | none |

`PanelColumn-MAX7313`: library default `8` for `Value` goes (empty default, P5).

`PanelLock`: keep the pins `Column`, `NWS`, `RWS`, `RWK`, `NWK` (D14). FieldUnit can encode an electric
lock as `WLS` (control) and `WLK` (office indication) (`WireCodec.h`); the SPCoast drawings do not use
them while D14 stands. Reset the instance `Kind` of lock 795 (South-cTc SW796) to the library
`LOCK_LEVER` (D2).

Lamps:

| Field | Change | Fact | Phase |
|---|---|---|---|
| `IndicationToken` | keep the name (D8); default empty (the `S` default goes). A comma-separated list of tokens; a bare track circuit name stands for its `K` token, so today's mix of circuit names (`795T1`) and tokens (`MC1K`) is valid. A list is the office-side form of a block (D16). Proxy form `<interlocking>:<name>` for a foreign function | the office indications OR'd onto this lamp | linker (resolve), generator |

Maintainer call and auxiliary levers:

| Symbol · field | Change | Fact | Phase |
|---|---|---|---|
| `PanelMCall` `Value` | default `MC1` → empty | which call this lever sends | linker, generator |
| `PanelMCall` `ControlToken` | remove (P1, P3: the function name follows from the Value) | none | none |
| `PanelMCall` `Vital` | keep (D6); library default `NO` (non-vital) | the class of the control | linker, generator (interlocking application) |
| `PanelAuxiliary` `ControlToken` | remove (P1, P3) | none | none |
| `PanelAuxiliary` `Vital` | keep (D6); library default `NO` | the class of the control: vital (ignored as a group when one is unsafe) or non-vital (processed anyway) | linker, generator (interlocking application) |

### Code line

ADR 0001 D13 and D15 (final form) decide the drawing (D9). For the libraries and drawings this means:

- The code line symbols the owner drew (`Codeline-Transport-*` with Role `CODELINE_TRANSPORT`,
  `Codeline-Encoding-*` with Role `CODELINE_ENCODING`) are the contract. The `Codeline` symbol (Role
  `CODELINE`) is retired.
- The old `Codeline-MQTT` symbol is deleted from the six other sheets of South-cTc (ADR 0001 D15,
  migration). Its fields `Station`, `Topic` and `Railroad` go with it; `Broker` lives on the MQTT
  transport. A CMRInet node UA is an `Address` on an encoding instance.
- A virtual target needs nothing drawn. The `VIRTUAL` default in the controller compiler goes.

The earlier proposal (`CODELINE` with `Address <field station>` fields) is kept as a record in
Appendix B, B2.8.

### Operator roles

- Dispatcher: `CtcMachine`, `Kind` = `DISPATCHER`. The only role drawn.
- Tower operator: reserved as Role `MACHINE`, `Kind` = `TOWER_OPERATOR` (direct to a locking bed, no
  code line). Where it is drawn (plant project or its own project) is not designed.
- Maintainer: reserved `Kind` = `MAINTAINER` (maintenance or debug mode, without the interlocking). Not
  designed. Fascia devices and service modes have their own ADR (ADR 0001, still open item 4; D17).

### Counts per project

Watsonville is excluded (as of 2026-10-01, changed by the owner on 2026-10-02, to be re-checked).

Read from the netlists (2026-10-01 for plants; 2026-09-30 16:12 for South-cTc, whose sheets are newer,
so its counts can be stale (unverified)). The library `Railroad.kicad_sym` changed on 2026-10-02 and
2026-10-03, after every netlist.

| Change | Luchessa | Sargent | GilroyInterchange | Christopher | Corporal | GilroyCalTrain | Script? |
|---|---|---|---|---|---|---|---|
| `MAIN HOUSE` Value: strip `CP ` | 3 | 0 | 0 | 0 | 0 | 0 | yes |
| `CP` values: strip `CP ` | 15 | 0 | 0 | 15 | 0 | 0 | yes |
| `CP` values that resolve to no `MAIN HOUSE` after the strip (empty IRJ `CP` included; those fields go) | 0 | 4 (3 IRJ, 1 proxy) | 4 (IRJ) | 6 (IRJ) | 10 (4 IRJ, 5 `FIXME`, 1 `INDUSTRY`) | 0 | no for `FIXME`; `INDUSTRY` needs no change (D17) |
| Role `CONTROLLED_POINT` → `CONTROL_POINT` | 3 | 1 | 2 | 3 | 2 | 3 | yes |
| Instance `Role`/`Kind` reset to library | 0 | 1 | 2 | 4 | 2 | 5 | yes |
| Mast `CP` from the IRJ on its `SIGNAL` net, then IRJ `CP` removed | 5 | 3 (IRJ empty: hand) | 4 (2 set on the mast; 2 by hand) | 6 (no nets: hand) | 4 (no nets, IRJ empty: hand) | 5 (no nets: hand) | Luchessa yes; others hand |
| Policy markers: instance `Kind` updated from the library (D3); remove `Rulebook`, `Name`, `Direction` where implied | 5 | 4 | 2 | 4 | 4 | 5 | yes |
| `NextCP` Value: bare interlocking name | 4 | 2 (`~`: hand) | 1 (`Gilroy Caltrain`: hand; as of 2026-10-01, changed by the owner on 2026-10-02, to be re-checked) | 0 | 0 | 1 (`CP_Lick`) | mostly |
| `MaintainerCall`: set Value; remove `CP` | 1 (Value `MC1`) | 0 | 2 (`CP`) | 2 (`CP`) | 0 | 0 | yes |
| `MaintainerCall`: connect pin to `MAIN HOUSE` where not wired | 0 | 0 | 0 | 2 (hand) | 1 (hand) | 0 | hand |
| Dependent derail `CP` emptied | 1 | 0 | 0 | 0 | 1 | 0 | yes |
| Proxy track circuit `CP` emptied | 0 | 1 | 0 | 0 | 0 | 0 | yes |
| Stray fields removed (`Direction`, `Name`, `CP` on IRJ/Bumper) | 0 | 0 | 56 | 0 | 0 | 3 | yes |
| `TC` list: valid as a block (D16); no change | 0 | 0 | 0 | 0 | 0 | 1 (as of 2026-10-01, changed by the owner on 2026-10-02, to be re-checked) | none |
| Empty Values on masts or heads | 0 | 0 | 0 | 7 | 0 | 0 | no |
| `Milepost` set (default or `FIXME`) | 3 | 1 | 0 | 0 | 2 | 0 | no |
| Interlocking name (`INTERLOCKING` symbol, D1) | 1 | 1 | 1 | 1 | 1 | 1 | placement yes |

South-cTc (Watsonville sheet excluded; as of 2026-10-01, changed by the owner on 2026-10-02, to be
re-checked):

| Change | Count | Script? |
|---|---|---|
| `PanelColumn`: remove `Interlocking`, `Machine`, `Column` | 13 × 3 | yes |
| `PanelColumn`: `CP Name` → `CP`; strip `CP ` (3); `FIXME` → empty (10) | 13 | yes; the 10 values by hand later |
| Lamps: `IndicationToken` entries resolve as tokens (D8) | 39 | the 30 that resolve need nothing; 9 `FIXME` entries by hand |
| `PanelMCall`: remove `ControlToken`; keep `Vital` (D6) | 8 | yes |
| `PanelLock`: reset `Kind` on 795 to the library (D2); pins unchanged (D14) | 1 | yes |
| Old `Codeline-MQTT` deleted on the other sheets (ADR 0001 D15) | 6 sheets | no |
| `CtcMachine`: `Type` → `PanelStyle` = `LEVER`, remove `Era`, add `Kind` | 1 | yes |
| Sheet names equal the interlocking names (`Gilroy CalTrain`, `Gilroy Interchange`; as of 2026-10-01, changed by the owner on 2026-10-02, to be re-checked) | 2 | no (owner picks the spelling) |

A script edits `.kicad_sch` files only when no `~*.lck` exists and KiCad is closed (AGENTS.md). It uses
the existing s-expression helpers; it writes no new parser. `tools/legacy_import/` already edits
properties this way (unverified that it fits).

### Compiler and linker changes

Plant compiler:

1. Classify by library `Role`/`Kind` through `lib_id`; drop `_PART_KIND`; never key on a symbol name
   (D2). Warn when an instance copy differs. This admits `Switch_HandThrow`, `Switch_Powered_NO_TC`,
   `Switch_Powered_Small`, `Track Circuit_Yellow`, `Rule93-Yard Limits`, `Rule105-RestrictedSpeed`, the
   semaphore heads, `AUXILIARY` and the new `IRJ_Diag` and `Switch_Powered_Diag` with no code change.
2. Error when a plant project has no `MAIN HOUSE` (D5); the message states the uncertainty. Warn on a
   `CP ` or `CP_` prefix in any name (a check, not normalization). Do not diagnose a missing or
   unresolved `CP` on an appliance that is not on the code line (D17).
3. Read the mast `CP`; during the transition fall back to the IRJ `CP` with a warning.
4. Read policy `Kind` (D3) and `Direction`; find dark track by `Kind` `RULE_105`; stop requiring
   `Rulebook` (D4).
5. Put maintainer calls and auxiliaries in the model, with the control point from the pin net to
   `MAIN HOUSE`. Then `setupCodec()` loses its hard-coded calls (FieldUnit-Subdivision runtime).
6. Read `IndicationCeiling` (fallback `Indications`).
7. Take the dependent derail's control point from its switch.
8. Recognize the proxy form `<interlocking>:<name>` as a foreign reference.
9. Take the interlocking name from the `INTERLOCKING` symbol (D1); `--plant-name` goes.
10. Read `MAIN HOUSE` `Milepost` for control point order (D12).
11. Read a `TC` list as a block with member track circuits (D16). The model gains the block entity
    (issue #24).
12. Accept `NEXT_CP` and `NEXT_INTERLOCKING` (D11).

Controller compiler:

1. Read `CP` (fallback `CP Name`); empty is a warning, not the error `cp-name-unset`.
2. Read `IndicationToken` entries as tokens; a bare track circuit name stands for its `K` token (D8).
3. Read the code lines as ADR 0001 D15 states: transports on the root sheet through the `CtcMachine`
   `Transports` pin, encoding instances (`Station`, `Address`) on the interlocking sheets, the pairing
   from the global label nets. Remove `_TRANSPORTS`, the `VIRTUAL` default, the "exactly one code line
   symbol for each sheet" rule and the reads of `Station` and `Topic` on the old symbol.
4. Read `PanelStyle` and `Kind` from `CtcMachine`; key the lever rule to the panel style.
5. Read `Kind` from the library (D2), so lock lever 795 is a lock lever. `PanelLock` keeps the switch
   tokens (D14).
6. Read `Vital` from `PanelMCall` and `PanelAuxiliary`. Warn, and ignore the attribute, when a switch or
   signal is marked non-vital (D6).

Linker:

1. Pair plant and sheet by interlocking name: case folded, spaces to `-`. `station_key()` (whitespace
   removed) goes.
2. Cross-check `PanelColumn` `CP`, maintainer calls and auxiliaries (now in the model). Locks stay a
   known gap until the plant model has them.
3. Check that addresses are unique on one code line instance, and that two attachments agree.
4. Carry the class of each auxiliary control into the model: non-vital by default, the panel `Vital`
   field where a CTC machine is drawn (D6; FieldUnit ADR 0002).

### Migration order

Each step leaves the drawings and the tools in agreement. Goldens and tests that hard-code Luchessa
facts change in their own step (AGENTS.md).

1. Put both libraries under git (in this repo, as AGENTS.md expects) before the first change.
2. Compilers read new and old names (the fallbacks above). Tests pass on today's drawings.
3. Change the library: renames, removals, empty defaults, new fields, new symbols (`INTERLOCKING`,
   `NextInterlocking`), pin changes.
4. Run the script per project, with KiCad closed. Rebuild netlists (`make netlist`). Run the compilers.
   Compare the models before and after by behavior gates, not by goldens.
5. Hand work: `FIXME` values, unresolved `CP` values, mast `CP` where nets are missing, the old
   `Codeline-MQTT` symbols, the `INTERLOCKING` symbols, maintainer call pins.
6. Update FieldUnit `examples/spcoast_ctc` `configureDesk()` and `tools/test_ctc_desk.py` for the bare
   names; update goldens and tests in their own commit.
7. Remove the fallbacks. Instance copy warnings become errors where the owner wants it.
8. Watsonville follows when its schematic is re-checked (changed by the owner on 2026-10-02).

### Cost

- A library change across the plant and panel symbols, with the new `INTERLOCKING` and
  `NextInterlocking` symbols. The code line symbols exist already (drawn by the owner on 2026-10-02).
- One script run per project, then hand work (list in step 5).
- Compiler, controller compiler and linker changes above, with a transition period of fallbacks.
- Test and golden updates in their own commit.

## Findings

These are facts from the inventory and from a read of the libraries on 2026-10-03, not proposals.
Watsonville was excluded (as of 2026-10-01, changed by the owner on 2026-10-02, to be re-checked).

- Library on 2026-10-03 (symbol names and `Role`/`Kind`/`Vital` only; not re-inventoried field by
  field): the plant library has 30 symbols. `Route` is gone. `Rule6.13-Yard Limits` and
  `Rule6.28-OtherThanMain` are now `Rule93-Yard Limits` (`RULE_93`) and `Rule105-RestrictedSpeed`
  (`RULE_105`). `IRJ_Diag` (`IRJ`) and `Switch_Powered_Diag` (`SWITCH_POWERED`) are new. `MAIN HOUSE`
  still has Role `CONTROLLED_POINT`. `NextCP` still has `Kind` `NEXT_CP`. `Direction` = `BOTH` is still
  on the 261, 93 and 105 markers.
- Library on 2026-10-03: the panel library has 20 symbols. `Codeline-MQTT` and `Codeline-CMRInet` are
  gone. The code line symbols are `Codeline` (Role `CODELINE`, retired by ADR 0001 D15),
  `Codeline-Encoding-AAR`, `-Bits`, `-US&S-506` (Role `CODELINE_ENCODING`) and
  `Codeline-Transport-CMRInet`, `-Loconet`, `-MQTT`, `-TimeCode` (Role `CODELINE_TRANSPORT`).
  `PanelMCall` and `PanelAuxiliary` have `Vital` = `NO`.
- Prototype drawn by the owner on 2026-10-02 on the South-cTc Luchessa sheet: `Codeline` (pin
  `Transports`), `Codeline-Transport-MQTT` and `Codeline-Transport-TimeCode` (pins `Codeline`,
  `Encoding`), `Codeline-Encoding-AAR` and `Codeline-Encoding-US&S-506` (pin `Encoding`). The netlist
  showed the graph complete. ADR 0001 D13 and D15 were amended to this shape, and later the same day
  to the final form (transports on the root sheet on the `CtcMachine` pin `Transports`).
- Instance copies of `Role` and `Kind` disagree with the library in 15 symbols (Sargent 1,
  GilroyInterchange 2, Christopher 4, Corporal 2, GilroyCalTrain 5, South-cTc 1). Examples are in
  "Principles for a field".
- The controller compiler reads the instance `Kind`, so it treats lock lever 795 as a switch lever. The
  plant compiler reads neither and classifies by symbol name (`_PART_KIND`).
- Compiler defect: policy markers fail outside Luchessa. The compiler requires `Rulebook`
  (`missing_policy_rulebook`), which the library does not carry on purpose (D4). Only the five Luchessa
  instances have `Rulebook` (`251`, `261`, `Rule 6.28`); the other five projects fail. The compiler finds
  dark track by `Rulebook` starting with `6.28`.
- At the inventory the `Kind` names of policy markers mixed Standard Code rule numbers (251, 261) with
  GCOR-style numbers (6.13, 6.28). The library was changed on 2026-10-03 (D3).
- The compiler rejects symbols that are not in `_PART_KIND`: `Switch_Powered_Small`,
  `Switch_Powered_NO_TC`, `Switch_HandThrow` (GilroyCalTrain 2, Sargent 1, Corporal 1), `Track Circuit_Yellow`
  (GilroyCalTrain 3), `Rule6.13-Yard Limits`, `Switch_Powered_Derail_TC`, the semaphore heads and
  `AUXILIARY`. `Switch_Powered_Derail_TC`, the semaphore heads and `AUXILIARY` are not drawn.
- The `Milepost` default `79.0` was never set in Luchessa (all three). Sargent and Corporal have `FIXME`.
- Instances carry `Rulebook` (Luchessa, 5), `Indications` (none drawn; the compiler reads it) and stray
  `Direction`/`Name` (GilroyInterchange, 27 and 29).
- At the inventory the `Route` symbol and `Milepost` entities were read by no phase. `Route` was not
  drawn. The owner deleted `Route` from the library (D13).
- Mast `CP` is drawn on 6 masts (GilroyInterchange 2, Christopher 4) and not read. The IRJ `CP` is today
  the only source of a mast's control point.
- Sargent TC4 is a proxy circuit with `CP` = `Corporal`.
- GilroyCalTrain 771 has `TC` = `771T1, 773T1, 775T1` (as of 2026-10-01, changed by the owner on
  2026-10-02, to be re-checked).
- Luchessa MC1 has Value `~`. Today `MaintainerCall` is in `_PART_KIND` but no phase puts it in the model
  (known gap; `setupCodec()` hard-codes the calls).
- Pin 1 of `Track Circuit` and of `MaintainerCall` and `AUXILIARY` is named `MC`, which misleads.
- At the inventory `Codeline-MQTT` had `Value` `MQTT`, `Railroad` `SPCoast`, `Broker`, `Topic`
  `ctc/${Railroad}/codeline/${Station}` and `Station` `${SHEETNAME}`. The controller compiler reads
  `Station`, `Broker` and `Topic`, and also looks for `TopicRoot`, which no symbol had. `Codeline-CMRInet`
  had `Station` (`Node UA`), `Port`, `Baud`. Neither had pins.
- No phase reads `Era`, `Interlocking`, `Machine`, `Column`, `Color`, `Vital` or `Railroad` on the panel
  side.
- Lamp `IndicationToken` entries mix circuit names (`795T1`) and tokens (`MC1K`). The `S` default and
  `COLUMN#` default are placeholders.
- `PanelLock` has the same pins as `PanelSwitch`; locks are not in the plant model, so the linker cannot
  check them. `PanelMCall` Value is reported as unchecked.
- `PanelColumn` `CP Name` holds `FIXME` in 10 of 13 columns.
- Spellings of the same interlocking differ between sources (as of 2026-10-01, changed by the owner on
  2026-10-02, to be re-checked). GilroyCalTrain has four spellings: folder `GilroyCalTrain`, title
  `Gilroy Caltrain Station`, desk sheet `Gilroy CalTrain`, and `NextCP` in GilroyInterchange `Gilroy
  Caltrain`. GilroyInterchange: folder and title `GilroyInterchange`, desk sheet `Gilroy Interchange`.
- The linker pairs plant and desk sheet by removing whitespace, a rule that ADR 0001 D12 (amended)
  withdraws.
- `NextCP` Values: GilroyCalTrain `CP_Lick`, Sargent `~` (2), GilroyInterchange `Gilroy Caltrain` (the
  GilroyCalTrain and GilroyInterchange values as of 2026-10-01, changed by the owner on 2026-10-02, to be
  re-checked).
- Christopher and GilroyCalTrain have no nets in the netlist (components only), so connectivity there is
  not verified. Mast and head Values are empty in Christopher (7).
- The library `Railroad.kicad_sym` changed on 2026-10-02 and 2026-10-03, after every netlist. South-cTc
  sheets are newer than its netlist (2026-09-30 16:12), so its counts can be stale (unverified).

## Appendix A: the requests and the owner's responses, verbatim

The requests as asked on 2026-10-02, with the owner's responses unchanged. In the source the last three
items carry the numbers 12, 13 and 14 a second time; this ADR cites them as requests 13 (panel style),
14 (`TC` list) and 15 (hand-throw switch). "Decision" in the text below means the proposal, now the
Consequences section.

Ordered by what blocks the migration first. Answer each in one line. The default is the proposal in
"Decision".

Already decided by the owner (2026-10-02), so not asked:

- The `Rulebook` field was replaced on purpose by the Kind/Role mechanism. The policy markers lose `Rulebook`.
  The compiler must be updated to match.
- A plant project with no `MAIN HOUSE` symbol is a compiler error that states the uncertainty.

Asked:

1. Interlocking name: which symbol or field names the interlocking? Options: 
   A. an `INTERLOCKING` symbol;
   B. a field on `MAIN HOUSE`
   C. the title block. 
   Default: A.

   RESPONSE: Agreed: A
   B fails when there are multiple MAIN HOUSE symbols
   C fails becaus title blocks are not authorative parts of the schematic/data model

2. Read `Role` and `Kind` from the library by `lib_id`, and only warn on instance copies that differ? Options:
   yes, no. Default: yes.

   RESPONSE: Agreed: warn when symbols don't match library Kind and Role.
   Disagreement means someone was trying to do something different, and we need to understand their problem better...

   Tied to this: making a new symbol with an existing KIND/ROLE and the same pin naming/count shoul dbe transparent to the compiler.  Saying another way, the names of the symbols should not be special/hardcoded into the compiler.

3. Policy marker `Kind` names: by meaning (`SIGNALED_ONE_DIRECTION`, `SIGNALED_BOTH_DIRECTIONS`,
   `YARD_LIMITS`, `NOT_SIGNALED`) or by one rulebook (which)? Default: by meaning.

   RESPONSE: Is this a reference to the direction of traffic?
   NEED MORE INFO TO RESPOND

4. Where does the `Vital` field (the control class) live? Options: on the plant `AUXILIARY` symbol (moved from the panel
   symbols), or stay on the panel symbols. Default: on `AUXILIARY`. The class names (vital, non-vital) and the field `Vital` come
   from FieldUnit ADR 0002 (control transaction classes).

   RESPONSE: These can only apply to **controls**, which makes them panel appliance attributes and not hardware I/O attributes.  
   This implies that PanelAuxiliary is the correct symbol, not the AUXILIARY lamp...
   Further, the attribute does not apply to signal and switch levers; only to auxiliary functions such as MCall and PanelAuxiliary...

   I hear a distinction between "plant" and "panel" symbols that should not exist - these symbols will merge into one library soon, and their names should not matter...

5. Lamp entries: office indication names (`795T1K`, `MC1K`) or appliance names (`795T1`, `MC1`)?
   
   Default: office indication names.

   RESPONSE:  The attribute `IndicationToken` exists for exactly this purpose.  It is a comma separated list of tokens...
   The lamp appliances don't generally have VALUES that are unique...
   
6. Addresses on `CODELINE`: one field per field station (`Address Gilroy`) or one list field (`Addresses`)?
   Default: one field per field station.

   RESPONSE: See new transport/encoding symbology in South-cTc

7. Encoding and transport symbols: once per code line on the root sheet (global label), or on every sheet?
   Default: once per code line on the root sheet.

      RESPONSE: See new transport/encoding symbology in South-cTc

8. `NextCP` Value: the neighbor interlocking or the neighbor control point? Default: the neighbor interlocking.

   RESPONSE: neighbor interlocking

9.  Rename `NextCP` / `NEXT_CP` to `NextInterlocking` / `NEXT_INTERLOCKING`: yes or no? Default: yes (optional).

   RESPONSE: I'll change the library, but allow both unless we kick off a task to modify the existing schematics...

10. `MAIN HOUSE` `Milepost`: keep as the geographic order of control points, or remove? Default: keep.

   RESPONSE: Keep

11. Remove the unread `Route` symbol: yes or no? Default: yes.

   RESPONSE: Deleted

12. Does a lock lever carry `NWK` and `RWK` as well as `WLS` and `WLK`? Default: `WLS` and `WLK` only until
    FieldUnit confirms (unverified).

   RESPONSE: Currently, locks and switches carry the SAME AAR tokens (both control and indication) for simplicity - the prototypical crew/dispatcher/field coordination is ignored.

   In order to "do" electric locks correctly, we need more structure and vocabulary, which is a large scoped task that I'm not sure we're ready for in this session.  I've captured it in `docs/design/ElectricLockProcedure.md` for reference.


12.  Spelling of the SPCoast panel style value (for example `LEVER`)? Default: `LEVER`.
    
     RESPONSE:  LEVER

13.  GilroyCalTrain switch 771 has `TC` = `771T1, 773T1, 775T1`: one shared OS circuit, or three? Default: none;
    the drawing owner knows.

   RESPONSE: All three switches are in one logical detection block.  If the layout uses detectors on each, they need to be aggregated.

14.  Is a hand-throw switch an appliance with a `CP` (Corporal 1 has `INDUSTRY`)? Default: none; the drawing
    owner knows.

   RESPONSE: The industry switches are not ctc/dispatcher controlled, though they may well (will) be electrically operated devices with local fascia mounted controls that need to be integrated into the field unit's I/O connections.


### Second round (2026-10-03)

The open items as written in the first final-review form, with the owner's responses unchanged.

- O1 (D6). How the interlocking application learns the class of an auxiliary control when no CTC
  machine is drawn, for example for a tower operator or a virtual target. The proposal put the class
  on the plant `AUXILIARY` symbol for this reason. FieldUnit ADR 0002 requires the class on each
  function of the interlocking model. Needed: the owner's rule (for example, the linker carries the
  panel class into the model, and an undrawn class defaults to one of the two).

  RESPONSE: This looks like a problem with the current "in two places" kicad sch setup more than a Data Model question.
  deconflating into two parts:
  Data model: The default for all AUXILIARY Appliances is "non-vital".  
              Without a cTc, the "appliances" are simply direct-access points to the field unit, there is no code line, no "code and look for an indication" workflow, and the concept behind this classification has no meaning
  Compiler: The data model is not complete until both the compiler and linker have run.

- O2 (D17). What the `CP` field of a hand-throw switch holds. Corporal SW901 has `INDUSTRY`, which
  resolves to no `MAIN HOUSE`. Needed: the fascia ADR.

  RESPONSE: why is a dispatcher-visible name for a point to control this non-remotely-managed appliance needed?
            The connection for a hand thrown "local" switch is via the field's hardware mapping, and is not
            exposed over a codeline.  The data model's connection is from a device to an I/O unit and from local I/O devices for fascia-mounted lamps, levers etc that are still TBD...

- O3 (D9). On the drawn prototype: the Value "USS Type L Form 506" ("Type L" and "Form 506" have no
  source; the glossary retires them) and the ATCS description on `Codeline-Encoding-AAR`. Needed: the
  owner's spelling.

  RESPONSE: Updated South-cTc's Luchessa encoding symbols to say "US&S 506 time-coded DC pulses"

## Appendix B: full inventory

Readers today (plant): `plant_graph/compiler.py` (C), `plant_graph/model.py` (M), `plant_graph/routes.py`
(R), `plant_graph/indications.py` (I), `plant_graph/picture.py` (P), `link/linker.py` (L).
Readers today (panel): `controller_graph/compiler.py` (CC) and `link/linker.py` (L). CC reads `Role`,
`Kind`, `Columns`, `Type`, `CP Name`, `Station`, `Broker`, `TopicRoot`, `Topic`, `Port`, `Baud`, `BusKind`,
`IndicationToken`, `ControlToken` and `Value`. No phase reads `Era`, `Interlocking`, `Machine`, `Column`,
`Color`, `Vital` or `Railroad`.

In the tables below, "request n" refers to Appendix A and "D n" to the Decisions. The "Today" columns
are the inventory of 2026-10-01 (South-cTc: netlist of 2026-09-30). The "Proposed" column is the
proposal as reviewed; where a decision changed it, the cell states the decided form. The Consequences
section is the current list of changes.

### B1. Plant library (`Railroad.kicad_sym`)

At the inventory: 29 symbols, 114 field slots, 11 field names (`CP`, `Direction`, `Head`, `Indication`, `Kind`,
`Milepost`, `Name`, `Role`, `Signal`, `TC`, `Value`). Instances also carry `Rulebook` (Luchessa, 5),
`Indications` (none drawn; the compiler reads it) and stray `Direction`/`Name` (GilroyInterchange, 27
and 29).

#### B1.1 Fields common to every plant symbol

| Field | Today | Proposed | Fact | Phase |
|---|---|---|---|---|
| `Role` | library value on all 29; no plant reader (C classifies by symbol name) | keep; read from the library (P4). Rename value `CONTROLLED_POINT` → `CONTROL_POINT` (retired term) | what the compiler does with the Value and pins | compiler |
| `Kind` | library value on 27; no plant reader | keep; read from the library; the compiler classifies by `Role`/`Kind`, never by symbol name, and `_PART_KIND` goes (D2) | the FieldUnit class, or the variant that changes derivation | compiler |
| `Value` | per symbol; read by C | keep; meaning per family below; library default empty (P5) | the railroad name | compiler |

#### B1.2 `MAIN HOUSE`

Pins: 1 `H`. In Luchessa, Sargent and GilroyInterchange pin `H` connects to the `MaintainerCall` pin.

| Field | Today: default · reader | Proposed | Fact | Phase |
|---|---|---|---|---|
| `Value` | empty · C, M (control point list, board order) | keep. Bare name (`Luchessa`, `Gilroy`, `Carnadero`). May display a title block variable (`${COMMENTx}`). No `MAIN HOUSE` in a plant project: error that states the uncertainty (D5) | the control point and its bungalow; on a 506-style encoding also the field station name | compiler, generator |
| `Role` | `CONTROLLED_POINT` · none | rename value → `CONTROL_POINT` | (P7) | compiler |
| `Milepost` | `79.0` · none. Luchessa has `79.0` on all three (the default, never set); Sargent, Corporal `FIXME` | keep, default empty; the compiler reads it to put `controlPoints[]` in geographic order (`layout-model.md` §1) instead of the x coordinate (D12) | the location of the control point | compiler |

#### B1.3 Switches: `Switch_Powered`, `Switch_Powered_Small`, `Switch_Powered_NO_TC`, `Switch_Lock`, `Switch_HandThrow`

Pins: 1 `C`, 2 `N`, 3 `R`. `Kind`: `SWITCH_POWERED` (three symbols), `SWITCH_LOCK`, `SWITCH_MANUAL`.
`Switch_Powered_Small`, `Switch_Powered_NO_TC` and `Switch_HandThrow` are not in `_PART_KIND`; the
compiler rejects them today (GilroyCalTrain 2, Sargent 1, Corporal 1).

| Field | Today: default · reader | Proposed | Fact | Phase |
|---|---|---|---|---|
| `Value` | empty · C | keep: switch number (`783`) | switch name; lever and tokens match it | compiler, linker, generator |
| `CP` | empty · C (checks), M (members), C (board section) | keep. Bare control point name | control point of the switch in the field (control point limits) | compiler; generator (model board; later the hardware sheet) |
| `TC` | `${VALUE}T1` (empty on `NO_TC`, `HandThrow`) · C, R | keep. One track circuit name, a list that names a logical detection block (D16; GilroyCalTrain 771 has `771T1, 773T1, 775T1`), or empty for no OS circuit. The proposal allowed one name only | the OS track circuit or block that detector-locks the switch | compiler, generator |
| `Indications` | not in library; none drawn · C, I | add to the library as `IndicationCeiling`, default empty. Form `NORMAL/REVERSE`, e.g. `CLEAR/APPROACH` | the most favorable signal indication over the switch in each position (glossary "indication ceiling") | compiler (route `bestIndication`) |

Variants that differ only in a field default or in graphics keep one `Kind`. Removing them is optional.

#### B1.4 Derails: `Switch_Powered_Derail`, `Switch_Powered_Derail_TC`

Pins: 1 `C`, 2 `R` (through path = REVERSE; verified in the library). `Kind` = `DERAIL` on both.
`Switch_Powered_Derail_TC` is not in `_PART_KIND` and is not drawn.

| Field | Today: default · reader | Proposed | Fact | Phase |
|---|---|---|---|---|
| `Value` | empty · C | keep. Dependent when its gang id (the Value minus its trailing letter) matches a switch or lock gang of the interlocking, by convention `<id>D`; independent otherwise. A Value used twice across switches, locks and derails is an error (ADR 0003 D8) | derail name; dependency on its gang | compiler |
| `CP` | empty · C (mismatch warning) | keep for an independent derail. Empty for a dependent derail: the compiler takes the switch's control point (P1). A value that differs is an error | control point of the derail | compiler |
| `TC` | empty / `${VALUE}T1` · C | keep; same rule as switches | own track circuit, if any | compiler |

`Switch_Powered_Derail_TC` only changes the `TC` default. Remove it, or keep it as a convenience (optional).

#### B1.5 Track circuits: `Track Circuit`, `Track Circuit_Yellow`

Pins: 1 named `MC`. `Kind` = `TRACK_CIRCUIT` on both. `Track Circuit_Yellow` is not in `_PART_KIND`
(GilroyCalTrain uses it 3 times). The difference between the two is graphics only (unverified).

| Field | Today: default · reader | Proposed | Fact | Phase |
|---|---|---|---|---|
| `Value` | empty · C | keep: circuit name (`1NA`), the authoritative name. A foreign circuit uses the proxy form `<interlocking>:<name>` (Sargent `Corporal:2NA`) | track circuit; or a reference to a circuit of another interlocking | compiler; generator (a foreign interlocking: listen on the code line; the same interlocking: local) |
| `CP` | empty · C, M | keep. Empty for a proxy: the circuit is not in this interlocking (Sargent TC4 has `Corporal`) | control point of the circuit | compiler |
| pin 1 name | `MC` | rename the pin name to `T` (number stays 1; the compiler reads numbers) | none (the name misleads) | none |

#### B1.6 Signals: `Mast_Single`, `Mast_Double`, `Mast_Dwarf`, `Signal Head - CL`, `Signal Head - SemaphoreU2`, `Signal Head - SemaphoreU3`, `IRJ-Signal`

Pins: masts 1 `SIGNAL` plus head pins (`H` or `H1`, `H2`); heads 1 `M`; `IRJ-Signal` 1 `A`, 2 `B`, 3
`SIGNAL`. The two semaphore heads are not in `_PART_KIND` and are not drawn.

| Symbol · field | Today: default · reader | Proposed | Fact | Phase |
|---|---|---|---|---|
| Mast `Value` | empty · C, R | keep: `^\d+[NSEW][A-E]+$` (`784EAB`) | mast name; signal number; direction (N/W = LEFT, S/E = RIGHT); its heads | compiler |
| Mast `CP` | not in library. Drawn on 6 masts (GilroyInterchange 2, Christopher 4); not read | add to the library, default empty; the compiler reads it (`layout-model.md` §1: "controlPoint: the mast's drawn CP field") | control point of the mast in the field | compiler |
| `IRJ-Signal` `CP` | empty · M (the only source of a mast's control point today), C (check) | remove after the mast `CP` is filled (P1). The IRJ is `TRACK`; it has no railroad name | (moves to the mast) | none |
| Head `Value` | empty · C | keep: one letter (ADR 0003 D9 allows any letter A–Z). The compiler checks that the letters of the heads on a mast equal the letters in the mast Value (unverified that it checks today) | head letter | compiler |

#### B1.7 Track terminals: `IRJ`, `Bumper`, `NextCP`

| Symbol · field | Today: default · reader | Proposed | Fact | Phase |
|---|---|---|---|---|
| `IRJ`, `Bumper` | `Value`, `Role`, `Kind` only · C (by reference) | keep; no instance fields. Remove the stray instance `CP` (GilroyCalTrain bumpers 3) and `Direction`/`Name` (GilroyInterchange) | a track graph edge or end | compiler |
| `NextCP` `Value` | empty · R (terminal designation) | keep. Bare name of the neighbor interlocking (`Christopher`, not `CP Christopher`). It names the interlocking, not the control point (D10). The library gains `NextInterlocking` / `NEXT_INTERLOCKING`; the compiler accepts both until the schematics move (D11; the term "CP" is not a common noun) | the neighbor across this plant edge | compiler; linker (subdivision topology); generator (proxy listening; train progression) |

#### B1.8 Policy markers: `Rule251-DoT-Left`, `Rule251-DoT-Right`, `Rule261-DoT-BiDirectional`, `Rule6.13-Yard Limits`, `Rule6.28-OtherThanMain`

On 2026-10-03 the library names the last two `Rule93-Yard Limits` and `Rule105-RestrictedSpeed` (D3).
At the inventory the `Kind` names mix Standard Code rule numbers (251, 261) with GCOR-style numbers (6.13, 6.28).
The compiler reads `Rulebook` (not in the library) and `Direction`. It finds dark track by `Rulebook`
starting with `6.28`. Only Luchessa instances have `Rulebook`, so the other five projects fail
`missing_policy_rulebook` today. This is a compiler defect: the owner replaced `Rulebook` by the Kind/Role
mechanism on purpose (D4), and the compiler must be updated. `Rule6.13-Yard Limits` is not in
`_PART_KIND`.

| Field | Today: default · reader | Proposed | Fact | Phase |
|---|---|---|---|---|
| `Kind` | `RULE_251`, `RULE_261`, `RULE_6.13`, `RULE_6.28` · none | the Standard Code number: `RULE_251`, `RULE_261`, `RULE_93`, `RULE_105` (D3). The proposal named them by meaning (`SIGNALED_ONE_DIRECTION`, `SIGNALED_BOTH_DIRECTIONS`, `YARD_LIMITS`, `NOT_SIGNALED`); the owner chose rule numbers. The compiler reads `Kind` | the operating method of the track at the marker | compiler |
| `Rulebook` | instance only (Luchessa 5: `251`, `261`, `Rule 6.28`) · C, R, P | remove (D4; P1: `Kind` records it). The description cites the GCOR equivalent (D3) | (in `Kind`) | none |
| `Name` | prose (`Track Signaled in One Direction`); on Left, 6.13, 6.28, not Right · none | remove (P2). Prose goes in the description | none | none |
| `Direction` | `LEFT`, `RIGHT`, `BOTH` · C (required on every marker) | keep on the one-direction markers only (library fact, P4). Remove from the others: `BOTH` is implied by `Kind` | the direction of traffic on one-direction track | compiler |
| `Value` | `RULE 251`, `Rule 261`, `YARD`, `DARK` · C ("track-name Value") | keep: the track name (`MT1`, `Branch`). Library default empty (P5); the defaults are labels, not names | the track name | compiler |

#### B1.9 `Route`

Fields `Signal`, `Head`, `Indication` (`CLEAR`), `Kind` = `ROUTE_INDICATION`. No reader. Not drawn.
Proposed: remove the symbol. `IndicationCeiling` on switches (B1.3) gives the authored input to
`bestIndication`. Keep it only if a route-level override is needed (request 11). Decided: deleted
(D13).

#### B1.10 `MaintainerCall` and `AUXILIARY`

Pins: 1 named `MC` on both. Today `MaintainerCall` is in `_PART_KIND` but no phase puts it in the model
(known gap; `setupCodec()` hard-codes the calls). `AUXILIARY` is not in `_PART_KIND` and is not drawn.

| Symbol · field | Today: default · reader | Proposed | Fact | Phase |
|---|---|---|---|---|
| `MaintainerCall` `Value` | empty · C (name only) | keep: `MC<n>`, unique in the interlocking. Required (Luchessa MC1 has `~`) | the call's name; functions `MC<n>S`, `MC<n>K` | compiler, linker, generator |
| `MaintainerCall` `CP` | not in library; drawn on 4 (GilroyInterchange 2, Christopher 2) · none | do not add. The control point is the `MAIN HOUSE` its pin connects to (P6); do not also require a `CP` field. Remove the 4 instance fields | the bungalow the maintainer is called to | compiler |
| `MaintainerCall` class | none | no field on this symbol; the class is on `PanelMCall` (D6). A maintainer call is a non-vital control (iteration 11) | (on the panel symbol) | linker, generator |
| `AUXILIARY` `Value` | empty · none | keep: the appliance name (switch heater, bungalow door) | auxiliary appliance name | compiler, linker, generator |
| `AUXILIARY` control point | none | pin connection to `MAIN HOUSE` pin `H` (P6); rename pin name `MC` → `H` | the bungalow of the appliance | compiler |
| `AUXILIARY` `Vital` field | none (the class is on the panel symbols today) | not added (D6: the class is on `PanelAuxiliary`). The proposal moved it here (request 4; reason in B2.7) | (on the panel symbol) | none |
| `AUXILIARY` `Functions` | none | add: `CONTROL`, `INDICATION`, or `CONTROL,INDICATION` (proposal) | which functions exist; their names are `<Value>S`, `<Value>K` | generator; linker (lever and lamp cross-check) |

The drawn pin connection records the bungalow of every connected call. It is verified in the Luchessa,
Sargent and GilroyInterchange netlists; in GilroyInterchange the `CP` field also exists and agrees
(MC1, MC2). Christopher and Corporal are not wired. Luchessa MC1 connects to `CP Luchessa`; its panel
lever and lamp are in column 6 (`CP Gilroy`). By ADR 0001 D3 this is not an error.

#### B1.11 `Milepost`

`Value` = `##.#`, `Role` = `ANNOTATION`. Entity made by C; no reader. Keep as documentation; default
empty. No phase reads it.

#### B1.12 Plant hardware sheet (planned, not designed here)

See Consequences, "Plant library: fields that change".

### B2. Panel library (`RailroadPanel.kicad_sym`)

At the inventory: 14 symbols, 62 field slots, 21 field names. On 2026-10-03: 20 symbols (see Findings).

#### B2.1 `CtcMachine` (Role `MACHINE`)

| Field | Today: default · reader | Proposed | Fact | Phase |
|---|---|---|---|---|
| `Value` | `SPCoast South cTc` (drawn `SPCoast South`) · CC | keep; default empty | machine name | compiler, generator |
| `Type` | `US&S506` · CC | rename → `PanelStyle`; value `LEVER` (a lever panel that is not NX; D15). The encoding leaves the machine (D9) | the panel style. It owns the lever rule (per column: at most one switch or lock lever, at most one signal lever, at least one) and the order of levers and lamps | compiler (lever rule), generator (order) |
| `Columns` | `14` · CC | keep | number of physical columns | compiler, generator |
| `Era` | empty · none | remove (P2). Title block comment 6 already records the era | none | none |
| `Kind` | none | add: `DISPATCHER`. Place for the other operator roles (B2.9) | the operator role the machine serves | compiler, generator |

#### B2.2 `PanelColumn` (Role `COLUMN`)

Pins 1–8 `Column` (all equal; membership only).

| Field | Today: default · reader | Proposed | Fact | Phase |
|---|---|---|---|---|
| `Value` | `COLUMN#` · CC | keep: column number; default empty | column number (known nowhere else) | compiler, generator |
| `CP Name` | empty · CC, L | rename → `CP` (same code name as the plant field; one meaning: a control point name). Bare name. Empty is allowed: the compiler warns; a generator for a 506-style target fails without it. A value that does not resolve to a `MAIN HOUSE` of the sheet's interlocking is an error | the control point (and so the 506-style field station) whose functions this column carries (ADR 0001 D3) | linker, generator |
| `Interlocking` | `Luchessa` · none | remove (P1: the sheet name records it) | none | none |
| `Machine` | `SPCoast South` · none | remove (P1: the one `CtcMachine` of the project) | none | none |
| `Column` | `${VALUE}` · none | remove (P1: copy of Value) | none | none |

#### B2.3 `PanelColumn-MAX7313` (Role `IODRIVER`)

Pins `bit0`–`bit15`. Keep `Value` (bus address, default empty; the library default `8` goes) and
`BusKind` (library fact, P4). Read by CC; used by the generator for the CTC machine application.

#### B2.4 Levers: `PanelSwitch`, `PanelLock`, `PanelSignal` (Role `APPLIANCE`)

| Symbol | Value | Pins today | Proposed |
|---|---|---|---|
| `PanelSwitch` (`SWITCH_LEVER`) | switch name; L matches plant switches | `Column`, `NWS`, `RWS`, `RWK`, `NWK` | keep |
| `PanelLock` (`LOCK_LEVER`) | switch name; L cannot check it (locks not in the model) | `Column`, `NWS`, `RWS`, `RWK`, `NWK` | keep (D14: locks carry the switch tokens for now). The proposal changed the pins to `Column`, `WLS`, `WLK`, `NWK`, `RWK`, because FieldUnit encodes an electric lock as `WLS` (control) and `WLK` (office indication) (`WireCodec.h`); whether the field unit also sends `NWK`/`RWK` for a lock switch is unverified (request 12) |
| `PanelSignal` (`SIGNAL_LEVER`) | signal number; L matches plant signals | `Column`, `NGS`, `HS`, `SGS`, `SGK`, `NGK`, `TEK` | keep |

Levers have no fields beyond `Value`, `Role`, `Kind`. Pin names are function names; the generator
reads them through the drive bindings.

#### B2.5 Lamps: `PanelLamp-RED`, `PanelLamp-YELLOW`, `PanelLamp-BLUE` (Kind `LAMP`)

| Field | Today: default · reader | Proposed | Fact | Phase |
|---|---|---|---|---|
| `Value` | `OS` / `TRACK` · none | keep as a free label (KiCad requires a Value); no phase reads it | none | none |
| `Color` | per symbol · none | keep; library fact (P4). `layout-model.md` has `color` on lamps | lamp color | generator (CTC machine screen, simulator) |
| `IndicationToken` | `S` · CC, L | keep the name (D8); default empty (the `S` default goes). A comma-separated list of tokens; a bare track circuit name stands for its `K` token. Today the entries mix circuit names (`795T1`) and tokens (`MC1K`); both are valid. Proxy form `<interlocking>:<name>` for a foreign function. The proposal (rename to `OfficeIndications`, office indication names only) is withdrawn | the office indications OR'd onto this lamp | linker (resolve), generator |

#### B2.6 `PanelCode` (Kind `CODE`)

`Value` = `CODE` (label). Pins `Column`, `CODE`. Keep. Which field stations one button serves is the
ADR 0001 D9 question; it is not a symbol field.

#### B2.7 `PanelMCall` and `PanelAuxiliary` (Role `APPLIANCE`)

| Symbol · field | Today: default · reader | Proposed | Fact | Phase |
|---|---|---|---|---|
| `PanelMCall` `Value` | `MC1` · L (reported as unchecked) | keep: names the plant `MaintainerCall`; default empty | which call this lever sends | linker, generator |
| `PanelMCall` `ControlToken` | `${VALUE}S` · CC | remove (P1, P3: the function name follows from the Value) | none | none |
| `PanelMCall` `Vital` | `NO` · none | keep (D6). The proposal removed it because the class of a maintainer call is fixed | the class of the control | linker, generator |
| `PanelAuxiliary` `Value` | empty · none | keep: names the plant `AUXILIARY` | which auxiliary this lever sends | linker, generator |
| `PanelAuxiliary` `ControlToken` | `${VALUE}S` · CC | remove (P1, P3) | none | none |
| `PanelAuxiliary` `Vital` | `NO` · none | keep (D6). The proposal moved it to the plant `AUXILIARY` (B1.10; request 4) | the class of the control | linker, generator |

Why the proposal moved the class (not adopted; D6). The class says how the field unit processes a control (iteration 11). The
interlocking application must know it with no CTC machine drawn, for example for a tower operator or a
virtual target. One fact, one place: the plant symbol. The CTC machine does not need it. The class names
(vital, non-vital) come from FieldUnit ADR 0002 (control transaction classes).

#### B2.8 Code line: `CODELINE`, encoding symbol, transport symbol (replace `Codeline-MQTT`, `Codeline-CMRInet`)

Withdrawn proposal, kept as a record. ADR 0001 D13 and D15 (final form) decide the drawing (D9).

At the inventory `Codeline-MQTT` has `Value` `MQTT` (the transport), `Railroad` `SPCoast`, `Broker`, `Topic`
`ctc/${Railroad}/codeline/${Station}` and `Station` `${SHEETNAME}`. CC reads `Station`, `Broker` and
`Topic`, and also looks for `TopicRoot`, which no symbol has. `Codeline-CMRInet` has `Station` (`Node
UA`), `Port`, `Baud`. Neither has pins. (Both are gone from the library on 2026-10-03.)

Proposed drawing (ADR 0001 D13, D15). Three symbols for one code line:

| Symbol | Role | Pins | Value | Fields | Phase |
|---|---|---|---|---|---|
| `CODELINE` | `CODELINE` | 1 `ENCODING`, 2 `TRANSPORT` | empty (label) | `Address <field station>`, one per field station that has an authored address (e.g. `Address Luchessa`, `Address Gilroy`). Form open (request 6) | compiler records the addresses and checks them for duplicates; generator uses them, and fails for a target that needs one and does not find it |
| `Encoding` | `ENCODING` | 1 | the name of the encoding definition (`AAR-TOKENS`, `USS-506`; spelling unverified) | none. The definition file in the SPCoast KiCad repo holds the rules (ADR 0001 D10, D11) | compiler (resolves the name), generator |
| `Transport-MQTT` | `TRANSPORT` | 1 | `MQTT` (the transport definition) | `Broker`, `TopicRoot` (`ctc/SPCoast/codeline`) | compiler, generator |
| `Transport-CMRInet` | `TRANSPORT` | 1 | `CMRInet` | `Port`, `Baud`. The node UA is an address: it goes on `CODELINE` | compiler, generator |

Field by field from today:

| Today | Proposed | Reason |
|---|---|---|
| `Value` = transport | the transport symbol's Value | ADR 0001 D1, D15 |
| `Station` = `${SHEETNAME}` | remove | P1: on AAR tokens the field station is the interlocking; on a 506-style encoding it is the `MAIN HOUSE` Value. The generator derives it |
| `Station` = node UA (CMRInet) | `Address <field station>` on `CODELINE` | it is an authored address (ADR 0001 D4, D13) |
| `Topic` | remove | P3: the topic form is transport policy; the MQTT definition builds it from `TopicRoot` and the field station name (spaces to `-`) |
| `Railroad` | remove | P2: only `Topic` used it; title block comment 4 records the railroad |
| `Broker` | keep, on the transport symbol | transport parameter |
| `Port`, `Baud` | keep, on the transport symbol | transport parameters |

Placement (proposal). One `CODELINE` on each interlocking sheet of the CTC machine project, as today.
One encoding symbol and one transport symbol for each code line, on the root sheet, joined to every
`CODELINE` pin by a global label. The net then names the code line instance; `Broker` is written once
(P1). Today's rule ("same transport and same `Broker` = one instance") becomes a check. The alternative
is one encoding and one transport symbol on every sheet, with the instance derived as today (request 7).

A virtual target needs nothing drawn. A sheet with no `CODELINE` is valid. The `VIRTUAL` default in CC
goes.

#### B2.9 Place for the other operator roles

- Dispatcher: `CtcMachine`, `Kind` = `DISPATCHER`. The only role drawn.
- Tower operator: reserved as Role `MACHINE`, `Kind` = `TOWER_OPERATOR` (direct to a locking bed, no
  code line). Where it is drawn (plant project or its own project) is not designed.
- Maintainer: reserved `Kind` = `MAINTAINER` (maintenance or debug mode, without the interlocking). Not
  designed. Fascia devices and service modes have their own ADR (ADR 0001, still open item 4).

See Consequences, "Operator roles".

### B3. What names the interlocking

Today: `--plant-name` on the command line, else the file stem; the folder name for membership; the
sheet name on the CTC machine side. The sources disagree (as of 2026-10-01, changed by the owner on
2026-10-02, to be re-checked). GilroyCalTrain: folder `GilroyCalTrain`, title `Gilroy Caltrain Station`,
desk sheet `Gilroy CalTrain`, `NextCP` in GilroyInterchange `Gilroy Caltrain`. GilroyInterchange: folder
and title `GilroyInterchange`, desk sheet `Gilroy Interchange`. The linker pairs them today by removing
whitespace, a rule that ADR 0001 D12 (amended) withdraws.

The options as proposed:

| Option | What is drawn | Cost |
|---|---|---|
| A. `INTERLOCKING` symbol | One symbol, Role `INTERLOCKING`, no pins, in each plant project. Value = the name; it may display `${TITLE}` | A new library symbol; 6 placements. Exactly one per plant project, else an error. Symmetric with `MAIN HOUSE`. Works for one or several control points. The name is free of file system limits. The desk sheet name must equal it (case folded) |
| B. Field on `MAIN HOUSE` | `Interlocking` = name on every `MAIN HOUSE`, or a flag on one | No new symbol; a script can add the field. On every house: N copies of one fact (P1), all must agree. On one house: moving or deleting that house loses the name. With one control point the field repeats or differs from the Value for no reason |
| C. Title block | The compiler reads `title` (already parsed into `document.title`) | No drawing change except fixing titles. A title is prose for print (`Gilroy Caltrain Station`), not a name, and it is not visible as a model fact. Close to what the owner rejected for `MAIN HOUSE` |

Recommendation: A. Under all options the desk side keeps the sheet name as the join, and the linker
compares names with case folded and spaces replaced by `-` only. Decided: A (D1).
