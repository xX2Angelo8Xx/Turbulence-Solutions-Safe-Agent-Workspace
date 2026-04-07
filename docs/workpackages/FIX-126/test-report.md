# Test Report — FIX-126: Harden Python runtime path persistence

**Verdict: FAIL**
**Date:** 2026-04-07
**Tester:** Tester Agent
**Environment:** Windows 11 / Python 3.11.9

---

## Scope Tested

| WP Requirement | Tested |
|---|---|
| ts-python.cmd self-healing fallback (ProgramFiles + LOCALAPPDATA\Programs) | ✅ |
| ts-python.cmd auto-heal writes path back to python-path.txt | ✅ |
| verify_ts_python() CREATE_NO_WINDOW on Windows | ✅ |
| verify_ts_python() no creationflags on Linux/macOS | ✅ |
| ensure_python_path_valid() called before verify_ts_python() in _create() | ✅ |
| FIX-126 unit tests (12 tests in tests/FIX-126/) | ✅ All pass |

---

## Code Review

### src/installer/shims/ts-python.cmd

Implementation is correct and follows the WP requirements. The fallback candidates
(`%ProgramFiles%\TurbulenceSolutions\python-embed\python.exe` and
`%LOCALAPPDATA%\Programs\TurbulenceSolutions\python-embed\python.exe`) are checked in
priority order. Auto-heal writes the found path back via `echo !PYTHON_PATH!>`.

**Issue found:** The developer restructured the empty-python-path guard from
the original negative form (`if not defined PYTHON_PATH`) to a positive form
(`if defined PYTHON_PATH (if exist "!PYTHON_PATH!" goto :run_python)`). Both forms
are functionally equivalent (both prevent execution when the path is undefined or
empty). However, the pre-existing FIX-050 test `test_cmd_has_not_defined_check`
explicitly requires the literal string `if not defined PYTHON_PATH`. This test
was passing on main and is now failing.

Security analysis of the fallback:
- Both fallback paths are under `%ProgramFiles%` and `%LOCALAPPDATA%\Programs` — user-writable  
  paths under `%LOCALAPPDATA%` are a mild concern (a local attacker could plant a fake python-embed/ there),
  but this risk was accepted in the WP requirements and is equivalent to the existing primary-path mechanism.
- Auto-heal writes back using `echo !PATH!>file` — this always adds a trailing CRLF which is
  correctly stripped by `read_python_path()` in shim_config.py.
- Deny is correctly emitted as the last resort with a valid hook JSON payload.

### src/launcher/core/shim_config.py

`verify_ts_python()` now includes:
```python
if sys.platform == "win32":
    extra_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
```
This is correct. The flag is gated behind a platform check, preserving cross-platform
compatibility. The `stdin=subprocess.DEVNULL` is also present for safety.

### src/launcher/gui/app.py

`ensure_python_path_valid()` is called on line 525, before `verify_ts_python()` on line 527,
inside the `_create()` background thread. The call order is correct per WP requirement 3.

**Issue found:** `ensure_python_path_valid()` was added to the `_create()` background thread
but no autouse mock was added to `tests/conftest.py` (unlike `verify_ts_python()` which has
`_mock_verify_ts_python`). This causes `ensure_python_path_valid()` to run for real in the
test environment, adding file-system I/O latency to the thread. The GUI-020 tests
(`TestAppPassesCounterEnabled`, `TestAppPassesCounterThreshold`,
`TestAppThresholdValidation`) assert `mock_create.called` immediately after
`_on_create_project()` starts the daemon thread — a race condition that the added I/O
latency makes consistently fail (8 tests affected).

---

## Test Execution

### FIX-126 dedicated tests
```
tests/FIX-126/test_fix126_python_path_hardening.py — 12/12 PASSED
```

### Full suite (excluding known-baseline DOC-002)
```
9157 passed, 266 failed/errored
```

Comparison against regression baseline (250 known failures):

| Category | Count |
|---|---|
| Failures known in baseline (pre-existing) | ~237 |
| Ordering artifacts (pass in isolation) | ~111 |
| **NEW regressions introduced by FIX-126** | **9** |

### Confirmed new regressions

