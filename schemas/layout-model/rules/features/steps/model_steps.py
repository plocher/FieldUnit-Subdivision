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

import re

from behave import given, then, when

from tools import layout_model
from tools.layout_model import derive, grammar, reference
from tools.railroad import codeline, routes

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
    named = entity.get("given", {}).pop("Name", None)                    # a named row (an industry): its pins go by its name
    _interlocking(context, name)["track"].setdefault(kind, []).append({"id": key, **({"name": f"{name}:{named}"} if named else {}), **entity})


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
    return {r["id"]: r for rows in ix.get("track", {}).values() for r in rows if "id" in r}      # a piece row has no id


def _named_rows(ix: dict) -> dict[str, dict]:
    """The named track rows by their unqualified name: a wire names their pins as it names an appliance's."""
    return {r["name"].partition(":")[2]: r for rows in ix.get("track", {}).values() for r in rows if "id" in r and r.get("name")}


@given('interlocking "{name}" has these wires:')
def wires(context, name):
    """Each pin on a wire names every other pin on it: an appliance's or a named row's pin by its qualified name, any
    other row's by its id."""
    ix = _interlocking(context, name)
    rows, named = _rows(ix), _named_rows(ix)
    ids = {i for other in _model(context)["interlockings"].values() for i in _rows(other)}   # a row id is global

    def canonical(pin: str) -> str:
        thing, _, side = pin.rpartition(".")
        return f"{thing}.{side}" if thing in ids or ":" in thing else f"{name}:{thing}.{side}"

    for row in context.table:
        pins = row["Pins"].split()
        for p in pins:
            thing, _, side = p.rpartition(".")
            holder = ix["appliances"].get(thing) or rows.get(thing) or named.get(thing)
            if holder is None:
                continue                                                 # another interlocking's pin, named as given
            others = sorted({canonical(o) for o in pins if o.rpartition(".")[0] != thing})
            holder.setdefault("relations", {})[side] = others


@given('interlocking "{name}" has house "{house}"')
def house(context, name, house):
    _interlocking(context, name)["houses"] = {house: {}}


@given('interlocking "{name}" has houses "{houses}"')
def houses(context, name, houses):
    _interlocking(context, name)["houses"] = {h.strip(): {} for h in houses.split(",")}


@given('the timetable has station "{station}"')
def station(context, station):
    _model(context)["layout"].setdefault("stations", {})[station] = {"given": {"Kind": "STATION"}}


@when("the layout is derived")
def derived(context):
    context.derived, context.report = derive.derive(_model(context), getattr(context, "user", None))


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


BY = {"a marker": "marker", "inheritance": "inherited"}


def _piece(context, name: str) -> dict:
    """The piece row called ``name`` in the interlocking whose name qualifies it (ADR 0013 §7.1)."""
    ix = context.derived["interlockings"][name.partition(":")[0]]
    found = [p["derived"] for p in ix.get("track", {}).get("pieces", []) if p["derived"]["name"] == name]
    assert len(found) == 1, f"{name}: {len(found)} pieces of that name in {[p['derived']['name'] for p in ix.get('track', {}).get('pieces', [])]}"
    return found[0]


@then('the piece "{name}" is under regime "{kind}" by {how}')
def piece_regime(context, name, kind, how):
    got = _piece(context, name)
    assert (got.get("regime"), got.get("by")) == (kind, BY[how]), f"{name}: regime {got.get('regime')!r} by {got.get('by')!r}"


@then('the piece "{name}" is under no regime')
def piece_no_regime(context, name):
    got = _piece(context, name)
    assert "regime" not in got and "by" not in got, f"{name}: regime {got.get('regime')!r} by {got.get('by')!r}"


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


@then('"{name}" stands on "{piece}"')
def stands_on(context, name, piece):
    """The piece of track a lamp, contact or actuator stands on, by the piece's name (#82)."""
    got = _named(context, name).get("derived", {}).get("track")
    assert got == piece, f"{name}: derived.track is {got!r}, not {piece!r}"


@then('"{name}" is on circuit "{circuit}"')
def on_circuit(context, name, circuit):
    """The circuit that names the piece a lamp, contact or actuator stands on (#82)."""
    got = _named(context, name).get("derived", {}).get("circuits", {}).get("track")
    assert got == circuit, f"{name}: derived.circuits.track is {got!r}, not {circuit!r}"


@then('"{name}" is on no circuit')
def on_no_circuit(context, name):
    got = _named(context, name).get("derived", {}).get("circuits", {}).get("track")
    assert got is None, f"{name}: derived.circuits.track is {got!r}"


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
    _, row = reference.train_order_inputs(getattr(context, "rulebook", None), getattr(context, "user_train_order", None))
    unknown = asserted - {i["input"] for i in row["inputs"]}
    assert not unknown, f"not a train order input: {', '.join(sorted(unknown))}"
    got = next((i["indication"] for i in row["inputs"] if i["input"] in asserted), row["rest"])
    assert got == word, f"{', '.join(context.asserted) or 'nothing'} asserted shows {got!r}, not {word!r}"


