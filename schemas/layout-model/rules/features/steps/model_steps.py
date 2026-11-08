"""Step definitions of the model features, against the reference derivation ``tools/layout_model/derive.py``.

A Given states facts of a Layout Data Model File as a table: one row per entity, the ``Name`` column its key, every
other column a ``given`` field, and a column ``relations.<key>`` a stated relation. An empty cell states nothing.
A track row (a joint, an end, a policy) is keyed by its ``Id``; ``relations.masts`` is ``A=<mast> B=<mast>``. A wire
joins track pins (``J1.A 832T.TC``): each pin then names every other, the stated adjacency of ADR 0011; a pin of a
thing the interlocking does not have (``Y:3NAT.TC``) is another interlocking's, named as given. The When derives. A
Then reads ``derived`` or the rule checks. A scenario's diagnostic code is its tag, so a Then never repeats it. A rule
that is a function of facts stated in the scenario alone (what a train order face shows for the inputs asserted) is
checked without a When. A step whose rule is not in the reference derivation yet raises ``Pending`` with its issue.
"""
from __future__ import annotations

from behave import given, then, when

from tools import layout_model
from tools.layout_model import derive, reference

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


def _entity(row, key: str = "Name") -> tuple[str, dict]:
    given_, relations = {}, {}
    for heading in row.headings:
        value = row[heading].strip()
        if heading == key or not value:
            continue
        if heading.startswith("relations."):
            relations[heading.removeprefix("relations.")] = value
        else:
            given_[heading] = value
    return row[key].strip(), {k: v for k, v in (("given", given_), ("relations", relations)) if v}


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


def _row(context, name: str, kind: str, row) -> None:
    key, entity = _entity(row, "Id")
    rel = entity.get("relations", {})
    if "masts" in rel:                                                   # A=<mast> B=<mast>
        rel["masts"] = dict(tok.split("=", 1) for tok in rel["masts"].split())
    _interlocking(context, name)["track"].setdefault(kind, []).append({"id": key, **entity})


@given('interlocking "{name}" has these joints:')
def joints(context, name):
    for row in context.table:
        _row(context, name, "joints", row)


@given('interlocking "{name}" has these ends:')
def ends(context, name):
    for row in context.table:
        _row(context, name, "ends", row)


@given('interlocking "{name}" has these policies:')
def policies(context, name):
    for row in context.table:
        _row(context, name, "policies", row)


def _rows(ix: dict) -> dict[str, dict]:
    return {r["id"]: r for rows in ix.get("track", {}).values() for r in rows}


@given('interlocking "{name}" has these wires:')
def wires(context, name):
    """Each pin on a wire names every other pin on it: an appliance's pin by its qualified name, a row's by its id."""
    ix = _interlocking(context, name)
    rows = _rows(ix)

    def canonical(pin: str) -> str:
        thing, _, side = pin.rpartition(".")
        return f"{thing}.{side}" if thing in rows or ":" in thing else f"{name}:{thing}.{side}"

    for row in context.table:
        pins = row["Pins"].split()
        for p in pins:
            thing, _, side = p.rpartition(".")
            holder = ix["appliances"].get(thing) or rows.get(thing)
            if holder is None:
                continue                                                 # another interlocking's pin, named as given
            others = sorted({canonical(o) for o in pins if o.rpartition(".")[0] != thing})
            holder.setdefault("relations", {})[side] = others


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


def _row_named(context, rid: str) -> dict:
    found = [r for ix in context.derived["interlockings"].values() for r in _rows(ix).values() if r["id"] == rid]
    assert len(found) == 1, f"{rid}: {len(found)} track rows of that id"
    return found[0]


@then('"{mast}" governs into "{governed}" and approaches over "{approach}"')
def governs(context, mast, governed, approach):
    got = _named(context, mast).get("derived", {}).get("circuits")
    assert got == {"governed": governed, "approach": approach}, f"{mast}: derived circuits are {got!r}"


