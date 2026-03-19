# FIX-057 Dev Log — Deploy ts-python shim in Linux AppImage build

## Status
Review

## Goal
Bundle the `ts-python` shim inside the Linux AppImage so that `ensure_shim_deployed()` can locate and deploy it on first launch.

## Implementation

### File Changed
**`src/installer/linux/build_appimage.sh`**

Added a shim bundling block immediately after the python-embed copy block (Step 2) and before Step 3 (`.desktop` file):

```bash
# FIX-057: Bundle the ts-python shim inside the AppImage for first-launch deployment
echo "==> Bundling ts-python shim..."
mkdir -p "${APPDIR}/usr/share/shims"
cp "src/installer/shims/ts-python" "${APPDIR}/usr/share/shims/ts-python"
chmod +x "${APPDIR}/usr/share/shims/ts-python"
```

This places the shim at `usr/share/shims/ts-python` inside the AppImage, which is exactly the path checked by `_find_bundled_shim()` in `shim_config.py` (Linux AppImage layout: `usr/bin/launcher → shim at usr/share/shims/`).

## Tests Written
- `tests/FIX-057/__init__.py`
- `tests/FIX-057/test_fix057.py`

Six tests covering:
1. `build_appimage.sh` contains `usr/share/shims/ts-python`
2. `build_appimage.sh` contains `chmod +x` for the bundled shim
3. `build_appimage.sh` creates `${APPDIR}/usr/share/shims` directory
4. The shim source path references `src/installer/shims/ts-python`
5. `_find_bundled_shim()` in `shim_config.py` checks the Linux AppImage path pattern
6. The shim bundling block appears before the `.desktop` file section

## Test Results
All 6 tests pass.

## Files Changed
- `src/installer/linux/build_appimage.sh` — added shim bundling step
- `docs/workpackages/workpackages.csv` — FIX-057 status → In Progress / Review
- `docs/workpackages/FIX-057/dev-log.md` — this file
- `tests/FIX-057/__init__.py`
- `tests/FIX-057/test_fix057.py`
