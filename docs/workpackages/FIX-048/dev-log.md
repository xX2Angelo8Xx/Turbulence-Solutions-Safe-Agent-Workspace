# Dev Log — FIX-048

**Developer:** Developer Agent
**Date started:** 2025-07-25
**Iteration:** 1

## Objective
Fix verify_ts_python() in shim_config.py to prevent hangs on Windows ARM and all platforms, increase timeout from 5 to 30 seconds, uncomment the Python embeddable download step in the CI release workflow, and bump the version from 3.0.0 to 3.0.1 in all 5 locations.

## Implementation Summary
Three root causes were addressed:

1. **cmd.exe /c for .cmd files (Windows):** Added a `use_cmd_wrapper` flag in `verify_ts_python()`. When the resolved shim path ends with `.cmd`, the subprocess is invoked as `["cmd.exe", "/c", shim_exe, "-c", "..."]` instead of `[shim_exe, "-c", "..."]`. This ensures correct interpretation of batch files on Windows ARM under x64 emulation and prevents stdin inheritance hangs.

2. **stdin=DEVNULL:** Added `stdin=subprocess.DEVNULL` to the subprocess.run call to prevent the GUI process's stdin from being inherited, which could cause cmd.exe to hang waiting for input.

3. **Timeout increased:** Timeout raised from 5 to 30 seconds. Timeout error message updated to match ("30 seconds").

4. **CI step uncommented:** Removed the `# ` prefix from the Python embeddable download step in `.github/workflows/release.yml` so installers are built with the bundled Python runtime.

5. **Version bump to 3.0.1:** Updated all 5 version locations: `src/launcher/config.py`, `pyproject.toml`, `src/installer/windows/setup.iss`, `src/installer/macos/build_dmg.sh`, `src/installer/linux/build_appimage.sh`.

6. **Bug and WP records:** Added BUG-077 to `docs/bugs/bugs.csv` and FIX-048 to `docs/workpackages/workpackages.csv`.

## Files Changed
- `src/launcher/core/shim_config.py` — Fixed verify_ts_python(): added cmd.exe /c wrapper for .cmd files, stdin=DEVNULL, timeout 5→30, updated timeout error message
- `.github/workflows/release.yml` — Uncommented Python embeddable download step
- `src/launcher/config.py` — Version 3.0.0 → 3.0.1
- `pyproject.toml` — Version 3.0.0 → 3.0.1
- `src/installer/windows/setup.iss` — Version 3.0.0 → 3.0.1
- `src/installer/macos/build_dmg.sh` — Version 3.0.0 → 3.0.1
- `src/installer/linux/build_appimage.sh` — Version 3.0.0 → 3.0.1
- `docs/bugs/bugs.csv` — Added BUG-077
- `docs/workpackages/workpackages.csv` — Added FIX-048
- `tests/FIX-048/test_fix048.py` — New test file

## Tests Written
- `test_windows_cmd_uses_cmd_exe_wrapper` — Verifies that on Windows with a .cmd shim, subprocess.run is called with ["cmd.exe", "/c", shim_exe, ...] as first arg
- `test_windows_non_cmd_no_wrapper` — Verifies that on Windows with a non-.cmd shim, no cmd.exe wrapper is used
- `test_uses_stdin_devnull` — Verifies that subprocess.run is always called with stdin=subprocess.DEVNULL
- `test_timeout_is_30` — Verifies that the timeout= argument passed to subprocess.run is 30
- `test_timeout_error_message_says_30_seconds` — Verifies that the TimeoutExpired message contains "30 seconds" and not "5 seconds"
- `test_success_returns_true` — Verifies existing success behavior still works
- `test_nonzero_exit_returns_false` — Verifies existing failure behavior still works
- `test_shim_not_found_returns_false` — Verifies not-found case still works
- `test_windows_shim_dir_used_first` — Verifies .cmd shim in shim dir takes priority over PATH
- `test_windows_fallback_to_path_cmd_wrapper` — Verifies fallback PATH .cmd also gets cmd.exe wrapper

## Iteration 2 — 2025-07-25

### Tester Feedback Addressed
- **SAF-034 test_verify_ts_python_windows_uses_shim_dir_when_exists**: Updated assertion from `args_used[0] == str(fake_cmd)` → `args_used[0] == "cmd.exe"` and `args_used[2] == str(fake_cmd)` to reflect cmd.exe /c wrapper.
- **SAF-034 test_verify_ts_python_windows_fallback_to_path**: Same pattern — updated to check `args_used[0] == "cmd.exe"` and path at index 2.
- **SAF-034 test_verify_ts_python_windows_shim_dir_takes_precedence**: Same update.
- **SAF-034 test_verify_ts_python_timeout_message_mentions_5_seconds**: Renamed to `test_verify_ts_python_timeout_message_mentions_30_seconds`; updated assertion to `"30" in msg`.
- **SAF-034 test_verify_ts_python_passes_timeout_5_to_subprocess** (in test_saf034_edge.py): Renamed to `test_verify_ts_python_passes_timeout_30_to_subprocess`; updated `== 5` → `== 30`.
- **SAF-034 test_verify_ts_python_shim_path_with_spaces** (in test_saf034_edge.py): Updated to check `args[0] == "cmd.exe"` and `args[2] == str(fake_cmd)`.
- **FIX-047 TARGET_VERSION**: Updated from `"3.0.0"` to `"3.0.1"` in test_fix047_version.py.

### Additional Changes
- `tests/SAF-034/test_saf034.py` — Updated 4 tests for new cmd.exe /c wrapper behavior and 30s timeout
- `tests/SAF-034/test_saf034_edge.py` — Updated 2 tests for 30s timeout and cmd.exe wrapper with spaces
- `tests/FIX-047/test_fix047_version.py` — Updated TARGET_VERSION to 3.0.1

### Tests Added/Updated
- All 12 previously-failing regression tests now pass
- Full suite: 61 tests (21 FIX-048 + 29 SAF-034 + 11 FIX-047) — 61/61 pass

- The cmd.exe /c wrapper applies to any shim path ending with `.cmd` (case-insensitive), which is the correct heuristic for Windows batch files.
- The CI fix (uncommenting the download step) requires internet access during the CI build; this is the expected behavior in the release workflow.
