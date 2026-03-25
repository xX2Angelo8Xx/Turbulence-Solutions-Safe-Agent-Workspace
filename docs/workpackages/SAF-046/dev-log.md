# Dev Log — SAF-046

**Developer:** Developer Agent
**Date started:** 2026-03-25
**Iteration:** 1

## Objective
Enable workspace root read access in the security gate. Currently the 2-tier zone model allows only paths inside the detected project folder. AGENT-RULES §1 and §3 specify that agents should be able to read config files at the workspace root (pyproject.toml, README.md, etc.) and list the workspace root directory. This WP implements scoped, read-only access for those operations without weakening any other security controls.

## Linked User Story
US-052 — Security Gate Must Match AGENT-RULES.md Permissions

## Related Bugs
- BUG-111: Workspace root access blocked despite AGENT-RULES allowing it (Fixed In WP: SAF-046)

## Acceptance Criteria
1. `read_file` on workspace root config files succeeds (e.g. pyproject.toml, README.md)
2. `list_dir` on the workspace root itself succeeds
3. Denied zones (.github/, .vscode/, NoAgentZone/) remain denied
4. Paths deeper than 1 level below the workspace root (that are not in the project folder) remain denied
5. Write operations to workspace root remain denied

## Implementation

### Files Changed
- `templates/agent-workbench/.github/hooks/scripts/zone_classifier.py` — Added `is_workspace_root_readable()` function
- `templates/agent-workbench/.github/hooks/scripts/security_gate.py` — Updated exempt-tool path in `decide()` to call `is_workspace_root_readable()` after `classify()` returns deny

### Design Decisions

**Why add a function in zone_classifier rather than in security_gate?**
The zone_classifier is the authoritative source for access-zone logic. Adding `is_workspace_root_readable()` there keeps the path-normalization logic centralized and consistent with the existing `classify()` and `is_git_internals()` functions.

**Why not expand `classify()` to return "allow" for workspace root?**
If `classify()` returned "allow" for workspace root paths, `validate_write_tool()` would also allow write operations there. The WP requires READ-ONLY access. The cleanest resolution is an additional predicate function (`is_workspace_root_readable()`) that security_gate.py calls only in the exempt (read) tool path.

**Security constraints maintained:**
- `.github/`, `.vscode/`, `NoAgentZone/` direct children → denied via `_DENY_DIRS` check
- `.git/` at root → denied via separate `is_git_internals()` check in security_gate.py
- Paths more than 1 level deep below workspace root (in non-project dirs) → denied (`len(rel.parts) == 1` constraint)
- Write operations to workspace root → `validate_write_tool()` still uses `classify()` only → denied
- Path traversal → `normalize_path()` resolves `..` sequences → caught by existing checks

## Tests Written
- `tests/SAF-046/test_saf046_workspace_root_access.py` — 20 tests covering:
  - `is_workspace_root_readable()` unit tests (allow/deny cases)
  - `decide()` integration tests (read_file, list_dir on workspace root)
  - Security bypass tests (write to root denied, deny zones remain denied, deep paths denied)
  - Cross-platform path format tests

## Test Results
All 20 tests pass.
