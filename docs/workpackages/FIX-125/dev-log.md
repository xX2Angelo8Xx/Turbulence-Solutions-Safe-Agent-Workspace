# Dev Log — FIX-125: Fix build_windows.py ISCC and PyInstaller issues

**Status:** In Progress  
**Branch:** FIX-125/build-script-fixes  
**Assigned To:** Developer Agent  
**Date Started:** 2026-04-07  

---

## Prior Art Check

No ADRs in `docs/decisions/index.jsonl` relate to `build_windows.py`, PyInstaller invocation, or ISCC path resolution. No prior architectural decisions to acknowledge.

---

## Problem Summary

`scripts/build_windows.py` has two defects discovered during local testing:

### Issue 1: ISCC.exe not found at per-user install path
`find_iscc()` only checks `C:\Program Files (x86)\...` and `C:\Program Files\...`, missing the per-user install path `%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe`.

### Issue 2: PyInstaller subprocess uses bare `pyinstaller` command
`step_pyinstaller()` calls `["pyinstaller", "launcher.spec"]` which fails with `FileNotFoundError` when `pyinstaller` is not on the system PATH (it lives in `.venv\Scripts\`).

---

## Implementation

### Fix 1 — `_ISCC_FALLBACK_PATHS` (scripts/build_windows.py)
Added a third entry using `os.environ.get("LOCALAPPDATA", "")` to avoid hardcoding the username:
```python
import os
...
_ISCC_FALLBACK_PATHS = [
    Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"),
    Path(r"C:\Program Files\Inno Setup 6\ISCC.exe"),
    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Inno Setup 6" / "ISCC.exe",
]
```

### Fix 2 — `step_pyinstaller()` (scripts/build_windows.py)
Changed command from bare `pyinstaller` to `sys.executable -m PyInstaller` with `-y` flag:
```python
cmd = [sys.executable, "-m", "PyInstaller", "launcher.spec", "-y"]
```

### MNT-031 test update (tests/MNT-031/test_mnt031_build_windows.py)
Updated `test_dry_run_prints_pyinstaller_command`: the assertion `assert "pyinstaller" in captured.out` now reads `assert "PyInstaller" in captured.out` to match the module-style invocation printed output.

---

## Files Changed

- `scripts/build_windows.py` — fix ISCC fallback paths + fix PyInstaller command
- `tests/MNT-031/test_mnt031_build_windows.py` — update dry-run assertion for new command format
- `tests/FIX-125/test_fix125_build_fixes.py` — new tests

---

## Tests Written

- `tests/FIX-125/test_fix125_build_fixes.py`:
  1. `test_find_iscc_localappdata_path` — verifies ISCC found at LOCALAPPDATA path when other paths absent
  2. `test_find_iscc_localappdata_path_not_found_falls_through` — LOCALAPPDATA path missing causes sys.exit(1)
  3. `test_step_pyinstaller_uses_sys_executable` — verifies command uses `sys.executable`
  4. `test_step_pyinstaller_uses_minus_m_flag` — verifies `-m` flag present in command
  5. `test_step_pyinstaller_includes_y_flag` — verifies `-y` flag in command
  6. `test_step_pyinstaller_module_name_is_PyInstaller` — verifies module name is `PyInstaller`
  7. `test_localappdata_env_var_absent` — behaves gracefully when LOCALAPPDATA is not set

---

## Known Limitations

None.
