# Test Report — FIX-128

**Tester:** Tester Agent  
**Date:** 2026-04-07  
**Test Run IDs:** TST-2767 (Iter 1 — FAIL), TST-2769 (Iter 2 — PASS)  
**Verdict:** ✅ PASS (Iteration 2)

---

## Summary

FIX-128 moves `AGENT-RULES.md` from `Project/` to `Project/AgentDocs/` in the
agent-workbench template and updates all cross-references. Both defects found in
Iteration 1 have been fully resolved in Iteration 2.

### Iteration 1 defects — now resolved

| Bug | Status | Evidence |
|-----|--------|---------|
| BUG-216 | ✅ Closed | `generate_manifest.py --check` returns exit 0, 0 discrepancies |
| BUG-217 | ✅ Closed | `TestAgentRulesDocumentation` both tests pass; path returns `AgentDocs/AGENT-RULES.md` |

All 6 previously-failing tests now pass. No new regressions were introduced.

---

## Test Results — Iteration 2 (TST-2769)

### FIX-128 acceptance tests — PASS (9/9)

All 9 tests in `tests/FIX-128/test_fix128_move_agent_rules.py` pass:

- `test_agent_rules_exists_in_agentdocs` ✅
- `test_agent_rules_not_at_project_root` ✅
- `test_clean_workspace_agent_rules_untouched` ✅
- `test_project_readme_references_new_path` ✅
- `test_project_readme_no_bare_agent_rules_link` ✅
- `test_copilot_instructions_references_new_path` ✅
- `test_workspace_readme_references_new_path` ✅
- `test_manifest_has_new_key` ✅
- `test_manifest_no_old_key` ✅

### BUG-216 fix verification — PASS

`generate_manifest.py --check` returns exit 0 with message "Manifest is up to date."
0 discrepancies for all 8 previously-stale `.github/agents/*.md` files.

Previously-failing tests now pass:
- `tests/DOC-064/test_doc064_tester_edge_cases.py::test_agent_workbench_manifest_is_current` ✅
- `tests/FIX-114/test_fix114_ci_regressions.py::test_manifest_check_passes` ✅
- `tests/FIX-122/test_fix122_manifest_relocation.py::test_generate_manifest_check_agent_workbench` ✅
- `tests/MNT-029/test_mnt029_manifest.py::test_manifest_check_exits_clean` ✅

### BUG-217 fix verification — PASS

`tests/FIX-117/test_fix117_get_changed_files_allow.py::TestAgentRulesDocumentation`
`_agent_rules_path()` now returns `... / "Project" / "AgentDocs" / "AGENT-RULES.md"`.

Previously-failing tests now pass:
- `TestAgentRulesDocumentation::test_agent_rules_documents_get_changed_files` ✅
- `TestAgentRulesDocumentation::test_agent_rules_marks_get_changed_files_as_allowed` ✅

### Impacted test areas — PASS

- `tests/FIX-119/` — all passed ✅
- `tests/FIX-123/` — passed ✅
- `tests/DOC-009/` — passed ✅
- `tests/DOC-047/` — 13 passed ✅
- `tests/DOC-045/` — 41 passed, 1 failed (pre-existing baseline) ✅
- `tests/MNT-029/` — passed ✅

### Pre-existing baseline failures (unrelated to FIX-128)

The following 5 failures are all registered in `tests/regression-baseline.json`
and were NOT introduced by this WP:

1. `FIX-117::TestAlwaysAllowToolsMembership::test_get_changed_files_is_in_always_allow` — baseline
2. `FIX-117::TestAlwaysAllowToolsMembership::test_validate_get_changed_files_removed` — baseline
3. `FIX-117::TestDecideGetChangedFiles::test_allowed_when_git_at_workspace_root` — baseline
4. `FIX-117::TestDecideGetChangedFiles::test_allowed_with_both_git_dirs` — baseline
5. `DOC-045::TestDeletedFilesAbsent::test_old_project_readme_deleted` — baseline

Introduced by FIX-123 superseding FIX-117. Unrelated to this WP.

---

## Regression Baseline Analysis

- Baseline before FIX-128 (main): 250 entries  
- Baseline after FIX-128: 213 entries (37 removed)  
- DOC-045 removal: 27 entries correctly removed (tests now pass with AgentDocs location)  
- DOC-047 removal: 10 entries correctly removed (tests now pass)  

**New regressions introduced by this WP: 0** (both BUG-216 and BUG-217 fully resolved in iteration 2)

---

## Security Review

No security concerns. This is a pure file move + reference update with no code changes to security-critical modules.

---

## Verdict: PASS

All WP acceptance criteria met. Both Iteration 1 blocking defects (BUG-216, BUG-217) resolved.
No new regressions. `validate_workspace.py --wp FIX-128` returns exit 0.