@then('"{mast}" has head positions "{positions}"')
def positions(context, mast, positions):
    """The positions heads are wired to, keyed by the field mast device pin (issue #80)."""
    got = list(_named(context, mast).get("derived", {}).get("positions", {}))
    want = [p.strip() for p in positions.split(",")]
    assert got == want, f"{mast}: positions {got!r}, not {want!r}"


@then('"{mast}" must show "{words}"')
def demand(context, mast, words):
    """A mast's demand: its explicit Indications list until #62 derives it."""
    got = _named(context, mast).get("derived", {}).get("demand")
    want = [w.strip() for w in words.split(",")]
    assert got == want, f"{mast}: demand {got!r}, not {want!r}"


def _position(context, mast: str, position: str) -> dict:
    positions = _named(context, mast).get("derived", {}).get("positions", {})
    assert position in positions, f"{mast}: no position {position}; positions: {sorted(positions)}"
    return positions[position]


@then('position "{position}" of "{mast}" presents "{words}"')
def presents(context, position, mast, words):
    """What a position presents: the head words of any head wired to it, from the head model table by Style."""
    got = _position(context, mast, position).get("presents")
    want = [w.strip() for w in words.split(",")]
    assert got == want, f"{mast} position {position}: presents {got!r}, not {want!r}"


@then('position "{position}" of "{mast}" presents nothing yet')
def presents_nothing(context, position, mast):
    got = _position(context, mast, position).get("presents")
    assert got is None, f"{mast} position {position}: presents {got!r}"


@then('position "{position}" of "{mast}" is head "{letter}"')
def position_letter(context, position, mast, letter):
    """The railroad's head letter of a position: the k-th stated letter is pin k (the owner, 2026-11-12)."""
    got = _position(context, mast, position).get("letter")
    assert got == letter, f"{mast} position {position}: letter {got!r}, not {letter!r}"


@then('the head on position "{position}" of "{mast}" is head "{letter}"')
def head_letter(context, position, mast, letter):
    """A head device derives its mast's letter for the pin its IND reaches."""
    heads = [d for ix in context.derived["interlockings"].values() for d in ix.get("devices", [])
             if d.get("given", {}).get("Appliance") == "head" and d.get("relations", {}).get("position") == position
             and d.get("relations", {}).get("mast", "").partition(":")[2] == mast]
    assert heads, f"{mast}: no head on position {position}"
    got = {d.get("derived", {}).get("letter") for d in heads}
    assert got == {letter}, f"{mast} position {position}: the heads derive letter {got!r}, not {letter!r}"


def _desk_lever(context, name: str) -> dict:
    found = [d for ou in context.derived.get("officeUnits", {}).values() for d in ou.get("devices", [])
             if d.get("given", {}).get("Appliance") == "lever" and d.get("given", {}).get("Name") == name]
    assert len(found) == 1, f"lever {name}: {len(found)} desk levers of that name"
    return found[0]


@then('lever "{name}" serves "{served}"')
def lever_serves(context, name, served):
    got = _desk_lever(context, name).get("derived", {}).get("serves")
    assert got == served, f"lever {name}: serves {got!r}, not {served!r}"


@then('lever "{name}" works masts "{masts}"')
def lever_masts(context, name, masts):
    """A signal lever's masts: those of its interlocking that state its signal number (the owner, 2026-11-12)."""
    got = _desk_lever(context, name).get("derived", {}).get("masts")
    want = [m.strip() for m in masts.split(",")]
    assert got == want, f"lever {name}: masts {got!r}, not {want!r}"


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


@given('field mast device "{name}" exists')
def signal_mast_device(context, name):
    """A field mast device (Appliance mast) named for its trackplan mast, once."""
    ixn = _holder(context, name)
    devices = _interlocking(context, ixn).setdefault("devices", [])
    if not any(d["given"].get("Appliance") == "mast" and d["given"].get("Name") == name for d in devices):
        devices.append({"given": {"Appliance": "mast", "Name": name}})


@given('field mast "{mast}" has these heads:')
def heads(context, mast):
    """Anonymous head devices on the field mast device's position pins (issue #80): ``Position`` the pin the head's IND
    wire reaches, ``Style`` its model; the facts as the importer writes them, ``relations.mast`` and
    ``relations.position``."""
    signal_mast_device(context, mast)
    ixn = _holder(context, mast)
    for row in context.table:
        _interlocking(context, ixn)["devices"].append({"given": {"Appliance": "head", "Style": row["Style"].strip()},
                                                       "relations": {"mast": f"{ixn}:{mast}", "position": row["Position"].strip()}})


