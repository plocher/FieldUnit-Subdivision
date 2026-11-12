"""Refreeze the SPCoast gates on Railroad eef8217 (re-runnable: each edit is an exact replacement that must match once)."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
EDITS = {
"tests/test_layout_compiler.py": [
("""        self.assertEqual(procs["Gilroy Caltrain"], "SPCoastApp")
""", """        self.assertEqual(procs["GCaltrain"], "SPCoastApp")                # Gilroy Caltrain until Railroad eef8217
"""),
("""        self.assertEqual(t["MQTT"].anchors, {"JohnCTC", "Gilroy"})
        self.assertEqual(t["CMRInet"].anchors, {"SPCoastApp"})
        self.assertEqual(t["TimeCode"].anchors, {"JohnCTC"})
""", """        self.assertEqual(t["MQTT"].anchors, {"SouthCTC", "Gilroy"})         # the office processor is SouthCTC since Railroad eef8217 (JohnCTC before)
        self.assertEqual(t["CMRInet"].anchors, {"SPCoastApp"})
        self.assertEqual(t["TimeCode"].anchors, {"SouthCTC"})
"""),
("""        self.assertEqual((e["AAR Tokens"].transport, e["AAR Tokens"].processor), ("MQTT", "JohnCTC"))
        self.assertEqual((e["JMRI"].transport, e["JMRI"].processor), ("MQTT", "Gilroy"))
        self.assertEqual((e["US&S 506"].transport, e["US&S 506"].processor), ("TimeCode", "JohnCTC"))
        self.assertEqual((e["CMRInet"].transport, e["CMRInet"].processor), ("CMRInet", "SPCoastApp"))
        self.assertEqual(e["AAR Tokens"].given["Topic"], "ctc/SPCoast/SouthCTC/codeline/")   # the office unit is SouthCTC (owner, 2026-11-09)
        self.assertEqual(self.model["layout"]["codelines"]["AAR Tokens"]["relations"], {"transport": "MQTT", "processor": "JohnCTC"})
""", """        self.assertEqual((e["AAR Tokens"].transport, e["AAR Tokens"].processor), ("MQTT", "SouthCTC"))
        self.assertEqual((e["JMRI"].transport, e["JMRI"].processor), ("MQTT", "Gilroy"))
        self.assertEqual((e["US&S 506"].transport, e["US&S 506"].processor), ("TimeCode", "SouthCTC"))
        self.assertEqual((e["CMRInet"].transport, e["CMRInet"].processor), ("CMRInet", "SPCoastApp"))
        self.assertEqual(e["AAR Tokens"].given["Topic"], "ctc/SPCoast/SouthCTC/codeline/")   # the office unit is SouthCTC (owner, 2026-11-09)
        self.assertEqual(self.model["layout"]["codelines"]["AAR Tokens"]["relations"], {"transport": "MQTT", "processor": "SouthCTC"})
