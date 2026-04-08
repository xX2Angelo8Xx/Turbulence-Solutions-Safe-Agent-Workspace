# DOC-066 Dev Log — Fix persistent documentation inversions

**WP ID:** DOC-066  
**Branch:** DOC-066/fix-doc-inversions  
**User Story:** US-082  
**Status:** In Progress  
**Date started:** 2026-04-08  

---

## ADR Check

Reviewed `docs/decisions/index.jsonl`. No ADRs directly related to navigation documentation, isBackground runtime behavior, or grep_search/file_search guidance. No conflicts found.

---

## Objective

Fix three persistent documentation inversion issues in both `agent-workbench` and `clean-workspace` templates:

1. **Change 1:** Remove `isBackground:true` from Known Tool Limitations — the tool functions correctly at runtime (confirmed across 3 audit iterations).
2. **Change 2:** Update navigation wording from "outward navigation blocked" to "above workspace root blocked" — SAF-079 merged, navigation within workspace root is now allowed.
3. **Change 3:** Separate `file_search` from `grep_search` guidance — `grep_search` requires `includePattern`; `file_search` uses glob patterns in the `query` parameter.

---

## Files Changed

### Change 1 — Remove `isBackground:true` row
- `templates/agent-workbench/.github/instructions/copilot-instructions.md`
- `templates/clean-workspace/.github/instructions/copilot-instructions.md`
- `templates/clean-workspace/Project/AGENT-RULES.md` (Section 6 Known Tool Workarounds)

### Change 2 — Update navigation wording
- `templates/agent-workbench/.github/instructions/copilot-instructions.md`
- `templates/clean-workspace/.github/instructions/copilot-instructions.md`
- `templates/agent-workbench/Project/AgentDocs/AGENT-RULES.md` (Blocked Commands table)
- `templates/clean-workspace/Project/AGENT-RULES.md` (Security Rules section 4, item 5)

### Change 3 — Separate file_search from grep_search guidance
- `templates/agent-workbench/Project/AgentDocs/AGENT-RULES.md` (Known Workarounds — add clarifying note)
- `templates/clean-workspace/Project/AGENT-RULES.md` (Tool Permission Matrix — fix file_search row)

### MANIFEST regeneration
- `templates/agent-workbench/MANIFEST.json`
- `templates/clean-workspace/MANIFEST.json`

---

## Implementation Notes

- Navigation wording updated: "outward navigation" → "above workspace root" to reflect that `cd` within workspace subdirectories is allowed.
- `isBackground:true` row removed: The Known Workarounds table in agent-workbench AGENT-RULES.md Section 7 already positively references `isBackground=true` (Long-running commands) — no replacement needed.
- `file_search` clarification added: `file_search` uses the `query` parameter as a glob pattern, not `includePattern`. This is explicitly noted.

---

## Tests Written

- `tests/DOC-066/test_doc066_doc_inversions.py`

Test coverage:
- `isBackground:true` NOT in copilot-instructions.md (both templates)
- Navigation wording mentions "above workspace root" not just "outward navigation"
- `file_search` not conflated with `grep_search` `includePattern` requirement in AGENT-RULES.md
- MANIFEST.json files are valid JSON

---

## Iteration History

### Iteration 1 (2026-04-08)
Initial implementation. All changes applied. Tests written and passing.
