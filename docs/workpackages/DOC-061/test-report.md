# Test Report — DOC-061

**Tester:** Tester Agent
**Date:** 2026-04-06
**Iteration:** 1

## Summary

PASS. All 24 tests pass (17 Developer + 7 Tester edge-cases). Both AGENT-RULES.md copies contain the required Subagent Budget Sharing warning in §6 and are byte-identical in that section. BUG-198 is confirmed fixed. No regressions introduced. Full suite failures (94 failed, 66 errors) are all pre-existing known baselines (INS-015/016 from MNT-027/ADR-010 macOS/Linux job removal; others in regression-baseline.json) — zero new failures from this WP.

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| TST-2678: DOC-061 targeted suite (Developer) | Unit | Pass | 17/17 passed — Developer pre-handoff run |
| TST-2679: DOC-061 full regression suite | Regression | Pass (known failures only) | 9007 passed, 344 skipped, 5 xfailed, 94 failed, 66 errors — all failures are pre-existing baselines |
| TST-2680: DOC-061 targeted suite (Tester) | Unit | Pass | 24/24 passed — 17 developer + 7 tester edge-cases |

## Code Review Findings

### templates/agent-workbench/Project/AGENT-RULES.md

- §6 `Session-Scoped Denial Counter` is present ✅
- `### Subagent Budget Sharing` subsection added inside §6 ✅
- `> **Warning:**` callout block present ✅
- Documents that subagent denials count against the parent session budget ✅
- Rule 1: Instruct subagents not to probe denied zones (specific zones named) ✅
- Rule 2: No bypass via subagent delegation ✅
- Rule 3: Monitor budget before spawning ✅
- Rule 4: Coordinator/Orchestrator pattern is high-risk ✅
- `runSubagent` tool explicitly named ✅

### templates/agent-workbench/Project/AgentDocs/AGENT-RULES.md (mirror)

- Confirmed byte-identical §6 content ✅
- All bullet checks above apply identically ✅

### MANIFEST.json

- Regenerated to reflect AGENT-RULES.md modifications ✅

## Edge-Case Analysis

| Concern | Finding |
|---------|---------|
| Bypass via subagent delegation | Rule 2 explicitly states "Delegating a task to a subagent does not change zone restrictions" ✅ |
| Low-budget parent spawning subagents | Rule 3 addresses budget monitoring before spawning ✅ |
| Coordinator/Orchestrator budget exhaustion | Rule 4 identifies multi-subagent patterns as high-risk ✅ |
| Mirror copy drift | `test_both_copies_section_6_are_identical` guards against this ✅ |
| Warning placement (must be inside §6, not after §7) | `test_subagent_warning_is_inside_section_6` verifies positional correctness ✅ |
| Specific zones named in instructions | `.github/hooks/`, `.vscode/`, `NoAgentZone/` all listed in Rule 1 ✅ |
| `runSubagent` tool identified | Present in both copies ✅ |

## Tester Edge-Case Tests Added

| Test | Purpose |
|------|---------|
| `test_primary_warning_mentions_bypass` | Guards against removing the no-bypass rule |
| `test_mirror_warning_mentions_bypass` | Mirror guard |
| `test_primary_warning_mentions_specific_zones` | Guards that specific denied zones are listed |
| `test_mirror_warning_mentions_specific_zones` | Mirror guard |
| `test_primary_warning_mentions_runsubagent` | Guards that the affected tool is identified |
| `test_mirror_warning_mentions_runsubagent` | Mirror guard |
| `test_subagent_warning_is_inside_section_6` | Guards that warning is not accidentally moved outside §6 |

## Bugs Found

None.

## ADR Conflicts

No ADRs in `docs/decisions/index.jsonl` relate to denial counter documentation or subagent budget behavior.

## Checklist

- [x] `dev-log.md` exists and is non-empty
- [x] `test-report.md` written by Tester
- [x] Test files exist in `tests/DOC-061/` (24 tests)
- [x] Test results logged via `scripts/run_tests.py` (TST-2679, TST-2680)
- [x] No bugs found during testing; pre-existing BUG-198 closed via `scripts/update_bug_status.py`
- [x] `scripts/validate_workspace.py --wp DOC-061` returns exit code 0
- [x] Branch: `DOC-061/subagent-denial-docs` ✅

## Verdict

**PASS** — WP set to `Done`.
