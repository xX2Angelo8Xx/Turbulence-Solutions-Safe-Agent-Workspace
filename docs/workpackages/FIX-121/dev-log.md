# Dev Log — FIX-121

**WP:** FIX-121 — Immediate button feedback on Create Project click  
**Developer:** Developer Agent  
**Date Started:** 2026-04-07  
**Branch:** FIX-121/button-feedback  
**Bug Reference:** BUG-206

---

## ADR Prior-Art Check

Reviewed `docs/decisions/index.jsonl`. No ADRs directly address GUI threading patterns.  
ADR-008 (Tests Must Track Current Codebase State) is noted — SAF-034 tests are updated to reflect
the new `_on_create_project` structure.

---

## Objective

Move `_set_creation_ui_state(disabled=True)` to immediately after the `_COMING_SOON_LABEL` guard
so the button greys out and the progress bar starts *before* any validation runs. Move all
validation logic (input checks, `verify_ts_python()`, counter config reads) into the background
`_create()` thread. On validation failure, post UI updates back to the main thread via
`self._window.after(0, callback)`.

---

## Implementation Summary

### `src/launcher/gui/app.py` — `_on_create_project()`

**Before (broken):** `_set_creation_ui_state(disabled=True)` was called at line 539, AFTER
all synchronous validation and `verify_ts_python()` (line 510). This caused a 1–2 second UI
freeze on click.

**After (fixed):** 
1. `open_vscode` flag is captured immediately after the COMING_SOON guard (main thread, before UI is disabled so the checkbox value is stable).
2. `_set_creation_ui_state(disabled=True)` is called right after, immediately giving visual feedback.
3. All validation (name, destination, duplicate check, template lookup, `verify_ts_python()`) and counter config reads move into `_create()`.
4. Validation failures in `_create()` post UI updates via `self._window.after(0, callback)` to the main thread and call `self._set_creation_ui_state(disabled=False)` to re-enable the UI.

### `tests/SAF-034/test_saf034.py` — Tests 11, 12, 14

These tests construct a bare `App` instance and call `_on_create_project()` directly. After the
change, `_set_creation_ui_state(disabled=True)` is called before validation, so the tests needed:
- `create_button`, `browse_button`, `create_progress_bar` MagicMocks
- `_window = MagicMock()` with `after.side_effect = lambda ms, cb: cb()` for synchronous dispatch
- `threading.Thread` replaced with a `_SyncThread` helper to run `_create()` inline

---

## Files Changed

- `src/launcher/gui/app.py`
- `tests/SAF-034/test_saf034.py`
- `tests/FIX-121/__init__.py` (new)
- `tests/FIX-121/test_fix121_button_feedback.py` (new)
- `docs/workpackages/workpackages.jsonl`

---

## Tests Written

- `tests/FIX-121/test_fix121_button_feedback.py`
  - `test_ui_disabled_before_validation` — Verifies `_set_creation_ui_state(disabled=True)` is called before any validation
  - `test_ui_reenabled_on_invalid_name` — Validates that UI re-enables when name validation fails
  - `test_ui_reenabled_on_invalid_dest` — Validates that UI re-enables when destination validation fails
  - `test_ui_reenabled_on_duplicate_folder` — Validates that UI re-enables when duplicate check fails
  - `test_ui_reenabled_on_shim_failure` — Validates that UI re-enables when verify_ts_python fails
  - `test_error_message_shown_on_shim_failure` — Validates error dialog shown when shim fails
  - `test_create_proceeds_on_valid_inputs` — Validates successful project creation flow

---

## Iteration 2 (Tester Feedback)

### Issues Found by Tester

1. **`tests/GUI-034/test_gui034_progress_bar.py::test_on_create_project_no_thread_on_invalid_name`** — Test asserted pre-FIX-121 behavior (no thread on invalid name). Updated to reflect new contract: thread always starts, UI always disabled before validation.

2. **BUG-206 status** — `docs/bugs/bugs.jsonl` still showed `"Status": "Open"`. Updated to `"Status": "Fixed"`.

3. **BUG-210** (filed by Tester) — Closed with `"Fixed In WP": "FIX-121"`.

### Additional Changes (Iteration 2)

- `tests/GUI-034/test_gui034_progress_bar.py` — `test_on_create_project_no_thread_on_invalid_name` updated
- `docs/bugs/bugs.jsonl` — BUG-206 → Fixed, BUG-210 → Fixed (Fixed In WP: FIX-121)

### Test Results (Iteration 2)

- FIX-121 suite: 12/12 passed (TST-2722; includes 5 Tester edge-cases)
- GUI-034 test: PASSED
- Workspace validation: clean (exit 0)

