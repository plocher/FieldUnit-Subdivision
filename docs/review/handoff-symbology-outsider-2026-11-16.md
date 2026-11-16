# Handoff: layout symbology from the designer's side (2026-11-16)

- From: the compiler orchestration session, 2026-11-15/16.
- For: a new session with an **outsider's view**. Do not start from the symbols, schema, importer or ADRs we have,
  and do not plan a migration. Design first; how to get there from here comes later and in another document.
- Deliverable: a proposed ADR (in `docs/adr/`, per the repo's ADR method) that answers the question in §2, with a
  storyline a layout designer can follow. Return one consolidated list of the decisions the owner must make, each with
  a default.

## 1. How we got here

The owner was working through how a JMRI signal mast and a JMRI train order signal fit our drawing. Each new case
needed another stand-in symbol, another tie between symbols, another rule. The owner then asked:

> WHATIF... our choice of low level seam was the underlying issue and the more flexible one would be smart
> appliances?

The owner's framing of the two seams:

- **Low-level seam**: the logic exchanges single bits with the field (one output lights one lamp, one input reads one
  contact). Words such as an indication must be turned into bits somewhere, and today the drawing does it.
- **High-level seam (smart appliance)**: the logic exchanges the appliance's own words with it (a mast is told
  `APPROACH`; a switch is told `REVERSE` and reports `REVERSE`). This maps well to IoT and to a functional view.
  JMRI's MQTT signal mast is an example.

The owner's hunch: each appliance has one, maybe two, common reusable low-level arrangements (JMRI builds its heads
out of two or four "turnouts"), and much of the stand-in and chained logic we have drawn would simplify. Much of the
recent ADR work may turn out to be chaff.

A research note was written: `docs/review/appliance-catalog-and-seams.md` (this branch, commit `f9ebfdd`). Read it as
**evidence only**. The owner rejected it as a design document, for the reasons in §3.

## 2. The question

> Given what we know from the survey research and our experiences, what symbology design patterns exist that would
> deliver correct results, and of them, which is the best fit from a comprehension, robustness, DRY, ...
> perspective?

The information flow that frames it:

- A. The designer's intent is captured in a layout design tool (KiCad today, Studio later), which flows into
- B. the layout data model, into
- C. FieldUnit, into
- D. apps, libraries and firmware, into
- E. virtual or physical electromechanical devices connected to processors.

The symbology offered to the designer must capture everything the later stages need. In the owner's words, the
symbology in the drawing "must be sufficient to capture the visual, logical/functional and physical relationships of
the trackplan geometry/geography, operational context and constraints, appliance abstractions, and physical devices
that the user wishes to describe."

FieldUnit's job, as the owner states it:

1. Give a logical abstraction of the appliances used on a model railroad, both railroad-inspired ones and
   owner-desired ones, through an extendable support library.
2. Give a logical framework that uses railroad rules, AREMA safety logic (relay charts) and the operational
   relationships between actors and appliances to make the logic that runs in the office and the field, in Arduino or
   other firmware, simulations or emulations.
3. Give a way to represent the connections to the physical devices on a layout or in an office.
4. Transform the owner's functional data model of a layout into a form that uses those capabilities to run the
   desired operating logic.

## 3. What went wrong last time (avoid these)

1. **FieldUnit read as requirements.** FieldUnit's current models and wiring assumptions were made before the data
   model, schema and symbols existed. They are not settled fact. They reflect requirements that come **from** the
   data model; they place no requirements on it.
2. **No storyline.** The note listed what we did, what JMRI does and what FieldUnit does, then jumped to one
   candidate with low-level rules. An ADR needs: the problem in the designer's terms, the criteria, the candidate
   patterns, an evaluation, the recommendation, its consequences. Rules come last.
3. **eCAD thinking.** KiCad is used only for its symbology and will be replaced by Studio. The drawing has nothing to
   do with electrical wiring. "Electrical rule check", "real wires", "nets" and "pins" are not design criteria.
4. **Implementation vocabulary.** Words such as kind, realization, tap, Name, binding, pin and net are insider words.
   They limit understanding when their operational definitions are not clear, and they pulled the discussion into
   "how do we migrate what we have". Use the designer's nouns and verbs: railroad appliances, rulebook forms, AREMA
   definitions, layout artifacts. Bring in an implementation word only after the design is settled, with an
   operational definition.
5. **Surveying our own drawing for good patterns.** The SPCoast drawing deliberately tries many arrangements, because
   it is inventing a symbology. Its patterns show that there are many patterns, not which ones are good.
6. **Over-reading JMRI.** JMRI's many signal head classes exist because JMRI often exposed only two primitives, a
   turnout (one output bit) and a sensor (one input bit). They show composition shapes, not what hardware needs.
   Also, an earlier claim that JMRI has no signal heads was wrong; check sources before you rely on them.

## 4. Useful material

- **Order of authority** (repo `AGENTS.md`): the relay model and AAR/AREMA practice (FieldUnit `docs/GLOSSARY.md`
  §10.6 inside an interlocking; ADR 0013 Part 2 between interlockings); then FieldUnit `src/` (where it differs, the
  code has the defect); then the KiCad-derived models; legacy sketches are evidence only. Cite only sources you
  opened; mark others (unverified). Never invent prototype mechanics.
- **Vocabulary**: FieldUnit `docs/GLOSSARY.md` (`~/Dropbox/Arduino/libraries/FieldUnit/docs/GLOSSARY.md`).
- **Rulebook**: `docs/review/gcor-2025.pdf` in the main checkout (the owner's copy, not committed).
- **Research note** `docs/review/appliance-catalog-and-seams.md`: its catalog (§2) and its grouping by the shape of
  what crosses the seam (§3: one bit in, one bit out, a fixed bundle of bits, a word) are the most reusable parts.
  Its §4 to §8 are written from the inside and are not a basis.
- **Experience to weigh**, each a symptom rather than a design input:
  - Each new way to make a signal mast real (lamps on an expander, a servo semaphore, a JMRI mast) needed new
    in-between symbols and new rules.
  - A train order signal has two faces, each with an operator's lever (`STOP`, `SLOW`), and a JMRI version needs
    three remote addresses. Ties by matching names and by drawn lines both got awkward.
  - Lamps, switch machines and sensors also come in local and JMRI forms; it is open whether they follow the mast's
    pattern.
  - Whether an input or output is active-low can be set at six levels: the whole layout, a driver type, one driver, a
    bank, one point, and inputs and outputs separately. It applies only to on/off quantities.

## 5. Out of scope

- Migration, refactoring recipes, and changes to the symbol libraries, schema, importer or drawings.
- The owner's KiCad files in `~/Dropbox/KiCad/Railroad`: read only, if at all.
- ADR 0018 (draft PR 157) stays a draft until this question is settled.
