# ADR-002: Mandatory CI Test Gate Before Release Builds

**Status:** Active  
**Date:** 2026-04-03  
**Related WPs:** N/A (structural overhaul)  
**Supersedes:** None  
**Superseded by:** None

## Context

The project has 3,961+ tests but zero CI automation. Tests were only executed manually by Developer and Tester agents. The release workflow (`release.yml`) built artifacts without running any tests, meaning broken security code could ship if agents skipped testing.

## Decision

1. A new `test.yml` workflow runs the full test suite on every push to main and every PR, across Windows/macOS/Linux.
2. The `release.yml` workflow now includes a `run-tests` job that must pass before platform builds begin.
3. A regression baseline (`tests/regression-baseline.json`) tracks known failures — CI flags any NEW failure as a regression.

## Consequences

- **Positive:** No release can be built without passing tests
- **Positive:** Cross-platform regressions are caught automatically
- **Positive:** Known failures are tracked explicitly rather than ignored
- **Negative:** CI run time increases (test suite must complete before builds start)
- **Negative:** Flaky tests may block releases — requires baseline maintenance

## Notes

Golden-file snapshot tests for `security_gate.py` decisions are stored in `tests/snapshots/security_gate/`. These catch any security decision change (allow↔deny) between versions.
