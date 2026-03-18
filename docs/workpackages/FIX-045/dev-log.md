# FIX-045 — Dev Log: Bump Version to 2.1.3

**WP ID:** FIX-045  
**Category:** Fix  
**Status:** Review  
**Assigned To:** Developer Agent  
**Date:** 2026-03-18  

---

## Summary

Version bump to 2.1.3 across all 5 canonical version locations. This release encompasses the security audit fixes (SAF-029, SAF-030, SAF-031), bug fixes (FIX-043, FIX-044), and documentation update (DOC-005) delivered in this sprint.

---

## Implementation Notes

All 5 version files were already updated to `2.1.3` by the SAF-029–SAF-031 and FIX-043/FIX-044/DOC-005 workpackages during this sprint. No source file changes were required — the version was already correct in:

1. `src/launcher/config.py` — `VERSION: str = "2.1.3"`
2. `pyproject.toml` — `version = "2.1.3"`
3. `src/installer/windows/setup.iss` — `#define MyAppVersion "2.1.3"`
4. `src/installer/macos/build_dmg.sh` — `APP_VERSION="2.1.3"`
5. `src/installer/linux/build_appimage.sh` — `APP_VERSION="2.1.3"`

---

## Files Changed

- `docs/workpackages/workpackages.csv` — FIX-045 status set to In Progress / Review
- `docs/workpackages/FIX-045/dev-log.md` — this file (created)
- `tests/FIX-045/test_fix045_version_consistency.py` — test suite created
- `docs/test-results/test-results.csv` — test run logged
- `docs/bugs/bugs.csv` — BUG-045, BUG-048, BUG-049, BUG-050, BUG-052 closed
- `docs/architecture.md` — updated tests directory listing for new WPs

---

## Tests Written

File: `tests/FIX-045/test_fix045_version_consistency.py`

| Test | Description |
|------|-------------|
| `test_config_py_version` | Verifies VERSION in config.py is `2.1.3` |
| `test_pyproject_toml_version` | Verifies version in pyproject.toml is `2.1.3` |
| `test_setup_iss_version` | Verifies MyAppVersion in setup.iss is `2.1.3` |
| `test_build_dmg_version` | Verifies APP_VERSION in build_dmg.sh is `2.1.3` |
| `test_build_appimage_version` | Verifies APP_VERSION in build_appimage.sh is `2.1.3` |
| `test_all_versions_identical` | Verifies all 5 locations contain the same version string |

---

## Test Results

All 6 tests pass. See `docs/test-results/test-results.csv` (TST-1840).

---

## Known Limitations

None. This is a documentation/verification WP — no code logic changed.
