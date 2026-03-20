# Test Report — MNT-002

**Tester:** Tester Agent
**Date:** 2026-03-20
**Iteration:** 1

## Summary

MNT-002 delivers the three required files (validation-exceptions.json, action-tracker.json, maintenance-protocol.md with Step 0). All 20 developer-written tests pass. However, a Tester-added edge-case test reveals a **schema contract violation** in action-tracker.json: the `_schema` key documents `resolved_by` as "empty if Open", but 5 Open actions carry non-empty WP-ID values in that field. This is a data/schema inconsistency that must be resolved before the WP can be marked Done.

**Verdict: FAIL — Return to Developer**

---

## Files Reviewed

| File | Status |
|------|--------|
| `docs/workpackages/validation-exceptions.json` | ✅ Created, valid schema |
| `docs/maintenance/action-tracker.json` | ⚠️ Created — schema violation (see below) |
| `docs/work-rules/maintenance-protocol.md` | ✅ Step 0 added correctly |
| `docs/workpackages/MNT-002/dev-log.md` | ✅ Exists, non-empty |
| `tests/MNT-002/` | ✅ 3 test files, 20 developer tests |
| `scripts/validate_workspace.py` | ⚠️ Not updated (deferred — see Observation 1) |

---

## Tests Executed

| TST-ID | Test | Type | Result | Notes |
|--------|------|------|--------|-------|
| TST-1968 | MNT-002 validation-exceptions.json schema | Unit | Pass | Developer run — 6/6 |
| TST-1969 | MNT-002 action-tracker.json schema | Unit | Pass | Developer run — 9/9 |
| TST-1970 | MNT-002 maintenance-protocol.md action tracker step | Unit | Pass | Developer run — 5/5 |
| TST-1971 | MNT-002 full developer test suite (Tester run) | Unit | Pass | 20/20 passed |
| TST-1972 | MNT-002 Tester edge-case test suite | Unit | **Fail** | 30 passed, 1 failed — schema violation |

---

## Findings

### FAIL: Schema Contract Violation — `resolved_by` for Open Actions (BUG-091)

**Test:** `test_mnt002_edge_cases.py::test_open_actions_resolved_by_schema_contract`

The `_schema` key in `action-tracker.json` documents the `resolved_by` field as:
> "WP-ID or commit that resolved this, **empty if Open**"

However, 5 actions with `status: "Open"` have non-empty `resolved_by` values:

| Action | Status | resolved_by |
|--------|--------|-------------|
| ACT-006 | Open | FIX-067 |
| ACT-007 | Open | FIX-067 |
| ACT-009 | Open | FIX-065 |
| ACT-010 | Open | FIX-066 |
| ACT-011 | Open | FIX-068 |

The developer's intent is clear (tracking which WP is planned to resolve each action), but the current implementation violates the documented schema. The schema description is the contract — if the data model needs to express "planned WP", that field must be in the schema too.

**Filed as:** BUG-091

---

### Observation 1: validate_workspace.py Does Not Read validation-exceptions.json

The WP acceptance criteria states: *"validate_workspace.py reads validation-exceptions.json and suppresses known-OK items."* This is **not implemented** on this branch. The developer explicitly noted in `dev-log.md`: *"Did NOT modify validate_workspace.py — that is FIX-065's scope per user instructions."*

FIX-065 (CSV strict parsing) does not cover this feature based on its description. **This acceptance criterion gap is noted but not treated as a blocking FAIL for this iteration**, given the explicit user-instruction deferral. However, when this feature is eventually implemented (whichever WP handles it), the acceptance criteria entry in `workpackages.csv` for MNT-002 should be retroactively satisfied or a new tracking entry created.

**Action required:** Clarify which WP will integrate validation-exceptions.json into validate_workspace.py.

---

## TODOs for Developer

- [ ] **Fix schema violation (REQUIRED to PASS):** Resolve the inconsistency between the `_schema` description "empty if Open" and the 5 Open actions that have WP-IDs in `resolved_by`. Choose one of:
  - **Option A:** Add a `planned_wp` field to the schema (e.g., `"planned_wp": "WP-ID planned to resolve this, empty if not yet assigned"`), clear `resolved_by` for all Open actions, move the planned WP-IDs to the new `planned_wp` field.
  - **Option B:** Update the `_schema` description for `resolved_by` to: `"WP-ID or commit that resolved this; may also contain a planned WP-ID for Open actions"`. Rename the field semantics clearly in the description.
- [ ] **Add a test for `resolved_by` consistency** (if choosing Option A): Verify Open actions have empty `resolved_by` and that Done actions have non-empty `resolved_by`.
- [ ] **Update existing developer test** `test_actions_have_required_fields` to enforce the schema contract (currently only checks field existence and type, not the "empty if Open" rule).

---

## Bugs Found

- BUG-091: `action-tracker.json: Open actions have non-empty resolved_by (schema contract violation)` — logged in `docs/bugs/bugs.csv`

---

## Verdict

**FAIL — Return WP to In Progress**

The core deliverables are correct (all three files exist with the right structure). One schema contract is violated: the `_schema` documentation says `resolved_by` is "empty if Open", but 5 Open actions have non-empty values. The fix is straightforward (2-option choice described above). All other checks pass.
