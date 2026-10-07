#!/usr/bin/env python3
"""Pass 2b: the owner's review of passes 1 and 2 (2026-10-07).

- Driver symbols: Kind I2C-<chip>, pins A1..A8, B1..B8 (pin N is chip bit N-1).
  PanelColumn-MAX7313 -> Driver-I2C-MAX7313.
- Device-Head-3LED-Mux2: S0, S1 plain (every select code is a meaningful state; no assertion).
- Heads, not lamps: a head device needs indication-to-aspect logic, a lamp does not.
  Device-Head-1LED-NeoPixel and Device-Head-1LED-PWM restored from the pre-pass library
  (Device-Signal-1LED_NEO, -1LED_PWM); Device-Lamp-NeoPixel stays as the lamp.
- Head symbols say HEAD, not SIG.
- PanelLock: Kind LOCK_LEVER_2LAMP_2CONTACT (two contacts and two lamps on one token pair), a
  sibling of the fascia's LOCK_LEVER and LOCK_LEVER_2LAMP.

Usage: python3 pass2b_owner_review.py
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from pass1_field_library import make  # noqa: E402
from symlib_edit import del_prop, edit_pin, join, pin_names, rename, set_prop, set_text, split  # noqa: E402

LIBDIR = Path.home() / "Dropbox/KiCad/InterlockingPlant/symbols"
FIELD = LIBDIR / "RailroadField.kicad_sym"
PANEL = LIBDIR / "RailroadPanel.kicad_sym"
PRE_PASS = "1eed088"


def ab_pins(b):
    names = [f"A{i}" for i in range(1, 9)] + [f"B{i}" for i in range(1, 9)]
    for i, n in enumerate(names, start=1):
        b = edit_pin(b, str(i), name=n)
    return b


def main():
    head, blocks, tail = split(FIELD.read_text())
    old = dict(split(subprocess.check_output(
        ["git", "-C", str(LIBDIR), "show", f"{PRE_PASS}:symbols/RailroadField.kicad_sym"], text=True))[1])
    out = []
    for n, b in blocks:
        if n == "Driver-I2C-MCP23017":
            b = set_prop(b, "Kind", "I2C-MCP23017")
        elif n == "Driver-I2C-PCA9685":
            b = set_prop(b, "Kind", "I2C-PCA9685")
        elif n == "Device-Head-3LED-Mux2":
            b = edit_pin(edit_pin(b, "1", name="S0"), "2", name="S1")
            b = del_prop(del_prop(b, "S0"), "S1")
        if n.startswith("Device-Head-"):
            b = set_text(b, "SIG ${VALUE}", "HEAD ${VALUE}")
        out.append((n, b))
    out.append(("Device-Head-1LED-NeoPixel",
                make(old["Device-Signal-1LED_NEO"], "Device-Signal-1LED_NEO", "Device-Head-1LED-NeoPixel", "DEVICE",
                     "HEAD_1LED_NEOPIXEL", attrs=[("Chain", ""), ("Index", "")])))
    out.append(("Device-Head-1LED-PWM",
                make(old["Device-Signal-1LED_PWM"], "Device-Signal-1LED_PWM", "Device-Head-1LED-PWM", "DEVICE",
                     "HEAD_1LED_PWM", pins=[("1", "D")], text=("SIG ${VALUE}", "HEAD ${VALUE}"))))
    out.sort(key=lambda nb: nb[0])
    FIELD.write_text(join(head, out, tail))

    head, blocks, tail = split(PANEL.read_text())
    out = []
    for n, b in blocks:
        if n == "PanelColumn-MAX7313":
            n, b = "Driver-I2C-MAX7313", ab_pins(rename(b, n, "Driver-I2C-MAX7313"))
        elif n == "PanelLock":
            b = set_prop(b, "Kind", "LOCK_LEVER_2LAMP_2CONTACT")
        out.append((n, b))
    out.sort(key=lambda nb: nb[0])
    PANEL.write_text(join(head, out, tail))
    for lib in (FIELD, PANEL):
        for n, b in split(lib.read_text())[1]:
            if n.startswith(("Driver-", "Device-Head-", "PanelLock")):
                kind = __import__("re").search(r'"Kind" "([^"]*)"', b).group(1)
                print(f"{n:28} {kind:26} {pin_names(b)}")


if __name__ == "__main__":
    main()
