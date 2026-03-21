# DOC-007 — Dev Log

## Workpackage

| Field | Value |
|-------|-------|
| ID | DOC-007 |
| Name | Create AGENT-RULES.md template |
| Branch | DOC-007/agent-rules-template |
| Assigned To | Developer Agent |
| Status | Review |

## Objective

Create `templates/coding/Project/AGENT-RULES.md` with all 7 required sections as defined in US-033 ACs 2–7:
1. Allowed Zone
2. Denied Zones
3. Tool Permission Matrix
4. Terminal Rules
5. Git Rules
6. Session-Scoped Denial Counter
7. Known Workarounds

Use `{{PROJECT_NAME}}` and `{{WORKSPACE_NAME}}` placeholders so DOC-009 can replace them during project creation.

## Implementation Summary

### Files Created

| File | Description |
|------|-------------|
| `templates/coding/Project/AGENT-RULES.md` | The primary deliverable — agent rule book template |
| `tests/DOC-007/test_doc007_agent_rules.py` | Test suite verifying file exists and all 7 sections are present |

### Implementation Notes

- File placed in `templates/coding/Project/` so it is inside the project folder — no `.github/` read exception required.
- All 7 ACs from US-033 addressed in corresponding sections.
- Placeholders `{{PROJECT_NAME}}` and `{{WORKSPACE_NAME}}` used throughout so DOC-009 can substitute real values.
- No existing source files were modified.

## Tests Written

| Test | Description |
|------|-------------|
| `test_file_exists` | Confirms AGENT-RULES.md exists at expected path |
| `test_has_allowed_zone_section` | Verifies Allowed Zone section with PROJECT_NAME placeholder |
| `test_has_denied_zones_section` | Verifies Denied Zones section listing all 3 denied paths |
| `test_has_tool_permission_matrix` | Verifies Tool Permission Matrix table is present |
| `test_has_terminal_rules_section` | Verifies Terminal Rules section with examples |
| `test_has_git_rules_section` | Verifies Git Rules section |
| `test_has_denial_counter_section` | Verifies Session-Scoped Denial Counter section |
| `test_has_workarounds_section` | Verifies Known Workarounds section with table |
| `test_has_read_first_directive` | Verifies "read this file" instruction at top |
| `test_placeholders_present` | Confirms {{PROJECT_NAME}} and {{WORKSPACE_NAME}} placeholders exist |
| `test_denied_zone_github` | Verifies .github/ in denied zones |
| `test_denied_zone_vscode` | Verifies .vscode/ in denied zones |
| `test_denied_zone_noagentzone` | Verifies NoAgentZone/ in denied zones |

## Known Limitations

None.
