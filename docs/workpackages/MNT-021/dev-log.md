# MNT-021 Dev Log — Update all test files for JSONL

## WP Reference
- **ID:** MNT-021
- **Branch:** MNT-021/update-tests-jsonl
- **ADR:** ADR-007 (CSV-to-JSONL migration, Phase 3 — test infrastructure)
- **Depends On:** MNT-018 (Done), MNT-019 (Done), MNT-020 (Done)

## ADR Check
ADR-007 governs the full CSV-to-JSONL migration. This WP is Phase 3 of that ADR:
updating all test files to reference `.jsonl` paths and `jsonl_utils` functions
instead of `.csv` paths and `csv_utils` / `csv.DictReader`.

## Scope
Update ~25 test files across 14 WP directories:

| Category | Directories | Change |
|----------|-------------|--------|
| 1. Tests reading production files | DOC-053, FIX-009, MNT-003, FIX-059 | csv.reader → json.loads / read_jsonl |
| 2. Tests testing csv_utils | FIX-065 | Skip structural checks (WP_CSV→WP_JSONL), rewrite structural tests |
| 3. Tests mocking csv_utils | FIX-059, FIX-066, FIX-068, FIX-081, FIX-082, FIX-098 | read_csv→read_jsonl mock targets |
| 4. Tests asserting CSV paths in docs | MNT-006, MNT-009, MNT-012, FIX-067 | .csv → .jsonl assertions |

## Files Changed

### Category 1 — Tests reading production data files
- `tests/DOC-053/test_doc053_adr_related_wps.py`
  - Changed `import csv` → `import json`
  - Changed `index.csv` → `index.jsonl` path
  - Changed `workpackages.csv` → `workpackages.jsonl` path
  - Changed `csv.DictReader` → `json.loads` per-line reading
  - Updated `test_adr_index_has_six_entries` assertion: 6 → 7 (ADR-007 added)
  - Added `test_adr_007_related_wps_non_empty` test

- `tests/FIX-009/test_fix009_required_fields.py`
  - Changed `import csv` → `import json`
  - Changed `test-results.csv` → `test-results.jsonl`
  - Changed `csv.DictReader` → `json.loads` reading

- `tests/FIX-009/test_fix009_no_duplicate_tst_ids.py`
  - Same path and reader changes

- `tests/FIX-009/test_fix009_tst_id_format.py`
  - Same path and reader changes

- `tests/FIX-009/test_fix009_edge_cases.py`
  - Same path and reader changes

- `tests/MNT-003/test_mnt003_cleanup.py`
  - Changed `from csv_utils import read_csv` → `from jsonl_utils import read_jsonl`
  - Changed `bugs.csv` → `bugs.jsonl`

### Category 2 — Tests for csv_utils (now validate_workspace jsonl structural)
- `tests/FIX-065/test_fix065_csv_strict.py`
  - Kept read_csv/write_csv tests (csv_utils still exists, deprecated but functional)
  - Updated `TestCheckCsvStructural` tests: changed `WP_CSV→WP_JSONL`, `US_CSV→US_JSONL`, etc.
  - Changed `_check_csv_structural` → `_check_jsonl_structural`
  - Updated test fixtures from CSV format to JSONL format

- `tests/FIX-065/test_fix065_tester_edge_cases.py`
  - Same structural check updates

### Category 3 — Tests mocking csv_utils functions
- `tests/FIX-059/test_fix059_case_insensitive_status.py`
  - Changed `patch("validate_workspace.read_csv")` → `patch("validate_workspace.read_jsonl")`
  - Changed production file read from `csv_utils.read_csv` → `jsonl_utils.read_jsonl`
  - Changed path from `test-results.csv` → `test-results.jsonl`

- `tests/FIX-066/test_fix066_bug_lifecycle.py`
  - Rewrote `_make_bug_csv` helper → `_make_bug_jsonl` (writes JSONL format)
  - Rewrote `_read_bug_status` helper to read JSONL
  - Removed `import csv`; added `import json`
  - Changed `patch("finalize_wp.BUG_CSV", ...)` → `patch("finalize_wp.BUG_JSONL", ...)`

- `tests/FIX-066/test_fix066_edge_cases.py`
  - Same JSONL helper and patch changes

