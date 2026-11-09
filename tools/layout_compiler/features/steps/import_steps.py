"""Step definitions of the import features, against the KiCad importer ``tools/layout_compiler``.

A Given states a drawing as netlist fragments: a table of placed symbols (``Ref``, ``Symbol``, ``Role``, every other
column a field; an empty cell is an empty field) and a table of nets (``Net``, ``Pins`` as ``REF.pin`` separated by
spaces, or ``REF.UNIT.pin`` for a pin drawn in a named unit of a multi-unit symbol). The interlocking's declaration
and its processor are scaffolding the step adds. The When imports. A Then
reads the facts written into the model or the import diagnostics. A scenario's diagnostic code is its tag. A step
whose rule is not in the importer yet raises ``Pending`` with its issue.
"""
from __future__ import annotations

from behave import given, then, when

import tools.layout_compiler as importer
from tools.layout_compiler import emit, seams
from tools.layout_compiler.source import Net, PinRef, Symbol, from_symbols

LEVELS = {"an error": "error", "a warning": "warning", "information": "info", "missing": "missing"}


class Pending(NotImplementedError):
    """The rule is stated; the importer does not have it yet."""


@given('this drawing of interlocking "{name}":')
def drawing(context, name):
    sheet = f"/{name}/"
    context.interlocking = name
    context.symbols = [Symbol("IX1", "Railroad-Trackplan:Interlocking", "", {"Role": "STRUCTURE", "Kind": "INTERLOCKING", "Name": name}, sheet),
                       Symbol("P1", "Railroad-HardwareIO:Processor", "", {"Role": "STRUCTURE", "Kind": "PROCESSOR", "Name": "Alpha", "Board": "cpNode"}, sheet)]
    context.nets = [Net("scaffold", (PinRef("IX1", "Processor"), PinRef("P1", "Processor")))]
    for row in context.table:
        fields = {h: row[h].strip() for h in row.headings if h not in ("Ref", "Symbol") and row[h].strip()}
        context.symbols.append(Symbol(row["Ref"].strip(), row["Symbol"].strip(), "", fields, sheet))


@given("these symbols too:")
def more_symbols(context):
    for row in context.table:
        fields = {h: row[h].strip() for h in row.headings if h not in ("Ref", "Symbol") and row[h].strip()}
        context.symbols.append(Symbol(row["Ref"].strip(), row["Symbol"].strip(), "", fields, f"/{context.interlocking}/"))


def _pin(text: str) -> PinRef:
    """``REF.pin``, or ``REF.UNIT.pin`` for a pin of a named unit (a train order device's face)."""
    parts = text.split(".")
    return PinRef(parts[0], parts[2], unit=parts[1]) if len(parts) == 3 else PinRef(parts[0], parts[1])


@given("these nets:")
def nets(context):
    for row in context.table:
        context.nets.append(Net(row["Net"].strip(), tuple(_pin(p) for p in row["Pins"].split())))


@when("the drawing is imported")
def imported(context):
    context.seams = seams.resolve(from_symbols(context.symbols, context.nets))
    context.model = emit.emit(context.seams)


def code_of(context) -> str:
    """The scenario's diagnostic code: its one tag that is a registered import diagnostic."""
    codes = [t for t in context.scenario.tags if t in importer.registry()]
    assert len(codes) == 1, f"a scenario that reports names one registered code as its tag, not {context.scenario.tags}"
    return codes[0]


def _on(diag, ref: str) -> bool:
    return (diag.where or diag.source).split(" ")[0].rsplit("/", 1)[-1] == ref


@then('it is reported as {level} on "{ref}"')
def reported(context, level, ref):
    code = code_of(context)
    assert importer.registry()[code]["level"] == LEVELS[level], f"{code} is registered at {importer.registry()[code]['level']}"
    hits = [d for d in context.seams.report.by_code(code) if _on(d, ref)]
    assert hits, f"{code} is not reported on {ref}; reported: {sorted((d.code, d.source) for d in context.seams.report.diags)}"
    assert all(d.severity == LEVELS[level] for d in hits), f"{code} on {ref} is {hits[0].severity}"


@then("it is not reported")
def not_reported(context):
    hits = context.seams.report.by_code(code_of(context))
    assert not hits, f"reported: {[str(d) for d in hits]}"


@then('"{name}" states the relation {key} "{value}"')
def relation(context, name, key, value):
    got = context.model["interlockings"][context.interlocking]["appliances"][name].get("relations", {}).get(key)
    assert got == value, f"{name}: relations.{key} is {got!r}, not {value!r}"


# ----------------------------------------------------------------------- rules stated before the importer has them

@then('"{name}" states the circuit "{circuit}"')
def circuit(context, name, circuit):
    raise Pending("the TRACK pin of a lamp or contact, issue #82")


@then('"{name}" states no circuit')
def no_circuit(context, name):
    raise Pending("the TRACK pin of a lamp or contact, issue #82")


def _device(context, ref: str):
    """The importer's device for the symbol ``ref``, in the scenario's interlocking."""
    devs = [d for d in context.seams.interlockings[context.interlocking].devices if d.sym.ref == ref]
    assert len(devs) == 1, f"{ref}: {len(devs)} devices"
    return devs[0]


@then('the {kind} "{ref}" is on face "{face}" of "{mast}"')
def on_face(context, kind, ref, face, mast):
    """A head's or a train order lever's IND wire reaches a face pin of the train order mast device (the owner, 2026-11-08)."""
    d = _device(context, ref)
    assert d.mast == f"{context.interlocking}:{mast}", f"{ref}: its mast is {d.mast!r}, not {mast!r}"
    assert d.face == face, f"{ref}: its face is {d.face!r}, not {face!r}"


@then('the lever "{ref}" binds "{pin}" to "{route}"')
def binds(context, ref, pin, route):
    got = {b.function: b.route for b in _device(context, ref).bindings}.get(pin)
    assert got == route, f"{ref}: {pin} binds {got!r}, not {route!r}"


@then('the head "{ref}" is position "{position}" of "{mast}"')
def position(context, ref, position, mast):
    raise Pending("head position = mast pin, issue #80")
