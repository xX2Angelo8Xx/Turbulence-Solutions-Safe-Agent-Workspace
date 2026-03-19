# FIX-022 to FIX-027 — Developer Log

## Summary
Fixed the relative path resolution issue in `security_gate.py` that caused legitimate agent operations inside the project folder to be incorrectly denied. Also resolved FIX-023 (venv creation), FIX-024/FIX-025/FIX-027 (investigation-resolved), and FIX-026 (get_errors).

## Root Cause
When agents work inside the project folder, relative paths like `src/app.py` and `tests/` are resolved against the workspace root (`ws_root/src/app.py`) instead of the project folder (`ws_root/<project>/src/app.py`). Since `ws_root/src/app.py` is outside the project folder, the zone classifier denies the path.

## Changes Made

### `Default-Project/.github/hooks/scripts/security_gate.py`

1. **Added `_PROJECT_FALLBACK_VERBS` frozenset** (after `_check_path_arg`): Read/execute verbs safe for project-folder fallback. Destructive verbs (rm, del, remove-item) are intentionally excluded.

2. **Added `_try_project_fallback()` helper**: Retries zone classification with the project folder prefix. Has guards for absolute paths, tildes, deny zones, and empty paths.

3. **Modified `_validate_args` step 4** (FIX-023): Added project-folder fallback for venv targets. Also tracks validated indices via `_step4_validated_indices` so step 5 skips re-checking them.

4. **Modified `_validate_args` step 5** (FIX-022, resolves FIX-025): After `_check_path_arg` denies a relative path, tries project-folder fallback for safe verbs. Guards:
   - No wildcards in token (wildcard denial from _check_path_arg should not be overridden)
   - Multi-segment paths (2+) always get fallback
   - Single-segment paths only get fallback if original token ends with "/" (directory reference)

5. **Added venv activation handler in `sanitize_terminal_command`** (FIX-022): Allows activation scripts like `.venv/Scripts/Activate.ps1` via zone check + fallback.

6. **Modified `validate_get_errors`** (FIX-026): Added fallback for relative paths in filePaths array.

### Test Updates
- **SAF-017**: Updated `test_python_m_venv_dot_venv_at_root_denied` → now expects allow (FIX-023 intentionally allows `.venv` via fallback)

### New Tests
- `tests/FIX-022/test_fix022_path_fallback.py` — 31 tests covering fallback for safe verbs, denial for destructive verbs, deny-zone guards, chained commands, and unit tests for `_try_project_fallback`
- `tests/FIX-023/test_fix023_venv_fallback.py` — 9 tests covering venv creation and activation scripts
- `tests/FIX-026/test_fix026_get_errors_fallback.py` — 7 tests covering get_errors with relative and absolute paths

### Investigation-Resolved WPs
- **FIX-024**: Root cause is hash staleness (SAF-008), not a code bug. Running `update_hashes.py` after changes resolves the issue.
- **FIX-025**: cat/type already in allowlist (Category G). Root cause was the same relative path resolution issue, resolved by FIX-022's fallback.
- **FIX-027**: Absolute Windows paths work correctly via zone_classifier Method 1. The original report's issue was the relative-path bug fixed by FIX-022.

## Test Results
- Full suite: 3256 passed, 2 failed (pre-existing: FIX-009 duplicate TST-IDs + INS-005 BUG-045), 29 skipped, 1 xfailed
- Zero regressions
