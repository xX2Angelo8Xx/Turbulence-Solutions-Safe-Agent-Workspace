# Test Report — FIX-019

**Tester:** Tester Agent
**Date:** 2026-03-16
**Iteration:** 1

## Summary

FIX-019 bumps the version string from `1.0.2` to `1.0.3` across 5 source files.
All 5 files were verified to contain the correct `1.0.3` version string.
The developer's 12 tests all pass. 19 Tester edge-case tests were added and all pass.
One pre-existing test failure (INS-005 BUG-045) was observed during the full suite run — it is unrelated to FIX-019 and was already logged in bugs.csv before this review.

**Verdict: PASS**

---

## Code Review

| File | Expected Change | Verified |
|------|----------------|---------|
| `src/launcher/config.py` | `VERSION: str = "1.0.3"` | ✓ |
| `pyproject.toml` | `version = "1.0.3"` | ✓ |
| `src/installer/windows/setup.iss` | `#define MyAppVersion "1.0.3"` | ✓ |
| `src/installer/macos/build_dmg.sh` | `APP_VERSION="1.0.3"` | ✓ |
| `src/installer/linux/build_appimage.sh` | `APP_VERSION="1.0.3"` | ✓ |

Updated test files:

| File | Change |
|------|--------|
| `tests/INS-005/test_ins005_setup_iss.py` | `test_app_version` → expects `1.0.3` |
| `tests/INS-006/test_ins006_build_dmg.py` | `test_app_version` → expects `1.0.3` |
| `tests/INS-007/test_ins007_build_appimage.py` | `test_app_version_embedded` → expects `1.0.3` |
| `tests/FIX-010/test_fix010_cicd_pipeline.py` | 3 version constants → `1.0.3` |
| `tests/FIX-014/test_fix014_version_bump.py` | `EXPECTED_VERSION` → `"1.0.3"` |
| `tests/FIX-017/test_fix017_version_bump.py` | `EXPECTED_VERSION` → `"1.0.3"` |
| `tests/FIX-017/test_fix017_edge_cases.py` | All version constants updated |

All updated test files verified against their expected values.

---

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| FIX-019 developer suite (12 tests) | Unit | Pass | All 5 version locations, old-version absence checks, consistency |
| FIX-019 Tester edge-case suite (19 tests) | Unit | Pass | Semver format, ordering, older-version regression, display version fallback, tag format |
| FIX-019 full suite (31 tests) | Unit | Pass | 31/31 pass |
| Full regression suite | Regression | Pass | 2074 pass, 1 pre-existing fail (INS-005 BUG-045), 29 skipped |

### Edge-Case Test Coverage Added (`tests/FIX-019/test_fix019_edge_cases.py`)

| Class | Tests | What It Validates |
|-------|-------|-------------------|
| `TestSemverFormat` | 4 | Valid X.Y.Z semver, no leading zeros, no whitespace, pyproject.toml also valid |
| `TestVersionOrdering` | 2 | 1.0.3 > 1.0.2 numerically; patch incremented by exactly 1 |
| `TestNoOlderVersions` | 10 | No reference to 1.0.1 or 1.0.0 in any of the 5 files |
| `TestDisplayVersion` | 1 | `get_display_version()` returns `"1.0.3"` via fallback path |
| `TestVersionTagFormat` | 2 | Version usable as `v1.0.3` git tag |

---

## Pre-Existing Failure Noted

**BUG-045** (`test_uninstall_delete_type_is_filesandirs`) — already logged as Open.
- `tests/INS-005/test_ins005_edge_cases.py` line 198 expects regex `Type:\s*filesandirs`
- `setup.iss` correctly uses `Type: filesandordirs` (valid Inno Setup syntax)
- The failure was introduced before FIX-019 (`setup.iss` was corrected in a commit between FIX-012 and FIX-014; the test was not updated)
- **Confirmed pre-existing**: running the test on the pre-FIX-019 commit produces the same failure
- **Not caused by FIX-019**: FIX-019 only changed the `MyAppVersion` define in `setup.iss`

---

## Bugs Found

None new. BUG-045 was already logged before this review.

---

## TODOs for Developer

None. All acceptance criteria met.

---

## Verdict

**PASS** — Set WP FIX-019 to `Done`. All 5 version locations show `1.0.3`. 31/31 FIX-019 tests pass. No new regressions introduced.
