# Dev Log — DOC-017

**Developer:** Developer Agent
**Date started:** 2026-03-25
**Iteration:** 1

## Objective
Update all documentation files to reflect the template rename from `templates/coding/` to `templates/agent-workbench/` and from `templates/creative-marketing/` to `templates/certification-pipeline/`. No stale references to the old names should remain.

## Implementation Summary
Searched all documentation, work-rules, and the repo-level copilot-instructions.md for references to `templates/coding/`, `creative-marketing/`, `Coding` (as a template type name), and related stale terminology. Updated each occurrence to reflect the new names:
- `templates/coding/` → `templates/agent-workbench/`
- `templates/creative-marketing/` (and `templates/creative/`) → `templates/certification-pipeline/`
- Template display names updated from "Coding" / "Creative / Marketing" to "Agent Workbench" / "Certification Pipeline"

## Files Changed
- `docs/architecture.md` — Updated Templates section: `coding/` → `agent-workbench/`, `creative-marketing/` → `certification-pipeline/`
- `docs/project-scope.md` — Updated Templates table: display names and folder paths
- `docs/work-rules/agent-workflow.md` — Updated restricted zone mention of `templates/coding/` → `templates/agent-workbench/`
- `docs/work-rules/index.md` — Updated key file reference `templates/coding/` → `templates/agent-workbench/`
- `docs/work-rules/maintenance-protocol.md` — Updated checklist item `templates/coding/` → `templates/agent-workbench/`
- `docs/work-rules/security-rules.md` — Updated restricted zones section `templates/coding/` → `templates/agent-workbench/`
- `.github/instructions/copilot-instructions.md` — Updated both references to `templates/coding/` → `templates/agent-workbench/`

## Tests Written
- `tests/DOC-017/test_doc017_template_rename.py` — Scans all documentation files for stale references to old template names; verifies new names are present in expected locations.

## Known Limitations
- Historical references inside per-WP dev-logs and test-reports in `docs/workpackages/` are intentionally left as-is (they are historical records, not live documentation).
- Security Audit files under `docs/Security Audits/` reference old names in a historical context — these are audit snapshots and are not updated.
