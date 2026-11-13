"""Step definitions of the import features, against the KiCad importer ``tools/layout_compiler``.

A Given states a drawing as netlist fragments: a table of placed symbols (``Ref``, ``Symbol``, ``Role``, every other
column a field; an empty cell is an empty field) and a table of nets (``Net``, ``Pins`` as ``REF.pin`` separated by
spaces, or ``REF.UNIT.pin`` for a pin drawn in a named unit of a multi-unit symbol). The interlocking's declaration
and its processor are scaffolding the step adds; a second drawing is a second interlocking's sheet, and a net may
join pins of both (block track is read across sheets, ADR 0013 §7.1). The When imports. A Then
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
    if not hasattr(context, "symbols"):
        context.interlocking, context.symbols, context.nets = name, [], []
    n = sum(1 for s in context.symbols if s.fields.get("Kind") == "INTERLOCKING") + 1
    context.symbols += [Symbol(f"IX{n}", "Railroad-Trackplan:Interlocking", "", {"Role": "STRUCTURE", "Kind": "INTERLOCKING", "Name": name}, sheet),
                        Symbol(f"P{n}", "Railroad-HardwareIO:Processor", "", {"Role": "STRUCTURE", "Kind": "PROCESSOR", "Name": "Alpha" if n == 1 else f"Alpha{n}", "Board": "cpNode"}, sheet)]
    context.nets.append(Net(f"scaffold{n}", (PinRef(f"IX{n}", "Processor"), PinRef(f"P{n}", "Processor"))))
    for row in context.table:
        fields = {h: row[h].strip() for h in row.headings if h not in ("Ref", "Symbol") and row[h].strip()}
        context.symbols.append(Symbol(row["Ref"].strip(), row["Symbol"].strip(), "", fields, sheet))


@given("these symbols on the sheet above:")
def parent_symbols(context):
    """Symbols on the root sheet, above every interlocking's (a NextCP wired to a hierarchical net)."""
    for row in context.table:
        fields = {h: row[h].strip() for h in row.headings if h not in ("Ref", "Symbol") and row[h].strip()}
        context.symbols.append(Symbol(row["Ref"].strip(), row["Symbol"].strip(), "", fields, "/"))


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


@then('nothing is reported on "{ref}"')
def nothing_on(context, ref):
    hits = [d for d in context.seams.report.diags if _on(d, ref)]
    assert not hits, f"reported on {ref}: {[str(d) for d in hits]}"


def _appliance(context, name: str) -> dict:
    """The appliance called ``name``, in whichever interlocking of the model holds it."""
    found = [ix["appliances"][name] for ix in context.model["interlockings"].values() if name in ix.get("appliances", {})]
    assert len(found) == 1, f"{name}: {len(found)} appliances of that name"
    return found[0]


def _row(context, ref: str) -> dict:
    """The track row written for the symbol ``ref``: its id is the symbol's UUID."""
    rid = context.seams.source.symbols[ref].uuid
    found = [r for ix in context.model["interlockings"].values() for rows in ix.get("track", {}).values() for r in rows if r.get("id") == rid]
    assert len(found) == 1, f"{ref}: {len(found)} track rows for it"
    return found[0]


@then('the row "{ref}" is in interlocking "{name}"')
def row_in(context, ref, name):
    rid = context.seams.source.symbols[ref].uuid
    hits = [n for n, ix in context.model["interlockings"].items() for rows in ix.get("track", {}).values() for r in rows if r.get("id") == rid]
    assert hits == [name], f"{ref}: in {hits}, not [{name!r}]"


@then('no row is written for "{ref}"')
def no_row(context, ref):
    rid = context.seams.source.symbols[ref].uuid
    hits = [n for n, ix in context.model["interlockings"].items() for rows in ix.get("track", {}).values() for r in rows if r.get("id") == rid]
    assert not hits, f"{ref}: a row in {hits}"


@then('"{name}" is in interlocking "{ix}"')
def appliance_in(context, name, ix):
    hits = [n for n, i in context.model["interlockings"].items() if name in i.get("appliances", {})]
    assert hits == [ix], f"{name}: in {hits}, not [{ix!r}]"


def _pin_name(context, pin: str) -> str:
    """A pin as the model names it: ``REF.side`` of a track row by the row's id, anything else as written."""
    thing, _, side = pin.rpartition(".")
    sym = context.seams.source.symbols.get(thing)
    return f"{sym.uuid}.{side}" if sym is not None and sym.fields.get("Role") in ("TRACK", "POLICY") else pin


