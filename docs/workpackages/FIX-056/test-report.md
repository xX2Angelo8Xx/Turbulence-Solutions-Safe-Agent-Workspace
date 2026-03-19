# Test Report — FIX-056: Deploy ts-python shim in macOS DMG build

## Verdict: PASS

## Tester
Tester Agent — 2026-03-19

---

## Code Review

### build_dmg.sh
- `mkdir -p "${APP_BUNDLE}/Contents/Resources/shims"` — directory creation confirmed.
- `cp "src/installer/shims/ts-python" "${APP_BUNDLE}/Contents/Resources/shims/ts-python"` — copy confirmed.
- `chmod +x "${APP_BUNDLE}/Contents/Resources/shims/ts-python"` — execute bit set.
- All three steps present and correct. ✓

### launcher.spec
- `(os.path.join(SPECPATH, 'src', 'installer', 'shims'), 'shims')` present in `datas` list with inline FIX-056 comment. ✓

### shim_config.py — new functions
| Function | Verified |
|---|---|
| `ensure_shim_deployed()` | Returns early on Windows (platform check first). Returns early when `python-path.txt` is non-empty. Returns early when shim not found. Returns early when Python not found. Deploys shim + writes config + adds to shell profile when all conditions met. ✓ |
| `_find_bundled_shim()` | Checks `sys._MEIPASS` guard first; tries `_MEIPASS/shims/ts-python`, then macOS `.app` layout, then Linux AppImage layout. Returns `None` without `_MEIPASS`. ✓ |
| `_find_bundled_python_exe()` | Checks `sys._MEIPASS` guard; tries Python.framework path, then `python-embed/python3`, then `python-embed/python`. Returns `None` without `_MEIPASS`. ✓ |
| `_add_to_shell_profile()` | Skips non-existent profiles (no creation). Checks for duplicate entry before appending. Swallows `OSError` (read-only file). Best-effort contract honoured. ✓ |

### main.py
- `from launcher.core.shim_config import ensure_shim_deployed` present. ✓
- `ensure_shim_deployed()` called after `PYTEST_CURRENT_TEST` guard, before `App().run()`. ✓
- Call is correctly placed: only runs in production (not under pytest). ✓

### Security Assessment
- No arbitrary path writes: shim deploy target is always `~/.local/share/TurbulenceSolutions/bin/` derived from `get_shim_dir()`.
- No command injection: no shell=True, no user-controlled string interpolated into commands.
- No SSRF or network calls.
- `os.chmod(str(shim_dest), 0o755)` is appropriate for an executable shim.
- `OSError` on profile write is silently swallowed — correct for best-effort, no security concern.
- **No security issues found.** ✓

---

## Test Runs

### TST-1882 — Targeted suite (FIX-056, 18 tests)
**Command:** `.\.venv\Scripts\python.exe -m pytest tests/FIX-056/ -v`  
**Result:** 18 passed / 0 failed  
**Date:** 2026-03-19

### TST-1883 — Full regression suite
**Command:** `.\.venv\Scripts\python.exe -m pytest tests/ --continue-on-collection-errors --tb=no -q`  
**Result:** exit code 0 — no new failures introduced  
**Date:** 2026-03-19

---

## Edge-Case Tests Added (5 tests)

| Test | What it verifies |
|---|---|
| `test_add_to_shell_profile_skips_nonexistent_file` | Profile files that don't exist are silently skipped; no file is created. |
| `test_add_to_shell_profile_readonly_file_does_not_raise` | Read-only profile files do not cause an exception; OSError is swallowed. |
| `test_ensure_shim_deployed_returns_early_when_shim_not_found` | When `_find_bundled_shim()` returns None, `_find_bundled_python_exe()` is never called. |
| `test_ensure_shim_deployed_returns_early_when_python_not_found` | When `_find_bundled_python_exe()` returns None, `get_shim_dir()` is never called. |
| `test_find_bundled_shim_returns_none_without_meipass` | `_find_bundled_shim()` returns None when `sys._MEIPASS` is absent (dev / non-bundled run). |

---

## Pre-Done Checklist

- [x] `docs/workpackages/FIX-056/dev-log.md` exists and is non-empty
- [x] `docs/workpackages/FIX-056/test-report.md` written by Tester
- [x] Test files exist in `tests/FIX-056/` with 18 tests (13 Developer + 5 Tester)
- [x] All test runs logged in `docs/test-results/test-results.csv` (TST-1882, TST-1883)
- [x] WP status set to `Done` in `workpackages.csv`
