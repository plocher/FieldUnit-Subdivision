#!/usr/bin/env python3
"""Resolve the field I/O symbols of one plant project against its plant and drivers.

Usage (from the FieldUnit-Subdivision repo root, after `make -B netlist` in the project):
    python3 docs/review/handoff-field-io-cleanup/field_resolve.py ~/Dropbox/KiCad/Railroad/SPCoast/Sargent/Sargent.net

Reports, for every RailroadField / RailroadPanel symbol on the sheet: the plant
item its Value resolves to (switch, circuit, head, auxiliary, or none), each pin's
binding to a driver pin, driver pins used by more than one device, and driver
addresses. It is the check the generator will do; the compiler does not know
these symbols yet.
"""
import argparse
import collections
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
from parse_kicad_plant import load_graph  # noqa: E402

LIB = Path.home() / "Dropbox/KiCad/InterlockingPlant/symbols/Railroad.kicad_sym"


def main(netlist):
    graph = load_graph(argparse.Namespace(library=LIB, schematic=None, netlist=Path(netlist),
                                          kicad_cli=None, aliases=None))
    ents = graph.entities
    heads = set()
    for e in ents.values():
        lib = (e.lib_id or "").split(":")[-1]
        if lib.startswith("Mast"):
            m = re.match(r"^(\d+)([NSEW])([A-Z]+)$", e.value or "")
            if m:
                heads.update(f"{m.group(1)}{m.group(2)}{letter}" for letter in m.group(3))
    plant = {
        "switch": {e.value for e in ents.values() if (e.lib_id or "").split(":")[-1].startswith("Switch")},
        "circuit": {e.value for e in ents.values() if "Track Circuit" in (e.lib_id or "")}
                   | {t.name for t in graph.derived_track_circuits},
        "head": heads,
        "aux": {e.value for e in ents.values() if (e.lib_id or "").split(":")[-1] in ("AUXILIARY", "MaintainerCall", "AUXILIARY_TRAFFIC")},
    }
    text = open(netlist).read()
    comps = {}
    for m in re.finditer(r'\(comp\n\t\t\t\(ref "([^"]+)"\)\n\t\t\t\(value "([^"]*)"\)([\s\S]*?)\n\t\t\)', text):
        ref, val, body = m.groups()
        lib = re.search(r'\(lib "([^"]+)"\)', body).group(1)
        part = re.search(r'\(part "([^"]+)"\)', body).group(1)
        fields = dict(re.findall(r'\(name "([^"]+)"\) "([^"]*)"\)', body))
        if lib in ("RailroadField", "RailroadPanel"):
            comps[ref] = (lib, part, val, fields)
    i = text.index("\n\t(nets")
    nets, pinnet = {}, {}
    for m in re.finditer(r'\n\t\t\(net\n\t\t\t\(code "[^"]*"\)\n\t\t\t\(name "([^"]*)"\)(.*?)\n\t\t\)', text[i:], re.S):
        nodes = re.findall(r'\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)\s*\(pinfunction "([^"]*)"', m.group(2))
        nets[m.group(1)] = nodes
        for r, p, _ in nodes:
            pinnet[(r, p)] = m.group(1)
    drivers = {r for r, (lib, part, v, f) in comps.items() if f.get("Role", "").upper() == "IODRIVER"}
    use = collections.defaultdict(list)
    print("== symbols")
    for r, (lib, part, val, f) in sorted(comps.items()):
        if r in drivers:
            print(f"  {r:8} {lib}:{part:30} addr={f.get('Address')}")
            continue
        where = [k for k, s in plant.items() if val in s]
        binds = []
        for (rr, pin), nn in pinnet.items():
            if rr != r:
                continue
            fn = [x[2] for x in nets[nn] if x[0] == r][0].rsplit("_", 1)[0]
            drv = [(x, xfn.rsplit("_", 1)[0]) for x, _, xfn in nets[nn] if x in drivers]
            for d in drv:
                use[d].append(r)
            binds.append((fn, drv[0] if drv else ("UNCONNECTED" if nn.startswith("unconnected") else "?")))
        print(f"  {r:8} {lib}:{part:30} {val!r:9} kind={f.get('Kind')!r:22} -> {where or 'NO PLANT ITEM'} {binds}")
    shared = {k: v for k, v in use.items() if len(v) > 1}
    print("== driver pins used by more than one device:", shared or "none")
    addrs = collections.Counter(comps[r][3].get("Address") for r in drivers)
    print("== driver addresses:", dict(addrs), "(duplicates are a conflict)")


if __name__ == "__main__":
    main(sys.argv[1])