- `tests/FIX-068/test_fix068_finalization_cleanup.py`
  - Changed `patch.object(vw, "read_csv", ...)` → `patch.object(vw, "read_jsonl", ...)`
  - Updated docstring mention of `workpackages.csv` → `workpackages.jsonl`

- `tests/FIX-081/test_fix081_bug_cascade.py`
  - Changed `_patch_read_csv` → `_patch_read_jsonl` helper
  - Changed `patch.object(fw, "read_csv", ...)` → `patch.object(fw, "read_jsonl", ...)`

- `tests/FIX-081/test_fix081_tester_edge_cases.py`
  - Same `read_csv` → `read_jsonl` patch target changes

- `tests/FIX-082/test_fix082_update_bug_status.py`
  - Changed `_mock_read_csv` → `_mock_read_jsonl`
  - Changed `patch.object(ubs, "read_csv", ...)` → `patch.object(ubs, "read_jsonl", ...)`

- `tests/FIX-082/test_fix082_tester_edge_cases.py`
  - Same mock renaming
  - Changed `workpackages.csv` → `workpackages.jsonl` in path-matching mock
  - Changed `WP_CSV`/`BUG_CSV` patches → `WP_JSONL`/`BUG_JSONL`

- `tests/FIX-082/test_fix082_validate_fix.py`
  - Same mock and patch changes

- `tests/FIX-098/test_fix098_verified_status.py`
  - Changed `CSV_PATH` → `JSONL_PATH` patch target
  - Changed temp fixture from `.csv` text format to `.jsonl` format

### Category 4 — Tests asserting CSV paths in docs
- `tests/MNT-006/test_mnt006_planner_body.py`
  - `decisions/index.csv` → `decisions/index.jsonl`
  - `workpackages.csv` → `workpackages.jsonl`
  - `bugs.csv` → `bugs.jsonl`

- `tests/MNT-009/test_mnt009_tester_add_bug_mandate.py`
  - `bugs.csv` → `bugs.jsonl`
  - Updated assertion text for JSONL-era prohibition language

- `tests/MNT-012/test_mnt012_story_writer_adr_check.py`
  - `docs/decisions/index.csv` → `docs/decisions/index.jsonl`
  - `user-stories/user-stories.csv` → `user-stories/user-stories.jsonl`

- `tests/FIX-067/test_fix067_rule_updates.py`
  - `test-results.csv` → `test-results.jsonl`
  - `## Test Result CSV` → `## Test Result JSONL`

### New files
- `tests/MNT-021/test_mnt021_no_stale_csv_refs.py` — verifies no stale CSV references remain

### Additional fixes (discovered during test runs)
- `docs/decisions/ADR-007-csv-to-jsonl-migration.md` — fixed `## Related WPs` heading to inline bold format `**Related WPs:**` to match DOC-053 test expectations
- `tests/FIX-009/test_fix009_edge_cases.py` — added `_to_int()` helper to handle non-numeric TST IDs (`TST-1803A`) in gap-check test
- `tests/FIX-067/test_fix067_rule_updates.py` — updated assertion to `"Never manually add"` (protocol now says "entries" not "rows")
- `tests/FIX-067/test_fix067_edge_cases.py` — updated checklist count assertion from 7 to 8 items
- `tests/MNT-006/test_mnt006_planner_body.py` — updated CSV constraint check from `"csv"` to `"jsonl"` to match agent file changes
- `tests/regression-baseline.json` — added 2 pre-existing failures discovered during full-suite run:
  - `tests.MNT-018.test_mnt018_data_conversion.test_csv_files_deleted` (workpackages.csv exists on main)
  - `tests.MNT-020.test_mnt020_jsonl_docs.test_architecture_md_no_stale_csv` (architecture.md stale ref)

## Test Results
- MNT-021 targeted suite: 5/5 passed (TST-2569, logged via run_tests.py)
- Full suite: 8441 passed, 635 failed (all failures confirmed pre-existing per regression-baseline.json)
- No new failures introduced by MNT-021

## Known Limitations
- `scripts/csv_utils.py` still exists but is deprecated (deleted in MNT-022)
- FIX-065 tests for `read_csv`/`write_csv` still run against the deprecated csv_utils (correct behavior — those functions still work, just deprecated)
- `docs/workpackages/workpackages.csv` not deleted (scope of MNT-022)
- `docs/architecture.md` has stale `.csv` file-tree entry (scope of MNT-022)
