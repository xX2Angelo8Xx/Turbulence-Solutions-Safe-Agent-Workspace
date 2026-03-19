# Test Report — FIX-050

**Tester:** Tester Agent
**Date:** 2026-03-19
**Iteration:** 1

---

## Summary

FIX-050 correctly fixes the two root causes of BUG-081: `ts-python.cmd` now uses
`setlocal EnableDelayedExpansion` and `!PYTHON_PATH!` syntax, and `verify_ts_python()`
bypasses `cmd.exe` entirely by reading `python-path.txt` directly.  All 31 FIX-050 unit
and edge-case tests pass.

However, **FIX-050 introduced two new regressions** not acknowledged in the dev-log:

1. **INS-019 regression** — `test_windows_shim_python_path_is_quoted` was passing
   before FIX-050. It checks for `"%PYTHON_PATH%"` in `ts-python.cmd`; the rewrite
   replaced that with `"!PYTHON_PATH!"`, breaking the test assertion.

2. **SAF-034 additional regressions** — BUG-078 documented 6 SAF-034 failures
   (introduced by FIX-048). FIX-050's new `read_python_path()` first step in
   `verify_ts_python()` causes ~13 additional SAF-034 tests to fail with "Python path
   configuration not found." because those tests mock `shutil.which` and
   `subprocess.run` but do **not** mock `read_python_path()`. Total SAF-034 failures
   jumped from 6 (pre-FIX-050) to 19 (post-FIX-050).

**Verdict: FAIL — returned to Developer.**

---

## Tests Executed

| Test ID | Test Name | Type | Result | Notes |
|---------|-----------|------|--------|-------|
| TST-1870 | FIX-050 Tester: developer test suite rerun (17 tests) | Unit | Pass | 17/17 pass; all developer assertions confirmed |
| TST-1871 | FIX-050 Tester: edge-case tests (14 tests) | Unit | Pass | 14/14 pass; added `test_fix050_edge.py` |
| TST-1872 | FIX-050 Tester: INS-019 regression check | Regression | Fail | `test_windows_shim_python_path_is_quoted` fails — checks `"%PYTHON_PATH%"` but shim now uses `"!PYTHON_PATH!"` |
| TST-1873 | FIX-050 Tester: full suite regression scan | Regression | Fail | 19 SAF-034 failures (13 new vs BUG-078 baseline of 6); 1 new INS-019 failure; all others pre-existing |

---

## Detailed Failure Analysis

### Failure 1 — INS-019 New Regression

**File:** `tests/INS-019/test_ins019_edge_cases.py::test_windows_shim_python_path_is_quoted`

**Root cause:** The test asserts `'"%PYTHON_PATH%"' in text`.  FIX-050 rewrote
`ts-python.cmd` to use `!PYTHON_PATH!` (delayed expansion) instead of `%PYTHON_PATH%`.
The final invocation line is now `"!PYTHON_PATH!" %*`, which correctly double-quotes the
path but uses the new syntax.

**Status before FIX-050:** PASSING  
**Status after FIX-050:** FAILING  
**BUG logged:** BUG-082

**Fix required:** Update `tests/INS-019/test_ins019_edge_cases.py` line ~95 to check for
`'"!PYTHON_PATH!"'` instead of (or in addition to) `'"%PYTHON_PATH%"'`.

---

### Failure 2 — SAF-034 Additional Regressions (13 new failures)

**Files:** `tests/SAF-034/test_saf034.py`, `tests/SAF-034/test_saf034_edge.py`

**Root cause:** FIX-050's new `verify_ts_python()` calls `read_python_path()` as its
**first step**. If `read_python_path()` returns `None` (no mock provided), the function
immediately returns `(False, "Python path configuration not found.")` —
before ever reaching the shim lookup or subprocess call.

SAF-034 tests were written for the **old shim-first** interface: they mock
`shutil.which` and `subprocess.run` but do **not** mock `read_python_path()`.
With the new implementation, `subprocess.run` is never called in these tests,
so they get wrong results.

