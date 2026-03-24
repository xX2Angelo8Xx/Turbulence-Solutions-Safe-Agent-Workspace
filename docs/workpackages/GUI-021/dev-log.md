# GUI-021 — Add Reset Agent Blocks button to launcher

## Status
Review

## Assigned To
Developer Agent

## Summary
Added a "Reset Agent Blocks" button to the launcher Settings dialog (`SettingsDialog` class in `src/launcher/gui/app.py`).  
When clicked, the button opens a folder browser to select a workspace, locates `.hook_state.json`, and resets all session counters.

## Implementation Details

### Placement: SettingsDialog (not main window)
The reset feature was placed in the Settings dialog to avoid changing `_WINDOW_HEIGHT = 590` (validated by existing GUI-012 permanent tests). The WP description explicitly permits "settings area or main window".

### New UI Elements in SettingsDialog
- `workspace_entry` (`CTkEntry`): displays the workspace path to reset
- `browse_workspace_button` (`CTkButton`): opens folder dialog to select workspace
- `reset_agent_blocks_button` (`CTkButton`): resets session counters for the selected workspace

### New Module-Level Functions
- `_reset_hook_state(state_path: Path) -> tuple[int, str]`: performs the actual JSON reset — mirrors `reset_counters()` logic from SAF-037's `reset_hook_counter.py`; returns `(num_reset, message)`
- `_atomic_write_hook_state(path: Path, data: dict) -> None`: atomic file write via temp-file + `os.replace`

### New Instance Methods on SettingsDialog
- `_browse_workspace()`: opens `filedialog.askdirectory`, populates `workspace_entry`
- `_on_reset_agent_blocks()`: validates path → constructs state_path → calls `_reset_hook_state` → shows result dialog

### New Imports (app.py)
- `json`, `os`, `tempfile` added to support atomic JSON write

### State File Location
`<workspace_root>/.github/hooks/scripts/.hook_state.json` — matching the `STATE_FILE` constant in `reset_hook_counter.py`.

### Edge Cases Handled
1. No workspace path entered → `showerror("No Workspace Selected", ...)`
2. Path is not a valid directory → `showerror("Invalid Workspace", ...)`
3. State file missing → `showinfo("Reset Complete", ...)` — "nothing to reset" is still success
4. Corrupt state file → replaces with empty `{}`, still shows confirmation
5. `OSError` during atomic write → `showerror("Reset Failed", ...)`

### Dialog Geometry Unchanged
`SettingsDialog` geometry remains `"480x280"` (as required by GUI-018 permanent test). The new rows are appended at the bottom of the settings dialog layout.

## Files Changed
- `src/launcher/gui/app.py` — added imports, module-level helpers, SettingsDialog new UI rows and methods
- `docs/workpackages/workpackages.csv` — status updated
- `docs/workpackages/GUI-021/dev-log.md` — this file
- `tests/GUI-021/__init__.py` — new
- `tests/GUI-021/test_gui021_reset_button.py` — new

## Tests Written
`tests/GUI-021/test_gui021_reset_button.py` — 18 tests in 6 classes:
- `TestResetButtonAttributesExist` (3): button, entry, browse button exist on SettingsDialog
- `TestBrowseWorkspace` (2): populates entry, no-op on cancel
- `TestResetNoWorkspace` (2): error on empty/whitespace path
- `TestResetInvalidWorkspace` (1): error on non-existent directory
- `TestResetSuccess` (4): confirmation shown, state cleared, missing file ok, OSError caught
- `TestResetHookState` (4): missing file, multi-session reset, corrupt file, non-session keys
- `TestAtomicWriteHookState` (2): writes valid JSON, no leftover temp files

**Result: 18 passed, 0 failed (TST-2070)**

## Known Limitations
- The Settings dialog at 280px height may require vertical scrolling in future if more content is added. The WP scope did not include a dialog resize (constrained by GUI-018 permanent test).
