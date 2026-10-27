"""Writes spcoast.layout.json, the ADR 0008 rev 4 §6 example: the KiCad importer's output on the SPCoast project, never
typed, with its three maps (ADR 0011) and its geometry and glyphs (ADR 0010), so the views of ADR 0010 read it as they
read any Layout Data Model File.

    uv run python schemas/layout-model/examples/make_spcoast_layout.py [PROJECT.kicad_sch | NETLIST.net]

By default the importer exports a fresh netlist of ~/Dropbox/KiCad/Railroad/SPCoast/SPCoast.kicad_sch into a
temporary location and deletes it (the netlist rule, AGENTS.md). A saved netlist may be named instead, on a machine
where kicad-cli cannot run; it is used only while it is still a snapshot of the Railroad repository (RAILROAD_REPO,
default ~/Dropbox/KiCad/Railroad: no uncommitted change under SPCoast/ and symbols/, no commit there newer than the
file), and a stale one stops this script with what is stale. The importer refuses to write while the drawing has an
error.
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROJECT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Dropbox/KiCad/Railroad/SPCoast/SPCoast.kicad_sch"
RAILROAD = Path(os.environ.get("RAILROAD_REPO", Path.home() / "Dropbox/KiCad/Railroad"))
SNAPSHOT_PATHS = ("SPCoast", "symbols")

if __name__ == "__main__":
    if PROJECT.suffix != ".kicad_sch":
        sys.path.insert(0, str(ROOT))
        from tools.kicad_services import snapshot
        reasons = snapshot.stale_reasons(PROJECT, RAILROAD, SNAPSHOT_PATHS)
        if reasons:
            print(f"the netlist {PROJECT} is stale; export it again:\n  " + "\n  ".join(reasons), file=sys.stderr)
            sys.exit(1)
    out = Path(__file__).with_name("spcoast.layout.json")
    sys.exit(subprocess.run([sys.executable, str(ROOT / "tools/compile_layout.py"), str(PROJECT), "-o", str(out), "--quiet"]).returncode)
