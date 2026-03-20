# Test Report — FIX-053: Fix INS-011 os._exit killing pytest process

**Tester:** Tester Agent  
**Date:** 2026-03-20  
**Verdict (Iteration 1):** FAIL — return to Developer (see below)  
**Verdict (Iteration 2):** ✅ PASS

---

## Summary

The developer's fix correctly patches `os._exit` in
`tests/INS-011/test_ins011_applier.py::TestNoShellTrue.test_windows_subprocess_no_shell_true`.
All 40 tests in `test_ins011_applier.py` pass.

However, **two additional tests** in `tests/INS-011/test_ins011_tester_edge_cases.py`
call `_apply_windows()` with the **same missing mock** that FIX-053 targeted. These
tests were written by a previous tester for INS-011 and contain an identical
defect. The developer was not exhaustive in scanning all call sites.

When the full `tests/INS-011/` suite is run, pytest is **killed** at test 47/66
by the real `os._exit(0)` call. Tests 47–66 never execute. The WP acceptance
criterion — "Full test suite runs to completion past INS-011 tests" — is **not
met**.

---

## Acceptance Criteria Evaluation

| Criterion | Result |
|-----------|--------|
| Full test suite runs to completion past INS-011 | ❌ FAIL — pytest killed at 47/66 |
| pytest process not killed by os._exit(0) | ❌ FAIL — killed at TestPathEdgeCases |
| 66/66 INS-011 tests pass | ❌ FAIL — 46 pass, process killed |

---

## Evidence

### Run 1 — test_ins011_applier.py only (PASS)
```
.venv\Scripts\python -m pytest tests/INS-011/test_ins011_applier.py -v
40 passed in 0.52s
```

### Run 2 — Full INS-011 suite (FAIL — process killed)
```
.venv\Scripts\python -m pytest tests/INS-011/ -v
...
tests/INS-011/test_ins011_tester_edge_cases.py::TestPathEdgeCases::test_windows_path_with_spaces
<pytest process killed — no output>
```
Pytest exits at test 47/66. The prompt returns immediately with no failure/error
output — signature of `os._exit(0)` bypassing Python's exception machinery.

### Root Cause

Both `test_windows_path_with_spaces` (line 109) and `test_windows_path_with_unicode`
(line 131) in `test_ins011_tester_edge_cases.py` use:

```python
with patch("launcher.core.applier.subprocess.Popen", side_effect=fake_popen), \
     patch("launcher.core.applier.sys.exit"):        # ← sys.exit only
    _apply_windows(installer)
```

`_apply_windows()` calls `os._exit(0)`, not `sys.exit(0)`. Without
`patch("launcher.core.applier.os._exit")`, the real `os._exit` fires.

---

## Tests Logged

| TST ID | Name | Status |
|--------|------|--------|
| TST-1942 | FIX-053 Tester: INS-011 developer file only (40 tests) | Pass |
| TST-1943 | FIX-053 Tester: full INS-011 suite (66 tests) | Fail |
| TST-1944 | FIX-053 Tester: FIX-053 edge-case tests (5 tests) | Pass |

---

## Edge Cases Added

Created `tests/FIX-053/test_fix053_os_exit_mock.py` with 5 tests:

1. `TestOsExitCalledWithZero.test_apply_windows_calls_os_exit_with_0` — verifies
   `os._exit(0)` called exactly once.
2. `TestOsExitCalledWithZero.test_apply_windows_does_not_call_sys_exit` — verifies
   `sys.exit` is NOT called.
3. `TestOsExitCalledWithZero.test_apply_windows_os_exit_called_after_popen` — verifies
   call ordering: `subprocess.Popen` before `os._exit`.
4. `TestOsExitCalledWithZero.test_pytest_survives_mocked_os_exit` — survival test:
   if `os._exit` is not mocked, this test kills pytest (direct regression guard for
   BUG-080).
5. `TestOsExitMockCoverage.test_no_shell_true_test_has_os_exit_patched` — source scan
   regression guard: confirms FIX-053's patch is still present in the target method.

All 5 pass.

---

## Bugs Logged

| Bug ID | Title | Severity |
|--------|-------|----------|
| BUG-087 | FIX-053 incomplete: two tests in test_ins011_tester_edge_cases.py missing os._exit mock | High |

---

## Developer TODOs (Iteration 2)

The following changes **must** be made to `tests/INS-011/test_ins011_tester_edge_cases.py`
before this WP can be re-submitted:

### Fix 1 — `TestPathEdgeCases.test_windows_path_with_spaces` (line 121–123)

Before:
```python
with patch("launcher.core.applier.subprocess.Popen", side_effect=fake_popen), \
     patch("launcher.core.applier.sys.exit"):
    _apply_windows(installer)
```

After:
```python
with patch("launcher.core.applier.subprocess.Popen", side_effect=fake_popen), \
     patch("launcher.core.applier.os._exit"), \
     patch("launcher.core.applier.sys.exit"):
    _apply_windows(installer)
```

### Fix 2 — `TestPathEdgeCases.test_windows_path_with_unicode` (line 143–145)

Same pattern — add `patch("launcher.core.applier.os._exit")` between the Popen mock
and the sys.exit mock.

### Verification

After applying both fixes, the developer must run:
```
.venv\Scripts\python -m pytest tests/INS-011/ -v
```
Expected output: **66 passed** (no process kill, no truncated output).

Also run:
```
.venv\Scripts\python scripts/validate_workspace.py --wp FIX-053
```
Must exit with code 0.

---

## Iteration 2 Results (2026-03-20)

### Developer Fix Applied
Both `patch("launcher.core.applier.os._exit")` entries added to:
- `TestPathEdgeCases.test_windows_path_with_spaces`
- `TestPathEdgeCases.test_windows_path_with_unicode`

in `tests/INS-011/test_ins011_tester_edge_cases.py`.

### Test Runs

#### Run 1 — INS-011 full suite (PASS)
```
.venv\Scripts\python -m pytest tests/INS-011/ -v
66 passed in 0.90s
```
All 66 tests pass. pytest process survives to completion. No process kill.

#### Run 2 — Full suite regression check (PASS — no new regressions)
```
.venv\Scripts\python -m pytest tests/ --tb=short -q  (excl. 8 yaml-broken folders)
4080 passed, 86 failed (pre-existing), 3 skipped in 41.29s
```
86 failures are pre-existing (INS-019, SAF-010, SAF-022, SAF-025). Zero failures in INS-011.
No regressions introduced by FIX-053.

### Acceptance Criteria — Final Evaluation

| Criterion | Result |
|-----------|--------|
| Full test suite runs to completion past INS-011 | ✅ PASS |
| pytest process not killed by os._exit(0) | ✅ PASS |
| 66/66 INS-011 tests pass | ✅ PASS |
| No regressions in broader suite | ✅ PASS |

### Tests Logged (Iteration 2)

| TST ID | Name | Status |
|--------|------|--------|
| TST-1946 | INS-011 full suite (66 tests) | Pass |
| TST-1947 | Full suite regression check (excl. yaml-broken folders) | Pass |

### Verdict: ✅ PASS
WP FIX-053 is approved. BUG-080 and BUG-087 closed. Status → Done.
