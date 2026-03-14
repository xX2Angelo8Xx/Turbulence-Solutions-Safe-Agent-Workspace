# Dev Log — INS-014: CI Windows Build Job

**Status:** Review
**Assigned To:** Developer Agent
**Date:** 2026-03-14
**Branch:** ins/INS-014-ci-windows-build

---

## Summary

Fleshed out the `windows-build` job in `.github/workflows/release.yml`. The job was previously a stub containing only the checkout step. All 7 required steps have been added.

---

## Implementation

### File Changed

**`.github/workflows/release.yml`**

The `windows-build` job now contains:

1. `actions/checkout@v4` — checks out the repository
2. `actions/setup-python@v5` with `python-version: '3.11'` — sets up Python 3.11
3. `pip install -e ".[dev]"` — installs project dependencies including PyInstaller and pytest
4. `pyinstaller launcher.spec` — builds the onedir bundle using the existing spec file
5. `choco install innosetup -y --no-progress` — installs Inno Setup via Chocolatey
6. `iscc src/installer/windows/setup.iss` — compiles the installer using the existing ISS script
7. `actions/upload-artifact@v4` with `name: windows-installer`, `path: Output/AgentEnvironmentLauncher-Setup.exe` — uploads the compiled EXE

### Path Decision

The artifact path uses `Output/AgentEnvironmentLauncher-Setup.exe` (not `Output/*.exe`) because:
- `setup.iss` has `OutputBaseFilename=AgentEnvironmentLauncher-Setup` — the exact filename is deterministic
- Using the exact filename is more robust than a glob in artifact uploads

---

## Tests Written

**`tests/INS-014/test_ins014_windows_build_job.py`** — 16 tests covering:

| Test | Description |
|------|-------------|
| `test_windows_build_job_exists` | Job present in workflow |
| `test_windows_build_runs_on_windows_latest` | Correct runner |
| `test_windows_build_job_has_7_steps` | Correct step count |
| `test_windows_build_checkout_step` | Checkout action present |
| `test_windows_build_python_setup_step` | setup-python action present |
| `test_windows_build_python_version_is_311` | Python version is exactly '3.11' |
| `test_windows_build_install_dependencies_step` | pip install step present |
| `test_windows_build_pip_install_command` | Command is pip install -e .[dev] |
| `test_windows_build_pyinstaller_step` | pyinstaller step present |
| `test_windows_build_pyinstaller_references_launcher_spec` | References launcher.spec |
| `test_windows_build_inno_setup_install_step` | Chocolatey innosetup install present |
| `test_windows_build_choco_command` | Correct choco command with -y flag |
| `test_windows_build_iscc_step` | iscc step present |
| `test_windows_build_iscc_references_setup_iss` | References correct setup.iss path |
| `test_windows_build_upload_artifact_step` | Upload artifact step present |
| `test_windows_build_artifact_name_and_path` | name=windows-installer, correct EXE path |

---

## Test Results

All 16 INS-014 tests pass. Full regression suite: 1699 passed / 2 skipped / 0 failed.

---

## Known Limitations

- The CI job will only run on GitHub Actions (windows-latest runner). Local validation is YAML-only.
- Python version is pinned to '3.11' (string), matching GitHub Actions convention.

---

## Iteration 2 — BUG-034 Fix (2026-03-14)

### Tester Findings Addressed

**BUG-034**: Artifact path in upload-artifact step was Output/AgentEnvironmentLauncher-Setup.exe
(repo-root-relative). Inno Setup resolves OutputDir relative to the .iss script file's
directory (src/installer/windows/), so the EXE is actually written to
src/installer/windows/Output/AgentEnvironmentLauncher-Setup.exe.

### Changes Made

**.github/workflows/release.yml**
- path: Output/AgentEnvironmentLauncher-Setup.exe  →  path: src/installer/windows/Output/AgentEnvironmentLauncher-Setup.exe

**	ests/INS-014/test_ins014_windows_build_job.py**
- 	est_windows_build_artifact_name_and_path: replaced in substring check on filename with exact
  equality assertion on the full path string src/installer/windows/Output/AgentEnvironmentLauncher-Setup.exe.

### Test Results

- INS-014 suite: **27 / 27 pass** (16 developer + 11 Tester edge-case)
- Full regression suite: **1710 passed, 2 skipped, 0 failed**
