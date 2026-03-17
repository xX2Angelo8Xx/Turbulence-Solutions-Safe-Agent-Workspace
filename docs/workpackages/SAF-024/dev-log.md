# Dev Log — SAF-024: Implement Generic Deny Messages

## Status
In Progress → Review

## WP Summary
Replace the `_DENY_REASON` constant in `security_gate.py` with a fully generic
message that does not reveal any restricted zone names to the agent. The approved
message is: *"Access denied. This action has been blocked by the workspace security
policy."* All deny paths that previously exposed `.github`, `.vscode`, or
`NoAgentZone` in the returned reason string now use this constant exclusively.

## Files Changed
- `Default-Project/.github/hooks/scripts/security_gate.py` — `_DENY_REASON` set to generic text; all deny return paths use `_DENY_REASON`
- `templates/coding/.github/hooks/scripts/security_gate.py` — sync with Default-Project/
- `docs/workpackages/workpackages.csv` — status updated to Review
- `docs/test-results/test-results.csv` — test run logged
- `tests/SAF-020/test_saf020_wildcard_blocking.py` — minor assertion update for new deny message text

## Implementation

### Changes to security_gate.py

1. **`_DENY_REASON` constant** (line 81) — changed from a message that revealed
   internal zone names to:
   `"Access denied. This action has been blocked by the workspace security policy."`

2. **All deny return paths** — verified that every `("deny", ...)` tuple in
   `sanitize_terminal_command()`, `decide()`, and `main()` uses `_DENY_REASON`
   (or an f-string incorporating it) rather than inline strings that mention
   `.github`, `.vscode`, or `NoAgentZone`.

3. **Internal comments and logging** left unchanged — zone names are still
   referenced in code comments and log statements, but never in the JSON
   response payload sent to VS Code stdout.

### Both copies updated in sync
`templates/coding/.github/hooks/scripts/security_gate.py` was updated to match
`Default-Project/.github/hooks/scripts/security_gate.py` exactly.

## Tests Written
- `tests/SAF-024/test_saf024_generic_deny_messages.py` — 10 tests (TST-601 through TST-610)
  - TST-601: `_DENY_REASON` equals the approved generic message exactly
  - TST-602: `_DENY_REASON` does not contain `.github`
  - TST-603: `_DENY_REASON` does not contain `.vscode`
  - TST-604: `_DENY_REASON` does not contain `NoAgentZone`
  - TST-605: `_DENY_REASON` does not start with the old `BLOCKED:` prefix
  - TST-606: `main()` stdout deny reason matches generic message (end-to-end)
  - TST-607: `main()` stdout deny reason contains no zone names (bypass check)
  - TST-608: All `sanitize_terminal_command()` deny paths contain no zone names
  - TST-609: `_DENY_REASON` is a plain `str`
  - TST-610: `templates/coding/` `security_gate.py` contains the same generic message

## Test Results
- All 10 SAF-024 tests: PASS
- Full regression suite: 2950 passed / 1 pre-existing failure (INS-005) / 29 skipped
- No new regressions introduced

## Decisions
- Zone names retained in comments and internal log statements: required for
  maintainability; they never appear in agent-visible JSON output.
- `_DENY_REASON` used as a constant rather than duplicated strings: single source
  of truth ensures future message changes propagate everywhere automatically.
- Templates sync: mandatory per project convention to keep both copies identical.
