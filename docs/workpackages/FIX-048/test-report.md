# Test Report — FIX-048

**Tester:** Tester Agent
**Date:** 2026-03-19
**Iteration:** 1

---

## Summary

FIX-048 correctly implements the three shim-fix root causes: `cmd.exe /c` wrapper for `.cmd` files on Windows, `stdin=DEVNULL` on all calls, and a 5 → 30 second timeout increase. The CI workflow `release.yml` embeddable-Python download step is correctly uncommented, and all five version files have been updated to `3.0.1`. The ten developer-written unit tests and eleven tester-added edge-case tests all pass.

**However, the WP introduces two sets of test regressions** that must be resolved before it can be marked Done:

1. **6 tests in `tests/SAF-034/`** — SAF-034 tested the *old* behaviour (no `cmd.exe` wrapper, `timeout=5`). FIX-048 changed that behaviour but did not update those tests.
2. **6 tests in `tests/FIX-047/`** — FIX-047 version tests hardcode `3.0.0`; the FIX-048 bump to `3.0.1` broke them.

Verdict: **FAIL — return to Developer.**

---

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| TST-1856 (developer) – FIX-048 unit suite (10 tests) | Unit | Pass | Already logged by developer |
| TST-1858 – FIX-048 tests incl. 11 tester edge cases (21 total) | Unit | Pass | All pass; see below for edge cases added |
| TST-1859 – SAF-034 regression check (29 tests) | Regression | **FAIL** | 6 failures; BUG-078 logged |
| TST-1860 – FIX-047 regression check (11 tests) | Regression | **FAIL** | 6 failures; BUG-079 logged |

### Tester Edge Cases Added (all pass — `tests/FIX-048/test_fix048.py`)

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
| `test_windows_cmd_wrapper_also_uses_stdin_devnull` | `stdin=DEVNULL` is set even when cmd.exe wrapper is active |
| `test_ci_python_embed_step_is_active` | Python embeddable download step in `release.yml` is uncommented |

---

## Bugs Found

- **BUG-078**: 6 SAF-034 tests broken by FIX-048 behavior change (cmd.exe wrapper + 30 s timeout) — logged in `docs/bugs/bugs.csv`
- **BUG-079**: 6 FIX-047 version tests broken by version bump 3.0.0 → 3.0.1 — logged in `docs/bugs/bugs.csv`

---

## Failing SAF-034 Tests (detail)

All 6 were passing before FIX-048 was committed and now fail:

| Failing Test | Root Cause |
|---|---|
| `test_verify_ts_python_windows_uses_shim_dir_when_exists` | Asserts `args_used[0] == str(fake_cmd)` — but `args_used[0]` is now `"cmd.exe"` |
| `test_verify_ts_python_windows_fallback_to_path` | Asserts `args_used[0] == "C:\\Windows\\ts-python.cmd"` — now `"cmd.exe"` |
| `test_verify_ts_python_windows_shim_dir_takes_precedence` | Same `args_used[0]` assertion — now `"cmd.exe"` |
| `test_verify_ts_python_timeout_message_mentions_5_seconds` | Asserts `"5" in msg` — message now says "30 seconds" |
| `test_verify_ts_python_passes_timeout_5_to_subprocess` | Asserts `timeout == 5` — now `30` |
| `test_verify_ts_python_shim_path_with_spaces` | Asserts `args[0] == str(fake_cmd)` — now `"cmd.exe"` |

---

## TODOs for Developer

- [ ] **[BLOCKING] Fix `tests/SAF-034/test_saf034.py` — update 4 tests for cmd.exe /c wrapper:**
  - `test_verify_ts_python_windows_uses_shim_dir_when_exists`: change `assert str(fake_cmd) == args_used[0]` → assert `args_used[0] == "cmd.exe"` AND `args_used[2] == str(fake_cmd)`.
  - `test_verify_ts_python_windows_fallback_to_path`: change `assert args_used[0] == "C:\\Windows\\ts-python.cmd"` → assert `args_used[0] == "cmd.exe"` AND `args_used[2] == "C:\\Windows\\ts-python.cmd"`.
  - `test_verify_ts_python_windows_shim_dir_takes_precedence`: same pattern — check `args_used[0] == "cmd.exe"` and shim path at `args_used[2]`.
  - `test_verify_ts_python_timeout_message_mentions_5_seconds`: update assertion to `"30 seconds" in msg`; rename test to `test_verify_ts_python_timeout_message_mentions_30_seconds`.

- [ ] **[BLOCKING] Fix `tests/SAF-034/test_saf034_edge.py` — update 2 tests:**
  - `test_verify_ts_python_passes_timeout_5_to_subprocess`: change `== 5` → `== 30`; rename to `test_verify_ts_python_passes_timeout_30_to_subprocess`.
  - `test_verify_ts_python_shim_path_with_spaces`: update assertion from `args[0] == str(fake_cmd)` → assert `args[0] == "cmd.exe"` AND `args[2] == str(fake_cmd)`.

- [ ] **[BLOCKING] Fix `tests/FIX-047/test_fix047_version.py` — update all 6 version assertions from `"3.0.0"` to `"3.0.1"`** (the expected version string in each check).

---

## Verdict

**FAIL — return to Developer (Iteration 2).**

The implementation is correct and the 21 FIX-048 tests (10 developer + 11 tester) all pass. However, 12 pre-existing tests in SAF-034 and FIX-047 are now broken. The testing protocol requires all existing tests to pass before a WP can be marked Done. The Developer must update those 12 tests as detailed in the TODOs above.

**Push status:** The original commit `ea54308` cannot be pushed by this agent (insufficient GITHUB_TOKEN permissions). The human or CI pipeline must push after the Developer fixes the regressions and the Tester re-approves.
