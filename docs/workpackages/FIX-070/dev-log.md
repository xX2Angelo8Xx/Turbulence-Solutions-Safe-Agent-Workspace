# Dev Log — FIX-070: Bump version to 3.1.2

## Summary

Hotfix version bump from 3.1.1 → 3.1.2 following FIX-069 (critical security fix).
Updated the canonical version string in all 5 required locations.

## Status

In Progress

## Assigned To

Developer Agent

## Files Changed

- `src/launcher/config.py` — VERSION constant: `"3.1.1"` → `"3.1.2"`
- `pyproject.toml` — version field: `"3.1.1"` → `"3.1.2"`
- `src/installer/windows/setup.iss` — MyAppVersion: `"3.1.0"` → `"3.1.2"` (was behind by one bump)
- `src/installer/macos/build_dmg.sh` — APP_VERSION: `"3.1.0"` → `"3.1.2"` (was behind by one bump)
- `src/installer/linux/build_appimage.sh` — APP_VERSION: `"3.1.0"` → `"3.1.2"` (was behind by one bump)
- `tests/FIX-070/test_fix070_version_bump.py` — new test file
- `docs/workpackages/FIX-070/dev-log.md` — this file

## Implementation Notes

The installer scripts (`setup.iss`, `build_dmg.sh`, `build_appimage.sh`) were at
version `3.1.0` rather than `3.1.1`, meaning FIX-069 did not bump them. All three are
now set to `3.1.2` as required by this WP.

Tests use `tests/shared/version_utils.py::CURRENT_VERSION` (dynamic read from config.py)
rather than hardcoding `"3.1.2"`, per the FIX-049 pattern.

## Tests Written

- `tests/FIX-070/test_fix070_version_bump.py`
  - `test_config_py_version` — verifies `src/launcher/config.py` VERSION = CURRENT_VERSION
  - `test_pyproject_toml_version` — verifies `pyproject.toml` version = CURRENT_VERSION
  - `test_setup_iss_version` — verifies `setup.iss` MyAppVersion = CURRENT_VERSION
  - `test_build_dmg_sh_version` — verifies `build_dmg.sh` APP_VERSION = CURRENT_VERSION
  - `test_build_appimage_sh_version` — verifies `build_appimage.sh` APP_VERSION = CURRENT_VERSION
  - `test_all_versions_consistent` — verifies all 5 sources agree on the same version
