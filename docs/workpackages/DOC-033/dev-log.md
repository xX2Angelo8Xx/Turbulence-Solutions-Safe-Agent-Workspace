# DOC-033 Dev Log — README management for agent-workbench template

**Status:** Review  
**Assigned To:** Developer Agent  
**Branch:** `DOC-033/readme-management`  
**User Story:** US-067

---

## Summary

Two changes to `templates/agent-workbench/`:
1. Replace existing agent-facing `README.md` with a minimal user-facing version.
2. Delete `templates/agent-workbench/.github/agents/README.md` (developer-only document).

---

## Implementation

### Files Changed
- `templates/agent-workbench/README.md` — replaced with user-facing workspace overview (uses `{{PROJECT_NAME}}` and `{{WORKSPACE_NAME}}` placeholders)
- `templates/agent-workbench/.github/agents/README.md` — deleted

### Decisions
- The existing README.md was agent-facing (describing security zones to AI agents). Replaced with a brief user-facing document per WP scope.
- Kept the new README under 30 lines for brevity.
- `{{PROJECT_NAME}}` and `{{WORKSPACE_NAME}}` are template placeholders replaced by the launcher at workspace creation time.

---

## Tests

Tests in `tests/DOC-033/test_doc033_readme_management.py`:
1. `templates/agent-workbench/README.md` exists
2. Contains `{{PROJECT_NAME}}` placeholder
3. Contains `{{WORKSPACE_NAME}}` placeholder
4. Mentions `NoAgentZone`
5. Is under 50 lines
6. `templates/agent-workbench/.github/agents/README.md` does NOT exist