**Newly failing tests (13):**
- `test_verify_ts_python_success_unix`
- `test_verify_ts_python_nonzero_exit`
- `test_verify_ts_python_timeout`
- `test_verify_ts_python_os_error`
- `test_verify_ts_python_unix_uses_which`
- `test_verify_ts_python_never_uses_shell_true`
- `test_verify_ts_python_uses_list_args`
- `test_verify_ts_python_timeout_message_mentions_30_seconds`
- `test_verify_ts_python_macos_uses_which`
- `test_verify_ts_python_passes_timeout_30_to_subprocess`
- `test_verify_ts_python_empty_stdout_on_success`
- `test_verify_ts_python_subprocess_args_are_static`
- `test_verify_ts_python_nonzero_exit_empty_stderr`
- `test_verify_ts_python_macos_full_success`
- `test_verify_ts_python_windows_returns_stripped_version`

**Pre-existing failures (still failing, BUG-078):**
- `test_verify_ts_python_windows_uses_shim_dir_when_exists`
- `test_verify_ts_python_windows_fallback_to_path`
- `test_verify_ts_python_windows_shim_dir_takes_precedence`
- `test_verify_ts_python_shim_path_with_spaces`

**Status before FIX-050:** 6 failing (BUG-078)  
**Status after FIX-050:** 19 failing (6 pre-existing + 13 new)  
**BUG logged:** BUG-083

**Fix required:** Add `patch.object(sc, "read_python_path", return_value=fake_python)`
to the mock context in each newly-failing test. Each test needs a `fake_python`
`tmp_path`-based fixture with the file created. Additionally, since the new
implementation calls `python_path.exists()`, `fake_python` must be created (not just
referenced).

---

## Bugs Found

- **BUG-082**: FIX-050 broke `tests/INS-019/test_ins019_edge_cases.py::test_windows_shim_python_path_is_quoted` — test asserts `"%PYTHON_PATH%"` which FIX-050 correctly replaced with `"!PYTHON_PATH!"` (logged in docs/bugs/bugs.csv)
- **BUG-083**: FIX-050 introduced 13+ new SAF-034 failures beyond BUG-078 baseline — new `read_python_path()` first step not mocked in SAF-034 tests (logged in docs/bugs/bugs.csv)

---

## Code Quality Assessment

The actual code changes in FIX-050 are **correct and well-implemented**:

- `ts-python.cmd`: Proper `setlocal EnableDelayedExpansion`, `!VAR!` in all `if ( )`
  blocks, quoted CONFIG assignment, empty-path guard, quoted final invocation.
- `verify_ts_python()`: Clean bypass of `cmd.exe`, direct Python invocation,
  `stdin=DEVNULL`, `timeout=30`, proper error handling for all exception types.
- Version bump: All 5 locations updated correctly to 3.0.2.

The failure is in **test maintenance** — two existing test suites (INS-019 and SAF-034)
were not updated to reflect the new interface/syntax, causing regressions.

---

## TODOs for Developer

- [ ] **Fix INS-019 test**: In `tests/INS-019/test_ins019_edge_cases.py`, update
  `test_windows_shim_python_path_is_quoted` (approx. line 95) to assert
  `'"!PYTHON_PATH!"' in text` instead of `'"%PYTHON_PATH%"' in text`. The underlying
  requirement (Python path is double-quoted in the shim) is still correctly met.

- [ ] **Fix SAF-034 newly-failing tests**: Update the 13 newly-failing tests in
  `tests/SAF-034/test_saf034.py` and `tests/SAF-034/test_saf034_edge.py` to mock
  `read_python_path()` with a valid path. For each test, add:
  ```python
  fake_python = tmp_path / "python"  # or python.exe on Windows
  fake_python.write_text("fake")
  # …
  with patch.object(sc, "read_python_path", return_value=fake_python), \
       …existing mocks…:
  ```
  The `fake_python` file must **exist** (create it with `.write_text("fake")`) because
  `verify_ts_python()` now calls `python_path.exists()` before proceeding.

- [ ] **Acknowledge in dev-log**: The updated dev-log should state which SAF-034 tests
  were pre-existing failures (BUG-078) and which were stale tests that needed updating.

- [ ] After fixing: run `python -m pytest tests/INS-019/ tests/SAF-034/ tests/FIX-050/ -v`
  to confirm all three suites pass before re-setting to Review.

---

## Verdict

**FAIL — return to Developer.**

FIX-050 status set back to `In Progress`. Developer must apply the fixes listed above,
then re-run the full test suite and re-submit for Tester review.
