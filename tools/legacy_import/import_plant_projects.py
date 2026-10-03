#!/usr/bin/env python3
"""Scaffold peer-of-Luchessa plant projects from the legacy ArduinoPoint XML.

One-shot bootstrap. It creates, for each interlocking the desk knows about, a
KiCad plant project holding the parts whose identity the legacy sources fix
beyond doubt:

  * one MAIN HOUSE per desk column (a column IS a controlled point),
  * every switch and lock, named with its AAR number from the desk lever,
    allocated to the controlled point whose column carries that lever,
  * every track circuit that is not a switch's derived OS circuit,
  * every maintainer call.

It deliberately does NOT invent the trackplan. Topology (IRJs, terminals,
direction-of-traffic markers), masts and heads are left to the designer,
because the legacy XML has no geometry and, as the ASCII art in those files
shows, its flat per-direction head list spans several masts. Each generated
sheet carries a FIXME recipe with the legacy diagram, the local-to-AAR map,
the signal inventory and the route list to check the compiler's derived
routes against.

The drawn Luchessa plant sheet is the template, so field sets and the cached
symbol table stay authentic.
"""
from __future__ import annotations

import copy
import json
import re
import sys
import uuid as uuidmod
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import kicad_sexpr as S  # noqa: E402

SPCOAST = Path.home() / "Dropbox/KiCad/Railroad/SPCoast"
LEGACY = Path.home() / "Dropbox/workspace/ArduinoPoint/definitions"
TEMPLATE_DIR = SPCOAST / "Luchessa"

# interlocking -> (project directory, legacy plant xml)
PROJECTS = {
    "GCaltrain": ("GilroyCalTrain", "GCaltrain.xml"),
    "GInterchange": ("GilroyInterchange", "GInterchange.xml"),
    "CP_Christopher": ("Christopher", "CP_Christopher.xml"),
    "CP_Corporal": ("Corporal", "CP_Corporal.xml"),
    "CP_Sargent": ("Sargent", "CP_Sargent.xml"),
    "CP_Watsonville": ("Watsonville", "CP_Watsonville.xml"),
}

# --- placement: tidy labelled rows on a 1.27 mm (50 mil) grid
GRID = 1.27
ROW_Y = {"house": 40.64, "switch": 66.04, "circuit": 91.44, "call": 116.84}
ROW_X0 = 38.10
ROW_DX = 25.40
ROW_WRAP = 8  # items per row before wrapping
ROW_DY = 12.70


def new_uuid() -> str:
    return str(uuidmod.uuid4())


# ---------------------------------------------------------------- legacy input
def desk_levers() -> dict[str, list[dict]]:
    """interlocking -> [{column, kind, local, label, calls}] from SouthCTC.xml."""
    root = ET.parse(LEGACY / "SouthCTC.xml").getroot()
    out: dict[str, list[dict]] = {}
    for cp in root.iter("controlpoint"):
        cols = cp.findall("column")
        if not cols:
            continue
        entries = []
        for col in cols:
            if col.find("custom") is not None:
                continue
            rec = {"column": int(col.get("name")), "kind": None,
                   "local": None, "label": None,
                   "calls": [c.get("name").lstrip(":") for c in col.findall("call")]}
            for tag, kind in (("switch", "SWITCH"), ("lock", "LOCK")):
                el = col.find(tag)
                if el is not None:
                    rec.update(kind=kind, local=el.get("name").lstrip(":"),
                               label=el.get("label"))
            entries.append(rec)
        if entries:
            out[cp.get("name")] = entries
    return out


def plant_facts(xml_name: str) -> dict:
    root = ET.parse(LEGACY / xml_name).getroot()
    doc = root.find("doc")
    switches = [{"local": s.get("name"), "tc": s.get("trackcircuit"),
                 "slaveto": s.get("slaveto")}
                for s in root.findall("switches/switch")]
    circuits = [t.get("name") for t in root.findall("trackcircuits/trackcircuit")]
    calls = [c.get("name") for c in root.findall("maintainers/call")]
    signals = []
    for sig in root.findall("signals/signal"):
        heads = []
        for h in sig.findall("head"):
            m = re.fullmatch(r"[HS](\d+)([NSEW])([A-E]+)", h.get("name") or "")
            heads.append({"name": h.get("name"), "direction": h.get("direction"),
                          "signal": m.group(1) if m else None,
                          "dir": m.group(2) if m else None,
                          "letters": m.group(3) if m else None,
                          "routes": [r.get("name") for r in h.findall("route")]})
        signals.append({"local": sig.get("name"), "heads": heads})
    return {"doc": (doc.text or "").rstrip() if doc is not None else "",
            "switches": switches, "circuits": circuits, "calls": calls,
            "signals": signals, "node": root.get("node")}


