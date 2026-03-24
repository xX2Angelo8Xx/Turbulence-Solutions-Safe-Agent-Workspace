# GUI-020 — Write counter config to workspace on creation

**Status:** Review  
**Assigned To:** Developer Agent  
**Branch:** `GUI-020/counter-config-write`  
**User Story:** US-038  
**Dependencies:** GUI-019, SAF-036  

---

## Summary

During project creation, write the counter configuration (threshold and enabled flag)
from the GUI controls into the created workspace's `.github/hooks/scripts/counter_config.json`.
This file is read by `security_gate.py` (SAF-036) to configure the denial counter behaviour.

---

## Implementation

### Files Changed

| File | Change |
|------|--------|
| `src/launcher/core/project_creator.py` | Added `write_counter_config()` function; added `counter_enabled` and `counter_threshold` parameters to `create_project()` |
| `src/launcher/gui/app.py` | `_on_create_project()` reads `counter_enabled_var` and calls `get_counter_threshold()`; passes both to `create_project()` |

### Approach

1. **Config format** — Matches the format `security_gate.py` (_load_counter_config) expects:
   ```json
   {
       "counter_enabled": true,
       "lockout_threshold": 20
   }
   ```
   File location: `<workspace>/.github/hooks/scripts/counter_config.json`
   (same path as in the template; written after `shutil.copytree` so it overwrites the template default).

2. **`write_counter_config(project_dir, counter_enabled, counter_threshold)`** —
   Pure helper that builds the config path, constructs the dict, and writes JSON.

3. **`create_project()`** — Accepts `counter_enabled` and `counter_threshold` as keyword
   arguments with safe defaults (`True`, `20`) so existing callers are unaffected.
   Calls `write_counter_config()` after `shutil.copytree()`.

4. **`_on_create_project()` in `app.py`** — Reads `self.counter_enabled_var.get()` and
   `self.get_counter_threshold()` (falling back to `20` on `ValueError`) before calling
   `create_project()`.

### Security Considerations

- The config file is written *inside* the project directory created by `create_project()`,
  which already validates the path against path-traversal (uses `is_relative_to`).
- No user input is written without going through `get_counter_threshold()` validation first.
- The fallback `counter_threshold = 20` on `ValueError` ensures we fail closed (default
  threshold) rather than failing open (writing a zero or negative threshold).

---

## Tests Written

All tests are in `tests/GUI-020/`.

| File | Coverage |
|------|----------|
| `test_gui020_write_counter_config.py` | `write_counter_config()` unit tests |
| `test_gui020_create_project_integration.py` | `create_project()` integration tests with counter args |
| `test_gui020_app_passes_counter_config.py` | `_on_create_project()` passes correct values to `create_project()` |

---

## Test Results

- All GUI-020 tests pass (see test-results.csv entry logged via `add_test_result.py`).
- No regressions in full test suite.

---

## Known Limitations / Notes

- The template already ships with a `counter_config.json` (threshold=20, enabled=true).
  `write_counter_config()` overwrites it after `copytree`, so the GUI values always win.
- Threshold validation is performed in `get_counter_threshold()` (GUI-019 scope);
  this WP relies on that validation and applies a safe fallback.
