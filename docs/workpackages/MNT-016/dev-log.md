# Dev Log — MNT-016: Create CSV-to-JSONL Conversion Script

## Status
Review

## Agent
Developer Agent

## Date
2026-04-04

## ADR Acknowledgement
ADR-007 (Migrate from CSV to JSONL for All Data Files) is the direct driver for
this WP. This script is Phase 1 of the migration: produce the one-time conversion
tool. The existing `csv_utils.py` is NOT deleted here — that happens in MNT-022.

---

## Plan

Create `scripts/migrate_csv_to_jsonl.py` that:
1. Reads each of the 7 CSV files via `csv_utils.read_csv()`
2. Converts nested comma-separated fields to JSON arrays
3. Writes each output via `jsonl_utils.write_jsonl()`
4. Verifies row counts match after writing
5. Deletes original CSV files on success (skipped in `--dry-run` mode)
6. Reports a summary

Nested field conversion:
- `workpackages.csv`: `Depends On` column
- `user-stories.csv`: `Linked WPs` column
- `decisions/index.csv`: `Related WPs` column

`archived-test-results.csv` is optional — handled gracefully if missing.

---

## Implementation

### Files Created
- `scripts/migrate_csv_to_jsonl.py` — the migration script
- `tests/MNT-016/test_mnt016_migrate_csv_to_jsonl.py` — unit tests

---

## Tests Written

| Test | Description |
|------|-------------|
| `test_dry_run_does_not_write` | Confirms `--dry-run` produces no JSONL files and no CSV deletion |
| `test_nested_depends_on_conversion` | Verifies `Depends On` CSV field becomes a JSON array |
| `test_nested_linked_wps_conversion` | Verifies `Linked WPs` CSV field becomes a JSON array |
| `test_nested_related_wps_conversion` | Verifies `Related WPs` CSV field becomes a JSON array |
| `test_empty_nested_field_becomes_empty_array` | Empty comma-separated fields → `[]` |
| `test_row_count_parity` | JSONL row count matches CSV row count after conversion |
| `test_csv_deleted_after_success` | Original CSVs are removed after successful conversion |
| `test_optional_archived_file_missing_is_ok` | Missing archived-test-results.csv does not abort |
| `test_optional_archived_file_present_is_converted` | If archive file exists, it is converted |
| `test_output_path_derivation` | .csv → .jsonl path logic is correct |
| `test_non_nested_fields_remain_strings` | Fields without array conversion stay as strings |
| `test_row_count_mismatch_exits_with_error` | Simulated row count mismatch triggers exit 1 |

---

## Known Limitations
- This script is a one-time migration tool; it is not idempotent.
- If a JSONL file already exists it is overwritten (write_jsonl uses atomic rename).

## Test Results
- 26 tests written and all 26 pass
- Logged as TST-2551 via `run_tests.py`
- `validate_workspace.py --wp MNT-016` → All checks passed

---

## Decisions Made
- Used `csv_utils.read_csv()` and `jsonl_utils.write_jsonl()` as specified.
- Row count verification re-reads the written JSONL via `jsonl_utils.read_jsonl()`.
- Script exits with code 1 on any failure, leaving all files untouched.
