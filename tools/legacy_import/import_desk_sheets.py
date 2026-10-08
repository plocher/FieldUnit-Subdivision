#!/usr/bin/env python3
"""Generate South-cTc interlocking sheets from the legacy SouthCTC.xml.

One-shot bootstrap: turns the historical ArduinoPoint desk definition into
drawn KiCad sheets so the compiler has more than one interlocking to chew
on. Everything it cannot derive is written as FIXME, on purpose.

The drawn Luchessa sheet is the template: symbol instances are deep-copied
from it, so field sets, property placement and effects stay authentic.
Placement uses the symbol pin geometry: an appliance dropped on its column
pin lands its function pins on the correct expander bits automatically.
"""
from __future__ import annotations

import copy
import re
import sys
import uuid as uuidmod
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import kicad_sexpr as S  # noqa: E402

DESK = Path.home() / "Dropbox/KiCad/Railroad/Archive/SPCoast/South-cTc"
LEGACY = Path.home() / "Dropbox/workspace/ArduinoPoint/definitions"
PANEL_LIB = Path.home() / "Dropbox/KiCad/InterlockingPlant/symbols/RailroadPanel.kicad_sym"
TEMPLATE_SHEET = DESK / "Luchessa.kicad_sch"
ROOT_SHEET = DESK / "South-cTc.kicad_sch"

# --- geometry (mm), read off the drawn Luchessa sheet and its symbols
COLUMN_Y = 97.79
COLUMN_X0 = 80.01
COLUMN_DX = 50.80
DRIVER_DX = 19.05
DRIVER_Y = 72.39
CODELINE_AT = (139.70, 193.04)
# PanelColumn pin -> library y
COL_PIN_Y = {1: 71.12, 2: 66.04, 3: 60.96, 4: 49.53, 5: 33.02, 6: 12.70, 7: 0.0, 8: -6.35}
# appliance lib_id -> (its Column pin library y, the column pin it sits on)
LEVER_COL_PIN_Y = -1.27  # PanelSwitch / PanelLock / PanelSignal
FLAT_COL_PIN_Y = 0.0  # lamps, MCall, Code, Auxiliary

# legacy expander index -> I2C address: column N uses 0x20 + N - 1 (IO-I2C.h colToDev)
def driver_address(column: int) -> str:
    return f"0x{0x20 + column - 1:02X}"


def symbol_pins(name: str) -> dict[str, tuple[float, float]]:
    """pin name -> (x, y) in library coordinates, for one panel symbol."""
    lib = S.parse(PANEL_LIB.read_text())
    sym = next(s for s in S.findall(lib, "symbol") if S.val(s[1]) == name)
    out = {}
    for unit in S.findall(sym, "symbol"):
        for pin in S.findall(unit, "pin"):
            at = S.find(pin, "at")
            out[S.val(S.find(pin, "name")[1])] = (float(at[1]), float(at[2]))
    return out


def appliance_y(column_pin: int, own_pin_y: float) -> float:
    return round(COLUMN_Y - COL_PIN_Y[column_pin] + own_pin_y, 2)


# --- interlocking name mapping: legacy XML name -> KiCad sheet name
SHEET_OF = {
    "GCaltrain": "Gilroy CalTrain",
    "GInterchange": "Gilroy Interchange",
    "CP_Luchessa": "Luchessa",
    "CP_Christopher": "Christopher",
    "CP_Corporal": "Corporal",
    "CP_Sargent": "Sargent",
    "CP_Watsonville": "Watsonville",
}
# legacy plant file per interlocking (for track-circuit vocabulary)
PLANT_XML = {
    "GCaltrain": "GCaltrain.xml",
    "GInterchange": "GInterchange.xml",
    "CP_Christopher": "CP_Christopher.xml",
    "CP_Corporal": "CP_Corporal.xml",
    "CP_Sargent": "CP_Sargent.xml",
    "CP_Watsonville": "CP_Watsonville.xml",
}
SKIP = {"CP_Luchessa"}  # drawn by hand; never overwrite

COLOR_SYMBOL = {"red": "PanelLamp-RED", "amber": "PanelLamp-YELLOW",
                "yellow": "PanelLamp-YELLOW", "blue": "PanelLamp-BLUE"}
COLOR_VALUE = {"red": "red", "amber": "yellow", "yellow": "yellow", "blue": "blue"}


def new_uuid() -> str:
    return str(uuidmod.uuid4())


