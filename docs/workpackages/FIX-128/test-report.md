# Test Report — FIX-128

**Tester:** Tester Agent  
**Date:** 2026-04-07  
**Test Run ID:** TST-2767  
**Verdict:** ❌ FAIL

---

## Summary

FIX-128 moves `AGENT-RULES.md` from `Project/` to `Project/AgentDocs/` in the
agent-workbench template and updates cross-references. The 9 FIX-128 acceptance
tests all pass. However, **6 new regressions** were introduced by incomplete
post-edit steps:

| Bug | Root Cause | Tests Failing |
|-----|-----------|---------------|
| BUG-216 | MANIFEST.json regenerated before all agent file edits completed | 4 |
| BUG-217 | `FIX-117 _agent_rules_path()` not updated to AgentDocs path | 2 |

---

## Test Results

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

### Impacted test areas — PASS

- `tests/FIX-119/` — 18 passed ✅
- `tests/FIX-124/` — passed ✅
- `tests/DOC-047/` — 13 passed ✅ (all 10 baseline entries now pass — correct removal)
- `tests/DOC-045/` — 41 passed, 1 failed (pre-existing in baseline) ✅
- `tests/FIX-123/` — passed ✅
- `tests/DOC-009/` — passed ✅
- `tests/DOC-064/` — 1 FAILED (BUG-216) ❌

### Regressions Introduced by FIX-128

#### BUG-216: MANIFEST.json stale (4 failures)

**Root cause:** The MANIFEST.json was regenerated before the 8 agent files
(`.github/agents/*.md`) received their final content. The hashes in
`templates/agent-workbench/.github/hooks/scripts/MANIFEST.json` do not match
the current on-disk content of these files.

Evidence:
```
generate_manifest.py --check:
  CHANGED:   .github/agents/brainstormer.agent.md
  CHANGED:   .github/agents/coordinator.agent.md
  CHANGED:   .github/agents/planner.agent.md
  CHANGED:   .github/agents/programmer.agent.md
  CHANGED:   .github/agents/README.md
  CHANGED:   .github/agents/researcher.agent.md
  CHANGED:   .github/agents/tester.agent.md
  CHANGED:   .github/agents/workspace-cleaner.agent.md
8 discrepancy(ies)
```

Failing tests:
- `tests/DOC-064/test_doc064_tester_edge_cases.py::test_agent_workbench_manifest_is_current`
- `tests/FIX-114/test_fix114_ci_regressions.py::test_manifest_check_passes`
- `tests/FIX-122/test_fix122_manifest_relocation.py::test_generate_manifest_check_agent_workbench`
- `tests/MNT-029/test_mnt029_manifest.py::test_manifest_check_exits_clean`

#### BUG-217: FIX-117 _agent_rules_path() not updated (2 failures)

**Root cause:** `tests/FIX-117/test_fix117_get_changed_files_allow.py` class
`TestAgentRulesDocumentation._agent_rules_path()` returns the old path
`Project/AGENT-RULES.md`. The file has been moved to `Project/AgentDocs/AGENT-RULES.md`
by FIX-128. The dev-log listed only 4 test files updated; this file was missed.

Evidence:
```
FileNotFoundError: 'templates/agent-workbench/Project/AGENT-RULES.md'
```

Failing tests:
- `tests/FIX-117/test_fix117_get_changed_files_allow.py::TestAgentRulesDocumentation::test_agent_rules_documents_get_changed_files`
- `tests/FIX-117/test_fix117_get_changed_files_allow.py::TestAgentRulesDocumentation::test_agent_rules_marks_get_changed_files_as_allowed`

Note: Other failing FIX-117 tests (`TestAlwaysAllowToolsMembership`, `TestDecideGetChangedFiles`) are pre-existing failures in the regression baseline — they were not introduced by FIX-128.

---

## Regression Baseline Analysis

- Baseline before FIX-128 (main): 250 entries  
- Baseline after FIX-128: 213 entries (37 removed)  
- DOC-045 removal: 27 entries correctly removed (tests now pass with AgentDocs location)  
- DOC-047 removal: 10 entries correctly removed (tests now pass)  
- Full suite: 183 failed, 84 in new baseline → 99 not in baseline, but 94 of these are pre-existing failures not tracked in either baseline (confirmed via git show main:tests/regression-baseline.json)

**New regressions introduced by this WP: 6** (BUG-216: 4, BUG-217: 2)

---

## Security Review

No security concerns. This is a pure file move + reference update with no code changes to security-critical modules.

---

## TODO for Developer

### TODO-1 (BLOCKING): Regenerate MANIFEST.json with correct hashes

After all agent file edits are finalized, run:

```powershell
.venv\Scripts\python.exe scripts/generate_manifest.py
```

Then verify with:
```powershell
.venv\Scripts\python.exe scripts/generate_manifest.py --check
```

The check must return exit code 0 before re-submitting.

### TODO-2 (BLOCKING): Update FIX-117 _agent_rules_path() to AgentDocs path

In `tests/FIX-117/test_fix117_get_changed_files_allow.py`, update the
`TestAgentRulesDocumentation._agent_rules_path()` method:

**Before:**
```python
def _agent_rules_path(self) -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "templates"
        / "agent-workbench"
        / "Project"
        / "AGENT-RULES.md"
    )
```

**After:**
```python
def _agent_rules_path(self) -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "templates"
        / "agent-workbench"
        / "Project"
        / "AgentDocs"
        / "AGENT-RULES.md"
    )
```

After both fixes, run the full test suite and confirm all 6 previously-failing
tests now pass before re-submitting for review.
