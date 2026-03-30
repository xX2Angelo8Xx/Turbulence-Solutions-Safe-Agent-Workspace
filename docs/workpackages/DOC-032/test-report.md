# DOC-032 Test Report

**Tester:** Tester Agent  
**Date:** 2026-03-30  
**Verdict:** FAIL  

---

## Summary

DOC-032 correctly removed the stale `| \`memory\` tool | Not available (blocked by design) |` row from `templates/agent-workbench/.github/instructions/copilot-instructions.md`. The change itself is scoped and correct. However, the developer did not update the pre-existing DOC-005 test that asserts the memory tool row's presence, causing a regression in the full test suite.

---

## Review

| Check | Result |
|-------|--------|
| `dev-log.md` exists and is non-empty | PASS |
| Git diff limited to one row removal | PASS |
| Correct row removed (`blocked by design`) | PASS |
| No other file changes | PASS |
| `tests/DOC-032/` test files exist | PASS |
| Known Tool Limitations section intact | PASS |
| Other limitation rows preserved (Out-File, dir, pip install, venv) | PASS |

---

## Test Runs

### DOC-032 suite (isolated)

```
.venv\Scripts\python.exe -m pytest tests/DOC-032/ -v
```

**Result: 8 passed, 0 failed**

All 8 developer tests pass in isolation:
- `test_file_exists` — PASS
- `test_blocked_by_design_not_present` — PASS
- `test_memory_not_in_limitations_table` — PASS
- `test_known_limitations_section_exists` — PASS
- `test_out_file_row_present` — PASS
- `test_dir_ls_row_present` — PASS
- `test_pip_install_row_present` — PASS
- `test_venv_activation_row_present` — PASS

### Full test suite (regression check)

```
.venv\Scripts\python.exe -m pytest tests/ -x --tb=short -q
```

**Result: 1 failed, 110 passed — REGRESSION**

```
FAILED tests\DOC-005\test_doc005_limitations.py::test_table_contains_memory_tool_entry
AssertionError: assert '`memory` tool' in <file contents>
```

---

## Root Cause

The DOC-005 test at `tests/DOC-005/test_doc005_limitations.py` contains:

```python
LIMITATION_ENTRIES = [
    ...
    "memory",
]

def test_table_contains_memory_tool_entry():
    content = _read(DEFAULT_FILE)
    assert "`memory` tool" in content
```

This test was written when the memory tool row existed in the limitations table. DOC-032's goal was to remove that row, but the developer did not update or remove this now-stale DOC-005 test. The result is a test suite regression.

---

## Bug Logged

**BUG-161** — `DOC-032 breaks DOC-005 test: test_table_contains_memory_tool_entry`  
Severity: Medium

---

## TODOs for Developer (return to In Progress)

1. **Update `tests/DOC-005/test_doc005_limitations.py`:**
   - Remove `"memory"` from the `LIMITATION_ENTRIES` list.
   - Remove the `test_table_contains_memory_tool_entry` function entirely (the assertion is now invalid — the memory tool row no longer exists in the file).

2. **Re-run the full test suite** to confirm zero failures:
   ```
   .venv\Scripts\python.exe -m pytest tests/ --tb=short -q
   ```

3. **Run `scripts/validate_workspace.py --wp DOC-032`** and confirm exit code 0.

4. **Stage, commit, and push** the updated test file:
   ```
   git add tests/DOC-005/test_doc005_limitations.py
   git commit -m "DOC-032: remove stale memory tool assertion from DOC-005 tests"
   git push origin DOC-032/copilot-instructions-fix
   ```

5. Set WP back to `Review` and re-hand off to Tester.

---

## Verdict: FAIL

WP returned to **In Progress**. See TODOs above.