"""),
("""        self.assertEqual(self.sm.office_units["SouthCTC"].processor, "JohnCTC")
""", """        self.assertEqual(self.sm.office_units["SouthCTC"].processor, "SouthCTC")      # the office unit and its processor share the name since Railroad eef8217
"""),
("""        self.assertEqual(cols, {f"SouthCTC:{n}" for n in range(1, 15)})
""", """        self.assertEqual(cols, {f"SouthCTC:{n}" for n in range(0, 15)})           # column 0 is GCaltrain's switch 771 (Railroad eef8217)
"""),
("""        one kind that states no Name today; every identity.name finding is one of them (Railroad 9fcf779).\"\"\"
""", """        one kind that states no Name today; every identity.name finding is one of them (Railroad eef8217).\"\"\"
"""),
("""        self.assertEqual(len(masts), 44)                              # Railroad 9fcf779 (38 at 5715653; the owner's masts of 2026-11-09)
""", """        self.assertEqual(len(masts), 46)                              # Railroad eef8217: Christopher's siding dwarfs 814NA and 818SA (44 at 9fcf779, 38 at 5715653)
"""),
("""        self.assertEqual(len(heads), 56)                              # Railroad 9fcf779 (47 at 5715653); the heads' names and letters are #80's
""", """        self.assertEqual(len(heads), 60)                              # Railroad eef8217: 58 masts' heads plus the two dwarfs' (56 at 9fcf779, 47 at 5715653); the heads' names and letters are #80's
"""),
],
"tests/test_layout_model_file.py": [
("""        bad["interlockings"]["Gilroy:Caltrain"] = bad["interlockings"].pop("Gilroy Caltrain")
""", """        bad["interlockings"]["G:Caltrain"] = bad["interlockings"].pop("GCaltrain")
"""),
],
"tests/test_derive.py": [
("""        \"\"\"Gilroy Caltrain's shape: the field processor anchors MQTT""", """        \"\"\"GCaltrain's shape: the field processor anchors MQTT"""),
("""        self.assertEqual(report.counts(), {"error": 7, "warning": 0, "info": 6, "missing": 23})   # driver.signal_system on Gilroy's six JMRI signal mast drivers (no SignalSystem drawn yet, #85). Railroad 9fcf779 with the owner's uncommitted edits to Corporal, Sargent and Watsonville (exported 2026-11-11): regime.ambiguous on seven Corporal and Sargent pieces reachable from the END CTC faces and Corporal's 829T1 6.28 marker (membership is no regime source, the owner 2026-11-10; the owner is redrawing), regime.limits for six interlockings; switch.lever on 13 switches (Watsonville, Gilroy Caltrain 771) and on the locks 777 and 781 with switch.lock.local (no field pair drawn), train_order.device for Gilroy (Railroad 5715653); the importer's train_order.heads and geometry.head are not the derivation's
""", """        self.assertEqual(report.counts(), {"error": 0, "warning": 0, "info": 7, "missing": 18})   # Railroad eef8217: regime.limits for the seven interlockings (every piece has a regime: the interlockings share their block circuits by hierarchical nets, GCaltrain's boundary joint stops its yard); switch.lever on Watsonville's twelve powered switches 3 to 25 (GCaltrain's 771 has its lever on column 0, Gilroy's locks 777 and 781 their Local-Lock levers); driver.signal_system on Gilroy's six JMRI signal mast drivers (no SignalSystem drawn yet, #85); the importer's identity.name and head.letter are not the derivation's
"""),
],
"tests/test_geometry.py": [
("""        self.assertIn("label:ToCorporalMT", next(t["relations"].values() for t in runs if t.get("derived", {}).get("circuit") == "Corporal:834T"))
        self.assertEqual(len(g["markers"]), 11)                                  # Railroad 9fcf779 with the owner's uncommitted Sargent edits of 2026-11-10: the 261 sign gone, the boundary a plain IRJ with two GCOR markers
""", """        self.assertIn("label:NMT", next(t["relations"].values() for t in runs if t.get("derived", {}).get("circuit") == "Corporal:834T"))   # the hierarchical net NMT since Railroad eef8217 (ToCorporalMT before)
        self.assertEqual(len(g["markers"]), 10)                                  # Railroad eef8217: the NextCP toward Watsonville gone (the block is a shared net); 11 at 9fcf779
"""),
("""        two masts and plate, 836T, and the block track leaving through ToCorporalMT in place of the consumer of
""", """        two masts and plate, 836T, and the block track leaving through the hierarchical net NMT in place of the consumer of
"""),
("""                         ["Corporal:834T", "Sargent:1NAT", "Sargent:1T1", "Sargent:1T1", "Sargent:2SAT", "Sargent:836T"])   # 834T reaches the 834 joint through ToCorporalMT (ADR 0013 §7.1)
""", """                         ["Corporal:834T", "Sargent:1NAT", "Sargent:1T1", "Sargent:1T1", "Sargent:2SAT", "Sargent:836T"])   # 834T reaches the 834 joint through NMT (ADR 0013 §7.1)
"""),
("""        ports = sorted(v for t in g["track"] for v in t.get("relations", {}).values() if ":" in v)
        self.assertEqual(ports, ["Luchessa:783.R", "Luchessa:799.N", "Luchessa:799.R"])
""", """        ports = sorted(v for t in g["track"] for v in t.get("relations", {}).values() if ":" in v and not v.startswith(geometry.LABEL_END))
        self.assertEqual(ports, ["Luchessa:783.R", "Luchessa:799.N", "Luchessa:799.R"])
        labels = sorted(v for t in g["track"] for v in t.get("relations", {}).values() if v.startswith(geometry.LABEL_END))
        self.assertEqual(labels, ["label:NMT", "label:SMT1", "label:SMT2"])          # Luchessa's three block circuits leave by hierarchical nets (Railroad eef8217)
"""),
("""        sides = sorted(e.rsplit(".", 1)[1] for t in lu for e in t["relations"].values())
        self.assertEqual(sides, ["approach", "track"])                           # from the signal joint's approach side to the NextCP
""", """        sides = sorted(e if e.startswith(geometry.LABEL_END) else e.rsplit(".", 1)[1] for t in lu for e in t["relations"].values())
        self.assertEqual(sides, ["approach", "label:SMT2"])                      # from the signal joint's approach side to the hierarchical net SMT2 (Railroad eef8217; a NextCP's track side before)
"""),
("""        \"\"\"ADR 0013 §7.1 (Railroad 56ff2e1, 2a1696e): 834T leaves Corporal's sheet through ToSargentMT and reaches Sargent's
        through ToCorporalMT; the Beet Loader labels carry dark track between the two sheets. Each such run ends on the
        label's name, no coordinate and nothing from the other sheet; the circuit it carries is the derivation's.\"\"\"
        ends = {name: sorted(e for t in ix["geometry"]["track"] for e in t.get("relations", {}).values() if e.startswith("label:"))
                for name, ix in self.model["interlockings"].items()}
        self.assertEqual(ends["Corporal"], ["label:Beet Loader 1", "label:Beet Loader 2", "label:ToSargentMT"])
        self.assertEqual(ends["Sargent"], ["label:Beet Loader 1", "label:Beet Loader 2", "label:ToCorporalMT"])
        self.assertEqual({n: e for n, e in ends.items() if n not in ("Corporal", "Sargent")}, {n: [] for n in ends if n not in ("Corporal", "Sargent")})
        out = next(t for t in self.model["interlockings"]["Corporal"]["geometry"]["track"] if t.get("relations", {}).get("to") == "label:ToSargentMT")
""", """        \"\"\"ADR 0013 §7.1 (Railroad eef8217): every interlocking's block circuits leave its sheet by hierarchical nets, NMT
        and SMT (Luchessa's two south mains SMT1 and SMT2; Christopher's siding sheet has none of its own); the Beet
        Loader labels carry dark track between Corporal's and Sargent's sheets. Each such run ends on the label's name,
        no coordinate and nothing from the other sheet; the circuit it carries is the derivation's.\"\"\"
        ends = {name: sorted(e for t in ix["geometry"]["track"] for e in t.get("relations", {}).values() if e.startswith("label:"))
                for name, ix in self.model["interlockings"].items()}
        self.assertEqual(ends, {"Christopher": [], "Corporal": ["label:Beet Loader 1", "label:Beet Loader 2", "label:SMT"],
                                "GCaltrain": ["label:NMT", "label:SMT"], "Gilroy": ["label:NMT", "label:SMT"],
                                "Luchessa": ["label:NMT", "label:SMT1", "label:SMT2"],
                                "Sargent": ["label:Beet Loader 1", "label:Beet Loader 2", "label:NMT", "label:SMT"], "Watsonville": ["label:NMT"]})
        out = next(t for t in self.model["interlockings"]["Corporal"]["geometry"]["track"] if t.get("relations", {}).get("to") == "label:SMT")
"""),
],
"tests/test_trackplan.py": [
("""        self.assertEqual(len(joints), 36)                                   # Watsonville's 838SAB joint (Railroad 253b666)
""", """        self.assertEqual(len(joints), 38)                                   # Railroad eef8217: Christopher's siding dwarfs 814NA and 818SA (36 at 9fcf779)
"""),
("""        # IRJ, IRJ_SIGNAL, IRJ_SIGNALS; NEXT_CP, BUMPER, INDUSTRY; policies by Kind with the one plate: the Corporal to
        # Sargent block drawn across sheets (Railroad 56ff2e1, 2a1696e, 31954c5) replaced that NextCP pair; the three
        # CTC boundaries are plain IRJs with a marker each side (Railroad 0ddd395). Read from Railroad 9fcf779 with the
        # owner's uncommitted edits of 2026-11-10 (two BEGIN CTC faces beyond Watsonville's yard IRJs); the policy
        # counts move with that redraw, the joints and ends do not.
        kinds = Counter(r["given"]["Kind"] for ix in self.model["interlockings"].values() for k in ("joints", "ends", "policies") for r in ix.get("track", {}).get(k, []))
        self.assertEqual({k: v for k, v in kinds.items() if not k.startswith("GCOR_")}, {"IRJ": 57, "IRJ_SIGNAL": 36, "IRJ_SIGNALS": 2, "NEXT_CP": 16, "BUMPER": 3, "INDUSTRY": 5, "RULE_290_G": 1})
        self.assertEqual({k: v for k, v in kinds.items() if k.startswith("GCOR_")}, {"GCOR_RULE_9_14": 10, "GCOR_RULE_10": 5, "GCOR_RULE_14": 2, "GCOR_RULE_6_13": 5, "GCOR_RULE_6_28": 4})
""", """        # IRJ, IRJ_SIGNAL, IRJ_SIGNALS; NEXT_CP, BUMPER, INDUSTRY; policies by Kind with the one plate. Railroad eef8217:
        # the interlockings share their block circuits by hierarchical nets, so of the 16 NextCPs only Luchessa's to
        # Hollister (off_layout) remains; Christopher's siding is a controlled siding (two dwarf signal joints in place
        # of two plain IRJs, its 6.28 marker gone); Gilroy's and Corporal's 6.28 markers are gone; GCaltrain keeps one
        # yard-limits marker behind its RegimeBoundary joint (a plain IRJ by Kind). The CTC boundaries are plain IRJs
        # with a marker each side (Railroad 0ddd395).
        kinds = Counter(r["given"]["Kind"] for ix in self.model["interlockings"].values() for k in ("joints", "ends", "policies") for r in ix.get("track", {}).get(k, []))
        self.assertEqual({k: v for k, v in kinds.items() if not k.startswith("GCOR_")}, {"IRJ": 55, "IRJ_SIGNAL": 38, "IRJ_SIGNALS": 2, "NEXT_CP": 1, "BUMPER": 3, "INDUSTRY": 5, "RULE_290_G": 1})
        self.assertEqual({k: v for k, v in kinds.items() if k.startswith("GCOR_")}, {"GCOR_RULE_9_14": 10, "GCOR_RULE_10": 5, "GCOR_RULE_14": 2, "GCOR_RULE_6_13": 3, "GCOR_RULE_6_28": 1})
"""),
("""    def test_every_next_cp_names_where_it_leads_and_is_answered(self):
        ends = [(i, e["given"].get("Interlocking")) for i, ix in self.model["interlockings"].items() for e in ix["track"].get("ends", [])
                if e["given"]["Kind"] == "NEXT_CP"]
        self.assertEqual(len(ends), 16)          # the Corporal to Sargent pair is gone: the block is drawn (Railroad 56ff2e1, 2a1696e)
        self.assertEqual([e for e in ends if not e[1]], [])
        self.assertEqual(sorted(b for a, b in ends if a == "Christopher"), ["Corporal", "Corporal", "Luchessa", "Luchessa"])
        self.assertEqual(self.sm.report.by_code("next_cp.pair"), [])
""", """    def test_the_blocks_are_shared_nets_and_the_one_next_cp_left_is_off_layout(self):
        \"\"\"Railroad eef8217: the interlockings share their block circuits through hierarchical nets, one circuit per shared
        net named by the station whose processor reads it, so a neighbour's joint stands on it; the only NextCP left
        leads off the layout to Hollister.\"\"\"
        ends = [(i, e["given"]) for i, ix in self.model["interlockings"].items() for e in ix["track"].get("ends", []) if e["given"]["Kind"] == "NEXT_CP"]
        self.assertEqual(ends, [("Luchessa", {"Kind": "NEXT_CP", "Interlocking": "Hollister", "Style": "off_layout"})])
        self.assertEqual(self.sm.report.by_code("next_cp.pair") + self.sm.report.by_code("next_cp.off_layout"), [])
        shared = {n: sorted({c for j in ix["track"]["joints"] for c in j["derived"].get("circuits", {}).values() if not c.startswith(n + ":")})
                  for n, ix in self.model["interlockings"].items()}
        self.assertEqual(shared, {"Christopher": ["Luchessa:1NAT", "Luchessa:2NAT"], "Corporal": ["Christopher:1NAT", "Christopher:2NAT"],
                                  "GCaltrain": [], "Gilroy": ["GCaltrain:1NAT"], "Luchessa": ["Gilroy:1NAT"],
                                  "Sargent": ["Corporal:834T"], "Watsonville": ["Sargent:1NAT"]})

    def test_a_desk_lamp_consumes_the_neighbours_circuit_as_a_remote_indication(self):
        \"\"\"Railroad eef8217: the station that does not read a shared circuit shows it from the other's indication; four
        lamps were retargeted with the shared nets, beside the six of the Corporal to Sargent block and Luchessa's traffic.\"\"\"
        lamps = sorted((d["given"]["Indication"], d["relations"]["interlocking"]) for d in self.model["officeUnits"]["SouthCTC"]["devices"]
                       if d["given"]["Appliance"] == "lamp" and ":" in d["given"].get("Indication", ""))
        self.assertEqual(lamps, [("Christopher:1NATK", "Corporal"), ("GCaltrain:1NATK", "Gilroy"), ("Luchessa:1NATK", "Christopher"), ("Luchessa:2NATK", "Christopher"),
                                 ("Luchessa:NFLK", "Gilroy"), ("Luchessa:SFLK", "Gilroy"), ("Watsonville:02TK", "Corporal"), ("Watsonville:837T1K", "Sargent"),
                                 ("Watsonville:NFLK", "Corporal"), ("Watsonville:SFLK", "Corporal")])
        self.assertEqual(self.sm.report.by_code("reference.indication"), [])
"""),
("""    def test_the_beet_loader_and_gilroy_caltrains_yard_carry_their_regimes(self):
        \"\"\"Railroad 0ddd395: TWC beyond Corporal's and Sargent's boundaries, where the Beet Loader tracks rejoin the two
        sheets; yard limits on Gilroy Caltrain's bumper tracks (ADR 0013 §7.1).\"\"\"
        for name in ("Corporal", "Sargent"):
            pieces = {p["derived"]["name"]: p["derived"] for p in self.ix(name)["track"]["pieces"]}
            self.assertEqual(pieces[f"{name}:1T1"], {"name": f"{name}:1T1", "circuit": f"{name}:1T1", "regime": "GCOR_RULE_14", "by": "marker"}, name)
        yard = [p["derived"] for p in self.ix("Gilroy Caltrain")["track"]["pieces"] if p["derived"].get("regime") == "GCOR_RULE_6_13" and p["derived"]["by"] == "marker"]
        self.assertEqual(len(yard), 3)                                # the three bumper tracks; what inherits from them is the rules' business
""", """    def test_the_beet_loader_and_gcaltrains_yard_carry_their_regimes(self):
        \"\"\"Railroad 0ddd395: TWC beyond Corporal's and Sargent's boundaries, where the Beet Loader tracks rejoin the two
        sheets. Railroad eef8217: GCaltrain's one yard-limits marker is on 773T1, behind the RegimeBoundary joint on
        771T1's far side; the lead 775T1 and the three bumper tracks inherit it, 771T1 and the mains CTC (ADR 0013 §7.1).\"\"\"
        for name in ("Corporal", "Sargent"):
            pieces = {p["derived"]["name"]: p["derived"] for p in self.ix(name)["track"]["pieces"]}
            self.assertEqual(pieces[f"{name}:1T1"], {"name": f"{name}:1T1", "circuit": f"{name}:1T1", "regime": "GCOR_RULE_14", "by": "marker"}, name)
        gc = self.ix("GCaltrain")
        self.assertEqual({p["derived"]["name"][10:]: (p["derived"]["regime"][10:], p["derived"]["by"]) for p in gc["track"]["pieces"]},
                         {"773T1": ("6_13", "marker"), "775T1": ("6_13", "inherited"), "01T": ("6_13", "inherited"), "02T": ("6_13", "inherited"), "03T": ("6_13", "inherited"),
                          "771T1": ("10", "inherited"), "1NAT": ("10", "inherited"), "1SAT": ("10", "inherited")})
        boundary = [j for j in gc["track"]["joints"] if j["given"].get("RegimeBoundary") == "yes"]
        self.assertEqual([(j["given"]["Kind"], j["derived"]["circuits"]) for j in boundary], [("IRJ", {"A": "GCaltrain:771T1", "B": "GCaltrain:773T1"})])
"""),
("""        # Railroad 9fcf779: 15 switch.lever (Watsonville's 3 to 25, Gilroy Caltrain 771, Gilroy's locks 777 and 781) and
        # 2 switch.lock.local are settled; identity.name and head.letter are the anonymous head devices, #80's; the
        # regime findings are the owner's redraw in progress (#113, #118); driver.signal_system is Gilroy's six JMRI signal
        # mast drivers with no SignalSystem drawn yet (#85). No warning: Lick and Hollister are marked off_layout and no
        # mast lacks its Kind.
        missing = Counter(d.code for d in self.sm.report.diags if d.severity == "missing")
        self.assertEqual({k: v for k, v in missing.items() if k.startswith("switch.")}, {"switch.lever": 15, "switch.lock.local": 2})
        heads = [d for ix in self.model["interlockings"].values() for d in ix["devices"] if d["given"]["Appliance"] == "head"]
        self.assertEqual(missing["identity.name"], len(heads))
        self.assertEqual(set(missing) - {"switch.lever", "switch.lock.local", "identity.name", "head.letter", "driver.signal_system"} - {k for k in missing if k.startswith("regime.")}, set())
        self.assertEqual(self.sm.report.counts()["warning"], 0)
""", """        # Railroad eef8217: switch.lever on Watsonville's twelve powered switches 3 to 25 only (GCaltrain's 771 has its
        # lever on column 0, Gilroy's locks 777 and 781 their Local-Lock levers, so no switch.lock.local); identity.name
        # and head.letter are the anonymous head devices, #80's; driver.signal_system is Gilroy's six JMRI signal mast
        # drivers with no SignalSystem drawn yet (#85). Every piece has a regime. No warning: Hollister is marked
        # off_layout and no mast lacks its Kind.
        missing = Counter(d.code for d in self.sm.report.diags if d.severity == "missing")
        self.assertEqual({k: v for k, v in missing.items() if k.startswith("switch.")}, {"switch.lever": 12})
        self.assertEqual(sorted(d.where for d in self.sm.report.by_code("switch.lever")), sorted(f"interlockings/Watsonville/appliances/{n}" for n in range(3, 27, 2)))
        heads = [d for ix in self.model["interlockings"].values() for d in ix["devices"] if d["given"]["Appliance"] == "head"]
        self.assertEqual(missing["identity.name"], len(heads))
        self.assertEqual(set(missing), {"switch.lever", "identity.name", "head.letter", "driver.signal_system"})
        self.assertEqual(self.sm.report.counts(), {"error": 0, "warning": 0, "info": 7, "missing": 136})
        self.assertEqual(sorted(d.entities[0] for d in self.sm.report.by_code("regime.limits")), [f"interlockings/{n}" for n in sorted(self.model["interlockings"])])
"""),
("""        edits/add_mast_kind.py sweep of 2026-11-03 did for every placement. As of the Railroad working tree of
        2026-11-03 (31954c5 plus uncommitted edits to the seven sheets and the library), all 40 masts state theirs:
        the four PERMISSIVE automatics of the Corporal to Sargent block and 36 CONTROLLED. Nothing is reported, and
        nothing is inferred: a mast with no Kind would be ``mast.kind`` at missing.\"\"\"
        masts = {(i, n): a["given"].get("Kind") for i, ix in self.model["interlockings"].items() for n, a in ix.get("appliances", {}).items()
                 if a["given"]["Appliance"] == "mast"}
        self.assertEqual(len(masts), 40)
""", """        edits/add_mast_kind.py sweep of 2026-11-03 did for every placement. As of Railroad eef8217 all 42 masts state
        theirs: the four PERMISSIVE automatics of the Corporal to Sargent block and 38 CONTROLLED, Christopher's siding
        dwarfs 814NA and 818SA among them. Nothing is reported, and nothing is inferred: a mast with no Kind would be
        ``mast.kind`` at missing.\"\"\"
        masts = {(i, n): a["given"].get("Kind") for i, ix in self.model["interlockings"].items() for n, a in ix.get("appliances", {}).items()
                 if a["given"]["Appliance"] == "mast"}
        self.assertEqual(len(masts), 42)
        self.assertEqual({(i, a["given"].get("Style")) for (i, n), a in ((k, self.ix(k[0])["appliances"][k[1]]) for k in masts) if n in ("814NA", "818SA")}, {("Christopher", "dwarf")})
"""),
],
}

def main() -> int:
    bad = 0
    for rel, pairs in EDITS.items():
        p = ROOT / rel
        text = p.read_text(encoding="utf-8")
        for old, new in pairs:
            n = text.count(old)
            if n == 1:
                text = text.replace(old, new)
            elif n == 0 and text.count(new) == 1:
                print(f"{rel}: already applied: {new.strip().splitlines()[0][:70]}")
            else:
                print(f"{rel}: {n} matches for {old.strip().splitlines()[0][:70]}"); bad += 1
        p.write_text(text, encoding="utf-8")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
