# Test Report — FIX-124

**Tester:** Tester Agent  
**Date:** 2026-04-07  
**Iteration:** 1  
**Verdict:** FAIL

---

## Summary

FIX-124 correctly fixes all 26 CI test regressions introduced by FIX-121, FIX-122, FIX-123, and DOC-064. The targeted test suites all pass (331/331 targeted tests). However, the FIX-070 version assertion update introduced one new regression in `tests/FIX-104/` that was not accounted for. The WP cannot be approved until this one failure is resolved.

---

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| TST-2742: Full suite via `scripts/run_tests.py` | Regression | Fail | 9148 passed, 249 failed, 91 errors — failures are pre-existing baseline entries except 1 new FIX-104 regression |
| TST-2743: Targeted suites (GUI-007, GUI-014, GUI-015, GUI-023, DOC-035, FIX-070, FIX-052, FIX-122, DOC-064) | Regression | Pass | 331 passed, 1 skipped |
| TST-2744: FIX-104 cross-test regression check | Regression | Fail | `test_fix070_updated_version_assertion` fails — BUG-213 |
| MANIFEST --check (agent-workbench) | Integration | Pass | `generate_manifest.py --check` exits 0 |
| MANIFEST --check (clean-workspace) | Integration | Pass | `generate_manifest.py --check --template clean-workspace` exits 0 |
| `validate_workspace.py --wp FIX-124` | Integration | Pass | Exits 0 after removing temp file |

---

## Findings

### BLOCKING: New Regression in FIX-104 (BUG-213)

**Test:** `tests/FIX-104/test_fix104_version_assertions.py::test_fix070_updated_version_assertion`  
**Status on main:** PASS  
**Status on FIX-124 branch:** FAIL  
**Not in regression baseline.**

**Root cause:** FIX-124 (Category 4) correctly renamed `test_current_version_is_3_3_11` → `test_current_version_is_3_4_0` and changed the version assertion from `"3.3.11"` to `"3.4.0"` in `tests/FIX-070/test_fix070_version_bump.py`. However, `tests/FIX-104/test_fix104_version_assertions.py` contains a guard test that checks that "3.3.11" explicitly appears in the FIX-070 test file:

```python
def test_fix070_updated_version_assertion() -> None:
    """FIX-070 must assert CURRENT_VERSION == '3.3.11', not '3.2.3'."""
    ...
    assert "3.3.11" in content, "FIX-070 doesn't reference 3.3.11"
```

After FIX-124 removed all "3.3.11" occurrences from the FIX-070 file, this assertion fails.

### Pre-existing (not blocking)

**Tests:** `tests/GUI-035/test_gui035_edge_cases.py::TestNoTemplatePollution::test_no_pycache_directories` and `::test_no_pyc_files`  
Both fail due to a `__pycache__` directory in `templates/clean-workspace/.github/hooks/scripts/` created by local test runs. These failures exist on `main` as well (confirmed by checkout comparison) and are gitignored artifacts. Not caused by FIX-124 and not in the regression baseline.

---

## Positive Findings

- All 23 GUI threading failures (GUI-007, GUI-014, GUI-015) now pass. The `_JoiningThread` conftest approach is sound — it uses a real thread (required for pipe reading in `_on_create_project`) but joins before `start()` returns, making it behave synchronously from the test's perspective.
- The `app._window.after = lambda ms, fn: fn()` synchronous dispatch in `_make_app()` helpers is correct.
- DOC-035 AGENT-RULES path fix is correct: `Project/AGENT-RULES.md` (no `AgentDocs/` subdirectory).
- GUI-023 template count 2→3 is correct and matches the current template directory count.
- FIX-052 fragile count replaced with `result.returncode == 0` — robust change.
- MANIFEST files are up to date for both templates.
- Regression baseline updated: the 26 previously-failing entries have been removed.

---

## Security / Edge Case Analysis

- **Conftest scope isolation:** The three new `_sync_thread` autouse fixtures are correctly scoped to their respective `tests/GUI-007/`, `tests/GUI-014/`, `tests/GUI-015/` directories. No leak into neighboring test suites was detected.
- **Real thread usage:** `_JoiningThread` starts a real thread (not a stub) — this is appropriate since `_on_create_project` reads from `subprocess.Popen` pipes inside the thread. A pure stub would silently skip error-path code.
- **Thread join before return:** `start()` calls `join()` synchronously. There is no race between the thread's `_window.after()` callback scheduling and the test assertions. This is safe.
- **No infinite recursion risk:** `_REAL_THREAD` is captured before the patch is active, preventing recursive `_JoiningThread` instantiation.

---

## Required TODOs for Developer (Iteration 2)

### TODO-1 (BLOCKING): Update `tests/FIX-104/test_fix104_version_assertions.py`

**File:** `tests/FIX-104/test_fix104_version_assertions.py`  
**Function:** `test_fix070_updated_version_assertion`

Update the assertion so it checks for the updated version reference rather than the stale "3.3.11". Recommended fix — replace the second assertion:

```python
# BEFORE (now fails because "3.3.11" was removed by FIX-124):
assert "3.3.11" in content, "FIX-070 doesn't reference 3.3.11"

# AFTER (checks for current version; also update the docstring):
assert "3.4.0" in content, "FIX-070 doesn't reference 3.4.0"
```

Also update the docstring from:
```python
"""FIX-070 must assert CURRENT_VERSION == '3.3.11', not '3.2.3'."""
```
to:
```python
"""FIX-070 must assert CURRENT_VERSION == '3.4.0', not '3.2.3'."""
```

After this change, run `pytest tests/FIX-104/ -v` to confirm all FIX-104 tests pass.

### Optional (not blocking): Add FIX-104's test to the baseline or make it version-agnostic

If you prefer to make the guard future-proof (so it survives the next version bump without a FIX-104 edit), consider changing the assertion to verify the test function name rather than the version string:

```python
assert "test_current_version_is_3_4_0" in content, "FIX-070 test name not updated"
```

This way, any future version bump will cause this guard to alert the developer automatically.

---

## Verdict: FAIL

**WP status set to:** `In Progress`

One new regression was introduced by FIX-124 that is not in the regression baseline:
- `tests/FIX-104/test_fix104_version_assertions.py::test_fix070_updated_version_assertion`

Fix TODO-1 above, re-run `pytest tests/FIX-104/ tests/FIX-124/`, confirm pass, re-handoff.