# ------------------------------------------------------------------- what works a switch or derail (the owner, 2026-11-09)

@given('the desk has these levers for interlocking "{name}":')
def desk_levers(context, name):
    """Desk levers (OfficeUnit devices) serving the appliances of ``name``: ``Name`` the appliance, ``Style`` the lever's."""
    ou = _model(context).setdefault("officeUnits", {}).setdefault("Desk", {"columns": {}, "devices": []})
    for row in context.table:
        key, entity = _entity(row)
        entity.setdefault("given", {}).update({"Appliance": "lever", "Name": key})
        entity.setdefault("relations", {})["interlocking"] = name
        ou["devices"].append(entity)


def _appliances_of(context, name: str) -> dict:
    found = [ix["appliances"] for ix in context.derived["interlockings"].values() if name in ix.get("appliances", {})]
    assert len(found) == 1, f"{name}: {len(found)} appliances of that name"
    return found[0]


@then('"{name}" is powered')
def powered(context, name):
    """ADR 0013 §4's seam word, as ``grammar.is_powered`` reads the derived file."""
    assert grammar.is_powered(name, _appliances_of(context, name)), f"{name} is not powered (regime {grammar.regime(name, _appliances_of(context, name))!r})"


@then('"{name}" is not powered')
def not_powered(context, name):
    assert not grammar.is_powered(name, _appliances_of(context, name)), f"{name} is powered"


@then('"{name}" follows switch "{switch}"')
def follows(context, name, switch):
    """A dependent derail (ADR 0003 D8) and the switch whose regime it takes."""
    got = grammar.depends_on(name, _appliances_of(context, name))
    assert got == switch, f"{name} follows {got!r}, not {switch!r}"


@then('"{name}" follows no switch')
def follows_none(context, name):
    got = grammar.depends_on(name, _appliances_of(context, name))
    assert got is None, f"{name} follows {got!r}"


@then('"{name}" has dependent derails "{derails}"')
def dependent_derails(context, name, derails):
    """A switch's derived derails: those of its interlocking whose stated switch it is (the owner, 2026-11-13)."""
    got = _named(context, name).get("derived", {}).get("derails")
    want = [d.strip() for d in derails.split(",")]
    assert got == want, f"{name}: derived derails are {got!r}, not {want!r}"


@then('nothing is reported on "{name}"')
def nothing_on(context, name):
    hits = [d for d in context.report.diags if any(e.rsplit("/", 1)[-1] == name for e in (d.where, *d.entities))]
    assert not hits, f"reported on {name}: {[str(d) for d in hits]}"


# ------------------------------------------------------------------- the code line's tokens

@given('interlocking "{name}" is on a code line')
def on_code_line(context, name):
    """One AAR-token code line; the interlocking is its own station."""
    _model(context)["layout"].setdefault("codelines", {})["Line"] = {"given": {"Kind": "AAR"}}
    _interlocking(context, name).setdefault("relations", {})["codeline"] = "Line"


ENCODINGS = {"US&S 506": "USS506", "AAR token": "AAR"}


@given('interlocking "{name}" is on {article} {kind} code line')
def on_code_line_of(context, name, article, kind):
    """One code line of the named encoding (US&S 506: each house is a station; AAR token: the interlocking is)."""
    _model(context)["layout"].setdefault("codelines", {})["Line"] = {"given": {"Kind": ENCODINGS[kind]}}
    _interlocking(context, name).setdefault("relations", {})["codeline"] = "Line"


def _desk(context) -> dict:
    return _model(context).setdefault("officeUnits", {}).setdefault("Desk", {"columns": {}, "devices": []})


@given("the desk has these columns:")
def desk_columns(context):
    """Desk columns: ``Column`` the number, ``CP Name`` the house or interlocking it names (empty states none),
    ``Interlocking`` the sheet it is drawn on (``relations.interlocking``)."""
    for row in context.table:
        column = {"relations": {"interlocking": row["Interlocking"].strip()}}
        if row["CP Name"].strip():
            column["given"] = {"CP Name": row["CP Name"].strip()}
        _desk(context)["columns"][row["Column"].strip()] = column


