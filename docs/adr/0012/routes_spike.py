"""Spike: can routes be found from the Layout Data Model File alone? Reads one file, reports routes and gaps.

Functional model used: switches have legs C, N, R; a joint separates two circuits and may touch switch legs on
either side; a link joins legs inside one circuit; a plain circuit (no switch) joins the joints that name it; a signal
joint governs movement from its B side into its A side; ends terminate the graph.
A route: from a signal joint, enter A; at a switch entered by C choose N or R, entered by N or R leave by C; stop at the first signal
joint that governs the same direction (reached from its B side), or at an end; opposing signals are passed.

Evidence for ADR 0012 §5.3 and §9, kept beside it (a throwaway, not a library). Run on 2026-10-26 against the KiCad
importer's output for the SPCoast netlist of Railroad 96c6b4e:

    uv run python docs/adr/0012/routes_spike.py SPCoast.layout.json
"""
import json
import sys
from collections import defaultdict

m = json.load(open(sys.argv[1]))
GAPS = defaultdict(list)

for ix, I in m["interlockings"].items():
    track = I.get("track", {})
    switches = {f"{ix}:{k}": v for k, v in I.get("appliances", {}).items() if v.get("appliance") == "switch"}
    # nodes: ("leg", "ix:sw", "C"), ("joint", i, side), ("end", i)
    adj = defaultdict(set)       # leg -> the places it touches
    circuit_places = defaultdict(set)
    joints = track.get("joints", [])
    for i, j in enumerate(joints):
        for side in ("A", "B"):
            c = j.get("circuits", {}).get(side)
            legs = j.get("ports", {}).get(side, [])
            for leg in legs:
                adj[leg].add(("joint", i, side))
                adj[("joint", i, side)].add(leg)
            if c and not legs:
                circuit_places[c].add(("joint", i, side))
        if j["kind"] == "IRJ_SIGNAL" and not j.get("mast"):
            GAPS[ix].append(f"signal joint {j['circuits']} has no mast")
    for k, e in enumerate(track.get("ends", [])):
        for c in e.get("circuits", {}).values():
            circuit_places[c].add(("end", k, None))
        for legs in e.get("ports", {}).values():
            for leg in legs:
                adj[leg].add(("end", k, None))
    for link in track.get("links", []):
        a, b = link["ports"][:2]
        adj[a].add(b); adj[b].add(a)
    # a plain circuit joins every place that names it, if there are exactly two
    for c, places in circuit_places.items():
        if len(places) == 2:
            p, q = sorted(places, key=str)
            adj[p].add(q); adj[q].add(p)
        elif len(places) > 2:
            GAPS[ix].append(f"plain circuit {c} has {len(places)} boundaries; adjacency is ambiguous")
    for sw in switches:
        for leg in "CNR":
            if not adj.get(f"{sw}.{leg}"):
                GAPS[ix].append(f"switch leg {sw}.{leg} touches nothing")

    def other_side(node):
        kind, i, side = node
        return ("joint", i, "B" if side == "A" else "A")

    routes = []

    def walk(node, path, aligns, entry):
        # node: a place we have just arrived at, moving away from `path[-1]`
        if node[0] == "end":
            e = track["ends"][node[1]]
            routes.append((entry, f"end {e['kind']} {e.get('interlocking') or e.get('name') or ''}".strip(), aligns))
            return
        if node[0] == "joint":
            j = joints[node[1]]
            if j["kind"] == "IRJ_SIGNAL" and node[2] == "B":
                routes.append((entry, f"next {j.get('mast')}", aligns))
                return
            nxt = other_side(node)
            for n in adj[nxt] - {node}:
                walk_into(n, path + [nxt], aligns, entry)
            if not adj[nxt]:
                GAPS[ix].append(f"route from {entry} stops at joint {j['circuits']} side {nxt[2]}: nothing beyond")
            return
        raise AssertionError(node)

    def walk_into(n, path, aligns, entry):
        if isinstance(n, str):  # a switch leg: leave by the other legs
            sw, leg = n.rsplit(".", 1)
            outs = [("N", "N"), ("R", "R")] if leg == "C" else [("C", leg)]
            for out, pos in outs:
                if len(path) > 60:
                    GAPS[ix].append(f"route from {entry} loops"); return
                a = dict(aligns)
                if sw in a and a[sw] != pos:
                    continue
                a[sw] = pos
                for nn in adj[f"{sw}.{out}"] - set(path):
                    if isinstance(nn, str):
                        walk_into(nn, path + [n], a, entry)
                    else:
                        walk(nn, path + [n], a, entry)
        else:
            walk(n, path, aligns, entry)

    for i, j in enumerate(joints):
        if j["kind"] == "IRJ_SIGNAL":
            start = ("joint", i, "B")
            entry = j.get("mast")
            for n in adj[("joint", i, "A")]:
                walk_into(n, [start, ("joint", i, "A")], {}, entry)
            if not adj[("joint", i, "A")]:
                GAPS[ix].append(f"signal {entry}: nothing on its A side")

    print(f"== {ix}: {len(switches)} switches, {sum(1 for j in joints if j['kind']=='IRJ_SIGNAL')} signal joints, {len(routes)} routes")
    for entry, exit_, aligns in sorted(routes, key=str):
        print(f"   {entry} -> {exit_}  [{', '.join(f'{k.split(':')[1]}{v}' for k, v in sorted(aligns.items()))}]")
    for g in sorted(set(GAPS[ix])):
        print(f"   GAP {g}")
