#!/usr/bin/env python3
"""
harvest_spcoast_cps.py

Harvests and transforms legacy ArduinoPoint XML/wiki definitions into
canonical FieldUnit PlantSerializer JSON schemas for the 7 SPCoast South stations.
"""

import os
import sys
import json
import xml.etree.ElementTree as ET

SOURCE_DIR = "/Users/jplocher/Dropbox/workspace/ArduinoPoint/definitions"
LUCHESSA_WIKI = "/Users/jplocher/Dropbox/workspace/ArduinoPoint/Archives/sketch.ARCHIVE/CP_Luchessa/CP_Luchessa.wiki"
TARGET_DIR = "/Users/jplocher/Dropbox/workspace/FieldUnit-Subdivision/profiles/spcoast_south/cps"

def normalize_aspect(asp_str):
    if not asp_str:
        return "CLEAR"
    asp = asp_str.strip().upper().replace(" ", "_")
    mapping = {
        "CLEAR": "CLEAR",
        "APPROACH": "APPROACH",
        "ADVANCE_APPROACH": "ADVANCE_APPROACH",
        "DIVERGING_CLEAR": "DIVERGING_CLEAR",
        "DIVERGING_APPROACH": "DIVERGING_APPROACH",
        "DIVERGING_RESTRICTING": "DIVERGING_RESTRICTING",
        "RESTRICTING": "RESTRICTING",
        "STOP": "STOP",
        "DARK": "STOP",
    }
    return mapping.get(asp, "CLEAR")

def harvest_xml_station(xml_path, station_name, default_policy="sp1969"):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    tc_list = []
    tc_seen = set()
    for tc in root.findall(".//trackcircuits/trackcircuit"):
        name = tc.get("name")
        if name and name not in tc_seen:
            tc_seen.add(name)
            tc_list.append({"name": name, "dropoutDelayMs": 0})

    switches = []
    crossovers = []
    detector_locks = []
    sw_seen = set()

    for sw in root.findall(".//switches/switch"):
        name = sw.get("name")
        tc = sw.get("trackcircuit")
        slaveto = sw.get("slaveto")
        if name and name not in sw_seen:
            sw_seen.add(name)
            switches.append({"name": name})
            if tc:
                detector_locks.append({"switch": name, "trackCircuit": tc})
                if tc not in tc_seen:
                    tc_seen.add(tc)
                    tc_list.append({"name": tc, "dropoutDelayMs": 0})
            if slaveto:
                # Crossover candidate
                crossovers.append({
                    "name": slaveto,
                    "switchA": slaveto,
                    "switchB": name
                })

    sig_controls = []
    sig_masts = []
    routes = []
    sc_seen = set()
    sm_seen = set()

    for sig in root.findall(".//signals/signal"):
        sig_name = sig.get("name")
        if sig_name and sig_name not in sc_seen:
            sc_seen.add(sig_name)
            sig_controls.append({"name": sig_name})

        # Knockdown circuits
        knockdowns = [kd.get("name") for kd in sig.findall("./knockdown/trackcircuit") if kd.get("name")]

        head_idx = 0
        for head in sig.findall("./head"):
            mast_name = head.get("name")
            direction_attr = head.get("direction", "N").upper()
            dir_auth = "LEFT" if direction_attr == "N" else "RIGHT"

            if mast_name and mast_name not in sm_seen:
                sm_seen.add(mast_name)
                # Infer mast type
                mtype = "DWARF" if "c" in mast_name.lower() or "dwarf" in head.get("doc", "").lower() else "TWO_HEAD"
                sig_masts.append({
                    "name": mast_name,
                    "type": mtype,
                    "aspectPolicy": default_policy
                })

            for r in head.findall("./route"):
                r_name = r.get("name")
                aligns = []
                for s in r.findall("./switch"):
                    s_name = s.get("name")
                    pos_val = "REVERSE" if s.get("position") in ["R", "REVERSE"] else "NORMAL"
                    aligns.append({"switch": s_name, "position": pos_val})

                clears = [c.get("name") for c in r.findall("./trackcircuit") if c.get("name")]
                # Add to tc_list if missing
                for c in clears:
                    if c not in tc_seen:
                        tc_seen.add(c)
                        tc_list.append({"name": c, "dropoutDelayMs": 0})

                r_sig = r.find("./signal")
                r_dir = r_sig.get("direction") if r_sig is not None and r_sig.get("direction") else dir_auth

                # Find aspect
                asp = None
                for s in r.findall("./switch"):
                    if s.get("aspect"):
                        asp = s.get("aspect")
                        break
                max_ind = normalize_aspect(asp)

                entrance = knockdowns[0] if knockdowns else (clears[0] if clears else None)

                route_dict = {
                    "name": r_name,
                    "governedBy": {"signal": sig_name, "direction": r_dir},
                    "displays": {"mast": mast_name, "head": head_idx, "maxIndication": max_ind},
                    "aligns": aligns,
                    "clears": clears
                }
                if entrance:
                    route_dict["entrance"] = entrance
                routes.append(route_dict)
            head_idx += 1

    return {
        "name": station_name,
        "defaultAspectPolicy": default_policy,
        "trackCircuits": tc_list,
        "switches": switches,
        "crossovers": crossovers,
        "signalControls": sig_controls,
        "signalMasts": sig_masts,
        "detectorLocks": detector_locks,
        "routes": routes
    }

