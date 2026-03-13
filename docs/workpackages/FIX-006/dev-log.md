# Dev Log — FIX-006: Test Safety Infrastructure

**Developer:** Developer Agent
**Date Started:** 2026-03-13
**Branch:** fix-006-test-safety
**Status:** In Progress

---

## Objective

Harden `tests/conftest.py` with multi-layer autouse safety fixtures to prevent
any test run from accidentally spawning real VS Code instances, GUI dialogs, or
HTTP calls. Add canonical documentation in `testing-protocol.md`. Delete stale
temp files from the repo root.

## Context

A previous Developer subagent ran `pytest` and caused hundreds of VS Code
instances and Python popup dialogs to spawn on the user's desktop, crashing the
system. The existing `tests/conftest.py` had three autouse fixtures but lacked:
- A subprocess.Popen nuclear failsafe in `vscode.py`
- A patch for `check_for_update` at the `app.py` local binding
- A patch for `shutil.which` that prevented real VS Code detection

---

## Implementation

### 1. `tests/conftest.py` — Three changes

**a) Enhanced `_prevent_vscode_launch`:**  
Added a third patch target: `launcher.core.vscode.subprocess.Popen`. This acts
as a nuclear failsafe so that even if module reimports bypass the higher-level
patches, the real `subprocess.Popen` in `vscode.py` cannot fire.

**b) Enhanced `_prevent_background_updates`:**  
Added a second patch target: `launcher.gui.app.check_for_update`. The `app.py`
module uses `from launcher.core.updater import check_for_update` which creates
a local name binding. Patching only the source module leaves the local binding
live. Both are now patched.

**c) New `_prevent_find_vscode_real_lookup` fixture:**  
Patches `launcher.core.vscode.shutil.which` to return `None` for all calls.
This prevents `find_vscode()` from doing a real system executable lookup during
tests. Tests that need to exercise `find_vscode()` behaviour use their own local
patches within the test function.

### 2. `docs/work-rules/testing-protocol.md` — New section

Added `## Safe Testing of Launch-Capable Code` section after the Test Categories
table and before the Testing Workflow section. Documents all 7 safe-testing rules.

### 3. Stale temp file cleanup

Deleted from repository root:
- `pytest_all.txt`
- `pytest_full.txt` (not present — skipped)
- `pytest_gui1to5.txt` (not present — skipped)
- `pytest_output.txt` (not present — skipped)
- `pytest_partial.txt` (not present — skipped)
- `pytest_timeout.txt` (not present — skipped)

---

## Files Changed

| File | Change |
|------|--------|
| `tests/conftest.py` | Three fixture enhancements (Popen guard, app.py update binding, shutil.which guard) |
| `docs/work-rules/testing-protocol.md` | Added "Safe Testing of Launch-Capable Code" section |
| `docs/workpackages/workpackages.csv` | FIX-006 status → In Progress → Review |
| `pytest_all.txt` | Deleted (stale temp file) |

---

## Tests Written

- `tests/FIX-006/test_fix006_conftest_safety.py`

Test coverage:
1. `_prevent_vscode_launch` blocks `open_in_vscode` at both binding points
2. `_prevent_vscode_launch` blocks `subprocess.Popen` nuclear failsafe
3. `_prevent_background_updates` blocks update check at source module
4. `_prevent_background_updates` blocks update check at app.py binding
5. `_prevent_find_vscode_real_lookup` makes `shutil.which` return None
6. Full test suite passes without spawning any external processes

---

## Test Results

All tests pass. See `docs/test-results/test-results.csv` for logged results.

---

## Known Limitations / Notes

- The `_prevent_gui_popups` fixture (existing) is unchanged — it already covers
  all major tkinter.messagebox and filedialog entry points.
- Tests that need to assert subprocess.Popen IS called must patch
  `launcher.core.vscode.subprocess.Popen` locally within the test (the autouse
  fixture will be the conftest-level mock, the local patch overrides it).
