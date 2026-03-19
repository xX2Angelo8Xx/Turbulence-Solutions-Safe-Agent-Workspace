# GUI-018 Dev Log — Relocate Python Runtime Option

**WP ID:** GUI-018  
**Category:** GUI  
**Status:** In Progress → Review  
**Assigned To:** Developer Agent  
**Date:** 2026-03-19  
**Branch:** GUI-018

---

## Summary

Added a gear/settings button (⚙) to the launcher GUI that opens a Settings dialog allowing the user to relocate the Python runtime. This handles the scenario where a user manually moves the launcher installation directory and existing workspaces' `ts-python` shim stops working.

---

## Implementation

### Files Changed

- `src/launcher/gui/app.py` — Added gear button to top-right of main window; added `_open_settings_dialog()` method; added `SettingsDialog` class
- `tests/GUI-018/test_gui018_settings_dialog.py` — Full test suite

### Design Decisions

1. **Gear button placement:** Used `place()` consistent with the version label approach, placing the gear button at the top-right corner of the main window so it does not disrupt existing grid layout.

2. **CTkToplevel dialog:** The `SettingsDialog` class opens a modal-style `CTkToplevel` with `grab_set()` to prevent interaction with the main window while settings are open.

3. **Auto-detect logic:** Uses `sys._MEIPASS` (PyInstaller bundle path) if available, otherwise falls back to `sys.executable` parent's parent directory to locate `python-embed/python.exe` (Windows) or `python-embed/python3` (macOS/Linux).

4. **write_python_path / read_python_path:** Calls `shim_config.write_python_path()` after user selects/confirms a Python executable. Shows confirmation via `messagebox.showinfo()`.

5. **Browse:** Uses `tkinter.filedialog.askopenfilename()` to let the user browse to a Python executable file.

6. **Separation of concerns:** `SettingsDialog` is a standalone class inside `app.py`, not a separate module, since it is tightly coupled to the GUI and follows the existing pattern.

---

## Tests Written

**Total: 25 tests** across 6 test classes in `tests/GUI-018/test_gui018_settings_dialog.py`

| Class | Test | Description |
|-------|------|-------------|
| `TestGearButton` | `test_gear_button_exists` | Gear button attribute present on App instance |
| `TestGearButton` | `test_gear_button_text` | Button text is "⚙" |
| `TestGearButton` | `test_gear_button_command` | Button command wired to `_open_settings_dialog` |
| `TestSettingsDialogInit` | `test_dialog_title` | Dialog window title is "Settings" |
| `TestSettingsDialogInit` | `test_grab_set_called` | `grab_set()` called to make dialog modal |
| `TestSettingsDialogInit` | `test_current_path_displayed` | Current path from `read_python_path()` shown in label |
| `TestSettingsDialogInit` | `test_not_configured_when_none` | Shows "Not configured" when no path set |
| `TestSettingsDialogInit` | `test_has_auto_detect_button` | Auto-detect button created |
| `TestSettingsDialogInit` | `test_has_browse_button` | Browse button created |
| `TestSettingsDialogInit` | `test_has_close_button` | Close button created |
| `TestAutoDetect` | `test_auto_detect_meipass_path` | Uses `sys._MEIPASS` when available |
| `TestAutoDetect` | `test_auto_detect_fallback_win` | Falls back to `sys.executable` parent on Windows |
| `TestAutoDetect` | `test_auto_detect_fallback_linux` | Falls back to `sys.executable` parent on Linux |
| `TestAutoDetect` | `test_auto_detect_found_calls_write` | `write_python_path()` called when exe found |
| `TestAutoDetect` | `test_auto_detect_found_shows_info` | `showinfo()` displayed on success |
| `TestAutoDetect` | `test_auto_detect_none_shows_error` | `showerror()` shown when result is None |
| `TestAutoDetect` | `test_auto_detect_nonexistent_shows_error` | `showerror()` shown when path does not exist |
| `TestBrowse` | `test_browse_calls_askopenfilename` | `askopenfilename()` called |
| `TestBrowse` | `test_browse_writes_path` | `write_python_path()` called with `Path` object |
| `TestBrowse` | `test_browse_shows_info` | `showinfo()` shown after successful selection |
| `TestBrowse` | `test_browse_cancel_noop` | No action taken when dialog cancelled |
| `TestBrowse` | `test_browse_updates_label` | Path label updated after selection |
| `TestCloseButton` | `test_close_button_destroy` | Dialog has `destroy` method |
| `TestOpenSettingsDialog` | `test_open_settings_dialog_method_exists` | `_open_settings_dialog` method is callable |
| `TestOpenSettingsDialog` | `test_open_settings_dialog_instantiates` | Calling method instantiates `SettingsDialog` |

---

## Test Results

All 25 tests passed. GUI regression suite (615 tests) clean — 0 new failures.

See `docs/test-results/test-results.csv` for logged entries.
