"""Writes spcoast.layout.json, the ADR 0008 rev 4 §6 example: the compiler's output on the SPCoast project, never typed.

    uv run python schemas/layout-model/examples/make_spcoast_layout.py [NETLIST.net]

The netlist is a kicad-cli kicadsexpr export of ~/Dropbox/KiCad/Railroad/SPCoast/SPCoast.kicad_sch (default:
SPCoast/production/railroad-after.net). The compiler refuses to write while the drawing has an error.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
NETLIST = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Dropbox/KiCad/Railroad/SPCoast/production/railroad-after.net"

if __name__ == "__main__":
    out = Path(__file__).with_name("spcoast.layout.json")
    sys.exit(subprocess.run([sys.executable, str(ROOT / "tools/compile_layout.py"), str(NETLIST), "-o", str(out), "--quiet"]).returncode)
