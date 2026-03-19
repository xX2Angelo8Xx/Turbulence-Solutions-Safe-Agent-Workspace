# FIX-041 Dev Log — Fix stale version label from .dist-info in overlay installs

**WP ID:** FIX-041  
**Branch:** fix/FIX-041-stale-version-distinfo  
**Developer:** Developer Agent  
**Date:** 2026-03-18  
**Status:** In Progress → Review

---

## Summary

Fixed BUG-075: version label showed stale version from a previous `.dist-info` directory after an overlay install on Windows.

## Root Cause

`get_display_version()` in `src/launcher/config.py` called `importlib.metadata.version("agent-environment-launcher")`. When Inno Setup performs an overlay install (v2.1.1 → v2.1.2), both `.dist-info` directories coexist inside `_internal/`:

- `agent_environment_launcher-2.1.1.dist-info/` (old — NOT removed by overlay)
- `agent_environment_launcher-2.1.2.dist-info/` (new)

`importlib.metadata` found the old one first and returned `"2.1.1"`, causing the version label to show `v2.1.1` even though the binary was `v2.1.2`.

`check_for_update()` in `app.py` uses `VERSION` directly (line 328, 351) and was therefore correct throughout — only the display label was affected.

## Fix Applied

**File:** `src/launcher/config.py`

Changed `get_display_version()` to check `sys._MEIPASS` first. When running inside a PyInstaller bundle (i.e. `sys._MEIPASS` is set), the function returns `VERSION` constant directly without consulting `importlib.metadata`. Only in development (no `_MEIPASS`) is `importlib.metadata` attempted as a convenience, with `VERSION` as the fallback if the package is not installed.

```python
def get_display_version() -> str:
    """Return the installed package version, falling back to VERSION constant."""
    # In PyInstaller bundles, always use the VERSION constant — importlib.metadata
    # may read stale .dist-info from a previous overlay install (BUG-075).
    if getattr(sys, '_MEIPASS', None):
        return VERSION
    try:
        from importlib.metadata import version, PackageNotFoundError
        return version("agent-environment-launcher")
    except PackageNotFoundError:
        return VERSION
```

## Files Changed

| File | Change |
|------|--------|
| `src/launcher/config.py` | `get_display_version()` — PyInstaller bundle guard added |
| `docs/bugs/bugs.csv` | BUG-075 entry added |
| `docs/workpackages/workpackages.csv` | FIX-041 entry added |
| `docs/workpackages/FIX-041/dev-log.md` | This file |
| `tests/FIX-041/test_fix041_version_display.py` | 6 tests written |

## Tests Written

| Test | Description |
|------|-------------|
| `test_get_display_version_in_pyinstaller_uses_VERSION` | With `sys._MEIPASS` set, returns `VERSION` constant |
| `test_get_display_version_without_meipass_uses_importlib` | Without `_MEIPASS`, tries `importlib.metadata` |
| `test_get_display_version_importlib_fallback_to_VERSION` | Without `_MEIPASS` and importlib raises `PackageNotFoundError`, falls back to `VERSION` |
| `test_get_display_version_pyinstaller_ignores_stale_distinfo` | With `_MEIPASS` and importlib returning stale version, still returns `VERSION` |
| `test_version_label_uses_get_display_version` | `app.py` version_label text includes `get_display_version()` result |
| `test_check_for_update_uses_VERSION_not_get_display_version` | `app.py` passes `VERSION` (not `get_display_version()`) to `check_for_update()` |

## Test Results

All 6 FIX-041 tests pass. Full suite run — no regressions.

## Known Limitations

None. The fix is minimal and targeted — only changes behaviour in PyInstaller bundles.
