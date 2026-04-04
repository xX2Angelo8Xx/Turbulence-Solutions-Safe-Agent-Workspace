# Test Report — FIX-105

**Tester:** Tester Agent  
**Date:** 2026-04-04  
**Iteration:** 1

---

## Summary

FIX-105 successfully updates all test assertions that referenced the old `TS-SAE-` prefix (→ `SAE-`) and the old `templates/coding/` path (→ `templates/agent-workbench/`). All 366 targeted tests pass. No new regressions were introduced. The regression baseline was correctly reduced from 643 to 610 entries by removing the 33 fixed entries. Workspace validation is clean.

---

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| TST-2588: FIX-105 full regression suite (`scripts/run_tests.py`) | Regression | Fail (47 collection errors) | All 47 collection errors are pre-existing (same errors existed on main/613b8fd before FIX-105) |
| TST-2589: FIX-105 targeted regression suite | Regression | Pass | 366 passed, 2 skipped — all modified test files pass |
| `tests/FIX-105/` (9 verification tests) | Unit | Pass | All 9 assertions about SAE- prefix and agent-workbench path pass |
| `tests/GUI-005/`, `tests/GUI-007/`, `tests/GUI-015/`, `tests/GUI-016/`, `tests/GUI-020/`, `tests/GUI-022/` | Regression | Pass | All GUI prefix tests use `SAE-` correctly |
| `tests/INS-004/` | Regression | Pass | All 6 template bundling assertions use `templates/agent-workbench/` |

---

## Pre-Existing Failures (Not Introduced by FIX-105)

The following 15 failures exist in the full suite but pre-date FIX-105 (confirmed by running against the main branch at commit 613b8fd before FIX-105 was applied):

**Hash integrity failures (5 tests across FIX-042, FIX-079, SAF-022, SAF-025, SAF-071):**
- `_KNOWN_GOOD_SETTINGS_HASH` in `security_gate.py` does not match the actual `security_gate_settings.json` hash
- Pre-existing issue requiring `update_hashes.py` to be run separately
- Not caused by FIX-105's `__pycache__` deletion (hash mismatch existed before)

**Missing PIL module failures (10 tests across FIX-015, FIX-016, GUI-013):**
- `ModuleNotFoundError: No module named 'PIL'` — Pillow is not installed in this Python environment
- Pre-existing environment issue, unrelated to FIX-105

None of these 15 failures are tracked in the regression baseline. This is a separate pre-existing gap that warrants a future cleanup WP.

---

## Regression Check

- Old baseline: 643 entries
- FIX-105 removed: 33 entries (27 GUI prefix failures + 6 INS-004 template bundling failures)
- New baseline: 610 entries ✓
- No entries that should have been removed remain in baseline
- No entries removed that should have been kept

**ADR Review:** ADR-003 (Template Manifest and Workspace Upgrade System) references `templates/agent-workbench/`. FIX-105 deleted `__pycache__` from the template (not tracked in MANIFEST.json) — no ADR conflict.

---

## Assertion Hygiene Verification

- **`TS-SAE-` in test assertions:** Only appears in *negative* assertion tests (FIX-105, DOC-048, DOC-049) that assert the old prefix is NOT present. Correct.
- **`templates/coding/`:** Remaining references are in comment/docstring text and in tests that specifically verify the rename happened (DOC-017). None are in pass-required path assertions for the current template structure.
- **All 8 modified GUI test files:** Confirmed to use `SAE-` only.
- **INS-004 template bundling file:** Confirmed to use `templates/agent-workbench/` only.

---

## Edge Cases Examined

- Double-prefix `TS-SAE-SAE-` hybrid: confirmed absent (checked by FIX-105 test + DOC-048)
- `SAF-034` uses `"TS-SAE-TestProject"` as test setup fixture data (not a system behavior assertion) — acceptable
- `scripts/validate_workspace.py --wp FIX-105` → clean (exit code 0)
- `__pycache__` deletion: pycache tests updated to use `git ls-files` (immune to conftest re-creation) — verified

---

## Bugs Found

None.

---

## TODOs for Developer

None.

---

## Verdict

**PASS — mark WP as Done.**

All acceptance criteria met:
- [x] All tests referencing template paths use `templates/agent-workbench/`
- [x] All prefix tests use `SAE-` (not `TS-SAE-`)
- [x] Regression baseline correctly updated to 610 entries
- [x] 9 FIX-105 verification tests pass
- [x] No new test regressions introduced
- [x] Workspace validation clean
