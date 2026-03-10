# Testing Protocol

Comprehensive testing standards for all workpackages. This protocol defines the **minimum** testing requirements — agents and humans are expected to exceed it where applicable.

---

## Test Structure

- Tests live in `Project/tests/`, mirroring the source structure under `Project/`.
- Naming convention: `test_<module>.py` or `test_<module>_<function>.py`.
- Use `pytest` as the test framework.
- Each test function should test **one specific behaviour**.

## Test Categories

Every workpackage with code changes must include tests from the applicable categories:

| Category | When Required | Description |
|----------|---------------|-------------|
| **Unit** | All WPs with code changes | Test every public function/method in isolation |
| **Integration** | WPs involving cross-component interaction | Test how components work together |
| **Security** | All security-critical WPs (SAF-xxx) | One test validates the protection works, one test attempts to bypass it |
| **Regression** | Every bug fix | Test that reproduces the original bug and confirms the fix |
| **Cross-platform** | All safety features | Must pass on Windows, macOS, and Linux |

## Testing Workflow

### For Developers (during implementation)

1. Write tests **alongside** implementation, not after.
2. All new tests must pass before setting the WP to `Review`.
3. All **existing** tests must still pass (no regressions).
4. Log test runs in `docs/test-results/test-results.csv`.
5. Document test approach and results in the WP's `dev-log.md`.

### For Testers (during review)

1. Read the Developer's `dev-log.md` in the WP folder.
2. Run the full test suite — not just the new tests.
3. Add edge-case tests the Developer may have missed.
4. **Think beyond the protocol**: consider attack vectors, boundary conditions, race conditions, concurrency issues, invalid inputs, and platform-specific quirks.
5. Log all test runs in `docs/test-results/test-results.csv`.
6. Write findings in the WP's `test-report.md` (see format below).

## Test Result CSV

All test runs are logged in `docs/test-results/test-results.csv`.

| Column | Description |
|--------|-------------|
| ID | Test identifier (`TST-NNN`) |
| Test Name | Descriptive name of the test |
| Test Type | `Unit` / `Integration` / `Security` / `Regression` / `Cross-platform` |
| WP Reference | Workpackage ID this test relates to |
| Status | `Pass` / `Fail` / `Blocked` / `Skipped` |
| Run Date | ISO 8601 date (YYYY-MM-DD) |
| Environment | OS + Python version (e.g., "Windows 11 + Python 3.11") |
| Result | Brief outcome description |
| Notes | Additional context, failure details |

## Test Report Format

The Tester writes `test-report.md` in the workpackage folder (`docs/workpackages/<WP-ID>/test-report.md`):

```markdown
# Test Report — <WP-ID>

**Tester:** <name or agent>
**Date:** YYYY-MM-DD
**Iteration:** <number>

## Summary
<Brief overall assessment>

## Tests Executed
| Test | Type | Result | Notes |
|------|------|--------|-------|
| ... | ... | ... | ... |

## Bugs Found
- BUG-NNN: <title> (logged in docs/bugs/bugs.csv)

## TODOs for Developer
- [ ] <specific actionable item>
- [ ] <specific actionable item>

## Verdict
<PASS — mark WP as Done> OR <FAIL — return to Developer with details above>
```

## Minimum Standards

- **No workpackage moves to `Done` without logged test results** in both the CSV and the WP's test-report.md.
- **Security WPs** require both protection tests and bypass-attempt tests — no exceptions.
- **Every bug fix** requires a regression test proving the bug is fixed and cannot recur.
- The testing protocol is the **floor**, not the ceiling. Always seek additional failure modes.
