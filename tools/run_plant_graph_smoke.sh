#!/usr/bin/env bash
# Regression smoke for the KiCad plant-graph spike.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo '== unit tests =='
python3 -m unittest tests.test_kicad_plant_graph -q

LIB="${KICAD_RAILROAD_LIB:-$HOME/Dropbox/KiCad/InterlockingPlant/symbols/Railroad.kicad_sym}"
SCH="${KICAD_LUCHESSA_SCH:-$HOME/Dropbox/KiCad/Railroad/SPCoast/CP_Luchessa/CP_Luchessa.kicad_sch}"

if [[ ! -f "$LIB" || ! -f "$SCH" ]]; then
  echo 'SKIP Luchessa integration (set KICAD_RAILROAD_LIB / KICAD_LUCHESSA_SCH)'
  exit 0
fi

echo '== Luchessa parse =='
OUT="$(mktemp -t plant_graph_smoke)"
ERR="$(mktemp -t plant_graph_smoke_err)"
set +e
python3 tools/parse_kicad_plant.py --library "$LIB" --schematic "$SCH" --format json >"$OUT" 2>"$ERR"
RC=$?
set -u
if [[ "$RC" -ne 0 ]]; then
  echo "Luchessa CLI exit $RC" >&2
  cat "$ERR" >&2
  exit "$RC"
fi
set -eu
python3 - "$OUT" <<'PY'
import json
import sys

g = json.load(open(sys.argv[1]))
errors = [
    diagnostic
    for diagnostic in g.get("diagnostics", [])
    if diagnostic["severity"] in {"syntax", "semantic"}
]
assert not errors, errors
assert len(g["routes"]) == 10, len(g["routes"])
geometry = {entry["switch"]: entry for entry in g["switch_geometries"]}
assert set(geometry) == {"783", "795", "799"}, geometry
assert geometry["783"]["cn_heading"] == "right", geometry
assert geometry["783"]["reverse_side"] == "left", geometry
assert geometry["795"]["cn_heading"] == "left", geometry
assert geometry["795"]["reverse_side"] == "left", geometry
assert geometry["799"]["cn_heading"] == "right", geometry
assert geometry["799"]["reverse_side"] == "right", geometry
kinds = {r["end_kind"] for r in g["routes"]}
assert kinds <= {"cp_limit", "dead_end", "dark_exit", "next_face"}, kinds
assert sum(1 for r in g["routes"] if r["end_kind"] == "dark_exit") == 2
assert sum(1 for r in g["routes"] if r["end_kind"] == "cp_limit") == 8
assert {route["name"] for route in g["routes"]} == {
    "MT2-MT",
    "MT1-Industry",
    "MT1-MT",
    "Branch-Industry",
    "Branch-MT",
    "MT-Branch",
    "MT-MT1",
    "MT-MT2",
    "2SA-Branch",
    "2SA-MT1",
}
indications_by_route = {
    route["name"]: route["static_indication"]
    for route in g["routes"]
}
assert indications_by_route["MT1-Industry"] == "DIVERGING_RESTRICTING"
assert indications_by_route["Branch-Industry"] == "DIVERGING_RESTRICTING"
layout = g["rail_layout"]
assert layout["width_units"] == 3, layout
components = {
    component["identifier"]: component
    for component in layout["components"]
}
ports = {
    port["identifier"]: port
    for component in layout["components"]
    for port in component["ports"]
}
connections = layout["connections"]
assert {
    component_id
    for component_id, component in components.items()
    if component["kind"] == "turnout"
} == {"turnout:783", "turnout:795", "turnout:799"}
assert len(connections) == len(layout["spans"]), connections
port_uses = {}
for connection in connections:
    for port_id in (connection["start_port_id"], connection["end_port_id"]):
        assert port_id in ports, connection
        assert ports[port_id]["row_name"] == connection["row_name"], connection
        port_uses[port_id] = port_uses.get(port_id, 0) + 1