@then('"{name}" counts toward "{a}" on side A and "{b}" on side B')
def counts_toward(context, name, a, b):
    got = _named(context, name).get("derived", {}).get("circuits")
    assert got == {"A": a, "B": b}, f"{name}: derived circuits are {got!r}"


@then('"{name}" counts toward "{a}" on side A and nothing on side B')
def counts_toward_one(context, name, a):
    got = _named(context, name).get("derived", {}).get("circuits")
    assert got == {"A": a}, f"{name}: derived circuits are {got!r}"


@then('joint "{rid}" has circuit "{a}" on side A and "{b}" on side B')
def joint_sides(context, rid, a, b):
    got = _row_named(context, rid).get("derived", {}).get("circuits")
    assert got == {"A": a, "B": b}, f"{rid}: derived circuits are {got!r}"


@then('joint "{rid}" governs over "{governed}" and approaches over "{approach}"')
def joint_governs(context, rid, governed, approach):
    got = _row_named(context, rid).get("derived", {}).get("circuits")
    assert got == {"governed": governed, "approach": approach}, f"{rid}: derived circuits are {got!r}"


@then('joint "{rid}" has circuit "{a}" on side A and dark track on side B')
def joint_side_a(context, rid, a):
    got = _row_named(context, rid).get("derived", {}).get("circuits")
    assert got == {"A": a}, f"{rid}: derived circuits are {got!r}"


@then('sign "{rid}" stands on circuit "{circuit}"')
def sign_on(context, rid, circuit):
    got = _row_named(context, rid).get("derived", {}).get("circuits")
    assert got == {"track": circuit}, f"{rid}: derived circuits are {got!r}"


@then('"{name}" belongs to control point "{cp}"')
def control_point(context, name, cp):
    got = _named(context, name).get("derived", {}).get("controlPoint")
    assert got == cp, f"{name}: derived controlPoint is {got!r}, not {cp!r}"


@then('"{name}" belongs to no control point')
def no_control_point(context, name):
    got = _named(context, name).get("derived", {})
    assert "controlPoint" not in got, f"{name}: derived controlPoint is {got['controlPoint']!r}"


@then('joint "{rid}" belongs to no control point')
def joint_no_control_point(context, rid):
    got = _row_named(context, rid).get("derived", {})
    assert "controlPoint" not in got, f"{rid}: derived controlPoint is {got['controlPoint']!r}"


@then('"{name}" has members "{members}"')
def members(context, name, members):
    got = _named(context, name).get("derived", {}).get("members")
    want = [m.strip() for m in members.split(",")]
    assert got == want, f"{name}: derived members are {got!r}, not {want!r}"


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


@then('"{name}" is on circuit "{circuit}"')
def on_circuit(context, name, circuit):
    """A lamp's, contact's or actuator's circuit relation, kept as stated once the rule checks accept it (#82)."""
    got = _named(context, name).get("relations", {}).get("circuit")
    assert got == circuit, f"{name}: relations.circuit is {got!r}, not {circuit!r}"


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


@then('"{name}" has faces "{faces}"')
def faces(context, name, faces):
    got = sorted(_named(context, name).get("derived", {}).get("faces", {}))
    want = sorted(f.strip() for f in faces.split(","))
    assert got == want, f"{name}: derived faces are {got!r}, not {want!r}"


def _face(context, name: str, face: str) -> dict:
    """The face ``face`` derived on the train order board named ``name``."""
    faces = _named(context, name).get("derived", {}).get("faces", {})
    assert face in faces, f"{name}: no derived face {face}; faces: {sorted(faces)}"
    return faces[face]


@then('the "{face}" face of "{name}" serves the direction "{direction}"')
def face_direction(context, face, name, direction):
    got = _face(context, name, face).get("direction")
    assert got == direction, f"{name} face {face}: derived direction is {got!r}, not {direction!r}"


