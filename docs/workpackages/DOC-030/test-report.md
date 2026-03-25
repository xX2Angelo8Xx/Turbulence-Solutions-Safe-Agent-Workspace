# Test Report — DOC-030

**Tester:** Tester Agent  
**Date:** 2026-03-25  
**Iteration:** 1

## Summary

The coordinator.agent.md template was correctly updated: all 10 agent names are PascalCase throughout the document (frontmatter, Delegation Table, How You Work, Persona, What You Do Not Do). The DOC-030-specific test suite (26 tests) passes cleanly. However, the PascalCase change introduces **9 regressions in `tests/DOC-029/`** — those tests hard-code lowercase agent names that DOC-030 intentionally changed. The Developer must update the DOC-029 test files before this WP can be approved.

## Tests Executed

| Test | Type | Result | TST-ID | Notes |
|------|------|--------|--------|-------|
| DOC-030 suite — 13 developer tests | Unit | PASS | TST-2177 | Frontmatter, Body, Delegation Table, Persona, What You Do Not Do |
| DOC-030 suite — 13 tester edge-case tests | Unit | PASS | TST-2177 | Full-file scan, frontmatter integrity, How You Work, file sanity |
| Full regression suite — DOC-029 tests | Regression | FAIL | TST-2178 | 9 tests broke; see Bugs Found below |

### DOC-030 Suite: 26/26 Passed

Classes and tests in `tests/DOC-030/`:

| Class | Tests |
|-------|-------|
| `TestFrontmatterAgentsCasing` (developer) | 3 |
| `TestBodyAtReferenceCasing` (developer) | 2 |
| `TestDelegationTable` (developer) | 2 |
| `TestPersonaSection` (developer) | 3 |
| `TestWhatYouDoNotDo` (developer) | 3 |
| `TestFullFileLowercaseScan` (tester) | 2 |
| `TestFrontmatterAgentListIntegrity` (tester) | 4 |
| `TestHowYouWorkSection` (tester) | 3 |
| `TestFileSanity` (tester) | 4 |
| **Total** | **26** |

### Regression Failures: 9 Tests in `tests/DOC-029/`

All 9 failures are caused by DOC-029 tests expecting **lowercase** agent names, which DOC-030 intentionally changed to PascalCase:

| Failing Test | File | Root Cause |
|---|---|---|
| `TestCoordinatorAgents::test_all_10_specialist_agents_present` | `test_doc029_coordinator_agent.py` | `EXPECTED_AGENTS` uses lowercase |
| `TestAgentsListExactCount::test_all_expected_agents_present` | `test_doc029_edge_cases.py` | `EXPECTED_AGENTS` uses lowercase |
| `TestAgentsListExactCount::test_no_unexpected_agents` | `test_doc029_edge_cases.py` | PascalCase flagged as "unexpected" |
| `TestAtSyntaxCrossReferences::test_at_syntax_used_for_programmer` | `test_doc029_edge_cases.py` | Looks for `@programmer` (lowercase) |
| `TestAtSyntaxCrossReferences::test_at_syntax_used_for_tester` | `test_doc029_edge_cases.py` | Looks for `@tester` (lowercase) |
| `TestAtSyntaxCrossReferences::test_at_syntax_used_for_planner` | `test_doc029_edge_cases.py` | Looks for `@planner` (lowercase) |
| `TestAtSyntaxCrossReferences::test_at_syntax_used_for_fixer` | `test_doc029_edge_cases.py` | Looks for `@fixer` (lowercase) |
| `TestAtSyntaxCrossReferences::test_at_syntax_used_for_criticist` | `test_doc029_edge_cases.py` | Looks for `@criticist` (lowercase) |
| `TestAtSyntaxCrossReferences::test_at_syntax_present_for_all_10_agents` | `test_doc029_edge_cases.py` | Looks for all 10 lowercase `@agent` refs |

## Bugs Found

None new. The regressions are a direct and expected consequence of fixing the bug (BUG-120). The DOC-029 tests simply need to be updated to reflect the now-correct PascalCase behavior.

## TODOs for Developer

- [ ] **Update `tests/DOC-029/test_doc029_coordinator_agent.py`** — change `EXPECTED_AGENTS` set from lowercase to PascalCase:
  ```python
  # OLD (incorrect after DOC-030)
  EXPECTED_AGENTS = {
      "programmer", "tester", "brainstormer", "researcher",
      "scientist", "criticist", "planner", "fixer", "writer", "prototyper"
  }
  # NEW (correct)
  EXPECTED_AGENTS = {
      "Programmer", "Tester", "Brainstormer", "Researcher",
      "Scientist", "Criticist", "Planner", "Fixer", "Writer", "Prototyper"
  }
  ```

- [ ] **Update `tests/DOC-029/test_doc029_edge_cases.py`** — apply the same PascalCase change to `EXPECTED_AGENTS`, AND update the `TestAtSyntaxCrossReferences` assertions from `@lowercase` to `@PascalCase`:
  ```python
  # In EXPECTED_AGENTS set — same change as above
  
  # In TestAtSyntaxCrossReferences methods, change references like:
  assert "@programmer" in self.body  →  assert "@Programmer" in self.body
  assert "@tester" in self.body      →  assert "@Tester" in self.body
  assert "@planner" in self.body     →  assert "@Planner" in self.body
  assert "@fixer" in self.body       →  assert "@Fixer" in self.body
  assert "@criticist" in self.body   →  assert "@Criticist" in self.body
  # Also update test_at_syntax_present_for_all_10_agents loop to use PascalCase
  ```

- [ ] After updating the DOC-029 tests, run the full `tests/DOC-029/` suite (all 48 tests must pass) and `tests/DOC-030/` suite (all 26 tests must pass).
- [ ] Re-submit for Tester review.

## Verdict

**FAIL — Return to Developer.**

The coordinator.agent.md template changes are correct and the DOC-030 test suite passes (26/26). However, 9 pre-existing tests in `tests/DOC-029/` now fail because they expected the old buggy lowercase names. The Developer must update those tests to use PascalCase before this WP can be marked Done.
