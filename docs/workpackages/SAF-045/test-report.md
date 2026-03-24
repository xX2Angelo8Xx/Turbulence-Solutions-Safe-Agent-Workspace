# Test Report — SAF-045

**Tester:** Tester Agent  
**Date:** 2026-03-24  
**Iteration:** 1

## Summary

SAF-045 verifies that `grep_search` is correctly scoped to the project folder and that VS Code `search.exclude` / `files.exclude` in `templates/coding/.vscode/settings.json` covers all three restricted zones. The Developer found and fixed a real gap (`**/NoAgentZone` was present in `search.exclude` but absent from `files.exclude`) and updated hashes accordingly. All 33 developer tests pass. 21 additional tester edge-case tests were added and pass.

Code quality, correctness, and defence-in-depth are all satisfactory. No new bugs found. No regressions introduced in the SAF-040–SAF-045 suite (337 tests, 0 failures).

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| TST-2082 | Integration | Fail (pre-existing) | Full suite run via `run_tests.py --full-suite`; 14 collection errors caused by missing `yaml` module unrelated to SAF-045 |
| TST-2083 | Security | Pass | Developer suite — 33 tests: includeIgnoredFiles deny, includePattern deny/allow, settings.json coverage |
| TST-2084 | Security | Pass | Tester edge cases — 21 tests: case variants, backslash paths, brace expansion, includeIgnoredFiles 0/2/mixed-case, empty pattern, filePath deny, non-dict tool_input, glob pattern checks |
| TST-2085 | Regression | Pass | SAF-040–SAF-045 suite: 337 passed, 0 failed, 2 xfailed |

## Tester Edge Cases Added

**File:** `tests/SAF-045/test_saf045_tester_edge_cases.py` — 21 tests

| Category | Tests |
|----------|-------|
| Case variants (NOAGENTZONE, .GITHUB, .VSCODE) | 3 deny |
| Windows backslash path (.github\\hooks, NoAgentZone\\secrets) | 2 deny |
| Brace expansion ({.github,project}/**, {project,NoAgentZone}/**) | 2 deny |
| Empty string includePattern | 1 allow |
| Security boundary: project-nested deny-zone names | 2 allow (project/.vscode/**, project/.github/**) |
| `includeIgnoredFiles` = 0, 2 (non-truthy integers) | 2 allow |
| `includeIgnoredFiles` = "True", "TRUE" (case-insensitive deny) | 2 deny |
| `includeIgnoredFiles` = "false", None | 2 allow |
| tool_input as non-dict | 1 allow (no crash) |
| Safe pattern + includeIgnoredFiles=True combined | 1 deny |
| filePath field pointing to .github zone | 1 deny |
| settings.json: NoAgentZone uses glob pattern (**/NoAgentZone) | 2 pass (files.exclude + search.exclude) |

**Security boundary note:** Tests confirmed that `project/.vscode/**` and `project/.github/**` are correctly *allowed*. These paths target directories inside the project folder (the agent's allowed zone), not the workspace-root restricted directories. The zone classifier is correctly designed to allow all content under the project folder; the restriction targets workspace-root `.github/`, `.vscode/`, and `NoAgentZone/`.

## Bugs Found

None. The gap already found and fixed by the Developer (missing `**/NoAgentZone` in `files.exclude`) was the sole issue. No new bugs discovered.

## Pre-existing Test Failures (not caused by SAF-045)

The following failures existed on `main` before this branch and are unrelated to SAF-045:

- `tests/SAF-022/` — 3 `ValueError: too many values to unpack` in tuple iteration (pre-existing test bug)
- `tests/SAF-025/test_saf025_hash_sync.py::test_no_pycache_in_templates_coding` — `__pycache__` pollution from test imports (pre-existing)
- `tests/FIX-010`, `tests/FIX-011`, `tests/FIX-029`, `tests/INS-013`–`INS-017` — `ModuleNotFoundError: No module named 'yaml'` (pre-existing, unrelated)

## TODOs for Developer

None.

## Verdict

**PASS — mark WP as Done.**

All acceptance criteria satisfied:
- AC 4: `grep_search` verified project-folder-only ✓
- AC 5: `search.exclude` covers all restricted zones ✓  
- AC 7: No search tool leaks paths from restricted zones ✓

The gap fix (missing `**/NoAgentZone` from `files.exclude`) is correctly applied and verified. No regressions.
