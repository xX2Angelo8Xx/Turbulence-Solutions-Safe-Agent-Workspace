# FIX-037 Dev Log — Remove .dist-info dirs from macOS bundle before signing

## WP Details

| Field | Value |
|-------|-------|
| WP ID | FIX-037 |
| Category | Fix |
| Status | In Progress → Review |
| Assigned To | Developer Agent |
| Branch | fix/FIX-037-remove-dist-info-codesign |
| Bug | BUG-070 |
| User Story | US-026 |
| Date | 2026-03-18 |

## Problem

macOS CI build for v2.1.0 fails during code signing with:

```
dist/AgentEnvironmentLauncher.app/Contents/MacOS/launcher: bundle format unrecognized, invalid, or unsuitable
In subcomponent: .../dist/AgentEnvironmentLauncher.app/Contents/MacOS/_internal/agent_environment_launcher-2.1.0.dist-info
```

The `agent_environment_launcher-2.1.0.dist-info` directory is Python package metadata that PyInstaller bundles when the project is installed via `pip install -e .`. macOS `codesign` treats every directory inside `_internal/` as a potential bundle subcomponent and cannot process `.dist-info` directories (they lack `Info.plist` and a valid bundle structure). The error is fatal — it prevents CI from producing a signed artifact.

## Root Cause

`pip install -e .` installs an editable build of the project. As a side effect, it creates a `.dist-info` directory (e.g. `agent_environment_launcher-2.1.0.dist-info`) inside the Python `site-packages`. PyInstaller then copies it into `_internal/` alongside the actual runtime files. `.dist-info` directories are standard Python packaging metadata — they are only needed by `pip` at development time and carry no runtime value for a PyInstaller bundle.

## Fix

Added **Step 3.1** to `src/installer/macos/build_dmg.sh`, placed after the Info.plist write (Step 3) and before code signing (Step 3.5):

```bash
# ---------------------------------------------------------------------------
# Step 3.1: Remove .dist-info directories (Python package metadata not needed
# at runtime; macOS codesign cannot process them as bundle subcomponents)
# ---------------------------------------------------------------------------
echo "==> Removing .dist-info directories from bundle..."
find "${APP_BUNDLE}/Contents/MacOS/_internal" -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
```

**Design decisions:**
- `find ... -exec rm -rf {} + 2>/dev/null || true` — error-suppressed, idempotent; if `_internal/` does not exist or contains no `.dist-info` dirs, the script continues cleanly.
- Targets only `_internal/` — this is where PyInstaller places runtime files; no risk of touching other bundle structures.
- Uses `-type d -name "*.dist-info"` — precisely targets the metadata directories by their well-known naming pattern.
- Runs before code signing so the bundle is clean before `codesign` inspects it.
- No changes to any other production code file.

## Files Changed

| File | Change |
|------|--------|
| `src/installer/macos/build_dmg.sh` | Added Step 3.1 — .dist-info cleanup before codesign |
| `docs/workpackages/workpackages.csv` | Added FIX-037 row |
| `docs/bugs/bugs.csv` | Added BUG-070 row |
| `docs/user-stories/user-stories.csv` | Added FIX-037 to US-026 Linked WPs |
| `docs/workpackages/FIX-037/dev-log.md` | This file |
| `tests/FIX-037/__init__.py` | Test package init |
| `tests/FIX-037/test_fix037_dist_info_cleanup.py` | Test suite (6 test cases) |

## Tests Written

| Test | Description |
|------|-------------|
| `test_script_contains_dist_info_find_command` | build_dmg.sh contains a `find` command targeting `*.dist-info` directories |
| `test_dist_info_removal_before_codesign` | The cleanup step appears before the Step 3.5 code signing section |
| `test_removal_targets_internal_directory` | The `find` command targets the `_internal` directory specifically |
| `test_removal_uses_rm_rf` | The cleanup uses `rm -rf` for directory removal |
| `test_codesign_steps_still_present` | All existing code signing steps are still present (regression) |
| `test_error_suppression_present` | The cleanup command uses `2>/dev/null \|\| true` for safe error suppression |

## Test Results

All 6 FIX-037 tests pass. Full suite run logged in `docs/test-results/test-results.csv`.

## Known Limitations

None. The fix is narrowly scoped to removing `.dist-info` directories before signing.
