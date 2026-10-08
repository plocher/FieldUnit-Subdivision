#!/usr/bin/env python3
"""Pass 2: desk and plant libraries to ADR 0003.

RailroadPanel: Role APPLIANCE -> PANEL on every operator-interface symbol (D8); every
BIT pin asserted-low (~{X}, D6: levers ground the selected contact against a pull-up,
lamps sink) with a blank polarity attribute per pin; PanelLock reconciled to WLS/WLK
(O3, owner 2026-10-07): same four pins and positions, N contact WLS, R contact ~{WLS},
R lamp ~{WLK} (unlocked), N lamp WLK (locked, the complement).
Railroad: the powered-switch variants take Kind SWITCH_REMOTE (D3).

Usage: python3 pass2_desk_plant_library.py [--dry-run]
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from symlib_edit import add_prop, edit_pin, get_prop, join, pin_names, set_prop, split  # noqa: E402

LIBDIR = Path.home() / "Dropbox/KiCad/InterlockingPlant/symbols"
PANEL = LIBDIR / "RailroadPanel.kicad_sym"
PLANT = LIBDIR / "Railroad.kicad_sym"

PANEL_SYMBOLS = {"PanelSwitch", "PanelLock", "PanelSignal", "PanelMCall", "PanelCode", "PanelAuxiliary",
                 "PanelLamp-AMBER", "PanelLamp-BLUE", "PanelLamp-GREEN", "PanelLamp-RED", "PanelLamp-YELLOW"}
LOCK_PINS = {"2": "WLS", "3": "~{WLS}", "4": "~{WLK}", "5": "WLK"}
REMOTE = {"Switch_Powered", "Switch_Powered_Diag", "Switch_Powered_NO_TC", "Switch_Powered_Small"}


def pin_numbers(b):
    return re.findall(r'\(pin \w+ \w+\n[\s\S]*?\(number "([^"]+)"', b)


def panel_pass(name, b):
    assert get_prop(b, "Role") == "APPLIANCE", name
    b = set_prop(b, "Role", "PANEL")
    for num, pname in zip(pin_numbers(b), pin_names(b)):
        if pname == "Column":
            continue
        if name == "PanelLock":
            b = edit_pin(b, num, name=LOCK_PINS[num])
        else:
            assert not pname.startswith("~{"), (name, pname)
            b = edit_pin(b, num, name="~{" + pname + "}")
    for base in dict.fromkeys(re.sub(r"^~\{(.*)\}$", r"\1", p) for p in pin_names(b) if p != "Column"):
        b = add_prop(b, base, "")
    return b


def main(dry):
    head, blocks, tail = split(PANEL.read_text())
    assert PANEL_SYMBOLS <= {n for n, _ in blocks}
    blocks = [(n, panel_pass(n, b) if n in PANEL_SYMBOLS else b) for n, b in blocks]
    for n, b in blocks:
        if n in PANEL_SYMBOLS:
            print(f"{n:18} Role={get_prop(b, 'Role')} pins={pin_names(b)}")
    panel_text = join(head, blocks, tail)

    head, pblocks, tail = split(PLANT.read_text())
    out = []
    for n, b in pblocks:
        if n in REMOTE and get_prop(b, "Kind") != "SWITCH_REMOTE":
            print(f"{n:22} Kind {get_prop(b, 'Kind')} -> SWITCH_REMOTE")
            b = set_prop(b, "Kind", "SWITCH_REMOTE")
        out.append((n, b))
    plant_text = join(head, out, tail)
    if not dry:
        PANEL.write_text(panel_text)
        PLANT.write_text(plant_text)
        print("wrote", PANEL, PLANT)


if __name__ == "__main__" and "--drivers" not in sys.argv:
    main("--dry-run" in sys.argv)


# Owner, 2026-10-07: a driver symbol has no direction or polarity of its own; each pin takes
# them from what is wired to it (an active-low input consumer means the pull-up is enabled).
def driver_pass(b):
    for num in pin_numbers(b):
        b = edit_pin(b, num, etype="bidirectional")
    return b


def drivers_main():
    from symlib_edit import del_prop
    head, blocks, tail = split(PANEL.read_text())
    PANEL.write_text(join(head, [(n, driver_pass(b) if n == "PanelColumn-MAX7313" else b) for n, b in blocks], tail))
    field = LIBDIR / "RailroadField.kicad_sym"
    head, blocks, tail = split(field.read_text())
    field.write_text(join(head, [(n, del_prop(b, "Pullups")) for n, b in blocks], tail))
    print("MAX7313 pins bidirectional; Pullups removed from the field library")


if __name__ == "__main__" and "--drivers" in sys.argv:
    drivers_main()
