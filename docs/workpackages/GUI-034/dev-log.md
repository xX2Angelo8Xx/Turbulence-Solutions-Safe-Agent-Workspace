# Dev Log — GUI-034: Add progress bar and disable Create button during project creation

**Status:** In Progress  
**Assigned To:** Developer  
**Branch:** `GUI-034/progress-bar-create`  
**User Story:** US-079

---

## ADR Check

No ADRs in `docs/decisions/index.jsonl` are directly related to GUI threading or progress indicators. The existing `_run_update_check` pattern (GUI-009) already establishes the `threading.Thread` + `self._window.after(0, callback)` convention — this WP follows that same pattern for project creation.

---

## Implementation Summary

### Problem
`_on_create_project()` called `create_project()` synchronously on the main UI thread. During creation the UI was frozen with no feedback, and a second click could potentially start a duplicate creation.

### Solution
- Added `CTkProgressBar` in indeterminate mode (hidden by default, shown during creation).
- Moved `create_project()` call to a `daemon=True` background thread.
- Disabled five widgets during creation: Create button, project name entry, destination entry, browse button, project type dropdown.
- Used `self._window.after(0, callback)` for all UI updates from the background thread (thread-safe).
- Re-enabled all widgets on success **or** failure (never leaves UI in a broken state).

### Files Changed
- `src/launcher/gui/app.py` — main implementation
  - `_build_ui`: inlined destination row to capture `self.browse_button`; added `create_progress_bar` at row 9; shifted counter/update rows by +1
  - `_on_create_project`: captures `open_vscode` flag before disabling UI; calls `_set_creation_ui_state(True)`; launches background thread
  - `_set_creation_ui_state(disabled)`: new method — enables/disables 5 widgets, shows/hides+starts/stops progress bar
  - `_on_creation_complete(...)`: new method — re-enables UI, shows success/error messagebox, opens VS Code if checked
  - `_WINDOW_HEIGHT`: increased from 630 → 660 to accommodate progress bar row

### Thread Safety
- All UI mutations are either on the main thread or scheduled via `self._window.after(0, ...)`.
- `str(exc)` is captured in the except block (before the lambda closure) to avoid the `NameError`/garbage-collection risk.

---

## Tests Written

Located in `tests/GUI-034/`:

| Test | Description |
|------|-------------|
| `test_set_creation_ui_state_disables` | Verifies all 5 widgets are set to "disabled" |
| `test_set_creation_ui_state_enables` | Verifies all 5 widgets are set to "normal" |
| `test_set_creation_ui_state_shows_progress_bar` | Progress bar `.grid()` and `.start()` called when disabled=True |
| `test_set_creation_ui_state_hides_progress_bar` | Progress bar `.stop()` and `.grid_remove()` called when disabled=False |
| `test_on_creation_complete_success_shows_info` | Messagebox showinfo called on success |
| `test_on_creation_complete_failure_shows_error` | Messagebox showerror called on failure |
| `test_on_creation_complete_opens_vscode` | VS Code opened when open_vscode=True and success |
| `test_on_creation_complete_no_vscode_on_failure` | VS Code NOT opened on failure |
| `test_on_create_project_launches_thread` | Thread is started when validation passes |
| `test_on_create_project_disables_ui_on_valid_input` | `_set_creation_ui_state(True)` called before thread |
| `test_on_creation_complete_re_enables_ui` | `_set_creation_ui_state(False)` called on completion |
| `test_progress_bar_initially_hidden` | `create_progress_bar` is hidden (grid_remove called) in _build_ui |

---

## Known Limitations

- The progress bar is indeterminate — no percentage completion is shown (create_project is opaque).
- The VS Code open call happens on the main thread after re-enabling the UI (consistent with prior behavior).

---

## Iteration 2 (Tester Feedback)

### Issues Found
1. **GUI-005, GUI-006 regressions (13 tests)**: Tests written for synchronous `_on_create_project` used `_window.after` implicitly (MagicMock) — callbacks never fired, so `messagebox` and `open_in_vscode` assertions failed.
2. **GUI-012 regression (1 test)**: Height assertion checked for `"630"` — now `"660"`.

### Fixes Applied
- Added `_SyncThread` helper class to `tests/GUI-005/test_gui005_project_creation.py`, `tests/GUI-006/test_gui006_vscode_auto_open.py`, `tests/GUI-006/test_gui006_tester_edge_cases.py`.
- Set `app._window.after.side_effect = lambda ms, cb: cb()` in `_make_app` helpers so `_on_creation_complete` fires synchronously in tests.
- Added `patch("launcher.gui.app.threading.Thread", _SyncThread)` to 12 tests that assert post-completion behavior.
- Updated `test_window_height_is_440` in GUI-012 from `"630"` → `"660"`.
- All 134 affected tests now pass.

