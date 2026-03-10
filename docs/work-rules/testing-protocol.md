# Testing Protocol

Comprehensive testing standards for all workpackages. This protocol defines the **minimum** testing requirements — agents and humans are expected to exceed it where applicable.

---

## Test Structure

- Tests live in `tests/<WP-ID>/`, one subfolder per workpackage.
  - Example: `tests/INS-001/test_ins001_structure.py`, `tests/SAF-001/test_saf001_security_gate.py`
- Naming convention: `test_<module>.py` or `test_<module>_<function>.py`.
- Use `pytest` as the test framework.
- Each test function should test **one specific behaviour**.
- Run tests using the workspace virtual environment: `.venv\Scripts\python -m pytest tests/`

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

1. Create `tests/<WP-ID>/` folder at the start of every workpackage.
2. Write tests **alongside** implementation, not after.
3. All new tests must pass before setting the WP to `Review`.
4. All **existing** tests must still pass (no regressions).
5. Log test runs in `docs/test-results/test-results.csv`.
6. Document test approach and results in the WP's `dev-log.md`.
7. **Never use interactive constructs** — no `input()`, no commands that await stdin, no `[y/n]` prompts.

### For Testers (during review)

1. Read the Developer's `dev-log.md` in the WP folder.
2. Run the full test suite — not just the new tests: `.venv\Scripts\python -m pytest tests/`
3. Add edge-case tests the Developer may have missed — place them in `tests/<WP-ID>/`.
4. **Think beyond the protocol**: consider attack vectors, boundary conditions, race conditions, concurrency issues, invalid inputs, and platform-specific quirks.
5. Log all test runs in `docs/test-results/test-results.csv`.
6. Write findings in the WP's `test-report.md` (see format below).
7. **Never run commands that require user input** — all test execution must be non-interactive.

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

---

## Test Script Preservation

Test scripts are **permanent project artifacts**. They are not throw-away code.

- The final test script for each workpackage (`tests/<WP-ID>/test_<name>.py`) **must never be deleted** after the WP reaches `Done`.
- These scripts serve as regression tests for every future version of the project.
- Minimize one-time / disposable code. If temporary test scaffolding is needed during development, remove it before handoff — the committed test script must be clean and reusable.
- The results produced by the final test script are what is archived in `docs/test-results/test-results.csv`. Future releases run the same scripts; if output changes, it is a regression.
- When adding edge-case tests during Tester review, add them to the same `tests/<WP-ID>/` file — do not create separate throw-away scripts.
