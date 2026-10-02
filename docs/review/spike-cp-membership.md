# Spike S3: can control point membership be derived from signals?

Status: spike report (2026-10-01). Throwaway code; nothing in `tools/` is changed. Source: subagent
run, saved by the orchestrating session. Parent: `vocabulary-review.md`, finding F4 and spike S3.

## Answer

- **As control point membership: yes, with no added fact.**
- **As what the `CP` field records today: no.** On the wired plants the `CP` field records which
  house an appliance is assigned to. Signals cannot derive that.
- **By the F4 definition, the drawn Luchessa is one control point, not three.** No controlled signal
  stands between switches 783, 795 and 799. GilroyInterchange is one control point with two houses.

## What was run

- Fresh netlists exported with `kicad-cli` for all seven SPCoast projects.
- Each compiled with `PlantGraphCompiler().compile(library, netlist, None)`. The layout path was not used.
- The throwaway rule was run on Luchessa, GilroyInterchange, Sargent and Watsonville. The Watsonville run is excluded: its schematic is incomplete and not valid evidence (owner, 2026-10-02).
- **Corporal, Christopher and GilroyCalTrain could not be run.** Their netlists have an empty
  `(nets)` section. The symbols are placed and nothing is connected.
- Reasoned only, not run: a plant with two or more signal-bounded control points and two or more
  houses. No wired plant like that exists.

## Rule A: control point membership

1. Cut the track graph at every Signal IRJ that carries a mast face, and at nothing else.
2. Each piece that contains a switch or derail is one control point. Its extent is the control point limits.
3. A signal belongs to the control point on its plant side.
4. A switch, its `T1` circuit and a dependent derail belong to the piece they sit in. The `<switch>D`
   name is then a cross-check, not the mechanism.
5. A track circuit inside a piece belongs to that control point. A track circuit outside every piece
   belongs to the control point whose signal faces it. If signals of two control points face it, it
   is a block between control points.
6. Dark track, industry track, hand-throw switches, and circuits beyond a plain IRJ on the approach
   side are members of no control point.
7. A MAIN HOUSE has no track pins. With one control point in a plant, all its houses attach to it.
   With two or more control points and two or more houses, nothing drawn pairs them.

## Rule B: house allocation (what `CP` is used for today)

1. Cut at every IRJ, giving sections.
2. Anchor each house by the switches assigned to it. This is the one added fact.
3. A signal belongs to the house of the switch section on its plant side.
4. A derail belongs to the house of its section.
5. An approach circuit belongs to the house of the signal that faces it.
6. An inner circuit with no switch belongs to the house of the neighbouring switch sections. If
   those are two houses, it is ambiguous.

## Results

Rule A:

| Project | Houses | Control points derived | Unplaced |
|---|---|---|---|
| Luchessa | 3 | 1: {783, 795, 795D, 799} | 0 of 15 |
| GilroyInterchange | 2 | 1: {777, 781} | 0 of 9 |
| Sargent | 1 | 1: {835} | 1: `Corporal:2NA` (belongs to the next plant) |
| Watsonville | excluded: the Watsonville schematic is incomplete and not valid evidence (owner, 2026-10-02) | | |
| Corporal, Christopher, GilroyCalTrain | 2, 3, 3 | not runnable: no nets | |

Support for the Luchessa result: masts 784EAB, 784WBC and 784WD each run one signal-to-signal route
through 783, 795 and 799. All five masts carry one signal number, 784. The desk has one signal lever
784 and one CODE button for columns 5 to 7.

Rule B against the drawn `CP` values (switches are anchors and are not counted):

| Project | Agree | Disagree | Ambiguous | No drawn value |
|---|---|---|---|---|
| Luchessa | 9 | 2: 784WA, 1NA | 1: 2NAA | 0 |
| GilroyInterchange | 3 | 0 | 2: TK1, INTER | 2: 778NAB, 778SC |
| Sargent | 4 | 0 | 1: `Corporal:2NA` | 3 masts |

- **784WA**: drawn CP Gilroy; derived CP Luchessa. Its plant pin leads into the reverse leg of 783.
- **1NA**: drawn CP Carnadero; derived CP Luchessa (784WA faces it). The desk puts its lamp in
  column 6, which is CP Gilroy. The drawn values do not agree with each other.
- **2NAA, TK1**: each lies between two switches of different houses. Both are drawn on the west house.
- **Masts with no value**: GilroyInterchange and Christopher write `CP` on the mast. `model.py` reads
  the IRJ field only. Those drawn values are not seen by the compiler today.

## Verdict

- The `CP` field can be retired as control point membership. Rule A replaces it.
- House allocation needs one fact for each switch (3 at Luchessa, in place of 15 drawn fields) and a
  rule for circuits between houses.
- **That fact already exists in the desk schematic**: the column that holds each switch lever
  (783 in column 5, 795 in column 6, 799 in column 7). If house allocation is a concern of the code
  line type, it belongs in the desk and linker layer, and the plant needs no `CP` field.
- The two Luchessa disagreements show that the drawn values are not geography. A derived value
  would not reproduce them.

## Owner's reading (2026-10-01, after the spike)

Rule A does not find control points. It finds the **interlocking limits**: the track between opposing
controlled signals. Its result "one piece for Luchessa" agrees with the owner: Luchessa is one
interlocking. A control point is declared by the designer with a `MAIN HOUSE` symbol. Luchessa has
three. The assignment of appliances to control points is a drawn fact (the `CP` field), as Rule B shows.
Read "control point" in the Rule A text and tables above as "interlocking". The section below is
kept as written by the spike and is superseded by this note.

## What this changes in the vocabulary review (superseded)

1. Ontology §8 and vocabulary review iteration 3 say that Luchessa has three control points. By the
   definition accepted in F4, it has one control point with three houses. Either the three houses are
   field stations (and their bungalows), or the drawing lacks the intermediate signals that would
   make three control points.
2. "An appliance belongs to a control point by geography" (ontology §7) is true of control points.
   It is not true of the field being retired. Retiring it changes the meaning, not only the mechanism.
3. Three of the seven plant projects are not wired. Nothing can be derived or checked on them yet.

## Code

Throwaway, in the spike worktree:
`.claude/worktrees/agent-a635548f0baa4d92a/tools/spike_cp_membership.py` and `spike_dump.py`.
Run from the worktree root: `PYTHONDONTWRITEBYTECODE=1 python3 tools/spike_cp_membership.py <exported .net>`.