@given("the desk has these levers:")
def desk_levers_on_columns(context):
    """Desk levers in columns: ``Name`` the appliance, ``Style`` the lever's, ``Column`` its desk column, ``Controls``
    and ``Indications`` the tokens of its bound pins (one pin per token, as Control.<pin> and Indication.<pin>)."""
    for row in context.table:
        given_ = {"Appliance": "lever", "Name": row["Name"].strip(), "Style": row["Style"].strip()}
        bindings = {}
        for field, column in (("Control", "Controls"), ("Indication", "Indications")):
            for token in (t.strip() for t in row.get(column, "").split(",") if t.strip()):
                pin = f"P{len(bindings) + 1}"
                given_[f"{field}.{pin}"] = token
                bindings[pin] = f"Desk/0x20/A{len(bindings)}"
        _desk(context)["devices"].append({"given": given_, "relations": {"column": f"Desk:{row['Column'].strip()}", "bindings": bindings}})


def _stations(context) -> dict:
    if not hasattr(context, "stations"):
        context.stations = {f"{b}:{h}" if h else b: s for (b, h), s in codeline.stations(context.derived).stations.items()}
    return context.stations


def _station(context, name: str):
    stations = _stations(context)
    assert name in stations, f"{name} is no station; stations: {sorted(stations)}"
    return stations[name]


def _tokens(text: str) -> list[str]:
    return [] if text.strip() == "nothing" else sorted(t.strip() for t in text.split(",") if t.strip())


@then('the stations of "{name}" are "{stations}"')
def stations_of(context, name, stations):
    got = sorted(s for s in _stations(context) if s.partition(":")[0] == name)
    assert got == sorted(_tokens(stations)), f"the stations of {name} are {got!r}"


@then('station "{name}" receives {controls}')
def receives(context, name, controls):
    got = sorted(_station(context, name).controls)
    assert got == _tokens(controls.strip('"')), f"station {name} receives {got!r}"


@then('the control functions station "{name}" receives are "{functions}"')
def receives_functions(context, name, functions):
    got = sorted((f.appliance, f.word) for f in _station(context, name).functions if f.direction == "control")
    want = sorted(tuple(f.split()) for f in _tokens(functions))
    assert got == want, f"station {name} receives the control functions {got!r}"


@then('station "{name}" must send {indications}')
def must_send(context, name, indications):
    got = sorted(_station(context, name).indications)
    assert got == _tokens(indications.strip('"')), f"station {name} must send {got!r}"


@given('the desk has these lamps for interlocking "{name}":')
def desk_lamps(context, name):
    """Desk lamps on the panel sheet of ``name``: ``Name`` and the ``Indication`` expression each consumes."""
    ou = _model(context).setdefault("officeUnits", {}).setdefault("Desk", {"columns": {}, "devices": []})
    for row in context.table:
        key, entity = _entity(row)
        entity.setdefault("given", {}).update({"Appliance": "lamp", "Style": "board", "Name": key})
        entity.setdefault("relations", {})["interlocking"] = name
        ou["devices"].append(entity)


@then('"{name}" reports "{token}" as a {kind}')
def reports(context, name, token, kind):
    """The appliance that states a token, as the codeline library reads the derived file."""
    ix = next(i for i, x in context.derived["interlockings"].items() if name in x.get("appliances", {}))
    got = codeline.reporters(context.derived, ix, token)
    assert got == [codeline.Reporter(kind, name)], f"{token} of {ix} is reported by {got!r}, not the {kind} {name}"


# ------------------------------------------------------------------- JMRI signal mast drivers (the owner, 2026-11-05, 2026-11-10)

@given("the layout has these I/O encodings:")
def io_encodings(context):
    """``Name`` the encoding's key, ``relations.transport`` and ``relations.processor`` its wire; every other column given."""
    encodings = _model(context).setdefault("layout", {}).setdefault("ioEncodings", {})
    for row in context.table:
        key, entity = _entity(row)
        encodings[key] = entity


@given('processor "{name}" has these drivers:')
def drivers(context, name):
    """``Key`` the driver's key on the processor's bus (an encoded driver's Kind.served); every other column given
    (IC, Kind, Address, JMRI.SignalSystem)."""
    proc = _model(context).setdefault("layout", {}).setdefault("processors", {}).setdefault(name, {"given": {"Board": "cpNode"}})
    for row in context.table:
        key, entity = _entity(row, key="Key")
        proc.setdefault("drivers", {})[key] = entity


@given('field mast device "{name}" of interlocking "{ixn}" binds "{pins}" to "{route}"')
def mast_binds(context, name, ixn, pins, route):
    """A signal mast device named for its mast, its position pins on the net of a driver pin: the bindings as the
    importer writes them, one per position the driver's net covers."""
    devices = _interlocking(context, ixn).setdefault("devices", [])
    dev = next((d for d in devices if d["given"].get("Appliance") == "mast" and d["given"].get("Name") == name), None)
    if dev is None:
        dev = {"given": {"Appliance": "mast", "Name": name}}
        devices.append(dev)
    dev.setdefault("relations", {}).setdefault("bindings", {}).update({p.strip(): route for p in pins.split(",")})


