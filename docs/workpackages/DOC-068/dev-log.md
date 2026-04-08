# DOC-068 Dev Log — Clean-workspace template doc gaps for v3.4.0

## Status
In Progress → Review

## ADR Reference
- **ADR-003** (Template Manifest and Workspace Upgrade System) — this WP modifies the clean-workspace template and regenerates its MANIFEST.json, consistent with ADR-003's mandate. No supersession required.

## Implementation Summary

Closed 7 documentation gaps in `templates/clean-workspace/` only. No files in `templates/agent-workbench/` were touched.

### Change 1 — `grep_search` upgraded to Zone-checked (AGENT-RULES.md §3)
- Permission changed from `Allowed` → `Zone-checked`
- Added explicit `includePattern` targeting `NoAgentZone/**` is blocked note

### Change 2 — `file_search` upgraded to Zone-checked (AGENT-RULES.md §3)
- Permission changed from `Allowed` → `Zone-checked`
- Added explicit `query` targeting `NoAgentZone/**` is blocked note

### Change 3 — `get_changed_files` row added to §3 under new **Git Tools** header
- Status: Blocked — exposes diff content from denied zones

### Change 4 — `mcp_gitkraken_*` row added to §3 under new **MCP Tools** header
- Status: Blocked — workspace security policy; use terminal git instead

### Change 5 — §6 Known Tool Workarounds extended (3 new rows):
1. `get_changed_files` tool denied → use `git status` or `git diff --stat` via terminal
2. `file_search` broad queries silently omit `NoAgentZone/` files → always scope explicitly
3. `Get-ChildItem .` (workspace root with explicit dot) blocked → use `list_dir` tool

### Change 6 — README.md Tier 2 description fixed
- Renamed "Tier 2 — Force Ask" → "Tier 2 — Controlled Access"
- Replaced inaccurate "trigger an approval dialog" with accurate description of auto-allow silently for authorized reads, deny for writes/restricted zones

### Change 7 — MANIFEST.json regenerated
- Run: `.venv\Scripts\python.exe scripts/generate_manifest.py --template clean-workspace`
- Files tracked: 17, Security-critical: 9

## Files Changed
- `templates/clean-workspace/Project/AGENT-RULES.md`
- `templates/clean-workspace/README.md`
- `templates/clean-workspace/.github/hooks/scripts/MANIFEST.json`
- `docs/workpackages/workpackages.jsonl` (status update)
- `docs/workpackages/DOC-068/dev-log.md` (this file)
- `tests/DOC-068/test_doc068_clean_workspace_doc_gaps.py` (new tests)
- `docs/test-results/test-results.jsonl` (test run logged)

## Tests Written
See `tests/DOC-068/test_doc068_clean_workspace_doc_gaps.py`

Tests verify:
- `grep_search` shows `Zone-checked` in §3
- `file_search` shows `Zone-checked` in §3
- `get_changed_files` appears in §3 as Blocked
- `mcp_gitkraken` appears in §3 as Blocked
- `NoAgentZone` blocking note present for `grep_search`
- `NoAgentZone` blocking note present for `file_search`
- README.md does NOT contain "Force Ask"
- README.md contains "Controlled Access"
- README.md does NOT contain "trigger an approval dialog"
- README.md contains accurate auto-allow/deny description
- §6 contains `get_changed_files` workaround row
- §6 contains `file_search` silent filtering row
- §6 contains `Get-ChildItem .` workaround row

## Known Limitations
None.