# ---------------------------------------------------------------- legacy input
def read_desk():
    """Return [(legacy_name, [column dicts])] from SouthCTC.xml."""
    root = ET.parse(LEGACY / "SouthCTC.xml").getroot()
    out = []
    for cp in root.iter("controlpoint"):
        cols = cp.findall("column")
        if not cols:
            continue
        entries = []
        for col in cols:
            if col.find("custom") is not None:
                continue  # column 15: custom yard code, not a lever column
            entries.append({
                "number": int(col.get("name")),
                "lamps": [(int(m.get("position")), m.get("color"), m.get("name"))
                          for m in col.findall("model")],
                "switch": next(((s.get("name"), s.get("label")) for s in col.findall("switch")), None),
                "lock": next(((s.get("name"), s.get("label")) for s in col.findall("lock")), None),
                "signal": next(((s.get("name"), s.get("label")) for s in col.findall("signal")), None),
                "call": next((c.get("name") for c in col.findall("call")), None),
                "code": col.find("code") is not None,
            })
        if entries:
            out.append((cp.get("name"), entries))
    return out


def read_circuits(legacy_name: str) -> set[str]:
    """Legacy track-circuit vocabulary of one interlocking."""
    fname = PLANT_XML.get(legacy_name)
    if not fname or not (LEGACY / fname).exists():
        return set()
    root = ET.parse(LEGACY / fname).getroot()
    tcs = root.find("trackcircuits")
    return {t.get("name") for t in tcs} if tcs is not None else set()


def lever_labels(columns) -> dict[str, str]:
    """local switch/lock index -> AAR label, e.g. '1' -> '783'."""
    out = {}
    for col in columns:
        for key in ("switch", "lock"):
            if col[key]:
                out[col[key][0].lstrip(":")] = col[key][1]
    return out


def resolve_token(raw: str, labels: dict[str, str], circuits: set[str]) -> tuple[str, str]:
    """Return (token, lamp label). FIXME-prefixed when not derivable."""
    if ":" in raw and not raw.startswith(":"):
        return f"FIXME {raw}", "TRACK"  # another interlocking's indication
    local = raw.lstrip(":")
    m = re.fullmatch(r"(\d+B?)T1", local)
    if m:
        base = m.group(1)
        if base in labels:
            return f"{labels[base]}T1", "OS"
        return f"FIXME {local}", "OS"
    if local in circuits:
        return local, "HBD" if local == "HBD" else "TRACK"
    return f"FIXME {local}", "TRAFFIC" if local in ("TL", "TR") else "TRACK"


# ------------------------------------------------------------------- templates
class Templates:
    def __init__(self):
        sheet = S.parse(TEMPLATE_SHEET.read_text())
        self.header = [c for c in sheet if isinstance(c, list)
                       and S.val(c[0]) in ("version", "generator", "generator_version", "paper")]
        self.lib_symbols = S.find(sheet, "lib_symbols")
        self.by_lib_id: dict[str, list] = {}
        for sym in S.findall(sheet, "symbol"):
            lid = S.find(sym, "lib_id")
            if lid:
                self.by_lib_id.setdefault(S.val(lid[1]), sym)
        self.contract = self._library_contract()
        self._add_blue_lamp()

    @staticmethod
    def _library_contract() -> dict[str, dict[str, str]]:
        """Role/Kind as the library fixes them, keyed by symbol name.

        Never inherited from a placed instance: KiCad keeps a symbol's old
        field values when you swap its symbol, so the drawn Luchessa sheet
        carries Kind=SWITCH_LEVER on a PanelLock.
        """
        lib = S.parse(PANEL_LIB.read_text())
        out = {}
        for sym in S.findall(lib, "symbol"):
            name = S.val(sym[1])
            out[name] = {k: v for k in ("Role", "Kind")
                         if (v := S.prop(sym, k)) is not None}
        return out

    def _add_blue_lamp(self):
        """PanelLamp-BLUE is not on the Luchessa sheet: cache it from the library."""
        want = "RailroadPanel:PanelLamp-BLUE"
        if any(S.val(s[1]) == want for s in S.findall(self.lib_symbols, "symbol")):
            return
        lib = S.parse(PANEL_LIB.read_text())
        src = next(s for s in S.findall(lib, "symbol") if S.val(s[1]) == "PanelLamp-BLUE")
        entry = copy.deepcopy(src)
        # Two traps, either of which makes KiCad reject the whole symbol table
        # and then silently drop every symbol on the sheet:
        #  - only the outer name carries the library nickname; inner unit
        #    names (PanelLamp-BLUE_1_1) stay bare, as KiCad caches them;
        #  - the table is ordered by name, so the entry is inserted, never
        #    appended.
        entry[1] = '"' + want
        at = len(self.lib_symbols)
        for i, sym in enumerate(self.lib_symbols):
            if isinstance(sym, list) and S.val(sym[0]) == "symbol" and S.val(sym[1]) > want:
                at = i
                break
        self.lib_symbols.insert(at, entry)

    def instance(self, lib_id: str, at: tuple[float, float], fields: dict[str, str],
                 path: str, fallback: str | None = None) -> list:
        src = self.by_lib_id.get(lib_id) or self.by_lib_id[fallback]
        node = copy.deepcopy(src)
        fields = dict(fields, **self.contract.get(lib_id.split(":", 1)[1], {}))
        S.find(node, "lib_id")[1] = '"' + lib_id
        old = S.find(node, "at")
        dx, dy = at[0] - float(old[1]), at[1] - float(old[2])
        old[1], old[2] = f"{at[0]:.2f}", f"{at[1]:.2f}"
        S.find(node, "uuid")[1] = '"' + new_uuid()
        for prop in S.findall(node, "property"):
            pat = S.find(prop, "at")
            if pat:  # property positions are absolute
                pat[1] = f"{float(pat[1]) + dx:.3f}"
                pat[2] = f"{float(pat[2]) + dy:.3f}"
            name = S.val(prop[1])
            if name in fields:
                prop[2] = '"' + fields[name]
        for pin in S.findall(node, "pin"):
            S.find(pin, "uuid")[1] = '"' + new_uuid()
        inst = S.find(node, "instances")
        pnode = S.find(S.find(inst, "project"), "path")
        pnode[1] = '"' + path
        S.find(pnode, "reference")[1] = '"' + fields["Reference"]
        return node


