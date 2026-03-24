# Test Report — FIX-064: Fix FIX-050 Hardcoded Version Tests

## Verdict: PASS

**Date:** 2026-03-24  
**Tester:** Tester Agent  
**Branch:** `FIX-064/fix-hardcoded-version-tests`

---

## Scope

FIX-064 replaces 5 hardcoded `"3.0.2"` version assertions in
`tests/FIX-050/test_fix050.py` with dynamic comparisons against
`CURRENT_VERSION` from `tests/shared/version_utils.py`.

---

## Code Review

**File changed:** `tests/FIX-050/test_fix050.py`

| Item | Verdict |
|------|---------|
| `import re` added at top of file | ✅ Correct |
| `from tests.shared.version_utils import CURRENT_VERSION` added | ✅ Consistent with FIX-058, FIX-061, FIX-070 |
| `test_config_py_version` — uses `re.search` + asserts `match.group(1) == CURRENT_VERSION` | ✅ Self-validating and robust |
| `test_pyproject_toml_version` — `assert f'version = "{CURRENT_VERSION}"' in content` | ✅ Correct pattern |
| `test_setup_iss_version` — `assert f'#define MyAppVersion "{CURRENT_VERSION}"' in content` | ✅ Correct pattern |
| `test_build_dmg_sh_version` — `assert f'APP_VERSION="{CURRENT_VERSION}"' in content` | ✅ Correct pattern |
| `test_build_appimage_sh_version` — `assert f'APP_VERSION="{CURRENT_VERSION}"' in content` | ✅ Correct pattern |
| No hardcoded `"3.0.2"` string remaining | ✅ Confirmed |
| Pattern matches other migrated files (FIX-058, FIX-061, FIX-070) | ✅ Consistent |

The `test_config_py_version` implementation is notably stronger than a direct
tautological comparison — it extracts the version value via regex and compares
it to `CURRENT_VERSION`, ensuring the regex pattern and the constant agree.

---

## Test Runs

### FIX-050 full suite (31 tests)
- **Command:** `pytest tests/FIX-050/ -v --tb=short`
- **Result:** 31 passed, 0 failed
- **Logged:** TST-2039

### FIX-064 Tester edge-case tests (9 tests — new)
- **Command:** `pytest tests/FIX-064/ -v --tb=short`
- **Result:** 9 passed, 0 failed
- **Logged:** TST-2040

### Related version-migration tests (FIX-050 + FIX-058 + FIX-061 + FIX-070)
- **Command:** `pytest tests/FIX-050 tests/FIX-058 tests/FIX-061 tests/FIX-070 -q`
- **Result:** 53 passed, 0 failed

### Full suite (modulo pre-existing yaml import errors)
- **Command:** `pytest tests/ -q --tb=short` (ignoring 14 yaml-module errors)
- **Result:** 4559 passed, 71 failed, 2 skipped, 1 xfailed
- **Note:** All 71 failures are in unrelated WPs (INS-019, SAF-010, SAF-022,
  SAF-025). None were introduced by FIX-064. The yaml import errors in 14 test
  files (FIX-010, FIX-011, FIX-029, INS-013–INS-017) are also pre-existing
  environment issues unrelated to this WP.

---

## Edge-Case Tests Added

`tests/FIX-064/test_fix064_no_hardcoded_versions.py` — 9 tests:

| Test | Purpose |
|------|---------|
| `test_no_hardcoded_302_version_string` | Regression guard: confirms "3.0.2" string removed |
| `test_current_version_imported_in_test_fix050` | Confirms dynamic import pattern applied |
| `test_version_function_uses_current_version[test_config_py_version]` | Body uses CURRENT_VERSION, no semver literal |
| `test_version_function_uses_current_version[test_pyproject_toml_version]` | Body uses CURRENT_VERSION, no semver literal |
| `test_version_function_uses_current_version[test_setup_iss_version]` | Body uses CURRENT_VERSION, no semver literal |
| `test_version_function_uses_current_version[test_build_dmg_sh_version]` | Body uses CURRENT_VERSION, no semver literal |
| `test_version_function_uses_current_version[test_build_appimage_sh_version]` | Body uses CURRENT_VERSION, no semver literal |
| `test_current_version_importable` | CURRENT_VERSION is a non-empty valid semver string |
| `test_version_utils_uses_regex_not_hardcoded` | version_utils.py uses re.search, no hardcoded literal |

---

## Security Considerations

No security concerns. This WP only modifies test assertions to read a version
dynamically from a local config file within the repository. No external inputs,
no credential handling, no subprocess calls.

---

## Pre-Done Checklist

- [x] `docs/workpackages/FIX-064/dev-log.md` exists and is non-empty
- [x] `docs/workpackages/FIX-064/test-report.md` written by Tester
- [x] Test files in `tests/FIX-064/` with 9 tests
- [x] Test results logged via `scripts/add_test_result.py` (TST-2039, TST-2040)
- [x] `scripts/validate_workspace.py --wp FIX-064` returns clean (exit 0)
- [x] `git add -A` staged; committed; pushed

---

## Conclusion

All requirements met. The 5 hardcoded version assertions have been correctly
replaced with dynamic `CURRENT_VERSION` comparisons. The implementation is
consistent with the pattern established in FIX-058, FIX-061, and FIX-070. All
31 FIX-050 tests and 9 new Tester edge-case tests pass.

**WP FIX-064 → Done.**
