# Test Report — MNT-027: Narrow CI to Windows-only

**Tester:** Tester Agent  
**Date:** 2026-04-05  
**Verdict:** ❌ FAIL — WP returned to In Progress

---

## Summary

MNT-027 correctly modifies all four workflow files and updates two documentation files as specified. The 14 developer tests all pass, and YAML structure is valid with no orphaned `needs` references. However, removing `macos-arm-build` and `linux-build` jobs from `release.yml` introduced **106 new test regressions** across 11 existing test suites that were not acknowledged in the regression baseline.

---

## Review Findings

### Code Quality: PASS
All workflow YAML files are structurally valid:
- `test.yml` — matrix narrowed to `[windows-latest]`, `manifest-check` and `parity-check` moved to `windows-latest`. ✅
- `macos-source-test.yml` — `if: false` correctly on `macos-source-install` job with ADR-010 comment. ✅
- `staging-test.yml` — `smoke-test-ubuntu` and `smoke-test-macos` removed; `staging-summary.needs` updated to `[smoke-test-windows]` only. ✅
- `release.yml` — `run-tests` matrix narrowed; `macos-arm-build` and `linux-build` removed; `release.needs` updated to `[windows-build]`. ✅
- No orphaned `needs` references. ✅
- No source code deleted — `src/installer/macos/`, `src/installer/linux/`, `scripts/install-macos.sh` all preserved. ✅

### Documentation: PASS
- `docs/project-scope.md` — Platform Support Status table present with correct Windows/Active, macOS/Deferred, Linux/Deferred rows. ✅
- `docs/architecture.md` — CI/CD scope note added with ADR-010 reference and "preserved but disabled" language. ✅

### Developer Tests: PASS (14/14)
All 14 developer tests in `tests/MNT-027/test_ci_windows_only.py` pass.

### Tester Edge-Case Tests: PASS (16/16)
16 additional edge-case tests added in `tests/MNT-027/test_ci_windows_only_edge.py`:
- Orphaned `needs` reference checks for `staging-summary`, `release`, and `windows-build`
- No ubuntu/macos runners in `test.yml` (including non-matrix `runs-on`)
- Source code preservation: `src/installer/macos/build_dmg.sh`, `src/installer/linux/build_appimage.sh`, `scripts/install-macos.sh`
- Workflow files not deleted (only modified/disabled)
- `macos-source-install` job still defined (just gated by `if: false`)
- `if: false` is on the correct job block
- Platform Support docs use "Deferred" (not Removed/Dropped)
- Architecture CI note references ADR-010 and "preserved"

---

## Regression Analysis: ❌ FAIL

**106 new regressions** detected — none in the regression baseline.

MNT-027 removed `macos-arm-build` and `linux-build` from `release.yml`. Eleven pre-existing test suites test those jobs and now fail. The developer did NOT add these expected failures to `tests/regression-baseline.json`.

### Affected test suites (106 total failures):

| Suite | Count | Root Cause |
|-------|-------|------------|
| `tests/INS-015/` | ~17 | `macos-arm-build` job removed from `release.yml` |
| `tests/INS-016/` | ~28 | `linux-build` job removed from `release.yml` |
| `tests/INS-013/` | ~6 | Tests expect 5 release.yml jobs (now has 3) |
| `tests/INS-017/` | ~4 | Tests expect `release.needs` to include `linux-build` and `macos-arm-build` |
| `tests/FIX-010/` | ~6 | Tests reference `linux-build` and `macos-arm-build` jobs |
| `tests/FIX-011/` | ~2 | Tests check `release.needs` count as exactly 4 |
| `tests/FIX-029/` | ~11 | Tests check macOS arm codesign step in `release.yml` |
| `tests/FIX-038/` | ~4 | Tests check macOS component codesign in `release.yml` |
| `tests/FIX-039/` | ~4 | Tests check macOS-specific verify steps in `release.yml` |
| `tests/FIX-106/` | ~3 | Tests assert `release.yml` has 6 jobs |
| `tests/MNT-005/` | ~4 | Tests check `linux-build` and `macos-arm-build` need `validate-version` |

---

## TODOs for Developer (Mandatory Before Re-Review)

### TODO 1 — Update regression baseline (REQUIRED)

All 106 new regressions must be added to `tests/regression-baseline.json`.

**Step-by-step:**

1. Run the full test suite and generate JUnit XML:
   ```powershell
   python -m pytest tests/ --tb=no -q --junitxml=docs/workpackages/MNT-027/tmp_results.xml
   ```

2. Identify all failures now caused by the removed jobs. The list is exactly those 106 tests listed above.

3. For each new failure, add an entry to `tests/regression-baseline.json` `known_failures` dict:
   ```json
   "tests.INS-015.test_ins015_macos_build_jobs.test_macos_arm_job_exists": {
     "reason": "macos-arm-build job removed from release.yml per MNT-027 (Windows-only CI)"
   }
   ```

4. Update `_count` and `_updated` fields in `tests/regression-baseline.json`.

5. **Alternative (cleaner):** Update the INS-015, INS-016, INS-013, INS-017, FIX-010, FIX-011, FIX-029, FIX-038, FIX-039, FIX-106, and MNT-005 test files to skip gracefully when the relevant jobs do not exist — e.g.:
   ```python
   import pytest
   # At fixture level:
   if "macos-arm-build" not in workflow["jobs"]:
       pytest.skip("macos-arm-build removed in MNT-027")
   ```
   This is more principled but involves modifying many test files outside MNT-027 scope — confirm with the Orchestrator if needed.

**The regression baseline approach (option 3/4) is the minimum required to unblock this WP.**

### TODO 2 — Re-run the full suite after baseline update

After updating the baseline:
```powershell
python scripts/run_tests.py --wp MNT-027 --type Unit --env "Windows/Python 3.13.5" --full-suite --notes "<result>"
```
Confirm zero new regressions (exit code 0 from CI regression gate).

### TODO 3 — Update dev-log.md

Add a new iteration section documenting:
- The regression baseline was not updated in Iteration 1
- Which test suites were affected and why
- The fix applied

---

## Test Log Reference

- **TST-2626** — MNT-027 Full Suite — Fail (Windows/Python 3.13.5, 2026-04-05)
