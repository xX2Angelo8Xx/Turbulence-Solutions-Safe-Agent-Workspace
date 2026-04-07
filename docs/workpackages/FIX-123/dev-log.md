# Dev Log — FIX-123: Fix get_changed_files zone bypass

## Status: In Progress

## Summary

FIX-117 added `get_changed_files` to `_ALWAYS_ALLOW_TOOLS` claiming the tool returns only changed file metadata. In reality, `get_changed_files` returns full diff content that includes content from all zones (NoAgentZone, `.github/`, `.vscode/`). This is a security regression (BUG-208) reintroducing BUG-136.

This WP reverts the FIX-117 change by:
1. Removing `"get_changed_files"` from `_ALWAYS_ALLOW_TOOLS` in both template `security_gate.py` files
2. Re-adding `validate_get_changed_files(ws_root)` — zone-aware handler: deny when `.git/` directory exists at workspace root, allow otherwise
3. Routing `get_changed_files` through `decide()` to this validator
4. Updating `AGENT-RULES.md §3` in both templates to document actual behavior
5. Running `update_hashes.py` to update security hash constants
6. Updating `tests/regression-baseline.json` — removing SAF-058 entries (now pass), adding FIX-117 entries (now fail)

## Related ADRs

No ADRs directly address this change. BUG-136 and BUG-208 are bug reports in the bugs tracker. FIX-117 introduced the regression being fixed here.

## Files Changed

- `templates/agent-workbench/.github/hooks/scripts/security_gate.py`
- `templates/clean-workspace/.github/hooks/scripts/security_gate.py`
- `templates/agent-workbench/Project/AGENT-RULES.md`
- `templates/clean-workspace/Project/AGENT-RULES.md`
- `tests/regression-baseline.json`
- `docs/workpackages/workpackages.jsonl`

## Tests Written

- `tests/FIX-123/test_fix123_get_changed_files_zone_bypass.py`

## Implementation Notes

- `validate_get_changed_files(ws_root)` uses `os.path.isdir()` to check for `.git/` at workspace root
- `.git` as a FILE (worktree pointer) is **not** caught by `isdir()` → allow (documented design decision per SAF-058 spec)
- `.git` as a symlink to a directory IS caught by `isdir()` (follows symlinks) → deny
- OSError → fail closed → deny
- The routing in `decide()` is added before the `_ALWAYS_ALLOW_TOOLS` catch-all, after `file_search` handler

## Iteration History

### Iteration 1 — Initial Implementation
