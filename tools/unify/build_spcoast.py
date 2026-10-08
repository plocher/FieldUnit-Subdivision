#!/usr/bin/env python3
"""Build the unified SPCoast KiCad project from the archived per-project drawings.

Owns ~/Dropbox/KiCad/Railroad/SPCoast/ until the owner's cutover: fixes go here and the
project is regenerated, never hand-edited. Deterministic: UUIDs are derived from names,
so a rebuild of unchanged sources writes identical files.

Hierarchy (FieldUnit-Subdivision ADR 0004 D12; first cut, minimal change):

    SPCoast.kicad_sch            layout root
    └ South-cTc                  machine: the archived desk root (CtcMachine, code line symbols);
      │                          its desk sheet symbols keep their geometry, now pointing at plants
      └ <Plant>                  the archived plant sheet (holds the INTERLOCKING symbol)
        └ Panel                  the archived desk sheet for that plant

References are renumbered page * 1000 + n so they are unique across the project.

Usage:
    build_spcoast.py            build, then check
    build_spcoast.py --check    check only: ERC, and every archived netlist reappears net for net
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kicad_services.sch_text import blocks, end_of, replace_spans  # noqa: E402

RAILROAD = Path.home() / "Dropbox/KiCad/Railroad"
ARCHIVE = RAILROAD / "Archive/SPCoast"
OUT = Path(os.environ.get("SPCOAST_OUT", RAILROAD / "SPCoast"))
PROJECT = "SPCoast"
MACHINE = "South-cTc"
KICAD_CLI = os.environ.get("KICAD_CLI", "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli")
NS = uuid.UUID("5b0c0a1e-3d4f-4e52-9a51-5c0a57000000")  # SPCoast unify namespace


def uid(key: str) -> str:
    return str(uuid.uuid5(NS, key))


def norm(name: str) -> str:
    return re.sub(r"[\s_\-]", "", name).casefold()


# ------------------------------------------------------------------ text edits

def set_file_uuid(text: str, new: str) -> str:
    return re.sub(r'^(\(kicad_sch\n(?:\t[^\n]*\n)*?\t\(uuid ")[^"]+"', lambda m: m.group(1) + new + '"', text, count=1)


def renumber(ref: str, page: int) -> str:
    m = re.match(r"^(#?[A-Za-z_]+?)(\d+)$", ref)
    return f"{m.group(1)}{page * 1000 + int(m.group(2))}" if m else ref


def rewrite_symbols(text: str, path: str, page: int, refmap: dict) -> str:
    """Every placed symbol: one instance entry for this project and path; reference renumbered."""
    edits = []
    for s, e in blocks(text, "symbol", 1):
        b = text[s:e]
        if not b.startswith("(symbol\n\t\t(lib_id"):
            continue
        im = re.search(r"\n\t\t\(instances\n", b)
        old_ref = re.search(r'\(reference "([^"]+)"\)', b[im.start():]).group(1)
        unit = re.search(r"\(unit (\d+)\)", b[im.start():]).group(1)
        new_ref = renumber(old_ref, page)
        refmap[old_ref] = new_ref
        ie = end_of(b, im.start() + 3)
        inst = (f'(instances\n\t\t\t(project "{PROJECT}"\n\t\t\t\t(path "{path}"\n'
                f'\t\t\t\t\t(reference "{new_ref}")\n\t\t\t\t\t(unit {unit})\n\t\t\t\t)\n\t\t\t)\n\t\t)')
        b = b[:im.start() + 3] + inst + b[ie:]
        b = re.sub(r'(\n\t\t\(property "Reference" ")[^"]*"', lambda m: m.group(1) + new_ref + '"', b, count=1)
        edits.append((s, e, b))
    return replace_spans(text, edits)


# The owner's title block (2026-10-07): the same on every sheet except the title.
TITLE_BLOCK = {
    "date": "2026.10",
    "rev": "0.2",
    "company": "SPCoast Railroad",
    "comments": ["JPlocher", "Layout Maintenance Drawing", "South cTc", "Southern Pacific Railroad",
                 "Coast Division", "Era: 1985", "As Planned", "Layout Plan Drawings", "active"],
}


def title_block(title: str) -> str:
    tb = TITLE_BLOCK
    lines = [f'(title_block\n\t\t(title "{title}")', f'(date "{tb["date"]}")', f'(rev "{tb["rev"]}")',
             f'(company "{tb["company"]}")']
    lines += [f'(comment {i} "{c}")' for i, c in enumerate(tb["comments"], start=1)]
    return "\n\t\t".join(lines) + "\n\t)"


def set_title_block(text: str, title: str) -> str:
    """Replace the sheet's title block (US Letter landscape is the KiCad default paper)."""
    text = re.sub(r'\n\t\(paper "[^"]*"[^\n]*', '\n\t(paper "USLetter")', text, count=1)
    for s, e in blocks(text, "title_block", 1):
        return text[:s] + title_block(title) + text[e:]
    i = text.index("\n\t(paper") + 1
    i = text.index("\n", i)
    return text[:i] + "\n\t" + title_block(title) + text[i:]


