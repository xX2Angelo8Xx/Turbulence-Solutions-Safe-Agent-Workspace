# Dev Log — FIX-091: Remove app.py and requirements.txt from template

## WP Info
- **WP ID:** FIX-091
- **Category:** FIX
- **Status:** In Progress
- **Assigned To:** Developer Agent
- **Branch:** FIX-091/remove-template-files

---

## Phase 1 — Implementation

### Summary
Delete `app.py` and `requirements.txt` from `templates/agent-workbench/Project/`. These files are boilerplate stubs that should not be included in the template; new workspaces must start with a clean project folder.

### Files Changed
- **Deleted:** `templates/agent-workbench/Project/app.py`
- **Deleted:** `templates/agent-workbench/Project/requirements.txt`

### Files NOT Changed
- `templates/agent-workbench/Project/README.md` — retained
- `templates/agent-workbench/Project/AGENT-RULES.md` — retained
- `templates/agent-workbench/Project/AgentDocs/` — retained

### Decisions
- No changes to `project_creator.py` or any other source file — WP scope is file deletion only.
- No additional template changes made.

---

## Phase 2 — Testing

### Test File
- `tests/FIX-091/test_fix091_template_files.py`

### Tests Written
1. `test_app_py_does_not_exist` — asserts `templates/agent-workbench/Project/app.py` is absent
2. `test_requirements_txt_does_not_exist` — asserts `templates/agent-workbench/Project/requirements.txt` is absent
3. `test_readme_still_exists` — asserts `templates/agent-workbench/Project/README.md` is present
4. `test_agent_rules_still_exists` — asserts `templates/agent-workbench/Project/AGENT-RULES.md` is present
5. `test_agentdocs_dir_still_exists` — asserts `templates/agent-workbench/Project/AgentDocs/` directory is present

### Test Results
- All 5 tests passed.

---

## Phase 3 — Handoff

- WP status set to `Review`.
- Committed and pushed on branch `FIX-091/remove-template-files`.
