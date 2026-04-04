# Test Report — MNT-016: Create CSV-to-JSONL Conversion Script

**Tester:** Tester Agent  
**Date:** 2026-04-04  
**Verdict:** PASS

---

## Summary

| Metric | Value |
|--------|-------|
| Developer tests | 26 (all pass) |
| Tester edge-case tests | 17 |
| Total tests | 43 |
| Failures | 0 |
| Regressions | 0 |
| Bugs filed | 0 |
| Test result IDs | TST-2552 (regression run), TST-2553 (targeted suite) |

---

## Code Review

### `scripts/migrate_csv_to_jsonl.py`

**Design correctness:**
- `_MIGRATIONS` list correctly enumerates all 7 CSV/JSONL path pairs with `required` flag.
- `_ARRAY_FIELDS` uses a `dict[tuple, None]` as a constant-time lookup set — correct and efficient.
- `_split_array_field()` handles empty strings, whitespace-only values, trailing commas, and leading/trailing whitespace on individual items.
- `_convert_row()` correctly restricts array conversion to matching `(stem, column)` keys — non-nested fields in any file are unaffected.
- `_convert_one()` uses `write_jsonl()` (which performs atomic temp-file rename internally) then re-reads and verifies row count parity via `read_jsonl()`.
- `main()` collects `csvs_to_delete` and only calls `unlink()` for all CSVs **after** all conversions succeed — correct atomicity at the batch level.
- Missing required CSV triggers immediate exit code 1.
- Missing optional `archived-test-results.csv` is gracefully skipped (SKIP message printed, loop continues).
- `--dry-run` flag propagates through to `_convert_one()` which reports without writing.
- Repo root is derived from `Path(__file__).resolve().parent.parent` — relative, not absolute. Compliant with security-rules.md.

**Security:**
- No user-controlled inputs reach file paths. `_MIGRATIONS` is a hardcoded constant.
- No `eval()` / `exec()` usage.
- `unlink()` is only called on paths from the hardcoded `_MIGRATIONS` table.
- Verified path traversal in CSV *content* is harmless: content is serialized to JSON strings or split into lists, never interpreted as file system paths.

**Edge cases verified (tester-added):**
- Partial failure when the 3rd file fails: all 6 original CSVs in `csvs_to_delete` are NOT deleted. ✓
- JSONL files written before the error still exist (expected; re-runnable). ✓
- Unicode content (German umlauts, Japanese, accented characters) preserved through JSON roundtrip. ✓
- Commas inside quoted fields in non-nested columns stay as strings, never split. ✓
- Pre-existing JSONL file is cleanly overwritten (not appended to). ✓
- Mixed rows (some empty `Depends On`, some populated): empty → `[]`, populated → list. ✓
- Single-element nested field becomes a one-element list, not a bare string. ✓
- Whitespace-only items between commas are filtered from array output. ✓
- All lines in JSONL output parse as valid JSON objects. ✓
- Dry-run prints row count; no JSONL file is created. ✓

---

## Test Execution

### Developer Tests (26 tests)
```
tests/MNT-016/test_mnt016_migrate_csv_to_jsonl.py  — 26 passed
```

### Tester Edge-Case Tests (17 tests)
```
tests/MNT-016/test_mnt016_tester_edge_cases.py  — 17 passed
```

### Full Regression Suite
Logged as TST-2552. Exit code 1 due to 635 pre-existing failures, all accounted for in `tests/regression-baseline.json` (baseline count: 684). No new failures introduced by MNT-016. Zero regressions confirmed.

---

## ADR Check

ADR-007 (Migrate from CSV to JSONL) drives this WP. The script is Phase 1 (create the tool). No conflict with any active ADRs. Dev-log acknowledges ADR-007 correctly.

---

## Known Observations (Non-Blocking)

1. **Partial failure leaves earlier JSONL files on disk.** If conversion fails partway through, already-written JSONL files remain while their source CSVs are preserved. This is acceptable — the script can be re-run and will overwrite the JSONL files. The WP description says "CSV deletion only after ALL conversions succeed" which is fully implemented.

2. **Script is not idempotent once CSVs are deleted.** Re-running after a successful conversion will fail because the CSVs no longer exist (required ones will trigger exit 1). This is documented in `dev-log.md` as a known limitation and is expected for a one-time migration tool.

---

## Verdict

**PASS** — All 43 tests pass. Implementation meets all WP requirements. No security issues found. No regressions. No bugs to file.
