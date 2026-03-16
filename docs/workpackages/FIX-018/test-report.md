# Test Report — FIX-018: Add GitHub Auth for Private Repo API Access

**Tester:** Tester Agent  
**Date:** 2026-03-16  
**Iteration:** 1  
**Verdict:** ❌ FAIL — Return to Developer (In Progress)

---

## Summary

FIX-018 correctly adds GitHub authentication headers to `updater.py` and
`downloader.py`, and the new `github_auth.py` helper covers most failure paths
correctly. However, a correctness bug was found in `get_github_token()`: the
function does not check `subprocess.run` return code before using the stdout
value as a token.

---

## Code Review

### `src/launcher/core/github_auth.py`
- ✅ No hardcoded tokens or credentials  
- ✅ `subprocess.run` uses list args `["gh", "auth", "token"]`, not `shell=True`  
- ✅ Token only forwarded via `Authorization: Bearer` header  
- ✅ Whitespace stripping applied to all three sources  
- ✅ Exceptions caught: `FileNotFoundError`, `TimeoutExpired`, `OSError`  
- ❌ **BUG-047**: `result.returncode` is never checked. If `gh auth token` exits
  with a non-zero code but writes any text to stdout (e.g. an error message),
  that text is returned as the "token" and injected into an Authorization header.

### `src/launcher/core/updater.py`
- ✅ `get_github_token()` imported and called once  
- ✅ `Authorization: Bearer {token}` added only when token is truthy  
- ✅ `Accept` header preserved alongside auth header  
- ✅ 404/401/403 errors silently caught (graceful degradation)  

### `src/launcher/core/downloader.py`
- ✅ Token retrieved once at the top of `download_update()`; shared across all
  three requests  
- ✅ Auth header added to metadata request, asset download, and SHA256 companion  
- ✅ No SSRF vectors introduced — existing `_validate_download_url()` unchanged  
- ✅ Token not logged in any `_LOGGER` calls  

### `tests/INS-001/test_ins001_structure.py`
- ✅ `test_updater_stub_returns_no_update` correctly fixed — now mocks
  `urllib.request.urlopen` instead of making a real network call  

---

## Test Results

### Full Suite Regression (Run 1)
- **Command:** `.venv\Scripts\python -m pytest tests/ --tb=short -q`  
- **Outcome:** 2049 passed, 1 failed (pre-existing), 29 skipped  
- **Pre-existing failure:**
  `tests/INS-005/test_ins005_edge_cases.py::TestShortcutsAndUninstaller::test_uninstall_delete_type_is_filesandirs`
  — test expects `Type: filesandirs` but setup.iss uses `Type: filesandordirs`.
  This failure pre-dates FIX-018 (setup.iss not touched by this WP). **Not a
  regression from FIX-018.**

### Developer Tests — FIX-018 Only (Run 2)
- **Command:** `.venv\Scripts\python -m pytest tests/FIX-018/ -v --tb=short`  
- **Outcome:** 34 passed  
- All three developer test files pass: github_auth (19), updater_auth (7),
  downloader_auth (8+1 compat)

### Tester Edge-Case Tests (Run 3)
- **Command:** `.venv\Scripts\python -m pytest tests/FIX-018/test_fix018_edge_cases.py -v --tb=short`  
- **Outcome:** 11 passed, 2 failed  

| Test | Result | Notes |
|------|--------|-------|
| `test_nonzero_exit_empty_stdout_returns_none` | ✅ PASS | Real-world gh failure path |
| `test_nonzero_exit_whitespace_stdout_returns_none` | ✅ PASS | Whitespace-only stdout on failure |
| `test_nonzero_exit_with_error_text_on_stdout_returns_none` | ❌ FAIL | **BUG-047** |
| `test_nonzero_exit_error_text_not_used_as_auth_header` | ❌ FAIL | **BUG-047** consequence |
| `test_updater_401_returns_no_update_silently` | ✅ PASS | |
| `test_downloader_401_raises_runtime_error` | ✅ PASS | |
| `test_updater_403_forbidden_returns_no_update_silently` | ✅ PASS | |
| `test_token_not_in_downloader_log_records` | ✅ PASS | Token never logged |
| `test_token_not_printed_to_stdout_in_github_auth` | ✅ PASS | Token never printed |
| `test_all_sources_fail_returns_none` | ✅ PASS | |
| `test_permission_error_from_subprocess_returns_none` | ✅ PASS | PermissionError subclass covered |
| `test_env_vars_missing_from_os_environ_entirely` | ✅ PASS | Keys absent from env |
| `test_check_for_update_survives_get_token_exception` | ✅ PASS | Defensive degradation |

---

## Bug Found

### BUG-047 — `get_github_token()` does not validate subprocess return code

**Severity:** Medium (security correctness)  
**File:** `src/launcher/core/github_auth.py`  
**Lines:** 32–41

**Description:**  
The function calls `subprocess.run(["gh", "auth", "token"], ...)` and checks
only `result.stdout.strip()` for truthiness, without checking
`result.returncode`. If `gh auth token` exits with a non-zero code but any
text appears on stdout, that text is returned as the token value and injected
as `Authorization: Bearer <error text>`.

**Observed behavior:**
```
token = get_github_token()
# With: subprocess returncode=1, stdout="error: not logged in to any GitHub hosts..."
# Returns: "error: not logged in to any GitHub hosts..."  (should be None)
```

**Authorization header sent:**
```
Authorization: Bearer error: not logged in to any GitHub hosts. Run gh auth login to authenticate.
```

**Spec violation:** dev-log.md states "Returns None if no auth is available
(graceful fallback)." A non-zero exit code from `gh auth token` IS a failure
state — no auth is available. The contract requires returning None.

**Impact:**  
Low-risk in practice (real `gh auth token` writes errors to stderr, not
stdout), but the function violates its stated contract. A future version of gh
or a misconfigured environment could place error text on stdout, causing bogus
auth headers.

**Fix required:**  
Add `result.returncode == 0` check before treating stdout as a valid token:

```python
if result.returncode == 0:
    token = result.stdout.strip()
    if token:
        return token
```

---

## TODOs for Developer (Iteration 2)

1. **Fix `get_github_token()` returncode check** in
   `src/launcher/core/github_auth.py` (lines ~32–41):
   - After `subprocess.run(...)`, check `result.returncode == 0` before
     treating stdout as a token.
   - The fix is one condition: wrap `token = result.stdout.strip()` inside
     `if result.returncode == 0:`.
   - This ensures any non-zero exit (e.g., gh not authenticated, permission
     error) always falls through to returning `None`.

2. **Verify the two currently-failing edge-case tests now pass:**
   - `test_nonzero_exit_with_error_text_on_stdout_returns_none`
   - `test_nonzero_exit_error_text_not_used_as_auth_header`

3. **No other changes required** — all security controls, header logic,
   fallback behavior, and existing tests are correct.

---

## Pre-Done Checklist

- [x] `docs/workpackages/FIX-018/dev-log.md` exists and is non-empty  
- [x] `docs/workpackages/FIX-018/test-report.md` written by Tester  
- [x] Test files exist in `tests/FIX-018/` (4 files: 3 developer + 1 Tester)  
- [ ] All tests pass — BLOCKED: 2 failures in edge-case tests  
- [x] Test runs logged in `docs/test-results/test-results.csv`  
- [ ] WP must NOT be marked Done — returning to In Progress  