def sheet_instances(path: str, page: int) -> str:
    return (f'(instances\n\t\t\t(project "{PROJECT}"\n\t\t\t\t(path "{path}"\n'
            f'\t\t\t\t\t(page "{page}")\n\t\t\t\t)\n\t\t\t)\n\t\t)')


# The owner's Panel link (Gilroy Caltrain, 2026-10-07): just above the title block, text inside.
PANEL_LINK = dict(at=(226.06, 164.86), size=(40.21, 6.59), fill="255 229 191 1",
                  name_at=(227.33, 167.132), file_at=(227.584, 168.148))


def sheet_block(name: str, file: str, sheet_uuid: str, parent_path: str, page: int,
                at=(235.0, 15.0), size=(30.0, 10.0), fill="0 0 0 0", name_at=None, file_at=None) -> str:
    x, y = at
    w, h = size
    nx, ny = name_at or (x, round(y - 0.7116, 4))
    fx, fy = file_at or (x, round(y + h + 0.5846, 4))
    autoplaced = "" if name_at else "\n\t\t(fields_autoplaced yes)"
    return f"""(sheet
		(at {x} {y})
		(size {w} {h})
		(exclude_from_sim no)
		(in_bom yes)
		(on_board yes)
		(dnp no){autoplaced}
		(stroke
			(width 0.1524)
			(type solid)
		)
		(fill
			(color {fill})
		)
		(uuid "{sheet_uuid}")
		(property "Sheetname" "{name}"
			(at {nx} {ny} 0)
			(show_name no)
			(do_not_autoplace no)
			(effects
				(font
					(size 1.27 1.27)
				)
				(justify left bottom)
			)
		)
		(property "Sheetfile" "{file}"
			(at {fx} {fy} 0)
			(show_name no)
			(do_not_autoplace no)
			(effects
				(font
					(size 1.27 1.27)
				)
				(justify left top)
			)
		)
		{sheet_instances(parent_path, page)}
	)"""


def drop_sheet_instances(text: str) -> str:
    """Only the root file carries (sheet_instances)."""
    for s, e in blocks(text, "sheet_instances", 1):
        return text[:s - 2] + text[e:]
    return text


def insert_before_end(text: str, block: str) -> str:
    """Insert a top-level block before (embedded_fonts) or the final ')'."""
    m = re.search(r"\n\t\(embedded_fonts", text)
    i = m.start() if m else text.rstrip().rindex(")") - 1
    return text[:i] + "\n\t" + block + text[i:]


def embedded_worksheet() -> str:
    """The project's page layout (kicad-embed://SPCoast.kicad_wks) lives in the root file."""
    t = (ARCHIVE / MACHINE / f"{MACHINE}.kicad_sch").read_text()
    for s, e in blocks(t, "embedded_files", 1):
        return t[s:e]
    return ""


ROOT_TEMPLATE = """(kicad_sch
	(version 20260306)
	(generator "eeschema")
	(generator_version "10.0")
	(uuid "{root}")
	(paper "USLetter")
	{title_block}
	(lib_symbols)
	{sheet}
	(sheet_instances
		(path "/"
			(page "1")
		)
	)
	(embedded_fonts no)
	{embedded_files}
)
"""


# ------------------------------------------------------------------ build

def plan():
    """Plants in desk order: (sheet name, plant dir, desk file, machine sheet uuid)."""
    desk_root = (ARCHIVE / MACHINE / f"{MACHINE}.kicad_sch").read_text()
    dirs = {norm(p.name): p.name for p in ARCHIVE.iterdir() if (p / f"{p.name}.kicad_sch").exists() and p.name != MACHINE}
    plants = []
    for s, e in blocks(desk_root, "sheet", 1):
        b = desk_root[s:e]
        name = re.search(r'\(property "Sheetname" "([^"]+)"', b).group(1)
        file = re.search(r'\(property "Sheetfile" "([^"]+)"', b).group(1)
        sid = re.search(r'\n\t\t\(uuid "([^"]+)"', b).group(1)
        plants.append((name, dirs[norm(name)], file, sid))
    return plants


