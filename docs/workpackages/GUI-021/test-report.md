# Test Report — GUI-021

**Tester:** Tester Agent  
**Date:** 2026-03-24  
**Iteration:** 1

## Summary

Implementation reviewed and tested. The Reset Agent Blocks button is correctly
placed in `SettingsDialog` (row 6 after the close button), uses atomic
temp-file + `os.replace` writes, and mirrors the SAF-037 `reset_counters()`
logic faithfully. All acceptance criteria from US-038 (ACs 6–9) are satisfied.
No bugs found. All 34 tests pass (18 Developer + 16 Tester edge-case).

## Code Review

### `_reset_hook_state` vs `reset_hook_counter.py` (SAF-037)

| Behaviour | SAF-037 | GUI-021 |
|-----------|---------|---------|
| Missing file → (0, message) | ✓ | ✓ |
| Corrupt file → write `{}`, return (0, warning) | ✓ | ✓ |
| Session detection: `isinstance(v, dict) and "deny_count" in v` | ✓ | ✓ |
| Non-session keys preserved | ✓ | ✓ |
| Atomic write via mkstemp + os.replace | ✓ | ✓ |
| Temp-file cleanup on failure | ✓ | ✓ |

Logic is correctly mirrored — no divergence.

### Edge-Case / Security Review

| Concern | Finding |
|---------|---------|
| Path traversal | Mitigated by `Path.is_dir()` — only existing directories accepted. Acceptable for local GUI use. |
| Whitespace in path | `.strip()` applied before validation — paths with surrounding spaces work correctly. |
| Locked file (PermissionError) | `PermissionError` is a subclass of `OSError`; caught and shown as "Reset Failed" dialog. |
| 1000-session file | All sessions reset, non-session keys preserved. No OOM or timeout risk. |
| Idempotency | Calling reset twice is safe — second call finds empty state and still shows confirmation. |
| Corrupt JSON variants (array/null/string root) | All handled by the `isinstance(state, dict)` guard → replaced with `{}`. |
| SettingsDialog geometry | Remains `"480x280"` — GUI-018 permanent test unaffected. |
| _WINDOW_HEIGHT (App) | Unchanged at 590 — GUI-012 permanent test unaffected. |

### Acceptance Criteria Verification (US-038 ACs 6–9)

| AC | Requirement | Status |
|----|-------------|--------|
| AC-6 | Launcher GUI includes a Reset Agent Blocks action | ✓ Reset Agent Blocks button in SettingsDialog |
| AC-7 | Reset action clears the workspace's stored counter state | ✓ `_reset_hook_state` removes all session entries |
| AC-8 | Shows confirmation after reset | ✓ `showinfo("Reset Complete", "All session counters have been reset.")` |
| AC-9 | Handles edge cases (no workspace, invalid path, missing file, locked file) | ✓ All four covered |

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| Dev: 18 tests in test_gui021_reset_button.py | Unit | Pass | Attributes, browse, no-workspace, invalid path, success, OSError, _reset_hook_state, atomic write |
| Tester: TestResetIdempotency (2) | Unit | Pass | Double reset succeeds, state stays empty |
| Tester: TestWorkspacePathWithSpaces (1) | Unit | Pass | Path with spaces handled correctly |
| Tester: TestLargeStateFile (2) | Unit | Pass | 1000 sessions cleared; non-session keys preserved |
| Tester: TestEmptyStateFile (2) | Unit | Pass | Empty `{}` state → 0 reset, confirmation shown |
| Tester: TestOnlyNonSessionKeys (1) | Unit | Pass | Non-session entries preserved, count=0 |
| Tester: TestLockedFile (2) | Unit | Pass | PermissionError shown as "Reset Failed"; temp file cleaned up on os.replace failure |
| Tester: TestCorruptStateVariants (3) | Unit | Pass | Array/null/string root replaced with `{}` |
| Tester: TestSessionEntryExtraKeys (1) | Unit | Pass | Session entries with extra fields correctly removed |
| Tester: TestPathWhitespaceStripping (2) | Unit | Pass | Leading/trailing whitespace stripped; whitespace-only rejected |
| Full regression suite (--full-suite, TST-2072) | Regression | Note | 72 pre-existing failures confirmed on main branch (yaml import errors in INS/FIX CI workflow tests — unrelated to GUI-021). No new failures introduced. |

TST IDs logged: TST-2071 (WP-specific, Pass), TST-2072 (full suite, pre-existing failures only)

## Bugs Found

None.

## TODOs for Developer

None.

## Verdict

**PASS — mark WP as Done.**

All 34 tests pass. Implementation is correct, complete, and matches the WP
description. Acceptance criteria ACs 6–9 of US-038 are all satisfied. No
regressions introduced. Pre-existing full-suite failures are unrelated to
this WP and exist on main branch.
