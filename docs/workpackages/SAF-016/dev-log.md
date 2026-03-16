# Dev Log — SAF-016

**Developer:** Developer Agent
**Date started:** 2026-03-16
**Iteration:** 1

## Objective

Add delete commands to the terminal allowlist with `path_args_restricted=True`:
`remove-item` (and aliases `ri`, `rm`, `del`, `erase`, `rmdir`). When ALL path
arguments are inside the project folder, return "allow". When ANY path argument
is outside the project folder, return "deny". Remove these commands from
`_EXPLICIT_DENY_PATTERNS` since they are now handled by the allowlist with zone
checking.

**Goal:** Delete commands work inside the project folder and are hard-denied when
targeting anything outside it.

## Implementation Summary

Added Category N (Delete commands) to `_COMMAND_ALLOWLIST` in both copies of
`security_gate.py`. Each command is registered with:
- `denied_flags=frozenset()` — no specific flags denied (flags like `-rf`, `-r`,
  `-f`, `-Recurse`, `-Force` are allowed because zone checking provides the
  safety boundary)
- `path_args_restricted=True` — ALL positional path arguments must resolve inside
  the project folder; any outside path → deny
- `allow_arbitrary_paths=False` — consistent with other restricted commands

The following commands were added to the allowlist (Category N):
- `remove-item` — PowerShell Remove-Item
- `ri` — PowerShell alias for Remove-Item
- `rm` — Unix/POSIX rm
- `del` — Windows del
- `erase` — Windows erase (alias for del)
- `rmdir` — Unix/Windows rmdir

Simultaneously, `rm`, `del`, `erase`, `rmdir`, `remove-item`, and `ri` were
removed from `_EXPLICIT_DENY_PATTERNS`. Their previous deny-all behaviour is now
replaced by the allowlist's zone check: operations inside `Project/` are allowed
while any path outside is denied.

Both `Default-Project/.github/hooks/scripts/security_gate.py` and
`templates/coding/.github/hooks/scripts/security_gate.py` were updated. The
integrity hash (`_KNOWN_GOOD_GATE_HASH`) in both files reflects the SHA256 of the
canonical file content (hash field zeroed). The templates/coding copy was synced
to be byte-for-byte identical to the Default-Project source.

The SAF-005 cascade test (`test_saf005_terminal_sanitization.py`) was updated to
reflect that delete commands are no longer in `_EXPLICIT_DENY_PATTERNS` and
instead route through the allowlist.

## Files Changed

- `Default-Project/.github/hooks/scripts/security_gate.py` — Added Category N
  block (lines ~675–718); removed `rm`/`del`/`erase`/`rmdir`/`remove-item`/`ri`
  from `_EXPLICIT_DENY_PATTERNS`; updated `_KNOWN_GOOD_GATE_HASH`
- `templates/coding/.github/hooks/scripts/security_gate.py` — Synced byte-for-
  byte with Default-Project copy (Category N additions + correct hash)
- `tests/SAF-005/test_saf005_terminal_sanitization.py` — Cascade fix: delete
  commands now expected in allowlist, not explicit deny list

## Tests Written

**`tests/SAF-016/test_saf016_delete_commands.py`** (40 tests):
- Per-command allow/deny coverage for all 6 commands: `remove-item`, `ri`, `rm`,
  `del`, `erase`, `rmdir`
- Targets `.github/`, `.vscode/`, `NoAgentZone/`, and root paths → denied
- Targets `Project/` paths → allowed
- Verifies all 6 commands are present in `_COMMAND_ALLOWLIST`
- Verifies none are present in `_EXPLICIT_DENY_PATTERNS`
- Verifies `path_args_restricted=True` for all Category N commands

**`tests/SAF-016/test_saf016_edge_cases.py`** (28 tests):
- `rm -rf`, `rm -f`, `rm -r` — flags allowed when path is in project
- `remove-item -Recurse`, `-Force`, `-Recurse -Force`
- `rmdir /s /q` variants
- Variable path arguments — denied
- Quoted paths with spaces — correctly resolved
- Mixed-case verbs (`REMOVE-ITEM`, `RM`, `DEL`)
- Chained commands (`&&`) mixing project and protected paths — denied
- Path traversal attempts (`../../.github`) — denied
- Multiple path args: all-project → allow; mixed project+protected → deny

## Known Limitations

- Delete commands do not distinguish between file vs. directory targets; the zone
  check applies uniformly to the path argument regardless of whether it resolves
  to a file or directory.
- The `-Recurse` / `-rf` flags are not individually restricted. The security
  boundary is the path zone, not the recursion depth; a recursive delete that
  targets only `Project/` subtrees is permitted by design.