def build():
    if list(OUT.glob("~*.lck")):
        sys.exit(f"{OUT} is open in KiCad (lock files); close it first")
    OUT.mkdir(exist_ok=True)
    root = uid("root")
    machine_uuid = uid(f"sheet/{MACHINE}")
    refmaps = {}  # (archive file) -> {old ref: new ref}
    pages = {}
    page = 2
    # machine sheet
    desk_root_file = ARCHIVE / MACHINE / f"{MACHINE}.kicad_sch"
    t = drop_sheet_instances(desk_root_file.read_text())
    mpath = f"/{root}/{machine_uuid}"
    refmaps[str(desk_root_file)] = {}
    t = rewrite_symbols(t, f"/{root}/{machine_uuid}", page, refmaps[str(desk_root_file)])
    pages[MACHINE] = page
    plants = plan()
    edits = []
    # pages left to right, as the plants sit on the machine sheet (for reading only; no meaning)
    spans = sorted(blocks(t, "sheet", 1), key=lambda se: float(re.search(r"\(at ([-\d.]+)", t[se[0]:se[1]]).group(1)))
    for s, e in spans:
        b = t[s:e]
        name = re.search(r'\(property "Sheetname" "([^"]+)"', b).group(1)
        pdir = next(p[1] for p in plants if p[0] == name)
        page += 2
        pages[name] = page - 1
        b = re.sub(r'(\(property "Sheetfile" ")[^"]+"', lambda m: m.group(1) + f'{pdir}.kicad_sch"', b, count=1)
        im = re.search(r"\n\t\t\(instances\n", b)
        b = b[:im.start() + 3] + sheet_instances(mpath, page - 1) + b[end_of(b, im.start() + 3):]
        edits.append((s, e, b))
    t = replace_spans(t, edits)
    t = set_title_block(t, "South cTc")
    t = set_file_uuid(t, uid(f"file/{MACHINE}"))  # its archived uuid was the old project's root
    (OUT / f"{MACHINE}.kicad_sch").write_text(t)
    sheets = [[root, "Root"], [machine_uuid, MACHINE]]
    for name, pdir, deskfile, sid in plants:
        ppage = pages[name]
        ppath = f"{mpath}/{sid}"
        panel_uuid = uid(f"sheet/{name}/Panel")
        # plant sheet
        src = ARCHIVE / pdir / f"{pdir}.kicad_sch"
        refmaps[str(src)] = {}
        pt = drop_sheet_instances(src.read_text())
        pt = set_file_uuid(pt, uid(f"file/{pdir}"))
        pt = rewrite_symbols(pt, ppath, ppage, refmaps[str(src)])
        pt = set_title_block(pt, name)
        pt = insert_before_end(pt, sheet_block("Panel", f"{pdir}-Panel.kicad_sch", panel_uuid, ppath, ppage + 1,
                                                **PANEL_LINK))
        (OUT / f"{pdir}.kicad_sch").write_text(pt)
        # panel sheet
        dsrc = ARCHIVE / MACHINE / deskfile
        refmaps[str(dsrc)] = {}
        dt = drop_sheet_instances(dsrc.read_text())
        dt = set_file_uuid(dt, uid(f"file/{pdir}-Panel"))
        dt = rewrite_symbols(dt, f"{ppath}/{panel_uuid}", ppage + 1, refmaps[str(dsrc)])
        dt = set_title_block(dt, name)
        (OUT / f"{pdir}-Panel.kicad_sch").write_text(dt)
        sheets += [[sid, name], [panel_uuid, "Panel"]]
    (OUT / f"{PROJECT}.kicad_sch").write_text(ROOT_TEMPLATE.format(
        root=root, title_block=title_block("South cTc"), embedded_files=embedded_worksheet(), sheet=sheet_block(MACHINE, f"{MACHINE}.kicad_sch", machine_uuid, f"/{root}", 2,
                                     at=(40.0, 40.0), size=(60.0, 30.0))))
    pro = json.loads((ARCHIVE / MACHINE / f"{MACHINE}.kicad_pro").read_text())
    pro["meta"]["filename"] = f"{PROJECT}.kicad_pro"
    pro["sheets"] = sheets
    # KiCad 10 takes the root from here, not from the file name
    pro["schematic"]["top_level_sheets"] = [{"filename": f"{PROJECT}.kicad_sch", "name": PROJECT, "uuid": root}]
    pro["schematic"]["used_designators"] = ""
    (OUT / f"{PROJECT}.kicad_pro").write_text(json.dumps(pro, indent=2) + "\n")
    (OUT / "refmap.json").write_text(json.dumps(refmaps, indent=1, sort_keys=True) + "\n")
    print(f"built {OUT}: {len(sheets)} sheets, {sum(len(m) for m in refmaps.values())} symbols")


# ------------------------------------------------------------------ check

