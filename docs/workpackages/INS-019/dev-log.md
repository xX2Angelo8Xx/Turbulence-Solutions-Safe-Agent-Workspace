# Dev Log — INS-019: Create ts-python shim and config system

**WP ID:** INS-019  
**Category:** Installer  
**Assigned To:** Developer Agent  
**Branch:** INS-019/create-ts-python-shim  
**Date:** 2026-03-19  
**Status:** In Progress → Review  

---

## Summary

Implements the ts-python shim system that allows the bundled Python runtime (installed by INS-018/INS-021) to be invoked as `ts-python` from any terminal. The shim reads the Python executable path from a config file (`python-path.txt`) at a well-known fixed location, enabling the runtime path to be updated without changing workspace hook configurations.

---

## Implementation

### Files Created

| File | Purpose |
|------|---------|
| `src/installer/shims/ts-python.cmd` | Windows batch shim (CRLF line endings) |
| `src/installer/shims/ts-python` | macOS/Linux shell script shim (LF line endings) |
| `src/installer/shims/README.md` | Shim system architecture documentation |
| `src/launcher/core/shim_config.py` | Python helper module for shim configuration |
| `tests/INS-019/test_ins019_shims.py` | Test suite |

### Design Decisions

1. **Config file location (Windows):** `%LOCALAPPDATA%\TurbulenceSolutions\python-path.txt` — uses the standard Windows per-user app data location, not a system-wide path. This isolates it per-user and does not require admin rights.

2. **Config file location (macOS/Linux):** `${XDG_DATA_HOME:-$HOME/.local/share}/TurbulenceSolutions/python-path.txt` — follows the XDG Base Directory spec for portability across Linux distributions.

3. **Shim error messages:** Both shims output to stderr and exit with code 1 on failure, providing actionable error messages pointing users to reinstall or use the Relocate Python Runtime option.

4. **Line endings:** `.cmd` file uses CRLF (required for Windows CMD), shell script uses LF (required for Unix shebangs to work).

5. **`shim_config.py` module:** Pure Python, no external dependencies. Uses only stdlib (`os`, `platform`, `pathlib`). Provides `get_config_dir()`, `get_shim_dir()`, `get_python_path_config()`, `write_python_path()`, `read_python_path()`, `verify_shim()`.

6. **Path validation:** `shim_config.py` does not validate against path traversal (that's the installer's responsibility), but returns `None` from `read_python_path()` when the config is absent or empty, preventing any forwarding attempt.

---

## Tests Written

**File:** `tests/INS-019/test_ins019_shims.py`

| Test | Category | Description |
|------|----------|-------------|
| `test_windows_shim_exists` | Unit | ts-python.cmd exists in shims/ |
| `test_unix_shim_exists` | Unit | ts-python exists in shims/ |
| `test_readme_exists` | Unit | shims/README.md exists |
| `test_windows_shim_content_reads_config` | Unit | .cmd reads %CONFIG% variable |
| `test_windows_shim_content_forwards_args` | Unit | .cmd uses %* for argument forwarding |
| `test_windows_shim_missing_config_error` | Unit | .cmd errors if config file missing |
| `test_windows_shim_missing_python_error` | Unit | .cmd errors if python exe missing |
| `test_windows_shim_crlf_line_endings` | Unit | .cmd has CRLF line endings |
| `test_unix_shim_shebang` | Unit | shell script starts with #!/bin/sh |
| `test_unix_shim_reads_config` | Unit | shell script reads CONFIG variable |
| `test_unix_shim_exec_python` | Unit | shell script uses exec with $@ |
| `test_unix_shim_missing_config_error` | Unit | shell script errors if config missing |
| `test_unix_shim_missing_python_error` | Unit | shell script errors if python not executable |
| `test_unix_shim_lf_line_endings` | Unit | shell script has LF-only line endings |
| `test_get_config_dir_windows` | Unit | Windows config dir uses LOCALAPPDATA |
| `test_get_config_dir_windows_fallback` | Unit | Windows fallback when LOCALAPPDATA missing |
| `test_get_config_dir_unix` | Unit | Unix config dir uses XDG_DATA_HOME |
| `test_get_config_dir_unix_fallback` | Unit | Unix fallback when XDG_DATA_HOME missing |
| `test_get_shim_dir` | Unit | Shim dir is config dir / bin |
| `test_get_python_path_config` | Unit | Config file is config dir / python-path.txt |
| `test_write_python_path_creates_file` | Unit | write_python_path() creates file with correct content |
| `test_write_python_path_creates_parent_dirs` | Unit | write_python_path() creates parent directories |
| `test_read_python_path_returns_path` | Unit | read_python_path() returns Path when file exists |
| `test_read_python_path_returns_none_missing` | Unit | read_python_path() returns None when file missing |
| `test_read_python_path_returns_none_empty` | Unit | read_python_path() returns None for empty file |
| `test_verify_shim_ok` | Unit | verify_shim() returns (True, msg) when config valid |
| `test_verify_shim_no_config` | Unit | verify_shim() returns (False, msg) when config missing |
| `test_verify_shim_bad_path` | Unit | verify_shim() returns (False, msg) when exe missing |

---

## Known Limitations

- The shim files are templates; actual installation is handled by INS-021 (Inno Setup integration).
- PATH modification is documented in the shim README but implemented by INS-021.
- macOS/Linux PATH modification is out of scope for this WP (handled by future WP).
