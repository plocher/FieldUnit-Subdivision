#!/usr/bin/env python3
"""Pass 2c: one fascia lock plate per ADR 0004 (owner, 2026-10-07).

Local-Lock-2Lamp becomes Local-Lock (Kind LOCK_LEVER): ~{WLQ} the crew's key or lever (the
request), ~{WLK} the R lamp (unlocked), WLK the N lamp (locked; blinks while the request waits,
in the Kind's logic). The one-lamp Local-Lock is deleted.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from symlib_edit import add_prop, del_prop, edit_pin, join, pin_names, rename, set_prop, split  # noqa: E402

FIELD = Path.home() / "Dropbox/KiCad/InterlockingPlant/symbols/RailroadField.kicad_sym"
if "--lamps" not in sys.argv:
    head, blocks, tail = split(FIELD.read_text())
    out = []
    for n, b in blocks:
        if n == "Local-Lock":
            continue
        if n == "Local-Lock-2Lamp":
            n = "Local-Lock"
            b = rename(b, "Local-Lock-2Lamp", n)
            b = set_prop(b, "Kind", "LOCK_LEVER")
            b = edit_pin(b, "1", name="~{WLQ}")
            b = add_prop(del_prop(b, "WLS"), "WLQ", "")
            print(n, pin_names(b))
        out.append((n, b))
    out.sort(key=lambda nb: nb[0])
    FIELD.write_text(join(head, out, tail))


# Owner, 2026-10-07: the two lamps are two concepts, not complements. Amber is the request
# lamp (~{WLQK}: blinks while the request waits, steady once WLK); green is the lock (WLK down).
def lamps_are_two_concepts():
    head, blocks, tail = split(FIELD.read_text())
    out = []
    for n, b in blocks:
        if n == "Local-Lock":
            b = edit_pin(b, "2", name="~{WLQK}")
            b = add_prop(b, "WLQK", "")
            print(n, pin_names(b))
        out.append((n, b))
    FIELD.write_text(join(head, out, tail))


if "--lamps" in sys.argv:
    lamps_are_two_concepts()
