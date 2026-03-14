# Test Report — INS-014

**Tester:** Tester Agent
**Date:** 2026-03-14
**Iteration:** 1

## Summary

INS-014 implements the `windows-build` job in `.github/workflows/release.yml`.
Seven steps were added and all 16 developer tests pass. However, a critical path
bug was discovered: the `upload-artifact` step references
`Output/AgentEnvironmentLauncher-Setup.exe` (repo-root-relative), but Inno Setup
places the compiled EXE at `src/installer/windows/Output/AgentEnvironmentLauncher-Setup.exe`
because `setup.iss` contains no `OutputDir` directive and Inno Setup resolves its
default `OutputDir` relative to the script file's directory. The CI artifact
upload would fail on every push with "No files were found with the provided path".

**Verdict: FAIL — return to Developer.**

---

## Tests Executed

### Developer Tests (16 / 16 pass)

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
| test_windows_build_artifact_name_and_path | Unit | PASS | name=windows-installer (path only checks filename, not full directory) |

### Tester Edge-Case Tests (10 / 11 pass, 1 fail)

| Test | Type | Result | Notes |
|------|------|--------|-------|
| test_no_shell_override_in_any_step | Unit | PASS | No shell: keys in any step |
| test_artifact_no_retention_days | Unit | PASS | No retention-days override |
| test_all_run_steps_have_human_readable_names | Unit | PASS | All run: steps have names |
| test_no_secrets_referenced_in_windows_build_steps | Unit | PASS | No ${{ secrets.* }} |
| test_artifact_path_matches_inno_setup_output_directory | Unit | **FAIL** | BUG-034: path is 'Output/...' should be 'src/installer/windows/Output/...' |
| test_setup_iss_exists_at_path_referenced_by_iscc | Unit | PASS | setup.iss exists at expected path |
| test_setup_iss_has_no_explicit_output_dir | Unit | PASS | Confirms no OutputDir in setup.iss |
| test_python_version_is_string_not_float | Unit | PASS | '3.11' is a string type |
| test_checkout_is_first_step | Unit | PASS | Checkout is step[0] |
| test_upload_artifact_is_last_step | Unit | PASS | upload-artifact is step[-1] |
| test_no_user_controlled_values_in_env | Unit | PASS | No github.event injected into env: |

### Full Regression Suite

| Run | Result | Notes |
|-----|--------|-------|
| Full suite (1699 + 11 Tester tests) | 26/27 INS-014 pass, 1 fail; 1699 other pass | Only test_artifact_path_matches_inno_setup_output_directory fails |

---

## Bugs Found

- **BUG-034**: CI Windows Build — artifact path does not match Inno Setup output directory
  (logged in docs/bugs/bugs.csv)

---

## Root Cause Analysis

Inno Setup's `OutputDir` directive default is `Output` — resolved relative to
the directory of the `.iss` script file, NOT relative to the process working
directory.

```
iscc src/installer/windows/setup.iss
     └─ setup.iss directory: src/installer/windows/
     └─ default OutputDir:   src/installer/windows/Output/
     └─ EXE written to:      src/installer/windows/Output/AgentEnvironmentLauncher-Setup.exe
```

The workflow's upload-artifact step uses:
```yaml
path: Output/AgentEnvironmentLauncher-Setup.exe
```

This resolves to `{repo_root}/Output/AgentEnvironmentLauncher-Setup.exe` — a
path Inno Setup never writes to. GitHub Actions upload-artifact will fail with
"No files were found with the provided path: Output/AgentEnvironmentLauncher-Setup.exe"

The developer test `test_windows_build_artifact_name_and_path` only asserts that
the EXE filename appears _somewhere_ in the path; it does not verify the full
directory prefix, which is why the bug was not caught.

---

## TODOs for Developer

- [ ] **Fix the artifact path in `.github/workflows/release.yml`** — change the
  upload-artifact `path:` from:
  ```
  Output/AgentEnvironmentLauncher-Setup.exe
  ```
  to:
  ```
  src/installer/windows/Output/AgentEnvironmentLauncher-Setup.exe
  ```
  **Alternatively**, add `OutputDir=..\..\..` to `setup.iss` [Setup] section to
  redirect Inno Setup output to the repo-root `Output/` directory — but this
  would require updating setup.iss and may affect INS-005 tests. The simpler fix
  is to correct the workflow path.

- [ ] **Strengthen `test_windows_build_artifact_name_and_path`** in the developer
  test file — replace the `assert "AgentEnvironmentLauncher-Setup.exe" in path`
  assertion with an exact equality check against the correct full path, so this
  class of bug cannot slip through again.

---

## Verdict

**FAIL** — WP set back to `In Progress`. Developer must fix the artifact path
and strengthen the artifact path test before re-submitting for Tester review.
