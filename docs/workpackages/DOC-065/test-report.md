# Test Report — DOC-065: Batch template documentation fixes for v3.4.0

**WP ID:** DOC-065
**Branch:** DOC-065/template-doc-fixes
**Tester:** Tester Agent
**Date:** 2026-04-07
**Verdict:** ❌ FAIL — 6 new regressions in DOC-064 tests not added to regression baseline

---

## Summary

All 20 DOC-065 targeted tests pass. The 5 documented changes are correctly implemented in the template files. However, DOC-065 introduces **6 genuine regressions** in `tests/DOC-064/` by removing `isBackground:true` from the agent-workbench Blocked Commands table without adding those DOC-064 tests to `tests/regression-baseline.json`.

| Verification Item | Result |
|-------------------|--------|
| Branch: DOC-065/template-doc-fixes | ✅ PASS |
| dev-log.md exists and non-empty | ✅ PASS |
| DOC-065 targeted suite (20 tests) | ✅ 20/20 PASS |
| Full suite regression check | ❌ FAIL — 6 DOC-064 regressions not in baseline |
| Validate workspace | ✅ PASS |

---

## Content Verification — All 5 Changes

### Change 1: isBackground:true removed from Blocked Commands (agent-workbench only)
- ✅ `isBackground:true` row removed from agent-workbench AGENT-RULES.md `### Blocked Commands` table
- ✅ clean-workspace AGENT-RULES.md still documents `isBackground:true` workaround (unchanged)

### Change 2: grep_search includePattern required (both templates)
- ✅ agent-workbench AGENT-RULES.md: `` `includePattern` is required `` present
- ✅ clean-workspace AGENT-RULES.md: `` `includePattern` is required `` present
- ✅ clean-workspace no longer claims "Scoped to `{{PROJECT_NAME}}/` by default"

### Change 3: Terminal navigation lock-in documented (both AGENT-RULES + copilot-instructions)
- ✅ agent-workbench AGENT-RULES.md Blocked Commands table includes `cd ..` / `Set-Location ..` / `Push-Location ..` outward navigation row
- ✅ clean-workspace AGENT-RULES.md Section 4 documents terminal navigation restriction
- ✅ agent-workbench copilot-instructions.md Known Tool Limitations includes outward navigation/Push-Location entry
- ✅ clean-workspace copilot-instructions.md Known Tool Limitations includes outward navigation/Push-Location entry

### Change 4: includeIgnoredFiles:true restriction (both templates)
- ✅ agent-workbench AGENT-RULES.md mentions `includeIgnoredFiles` restriction
- ✅ clean-workspace AGENT-RULES.md Known Tool Workarounds explicitly warns against `` `includeIgnoredFiles: true` in `grep_search` ``

### Change 5: list_dir .github/ scope clarification (both templates)
- ✅ agent-workbench AGENT-RULES.md: `subdirectory listings` allowed and `.github/instructions/` example present
- ✅ agent-workbench AGENT-RULES.md: `top-level `.github/` listing is denied` text present
- ✅ clean-workspace AGENT-RULES.md: same two assertions pass

### MANIFEST.json regenerated
- ✅ Both MANIFEST.json files exist
- ✅ Both MANIFEST.json files track AGENT-RULES.md

---

## Regression Analysis

### DOC-065 targeted suite: 20 passed ✅

### Full suite: 184 failed — 6 NEW regressions ❌

All other failures in the full suite are either:
- Pre-existing baseline failures (83 confirmed matches)
- Pre-existing test isolation flakiness (verified by running in isolation on both `main` and DOC-065 branch — all pass in isolation)

**NEW regressions introduced by DOC-065** (6 total, confirmed by running DOC-064 tests in isolation on both branches):

