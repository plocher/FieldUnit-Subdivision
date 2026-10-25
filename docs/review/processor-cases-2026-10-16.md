# Processors on the sheet: the cases (2026-10-16, rev 1)

- Status: a companion to `layout-model-view-2026-10-16.md` §4.5, written for the owner's question of 2026-10-16: for each deployment case, what is drawn today, what the compiler assumes, what the model gets, what one would draw to state the same thing explicitly, and what one would draw to go beyond it. The point is to count the symbols and fields before deciding anything, and to check that nothing is being overconstrained.
- Decided already: a chip's `Processor` field names its processor when the context holds more than one (E44); a device's consumer is the processor that owns the pin it lands on (E43); processor, field unit and control point are independent entities, chips name their processor, field units name their host (O9); the drawn deployment is a default a generator may override (`layout-model.md` §5, "both-and").

## 1. The two relations and the one default

The model's `processors` section holds, per processor, its side, an optional board, its settings and its chips. Each field unit names its host processor; the office unit names its host too. Two relations: **chip to processor** (which hardware holds this expander) and **unit to host** (which processor runs this logic). Everything else about deployment is derived: a chip whose processor is not its unit's host is remote I/O; a processor that hosts no unit is an I/O node.

The default the KiCad compiler applies when nothing names a processor:

- Field side: one processor per interlocking, named after it. Every IODRIVER chip in the interlocking's hierarchy belongs to it, unless the chip's sheet or an ancestor below the interlocking carries a COLUMN symbol, in which case the chip belongs to the office unit of that column's machine. The interlocking's field unit is hosted by it.
- Office side: one processor per MACHINE, named after it. The office unit is hosted by it.

Two symbols and three fields are enough to state any of the cases below explicitly:

| Symbol or field | Role | Value or content |
|---|---|---|
| `Processor` symbol | STRUCTURE, like the house | Value: the processor's name, unique in the layout; fields: `Board`, and settings only a processor has (§4) ; no pins |
| `Processor` field on an IODRIVER symbol | | the name of the processor that holds the chip (E44) |
| `Host` field on the `Interlocking` symbol, and on the `CtcMachine` symbol | | the name of the processor that runs the unit |

The `Processor` symbol can sit on any sheet; its Value is the join, as for every other symbol (E34). Its name is layout-wide, because one processor can serve several interlockings.

## 2. The cases

| # | Case | Drawn today | What the compiler assumes | What the model gets | To state the default explicitly, draw | To go beyond it, draw |
|---|---|---|---|---|---|---|
| 1 | **Sargent.** One house, three chips on the field sheet, one column on the Panel sheet | `MAIN HOUSE Sargent`; `Interlocking Sargent`; chips `0x20 MCP23017`, `0x27 PCA9685-PWM`, `0x20 PCA9685-Servo`; `PanelColumn 13` with `MAX7313 0x2C` | field processor `Sargent` holds the three chips and hosts field unit `Sargent`; office processor `SPCoast South` holds the MAX7313 and hosts the office unit | `processors: { Sargent: {side: field, chips: 3}, "SPCoast South": {side: office, chips: 1} }`; `fieldUnits: { Sargent: {host: Sargent} }`; `officeUnits: { "SPCoast South": {host: "SPCoast South"} }` | a `Processor` symbol with Value `Sargent` on the Sargent sheet; `Processor = Sargent` on the three chips; `Host = Sargent` on the `Interlocking` symbol; a `Processor` symbol `SPCoast South` on the root sheet; `Processor = SPCoast South` on the MAX7313; `Host = SPCoast South` on `CtcMachine`. Two symbols, six field values, no new information | nothing: this is the common case and the default covers it |
| 2 | **Luchessa on one ESP32.** Three houses, every chip on one field sheet | three `MAIN HOUSE`s; chips, when the field sheet is drawn | one processor `Luchessa` holds every chip and hosts the one field unit; the three houses are 506 addresses and nothing else | `processors: { Luchessa: {...} }`; `fieldUnits: { Luchessa: {host: Luchessa} }`; `controlPoints`: three | the same two symbols and fields as case 1, with `Luchessa` | nothing |
| 3 | **Luchessa on two ESP32s.** The east house's chips on a second board in its own bungalow | nothing: the default gives one processor and is wrong for this layout | cannot be assumed: the compiler never guesses between two (E44) | `processors: { "Luchessa-West": {...}, "Luchessa-East": {...} }`; `fieldUnits: { Luchessa: {host: "Luchessa-West"} }`; the east chips are remote I/O of field unit Luchessa | two `Processor` symbols, `Luchessa-West` and `Luchessa-East`, the names the designer's; `Processor = Luchessa-East` on the east chips, `Luchessa-West` on the rest; `Host = Luchessa-West` on `Interlocking` | the same; the transport between the host and its node is a processor setting (§4, open) |
| 4 | **One ESP32 for Sargent and Corporal.** Two small plants, one bungalow between them | nothing: the default gives two processors | cannot be assumed | one processor holds the chips of two interlockings and hosts two field units | one `Processor` symbol, Value say `Sargent-Corporal`, on either plant's sheet; `Processor = Sargent-Corporal` on every chip of both plants; `Host = Sargent-Corporal` on both `Interlocking` symbols | the same |
| 5 | **Processor facts.** The board is an ESP32-C6, the clock comes from NTP, the store is its flash | nothing: `Driver-GPIO-*` Values are the board core's pin names and the C++ build is the check (I22) | an unknown board; layout-scope settings for the clock and the release policy (environment view §4.4) | `processors: { Sargent: { board: "ESP32-C6", settings: { clock_source: ntp } } }` | a `Processor` symbol with `Board = ESP32-C6` and `clock_source = ntp` as fields; chips and `Interlocking` as in case 1 | a board profile for pin validation, when it earns its place (I22) |
| 6 | **The simulator.** Seven field units in one process on a Mac | nothing | nothing: not a drawing fact | nothing: the generator re-hosts every field unit on one virtual processor and the drawn processors are ignored (`layout-model.md` §5) | nothing | nothing: a generator option |
| 7 | **A CMRInet node.** A remote expander with no logic of its own (E32) | nothing yet | a chip with a `Processor` that hosts no unit is an I/O node | `processors: { "Node 3": { side: field, chips: [...] } }`, hosting nothing; its chips are remote I/O of whichever unit consumes them | a `Processor` symbol `Node 3`; `Processor = Node 3` on its chips; no `Host` names it | the same; the transport is the node's setting (§4, open) |
| 8 | **Two machines.** A second office unit for a second dispatcher | a second `CtcMachine` | one office processor per machine | two office processors, two office units | as case 1, per machine | nothing |