| Test | Root Cause |
|---|---|
| `tests/FIX-050/test_fix050.py::test_cmd_has_not_defined_check` | FIX-126 changed `if not defined PYTHON_PATH` to `if defined PYTHON_PATH` |
| `tests/GUI-020/test_gui020_app_passes_counter_config.py::TestAppPassesCounterEnabled::test_counter_enabled_true_forwarded` | `ensure_python_path_valid()` thread I/O causes race condition |
| `tests/GUI-020/test_gui020_app_passes_counter_config.py::TestAppPassesCounterEnabled::test_counter_enabled_false_forwarded` | same |
| `tests/GUI-020/test_gui020_app_passes_counter_config.py::TestAppPassesCounterThreshold::test_valid_threshold_forwarded` | same |
| `tests/GUI-020/test_gui020_app_passes_counter_config.py::TestAppPassesCounterThreshold::test_invalid_threshold_falls_back_to_20` | same |
| `tests/GUI-020/test_gui020_app_passes_counter_config.py::TestAppPassesCounterThreshold::test_threshold_custom_value_5_forwarded` | same |
| `tests/GUI-020/test_gui020_app_passes_counter_config.py::TestAppPassesCounterThreshold::test_both_counter_args_present_in_call` | same |
| `tests/GUI-020/test_gui020_tester_edge_cases.py::TestAppThresholdValidation::test_on_create_project_zero_threshold_falls_back_to_20` | same |
| `tests/GUI-020/test_gui020_tester_edge_cases.py::TestAppThresholdValidation::test_on_create_project_negative_threshold_falls_back_to_20` | same |

### Confirmed false positives (pre-existing or contextual)
- `FIX-028 test_no_crlf_line_endings` — build_dmg.sh CRLF pre-dates FIX-126 (confirmed on main)
- `DOC-010 test_src_directory_not_modified_by_wp` — git-relative test (`HEAD~2`) always triggers when src changes in recent commits; not a WP defect
- `GUI-009`, `SAF-073`, `SAF-074`, `INS-012`, `SAF-001` groups — all pass in isolation; test ordering artifacts in the full-suite run

---

## Edge Cases Checked

1. **Empty python-path.txt**: `set "PYTHON_PATH="` + `set /p` on empty file leaves PYTHON_PATH empty; `if defined` guard correctly skips to fallback.
2. **Missing python-path.txt**: `if exist "%CONFIG%"` is false; PYTHON_PATH stays empty; `if defined` guard skips to fallback.
3. **Both fallbacks missing**: Correct deny JSON emitted.
4. **Non-Windows CREATE_NO_WINDOW**: Verified flag is absent on linux and darwin.
5. **Ensure called before verify in startup AND in _create**: Both calls present; startup warning on False return.
6. **Auto-heal CRLF in path write**: `read_python_path()` strips whitespace — confirmed safe.

---

## Verdict: FAIL

Two actionable issues must be resolved before this WP can be approved. The FIX-126
implementation is correct in its core behavior, but it broke pre-existing tests
through restructuring and missing test infrastructure.

---

## Required Fixes (TODOs for Developer)

### TODO-1: Fix ts-python.cmd to satisfy FIX-050 test

The `test_cmd_has_not_defined_check` test in `tests/FIX-050/test_fix050.py` requires
the literal string `if not defined PYTHON_PATH`. The simplest fix is to add an explicit
negative guard that mirrors the original form. Example restructuring:

```batch
rem --- Primary path: read python-path.txt ---
set "PYTHON_PATH="
if exist "%CONFIG%" (
    set /p PYTHON_PATH=<"%CONFIG%"
)
if not defined PYTHON_PATH goto :try_fallbacks
if exist "!PYTHON_PATH!" goto :run_python

:try_fallbacks
rem --- Fallback 1: standard per-machine install location ---
...
```

Alternatively, if the developer believes the FIX-050 test assertion is overly strict
(checking form rather than behavior), they may update the FIX-050 test to check
`if defined PYTHON_PATH` instead — but that change requires a clear comment explaining
the equivalence and WHY the form changed, and the updated test must be added to the
FIX-126 commit.

### TODO-2: Add autouse mock for ensure_python_path_valid in conftest.py

Add a conftest.py autouse fixture analogous to `_mock_verify_ts_python` to prevent
`ensure_python_path_valid()` from running for real in tests:

```python
@pytest.fixture(autouse=True)
def _mock_ensure_python_path_valid():
    """Prevent real filesystem access from ensure_python_path_valid() during tests (FIX-126)."""
    with patch("launcher.gui.app.ensure_python_path_valid", return_value=True):
        yield
```

After this fix, re-run `tests/GUI-020/` in isolation and confirm all 8 failing
tests pass.

### TODO-3: Verify full test suite passes after fixes

After applying TODO-1 and TODO-2, run:
```
.venv\Scripts\python.exe -m pytest tests/FIX-050/ tests/GUI-020/ tests/FIX-126/ -v
```
All tests must pass. Then run `scripts/validate_workspace.py --wp FIX-126`.
