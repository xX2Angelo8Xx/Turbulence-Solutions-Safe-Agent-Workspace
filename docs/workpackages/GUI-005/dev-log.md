# Dev Log — GUI-005

**Developer:** Developer Agent
**Date started:** 2026-03-12
**Iteration:** 1

## Objective
Implement the "Create Project" button handler. When clicked, the app should:
- Read the project name, selected template type, and destination path from the UI.
- Validate all inputs using existing validation helpers.
- Show inline errors for validation failures.
- Reverse-map the display (title-cased) template name back to the actual directory name.
- Call `create_project()` to copy the template to `<destination>/<folder_name>/`.
- Show a success dialog on success or an error dialog on failure.

## Implementation Summary
- Added `import tkinter.messagebox as messagebox` and `from pathlib import Path` to `app.py` imports.
- Extended the `from launcher.core.project_creator import` line to also import `create_project`.
- Implemented `_on_create_project()` in `src/launcher/gui/app.py`:
  1. Reads and strips the three input values.
  2. Clears any previous inline error labels.
  3. Runs `validate_folder_name()` — shows inline error and returns early on fail.
  4. Runs `validate_destination_path()` — shows inline error and returns early on fail.
  5. Runs `check_duplicate_folder()` — shows inline error and returns early on duplicate.
  6. Reverse-maps the dropdown display name to the raw template directory name by
     iterating `list_templates(TEMPLATES_DIR)` and comparing `_format_template_name(t)`.
  7. Calls `create_project(template_path, Path(destination), folder_name)`.
  8. Shows `messagebox.showinfo` on success.
  9. Shows `messagebox.showerror` on `Exception` from `create_project` or unknown template.

## Files Changed
- `src/launcher/gui/app.py` — added imports; implemented `_on_create_project()`

## Tests Written
- `tests/GUI-005/test_gui005_project_creation.py`
  - `TestOnCreateProjectValidation` — inline errors shown for empty name, invalid name, bad destination, duplicate folder
  - `TestOnCreateProjectSuccess` — success path calls `create_project` and shows info dialog
  - `TestOnCreateProjectErrors` — `create_project` exception triggers error dialog; unknown template triggers error
  - `TestOnCreateProjectClearsPreviousErrors` — error labels cleared on each call

## Known Limitations
- The success/error dialogs use `tkinter.messagebox` which may behave differently on macOS (standard native dialogs).
- Template reverse-mapping relies on `_format_template_name()` being a pure function; if two different template dir names happen to produce the same display string, the first match in the sorted list would be used.
