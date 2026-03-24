# Dev Log — FIX-064: Fix FIX-050 hardcoded version tests

## Status
Review

## Assigned To
Developer Agent

## Summary
Replace 5 hardcoded version string assertions (`"3.0.2"`) in `tests/FIX-050/test_fix050.py`
with dynamic comparisons against `CURRENT_VERSION` from `tests/shared/version_utils.py`.

## Problem
The 5 version tests at the bottom of `tests/FIX-050/test_fix050.py` all use the
hardcoded string `"3.0.2"`. After any version bump these tests will fail, forcing
manual edits to the test file. That regression pattern is tracked as BUG-086.

## Implementation

### File changed
- `tests/FIX-050/test_fix050.py`

### Changes made
Replaced the body of each of the 5 version assertion tests:

| Test | Before | After |
|------|--------|-------|
| `test_config_py_version` | Asserted `CURRENT_VERSION == "3.0.2"` | Uses regex to extract VERSION from config.py and asserts it equals `CURRENT_VERSION` |
| `test_pyproject_toml_version` | `assert 'version = "3.0.2"' in content` | `assert f'version = "{CURRENT_VERSION}"' in content` |
| `test_setup_iss_version` | `assert '#define MyAppVersion "3.0.2"' in content` | `assert f'#define MyAppVersion "{CURRENT_VERSION}"' in content` |
| `test_build_dmg_sh_version` | `assert 'APP_VERSION="3.0.2"' in content` | `assert f'APP_VERSION="{CURRENT_VERSION}"' in content` |
| `test_build_appimage_sh_version` | `assert 'APP_VERSION="3.0.2"' in content` | `assert f'APP_VERSION="{CURRENT_VERSION}"' in content` |

`import re` was also added to the top-level imports since `test_config_py_version`
now uses a regex extraction instead of the tautological direct comparison.

## Tests Written
- No new test file created — the test file being modified IS the test deliverable.
- Test suite: `tests/FIX-050/` (the 5 version tests + 7 existing behaviour tests = 12 total)

## Test Results
- **Run:** `pytest tests/FIX-050/ -v`
- **Result:** 31 passed, 0 failed
- **Logged:** TST-2038 (via `scripts/add_test_result.py`)

## Known Limitations
None.