# -------------------------------------------------------------------- emission
def build_sheet(legacy_name: str, columns, tpl: Templates, path: str) -> list:
    labels = lever_labels(columns)
    circuits = read_circuits(legacy_name)
    sheet_name = SHEET_OF[legacy_name]
    symbols = []
    placed: list[list[tuple[str, float]]] = [[] for _ in columns]

    def add(lib_id, pin, own_y, fields, fallback=None):
        x = COLUMN_X0 + COLUMN_DX * idx
        y = appliance_y(pin, own_y)
        placed[idx].append((lib_id, y))
        symbols.append(tpl.instance(f"RailroadPanel:{lib_id}",
                                    (x, y), fields, path, fallback))

    for idx, col in enumerate(columns):
        n = col["number"]
        x = COLUMN_X0 + COLUMN_DX * idx
        symbols.append(tpl.instance("RailroadPanel:PanelColumn", (x, COLUMN_Y), {
            "Reference": f"COL{20 + n}", "Value": str(n),
            "Interlocking": sheet_name, "Machine": "SPCoast South",
            "CP Name": "FIXME",
        }, path))
        symbols.append(tpl.instance("RailroadPanel:PanelColumn-MAX7313",
                                    (x + DRIVER_DX, DRIVER_Y), {
            "Reference": f"U{20 + n}", "Value": driver_address(n),
        }, path))
        for pos, color, raw in sorted(col["lamps"]):
            token, label = resolve_token(raw, labels, circuits)
            add(COLOR_SYMBOL[color], pos, FLAT_COL_PIN_Y, {
                "Reference": f"LMP{n}{pos}", "Value": label,
                "IndicationToken": token, "Color": COLOR_VALUE[color],
            }, fallback="RailroadPanel:PanelLamp-RED")
        if col["switch"]:
            add("PanelSwitch", 5, LEVER_COL_PIN_Y,
                {"Reference": f"SWL{n}", "Value": col["switch"][1]})
        if col["lock"]:
            add("PanelLock", 5, LEVER_COL_PIN_Y,
                {"Reference": f"LKL{n}", "Value": col["lock"][1]})
        if col["signal"]:
            add("PanelSignal", 6, LEVER_COL_PIN_Y,
                {"Reference": f"SGL{n}", "Value": col["signal"][1]})
        if col["call"]:
            mc = col["call"].lstrip(":")
            add("PanelMCall", 4, FLAT_COL_PIN_Y,
                {"Reference": f"MCL{n}", "Value": mc, "ControlToken": f"{mc}S"})
            add("PanelLamp-YELLOW", 8, FLAT_COL_PIN_Y, {
                "Reference": f"MCK{n}", "Value": "MC",
                "IndicationToken": f"{mc}K", "Color": "yellow",
            })
        if col["code"]:
            add("PanelCode", 7, FLAT_COL_PIN_Y, {"Reference": f"CDE{n}", "Value": "CODE"})

    symbols.append(tpl.instance("RailroadPanel:Codeline-MQTT", CODELINE_AT, {
        "Reference": f"CL{columns[0]['number']}",
    }, path))
    return symbols + no_connects(columns, placed)


