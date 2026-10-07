#!/usr/bin/env python3
"""Pass 3: the Sargent sandbox to the ADR 0003/0004 libraries.

Rewrites lib_ids (instances and the embedded definition, taken from the library), refreshes
instance Role/Kind from the library, drops the retired Polarity field. Refuses a mapping whose
old and new symbols differ in pin numbers or positions (wires would come loose).

Usage: python3 pass3_sargent.py [--dry-run]
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from refresh_embedded import embedded_form  # noqa: E402
from symlib_edit import end_of, split  # noqa: E402

LIBDIR = Path.home() / "Dropbox/KiCad/InterlockingPlant/symbols"
SHEET = Path.home() / "Dropbox/KiCad/Railroad/Archive/SPCoast/Sargent/Sargent.kicad_sch"
MAP = {
    "RailroadField:Device-I2C-IOx4": "RailroadField:Driver-I2C-MCP23017",
    "RailroadField:Device-I2C-PWMx4": "RailroadField:Driver-I2C-PCA9685",
    "RailroadField:Device-TrackCircuit": "RailroadField:Device-Detector-Optical",
    "RailroadField:Device-Digital_Output": "RailroadField:Device-Lamp-Bit",
    "RailroadField:Device-Signal-1LED_NEO": "RailroadField:Device-Lamp-NeoPixel",
    "RailroadField:Device-Signal-3LED_2MUX": "RailroadField:Device-Head-3LED-Mux2",
    "RailroadField:Device-Signal-3LED_PWM": "RailroadField:Device-Head-3LED-PWM",
    "RailroadField:Device-Signal-Semaphore_2PWM": "RailroadField:Device-Head-Semaphore-Servo",
    "RailroadField:Device-Switch-HandThrow": "RailroadField:Device-Switch-Sense",
    "Railroad:Switch_HandThrow": "Railroad:Switch_Manual_Sensed",
}
LIBS = {n: dict(split((LIBDIR / f"{n}.kicad_sym").read_text())[1]) for n in ("Railroad", "RailroadField")}


def pins(block):
    """{number: (x, y, unit)} for every pin in a symbol definition."""
    out = {}
    for u in re.finditer(r'\(symbol "[^"]*_(\d+)_\d+"', block):
        ub = block[u.start():end_of(block, u.start())]
        for p in re.finditer(r'\(pin \w+ \w+\s*\(at ([-\d.]+) ([-\d.]+)[^)]*\)[\s\S]*?\(number "([^"]+)"', ub):
            out[p.group(3)] = (float(p.group(1)), float(p.group(2)), u.group(1))
    return out


def embedded_block(t, lib_id):
    m = re.search(r'\n\t\t\(symbol "' + re.escape(lib_id) + r'"\n', t)
    if not m:
        return None
    s = m.start() + 3
    return s, end_of(t, s)


def main(dry):
    t = SHEET.read_text()
    ok = True
    for old, new in MAP.items():
        span = embedded_block(t, old)
        if span is None:
            print(f"  (not on sheet) {old}")
            continue
        lib, name = new.split(":")
        nb = LIBS[lib][name]
        po, pn = pins(t[span[0]:span[1]]), pins(nb)
        if po != pn:
            ok = False
            print(f"  ! pin mismatch {old} -> {new}: {po} vs {pn}")
            continue
        t = t[:span[0]] + embedded_form(lib, name, nb) + t[span[1]:]
        n = t.count(f'(lib_id "{old}")')
        t = t.replace(f'(lib_id "{old}")', f'(lib_id "{new}")')
        print(f"  {old} -> {new}: {n} instance(s), pins match")
    if not ok:
        print("NOT WRITTEN")
        return
    # instance Role/Kind from the library; Polarity retired
    out, pos = [], 0
    for m in re.finditer(r'\n\t\(symbol\n\t\t\(lib_id "(Railroad(?:Field)?):([^"]+)"\)', t):
        s = m.start() + 2
        e = end_of(t, s)
        b = t[s:e]
        L = LIBS[m.group(1)].get(m.group(2))
        if L:
            for k in ("Role", "Kind"):
                lv = re.search(r'\(property "' + k + r'" "([^"]*)"', L)
                iv = re.search(r'\(property "' + k + r'" "([^"]*)"', b)
                if lv and iv and lv.group(1) != iv.group(1):
                    print(f"  {m.group(2)}: {k} {iv.group(1)!r} -> {lv.group(1)!r}")
                    b = b[:iv.start(1)] + lv.group(1) + b[iv.end(1):]
        pm = re.search(r'\n\t\t\(property "Polarity" "', b)
        if pm:
            b = b[:pm.start()] + b[end_of(b, pm.start() + 3):]
            print(f"  {m.group(2)}: Polarity dropped")
        out += [t[pos:s], b]
        pos = e
    t = "".join(out) + t[pos:]
    if not dry:
        SHEET.write_text(t)
        print("wrote", SHEET)


if __name__ == "__main__":
    main("--dry-run" in sys.argv)
