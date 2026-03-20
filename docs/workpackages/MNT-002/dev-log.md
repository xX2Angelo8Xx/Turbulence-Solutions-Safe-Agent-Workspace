# MNT-002 — Dev Log

## Workpackage
**ID:** MNT-002
**Name:** Validation exception registry and action tracker
**Status:** Review
**Assigned To:** Developer Agent

## Requirements
1. Create `docs/workpackages/validation-exceptions.json` — JSON registry of known validation exceptions.
2. Create `docs/maintenance/action-tracker.json` — JSON action tracker from maintenance logs.
3. Update `docs/work-rules/maintenance-protocol.md` — Add step 0 for action tracker review.

## Implementation Summary

### Iteration 1

**Files created:**
- `docs/workpackages/validation-exceptions.json` — Registry with INS-008 and MNT-001 initial entries.
- `docs/maintenance/action-tracker.json` — Action tracker with 11 initial actions from 2026-03-20b maintenance log.

**Files modified:**
- `docs/work-rules/maintenance-protocol.md` — Added step 0 (Action Tracker Review) before existing checklist.
- `docs/workpackages/workpackages.csv` — Set MNT-002 to In Progress.

**Tests written:**
- `tests/MNT-002/test_mnt002_validation_exceptions.py` — Validates JSON schema and content of validation-exceptions.json.
- `tests/MNT-002/test_mnt002_action_tracker.py` — Validates JSON schema and content of action-tracker.json.
- `tests/MNT-002/test_mnt002_maintenance_protocol.py` — Validates maintenance-protocol.md references action tracker at step 0.

**Decisions:**
- Did NOT modify `validate_workspace.py` — that is FIX-065's scope per user instructions.
- Used exact JSON content specified in the workpackage requirements.

---

### Iteration 2 (BUG-091 fix)

**Bug addressed:** BUG-091 — Schema contract violation in action-tracker.json

**Root cause:** The `_schema.resolved_by` description said "empty if Open", but 5 Open actions (ACT-006, ACT-007, ACT-009, ACT-010, ACT-011) had non-empty WP-ID values representing planned resolution.

**Fix chosen:** Option B — Update schema description to explicitly allow planned WP-IDs for Open actions.

**Files modified:**
- `docs/maintenance/action-tracker.json` — Updated `_schema.resolved_by` to: "WP-ID or commit that resolved this; may contain planned WP-ID while Open, must be non-empty when Done"
- `tests/MNT-002/test_mnt002_edge_cases.py` — Updated `test_open_actions_resolved_by_schema_contract` per the comment's instruction to reflect the new schema contract (schema must explicitly allow planned WP-IDs; any non-empty resolved_by on Open actions must match WP-ID/commit format)
- `docs/workpackages/workpackages.csv` — Set MNT-002 to Review

**Tests run:** TST-1973 — 31 passed, 0 failed (all MNT-002 tests)
