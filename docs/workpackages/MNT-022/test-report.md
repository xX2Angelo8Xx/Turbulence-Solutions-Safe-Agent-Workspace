# Test Report — MNT-022: Retire csv_utils.py and verify clean state

**Tester:** Tester Agent  
**Date:** 2026-04-04  
**Branch:** MNT-022/retire-csv-utils  
**Verdict:** PASS

---

## Summary

MNT-022 is the Phase 3 (final) WP in the ADR-007 CSV-to-JSONL migration series. All deliverables were implemented correctly. The scope decision to retain `csv_utils.py` and `migrate_csv_to_jsonl.py` is valid and well-documented. No regressions were introduced.

---

## Reviews

### Code Review

| File | Assessment |
|------|-----------|
| `docs/decisions/index.csv` | Correctly deleted — data preserved in `index.jsonl` |
| `docs/workpackages/workpackages.csv` | Correctly deleted — data preserved in `workpackages.jsonl` |
| `scripts/add_bug.py` (docstring) | Updated: "bugs.csv" → "bugs.jsonl" ✓ |
| `scripts/add_test_result.py` (docstring) | Updated: "test-results.csv" → "test-results.jsonl" ✓ |
| `scripts/add_workpackage.py` (docstring) | Updated: "workpackages.csv" → "workpackages.jsonl" ✓ |
| `scripts/archive_test_results.py` (docstring) | Updated CSV → JSONL throughout ✓ |
| `scripts/dedup_test_ids.py` (docstring) | Updated: "test-results.csv" → "test-results.jsonl" ✓ |
| `scripts/run_tests.py` (docstring) | Updated: "test-results.csv" → "test-results.jsonl" ✓ |
| `scripts/update_bug_status.py` (docstring) | Updated: "bugs.csv" → "bugs.jsonl" (2 occurrences) ✓ |
| `.github/prompts/status-report.prompt.md` | 4 data source paths updated to .jsonl ✓ |
| `scripts/README.md` | csv_utils section replaced with jsonl_utils; deprecation note added ✓ |
| `docs/architecture.md` | Regenerated via update_architecture.py; deleted CSV files absent ✓ |
| `tests/regression-baseline.json` | Count: 686 → 684; 2 entries correctly removed ✓ |

### Scope Decision Validation

The retention of `csv_utils.py` and `migrate_csv_to_jsonl.py` is correct per `coding-standards.md`:
- `tests/FIX-065/` (33 tests) permanently import `from csv_utils import read_csv, write_csv` — these 33 tests pass ✓
- `tests/MNT-016/` (43 tests) permanently import from `migrate_csv_to_jsonl` — these 43 tests pass ✓
- Both files are documented as legacy infrastructure in `scripts/README.md` ✓

### ADR Review

- **ADR-007** (Status: Active) — MNT-022 is the designated Phase 3 WP. No conflict. All changes align with the stated goal: zero stale .csv references in operational data files and documentation.

---

## Test Execution

### MNT-022 Targeted Suite (8 Developer + 4 Tester tests)

| Test | Result |
|------|--------|
| `test_workpackages_csv_deleted` | PASS |
| `test_decisions_index_csv_deleted` | PASS |
| `test_status_report_prompt_no_csv_paths` | PASS |
| `test_status_report_prompt_uses_jsonl` | PASS |
| `test_operational_scripts_no_stale_csv_in_docstrings` | PASS |
| `test_no_non_exempt_script_imports_csv_utils` | PASS |
| `test_readme_documents_jsonl_utils` | PASS |
| `test_readme_no_csv_utils_active_section` | PASS |
| `test_csv_utils_retained_for_legacy_tests` (Tester) | PASS |
| `test_migrate_csv_to_jsonl_retained_for_legacy_tests` (Tester) | PASS |
| `test_architecture_md_no_stale_csv_data_files` (Tester) | PASS |
| `test_readme_has_legacy_deprecation_note` (Tester) | PASS |

**Result: 12 passed, 0 failed** (TST-2573)

### Baseline Validation Tests

Both entries removed from the regression baseline now pass:

| Test | Result |
|------|--------|
| `tests/MNT-018/test_mnt018_data_conversion.py::test_csv_files_deleted` | PASS ✓ |
| `tests/MNT-020/test_mnt020_jsonl_docs.py::test_architecture_md_no_stale_csv` | PASS ✓ |

### Legacy Infrastructure Tests

| Suite | Result |
|-------|--------|
| `tests/FIX-065/` — 33 tests importing csv_utils | 33 PASS ✓ |
| `tests/MNT-016/` — 43 tests importing migrate_csv_to_jsonl | 43 PASS ✓ |
| Combined FIX-065 + MNT-016 | **76 passed** ✓ |

### Full Regression Check

- **Total failures:** 634 failed + 50 errors = **684**
- **Baseline count:** 684
- **New failures:** 0
- **Result: PASS** (TST-2574)

### Workspace Validation

`scripts/validate_workspace.py --wp MNT-022` → **All checks passed** (exit code 0)

---

## Edge Case Analysis

### Covered in Additional Tests

1. **csv_utils.py retention** — verified it still exists (prevents accidental future deletion)
2. **migrate_csv_to_jsonl.py retention** — verified it still exists
3. **architecture.md cleanliness** — verified workpackages.csv and index.csv absent from tree
4. **README legacy note** — verified deprecation context is present

### Minor Finding (Non-Blocking)

`.github/prompts/status-report.prompt.md` line 45 contains the table cell text "Count from CSV" (a description artifact in the KPI template table). This is not a data file path reference and does not affect actual file reads. The 4 data source file paths on lines 14-17 are all correctly updated to `.jsonl`. Finding classified as cosmetic/documentation debt, not a functional defect.

---

## Security Review

- No executable logic changed — changes are limited to file deletions, docstrings, and documentation.
- No secrets, credentials, or dynamic code execution introduced.
- No path traversal risks in test files.
- OWASP Top 10 not applicable to this documentation/cleanup WP.

---

## Pre-Done Checklist

- [x] `docs/workpackages/MNT-022/dev-log.md` exists and is non-empty
- [x] `docs/workpackages/MNT-022/test-report.md` written by Tester
- [x] Test files exist in `tests/MNT-022/` with 12 tests (8 Developer + 4 Tester)
- [x] Test results logged via `scripts/add_test_result.py` (TST-2572, TST-2573, TST-2574)
- [x] No bugs found requiring logging
- [x] `scripts/validate_workspace.py --wp MNT-022` returns clean (exit code 0)
- [x] All changes staged with `git add -A`
- [x] Commit: `MNT-022: Tester PASS`
- [x] Push: `git push origin MNT-022/retire-csv-utils`

---

## Verdict: PASS
