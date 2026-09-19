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
kinds = {r["end_kind"] for r in g["routes"]}
assert kinds <= {"cp_limit", "dead_end", "dark_exit", "next_face"}, kinds
assert sum(1 for r in g["routes"] if r["end_kind"] == "dark_exit") == 2
assert sum(1 for r in g["routes"] if r["end_kind"] == "cp_limit") == 8
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