@given('the head on face "{face}" of "{name}" binds "{pin}" to "{route}"')
def head_binds(context, face, name, pin, route):
    ixn = _holder(context, name)
    heads = [d for d in _interlocking(context, ixn).get("devices", [])
             if d["given"].get("Appliance") == "head" and d.get("relations", {}).get("mast") == f"{ixn}:{name}" and d["relations"].get("face") == face]
    assert len(heads) == 1, f"{name} face {face}: {len(heads)} heads"
    heads[0]["relations"].setdefault("bindings", {})[pin] = route


def _driver(context, key: str, proc: str) -> dict:
    found = context.derived["layout"]["processors"][proc]["drivers"].get(key)
    assert found is not None, f"{proc}: no driver {key!r}"
    return found


@then('the driver "{key}" on "{proc}" stands in for positions "{positions}" of "{mast}"')
def stands_in(context, key, proc, positions, mast):
    d = _driver(context, key, proc).get("derived", {})
    want = [p.strip() for p in positions.split(",")]
    assert (d.get("mast"), d.get("positions")) == (mast, want), f"{key}: derived mast {d.get('mast')!r}, positions {d.get('positions')!r}"


@then('the driver "{key}" on "{proc}" publishes to the topic "{topic}"')
def topic(context, key, proc, topic):
    got = _driver(context, key, proc).get("derived", {}).get("topic")
    assert got == topic, f"{key}: derived.topic is {got!r}, not {topic!r}"


@then('the driver "{key}" on "{proc}" uses the signal system "{system}"')
def signal_system(context, key, proc, system):
    got = _driver(context, key, proc).get("derived", {}).get("jmriSignalSystem")
    assert got == system, f"{key}: derived.jmriSignalSystem is {got!r}, not {system!r}"


# ------------------------------------------------------------------- the aspect name tables (reference data, ADR 0012 §6)

@given('the signal system "{system}"')
def system(context, system):
    context.signal_system, context.user_aspects = system, {}


@given('the user\'s table says "{indication}" on a {kind} mast is "{name}"')
def user_aspect(context, indication, kind, name):
    context.user_aspects.setdefault(context.signal_system, {})[indication] = {kind: name}


@then('the indication "{indication}" on a {kind} mast has the aspect name "{name}"')
def aspect_name(context, indication, kind, name):
    got = reference.aspect_name(context.signal_system, indication, kind, context.user_aspects or None)
    assert got == name, f"{context.signal_system}: {indication} on a {kind} mast is {got!r}, not {name!r}"


@then('the indication "{indication}" on a {kind} mast has no aspect name')
def no_aspect_name(context, indication, kind):
    got = reference.aspect_name(context.signal_system, indication, kind, context.user_aspects or None)
    assert got is None, f"{context.signal_system}: {indication} on a {kind} mast is {got!r}"


# ------------------------------------------------------- reference data selected by the layout, resolved per entity (ADR 0012 §6)

def _pairs(text: str) -> list[tuple[str, str]]:
    """``A=B, C=D``."""
    return [tuple(p.strip() for p in item.split("=", 1)) for item in text.split(",") if item.strip()]


def _user(context) -> dict:
    if not hasattr(context, "user"):
        context.user = {}
    return context.user


@given('the layout states Railroad "{railroad}", Era "{era}" and Rulebook "{rulebook}"')
def layout_selection(context, railroad, era, rulebook):
    _model(context)["layout"].setdefault("given", {}).update({"Railroad": railroad, "Era": era, "Rulebook": rulebook})
    context.rulebook = rulebook


@given('the layout states Rulebook "{rulebook}"')
def layout_rulebook(context, rulebook):
    _model(context)["layout"].setdefault("given", {})["Rulebook"] = rulebook
    context.rulebook = rulebook


@given('the user\'s train order inputs for rulebook "{rulebook}" rank "{pairs}" and rest "{rest}"')
def user_train_order(context, rulebook, pairs, rest):
    row = {"inputs": [{"input": i, "indication": w} for i, w in _pairs(pairs)], "rest": rest}
    _user(context).setdefault("trainOrderInputs", {})[rulebook] = row
    context.user_train_order = _user(context)["trainOrderInputs"]


@given('the user\'s policy for rulebook "{rulebook}" with {count:d} heads says "{rows}"')
def user_policy(context, rulebook, count, rows):
    """``CLEAR = CLEAR, STOP; STOP = STOP, STOP``: mast indication = the head word of each position top down."""
    table = {}
    for item in rows.split(";"):
        indication, _, words = item.partition("=")
        table[indication.strip()] = [w.strip() for w in words.split(",") if w.strip()]
    _user(context).setdefault("policies", {}).setdefault(rulebook, {})[str(count)] = table


