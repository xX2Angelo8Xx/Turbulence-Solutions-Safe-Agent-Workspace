# Test Report — MNT-015

**Tester:** Tester Agent
**Date:** 2026-04-04
**Iteration:** 1

## Summary

MNT-015 delivers `scripts/jsonl_utils.py` — the JSONL foundation library for ADR-007 Phase 1. The implementation is correct, complete, and secure. All 32 developer tests pass, and 22 additional tester edge-case tests were written and pass. The full regression suite shows no new failures attributable to this WP (635 failures, all present in the `_count: 684` baseline).

## API Completeness Check

| Symbol | Present | Notes |
|--------|---------|-------|
| `REPO_ROOT` | ✅ | `Path(__file__).resolve().parent.parent` — correct |
| `FileLock` | ✅ | Verbatim copy from `csv_utils.py`, confirmed line-by-line |
| `read_jsonl` | ✅ | Returns `(fieldnames, rows)`, handles blank lines, validates expected_fields |
| `write_jsonl` | ✅ | Atomic write-verify-rename, UTF-8 no BOM |
| `append_row` | ✅ | Duplicate-ID check, fills missing fields, file-locked |
| `update_cell` | ✅ | Locked, KeyError on missing ID or column |
| `locked_next_id_and_append` | ✅ | Single lock covers read-compute-write cycle |
| `next_id` | ✅ | Unlocked read-only helper, documented warning |

## FileLock Parity Verification

`FileLock` in `jsonl_utils.py` is byte-for-byte identical to `csv_utils.py`:
- `os.O_CREAT | os.O_EXCL | os.O_WRONLY` atomic lock acquisition ✅
- PID written to lock file ✅
- `_STALE_THRESHOLD = 300.0` ✅
- Stale lock auto-removal with `continue` on retry ✅
- `TimeoutError` on timeout with actionable message ✅
- `__exit__` silently ignores `FileNotFoundError` ✅

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| TST-2548 — Developer: 32 unit tests | Unit | Pass | Logged by Developer |
| TST-2549 — Tester: MNT-015 targeted suite (54 tests) | Unit | Pass | `run_tests.py` |
| TST-2550 — Full regression suite | Regression | Fail* | *All 635 failures pre-existing in baseline |

## Edge Cases Added (22 tests in `test_mnt015_tester_edge_cases.py`)

**read_jsonl:**
- CRLF line endings handled transparently (`splitlines()` covers this)
- UTF-8 BOM raises `ValueError` — correct, spec says no BOM; `read_text("utf-8")` does not strip BOM unlike `utf-8-sig`
- Whitespace-only lines (spaces, tabs) correctly skipped
- `expected_fields` validates against first-row keys only — documented behavior
- Special characters (`<script>`, `&`, `"`, `\`) survive round-trip intact

**write_jsonl:**
- No BOM written — confirmed via `read_bytes()` check
- `.tmp` cleanup on `os.replace` failure — verified via `patch("os.replace")`
- Embedded newlines in values are JSON-escaped, not raw line breaks
- Extra row keys not in `fieldnames` are appended after declared fields

**append_row:**
- `FileNotFoundError` on missing file — callers must pre-create the file
- Empty-string ID allowed on a fresh file; duplicate empty-string ID blocked correctly

**update_cell:**
- Only the first matching row is updated when duplicate IDs exist (malformed data resilience)

**next_id:**
- Malformed IDs (`TST-abc`, `TST-`, `TST`) are silently ignored
- Custom `id_column` parameter works correctly
- Numbers larger than `zero_pad` width (e.g., `TST-9999` → `TST-10000`) do not overflow

**locked_next_id_and_append:**
- `row_template` dict is mutated in-place — callers should be aware of this side effect
- `FileNotFoundError` on missing file
- **Concurrency test (10 threads):** 10 concurrent calls produce 10 unique sequential IDs — FileLock is effective under real thread concurrency on NTFS

**FileLock:**
- Lock file contains owner PID as plain string
- Lock files younger than `_STALE_THRESHOLD` are NOT auto-removed (timeout instead)
- Re-entrant acquisition on the same thread causes `TimeoutError` (not reentrant — expected)

## Bugs Found

None.

## Security Assessment

- No `eval()` or dynamic code execution
- No external process spawning
- No logging of sensitive data
- `ensure_ascii=False` is correct for UTF-8 JSONL (special chars are JSON-encoded, not raw)
- No path traversal protection at the library level — this is appropriate; jsonl_utils is an internal library and callers are responsible for path validation per project security-rules.md rule 4
- `os.O_CREAT | os.O_EXCL` is truly atomic on NTFS/ext4/APFS — correct implementation

## Known Limitations Documented

1. **`read_jsonl` rejects BOM files** — any JSONL file written outside this library with a BOM will fail. This is correct per spec but should be noted in downstream migration WPs.
2. **`expected_fields` checks first row's keys only** — if field schema is inconsistent across rows, the check may miss missing fields in later rows. Acceptable for this project's use case.
3. **`row_template` is mutated by `locked_next_id_and_append`** — callers that reuse templates must copy before passing.
4. **`append_row` / `locked_next_id_and_append` require the file to pre-exist** — callers must create an empty file before first use.

## Verdict

**PASS** — Mark WP as Done.

All acceptance criteria met:
- `jsonl_utils.py` exists with all 8 public symbols ✅
- Unit tests pass for `read`, `write`, `append`, `update`, `lock`, `next_id` ✅
- FileLock copied verbatim from `csv_utils.py` ✅
- Atomic write-verify-rename implemented ✅
- JSONL format is one JSON object per line, UTF-8, no BOM ✅
- No new regressions introduced ✅
