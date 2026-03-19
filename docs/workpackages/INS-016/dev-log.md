# Dev Log — INS-016: CI Linux Build Job

**Status:** Review  
**Branch:** ins/INS-016-ci-linux-build  
**Assigned To:** Developer Agent  
**Date:** 2026-03-14  

---

## Objective

Flesh out the `linux-build` job stub in `.github/workflows/release.yml` so that it:
1. Sets up Python 3.11
2. Installs project dependencies
3. Installs `libfuse2` (required to run AppImages on Ubuntu)
4. Runs PyInstaller to build the launcher binary
5. Runs `build_appimage.sh x86_64` to produce the AppImage
6. Uploads the resulting `dist/*.AppImage` as the `linux-appimage` artifact

---

## Implementation

### File Changed

**`.github/workflows/release.yml`** — The `linux-build` job previously contained only a checkout step. The following steps were added:

| Step Name | Action |
|---|---|
| Set up Python 3.11 | `actions/setup-python@v5`, `python-version: '3.11'` |
| Install dependencies | `pip install -e ".[dev]"` |
| Install libfuse2 | `sudo apt-get update && sudo apt-get install -y libfuse2` |
| Build with PyInstaller | `pyinstaller launcher.spec` |
| Build AppImage | `chmod +x src/installer/linux/build_appimage.sh` then `src/installer/linux/build_appimage.sh x86_64` |
| Upload Linux AppImage | `actions/upload-artifact@v4`, name `linux-appimage`, path `dist/*.AppImage` |

### Key Design Decisions

- **Architecture arg `x86_64`:** `ubuntu-latest` runners are x86_64. The script accepts `x86_64` or `aarch64`; using explicit arg avoids `uname -m` ambiguity in CI.
- **PyInstaller before AppImage script:** `build_appimage.sh` includes an internal PyInstaller invocation that is **skipped** if `dist/launcher/` already exists. Running PyInstaller explicitly in a named step gives cleaner CI log output. The script's guard ensures no double build.
- **Artifact path `dist/*.AppImage`:** The script outputs `dist/TurbulenceSolutionsLauncher-x86_64.AppImage`. Using a glob mirrors the macOS DMG pattern in this workflow and accommodates future architecture changes without editing the workflow.
- **`libfuse2` install placement:** Placed before PyInstaller and AppImage steps as it is a system dependency needed at AppImage packaging time.
- **Pattern follows INS-014/INS-015:** Same Python setup, dependency install, and artifact upload structure for consistency.

---

## Files Changed

| File | Change |
|---|---|
| `.github/workflows/release.yml` | Added 6 steps to the `linux-build` job |
| `docs/workpackages/workpackages.csv` | INS-016 status → In Progress → Review |
| `docs/workpackages/INS-016/dev-log.md` | Created (this file) |
| `tests/INS-016/test_ins016_linux_build_job.py` | Created — 24 test cases |
| `docs/test-results/test-results.csv` | Test run logged |

---

## Tests Written

Test file: `tests/INS-016/test_ins016_linux_build_job.py`

Tests verify the `linux-build` job in the parsed YAML:
- Job exists and runs on `ubuntu-latest`
- All 6 expected step names are present
- Python version is `'3.11'`
- `pip install -e ".[dev]"` is the dependency install command
- `libfuse2` apt-get install command is present and uses `sudo` and `-y`
- PyInstaller command uses `launcher.spec`
- AppImage script is called with `x86_64` argument
- `chmod +x` precedes the script invocation
- Artifact name is `linux-appimage`
- Artifact path is `dist/*.AppImage`
- Step ordering is correct (libfuse2 before build, upload last)
- YAML is valid and parses without error
- `release` job still lists `linux-build` in its `needs`

---

## Known Limitations

None. This WP is a YAML configuration change only — no Python code is modified.
