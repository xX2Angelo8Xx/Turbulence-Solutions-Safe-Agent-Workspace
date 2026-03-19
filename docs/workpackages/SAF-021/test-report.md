# Test Report — SAF-021: Wildcard Bypass Regression Tests

**WP ID:** SAF-021  
**Tester:** Tester Agent  
**Date:** 2026-03-17  
**Verdict:** ✅ PASS  

---

## 1. Review Summary

The Developer delivered a test-only workpackage targeting the critical wildcard
bypass vectors from the security audit. No production code was modified. The work
product is `tests/SAF-021/test_saf021_wildcard_regression.py` (58 tests) plus a
supporting `tests/SAF-021/conftest.py` that patches `detect_project_folder` for
the fake `c:/workspace` root used in the tests.

### Code Review Findings

| Area | Finding |
|------|---------|
| Coverage of 10 audit vectors | ✅ All 10 explicitly covered with dedicated test classes |
| Bracket wildcard bypass (BUG-051) | ✅ Covered in `TestBracketWildcardBypass` |
| Globstar (`**`) bypass | ✅ Covered in `TestDoubleStarBypass` |
| CMD-style patterns | ✅ Covered in `TestCmdExeWildcardPatterns` |
| conftest.py isolation | ✅ Correct pattern — mirrors SAF-020 conftest |
| Tests are deterministic | ✅ No real I/O; fake workspace root; no external state |
| Helper function unit tests | ✅ `_wildcard_prefix_matches_deny_zone` called directly |

---

## 2. Audit Vector Coverage Matrix

| # | Audit Vector | Test Class | Tests | Status |
|---|-------------|-----------|-------|--------|
| 1 | `Get-ChildItem .g*` | `TestAuditVector1_GetChildItemDotGStar` | 4 | ✅ All pass |
| 2 | `Get-ChildItem N*` | `TestAuditVector2_GetChildItemNStar` | 4 | ✅ All pass |
| 3 | `Get-ChildItem .v*` | `TestAuditVector3_GetChildItemDotVStar` | 3 | ✅ All pass |
| 4 | `Get-ChildItem .g* \| Get-Content` | `TestAuditVector4_PipedWildcardCommands` | 4 | ✅ All pass |
| 5 | `Get-ChildItem .g* -Force -Recurse -Name` | `TestAuditVector5_WildcardWithFlags` | 4 | ✅ All pass |
| 6 | `ls .g*` | `TestAuditVector6_LsDotGStar` | 4 | ✅ All pass |
| 7 | `cat N*/*` | `TestAuditVector7_CatNStarSlash` | 4 | ✅ All pass |
| 8 | Wildcards targeting project folder — allowed | `TestAuditVector8_ProjectFolderAllowed` | 6 | ✅ All pass |
| 9 | `dir .g*` | `TestAuditVector9_DirDotGStar` | 4 | ✅ All pass |
| 10 | Path traversal + wildcard (`../../.g*`, `./.g*`) | `TestAuditVector10_PathTraversalCombinations` | 6 | ✅ All pass |
| Extra | Bracket wildcards `[.g]*`, `[Nn]*`, `[.v]*` | `TestBracketWildcardBypass` | 6 | ✅ All pass |
| Extra | Globstar `**` at root vs inside Project/ | `TestDoubleStarBypass` | 6 | ✅ All pass |
| Extra | CMD-style `dir .g*`, `dir N*`, `dir .v*` | `TestCmdExeWildcardPatterns` | 3 | ✅ All pass |

**Developer total: 58 tests — all pass.**

---

## 3. Tester Edge-Case Analysis

### 3.1 Reasoning about gaps

While reviewing the test suite, the following creative bypass categories were
identified as absent from the Developer's tests:

1. **Question mark (`?`) wildcard** — the `?` shell wildcard replaces exactly
   one character. `.githu?` expands to `.github`, `N?` has prefix `n` which
   matches `noagentzone`. SAF-020 explicitly triggers on `?` in tokens (line
   1171 of security_gate.py), but no `?`-specific tests existed in the suite.

