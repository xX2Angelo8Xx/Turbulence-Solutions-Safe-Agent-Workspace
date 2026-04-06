# Test Report — GUI-034

**Tester:** Tester Agent  
**Date:** 2026-04-06  
**Iteration:** 1

---

## Summary

GUI-034 WP-specific tests (24) all pass. However, the change to `_on_create_project`
(moving creation to a background thread with `_window.after()` for UI callbacks) breaks
14 pre-existing tests in GUI-005, GUI-006, and GUI-012 that were written for the
synchronous API. These failures are **not** in the regression baseline and are therefore
genuine new regressions introduced by this WP.

Per `testing-protocol.md` rule: "Any code change that alters externally-asserted behavior
MUST update all affected test assertions in the same commit or PR."

**Verdict: FAIL — return to Developer.**

---

## Tests Executed

| Test Suite | Type | Result | Notes |
|-----------|------|--------|-------|
| `tests/GUI-034/` (24 tests) | Unit | PASS | All 24 WP-specific tests pass |
| `tests/FIX-072/` (17 tests) | Unit | PASS | No regression from make_browse_row removal |
| Full regression suite | Regression | FAIL | 274 failures total; pre-existing failures match baseline; 14 new failures (below) |

### New regressions (not in regression-baseline.json)

| Test | File | Failure Reason |
|------|------|----------------|
| `TestOnCreateProjectSuccess::test_success_shows_info_dialog` | `tests/GUI-005/test_gui005_project_creation.py` | `showinfo` never called — it's now in `_on_creation_complete` which runs via `_window.after()` and is never invoked during the test |
| `TestOnCreateProjectSuccess::test_success_info_dialog_mentions_project_name` | `tests/GUI-005/test_gui005_project_creation.py` | Same as above |
| `TestOnCreateProjectCreationError::test_create_project_exception_shows_error_dialog` | `tests/GUI-005/test_gui005_project_creation.py` | `showerror` never called — same threading issue |
| `TestOnCreateProjectCreationError::test_create_project_exception_message_passed_to_dialog` | `tests/GUI-005/test_gui005_project_creation.py` | Same as above |
| `TestOnCreateProjectCreationError::test_create_project_oserror_shows_error_dialog` | `tests/GUI-005/test_gui005_project_creation.py` | Same as above |
| `TestOnCreateProjectHandlerEdgeCases::test_generic_runtime_error_shows_error_dialog` | `tests/GUI-005/test_gui005_project_creation.py` | Same as above |
| `TestOnCreateProjectHandlerEdgeCases::test_success_info_dialog_includes_created_path` | `tests/GUI-005/test_gui005_project_creation.py` | Same as above |
| `TestOnCreateProjectHandlerEdgeCases::test_create_project_exception_does_not_show_success` | `tests/GUI-005/test_gui005_project_creation.py` | Same as above |
| `TestVSCodeCallOrdering::test_success_message_shown_before_vscode_opened` | `tests/GUI-006/test_gui006_tester_edge_cases.py` | Callback never fires via `_window.after()` mock |
| `TestOpenInVSCodeCalledExactlyOnce::test_called_exactly_once_on_success` | `tests/GUI-006/test_gui006_tester_edge_cases.py` | Same as above |
| `TestSuccessMessageWithCheckboxUnchecked::test_success_info_shown_even_when_checkbox_unchecked` | `tests/GUI-006/test_gui006_tester_edge_cases.py` | Same as above |
| `TestOpenInVSCodeCalledOnSuccess::test_open_in_vscode_called_when_checked` | `tests/GUI-006/test_gui006_vscode_auto_open.py` | `open_in_vscode` never called — same threading issue |
| `TestOpenInVSCodeCalledOnSuccess::test_open_in_vscode_called_with_correct_path` | `tests/GUI-006/test_gui006_vscode_auto_open.py` | Same as above |
| `TestWindowHeight::test_window_height_is_440` | `tests/GUI-012/test_gui012_spacing.py` | Asserts `"630" in geometry_call` but height is now 660 |

---

## Root Cause Analysis

### Issue 1 — Synchronous test assumptions broken by threading (GUI-005, GUI-006)

`_on_create_project()` previously called `create_project()` and `messagebox` / `open_in_vscode`
**synchronously** on the main thread. GUI-034 moved `create_project()` to a daemon thread and
moved all post-creation UI calls (`showinfo`, `showerror`, `open_in_vscode`) into
`_on_creation_complete()`, which is scheduled via `self._window.after(0, callback)`.

