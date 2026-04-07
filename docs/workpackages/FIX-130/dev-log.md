# Dev Log — FIX-130

**Developer:** Developer Agent  
**Date started:** 2026-04-08  
**Iteration:** 1

## Objective

Fix 16 CI test failures for v3.4.0. Four distinct root causes were identified and resolved:

1. GUI-007 mock pollution — `app._window.after = lambda` replaces MagicMock, breaking downstream `reset_mock()` calls in GUI-009/010 tests
2. GUI-018 geometry assertion — still asserts `480x620` after GUI-037 increased SettingsDialog height to `720px`
3. Missing `.gitattributes` rules for `templates/clean-workspace/` — line-ending hash mismatches in CI
4. Regression baseline missing two CI-environment-specific entries

## ADR Check

No ADRs in `docs/decisions/index.jsonl` were found to be directly relevant to test mock patterns, geometry assertions, or `.gitattributes` configuration.

## Implementation Summary

### Fix 1: GUI-007 Mock Pollution (7 tests fixed)

Changed `app._window.after = lambda ms, fn: fn()` to `app._window.after.side_effect = lambda ms, fn: fn()` in all three GUI-007 test helper functions. The direct assignment replaced the MagicMock attribute with a plain function, causing `AttributeError: 'function' object has no attribute 'reset_mock'` when GUI-009/010 tests called `reset_mock()` on the shared ctk mock.

### Fix 2: GUI-018 Geometry Assertion (1 test fixed)

Updated `test_dialog_geometry_is_480x620` → `test_dialog_geometry_is_480x720` and changed `assert_called_with("480x620")` → `assert_called_with("480x720")` to match the height increase made in GUI-037.

### Fix 3: .gitattributes Clean-Workspace Rules (3-5 CI tests)

Added LF-enforcement rules for `templates/clean-workspace/` parallel to the existing `templates/agent-workbench/` rules. Re-normalized files via `git rm --cached -r templates/clean-workspace/ && git add templates/clean-workspace/`. Regenerated clean-workspace MANIFEST.json and verified both manifests pass `--check`. Cleaned up `__pycache__` created during manifest generation.

### Fix 4: Regression Baseline (FIX-125 CI entry)

Added `tests.FIX-125.test_fix125_build_fixes.TestFindIsccLocalAppData.test_find_iscc_localappdata_path_wins_over_absent_system_paths` to `tests/regression-baseline.json` with reason: CI runner has Inno Setup pre-installed at system path. Updated `_count` from 219 → 220, `_updated` to 2026-04-08.

Note: `pytest.internal` was considered but NOT added — it does not match the required `tests.<WP-ID>.<module>.<testname>` key format enforced by MNT-029 `test_baseline_no_stale_entries`, and it never appears as a `FAILED` line in pytest output.

## Verification

- **Pre-fix (main):** 94 cross-check "new failures", 250 total
- **Post-fix (FIX-130):** 85 cross-check "new failures", 241 total
- **Net improvement:** 9 failures eliminated (7 GUI-009/010 + 1 GUI-018 + 1 GUI-010-tester)  
- The 85 remaining are all pre-existing on main (confirmed by stash-and-compare)

## Files Changed

- `.gitattributes` — Added clean-workspace LF-enforcement rules
- `tests/GUI-007/test_gui007_edge_cases.py` — Fix 1: side_effect
- `tests/GUI-007/test_gui007_tester_additions.py` — Fix 1: side_effect  
- `tests/GUI-007/test_gui007_validation.py` — Fix 1: side_effect
- `tests/GUI-018/test_gui018_edge_cases.py` — Fix 2: geometry 480x720
- `templates/clean-workspace/.github/hooks/scripts/MANIFEST.json` — Regenerated after line-ending normalization
- `tests/regression-baseline.json` — Fix 4: FIX-125 entry added, count 219→220
- `tests/FIX-130/test_fix130_ci_failures.py` — Regression tests for all 4 fixes
- `docs/workpackages/FIX-130/dev-log.md` — This file
- `docs/workpackages/workpackages.jsonl` — Status updated

## Tests Written

- `tests/FIX-130/test_fix130_ci_failures.py` — 10 regression tests covering:
  - GUI-007: 3 tests verifying `.side_effect` usage in each file
  - GUI-018: 2 tests verifying correct geometry assertion and method name
  - `.gitattributes`: 3 tests verifying clean-workspace LF rules present
  - Regression baseline: 2 tests verifying FIX-125 entry and count integrity

**Test result:** TST-2778 — 10 passed, 0 failed (logged via run_tests.py)

## Known Limitations

The 85 pre-existing "new failures" (relative to baseline) are test-ordering/contamination issues that exist on main and are unrelated to FIX-130. They include: SAF-073/074/077 security gate tests that fail due to module state contamination when run in the full suite, INS-012/019, GUI-035/036, MNT-002/015/029. These require separate investigation.
