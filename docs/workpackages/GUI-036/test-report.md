# Test Report — GUI-036

**Tester:** Tester Agent  
**Date:** 2026-04-07  
**Iteration:** 2  

---

## Summary

**PASS.** All acceptance criteria met. BUG-205 geometry regression was resolved in Iteration 2: `test_dialog_geometry_is_480x480` renamed to `test_dialog_geometry_is_480x620` with updated assertion. Full suite shows 199 pre-existing failures only — no new regressions introduced by GUI-036.

---

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| GUI-036: targeted suite (13 tests) | Unit | **PASS** | TST-2717 — all 13 tests pass |
| GUI-036: geometry regression fix (GUI-018) | Regression | **PASS** | TST-2718 — test_dialog_geometry_is_480x620 passes |
| GUI-036: full regression suite | Regression | **PASS*** | TST-2716 — 9138 passed, 199 pre-existing failures, 0 new |

*199 failures are all pre-existing (baseline: 261 entries). No new failure introduced by GUI-036.

### Full Suite Summary (Iteration 2)
- 9138 passed, 199 failed, 348 skipped, 4 xfailed, 1 xpassed, 3 warnings, 66 errors
- All 199 failures are pre-existing baseline failures
- **0 new failures** introduced by GUI-036

### Comparison to Iteration 1
| Metric | Iteration 1 | Iteration 2 |
|--------|-------------|-------------|
| Passed | 9136 | 9138 |
| Failed | 201 | 199 |
| New failures | 1 (geometry) | 0 |

---

## Code Review Findings

### Implementation Quality — OK
- `_find_uninstaller()`: correct platform guard (`sys.platform != "win32"`), fixed path from `sys.executable` parent, no user input involved.
- `_on_uninstall()`: mandatory confirmation via `messagebox.askyesno()` — no bypass possible.
- Subprocess call: `subprocess.Popen([str(uninstaller)])` — list form prevents shell injection.
- TOCTOU protection: uninstaller re-checked at click time (not just at button construction).
- Button disabled when uninstaller not found — correct dev/source mode behaviour.

### Security Analysis — PASS
- **No shell injection**: `subprocess.Popen` called with list, not string; `shell=True` not used.
- **No user-controlled path**: path is always `Path(sys.executable).parent / "unins000.exe"`.
- **Confirmation mandatory**: `askyesno` must return `True` before any destructive action.
- **TOCTOU mitigated**: second `_find_uninstaller()` call at click time guards against the file disappearing.
- **No information leakage**: error and info dialogs reveal no sensitive internal state.

### Acceptance Criteria — PASS
- ✅ AC1: Red "Uninstall Application" button present in Settings (Danger Zone section).
- ✅ AC2: Confirmation dialog shown before any action.
- ✅ AC3: Windows — launches `unins000.exe` via `Popen` + `sys.exit(0)`.
- ✅ AC4: macOS/Linux — shows manual uninstall instructions via `showinfo`.
- ✅ AC5: Button disabled in dev/source mode (`_find_uninstaller()` returns None).

---

## Bugs Found

| Bug | Status |
|-----|--------|
| BUG-205: GUI-036 broke GUI-018 geometry test | **Closed** |

---

## Verdict

**PASS — approved for Done.**

All 13 GUI-036 tests pass. Geometry regression (BUG-205) resolved. No new regressions in the full suite. Workspace validation clean (exit 0).
