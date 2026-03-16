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
