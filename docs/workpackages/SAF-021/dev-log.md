# Dev Log — SAF-021: Wildcard Bypass Regression Tests

**WP ID:** SAF-021  
**Branch:** SAF-021/wildcard-regression-tests  
**Developer:** Developer Agent  
**Date Started:** 2026-03-17  

---

## Summary

This is a test-only workpackage. No changes were made to `security_gate.py` or any
production code. The work product is a comprehensive regression test suite in
`tests/SAF-021/` that reproduces every wildcard bypass vector from the security
audit and verifies each is correctly blocked by the SAF-020 implementation.

---

## Files Changed

| File | Change Type | Description |
|------|------------|-------------|
| `tests/SAF-021/__init__.py` | Created | Package marker |
| `tests/SAF-021/conftest.py` | Created | Fake-workspace patch for zone_classifier |
| `tests/SAF-021/test_saf021_wildcard_regression.py` | Created | Comprehensive regression tests |
| `docs/workpackages/SAF-021/dev-log.md` | Created | This file |
| `docs/workpackages/workpackages.csv` | Updated | SAF-021 status → Review |
| `docs/test-results/test-results.csv` | Updated | TST-1399 – TST-1401 logged |

---

## Implementation Notes

### Approach

SAF-020 added wildcard detection to `security_gate.py`. SAF-021 creates additional
regression tests that are specifically anchored to the 10 audit report vectors plus
three additional bypass technique categories.

### Test Structure

The test file is organized into 13 test classes:

| Class | Audit Vector | Tests |
|-------|-------------|-------|
| `TestAuditVector1_GetChildItemDotGStar` | Vector 1 | 3 |
| `TestAuditVector2_GetChildItemNStar` | Vector 2 | 3 |
| `TestAuditVector3_GetChildItemDotVStar` | Vector 3 | 3 |
| `TestAuditVector4_PipedWildcardCommands` | Vector 4 | 4 |
| `TestAuditVector5_WildcardWithFlags` | Vector 5 | 4 |
| `TestAuditVector6_LsDotGStar` | Vector 6 | 3 |
| `TestAuditVector7_CatNStarSlash` | Vector 7 | 3 |
| `TestAuditVector8_ProjectFolderAllowed` | Vector 8 | 5 |
| `TestAuditVector9_DirDotGStar` | Vector 9 | 3 |
| `TestAuditVector10_PathTraversalCombinations` | Vector 10 | 4 |
| `TestBracketWildcardBypass` | Additional | 5 |
| `TestDoubleStarBypass` | Additional | 4 |
| `TestCmdExeWildcardPatterns` | Additional | 3 |

**Total: 58 regression tests**

### Conftest Design

`tests/SAF-021/conftest.py` patches `zone_classifier.detect_project_folder` to
return `"project"` when called with a non-existent workspace path. This preserves
the test intent for allow-zone assertions without modifying any test logic — the
same pattern used by SAF-020's conftest.

### All 10 Audit Vectors Covered

1. `Get-ChildItem .g*` → denied (with GCI alias and uppercase variant)
2. `Get-ChildItem N*` → denied (with lowercase and prefix variant)
3. `Get-ChildItem .v*` → denied (with `.vscode*` variant)
4. `Get-ChildItem .g* | Get-Content` → denied (piped; also alias variants)
5. `Get-ChildItem .g* -Force -Recurse -Name` → denied (flags after wildcard)
6. `ls .g*` → denied (also with `-la` flags and `.github*` variant)
7. `cat N*/*` → denied (also `noagent*` and `NoAgentZone*`)
8. `ls Project/*.py`, `cat Project/app.*` etc. → allowed
9. `dir .g*` → denied (also `.vscode*` and `N*` via dir)
10. `ls ../../.g*`, `ls ./../.g*` etc. → denied (path traversal + wildcard)

### Additional Bypass Techniques Covered

- **Bracket wildcards**: `[.g]*`, `[Nn]*`, `[.v]*` — all denied (SAF-020 iter 2 fix)
- **Double-star (globstar)**: `ls **`, `cat **/.g*` → denied; `cat Project/**` → allowed
- **cmd.exe-style**: `dir /b .g*`, `copy N*\*` → denied

---

## Tests Written

| TST-ID | Test Name | Type | Result |
|--------|-----------|------|--------|
| TST-1399 | SAF-021 regression suite (58 tests) | Regression/Security | Pass |
| TST-1400 | SAF-021 full suite regression (2840 passed / 1 pre-existing / 29 skipped) | Regression | Pass |

---

## Decision Log

- No production code changes — this WP is test-only per the scope definition.
- Conftest uses the same fake-workspace pattern as SAF-020 to avoid test coupling.
- Tests are written as individual functions (not parameterized) to make failures
  immediately identifiable by test name, matching project conventions.
