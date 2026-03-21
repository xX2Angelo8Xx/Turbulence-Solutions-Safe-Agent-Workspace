# DOC-008 Dev Log

## Workpackage
**ID:** DOC-008  
**Name:** Add read-first directive to copilot-instructions  
**Branch:** DOC-008/read-first-directive  
**Assigned To:** Developer Agent  

---

## Implementation Summary

Added a prominent first-action directive to `templates/coding/.github/instructions/copilot-instructions.md` 
that instructs agents to read `{{PROJECT_NAME}}/AGENT-RULES.md` as their very first action in every session.

The directive was inserted at the very top of the file (before any other content), formatted as a 
callout-style block using a `> [!IMPORTANT]` blockquote to make it visually prominent. It uses the 
`{{PROJECT_NAME}}` placeholder which will be replaced by `project_creator.py` at project creation time.

All existing content in the file was preserved unchanged.

---

## Files Changed

| File | Change |
|------|--------|
| `templates/coding/.github/instructions/copilot-instructions.md` | Added read-first directive at top of file |

---

## Tests Written

| File | What It Tests |
|------|---------------|
| `tests/DOC-008/test_doc008_read_first_directive.py` | 5 tests verifying presence, placement, and correctness of the directive |

### Test Coverage
1. `test_read_first_directive_present` — copilot-instructions.md contains a read-first directive
2. `test_directive_mentions_agent_rules` — directive references AGENT-RULES.md
3. `test_directive_uses_project_name_placeholder` — directive uses {{PROJECT_NAME}} placeholder
4. `test_directive_is_near_top` — directive appears within first 10 lines or first section
5. `test_existing_content_preserved` — all major existing content sections are preserved

---

## Decisions Made

- Used `> [!IMPORTANT]` GitHub-flavored markdown callout for visual prominence without disrupting document structure.
- Inserted directive as the very first content (before the `# Turbulence Solutions – Copilot Instructions` heading) 
  so no scrolling is required to see it.
- Used exact filename `AGENT-RULES.md` as specified in acceptance criteria.

---

## Known Limitations

None. This is a documentation-only change to a template file.

---

## AC Verification

- AC 8 of US-033: "copilot-instructions.md contains a first-action directive pointing agents to AGENT-RULES.md" — **SATISFIED**

---

## Iteration 1 — Tester Regression Fixes

**Date:** 2026-03-21  
**Tester Report:** `docs/workpackages/DOC-008/test-report.md`

### Problem
The DOC-008 directive added a second `{{PROJECT_NAME}}` occurrence at the top of the template file. This caused 3 DOC-003 edge-case tests (in `tests/DOC-003/test_doc003_edge_cases.py`) to fail:
1. `test_placeholder_count_exactly_one_in_default_project` — asserted `count == 1`, now 2
2. `test_placeholder_count_exactly_one_in_templates_coding` — same
3. `test_placeholder_is_in_workspace_rules_section` — checked index of first occurrence; first occurrence is now at line 2 (before Workspace Rules)

### Fix Applied
Updated `tests/DOC-003/test_doc003_edge_cases.py`:
1. Changed count assertions from `== 1` to `>= 1` (multiple occurrences are legitimate)
2. Rewrote `test_placeholder_is_in_workspace_rules_section` to extract the Workspace Rules section body (from `## Workspace Rules` to the next `##` heading) and assert `{{PROJECT_NAME}}` appears within that body, rather than relying on the index of the first file-wide occurrence.

### Files Changed
| File | Change |
|------|--------|
| `tests/DOC-003/test_doc003_edge_cases.py` | Relaxed 2 count assertions; rewrote 1 section test |

### Test Results
- 29 tests passed, 0 failed (DOC-003 + DOC-008)
- Test run logged as TST-2007
- BUG-093 resolved by this fix
