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
