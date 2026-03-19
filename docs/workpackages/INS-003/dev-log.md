# Dev Log — INS-003

**Developer:** Developer Agent
**Date started:** 2026-03-12
**Iteration:** 1

## Objective
Create a PyInstaller `.spec` file that configures `--onedir` bundling for the Turbulence Solutions Launcher. The entry point is `src/launcher/main.py`. The `templates/` directory must be included as bundled data so the app can locate project templates at runtime.

## Implementation Summary

Created `launcher.spec` at the repository root. Key design decisions:

- **Onedir mode**: `EXE` uses `exclude_binaries=True` and a `COLLECT()` step bundles the executable with its supporting libraries in a single directory. This is the standard `--onedir` pattern.
- **Entry point**: `src/launcher/main.py` — referenced using `os.path.join(SPECPATH, ...)` so the path resolves correctly regardless of where `pyinstaller` is invoked from.
- **`pathex`**: Set to `src/` so PyInstaller resolves the `launcher.*` package imports correctly during analysis.
- **`datas`**: `(os.path.join(SPECPATH, 'templates'), 'templates')` bundles the `templates/` directory (created in INS-004). At build time this directory must exist; the spec file is valid before INS-004 is complete, but a full `pyinstaller` build will require it.
- **`hiddenimports`**: `['customtkinter']` — customtkinter uses dynamic imports internally that PyInstaller may not detect statically. This prevents missing-module errors at runtime.
- **`console=False`**: GUI app; suppresses the console window on Windows.
- **Cross-platform**: `os.path.join` uses OS-appropriate separators; `SPECPATH` is a PyInstaller built-in available on all platforms.

### .gitignore Conflict — Noted
`docs/workpackages/INS-012/` added `*.spec` to `.gitignore` (intended for auto-generated specs). `launcher.spec` is a source file, not a generated artifact. Per WP instructions, `.gitignore` was NOT modified. The spec file must be committed with `git add -f launcher.spec` to force-track it. The INS-012 regression test `test_gitignore_git_recognises_spec` relies on `*.spec` being in `.gitignore`; adding a `!launcher.spec` exception would break that test, so force-add is the correct approach.

## Files Changed
- `launcher.spec` — created; PyInstaller onedir spec file
- `tests/INS-003/__init__.py` — created; makes INS-003 a test package
- `tests/INS-003/test_ins003_pyinstaller_spec.py` — created; 7 unit tests for the spec file

## Tests Written
- `test_spec_file_exists` — spec file exists at repository root
- `test_spec_is_valid_python` — `ast.parse` succeeds (no syntax errors)
- `test_spec_references_entry_point` — `main.py` referenced in the Analysis sources
- `test_spec_entry_point_path_contains_src_launcher` — full path `src/launcher/main.py` present
- `test_spec_includes_templates_in_datas` — `templates` appears in the datas section
- `test_spec_uses_onedir_collect` — `COLLECT(` call is present (onedir mode requires it)
- `test_spec_exclude_binaries_true` — `exclude_binaries=True` is set in `EXE()` (onedir, not onefile)

## Known Limitations
- `templates/` does not yet exist (INS-004 will create it). A `pyinstaller launcher.spec` build will fail until INS-004 is complete. The spec file itself is correct and all tests pass.
- `launcher.spec` requires `git add -f` at commit time due to the `*.spec` glob in `.gitignore`. This is a known workflow quirk documented here.
