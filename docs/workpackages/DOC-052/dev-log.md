# DOC-052 Dev Log — Add generate_manifest.py to Mandatory Scripts

**WP ID:** DOC-052  
**Branch:** DOC-052/add-generate-manifest-to-mandatory-scripts  
**Status:** In Progress  
**Assigned To:** Developer Agent  
**Date Started:** 2026-04-04

---

## ADR Acknowledgment

**ADR-003** ("Template Manifest and Workspace Upgrade System") is directly relevant to this WP:
- ADR-003 establishes that `scripts/generate_manifest.py` must be run before releases to regenerate `MANIFEST.json`.
- This WP enforces that requirement at the workflow level by adding it to the Mandatory Script Usage table and the developer pre-handoff checklist.

The WP description also references **M-03/ADR-04**. The WP formalises ADR-003's requirement in the agent workflow documentation.

---

## Implementation Summary

Two documentation files were modified to add `generate_manifest.py` to the mandatory workflow:

1. **`docs/work-rules/agent-workflow.md`** — Added a new row to the Mandatory Script Usage table:
   - Operation: `Regenerate template manifest`
   - Script: `scripts/generate_manifest.py`
   - Who: `Developer`
   - Trigger: before committing any changes to template files in `templates/agent-workbench/`

2. **`.github/agents/developer.agent.md`** — Added a new checklist item to the Pre-Handoff Checklist:
   - Conditional check: if template files in `templates/agent-workbench/` were modified, run `scripts/generate_manifest.py` to regenerate `MANIFEST.json`

---

## Files Changed

- `docs/work-rules/agent-workflow.md` — Added `generate_manifest.py` row to Mandatory Script Usage table
- `.github/agents/developer.agent.md` — Added pre-handoff checklist item for template manifest
- `docs/workpackages/workpackages.csv` — Status updated to In Progress / Review

---

## Tests Written

- `tests/DOC-052/test_doc052_mandatory_scripts.py` — Verifies:
  1. `generate_manifest.py` row is present in `agent-workflow.md` Mandatory Script Usage table
  2. `developer.agent.md` pre-handoff checklist contains the `generate_manifest.py` item
  3. `scripts/generate_manifest.py` exists in the repository

---

## Decisions Made

- Placed the new row after the "Update bug status" row, before the "Update regression baseline" row, to keep the mandatory script entries sorted by operational area.
- The checklist item in `developer.agent.md` is conditional (prefixed with "If template files ... were modified") matching the pattern of the existing FIX-xxx conditional checklist item.

---

## Known Limitations

None. This is a pure documentation change.
