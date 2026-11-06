"""Step definitions of the model features, against the reference derivation ``tools/layout_model/derive.py``.

A Given states facts of a Layout Data Model File as a table: one row per entity, the ``Name`` column its key, every
other column a ``given`` field, and a column ``relations.<key>`` a stated relation. An empty cell states nothing.
The When derives. A Then reads ``derived`` or the rule checks. A scenario's diagnostic code is its tag, so a Then
never repeats it. A step whose rule is not in the reference derivation yet raises ``Pending`` with its issue.
"""
from __future__ import annotations

from behave import given, then, when

from tools import layout_model
from tools.layout_model import derive

LEVELS = {"an error": "error", "a warning": "warning", "information": "info", "missing": "missing"}


class Pending(NotImplementedError):
    """The rule is stated; the reference derivation does not have it yet."""


def _model(context) -> dict:
    if not hasattr(context, "model"):
        context.model = {"schema": layout_model.SCHEMA_ID, "layout": {"name": "T"}, "interlockings": {},
                         "provenance": {"sourceType": "test", "writer": {"name": "features", "version": "0"}}}
    return context.model


def _interlocking(context, name: str) -> dict:
    return _model(context)["interlockings"].setdefault(name, {"houses": {"House": {}}, "appliances": {}, "track": {}})


def _entity(row) -> tuple[str, dict]:
    given_, relations = {}, {}
    for heading in row.headings:
        value = row[heading].strip()
        if heading == "Name" or not value:
            continue
        if heading.startswith("relations."):
            relations[heading.removeprefix("relations.")] = value
        else:
            given_[heading] = value
    return row["Name"].strip(), {k: v for k, v in (("given", given_), ("relations", relations)) if v}


def code_of(context) -> str:
    """The scenario's diagnostic code: its one tag that is a registered rule check."""
    codes = [t for t in context.scenario.tags if t in derive.registry()]
    assert len(codes) == 1, f"a scenario that reports names one registered code as its tag, not {context.scenario.tags}"
    return codes[0]


def _named(context, name: str) -> dict:
    """The appliance called ``name`` in the derived model, in whichever interlocking holds it."""
    found = [ix["appliances"][name] for ix in context.derived["interlockings"].values() if name in ix.get("appliances", {})]
    assert len(found) == 1, f"{name}: {len(found)} appliances of that name"
    return found[0]


@given('interlocking "{name}" has these appliances:')
def appliances(context, name):
    for row in context.table:
        key, entity = _entity(row)
        _interlocking(context, name)["appliances"][key] = entity


@given('interlocking "{name}" has these devices:')
def devices(context, name):
    for row in context.table:
        key, entity = _entity(row)
        entity.setdefault("given", {})["Name"] = key
        _interlocking(context, name).setdefault("devices", []).append(entity)


@given('interlocking "{name}" has house "{house}"')
def house(context, name, house):
    _interlocking(context, name)["houses"] = {house: {}}


@given('the timetable has station "{station}"')
def station(context, station):
    _model(context)["layout"].setdefault("stations", {})[station] = {"given": {"Kind": "STATION"}}


@when("the layout is derived")
def derived(context):
    context.derived, context.report = derive.derive(_model(context))


@then('"{name}" has derived {key} "{value}"')
def has_derived(context, name, key, value):
    got = _named(context, name).get("derived", {}).get(key)
    assert str(got) == value, f"{name}: derived {key} is {got!r}, not {value!r}"


@then('"{name}" has no derived {key}')
def has_no_derived(context, name, key):
    got = _named(context, name).get("derived", {}).get(key)
    assert got is None, f"{name}: derived {key} is {got!r}"


@then('it is reported as {level} on "{name}"')
def reported(context, level, name):
    code = code_of(context)
    assert derive.registry()[code]["level"] == LEVELS[level], f"{code} is registered at {derive.registry()[code]['level']}"
    hits = [d for d in context.report.by_code(code) if any(e.rsplit("/", 1)[-1] == name for e in (d.where, *d.entities))]
    assert hits, f"{code} is not reported on {name}; reported: {sorted((d.code, d.where) for d in context.report.diags)}"
    assert all(d.severity == LEVELS[level] for d in hits), f"{code} on {name} is {hits[0].severity}"


@then("it is not reported")
def not_reported(context):
    code = code_of(context)
    hits = context.report.by_code(code)
    assert not hits, f"{code} is reported: {[str(d) for d in hits]}"


# ------------------------------------------------------------------- rules stated before the derivation has them

@then('a route through "{name}" {position} shows no better than "{word}"')
def ceiling(context, name, position, word):
    raise Pending("the route ceiling is the routes library's, issues #62 and #81")


@then('a route through "{name}" {position} takes the ceiling the route derivation sets')
def derived_ceiling(context, name, position):
    raise Pending("the route ceiling is the routes library's, issues #62 and #81")


@then('a route through "{name}" {position} takes the reference data\'s ceiling for a hand-operated switch')
def hand_ceiling(context, name, position):
    raise Pending("the hand-switch rule moves to reference data, issue #81")


@then('"{name}" is on circuit "{circuit}"')
def on_circuit(context, name, circuit):
    raise Pending("the circuit relation of a lamp or contact, issue #82")


@then('"{name}" has faces "{faces}"')
def faces(context, name, faces):
    raise Pending("a train order board's faces come from its device units, issue #83")


@given('the "{face}" face of "{name}" has {inputs} asserted')
def asserted(context, face, name, inputs):
    raise Pending("the train order device's local logic is FieldUnit's, issue #83")


@then('the "{face}" face of "{name}" shows "{word}"')
def shows(context, face, name, word):
    raise Pending("the train order device's local logic is FieldUnit's, issue #83")


@then('"{mast}" has head positions "{positions}"')
def positions(context, mast, positions):
    raise Pending("head position = mast pin, issue #80")


@then('position "{position}" of "{mast}" presents "{words}"')
def presents(context, position, mast, words):
    raise Pending("derived.presents from the head model table, issue #80")


@given('train order device "{name}" has units for the faces "{faces}"')
def units(context, name, faces):
    raise Pending("a train order device has one unit per face, issue #83")


@given('field mast "{mast}" has these heads:')
def heads(context, mast):
    raise Pending("head position = mast pin, issue #80")
