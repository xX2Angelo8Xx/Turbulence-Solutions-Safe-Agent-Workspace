# Test Report — INS-012

**Tester:** Tester Agent
**Date:** 2026-03-11
**Iteration:** 1

## Summary

WP goal confirmed: no Python bytecache, build artifacts, or virtualenv files are
tracked by git. All 14 required `.gitignore` patterns are present and verified
by both static text inspection and live `git check-ignore` integration tests.
The Developer's 22-test suite passed cleanly. 8 additional edge-case tests were
added by the Tester (TST-166 to TST-173). Full regression: 207/207 pass, no
regressions introduced by INS-012.

Note: the Developer's dev-log claimed one pre-existing SAF-001 failure
(`test_decide_project_sibling_prefix_bypass`). That test **PASSES** in the
current environment (likely resolved by SAF-002 work on the same branch). No
blocking failures exist.

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| test_gitignore_exists | Unit | PASS | |
| test_pycache_excluded | Unit | PASS | |
| test_pyc_excluded | Unit | PASS | |
| test_pyo_excluded | Unit | PASS | |
| test_eggs_dir_excluded | Unit | PASS | |
| test_egg_info_excluded | Unit | PASS | |
| test_dist_excluded | Unit | PASS | |
| test_build_excluded | Unit | PASS | |
| test_pytest_cache_excluded | Unit | PASS | |
| test_venv_excluded | Unit | PASS | |
| test_env_excluded | Unit | PASS | |
| test_venv_plain_excluded | Unit | PASS | |
| test_spec_excluded | Unit | PASS | |
| test_ds_store_excluded | Unit | PASS | |
| test_thumbs_db_excluded | Unit | PASS | |
| test_no_duplicate_patterns | Unit | PASS | |
| test_gitignore_git_recognises_pyc | Integration | PASS | git check-ignore |
| test_gitignore_git_recognises_pycache | Integration | PASS | git check-ignore |
| test_gitignore_git_recognises_spec | Integration | PASS | git check-ignore |
| test_gitignore_git_recognises_venv | Integration | PASS | git check-ignore |
| test_pycache_not_tracked_in_git_index | Integration | PASS | git ls-files |
| test_egg_info_not_tracked_in_git_index | Integration | PASS | git ls-files |
| test_no_negation_overrides_required_patterns | Unit | PASS | Tester edge-case — TST-166 |
| test_gitignore_file_has_active_patterns | Unit | PASS | Tester edge-case — TST-167 |
| test_gitignore_git_recognises_dist | Integration | PASS | Tester edge-case — TST-168 |
| test_gitignore_git_recognises_build | Integration | PASS | Tester edge-case — TST-169 |
| test_gitignore_git_recognises_pytest_cache | Integration | PASS | Tester edge-case — TST-170 |
| test_gitignore_git_recognises_ds_store | Integration | PASS | Tester edge-case — TST-171 |
| test_pyc_files_not_tracked_in_git_index | Integration | PASS | Tester edge-case — TST-172 |
| test_venv_not_tracked_in_git_index | Integration | PASS | Tester edge-case — TST-173 |
| Full regression suite (207 tests) | Regression | PASS | TST-174 — 207/207; no regressions |

## Bugs Found

- BUG-009: Duplicate TST IDs in test-results.csv — TST-125 to TST-158 assigned
  to SAF-002, then reused by GUI-001 Developer; TST-125 to TST-147 additionally
  reused by INS-012 Developer. Severity: Minor. Logged in docs/bugs/bugs.csv.

## TODOs for Developer

None — all acceptance criteria met.

## Verdict

PASS — mark WP INS-012 as Done.