# ------------------------------------------------------------------- templates
class Templates:
    def __init__(self):
        sheet = S.parse((TEMPLATE_DIR / "Luchessa.kicad_sch").read_text())
        self.header = {S.val(c[0]): c for c in sheet if isinstance(c, list)}
        self.lib_symbols = S.find(sheet, "lib_symbols")
        self.by_lib_id: dict[str, list] = {}
        for sym in S.findall(sheet, "symbol"):
            self.by_lib_id.setdefault(S.val(S.find(sym, "lib_id")[1]), sym)
        self.text = next(c for c in sheet if isinstance(c, list) and S.val(c[0]) == "text")

    def instance(self, lib_id: str, at: tuple[float, float],
                 fields: dict[str, str], path: str, project: str) -> list:
        node = copy.deepcopy(self.by_lib_id[lib_id])
        old = S.find(node, "at")
        dx, dy = at[0] - float(old[1]), at[1] - float(old[2])
        old[1], old[2] = f"{at[0]:.2f}", f"{at[1]:.2f}"
        S.find(node, "uuid")[1] = '"' + new_uuid()
        for prop in S.findall(node, "property"):
            pat = S.find(prop, "at")
            if pat:
                pat[1] = f"{float(pat[1]) + dx:.2f}"
                pat[2] = f"{float(pat[2]) + dy:.2f}"
            name = S.val(prop[1])
            if name in fields:
                prop[2] = '"' + fields[name]
        for pin in S.findall(node, "pin"):
            S.find(pin, "uuid")[1] = '"' + new_uuid()
        inst = S.find(node, "instances")
        pr = S.find(inst, "project")
        pr[1] = '"' + project
        pnode = S.find(pr, "path")
        pnode[1] = '"' + path
        S.find(pnode, "reference")[1] = '"' + fields["Reference"]
        return node

    def note(self, text: str, at: tuple[float, float]) -> list:
        node = copy.deepcopy(self.text)
        node[1] = '"' + text
        a = S.find(node, "at")
        a[1], a[2] = f"{at[0]:.2f}", f"{at[1]:.2f}"
        S.find(node, "uuid")[1] = '"' + new_uuid()
        return node


