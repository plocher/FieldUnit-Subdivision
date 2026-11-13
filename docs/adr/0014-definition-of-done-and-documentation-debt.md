# 0014. Definition of done, documentation debt and the developer map

- Status: **accepted by the owner 2026-11-12** as the initial decision, subject to refinement as the metric shows what
  it shows. The ask was: ratify the three decisions below.
- Amends: nothing. Adds a process rule that every later ADR, feature and PR follows.
- Builds on: ADR 0011 (what lasts: the schema, the rules, the conformance suite), ADR 0012 (rules as Gherkin features
  with a registry of diagnostic codes), the rules-as-features structure, the working agreements in `AGENTS.md`
  (proposals are ADRs; ADRs amended in place; goldens change in their own commit).

## Why

In the week of 2026-11-05 to 11-12 six rulings changed how the importer keys drivers, places trackplan symbols, reads
the signal system and treats aggregated devices. Each landed in code, a feature scenario and a docstring. The places a
reader looks, ADR 0009 for the seams and keys, the symbols manual for what a field or pin commits to, received nothing.
The work was correct and invisible. Parallel sessions make this the normal case, not the exception, so the cure is a
rule applied per change, with a number that shows whether the rule is followed.

## Decisions (ratified 2026-11-12)

1. **Definition of done.** A change is complete when every artifact that states the fact it changes is changed with
   it, in the same PR. In this repo those artifacts are named, so the rule is a list a reviewer can check by path:
   - a change to a **rule** (what the importer derives, what a derivation computes, what a check reports) amends the ADR
     section that states the rule, in place with a footnote naming the old commit, and the feature file that is its
     specification;
   - a change to **what a symbol field or pin name commits to** touches the symbols manual fragment for that symbol
     (Railroad `symbols/manual.html` and its generator's inputs) and the library's field lint where a field is added;
   - a new or renamed **diagnostic code** is registered (`tools/layout_compiler/diagnostics.json` or
     `schemas/layout-model/rules/diagnostics.json`) and cited by the ADR section or feature that owns its rule;
   - a change to the **file format** bumps the schema under its semver rule and regenerates the example golden in its
     own commit;
   - a change to **how a developer works** (commands, layout, conventions) updates `AGENTS.md` and the README map.

   A brief that dispatches a change names the artifacts the change will touch; the PR body lists them under
   "Done means"; the reviewer looks for each path before relaying the PR.

2. **Two measures, reported, not yet enforced.**
   - **Trigger and blast radius.** A mapping from code paths to the documents that state their rules, kept as data
     (`docs/agents/doc-map.json` or beside the registries). A script over git history reports, per merged PR, which
     triggers fired (`tools/layout_compiler/seams.py`, `tools/layout_model/derive.py`, `reference.py`, `grammar.py`,
     the two registries, the Railroad symbol libraries) and which mapped documents moved with them. A trigger with no
     document moved is a miss.
   - **Accumulated debt.** Every registered diagnostic code and every feature scenario is machine-readable. Debt is the
     set of registered codes with no feature scenario, and the set of codes and scenarios cited by no ADR section and no
     manual fragment, each with the age of its first commit. The existing registry gate
     (`tests/test_diagnostic_registries.py`) already walks the registries; this extends it to citations.

   Both are written as one generated report, committed where the README can link it, with the date and the commit it
   was computed on. No CI gate blocks on either until the numbers have been watched for a while; the gate is a later
   refinement of this ADR.

3. **A developer map in the README hierarchy.** The top `README.md` is rewritten as the entry for a developer: what
   the repo owns, the three maps of ADR 0011 (what lasts, what is transient, what is derived), where each kind of fact
   lives (symbol field, importer, derivation, reference data, domain library, ADR, feature, manual), the commands, and
   a link to the generated report of decision 2 so the state of decisions 1 and 2 is visible without running anything.
   The three-reader documentation of issue #122 (symbol author, project developer, layout designer) hangs off this
   map: the developer's guide is this README and `AGENTS.md`; the other two are the symbols manual and a designer's
   guide.

## Consequences

- Each ticket brief from this date names the documents the change touches. A PR that touches a trigger path and no
  mapped document is sent back before the link is relayed, unless the brief said why none applies.
- The backlog of the week's six rulings is paid first, as the first application of decision 1: ADR 0009 §3.4 (devices
  may aggregate appliances; the matching-pin key rule; `JMRI.SignalSystem`), §3.9 or the trackplan section (placement
  by `CP Name`, sheet, track net, else `trackplan.unit`), and the symbols manual fragments for `Device-Switch-OS`, the
  JMRI drivers, `Encoding-JMRI` and the Local-Lock lever.
- The urgent documentation work is bounded so it does not displace the important one: the roadmap of 2026-11-10 (heads
  #80, the contract freeze, the Luchessa generator in FieldUnit) continues in parallel; the documentation effort is a
  delegated stream with its own sessions and reports, not the orchestrator's own hands.
- Measuring debt as uncited codes may over-count checks whose rule is stated only in a docstring; a docstring is not a
  document a reader finds, so that count is intended.

## Not decided

- A blocking CI gate on either measure. Revisit when the report has run for several weeks.
- The designer's guide form (generated page beside the manual, or hand-written). Issue #122.
- How debt in the Railroad repo (libraries, drawings) is counted beyond the symbols manual.
