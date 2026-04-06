# Dev Log — GUI-036: Add Uninstall Application button to Settings dialog

**Status:** In Progress  
**Branch:** `GUI-036/uninstall-button`  
**Developer:** Developer Agent  
**Date:** 2026-04-06  

---

## Prior Art Check

No relevant ADRs found in `docs/decisions/index.jsonl` for GUI settings dialog or uninstall functionality.

---

## WP Summary

Add a "Danger Zone" section to `SettingsDialog._build_ui()` with a red "Uninstall Application" button. The button:
- On Windows: detects `unins000.exe` next to `sys.executable`, prompts for confirmation, then runs the uninstaller + exits.
- On macOS/Linux: shows a manual uninstall instructions dialog.
- Is disabled in dev/source mode when `unins000.exe` is not found.

---

## Implementation Plan

1. Add `import subprocess` to `src/launcher/gui/app.py`.
2. Add `_find_uninstaller()` to `SettingsDialog` — checks `Path(sys.executable).parent / "unins000.exe"` on Windows.
3. Add `_on_uninstall()` handler — confirmation dialog, then `subprocess.Popen` + `sys.exit(0)` on Windows; instructions message on others.
4. Extend `_build_ui()` with a "Danger Zone" / "Uninstall" section at the bottom (rows 7–9).
5. Increase dialog height from 480 to 620 to fit the new section.

---

## Files Changed

- `src/launcher/gui/app.py` — added uninstall button, `_find_uninstaller()`, `_on_uninstall()`
- `tests/GUI-036/test_gui036_uninstall_button.py` — unit tests

---

## Tests Written

- `TestFindUninstaller` — Windows found, Windows not found, non-Windows returns None
- `TestOnUninstallConfirmation` — confirmation dialog shown, on cancel no action
- `TestOnUninstallWindows` — on confirm: runs subprocess.Popen + sys.exit(0)
- `TestOnUninstallNonWindows` — shows instructions message
- `TestButtonState` — button disabled when no uninstaller; enabled when found

---

## Known Limitations

- Only `unins000.exe` in the same directory as `sys.executable` is checked. Advanced Inno Setup custom install paths are not searched.

---

## Iteration 2 — Tester Feedback Resolution (2026-04-06)

### Tester Findings
- BUG-205: `tests/GUI-018/test_gui018_edge_cases.py::TestDialogGeometry::test_dialog_geometry_is_480x480` failed because GUI-036 increased SettingsDialog height from 480 to 620, but the GUI-018 edge-case test still asserted the old geometry string.

### Changes Made
- `tests/GUI-018/test_gui018_edge_cases.py` — renamed `test_dialog_geometry_is_480x480` → `test_dialog_geometry_is_480x620`; updated `assert_called_with("480x480")` → `assert_called_with("480x620")`
- `docs/bugs/bugs.jsonl` — set `"Status": "Closed"` and `"Fixed In WP": "GUI-036"` on BUG-205

### Test Results
- `tests/GUI-036/` — 13 passed
- `tests/GUI-018/` — 37 passed (including renamed geometry test)
- Full regression suite — 200 pre-existing failures (matches regression baseline of 261); no new failures introduced by GUI-036
