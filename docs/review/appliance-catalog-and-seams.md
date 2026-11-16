# Appliance catalog and the two seams

- Status: **draft for the owner, 2026-11-15**. Research only; no decision is made here. §8 lists the questions.
- Asked by the owner on 2026-11-15: start from the appliances of real railroads, group them, map them to our
  symbology, and compare an all-high-level seam with the low-level seam we draw today.
- Order of authority: the relay model and AAR/AREMA practice (FieldUnit `docs/GLOSSARY.md` §10.6, ADR 0013 Part 2);
  then FieldUnit `src/`; then the KiCad-derived model; legacy code is evidence only. A claim with no source opened is
  marked (unverified).
- Sources opened: FieldUnit `src/` and `src/drivers/` at the working copy of 2026-11-15; FieldUnit
  `docs/GLOSSARY.md` §5, §7; Subdivision ADR 0016; JMRI `java/src/jmri/implementation` and `jmrix/mqtt` at
  `c2cf6c7aa32` (2026-11-05); the Railroad symbol libraries at `HEAD` (read only).
- The SPCoast drawing is a deliberately varied test set. It is not used as a source of good patterns here.

## 1. The two seams already exist in FieldUnit

FieldUnit's runtime has two driver policies, side by side:

| Policy | FieldUnit's own words | What it binds | Source |
|---|---|---|---|
| `MqttDriverPolicy` | "High-Level Semantic Device Interface. Drives smart trackside nodes over MQTT domain topics" | an appliance by name to a topic: a track circuit to `{prefix}/sensor/{name}`, a switch to `{prefix}/turnout/{name}` and `/state`, a mast to `{prefix}/signalmast/{name}` | `drivers/DriverPolicy.h:135`; `drivers/MqttApplianceBus.h:67`, `:80`, `:103` |
| `IoBitDriverPolicy` | "Low-Level Electrical Hardware Device Interface. Drives physical pins, I2C port expanders, and PWM servos over IOBus" | an appliance to a fixed set of bits | `drivers/DriverPolicy.h:161`, `:177`, `:183`, `:189` |

Between the logic and either policy sits an appliance object: `Switch`, `TrackCircuit`, `SignalMast`,
`TrainOrderFace`. The logic sees only the appliance. The policy realizes it.

Our drawing and model describe only the low-level form (device pins wired to driver bits). The JMRI proxies
(`Device-Mast-JMRI`, `Device-TrainOrder-JMRI`) are the first high-level form we drew, and they did not fit the
low-level structure. That is the tension the owner saw on 2026-11-15.

JMRI has the same two levels. Smart masts take a word: `DccSignalMast` (an aspect packet), `MqttSignalMast`. Composed
masts are built from outputs: `SignalHeadSignalMast` (heads), `TurnoutSignalMast`, `MatrixSignalMast` ("a Binary
Matrix (Truth Table) of Aspects x Turnout objects"). JMRI's head classes (`SingleTurnout`, `DoubleTurnout`,
`TripleTurnout`, `TripleOutput`, `QuadOutput` `SignalHead`) are compositions forced by JMRI's two primitives: a turnout
is one output bit and a sensor is one input bit. They show composition shapes, not hardware needs.

## 2. Catalog

The appliances of a real railroad, with the words each one exchanges with the logic (its functional seam).

