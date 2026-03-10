# Dev Log — INS-001

**Developer:** Developer Agent
**Date started:** 2026-03-10
**Iteration:** 1

## Objective

Create the `src/` directory structure that forms the foundation of the Turbulence Solutions Launcher. Required files: `launcher/main.py`, `gui/app.py`, `gui/components.py`, `core/project_creator.py`, `core/vscode.py`, `core/os_utils.py`, `config.py`, and `installer/` with per-platform subdirectories (`windows/`, `macos/`, `linux/`). Entry point `python src/launcher/main.py` must run without import errors.

## Implementation Summary

Created the full `src/` layout following the `src`-layout convention (standard for Python packaging):

- `src/launcher/` is the top-level Python package (has `__init__.py`).
- `src/launcher/gui/` and `src/launcher/core/` are sub-packages (each has `__init__.py`).
- `src/launcher/main.py` inserts `src/` onto `sys.path` at startup so it can be run directly via `python src/launcher/main.py` without a prior `pip install`.
- `src/installer/windows/`, `macos/`, `linux/` are platform directories for future installer scripts (INS-005/006/007); they contain README placeholders.
- All modules are stubs with correct imports — ready for implementation in subsequent WPs.

Key decisions:
- Used the `src`-layout (no `src/__init__.py`) so `pip install -e .` in INS-002 can declare the package root as `src/`.
- `main.py` dynamically patches `sys.path` only when run as a script so it is transparent when imported as a module during testing or after packaging.
- Added basic input validation in `project_creator.py` (path traversal guard) at the system boundary as required by security-rules.md.

## Files Changed

- `src/launcher/__init__.py` — Package marker
- `src/launcher/main.py` — Entry point; patches sys.path, imports core modules
- `src/launcher/config.py` — APP_NAME and VERSION constants
- `src/launcher/gui/__init__.py` — Package marker
- `src/launcher/gui/app.py` — Stub App class
- `src/launcher/gui/components.py` — Stub for reusable GUI components
- `src/launcher/core/__init__.py` — Package marker
- `src/launcher/core/project_creator.py` — Stub project creation logic with path-traversal guard
- `src/launcher/core/vscode.py` — VS Code detection and launch utilities
- `src/launcher/core/os_utils.py` — OS detection utility
- `src/launcher/core/updater.py` — Stub updater (full implementation deferred to INS-009)
- `src/installer/windows/README.md` — Placeholder
- `src/installer/macos/README.md` — Placeholder
- `src/installer/linux/README.md` — Placeholder
- `tests/__init__.py` — Test package marker
- `tests/conftest.py` — Adds src/ to sys.path for pytest
- `tests/test_ins001_structure.py` — Structure and import tests

## Tests Written

- `test_src_dir_exists` — Verifies `src/` directory exists
- `test_launcher_dir_exists` — Verifies `src/launcher/` exists
- `test_launcher_main_exists` — Verifies `src/launcher/main.py` exists
- `test_launcher_init_exists` — Verifies `src/launcher/__init__.py` exists
- `test_launcher_config_exists` — Verifies `src/launcher/config.py` exists
- `test_gui_package_exists` — Verifies `src/launcher/gui/__init__.py` exists
- `test_gui_app_exists` — Verifies `src/launcher/gui/app.py` exists
- `test_gui_components_exists` — Verifies `src/launcher/gui/components.py` exists
- `test_core_package_exists` — Verifies `src/launcher/core/__init__.py` exists
- `test_core_project_creator_exists` — Verifies `src/launcher/core/project_creator.py` exists
- `test_core_vscode_exists` — Verifies `src/launcher/core/vscode.py` exists
- `test_core_os_utils_exists` — Verifies `src/launcher/core/os_utils.py` exists
- `test_core_updater_exists` — Verifies `src/launcher/core/updater.py` exists
- `test_installer_dir_exists` — Verifies `src/installer/` exists
- `test_installer_windows_dir_exists` — Verifies `src/installer/windows/` exists
- `test_installer_macos_dir_exists` — Verifies `src/installer/macos/` exists
- `test_installer_linux_dir_exists` — Verifies `src/installer/linux/` exists
- `test_main_py_runs_without_import_errors` — Runs `python src/launcher/main.py` as subprocess; asserts exit code 0
- `test_launcher_config_importable` — Imports `launcher.config` and checks APP_NAME and VERSION attributes
- `test_os_utils_get_platform` — Calls `get_platform()` and asserts result is one of the three known OS strings

## Known Limitations

- All module implementations are stubs; full logic is deferred to downstream WPs (GUI-001–GUI-007 for gui/, INS-009–INS-011 for updater.py, INS-005–INS-007 for installer scripts).
- `customtkinter` is not yet declared as a dependency (deferred to INS-002); `gui/app.py` and `gui/components.py` do not import it yet.
- `tests/` location is at the repository root — consistent with `src`-layout convention; the testing-protocol references `Project/tests/` which is interpreted as the project root `tests/`.
