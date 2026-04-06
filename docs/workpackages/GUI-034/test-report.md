# Test Report — GUI-034

**Tester:** Tester Agent  
**Date:** 2026-04-06  
**Iteration:** 2

---

## Summary

Iteration 2 fixes the 14 regressions identified in Iteration 1. The GUI-034 WP-specific tests
(24) and all previously-failing GUI-005, GUI-006, and GUI-012 tests now pass (117 total, 0
failed). However, regression analysis reveals 1 new failure not caught by the Developer:

`tests/SAF-034/test_saf034.py::test_on_create_project_proceeds_when_shim_ok`

This test creates a bare App instance to verify `create_project` is called when `verify_ts_python`
returns `(True, ...)`. It fails with `AttributeError: 'App' object has no attribute 'create_button'`
because GUI-034 added `_set_creation_ui_state(disabled=True)` to `_on_create_project()` before the
background thread is started, but the SAF-034 test does not set up the widget attributes now
required by `_set_creation_ui_state`.

**Verdict: FAIL — return to Developer.**

---

## Tests Executed

| Test Suite | Type | Logged As | Result | Notes |
|-----------|------|-----------|--------|-------|
| `tests/GUI-034/` (24 tests) | Unit | TST-2696 | PASS | All WP-specific tests pass |
| `tests/GUI-034/ + GUI-005 + GUI-006 + GUI-012` (117 tests) | Unit | TST-2698 | PASS | All 14 Iteration 1 regressions now fixed |
| Full regression suite | Regression | TST-2697 | FAIL | 1 new failure in SAF-034 (below) |

### New regression found in Iteration 2 (not in regression-baseline.json)

| Test | File | Failure |
|------|------|---------|
| `test_on_create_project_proceeds_when_shim_ok` | `tests/SAF-034/test_saf034.py` | `AttributeError: 'App' object has no attribute 'create_button'` at `_set_creation_ui_state` |

---

## Root Cause Analysis

`_on_create_project()` now calls `self._set_creation_ui_state(disabled=True)` immediately after
all validations pass, before launching the background thread. `_set_creation_ui_state` accesses:

- `self.create_button`
- `self.browse_button`
- `self.project_name_entry`
- `self.destination_entry`
- `self.project_type_dropdown`
- `self.create_progress_bar`

Additionally, the background thread calls `self._window.after(0, callback)` — which requires a
`_window` mock with an `.after` side-effect if the test wants to observe post-creation behavior.

The SAF-034 test `test_on_create_project_proceeds_when_shim_ok` creates a bare App instance via
`object.__new__` and sets up only the attributes that existed before GUI-034. The three newly
required attributes (`create_button`, `browse_button`, `create_progress_bar`) and a `_window`
mock with `.after` side-effects were never added.

---

## Bugs Found

- BUG-204: GUI-034: SAF-034 test_on_create_project_proceeds_when_shim_ok fails — missing widget
  attrs after threading refactor (logged in `docs/bugs/bugs.jsonl`)

---

## TODOs for Developer

### Mandatory fix: update `tests/SAF-034/test_saf034.py`

In `test_on_create_project_proceeds_when_shim_ok`, add the missing attributes to the `instance`
setup block (after the existing `include_readmes_var` lines):

```python
# GUI-034: _on_create_project calls _set_creation_ui_state which needs these.
instance.create_button = MagicMock()
instance.browse_button = MagicMock()
instance.create_progress_bar = MagicMock()
instance._window = MagicMock()
instance._window.after.side_effect = lambda ms, cb: cb()
```

And add `patch("launcher.gui.app.threading.Thread", _SyncThread)` to the `with patch(...)` block
so the background thread fires synchronously and `create_project` is actually called during the
test. The `_SyncThread` class is already defined in `tests/GUI-005/test_gui005_project_creation.py`
and `tests/GUI-006/` — replicate the same pattern here.

Full corrected `with patch(...)` context:

```python
with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
     patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
     patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
     patch("launcher.gui.app.list_templates", return_value=["agent-workbench"]), \
     patch("launcher.gui.app._format_template_name", return_value="Coding"), \
     patch("launcher.gui.app.verify_ts_python", return_value=(True, "3.11.0")), \
     patch("launcher.gui.app.threading.Thread", _SyncThread), \
     patch("launcher.gui.app.create_project", return_value=fake_project) as mock_cp, \
     patch("launcher.gui.app.messagebox"):
    app_module.App._on_create_project(instance)

mock_cp.assert_called_once()
```

- [ ] **Add missing widget mocks** (`create_button`, `browse_button`, `create_progress_bar`,
  `_window` with `after` side-effect) to `test_on_create_project_proceeds_when_shim_ok` in
  `tests/SAF-034/test_saf034.py`.
- [ ] **Add** `patch("launcher.gui.app.threading.Thread", _SyncThread)` to the same test's
  `with patch(...)` block so the background thread runs synchronously and `create_project` is called.
- [ ] **Add** a `_SyncThread` class (or import equivalent) at the top of `tests/SAF-034/test_saf034.py`.
- [ ] Re-run `scripts/run_tests.py --wp GUI-034 --type Regression --env "Windows 11 + Python 3.11" --full-suite`
  and confirm 0 new failures beyond the established regression baseline.

---

## Verdict

**FAIL — return to Developer (Iteration 3).**

The 14 Iteration-1 regressions are all fixed. However, 1 new regression in `tests/SAF-034/` was
introduced by the same threading change and was not caught before handoff. The SAF-034 test
`test_on_create_project_proceeds_when_shim_ok` raises `AttributeError` because the bare instance
setup does not include the three new widget attributes now required by `_set_creation_ui_state`.

Fix per the TODO above, confirm the test passes, re-run the full regression suite, and
re-submit for Tester review.
