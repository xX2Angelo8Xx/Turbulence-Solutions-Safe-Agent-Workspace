# Dev Log — FIX-120: Suppress terminal windows during git init in project creation

**Status:** Review  
**Assigned To:** Developer Agent  
**Date:** 2026-04-06  
**Branch:** FIX-120/suppress-git-terminal-windows  

---

## Prior Art Check

No ADRs in `docs/decisions/index.jsonl` directly related to subprocess window suppression.  
FIX-092 established the pattern for suppressing console windows when launching VS Code via `src/launcher/core/vscode.py` — this WP mirrors that pattern for git subprocesses.

---

## Problem

On Windows, `_init_git_repository()` in `src/launcher/core/project_creator.py` calls
`subprocess.run(["git", ...])` multiple times (5 calls: init, config ×2, add, commit).
Each call spawns a visible console window momentarily, causing 4–5 terminal window flashes
during project creation.

---

## Implementation

**File changed:** `src/launcher/core/project_creator.py`

1. Added `import sys` to the imports.
2. In `_init_git_repository()`: after building the `common` dict, conditionally add
   `creationflags=subprocess.CREATE_NO_WINDOW` when `sys.platform == "win32"`.
   This suppresses all console windows for all five git subprocess calls without
   affecting behaviour on macOS or Linux.

Pattern mirrors `src/launcher/core/vscode.py` exactly (established by FIX-092).

---

## Tests Written

- `tests/FIX-120/test_fix120_no_window_flag.py`
  - `test_create_no_window_flag_set_on_windows` — verifies `creationflags=CREATE_NO_WINDOW` passed on win32
  - `test_no_creationflags_on_non_windows` — verifies no creationflags on non-win32
  - `test_git_init_called_with_correct_args` — verifies `git init` is called
  - `test_returns_true_on_success` — verifies True returned when git succeeds
  - `test_returns_false_on_git_failure` — verifies False returned when git init fails
  - `test_returns_false_on_os_error` — verifies False returned on OSError
  - `test_returns_false_on_timeout` — verifies False returned on TimeoutExpired

---

## Files Changed

- `src/launcher/core/project_creator.py` — added `sys` import + `CREATE_NO_WINDOW` on win32
- `docs/workpackages/workpackages.jsonl` — status updated
- `docs/workpackages/FIX-120/dev-log.md` — this file
- `tests/FIX-120/test_fix120_no_window_flag.py` — regression & unit tests
