# Dev Log — MNT-011: Fix Maintenance Agent Definition

**WP ID:** MNT-011  
**Assigned To:** Developer Agent  
**Date:** 2026-04-04  
**Branch:** MNT-011/fix-maintenance-agent-definition  

---

## Summary

Three targeted fixes to `.github/agents/maintenance.agent.md`:

1. **G-04/X-01 — Stale path:** Replace `templates/coding/` with `templates/agent-workbench/` in the Constraints section.
2. **G-03/U-05 — Missing step:** Add mandatory `action-tracker.json` update step to Workflow (between step 5 "Present log" and end).
3. **C-02/X-04 — Wrong count:** Fix YAML `description` field from "9-point maintenance checklist" to "12-point maintenance checklist".

## Prior Art Check

Reviewed `docs/decisions/index.csv` (ADR-001 through ADR-006). No ADRs are related to maintenance agent workflows or agent customization files.

---

## Implementation

### Fix 1 — Stale path in Constraints
**File:** `.github/agents/maintenance.agent.md`  
**Change:** `templates/coding/` → `templates/agent-workbench/` in the last Constraints bullet point.

### Fix 2 — Add action-tracker step to Workflow
**File:** `.github/agents/maintenance.agent.md`  
**Change:** Added new step 6 between "Present the log to the user for review" (former last step 5) and end of Workflow section:
> "Update `docs/maintenance/action-tracker.json` — add all proposed actions from the maintenance log as new ACT-NNN entries with status Open. This step is mandatory per `docs/work-rules/maintenance-protocol.md`."

### Fix 3 — YAML description count
**File:** `.github/agents/maintenance.agent.md`  
**Change:** `"9-point maintenance checklist"` → `"12-point maintenance checklist"` in YAML frontmatter `description` field.

---

## Files Changed

- `.github/agents/maintenance.agent.md` — 3 targeted text fixes

---

## Tests Written

- `tests/MNT-011/test_mnt011_maintenance_agent.py` — 3 tests:
  1. Verify `templates/agent-workbench/` present, `templates/coding/` absent
  2. Verify action-tracker step present in Workflow section
  3. Verify YAML description says "12-point maintenance checklist"

---

## Known Limitations

None. All changes are textual corrections to an agent definition file.
