# INS-030 Dev Log — Add git init to newly created workspaces

## Problem Statement

BUG-171: Workspaces created by the installer have no `.git` directory.
Agents trying to use git (as described in AGENT-RULES.md §5) hit
`fatal: not a git repository` immediately on their first session.

The documentation fix (prerequisite note in §5) was shipped in DOC-050.
This WP delivers the code fix: auto-initialise git at workspace creation time.

## Changes Made

### `src/launcher/core/project_creator.py`

- Added `import subprocess` to standard-library imports.
- Added `_init_git_repository(workspace: Path) -> bool` helper function.
  - Runs `git init`, `git add -A`, `git commit -m "Initial commit"` in sequence.
  - Returns `True` on success, `False` if git is unavailable or fails.
  - Errors are caught (`OSError`, `TimeoutExpired`) — failure is non-fatal.
  - Each subprocess call has a 30-second timeout.
- Added `_init_git_repository(target)` call in `create_project()` after the
  `include_readmes` block and before `return target`.

## Design Rationale

- **Non-fatal design**: If git is not installed (unlikely on developer machines
  but possible), workspace creation must still succeed. The user or an agent
  can run `git init` manually later.
- **Single initial commit**: Captures the full template state so agents have a
  clean baseline to diff against and can use `git status`, `git diff`, `git log`
  from session one.
- **No user-facing changes**: The git init is transparent — the GUI and launcher
  surface are unchanged.

## Test Coverage

8 tests in `tests/INS-030/test_ins030_git_init.py`:
- Unit tests for `_init_git_repository`: success, OSError, TimeoutExpired, non-zero exit.
- Integration tests for `create_project`: `.git` exists, initial commit exists, succeeds when git mocked away.
