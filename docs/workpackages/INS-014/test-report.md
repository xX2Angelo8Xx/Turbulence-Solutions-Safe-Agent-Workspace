# Test Report — INS-014

**Tester:** Tester Agent
**Date:** 2026-03-14
**Iteration:** 2 (final)

## Summary

INS-014 implements the `windows-build` job in `.github/workflows/release.yml`.
BUG-034 (artifact path mismatch) reported in Iteration 1 has been resolved:
the `upload-artifact` step now correctly references
`src/installer/windows/Output/AgentEnvironmentLauncher-Setup.exe`, matching the
actual Inno Setup default `OutputDir` (relative to the `.iss` script file directory).
The developer test `test_windows_build_artifact_name_and_path` was strengthened
to use exact equality assertion on the full path. All 27 tests (16 developer + 11
Tester edge-case) pass. Full suite of 1710 tests passes with 2 expected skips and
no failures.

**Verdict: PASS — marking Done.**

---

## Iteration 1 Summary (archived)

Iteration 1 FAIL: BUG-034 — artifact path was `Output/AgentEnvironmentLauncher-Setup.exe`
(repo-root-relative); correct path is `src/installer/windows/Output/AgentEnvironmentLauncher-Setup.exe`.
Developer test only checked that the EXE filename appeared somewhere in the path (not the full
prefix), so the bug was not caught by developer tests. Returned to Developer with specific TODOs.

---

## Tests Executed

### Developer Tests — Iteration 2 (16 / 16 pass)

| Test | Type | Result | Notes |
|------|------|--------|-------|
| test_windows_build_job_exists | Unit | PASS | Job present in jobs map |
| test_windows_build_runs_on_windows_latest | Unit | PASS | runs-on: windows-latest |
| test_windows_build_job_has_7_steps | Unit | PASS | Exactly 7 steps |
| test_windows_build_checkout_step | Unit | PASS | actions/checkout@v4 |
| test_windows_build_python_setup_step | Unit | PASS | actions/setup-python@v5 |
| test_windows_build_python_version_is_311 | Unit | PASS | python-version: '3.11' |
| test_windows_build_install_dependencies_step | Unit | PASS | Step name present |
| test_windows_build_pip_install_command | Unit | PASS | pip install -e .[dev] |
| test_windows_build_pyinstaller_step | Unit | PASS | Step name present |
| test_windows_build_pyinstaller_references_launcher_spec | Unit | PASS | launcher.spec referenced |
| test_windows_build_inno_setup_install_step | Unit | PASS | Step name present |
| test_windows_build_choco_command | Unit | PASS | choco install innosetup -y |
| test_windows_build_iscc_step | Unit | PASS | Step name present |
| test_windows_build_iscc_references_setup_iss | Unit | PASS | src/installer/windows/setup.iss |
| test_windows_build_upload_artifact_step | Unit | PASS | actions/upload-artifact@v4 |
| test_windows_build_artifact_name_and_path | Unit | PASS | exact equality on full path src/installer/windows/Output/... |

### Tester Edge-Case Tests — Iteration 2 (11 / 11 pass)

| Test | Type | Result | Notes |
|------|------|--------|-------|
| test_no_shell_override_in_any_step | Unit | PASS | No shell: keys in any step |
| test_artifact_no_retention_days | Unit | PASS | No retention-days override |
| test_all_run_steps_have_human_readable_names | Unit | PASS | All run: steps have names |
| test_no_secrets_referenced_in_windows_build_steps | Unit | PASS | No ${{ secrets.* }} |
| test_artifact_path_matches_inno_setup_output_directory | Unit | **PASS** | BUG-034 fixed; path is now src/installer/windows/Output/... |
| test_setup_iss_exists_at_path_referenced_by_iscc | Unit | PASS | setup.iss exists at expected path |
| test_setup_iss_has_no_explicit_output_dir | Unit | PASS | Confirms no OutputDir in setup.iss |
| test_python_version_is_string_not_float | Unit | PASS | '3.11' is a string type |
| test_checkout_is_first_step | Unit | PASS | Checkout is step[0] |
| test_upload_artifact_is_last_step | Unit | PASS | upload-artifact is step[-1] |
| test_no_user_controlled_values_in_env | Unit | PASS | No github.event injected into env: |

### Full Regression Suite — Iteration 2

| Run | Result | Notes |
|-----|--------|-------|
| Full suite — Tester Iteration 2 (1710 tests) | 1710 pass, 2 skip, 0 fail; all 27 INS-014 pass | TST-773 |

---

## Bugs Found

- **BUG-034**: CI Windows Build — artifact path does not match Inno Setup output directory
  (logged in docs/bugs/bugs.csv — **Closed in Iteration 2**)

---

## Root Cause Analysis (from Iteration 1, resolved)

Inno Setup's `OutputDir` directive default is `Output` — resolved relative to
the directory of the `.iss` script file, NOT relative to the process working
directory.

```
iscc src/installer/windows/setup.iss
     └─ setup.iss directory: src/installer/windows/
     └─ default OutputDir:   src/installer/windows/Output/
     └─ EXE written to:      src/installer/windows/Output/AgentEnvironmentLauncher-Setup.exe
```

**Fix applied (Iteration 2):** workflow artifact path corrected to
`src/installer/windows/Output/AgentEnvironmentLauncher-Setup.exe`.
Developer test `test_windows_build_artifact_name_and_path` now uses exact equality
assertion. Both changes verified.

---

## Verdict

**PASS** — WP set to `Done`. BUG-034 closed.
