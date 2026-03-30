# SAF-059 — Dev Log: Fix 4 terminal command filtering inconsistencies

## Status: In Progress

## Assignment
Fix four terminal command filtering bugs in `security_gate.py`:
- BUG-140: Remove-Item blocked but del allowed (Stage 3 false-positive risk)
- BUG-141: dir -Name blocked (flag treated as path argument)
- BUG-142: Parenthesized subexpressions blocked (e.g. `(Get-Content file).Count`)
- BUG-143: Test-Path not in `_COMMAND_ALLOWLIST`

## Investigation Notes

### BUG-140 (Remove-Item vs del)
Both `remove-item` and `del` are in `_COMMAND_ALLOWLIST` (Category N) with
identical `CommandRule` (path_args_restricted=True, allow_arbitrary_paths=False).

The root cause: Stage 3 obfuscation pre-scan runs on the FULL lowered segment
string BEFORE verb extraction. If a path argument contains a token matching an
obfuscation pattern (e.g., `project/exec-scripts/` triggers P-21 `\bexec\b`,
`project/source.sh` triggers P-22 `\bsource\s+`), the whole command is denied
even though the verb is allowlisted.

**Fix**: Pre-extract each segment's verb before Stage 3. If the verb is in
`_COMMAND_ALLOWLIST`, skip Stage 3 for that segment — Stage 5 arg-zone checks
provide the necessary security validation.

### BUG-141 (dir -Name)
`-Name` already starts with `-` and is correctly skipped (not treated as a path
argument) in both Step 5 and Step 8 of `_validate_args`. The behavior of
`dir -Name` is functionally identical to plain `dir` — both use the CWD ancestor
check in Step 8 when no path argument is present.

The existing code is correct. This WP adds explicit test coverage to document
and lock in the behavior as a regression baseline.

### BUG-142 (Parenthesized subexpressions)
`(Get-Content file.txt).Count` tokenizes to verb `(Get-Content`, which is not
in `_COMMAND_ALLOWLIST` → unknown-verb deny path.

The `$(...)` subshell pattern (P-19) does NOT fire here; the issue is in Stage 4
verb extraction from the raw token list. The outer `(` becomes part of the verb
token.

**Fix**: In `sanitize_terminal_command`, before tokenizing each segment, check
if the segment matches the `(inner_cmd).property` pattern. If so, unwrap to use
the inner command for all validation. Also apply this unwrapping in the Stage 3
pre-extraction for BUG-140 fix so that allowlisted-inner-verb segments skip Stage 3.

Added module-level constant `_PAREN_SUBEXPR_RE` to match these expressions.

### BUG-143 (Test-Path not in allowlist)
`Test-Path` is a read-only PowerShell diagnostic cmdlet. Simple addition to
Category G with `path_args_restricted=True`, `allow_arbitrary_paths=False`.

## Implementation

### Files Changed
- `templates/agent-workbench/.github/hooks/scripts/security_gate.py`

### Changes Made

#### 1. Added `_PAREN_SUBEXPR_RE` constant (BUG-142)
Module-level compiled regex for detecting `(inner_cmd).Property` patterns.

#### 2. Added `test-path` to `_COMMAND_ALLOWLIST` Category G (BUG-143)
Placed after `get-content` in the read-only file inspection section.

#### 3. Modified Stage 3 scan to skip allowlisted-verb segments (BUG-140)
For each non-venv segment, pre-extract the verb (handling paren expressions).
If the verb is in `_COMMAND_ALLOWLIST`, skip Stage 3 for that segment.
Unknown-verb segments still receive the full Stage 3 obfuscation scan.

#### 4. Added paren subexpression unwrapping in Stage 4/5 (BUG-142)
In the per-segment processing loop, before tokenizing, check if the segment
matches `_PAREN_SUBEXPR_RE`. If so, replace the segment with its inner command
for all subsequent validation (verb extraction, allowlist lookup, arg validation).

## Tests Written
- `tests/SAF-059/test_saf059_terminal_filtering.py` — all 4 bug scenarios

## Post-Implementation Verification
- All SAF-059 tests pass
- All SAF-016 (delete commands) tests pass
- All existing suite tests pass
