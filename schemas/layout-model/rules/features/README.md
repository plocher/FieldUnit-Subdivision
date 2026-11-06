# Model features

The derivation rules of the Layout Data Model File, as Gherkin features (ADR 0012 §3). Every writer of the file
must pass them: the reference derivation here, Studio later. A feature in this tree starts from facts of the file
(`given`, `relations`) and ends at `derived` facts or a rule check. Nothing here names a KiCad wire, pin, sheet or
symbol. The rules for reading a drawing are the importer's, in `tools/layout_compiler/features/`.

## Layout

- `logical/`: what the facts mean on the railroad: trackplan, office, code line, policy and demand tables. A rule
  answers "is this correct".
- `physical/`: how a logical fact is realised: field devices, encoders, drivers, transports. A rule answers "are
  these equivalent".
- Inside each: the seam (`trackplan/`, `field/`, ...), then one file per Role, or Role plus Appliance where Role is
  too wide (`appliance_switch_ceiling.feature`, `device_mast_head.feature`).

## Scenarios

- A scenario is one route through the rule, named in the user's words.
- A scenario that reports has its diagnostic code as a tag (`@train_order.station`). A Then step does not repeat it.
- The registry `../diagnostics.json` names one scenario per code as `file#scenario`, the file relative to this
  directory.
- `@pending` marks a rule that is stated before the reference derivation has it. Its code is `proposed` in the
  registry. behave does not run it; its steps exist and raise `Pending` with the issue.

## Steps

`steps/model_steps.py`. A Given is a table: one row per entity, `Name` its key, every other column a `given`
field, a column `relations.<key>` a stated relation; an empty cell states nothing.

## Run

    cd schemas/layout-model/rules/features && uv run behave --tags='not @pending'

`tests/test_rule_features.py` runs both roots and checks the registry links in the unittest run.
