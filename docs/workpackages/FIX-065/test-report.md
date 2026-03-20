# Test Report — FIX-065

**Tester:** Tester Agent
**Date:** 2026-03-20
**Iteration:** 1

## Summary

FIX-065 introduces three correctness and integrity improvements to `scripts/csv_utils.py`
and one new structural validation check to `scripts/validate_workspace.py`:

1. `read_csv(strict=True)` — raises `ValueError` on overflow columns instead of silently
   merging, protecting downstream consumers from corrupt row data.
2. `write_csv()` — atomic write-verify-rename pattern using a `.csv.tmp` intermediate file
   and `os.replace()`, with on-failure temp-file cleanup.
3. `write_csv()` field sanitization — rejects bare `\r` or `\n` characters in field values
   (while allowing `\r\n` sequences that the csv module handles natively).
4. `_check_csv_structural()` in `validate_workspace.py` — called by `--full` validation to
   parse all 4 project CSVs in strict mode and report invalid Status enum values.

All acceptance criteria are met. No bugs were found. 17 developer tests + 16 tester
edge-case tests: **33/33 passed**.

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| TST-1972: Developer tests (17) — strict overflow, backward-compat, atomic write, sanitization, `_check_csv_structural` | Unit | PASS | All 17 developer tests pass |
| TST-1973: Tester edge cases (16) — `\r\n` boundary, mixed CRLF+LF, header-only, UTF-8 BOM, empty rows, unicode round-trip, `os.replace` failure cleanup, missing CSV, overflow isolation, TST/US enum warnings | Unit | PASS | All 16 tester edge cases pass |

### Edge Cases Verified by Tester

| Scenario | Expected Behaviour | Result |
|---|---|---|
| Field value = `"line1\r\nline2"` | Not rejected (`\r\n` is csv-safe) | PASS |
| Field value = `"line1\r\nline2\nextra"` | Rejected — mixed CRLF + bare `\n` | PASS |
| Field value = only `"\r\n"` | Not rejected | PASS |
| Multiple `\r\n` pairs in one value | Not rejected | PASS |
| `read_csv` on header-only CSV | Returns empty row list | PASS |
| `read_csv` on UTF-8 BOM file | BOM stripped, rows parsed correctly | PASS |
| `write_csv` with empty row list | Creates valid header-only CSV | PASS |
| `write_csv` with unicode content | Round-trips correctly via read_csv | PASS |
| `write_csv` with non-string dict values | Sanitization skips non-str, no false positive | PASS |
| `write_csv` with `os.replace` raising `OSError` | Temp file cleaned up, exception re-raised | PASS |
| `_check_csv_structural` with missing CSV file | Adds ERROR for missing file, continues checking others | PASS |
| WP CSV has overflow, others valid | Error on WP CSV only; Bug/US/TST checked independently | PASS |
| TST Status = `"PASS"` (wrong case) | Warning generated, not an error | PASS |
| US Status = `"UNKNOWN"` | Warning generated, not an error | PASS |

### Regression: Full suite scan on FIX-065 branch

- `scripts/validate_workspace.py --wp FIX-065` → **All checks passed** (exit code 0)
- Pre-existing FIX-009 failures (TST-1803A format, empty Result fields) and yaml-import
  errors in CI-related tests are not caused by FIX-065 and are unchanged.

## Security Analysis

| Vector | Assessment |
|---|---|
| CSV injection via overflow | Correctly blocked by strict mode — overflow raises before data enters consumers |
| Newline injection in field values | Bare `\n`/`\r` rejected; `\r\n` allowed (handled by csv module) |
| Temp file race condition | `os.replace()` is atomic on NTFS/ext4/APFS; temp file in same directory ensures same filesystem |
| Lock bypass via direct `write_csv()` call | By design — `write_csv` is lower-level; callers with concurrency (`append_row`, `update_cell`) hold FileLock |
| Non-string values bypassing sanitization | `isinstance(value, str)` check is intentional — non-str values coerced by DictWriter are not injection vectors |
| Enum mismatch silently accepted | Correctly reported as WARNING (non-blocking) — pre-existing data with legacy values must not fail builds |

No security issues found.

## Bugs Found

None.

## TODOs for Developer

None.

## Verdict

**PASS** — marking FIX-065 as Done.
