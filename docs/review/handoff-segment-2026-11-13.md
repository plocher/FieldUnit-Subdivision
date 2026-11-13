# Hand-off: segment 2026-11-12 to 2026-11-13 (Compiler Orchestration)

For the next orchestrating session. State, rulings, open items. Rulings are the owner's; cite them, do not re-argue
them. The order of authority and the working agreements are in `AGENTS.md`.

## State

| Repo | Branch / commit | Note |
| --- | --- | --- |
| FieldUnit-Subdivision | `main` 3b90a2a | PRs 126, 127, 129, 130, 131, 132, 135, 136 merged this segment. No PR open. Schema `layout-model/v3.4.0`. |
| Railroad (`~/Dropbox/KiCad/Railroad`) | `main` = `feat/merge-signal-libraries` = 87f6aa4, pushed | Corporal renumbered (520c509); libraries: Value is the literal, `Milepost` declared on every trackplan symbol, JMRI descriptions and `JMRI.SignalSystem`. `Panels/` untracked by design. |
| FieldUnit | main after PR 50 | ADR 0010 accepted (PR 48); `TrainOrderFace` in `src/`; generator spike `tools/layoutgen` reads the 3.4.0 example, six of seven interlockings pass, Watsonville fails on FieldUnit capacity. |

Live compile of SPCoast at 87f6aa4: 0 error, 2 warning (`reference.switches`, the Beet Loader net shared by Corporal and
Sargent), 7 info (`regime.limits`), 27 missing (`mast.lever` 15: Gilroy 778 x4, Sargent 836 x3, Watsonville 840 x8;
`switch.lever` 12, all Watsonville). `lever.masts` reports nothing.

## Rulings this segment (owner, 2026-11-12/13)

1. **Value is the literal.** On every library symbol and instance, `Value` is the user-editable literal; the key field
   (Address, Bit, CP Name) is `${Value}`. KiCad "Update Symbols from Library" is safe with all fields except Reference
   and Value selected, "Remove fields if not in library symbol" checked, the two text-reset boxes unchecked. A library
   symbol's field set is the contract; undeclared instance fields are noise.
2. **`mast.presents` stays info.** A head that cannot show Stop sits where Stop is never vital; the wrong head is a logic
   error, not a model inconsistency.
3. **The importer states the atoms.** A mast's Name is a composite; the importer decomposes it (`given.signal`,
   `given.heads`, `relations.facing`, `derived.positions.<pin>`); a derail states its switch (`relations.switch`,
   `derived.derails`). Derivation and consumers never parse a Name (ADR 0009 §3.7 `[^atoms]`, §3.12 `[^derail]`).
4. **Corporal is the first consumer** (Luchessa: US&S 506 line, three houses; Sargent: signal 836 has no lever yet).
   Corporal's lock and switch renumbered to 827 and 829 so column 11 = 827 + 828, column 12 = 829 + 830.
5. **M1, reference data:** JSON files under `schemas/layout-model/reference/`, one per table with a schema beside it,
   `schemaVersion` 0 and a provenance date; the files are the source, there is no second compiler; resolved per
   entity into `derived`; selection stated by `layout.given.Railroad/Era/Rulebook`, overrides beside the item.
6. **Versioning:** no bump rules policed until the compiler and FieldUnit work end to end. The one-sentence
   pre-release clause for ADR 0012 waits for the contract-freeze ticket (#30/#98/#99).
7. **No REFDES anywhere.** Nothing locates a thing by KiCad reference; `Diag.source` is `library:symbol(Name)` plus
   the pin (ADR 0012 §3.3 `[^source]`). The owner does not re-annotate.
8. **A middle home** for the schema, the rules, the reference derivation, the reference data, the domain libraries
   and the model ADRs is agreed in principle (neither the KiCad importer nor FieldUnit owns them); the move is keyed to
   the contract freeze. Until then: nothing under `tools/layout_model`, `tools/railroad` or `schemas/` imports the
   importer; new data goes under the schema folder. This retires the 2026-10-07 note "schema in FieldUnit".
9. **Train order signal names:** not block signals; a parallel, non-overlapping pattern is fine. FieldUnit generates
   `<board>.<face>` (`Gilroy.E`); the model stores no composed name (faces keyed by pin under the board).
10. **M4 is by design:** station packets are computed on demand (feature
    `logical/office/device_lever_station.feature`), not stored.

## Open for the owner

- Drawing: signal lever 836 at Sargent (then Sargent can be a consumer); the Beet Loader hierarchical labels that join
  Corporal's and Sargent's spurs (`reference.switches`); Watsonville's 12 leverless switches and 840's 8 masts.
- Data: rows for `schemas/layout-model/reference/policies.json` (rulebook, head count, mast indication, head word per
  position), with routes (#62).
- Design, in order: routes, blocks and ceilings (#62); then traffic flow between interlockings (NFL/SFL repeater lamps
  at Luchessa and Watsonville are today lamps named for a flow; ADR 0013 lists it as open item 6); then the contract
  freeze (#30/#98/#99) with the middle-home ADR and the TestCorpus split (#66).
- Sessions: ticket-133 and ticket-134 are done and idle; archive them and their worktrees.

## FieldUnit side (cross-session: "FieldUnit Orchestration", `local_7a690c8e-fad9-4f67-b955-dd4034779c05`)

Closed: M1, M2, M4 (by design), M5 (withdrawn: every token has a stated reporter; it is now FieldUnit finding L11, no
class produces an indication from a repeater or a contact). FieldUnit pairs a derail by name in its library (their
issue 29). Their desk spells a maintainer call `MC1MCK` where the template says `1MCK` (theirs). They read the
resolved `derived.faces`, not the tables; `policies` rows will be read from `derived.positions.<pin>.shows`.

## Lessons recorded in memory

Never `git worktree remove` right after `start_session` (the app reuses folder names); check a claim against the file
before relaying it (M5); PR merges on a branch do not carry a later push to that branch (520c509 sat outside main
until merged by hand).
