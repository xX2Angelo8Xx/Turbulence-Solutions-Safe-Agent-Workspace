# Test Report — FIX-070

**Tester:** Tester Agent
**Date:** 2026-03-21
**Iteration:** 1

## Summary

Version bump from 3.1.1 → 3.1.2 correctly applied across all 5 canonical
version locations. All 8 tests pass. No regressions introduced by this WP.
Pre-existing failures in the full suite (76) are documented below and are
unrelated to this change.

## Version Files Verified

| File | Field | Value |
|------|-------|-------|
| `src/launcher/config.py` | `VERSION` | `"3.1.2"` ✓ |
| `pyproject.toml` | `version` | `"3.1.2"` ✓ |
| `src/installer/windows/setup.iss` | `MyAppVersion` | `"3.1.2"` ✓ |
| `src/installer/macos/build_dmg.sh` | `APP_VERSION` | `"3.1.2"` ✓ |
| `src/installer/linux/build_appimage.sh` | `APP_VERSION` | `"3.1.2"` ✓ |

Note from dev-log: installer scripts were at `3.1.0` (not `3.1.1`), so this WP
bumped them by two patch levels. This is correct — the files now match the
canonical version.

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| `test_config_py_version` | Regression | PASS | VERSION == CURRENT_VERSION |
| `test_pyproject_toml_version` | Regression | PASS | version == CURRENT_VERSION |
| `test_setup_iss_version` | Regression | PASS | MyAppVersion == CURRENT_VERSION |
| `test_build_dmg_sh_version` | Regression | PASS | APP_VERSION == CURRENT_VERSION |
| `test_build_appimage_sh_version` | Regression | PASS | APP_VERSION == CURRENT_VERSION |
| `test_all_versions_consistent` | Regression | PASS | All 5 sources agree on same version |
| `test_current_version_is_3_1_2` (tester) | Regression | PASS | CURRENT_VERSION == "3.1.2" hardened assertion |
| `test_no_stale_3_1_1_in_version_files` (tester) | Regression | PASS | No stale 3.1.1 strings in any version file |

**TST-ID logged:** TST-1991

### Full suite context

Full suite run (excluding 14 YAML-import-broken collection errors):
- **4318 passed, 76 failed, 2 skipped**
- All 76 failures are pre-existing in WPs FIX-028, FIX-031, FIX-037, FIX-038,
  FIX-039, FIX-049, FIX-050, INS-004, INS-019, SAF-010, SAF-022, SAF-025 and
  are not caused by FIX-070.
- FIX-050 tests check for hardcoded version `3.0.2` — these were already failing
  before this WP (they are an acknowledged pre-existing issue from the FIX-050
  test file never being updated to use dynamic version lookup).

## Security Analysis

- No attack surface introduced. This is a plain string constant update.
- No secrets, credentials, or user-controlled input involved.
- Version strings are used only for display and installer metadata — no security
  boundary crossed.

## Edge Cases Checked

- No stale `3.1.1` strings remain in any of the 5 version files.
- `CURRENT_VERSION` as read by `tests/shared/version_utils.py` equals `"3.1.2"`.
- All 5 sources agree on the same version (checked by `test_all_versions_consistent`).
- Installer scripts that were at `3.1.0` are now correctly set to `3.1.2`.

## Bugs Found

None.

## TODOs for Developer

None.

## Verdict

**PASS — mark WP as Done.**

All 8 FIX-070 tests pass. No regressions. Workspace validator clean (exit 0).
Version bump is complete, consistent, and correct.
