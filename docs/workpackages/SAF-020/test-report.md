# SAF-020 Test Report — Detect and Block Terminal Wildcard Patterns

**Verdict: FAIL**

**Tester:** Tester Agent  
**Date:** 2026-03-16  
**Branch:** `SAF-020/wildcard-blocking`  
**WP Goal:** Terminal wildcard bypass vector is fully closed; no glob pattern can resolve to restricted zones.

---

## Summary

The SAF-020 implementation correctly handles `*` and `?` wildcard patterns via the new `_wildcard_prefix_matches_deny_zone()` helper function. All 69 Developer-written tests pass. However, the Tester's edge-case suite uncovered an active security bypass: **bracket expression wildcards** (`[.g]*`, `[Nn]*`, `[.v]*`) are not detected as deny-zone patterns. This violates the WP goal that "no glob pattern can resolve to restricted zones."

**Result:** 7 Tester edge-case tests FAIL. WP is returned to the Developer for fixing.

---

## Test Run Results

| Run | Suite | Result | Tests |
|-----|-------|--------|-------|
| TST-1392 | SAF-020 Developer suite (69 tests) | PASS | 69 passed |
| TST-1393 | SAF-020 Tester edge-case suite | FAIL | 7 failed / 100 passed (107 total) |
| TST-1394 | Full regression suite | FAIL | 7 new fails / 2749 passed / 3 pre-existing |

Pre-existing failures (not caused by SAF-020):
- `SAF-008`: Hash integrity (deferred to SAF-025)
- `INS-005`: `filesandirs` assertion (pre-existing, unrelated)
- `FIX-009`: Duplicate TST-1389 — **fixed by Tester** (duplicate corrected to TST-1391)

---

## Code Review

### What Was Implemented Correctly

1. **`_wildcard_prefix_matches_deny_zone(token)`** — New helper that checks whether a wildcard token's leading prefix (before first `*` or `?`) matches the start of any deny-zone name. Logic is sound for `*` and `?` characters.
2. **`_WILDCARD_DENY_ZONES`** — New constant defining lowercase deny zone names. Correctly populated.
3. **Defense-in-depth wiring** — Wildcard check added in three places:
   - `_check_path_arg()` — line 1038 (path-like tokens)
   - `_validate_args()` step 5 — line 1171 (non-path-like tokens like `N*`)
   - Exception-listed command validation — line 1364
4. **Mirror sync** — `templates/coding/.github/hooks/scripts/security_gate.py` is in sync.
5. **Backslash normalization** — Windows-style paths (`N*\subdir`) are normalized to forward slashes before prefix check.
6. **Quote stripping** — `tok.strip("\"'")` is applied in `_validate_args` before the wildcard check, so quoted wildcards (`"N*"`, `'.g*'`) are correctly caught.

### The Bug: Bracket Expression Wildcards Not Detected

The implementation only checks for `*` and `?` as wildcard characters (line 1171):

```python
if not _prev_was_flag and ("*" in stripped or "?" in stripped) and _wildcard_prefix_matches_deny_zone(stripped):
```

Unix and PowerShell shells also support **bracket expressions** `[chars]` as glob wildcards. For example:
- `[.g]*` — matches any path whose first character is `.` or `g`, **expanding to `.github`**
- `[Nn]*` — matches paths starting with `N` or `n`, **expanding to `NoAgentZone`**
- `[.v]*` — matches paths starting with `.` or `v`, **expanding to `.vscode`**

When the implementation processes `[.g]*`:
1. `"*" in "[.g]*"` → True — the wildcard check IS triggered
2. `comp_prefix = "[.g]"` — prefix before first `*`
3. Checks: `.github.startswith("[.g]")` → False, `.vscode.startswith("[.g]")` → False
4. Returns `False` (allow) → **active bypass**

Additionally, pure bracket expressions with no `*` or `?` (e.g., `[.g][it]hub`) are completely invisible to the check since neither `"*" in token` nor `"?" in token` would trigger the wildcard test.

**Logged as:** BUG-051

---

## Failing Tester Tests

All 7 failing tests are in `tests/SAF-020/test_saf020_tester_edge_cases.py::TestBracketExpressionWildcards` and one in `TestWildcardsAfterPipe`.

```
FAILED TestBracketExpressionWildcards::test_bracket_dotg_star_helper_denied
FAILED TestBracketExpressionWildcards::test_bracket_n_upper_lower_star_helper_denied
FAILED TestBracketExpressionWildcards::test_bracket_dotv_star_helper_denied
FAILED TestBracketExpressionWildcards::test_bracket_dotg_star_sanitize_denied
FAILED TestBracketExpressionWildcards::test_bracket_n_star_via_gci_denied
FAILED TestBracketExpressionWildcards::test_bracket_dotv_star_via_dir_denied
FAILED TestWildcardsAfterPipe::test_pipe_bracket_dotg_still_caught_by_ls
```

---

