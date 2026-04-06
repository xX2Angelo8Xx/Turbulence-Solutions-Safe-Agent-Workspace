# FIX-118 — Allow Remove-Item for project folder files

## Status
In Progress → Review

## Assigned To
Developer

## Summary
Extends the `security_gate.py` terminal validator to allow `Remove-Item`, `ri`, `rm`,
`del`, `erase`, and `rmdir` when targeting files and directories inside the project folder.
Previously only `Remove-Item`/`ri` had a limited dot-prefix fallback (SAF-029), and no
delete verb handled multi-segment paths like `src/oldfile.py`.

## Root Cause
`_validate_args()` invoked `_try_project_fallback()` for delete verbs only for single-segment
dot-prefix names (`.venv`, `.env`).  The condition explicitly excluded:
- Multi-segment paths (`src/app.py`, `docs/old/file.md`)
- Unix `rm`/`del`/`erase`/`rmdir` (only `remove-item`/`ri` were in the old set)

This meant `Remove-Item src/oldfile.py` was denied even when the resolved path was
`ws_root/project/src/oldfile.py` — clearly inside the project folder.

## ADR Review
Checked `docs/decisions/index.jsonl`; no ADR directly governs delete fallback expansion.
ADR-011 (settings.json hash removal) and ADR-007 (zone classifier design) are related
but not affected by this change.

## Bugs Fixed
- **BUG-199** — "File deletion impossible despite full CRUD access promise"
  `Fixed In WP` set to `FIX-118`.

## Implementation

### `templates/agent-workbench/.github/hooks/scripts/security_gate.py`

**Renamed constant:**
- `_DELETE_DOT_FALLBACK_VERBS` → `_DELETE_PROJECT_FALLBACK_VERBS`
- Added `rm`, `del`, `erase`, `rmdir` to the set (was: `remove-item`, `ri` only)

**Expanded fallback logic in `_validate_args` (step 5):**
- Was: single-segment dot-prefix only
- Now: same condition as `_PROJECT_FALLBACK_VERBS` — multi-segment paths
  (`src/file.py`) AND single-segment dot-prefix (`.venv`, `.env`) are tried
  via `_try_project_fallback()`.
- Single-segment non-dot paths without trailing slash (e.g. `./MANIFEST.json`
  normalizes to `MANIFEST.json`) are still excluded — conservative guard
  against ambiguous workspace-root references.

**Security invariants preserved:**
- `_try_project_fallback()` already rejects deny-zone names (`.github`,
  `.vscode`, `noagentzone`) in any path component.
- Paths resolving outside the project folder are denied.
- Wildcard expansion bypass (SAF-020) remains active — `rm .g*` is denied.
- Absolute paths outside the workspace (`rm c:/other/...`) are denied.

### `templates/agent-workbench/Project/AGENT-RULES.md`
Added `Remove-Item` / `rm` file-deletion examples to the Terminal Rules section's
"Permitted Commands" block.

### `tests/SAF-029/test_saf029_delete_dot_prefix.py`
Tests TST-5343 to TST-5347 previously asserted `deny` for behaviours that FIX-118
intentionally changes to `allow`. These tests have been updated to the new expected
behaviour with updated docstrings explaining the FIX-118 rationale.

## Tests Written
- `tests/FIX-118/test_fix118_delete_project_fallback.py` — comprehensive unit/security tests
  covering allow cases, deny-zone protection, wildcard protection, and regression checks.
- 2 new snapshot files added to `tests/snapshots/security_gate/`.

## Files Changed
- `templates/agent-workbench/.github/hooks/scripts/security_gate.py`
- `templates/agent-workbench/Project/AGENT-RULES.md`
- `tests/SAF-029/test_saf029_delete_dot_prefix.py`
- `tests/FIX-118/__init__.py`
- `tests/FIX-118/test_fix118_delete_project_fallback.py`
- `tests/snapshots/security_gate/allow_delete_project_multisegment.json`
- `tests/snapshots/security_gate/deny_delete_github_path.json`
- `docs/workpackages/FIX-118/dev-log.md`
- `docs/workpackages/workpackages.jsonl`
- `docs/bugs/bugs.jsonl`
- `templates/agent-workbench/.github/hooks/scripts/MANIFEST.json`

## Known Limitations
- Single-segment non-dot paths (e.g. `rm file.txt`) are already allowed by the gate
  since they are not recognized as path-like by `_is_path_like()`. The new fallback
  does not change this behaviour.
