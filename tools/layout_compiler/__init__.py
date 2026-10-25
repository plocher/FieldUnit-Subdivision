"""The milestone D compiler: KiCad project to the Layout Data Model File (ADR 0008 rev 4, ADR 0009).

Three parts, each behind a narrow seam so the KiCad side can move to a shared services API later:

- ``source``: the one interface the compiler reads, symbols with fields and nets with pin names, and its only
  implementation today, the kicad-cli netlist export read through ``kicad_services``.
- ``seams``: the explicit-seams model of ADR 0009. Every relation of the §3.12 table is resolved twice, by wire and
  by its implicit fallback, and a disagreement is an error. Macros ``<ROLE:KIND:Field>`` are expanded here.
- ``emit``: the seam facts as the schema ``layout-model/v3.0.0`` dictionary, written canonically by ``layout_model``.

The compiler writes nothing when it reports an error (ADR 0008 §4.6); its observations about the drawing stay in
its log.
"""
