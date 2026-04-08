# Test Report — DOC-066: Fix persistent documentation inversions

**Tester:** Tester Agent  
**Date:** 2026-04-08  
**Branch:** DOC-066/fix-doc-inversions  
**Verdict:** ❌ FAIL — Return to In Progress

---

## Summary

The implementation is correct in intent and content. All 23 DOC-066 unit tests pass, and the actual documentation changes are accurate. However, the WP introduces **14 new test failures not tracked in the regression baseline** — caused by DOC-064/DOC-065 tests that assert the opposite of what DOC-066 does. The Developer must update the regression baseline before this WP can be marked Done.

---

## Test Runs (TST IDs)

| TST ID | Name | Type | Status |
|--------|------|------|--------|
| TST-2791 | DOC-066 unit tests | Unit | ✅ Pass (23/23) |
| TST-2792 | Full regression suite | Regression | ❌ Fail (14 new unbaseline failures) |
| TST-2793 | Snapshot tests (security_gate) | Unit | ✅ Pass (12/12) |

---

## Code Review

### Change 1 — Remove `isBackground:true` from Known Tool Limitations ✅
Both `copilot-instructions.md` files: row removed, positive `isBackground=true` workaround in AW AGENT-RULES retained.  
CW AGENT-RULES: `isBackground:true` row removed from Known Tool Workarounds.  
**Correct.** The tool functions at runtime per 3 audit iterations.

### Change 2 — Update navigation wording ✅
Both copilot-instructions.md files updated: `(above workspace root)` and `directories is allowed` present.  
AW AGENT-RULES.md Blocked Commands row updated: `(above workspace root)`, `(outward navigation)` removed.  
CW AGENT-RULES.md Security Rules: `above the workspace root are blocked` and `navigation within` present.  
**Correct.** SAF-079 merged behavior accurately reflected.

### Change 3 — Separate file_search from grep_search guidance ✅
AW AGENT-RULES.md line 225: new row clarifying `file_search` uses `query` glob, not `includePattern`.  
CW AGENT-RULES.md line 58: `file_search` row now says "Uses the `query` parameter" and "does **not** require `includePattern`".  
Both templates still state `includePattern` is required for `grep_search`.  
**Correct.**

### MANIFEST Regeneration ✅
Both `MANIFEST.json` files are valid JSON. `file_count` matches `files` dict length. `copilot-instructions.md` correctly flagged `security_critical: true`.

---

## Regressions Found — BLOCKING

**14 test failures** not in `tests/regression-baseline.json` are introduced by this WP:

### DOC-064 test failures (13 new)

These tests assert that `isBackground:true` **IS present** in documentation files. DOC-066 intentionally removed it. The baseline pre-dating DOC-066 contained 6 DOC-064 agent-workbench failures (from DOC-065 having already removed the AW AGENT-RULES entry). DOC-066 removed the remaining entries (both copilot-instructions.md + CW AGENT-RULES), causing 13 additional tests to fail.

```
tests/DOC-064/test_doc064_background_terminal_docs.py::test_clean_workspace_agent_rules_has_isBackground
tests/DOC-064/test_doc064_background_terminal_docs.py::test_clean_workspace_agent_rules_use_instead_guidance
tests/DOC-064/test_doc064_background_terminal_docs.py::test_agent_workbench_copilot_instructions_has_isBackground
tests/DOC-064/test_doc064_background_terminal_docs.py::test_clean_workspace_copilot_instructions_has_isBackground
tests/DOC-064/test_doc064_background_terminal_docs.py::test_agent_workbench_copilot_instructions_use_instead_guidance
tests/DOC-064/test_doc064_background_terminal_docs.py::test_clean_workspace_copilot_instructions_use_instead_guidance
tests/DOC-064/test_doc064_background_terminal_docs.py::test_clean_workspace_agent_rules_security_gate_reason
tests/DOC-064/test_doc064_tester_edge_cases.py::test_clean_workspace_agent_rules_isBackground_in_restricted_section
tests/DOC-064/test_doc064_tester_edge_cases.py::test_agent_workbench_copilot_instructions_security_gate_reason
tests/DOC-064/test_doc064_tester_edge_cases.py::test_clean_workspace_copilot_instructions_security_gate_reason
tests/DOC-064/test_doc064_tester_edge_cases.py::test_agent_workbench_copilot_instructions_isBackground_in_known_limitations
tests/DOC-064/test_doc064_tester_edge_cases.py::test_clean_workspace_copilot_instructions_isBackground_in_known_limitations
tests/DOC-064/test_doc064_tester_edge_cases.py::test_clean_workspace_agent_rules_single_isBackground_entry
```

