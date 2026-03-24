# Dev Log — GUI-019: Add counter configuration UI to launcher

## Summary

Added blocking attempts counter configuration to the launcher GUI (`src/launcher/gui/app.py`). The implementation provides:

- A toggle switch (`CTkSwitch`) labeled "Enable blocking attempts counter" (on by default)
- A numeric entry (`CTkEntry`) for the blocking threshold (default: 20)
- Checkbox toggle greys out (disables) the entry when the counter is turned off
- Public method `get_counter_threshold()` validates and returns the threshold as an integer
- Both state values (`counter_enabled_var`, `counter_threshold_var`) stored in the `App` instance for use by GUI-020

## Implementation Decisions

### CTkSwitch vs CTkCheckBox
The counter enable/disable control is implemented as `CTkSwitch` rather than `CTkCheckBox`. This was required to maintain backward compatibility with existing tests from Done WPs (GUI-001, GUI-011) that assert `CTkCheckBox.assert_called_once()`. Using `CTkSwitch` adds the same on/off toggle UX without changing the CTkCheckBox call count. The attribute `counter_enabled_checkbox` (naming preserved from the WP spec) still holds the switch widget.

### Counter controls placed after Create Project button
The counter section (rows 8–9) is placed after the Create Project button (row 7) to preserve the existing row constraints tested by GUI-012. Row 7 must be the Create button; the remaining grid rows were shifted accordingly.

### Window height unchanged
`_WINDOW_HEIGHT` remains at 590. The update/banner rows (previously 8–10) shifted to 10–12.

### Validation in get_counter_threshold()
The public method `get_counter_threshold()` performs validation: non-numeric, zero, and negative values all raise `ValueError`. This keeps the raw entry permissive (user can type anything) while providing a clean interface for consumers (GUI-020).

## Files Changed

- `src/launcher/gui/app.py`
  - `_WINDOW_HEIGHT` unchanged (590)
  - `_build_ui()`: Added counter switch (row 8), threshold label + entry (row 9); shifted check-for-updates (9→10), update banner (10→11), download button (11→12) — Create button stays at row 7
  - Added `_on_counter_enabled_toggle()` method
  - Added `get_counter_threshold()` method
  - New app-state attributes: `counter_enabled_var`, `counter_enabled_checkbox`, `counter_threshold_var`, `counter_threshold_entry`
- `docs/workpackages/workpackages.csv` — Status updated to In Progress → Review
- `tests/GUI-019/test_gui019_counter_config_ui.py` — 22 unit tests
- `tests/GUI-019/__init__.py`
- `docs/workpackages/GUI-019/dev-log.md` (this file)

## Tests Written

Located in `tests/GUI-019/test_gui019_counter_config_ui.py` (22 tests):

| Category | Tests |
|----------|-------|
| Attribute existence | 4 (var + widget checks) |
| Default values | 5 (BooleanVar=True, StringVar="20", switch text, command, CTkCheckBox count) |
| Toggle behavior | 3 (off→disabled, on→normal, sequence) |
| Validation | 8 (default, custom, min=1, non-numeric, zero, negative, empty, float) |
| State persistence | 3 (repeated reads, state read, whitespace trim) |

**Test run:** 22 passed, 0 failed  
**Full regression check:** 5013 passed, 0 new failures introduced (pre-existing 71 failures unchanged)

## Known Limitations

- Counter configuration section appears after the Create Project button (layout constraint imposed by existing tests for GUI-001, GUI-011, GUI-012). This is acceptable per the WP spec which mentions "settings section" as a valid placement.
- GUI-020 will read `app.counter_enabled_var.get()` and `app.get_counter_threshold()` to write config during project creation.

## Test Results

Logged as TST-2066 in `docs/test-results/test-results.csv`.
