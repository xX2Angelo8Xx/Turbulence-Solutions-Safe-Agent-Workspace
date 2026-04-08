---
name: agentdocs-update
description: "How to write, update, and cross-reference AgentDocs entries consistently. Load this skill before writing to any AgentDocs document."
---

# AgentDocs Update Skill

Follow these rules when writing to any document in `AgentDocs/`.

## Entry Format

Every entry you add or modify must include:

1. **Agent tag and date** — Start with `> Updated by: [AgentName] | [YYYY-MM-DD]`
2. **One topic per entry** — Do not combine unrelated changes in a single section.
3. **Plain language** — Write for a developer who has no context. Avoid jargon without explanation.

## Update vs Append

| Situation | Action |
|-----------|--------|
| Section exists and is still accurate | Update it in place with new information |
| Section exists but is now wrong | **Rewrite** the section — do not add a contradicting paragraph below |
| Topic is entirely new | Append a new section using the document's template format |
| Section is obsolete | Delete it. Dead documentation is worse than missing documentation |

## Cross-Referencing

When a change in one document affects another, add a brief cross-reference:

- `decisions.md` → reference the question in `open-questions.md` if it resolves one (e.g., "Resolves Q-003")
- `architecture.md` → reference the decision that drove the change (e.g., "See DEC-005")
- `research-log.md` → reference which decision or question prompted the research
- `progress.md` → no cross-references needed; keep it clean and scannable

## Staleness Check

Before writing, **read the existing content** of the document you are about to update. If you find stale or contradictory information already there, fix it as part of your update. Do not leave known-stale content behind.

## What Not to Do

- Do not create new files in `AgentDocs/` unless the user explicitly asks.
- Do not use bullet-point dumps as entries. Write structured prose or use the document's template.
- Do not duplicate information that already exists in another AgentDocs document.
- Do not leave placeholder text (e.g., "TBD", "TODO") in entries you write — either fill it in or leave the section out.
