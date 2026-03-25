# Test Report — FIX-076

**Tester:** Tester Agent  
**Date:** 2026-03-25  
**Verdict:** ❌ FAIL — return to Developer  

---

## WP Summary

**Goal:** Fix Reset Agent Blocks button visibility and functionality. Root cause of BUG-119 was dialog height (280px) too small to show rows 4–6. Fix: increase geometry to 480x480 and add `grid_columnconfigure(1, weight=1)`.

---

## Review of Implementation

The implementation is logically correct:

- `SettingsDialog` geometry changed from `"480x280"` → `"480x480"` — correct fix for BUG-119.  
- `grid_columnconfigure(1, weight=1)` added in `_build_ui()` — correct, ensures the workspace entry stretches.  
- `_reset_hook_state()` — correct. Handles missing file, corrupt JSON (replaced with `{}`), and clears all session keys with `deny_count`. Non-session metadata is preserved.  
- `_atomic_write_hook_state()` — correct. Uses `tempfile.mkstemp` + `os.replace` for atomicity; temp file cleaned up on failure.  
- `_on_reset_agent_blocks()` — correct. Input validated (empty workspace → error, non-directory → error, OSError → error). Success → `showinfo`.  
- `_browse_workspace()` — correct. Folder dialog result inserted into entry.  
- No new dependencies.  
- No security vulnerabilities found. `_HOOK_STATE_RELATIVE` is hardcoded; no injection risk.

---

## Test Execution Results

| Run | Scope | Status | Tests |
|-----|-------|--------|-------|
| TST-2220 | FIX-076 targeted (Unit) | **PASS** | 27 passed, 0 failed |
| TST-2219 | Full regression suite | **FAIL** | 74 failed, 6814 passed |

---

## Failures Analysis

### ❌ BLOCKING — GUI-018 regression (FIX-076 caused)

**Test:** `tests/GUI-018/test_gui018_edge_cases.py::TestDialogGeometry::test_dialog_geometry_is_480x280`

```
AssertionError: expected call not found.
Expected: geometry('480x280')
  Actual: geometry('480x480')
```

**Root cause:** The FIX-076 Developer correctly changed the geometry from `480x280` to `480x480` but did **not** update the existing GUI-018 tester edge-case test that hard-codes the old geometry string. This test is now a false regression — it tests the old (broken) layout from before BUG-119 was fixed.

**Filed as:** BUG-130 (Status: Open).

---

### ⚠️ NON-BLOCKING — DOC-010 test design flaw

**Test:** `tests/DOC-010/test_doc010_tester_edge_cases.py::TestSourceCodeUnmodified::test_src_directory_not_modified_by_wp`

This test runs `git diff HEAD~2 HEAD -- src/` and asserts no `src/` files were changed. On the FIX-076 feature branch, `HEAD` is the FIX-076 commit which modified `src/launcher/gui/app.py`, so the assertion fails. This is a **pre-existing test design flaw** (relative HEAD range is fragile across feature branches), not a regression caused by FIX-076. The test was passing on `main` before this branch.

**This failure is pre-existing and unrelated to FIX-076** — the 74-failure count includes 72 other pre-existing failures (CI/CD workflow file tests, etc.) that are also on `main`.

---

## Pre-existing Baseline Failures (not caused by FIX-076)

The following test modules were already failing before FIX-076 (not affected by the GUI dialog change):

- FIX-007, FIX-009, FIX-019, FIX-028, FIX-029, FIX-031, FIX-036, FIX-037, FIX-038, FIX-039 — CI/CD workflow / codesign YAML tests  
- DOC-018 — README agent count  
- INS-015, INS-017, INS-019 — macOS build / shim tests  
- MNT-002 — action tracker count  
- SAF-010, SAF-025 — hook config / hash sync  

Total pre-existing: 72 of 74 failures.

---

## Edge-Case Tests Added by Tester

File: `tests/FIX-076/test_fix076_edge_cases.py` (27 tests total across both FIX-076 test files)

Covers:
- `_reset_hook_state`: session key without `deny_count` preserved; empty dict value preserved; non-dict values preserved; result file is valid JSON after reset.  
- `_atomic_write_hook_state`: temp file cleaned up on `os.replace` failure; written content is valid JSON.  
- `_on_reset_agent_blocks` security: path traversal (`..` segments) — resolves safely; whitespace-only workspace → error; nonexistent subdirectory → error; valid workspace without state file → info/error (no crash).

---

## Security Assessment

- No injection vulnerabilities in workspace path handling (Path() construction used throughout).  
- `_HOOK_STATE_RELATIVE` is hardcoded — user input cannot redirect write target.  
- No credential exposure, no external network calls, no subprocess spawning.  
- Error handling is consistent: all error paths surface to user via `messagebox.showerror`, no silent failures.

---

## Verdict: FAIL ❌

### Blocking Issue — Developer TODO

1. **Update `tests/GUI-018/test_gui018_edge_cases.py`** — In class `TestDialogGeometry`, method `test_dialog_geometry_is_480x280`:
   - Change `dlg._dialog.geometry.assert_called_with("480x280")` → `dlg._dialog.geometry.assert_called_with("480x480")`
   - Also update the method name from `test_dialog_geometry_is_480x280` → `test_dialog_geometry_is_480x480` (and update the docstring accordingly).
   - This test was asserting the old broken geometry; the new 480x480 geometry is the correct value after BUG-119 is fixed.
   - **Reference:** BUG-130 tracks this exact issue.

2. Re-run the full test suite after fixing the test. Confirm 0 FIX-076-related failures before re-submitting.

After the fix, re-set WP status to `Review` and re-submit.