def no_connects(columns, placed) -> list:
    """A no_connect on every expander bit no appliance lands on, as the drawn
    Luchessa sheet has. Doubles as the geometry self-check: every function pin
    must coincide with a bit pin."""
    bits = symbol_pins("PanelColumn-MAX7313")
    out = []
    for idx, col in enumerate(columns):
        base_x = COLUMN_X0 + COLUMN_DX * idx
        bit_at = {name: (round(base_x + DRIVER_DX + x, 2), round(DRIVER_Y - y, 2))
                  for name, (x, y) in bits.items()}
        used = set()
        for lib_name, ay in placed[idx]:
            for pin_name, (px, py) in symbol_pins(lib_name).items():
                if pin_name == "Column":
                    continue
                at = (round(base_x + px, 2), round(ay - py, 2))
                hit = [b for b, xy in bit_at.items() if xy == at]
                if not hit:
                    raise SystemExit(
                        f"geometry error: {lib_name} pin {pin_name} at {at} "
                        f"on column {col['number']} lands on no expander bit")
                used.add(hit[0])
        for name, xy in sorted(bit_at.items()):
            if name not in used:
                out.append(["no_connect", ["at", f"{xy[0]:.2f}", f"{xy[1]:.2f}"],
                            ["uuid", '"' + new_uuid()]])
    return out


RECIPE = """FIXME recipe for this generated sheet

Generated from the historical ArduinoPoint desk definition
(ArduinoPoint/definitions/SouthCTC.xml). It is scaffolding, not truth:
finish it to the same fidelity as the hand-drawn Luchessa sheet.

1. CP Name on every column is FIXME. One column IS one controlled point;
   give each the geographic name it has on the railroad (Luchessa's three
   columns are CP Luchessa, CP Gilroy, CP Carnadero). Nothing in the
   legacy sources records these.
2. IndicationToken values starting with FIXME could not be resolved:
   - FIXME <n>T1 : the OS circuit of a switch with no lever on this desk
     (a crossover slave, e.g. 3B); name it once the plant is drawn.
   - FIXME TL / TR : traffic lamps, not track circuits. Expect these to
     become PanelAuxiliary appliances or a new indication kind.
   - FIXME CP_Other:token : this lamp shows another interlocking's
     indication. The model resolves lamp tokens per interlocking today,
     so this needs a schema and compiler addition.
3. Lever kinds came from the legacy XML and are suggestions: it called
   Luchessa's 795 a switch when it is a lock. Check each against the plant.
4. Expander addresses are computed as 0x20 + column - 1, which is the
   legacy convention baked into the hand-written IO-I2C.h. Verify each
   against the built hardware; the model takes the address from here.
5. Lamp Values are descriptive labels only (OS, TRACK, MC, TRAFFIC) and
   nothing reads them. Rename freely.
"""


def emit(target: Path, symbols, tpl: Templates, keep_uuid: str, title_block) -> None:
    node = ["kicad_sch"]
    node.extend(copy.deepcopy(c) for c in tpl.header
                if S.val(c[0]) in ("version", "generator", "generator_version"))
    node.append(["uuid", '"' + keep_uuid])
    node.append(copy.deepcopy(next(c for c in tpl.header if S.val(c[0]) == "paper")))
    if title_block is not None:
        node.append(copy.deepcopy(title_block))
    node.append(tpl.lib_symbols)
    # A plain (text ...), not (text_box ...): a hand-built text_box makes
    # KiCad reject the sheet and silently drop every symbol on it.
    node.append(["text", '"' + RECIPE,
                 ["exclude_from_sim", "no"],
                 ["at", "20.32", "120.65", "0"],
                 ["effects", ["font", ["size", "1.27", "1.27"]],
                  ["justify", "left", "top"]],
                 ["uuid", '"' + new_uuid()]])
    node.extend(symbols)
    node.append(["embedded_fonts", "no"])
    target.write_text(S.dump(node) + "\n")


def main() -> int:
    root = S.parse(ROOT_SHEET.read_text())
    root_uuid = S.val(S.find(root, "uuid")[1])
    sheet_uuid, sheet_file = {}, {}
    for sh in S.findall(root, "sheet"):
        name = S.prop(sh, "Sheetname")
        sheet_uuid[name] = S.val(S.find(sh, "uuid")[1])
        sheet_file[name] = S.prop(sh, "Sheetfile")

    tpl = Templates()
    written = []
    for legacy_name, columns in read_desk():
        if legacy_name in SKIP:
            continue
        name = SHEET_OF[legacy_name]
        target = DESK / sheet_file[name]
        existing = S.parse(target.read_text())
        keep_uuid = S.val(S.find(existing, "uuid")[1])
        if S.findall(existing, "symbol"):
            print(f"  SKIP {target.name}: already has symbols", file=sys.stderr)
            continue
        path = f"/{root_uuid}/{sheet_uuid[name]}"
        symbols = build_sheet(legacy_name, columns, tpl, path)
        emit(target, symbols, tpl, keep_uuid, S.find(existing, "title_block"))
        written.append((target.name, len(columns), len(symbols)))
    for fname, ncol, nsym in written:
        print(f"  wrote {fname:28s} {ncol} column(s), {nsym} symbols")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
