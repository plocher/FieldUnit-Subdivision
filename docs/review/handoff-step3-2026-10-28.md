# Handoff: after step 2 (derive.py and per-pin codeline tokens)

Written 2026-10-28, when step 2 of ADR 0011/0012 closed and every branch was merged. Next comes the queue below, worked
in order and **one item per turn**: give a recommendation and ask one question, the owner answers, then move to the
next item. The owner's rulings are in memory: `spcoast-controls-follow-column`, `spcoast-symbol-fields-are-draft-kind-table`,
`spcoast-remote-refs-are-indications`, `spcoast-sheet-scope-is-a-default`, `spcoast-adr-0011-0012-2026-10-26`.

## Where things stand

- **Merged on 2026-10-28:**
  - Subdivision #52 (step 2) and #53 (the route spike beside ADR 0012);
  - Railroad #14 (CP Name, per-pin tokens, lamp expressions, 1MC maintainer calls, 838SAB, 840SA);
  - FieldUnit #38 (lock tokens WLS, WLK, WLQK in the glossary).

  All three repos are on `main` with no other branches.
- **`tools/layout_model/derive.py`** is the reference derivation. The importer (`tools/layout_compiler`) writes
  `given` and `relations`, calls derive, and adds the drawing location to each derived diagnostic's `about`.
  `tools/layout_model/expression.py` parses lamp `Indication` expressions (`|`, `&`, `!`, parentheses; a comma is OR
  during the transition). `tools/railroad/codeline.py` computes station packets on demand, and nothing is stored.
- **Station rules:**
  - A station is what the codeline's encoding says it is: each house on the US&S 506 (Luchessa), the interlocking on
    AAR tokens.
  - A lever's controls and indications go to its desk column's station.
  - Masts never report.
  - Lamps resolve through the reporting appliance, using an interim template lookup in `codeline.py`.
  - Device feedback (the JMRI MQTT feedback topics) belongs to the binding layer and never to the codeline.
- **Tokens:**
  - PANEL symbols state them per pin, as in `Control.NWS=${Value}NWS` and `Indication.NWK=${Value}NWK`.
  - An empty field means tokenless on purpose. A missing field means not done yet.
  - Trackplan appliances carry no tokens and match their panel appliance by Name.
  - The lint (`tools/contract/lint_symbol_fields.py`) enforces the structure, and the conventions tab of
    `tools/kicad_library_overview.py` is the audit.
- **Gates:**
  - `uv run python -m unittest discover -s tests -q`: 341 tests pass.
  - A fresh SPCoast compile gives 0 errors, 0 warnings, 9 info and 2 missing.
  - The two missing are `interlocking.no_lever`: Gilroy Caltrain 771, whose lever is on another office unit that is
    not implemented yet, and Watsonville's ladder 3–25, which will be worked by NX.
  - Railroad ERC is 1: Sargent AUX1 `pin_not_connected`, which predates this work.

## Queue, in order

1. **ADR text amendments.** No ADR has been edited yet. Present them one at a time and discuss before editing; commit a
   baseline first.
   - ADR 0011, consumer amendment of 2026-10-27:
     - the consumed token is the consumer's `Indication` field, with Name+K as the fallback, reported at info as
       `consumer.legacy_token`;
     - consumers resolve against the appliances that can report the token;
     - station packets are computed on demand.
   - ADR 0012 §5.1 and §10: add `tools/railroad/codeline.py` and `tools/layout_model/grammar.py`.
   - ADR 0012 §3.3 and ADR 0011 §5: diagnostics carry model paths, and a writer may add its own location (`about`).
   - ADR 0008 or 0009: the column's CP Name names the interlocking or one of its houses, and defaults to the
     interlocking. A sheet's interlocking is only the default for symbols that state no CP Name. Lamps never use
     columns.
   - ADR 0009: the new checks `reference.track` (cross-interlocking references on switch ports or track rows, error)
     and `track.shorted` (two track pins of one symbol on one net, error).
   - Drop the line "a switch so named is checked as a thing with its ports".
2. **The consumer-marker `Indication` field.** Add `Indication=${Name}K` to the Track Circuit marker in
   `Railroad-Trackplan`. Owner edit in KiCad, then the lint. After it, the fallback in item 1 reports nothing on
   SPCoast.
3. **Library leftovers.** These are owner edits in KiCad; check each afterwards with the lint, ERC and a fresh
   compile.
   - The descriptions of the lamp, PanelMCall and PanelMCall-Lamp symbols still mention `IndicationToken`.
   - Retire PanelMCall-Lamp, which is no longer used.
   - Watsonville's virtual track circuits TC15032 and TC15034 still use `IndicationToken` OR-lists, which are
     candidates for expressions.
   - `Invert=WLK` on the field Local-Lock devices is out of scope unless the owner says otherwise.
4. **User doc note on the maintainer call.** SPCoast names maintainer calls in AAR style (3), with the number first
   (`1MC`, `1MCS`, `1MCK`), and deliberately diverges from AAR's suffix form (MCE, MCW). Location always goes in the
   prefix.
5. **Remaining audit groups** on the conventions tab:
   - TRACK and STRUCTURE Names;
   - DEVICE and IODRIVER drive and unit differences;
   - field gaps.

   20 of 76 kinds are flagged, all in these groups.
6. **ABS/APB ADR, before step 3.** Parked here so far:
   - two masts on one joint (normal on single track), so `joint.masts` and the NextCP pair level;
   - whether consumer markers (`Corporal:2NAT`) need expressions, or whether ABS/APB replaces them;
   - Watsonville's 838S proxy (Corporal's 830S).

   The chain of signals can already be found in the model without storing routes: from a mast's joint, through the
   track adjacency and switch ports, to the next approach side with a mast (for example 840NC→838NAB→NextCP Sargent).
7. **NX ADR.** The dispatcher makes three choices: an arrival track, a departure track, and a signal lever saying
   which of the two may use the single in/out track. The ladder switches follow from those as routes. Whether masts
   join the no-lever check is decided here too.
8. **Step 3: rules as Gherkin features**, with the diagnostic registry in `schemas/layout-model/rules/` (ADR 0012 §3).
   This is development for orchestrated subagents.
9. **Step 4: domain libraries** for routes, blocks and indication ceilings (ADR 0012 §5).
10. **Later:** the "timetable" documentation tool. Lamp drive capability matching: a level (PWM) driver pin may
    drive a `binary` pin, but no check for it exists yet.

## Standing rules (also in AGENTS.md and memory)

- Netlists are transient: export fresh with kicad-cli, use, then delete.
- Run everything with `uv run python`.
- Before any `.kicad_sch` edit, check for a lock file. Goldens change in their own commit.
- Commit each finished piece on a feature branch, using Conventional Commits with a Verified section. Push or open a
  PR only when the owner asks; the owner merges.
- Discuss before changing any ADR, library, memory or drawing.
- No AskUserQuestion cards.
- Delegate development to subagents and keep the main context for review.