Counting: the default covers cases 1, 2, 6 and 8 with nothing drawn. Cases 3, 4, 5 and 7 need one symbol and a field per chip, and a `Host` field when there is more than one processor in an interlocking's hierarchy. No case needs a pin, a wire, or a sheet rule beyond the one already in place for columns.

## 3. Why fields and not wires

A chip could be wired to a processor symbol's pin instead of naming it. That was considered for `Terminal` and rejected for the same reasons that apply here (E56, learned 3): wires between sheets are cumbersome, a processor that serves two plants would need a wire across two hierarchies, and the join by Value is the mechanism every other symbol uses (E34). A GPIO pin is a different thing: `Driver-GPIO-*` symbols already are the processor's pins, placed where their devices are, and they take `Processor` like a chip.

## 4. What belongs on the symbol and what does not

The test, from O1: does the fact change what the railroad does, or what the generated application is? If yes it is design and goes on the symbol. If it only changes how the firmware reaches the hardware this week, it is a deployment option or a secret and stays out.

| Fact | On the symbol | Why |
|---|---|---|
| name | yes | the join |
| board (`ESP32-C6`, `cpNode`, `Mac`) | yes | changes the generated code: pin names, store, timers |
| clock source, store kind | yes, as processor settings | facts only a processor has; a GPS is on one board, not on a layout |
| the transport between a host and its remote I/O node (case 3, 7) | open | a design fact (CMRInet over RS-485 is a wiring decision) but it may belong with the node's chips rather than the processor; default: a processor setting, `io_transport`, until a drawing needs more |
| the USB port the IDE uploads through | no | changes nothing the railroad does; a deploy option |
| WiFi credentials, OTA host name, IP addresses | no | secrets and deployment; `secrets.h` is gitignored everywhere (AGENTS.md) |
| the MQTT broker | no | a code line fact, on the transport symbol already |
| which interlockings it hosts | no | derived from the `Host` fields; a list on the processor would be a second copy |
| which chips it holds | no | derived from the chips' `Processor` fields; same reason |

Processor settings are not a scope for driver settings. The setting scopes stay factory, layout, interlocking, binding, instance, calibrated (I15); a processor hosts several interlockings and an interlocking may span processors, so neither is more specific than the other and a precedence would be arbitrary. Processor settings are only the facts in the table above.

## 5. Open

1. The transport between a host and its remote I/O node (cases 3 and 7): a processor setting, or a fact of the node's chips. Default: a processor setting, `io_transport`.
2. `Host` as a field on `Interlocking` and `CtcMachine`, or a `Host` pin that the processor symbol is wired to on the same sheet. Default: the field, by §3.
3. Whether the office side's chips should name their processor by the column's machine rather than by sheet context, so that the rule reads from a fact and not from "a sheet with a COLUMN symbol". Default: the column's `Machine` field, which is the fact the sheet rule was standing in for (ADR 0001 D15, "facts, not symbols").
4. The term "office unit" and the symmetric section `officeUnits`, pending the glossary amendment (step 8).
