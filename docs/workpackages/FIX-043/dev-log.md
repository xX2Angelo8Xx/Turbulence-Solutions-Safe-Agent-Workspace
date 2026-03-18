# Dev Log — FIX-043

**Workpackage:** FIX-043 — Fix INS-005 test expected value for uninstall delete type  
**Status:** Review  
**Assigned To:** Developer Agent  
**Branch:** FIX-043/fix-ins005-test  
**Date:** 2026-03-18  

---

## Summary

Fixed a pre-existing test bug (BUG-045, Low severity) in `tests/INS-005/test_ins005_edge_cases.py`. The test assertion used the incorrect Inno Setup keyword `filesandirs` instead of the correct `filesandordirs`. The actual `setup.iss` file correctly uses `filesandordirs`; the test was wrong.

## Changes Made

### `tests/INS-005/test_ins005_edge_cases.py`
- Renamed `test_uninstall_delete_type_is_filesandirs` → `test_uninstall_delete_type_is_filesandordirs`
- Updated the regex pattern from `r"Type:\s*filesandirs"` to `r"Type:\s*filesandordirs"`
- Updated the failure message string to match the corrected keyword

### `docs/workpackages/workpackages.csv`
- Set FIX-043 status to `In Progress` (then `Review` on handoff)
- Set `Assigned To` to `Developer Agent`

---

## Root Cause

`setup.iss` line 43 contains `Type: filesandordirs; Name: "{app}"`. The original test author wrote `filesandirs` (missing `or`), so the test was always failing against the correct implementation.

---

## Tests Run

| Run | Scope | Result |
|-----|-------|--------|
| INS-005 only | `pytest tests/INS-005/ -v --tb=short` | 40 passed, 1 pre-existing failure (`test_app_version` expects `2.0.1`, file has `2.1.3` — BUG-045 companion, unrelated to this WP) |
| Regression | `pytest tests/INS-005/ tests/INS-003/ tests/INS-004/ -q --tb=no` | 125 passed, 1 pre-existing failure (same `test_app_version`) |

The target test `test_uninstall_delete_type_is_filesandordirs` **PASSES**.

---

## Notes

- No source code changes — this is a test-only fix.
- The single remaining failure (`test_app_version`) is a pre-existing issue (tracked separately), not introduced or worsened by this WP.
