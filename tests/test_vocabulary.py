"""Gate: no retired term (FieldUnit docs/GLOSSARY.md §11) in a living document of this repo.

Living documents state current rules and instructions: everything tracked as Markdown except the dated records
(`docs/archive/`, `docs/review/`, `docs/CHANGELOG.md`) and the decision records (`docs/adr/NNNN-*.md`, which carry a
terms note instead of being reworded). Code (fenced or inline) and quoted mentions ("compiler") are not uses.

A §11 term with a qualifier in parentheses ("plant (alone)") depends on meaning and is checked only where QUALIFIED
gives a pattern for it. A qualifier on the last term of a row qualifies the whole row.
"""
import os
import re
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FIELDUNIT = Path(os.environ.get("FIELDUNIT_DIR", Path.home() / "Dropbox/Arduino/libraries/FieldUnit"))
GLOSSARY = FIELDUNIT / "docs" / "GLOSSARY.md"

RECORDS = re.compile(r"^(docs/archive/|docs/review/|docs/CHANGELOG\.md$|docs/adr/\d{4}-)")

# Qualified terms a pattern can tell apart from their allowed uses.
QUALIFIED = {
    "compiler (alone)": r"(?<![Pp]lant[\s-])(?<![Cc]ontroller[\s-])(?<![Pp]roof-of-concept[\s-])\b[Cc]ompilers?\b",
}

# Retired terms still in use, each waiting on the owner's ruling. Remove an entry when its sweep lands.
DEFERRED = {}

# Living documents not yet swept, each waiting on the owner's ruling: archive (superseded) or reword.
PENDING = {
    "docs/design/layout-model.md": "rev 8 draft of 2026-10-02, overtaken by ADR 0008 to 0011",
    "docs/design/layout-model-plan.md": "rev 3 draft of 2026-10-02, overtaken by ADR 0008 to 0011",
    "docs/design/ontology.md": "rev 5 draft of 2026-10-01, awaiting review since",
    "docs/design/desk-codeline-kicad-pattern.md": "draft of 2026-10-02, overtaken in part by ADR 0009",
}


def retired_terms(text):
    """The §11 terms as (term, pattern) pairs; qualified terms only where QUALIFIED knows them."""
    table = text[text.index("## 11."):text.index("## 12.")]
    terms = []
    for line in table.splitlines():
        cells = line.split("|")
        if len(cells) < 3 or not line.startswith("| ") or cells[1].strip() in ("Term", "---"):
            continue
        parts = [p.strip() for p in re.split(r",\s*(?![^()]*\))", cells[1].strip())]
        whole_row_qualified = "(" in parts[-1]
        for part in parts:
            if part in QUALIFIED:
                terms.append((part, QUALIFIED[part]))
            elif "(" not in part and not whole_row_qualified:
                variants = {part, part[0].upper() + part[1:]}
                terms.append((part, r"(?<!\w)(?:" + "|".join(map(re.escape, sorted(variants))) + r")(?!\w)"))
    return terms


def prose(text):
    """The text with code and quoted mentions blanked, line numbers kept."""
    blank = lambda m: re.sub(r"[^\n]", " ", m.group())
    text = re.sub(r"```.*?```", blank, text, flags=re.S)
    text = re.sub(r"`[^`\n]*`", blank, text)
    return re.sub(r"\"[^\"\n]*\"|“[^”\n]*”", blank, text)


def living_documents():
    files = subprocess.check_output(["git", "ls-files", "*.md"], cwd=REPO, text=True).split()
    return [f for f in files if not RECORDS.match(f) and f not in PENDING]


def hits(terms, files):
    found = []
    for name in files:
        text = prose((REPO / name).read_text(encoding="utf-8"))
        for term, pattern in terms:
            for m in re.finditer(pattern, text):
                found.append((name, text.count("\n", 0, m.start()) + 1, term))
    return found


@unittest.skipUnless(GLOSSARY.exists(), f"FieldUnit glossary not present: {GLOSSARY}")
class RetiredTermTests(unittest.TestCase):
    def setUp(self):
        self.terms = retired_terms(GLOSSARY.read_text(encoding="utf-8"))

    def test_no_retired_term_in_a_living_document(self):
        live = [(t, p) for t, p in self.terms if t not in DEFERRED]
        found = hits(live, living_documents())
        self.assertEqual(found, [], "\n".join(f"{f}:{n}: {t}" for f, n, t in found))

    def test_every_deferred_and_qualified_term_is_in_the_glossary(self):
        names = {t for t, _ in self.terms}
        self.assertLessEqual(set(DEFERRED) | set(QUALIFIED), names)

    def test_every_pending_document_exists(self):
        self.assertLessEqual(set(PENDING), set(subprocess.check_output(["git", "ls-files"], cwd=REPO, text=True).split()))


class ParserTests(unittest.TestCase):
    TABLE = (
        "## 11. Retired\n\n| Term | Use instead |\n|---|---|\n"
        "| corridor | subdivision |\n"
        "| compiler (alone), seam reader | KiCad importer |\n"
        "| host, plant host (for what runs a FieldUnit) | processor |\n"
        "| plant (alone) | interlocking plant |\n\n## 12. Sources\n"
    )

    def test_rows_and_qualifiers(self):
        self.assertEqual([t for t, _ in retired_terms(self.TABLE)], ["corridor", "compiler (alone)", "seam reader"])

    def test_uses_and_mentions(self):
        terms = retired_terms(self.TABLE)
        text = 'The compiler reads.\nThe plant compiler and `compile_layout` and "compiler".\nCorridor here.\n'
        self.assertEqual(
            [(n, t) for t, p in terms for m in re.finditer(p, prose(text)) for n in [prose(text).count("\n", 0, m.start()) + 1]],
            [(3, "corridor"), (1, "compiler (alone)")],
        )


if __name__ == "__main__":
    unittest.main()
