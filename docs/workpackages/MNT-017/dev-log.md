# Dev Log — MNT-017: Migrate all data scripts to JSONL

## WP Summary
- **ID**: MNT-017
- **Branch**: MNT-017/migrate-scripts-to-jsonl
- **Depends On**: MNT-015 (jsonl_utils.py), MNT-016 (data conversion script)
- **ADRs Referenced**: ADR-007 (CSV → JSONL migration)

## ADR Acknowledgement
ADR-007 (Active, 2026-04-04) mandates migration of all 7 CSV data files to JSONL and replacement of `csv_utils.py` with `jsonl_utils.py`. MNT-015 implemented `jsonl_utils.py`. MNT-016 created the conversion script. This WP (MNT-017) updates all 10 consumer scripts to use `jsonl_utils` instead of `csv_utils`.

## Implementation Summary

### Scripts Updated (10 files)
1. **scripts/add_workpackage.py** — Import changed to `jsonl_utils`, paths changed to `.jsonl`, `read_csv`/`write_csv` → `read_jsonl`/`write_jsonl`. `Linked WPs` field handled as JSON array (list after `read_jsonl()`).
2. **scripts/add_bug.py** — Import changed to `jsonl_utils`, `bugs.csv` → `bugs.jsonl`.
3. **scripts/add_test_result.py** — Import changed to `jsonl_utils`, `test-results.csv` → `test-results.jsonl`.
4. **scripts/run_tests.py** — Import changed to `jsonl_utils`, `test-results.csv` → `test-results.jsonl`.
5. **scripts/finalize_wp.py** — All imports/paths updated. `Linked WPs` in `_cascade_us_status` handled as list.
6. **scripts/validate_workspace.py** — All imports/paths updated. `_check_csv_structural()` replaced by `_check_jsonl_structural()`. `Depends On` and `Linked WPs` fields handled as lists. ADR index path updated to `.jsonl`.
7. **scripts/dedup_test_ids.py** — Import changed, `test-results.csv` → `test-results.jsonl`.
8. **scripts/archive_test_results.py** — Import changed, all three paths updated to `.jsonl`.
9. **scripts/update_bug_status.py** — Import changed, `bugs.csv` → `bugs.jsonl`.
10. **scripts/_add_wps_batch.py** — Import changed, both paths updated. `Linked WPs` handled as list.

### Script Updated (1 file — import only)
11. **scripts/update_architecture.py** — `from csv_utils import REPO_ROOT` → `from jsonl_utils import REPO_ROOT`.

### Scripts Retired (2 files deleted)
12. **scripts/_repair_csvs.py** — CSV-specific emergency repair tool. No JSONL equivalent needed (JSONL corruption is isolated per line). Deleted.
13. **scripts/_verify.py** — One-time CSV verification script. Already completed its purpose. Deleted.

### Key Design Decisions
- **List handling for nested fields**: `Depends On` and `Linked WPs` stored as JSON arrays in JSONL; `read_jsonl()` returns them as Python lists. All scripts updated to handle list values (with fallback for string values for defensive compatibility).
- **`_check_jsonl_structural()`**: Replaces `_check_csv_structural()`. Validates JSON parse integrity and status enum values against the same enum sets.
- **`strict` parameter removed**: `read_csv(path, strict=False)` calls in `_add_wps_batch.py` had no `read_jsonl` equivalent; the `strict` kwarg was dropped (JSONL is inherently strict — each line either parses as JSON or raises ValueError).

## Files Changed
- `scripts/add_workpackage.py`
- `scripts/add_bug.py`
- `scripts/add_test_result.py`
- `scripts/run_tests.py`
- `scripts/finalize_wp.py`
- `scripts/validate_workspace.py`
- `scripts/dedup_test_ids.py`
- `scripts/archive_test_results.py`
- `scripts/update_bug_status.py`
- `scripts/_add_wps_batch.py`
- `scripts/update_architecture.py`
- `scripts/_repair_csvs.py` (deleted)
- `scripts/_verify.py` (deleted)
- `docs/workpackages/workpackages.csv` (WP status update)
- `tests/MNT-017/test_mnt017_script_migration.py` (new)

## Tests Written
- `tests/MNT-017/test_mnt017_script_migration.py`
  - 30+ tests across all updated scripts
  - Import sanity checks (no `csv_utils` imports remain)
  - Path constant verification (all `.jsonl`)
  - Functional tests using temporary JSONL files for key operations
  - Deletion verification for retired scripts

## Known Limitations
- Scripts cannot be tested against real data files until MNT-018 converts the CSV files to JSONL format.
- Tests use mock JSONL files created in temp directories.
