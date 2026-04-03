# Dev Log — SAF-076: Golden-File Snapshot Infrastructure

**WP ID:** SAF-076  
**Status:** In Progress  
**Assigned To:** Developer Agent  
**Date:** 2026-04-03  

---

## ADR Check

Checked `docs/decisions/index.csv`. No ADRs directly related to snapshot testing infrastructure.
ADR-004 (Adopt ADRs) establishes the decision-record practice that motivates keeping snapshot
tests well-documented. No conflicts; no supersession needed.

---

## Prior Art

`tests/snapshots/security_gate/` already exists with:
- `test_snapshots.py` — auto-discovers all `*.json` files in its directory and runs parametrized tests.
- `conftest.py` — patches `zone_classifier.detect_project_folder()` for fake workspace roots.
- `README.md` — explains the security_gate-specific snapshot format.
- 10 snapshot `.json` files (5 allow, 5 deny).

The existing `test_snapshots.py` already satisfies the auto-discovery requirement for the
`security_gate` sub-directory. The WP deliverables are:
1. `tests/snapshots/README.md` — top-level README covering the whole snapshot system.
2. Updated `developer.agent.md` — reference the README in the snapshot checklist item.
3. Updated `tester.agent.md` — reference the README in the Regression Check step.

---

## Implementation

### Files Created
- `tests/snapshots/README.md` — new top-level README documenting format, run, update, and
  regression-vs-intentional-change guidance.

### Files Modified
- `.github/agents/developer.agent.md` — Pre-Handoff Checklist snapshot item now links
  `tests/snapshots/README.md`.
- `.github/agents/tester.agent.md` — Regression Check step now links `tests/snapshots/README.md`
  and shows the exact `pytest` command.

---

## Tests Written

`tests/SAF-076/test_saf076_snapshot_infra.py` — 7 unit tests:
1. `test_top_level_readme_exists` — `tests/snapshots/README.md` exists.
2. `test_readme_contains_run_section` — README documents how to run snapshot tests.
3. `test_readme_contains_update_section` — README documents how to update snapshots.
4. `test_readme_contains_format_section` — README describes the JSON format.
5. `test_readme_contains_regression_guidance` — README explains when a failure is a regression.
6. `test_snapshot_test_file_exists` — `tests/snapshots/security_gate/test_snapshots.py` exists.
7. `test_snapshot_files_are_valid_json` — All `*.json` in `tests/snapshots/security_gate/` are
   valid JSON with required fields.

All 7 tests pass.

---

## Known Limitations

- The current snapshot infrastructure only covers `security_gate`. When additional components
  are added in the future, new sub-directories should be created under `tests/snapshots/`
  following the same pattern. The top-level README documents this pattern.
