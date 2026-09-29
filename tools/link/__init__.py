"""Subdivision linker: controller fragments + plant models -> linked model.

The linker is the only cross-ecosystem actor. It pairs fragments by
normalized name, derives codeline instances, runs whatever cross-checks the
present fragments allow, and always emits. Missing counterparts become
placeholder stations; generators decide what is fatal for their output.
"""