## Additional Finding: Pipe-via-echo Bypass (Not a New Regression)

Commands routed through `echo` (or any command with `allow_arbitrary_paths=True`) skip the wildcard check entirely. For example:

```
echo blah | ls .g*   → ALLOW  (expected DENY)
echo | gci .v*       → ALLOW  (expected DENY)
```

This occurs because:
1. `|` is not in `_CHAIN_RE` (splits only on `;`, `&&`, `||`)
2. `echo` has `allow_arbitrary_paths=True`, so `_validate_args` skips the argument validation block that contains the wildcard check

**This is a pre-existing structural issue** — it predates SAF-020 and also allows non-wildcard path access (`echo | cat .github/hooks/security_gate.py`). It should be addressed in a separate WP (recommended: SAF-022 or similar). It is NOT counted as a SAF-020 failure.

---

## Passing Edge Cases (All Pass)

| Category | Examples | Result |
|----------|----------|--------|
| Double-star at root | `**/*.py` → deny; `Project/**/*.py` → allow | ✅ PASS |
| Backslash Windows paths | `.g*\file` → deny; `Project\*.py` → allow | ✅ PASS |
| Wildcards after pipe (path-restricted verbs) | `ls \| cat N*` → deny | ✅ PASS |
| Bare wildcards | `*` → deny; `?` → deny | ✅ PASS |
| Quoted wildcards | `ls '.g*'` → deny; `cat "N*"` → deny | ✅ PASS |
| Wildcards in safe parent | `some/.g*/file` helper → False | ✅ PASS |
| Quote preservation of allow paths | `ls 'Project/*.py'` → allow | ✅ PASS |

---

## TODOs for Developer (Required to Pass)

### TODO 1 — Add bracket expression detection to `_wildcard_prefix_matches_deny_zone`

**File:** `Default-Project/.github/hooks/scripts/security_gate.py` (and mirror in `templates/`)

The function must treat `[` as a wildcard character trigger. Recommended approach:

```python
def _wildcard_prefix_matches_deny_zone(token: str) -> bool:
    # Add [ to the early-exit check:
    if "*" not in token and "?" not in token and "[" not in token:
        return False
    ...
    # In the per-component logic, extend the wildcard position calculation:
    wc_pos = len(part)
    for wc_char in ("*", "?", "["):
        pos = part.find(wc_char)
        if pos != -1:
            wc_pos = min(wc_pos, pos)
    comp_prefix = part[:wc_pos]
    ...
```

With this fix:
- `[.g]*` → wildcard detected at index 0 → comp_prefix = `""` (empty) → conservative deny ✓
- `[Nn]*` → wildcard at 0 → empty prefix → deny ✓
- `some/[.g]*` → safe parent entered → allow (unchanged, correct) ✓

### TODO 2 — Update the wildcard check triggers in `_validate_args` and `_check_path_arg`

**Line 1038 in `_check_path_arg`:**
```python
if _wildcard_prefix_matches_deny_zone(token):
```
This is already correct since `_wildcard_prefix_matches_deny_zone` will be fixed.

**Line 1171 in `_validate_args`:**
```python
if not _prev_was_flag and ("*" in stripped or "?" in stripped) and _wildcard_prefix_matches_deny_zone(stripped):
```
Update the trigger condition to also include `[`:
```python
if not _prev_was_flag and ("*" in stripped or "?" in stripped or "[" in stripped) and _wildcard_prefix_matches_deny_zone(stripped):
```

**Line 1364 in exception-listed command handling** — same update:
```python
if ("*" in stripped or "?" in stripped or "[" in stripped) and _wildcard_prefix_matches_deny_zone(stripped):
```

### TODO 3 — Sync the templated copy

After fixing `Default-Project/.github/hooks/scripts/security_gate.py`, sync all changes to `templates/coding/.github/hooks/scripts/security_gate.py`.

### TODO 4 — Update the `_WILDCARD_DENY_ZONES` docstring / comment

Update the `_wildcard_prefix_matches_deny_zone` docstring to mention bracket expressions:
```
Wildcards: *, ?, and [ (bracket expression start).
```

### TODO 5 — Run update_hashes.py

After modifying `security_gate.py`, run `.github/hooks/scripts/update_hashes.py` to update `_KNOWN_GOOD_GATE_HASH`. This will fix the SAF-008 hash test (which can then be removed from expected-fail notes).

---

## Pre-Done Checklist Result

- [x] `docs/workpackages/SAF-020/dev-log.md` exists and is non-empty
- [x] `docs/workpackages/SAF-020/test-report.md` written by Tester
- [x] Test files exist in `tests/SAF-020/` (developer + tester suites)
- [x] All test runs logged in `docs/test-results/test-results.csv`
- [ ] **BLOCKED: 7 security tests fail — WP cannot be marked Done**
- [ ] git commit / push — deferred until Developer fixes the bypass

**WP Status: Back to In Progress. Fix BUG-051 then re-submit for Tester review.**
