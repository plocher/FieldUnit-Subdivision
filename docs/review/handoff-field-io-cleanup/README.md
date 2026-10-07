# Handoff: field I/O symbol cleanup and the generator POC (2026-10-06)

For a fresh session. Read AGENTS.md ("Working agreements") first, then `docs/design/goals.md` (PR #32) for the long-term
chain, then FieldUnit ADR 0003 (`FieldUnit/docs/adr/0003-field-io-symbols.md`, merged via PR plocher/FieldUnit#30). This file carries what the
ADR does not: where everything is, what is decided but not written anywhere else, how each pass is
verified, and what comes next. The scripts beside this file are the verification tools used so far.

## Where things are (all local paths under `~/Dropbox`)

| Repo | Path | Branch now | Tip | State (2026-10-07, after the merges) |
|---|---|---|---|---|
| FieldUnit-Subdivision | `workspace/FieldUnit-Subdivision` | `main` | `068535d` | PRs #27 and #28 merged: `docs/adr/0001–0003` and `docs/design/` are on `main`. PR #32 (open) adds `docs/design/goals.md` and `docs/archive/part-c-ontology/`; the two old September branches were salvaged into it, tagged `archive/feature/*`, and deleted. Issue #31 tracks documentation-set generation. |
| Railroad (KiCad projects) | `KiCad/Railroad/SPCoast/` | `sandbox/sargent-field-io` | `4105493` | `main` = `67b368a` = tag `split-projects-final`; the sandbox is 3 baseline commits beyond it. All merged branches deleted. |
| InterlockingPlant (symbol libraries) | `KiCad/InterlockingPlant/symbols/` | `main` | `1eed088` | no remote; tag `split-projects-final` pairs with Railroad's; `Railroad`, `RailroadPanel`, `RailroadField` all tracked (AGENTS.md's "not in git" is out of date). |
| FieldUnit (C++ library) | `Arduino/libraries/FieldUnit` | `main` | `54ef63b` | PRs #27, #28, #30 merged: ADR 0003 is `docs/adr/0003-field-io-symbols.md` on `main`. All merged branches deleted. |

Netlists (`*.net`) and `*-plant.json`/`*-field.json` are derived and ignored; always `make -B netlist` in a
project before reading it (a stale `.net` bit us once). KiCad lock files `~*.lck` mean the owner has the
project open: never edit a locked project; scripts must skip locked sheets themselves.

## Decided, and where it is written

- Circuit classes, END_CTC, CP on the IRJ-Signal, STRUCTURE roles, Interlocking symbol, `Virtual Indication`,
  exposure by demand: Railroad `main` history (PR #2 and the commits after it) and the owner's memory notes.
  Issue #24 here records the CP rule; #30 is the cleanup epic; #13 the unification.
- Field I/O vocabulary: ADR 0003 (D1–D11, Kind table, rules, naming axioms, worked examples for Sargent 835
  and Luchessa 783). Nothing in it is implemented yet.
- Only in conversation so far (not in any file but this one):
  - Authoritative interlocking names have spaces (`Gilroy Caltrain`, `Gilroy Interchange`); names are
    compared ignoring spaces, case, `-`, `_`. Done in the drawings; the desk compiler still takes the
    interlocking from the sheet name, which is a bug to fix by reading `PanelColumn.Interlocking`.
  - References are anonymous; the unified project will renumber them `sheet# * 1000 + old`.
  - Unification (#13): one project `SPCoast`; machines (`South-cTc`, later Central/North) as first-level
    sheets; under each interlocking: Trackplan, Panel, Field I/O (Field I/O as a child of the Trackplan,
    interim); old projects archived read-only, new project built from scratch; parity gates = the net
    counts below, desk 341 nets / 677 components, clean ERC. Not started.
  - Deferred to a later "Studio" editor: a panel scaffold generator and any panel-from-trackplan derivation.
  - DoT policy markers carry no track-name Value (the circuit on the same net names the track); the
    compiler's `missing_policy_track_name` check is wrong and goes in #30 step 3.
  - A bumper dead end and an END_CTC both cap routes at RESTRICTING; today only `DARK_EXIT` does
    (`tools/plant_graph/indications.py`, `_derive_static_indication`); the fix changes the Luchessa golden.

## Current per-plant net counts (gates for any pass)

Christopher 30, Corporal 27, GilroyCalTrain 28, GilroyInterchange 23, Luchessa 35, Sargent 19 (plus the
sandbox devices), Watsonville 99, South-cTc 341 nets / 677 components; desk compiles to 75 appliances,
137 bindings, 14 columns (`tools/parse_kicad_controller.py`).

## Next: three scripted passes, then the generator POC

PR #30 is merged; the passes may start once the owner says go.

1. **Field library** (`InterlockingPlant/symbols/RailroadField.kicad_sym`), per ADR 0003 "Consequences":
   rename symbols and Kinds to the table; pin names to the `~{X}` convention (asserted-low on every BIT pin);
   a blank polarity attribute per BIT pin; `NormalIs`, `Hold_ms`, `Pullups` where listed; delete
   `Device-Switch-ElectricLock`, `-HandThrow`, `-Turtle` (becomes `-StallMotor-Sensed-OS`), `Device-Signal-*`,
   `Device-Digital_*`; `Local-Lock` → `~{WLS}`/`~{WLK}`, `Local-Lock-2Lamp` adds `WLK`; add `Local-Lamp`,
   `-PWM`, `-NeoPixel`; Role `PANEL` on `Local-*`; `IODriver` → `IODRIVER`. Commit as its own baseline
   there first (the owner's state), then the pass as a second commit.
2. **Desk and plant libraries**: Role `APPLIANCE` → `PANEL` on `PanelSwitch/Lock/Signal/Lamp-*/MCall/Code`;
   reconcile `PanelLock` pins to `WLS`/`WLK` (ADR 0003 O3); plant `Switch_Lock` Kind `SWITCH_LOCK`;
   `Switch_Manual`, `Switch_Manual_Sensed` stay. Then `sweep_role_kind_fields.py` over the South-cTc sheets
   (it refreshes instance Role/Kind from the library by `lib_id` and drops stale fields) and
   `tools/controller_graph/compiler.py` `_ROLES` gains `PANEL`.
3. **Sargent sandbox** (`Railroad`, branch `sandbox/sargent-field-io`): rewrite `lib_id`s to the new names;
   `ELEC_LOCK 835` → `Device-Switch-Sense 835` + `Local-Lock 835`; `HAND_THROW 1` → `Device-Switch-Sense 1`;
   remove the `PanelLock`/`PanelSwitch` placeholders; refresh instance Role/Kind. Verify with
   `field_resolve.py` (every device resolves to a plant item, every pin to one driver pin of the right
   channel type, no shared driver pins, addresses unique).
4. **Generator POC** (scratch, then `tools/`): from the Sargent netlist emit one FieldUnit driver constructor
   per device symbol and compile against `FieldUnit/src` (stubs for the drivers the ADR lists as new).
   Compiling is the proof that Kind → class and pin → constructor parameter hold. Then #30 step 3 proper:
   the `(Role, Kind)` table with the ADR's columns, library-by-`lib_id` reads, END_CTC and dead-end caps,
   CP from the IRJ-Signal, the gates (empty netlist, `.kicad_pro` UUID mismatch, desk token with no plant
   circuit, lamp Color vs symbol variant).

## How every pass was verified (do the same)

- Baseline first: commit the owner's saved state as its own commit before any scripted change.
- Per-symbol before/after comparison (`verify_symbol_diff.py`): same symbol set (by uuid), same `lib_id`,
  same position; only the intended properties changed. Print anything unexpected and stop.
- `make -B netlist` in every touched project; net counts unchanged unless the change adds pins.
- Desk: `parse_kicad_controller.py` still 75/137/14; plant: `parse_kicad_plant.py --format text` diagnostics
  compared before/after.
- Root-UUID regression check: no `.kicad_sch` or `.kicad_pro` outside `Luchessa/` contains
  `87b90fc6-5e27-4e06-8416-fb28e674fdea` (the copy bug from the project-creation script; a GUI save
  restores it if the `.kicad_pro` still carries it).

## Known debts to file or fix along the way

- AGENTS.md: the libraries are in git (`InterlockingPlant` repo); `Switch_HandThrow` is gone; the station
  cutover checklist predates the unification plan.
- Desk compiler: interlocking from `PanelColumn.Interlocking`, Role `PANEL`, `CMRI` kind.
- FieldUnit: `ElectricLockDriver` is not needed (lock is firmware) but local-client demands on `Switch`,
  the unlock-request indication, the locked-and-reversed rule, mux/PWM head drivers, servo switch driver,
  `IOBus` duty write, and `Hold_ms` on the optical detector are.
- ADR 0003 open items O1 (unlock-request token), O2 (which Luchessa switches use `-OS` cables), O3
  (`PanelLock` pins).
