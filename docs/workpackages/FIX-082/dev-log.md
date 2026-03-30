# Dev Log — FIX-082: Add update_bug_status.py and validate --fix flag

**WP ID:** FIX-082  
**Branch:** FIX-082/tooling-fix-flag  
**Assigned To:** Developer Agent  
**Date:** 2026-03-30

---

## Summary

Implemented three related tooling improvements to close maintenance workflow gaps:

1. **`scripts/update_bug_status.py`** — new CLI tool for atomic bug status updates
2. **`--fix` flag on `validate_workspace.py`** — auto-cleans orphaned state files and closes Fixed bugs
3. **`validation-exceptions.json` wired into `validate_workspace.py`** — replaces hardcoded exemptions

---

## Task 1: `scripts/update_bug_status.py`

**File created:** `scripts/update_bug_status.py`

- Accepts positional `bug_id` argument and `--status` argument
- Validates status against: `Closed`, `Fixed`, `In Progress`, `Open`
- Uses `csv_utils.update_cell()` for atomic, file-locked writes to `docs/bugs/bugs.csv`
- Prints `BUG-111: Fixed → Closed` on success
- Exits with code 1 and message to stderr if bug not found or argparse rejects invalid status
- Follows patterns from `add_bug.py`

---

## Task 2: `--fix` flag on `validate_workspace.py`

**File modified:** `scripts/validate_workspace.py`

Added `apply_fixes()` function and `--fix` argument to `main()`:

- `--fix` with `--wp`: prints error to stderr, exits 1
- `--fix` without `--wp` (requires `--full`): calls `apply_fixes()` then runs validation
- `apply_fixes()` Fix 1: deletes `.finalization-state.json` for Done WPs
- `apply_fixes()` Fix 2: sets `Fixed` bugs to `Closed` when their `Fixed In WP` WP is Done
- Prints `Applied N fix(es).` summary

---

## Task 3: `validation-exceptions.json` wired in

**File modified:** `scripts/validate_workspace.py`

- Removed `EXEMPT_PREFIXES_TEST_REPORT = {"MNT-"}` hardcoded constant
- Added `EXCEPTIONS_JSON` path constant pointing to `docs/workpackages/validation-exceptions.json`
- Added `_load_exceptions()` function that reads and parses the JSON (returns `{}` on any error)
- Updated `_check_wp_artifacts()` to accept optional `exceptions` dict; skips `test-report.md` check if `"test-report"` in `skip_checks`, skips test-folder check if `"test-folder"` in `skip_checks`
- Updated `_check_tst_coverage()` to accept optional `exceptions` dict; skips WPs with `"test-report"` or `"test-folder"` in `skip_checks`
- Both `validate_full()` and `validate_wp()` now load exceptions and pass them down
- Backward compatible: `INS-008` and `MNT-001` already in the JSON file continue to be exempt

---

## Files Changed

- `scripts/update_bug_status.py` — new file
- `scripts/validate_workspace.py` — modified
- `tests/FIX-082/test_fix082_update_bug_status.py` — new file (8 tests)
- `tests/FIX-082/test_fix082_validate_fix.py` — new file (11 tests)
- `tests/FIX-082/__init__.py` — new file
- `docs/workpackages/workpackages.csv` — status set to In Progress
- `docs/test-results/test-results.csv` — TST-2291 logged

---

## Tests Written

**`tests/FIX-082/test_fix082_update_bug_status.py`** (8 tests):
- `test_changes_status_from_fixed_to_closed`
- `test_prints_before_after_message`
- `test_rejects_invalid_status`
- `test_errors_on_nonexistent_bug_id`
- `test_accepts_status_open`
- `test_accepts_status_in_progress`
- `test_accepts_status_fixed`
- `test_accepts_status_closed`

**`tests/FIX-082/test_fix082_validate_fix.py`** (11 tests):
- `test_deletes_orphaned_state_file_for_done_wp`
- `test_closes_fixed_bug_with_done_wp`
- `test_skips_open_bug_that_is_not_fixed`
- `test_noop_when_no_orphans_or_fixed_bugs`
- `test_fix_and_wp_together_produces_error`
- `test_exceptions_json_is_loaded`
- `test_exceptions_json_missing_returns_empty`
- `test_exceptions_json_invalid_json_returns_empty`
- `test_wp_in_exceptions_skips_test_report_check`
- `test_wp_in_exceptions_skips_test_folder_check`
- `test_wp_not_in_exceptions_does_require_test_artifacts`

**Result:** 19 passed, 0 failed (TST-2291)

---

## Known Limitations

- `validation-exceptions.json` now requires per-WP entries for maintenance WPs (no prefix-glob). New MNT- WPs must be individually added.
- `apply_fixes()` Fix 2 processes bugs sequentially; each `update_cell()` call holds the file lock briefly. This is safe but not batched.
