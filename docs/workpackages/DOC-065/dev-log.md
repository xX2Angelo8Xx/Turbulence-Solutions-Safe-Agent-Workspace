# DOC-065 Dev Log — Batch template documentation fixes for v3.4.0

## Status
In Progress → Review

## ADR Acknowledgement
- ADR-003 (Template Manifest and Workspace Upgrade System) is relevant — this WP modifies template files and regenerates MANIFEST.json for both templates, consistent with ADR-003's mandate.

## Summary
Five documentation gaps closed across both agent-workbench and clean-workspace templates:

1. **Remove `isBackground:true` from Blocked Commands** — agent-workbench AGENT-RULES only
2. **Fix grep_search docs** — AGENT-RULES S3 updated in both templates; `includePattern` is required, not auto-scoped
3. **Document terminal navigation lock-in** — AGENT-RULES S4 and copilot-instructions Known Tool Limitations in both templates
4. **Add `includeIgnoredFiles:true` restriction** — AGENT-RULES Known Tool Workarounds in clean-workspace; already in S3 of agent-workbench
5. **Clarify list_dir scope for .github/** — AGENT-RULES S3 in both templates; top-level listing denied, subdirectories allowed

## Files Changed
- `templates/agent-workbench/Project/AgentDocs/AGENT-RULES.md`
- `templates/clean-workspace/Project/AGENT-RULES.md`
- `templates/agent-workbench/.github/instructions/copilot-instructions.md`
- `templates/clean-workspace/.github/instructions/copilot-instructions.md`
- `templates/agent-workbench/MANIFEST.json` (regenerated)
- `templates/clean-workspace/MANIFEST.json` (regenerated)

## Tests Written
- `tests/DOC-065/test_doc065_template_docs.py` — validates all 5 documentation changes in both templates

## Implementation Notes
- Change (1) is agent-workbench ONLY — `isBackground:true` block row removed from Blocked Commands table
- Change (2): clean-workspace grep_search/file_search rows previously said "Scoped to default" which incorrectly implied auto-scoping; corrected to require explicit `includePattern`
- Change (3): Added to agent-workbench AGENT-RULES S4 Blocked Commands table + both copilot-instructions Known Tool Limitations tables; for clean-workspace added to Section 4 Security Rules
- Change (4): Added to clean-workspace AGENT-RULES S6 Known Tool Workarounds table
- Change (5): Clarified list_dir notes in both AGENT-RULES S3 Tool Permission Matrix tables
