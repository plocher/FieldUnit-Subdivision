# Three maps: where every key of the Layout Data Model File goes, 2026-10-27

Draft for the owner. Input to ADR 0011's reshape of the schema (§9). No code, schema or test changes here.

**Ruled by the owner 2026-10-27.** Every decision is closed; each one in "Decisions" below carries its ruling. D10 was
replaced (geometry keeps its own shape and joins the semantic sections by identity only), D5 and D15 were extended or
narrowed, and the rest were accepted as their defaults. The rows below are written to the rulings.

## Purpose

ADR 0011 gives every entity and row three maps: `given`, `relations`, `derived`. This document takes every key the
file holds today (schema `layout-model/v3.1.0`, example `schemas/layout-model/examples/spcoast.layout.json` at
Railroad `96c6b4e`) and assigns it to one map, or drops it with the reason. Where the assignment needs a choice the
ADRs do not make, the choice is listed once, in "Decisions pending", with a default. The source of each key is cited
by the KiCad importer's function (`tools/layout_compiler/`), so the reshape moves code knowingly. Where a ruling
changed a row, the row is rewritten; "Decisions" keeps the question, the ruling and the original default.

## Rules applied

By reference; not restated.

| Rule | Source |
|---|---|
| `given`: every stated field, keyed as drawn, string values; out: KiCad housekeeping and the key field | ADR 0011 §2; GLOSSARY §2.6 |
| `relations`: every stated connection, as the qualified name it reaches; hierarchy is not stated | ADR 0011 §2 |
| `derived`: what the rules compute; never a copy of a stated value under another form | ADR 0011 §2, §3 |
| Reader precedence `derived`, `relations`, `given` | ADR 0011 §4 |
| The Studio test | ADR 0011 §1; ADR 0008 R3 |
| Functional model only; KiCad mechanisms only in the importer; pin names do not carry meaning | ADR 0012 §2, §8 |
| No fallbacks: the seven implicit forms retire; every derivation stays | ADR 0012 §4 |
| Geometry always; geometry joins the semantic sections by identity only (D10, ruled 2026-10-27) | ADR 0011 §7 |

Legend for the `map` column:

