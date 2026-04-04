# Dev Log — MNT-015: Create jsonl_utils.py core library

## Status
In Progress

## Agent
Developer Agent

## ADRs Referenced
- **ADR-007** (CSV-to-JSONL migration): Directly implements Phase 1 of ADR-007. This WP creates the foundation library (`jsonl_utils.py`) that all subsequent migration WPs depend on.

## Implementation Plan

1. Create `scripts/jsonl_utils.py` with identical public interface to `csv_utils.py`
2. Copy `FileLock` class verbatim from `csv_utils.py`
3. Implement `read_jsonl`, `write_jsonl`, `append_row`, `update_cell`, `locked_next_id_and_append`, `next_id`
4. Write unit tests in `tests/MNT-015/`

## Files Changed

- `scripts/jsonl_utils.py` — new file, JSONL utility library
- `tests/MNT-015/test_mnt015_jsonl_utils.py` — new file, unit tests
- `docs/workpackages/workpackages.csv` — status updated to In Progress / Review
- `docs/workpackages/MNT-015/dev-log.md` — this file

## Implementation Summary

Created `scripts/jsonl_utils.py` as a standalone JSONL utility module. Key design decisions:

- `FileLock` copied verbatim from `csv_utils.py` — no changes
- `read_jsonl` extracts fieldnames from the first row's keys; validates expected fields if provided
- `write_jsonl` uses atomic write-verify-rename pattern (same as `write_csv`)
- `append_row` signature adapted: takes `(path, fieldnames, row)` matching workpackage spec
- `update_cell` signature unchanged from csv_utils
- `locked_next_id_and_append` uses `zero_pad=3` default (matching workpackage spec)
- `next_id` uses `zero_pad=3` default (matching workpackage spec)
- All JSON written with `ensure_ascii=False`, UTF-8 encoding
- Empty lines skipped during read

## Tests Written

- `test_read_empty_file` — read an empty JSONL file
- `test_read_single_row` — read one-row JSONL
- `test_read_multiple_rows` — read multi-row JSONL, verify fieldnames
- `test_read_skips_blank_lines` — blank lines between records are ignored
- `test_read_expected_fields_valid` — expected_fields validation passes
- `test_read_expected_fields_missing` — expected_fields raises ValueError on missing field
- `test_write_creates_file` — write creates file with correct content
- `test_write_atomic_no_partial_on_failure` — failed write does not leave partial file
- `test_write_field_order_follows_fieldnames` — JSON key order follows fieldnames list
- `test_append_row_to_existing` — append adds row to existing file
- `test_append_row_duplicate_id` — duplicate ID raises ValueError
- `test_update_cell_existing_row` — update_cell changes correct cell
- `test_update_cell_missing_id` — update_cell raises KeyError for unknown ID
- `test_update_cell_missing_column` — update_cell raises KeyError for unknown column
- `test_next_id_empty` — next_id on empty file returns prefix-001
- `test_next_id_existing` — next_id skips existing IDs
- `test_locked_next_id_and_append` — atomic ID assignment and append
- `test_filelock_timeout` — lock timeout raises TimeoutError
- `test_filelock_stale_removal` — stale lock file is cleaned up automatically

## Known Limitations

None. This is a self-contained utility library with no external dependencies beyond stdlib.

## Iteration History

(none yet)