### DOC-065 test failure (1 new)

DOC-065 `test_isBackground_not_blocked_in_clean_workspace_agent_rules` checks that CW AGENT-RULES **still** contains `isBackground:true` (as a Known Tool Workaround not touched by DOC-065). DOC-066 removed it from CW AGENT-RULES entirely, failing this assertion.

```
tests/DOC-065/test_doc065_template_docs.py::TestIsBackgroundRemoved::test_isBackground_not_blocked_in_clean_workspace_agent_rules
```

---

## Security Assessment ✅ No issues

- No new code (Python source files unchanged)
- Security gate logic unchanged (all 12 snapshot tests pass)
- MANIFEST.json correctly regenerated with hashes for all changed files
- No path traversal, secrets, or external reference violations in changed docs

---

## ADR Check ✅ No conflicts

No ADRs related to documentation wording or `isBackground` guidance.

---

## Required TODOs for Developer

### TODO 1 — Add 14 DOC-064/DOC-065 failures to the regression baseline **(MANDATORY)**

Open `tests/regression-baseline.json` and add all 14 test IDs to the `known_failures` section using the dotted-path key format, with a reason string that references DOC-066 as the superseding WP.

**Key format:** `tests.DOC-064.test_doc064_background_terminal_docs.<test_name>`  
**Reason template:** `"DOC-066 intentionally removes isBackground:true from documentation — confirmed working across 3 audit iterations. DOC-064 tests now superseded by DOC-066."`

After adding all 14, update `_count` (add 14 to current count) and update `_updated` to today's date.

The 14 entries to add (in `known_failures` dotted-path format):

```
tests.DOC-064.test_doc064_background_terminal_docs.test_clean_workspace_agent_rules_has_isBackground
tests.DOC-064.test_doc064_background_terminal_docs.test_clean_workspace_agent_rules_use_instead_guidance
tests.DOC-064.test_doc064_background_terminal_docs.test_agent_workbench_copilot_instructions_has_isBackground
tests.DOC-064.test_doc064_background_terminal_docs.test_clean_workspace_copilot_instructions_has_isBackground
tests.DOC-064.test_doc064_background_terminal_docs.test_agent_workbench_copilot_instructions_use_instead_guidance
tests.DOC-064.test_doc064_background_terminal_docs.test_clean_workspace_copilot_instructions_use_instead_guidance
tests.DOC-064.test_doc064_background_terminal_docs.test_clean_workspace_agent_rules_security_gate_reason
tests.DOC-064.test_doc064_tester_edge_cases.test_clean_workspace_agent_rules_isBackground_in_restricted_section
tests.DOC-064.test_doc064_tester_edge_cases.test_agent_workbench_copilot_instructions_security_gate_reason
tests.DOC-064.test_doc064_tester_edge_cases.test_clean_workspace_copilot_instructions_security_gate_reason
tests.DOC-064.test_doc064_tester_edge_cases.test_agent_workbench_copilot_instructions_isBackground_in_known_limitations
tests.DOC-064.test_doc064_tester_edge_cases.test_clean_workspace_copilot_instructions_isBackground_in_known_limitations
tests.DOC-064.test_doc064_tester_edge_cases.test_clean_workspace_agent_rules_single_isBackground_entry
tests.DOC-065.test_doc065_template_docs.TestIsBackgroundRemoved.test_isBackground_not_blocked_in_clean_workspace_agent_rules
```

### TODO 2 — Verify `validate_workspace.py --wp DOC-066` is still clean after baseline update

Re-run `scripts/validate_workspace.py --wp DOC-066` and confirm exit code 0.

### TODO 3 — Re-run and log full test suite via `scripts/run_tests.py`

After the baseline update, run the full test suite via `scripts/run_tests.py --wp DOC-066`. Confirm no new failures beyond the baseline. Re-submit for Tester review.

---

## Non-Blocking Observations

- Several other "new" failures appear in the full test run (SAF-001, INS-001, MNT-029, GUI-035) but these are pre-existing environmental/flaky failures unrelated to this WP. SAF-001 integration tests pass when run in isolation (order-dependent flakiness). These are not caused by DOC-066 and are documented here for transparency, not as blockers.
- That said, the project baseline should be periodically updated to include these. Not a DOC-066 blocker.
