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
python3 - "$OUT" <<'PY'
import json
import sys

g = json.load(open(sys.argv[1]))
assert not g.get("diagnostics"), g.get("diagnostics")
assert len(g["routes"]) == 10, len(g["routes"])
kinds = {r["end_kind"] for r in g["routes"]}
assert kinds <= {"cp_limit", "dead_end", "next_face"}, kinds
assert sum(1 for r in g["routes"] if r["end_kind"] == "dead_end") == 2
assert sum(1 for r in g["routes"] if r["end_kind"] == "cp_limit") == 8
r0 = g["routes"][0]
for key in (
    "switch_alignments",
    "clear_track_circuits",
    "head_letters",
    "end_kind",
    "mast_name",
    "exit_face_mast",
):
    assert key in r0, key
assert "name_aliases" in g
print("Luchessa OK: 10 routes, diagnostics clean, eval fields present")
PY
echo 'SMOKE OK'