@given('the user\'s indication tokens for encoding "{encoding}" class "{cls}" are "{templates}"')
def user_tokens(context, encoding, cls, templates):
    _user(context).setdefault("indicationTokens", {}).setdefault(encoding, {})[cls] = [t.strip() for t in templates.split(",")]


@given('the layout has code line "{name}" of Kind "{kind}"')
def code_line(context, name, kind):
    _model(context)["layout"].setdefault("codelines", {})[name] = {"given": {"Kind": kind}}


@then('the layout resolved "{table}" to row "{key}"')
def resolved(context, table, key):
    got = context.derived["layout"].get("derived", {}).get("reference", {}).get(table)
    assert got == key, f"layout.derived.reference.{table} is {got!r}, not {key!r}"


@then('the layout resolved no row of "{table}"')
def resolved_none(context, table):
    got = context.derived["layout"].get("derived", {}).get("reference", {})
    assert table not in got, f"layout.derived.reference names {table}: {got[table]!r}"


@then('code line "{name}" has station "{what}"')
def code_line_station(context, name, what):
    got = context.derived["layout"]["codelines"][name].get("derived", {}).get("station")
    assert got == what, f"code line {name}: derived.station is {got!r}, not {what!r}"


@then('code line "{name}" has templates "{cls}: {templates}"')
def code_line_templates(context, name, cls, templates):
    got = context.derived["layout"]["codelines"][name].get("derived", {}).get("tokens", {}).get(cls)
    want = [t.strip() for t in templates.split(",")]
    assert got == want, f"code line {name}: derived.tokens.{cls} is {got!r}, not {want!r}"


@then('the "{face}" face of "{name}" ranks "{pairs}" and rests at "{rest}"')
def face_ranks(context, face, name, pairs, rest):
    f = _face(context, name, face)
    inputs = f.get("inputs", {})
    assert list(inputs) == [str(k) for k in range(1, len(inputs) + 1)], f"{name} face {face}: inputs are keyed by rank from 1, not {list(inputs)}"
    got = [(i["input"], i["indication"]) for i in inputs.values()]
    assert got == _pairs(pairs), f"{name} face {face}: inputs are {got!r}, not {_pairs(pairs)!r}"
    assert f.get("rest") == rest, f"{name} face {face}: rest is {f.get('rest')!r}, not {rest!r}"


@then('position "{position}" of "{mast}" shows "{pairs}"')
def position_shows(context, position, mast, pairs):
    got = _position(context, mast, position).get("shows")
    assert got == dict(_pairs(pairs)), f"{mast} position {position}: shows {got!r}, not {dict(_pairs(pairs))!r}"


@then('position "{position}" of "{mast}" shows nothing')
def position_shows_nothing(context, position, mast):
    got = _position(context, mast, position).get("shows")
    assert got is None, f"{mast} position {position}: shows {got!r}"


@then('the driver "{key}" on "{proc}" publishes the aspect names "{pairs}"')
def driver_aspect_names(context, key, proc, pairs):
    got = _driver(context, key, proc).get("derived", {}).get("aspectNames")
    assert got == dict(_pairs(pairs)), f"{key}: derived.aspectNames is {got!r}, not {dict(_pairs(pairs))!r}"


# ------------------------------------------------------------------- the routes of a mast (tools/railroad/routes.py, #139)

@when("the routes are found")
def routes_found(context):
    """Derive, then find the routes; the findings a Then checks are the routes library's."""
    context.derived, _ = derive.derive(_model(context), getattr(context, "user", None))
    context.routes = routes.find(context.derived)
    context.report = context.routes.report


def _q(context, mast: str) -> str:
    """A mast's qualified name: as written when qualified, else the one interlocking that has it."""
    if ":" in mast:
        return mast
    found = [b for b, ix in context.derived["interlockings"].items() if mast in ix.get("appliances", {})]
    assert len(found) == 1, f"{mast}: in {found}"
    return f"{found[0]}:{mast}"


def _local(scope: str, name: str) -> str:
    """A name as the scenario writes it: bare in the mast's own interlocking, qualified in another."""
    b, _, n = name.partition(":")
    return n if b == scope and n else name


def _alignment(context, mast: str, route) -> str:
    scope = _q(context, mast).partition(":")[0]
    return ", ".join(f"{_local(scope, s)} {p}" for s, p in route.alignment) or "nothing"


def _route(context, mast: str, alignment: str):
    found = [r for r in context.routes.of(_q(context, mast)) if _alignment(context, mast, r) == alignment]
    got = [_alignment(context, mast, r) for r in context.routes.of(_q(context, mast))]
    assert len(found) == 1, f"{mast}: {len(found)} routes aligned {alignment!r}; its routes: {got}"
    return found[0]