assert max(port_uses.values(), default=0) == 1, port_uses
turnout_ports = {
    component_id: {port["name"]: port for port in component["ports"]}
    for component_id, component in components.items()
    if component["kind"] == "turnout"
}
assert turnout_ports["turnout:783"]["R"]["x_units"] > (
    turnout_ports["turnout:783"]["C"]["x_units"]
)
assert turnout_ports["turnout:795"]["R"]["x_units"] < (
    turnout_ports["turnout:795"]["C"]["x_units"]
)
assert turnout_ports["turnout:799"]["R"]["x_units"] > (
    turnout_ports["turnout:799"]["C"]["x_units"]
)
assert {
    component_id: (
        component["actuator_kind"],
        component["mirror_x"],
        component["mirror_y"],
    )
    for component_id, component in components.items()
    if component["kind"] == "turnout"
} == {
    "turnout:783": ("switch", False, False),
    "turnout:795": ("lock", True, True),
    "turnout:799": ("switch", False, False),
}
connections_by_name = {
    connection["identifier"]: connection
    for connection in connections
}
assert connections_by_name["Net-(B10-A)"]["start_port_id"] == "irj:B10:left"
assert connections_by_name["2SA"]["start_port_id"] == "irj:B10:right"
for connection in connections:
    endpoint_ids = (connection["start_port_id"], connection["end_port_id"])
    if any(port_id.endswith(":R") for port_id in endpoint_ids):
        other_port_id = next(
            port_id
            for port_id in endpoint_ids
            if not port_id.endswith(":R")
        )
        if other_port_id.startswith("irj:"):
            turnout_port_id = next(
                port_id for port_id in endpoint_ids if port_id.endswith(":R")
            )
            assert (
                abs(
                ports[turnout_port_id]["x_units"]
                - ports[other_port_id]["x_units"]
                )
                >= 0.249999
            ), connection
signal_components = {
    component["label"]: component
    for component in components.values()
    if component["kind"] == "signal"
}
assert (
    signal_components["784EC"]["x_units"]
    == components["irj:B4"]["x_units"]
)
assert [
    (section["name"], section["index"])
    for section in layout["sections"]
] == [
    ("CP Luchessa", 0),
    ("CP Gilroy", 1),
    ("CP Carnadero", 2),
], layout["sections"]
for section, expected_center in zip(
    layout["sections"],
    (0.45, 1.35, 2.25),
):
    assert abs(section["center_units"] - expected_center) < 1e-9, section
assert len(layout["rows"]) == 3, layout["rows"]
assert {terminal["name"] for terminal in layout["terminals"]} == {
    "Industry", "Branch", "MT", "MT1", "MT2"
}, layout["terminals"]
assert {
    terminal["name"]
    for terminal in layout["terminals"]
    if terminal["is_plant_edge"]
} == {"MT", "Branch", "MT1", "MT2"}, layout["terminals"]
terminal_rows = {
    terminal["name"]: terminal["row_name"]
    for terminal in layout["terminals"]
}
assert terminal_rows["MT"] == terminal_rows["MT1"], terminal_rows
assert terminal_rows["Industry"] == terminal_rows["Branch"], terminal_rows
assert terminal_rows["MT2"] not in {
    terminal_rows["MT"],
    terminal_rows["Industry"],
}, terminal_rows
assert {turnout["switch_name"] for turnout in layout["turnouts"]} == {
    "783", "795", "799"
}, layout["turnouts"]
for turnout in layout["turnouts"]:
    assert turnout["c_row"] == turnout["n_row"], turnout
assert {
    turnout["switch_name"]: turnout["r_row"]
    for turnout in layout["turnouts"]
} == {
    "783": terminal_rows["MT2"],
    "795": terminal_rows["Industry"],
    "799": terminal_rows["Branch"],
}
turnout_anchors = {
    turnout["switch_name"]: turnout["anchor"]
    for turnout in layout["turnouts"]
}
assert {
    turnout["switch_name"]: turnout["section_index"]
    for turnout in layout["turnouts"]
} == {"783": 0, "795": 1, "799": 2}
signal_anchors = {
    signal["mast_name"]: signal["anchor"]
    for signal in layout["signal_bases"]
}
anchor_positions = {
    int(anchor): position
    for anchor, position in layout["anchor_positions"].items()
}
# Signal masts sit a short physical dogleg from their protected turnout.
# Exact anchor-index adjacency is not guaranteed once other real appliances
# (e.g. a derail) share the same corridor and consume intermediate anchors.
for mast_name, switch_name in (("784EAB", "783"), ("784EC", "795"), ("784WD", "799")):
    dogleg = abs(
        anchor_positions[signal_anchors[mast_name]]
        - anchor_positions[turnout_anchors[switch_name]]
    )
    assert 0.0 < dogleg <= 0.9, (mast_name, switch_name, dogleg)
