# Dev Log — FIX-092: Hide terminal flash when opening VS Code

**Status:** Review  
**Assigned To:** Developer Agent  
**Date Started:** 2026-03-31  

---

## Summary

On Windows, `subprocess.Popen(["code", path])` spawns `code.cmd`, a batch file
interpreted by `cmd.exe`. Windows creates a console window for the command
processor before VS Code opens, causing a brief visible flash.

Fix: pass `creationflags=subprocess.CREATE_NO_WINDOW` on `win32` platforms when
calling `subprocess.Popen` and `subprocess.run` for background processes.

---

## Files Changed

| File | Change |
|------|--------|
| `src/launcher/core/vscode.py` | Added `CREATE_NO_WINDOW` creationflag on Windows in `open_in_vscode()` |
| `src/launcher/core/github_auth.py` | Added `CREATE_NO_WINDOW` creationflag on Windows in `get_github_token()` subprocess call |
| `src/launcher/core/updater.py` | Added `CREATE_NO_WINDOW` creationflag on Windows in `_get_local_git_version()` and `check_for_update_source()` subprocess calls |

---

## Implementation Notes

- `subprocess.CREATE_NO_WINDOW` (`0x08000000`) is a Windows-only constant; it is
  guarded by `if sys.platform == "win32"` to remain cross-platform safe.
- `shell=False` is preserved throughout — this is a security requirement.
- `capture_output=True` (used in `github_auth.py` and `updater.py`) already
  redirects stdio, which partially suppresses console windows in some scenarios,
  but adding the explicit creationflag is the belt-and-suspenders approach and
  is the only reliable way to prevent the window.

---

## Tests Written

Location: `tests/FIX-092/`

- `test_fix092_terminal_flash.py`
  - `test_open_in_vscode_win32_creationflag` — Windows: `CREATE_NO_WINDOW` is passed
  - `test_open_in_vscode_non_win32_no_creationflag` — non-Windows: no `creationflags` key
  - `test_open_in_vscode_correct_args` — Popen receives `[exe, workspace_path]`
  - `test_open_in_vscode_returns_true_on_success` — returns `True` when VS Code found
  - `test_open_in_vscode_returns_false_when_not_found` — returns `False` when `find_vscode` is None
  - `test_github_auth_win32_creationflag` — GitHub CLI call uses `CREATE_NO_WINDOW` on Windows
  - `test_github_auth_non_win32_no_creationflag` — GitHub CLI call has no `creationflags` key on non-Windows
  - `test_updater_git_describe_win32_creationflag` — `_get_local_git_version` uses `CREATE_NO_WINDOW` on Windows
  - `test_updater_git_fetch_win32_creationflag` — `check_for_update_source` git fetch uses `CREATE_NO_WINDOW` on Windows

---

## Test Results

All 9 tests passed. See `docs/test-results/test-results.csv` for logged entry.

---

## Known Limitations

- `CREATE_NO_WINDOW` applies only to Windows; macOS/Linux are unaffected (the
  flag is never set on those platforms).
- The flag only suppresses the window created by the child process; it does not
  affect any grandchild processes that VS Code itself spawns.