| Appliance | Prototype function | Words from the logic | Words to the logic | Sources |
|---|---|---|---|---|
| track circuit | detects a train in a section | — | `OCCUPIED` (with quality) | GLOSSARY:409; `TrackCircuit.h:14`, `:75`; ADR 0016 §3.2 |
| powered switch | points moved by a switch machine | `NORMAL`, `REVERSE` | `NORMAL`, `REVERSE`, moving, out of correspondence | GLOSSARY:404, :406; `types.h` `SwitchPosition`; `SwitchDriver.h:9-11` |
| manual switch, sensed | hand-thrown; points detected | — | `NORMAL`, `REVERSE` | GLOSSARY:407 |
| manual switch | hand-thrown, not detected | — | — | GLOSSARY:407 |
| dual-control switch | powered; the crew may work it after release | `NORMAL`, `REVERSE` | as powered | GLOSSARY:408 |
| derail | switch-shaped; NORMAL derails | as a switch | as a switch | GLOSSARY:346; `Switch.h:18-20` |
| dependent derail | moves with its switch | none of its own | none on the code line | `Switch.h:12`, `:138-140` |
| electric lock | locks a hand-operated switch; the dispatcher releases it | `RELEASE` | `RELEASED`, `REQUEST` | GLOSSARY:363; ADR 0016 §3.2; `types.h:67` |
| signal mast | carries heads; shows an aspect | an indication (`CLEAR`, `APPROACH`, `STOP` …) | — | GLOSSARY:370, :383; `SignalMast.h:9`; `types.h` `Indication` |
| automatic signal | a block signal worked by track circuits | (computed in the field) | — | GLOSSARY:326; `AutomaticSignal.h:48` |
| train order face | one face of a train order signal, worked by the operator | an indication | `STOP`, `SLOW` (the operator's lever) | GLOSSARY:415; `TrainOrderFace.h:16`, `:34` |
| lamp (fascia, model board) | shows one fact | on, off | — | trackplan `Lamp Controlled`, `Lamp Repeater` |
| maintainer call | calls the maintainer | `CALL` | `CALL` | GLOSSARY:254; ADR 0016 §3.2; `InterlockingPlant.h:830` |
| sensor (contact) | any one-bit fact from the field | — | asserted | trackplan `Sensor` |
| actuator | any one-bit action in the field | on, off | — | trackplan `Actuator Controlled` |
| desk lever (switch, signal, lock, auxiliary) | states one intent | lamps: the indications | the lever position | GLOSSARY:250 |
| code button | sends the controls of one station | — | `CODE` | GLOSSARY:242 |
| selector | picks one of several values (a yard ladder) | a colour (feedback) | a value, a button | ADR 0016; `PanelSelector` (Office) |

Not in the catalog: line circuits (`H`, `D`, `F` of ADR 0013) and code line transports. They are seams between
logics, not appliances.

## 3. Groups

The catalog falls into four groups by the shape of its seam.

| Group | Seam | Members | Bits in the low-level form |
|---|---|---|---|
| **A. one bit in** | one boolean to the logic | track circuit, sensor, manual switch's detector (each contact), code button, any lever contact | 1 in |
| **B. one bit out** | one boolean from the logic | lamp, actuator, maintainer-call lamp, any lever lamp | 1 out |
| **C. fixed multi-bit** | a few booleans with fixed meanings | powered switch (`M` out; `N`, `R` in), the same with its OS circuit (`M` out; `N`, `R`, `OCC` in), electric lock (`RELEASE` out; `RELEASED`, `REQUEST` in), desk switch lever (`NWS`, `RWS` in; `NWK`, `RWK` out), desk signal lever (`NGS`, `HS`, `SGS` in; `NGK`, `SGK`, `TIME` out), train order lever (`STOP`, `SLOW` in) | 2 to 6 |
| **D. word** | a word from a set | signal mast (indication), train order face (indication out, `STOP`/`SLOW` in), RGB lamp (a colour), selector (a value) | many bits, an encoder, or a smart object |

Notes:

- Group C is A and B in a fixed bundle. FieldUnit's `SwitchDriver` is exactly one bundle: "1 motor output bit … 2
  contact sense input bits" (`SwitchDriver.h:10-11`). The OS circuit is not in it: it is a separate
  `TrackCircuitDriver`. So "a switch with its OS circuit is four bits" is two appliances realized together, not one.
- Group D is the only group where a word crosses. Under the low-level seam a word needs a translation to bits (a head
  to `R`, `Y`, `G`; a colour to `R`, `G`, `B`; an indication to a servo angle). Under the high-level seam the word
  crosses as it is.
- A desk lever is a group C bundle on the office side. It is the same shape as a fascia lever on the field side
  (ADR 0017 decision 5).

## 4. Map to our symbols

| Group | Trackplan (appliance) | Field and Office (device) | Encoder | HardwareIO (driver) |
|---|---|---|---|---|
| A | `Track Circuit*`, `Sensor`, `Switch_Manual_Sensed`, `Derail Manual Sensed` | `Device-TrackCircuit-Current`, `-Optical`, `Device-Contact`, `Device-Switch-ManualSensed`, `PanelCode` | — | `Driver-GPIO-Digital`, `Driver-I2C-MAX731x`, `MCP23017`, `Driver-CMRInet-IB`, `Driver-JMRI-Sensor*` |
| B | `Lamp Controlled`, `Lamp Repeater`, `Actuator *`, `MaintainerCall` | `Device-Lamp`, `ModelLamp-*` | `Encoder-Lamp` | the same, `Driver-CMRInet-OB`, `Driver-JMRI-Light` |
| C | `Switch_Powered*`, `Switch_Dual`, `Switch_Lock`, `Switch_Local`, `Derail*` | `Device-Switch`, `Device-Switch-OS`, `Device-Lock`, `Local-Switch`, `Local-Derail`, `Local-Lock`, `Local-TrainOrder`, `PanelSwitch`, `PanelSignal`, `PanelLock`, `PanelMCall`, `PanelAuxiliary` | — | the same, `Driver-JMRI-Turnout`, `-Turnout-Feedback` |
| D | `Signal Mast *`, `Stop`, `Train Order Mast *` | `Device-Mast-*` (taps), `Device-Head-*`, `Device-Lamp-RGB`, `Device-TrainOrder-Mast-*`, `Device-Mast-JMRI`, `Device-TrainOrder-JMRI`, `PanelSelector` | `Encoder-RYG`, `-RGB`, `-3MUX2A`, `-Pixel-*`, `-Servo` | `Driver-GPIO-Pixel`, `Driver-I2C-PCA9685-*`, `Driver-I2C-KnobEncoderRGB`, `Driver-JMRI-SignalMast` |

What the map shows:

- **Groups A and B already have one device symbol each**, and every driver family can realize them. They are
  high-level and low-level at once: the word is one bit.
- **Group C has one device per bundle**, plus a desk twin and a fascia twin for the levers. The pin set of the device
  is the bundle.
- **Group D carries most of our symbols**: taps, heads, encoders, and now proxies. Here the drawing holds the
  translation from word to bits, which the runtime already does in its drivers (`SignalMastDriver.h:23`,
  `SemaphoreDriver.h:10`, `CplMastDriver.h`).
- The trackplan family already states the regime of a switch (`Switch_Powered`, `_Dual`, `_Lock`, `_Manual`,
  `_Manual_Sensed`). That is the information that selects a group C bundle. The device symbol then repeats it.

## 5. Low-level seam today versus an all-high-level seam

"High-level" here means: the appliance is one named symbol, and its realization is a reusable template chosen by
kind, bound to a driver. "Low-level" means what we draw today: device pins wired to driver bits.

### 5.1 By group

| Group | Today (low-level) | All-high-level | Template needed | FieldUnit realization |
|---|---|---|---|---|
| A | device with one input pin, wired to a driver pin | the appliance, bound to one input bit | none: one bit | `TrackCircuitDriver` (`InputBit`); `MqttApplianceBus` sensor topic |
| B | device with one output pin, wired to a driver pin | the appliance, bound to one output bit | none: one bit | none in `IoBitDriverPolicy` today (no lamp driver) |
| C | device whose pins are the bundle, each wired to a driver pin | the appliance, bound to a bundle template: "powered switch, M out, N in, R in" | one per bundle kind (switch, switch with lock, electric lock, each lever kind) | `SwitchDriver` (`OutputBit`, 2 × `InputBit`); `MqttApplianceBus` turnout topics |
| D | appliance → tap → heads → encoders → driver bits, all drawn | the appliance, bound to a word template: "two-head color light, RYG + lunar per head", "upper quadrant semaphore, one servo", "JMRI mast", "RGB lamp" | one per realization kind | `SignalMastDriver` (`HeadPins` = R, Y, G, lunar), `SemaphoreDriver` (`SemaphoreArm`: servo, three angles), `CplMastDriver`; `MqttApplianceBus` signalmast topic |

### 5.2 What a template is

A template states, for one realization kind:

1. **Its appliance kind and the words it carries** (from §2).
2. **Its bits, by role**: for example `motor` out, `normal` in, `reverse` in. Each role has a direction and a
   capability kind (ADR 0016 §4: `binary`, `level`, `value`, `position`, `pixel`).
3. **Its parameters**: for a semaphore, the three angles (`SemaphoreDriver.h:10`); for a color light head, which lamps
   exist; for a JMRI object, its address.
4. **Its FieldUnit realization**: the driver class and its add call.

In the drawing, an instance of a template is the appliance's realization: a small group of bits on one driver, or one
smart object on a transport. Two ways to draw it were discussed; neither is chosen here:

- **One device symbol per template**, whose pins are the roles. This is what `Device-Switch` is today, so groups A, B
  and C are already drawn this way.
- **A reusable hierarchical sheet per template**, placed once per appliance (KiCad allows one sheet file in many
  places). A sheet can hold an encoder and a driver, which a symbol cannot. (unverified for our importer: it reads
  sheets, but has not been tested on a sheet placed more than once.)

### 5.3 How a template binds to a driver

- **Low-level drivers** (GPIO, I2C expanders, CMRInet bits): each role lands on one driver pin. This is today's
  binding, and it stays: the wire from a role to a driver pin is a real fact (which pin of which chip).
- **Smart objects** (JMRI, MQTT): the whole template binds once, to a transport, and the role names become topic or
  object names. FieldUnit derives the topic from the appliance name (`MqttApplianceBus.h:67`, `:80`, `:103`).
- **Word-to-bits translators** (encoders): under the high-level seam they belong inside the template, not between
  the appliance and the driver. FieldUnit already does this translation in `SignalMastDriver` and `SemaphoreDriver`.
  `Encoder-3MUX2A` is the one encoder FieldUnit has no driver for (its truth table is reference data in our model).

### 5.4 Where polarity lives

FieldUnit holds one polarity per bit: `IOBit` has a `Polarity` (`NORMAL` active high, `INVERTED` active low), and
`IOBus` applies it on every `readBit` and `writeBit` (`IOBit.h:10`, `:24`; `IOBus.h:36`, `:44`). That is the owner's
layer E (the pin) only.

The owner's layers (2026-11-14) and where each one would live:

| Layer | Says | Home under the high-level seam |
|---|---|---|
| A layout | a layout-wide default | the layout (one setting) |
| B driver type | every chip of a type | the driver's library symbol |
| C driver instance | every pin of one chip | the placed driver |
| D sub-driver | one bank of a chip (the MCP23017 has two) | the placed driver, per bank |
| E pin | one pin | the template instance, per role |
| F in versus out | A to E, separately for inputs and outputs | a split of each layer |

Rules that follow, unchanged from the owner's ruling: polarity applies only to `binary` roles; the layers resolve in
a fixed order to one `Polarity` per bit; FieldUnit receives only the result. A word role (group D) has no polarity.

## 6. Findings

1. **FieldUnit already separates the two seams.** `MqttDriverPolicy` is high-level, `IoBitDriverPolicy` low-level, with
   the appliance object between them and the logic (§1). Our model has only the low-level form.
2. **FieldUnit's low-level policy covers three appliances.** Track circuits, switches and color light masts are in
   `IoBitDriverPolicy`. Semaphores and CPL masts have drivers but are not in the policy. Lamps, locks, maintainer
   calls, train order levers and selectors have no driver. The generator writes those bits into the sketch directly
   (`TrainOrderFace.h:16`: "the present state of the lever contacts, as the I/O system reports them").
3. **Group D is where the drawing does the runtime's job.** Taps, head devices and encoders draw the word-to-bits
   translation that `SignalMastDriver` and `SemaphoreDriver` already perform. Drawing it twice is where the head and
   face problems of ADR 0018 came from.
4. **Groups A, B and C are already high-level in effect.** Each device symbol is one appliance with its bundle of bits.
   The only change the high-level view asks of them is to name the device by its appliance.
5. **The switch-and-OS bundle is two appliances.** FieldUnit realizes it with two drivers. A single four-bit symbol
   (`Device-Switch-OS`) is a drawing convenience, not one appliance.
6. **Polarity has one layer in FieldUnit.** The owner's layers A to D and F have no home today. They are a generator
   concern: resolve them to one bit polarity.
7. **JMRI shows both shapes and one gap.** Smart masts and composed masts both exist. Over MQTT, JMRI implements only
   the mast: `MqttAdapter.java:87` offers a "Signal Head topic", but no class in `jmrix/mqtt` uses it.

## 7. Candidate design

### 7.1 Rules

1. **An appliance is one named symbol on the trackplan, and its words are its seam.** The words are ADR 0016's
   function words, plus the indication for a mast or a face.
2. **Each appliance has one realization, chosen from a short list of templates for its kind.** The list is per kind:
   for a track circuit, "one input bit" or "smart sensor"; for a color light mast, "N heads of R, Y, G, lunar bits" or
   "smart mast"; and so on.
3. **A low-level template binds role by role to driver pins. A smart template binds once to a transport.**
4. **Word-to-bits translation is inside the template, never drawn between the appliance and the driver.** Encoders
   become template parameters (lamps present, servo angles, a truth table), not symbols in the chain.
5. **A device symbol serves its appliance by Name** (ADR 0018 rule 1). A part (a head, a face) is `<appliance>.<part>`
   where a template needs one.
6. **Polarity is resolved from layers A to F to one value per binary bit**, and only that value reaches FieldUnit.
7. **Direction and sharing come from the template's roles** (ADR 0018 rule 3: outputs fan out, inputs have one
   source).

