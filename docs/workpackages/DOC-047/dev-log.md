# DOC-047 Dev Log — Update tests for AGENT-RULES consolidation

**Status:** Review  
**Assigned To:** Developer Agent  
**Branch:** DOC-047/update-agent-rules-tests  
**Date:** 2026-04-01

---

## Objective

Update all test files that reference the old `AGENT-RULES.md` path (`Project/AGENT-RULES.md`) to reflect its new location at `Project/AgentDocs/AGENT-RULES.md` following the DOC-045 consolidation.

---

## Files Changed

### Test Files Updated

1. **`tests/DOC-007/test_doc007_agent_rules.py`**
   - Updated `AGENT_RULES_PATH` constant: added `"AgentDocs"` segment
   - Updated module docstring to reference new path

2. **`tests/DOC-008/test_doc008_read_first_directive.py`**
   - Updated assertion in `test_directive_uses_project_name_placeholder` to check for `{{PROJECT_NAME}}/AgentDocs/AGENT-RULES.md`

3. **`tests/DOC-008/test_doc008_tester_edge_cases.py`**
   - Updated `test_agent_rules_path_format` docstring and assertion to check for `{{PROJECT_NAME}}/AgentDocs/AGENT-RULES.md`

4. **`tests/DOC-009/test_doc009_placeholder_replacement.py`**
   - Updated `AGENT_RULES_TEMPLATE` constant: added `"AgentDocs"` segment
   - Updated `_setup_agent_rules` helper: destination path now uses `project_dir / "AgentDocs" / "AGENT-RULES.md"`

5. **`tests/DOC-002/test_doc002_readme_placeholders.py`**
   - Updated `test_placeholder_present_in_agent_rules_section` assertion to check for `` `{{PROJECT_NAME}}/AgentDocs/AGENT-RULES.md` ``

---

## Implementation Notes

- No source or template files were modified — only test files updated.
- `tests/DOC-009/test_doc009_tester_edge_cases.py` required no changes (uses synthetic content, no path constants pointing to the old location).
- The `_setup_agent_rules` helper in DOC-009 now mirrors the real directory structure (`AgentDocs/` subdirectory).

---

## Tests

All tests run: `tests/DOC-002/`, `tests/DOC-007/`, `tests/DOC-008/`, `tests/DOC-009/`

Results: **94 passed, 0 failed** (TST-2394)
