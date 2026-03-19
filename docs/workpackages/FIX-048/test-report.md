# Test Report — FIX-048

**Tester:** Tester Agent
**Date:** 2026-03-19
**Iteration:** 2

---

## Summary

All 12 regressions identified in Iteration 1 have been resolved by the Developer. The full targeted suite of 61 tests (21 FIX-048 + 29 SAF-034 + 11 FIX-047) now passes with zero failures.

Verified changes:
- `verify_ts_python()` uses `cmd.exe /c` wrapper for `.cmd` shims on Windows ✓
- `stdin=subprocess.DEVNULL` is always passed ✓
- Timeout is 30 seconds; error message says "30 seconds" ✓
- CI `release.yml` Python embeddable download step is uncommented ✓
- All 5 version locations read `3.0.1` ✓
- All 12 previously-failing SAF-034 / FIX-047 regression tests updated and passing ✓

---

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| TST-1858 – FIX-048: 21 tests (10 dev + 11 tester edge cases) | Unit | Pass | All pass |
| TST-1859 – SAF-034: 29 tests (regression check) | Regression | ~~FAIL~~ → **Pass** | 6 tests updated for cmd.exe wrapper + 30 s timeout |
| TST-1860 – FIX-047: 11 tests (regression check) | Regression | ~~FAIL~~ → **Pass** | TARGET_VERSION updated to 3.0.1 |
| TST-1862 – FIX-048 Iteration 2: full 61-test suite | Regression | **Pass** | 61 passed / 0 failed / 0 errors |

### Tester Edge Cases (all pass — `tests/FIX-048/test_fix048.py`)

| Test | What It Validates |
|------|-------------------|
| `test_version_config_py` | `src/launcher/config.py` contains `3.0.1` |
| `test_version_pyproject_toml` | `pyproject.toml` version field is `3.0.1` |
| `test_version_setup_iss` | `setup.iss` `MyAppVersion` is `3.0.1` |
| `test_version_build_dmg_sh` | `build_dmg.sh` `APP_VERSION` is `3.0.1` |
| `test_version_build_appimage_sh` | `build_appimage.sh` `APP_VERSION` is `3.0.1` |
| `test_version_consistency_all_five_locations` | All 5 locations agree on exactly `3.0.1` |
| `test_file_not_found_error_handled` | `FileNotFoundError` from `subprocess.run` returns `(False, msg)` |
| `test_oserror_handled` | `OSError` from `subprocess.run` returns `(False, msg)` |
| `test_macos_no_cmd_wrapper` | macOS does NOT use `cmd.exe /c` wrapper |
| `test_windows_cmd_wrapper_also_uses_stdin_devnull` | `stdin=DEVNULL` set even when cmd.exe wrapper is active |
| `test_ci_python_embed_step_is_active` | Python embeddable download step in `release.yml` is uncommented |

---

## Bugs Found

- No new bugs found in Iteration 2.
- BUG-077 (original shim timeout hang) — confirmed fixed.
- BUG-078 / BUG-079 (SAF-034 / FIX-047 regression tests) — confirmed resolved by Developer.

---

## TODOs for Developer

None.

---

## Verdict

**PASS — mark WP as Done.**

All 61 tests in the FIX-048 / SAF-034 / FIX-047 suite pass. All acceptance criteria are met. The implementation is correct, secure (no `shell=True`, list args, `stdin=DEVNULL`), and all regressions from Iteration 1 are resolved.

**Push status:** GITHUB_TOKEN lacks push access in this environment. A human must run `git push origin copilot/hotfix-v3-0-1-bundled-python-runtime` after this commit.
