# 0007. KiCad services: the ownership split between Subdivision and kicad-primitives

- Status: accepted by the owner 2026-10-19 (rev 2, after the reviewer's second pass the same day (three qualifications and a round-trip note, §3.2; all accepted). The counter-proposal the adversarial review of ADR 0006 rev 4 asked for: "preserve ADR 0006's inventory and incident evidence, but replace its conversion mandate with this ownership split". ADR 0006 is now that evidence record; this document is the split.
- Decision (the owner, 2026-10-19): **shared development moves to the kicad-primitives effort now.** There is no intermediate step in which this repo first builds a new service layer that the package later ports. **Kept in Subdivision:** Railroad field ownership rules, mast and head interpretation, dated rulings, the `production/` conventions, urgent consumer workflows, and temporary migration adapters.
- Confirmed by the owner 2026-10-19: §2 as applied and §3's disposition of the findings.
- Date: 2026-10-19
- Sources: ADR 0006 (the evidence); the adversarial review of its rev 4 by the kicad-primitives orchestrator (2026-10-19); `kicad-primitives/AGENTS.md` (operating model, migration rule), ADR 0002, tickets #4, #8, #9, #12.
- Paths as in ADR 0006.

## 1. Problem

Two efforts hold one body of code. This repo has the scripts, the shared module and the gates that a week of SPCoast edits produced (ADR 0006 §3). The package is to be the one long-term home for shared KiCad I/O and names this repo as a donor. ADR 0006 rev 4 proposed to bridge them by converting our scripts into a service layer here, in the package's shape, for the package to lift later. The review rejected that as an unnecessary intermediate step and a design the package had not agreed to inherit, and accepted the evidence. What is left to settle is ownership: what of ours is railroad and stays, what goes to the package and in what form, and what we do here while the package is built.

## 2. The split

### 2.1 Why no intermediate step

ADR 0006 rev 4 proposed converting the scripts into a service layer here, in the package's shape, and lifting it later. The review rejected that as "not a necessary intermediate step": donor tooling is evidence, the package's namespaces are undecided, its write-philosophy ticket now requires one internal representation, and its migration rule places consumer compatibility adapters in consumers, not in the shared foundation (finding 9). The owner agreed. A layer built here now would be a second architecture to port, and a third copy of the text primitives beside jBOM's and kDoctor's, which is the thing ADR 0006 §1 records.

### 2.2 What stays in Subdivision

The owner's list, applied to ADR 0006 §3 and its Appendix A:

| Kept here | What that is in our inventory |
|---|---|
| Railroad field ownership rules | the Role lint (`C/lint_symbol_fields.py`), which fields each Role requires, the libraries-carry-no-instance-defaults rule (`421cff0`), and the two field-sync policies as rulings (which fields the library wins and which the instance keeps) |
| Mast and head interpretation | the railroad half of the pairing routine (odd pin is indication, even is aspect, unit N is head letter N, the mast on the net); the contact sheet's Role grouping; the overview's railroad presentation |
| Dated rulings | every script under `E/` and `S/`, as records; the next one too |
| `production/` conventions | derived files there, never beside the schematics; the baseline netlist named in the commit; the Verified section |
| Urgent consumer workflows | the ADR 0005 Caltrain edit and the cleanup pass (#30): written as dated scripts on the existing `K/sch_text.py`, with a gate script that fails (ADR 0006 L10), not a new layer |
| Temporary migration adapters | when the package offers a slice, the freeze-and-replace recipe and any shim live here (the package's migration rule); they are removed when the slice is adopted |

### 2.3 What goes to the package, and as what

Evidence, not design. The package decides contracts, representation and namespaces in its own tickets.

- ADR 0006 Appendix A, with its last column as candidate homes and the railroad rows marked, to the lift inventory (#9). The generic halves of the pairing routine and the library overview are offered; their railroad halves are not.
- ADR 0006 §3.3 L1 to L5 and L10 as incidents to the write-philosophy ticket (#4): what a connectivity-only gate missed, what "Update Symbols from Library" does, why a restore reads a baseline, which comparisons printed instead of failing. They support the verification distinctions that ticket has locked; they do not propose a library-versus-schematic split (finding 8).
- The list of §2.2 to the session ticket (#8), as the consumer's statement of what it keeps.
- L9 on the locator and its environment variable to #12.
- The donor-side defects in ADR 0006 §5, filed as issues, not fixed by us.
- When a port moves a capability out of `K/`, its tests and scenarios go with it (the package's operating model).

### 2.4 What we do here meanwhile

- `K/` and `C/` are frozen as they are: bug fixes and the lock check the paint script lacks, no new modules, no consolidation of the span and regex helpers into a package-ready implementation (finding 10 accepts them as temporary donor practice only).
- The next edit script is one more dated script in the existing style. That is named debt, accepted because the alternative is waiting on another repo's decision spine for a 68-field edit.
- Its gate script gates the expected delta, not equality alone: it requires the approved additions, removals and value changes to be present, rejects any other field change, and requires unchanged connectivity where the ruling promises it; it exits non-zero on any of those (ADR 0006 L10). An allow list alone permits a change without proving the required change happened. The field comparison is against the baseline netlist and is evidence of a wipe, not proof that the document was preserved (finding 3).
- A formatting round trip is claimed only after a controlled experiment. `kicad-cli sch upgrade --force` resaves a schematic regardless of version (verified in its help; the reviewer confirmed the same) and `sym upgrade` does the like for a library; `sch export netlist` is not a save and proves readability and connectivity only (finding 11). The experiment runs on disposable copies, because the upgrade command rewrites its input, and records three separate observations: our no-op save preserves the original bytes; KiCad accepts our edited output; KiCad's forced rewrite of our output produces the expected formatting. Until it has run, C8 below is a hypothesis. It is not a condition of the Caltrain edit.
- Cache refresh after a library edit is an explicitly approved Railroad workflow, not an automatic step: a wholesale rewrite of every sheet's embedded definitions can replace an intentional embedded difference and change unrelated content. For the Caltrain edit the script names the definitions and sheets it refreshes, preserves everything else, and the gate verifies the instance fields afterwards. It is not a precondition every schematic command enforces (finding 5), and it does not expand the edit beyond its approved purpose.

## 3. The review findings and their disposition

The review was of ADR 0006 rev 4, whose §4 proposed the conversion. All eleven findings are accepted. The place each changed is named; "0006" means the evidence record as it now stands.

| # | Finding (short) | Disposition |
|---|---|---|
| 1 | "The package inherits jBOM's definition" imports conventions #8 has not settled | accepted; 0006 §2 opening qualified |
| 2 | pairing from the baseline is part generic, part railroad | accepted, verified in `head-cast.py:217-225`; 0006 L4 and Appendix A split |
| 3 | a netlist field diff is evidence, not authority for document preservation | accepted; §2.4 here, 0006 Appendix A row reworded; C5 withdrawn as a gate definition |
| 4 | "contact sheet and overview stay here" is too broad | accepted; generic inspection offered to #9, railroad presentation stays (§2.2, 0006 Appendix A) |
| 5 | cache freshness is not a universal precondition | accepted; §2.4; C6 withdrawn |
| 6 | object ownership does not make gates unforgettable; the gate script prints | accepted, verified; 0006 L10 added; the rev 4 gates-as-preconditions section withdrawn |
| 7 | a staged write is not atomic | accepted, verified (the script writes library, sheets and project in sequence); the rev 4 workflow withdrawn, 0006 Appendix A row reworded |
| 8 | byte-equal for libraries and fields-equal for sheets is not the package's gate definition | accepted; §2.3 sends incidents, not a definition |
| 9 | the intermediate conversion step is unnecessary | accepted by the owner; §2.1 |
| 10 | spans versus tree is a false opposition; donor practice only | accepted; 0006 L5 reworded; §2.4 |
| 11 | `sch export netlist` is not a save | accepted, verified against `kicad-cli sch --help`; §2.4 names `sch upgrade` as the candidate instrument, untested |

### 3.2 Second pass

The reviewer read rev 1 of this document and returned three qualifications and one note, with the bottom line "proceed with the ownership split and the narrowly scoped Caltrain exception, subject to those verification corrections". All are accepted.

| # | Qualification (short) | Disposition |
|---|---|---|
| 12 | C11 "no new tests here" is too strong; freezing services is not freezing verification | accepted; C11 rewritten: no new architecture or framework, but consumer changes and gate behaviour get focused tests |
| 13 | C7 automatic whole-project cache replacement is too broad; it can replace intentional embedded differences | accepted; C7 and §2.4 narrowed to named definitions on named sheets as an approved step; ADR 0006 L2 reworded as a workaround with observed results |
| 14 | §2.4 and C5 must gate the expected delta, not equality alone; an allow list permits but does not prove | accepted; §2.4 and C5 rewritten: required changes present, no others, connectivity unchanged where promised |
| note | `sch upgrade --force` resaves regardless of version and is a credible round-trip instrument, not yet proof; run on disposable copies; three separate observations | accepted; §2.4 states the experiment that way and keeps it out of the Caltrain edit's scope |

## 4. Consequences

The labels in brackets are ADR 0006's first draft's. Several are withdrawn by §2 and are listed so the reader can see what changed.

- C1 (was D1, D11). The ten scripts stay as records; the next edit is one more dated script plus a gate script that fails on a false comparison. The ruling stays in the docstring, the gate output in the commit's Verified section.
- C2 (was D2). Withdrawn: no new layout of `K/` by areas, eleven or seven.
- C3 (was D3). The paint script gains the lock check the others have; jBOM's `check_write_permitted` is not adopted (ADR 0006 L6); issue to jBOM. No wider consolidation.
- C4 (was D4). The three `kicad-cli` locators stay until #12 closes; the finding is sent there.
- C5 (was D5). Every gate script from now on gates the expected delta (§2.4): required changes present, no other field change, connectivity unchanged where promised, against the baseline netlist. `C/netlist_diff.py` may gain `--fields` for the manual case. It is evidence, not a preservation guarantee.
- C6 (was D6). ERC with every severity stays a by-hand step named in the Verified section; it is the project's check and the package will own it.
- C7 (was D7). "Update Symbols from Library" is never run. When a library edit needs the embedded definitions refreshed, the script that made the edit refreshes the named definitions on the named sheets and nothing else, as an approved step of that ruling (§2.4; ADR 0006 L2 records the workaround and what it was observed to do).
- C8 (was D8). Builders write KiCad 10's own format; this is a hypothesis until the controlled round trip in §2.4 exists.
- C9 (was D9). Spans and the existing regexes stay as temporary donor practice; no consolidation here; #4 decides the representation.
- C10 (was D10). Upstream gets issues and evidence, not code (§2.3, §5).
- C11 (was D12, D13). No new shared-service architecture and no test-framework project here. Consumer changes and gate behaviour are verified: a changed lock check or a gate newly expected to fail gets a focused test that shows the failure. Tests for generic capabilities travel with their eventual ports; railroad-specific gate tests stay with the consumer. A restore reads its truth from a baseline netlist (ADR 0006 L3).

## 5. Follow-ups, not decisions

| Where | What |
|---|---|
| kicad-primitives | ADR 0006 Appendix A to #9; ADR 0006 §3.3 incidents to #4; §2.2 here to #8; ADR 0006 L9 to #12. |
| jBOM, kproj, kDoctor | the defects in ADR 0006 §5, as issues. |
| this repo | the next gate script fails on a false comparison and diffs fields (C1, C5); the paint script's lock check (C3); a controlled `sch upgrade` and `sym upgrade` round trip before C8 is claimed; the freeze-and-replace recipe when the package offers its first slice. |