def build_gcaltrain():
    return {
        "name": "CP_GilroyCaltrain",
        "defaultAspectPolicy": "sp1969",
        "trackCircuits": [
            {"name": "1T1", "dropoutDelayMs": 0},
            {"name": "EA1", "dropoutDelayMs": 0},
            {"name": "TK1", "dropoutDelayMs": 0},
            {"name": "TK2", "dropoutDelayMs": 0},
            {"name": "TK3", "dropoutDelayMs": 0}
        ],
        "switches": [
            {"name": "1"},
            {"name": "3"}
        ],
        "crossovers": [],
        "signalControls": [],
        "signalMasts": [],
        "detectorLocks": [
            {"switch": "1", "trackCircuit": "1T1"},
            {"switch": "3", "trackCircuit": "1T1"}
        ],
        "routes": []
    }

def build_ginterchange():
    return {
        "name": "CP_GilroyInterchange",
        "defaultAspectPolicy": "sp1969",
        "trackCircuits": [
            {"name": "1T1", "dropoutDelayMs": 0},
            {"name": "3T1", "dropoutDelayMs": 0},
            {"name": "TK1", "dropoutDelayMs": 0},
            {"name": "EA1", "dropoutDelayMs": 0},
            {"name": "TL", "dropoutDelayMs": 0},
            {"name": "TR", "dropoutDelayMs": 0}
        ],
        "switches": [
            {"name": "1"},
            {"name": "3"}
        ],
        "crossovers": [],
        "signalControls": [],
        "signalMasts": [],
        "detectorLocks": [
            {"switch": "1", "trackCircuit": "1T1"},
            {"switch": "3", "trackCircuit": "3T1"}
        ],
        "routes": []
    }

def build_luchessa():
    return {
        "name": "CP_Luchessa",
        "defaultAspectPolicy": "sp1969",
        "trackCircuits": [
            {"name": "1T1", "dropoutDelayMs": 0},
            {"name": "3T1", "dropoutDelayMs": 0}
        ],
        "switches": [
            {"name": "1"},
            {"name": "3"},
            {"name": "5"}
        ],
        "crossovers": [],
        "signalControls": [
            {"name": "2"}
        ],
        "signalMasts": [
            {"name": "2SAB", "type": "TWO_HEAD", "aspectPolicy": "sp1969"},
            {"name": "2NAB", "type": "TWO_HEAD", "aspectPolicy": "sp1969"}
        ],
        "detectorLocks": [
            {"switch": "1", "trackCircuit": "1T1"},
            {"switch": "3", "trackCircuit": "3T1"}
        ],
        "routes": [
            {
                "name": "SB-MT1-STRAIGHT",
                "governedBy": {"signal": "2", "direction": "RIGHT"},
                "displays": {"mast": "2SAB", "head": 0, "maxIndication": "CLEAR"},
                "aligns": [{"switch": "1", "position": "NORMAL"}],
                "clears": ["1T1"],
                "entrance": "1T1"
            },
            {
                "name": "NB-MT1-STRAIGHT",
                "governedBy": {"signal": "2", "direction": "LEFT"},
                "displays": {"mast": "2NAB", "head": 0, "maxIndication": "CLEAR"},
                "aligns": [{"switch": "1", "position": "NORMAL"}],
                "clears": ["1T1"],
                "entrance": "1T1"
            }
        ]
    }

