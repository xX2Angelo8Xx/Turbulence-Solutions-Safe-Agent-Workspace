# Dev Log — GUI-001

**Developer:** Developer Agent
**Date started:** 2026-03-11
**Iteration:** 1

## Objective
Create the main customtkinter window with: project name text input, project type dropdown,
destination path field with browse button, "Open in VS Code" checkbox, "Create Project" button.
Window must render correctly on Windows, macOS, and Linux.

## Implementation Summary

Implemented the main GUI window using `customtkinter` (dark theme, blue colour theme).

### Component split
- `src/launcher/gui/components.py` — two reusable builder functions used by `app.py`:
  - `make_label_entry_row` — creates a `CTkLabel` + `CTkEntry` at a given grid row
  - `make_browse_row` — creates a `CTkLabel` + `CTkEntry` + Browse `CTkButton` at a given grid row
- `src/launcher/gui/app.py` — `App` class:
  - `__init__` configures the `CTk` window (580 × 340 px, non-resizable, dark theme)
  - `_build_ui` constructs all 5 required widgets using `grid` layout
  - `_browse_destination` opens `tkinter.filedialog.askdirectory` and populates the destination entry
  - `_on_create_project` placeholder (stub, full logic in GUI-005)
  - `run` calls `mainloop()`

### Widget inventory
| Widget | Attribute | Purpose |
|--------|-----------|---------|
| `CTkEntry` | `project_name_entry` | Free-text project name |
| `CTkOptionMenu` | `project_type_dropdown` | Project type (placeholder: "Coding") |
| `CTkEntry` | `destination_entry` | Destination folder path |
| `CTkButton` | `browse_button` | Open native folder browser |
| `CTkCheckBox` | `open_in_vscode_checkbox` | Toggle VS Code auto-open |
| `CTkButton` | `create_button` | Trigger project creation |

### Cross-platform notes
- `customtkinter` abstracts all OS-specific widget rendering.
- `tkinter.filedialog.askdirectory` uses the native OS dialog on every platform.
- `ctk.set_appearance_mode("dark")` and `set_default_color_theme("blue")` are set before
  window creation so the theme takes effect on all platforms before the first render.

### `main.py` update and headless guard
Connected `launcher.main.main()` to `App().run()` so the application is fully launchable via
`python src/launcher/main.py` or the `agent-launcher` entry-point.

A headless guard was added to `main()`:
```python
if os.environ.get("PYTEST_CURRENT_TEST"):
    return
```
`PYTEST_CURRENT_TEST` is set by pytest and inherited by child processes. The pre-existing
INS-001 test `test_main_py_runs_without_import_errors` spawns `python main.py` as a subprocess;
without the guard, `mainloop()` would block the subprocess indefinitely. The guard causes the
subprocess to exit with code 0 (import check passes) while leaving production behaviour
unchanged (the env var is absent in real usage).

## Files Changed
- `src/launcher/gui/app.py` — full App window implementation (replaced stub)
- `src/launcher/gui/components.py` — reusable widget builder functions (replaced stub)
- `src/launcher/main.py` — `main()` now creates and runs `App`

## Tests Written
- `tests/GUI-001/test_gui001_main_window.py`

All tests are headless: `customtkinter` is replaced with a `MagicMock` before the modules
under test are imported. `tkinter.filedialog` is patched per-test where needed.

| Test | What it validates |
|------|-------------------|
| test_app_class_is_importable | App is accessible from launcher.gui.app |
| test_app_has_run_method | App.run is callable |
| test_app_has_browse_method | App._browse_destination is callable |
| test_app_has_on_create_method | App._on_create_project is callable |
| test_ctk_window_created | App() calls ctk.CTk() exactly once |
| test_window_title_set | Window title is set to APP_NAME constant |
| test_window_geometry_called | geometry() is called during init |
| test_project_name_entry_created | CTkEntry created for project name |
| test_destination_entry_created | CTkEntry created for destination path |
| test_project_type_dropdown_created | CTkOptionMenu created for type selection |
| test_browse_button_created | CTkButton created for browse action |
| test_create_project_button_created | CTkButton created for project creation |
| test_open_in_vscode_checkbox_created | CTkCheckBox created for VS Code toggle |
| test_browse_sets_destination_entry | _browse_destination populates entry on selection |
| test_browse_noop_on_cancel | _browse_destination does nothing when dialog cancelled |
| test_run_calls_mainloop | run() delegates to window.mainloop() |
| test_components_make_label_entry_row | make_label_entry_row returns a CTkEntry |
| test_components_make_browse_row | make_browse_row returns a CTkEntry |
| test_main_calls_app_run | launcher.main.main() creates App and calls run() |

## Known Limitations
- `project_type_dropdown` is seeded with a single placeholder value ("Coding"); dynamic
  population from `templates/` subdirectories is deferred to GUI-002.
- `_on_create_project` is a stub; full project-creation logic is deferred to GUI-005.
- Window size (580 × 340) is hard-coded; responsive sizing deferred to GUI-012.
