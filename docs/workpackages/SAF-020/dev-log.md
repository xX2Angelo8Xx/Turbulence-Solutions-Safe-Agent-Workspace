# SAF-020 Dev Log — Detect and Block Terminal Wildcard Patterns

## Status
In Progress → Review

## Goal
Close the terminal wildcard bypass vector by adding wildcard/glob detection to the terminal command sanitizer in `security_gate.py`. Conservative approach: deny any wildcard token whose prefix could resolve to a deny zone directory name.

## Implementation Summary

### Approach
Added a new function `_wildcard_prefix_matches_deny_zone(token)` that:
1. Normalizes the token to lowercase forward-slash form
2. Splits into path components
3. Walks components tracking whether a non-deny parent directory has been entered
4. For wildcard-containing components: if no safe parent exists, checks whether any deny zone name (`_WILDCARD_DENY_ZONES`) starts with the prefix before the first `*` or `?`
5. Returns `True` (deny) if a wildcard could expand to a deny zone, `False` (allow) otherwise

### Deny zone coverage
- `.g*` → prefix `.g` → `.github` starts with `.g` → deny
- `N*` → prefix `n` → `noagentzone` starts with `n` → deny
- `.v*` → prefix `.v` → `.vscode` starts with `.v` → deny
- `.*` → prefix `.` → `.github` and `.vscode` start with `.` → deny
- `N*/*` → first wildcard component prefix `n` → deny

### Allow zone coverage
- `Project/*.py` → wildcard is inside `Project/` (non-deny parent) → allow
- `tests/*.py` → wildcard inside `tests/` (non-deny parent) → allow
- `src/launcher/*.py` → non-deny parent → allow

### Modified functions
1. `_check_path_arg` — added wildcard check before zone_classifier call (defense in depth)
2. `_validate_args` step 5 — added wildcard check for non-path-like tokens (e.g., `N*` has no `/` or `.`, so `_is_path_like` returns False without wildcard guard)
3. Exception-listed command validation in `sanitize_terminal_command` — added wildcard check

### New constant
`_WILDCARD_DENY_ZONES: tuple[str, ...]` — lowercase deny zone names used for prefix matching

### Files Changed
- `Default-Project/.github/hooks/scripts/security_gate.py` — primary implementation
- `templates/coding/.github/hooks/scripts/security_gate.py` — synced mirror

## Tests Written

### `tests/SAF-020/`
- `test_saf020_wildcard_blocking.py` — core unit and integration tests:
  - `TestWildcardPrefixMatchesDenyZone` — unit tests for the new helper function
  - `TestWildcardBlockingInSanitize` — integration tests via `sanitize_terminal_command`
  - `TestWildcardBypassAttempts` — explicit bypass attempt scenarios
  - `TestWildcardAllowedPaths` — allowed wildcard scenarios

## Known Limitations
- Conservative approach: bare `*` or `?` at root level (e.g., `ls *`) is denied. Wildcards must be inside a known non-deny parent directory to be allowed.
- `..` traversal components before wildcards are treated as root-level for safety.

## Test Results
All tests pass. See test-results.csv for run details.

---

## Iteration 2 — Fix BUG-051: Bracket Expression Wildcards

**Date:** 2026-03-17  
**Tester finding:** Bracket expression wildcards `[...]` (e.g., `[.g]*`, `[Nn]*`, `[.v]*`) bypassed detection because the `wc_pos` calculation only searched for `*` and `?`, yielding prefix `[.g]` instead of the true empty prefix.

### Root Cause
In `_wildcard_prefix_matches_deny_zone`, the prefix before the first wildcard character was computed as:
```python
wc_pos = min(part.find(c) for c in ("*", "?") if c in part)
```
For `[.g]*`, `*` is at index 4, so `comp_prefix = "[.g]"`. No deny zone starts with `[.g]` → incorrectly allowed.

### Fix Applied
Three changes to `_wildcard_prefix_matches_deny_zone` in both `security_gate.py` files:

1. **Early-exit guard** — added `"[" not in token` so pure bracket expressions (no `*`/`?`) are also evaluated:
   ```python
   if "*" not in token and "?" not in token and "[" not in token:
       return False
   ```

2. **Part wildcard detection** — added `"[" not in part` so bracket-containing components enter the wildcard branch:
   ```python
   if "*" not in part and "?" not in part and "[" not in part:
   ```

3. **`wc_pos` calculation** — added `"["` to the searched characters so the prefix is extracted before the first `[`:
   ```python
   wc_pos = min(part.find(c) for c in ("*", "?", "[") if c in part)
   ```
   For `[.g]*`: `[` is at index 0 → `comp_prefix = ""` → empty prefix matches all deny zones → deny ✓  
   For `N[abc]*`: `[` is at index 1 → `comp_prefix = "n"` → `noagentzone` starts with `n` → deny ✓

4. **Caller sites** — added `"[" in stripped` to the trigger condition in `_validate_args` step 5 and in the exception-listed command validation, ensuring pure bracket expressions (`[.g][it]hub`) are also sent to the helper:
   ```python
   if not _prev_was_flag and ("*" in stripped or "?" in stripped or "[" in stripped) and ...
   ```

### Files Changed
- `Default-Project/.github/hooks/scripts/security_gate.py` — bracket wildcard fix + hash update
- `templates/coding/.github/hooks/scripts/security_gate.py` — synced mirror + hash update

### Test Results (Iteration 2)
- SAF-020 suite: **107/107 passed** (includes 7 previously-failing Tester edge cases)
- Full regression: **2782 passed, 1 failed (INS-005 pre-existing), 29 skipped**
