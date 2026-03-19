# FIX-047 Dev Log — Bump version to 3.0.0

**WP ID:** FIX-047  
**Branch:** FIX-047/bump-version-3.0.0  
**Date:** 2026-03-19  
**Developer:** Developer Agent  
**Status:** Review  

---

## Summary

Updated all version references from `2.1.3` to `3.0.0` across the five canonical
version locations. Updated `docs/architecture.md` to reflect V3.0.0 structural
changes (new core modules, new installer subdirectories, new test directories).

---

## Files Changed

| File | Change |
|------|--------|
| `src/launcher/config.py` | `VERSION = "3.0.0"` |
| `pyproject.toml` | `version = "3.0.0"` |
| `src/installer/windows/setup.iss` | `#define MyAppVersion "3.0.0"` |
| `src/installer/macos/build_dmg.sh` | `APP_VERSION="3.0.0"` |
| `src/installer/linux/build_appimage.sh` | `APP_VERSION="3.0.0"` |
| `docs/architecture.md` | Added new core files, installer subdirs, test directories |
| `docs/workpackages/workpackages.csv` | Status → Review, Assigned To → Developer Agent |

---

## Architecture.md Changes

- Added to `src/launcher/core/`: `applier.py`, `os_utils.py`, `project_creator.py`, `shim_config.py`, `vscode.py`
- Added to `src/installer/`: `linux/`, `macos/`, `windows/`, `python-embed/`, `shims/`
- Added missing test directories: FIX-031 through FIX-035, FIX-046, FIX-047, GUI-018, INS-018 through INS-021, SAF-032 through SAF-034, DOC-006

---

## Tests Written

Location: `tests/FIX-047/test_fix047_version.py`

| Test | Description |
|------|-------------|
| `test_config_py_version` | `src/launcher/config.py` contains `3.0.0` |
| `test_pyproject_toml_version` | `pyproject.toml` contains `3.0.0` |
| `test_setup_iss_version` | `src/installer/windows/setup.iss` contains `3.0.0` |
| `test_build_dmg_sh_version` | `src/installer/macos/build_dmg.sh` contains `3.0.0` |
| `test_build_appimage_sh_version` | `src/installer/linux/build_appimage.sh` contains `3.0.0` |
| `test_no_old_version_config_py` | No `2.1.3` in `config.py` |
| `test_no_old_version_pyproject` | No `2.1.3` in `pyproject.toml` |
| `test_no_old_version_setup_iss` | No `2.1.3` in `setup.iss` |
| `test_no_old_version_build_dmg` | No `2.1.3` in `build_dmg.sh` |
| `test_no_old_version_build_appimage` | No `2.1.3` in `build_appimage.sh` |
| `test_version_consistency` | All 5 files report the same version string |

---

## Known Limitations

None. This is a pure version-string update with no logic changes.
