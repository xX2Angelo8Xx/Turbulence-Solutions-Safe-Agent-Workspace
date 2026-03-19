# Dev Log — FIX-049

**Developer:** Developer Agent
**Date started:** 2025-01-31
**Iteration:** 1

## Objective
Fix the version test regression pattern where version bump workpackages (FIX-014, FIX-017, FIX-019, FIX-020, FIX-030, FIX-036, FIX-045, FIX-047, FIX-048) hardcode the expected version string, causing ALL these old tests to break whenever a new version bump occurs.

Create a shared version utility (`tests/shared/version_utils.py`) that reads CURRENT_VERSION dynamically from `src/launcher/config.py`, and update all affected test files to use this dynamic source of truth instead of hardcoded version strings.

## Implementation Summary

### Approach
Used the inline re.search pattern to dynamically read the current version from `src/launcher/config.py` via the already-defined `REPO_ROOT` in each test file. This avoids any sys.path manipulation issues.

For files where `re` was already imported at module level, the existing import is used. For files without module-level `re`, a temporary `import re as _re` is used and cleaned up with `del _re`.

A shared utility `tests/shared/version_utils.py` is also created as a reusable single source of truth for future test authors.

### Files Changed
1. Created `tests/shared/__init__.py` — makes tests/shared a Python package
2. Created `tests/shared/version_utils.py` — shared CURRENT_VERSION utility
3. Updated `tests/FIX-014/test_fix014_version_bump.py` — dynamic EXPECTED_VERSION
4. Updated `tests/FIX-014/test_fix014_edge_cases.py` — dynamic EXPECTED_VERSION
5. Updated `tests/FIX-017/test_fix017_version_bump.py` — dynamic EXPECTED_VERSION
6. Updated `tests/FIX-017/test_fix017_edge_cases.py` — dynamic EXPECTED_VERSION (was stale 2.0.1)
7. Updated `tests/FIX-019/test_fix019_version_bump.py` — dynamic EXPECTED_VERSION
8. Updated `tests/FIX-019/test_fix019_edge_cases.py` — dynamic EXPECTED_VERSION
9. Updated `tests/FIX-020/test_fix020_version_bump.py` — dynamic EXPECTED_VERSION
10. Updated `tests/FIX-020/test_fix020_edge_cases.py` — dynamic EXPECTED_VERSION
11. Updated `tests/FIX-030/test_fix030_version_bump.py` — dynamic EXPECTED_VERSION
12. Updated `tests/FIX-036/test_fix036_version_consistency.py` — dynamic EXPECTED_VERSION
13. Updated `tests/FIX-045/test_fix045_version_consistency.py` — dynamic EXPECTED_VERSION
14. Updated `tests/FIX-047/test_fix047_version.py` — dynamic TARGET_VERSION
15. Updated `tests/FIX-048/test_fix048.py` — dynamic CURRENT_VERSION for inline assertions
16. Updated `tests/INS-005/test_ins005_setup_iss.py` — dynamic CURRENT_VERSION
17. Updated `tests/INS-006/test_ins006_build_dmg.py` — dynamic CURRENT_VERSION
18. Updated `tests/INS-007/test_ins007_build_appimage.py` — dynamic CURRENT_VERSION
19. Updated `tests/FIX-010/test_fix010_cicd_pipeline.py` — dynamic CURRENT_VERSION
20. Updated `docs/work-rules/testing-protocol.md` — added version bump testing section
21. Created `tests/FIX-049/test_fix049_version_utils.py` — tests for this WP
- `tests/shared/__init__.py` — new: package marker
- `tests/shared/version_utils.py` — new: shared version utility
- `tests/FIX-014/test_fix014_version_bump.py` — EXPECTED_VERSION now dynamic
- `tests/FIX-014/test_fix014_edge_cases.py` — EXPECTED_VERSION now dynamic
- `tests/FIX-017/test_fix017_version_bump.py` — EXPECTED_VERSION now dynamic
- `tests/FIX-017/test_fix017_edge_cases.py` — EXPECTED_VERSION now dynamic (was stale)
- `tests/FIX-019/test_fix019_version_bump.py` — EXPECTED_VERSION now dynamic
- `tests/FIX-019/test_fix019_edge_cases.py` — EXPECTED_VERSION now dynamic
- `tests/FIX-020/test_fix020_version_bump.py` — EXPECTED_VERSION now dynamic
- `tests/FIX-020/test_fix020_edge_cases.py` — EXPECTED_VERSION now dynamic
- `tests/FIX-030/test_fix030_version_bump.py` — EXPECTED_VERSION now dynamic
- `tests/FIX-036/test_fix036_version_consistency.py` — EXPECTED_VERSION now dynamic
- `tests/FIX-045/test_fix045_version_consistency.py` — EXPECTED_VERSION now dynamic
- `tests/FIX-047/test_fix047_version.py` — TARGET_VERSION now dynamic
- `tests/FIX-048/test_fix048.py` — version assertions now dynamic
- `tests/INS-005/test_ins005_setup_iss.py` — version assertion now dynamic
- `tests/INS-006/test_ins006_build_dmg.py` — version assertion now dynamic
- `tests/INS-007/test_ins007_build_appimage.py` — version assertion now dynamic
- `tests/FIX-010/test_fix010_cicd_pipeline.py` — version assertions now dynamic
- `docs/work-rules/testing-protocol.md` — added Version Bump Tests section

## Tests Written
- `tests/FIX-049/test_fix049_version_utils.py`:
  - `test_shared_version_utils_exists` — verifies tests/shared/version_utils.py exists
  - `test_current_version_matches_config_py` — CURRENT_VERSION matches src/launcher/config.py
  - `test_current_version_is_semver` — CURRENT_VERSION is X.Y.Z format
  - `test_current_version_is_not_empty` — CURRENT_VERSION is non-empty
  - `test_no_stale_hardcoded_versions_in_fix014` — no "3.0.0" hardcoded in FIX-014 test
  - `test_no_stale_hardcoded_versions_in_fix017` — no stale version in FIX-017 test
  - `test_no_stale_hardcoded_versions_in_ins005` — no "2.0.1" hardcoded in INS-005 test

## Known Limitations
- Historical version constants (OLD_VERSION, PREVIOUS_VERSION, SKIP_ONE_VERSION, STALE_VERSIONS) remain hardcoded — this is correct and intentional.
- The shared utility requires that `src/launcher/config.py` always contains the VERSION constant in the expected format.
