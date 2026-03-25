# Test Report — FIX-077

**Tester:** Tester Agent
**Date:** 2026-03-26
**Iteration:** 1

## Summary

FIX-077 bumps the version constant from `3.2.1` to `3.2.2` across all 5 canonical version files and
repairs the `FIX-070` regression test suite. The implementation is correct and complete. All 21 tests
(13 FIX-077 + 8 FIX-070) pass without regressions introduced by this WP.

The 73 full-suite failures reported during the Regression run are **pre-existing failures** unrelated to
FIX-077 — confirmed by checking them on the base commit without FIX-077's changes applied.

## Version File Verification

| File | Field | Value | Status |
|------|-------|-------|--------|
| `src/launcher/config.py` | `VERSION` | `"3.2.2"` | ✅ |
| `pyproject.toml` | `version` | `"3.2.2"` | ✅ |
| `src/installer/windows/setup.iss` | `MyAppVersion` | `"3.2.2"` | ✅ |
| `src/installer/macos/build_dmg.sh` | `APP_VERSION` | `"3.2.2"` | ✅ |
| `src/installer/linux/build_appimage.sh` | `APP_VERSION` | `"3.2.2"` | ✅ |

Stale `3.2.1` scan across all `src/` files: **no matches** — clean.

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| `test_config_py_is_322` | Unit | PASS | VERSION constant 3.2.2 confirmed |
| `test_pyproject_toml_is_322` | Unit | PASS | pyproject.toml version 3.2.2 confirmed |
| `test_setup_iss_is_322` | Unit | PASS | MyAppVersion 3.2.2 confirmed |
| `test_build_dmg_sh_is_322` | Unit | PASS | APP_VERSION 3.2.2 confirmed |
| `test_build_appimage_sh_is_322` | Unit | PASS | APP_VERSION 3.2.2 confirmed |
| `test_no_stale_321_in_any_version_file` | Unit | PASS | No 3.2.1 in any version file |
| `test_all_version_files_agree` | Unit | PASS | All 5 files consistent at 3.2.2 |
| `test_shared_version_utils_current_version_is_322` (edge) | Unit | PASS | CURRENT_VERSION from version_utils.py reads 3.2.2 |
| `test_get_display_version_returns_322` (edge) | Unit | PASS | Fallback path (PackageNotFoundError) returns VERSION constant 3.2.2 |
| `test_check_for_update_no_update_when_at_same_version` (edge) | Unit | PASS | (False, "3.2.2") for same-version mock |
| `test_check_for_update_detects_newer_version` (edge) | Unit | PASS | (True, "3.2.3") for newer mock tag |
| `test_parse_version_322_correct` (edge) | Unit | PASS | parse_version("3.2.2") == (3, 2, 2) |
| `test_no_stale_321_in_docs_version_bump_wp` (edge) | Unit | PASS | dev-log.md contains target version 3.2.2 |
| `FIX-070` suite (8 tests) | Regression | PASS | All 8 FIX-070 version tests pass with 3.2.2 |
| Full regression suite | Regression | NOTE | 73 pre-existing failures (confirmed on base commit), 6828 passed — none caused by FIX-077 |

## Edge-Case Analysis

- **`CURRENT_VERSION` from `tests/shared/version_utils.py`:** Reads dynamically from `config.py` → correctly returns `"3.2.2"`.
- **`get_display_version()` fallback path:** When package is not installed (`PackageNotFoundError`), falls back to the `VERSION` constant `"3.2.2"`. Note: in this dev environment the installed `.dist-info` is stale at `3.1.0` (pre-existing known issue, not in scope of FIX-077).
- **`check_for_update("3.2.2")` at same version:** Returns `(False, "3.2.2")` — no false update loop.
- **`check_for_update("3.2.2")` for newer tag:** Returns `(True, "3.2.3")` — update detection still works.
- **`parse_version("3.2.2")`:** Returns `(3, 2, 2)` — semantic version parsing is correct.
- **No stale `3.2.1` in source:** Full PowerShell scan of `src/` confirms zero remaining references.

## Bugs Found

No new bugs found during testing.

## TODOs for Developer

None.

## Verdict

**PASS — mark WP as Done.**

All 5 version files are correct. All 21 WP-specific tests pass. FIX-070 regression suite updated and passing. BUG-131, BUG-133, and BUG-134 are resolved by this version bump (code fixes were already merged; rebuild from HEAD delivers them to users).