assert abs(anchor_positions[turnout_anchors["783"]] - 0.45) < 1e-9
assert abs(anchor_positions[turnout_anchors["795"]] - 1.35) < 1e-9
assert abs(anchor_positions[turnout_anchors["799"]] - 2.25) < 1e-9
two_naa = next(span for span in layout["spans"] if span["name"] == "2NAA")
assert abs(
    (anchor_positions[two_naa["start_anchor"]]
     + anchor_positions[two_naa["end_anchor"]]) / 2
    - (anchor_positions[turnout_anchors["795"]]
       + anchor_positions[turnout_anchors["799"]]) / 2
) < 1e-9
edge_circuit_spans = {
    span["circuit_name"]: span
    for span in layout["spans"]
    if span["circuit_name"] in {"1SA", "2NA", "3NA"}
}
for circuit_name, span in edge_circuit_spans.items():
    assert (
        anchor_positions[span["end_anchor"]]
        - anchor_positions[span["start_anchor"]]
        >= 0.18
    ), (circuit_name, span)
assert {
    turnout["switch_name"]: turnout["actuator_kind"]
    for turnout in layout["turnouts"]
} == {"783": "switch", "795": "lock", "799": "switch"}
assert {
    turnout["switch_name"]: turnout["actuator_flipped"]
    for turnout in layout["turnouts"]
} == {"783": False, "795": True, "799": False}
assert {lamp["circuit_name"] for lamp in layout["track_circuit_lamps"]} == {
    "1SA", "2SA", "1NA", "2NAA", "2NA", "3NA"
}
assert len(layout["signal_bases"]) == 5, layout["signal_bases"]
assert all(span["row_name"] for span in layout["spans"]), layout["spans"]
assert [span["name"] for span in layout["spans"] if span["is_dark"]] == [
    "Net-(B10-A)"
], layout["spans"]
dark_stub = next(span for span in layout["spans"] if span["is_dark"])
assert dark_stub["is_local_stub"], dark_stub
assert dark_stub["local_stub_direction"] == "left", dark_stub
r0 = g["routes"][0]
for key in (
    "switch_alignments",
    "clear_track_circuits",
    "head_letters",
    "head_names",
    "end_kind",
    "mast_name",
    "exit_face_mast",
):
    assert key in r0, key
for route in g["routes"]:
    for crossing in route["switch_traversals"]:
        assert crossing["switch"] in geometry, crossing
        assert crossing["point_traversal"] in {"facing", "trailing"}, crossing
    roles = {item["role"] for item in route["circuit_roles"]}
    if route["end_kind"] == "dead_end":
        assert "downstream" not in roles, route
heads_by_mast = {}
for attachment in g["mast_heads"]:
    heads_by_mast.setdefault(attachment["mast_reference"], []).append(
        attachment["head_name"]
    )
for route in g["routes"]:
    assert sorted(route["head_names"]) == sorted(
        heads_by_mast.get(route["mast_reference"], [])
    ), route
assert "name_aliases" in g
print("Luchessa OK: 10 routes, diagnostics clean, route heads attached")
PY
echo 'SMOKE OK'
echo '== Luchessa portable model =='
MODEL_JSON="$(mktemp -t plant_graph_model)"
python3 tools/parse_kicad_plant.py \
  --library "$LIB" \
  --schematic "$SCH" \
  --format plant-model-json \
  --plant-name "CP Luchessa" \
  --plant-id spcoast.luchessa \
  --output "$MODEL_JSON"
