# Test Report — SAF-022

**Tester:** Tester Agent  
**Date:** 2026-03-17  
**Iteration:** 1  

---

## Summary

SAF-022 adds `"**/NoAgentZone": true` to both `files.exclude` and `search.exclude`
in both VS Code settings files, re-runs `update_hashes.py` to embed the new SHA256
hash in both `security_gate.py` files, and keeps all four files byte-for-byte in
sync.

All developer requirements were verified: both settings.json files contain the
exclusion in both sections, both files are byte-identical, both security_gate.py
files embed the correct hash for their respective (identical) settings.json, and the
hash self-check (`_KNOWN_GOOD_GATE_HASH`) is also correct.

The full test suite produced **2880 passed, 1 pre-existing failure (INS-005 /
BUG-045), 29 skipped** — identical to the pre-SAF-022 baseline. No regressions were
introduced.

16 Tester edge-case tests were added in `tests/SAF-022/test_saf022_edge_cases.py`;
all 16 pass. Combined SAF-022 total: **34 tests, 34 passed**.

---

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| 18 developer tests — `test_saf022_noagentzone_exclude.py` | Security / Integration / Regression | PASS | All 18 pass |
| TST-1421 test_bare_key_absent_from_files_exclude [Default-Project] | Security | PASS | Bare key without `**/` absent |
| TST-1422 test_bare_key_absent_from_files_exclude [templates/coding] | Security | PASS | Bare key without `**/` absent |
| TST-1423 test_bare_key_absent_from_search_exclude [Default-Project] | Security | PASS | Bare key without `**/` absent |
| TST-1424 test_bare_key_absent_from_search_exclude [templates/coding] | Security | PASS | Bare key without `**/` absent |
| TST-1425 test_files_and_search_exclude_have_same_keys [Default-Project] | Integration | PASS | files.exclude and search.exclude key sets identical |
| TST-1426 test_files_and_search_exclude_have_same_keys [templates/coding] | Integration | PASS | files.exclude and search.exclude key sets identical |
| TST-1427 test_all_files_exclude_values_are_bool_true [Default-Project] | Security | PASS | All values strict Python bool True |
| TST-1428 test_all_files_exclude_values_are_bool_true [templates/coding] | Security | PASS | All values strict Python bool True |
| TST-1429 test_all_search_exclude_values_are_bool_true [Default-Project] | Security | PASS | All values strict Python bool True |
| TST-1430 test_all_search_exclude_values_are_bool_true [templates/coding] | Security | PASS | All values strict Python bool True |
| TST-1431 test_no_utf8_bom [Default-Project] | Security | PASS | No BOM — hash would break if BOM present |
| TST-1432 test_no_utf8_bom [templates/coding] | Security | PASS | No BOM |
| TST-1433 test_no_whitespace_in_key_files_exclude [Default-Project] | Security | PASS | Key is exactly `**/NoAgentZone`, no padding |
| TST-1434 test_no_whitespace_in_key_files_exclude [templates/coding] | Security | PASS | Key is exactly `**/NoAgentZone`, no padding |
| TST-1435 test_no_whitespace_in_key_search_exclude [Default-Project] | Security | PASS | Key is exactly `**/NoAgentZone`, no padding |
| TST-1436 test_no_whitespace_in_key_search_exclude [templates/coding] | Security | PASS | Key is exactly `**/NoAgentZone`, no padding |
| TST-1437 SAF-022 Tester — 34-test suite (18 dev + 16 edge-case) | Security | PASS | 34/34 pass |
| TST-1438 SAF-022 Tester — full regression suite | Regression | PASS | 2880 passed / 1 pre-existing INS-005 / 29 skipped |

---

## Edge Cases Added by Tester

**File:** `tests/SAF-022/test_saf022_edge_cases.py` (16 tests)

| Class | Coverage |
|-------|----------|
| `TestNoBareNoAgentZoneKey` | Bare `NoAgentZone` (no `**/`) must NOT appear in either section for either file |
| `TestExcludeSectionConsistency` | `files.exclude` and `search.exclude` must share the exact same key set |
| `TestExcludeValueTypes` | All values in both sections must be strict JSON `true` (Python `bool`, not string or int) |
| `TestNoBOM` | settings.json must not start with a UTF-8 BOM (would silently corrupt the SHA256 hash) |
| `TestExactKeyString` | The NoAgentZone key must be exactly `**/NoAgentZone` with no leading/trailing whitespace |

---

## Bugs Found

None.

---

## TODOs for Developer

None.

---

## Verdict

**PASS — mark WP as Done.**

All requirements are met:
- `"**/NoAgentZone": true` is present in both `files.exclude` and `search.exclude` in both settings files.
- Both settings.json files are byte-identical.
- Both security_gate.py files embed the correct `_KNOWN_GOOD_SETTINGS_HASH` and `_KNOWN_GOOD_GATE_HASH`.
- Both security_gate.py files are byte-identical.
- Full test suite: 2880 passed, no new failures.
- 34 SAF-022 tests all pass, including 16 Tester edge-case additions.