### 7.2 What would become unnecessary

| Item | Why |
|---|---|
| `Device-Mast-*` taps and the position-pin mapping | the template knows its heads |
| `Device-TrainOrder-Mast-*` taps | the face is the appliance part; the template knows its arm or lamp |
| `IND` pins on heads and `Local-TrainOrder` | identity comes from the Name |
| `Encoder-*` symbols in the chain | translation is inside the template (rule 4) |
| `Device-Head-*` as separate symbols, if each mast template carries its heads | a head is a role group of the mast template |
| the separate JMRI proxies as a special case | a smart template of the same appliance |
| ADR 0016 §4 seam word sets on device and encoder pins (`indication`, `head`, `color`) | no word crosses a drawn wire; words stay at the appliance |
| ADR 0018's head naming (`778NAB.A`) for local masts | needed only if heads stay drawn |
| ADR 0017 decision 5's desk and fascia twin symbols | one bundle template, two placements |
| parts of ADR 0009 §3 (the field mast device, head devices, encoders in the relation table) | the chain is gone |
| parts of ADR 0012 (derived mast `positions` from pins, the encoder kind tables) | template parameters instead |

### 7.3 What stays

| Item | Why |
|---|---|
| the trackplan appliances and their Names (ADR 0003, ADR 0011) | they are the high-level seam |
| ADR 0016's function words and ADR 0016 §4 driver capability kinds | the words of the seam and the capability of a bit |
| ADR 0017 decisions 1 to 4 (side from the processor; demands through the owning logic) | they are about bindings, not symbols |
| ADR 0018 rule 3 (outputs fan out, inputs have one source) | it applies to template roles unchanged |
| ADR 0008's data model with `given`, `relations`, `derived` (ADR 0011) | a template instance is a relation |
| driver symbols, processors, transports, the IO bus (ADR 0005, ADR 0009) | the low-level binding is still real |
| groups A, B and C device symbols | they are already templates; they gain a Name |

