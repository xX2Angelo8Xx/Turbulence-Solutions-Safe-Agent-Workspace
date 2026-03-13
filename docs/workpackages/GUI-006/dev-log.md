# Dev Log — GUI-006

**Developer:** Developer Agent
**Date started:** 2026-03-12
**Iteration:** 1

## Objective
Detect VS Code executable (platform-specific paths + PATH lookup). When "Open in VS Code"
is checked and project creation succeeds, launch VS Code with the new folder as workspace.
Grey out checkbox if VS Code is not detected.

## Implementation Summary

GUI-006 integrates the existing `find_vscode()` and `open_in_vscode()` utilities
(from `src/launcher/core/vscode.py`) into the main application window:

1. **Startup detection:** At the end of `_build_ui()`, `find_vscode()` is called.
   If it returns `None`, the checkbox is disabled and unchecked.
2. **Post-creation launch:** In `_on_create_project()`, after a successful
   `create_project()` call, if `open_in_vscode_var` is `True`, `open_in_vscode()`
   is called with the newly created project path.
3. **Graceful fallback:** When VS Code is not found, the checkbox is greyed out
   (`state="disabled"`) and the BooleanVar is set to `False`, preventing any
   attempt to launch VS Code.

## Files Changed
- `src/launcher/gui/app.py` — added `find_vscode`/`open_in_vscode` import; checkbox
  disable logic on startup; `open_in_vscode()` call after successful project creation.

## Tests Written
- `tests/GUI-006/__init__.py` — package marker
- `tests/GUI-006/test_gui006_vscode_auto_open.py`:
  - `TestVSCodeCheckboxExists` — AC-1: checkbox and var attributes exist
  - `TestVSCodeCheckboxDisabledWhenNotFound` — AC-3: checkbox disabled when find_vscode returns None
  - Tests for AC-2: VS Code opened after successful project creation when checkbox checked
  - Tests for unchecked / failed creation paths

## Known Limitations
- None identified. The implementation relies on the existing `vscode.py` module;
  any platform-specific edge cases are handled there.
