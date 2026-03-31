# Dev Log — FIX-089: Fix Inno Setup stale template files on upgrade

**Status:** In Progress  
**Assigned To:** Developer Agent  
**Branch:** FIX-089/inno-setup-stale-templates  
**Date Started:** 2026-03-31  

---

## Problem

When upgrading the Windows installer from a previous version (e.g. v3.2.6 → v3.3.0),
Inno Setup overlays new files on top of the existing installation directory but never
removes old files. Template files that were deleted between versions — such as old agents
(e.g. `scientist.agent.md`) or old skills (e.g. `ts-code-review/`) — persist in the
installation directory. When users create new workspaces, `shutil.copytree` copies ALL
files from `_internal\templates`, including the stale ones.

## Root Cause

The `[Files]` section in `setup.iss` uses `Flags: ignoreversion recursesubdirs createallsubdirs`,
which copies new files but never removes old ones. There was no `[InstallDelete]` section
to clean stale files before new files are installed.

## Fix

Added an `[InstallDelete]` section before the `[Files]` section in
`src/installer/windows/setup.iss`. The directive removes `{app}\_internal\templates`
(the PyInstaller bundle's templates directory) before Inno Setup copies the new files.
Inno Setup processes `[InstallDelete]` before `[Files]`, so the fresh templates
directory is written cleanly after the old one is deleted.

```ini
[InstallDelete]
; FIX-089: Remove stale template files from previous installations.
; Inno Setup overlays new files but never deletes old ones, so template
; files deleted between versions would persist and contaminate new workspaces.
Type: filesandordirs; Name: "{app}\_internal\templates"
```

## Files Changed

- `src/installer/windows/setup.iss` — added `[InstallDelete]` section

## Tests Written

- `tests/FIX-089/test_fix089_inno_setup_install_delete.py`

Tests verify:
1. `[InstallDelete]` section exists in setup.iss
2. The directive targets `{app}\_internal\templates`
3. The `Type` is `filesandordirs`
4. The `[Files]` section still has `recursesubdirs` flag (unchanged)
5. The `[InstallDelete]` section appears before the `[Files]` section

## Decisions

- Placed `[InstallDelete]` before `[Files]` for readability; Inno Setup processes
  `[InstallDelete]` first regardless of script order.
- Used `Type: filesandordirs` to ensure both files and subdirectories within
  `templates` are removed (covers nested skill folders like `ts-code-review/`).
- Only `_internal\templates` is removed — not the full `_internal` directory —
  to avoid disrupting other bundled files (Python runtime, launcher binaries, etc.).

## Known Limitations

- This fix only applies to the Windows installer. macOS and Linux use separate install
  mechanisms and are not affected by this change.
- On a fresh install (no previous installation present), the `[InstallDelete]` entry
  is safely ignored by Inno Setup if the path does not exist.
