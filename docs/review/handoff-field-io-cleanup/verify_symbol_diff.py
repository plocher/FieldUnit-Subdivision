#!/usr/bin/env python3
"""Per-symbol before/after comparison of KiCad schematics against git HEAD.

Usage (from the repo that holds the schematics):
    python3 verify_symbol_diff.py [path/to/file.kicad_sch ...]
With no arguments, every modified .kicad_sch in `git diff --name-only` is checked.

For each placed symbol (keyed by its uuid) it reports: added/removed symbols,
lib_id or position changes, and every property whose value changed. Use it to
confirm that a scripted pass changed only what it was meant to change.
"""
import re
import subprocess
import sys


def placed(text):
    start = text.index("(lib_symbols")
    depth, j = 0, start
    while True:
        depth += (text[j] == "(") - (text[j] == ")")
        j += 1
        if depth == 0:
            break
    tail = text[j:]
    out = {}
    for m in re.finditer(r'\n\t\(symbol\n\t\t\(lib_id "([^"]+)"\)', tail):
        i = m.start() + 2
        depth, k = 0, i
        while True:
            depth += (tail[k] == "(") - (tail[k] == ")")
            k += 1
            if depth == 0:
                break
        block = tail[i:k]
        uuid = re.search(r'\n\t\t\(uuid "([^"]+)"', block).group(1)
        props = dict(re.findall(r'\(property "([^"]+)" "([^"]*)"', block))
        at = re.search(r"\(at [^)]*\)", block).group(0)
        out[uuid] = (m.group(1), props, at)
    return out


def main(files):
    if not files:
        files = [f for f in subprocess.check_output(["git", "diff", "--name-only"], text=True).split()
                 if f.endswith(".kicad_sch")]
    for f in files:
        old = placed(subprocess.check_output(["git", "show", "HEAD:" + f], text=True))
        new = placed(open(f).read())
        print(f"== {f}: {len(old)} -> {len(new)} symbols")
        for u in sorted(set(old) - set(new), key=lambda x: old[x][1].get("Reference", "")):
            print("   removed", old[u][0], old[u][1].get("Reference"), repr(old[u][1].get("Value")))
        for u in sorted(set(new) - set(old), key=lambda x: new[x][1].get("Reference", "")):
            print("   added  ", new[u][0], new[u][1].get("Reference"), repr(new[u][1].get("Value")))
        for u in set(old) & set(new):
            lo, po, ao = old[u]
            ln, pn, an = new[u]
            ref = po.get("Reference")
            if lo != ln:
                print("   lib_id ", ref, lo, "->", ln)
            if ao != an:
                print("   moved  ", ref, lo.split(":")[-1])
            for k in sorted(set(po) | set(pn)):
                if k == "Description":
                    continue
                if po.get(k) != pn.get(k):
                    print("   changed", lo.split(":")[-1], ref, k, repr(po.get(k)), "->", repr(pn.get(k)))


if __name__ == "__main__":
    main(sys.argv[1:])
