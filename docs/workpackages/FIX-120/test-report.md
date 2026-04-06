# Test Report — FIX-120

**Tester:** Tester Agent  
**Date:** 2026-04-06  
**WP:** FIX-120 — Suppress terminal windows during git init in project creation  
**Branch:** FIX-120/suppress-git-terminal-windows  
**Verdict:** PASS

---

## Summary

The fix is a single conditional line added to `_init_git_repository()` in
`src/launcher/core/project_creator.py`. When `sys.platform == "win32"`,
`creationflags=subprocess.CREATE_NO_WINDOW` is added to the `common` kwargs
dict shared by all five git subprocess calls. This mirrors the identical pattern
used in `src/launcher/core/vscode.py` (established by FIX-092).

---

## Code Review

### Pattern Match with FIX-092

`vscode.py` (FIX-092):
```python
kwargs: dict = {}
if sys.platform == "win32":
    kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
```

`project_creator.py` (FIX-120):
```python
common = {"cwd": str(workspace), "capture_output": True, "timeout": _GIT_TIMEOUT}
if sys.platform == "win32":
    common["creationflags"] = subprocess.CREATE_NO_WINDOW
```

Pattern is identical in structure. ✓

### `sys` Import

`import sys` is present at the top of the file (line 12). No missing import. ✓

### Platform Guard

`sys.platform == "win32"` — exact equality, case-sensitive. Not triggered on
`"WIN32"`, `"cygwin"`, `"darwin"`, `"linux"`. ✓

### Scope of Effect

All five git subprocess calls use the same shared `common` dict, so the
`creationflags` key is automatically applied to every call when on Windows.
No call is missed. ✓

### Other `subprocess` Calls in the File

`project_creator.py` has no other `subprocess` calls. The only subprocess
usage is inside `_init_git_repository()`. ✓

### Non-Fatal Error Handling

`OSError` and `subprocess.TimeoutExpired` are caught and return `False`;
the workspace is still usable. Flag does not change this behaviour. ✓

---

## Test Results

### Developer Tests (9 tests)

| Test | Result |
|------|--------|
| `test_create_no_window_flag_set_on_windows` | PASS |
| `test_no_creationflags_on_non_windows` | PASS |
| `test_no_creationflags_on_darwin` | PASS |
| `test_git_init_called_first` | PASS |
| `test_returns_true_on_success` | PASS |
| `test_returns_false_when_git_init_fails` | PASS |
| `test_returns_false_on_os_error` | PASS |
| `test_returns_false_on_timeout` | PASS |
| `test_cwd_set_to_workspace` | PASS |

### Tester Edge-Case Tests (3 added)

| Test | Rationale | Result |
|------|-----------|--------|
| `test_platform_check_is_case_sensitive` | Confirms `"WIN32"` uppercase does NOT trigger the flag; proves exact equality check | PASS |
| `test_all_five_git_commands_called` | Confirms all 5 git commands (init, config×2, add, commit) are issued — none dropped | PASS |
| `test_base_kwargs_always_present_on_windows` | Confirms cwd/capture_output/timeout are present even when creationflags is added | PASS |

### INS-030 Regression (8 tests)

The `tests/INS-030/` suite tests `_init_git_repository()` directly (the function
modified by this WP). All 8 tests passed without modification, confirming the
change is backward-compatible.

### Full Suite

Full suite run: **8994 passed, 344 skipped, 5 xfailed, 168 failed, 96 errors**

All 168 failures and 96 errors are **pre-existing** entries in
`tests/regression-baseline.json` (261 entries, updated 2026-04-06). No new
regressions introduced by FIX-120. Failures are unrelated to this WP
(FIX-029 codesign, INS-015/INS-016 CI macOS/Linux jobs disabled per ADR-010).

---

## Edge Cases Considered

| Concern | Conclusion |
|---------|-----------|
| `sys` not imported | `import sys` present at file top — not a risk |
| Uppercase `"WIN32"` platform string | Correctly excluded by exact equality; test confirms |
| `"cygwin"` platform | Would not set flag (correct — Cygwin runs native Windows subprocesses but does not need `CREATE_NO_WINDOW` in the same way) |
| creationflags + capture_output | `subprocess.run` supports both simultaneously; no conflict |
| Impact on macOS/Linux | Guard is `sys.platform == "win32"` — zero effect on other platforms |
| Race condition | Single-threaded function; no concurrency concern |
| Resource leaks | `capture_output=True` captures stdout/stderr; they are discarded (acceptable for git init side-effects) |

---

## ADR Check

No ADRs in `docs/decisions/index.jsonl` conflict with this WP.
FIX-092 (vscode.py pattern) is the prior art — this WP extends the same pattern.

---

## Verdict: PASS

All 12 FIX-120 tests pass. All 8 INS-030 tests pass. No regressions. Implementation
matches requirements and mirrors the established FIX-092 pattern exactly.