- **given / relations / derived**: the key moves into that map under `new key`.
- **dropped**: the key goes; the reason is in `note`.
- **structure**: not a fact of the entity: the schema string, an identity (a map key or a row's `name`), a collection,
  or a file-level block. It stays outside the three maps.
- `new key` written `given.X` keeps the drawn field name `X` exactly (spaces included: `given."CP Name"`).
- A row with current key `—` is a field or wire that is stated today but not written; it enters the file.
- `Dn` points to "Decisions".

## 1. Layout (`$defs/layout`)

| current key | map | new key | comes from | note |
|---|---|---|---|---|
| `schema` | structure | `schema` | importer constant (`emit.SCHEMA`) | top level, unchanged |
| `layout.name` | structure | `layout.name` | Railroad symbol `Name` (`seams._railroad`) | the key field: `SPCoast` |
| `railroad` | given | `given.Railroad` | field (`_railroad`) | `Southern Pacific`; ADR 0012 §6 looks reference data up by it |
| `region` | given | `given.Region` | field (`_railroad`) | `Coast Line` |
| `era` | given | `given.Era` | field (`_railroad`) | `1960+` |
| `rulebook` | given | `given.Rulebook` | field (`_railroad`) | `GCOR` |
| `settings` | given | `given.<field>` | any other Railroad field | never written today (`_railroad` reads five fields only) |
| `description` | dropped | — | `Description` | KiCad housekeeping (ADR 0011 §2) |
| — | given | `given.Kind` | Railroad `Kind` = `RAILROAD` | D1 |
| `transports`, `codelines`, `ioEncodings`, `processors` | structure | same | collections | |
| `glyphs` | structure | `glyphs` | `geometry.read` | D4 |

## 2. Transports, CMRInet Nodes and their bits

### 2.1 Transport (`$defs/transport`), e.g. `MQTT`

| current key | map | new key | comes from | note |
|---|---|---|---|---|
| map key | structure | map key | `Name` (`key_of`) | one entity over every placement (ADR 0012 §2) |
| `kind` | given | `given.Kind` | field (`_transports`, `s.kind`) | `MQTT`; typed copy dropped; D1 |
| `settings.Broker`, `.Port`, `.Baud` | given | `given.Broker`, `given.Port`, `given.Baud` | fields (`settings_of`) | merged over placements; a conflict stays an error |
| `anchors` | relations | `relations.anchors` | `Processor` wire of each placement (`_anchor_of`) | `MQTT`: `Gilroy`, `JohnCTC`. The `Processor` field and code line forms retire (ADR 0012 §4); a drawn `Processor` field stays in `given`, read by nothing |
| `nodes` | structure | `nodes` | collection keyed by UA | |
| `description` | dropped | — | `Description` | housekeeping |

### 2.2 CMRInet Node (`$defs/cmrinetNode`), e.g. `CMRInet` node `30`

| current key | map | new key | comes from | note |
|---|---|---|---|---|
| map key (UA) | structure | map key | `Address` field (`_nodes`) | D11 |
| (its place under a transport) | structure | container | `Transport` wire (`_transport_on_net`) | the container is the relation (D12); the `Transport` field form: D13 |
| `ic` | given | `given.IC` | field | `CMRI` |
| `nodeType` | given | `given.NodeType` | field | `C` |
| `inputBytes` | given | `given.InputBytes` | field, parsed to int today | `"2"`; the int is a copy, dropped; the bytes-cover-bits check stays a rule |
| `outputBytes` | given | `given.OutputBytes` | field, parsed to int today | `"3"`; as above |
| `bits` | structure | `bits` | collection | |
| `description` | dropped | — | `Description` | housekeeping |
| — | given | `given.Transport` | field, when drawn | read by nothing (D13) |

### 2.3 Bit (`cmrinetNode.bits`, `$defs/driver`), e.g. `IB.1`

| current key | map | new key | comes from | note |
|---|---|---|---|---|
| map key `IB.n` / `OB.n` | structure | map key | computed: `Bit` field plus the direction of pin D (`_drivers`) | a computed key; the direction is a library pin fact (D11) |
| (its place under a node) | structure | container | `IOBus` wire to the node (`_bus_owner`) | "the one CMRInet Node on the sheet" retires (ADR 0012 §4) |
| `ic` | given | `given.IC` | field | `CMRI` |
| `settings` | given | `given.<field>` | fields | none in SPCoast |
| — | given | `given.Bit` | field | `"1"` |
| — | given | `given.Node` | field, when drawn | read by nothing (D13) |

## 3. Code lines and I/O encodings (`$defs/encodingInstance`)

Same shape in `codelines{}` (`AAR Tokens`, `US&S 506`) and `ioEncodings{}` (`CMRInet`, `JMRI`).

| current key | map | new key | comes from | note |
|---|---|---|---|---|
| map key | structure | map key | `Name` | |
| `encoding` | given | `given.Kind` | field `Kind` (`_encodings`, `s.kind`) | `AAR`; the typed key renamed a stated field; dropped |
| `transport` | relations | `relations.transport` | `Transport` wire (`_transport_on_net`) | `MQTT`. The field and by-layout forms retire (ADR 0012 §4) |
| `processor` | relations | `relations.processor` | the `Processor` wire of the transport placement on the encoding's `Transport` net (`_encodings`) | `JohnCTC`; D7 |
| `settings.Topic`, `.Version`, `.Chart`, ... | given | `given.Topic`, ... | fields, macros expanded (`expand_macros`) | `ctc/SPCoast/codeline/`; expansion is the importer's (GLOSSARY §2.6) |
| `description` | dropped | — | `Description` | housekeeping |
| — | given | `given.ControlBytes`, `given.IndicationBytes` | fields on `Encoding-Bits` | not used in SPCoast |

## 4. Processors and drivers

### 4.1 Processor (`$defs/processor`), e.g. `Christopher`

| current key | map | new key | comes from | note |
|---|---|---|---|---|
| map key | structure | map key | `Name` | one entity over every placement |
| `board` | given | `given.Board` | field (`_processors`) | `cpNode-Xiao`; typed copy dropped |
| `drivers` | structure | `drivers` | collection | |
| `settings` | given | `given.<field>` | fields | none in SPCoast |
| `description` | dropped | — | `Description` | housekeeping; `_processors` reads it today for a conflict check, which goes |
| — | given | `given.Kind` | `PROCESSOR` | D1 |

### 4.2 Driver (`$defs/driver`), e.g. `Christopher` `0x20`, `Gilroy` `LIGHT.MC1`

| current key | map | new key | comes from | note |
|---|---|---|---|---|
| map key | structure | map key | `Address` field; for an encoded driver computed as `Kind.served` (`_encoded_address`) | D11 |
| (its place under a processor) | structure | container | `IOBus` wire (`_bus_owner`) | "one Processor on the sheet" and the `Processor` field retire (ADR 0012 §4) |
| `ic` | given | `given.IC` | field | `MCP23017` |
| `kind` | given | `given.Kind` | field | `LIGHT`; D1 |
| `settings` | given | `given.<field>` | fields (`settings_of`) | `frequency_hz`, `min_us`, `max_us` |
| `description` | dropped | — | `Description` | housekeeping |
| — | given | `given.Address` | field on an encoded driver, when drawn | the override of the computed key (ADR 0008 §4.5) |
| — | given | `given.Processor` | field, when drawn | read by nothing |

## 5. Interlockings and the FieldUnit

### 5.1 Interlocking (`$defs/interlocking`), e.g. `Luchessa`

| current key | map | new key | comes from | note |
|---|---|---|---|---|
| map key | structure | map key | `Name` | |
| `codeline` | relations | `relations.codeline` | `Codeline` wire to an encoding's `Codeline` net (`_codeline_of`) | `US&S 506`; the folder form retires (ADR 0012 §4) |
| `settings` | given | `given.<field>` | fields | none in SPCoast |
| `description` | dropped | — | `Description` | housekeeping |
| — | given | `given.Kind` | `INTERLOCKING` | D1 |
| `fieldUnit` | structure | see 5.2 | | D14 |
| `houses`, `appliances`, `track`, `devices`, `geometry` | structure | same | collections | |

### 5.2 FieldUnit (`$defs/fieldUnit`)

| current key | map | new key | comes from | note |
|---|---|---|---|---|
| `fieldUnit.processor` | relations | `relations.processor` on the interlocking | the Interlocking symbol's `Processor` wire (`_anchor_of`) | `Luchessa`; "one Processor on the sheet" retires; D14 |
| `fieldUnit.settings` | dropped | — | no source symbol | never written; the FieldUnit is declared by the Interlocking symbol |
| `fieldUnit.description` | dropped | — | none | housekeeping |

## 6. Houses (`$defs/house`), e.g. `Luchessa:Gilroy`

| current key | map | new key | comes from | note |
|---|---|---|---|---|
| map key | structure | map key | `CP Name` (`KEYS`) | |
| (its place under an interlocking) | structure | container | sheet hierarchy (`_unit_of_sheet`) | a namespace member (ADR 0012 §2) |
| `milepost` | given | `given.Milepost` | field (`milepost_of`) | `"79.5"`; the number is a copy, dropped (ADR 0011 §2); the schema checks numeric text |
| `maintainerCall` | relations | `relations.maintainerCall` | `MC` wire (`_houses`) | `Luchessa:MC1`; D8 |
| `settings` | given | `given.<field>` | fields | none in SPCoast |
| `description` | dropped | — | `Description` | housekeeping |
| — | given | `given.Kind` | `CONTROL_POINT` | D1 |
| — | relations | `relations.codeline` | `Codeline` wire, when drawn (`_houses`) | read today, never written |

## 7. Appliances (`$defs/appliance`)

### 7.1 Every appliance

| current key | map | new key | comes from | note |
|---|---|---|---|---|
| map key | structure | map key | `Name` | `783` |
| `appliance` | given | `given.Appliance` | field (`trackplan._plan`) | `switch`; D1 |
| `style` | given | `given.Style` | field | `powered`; D1 |
| `milepost` | given | `given.Milepost` | field (`milepost_of`) | Sargent `HBA`: `"83.4"`; number dropped |
| `controlPoint` | derived | `derived.controlPoint` | propagation (`_control_points`) | `Luchessa:Luchessa`; the stated `CP` stays in `given.CP` |
| `settings` | given | `given.<field>` | fields (`settings_of`) | |
| `description` | dropped | — | `Description` | housekeeping |
| — | given | `given.CP` | field | stated on few appliances; the root of propagation |

### 7.2 Switch and derail (`appliance: switch`), e.g. `Luchessa:783`, `Luchessa:795D`

| current key | map | new key | comes from | note |
|---|---|---|---|---|
| `osCircuit` | derived | `derived.osCircuit` | the circuit at its ports (`_plan`) | `Luchessa:783T1` |
| `indicationCeiling` | given | `given.IndicationCeiling` | field | `RESTRICTING/RESTRICTING`; typed copy dropped |
| — | given | `given.TC` | field | library default `${VALUE}T1` (D16); a comma list is still the held `switch.tc_block` question |
| — | relations | `relations.C`, `.N`, `.R` (a derail `.C`, `.R`) | the wire at each port | D5 |

### 7.3 Mast, e.g. `Luchessa:784EAB`

| current key | map | new key | comes from | note |
|---|---|---|---|---|
| `heads` | structure | `heads.<letter>` | trackplan heads on the mast's `H*` pins (`trackplan._heads`) | D9 |
| `heads.<letter>.style` | given | `heads.<letter>.given.Style` | the head's field | `CPL` |
| — | relations | on the signal joint's row | `SIGNAL` wire | a mast cannot name a row; the joint holds it (8.1) |

### 7.4 Track circuit (`appliance: track_circuit`), e.g. `Luchessa:1SAT`, `Watsonville:0100T`

| current key | map | new key | comes from | note |
|---|---|---|---|---|
| `members` | derived | `derived.members` | `IndicationToken` split and qualified (`_plan`) | virtual circuits only; a resolution, not a copy |
| `settings.Display` | given | `given.Display` | field | `0100T: [15T1,...]` |
| — | given | `given.IndicationToken` | field | |
| — | relations | `relations.TC` | the wire at its `TC` pin | D5 |

### 7.5 Lamp and maintainer call (`appliance: lamp`), contact

| current key | map | new key | comes from | note |
|---|---|---|---|---|
| — | relations | `relations.house` | `MC` wire | `Gilroy Interchange:MC1` → `Gilroy Interchange:Gilroy North` (ADR 0011 §2); D8 |
| (contact) | — | — | — | no contact in SPCoast; same rows as 7.1 |

## 8. Track rows (`$defs/trackplan`, `$defs/trackSymbol`)

Each row holds the three maps; a row with a key field keeps it as `name` (D20). Every row of joints, ends and policy
signs also carries `id`, a stable opaque identity outside the maps (D10): by default the KiCad per-instance UUID of
its symbol (the netlist's component `tstamps`, which is the `.kicad_sch` symbol `uuid`). Geometry's markers and runs
reference the row by it. Pin names are translated by the KiCad importer into side names (D15); no library pin is
renamed.

### 8.1 Joints (`track.joints[]`): `IRJ` (56), `IRJ_SIGNAL` (35)

| current key | map | new key | comes from | note |
|---|---|---|---|---|
| `kind` | given | `given.Kind` | field | D1 |
| `circuits.A`, `.B` (signal joint) | derived | `derived.circuits.governed`, `.approach` | union of nets (`_plan`) | ADR 0012 §8: A is governed, B is approach. `Luchessa:784EAB`'s joint: governed `783T1`, approach `1SAT` |
| `circuits.A`, `.B` (plain joint) | derived | `derived.circuits.A`, `.B` | union of nets | neutral sides kept (ADR 0012 §8) |
| `ports` | relations | `relations.approach`, `.governed` (signal joint); `relations.A`, `.B` (plain joint) | the pin's own net (`pin_refs`) | D5; the importer translates `B` to approach and `A` to governed (D15, ADR 0012 §8) |
| `mast` | relations | `relations.mast` | `SIGNAL` wire | `Luchessa:784EAB` |
| `controlPoint` | derived | `derived.controlPoint` | propagation | `given.CP` stays |
| — | given | `given.CP` | field on `IRJ-Signal` | |

### 8.2 Ends (`track.ends[]`): `NEXT_CP` (18), `INDUSTRY` (5), `END_CTC` (3), `BUMPER` (3)

| current key | map | new key | comes from | note |
|---|---|---|---|---|
| `kind` | given | `given.Kind` | field | D1 |
| `name` | structure | `name` | `Name`, qualified (`_plan`) | an industry only; D20 |
| `circuits.To`, `.CTC`, `.EoT` | derived | `derived.circuits.<side>` | union of nets | NextCP `To` becomes `track`; `END_CTC` `CTC`/`DARK` and `EoT` stay; D15 |
| `ports` | relations | `relations.<side>` | the pin's own net | `END_CTC` `DARK` → `Corporal:1.C`; NextCP `track`; D5 |
| `interlocking` | given | `given.Interlocking` | field | `Corporal`; may name an interlocking beyond the layout (`Lick`), so it is no resolved relation; typed copy dropped |
| — | derived | (none today) | NextCP pairing (`_pair_next_cps`) | checked, never written; adding it is a MINOR change (ADR 0012 §7) |

### 8.3 Policy signs (`track.policies[]`): `RULE_251`, `RULE_261`, `RULE_105`, `RULE_93`

| current key | map | new key | comes from | note |
|---|---|---|---|---|
| `kind` | given | `given.Kind` | field | D1 |
| `direction` | given | `given.Direction` | field | `RIGHT`; typed copy dropped; library default `BOTH` (D16) |
| `circuits.To`, `.Track` | derived | `derived.circuits.track` | union of nets | one meaning, two pin names: `Track` on `RULE_261`, `To` on the rest, both translated to `track` by the importer; D15 |
| `ports` | relations | `relations.track` | the pin's own net | D5, D15 |

### 8.4 Links and mileposts

| current key | map | new key | comes from | note |
|---|---|---|---|---|
| `track.links[]` (`ports`, `circuit`) | derived | `track.links[].derived` | two switch ports on one net (`_plan`) | `Luchessa:795.R` + `795D.R`; computed from the ports' relations (D5); ADR 0012 §4 |
| `track.mileposts[]` | dropped | — | milepost names (`_plan`) | the key set of `geometry.mileposts`, which is always written (ADR 0011 §7) |

## 9. Devices and bindings (`$defs/device`, `$defs/binding`)

Rows under `interlockings.*.devices[]` (193) and `officeUnits.*.devices[]` (75). A row has no identity (ADR 0008 §4.5),
so its `Name` is not a map key and lands in `given`.

| current key | map | new key | comes from | note |
|---|---|---|---|---|
| `type.appliance` | given | `given.Appliance` | field (`_devices`) | `lamp`; D1 |
| `type.style` | given | `given.Style` | field, split and sorted today (`styles_of`) | `"powered,lock,dual"` as drawn; the list is a copy, dropped (D17) |
| `serves` | derived | `derived.serves` | `given.Name` qualified by the scope; a head's `relations.mast` | `Christopher:MC1`; D3 |
| `head` | given | `given.Head` | field | `A` |
| `shows` | derived | `derived.shows` | `IndicationToken` qualified by the column's interlocking or the folder (`_devices`) | `Corporal:829T1`; D6 |
| `column` | relations | `relations.column` | `Column` wire (`_devices`) | `12`; D19 |
| `address` | given | `given.Address` | field | a pixel index, `"1"` |
| `settings` | given | `given.<field>` | fields (`settings_of`) | `hold_ms`, `Color`, `settle_ms`, `*_deg` |
| `bindings[]` | relations | `relations.bindings` | each pin's wire to a driver pin (`_driver_route`) | D3 |
| `bindings[].function` | relations | key of `relations.bindings` | the device pin name, `~{}` removed (`base`) | `LAMP`; no device in SPCoast binds one function twice |
| `bindings[].route` | relations | value of `relations.bindings` | driver's owner, key and pin | `Christopher/0x23/A2`; an encoded driver's key is computed (D11) |
| `bindings[].invert` | dropped | — | `Invert` field | a per-pin copy of `given.Invert` |
| `description` | dropped | — | `Description` | housekeeping |
| — | given | `given.Name` | field | names the appliance served; on a code lever a label (`serves` is cleared today) |
| — | given | `given.Invert`, `given.IndicationToken` | fields | |
| — | relations | `relations.mast` | a head device's `IND` wire to a Mast device | today folded into `serves` |
| — | — | `Pin.*` | library contract fields | D2 |

## 10. Office units and columns

### 10.1 OfficeUnit (`$defs/officeUnit`), `SPCoast South`

| current key | map | new key | comes from | note |
|---|---|---|---|---|
| map key | structure | map key | `Name` | |
| `style` | given | `given.Style` | field (`_office_units`) | `US&S`; D1 |
| `processor` | relations | `relations.processor` | `Processor` wire (`_anchor_of`) | `JohnCTC`; "one Processor on its sheet" retires |
| `columns`, `devices` | structure | same | collections; membership by "the one OfficeUnit" (`_columns`, `_devices`) | D6 |
| `geometry` | structure | `geometry` | none | open and empty (ADR 0010 §4.8) |
| `settings` | given | `given.<field>` | fields | none in SPCoast |
| `description` | dropped | — | `Description` | housekeeping |

### 10.2 Column (`$defs/column`), e.g. `5`, `12`

| current key | map | new key | comes from | note |
|---|---|---|---|---|
| map key | structure | map key | `Column` (`KEYS`) | |
| `house` | derived | `derived.house` | `given."CP Name"` resolved (`_house_by_cp`) | `Luchessa:Luchessa`; 3 of 14 columns state it |
| `interlocking` | relations | `relations.interlocking` | the folder (`_unit_of_sheet`) | 11 of 14 columns; written today only when `house` is absent; D6 |
| — | derived | `derived.interlocking` | from `derived.house` | today omitted when `house` is present |
| — | given | `given."CP Name"` | field | |
| `settings` | given | `given.<field>` | fields | none |
| `description` | dropped | — | `Description` | housekeeping |

## 11. Geometry (`$defs/geometry`, `placement`, `track`, `marker`, `glyph`)

Ruled 2026-10-27 (D10 replaced): geometry stays an independent section that can evolve on its own. Its only contract
with the semantic sections is identity: it references semantic things by identity and never copies their facts. Named
things are keyed by railroad name already; track rows are referenced by their `id` (§8). Nothing else about
geometry's internal shape changes in this step.

| current key | map | new key | comes from | note |
|---|---|---|---|---|
| `geometry.appliances`, `.houses`, `.mileposts` keys | structure | same | names | join to the entity by name (ADR 0010 §4.5) |
| placement `at`, `glyph`, `rotation`, `mirror` | structure | unchanged | page position, anchor moved to the bottom-left pin, frame translated (`geometry._interlocking`); `lib_id` | geometry's own shape, unchanged (D10) |
| placement `heads.<letter>` | structure | nested placement | head's `M` wire to the mast | as 7.3 |
| `track[].points` | structure | unchanged | wires chained (`chain`) | |
| `track[].circuit` | derived | `track[].derived.circuit` | `circuit_of_net` | ADR 0011 §7 |
| `track[].from`, `.to` | relations | `track[].relations.from`, `.to` | the switch port or the track row pin a run's end meets | D5 extended: a switch port by name (`Luchessa:783.R`), a track row pin by the row's `id` and its side (`<id>.governed`). The importer may use grid positions at ingest to find the pin; it records the connection, never a position-derived fact |
| `markers[].kind` | dropped | — | `Kind` | a copy of the track row's `given.Kind`; D10 |
| — | structure | `markers[].row` | the track row's `id` | the one join key (D10) |
| `markers[].at`, `.glyph`, `.rotation`, `.mirror` | structure | unchanged | placement | D10 |
| `markers[].circuits`, `.name`, `.ports` | dropped | — | copies of the track row's facts (`row_of`) | join keys only; D10 |
| `layout.glyphs.*.ports`, `.shape` (`primitive`; `stroke` width, type; `fill` type, color, opacity) | structure | unchanged | the symbol library (`glyph_of`) | library pictures, not instance facts; D4 |

## 12. Provenance (`$defs/provenance`)

| current key | map | new key | comes from | note |
|---|---|---|---|---|
| `sourceType` | structure | same | constant `KiCad` | file level; no maps |
| `compiler.name`, `.version` | structure | `writer.name`, `.version` | `emit.COMPILER` | D18 |
| `source.path`, `.describe` | structure | same | git (`emit._source`) | |
| `libraries` | structure | same | git of each library (`_Project.version`) | |
| `referenceData` | structure | same | `seams.REFERENCE_DATA` | |
| — | structure | `rules` | the derivation's version | ADR 0011 §3 item 3, ADR 0012 §7 |

## 13. Value types and `settings`

`name`, `qualifiedName`, `layoutName`, `route`, `namedMap`, `portRef`, `coordinate`, `point`, `polyline`, `glyphKey`,
`primitive`, `stroke`, `fill` are value types, not entities: unchanged, used inside the maps. `settings` goes; every key
it held moves to `given` under the same name.

## 14. Typed keys that hold a stated fact

Each is the drawn field under another name, often another type. Rule: the field moves to `given` as drawn; the typed
key is dropped; a reader that wants a number or a list parses `given` (ADR 0011 §2).

| typed key today | where | drawn field | value today → in `given` |
|---|---|---|---|
| `milepost` | house, appliance | `Milepost` | `81.3` → `"81.3"` |
| `kind` | transport, driver, track row, marker | `Kind` | unchanged text |
| `encoding` | code line, I/O encoding | `Kind` | `AAR` → `given.Kind` |
| `appliance`, `type.appliance` | appliance, device | `Appliance` | unchanged text |
| `style` | appliance, OfficeUnit, head | `Style` | unchanged text |
| `type.style` | device | `Style` | `["dual","lock","powered"]` → `"powered,lock,dual"` as drawn |
| `board` | processor | `Board` | unchanged text |
| `ic` | driver, bit, CMRInet Node | `IC` | unchanged text |
| `nodeType` | CMRInet Node | `NodeType` | unchanged text |
| `inputBytes`, `outputBytes` | CMRInet Node | `InputBytes`, `OutputBytes` | `2` → `"2"` |
| `indicationCeiling` | switch | `IndicationCeiling` | unchanged text |
| `direction` | policy sign | `Direction` | unchanged text |
| `interlocking` | NextCP | `Interlocking` | unchanged text |
| `head` | head device | `Head` | unchanged text |
| `address` | device | `Address` | unchanged text |
| `invert` | binding | `Invert` (on the device) | `true` per pin → the device's list as drawn |

The other typed keys are not stated fields: they move to `relations` (`anchors`, `transport`, `processor`, `codeline`,
`maintainerCall`, `mast`, `column`, `ports`, `bindings`) or `derived` (`controlPoint`, `osCircuit`, `members`,
`circuits`, `serves`, `shows`, `house`, `links`, a run's `circuit`, `from`, `to`).

## Decisions

One line each: the question, the default, the reason, and the owner's ruling of 2026-10-27.

1. **`Role`, `Kind`, `Appliance`, `Style`.** Default: `Role` is left out of `given` (it only picks the collection, a
   KiCad mechanism, ADR 0012 §2); `Kind`, `Appliance` and `Style` stay in `given` on every entity, even where the
   collection implies them. Reason: Studio needs them inside one collection (switch or mast, `IRJ` or `IRJ_SIGNAL`,
   `MQTT` or `CMRI`), and one rule beats per-collection exceptions.
   **Ruling: accepted.**
2. **`Pin.*` fields.** Default: library facts, left out of `given`; they belong with the device definitions in
   reference data. Reason: identical on every instance; no instance can change a pin's signal type.
   **Ruling: accepted** (group B).
3. **A device row's `serves` and `bindings`.** Default: `serves` is `derived` (from `given.Name` and the scope, or a
   head device's `relations.mast`); `bindings` is `relations`, a map from function to route; `invert` dropped for
   `given.Invert`. Reason: the wire to a driver pin is stated; `serves` needs the namespace resolved.
   **Ruling: accepted** (group B).
4. **Geometry rows and the three maps.** Default: placements and runs take them (a placement `given` only, typed
   values allowed in geometry; a run `given.points` plus `derived`); glyphs and provenance take none. Reason: ADR 0011
   §7 asks for the maps on geometry's rows; a glyph is a library picture and provenance is about the file.
   **Ruling: accepted** (group B), as far as D10's replacement leaves it: glyphs and provenance take no maps; a
   run's `circuit` is `derived` and its ends are `relations` (D5); placements keep geometry's own shape (D10).
5. **Stated track connectivity.** Default: each track pin of each trackplan entity and row carries `relations.<pin>`,
   the named pins its wire reaches (today's `ports`, plus a track circuit marker's `TC`), so `derived` holds only
   `circuits`, `osCircuit`, `links` and the chains. Reason: the reference derivation must recompute these from stated
   facts (ADR 0011 §3 item 2), and today the file carries only results; ADR 0011 §2 lists `ports` as derived, but
   `pin_refs` reads only the pin's own net, a stated wire. Track joining only unnamed rows (dark track between two
   joints) has no stated form and is reported `missing`.
   **Ruling: accepted and extended.** Each track pin's wire is `relations.<pin>`; `derived` holds only what is
   computed. A run's ends are relations too: `from`/`to` name the switch port or the track row they meet. The importer
   may use KiCad grid positions at ingest to find them, but records the connection, never a position-derived fact. A
   signal joint's relations use `approach` and `governed`, like its circuits.
6. **Membership implied only by the sheet hierarchy.** Default: where no container states it, the KiCad importer
   writes it as `relations.interlocking` (11 columns; the 34 board lamps whose `shows` scope is their folder), and
   "the one OfficeUnit of the layout" becomes the container. Reason: a fact only the importer can see must be input
   to the derivation, not output (ADR 0011 §3 items 2 and 4); ADR 0011 §2's "resolved into `derived`" needs this
   amendment.
   **Ruling: accepted.**
7. **An encoding's processor.** Default: `relations.processor`, written by the KiCad importer from the transport
   placement the encoding is wired to. Reason: the model merges placements into one transport (ADR 0012 §2), and
   `MQTT` has two anchors, so no rule can recover which one.
   **Ruling: accepted** (group B).
8. **A wire between two named entities (a house's `MC` and a maintainer call).** Default: each holder writes its own
   end: `house.relations.maintainerCall` and `MC1.relations.house`; the suite checks they agree. Reason: each
   entity reads complete in an editor; one-sided storage needs a tie-break rule.
   **Ruling: accepted** (group B).
9. **A mast's heads.** Default: `heads.<letter>` are entities nested under the mast, each with its own `given`
   (`Style`); no `derived.heads`. Reason: a head's `Style` is stated on the head; a `derived` copy would break
   ADR 0011 §2.
   **Ruling: accepted** (group B).
10. **Geometry markers.** Default: fold each marker's placement into its track row and drop `markers[]` with its join
    keys. Reason: one symbol, one row; the join by derived `circuits` and `ports` copies facts and is ambiguous where
    two rows share them.
    **Ruling: replaced.** Geometry stays an independent section that can evolve on its own; its only contract with
    the semantic sections is identity: it references semantic things by identity and never copies their facts. Track
    rows (joints, ends, policy signs, links if drawn) gain a stable opaque `id`, by default the KiCad per-instance UUID
    of the symbol. `markers[]` reference their row by that id; the copied `kind`, `circuits`, `name` and `ports` go.
    Runs reference ports and rows by name or id. Nothing else about geometry's internal shape changes now.
11. **Keys from `Address`, and computed keys.** Default: `Address` is the key field of a driver and a CMRInet Node
    (left out of `given`); a bit's `IB.n` and an encoded driver's `Kind.served` stay computed map keys. Reason: today
    `KEYS` does not name `Address`, so the rule would write it twice; a computed key is the identity ADR 0008 §4.5
    already chose.
    **Ruling: accepted** (group B).
12. **Containers that encode a stated relation** (driver under processor, bit under CMRInet Node, CMRInet Node under
    transport). Default: the container is the relation; no copy in `relations`. Reason: the key is unique only within
    its owner, so the owner is part of the identity.
    **Ruling: accepted** (group B).
13. **A CMRInet Node's `Transport` field and a bit's `Node` field.** Default: they retire as forms with the seven of
    ADR 0012 §4 and stay in `given`, read by nothing. Reason: same pattern as the `Processor` field; the wires resolve
    every one in SPCoast.
    **Ruling: accepted** (group B).
14. **The `fieldUnit` wrapper.** Default: flatten to the interlocking's `relations.processor`. Reason: it holds one
    relation and no symbol states anything else for it.
    **Ruling: accepted** (group B).
15. **Side names that are pin names** (policy `To` and `Track`; NextCP `To`; END CTC `CTC`, `DARK`; industry `EoT`).
    Default: one name per meaning, `track` for every policy sign and NextCP; `CTC`, `DARK`, `EoT` kept as functional.
    Reason: one fact under two pin names is the library leaking (ADR 0012 §8).
    **Ruling: accepted, with no library pin renames.** The KiCad importer translates pin names into functional
    names: a policy sign's and a NextCP's `To`/`Track` become `track`; a signal joint's `A`/`B` become
    `governed`/`approach`; `CTC`, `DARK` and `EoT` stay.
16. **Library defaults in `given`** (`TC = ${VALUE}T1`, `Direction = BOTH`). Default: `given` holds the instance's
    value whatever its source. Reason: the netlist cannot tell a default from a statement; Studio will state them.
    **Ruling: accepted** (group B).
17. **Multi-valued fields** (`Style` on a device, `Invert`, `IndicationToken`, `TC`). Default: as drawn, one string;
    no parsed copy except a resolved one in `derived` (`members`, `shows`). Reason: `given` is the person's text;
    a sorted list is a copy.
    **Ruling: accepted** (group B).
18. **`provenance.compiler`.** Default: rename to `writer`. Reason: Studio is a writer too, and GLOSSARY §11 retires
    "compiler" alone.
    **Ruling: accepted** (group B).
19. **A reference to a column.** Default: qualified with the OfficeUnit, `SPCoast South:12`, and `qualifiedName`
    widened to OfficeUnit namespaces. Reason: ADR 0008 §4.5 always qualifies; ADR 0012 §2 makes the OfficeUnit a
    namespace.
    **Ruling: accepted.**
20. **A row with a key field** (an industry). Default: `name` stays on the row, outside the maps, as its identity.
    Reason: the key field never lands in `given` (ADR 0011 §2), and ports reference it (`Luchessa:Gilroy Industry.EoT`).
    **Ruling: accepted** (group B).
21. **Empty fields.** Default: an empty field or KiCad's `~` is not stated and is left out of `given`. Reason: KiCad
    writes every library field on every instance; `key_of` already reads `~` as none.
    **Ruling: accepted** (group B).

## ADR amendments implied

Not edited here; each waits for its own change to the ADR.

- ADR 0011 §2: a track pin's wire is a stated relation, `relations.<pin>` (today's `ports`), not `derived` (D5); a
  run's ends are relations (D5 extended); membership implied only by the sheet hierarchy is written by the KiCad
  importer as `relations.interlocking`, not resolved into `derived` (D6).
- ADR 0008 §4.5: a row may carry a stable opaque `id` (track rows: joints, ends, policy signs), by default the KiCad
  per-instance UUID of its symbol; a row still has no name (D10).
- ADR 0010 C6: geometry's markers join their track row by `id`, not by kind, circuits, name or ports (D10).