def nets_of(netfile: Path):
    t = netfile.read_text()
    comps = {}
    for m in re.finditer(r'\(comp\n\t\t\t\(ref "([^"]+)"\)[\s\S]*?\(sheetpath\n\t\t\t\t\(names "([^"]*)"\)', t):
        comps[m.group(1)] = m.group(2)
    i = t.index("\n\t(nets")
    nets = [frozenset(re.findall(r'\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)', m.group(1)))
            for m in re.finditer(r"\n\t\t\(net\n(.*?)\n\t\t\)", t[i:], re.S)]
    return comps, nets


def export_netlist(sch: Path, out: Path):
    subprocess.run([KICAD_CLI, "sch", "export", "netlist", "--output", str(out), str(sch)],
                   check=True, capture_output=True)


def check():
    ok = True
    net = OUT / f"{PROJECT}.net"
    export_netlist(OUT / f"{PROJECT}.kicad_sch", net)
    comps, nets = nets_of(net)
    print(f"new: {len(comps)} components, {len(nets)} nets")
    refmaps = json.loads((OUT / "refmap.json").read_text())
    new_by_ref = {}
    for n in nets:
        for r, p in n:
            new_by_ref.setdefault(r, set()).add(n)
    projects = [(MACHINE, [str(ARCHIVE / MACHINE / f) for f in os.listdir(ARCHIVE / MACHINE) if f.endswith(".kicad_sch")])]
    projects += [(p, [str(ARCHIVE / p / f"{p}.kicad_sch")]) for p in sorted(os.listdir(ARCHIVE))
                 if p != MACHINE and (ARCHIVE / p / f"{p}.kicad_sch").exists()]
    for proj, files in projects:
        old_net = ARCHIVE / proj / f"{proj}.net"
        export_netlist(ARCHIVE / proj / f"{proj}.kicad_sch", old_net)
        ocomps, onets = nets_of(old_net)
        # archived sheets of a project: map each ref through its file's refmap
        sheet_file = {}
        if proj == MACHINE:
            names = {}
            for f in files:
                txt = Path(f).read_text()
                for r in re.findall(r'\(reference "([^"]+)"\)', txt):
                    sheet_file[r] = f
        else:
            for r in ocomps:
                sheet_file[r] = files[0]
        mapped = set()
        for n in onets:
            mapped.add(frozenset((refmaps[sheet_file[r]][r], p) for r, p in n))
        refs = {r for n in mapped for r, _ in n}
        sub = {frozenset((r, p) for r, p in n if r in refs) for n in nets if any(r in refs for r, _ in n)}
        extra = {n for n in nets if any(r in refs for r, _ in n) and any(r not in refs for r, _ in n)}
        same = mapped == sub
        ok &= same
        print(f"  {proj:18} archived {len(onets):3} nets  {'identical' if same else 'DIFFERENT'}"
              f"{'' if not extra else f'  ({len(extra)} nets also reach outside it)'}")
        if not same:
            for n in sorted(mapped - sub, key=sorted)[:5]:
                print("     only archived:", sorted(n))
            for n in sorted(sub - mapped, key=sorted)[:5]:
                print("     only new:     ", sorted(n))
    erc = OUT / f"{PROJECT}-erc.rpt"
    subprocess.run([KICAD_CLI, "sch", "erc", "--output", str(erc), str(OUT / f"{PROJECT}.kicad_sch")],
                   capture_output=True)
    summary = [ln for ln in erc.read_text().splitlines() if "ERC messages" in ln or "Errors" in ln]
    print("ERC:", " | ".join(summary) or erc.read_text()[-300:])
    old_roots = {json.loads(p.read_text())["sheets"][0][0] for p in ARCHIVE.glob("*/*.kicad_pro")}
    old_roots.add("87b90fc6-5e27-4e06-8416-fb28e674fdea")
    bad = [f"{p.name}:{u[:8]}" for p in OUT.glob("*.kicad_*") for u in old_roots if u in p.read_text()]
    pro = json.loads((OUT / f"{PROJECT}.kicad_pro").read_text())
    top = pro["schematic"]["top_level_sheets"]
    root_uuid = re.search(r'\(uuid "([^"]+)"', (OUT / f"{PROJECT}.kicad_sch").read_text()).group(1)
    if [s["uuid"] for s in top] != [root_uuid] or top[0]["filename"] != f"{PROJECT}.kicad_sch":
        bad.append(f"top_level_sheets {top}")
    print("archived root UUIDs / top level:", bad or "none; root is SPCoast.kicad_sch")
    return ok and not bad


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="check only")
    a = ap.parse_args()
    if not a.check:
        build()
    sys.exit(0 if check() else 1)