@then('the "{face}" face of "{name}" can show "{words}"')
def face_indications(context, face, name, words):
    got = _face(context, name, face).get("indications")
    want = [w.strip() for w in words.split(",")]
    assert got == want, f"{name} face {face}: derived indications is {got!r}, not {want!r}"


def _inputs(text: str) -> list[str]:
    """``nothing``, one input, or inputs joined by ``and`` or commas."""
    return [] if text.strip() == "nothing" else [w.strip() for w in text.replace(" and ", ",").split(",") if w.strip()]


@given('the "{face}" face of "{name}" has {inputs} asserted')
def asserted(context, face, name, inputs):
    context.asserted = _inputs(inputs)


@then('the "{face}" face of "{name}" shows "{word}"')
def shows(context, face, name, word):
    """The run-time rule is FieldUnit's (its issue #44), not the model library's: the step reads the ordered input
    table of the reference data, most restrictive first, and the word of the first asserted input, else CLEAR."""
    asserted = set(context.asserted)
    unknown = asserted - {pin for pin, _ in reference.TRAIN_ORDER_INPUTS}
    assert not unknown, f"not a train order input: {', '.join(sorted(unknown))}"
    got = next((w for pin, w in reference.TRAIN_ORDER_INPUTS if pin in asserted), reference.TRAIN_ORDER_CLEAR)
    assert got == word, f"{', '.join(context.asserted) or 'nothing'} asserted shows {got!r}, not {word!r}"


@then('"{mast}" has head positions "{positions}"')
def positions(context, mast, positions):
    raise Pending("head position = mast pin, issue #80")


@then('position "{position}" of "{mast}" presents "{words}"')
def presents(context, position, mast, words):
    raise Pending("derived.presents from the head model table, issue #80")


def _holder(context, name: str) -> str:
    """The interlocking that holds the appliance ``name``, else the one interlocking stated so far."""
    model = _model(context)
    holders = [ixn for ixn, ix in model["interlockings"].items() if name in ix.get("appliances", {})]
    return holders[0] if holders else next(iter(model["interlockings"]), "X")


@given('train order mast device "{name}" exists')
def mast_device(context, name):
    """A field mast device of Appliance train_order_mast named for its board (the owner, 2026-11-08), once."""
    ixn = _holder(context, name)
    devices = _interlocking(context, ixn).setdefault("devices", [])
    if not any(d["given"].get("Appliance") == "train_order_mast" and d["given"].get("Name") == name for d in devices):
        devices.append({"given": {"Appliance": "train_order_mast", "Name": name}})


@given('train order mast "{name}" has a head on face "{face}"')
def face_head(context, name, face):
    """A head device whose IND wire reaches the mast's face pin: relations.mast and relations.face as the importer
    writes them (the owner, 2026-11-08)."""
    mast_device(context, name)
    ixn = _holder(context, name)
    _interlocking(context, ixn)["devices"].append({"given": {"Appliance": "head", "Style": "UQ"},
                                                   "relations": {"mast": f"{ixn}:{name}", "face": face}})


@given('train order mast "{name}" has a lever on face "{face}" wiring "{inputs}"')
def face_lever(context, name, face, inputs):
    """A train order lever (Appliance lever, Style train_order) whose IND wire reaches the mast's face pin, its STOP
    and SLOW bound to a driver pin each; the route is any, the binding is the fact. ``nothing`` binds none."""
    mast_device(context, name)
    ixn = _holder(context, name)
    _interlocking(context, ixn)["devices"].append({"given": {"Appliance": "lever", "Style": "train_order"},
                                                   "relations": {"mast": f"{ixn}:{name}", "face": face,
                                                                 "bindings": {w: f"Field/0x20/A{i}" for i, w in enumerate(_inputs(inputs))}}})


@given('field mast "{mast}" has these heads:')
def heads(context, mast):
    raise Pending("head position = mast pin, issue #80")