2. **Windows CMD-style flag before wildcard** (`dir /b .g*`, `dir /s N*`) —
   the dev-log mentioned `dir /b .g*` but the three CMD tests only covered
   `dir .g*`, `dir N*`, `dir .v*` (no flag). The `/b` flag starts with `/`
   (not `-`), so it does NOT set `_prev_was_flag = True`. The wildcard in the
   next token is therefore still checked — verified by test.

3. **Chained commands with wildcard in a later segment** — a rogue agent
   could prepend an innocuous command (`echo ok; ls .g*`) to hide the
   dangerous wildcard in the second segment. The security gate splits on `;`,
   `&&`, `||` and evaluates each independently, so this must be denied.

4. **Allowlisted read commands (`Get-Content`, `Select-String`, `gc`) with
   wildcard paths** — these commands are in the allowlist with
   `path_args_restricted=True` (from SAF-014). A wildcard targeting a deny
   zone in their path arguments must still be denied.

### 3.2 Edge-case test classes added

| Class | Tests | Rationale |
|-------|-------|-----------|
| `TestCmdExeWildcardPatterns` (extended) | +3 (`dir /b`, `dir /s`, `dir /b .v*`) | Dev-log mentioned but omitted flag variants |
| `TestQuestionMarkWildcard` | 9 | `?` wildcard entirely absent from Developer suite |
| `TestChainedCommandsWithWildcard` | 5 | Single-segment assumption; chained attack not tested |
| `TestAllowlistedReadCommandsWithWildcard` | 5 | `gc`/`Get-Content`/`Select-String` wildcard paths untested |

**Tester additions: 22 tests — all pass.**

---

## 4. Test Runs

| TST-ID | Description | Result |
|--------|------------|--------|
| TST-1399 | Developer SAF-021 suite (58 tests) | ✅ 58 passed |
| TST-1400 | Developer full regression suite | ✅ 2840 passed / 1 pre-existing / 29 skipped |
| TST-1401 | Tester SAF-021 suite with additions (80 tests) | ✅ 80 passed |
| TST-1402 | Tester full regression suite | ✅ 2862 passed / 1 pre-existing / 29 skipped |

Pre-existing failure: `tests/INS-005/test_ins005_edge_cases.py::TestShortcutsAndUninstaller::test_uninstall_delete_type_is_filesandirs` — tracked as BUG-045 (`filesandordirs` vs `filesandirs`). Pre-dates this WP, not introduced by SAF-021.

---

## 5. Security Analysis

Attack vectors systematically considered:

| Category | Verdict |
|----------|---------|
| `*` at root level targeting all three deny zone prefixes | ✅ Blocked |
| `?` single-char wildcard targeting deny zone name endings | ✅ Blocked |
| `[...]` bracket wildcard (BUG-051) | ✅ Blocked |
| `**` globstar at root | ✅ Blocked (empty prefix matches every zone) |
| Windows `/b` flag before wildcard | ✅ Blocked (flag uses `/`, not `-`, so `_prev_was_flag` stays False) |
| Chained commands (`;`, `&&`) with wildcard in later segment | ✅ Blocked (each segment evaluated independently) |
| Wildcard in allowlisted read commands (`gc`, `Get-Content`) | ✅ Blocked (path_args_restricted=True applies wildcard check) |
| Wildcards safely inside `Project/` parent | ✅ Allowed (safe parent directory entered before wildcard) |
| Path traversal + wildcard (`../../.g*`) | ✅ Blocked (`..` and `.` treated as transparent) |

No bypass vectors were found. All 10 audit vectors have regression tests.

---

## 6. Pre-Done Checklist

- [x] `docs/workpackages/SAF-021/dev-log.md` exists and is non-empty
- [x] `docs/workpackages/SAF-021/test-report.md` written (this file)
- [x] Test files exist in `tests/SAF-021/` (3 files + \_\_pycache\_\_)
- [x] All test runs logged in `docs/test-results/test-results.csv` (TST-1399 – TST-1402)
- [x] No production code modified — test-only WP

---

## 7. Verdict

**PASS** — All 10 audit vectors are covered by passing regression tests. 22
additional edge-case tests were added by the Tester (question mark wildcards,
Windows flag variants, chained commands, allowlisted read commands with wildcard
paths). The full suite (2862 tests) passes with zero new regressions.  WP
SAF-021 is approved for Done.
