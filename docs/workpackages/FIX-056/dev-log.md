# Dev Log — FIX-056: Deploy ts-python shim in macOS DMG build

## Status
Review

## Goal
On macOS DMG installs and Linux AppImage, the ts-python shim was never deployed. This WP adds:
1. Shim bundling in `build_dmg.sh` (copied into `Contents/Resources/shims/`)
2. `ensure_shim_deployed()` first-launch logic in `shim_config.py`
3. Call to `ensure_shim_deployed()` in `main.py`
4. PyInstaller `datas` entry in `launcher.spec` to bundle the shim

## Files Changed
- `src/installer/macos/build_dmg.sh` — bundle shim into Contents/Resources/shims/
- `src/launcher/core/shim_config.py` — add ensure_shim_deployed(), helper functions
- `src/launcher/main.py` — call ensure_shim_deployed() on startup (non-test mode)
- `launcher.spec` — add shims/ to PyInstaller datas

## Implementation Summary

### build_dmg.sh
After the `cp -R` that copies PyInstaller output into `Contents/MacOS/`, a new block:
- Creates `Contents/Resources/shims/` directory
- Copies `src/installer/shims/ts-python` into it
- Sets `chmod +x` on the shim

### shim_config.py — new functions
- `ensure_shim_deployed()` — entry point; skips on Windows, skips if config already exists,
  finds bundled shim and Python, deploys to `~/.local/share/TurbulenceSolutions/bin/`
- `_find_bundled_shim()` — locates shim from PyInstaller bundle (_MEIPASS or macOS .app layout)
- `_find_bundled_python_exe()` — locates bundled Python for writing python-path.txt
- `_add_to_shell_profile()` — appends export line to ~/.zshrc / ~/.bashrc (best-effort)

### main.py
Imports `ensure_shim_deployed` and calls it before the GUI launches (skipped under pytest).

### launcher.spec
Adds `(os.path.join(SPECPATH, 'src', 'installer', 'shims'), 'shims')` to the `datas` list.

## Tests Written
- `tests/FIX-056/test_fix056.py` — 11 test cases covering all new code paths

## Test Results
- TST-1880: 13/13 FIX-056 tests pass (targeted suite)
- TST-1881: Full suite exit code 0; pre-existing failure baseline unchanged
