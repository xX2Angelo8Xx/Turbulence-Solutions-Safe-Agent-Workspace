# Dev Log — FIX-107: Fix JSONL migration test assertions

**Agent:** Developer Agent  
**Date:** 2026-04-04  
**Branch:** FIX-107/jsonl-migration-tests  

---

## ADR Acknowledgement

**ADR-007** ("Migrate from CSV to JSONL for All Data Files") is directly relevant. It covers MNT-014 through MNT-023 and defines the new JSONL-based data structures. This WP fixes test drift caused by that migration.

---

## Prior Art Check

- ADR-007 is Active. Related WPs: MNT-014 through MNT-023. No supersession required.
- Regression baseline had 2 known failures for this domain (both being fixed here).

---

## Analysis

Running `python -m pytest tests/MNT-014 ... tests/MNT-023 -v` revealed exactly **2 failures**:

### Failure 1: `tests/MNT-017/test_mnt017_script_migration.py::test_check_jsonl_structural_passes_valid_data`

The test created a user-story JSONL record with field `"Name"` but `validate_workspace._check_jsonl_structural` now requires `"Title"` as a mandatory field for US rows (line 268 of `validate_workspace.py`).

**Fix:** Changed `{"ID": "US-001", "Status": "Open", "Name": "T"}` → `{"ID": "US-001", "Status": "Open", "Title": "T"}`.

### Failure 2: `tests/MNT-021/test_mnt021_tester_edge_cases.py::test_no_functional_csv_file_paths_in_tests`

The test scans all test files for quoted CSV production file paths. It correctly excludes `ALLOWED_DIRS` but `MNT-022` (the CSV retirement WP) was not in `ALLOWED_DIRS`. `test_mnt022_csv_retire.py` legitimately references `workpackages.csv` and `index.csv` to verify those files were removed.

**Fix:** Added `"MNT-022"` to `ALLOWED_DIRS` in `test_mnt021_tester_edge_cases.py`.

---

## Files Changed

- `tests/MNT-017/test_mnt017_script_migration.py` — fixed US JSONL field from `Name` to `Title`
- `tests/MNT-021/test_mnt021_tester_edge_cases.py` — added `"MNT-022"` to `ALLOWED_DIRS`
- `docs/workpackages/workpackages.jsonl` — status updated
- `tests/regression-baseline.json` — removed 2 fixed entries

---

## Test Results

All 281 tests in MNT-014 through MNT-023 pass after fixes.

---

## Regression Baseline

Removed the following entries from `tests/regression-baseline.json`:
- `tests.MNT-017.test_mnt017_script_migration.test_check_jsonl_structural_passes_valid_data`
- `tests.MNT-021.test_mnt021_tester_edge_cases.test_no_functional_csv_file_paths_in_tests`
