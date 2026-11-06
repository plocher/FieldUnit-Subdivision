# Import features

How the KiCad importer turns a drawing into facts of the Layout Data Model File, as Gherkin features. A feature
in this tree starts from a drawing (placed symbols, pins, nets) and ends at the `given` and `relations` written, or
an import diagnostic. These rules belong to the importer and retire with it (ADR 0012 §3.3): Studio draws no wire
and never runs them. The rules about the model itself are in `schemas/layout-model/rules/features/`.

## Layout

The seam (`trackplan/`, `field/`, ...), then one file per Role, or Role plus Appliance where Role is too wide, with
the same file names as the model features of the same rule.

## Scenarios

- A scenario is one route through the rule, named in the user's words.
- A scenario that reports has its import diagnostic code as a tag (`@train_order.track`).
- The registry `../diagnostics.json` names one scenario per code as `file#scenario`, the file relative to this
  directory.
- `@pending` marks a rule that is stated before the importer has it. Its code is `proposed` in the registry.

## Steps

`steps/import_steps.py`. A Given is netlist fragments: a table of placed symbols (`Ref`, `Symbol`, `Role`, every
other column a field) and a table of nets (`Net`, `Pins` as `REF.pin`). The interlocking's declaration and its
processor are scaffolding the step adds.

## Run

    cd tools/layout_compiler/features && uv run behave --tags='not @pending'