# --------------------------------------------------------------------- content
def recipe(interlocking: str, project: str, facts: dict, levers: list[dict],
           houses: dict[int, str]) -> str:
    lines = [f"FIXME recipe for {project} (generated scaffolding, not truth)",
             "",
             "Generated from the historical ArduinoPoint definitions",
             f"(ArduinoPoint/definitions/{PROJECTS[interlocking][1]} and SouthCTC.xml).",
             "Finish it to the same fidelity as the hand-drawn Luchessa plant.",
             "",
             "WHAT IS HERE (identity is certain):",
             "  - one MAIN HOUSE per desk column; a column IS a controlled point",
             "  - switches and locks, AAR-named from the desk levers",
             "  - track circuits that are not a switch's derived OS circuit",
             "  - maintainer calls",
             "",
             "WHAT IS MISSING (you draw it):",
             "  - the trackplan: track nets, IRJs, IRJ-Signals, NextCP/Bumper",
             "    terminals, direction-of-traffic and rulebook markers",
             "  - masts and heads (see SIGNALS below)",
             "  - Milepost values",
             "",
             "1. Every MAIN HOUSE Value is a FIXME placeholder. Give each the",
             "   geographic name it has on the railroad; Luchessa's three are",
             "   CP Luchessa, CP Gilroy, CP Carnadero. Each switch's CP field",
             "   already points at the house of the column that levers it, so",
             "   renaming the house is enough.",
             "2. Track circuit CP fields are FIXME: the legacy sources do not",
             "   record which controlled point owns a circuit, and which lamp",
             "   shows it on the desk carries no CP meaning.",
             "",
             "LOCAL TO AAR NAME MAP (from the desk levers):"]
    for lev in levers:
        if lev["label"]:
            lines.append(f"   column {lev['column']:>2}  :{lev['local']:<3} = "
                         f"{lev['label']:<5} ({lev['kind'].lower()})  ->  "
                         f"{houses[lev['column']]}")
    slaves = [s for s in facts["switches"] if s["slaveto"]]
    if slaves:
        lines += ["", "SLAVED SWITCHES (no desk lever, so no AAR number yet):"]
        for s in slaves:
            lines.append(f"   :{s['local']} slaved to :{s['slaveto']}, "
                         f"circuit {s['tc']} -- named FIXME here")
        lines.append("   These are crossover partners: give each its own number,")
        lines.append("   the way Luchessa's dependent derail is 795D.")
    if facts["signals"]:
        lines += ["", "SIGNALS (draw these yourself):"]
        for sig in facts["signals"]:
            label = next((l["label"] for l in levers
                          if l.get("signal_local") == sig["local"]), None)
            lines.append(f"   signal :{sig['local']}"
                         + (f" = {label}" if label else " = FIXME (no desk lever found)"))
            groups: dict[tuple[str, str], set[str]] = {}
            for h in sig["heads"]:
                if h["letters"]:
                    groups.setdefault((h["signal"], h["dir"]), set()).update(h["letters"])
            for (s_no, d), letters in sorted(groups.items()):
                lines.append(f"      direction {d}: heads {''.join(sorted(letters))}")
        lines += [
            "   The head names encode signal, direction and head letter",
            "   (H<signal><dir><head>, S<signal><dir><heads>), but the flat",
            "   per-direction list above spans SEVERAL masts: the ASCII diagram",
            "   below shows the real grouping (Christopher draws 2Nab and 2Nc as",
            "   two masts). Group the heads into masts as the diagram shows, the",
            "   way Luchessa splits signal 784 into 784EAB and 784EC.",
            "   Mast Value is <signal><direction><heads>, e.g. 816NAB.",
            "   Direction letters here are the legacy N/S; Luchessa uses E/W.",
            "   Pick the convention that matches the railroad's geography.",
            "   NOTE: the library has Mast_Single, Mast_Double and Mast_Dwarf",
            "   only, so a three- or four-head mast needs a new symbol.",
        ]
    routes = [(sig["local"], h["name"], r)
              for sig in facts["signals"] for h in sig["heads"] for r in h["routes"]]
    if routes:
        lines += ["", f"LEGACY ROUTES ({len(routes)}) -- routes are DERIVED by the",
                  "compiler from the trackplan; use this list only to check that",
                  "what it derives matches what the railroad used to do:"]
        for local, head, rname in routes:
            lines.append(f"   :{local} {head:<7} {rname}")
    if facts["doc"]:
        lines += ["", "LEGACY DIAGRAM AND NOTES", ""]
        lines += ["   " + ln for ln in facts["doc"].splitlines()]
    return "\n".join(lines)


