# Dev Log — DOC-038

**WP:** DOC-038 — Replace ts-code-review with agentdocs-update and safety-critical skills  
**Assigned To:** Developer Agent  
**Date Started:** 2026-03-31  
**Branch:** main (direct — no feature branch per WP instructions)

---

## Goal

Remove the obsolete `ts-code-review` skill and replace it with two new skills:
1. `agentdocs-update` — teaches proper AgentDocs entry formatting, tagging, cross-referencing, and rewrite-vs-append rules.
2. `safety-critical` — hazard identification, fail-safe defaults, input validation, no silent failures, documented assumptions, and mandatory failure-mode tests.

---

## Implementation Summary

### Files Deleted
- `templates/agent-workbench/.github/skills/ts-code-review/SKILL.md`
- `templates/agent-workbench/.github/skills/ts-code-review/` (folder)

### Files Created
- `templates/agent-workbench/.github/skills/agentdocs-update/SKILL.md`
- `templates/agent-workbench/.github/skills/safety-critical/SKILL.md`

### No code changes
This WP is a documentation/template change only. No Python source files were modified.

---

## Tests

This WP has no executable code to test. The deliverables are two SKILL.md files and a folder deletion.

Verification performed:
- `templates/agent-workbench/.github/skills/ts-code-review/` confirmed deleted
- `templates/agent-workbench/.github/skills/agentdocs-update/SKILL.md` confirmed created with valid YAML frontmatter
- `templates/agent-workbench/.github/skills/safety-critical/SKILL.md` confirmed created with valid YAML frontmatter
- Both skills reference AgentDocs documents

---

## Known Limitations

None.
