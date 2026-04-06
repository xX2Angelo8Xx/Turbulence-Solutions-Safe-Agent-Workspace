# Test Report — DOC-063

**Tester:** Tester Agent  
**Date:** 2026-04-06  
**Iteration:** 1  

---

## Summary

WP DOC-063 delivers 20 unit tests for the clean-workspace template creation workflow. After review, the Tester found a **cross-test contamination bug** in the security-gate functional test, corrected it, and added 5 edge-case tests covering previously untested US-078 acceptance criteria. The final suite of 25 tests passes in full, and no new regressions are introduced against the main branch.

---

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| TST-2708 DOC-063: full regression suite (initial) | Regression | Fail | 4 snapshot failures — caused by test bug in DOC-063 (sys.modules contamination), not a source bug |
| TST-2709 DOC-063: full regression suite (after fix) | Regression | Fail* | 198 failures — all pre-existing on main branch (verified via stash test); snapshot regressions eliminated |
| TST-2710 DOC-063: targeted suite (25 tests) | Unit | Pass | 25 passed, 0 failed — final official result |

*"Fail" in run_tests.py output reflects pre-existing known failures and cross-test timeout flakiness (SAF-073/074/077) present on main branch. No regressions introduced by DOC-063.

---

## Review Findings

### Bug Found — sys.modules Contamination (test-level, no source change required)

**Symptom:** Four snapshot tests (`allow_delete_project_multisegment`, `allow_grep_project_pattern`, `allow_read_project_file`, `allow_write_project_file`) failed when run after DOC-063's `test_security_gate_importable_and_decide_returns_action`.

**Root Cause:** The original `finally` block unconditionally deleted `zone_classifier` from `sys.modules`. The snapshot test conftest (`tests/snapshots/security_gate/conftest.py`) patches `sys.modules["zone_classifier"].detect_project_folder` before each snapshot test. After DOC-063's cleanup, the conftest would re-import and patch a newer `zone_classifier` module object — but `sg` (the module-level import in `test_snapshots.py`) still held a reference to the old object, so the patch had no effect and `detect_project_folder` raised `OSError` on the fake `/workspace` path, causing `classify()` to return `"deny"` instead of `"allow"`.

**Fix Applied (in `tests/DOC-063/test_doc063_clean_workspace_creation.py`):**
- Pop existing `security_gate` and `zone_classifier` from `sys.modules` BEFORE the test, so `importlib.import_module()` actually loads the clean-workspace versions (not the cached agent-workbench versions).
- After the test, remove the clean-workspace versions and restore the original agent-workbench objects to `sys.modules`, preserving the snapshot conftest's patch target.

### Missing Acceptance-Criteria Coverage (5 tests added)

US-078 acceptance criteria items not covered by the Developer's 20 tests:

| AC item | Added test |
|---------|-----------|
| AC 2 — MANIFEST.json at workspace root | `test_manifest_json_exists` |
| AC 5 — copilot-instructions.md exists | `test_copilot_instructions_exists` |
| AC 5 — no .github/agents references | `test_copilot_instructions_no_agents_dir_reference` |
| AC 6 — security gate denies NoAgentZone | `test_security_gate_denies_noagentzone` |
| Edge case — hyphenated project name | `test_create_project_hyphenated_name` |

---

## Bugs Found

None — the contamination issue was a test-code defect, not a production code bug.

---

## Acceptance-Criteria Coverage (US-078)

| AC | Description | Covered |
|----|-------------|---------|
| 1 | Template appears in dropdown | ✅ `test_clean_workspace_in_list_templates` |
| 2 | security gate, settings.json, MANIFEST.json, AGENT-RULES.md created | ✅ (all 4 items tested) |
| 3 | No .github/agents, .github/prompts, .github/skills | ✅ `test_no_agents_directory` etc. |
| 4 | No AgentDocs/ directory | ✅ `test_no_agentdocs_directory` |
| 5 | Simplified copilot-instructions.md, no agent references | ✅ `test_copilot_instructions_no_agents_dir_reference` |
| 6 | Security gate is functional and blocks denied zones | ✅ `test_security_gate_importable_and_decide_returns_action` + `test_security_gate_denies_noagentzone` |

---

## Verdict

**PASS — mark WP as Done**

All 25 tests pass. The sys.modules contamination bug was corrected within the test file (no source changes needed). No new regressions introduced against main branch.
