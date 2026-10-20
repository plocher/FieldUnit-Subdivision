# 0006. KiCad services: inventory and incident evidence from the SPCoast edits

- Status: evidence record, accepted by the owner 2026-10-19 (rev 6). No decision was asked here. Revs 1 to 4 of this number also carried a conversion design; the kicad-primitives orchestrator's adversarial review of rev 4 (2026-10-19) accepted the document "as an inventory and incident report" and rejected the conversion design, and recommended "a separate counter-proposal: preserve ADR 0006's inventory and incident evidence, but replace its conversion mandate with this ownership split". The owner agreed. The ownership split is ADR 0007; this document is the evidence it and the package's tickets cite.
- Date: 2026-10-19
- Sources: jBOM `docs/design/service-command-architecture.md`, `architecture-overview.md`, `anti-patterns.md`, `bdd-axioms.md`, ADR 0013, ADR 0014; `kicad-primitives/AGENTS.md`, `CONTEXT.md`, ADR 0001 and ADR 0002 (both accepted 2026-10-19); `docs/review/kicad-services-survey-2026-10-12.md`; the ten edit scripts under Railroad `SPCoast/edits/` and `symbols/edits/`; the field-reset incidents (Railroad `e18f56a`, `421cff0`); the adversarial review of rev 4.
- Scope: the Python that reads and edits `.kicad_sch` and `.kicad_sym` for SPCoast and the four Railroad libraries, the gates around such edits, and the process we ran them under, as they are. What moves where is ADR 0007.
- Paths: `E/` is `~/Dropbox/KiCad/Railroad/SPCoast/edits/`, `S/` is `~/Dropbox/KiCad/Railroad/symbols/edits/`, `K/` is `tools/kicad_services/`, `C/` is `tools/contract/`.

## 1. What this records

Between 2026-10-12 and 18 we migrated every SPCoast sheet to the four Railroad libraries, rebuilt the head device chain three times, restored 94 fields that KiCad's "Update Symbols from Library" had wiped (twice), synced instance fields to the libraries and painted 29 driver bodies. That work produced three things worth keeping: code, a process, and learnings. All three exist only as ten scripts that copy each other (Appendix A), one 99-line shared module with no tests, and the memory of the people who ran them.

§2 gives the vocabulary used to sort the inventory, which is the package's own. §3 is the inventory, the process and the learnings. §4 lists the defects and open questions in what we have. §5 lists the donor-side defects found in jBOM, kproj and kDoctor on the way. Appendix A is the piece-by-piece inventory with a candidate home for each; Appendix B shows what the other donors already cover.

## 2. What a service is

