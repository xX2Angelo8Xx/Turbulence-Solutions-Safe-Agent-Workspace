# Dev Log — FIX-088: Bump all version strings to 3.2.6

**WP ID:** FIX-088  
**Branch:** FIX-088/version-bump-326  
**Assigned To:** Developer Agent  
**Status:** In Progress  
**User Story:** US-067  
**Fixes:** BUG-163  

---

## Summary

Bump all 4 version strings from their current values to `3.2.6`.

| File | Old Value | New Value |
|------|-----------|-----------|
| `src/launcher/config.py` | `"3.2.5"` | `"3.2.6"` |
| `pyproject.toml` | `"3.2.5"` | `"3.2.6"` |
| `src/installer/windows/setup.iss` | `"3.2.4"` | `"3.2.6"` |
| `src/installer/macos/build_dmg.sh` | `"3.2.4"` | `"3.2.6"` |

---

## Implementation

### Files Changed

1. `src/launcher/config.py` — `VERSION: str = "3.2.5"` → `"3.2.6"`
2. `pyproject.toml` — `version = "3.2.5"` → `"3.2.6"`
3. `src/installer/windows/setup.iss` — `#define MyAppVersion "3.2.4"` → `"3.2.6"`
4. `src/installer/macos/build_dmg.sh` — `APP_VERSION="3.2.4"` → `"3.2.6"`
5. `docs/bugs/bugs.csv` — BUG-163 status set to `Fixed`, Fixed In WP set to `FIX-088`
6. `docs/workpackages/workpackages.csv` — FIX-088 status updated

### Tests Written

- `tests/FIX-088/test_fix088_version_bump.py`
  - `test_config_py_version` — reads config.py, asserts VERSION == "3.2.6"
  - `test_pyproject_toml_version` — reads pyproject.toml, asserts version = "3.2.6"
  - `test_setup_iss_version` — reads setup.iss, asserts MyAppVersion "3.2.6"
  - `test_build_dmg_version` — reads build_dmg.sh, asserts APP_VERSION="3.2.6"
  - `test_all_versions_consistent` — verifies all 4 files report matching version 3.2.6

---

## Known Limitations

None. Purely a string substitution task.