python3 - "$MODEL_JSON" <<'PY'
import json
import sys

model = json.load(open(sys.argv[1]))
assert model["$schema"] == "https://fieldunit.dev/schema/interlocking-plant/v1.json"
assert model["schemaVersion"] == "1.0.0"
assert model["identity"] == {"id": "spcoast.luchessa", "name": "CP Luchessa"}
assert len(model["routes"]) == 10
assert {item["id"] for item in model["appliances"]["switches"]} == {
    "783", "795", "799",
}
assert "diagnostics" not in model
assert "rail_layout" not in model
assert "raw_name" not in json.dumps(model)
assert "lib_id" not in json.dumps(model)
print("Luchessa portable model OK")
PY
echo '== Luchessa FieldUnit projection =='
FIELDUNIT_JSON="$(mktemp -t plant_graph_fieldunit)"
python3 tools/parse_kicad_plant.py \
  --library "$LIB" \
  --schematic "$SCH" \
  --format fieldunit-json \
  --plant-name "CP Luchessa" \
  --plant-id spcoast.luchessa \
  --output "$FIELDUNIT_JSON"
python3 - "$FIELDUNIT_JSON" <<'PY'
import json
import sys

plant = json.load(open(sys.argv[1]))
assert plant["name"] == "CP Luchessa"
assert len(plant["routes"]) == 10
assert {item["name"] for item in plant["switches"]} == {
    "783", "795", "795D", "799",
}
assert {
    item["type"] for item in plant["signalMasts"]
} <= {"ONE_HEAD", "TWO_HEAD", "THREE_HEAD", "DWARF"}
for route in plant["routes"]:
    assert set(route) >= {
        "name", "governedBy", "displays", "aligns", "clears",
    }, route
    assert "headIndex" not in route["displays"], route
deferred = plant["projectionDeferred"]
assert deferred["document"]["title"] == "CP Luchessa"
assert deferred["profile"]["ctc"] == "US&S 506"
assert deferred["controlledPoints"]
assert deferred["derails"] == [{
    "id": "795D",
    "controlMode": "dependent",
    "controllingSwitch": "795",
    "trackCircuit": None,
}]
assert len(deferred["routeTopology"]) == len(plant["routes"])
print("Luchessa FieldUnit projection OK")
PY
echo '== Luchessa route overlays =='
ROUTE_SVG="$(mktemp -t plant_graph_route_overlay)"
python3 tools/render_plant_picture.py \
  --library "$LIB" \
  --schematic "$SCH" \
  --format route-board-svg \
  --output "$ROUTE_SVG"
python3 - "$ROUTE_SVG" <<'PY'
import sys

svg = open(sys.argv[1]).read()
assert 'id="board-route-list"' in svg
assert 'function showRoute(id)' in svg
assert svg.count('class="route-overlay"') == 10
assert svg.count('style="display:none"') >= 10
PY
python3 tools/render_plant_picture.py \
  --library "$LIB" \
  --schematic "$SCH" \
  --format route-board-svg \
  --route MT-MT1 \
  --output "$ROUTE_SVG"
python3 - "$ROUTE_SVG" <<'PY'
import sys

svg = open(sys.argv[1]).read()
assert 'class="route-overlay" data-route="MT-MT1"' in svg
assert 'data-indication="CLEAR"' in svg
assert 'data-route-color="#22C55E"' in svg
assert 'data-aspect="green"' in svg
assert svg.count('data-aspect="red"') >= 2
PY
python3 tools/render_plant_picture.py \
  --library "$LIB" \
  --schematic "$SCH" \
  --format route-board-svg \
  --route MT-Branch \
  --output "$ROUTE_SVG"
python3 - "$ROUTE_SVG" <<'PY'
import sys

svg = open(sys.argv[1]).read()
assert 'class="route-overlay" data-route="MT-Branch"' in svg
assert 'data-indication="APPROACH"' in svg
assert 'data-route-color="#FACC15"' in svg
assert 'data-aspect="yellow"' in svg
PY
