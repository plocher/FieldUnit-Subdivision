# Goals: the design provenance chain

Living document. First written as a reset note on 2026-09-24 (archived as
`docs/archive/part-c-ontology/DraftPlans-2026-09-24.md`); restated here with the settled vocabulary.

## Long term

A design provenance chain that starts with a set of KiCad schematics and compiles them into one
functional data model. The model has several consumers, and every one of them is generated from it
rather than written by hand:

1. **A field unit in the field**: a sketch for a field processor that runs the interlocking logic for one
   interlocking and drives the layout's physical devices through its I/O (I2C expanders, PWM, buses).
2. **A field unit in the office**: the same logic as a hosted application that reaches the devices through
   remote I/O nodes (a CMRInet host with C/MRI nodes, for example).
3. **A simulation**: the plants and the trains, moved by people or by automata, for operating sessions and
   for exercising the dispatcher's CTC machine (FieldUnit-Studio holds the germ of this).
4. **An emulation**: the appliances represented and introspectable, so that test vectors, debugging and
   replay of dynamic operations are possible (`spcoast_virtual_plant` is the simple version).
5. **A documentation set**: printable packets, web pages and review views of each interlocking and of the
   territory, generated from the model so they are never stale (issue #31; an incomplete first attempt is archived
   in `docs/archive/part-c-ontology/`).
6. **The CTC machine application** for the dispatcher's desk, generated from the desk sheets.

## Medium term

- Collect the historical control point definitions (ArduinoPoint XML, OmniGraffle drawings) for the
  SPCoast layout and use them to seed KiCad schematics mechanically; the user then curates each into a
  high-quality drawing. (Done for the six legacy stations; the drawings are now the source and the XML is
  evidence only.)
- Identify and create the data concepts the model still lacks: the CTC machine itself, the structure of a
  field unit sketch, the scope of a dispatcher's territory, the operating topology for train progression.
  Method: list every datum a consumer needs and map it to the model, or flag it as missing.
- Reorganize the documentation into a consumable, user-focused set. The repositories have accumulated
  in-progress notes, reviews and handoffs; those are records and belong in `docs/archive/`, while the
  guidance a user or a new contributor needs should be short, current and findable.

## Short term (the order of work as of 2026-10-07)

1. Apply the symbol contract and the name grammar to the drawings (done for the seven plants and the desk;
   Railroad tag `split-projects-final`).
2. Define how plant appliances bind to hardware and to operator interfaces (FieldUnit ADR 0003) and clean the
   symbol libraries and the Sargent sandbox to it.
3. Rebuild the compiler's model layer to the ADRs: one `(Role, Kind)` table, library defaults by `lib_id`,
   END_CTC and dead-end caps, control points from the IRJ-Signal, the gates (issue #30 step 3).
4. The generator: emit the interlocking application for one interlocking (Sargent first) and compile it
   against FieldUnit; then the CTC machine application; then AAR tokens over MQTT to the physical desk.
5. Unify the KiCad projects into one `SPCoast` project (issue #13).

## Principles that follow from the goals

- Each fact has one source; when a fact exists both in a drawing and in code, the code is generated or
  validated from the drawing.
- The compiler emits one complete model; generators consume parts of it. Fragments are not an interface.
- Vital logic lives in FieldUnit only. Nothing in the drawings or the generators reimplements an
  interlocking rule.
- Hardware never enters the interlocking model; the generator emits a separate hardware binding for the
  same interlocking.
