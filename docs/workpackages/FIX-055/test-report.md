# Test Report — FIX-055

**Tester:** Tester Agent
**Date:** 2026-03-19
**Iteration:** 1

## Summary

FIX-055 correctly removes the `Check: PythonEmbedExists` runtime function and replaces it with the compile-time `skipifsourcedoesntexist` flag.  All 13 FIX-055 tests pass (8 developer + 5 tester edge-case).  However, the implementation introduces **6 new test regressions** in pre-existing test suites (FIX-012 ×2, INS-005 ×1, INS-018 ×2, INS-021 ×1) that were NOT pre-existing before this WP.

**Verdict: FAIL — return to Developer.**

---

## Tests Executed

### FIX-055 Developer Tests (8 tests)

| Test | Type | Result | Notes |
|------|------|--------|-------|
| test_skipifsourcedoesntexist_in_python_embed_flags | Regression | PASS | Flag present in python-embed [Files] entry |
| test_no_check_parameter_on_python_embed | Regression | PASS | Check: parameter absent |
| test_python_embed_exists_function_removed | Regression | PASS | PythonEmbedExists absent from [Code] |
| test_architectures_install_in_64bit_mode | Unit | PASS | ArchitecturesInstallIn64BitMode=x64compatible in [Setup] |
| test_architectures_allowed | Unit | PASS | ArchitecturesAllowed=x64compatible in [Setup] |
| test_cur_step_changed_still_exists | Regression | PASS | CurStepChanged + python-path.txt intact |
| test_python_embed_source_path_unchanged | Unit | PASS | Source path ..\python-embed\* intact |
| test_python_embed_dest_dir_unchanged | Unit | PASS | DestDir {app}\python-embed intact |

### Tester Edge-Case Tests (5 tests added by Tester)

| Test | Type | Result | Notes |
|------|------|--------|-------|
| test_autopf_not_alongside_x86_in_default_dir_name | Unit | PASS | {autopf} used; no Program Files (x86) in [Setup] |
| test_uninstall_delete_still_references_python_embed | Regression | PASS | [UninstallDelete] entry for python-embed intact |
| test_python_embed_dest_dir_not_bare_path | Unit | PASS | DestDir starts with {app}, includes python-embed |
| test_no_python_embed_exists_reference_anywhere | Regression | PASS | No PythonEmbedExists in any form anywhere in file |
| test_shim_files_entry_unmodified | Regression | PASS | ts-python.cmd entry: {localappdata}\TurbulenceSolutions\bin, ignoreversion, no skipifsourcedoesntexist |

### Full Regression Suite (excluding yaml-dependent and INS-011)

Run: `python -m pytest tests/ --ignore=tests/INS-011 --ignore=tests/INS-013 --ignore=tests/INS-014 --ignore=tests/INS-015 --ignore=tests/INS-016 --ignore=tests/INS-017 --ignore=tests/FIX-010 --ignore=tests/FIX-011 --ignore=tests/FIX-029 -q`

| Result | Count |
|--------|-------|
| PASSED | 3955 |
| FAILED | 61 |
| SKIPPED | 3 |

**Pre-existing failures (55):** FIX-009 (5), FIX-015 (4), FIX-016 (1), FIX-028 (4), FIX-031 (5), FIX-037 (1), FIX-038 (2), FIX-048 (12 — BUG-084), GUI-013 (3), INS-004 (3), SAF-010 (2), SAF-022 (8), SAF-025 (1), SAF-034 (4 — BUG-078).

**New failures introduced by FIX-055 (6):**

| Test | Root Cause |
|------|-----------|
| tests/FIX-012/test_fix012_ci_build_fixes.py::TestSetupIssArchDirectives::test_architectures_allowed_absent | FIX-012 regression guard: ArchitecturesAllowed re-added by FIX-055 |
| tests/FIX-012/test_fix012_edge_cases.py::TestSetupIssIntegrityAfterFix::test_architectures_allowed_absent_case_insensitive | Same — case-insensitive check |
| tests/INS-005/test_ins005_edge_cases.py::TestPrivilegesAndArch::test_architecture_directives_not_present | INS-005 guard for BUG-041 workaround |
| tests/INS-018/test_ins018_bundle_python_embed.py::test_setup_iss_python_embed_check_function | INS-018 asserts PythonEmbedExists must exist |
| tests/INS-018/test_ins018_bundle_python_embed.py::test_setup_iss_python_embed_exists_uses_file_exists | INS-018 asserts FileExists used in PythonEmbedExists |
| tests/INS-021/test_ins021_setup_iss.py::test_python_embed_exists_function_preserved | INS-021 regression guard for PythonEmbedExists |

---

## Bugs Found

- BUG-085: FIX-055 re-introduces ArchitecturesAllowed/ArchitecturesInstallIn64BitMode into setup.iss, breaking 3 tests in FIX-012 and INS-005 that were written specifically to prevent reintroduction of these directives (BUG-041 guardrails). The developer must either: (a) verify CI Inno Setup now supports these directives and update the FIX-012/INS-005 tests to account for the new, correct directive names, or (b) find an alternative approach that does not conflict with the BUG-041 guardrails.

---

## TODOs for Developer

- [ ] **Critical — CI compatibility**: Verify that the chocolatey Inno Setup version on GitHub Actions CI supports `ArchitecturesInstallIn64BitMode=x64compatible` and `ArchitecturesAllowed=x64compatible`. BUG-041 was filed because the old `ArchitecturesInstallMode=x64compatible` directive caused `iscc` compilation failure on CI. The current FIX-012 regression tests guard against any `ArchitecturesAllowed` appearing in setup.iss. You must either (a) update `tests/FIX-012/test_fix012_ci_build_fixes.py::TestSetupIssArchDirectives::test_architectures_allowed_absent`, `tests/FIX-012/test_fix012_edge_cases.py::TestSetupIssIntegrityAfterFix::test_architectures_allowed_absent_case_insensitive`, and `tests/INS-005/test_ins005_edge_cases.py::TestPrivilegesAndArch::test_architecture_directives_not_present` with a clear comment documenting why the Inno Setup version now supports these directives, or (b) remove the directives and use an alternative approach.

- [ ] **Required — Update INS-018 stale tests**: `tests/INS-018/test_ins018_bundle_python_embed.py::test_setup_iss_python_embed_check_function` asserts `PythonEmbedExists` must exist. `test_setup_iss_python_embed_exists_uses_file_exists` asserts `FileExists` must appear. Both tests encode the old (now-removed) behavior. Update them to assert the new behavior (no `PythonEmbedExists`, no `Check:`, `skipifsourcedoesntexist` instead).

- [ ] **Required — Update INS-021 stale test**: `tests/INS-021/test_ins021_setup_iss.py::test_python_embed_exists_function_preserved` asserts `function PythonEmbedExists` must be present. FIX-055 removes it. Update this test to assert the new invariant (function is absent, `skipifsourcedoesntexist` is present).

- [ ] **Verify FIX-012 CI blocker is resolved before re-submitting**: FIX-012 was created specifically to fix a CI build failure from these directives. Do not re-submit FIX-055 without either (a) confirmed CI support or (b) removal of the conflicting directives.

---

## Verdict

**FAIL — return to Developer (In Progress).**

6 new test regressions in FIX-012 (BUG-041 guardrails), INS-005, INS-018, and INS-021. The developer must update stale tests in those WPs and resolve the potential CI Inno Setup compatibility conflict before resubmitting. All TODOs above are required.
