# Test Report — FIX-125: Fix build_windows.py ISCC and PyInstaller issues

**Tester:** Tester Agent  
**Date:** 2026-04-07  
**Branch:** FIX-125/build-script-fixes  
**Verdict:** PASS  

---

## Summary

Both defects addressed by FIX-125 are correctly fixed and verified. All 11 new tests pass. The full test suite shows no new regressions attributable to this WP.

---

## Files Reviewed

| File | Assessment |
|------|------------|
| `scripts/build_windows.py` | Fix 1 (LOCALAPPDATA fallback) and Fix 2 (sys.executable -m PyInstaller) correctly implemented. |
| `tests/FIX-125/test_fix125_build_fixes.py` | 11 tests across two classes. Thorough coverage of both fixes. |
| `tests/MNT-031/test_mnt031_build_windows.py` | Assertion updated from `"pyinstaller"` to `"PyInstaller"` to match new capitalised module invocation. |
| `docs/workpackages/FIX-125/dev-log.md` | Complete, accurate, references correct file names and implementation. |

---

## Test Execution

### FIX-125 + MNT-031 targeted run

```
.venv\Scripts\python.exe -m pytest tests/FIX-125/ tests/MNT-031/ -v --tb=short
```

**Result: 31 passed, 0 failed, 1 warning** (0.56s)

All 11 new FIX-125 tests pass; all 20 existing MNT-031 tests continue to pass with the updated assertion.

### Full suite

```
.venv\Scripts\python.exe -m pytest tests/ --tb=short -q
```

**Result: 9192 passed, 353 skipped, 4 xfailed, 1 xpassed, 249 failed, 91 errors**

- 249 failures and 91 errors are all pre-existing (confirmed by checking main branch).
- GUI-035 `test_no_pycache_directories` / `test_no_pyc_files` fail on main branch identically (pre-existing pycache pollution from prior test runs, not in baseline yet but not caused by FIX-125).
- No new failures introduced by FIX-125.

### Functional dry-run verification

```
.venv\Scripts\python.exe scripts/build_windows.py --dry-run --skip-embed
```

Output confirmed:
- PyInstaller command: `E:\...\python.exe -m PyInstaller launcher.spec -y` ✓
- ISCC found at: `C:\Users\angel\AppData\Local\Programs\Inno Setup 6\ISCC.exe` (LOCALAPPDATA path) ✓

---

## Regression Check

Compared full-suite failures against `tests/regression-baseline.json` (250 entries, `_count: 250`). No new failures are attributable to the FIX-125 changes (verified by diffing failures between main and FIX-125/build-script-fixes branches).

---

## Code Quality Assessment

### Fix 1 — LOCALAPPDATA fallback

- `os.environ.get("LOCALAPPDATA", "")` correctly uses an empty string default to avoid crashing when LOCALAPPDATA is not set.
- The fallback path list now covers: system-wide Program Files (x86), system-wide Program Files, and per-user AppData.
- No hardcoded usernames or absolute user paths.

### Fix 2 — PyInstaller as module

- `[sys.executable, "-m", "PyInstaller", "launcher.spec", "-y"]` is the correct form.
- `-y` flag ensures non-interactive overwrite of `dist/` — appropriate for automated builds.
- Works regardless of whether `.venv\Scripts\` is on system PATH.

### Security considerations

- No new inputs, no new subprocess parameters from user-controlled data.
- `sys.executable` is safe — it is the interpreter running the script, not external input.
- `LOCALAPPDATA` env var is used only for directory lookup, not executed.

---

## Edge Cases Tested by New Tests

| Scenario | Covered |
|----------|---------|
| ISCC found at LOCALAPPDATA per-user path | ✓ |
| LOCALAPPDATA env var reflected in `_ISCC_FALLBACK_PATHS` | ✓ |
| LOCALAPPDATA absent/empty — exits cleanly with code 1 | ✓ |
| Per-user path wins when system paths absent | ✓ |
| step_pyinstaller uses `sys.executable` as cmd[0] | ✓ |
| `-m` flag present | ✓ |
| Module name is `PyInstaller` (not `pyinstaller`) | ✓ |
| `-y` flag present | ✓ |
| `launcher.spec` included | ✓ |
| Full command structure matches exactly | ✓ |
| Bare `pyinstaller` not used | ✓ |

---

## Verdict

**PASS** — Both defects fixed correctly, all tests pass, no regressions introduced, functional dry-run confirms both fixes work on this machine. Setting WP to Done.