def build(interlocking: str, project: str, facts: dict, levers: list[dict],
          tpl: Templates, path: str) -> list:
    def place(lib_id, at, fields):
        return tpl.instance(lib_id, at, fields, path, project)

    symbols: list = []
    houses = {lev["column"]: f"FIXME CP {i + 1}" for i, lev in enumerate(levers)}

    def row(kind: str, items, make):
        for i, item in enumerate(items):
            x = ROW_X0 + ROW_DX * (i % ROW_WRAP)
            y = ROW_Y[kind] + ROW_DY * (i // ROW_WRAP)
            symbols.append(make(item, (round(x, 2), round(y, 2))))

    symbols.append(tpl.note(
        "MAIN HOUSES -- one per desk column; rename each (FIXME)",
        (ROW_X0, ROW_Y["house"] - 7.62)))
    row("house", levers, lambda lev, at: place("Railroad:MAIN HOUSE", at, {
        "Reference": f"HOUSE{levers.index(lev) + 1}", "Value": houses[lev["column"]],
        "Milepost": "FIXME",
    }))

    by_local = {s["local"]: s for s in facts["switches"]}
    entries = []
    for lev in levers:
        if not lev["label"]:
            continue
        legacy = by_local.get(lev["local"], {})
        entries.append({
            "lib": "Railroad:Switch_Lock" if lev["kind"] == "LOCK"
                   else "Railroad:Switch_Powered",
            "ref": f"SW{lev['label']}", "value": lev["label"],
            "cp": houses[lev["column"]], "tc": legacy.get("tc"),
            "local": lev["local"],
        })
    levered = {e["local"] for e in entries}
    for n, s in enumerate(x for x in facts["switches"] if x["local"] not in levered):
        # A reference must end in digits, so a local like "3B" cannot be one.
        entries.append({"lib": "Railroad:Switch_Powered",
                        "ref": f"SW90{n}",
                        "value": f"FIXME {s['local']}", "cp": "FIXME",
                        "tc": s["tc"], "local": s["local"]})
    symbols.append(tpl.note(
        "SWITCHES AND LOCKS -- AAR-named from the desk levers; CP points at "
        "the house of the column that levers it",
        (ROW_X0, ROW_Y["switch"] - 7.62)))

    def make_switch(e, at):
        # The OS circuit defaults to <switch>T1; only an odd legacy circuit
        # (a shared yard-ladder circuit) needs an explicit TC.
        tc = "${VALUE}T1"
        if e["tc"] and e["tc"] != f"{e['local']}T1":
            tc = e["tc"]
        return place(e["lib"], at, {
            "Reference": e["ref"], "Value": e["value"], "CP": e["cp"], "TC": tc,
        })
    row("switch", entries, make_switch)

    os_circuits = {s["tc"] for s in facts["switches"] if s["tc"]}
    circuits = [c for c in facts["circuits"] if c not in os_circuits]
    symbols.append(tpl.note(
        "TRACK CIRCUITS -- OS circuits are derived from their switch and are "
        "not drawn; CP allocation is FIXME",
        (ROW_X0, ROW_Y["circuit"] - 7.62)))
    row("circuit", circuits, lambda c, at: place("Railroad:Track Circuit", at, {
        "Reference": f"TC{circuits.index(c) + 1}", "Value": c, "CP": "FIXME",
    }))

    calls = facts["calls"] or sorted({c for lev in levers for c in lev["calls"]})
    symbols.append(tpl.note("MAINTAINER CALLS", (ROW_X0, ROW_Y["call"] - 7.62)))
    row("call", calls, lambda c, at: place("Railroad:MaintainerCall", at, {
        "Reference": f"MC{calls.index(c) + 1}", "Value": c,
    }))

    symbols.append(tpl.note(recipe(interlocking, project, facts, levers, houses),
                            (ROW_X0, ROW_Y["call"] + 25.40)))
    return symbols


def main() -> int:
    levers_by_interlocking = desk_levers()
    tpl = Templates()
    pro_template = json.loads((TEMPLATE_DIR / "Luchessa.kicad_pro").read_text())
    made = []
    for interlocking, (project, xml_name) in PROJECTS.items():
        levers = levers_by_interlocking.get(interlocking)
        if not levers:
            print(f"  SKIP {project}: no desk columns", file=sys.stderr)
            continue
        out = SPCOAST / project
        sch = out / f"{project}.kicad_sch"
        if sch.exists():
            print(f"  SKIP {project}: {sch.name} already exists", file=sys.stderr)
            continue
        out.mkdir(exist_ok=True)
        facts = plant_facts(xml_name)
        sheet_uuid = new_uuid()
        symbols = build(interlocking, project, facts, levers, tpl, f"/{sheet_uuid}")
        node_uuid = sheet_uuid
        # emit with the sheet uuid the instance paths already reference
        target = sch
        n = ["kicad_sch"]
        for key in ("version", "generator", "generator_version"):
            n.append(copy.deepcopy(tpl.header[key]))
        n.append(["uuid", '"' + node_uuid])
        n.append(copy.deepcopy(tpl.header["paper"]))
        tb = copy.deepcopy(tpl.header["title_block"])
        S.find(tb, "title")[1] = '"' + project
        n.append(tb)
        n.append(tpl.lib_symbols)
        n.extend(symbols)
        n.append(["sheet_instances", ["path", '"/', ["page", '"1']]])
        n.append(["embedded_fonts", "no"])
        target.write_text(S.dump(n) + "\n")

        pro = copy.deepcopy(pro_template)
        pro["meta"]["filename"] = f"{project}.kicad_pro"
        pro["sheets"] = [[node_uuid, project]]
        (out / f"{project}.kicad_pro").write_text(json.dumps(pro, indent=2) + "\n")
        (out / "Makefile").write_text("KIND := plant\ninclude ../kicad.mk\n")
        made.append((project, len(symbols)))
    for project, count in made:
        print(f"  created {project:22s} {count} symbols + notes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