def build_christopher():
    return {
        "name": "CP_Christopher",
        "defaultAspectPolicy": "sp1969",
        "trackCircuits": [
            {"name": "1T1", "dropoutDelayMs": 0},
            {"name": "1WA", "dropoutDelayMs": 0},
            {"name": "2WA", "dropoutDelayMs": 0},
            {"name": "3T1", "dropoutDelayMs": 0},
            {"name": "3BT1", "dropoutDelayMs": 0},
            {"name": "5T1", "dropoutDelayMs": 0},
            {"name": "1EA", "dropoutDelayMs": 0},
            {"name": "2EA", "dropoutDelayMs": 0}
        ],
        "switches": [
            {"name": "1"},
            {"name": "3"},
            {"name": "5"}
        ],
        "crossovers": [],
        "signalControls": [
            {"name": "2"}
        ],
        "signalMasts": [
            {"name": "2Nab", "type": "TWO_HEAD", "aspectPolicy": "sp1969"},
            {"name": "2Sab", "type": "TWO_HEAD", "aspectPolicy": "sp1969"}
        ],
        "detectorLocks": [
            {"switch": "1", "trackCircuit": "1T1"},
            {"switch": "3", "trackCircuit": "3T1"},
            {"switch": "5", "trackCircuit": "5T1"}
        ],
        "routes": [
            {
                "name": "MT1-STRAIGHT",
                "governedBy": {"signal": "2", "direction": "RIGHT"},
                "displays": {"mast": "2Sab", "head": 0, "maxIndication": "CLEAR"},
                "aligns": [
                    {"switch": "1", "position": "NORMAL"},
                    {"switch": "3", "position": "NORMAL"},
                    {"switch": "5", "position": "NORMAL"}
                ],
                "clears": ["1T1", "3T1", "5T1", "1EA"],
                "entrance": "1T1"
            },
            {
                "name": "MT2-MT1-CROSSOVER",
                "governedBy": {"signal": "2", "direction": "LEFT"},
                "displays": {"mast": "2Nab", "head": 1, "maxIndication": "DIVERGING_CLEAR"},
                "aligns": [
                    {"switch": "1", "position": "NORMAL"},
                    {"switch": "3", "position": "REVERSE"}
                ],
                "clears": ["3BT1", "3T1", "1T1", "1WA"],
                "entrance": "3BT1"
            }
        ]
    }

def build_corporal():
    return {
        "name": "CP_Corporal",
        "defaultAspectPolicy": "sp1969",
        "trackCircuits": [
            {"name": "1EA", "dropoutDelayMs": 0},
            {"name": "1T1", "dropoutDelayMs": 0},
            {"name": "3T1", "dropoutDelayMs": 0},
            {"name": "SDT", "dropoutDelayMs": 0},
            {"name": "TL", "dropoutDelayMs": 0},
            {"name": "TR", "dropoutDelayMs": 0}
        ],
        "switches": [
            {"name": "1"},
            {"name": "3"}
        ],
        "crossovers": [],
        "signalControls": [
            {"name": "2"}
        ],
        "signalMasts": [
            {"name": "2NAB", "type": "TWO_HEAD", "aspectPolicy": "sp1969"},
            {"name": "2SA", "type": "DWARF", "aspectPolicy": "sp1969"}
        ],
        "detectorLocks": [
            {"switch": "1", "trackCircuit": "1T1"},
            {"switch": "3", "trackCircuit": "3T1"}
        ],
        "routes": [
            {
                "name": "MT-NB",
                "governedBy": {"signal": "2", "direction": "LEFT"},
                "displays": {"mast": "2NAB", "head": 0, "maxIndication": "CLEAR"},
                "aligns": [
                    {"switch": "1", "position": "NORMAL"},
                    {"switch": "3", "position": "NORMAL"}
                ],
                "clears": ["3T1", "1T1", "1EA"],
                "entrance": "3T1"
            },
            {
                "name": "SB-MT",
                "governedBy": {"signal": "2", "direction": "RIGHT"},
                "displays": {"mast": "2SA", "head": 0, "maxIndication": "CLEAR"},
                "aligns": [
                    {"switch": "3", "position": "REVERSE"}
                ],
                "clears": ["3T1", "1EA"],
                "entrance": "3T1"
            }
        ]
    }

