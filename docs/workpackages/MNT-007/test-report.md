# Test Report — MNT-007

**Tester:** Tester Agent
**Date:** 2026-04-03
**Iteration:** 1

## Summary

MNT-007 standardizes the pre-handoff test command chain across three documentation
files. All acceptance criteria are met. The banned pattern `pytest tests/ -v` returns
zero matches in all agent and work-rules files. All three target files mandate
`scripts/run_tests.py`. The `add_test_result.py` script is correctly labeled as
fallback in both the developer checklist and the testing-protocol.

The Developer's 13 tests all pass. 6 tester edge-case tests were added and all
19 MNT-007 tests pass. The full regression suite has 633 pre-existing failures
that were confirmed to exist on `main` before MNT-007 was branched — no regressions
introduced.

## Verification Checks

| Check | Result |
|-------|--------|
| `agent-workflow.md` Step 5 mandates `scripts/run_tests.py` | PASS |
| `developer.agent.md` pre-handoff checklist references `run_tests.py` | PASS |
| `developer.agent.md` pre-handoff checklist has `add_test_result.py` as fallback | PASS |
| `testing-protocol.md` labels `add_test_result.py` as fallback | PASS |
| Grep `pytest tests/ -v` in `.github/agents/` — 0 matches | PASS |
| Grep `pytest tests/ -v` in `docs/work-rules/` — 0 matches | PASS |
| `scripts/run_tests.py` script exists on disk | PASS |
| `scripts/add_test_result.py` script exists on disk | PASS |

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| MNT-007: full regression suite (TST-2469) | Regression | Pre-existing failures only | 7799 passed, 633 failed (all pre-existing on main), 37 skipped |
| MNT-007: targeted suite (TST-2470) | Unit | PASS | 19 passed in 0.30s |
| test_add_test_result_not_primary_checklist_item | Unit | PASS | developer.agent.md checklist |
| test_run_tests_appears_before_add_test_result_in_checklist | Unit | PASS | ordering verified |
| test_testing_protocol_add_test_result_labeled_fallback | Unit | PASS | TST-ID section checked |
| test_developer_agent_no_raw_pytest | Unit | PASS | 0 banned pattern matches |
| test_tester_agent_no_raw_pytest | Unit | PASS | 0 banned pattern matches |
| test_agent_workflow_no_raw_pytest | Unit | PASS | 0 banned pattern matches |
| test_testing_protocol_no_raw_pytest | Unit | PASS | 0 banned pattern matches |
| test_all_work_rules_no_raw_pytest | Unit | PASS | all work-rules/*.md clean |
| test_agent_workflow_mentions_run_tests | Unit | PASS | present in file |
| test_developer_agent_mentions_run_tests | Unit | PASS | present in file |
| test_testing_protocol_mentions_run_tests_mandatory | Unit | PASS | scripts/run_tests.py present |
| test_agent_workflow_step5_mentions_run_tests | Unit | PASS | Step 5 row found and contains reference |
| test_developer_agent_checklist_references_run_tests | Unit | PASS | checklist item confirmed |
| test_run_tests_script_exists (Tester) | Unit | PASS | scripts/run_tests.py exists |
| test_testing_protocol_tester_workflow_mandates_run_tests (Tester) | Unit | PASS | For Testers section verified |
| test_testing_protocol_full_suite_flag_mentioned_for_testers (Tester) | Unit | PASS | --full-suite flag present |
| test_no_raw_pytest_v_variant_in_developer_agent (Tester) | Unit | PASS | reversed flag order also absent |
| test_agent_workflow_step5_contains_mandatory_label (Tester) | Unit | PASS | 'mandatory' confirmed |
| test_add_test_result_script_exists (Tester) | Unit | PASS | scripts/add_test_result.py exists |

## Regression Analysis

- **Full suite:** 633 failures, 7799 passed
- **Pre-existing baseline:** 680 known failures
- **New failures vs baseline format:** 51 items appear to be pre-existing (confirmed by
  running same tests against `main` branch before MNT-007 changes — same failures on main)
- **MNT-007-related regressions:** 0

The 51 failures not yet in the formal baseline are pre-existing issues in DOC-023/024/026/027/028,
FIX-004/009/028/062/063/073/077/078/088/090, INS-006/007/013/019/029, SAF-010/056, and DOC-039/042.
None of them touch the files modified by MNT-007. They existed on `main` before this branch.

## Bugs Found

None.

## TODOs for Developer

None — WP passes all criteria.

## Verdict

**PASS — mark WP as Done.**

All acceptance criteria verified. 19/19 MNT-007 tests pass. Zero regressions introduced.
Documentation changes are consistent, complete, and correct.
