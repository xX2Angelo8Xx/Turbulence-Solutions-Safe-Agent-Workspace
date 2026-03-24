# Dev Log — INS-022: Create persistent settings module

## Overview

| Field | Value |
|-------|-------|
| WP ID | INS-022 |
| Name | Create persistent settings module |
| Assigned To | Developer Agent |
| Branch | `INS-022/persistent-settings` |
| Status | Review |
| User Story | US-039 |

---

## Implementation Summary

### What was built

Created `src/launcher/core/user_settings.py` — a stdlib-only persistent settings
module for the Turbulence Solutions Launcher.

**Public API:**

| Symbol | Purpose |
|--------|---------|
| `_DEFAULT_SETTINGS` | Module-level dict with `include_readmes: True` |
| `_settings_path()` | Returns OS-appropriate `Path` to `settings.json` |
| `load_settings()` | Reads JSON from disk; merges with defaults; handles missing/corrupt gracefully |
| `save_settings(settings)` | Atomic write via `tempfile.mkstemp` + `os.replace()` |
| `get_setting(key, default)` | Convenience getter; returns `default` if key absent |
| `set_setting(key, value)` | Load → update single key → save |

**OS path logic:**

| OS | Path |
|----|------|
| Windows | `%LOCALAPPDATA%\TurbulenceSolutions\settings.json` |
| macOS/Linux | `${XDG_CONFIG_HOME:-~/.config}/TurbulenceSolutions/settings.json` |

**Safety decisions:**
- Atomic write uses same-directory temp file + `os.replace()` — safe across
  filesystems and power loss; no partial-write corruption risk.
- `load_settings()` catches all exceptions (JSONDecodeError, PermissionError,
  UnicodeDecodeError, OSError) and returns defaults — never raises to caller.
- `save_settings()` cleans up the temp file on write failure before re-raising.
- `load_settings()` merges defaults *under* on-disk values, so new default keys
  are always present while user overrides and extra keys are preserved.

### Files changed

| File | Action |
|------|--------|
| `src/launcher/core/user_settings.py` | Created |
| `tests/INS-022/test_ins022_user_settings.py` | Created |
| `docs/workpackages/workpackages.csv` | Status → In Progress → Review |
| `docs/workpackages/INS-022/dev-log.md` | Created |

---

## Tests Written

Test file: `tests/INS-022/test_ins022_user_settings.py`

| Test class | Tests |
|------------|-------|
| `TestLoadSettings` | defaults when no file, copy-of-defaults, corrupt file, non-dict JSON, load saved value, extra keys preserved, missing key filled from defaults |
| `TestSaveSettings` | creates file, creates missing directory, roundtrip, no temp file left, file contains valid JSON |
| `TestGetSetting` | existing value, default for missing key, default is None |
| `TestSetSetting` | updates single key, creates new key |
| `TestSettingsPath` | Windows LOCALAPPDATA, Linux XDG, Linux XDG_CONFIG_HOME override, macOS |

**Run:** 21 passed, 0 failed  
**Test result record:** TST-2063

---

## Known Limitations / Notes

- `save_settings()` uses `tempfile.mkstemp()` in the same directory as the
  target, which requires the settings directory to exist first. The function
  creates the directory with `mkdir(parents=True, exist_ok=True)` before
  calling mkstemp, so this is always safe.
- The module does not support concurrent processes writing settings simultaneously.
  This is acceptable — the launcher is a single-process application.