@then('"{name}" states the relation {key} "{value}"')
def relation(context, name, key, value):
    got = _appliance(context, name).get("relations", {}).get(key)
    assert got == value, f"{name}: relations.{key} is {got!r}, not {value!r}"


@then('"{name}" is written with {field} "{value}"')
def appliance_given(context, name, field, value):
    got = _appliance(context, name).get("given", {}).get(field)
    assert got == value, f"{name}: {field} is {got!r}, not {value!r}"


@then('"{name}" names "{pin}" on side {side}')
def names_on_side(context, name, pin, side):
    got = _appliance(context, name).get("relations", {}).get(side) or []
    assert _pin_name(context, pin) in got, f"{name}: side {side} names {got!r}, not {pin!r}"


@then('"{name}" stands on no track')
def no_track(context, name):
    got = {k: v for k, v in _appliance(context, name).get("relations", {}).items() if isinstance(v, list)}
    assert not got, f"{name}: track sides {got!r}"


@then('the row "{ref}" is written with {field} "{value}"')
def row_given(context, ref, field, value):
    got = _row(context, ref).get("given", {}).get(field)
    assert got == value, f"{ref}: {field} is {got!r}, not {value!r}"


@then('the row "{ref}" states the relation {key} "{value}"')
def row_relation(context, ref, key, value):
    got = _row(context, ref).get("relations", {}).get(key)
    assert got == value, f"{ref}: relations.{key} is {got!r}, not {value!r}"


@then('the row "{ref}" states no relation {key}')
def row_no_relation(context, ref, key):
    got = _row(context, ref).get("relations", {})
    assert key not in got, f"{ref}: relations.{key} is {got[key]!r}"


@then('the row "{ref}" names "{pin}" on side {side}')
def row_names_on_side(context, ref, pin, side):
    got = _row(context, ref).get("relations", {}).get(side) or []
    assert _pin_name(context, pin) in got, f"{ref}: side {side} names {got!r}, not {pin!r}"


@then('the joint "{ref}" states the mast "{mast}" on side {side}')
def joint_mast(context, ref, mast, side):
    got = _row(context, ref).get("relations", {}).get("masts", {}).get(side)
    assert got == mast, f"{ref}: the mast on side {side} is {got!r}, not {mast!r}"


@then('the joint "{ref}" states no mast on side {side}')
def joint_no_mast(context, ref, side):
    got = _row(context, ref).get("relations", {}).get("masts", {})
    assert side not in got, f"{ref}: the mast on side {side} is {got[side]!r}"


# ----------------------------------------------------------------------- rules stated before the importer has them

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


# ----------------------------------------------------------------------- head positions (issue #80)

@then('the head "{ref}" is position "{position}" of "{mast}"')
def position(context, ref, position, mast):
    """A head's IND wire reaches a position pin of its signal mast device (issue #80; the owner, 2026-11-04)."""
    d = _device(context, ref)
    assert d.mast == f"{context.interlocking}:{mast}", f"{ref}: its mast is {d.mast!r}, not {mast!r}"
    assert d.position == position, f"{ref}: its position is {d.position!r}, not {position!r}"


# ----------------------------------------------------------------------- encoded drivers (the owner, 2026-11-10)

def _driver_keys(context) -> dict[str, str]:
    """Each driver symbol's key on its processor: ref -> address, every symbol that draws a driver included."""
    return {x.ref: a for p in context.seams.processors.values() for a, d in p.drivers.items() for x in d.syms}


@then('processor "{name}" has the drivers "{keys}"')
def has_drivers(context, name, keys):
    got = set(context.seams.processors[name].drivers)
    want = {k.strip() for k in keys.split(",")}
    assert got == want, f"{name}: drivers {sorted(got)}, not {sorted(want)}"


@then('the driver "{ref}" is keyed "{key}"')
def keyed(context, ref, key):
    got = _driver_keys(context).get(ref)
    assert got == key, f"{ref}: keyed {got!r}, not {key!r}; drivers: {sorted(set(_driver_keys(context).values()))}"


@then('the driver "{key}" on "{name}" is drawn by "{refs}"')
def drawn_by(context, key, name, refs):
    d = context.seams.processors[name].drivers[key]
    got = sorted(x.ref for x in d.syms)
    assert got == sorted(r.strip() for r in refs.split(",")), f"{key}: drawn by {got}"


@then("no driver is written with an Address")
def no_address(context):
    written = [(p, a) for p, proc in context.model["layout"]["processors"].items() for a, d in proc.get("drivers", {}).items()
               if "Address" in d.get("given", {})]
    assert not written, f"an Address is written on {written}"
