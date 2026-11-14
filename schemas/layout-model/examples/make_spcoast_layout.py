"""Writes spcoast.layout.json, the ADR 0008 rev 4 §6 example: the KiCad importer's output on the SPCoast project, never
typed, with its three maps (ADR 0011) and its geometry and glyphs (ADR 0010), so the views of ADR 0010 read it as they
read any Layout Data Model File.

    uv run python schemas/layout-model/examples/make_spcoast_layout.py
    uv run python schemas/layout-model/examples/make_spcoast_layout.py --live [PROJECT.kicad_sch | NETLIST.net]

By default the example is built from the SPCoast test corpus: the Railroad repository at the commit spcoast.corpus.json
pins, checked out into a temporary directory (kicad_services.pinned), its netlist exported there by kicad-cli and its
own symbol libraries read, all deleted after. The example is then reproducible however the live drawing changes. To
refreeze the corpus, change the commit in spcoast.corpus.json and run this script; the gates that read the corpus
(tests.spcoast_corpus) then read the same commit.

--live builds from the live drawing instead, by default ~/Dropbox/KiCad/Railroad/SPCoast/SPCoast.kicad_sch exported
fresh. A saved netlist may be named instead, on a machine where kicad-cli cannot run; it is used only while it is
still a snapshot of the Railroad repository (RAILROAD_REPO, default ~/Dropbox/KiCad/Railroad: no uncommitted change
under SPCoast/ and symbols/, no commit there newer than the file), and a stale one stops this script with what is
stale. The importer refuses to write while the drawing has an error.
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CORPUS = Path(__file__).with_name("spcoast.corpus.json")
OUT = Path(__file__).with_name("spcoast.layout.json")
LIVE = Path.home() / "Dropbox/KiCad/Railroad/SPCoast/SPCoast.kicad_sch"
RAILROAD = Path(os.environ.get("RAILROAD_REPO", Path.home() / "Dropbox/KiCad/Railroad"))
SNAPSHOT_PATHS = ("SPCoast", "symbols")


def compile_layout(project: Path, *extra: str) -> int:
    return subprocess.run([sys.executable, str(ROOT / "tools/compile_layout.py"), str(project), "-o", str(OUT), "--quiet", *extra]).returncode


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--live", nargs="?", type=Path, const=LIVE, metavar="PROJECT_OR_NETLIST",
                    help="build from the live drawing (default %(const)s) instead of the pinned corpus")
    a = ap.parse_args()
    sys.path.insert(0, str(ROOT))
    if a.live is None:
        from tools.kicad_services import pinned
        pin = pinned.Pin.load(CORPUS)
        if not pin.available():
            sys.exit(f"the corpus commit {pin.commit} is not in {pin.repository}")
        with pinned.checkout(pin.repository, pin.commit, pin.paths) as work:
            sys.exit(compile_layout(work / pin.project, "--symbols", str(work / pin.symbols)))
    if a.live.suffix != ".kicad_sch":
        from tools.kicad_services import snapshot
        reasons = snapshot.stale_reasons(a.live, RAILROAD, SNAPSHOT_PATHS)
        if reasons:
            print(f"the netlist {a.live} is stale; export it again:\n  " + "\n  ".join(reasons), file=sys.stderr)
            sys.exit(1)
    sys.exit(compile_layout(a.live))
