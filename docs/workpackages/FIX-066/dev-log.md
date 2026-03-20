# FIX-066: Bug lifecycle automation in finalization

## Dev Log

### Iteration 1

**Date:** 2026-03-20
**Status:** In Progress

#### Requirements
1. Enhance `_cascade_bug_status()` in `scripts/finalize_wp.py` to scan dev-log.md and test-report.md for `BUG-\d{3}` references and auto-close unlinked Open/In Progress bugs.
2. Add `_check_bug_linkage()` to `scripts/validate_workspace.py` for `--wp` validation — warn about bugs referenced in dev-log/test-report but missing `Fixed In WP`.
3. Bug status enum validation — already covered by FIX-065's `_check_csv_structural()` function. Skipping to avoid duplication.

#### Plan
- Modify `_cascade_bug_status()` in finalize_wp.py to add document-scanning logic after existing loop
- Add `_check_bug_linkage()` to validate_workspace.py and call it from `validate_wp()`
- Create tests in `tests/FIX-066/`

#### Files Changed
- `scripts/finalize_wp.py` — enhanced `_cascade_bug_status()` with Phase 2: scans dev-log.md and test-report.md for BUG-NNN references and auto-closes Open/In Progress bugs
- `scripts/validate_workspace.py` — added `_check_bug_linkage()` for --wp validation; added `_check_bug_status_enum()` for --full validation (FIX-065's `_check_csv_structural` was not merged to main)
- `tests/FIX-066/test_fix066_bug_lifecycle.py` — 16 tests across 3 classes
- `docs/workpackages/FIX-066/dev-log.md` — this file

#### Implementation Summary
1. **`_cascade_bug_status()` enhancement**: Added Phase 2 after existing Phase 1. Scans `docs/workpackages/<wp_id>/dev-log.md` and `test-report.md` for `BUG-\d{3}` regex matches. For each discovered bug that is Open or In Progress: auto-populates `Fixed In WP` (if empty) and sets Status to Closed. Respects dry-run mode. Skips Closed/Verified bugs. Handles missing files gracefully.
2. **`_check_bug_linkage()`**: New validator in validate_workspace.py called during `--wp` validation. Scans dev-log/test-report for BUG-NNN references and warns if `Fixed In WP` doesn't match the WP-ID.
3. **`_check_bug_status_enum()`**: New validator for `--full` validation. Checks all bugs in bugs.csv have a valid Status (Open, In Progress, Fixed, Verified, Closed). Note: FIX-065's `_check_csv_structural()` was not present on main, so this was needed.

#### Tests Written
- `TestCascadeBugStatusDocScanning` (9 tests): auto-close from dev-log, from test-report, In Progress bugs, skip Closed, skip Verified, dry-run, preserve Fixed In WP, handle missing files, Phase 1 still works
- `TestCheckBugLinkage` (5 tests): warns unlinked, no warning when linked, no warning when no refs, warns from test-report, handles missing files
- `TestBugStatusEnum` (2 tests): catches invalid status, valid statuses pass

#### Decisions
- FIX-065's `_check_csv_structural()` was not found on main branch. Added standalone `_check_bug_status_enum()` for bug-specific validation.
- Phase 2 re-reads bugs.csv after Phase 1 to get updated status values.
- `already_closed` set prevents double-processing bugs hit by both Phase 1 and Phase 2.
