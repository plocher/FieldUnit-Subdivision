# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Before exploring, read these

- **Glossary**: FieldUnit `docs/GLOSSARY.md` (`~/Dropbox/Arduino/libraries/FieldUnit/docs/GLOSSARY.md`), the
  vocabulary shared by FieldUnit, FieldUnit-Subdivision and FieldUnit-Studio. Its section 11 lists retired terms.
  There is no `CONTEXT.md` here on purpose: one glossary serves the three repos, which are to be refactored into a
  better abstraction mix, and a per-repo glossary would fork it. `docs/archive/vocabulary-review.md` records how
  the terms were chosen.
- **`docs/adr/`**: the decision record; `docs/adr/README.md` is the index with what is accepted and what waits for
  the owner. FieldUnit's `docs/adr/` holds the decisions on the logic side and is cited from the index.
- **Order of authority** when sources disagree: AGENTS.md "Working agreements" (relay model and practice, then
  FieldUnit `src/`, then the KiCad-derived models, then legacy sketches as evidence only).

If a file is missing, **proceed silently**. Don't flag its absence; don't suggest creating it upfront.

## File structure

Single context, with the glossary held by a sibling repository:

```
~/Dropbox/Arduino/libraries/FieldUnit/docs/GLOSSARY.md   ← the glossary (CONTEXT.md's role)
~/Dropbox/Arduino/libraries/FieldUnit/docs/adr/          ← logic-side decisions
docs/adr/                                                ← this repo's decisions, README.md the index
docs/archive/vocabulary-review.md                        ← how the vocabulary was settled
```

When `/domain-modeling` resolves a term, it goes in the glossary, not in a new `CONTEXT.md`; when it resolves a
decision, it goes in `docs/adr/` as a proposed ADR that opens with the decisions requested (AGENTS.md "Proposals
are ADRs").

## Use the glossary's vocabulary

When your output names a domain concept (in an issue title, a refactor proposal, a hypothesis, a test name), use the term as defined in the glossary. Don't drift to synonyms the glossary explicitly avoids.

If the concept you need isn't in the glossary yet, that's a signal — either you're inventing language the project doesn't use (reconsider) or there's a real gap (note it for `/domain-modeling`).

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding:

> _Contradicts ADR-0007 (event-sourced orders) — but worth reopening because…_
