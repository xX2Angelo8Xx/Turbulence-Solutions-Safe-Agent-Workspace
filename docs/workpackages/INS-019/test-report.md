# Test Report — INS-019

**Tester:** Tester Agent
**Date:** 2026-03-19
**Iteration:** 1

## Summary

INS-019 delivers the ts-python shim system: a Windows batch shim (`ts-python.cmd`), a macOS/Linux shell script shim (`ts-python`), and a pure-Python helper module (`shim_config.py`). All 59 tests pass (38 developer + 21 Tester edge-case). No regressions in the full suite (3807 passed, 82 pre-existing failures unchanged). **PASS.**

## Tests Executed

### Developer tests — `tests/INS-019/test_ins019_shims.py` (38 tests)

| Test | Type | Result | Notes |
|------|------|--------|-------|
| test_windows_shim_exists | Unit | PASS | ts-python.cmd present in shims/ |
| test_unix_shim_exists | Unit | PASS | ts-python present in shims/ |
| test_readme_exists | Unit | PASS | shims/README.md present |
| test_windows_shim_content_reads_config | Unit | PASS | .cmd reads %CONFIG% variable |
| test_windows_shim_content_forwards_args | Unit | PASS | .cmd uses %* for argument forwarding |
| test_windows_shim_missing_config_error | Unit | PASS | .cmd errors with code 1 if config missing |
| test_windows_shim_missing_python_error | Unit | PASS | .cmd errors with code 1 if python exe missing |
| test_windows_shim_crlf_line_endings | Unit | PASS | .cmd has CRLF line endings |
| test_unix_shim_shebang | Unit | PASS | shell script starts with #!/bin/sh |
| test_unix_shim_reads_config | Unit | PASS | shell script reads CONFIG variable |
| test_unix_shim_exec_python | Unit | PASS | shell script uses exec with $@ |
| test_unix_shim_missing_config_error | Unit | PASS | shell script errors with code 1 if config missing |
| test_unix_shim_missing_python_error | Unit | PASS | shell script errors if python not executable |
| test_unix_shim_lf_line_endings | Unit | PASS | shell script has LF-only line endings |
| test_get_config_dir_windows | Unit | PASS | Windows config dir uses LOCALAPPDATA |
| test_get_config_dir_windows_fallback | Unit | PASS | Windows fallback when LOCALAPPDATA missing |
| test_get_config_dir_unix | Unit | PASS | Unix config dir uses XDG_DATA_HOME |
| test_get_config_dir_unix_fallback | Unit | PASS | Unix fallback when XDG_DATA_HOME missing |
| test_get_shim_dir | Unit | PASS | Shim dir is config_dir / bin |
| test_get_python_path_config | Unit | PASS | Config file is config_dir / python-path.txt |
| test_write_python_path_creates_file | Unit | PASS | write_python_path() creates file with correct content |
| test_write_python_path_creates_parent_dirs | Unit | PASS | write_python_path() creates parent directories |
| test_read_python_path_returns_path | Unit | PASS | read_python_path() returns Path when file exists |
| test_read_python_path_returns_none_missing | Unit | PASS | read_python_path() returns None when file missing |
| test_read_python_path_returns_none_empty | Unit | PASS | read_python_path() returns None for empty file |
| test_verify_shim_ok | Unit | PASS | verify_shim() returns (True, msg) when config valid |
| test_verify_shim_no_config | Unit | PASS | verify_shim() returns (False, msg) when config missing |
| test_verify_shim_bad_path | Unit | PASS | verify_shim() returns (False, msg) when exe missing |

### Tester edge-case tests — `tests/INS-019/test_ins019_edge_cases.py` (21 tests)

| Test | Type | Result | Notes |
|------|------|--------|-------|
| test_read_python_path_traversal_returned_as_is | Security | PASS | Traversal path returned as-is; verify_shim fails closed |
| test_verify_shim_traversal_path_returns_false | Security | PASS | verify_shim returns False for non-existent traversal path |
| test_verify_shim_existence_only_check | Security | PASS | Existence-only check is the documented contract |
| test_windows_shim_python_path_is_quoted | Security | PASS | %PYTHON_PATH% double-quoted — injection prevented |
| test_unix_shim_python_path_is_double_quoted | Security | PASS | "$PYTHON_PATH" double-quoted — word split / glob prevented |
| test_unix_shim_args_double_quoted | Security | PASS | "$@" used — per-argument boundaries preserved |
| test_read_python_path_crlf_stripped | Unit | PASS | CRLF ending stripped from config path |
| test_read_python_path_bom_causes_fail_closed | Unit | PASS | UTF-8 BOM → invalid path → verify_shim fails closed |
| test_read_python_path_unicode_path | Unit | PASS | Non-ASCII path decoded correctly (UTF-8) |
| test_read_python_path_embedded_newline_safe | Unit | PASS | Embedded newline produces invalid path → fail closed |
| test_get_config_dir_windows_empty_localappdata | Unit | PASS | Empty LOCALAPPDATA falls through to home fallback |
| test_get_config_dir_unix_empty_xdg_data_home | Unit | PASS | Empty XDG_DATA_HOME falls through to home fallback |
| test_read_python_path_very_long_path | Unit | PASS | 200-char path segment handled without error |
| test_write_read_roundtrip | Unit | PASS | write then read reproduces exact path |
| test_write_python_path_overwrites_existing | Unit | PASS | Overwrite replaces old content completely |
| test_read_python_path_propagates_permission_error | Unit | PASS | PermissionError propagates (fail-closed) |
| test_get_config_dir_returns_path_object_windows | Unit | PASS | Returns Path (not str) on Windows |
| test_get_config_dir_returns_path_object_unix | Unit | PASS | Returns Path (not str) on Unix |
| test_get_python_path_config_returns_path_object | Unit | PASS | Returns Path (not str) for config getter |
| test_unix_shim_home_variable_in_fallback | Unit | PASS | $HOME referenced in XDG fallback expression |
| test_unix_shim_xdg_default_value_expression | Unit | PASS | ${XDG_DATA_HOME:-…} POSIX syntax present |

### Regression — full suite

| Run | Result | Notes |
|-----|--------|-------|
| Full suite post-INS-019 (Developer logged as TST-1850) | 3807 passed / 82 pre-existing failures / 29 skipped | Zero new failures introduced |
| Tester full suite with edge-case tests (TST-1852) | 59/59 INS-019 tests pass; no new regressions | |

## Bugs Found

None. No bugs identified during Tester review.

## TODOs for Developer

None.

## Verdict

**PASS** — All 59 tests pass (38 developer + 21 Tester edge-case). Zero new regressions in full suite. Security surface reviewed: shim quotation correct, path traversal fail-closed, BOM/CRLF/newline edge cases all fail safely. WP marked **Done**.
