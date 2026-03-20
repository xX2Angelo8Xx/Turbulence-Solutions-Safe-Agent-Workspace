# FIX-054 Dev Log — Fix FIX-048 stale tests asserting removed cmd.exe wrapper

**Status:** In Progress → Review  
**Assigned To:** Developer Agent  
**Date:** 2026-03-20  
**Bug:** BUG-084

---

## Problem Statement

FIX-050 removed the cmd.exe /c wrapper from `verify_ts_python()` in
`src/launcher/core/shim_config.py`. The function now reads `python-path.txt` via
`read_python_path()` and directly invokes the Python executable. The FIX-054
assignment stated that 12 tests in `tests/FIX-048/test_fix048.py` were still
asserting the old behavior and failing.

---

## Investigation

Upon starting this WP, all 21 tests in `tests/FIX-048/test_fix048.py` were
already passing (21/21). Investigation via `git log` revealed that the test file
was previously updated (commits `adf50a7` via FIX-049 and `a36c7d8` via FIX-048
tester review). The current tests:

- Mock `read_python_path()` to return a fake Path object (`mock_py.exists.return_value = True`)
- Assert `args_used[1] == "-c"` and `"sys.version" in args_used[2]` (direct Python invocation)
- Assert `timeout=30` (updated from 5)
- Assert "30 seconds" in timeout error messages

All assertions match the current `verify_ts_python()` implementation in `shim_config.py`.

---

## Implementation

No code changes were required. The test file was already correctly updated in
a prior commit. The WP was created after those tests were written (the WP
describes a state that no longer existed on the current branch).

**Files changed:** None (tests already correct)

---

## Tests Written

No new tests needed — the existing 21 tests in `tests/FIX-048/test_fix048.py`
cover all required scenarios and all pass.

Test run results: **21 passed / 0 failed**

---

## Commands Run

```
.venv\Scripts\python -m pytest tests/FIX-048/ -v
```

Result: 21 passed in 0.26s

---

## Known Limitations

None.

---

## Checklist

- [x] All FIX-048 tests pass (21/21)
- [x] dev-log.md created
- [x] No tmp_ files
- [x] validate_workspace.py clean
- [x] Branch: FIX-054/fix-stale-tests
- [x] Committed and pushed