| Test | Root Cause |
|------|-----------|
| `tests/DOC-064/test_doc064_background_terminal_docs.py::test_agent_workbench_agent_rules_has_isBackground` | DOC-065 removed `isBackground:true` from agent-workbench Blocked Commands; DOC-064 test asserts it must be present |
| `tests/DOC-064/test_doc064_background_terminal_docs.py::test_agent_workbench_agent_rules_use_instead_guidance` | Same — `timeout` guidance was in the blocked-commands row, now removed |
| `tests/DOC-064/test_doc064_background_terminal_docs.py::test_agent_workbench_agent_rules_blocked_commands_section` | Same — `isBackground:true` absent from Blocked Commands section |
| `tests/DOC-064/test_doc064_background_terminal_docs.py::test_agent_workbench_agent_rules_security_gate_reason` | Same — "Security gate cannot validate background command streams" text removed |
| `tests/DOC-064/test_doc064_tester_edge_cases.py::test_agent_workbench_agent_rules_isBackground_in_blocked_section` | Same — `isBackground:true` absent from Blocked Commands section |
| `tests/DOC-064/test_doc064_tester_edge_cases.py::test_agent_workbench_agent_rules_single_isBackground_entry` | Same — expects count == 1, finds 0 |

**Root cause**: DOC-065 intentionally supersedes DOC-064 by removing `isBackground:true` from blocked commands (because the tool now works). This is correct behavior, but the Developer did not add the 6 DOC-064 tests to `tests/regression-baseline.json` as known stale failures. Per the Developer Pre-Handoff Checklist, all tests must pass or be registered in the baseline.

---

## Bugs Logged

- BUG filed for the 6 DOC-064 regression test failures (see bugs.jsonl)

---

## TODOs for Developer (Actionable)

**1. Add 6 DOC-064 tests to `tests/regression-baseline.json`**

Add these 6 entries to the `known_failures` dictionary:

```json
"tests.DOC-064.test_doc064_background_terminal_docs.test_agent_workbench_agent_rules_has_isBackground": {
  "reason": "DOC-065 supersedes DOC-064: isBackground:true removed from agent-workbench Blocked Commands table because background terminal now works. DOC-064 test asserts the old presence of the block which is intentionally gone."
},
"tests.DOC-064.test_doc064_background_terminal_docs.test_agent_workbench_agent_rules_use_instead_guidance": {
  "reason": "DOC-065 supersedes DOC-064: timeout guidance was part of the isBackground:true blocked-commands row, removed because background terminal now works."
},
"tests.DOC-064.test_doc064_background_terminal_docs.test_agent_workbench_agent_rules_blocked_commands_section": {
  "reason": "DOC-065 supersedes DOC-064: isBackground:true blocked commands row removed from agent-workbench AGENT-RULES as it now works."
},
"tests.DOC-064.test_doc064_background_terminal_docs.test_agent_workbench_agent_rules_security_gate_reason": {
  "reason": "DOC-065 supersedes DOC-064: security gate reason text removed because isBackground:true is no longer a blocked command."
},
"tests.DOC-064.test_doc064_tester_edge_cases.test_agent_workbench_agent_rules_isBackground_in_blocked_section": {
  "reason": "DOC-065 supersedes DOC-064: isBackground:true removed from Blocked Commands section in agent-workbench AGENT-RULES."
},
"tests.DOC-064.test_doc064_tester_edge_cases.test_agent_workbench_agent_rules_single_isBackground_entry": {
  "reason": "DOC-065 supersedes DOC-064: isBackground:true entry count in Blocked Commands section is now 0, not 1, because the block was intentionally removed."
}
```

Update `_count` from 213 to 219 and `_updated` to `"2026-04-07"`.

**2. Rerun the full test suite after updating the baseline**

```powershell
.venv\Scripts\python.exe -m pytest tests/ -q --tb=no 2>&1 | Select-Object -Last 10
```

Confirm the 6 DOC-064 failures now appear as baseline (not new) and no other NEW failures exist.

**3. Recommit and push**

```powershell
git add tests/regression-baseline.json
git commit -m "DOC-065: Add DOC-064 superseded tests to regression baseline"
git push origin DOC-065/template-doc-fixes
```

**4. Return WP to Review**
Set WP status back to `Review` and hand off to Tester.

---

## WP Status

Set to: **In Progress** (returned to Developer)