The definition is jBOM's, which the package takes as its architectural starting point, plus the package's own decision on what its public surface is. Which of jBOM's conventions transfer (diagnostics tuples, CLI-first testing, constructor rules, force and backup, a friend serializer) is not settled by inheritance; the package's ADR 0002 leaves detailed contracts and execution strategy open, and its seam ticket (#8) exists to decide what transfers (review finding 1).

### 2.1 jBOM's layers and axioms

| Layer | What lives there | Rule |
|---|---|---|
| `common/` | pure functions, frozen dataclasses, constants, the domain types every layer speaks | stateless; no `__init__` with instance state; imports nothing outside itself |
| `services/` | business processes with state established at construction | **"the presence of an `__init__` method with instance variables is what makes something a service"**; strategy by constructor parameter, not injected objects; private factories build internal state |
| `application/` | workflows: `.run(request) -> result`, request and result as frozen dataclasses, result carries the artifact and a `tuple[str, ...]` of diagnostics | orchestration only, no business logic; three to five services in sequence; file writing delegated to a friend serializer |
| `cli/` and the plugin | adapters | exactly four jobs: parse, build the request and `.run`, render diagnostics, map to an exit code; about 50 lines or logic has leaked |

Dependencies flow inward only: `cli → application → services → common`.

The axioms that bind every layer (`anti-patterns.md`, `service-command-architecture.md`):

- **Command or query, never both.** A command produces a new object and does not mutate its input; a query reads and returns.
- **Diagnostics are data.** A service returns the full set as structured values; the adapter decides what to show. No `print`, no `os.environ` gating inside a service.
- **Typed results, not dicts.** A result dataclass is the contract; an adapter never calls a private method on what it gets back.
- **No file I/O in a constructor.** Reading is a reader's job; the service takes domain objects.
- **Shared helpers are pure functions in `common/`**, never one service reaching into another's private method.
- **File safety is a service concern.** A production artifact is never overwritten without `--force`, and `--force` makes a timestamped backup first; this holds for every adapter.
- **Test through the thin CLI** (BDD axiom 4): define the service API, wrap it in a thin CLI, test the CLI, add the plugin on the same API.
- **Jobs** (ADR 0014): one adapter-neutral shape, `JobRequest`, `JobContext`, ordered `JobEvent`s, `JobResult` with outcome, artifacts and the event stream. Where that seam sits relative to the package is the package's open ticket #8.

### 2.2 kicad-primitives' public surface (ADR 0002, accepted today)

- Public interfaces say **what a client accomplishes, not how**. The eleven mechanism areas of the survey (text, sexp, cli, checks, runtime and so on) are superseded; the public surface is seven **functional areas**: Projects, Schematics, PCBs, Symbol libraries, Footprint libraries, Library tables and resolution, Connectivity. They are not seven entry points or final namespace names.
- **Ownership.** A project owns its schematics and PCBs and the public interface does not open them independently. Library services own reusable definitions; document services own placed instances and embedded (cached) definitions. They share internal machinery.
- **Checks belong to the object checked.** Project ERC is the project's; a scoped check honours its scope or rejects it. "Preconditions and postconditions belong to each abstraction, not to a separate public checks area."
- **Connectivity belongs to project context**, built through CLI export and parsing or directly from the loaded design; a netlist file is an exchange dataset that can lack provenance and freshness.
- **Internal, not public:** parsing (`sexp`), byte-preserving text editing, runtime safeguards (locks), and KiCad integration (`kicad-cli`), which is provisional machinery.
- **Capability profile:** used, unused, unimplemented, inventoried from actual usage, never guessed from donor code. An exposed but unimplemented operation raises an unsupported-operation exception before changing anything. Parity equals used capabilities; the owner locks the 1.0 bar.
- **Operating model:** package work does not wait on consumer migration; a ready slice becomes an issue on the consumer's tracker with a freeze-and-replace recipe; ports bring their donor tests; functional gates (byte round trip, netlist connectivity) over fixtures; one parser; each fact one source; debt is not policy.

### 2.3 In one sentence

A service is a stateful object configured once that performs one business process on domain objects and returns typed results and diagnostics; pure helpers sit below it, a workflow orchestrates several of them above it, and an adapter that only parses, runs, renders and exits sits on top. In the package, a client reaches services through seven functional areas that own their documents and their checks, and never through the file format.

## 3. What we built here

The work product, sorted by what it is in the vocabulary of §2. Appendix A lists every piece with its file and line; Appendix B shows what jBOM, kproj and kDoctor already cover. The review accepted this section and the appendices as the inventory and incident report; its corrections (findings 2, 6 and 10) are applied in L4, L5 and L10.

### 3.1 Code

| Kind (§2) | What we have | State |
|---|---|---|
| pure functions over file text (internal: text) | quote-aware node spans by head and depth, end of a node, non-overlapping span replacement; property locate, set, add, drop, rename, duplicate; `num`, `uid`; builders for library nodes (`prop`, `pin`, `rect`, `text`, `polyline`, arrowhead, `symbol`, multi-unit symbol) and sheet nodes (`instance`, `wire`, `label`, `junction`) | the first three in `K/sch_text.py` (99 lines, no tests); the rest copied two to seven times across `E/` and `S/` |
| document models (readers) | the symbol-library model with units, `extends`, locked and autoplace (`library_symbols`); the netlist model, components, fields, nets and nodes (`NetlistReader`); the placed-instance read (`lib_id`, `at`, `unit`, `path`, fields); cached pin geometry and shown fields from a sheet's `lib_symbols` | `K/`; the instance read exists five times in `E/` |
| operations on a symbol library (Symbol libraries) | retire a symbol; append symbols; rename a symbol or a pin; paint a unit body; fields owned by the library | `E/`, `S/`, one to three copies each |
| operations on a schematic (Schematics) | replace an instance's `lib_id`; complete a multi-unit instance; sync instance fields to the library under two policies (`library_wins`, `fill_empty`); restore per-instance fields by reference; write a cache entry from a library symbol, add and remove entries; drop wires, labels and junctions at points; annotate | `E/`, one to two copies each |
| operations on the project (Projects) | edit `.kicad_pro` ERC severities (as text; it is JSON) | `E/`, once |
| checks (belong to the object checked) | lock files present (`~*.lck`); cache entry stale against the library; ERC with every severity; netlist connectivity equal; netlist fields equal, with an allow list; pairing taken from the baseline netlist, never coordinates | lock: six copies and one script without; cache staleness and field diff: ad hoc; ERC: by hand |
| railroad domain (stays here) | field lint by Role; symbol contact sheet; the library overview page | `C/`, `tools/` |
| KiCad integration (internal) | `kicad-cli` locator; netlist export; ERC run; `sym export svg`; Fontconfig noise dropped | three locators |

### 3.2 Process

What every bulk edit ran under, by hand (Railroad `AGENTS.md`; the commit bodies of `421cff0`, `1d8aaea`):

1. Check for a lock file or a running KiCad before touching a sheet or library.
2. Commit the owner's current drawing as a baseline, so the change is an auditable diff.
3. Write the edit as a dated script whose docstring states the ruling it applies; keep it beside what it changed; a gate script beside it when the ruling needs one.
4. Export the netlist before, into `production/`; run the script with `--dry-run`, read its report; run it for real.
5. Export the netlist after; diff connectivity; run ERC with every severity; run the Role lint; render the contact sheet when a library changed.
6. Commit with a "Verified:" section naming the gates and their result. Never push unasked.

### 3.3 Learnings

Each from a thing that went wrong or nearly did:

- L1. **A gate on nets passes a field reset.** Both incidents (2026-10-17 and 18) wiped per-instance fields and the connectivity diff was clean. The gate the process lacked is a field diff against the baseline netlist, with an allow list the script declares.
- L2. **"Update Symbols from Library" is the operation that resets fields.** The workaround we used instead, after a library edit, was to rewrite the edited symbols' `lib_symbols` entries on the sheets that use them from the library file (`cast-chain.py:276-283`, `migrate-libraries.py:224-242`); observed result: the embedded definitions matched the library and the instance fields were untouched on those runs. This is a per-ruling step with named definitions and sheets, not a universally safe whole-project replacement: a wholesale rewrite could replace an intentional embedded difference or change unrelated content (second review, qualification 2).
- L3. **A restore reads its truth from the baseline netlist**, not from a table in the script: the 2026-10-17 table reused on the 18th wrote stale values into 32 Addresses.
- L4. **Pairing comes from the netlist; geometry is a one-off.** Placement by fixed offsets, wire removal by coordinate match and the refusal of rotated instances have no general form; the connectivity side does. The pairing routine itself mixes the generic part (which references share a net) with railroad meaning (an odd pin is an indication input, an even pin an aspect output, unit N is head letter N); only the first is a package capability (review finding 2).
- L5. **A write that leaves untouched bytes untouched is what makes a diff reviewable**; a whole-file re-serialisation (jBOM's `sexpdata.dumps`) hides the edit. Whether that is done by spans over text or by a source-preserving tree is the package's write-philosophy ticket (#4); the two are not opposites (review finding 10).
- L6. **The lock KiCad 10 writes is `~<file>.lck`**; jBOM's check looks for `<base>.lck` and never fires. Whether the Symbol Editor writes one for an open library is unverified.
- L7. **The libraries carry no per-instance defaults** (since `421cff0`), so a future reset leaves blanks rather than wrong values; a lint for blank required fields is the companion.
- L8. **Helpers copied forward script to script** become six lock checks of which one is missing. Each fact one source applies to tooling too.
- L10. **A gate that prints is not a gate.** The head-cast gate script reports each comparison with `print` and exits zero whatever it finds; it is evidence a person reads, not an enforced guarantee (review finding 6, verified in `E/2026-10-18-head-cast-gate.py:40-88`).
- L9. Smaller: `uuid4` makes a re-run unreproducible (the retired unifier used `uuid5`); `.kicad_pro` is JSON; span locators key on exact tab depth and no script checks `(version …)`; `kicad-cli` prints Fontconfig noise on stderr; the three locators disagree on the environment variable (`KICAD_CLI` here and in `kicad.mk`, `KPROJ_KICAD_CLI` in kproj).

## 4. Defects and open questions in what we have

1. Depth coupling: `blocks` keys on exact tab depth (`K/sch_text.py:35`) and `(version 20251024)` is never checked.
2. Geometry by convention (L4): a script that moves symbols stays a one-off.
3. Reference allocation: `Counter(12)` hard-codes where the previous pass stopped (`mast-chain.py:241`); `annotate` scans one sheet.
4. `uuid4` (L9): a re-run never reproduces a diff.
5. Unverified: that the cache re-indent in `cached` (`cast-chain.py:280`) is safe for every body; kDoctor's does not re-indent at all.
6. Unverified: whether KiCad writes a lock for a library open in the Symbol Editor; the lock check globs `symbols/` on the assumption it does.
7. `Archive/SPCoast/kicad.mk` has no ERC rule and stale defaults (survey decision 10); the unified project has no Makefile. Out of scope; noted so it is not forgotten.

8. The gate script prints and never fails (L10); the staged write is sequential, not atomic (library, sheets, project in turn, `E/2026-10-18-head-cast.py`).
9. No formatting round trip has been run. `kicad-cli sch export netlist` is not a save; `kicad-cli sch upgrade --force` resaves a schematic regardless of version and `sym upgrade` a library, and they are the candidate instruments, untested. The experiment is defined in ADR 0007 §2.4.

## 5. Donor-side defects found on the way

Filed as issues, not fixed by us.

| Repo | Defect |
|---|---|
| jBOM | `ProjectContext.lock_file` is `<base>.lck`; KiCad 10 writes `~<file>.lck`, so `check_write_permitted` never fires (`project_context.py:79`). |
| kproj | `find_kicad_cli` reads only `KPROJ_KICAD_CLI`; every other repo and `kicad.mk` use `KICAD_CLI`. |
| kDoctor | `_restore_one_symbol_sexpr_replace` does not re-indent and cannot add or remove cache entries; `_extract_named_symbol_block` is not quote-aware. |

## Appendix A. Inventory of what was built, with where each piece lands

The last column names the kicad-primitives functional area (its ADR 0002) or the internal layer a piece lands in, or says that it stays here. The last column is a candidate home for the capability, not acceptance of the implementation named in the row (review, §2 closing); ADR 0007 says what is offered to the package's lift inventory ticket (#9) and what stays.

| Group | Primitive | Where it is written today (`file:line`) | Copies | Area |
|---|---|---|---|---|
| read | netlist: components, fields, nets, nodes | `K/netlist_reader.py:37` `NetlistReader.read`; used by `C/netlist_diff.py:24`, `E/2026-10-18-head-cast-gate.py:13`, `E/2026-10-18-head-cast.py:344` | 1 | Connectivity |
| read | library symbols: fields, pins, `extends`, units, locked, autoplace | `K/sch_text.py:73` `library_symbols`; standard fields `:60` | 1 | Symbol libraries |
| read | library fields owned by the library, by `lib_id` | `E/2026-10-16-sync-library-fields.py:62`; `E/2026-10-17-cast-chain.py:320` `lib_fields`; `E/2026-10-12-migrate-libraries.py:117-126` | 3 | Symbol libraries |
| read | unit body (largest rectangle) | `C/lint_symbol_fields.py:58` `library_bodies`; `E/2026-10-18-paint-driver-bodies.py:31` `body_rect` | 2 | Symbol libraries |
| read | pins of a library symbol with position and type | `E/2026-10-18-head-cast.py:81` `PIN_RE`; `E/2026-10-12-migrate-libraries.py:130` `unit_pins` | 2 | Symbol libraries |
| read | placed instance: `lib_id`, `at`, `unit`, `path`, fields | `E/2026-10-17-cast-chain.py:348-359`; `E/2026-10-17-mast-chain.py:147-154`; `E/2026-10-18-head-cast.py:230-245`; `E/2026-10-16-sync-library-fields.py:78-86`; `E/2026-10-12-migrate-libraries.py:245-256` | 5 | Schematics |
| read | cached pin geometry from a sheet's `lib_symbols`; shown fields of a symbol | `E/2026-10-18-head-cast.py:199` `cached_pin_dx`, `:188` `symbol_shown_at` | 1 | Schematics, Symbol libraries |
| locate | node spans by head and depth; end of a node (quote-aware) | `K/sch_text.py:33` `blocks`, `:15` `end_of` | 1 | internal: text |
| locate | top-level symbols `{name: span}` | `E/2026-10-17-cast-chain.py:172`; `E/2026-10-12-migrate-libraries.py:87`; `S/2026-10-12-four-libraries.py:25`; `S/2026-10-13-head-set.py:25` | 4 | internal: text |
| locate | properties of a block `{name: (value, start, end)}` | `E/2026-10-17-cast-chain.py:179` `props_in`; `E/2026-10-16-sync-library-fields.py:40`; `E/2026-10-12-migrate-libraries.py:94`; `E/2026-10-17-restore-reset-fields.py:114` | 4 | internal: text |
| locate | the `lib_symbols` section | `E/2026-10-17-cast-chain.py:284`; `E/2026-10-12-migrate-libraries.py:224`; `E/2026-10-18-head-cast.py:201` | 3 | Schematics |
| locate | `num()` coordinate format; `uid()` | `E/2026-10-17-cast-chain.py:51`, `:56` | 1 | internal: text |
| mutate | set a property value (escape-aware) | `E/2026-10-17-cast-chain.py:187`; `E/2026-10-16-sync-library-fields.py:48`; `E/2026-10-17-restore-reset-fields.py:95`; `E/2026-10-12-migrate-libraries.py:103`; `S/2026-10-12-four-libraries.py:33`; `S/2026-10-13-head-set.py:33` | 6 | internal: text |
| mutate | add a property (hidden, at the origin) | `E/2026-10-16-sync-library-fields.py:57`; `E/2026-10-12-migrate-libraries.py:111` | 2 | internal: text |
| mutate | drop, rename, duplicate a property | `E/2026-10-17-cast-chain.py:197`, `:205`, `:210`; `S/2026-10-13-head-set.py:45`, `:53`; `E/2026-10-12-migrate-libraries.py:154-157`, `:166` | 3 | internal: text |
| mutate | rename a symbol, rename a pin | `S/2026-10-12-four-libraries.py:44`; `S/2026-10-13-head-set.py:57`, `:61` | 2 | Symbol libraries |
| mutate | retire a symbol; append symbols before the closing paren | `E/2026-10-17-cast-chain.py:226-240`; `E/2026-10-17-mast-chain.py:84-97`; `E/2026-10-18-head-cast.py:148-162` | 3 | Symbol libraries |
| mutate | replace a unit body's stroke and fill | `E/2026-10-18-paint-driver-bodies.py:42` `paint` | 1 | Symbol libraries |
| mutate | replace an instance's `lib_id`; complete a multi-unit instance | `E/2026-10-12-migrate-libraries.py:264`, `:188` `complete_units` | 1 | Schematics |
| mutate | sync instance fields to the library (two policies) | `E/2026-10-16-sync-library-fields.py:74`; `E/2026-10-12-migrate-libraries.py:141` | 2 | Schematics |
| mutate | restore per-instance fields by reference | `E/2026-10-17-restore-reset-fields.py:104` | 1 | Schematics |
| mutate | cache entry from a library symbol; add and remove entries | `E/2026-10-17-cast-chain.py:276` `cached`, `:283` `update_cache`; `E/2026-10-12-migrate-libraries.py:224-242` | 2 | Schematics |
| mutate | drop wires, labels, junctions at points | `E/2026-10-18-head-cast.py:258-278` | 1 | Schematics |
| mutate | annotate an unannotated reference | `E/2026-10-17-cast-chain.py:426-429` | 1 | Schematics |
| mutate | edit `.kicad_pro` ERC severities | `E/2026-10-18-head-cast.py:325` (string replace in JSON) | 1 | Projects |
| mutate | apply non-overlapping span edits | `K/sch_text.py:41`; `E/2026-10-17-cast-chain.py:216` `splice`; inline in `E/2026-10-18-paint-driver-bodies.py:68`, `E/2026-10-16-sync-library-fields.py:108`, `E/2026-10-17-restore-reset-fields.py:127`, `E/2026-10-12-migrate-libraries.py:240`, `:269` | 7 | internal: text |
| build | library nodes: `_prop`, `_pin`, `_rect`, `_text`, `symbol`, multi-unit symbol, arrowhead | `E/2026-10-17-cast-chain.py:61-102`; `E/2026-10-17-mast-chain.py:53`; `E/2026-10-18-head-cast.py:86`, `:99` | 1 | internal: text; Symbol libraries |
| build | sheet nodes: `instance` (three variants), `wire`, `label`, `junction` | `E/2026-10-17-cast-chain.py:293-317`; `E/2026-10-18-head-cast.py:166`; `E/2026-10-17-mast-chain.py:120`, `:136` | 3 | Schematics |
| gate | lock file | six `main`s (`sync-library-fields.py:122`, `restore-reset-fields.py:143`, `cast-chain.py:450`, `mast-chain.py:234`, `head-cast.py:338`, `migrate-libraries.py:282`); none in `paint-driver-bodies.py` | 6 | internal: runtime safeguard |
| gate | netlist diff of nets | `C/netlist_diff.py:23` | 1 | Connectivity |
| gate | netlist diff of fields and parts (prints, does not fail) | `E/2026-10-18-head-cast-gate.py:74-88` (ad hoc) | 1 | Connectivity (the comparison); evidence of a wipe, not proof of preservation |
| gate | pairing from the baseline netlist, never coordinates: the generic part (references on one net) | `E/2026-10-18-head-cast.py:209` | 1 | Connectivity |
| gate | pairing: the railroad part (odd pin = indication, even = aspect, unit N = head letter N, the mast on the net) | `E/2026-10-18-head-cast.py:217-225` | 1 | railroad domain (ADR 0007) |
| gate | ERC with `--severity-all` | by hand (commit bodies `421cff0`, `1d8aaea`); no rule in `Archive/SPCoast/kicad.mk` | 0 | Projects (ERC is the project's) |
| gate | `lib_symbol_mismatch` in Python | none | 0 | Schematics (cache precondition) |
| gate | render via `kicad-cli sym export svg`; generic library inspection in the overview | `C/symbol_contact_sheet.py:32`; `tools/kicad_library_overview.py:173` | 2 | internal: KiCad integration; generic inspection is donor material (#9) |
| gate | the contact sheet's Role grouping and the overview's railroad presentation | `C/symbol_contact_sheet.py`; `tools/kicad_library_overview.py` | 2 | railroad domain (ADR 0007) |
| gate | field lint by Role | `C/lint_symbol_fields.py:81` | 1 | railroad domain (ADR 0007) |
| process | `kicad-cli` locator | `K/netlist_reader.py:283`; `C/symbol_contact_sheet.py:27`; `tools/kicad_library_overview.py:117`; pass-through `tools/parse_kicad_plant.py:74`, `tools/parse_kicad_controller.py:32` | 3 | internal: KiCad integration |
| process | dry run, report list, write all at the end (sequential writes, not atomic) | every `E/` script's `main` | 8 | consumer workflow (ADR 0007) |
| process | derived files in `production/`; dated script plus gate | Railroad `AGENTS.md`; `E/2026-10-18-head-cast-gate.py` | convention | consumer process (ADR 0007) |

## Appendix B. What already covers each primitive

| Primitive | `tools/kicad_services` | jBOM 7.10.2 | kproj 0.13.4 | kDoctor `poc/` | Verdict |
|---|---|---|---|---|---|
| s-expression read to a tree | the three readers call `jbom.common.sexp_parser.load_kicad_file` | `common/sexp_parser.py:19` `load_kicad_file`, `:35` `walk_nodes`, `:66` `find_child`, `:87` `find_all_children` | wraps jBOM | regex and balanced parens, by choice | covered, reading only |
| node spans, quote-aware | `sch_text.py:15`, `:33`, `:41` | none | none | `location_service.py:34` `_scan_balanced_block` (does not skip strings); `symbol_lineage_service.py:76` `_extract_named_symbol_block` (`str.find`, no depth) | ours is the stronger; no tests |
| property get, set, add, drop | none (scripts) | `annotation_service.py:558`, `:584`, `:604`, `:612`: private, on the tree, written by `sexpdata.dumps` (`:199`, `:365`), whole-file reformat | none | `symbol_lineage_service.py:208` (read only) | jBOM has the semantics; no byte-preserving writer anywhere |
| library symbol model with units | `sch_text.py:73` (units by pin name); `symbol_library_reader.py:26` (flattens units) | none | none | `symbol_lineage_service.py:133` `_resolve_extends_block`, `:122` `_extract_pin_kinds` | ours; `extends` resolution is kDoctor's to borrow |
| cache entry from library; refresh | none | none | none | `symbol_lineage_service.py:322`, `:326`, `update_from_parent` `:502`: replaces one existing entry by `str.replace`, no re-indent, no add or remove, library via `sym-lib-table` (`:246`) | kDoctor covers one existing entry; `cached` + `update_cache` cover add and remove |
| cache staleness (`lib_symbol_mismatch` in Python) | none | none | none | `classify_symbol` `:351`, `deep_diff_symbol` `:434` | kDoctor covers it, with hard-coded `${KICAD10_*}` defaults |
| placed instance read | `schematic_reader.py:12` (transform only) | `services/schematic_reader.py:28` `load_components` (BOM view; no unit, pins, path) | none | `sch_symbol_transfer.py:93`, `:164` (uuid regen, instances path) | three partial views |
| builders; multi-unit completion; field sync policies | none | none | none | none | scripts only |
| lock check | none | `kicad_runtime.py:52` `check_write_permitted`, `project_context.py:79` `lock_file` = `<base>.lck` | none | `symbol_lineage_service.py:173`, `:198` (`~*.lck`) | jBOM's checks a name KiCad 10 does not write |
| `kicad-cli` locator | `netlist_reader.py:283` | `gerber_service._find_kicad_cli` (private) | `common/kicad_install.py:120` `find_kicad_cli` (`KPROJ_KICAD_CLI`; verified it returns the bundle path) | `erc_drc_summary.py` | kproj's is the strongest; env var differs |
| netlist export; connectivity diff; field diff | `netlist_reader.py:271`; `C/netlist_diff.py`; ad hoc `head-cast-gate.py:74` | none | none | `renumber_power_refs.py` ("netlist byte-identical") | ours; field diff is a gap |
| ERC run and parse | none | none | `design_analyzer.py:107`, `:158` (`--severity-all` `:201`), `:231`; `subprocess_runner.py:232`, `:156` Fontconfig filter | `erc_drc_summary.py:150`, `:126` | kproj covers run and parse; kDoctor the interpretation |
| `sym export svg`, `sym upgrade` | `C/symbol_contact_sheet.py:32` | none | `schematic_exporter.py:56` (`sch` only) | none | ours; `sym upgrade` nowhere yet |
| dry run, report, write at end | per script | `check_write_permitted(dry_run=)` | `WriteTracker` (site files) | `SymbolUpdateResult(dry_run=)` | the pattern exists everywhere; ours is per script (ADR 0007 §2.4) |
