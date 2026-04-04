# ADR-008: Tests Must Track Current Codebase State

**Status:** Active  
**Date:** 2026-04-04  
**Related WPs:** FIX-103, FIX-104, FIX-105, FIX-106, FIX-107, MNT-024, DOC-059  
**Supersedes:** None  
**Superseded by:** None

## Context

Between 2025 and 2026, five waves of codebase evolution each changed externally-visible identifiers, paths, or content without updating the corresponding test assertions:

| Wave | Change | Tests Broken |
|------|--------|-------------|
| 1 | Template rename: `templates/coding/` → `templates/agent-workbench/` | ~40 |
| 2 | Agent redesign: 10 agent files rewritten with new content/structure | ~452 |
| 3 | Prefix rename: `TS-SAE-` → `SAE-` in WP and test IDs | ~27 |
| 4 | Version churn: `3.2.x` → `3.3.11` across source files | ~60 |
| 5 | JSONL migration: CSV → JSONL for all data files | ~30 |

**Total drift: ~688 known failures + ~400 uncovered failures**, completely blocking the CI release pipeline.

The project had an existing rule: *"Test scripts are permanent — never delete them after the WP reaches Done."* This rule served its purpose well (no tests were lost), but it created a false sense of safety. The rule governed **deletion** but said nothing about **mutation** — it did not require assertions to be kept in sync with the code they assert against.

Each wave was implemented as a standalone refactor without searching `tests/` for assertions that referenced the old values. Because no process rule existed to prompt this search, the drift went unnoticed until CI was fully broken.

The fix required FIX-103 through FIX-107 (code + test restoration) and MNT-024 (regression baseline update) — roughly 5–7 WPs of remediation work for 5 refactors that should each have taken one extra step.

## Decision

**Tests must be updated alongside any refactor that changes externally-asserted behavior, in the same commit or PR as the refactor.**

### Definition: Externally-Asserted Behavior

A value or artifact is "externally-asserted" if any test file in `tests/` reads it, imports it, string-matches it, or checks for its presence. This includes:

- File paths and directory names
- WP/test/entity identifier prefixes and formats
- Version strings in source files, pyproject.toml, or build scripts
- Data file schemas and formats (CSV vs. JSONL, field names, key casing)
- Agent file names, headings, required sections, and content patterns
- Config keys, environment variable names, and CLI flags

### New Process Rule (added to `docs/work-rules/testing-protocol.md`)

> Before opening a PR that renames, moves, or reformats anything, the Developer MUST grep `tests/` for the old name/path/format and update every matching assertion. These test updates must be included in the same commit as the refactor — they are not separate work.

### Clarification of "Permanent"

"Test scripts are permanent" continues to mean that test files are never deleted. It does **not** mean assertions are immutable. The two rules coexist:

- The file is permanent.
- The assertions inside the file evolve with the code.

## Consequences

### Positive

- Refactors no longer silently break CI. Green tests remain green.
- The cost of a refactor is accurately reflected upfront — updating tests is part of the refactor, not a separate cleanup task.
- Developers who grep `tests/` before a refactor gain a free audit of what relies on the old interface, which surfaces unintended coupling.
- Future release pipelines run against a clean test suite; ADR-002 (Mandatory CI Test Gate) is enforceable without a permanent backlog of known failures.

### Negative

- Refactors that touch many test assertions take more time. This is intentional — it reflects the true cost of changing a widely-asserted interface.
- Developers must search `tests/` before every rename/move, not just when they remember to. This is a new habit that requires deliberate enforcement during review.

## Notes

The Version Bump Tests section of `testing-protocol.md` already provides an example of forward-looking test design: version tests read `src/launcher/config.py` dynamically instead of hardcoding the version. This pattern — **tests that read from source rather than asserting a fixed future value** — is the gold standard for high-churn values and should be adopted wherever feasible.

For values that cannot be made dynamic (e.g., directory structure, file presence, identifier formats), the grep-and-update rule in this ADR is the required fallback.
