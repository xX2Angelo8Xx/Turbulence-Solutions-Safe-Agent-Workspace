# FIX-062 — Dev Log

## Workpackage
**ID:** FIX-062  
**Name:** Fix macOS codesign TS-Logo.png failure  
**Bug Reference:** BUG-088  
**Branch:** FIX-062/fix-macos-codesign-resource-relocation  
**Assigned To:** Developer Agent  
**Status:** In Progress  

---

## Problem Summary

The macOS CI build fails during ad-hoc code signing in `src/installer/macos/build_dmg.sh`. The
`codesign --options runtime` command on the `.app` bundle rejects non-code data files
(`TS-Logo.png`, `TS-Logo.ico`) that reside in `Contents/MacOS/_internal/` as unsigned
subcomponents.

Root cause: `build_dmg.sh` copies ALL PyInstaller `--onedir` output (including image assets
bundled via `launcher.spec` datas) into `Contents/MacOS/`. macOS treats every file in
`Contents/MacOS/` as a code subcomponent and refuses to sign the bundle when it encounters
non-executable files there.

---

## Implementation

### Files Changed

| File | Change |
|------|--------|
| `src/installer/macos/build_dmg.sh` | Added Step 3.2 — relocate non-code resources to `Contents/Resources/` and create relative symlinks in `_internal/` |

### Step 3.2 — Resource Relocation Logic

After the existing Step 3.1 (`.dist-info` removal) and before Step 3.5 (code signing):

```bash
for f in TS-Logo.png TS-Logo.ico; do
    if [ -f "${APP_BUNDLE}/Contents/MacOS/_internal/${f}" ]; then
        mv "${APP_BUNDLE}/Contents/MacOS/_internal/${f}" "${APP_BUNDLE}/Contents/Resources/${f}"
        ln -s "../../Resources/${f}" "${APP_BUNDLE}/Contents/MacOS/_internal/${f}"
    fi
done
```

**Why relative symlinks work:** The path `../../Resources/<filename>` resolves correctly
because `Contents/MacOS/_internal/` is two levels deep relative to `Contents/`, and
`Contents/Resources/` is a sibling of `Contents/MacOS/`. At runtime `sys._MEIPASS` points
to `Contents/MacOS/_internal/`, so following the symlink resolves to the actual file in
`Contents/Resources/`.

### No Runtime Impact

The PyInstaller-generated executable uses `sys._MEIPASS` to locate bundled data. Because the
symlink is placed at the original location, the lookup path is unchanged. The file is simply
transparently redirected to `Contents/Resources/` — the macOS-blessed location for non-code
bundle resources.

---

## Tests Written

| Test File | Description |
|-----------|-------------|
| `tests/FIX-062/test_fix062_resource_relocation.py` | Verifies the relocation block is present and syntactically correct in build_dmg.sh; validates symlink path correctness |

---

## Iteration 1 — Initial Implementation

**Date:** 2026-03-20  
**Result:** Implementation complete, tests pass.

### Summary of Changes
- Added Step 3.2 to `src/installer/macos/build_dmg.sh` between Step 3.1 and Step 3.5
- Step loops over `TS-Logo.png` and `TS-Logo.ico`, moves each present file to `Contents/Resources/`, and creates a relative symlink back in `_internal/`
- Created `tests/FIX-062/test_fix062_resource_relocation.py` with regression and unit tests
