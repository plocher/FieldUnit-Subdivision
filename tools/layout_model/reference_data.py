"""Reference data resolved per entity into ``derived`` (ADR 0012 §6; the owner, 2026-11-13): the tables are selected by the
model and the result is written beside the entity that needs it, so a consumer in another repository reads the resolved
words from the file and never a table by name. The selection is stated, never re-derived: the layout's ``given.Railroad``,
``Era`` and ``Rulebook`` (the Railroad symbol's fields) choose the row of every layout-keyed table, and
``layout.derived.reference`` names the row key each resolved to; an entity's own fields choose the rest (a head's
``Style``, a driver's ``JMRI.SignalSystem``, a code line's ``Kind``). An explicit override is a stated field beside the
item it overrides: a train order board's ``Rest`` and ``Shows.<input>`` over the table's words, a mast's ``Indications``
over the derived demand, a driver's ``JMRI.SignalSystem`` over its encoding's. The user's own tables layer over the
shipped ones (``reference``); a key with no row resolves to nothing, never a guess.

What is resolved, in the consumers' reading order:

- **Train order inputs**, on each face of a train order board (``derived.faces.<pin>``): ``inputs``, the ranked pairs
  of the inputs the face's lever binds, keyed by rank from 1, the most restrictive, each ``{input, indication}``
  (keyed, not listed: a list in the file is a set, ADR 0008 §4.8); ``rest``, the word
  nothing asserted shows; ``indications``, the set of words the face can show (FieldUnit ADR 0010 D1, D2).
- **Head policy**, on each position of a mast (``derived.positions.<pin>.shows``): mast indication -> the head word
  this position shows, the owner's lookup (mast indication, head count, head number, context: the rulebook). Written
  only where the policies table has a row for the rulebook and head count; none is shipped yet (#62).
- **Aspect names**, on each JMRI signal mast driver (``derived.aspectNames``): indication -> the name it publishes, for
  its signal system and its mast's Kind.
- **Indication tokens and stations**, on each code line (``layout.codelines.<name>.derived``): ``station``, what one
  station on it is (house or interlocking), and ``tokens``, the office indication templates by appliance class. The
  station packets themselves are not stored (the owner, 2026-10-28); ``tools/railroad/codeline.py`` computes them from
  these same rows.
"""
from __future__ import annotations

from typing import Any, Optional

from . import reference, sort_key


class Resolver:
    """The reference data of one model: its selection, and each resolution the derivation writes."""

    def __init__(self, model: dict[str, Any], user: Optional[dict[str, Any]] = None) -> None:
        self.m, self.user = model, user or {}
        g = model.get("layout", {}).get("given", {})
        self.railroad, self.era, self.rulebook = g.get("Railroad"), g.get("Era"), g.get("Rulebook")

    # ---------------------------------------------------------------------------------------------- selection

    def selected(self) -> dict[str, str]:
        """Each layout-keyed table to the row key the layout's selection resolved to: ``default`` where the rulebook has
        no row. A table with no row at all for this layout is not named."""
        out: dict[str, str] = {}
        key, _ = reference.train_order_inputs(self.rulebook, self.user.get("trainOrderInputs"))
        out["trainOrderInputs"] = key
        if self.rulebook and reference.policy(self.rulebook, self.user.get("policies")) is not None:
            out["policies"] = self.rulebook
        return out

    def resolve_layout(self) -> None:
        """``layout.derived.reference`` and each code line's ``derived.station`` and ``derived.tokens``."""
        layout = self.m.setdefault("layout", {})
        _set(layout, {**layout.get("derived", {}), "reference": self.selected()})
        for line in layout.get("codelines", {}).values():
            _set(line, {**line.get("derived", {}), **self.codeline(line.get("given", {}).get("Kind"))})

    # ------------------------------------------------------------------------------------------- train orders

    def train_order_face(self, bound: set[str], board: dict[str, str]) -> dict[str, Any]:
        """What one face can show from the inputs its lever binds: the selected row's ranked pairs for those inputs, the
        rest word, and the set of words. The board's ``Rest`` overrides the rest word, its ``Shows.<input>`` the word of
        that input (an explicit choice carried in the model, FieldUnit ADR 0010 D2)."""
        _, row = reference.train_order_inputs(self.rulebook, self.user.get("trainOrderInputs"))
        rest = board.get("Rest") or row["rest"]
        ranked = [{"input": i["input"], "indication": board.get(f"Shows.{i['input']}") or i["indication"]}
                  for i in row["inputs"] if i["input"] in bound]
        inputs = {str(k): i for k, i in enumerate(ranked, 1)}            # keyed by rank: a list in the file is a set (ADR 0008 §4.8)
        words = sorted({rest, *(i["indication"] for i in ranked)}, key=sort_key)
        return {**({"inputs": inputs} if inputs else {}), "rest": rest, "indications": words}   # absent is absent

    # -------------------------------------------------------------------------------------------- head policy

    def shows(self, head_count: int) -> Optional[list[dict[str, str]]]:
        """For a mast of ``head_count`` positions, each position's mast indication -> head word, top down, from the
        rulebook's policy row for that count; None when no row states it (nothing is inferred)."""
        row = (reference.policy(self.rulebook, self.user.get("policies")) or {}).get(str(head_count))
        if not row:
            return None
        return [{ind: words[k] for ind, words in row.items() if k < len(words)} for k in range(head_count)]

    # ------------------------------------------------------------------------------------------- aspect names

    def aspect_names(self, system: Optional[str], kind: Optional[str]) -> dict[str, str]:
        return reference.aspect_names(system, kind, self.user.get("aspectNames"))

    # ---------------------------------------------------------------------------------------------- code line

    def codeline(self, encoding: Optional[str]) -> dict[str, Any]:
        """What one station on a code line of ``encoding`` is, and the indication templates by appliance class."""
        return {"station": reference.station_of(encoding, self.user.get("stations")),
                "tokens": {cls: list(t) for cls, t in reference.indication_tokens(encoding, self.user.get("indicationTokens")).items()}}


def _set(entity: dict[str, Any], derived: dict[str, Any]) -> None:
    """Absent is absent (ADR 0008 §4.7)."""
    d = {k: v for k, v in derived.items() if v not in (None, "", [], {})}
    if d:
        entity["derived"] = d
    else:
        entity.pop("derived", None)
