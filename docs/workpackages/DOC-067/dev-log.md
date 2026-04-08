# DOC-067 — Dev Log

**WP:** DOC-067  
**Name:** Agent-workbench template doc gaps for v3.4.0  
**Branch:** DOC-067/agent-workbench-doc-gaps  
**Agent:** Developer Agent  
**Started:** 2026-04-08  

---

## ADR Check

- **ADR-003** (Template Manifest and Workspace Upgrade System) — directly relevant. This WP regenerates MANIFEST.json for the agent-workbench template. ADR-003 mandates that `generate_manifest.py` is run after any template file changes. Acknowledged and followed.
- No other ADRs conflict with this WP's scope.

---

## Scope

Three documentation gaps in `templates/agent-workbench/` only. No `templates/clean-workspace/` files touched.

1. Add `mcp_gitkraken_*` row to Tool Permission Matrix (AGENT-RULES.md §3)  
2. Fix README.md Tier 2 description — replace "Force Ask" / "trigger an approval dialog" wording  
3. Add `Get-ChildItem .` workaround to §7 Known Workarounds  
4. Regenerate MANIFEST.json  

---

## Implementation

### Change 1 — AGENT-RULES.md §3 mcp_gitkraken_* row

Added a new `**MCP Tools**` section header and `mcp_gitkraken_*` blocked row after the `get_changed_files` row in the Tool Permission Matrix.

### Change 2 — AGENT-RULES.md §7 Get-ChildItem . workaround

Added a new row after the existing `Get-ChildItem` excessive output row documenting that `Get-ChildItem .` (explicit dot) is blocked and the approved workaround is `list_dir` at workspace root.

### Change 3 — README.md Tier 2 description

Replaced "**Tier 2 — Force Ask**" with "**Tier 2 — Controlled Access**" and replaced the description "Operations outside `{{PROJECT_NAME}}/` trigger an approval dialog" with accurate wording describing silent auto-allow for authorized reads vs. denial for writes/restricted zones.

### Change 4 — MANIFEST.json regenerated

Ran `scripts/generate_manifest.py` after all template edits.

---

## Files Changed

- `templates/agent-workbench/Project/AgentDocs/AGENT-RULES.md`
- `templates/agent-workbench/README.md`
- `templates/agent-workbench/.github/hooks/scripts/MANIFEST.json`
- `docs/workpackages/workpackages.jsonl`
- `docs/workpackages/DOC-067/dev-log.md` (this file)
- `tests/DOC-067/test_doc067_agent_workbench_doc_gaps.py`

---

## Tests Written

- `tests/DOC-067/test_doc067_agent_workbench_doc_gaps.py` — 5 tests:
  1. `mcp_gitkraken` appears in AGENT-RULES.md
  2. README.md does NOT contain "Force Ask"
  3. README.md does NOT contain "trigger an approval dialog"
  4. README.md contains the corrected Tier 2 wording ("Controlled Access")
  5. `Get-ChildItem .` appears in §7 Known Workarounds

---

## Test Results

All 5 tests passed. See test-results.jsonl for the logged record.

---

## Known Limitations

None.
