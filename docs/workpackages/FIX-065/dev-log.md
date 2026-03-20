# FIX-065: CSV strict parsing and write-time integrity

## Developer Log

### Iteration 1

**Date:** 2026-03-20
**Assigned To:** Developer Agent
**Branch:** FIX-065/csv-strict-integrity

#### Objective

Three changes to `scripts/csv_utils.py`:
1. Make `read_csv()` strict by default — raise `ValueError` on overflow columns instead of silently merging.
2. Make `write_csv()` use atomic write-verify-rename pattern.
3. Add field-level sanitization to `write_csv()` — reject bare `\r` or `\n` in field values.

One new check in `scripts/validate_workspace.py`:
4. Add `_check_csv_structural()` for `--full` validation — parse all 4 CSVs with strict mode, validate enum values.

#### Files Changed

- `scripts/csv_utils.py` — `read_csv()` strict parameter, `write_csv()` atomic write + sanitization
- `scripts/validate_workspace.py` — `_check_csv_structural()` added to `validate_full()`
- `tests/FIX-065/test_fix065_csv_strict.py` — all unit tests

#### Implementation Notes

1. **`read_csv()` strict parameter:** Added `strict: bool = True`. When strict and overflow detected (None key in DictReader row), raises `ValueError` with row index, ID, and overflow details. When `strict=False`, preserves legacy merge behavior.

2. **`write_csv()` atomic write-verify-rename:** Scans all field values for bare `\r` or `\n` (excluding `\r\n` which csv handles). Writes to `.csv.tmp` file, re-reads with `read_csv(strict=True)` to verify row count and no overflow, then uses `os.replace()` for atomic rename. On any failure, deletes temp file and re-raises.

3. **`_check_csv_structural()` in validate_workspace.py:** Called during `--full` validation. Parses all 4 CSVs with strict mode. Validates Status enum values against defined sets (WP: Open/In Progress/Review/Done, Bug: Open/In Progress/Fixed/Verified/Closed, Test: Pass/Fail/Blocked/Skipped, US: Open/In Progress/Done/Closed).

4. All existing callers work with `strict=True` default — verified all 4 project CSVs parse cleanly.

#### Tests Written

- `tests/FIX-065/test_fix065_csv_strict.py` — 17 tests across 5 classes:
  - `TestReadCsvStrict` (4 tests): overflow raises, mentions row ID, default is strict, clean CSV passes
  - `TestReadCsvNonStrict` (2 tests): overflow merges backward compat
  - `TestWriteCsvAtomic` (3 tests): valid write, no temp file left, overwrites
  - `TestWriteCsvSanitization` (4 tests): bare newline/CR rejected, no temp on failure, error identifies field+row
  - `TestCheckCsvStructural` (4 tests): valid enums pass, invalid WP/Bug status reported, overflow CSV reported
- TST-1971: 17 passed / 0 failed
- Full regression: 4171 passed, 90 pre-existing failures (unrelated), 0 new failures