def _demand(context, mast: str, text: str) -> dict[str, str]:
    """A demand as a scenario writes it, ``830(RIGHT)`` or ``Y:816(LEFT)``, as the atoms the library states; a bare
    demand is in the interlocking of ``mast``. The scenario's words are parsed here, never the model's."""
    m = re.fullmatch(r"(?:([^:]+):)?(.+)\((LEFT|RIGHT)\)", text.strip())
    assert m, f"demand {text!r}"
    return {"interlocking": m.group(1) or _q(context, mast).partition(":")[0], "signal": m.group(2), "direction": m.group(3)}


def _names(text: str) -> list[str]:
    return [t.strip() for t in text.split(",") if t.strip()]


@then('"{mast}" has routes aligned "{alignments}"')
def has_routes(context, mast, alignments):
    got = [_alignment(context, mast, r) for r in context.routes.of(_q(context, mast))]
    want = [a.strip() for a in alignments.split(";")]
    assert sorted(got) == sorted(want), f"{mast}: routes aligned {got}, not {want}"


@then('"{mast}" has no routes')
def has_no_routes(context, mast):
    got = context.routes.of(_q(context, mast))
    assert not got, f"{mast}: {[r.label() for r in got]}"


@then('the route of "{mast}" aligned "{alignment}" is demanded by "{demand}"')
def demanded(context, mast, alignment, demand):
    got, want = _route(context, mast, alignment).demand, _demand(context, mast, demand)
    assert got == want, f"demand {got!r}, not {want!r}"


@then('the route of "{mast}" aligned "{alignment}" has no entering demand')
def no_demand(context, mast, alignment):
    got = _route(context, mast, alignment).demand
    assert got is None, f"demand {got!r}"


@then('the route of "{mast}" aligned "{alignment}" passes "{circuits}"')
def passes(context, mast, alignment, circuits):
    scope = _q(context, mast).partition(":")[0]
    got = [_local(scope, c) for c in _route(context, mast, alignment).circuits]
    assert got == _names(circuits), f"circuits {got}, not {_names(circuits)}"


@then('the route of "{mast}" aligned "{alignment}" enters at "{circuit}"')
def enters(context, mast, alignment, circuit):
    scope = _q(context, mast).partition(":")[0]
    got = _route(context, mast, alignment).entrance
    assert got and _local(scope, got) == circuit, f"entrance {got!r}, not {circuit!r}"


@then('the route of "{mast}" aligned "{alignment}" approaches over "{circuit}"')
def approaches(context, mast, alignment, circuit):
    scope = _q(context, mast).partition(":")[0]
    got = _route(context, mast, alignment).approach
    assert got and _local(scope, got) == circuit, f"approach {got!r}, not {circuit!r}"


@then('the route of "{mast}" aligned "{alignment}" ends at mast "{end}" demanding "{demand}"')
def ends_demanding(context, mast, alignment, end, demand):
    got = _route(context, mast, alignment).end or {}
    assert got.get("mast") == _q(context, end) and got.get("demand") == _demand(context, mast, demand), f"end {got}"


@then('the route of "{mast}" aligned "{alignment}" ends at mast "{end}" with no demand')
def ends_no_demand(context, mast, alignment, end):
    got = _route(context, mast, alignment).end or {}
    assert got.get("mast") == _q(context, end) and "demand" not in got, f"end {got}"


@then('the route of "{mast}" aligned "{alignment}" ends at the limit "{limit}"')
def ends_at_limit(context, mast, alignment, limit):
    got = _route(context, mast, alignment).end or {}
    assert got.get("limit") == limit and "mast" not in got, f"end {got}"


@then('the route of "{mast}" aligned "{alignment}" has no end')
def has_no_end(context, mast, alignment):
    got = _route(context, mast, alignment).end
    assert got is None, f"end {got}"


@then('the route of "{mast}" aligned "{alignment}" is opposed by masts "{masts}"')
def opposed_masts(context, mast, alignment, masts):
    got = sorted(o["mast"] for o in _route(context, mast, alignment).opposing)
    want = sorted(_q(context, m) for m in _names(masts))
    assert got == want, f"opposing masts {got}, not {want}"


@then('the route of "{mast}" aligned "{alignment}" is opposed by demands "{demands}"')
def opposed_demands(context, mast, alignment, demands):
    key = lambda d: (d["interlocking"], d["signal"], d["direction"])
    got = sorted((o["demand"] for o in _route(context, mast, alignment).opposing if "demand" in o), key=key)
    want = sorted((_demand(context, mast, d) for d in _names(demands)), key=key)
    assert got == want, f"opposing demands {got}, not {want}"


@then('the route of "{mast}" aligned "{alignment}" passes no circuit')
def passes_no_circuit(context, mast, alignment):
    got = _route(context, mast, alignment).circuits
    assert not got, f"circuits {got}"