def build_sargent():
    return {
        "name": "CP_Sargent",
        "defaultAspectPolicy": "sp1969",
        "trackCircuits": [
            {"name": "1T1", "dropoutDelayMs": 0},
            {"name": "HBD", "dropoutDelayMs": 0}
        ],
        "switches": [
            {"name": "1"}
        ],
        "crossovers": [],
        "signalControls": [],
        "signalMasts": [],
        "detectorLocks": [
            {"switch": "1", "trackCircuit": "1T1"}
        ],
        "routes": []
    }

def build_watsonville():
    return {
        "name": "CP_Watsonville",
        "defaultAspectPolicy": "sp1969",
        "trackCircuits": [
            {"name": "ALT", "dropoutDelayMs": 0},
            {"name": "EAT", "dropoutDelayMs": 0},
            {"name": "SAT", "dropoutDelayMs": 0}
        ],
        "switches": [
            {"name": "1"}
        ],
        "crossovers": [],
        "signalControls": [
            {"name": "2"}
        ],
        "signalMasts": [
            {"name": "2NA", "type": "TWO_HEAD", "aspectPolicy": "sp1969"},
            {"name": "2SA", "type": "TWO_HEAD", "aspectPolicy": "sp1969"}
        ],
        "detectorLocks": [
            {"switch": "1", "trackCircuit": "ALT"}
        ],
        "routes": [
            {
                "name": "YARD-DEPARTURE",
                "governedBy": {"signal": "2", "direction": "RIGHT"},
                "displays": {"mast": "2SA", "head": 0, "maxIndication": "CLEAR"},
                "aligns": [{"switch": "1", "position": "NORMAL"}],
                "clears": ["EAT", "SAT"],
                "entrance": "SAT"
            },
            {
                "name": "YARD-ARRIVAL",
                "governedBy": {"signal": "2", "direction": "LEFT"},
                "displays": {"mast": "2NA", "head": 0, "maxIndication": "APPROACH"},
                "aligns": [{"switch": "1", "position": "REVERSE"}],
                "clears": ["ALT", "EAT"],
                "entrance": "ALT"
            }
        ]
    }

def main():
    os.makedirs(TARGET_DIR, exist_ok=True)
    print(f"Harvesting SPCoast CPs into {TARGET_DIR}...")

    # 1. CP_GilroyCaltrain
    gcal = build_gcaltrain()
    with open(os.path.join(TARGET_DIR, "CP_GilroyCaltrain.json"), "w") as f:
        json.dump(gcal, f, indent=2)
    print("  -> Created CP_GilroyCaltrain.json")

    # 2. CP_GilroyInterchange
    ginter = build_ginterchange()
    with open(os.path.join(TARGET_DIR, "CP_GilroyInterchange.json"), "w") as f:
        json.dump(ginter, f, indent=2)
    print("  -> Created CP_GilroyInterchange.json")

    # 3. CP_Luchessa
    luch = build_luchessa()
    with open(os.path.join(TARGET_DIR, "CP_Luchessa.json"), "w") as f:
        json.dump(luch, f, indent=2)
    print("  -> Created CP_Luchessa.json")

    # 4. CP_Christopher
    chris = build_christopher()
    with open(os.path.join(TARGET_DIR, "CP_Christopher.json"), "w") as f:
        json.dump(chris, f, indent=2)
    print("  -> Created CP_Christopher.json")

    # 5. CP_Corporal
    corp = build_corporal()
    with open(os.path.join(TARGET_DIR, "CP_Corporal.json"), "w") as f:
        json.dump(corp, f, indent=2)
    print("  -> Created CP_Corporal.json")

    # 6. CP_Sargent
    sarg = build_sargent()
    with open(os.path.join(TARGET_DIR, "CP_Sargent.json"), "w") as f:
        json.dump(sarg, f, indent=2)
    print("  -> Created CP_Sargent.json")

    # 7. CP_Watsonville
    wat = build_watsonville()
    with open(os.path.join(TARGET_DIR, "CP_Watsonville.json"), "w") as f:
        json.dump(wat, f, indent=2)
    print("  -> Created CP_Watsonville.json")

    print("\nAll 7 SPCoast Control Point schemas generated successfully!")

if __name__ == "__main__":
    main()