In tests, `self._window` is a `MagicMock`. Calling `.after(0, callback)` on a MagicMock simply
records the call — **it never executes the callback**. So `_on_creation_complete` is never called,
and none of the post-creation assertions (messagebox, VS Code) can ever be satisfied.

The Developer must update the affected GUI-005 and GUI-006 tests to match the new async API.

**Recommended fix:** In the tests that assert post-completion behavior, patch `threading.Thread`
so its target runs synchronously, AND patch `_window.after` to invoke the callback immediately.
For example:

```python
def _sync_after(delay, callback):
    callback()

app._window.after = _sync_after

with patch("launcher.gui.app.threading.Thread") as mock_thread:
    def immediate_start(target, **kwargs): target()
    mock_thread.return_value.start.side_effect = lambda: create_thread_target()
    ...
```

Or more simply, test `_on_creation_complete` directly (it's a public-enough method):
```python
app._on_creation_complete(success=True, error_msg="", created_path=..., ...)
```
and separately test that `_on_create_project` starts a thread (already covered in GUI-034 tests).

### Issue 2 — Window height assertion stale (GUI-012)

`tests/GUI-012/test_gui012_spacing.py::TestWindowHeight::test_window_height_is_440` contains:
```python
assert "630" in geometry_call
```
The height was intentionally increased from 630 → 660 by GUI-034. This string check is now stale
and must be updated to `"660"`.

---

## Bugs Found

None. These are test maintenance failures caused by the Developer not updating existing tests
alongside the behavioral change, as required by `testing-protocol.md`.

---

## TODOs for Developer

- [ ] **Update `tests/GUI-012/test_gui012_spacing.py`** — change `assert "630" in geometry_call` to `assert "660" in geometry_call` in `test_window_height_is_440`.

- [ ] **Update `tests/GUI-005/test_gui005_project_creation.py`** — the following 8 tests (in
  `TestOnCreateProjectSuccess`, `TestOnCreateProjectCreationError`, `TestOnCreateProjectHandlerEdgeCases`)
  assert that `messagebox.showinfo` / `messagebox.showerror` is called after `_on_create_project()`.
  Since these calls are now asynchronous (via `_window.after()` in a thread callback), the tests
  must be adapted. See recommendations in Root Cause Analysis above.
  - `test_success_shows_info_dialog`
  - `test_success_info_dialog_mentions_project_name`
  - `test_create_project_exception_shows_error_dialog`
  - `test_create_project_exception_message_passed_to_dialog`
  - `test_create_project_oserror_shows_error_dialog`
  - `test_generic_runtime_error_shows_error_dialog`
  - `test_success_info_dialog_includes_created_path`
  - `test_create_project_exception_does_not_show_success`

- [ ] **Update `tests/GUI-006/test_gui006_tester_edge_cases.py`** — the following 3 tests assert
  VS Code / messagebox calls happen after `_on_create_project()`. Same threading fix needed.
  - `TestVSCodeCallOrdering::test_success_message_shown_before_vscode_opened`
  - `TestOpenInVSCodeCalledExactlyOnce::test_called_exactly_once_on_success`
  - `TestSuccessMessageWithCheckboxUnchecked::test_success_info_shown_even_when_checkbox_unchecked`

- [ ] **Update `tests/GUI-006/test_gui006_vscode_auto_open.py`** — the following 2 tests assert
  `open_in_vscode` is called after `_on_create_project()`. Same threading fix needed.
  - `TestOpenInVSCodeCalledOnSuccess::test_open_in_vscode_called_when_checked`
  - `TestOpenInVSCodeCalledOnSuccess::test_open_in_vscode_called_with_correct_path`

- [ ] After all test fixes: run `scripts/run_tests.py --wp GUI-034 --type Regression --env "Windows 11 + Python 3.11" --full-suite` and confirm 0 new failures beyond the regression baseline.

---

## Verdict

**FAIL — return to Developer.**

The WP implementation is correct, but 14 pre-existing tests in GUI-005, GUI-006, and GUI-012
were broken by the behavioral change and were not updated. Per testing-protocol.md, these must be
fixed in the same commit. Address all TODOs above and re-submit for Tester review.
