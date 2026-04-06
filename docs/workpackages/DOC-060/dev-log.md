# DOC-060 — Dev Log

## Workpackage
- **ID:** DOC-060
- **Name:** Document semantic_search limitation in fresh workspaces
- **Branch:** DOC-060/semantic-search-docs
- **Status:** In Progress
- **Assigned To:** Developer
- **Fixes:** BUG-196

## ADR Check
No ADRs in `docs/decisions/index.jsonl` related to documentation tooling or semantic_search. No conflicts.

## Implementation Summary

### Problem
`semantic_search` returns empty results in fresh agent-workbench workspaces because VS Code must index the workspace before semantic search can return results. This is a runtime timing issue, not a code bug. Agents may be blocked if they rely solely on `semantic_search` without being aware of this limitation.

### Changes Made

1. **`templates/agent-workbench/Project/AGENT-RULES.md`**
   - §7 Known Workarounds table already had a row for `semantic_search returns empty or stale results`.
   - Updated the row wording to explicitly call out **fresh workspaces** and **VS Code indexing delay** as the root cause.

2. **`templates/agent-workbench/.github/instructions/copilot-instructions.md`**
   - Added a new row to the *Known Tool Limitations* table documenting that `semantic_search` may return empty results in a fresh workspace before VS Code indexing completes, and pointing to `grep_search` as the fallback.

3. **`docs/bugs/bugs.jsonl`**
   - Updated BUG-196 `Fixed In WP` to `DOC-060`.

4. **`docs/workpackages/workpackages.jsonl`**
   - Set status to `In Progress`, assigned to `Developer`.

### Tests
- `tests/DOC-060/test_doc060_semantic_search_docs.py` — verifies AGENT-RULES.md and copilot-instructions.md contain the required documentation strings.

## Files Changed
- `templates/agent-workbench/Project/AGENT-RULES.md`
- `templates/agent-workbench/.github/instructions/copilot-instructions.md`
- `docs/bugs/bugs.jsonl`
- `docs/workpackages/workpackages.jsonl`
- `docs/workpackages/DOC-060/dev-log.md` (this file)
- `tests/DOC-060/test_doc060_semantic_search_docs.py`
- `templates/agent-workbench/MANIFEST.json` (regenerated)

## Known Limitations
None — documentation-only change.