## 8. Questions for the owner

Each has a default. They are in the order the work would need them.

1. **Is the high-level seam the primary seam of the model?** The model states appliances, their words, and one
   realization each; bits are a property of a realization. *Default: yes.*
2. **Where does a template live?** As (a) a device symbol whose pins are its roles, (b) a reusable hierarchical sheet,
   or (c) reference data in the model with a symbol only for the bits. *Default: (a) for groups A to C, which is what
   we have; try (b) for group D in one POC.*
3. **Do encoders leave the drawing?** Their translation moves into the template as parameters. *Default: yes, for
   the color light and semaphore templates FieldUnit already drives; keep `Encoder-3MUX2A` until FieldUnit has a
   driver for it.*
4. **Do heads stay drawn?** If a mast template carries its heads, `Device-Head-*` go and ADR 0018's head naming is not
   needed. *Default: heads become roles of the mast template; decide after the question 2 POC.*
5. **Where do polarity layers A to D and F live?** *Default: on the layout, the driver symbol, the placed driver and
   its banks, as §5.4; the generator resolves them to one `Polarity` per bit.*
6. **Which templates are the first list?** *Default: from §5.1: one bit in; one bit out; powered switch (M, N, R);
   electric lock; each desk lever; color light head (R, Y, G, lunar); semaphore arm (servo, three angles); RGB lamp;
   smart sensor, turnout, mast and train order face.*
7. **Does FieldUnit need more low-level drivers** (lamp, lock, lever, face) so that every template has a runtime
   counterpart? *Default: yes; a FieldUnit question for FieldUnit Orchestration.*
8. **What happens to ADR 0018?** *Default: hold it as a draft; rewrite it after questions 1 to 4, keeping rule 3.*
9. **Is the SPCoast drawing checked against the template list only after the list exists?** *Default: yes; misfits
   are then either symbology debt or a missing template.*