@then('the route of "{mast}" aligned "{alignment}" has ceiling "{word}"')
def route_ceiling(context, mast, alignment, word):
    got = _route(context, mast, alignment).ceiling
    assert got == word, f"ceiling {got!r}, not {word!r}"


# ------------------------------------------------------------------- ladders and selectors (issue #145; the owner, 2026-11-13)

def _selector(context, name: str) -> dict:
    found = [d for ix in context.derived["interlockings"].values() for d in ix.get("devices", [])
             if d.get("given", {}).get("Appliance") == "selector" and d["given"].get("Name") == name]
    assert len(found) == 1, f"{name}: {len(found)} selectors of that name"
    return found[0]


def _label(choice: dict) -> str:
    """A choice in the owner's notation, ``17R: 15N 17R``: the leg, then the alignment, each switch unqualified."""
    switch, _, port = choice["leg"].rpartition(".")
    return f"{switch.partition(':')[2]}{port}: " + " ".join(
        f"{a['appliance'].partition(':')[2]}{a['position'][0]}" for a in choice["alignment"])


@then('selector "{name}" offers "{choices}"')
def selector_offers(context, name, choices):
    got = _selector(context, name).get("derived", {}).get("choices", [])
    assert [c["detent"] for c in got] == list(range(1, len(got) + 1)), f"{name}: detents {[c['detent'] for c in got]}"
    labels = "; ".join(_label(c) for c in got)
    assert labels == choices, f"{name} offers {labels!r}, not {choices!r}"


@then('selector "{name}" offers no choices')
def selector_offers_none(context, name):
    got = _selector(context, name).get("derived", {}).get("choices")
    assert got is None, f"{name} offers {got!r}"


@then('selector "{name}" ranges from {low:d} to {high:d}')
def selector_range(context, name, low, high):
    got = _selector(context, name).get("derived", {}).get("range")
    assert got == {"min": low, "max": high}, f"{name}: range {got!r}"


@then('ladder "{rid}" starts at "{start}" with switches "{switches}"')
def ladder_switches(context, rid, start, switches):
    d = _row_named(context, rid).get("derived", {})
    assert d.get("start") == start, f"{rid}: start {d.get('start')!r}"
    assert d.get("switches") == [s.strip() for s in switches.split(",")], f"{rid}: switches {d.get('switches')!r}"


def _given_selector(context, name: str) -> dict:
    return next(d for ix in _model(context)["interlockings"].values() for d in ix.get("devices", [])
                if d.get("given", {}).get("Appliance") == "selector" and d["given"].get("Name") == name)


@given('selector "{name}" binds VALUE to "{value}" and BUTTON to "{lock}"')
def selector_binds(context, name, value, lock):
    _given_selector(context, name).setdefault("relations", {})["bindings"] = {"VALUE": value, "BUTTON": lock}


@given('selector "{name}" binds VALUE to "{value}"')
def selector_binds_value(context, name, value):
    _given_selector(context, name).setdefault("relations", {})["bindings"] = {"VALUE": value}


@given('the desk has a CODE button on column "{column}" bound to "{route}"')
def code_button(context, column, route):
    """A desk code lever (Appliance lever, Style code) in a column, its CODE pin bound to ``route``."""
    _desk(context)["devices"].append({"given": {"Appliance": "lever", "Name": "CODE", "Style": "code", "Control.CODE": ""},
                                      "relations": {"column": f"Desk:{column}", "bindings": {"CODE": route}}})


@then('selector "{name}" goes to station "{station}"')
def selector_station(context, name, station):
    got = _selector(context, name).get("derived", {}).get("station")
    assert got == station, f"{name}: station {got!r}, not {station!r}"


@then('selector "{name}" goes to no station')
def selector_no_station(context, name):
    got = _selector(context, name).get("derived", {}).get("station")
    assert got is None, f"{name}: station {got!r}"


@then('selector "{name}" is sent by the CODE button of column "{column}"')
def selector_code(context, name, column):
    got = _selector(context, name).get("derived", {}).get("code")
    assert got == column, f"{name}: code {got!r}, not {column!r}"


@then('selector "{name}" is sent by no CODE button')
def selector_no_code(context, name):
    d = _selector(context, name).get("derived", {})
    assert d.get("code") is None and "send" not in d.get("inputs", {}), f"{name}: code {d.get('code')!r}, inputs {d.get('inputs')!r}"


@then('selector "{name}" shows its choice on "{value}", locks it in on "{lock}" and sends it on "{send}"')
def selector_inputs(context, name, value, lock, send):
    got = _selector(context, name).get("derived", {}).get("inputs")
    want = {"value": value, "lock": lock, "send": send}
    assert got == want, f"{name}: inputs {got!r}, not {want!r}"
