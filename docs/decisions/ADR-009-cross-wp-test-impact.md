# ADR-009: Advisory Pre-Commit Hook for Cross-WP Test Impact Detection

**Status:** Active  
**Date:** 2026-04-05  
**Related WPs:** MNT-025, MNT-026  
**Supersedes:** None  
**Superseded by:** None

## Context

Between 2025 and 2026, five waves of codebase evolution broke tests without updating them:

| Wave | Change | Tests Broken |
|------|--------|-------------|
| 1 | Template rename: `templates/coding/` → `templates/agent-workbench/` | ~40 |
| 2 | Agent redesign: 10 agent files rewritten with new content/structure | ~452 |
| 3 | Prefix rename: `TS-SAE-` → `SAE-` in WP and test IDs | ~27 |
| 4 | Version churn: `3.2.x` → `3.3.11` across source files | ~60 |
| 5 | JSONL migration: CSV → JSONL for all data files | ~30 |

The cumulative drift (~688 known failures + ~400 uncovered) blocked releases and required FIX-103 through FIX-107 + MNT-024 + DOC-059 to remediate.

ADR-008 established the rule that assertions must track code changes, but lacked enforcement tooling. Cross-WP test divergence occurs because each workpackage only updates its own tests in `tests/<WP-ID>/`, even when the code change affects tests from other WPs. No process check existed to alert the developer that tests outside their own WP folder might be affected.

## Decision

Add an advisory pre-commit hook (`scripts/check_test_impact.py`) that scans the test suite for references to modified source modules and outputs warnings. The hook is advisory-only (exit code 0) — it never blocks commits. Developers are responsible for reviewing flagged tests and updating assertions in the same commit where relevant.

The hook is registered via `scripts/install_hooks.py`. Running it is optional per developer; the Orchestrator may require it as part of onboarding.

### What the hook does

1. Reads the list of staged files from `git diff --cached --name-only`.
2. For each staged Python source file, extracts the module name.
3. Greps `tests/` for any test file that imports or references that module name.
4. Prints a warning for each such test file, listing which staged source file triggered it.
5. Exits with code 0 regardless of findings.

### What the hook does not do

- It does not run tests.
- It does not block commits.
- It does not detect semantic breakage — only textual references.

## Consequences

### Positive

- Drift is caught at commit time rather than weeks later in CI.
- Developers get a low-cost signal before breakage propagates.
- Reinforces ADR-008 with tooling without adding friction.

### Negative

- False positives are possible: a test may reference a module name without being logically affected by the change.
- Developer must exercise judgment when reviewing flagged tests.
- The hook does not replace full suite runs — it is a supplement, not a substitute.

## Notes

- ADR-008 (`docs/decisions/ADR-008-tests-track-code.md`) established the underlying rule; ADR-009 adds enforcement tooling for it.
- MNT-025 implemented `scripts/check_test_impact.py`.
- Related remediation: FIX-103, FIX-104, FIX-105, FIX-106, FIX-107, MNT-024, DOC-059.
