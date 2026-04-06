# Test Report — GUI-036

**Tester:** Tester Agent  
**Date:** 2026-04-06  
**Iteration:** 1  

---

## Summary

**FAIL.** The implementation is functionally correct and all 13 Developer-written tests pass in isolation. However, GUI-036 changed the `SettingsDialog` geometry from `480x480` to `480x620` without updating the pre-existing assertion in `tests/GUI-018/test_gui018_edge_cases.py`. This constitutes a regression: `test_dialog_geometry_is_480x480` now fails on the GUI-036 branch. The same mistake occurred previously with FIX-076 (BUG-130). Per the testing protocol, any code change that alters externally-asserted behavior must update all affected test assertions in the same commit.

---

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| GUI-036: targeted suite (13 tests) | Unit | **PASS** | TST-2712 — all 13 tests pass in isolation |
| GUI-036: full regression suite | Regression | **FAIL** | TST-2713 — real regression: test_dialog_geometry_is_480x480 |

### Full Suite Summary
- 9136 passed, 201 failed, 348 skipped, 3 warnings, 66 errors
- 200 of those failures are pre-existing (in regression baseline or prior-WP failures)
- **1 new failure is directly caused by GUI-036**: `tests/GUI-018/test_gui018_edge_cases.py::TestDialogGeometry::test_dialog_geometry_is_480x480`

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

### Acceptance Criteria — PASS (functionally)
- ✅ AC1: Red "Uninstall Application" button present in Settings (Danger Zone section).
- ✅ AC2: Confirmation dialog shown before any action.
- ✅ AC3: Windows — launches `unins000.exe` via `Popen` + `sys.exit(0)`.
- ✅ AC4: macOS/Linux — shows manual uninstall instructions via `showinfo`.
- ✅ AC5: Button disabled in dev/source mode (`_find_uninstaller()` returns None).

---

## Bugs Found

- **BUG-205**: GUI-036 broke GUI-018 geometry test: `test_dialog_geometry_is_480x480` (logged in `docs/bugs/bugs.jsonl`)

---

## TODOs for Developer

- [ ] **Update `tests/GUI-018/test_gui018_edge_cases.py`**: Change the assertion on line 145 from `assert_called_with("480x480")` to `assert_called_with("480x620")`. Rename the test function `test_dialog_geometry_is_480x480` → `test_dialog_geometry_is_480x620` and update the docstring accordingly (line 139–145). This is the same fix that was required in FIX-076/Iteration 2 (BUG-130) when the height changed from 480x280 → 480x480. Include this change in the same commit as the rest of GUI-036.
- [ ] Populate `Fixed In WP` for BUG-205 with `GUI-036` in `docs/bugs/bugs.jsonl` after fixing.

---

## Verdict

**FAIL — return to Developer.**

The test suite regression `tests/GUI-018/test_gui018_edge_cases.py::TestDialogGeometry::test_dialog_geometry_is_480x480` must be fixed before this WP can be marked Done. The fix is a one-line assertion update plus a rename of the test function. See TODOs above.
