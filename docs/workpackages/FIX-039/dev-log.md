# Dev Log — FIX-039

**WP:** FIX-039 — Skip launcher re-sign inside .app — verify pre-bundle binary  
**Status:** In Progress → Review  
**Assigned To:** Developer Agent  
**Date:** 2026-03-18  
**Branch:** fix/FIX-039-skip-launcher-resign  
**Bug Reference:** BUG-072

---

## Summary

macOS CI build was failing with:

```
dist/AgentEnvironmentLauncher.app/Contents/MacOS/launcher: replacing existing signature
dist/AgentEnvironmentLauncher.app/Contents/MacOS/launcher: code object is not signed at all
In subcomponent: .../dist/AgentEnvironmentLauncher.app/Contents/MacOS/_internal/TS-Logo.png
Error: Process completed with exit code 1.
```

**Root cause:** `launcher` is declared as `CFBundleExecutable` in `Info.plist`. When `codesign --force --sign -` or `codesign --verify` is invoked on `Contents/MacOS/launcher`, macOS treats this as a bundle operation and recursively validates all subcomponents — including non-code data files like `TS-Logo.png`, which are not signable code objects.

PyInstaller already ad-hoc signs the binary at build time (`Re-signing the EXE`). The pre-bundle binary at `dist/launcher/launcher` has a valid ad-hoc signature that is preserved when copied into the `.app` via `cp -R`.

---

## Changes Made

### `src/installer/macos/build_dmg.sh`

1. **Removed** `codesign --force --sign - "${APP_BUNDLE}/Contents/MacOS/launcher"` — this triggered bundle validation on re-sign.
2. **Removed** `codesign --verify "${APP_BUNDLE}/Contents/MacOS/launcher"` — this also triggered bundle validation.
3. **Added** `codesign --verify "${DIST_DIR}/launcher/launcher"` — verifies the pre-bundle binary that has the PyInstaller ad-hoc signature.
4. **Kept unchanged:** `.dylib`, `.so`, and `Python.framework` signing — these are standalone code objects, not the `CFBundleExecutable`, and work correctly.

### `.github/workflows/release.yml`

- Changed `Verify Code Signing` step in `macos-arm-build` job from:
  ```
  codesign --verify dist/AgentEnvironmentLauncher.app/Contents/MacOS/launcher
  ```
  to:
  ```
  codesign --verify dist/launcher/launcher
  ```
- Python.framework verification line left unchanged.

---

## Files Changed

| File | Change |
|------|--------|
| `src/installer/macos/build_dmg.sh` | Removed launcher re-sign and in-bundle verify; added pre-bundle verify |
| `.github/workflows/release.yml` | Updated launcher verify path to pre-bundle binary |

---

## Tests Written

- `tests/FIX-039/test_fix039_skip_launcher_resign.py`

Tests verify:
- `build_dmg.sh` does NOT contain `codesign --force --sign -` on `Contents/MacOS/launcher`
- `build_dmg.sh` does NOT contain `codesign --verify` on `Contents/MacOS/launcher`
- `build_dmg.sh` DOES contain `codesign --verify` on `${DIST_DIR}/launcher/launcher`
- `build_dmg.sh` still signs `.dylib` files
- `build_dmg.sh` still signs `.so` files
- `build_dmg.sh` still signs `Python.framework`
- `release.yml` verifies `dist/launcher/launcher` (not inside the `.app`)
- `release.yml` still verifies `Python.framework`

---

## Decisions

- The launcher's in-bundle path (`Contents/MacOS/launcher`) was the `CFBundleExecutable`, so both signing and verifying it operate at the bundle level, not the binary level. Verification must target the pre-bundle binary.  
- No change to architecture, build flow, or other signing steps — minimal targeted fix per scope rules.

---

## Known Limitations

None. The fix is complete for ad-hoc (unsigned developer) signing. Distributable `.app` bundles would require a Developer ID certificate and notarisation, but that is out of scope for this project.
