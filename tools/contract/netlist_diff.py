#!/usr/bin/env python3
"""Netlist gate: compare two KiCad netlists by connectivity, ignoring net names.

    python3 tools/contract/netlist_diff.py BEFORE.net AFTER.net [--ignore REGEX]

A net is the set of its (reference, pin number) nodes. The report lists nets lost, nets gained,
nodes that were on a net before and are on none after (dangling), nodes new after, and
components added or removed. Exit 1 when anything differs. `--ignore` drops nodes whose
reference matches the regex (for parts deleted on purpose).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kicad_services.netlist_reader import NetlistReader  # noqa: E402


def connectivity(path: Path, ignore: re.Pattern | None) -> tuple[set[frozenset], dict[str, str]]:
    model = NetlistReader().read(path)
    nets = set()
    for net in model.nets:
        nodes = frozenset((n.reference, n.pin) for n in net.nodes if not (ignore and ignore.search(n.reference)))
        if len(nodes) > 1:
            nets.add(nodes)
    parts = {ref: f"{c.lib}:{c.part}" for ref, c in model.components.items() if not (ignore and ignore.search(ref))}
    return nets, parts


def fmt(net: frozenset) -> str:
    return ", ".join(f"{r}.{p}" for r, p in sorted(net))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("before", type=Path)
    ap.add_argument("after", type=Path)
    ap.add_argument("--ignore", type=re.compile, default=None, help="regex on references to leave out of the comparison")
    a = ap.parse_args(argv)
    nets_a, parts_a = connectivity(a.before, a.ignore)
    nets_b, parts_b = connectivity(a.after, a.ignore)
    nodes_a = {n for net in nets_a for n in net}
    nodes_b = {n for net in nets_b for n in net}
    lost, gained = sorted(nets_a - nets_b, key=fmt), sorted(nets_b - nets_a, key=fmt)
    dangling, new_nodes = sorted(nodes_a - nodes_b), sorted(nodes_b - nodes_a)
    removed = sorted(set(parts_a) - set(parts_b)); added = sorted(set(parts_b) - set(parts_a))
    changed = sorted(r for r in set(parts_a) & set(parts_b) if parts_a[r] != parts_b[r])
    print(f"before: {len(nets_a)} nets, {len(nodes_a)} nodes, {len(parts_a)} parts; after: {len(nets_b)} nets, {len(nodes_b)} nodes, {len(parts_b)} parts")
    for title, items, f in (("nets lost", lost, fmt), ("nets gained", gained, fmt),
                            ("nodes dangling after", dangling, lambda n: f"{n[0]}.{n[1]}"),
                            ("nodes new after", new_nodes, lambda n: f"{n[0]}.{n[1]}"),
                            ("parts removed", removed, lambda r: f"{r} ({parts_a[r]})"),
                            ("parts added", added, lambda r: f"{r} ({parts_b[r]})"),
                            ("parts re-symbolled", changed, lambda r: f"{r}: {parts_a[r]} -> {parts_b[r]}")):
        if items:
            print(f"== {title} ({len(items)})")
            for it in items:
                print("  " + f(it))
    same = not (lost or gained or dangling or new_nodes or removed or added)
    print("connectivity identical" if same else "connectivity differs")
    return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main())
