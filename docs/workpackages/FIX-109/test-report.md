# Test Report — FIX-109: Update FIX-073 tests to match current template

**Tester:** Tester Agent  
**Date:** 2026-04-05  
**WP Status:** PASS → Done  
**Branch:** FIX-109/update-fix073-tests-to-match-current-template

---

## Scope

Review and test the Developer's updates to `tests/FIX-073/` test files and `tests/regression-baseline.json`, ensuring they match the current 7-agent template.

---

## Verification Points

| Check | Result |
|-------|--------|
| `AGENT_FILES` in both test files has exactly 7 agents | PASS |
| Removed agents (scientist, criticist, fixer, writer, prototyper) absent from both test files | PASS |
| Planner tools check uses `vscode/askQuestions` (not bare `ask`) | PASS |
| Coordinator uses both Opus + Sonnet model list | PASS |
| Planner uses Opus; programmer/brainstormer/tester/researcher/workspace-cleaner use Sonnet | PASS |
| All 32 FIX-073 entries removed from `regression-baseline.json` | PASS (0 FIX-073 entries found) |
| `_count` in baseline matches actual `known_failures` count | PASS (both = 152) |
| `test_frontmatter_has_exactly_four_keys` allows superset (coordinator has 6 keys) | PASS |

---

## Test Execution

### FIX-073 Tests (35 tests)

```
python -m pytest tests/FIX-073/ -v
35 passed in 0.34s
```

All tests pass. Covers: 7 agent tool assertions, 7 agent model assertions, no-old-tool-names check, no-fetch_webpage check, planner-specific checks, README example checks, and edge cases (file existence, type checks, frontmatter key requirements).

### FIX-109 Tests (8 new tests — TST-2637)

```
python -m pytest tests/FIX-109/ -v
8 passed in 0.23s
```

New tests verify:
- `regression-baseline.json` has no FIX-073 entries
- `_count` matches `known_failures` length
- Both FIX-073 test files have exactly 7 entries in `AGENT_FILES`
- Removed agents not referenced in either test file
- `vscode/askQuestions` used (not bare `ask`) in frontmatter test
- Planner's `EXPECTED_TOOLS` does not contain bare `"ask"`

### Full Suite

```
python -m pytest tests/ -q --tb=no
8897 passed, 79 failed, 345 skipped, 4/5 xfailed, 66 errors, 218 warnings
```

**Regression analysis:** All 79 failures are present in `tests/regression-baseline.json`. Zero new regressions introduced by FIX-109.

---

## Workspace Validation

```
python scripts/validate_workspace.py --wp FIX-109
All checks passed.
```

---

## Edge Cases Examined

1. **Coordinator dual-model**: coordinator has `["Claude Opus 4.6 (copilot)", "Claude Sonnet 4.6 (copilot)"]` — test correctly uses `COORDINATOR_MODEL` list, not the single-value `OPUS_MODEL`.
2. **workspace-cleaner hyphen in key**: Python dict key `"workspace-cleaner"` — handled correctly via dict access, no naming issues.
3. **Frontmatter key count flex**: The `test_frontmatter_has_exactly_four_keys` test was correctly changed from exact-4-key check to subset check, accommodating coordinator (6 keys) and workspace-cleaner (5 keys).
4. **Removed entry count**: The dev-log claims 32 FIX-073 entries removed. Baseline has no FIX-073 entries — confirmed correct.
5. **No remaining references to old agents**: `grep` confirmed none of scientist, criticist, fixer, writer, or prototyper appear in either FIX-073 test file.

---

## Verdict

**PASS**

All verification points confirmed. 35 FIX-073 tests pass. 8 new FIX-109 tests pass. No regressions. Workspace validates clean.
