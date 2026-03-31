# DOC-043 — Dev Log: Add Plan.md system to agent-workbench template

**Status:** Review  
**Assigned To:** Developer Agent  
**Branch:** DOC-043/plan-file-system  
**Date Started:** 2026-03-31  

---

## Goal

Add a structured Plan.md system to the AgentDocs framework in the agent-workbench template.  
Planner creates named plan files; Coordinator executes them; Tidyup audits them.

## Tasks

- [x] Claim WP (In Progress), create branch
- [x] Create dev-log.md
- [x] Update `planner.agent.md` — plan file writing, naming convention
- [x] Update `coordinator.agent.md` — plan file execution capability
- [x] Update `tidyup.agent.md` — plan file audit section
- [x] Update `AgentDocs/README.md` — add plan files row to table
- [x] Update `AGENT-RULES.md` — map Planner to plan files
- [x] Create `AgentDocs/plan.md` template file
- [x] Write tests in `tests/DOC-043/`
- [x] Run tests (18/18 passed)
- [x] Log test results via `add_test_result.py` (TST-2383)
- [x] Validate workspace (`validate_workspace.py --wp DOC-043` → All checks passed)
- [x] Commit and push

---

## Implementation Summary

### Files Modified
- `templates/agent-workbench/.github/agents/planner.agent.md`
- `templates/agent-workbench/.github/agents/coordinator.agent.md`
- `templates/agent-workbench/.github/agents/tidyup.agent.md`
- `templates/agent-workbench/Project/AgentDocs/README.md`
- `templates/agent-workbench/Project/AGENT-RULES.md`
- `docs/workpackages/workpackages.csv` (claimed WP)

### Files Created
- `templates/agent-workbench/Project/AgentDocs/plan.md`
- `tests/DOC-043/test_doc043_plan_system.py`
- `docs/workpackages/DOC-043/dev-log.md` (this file)

### Key Decisions
- Plan files use naming convention: `plan.md` (initial) / `plan-<topic>.md` (sub-plans)
- Plan file duplication check added to Planner's How You Work
- Coordinator step 3 updated to reference plan file execution
- Coordinator reads active plan file referenced in progress.md
- Tidyup gains a new `### Plan files (plan*.md)` audit section
- README Pillar 2 updated: plan files are the explicit exception to "no new files"
- AGENT-RULES.md section 1a updated for all three agents

---

## Tests Written

| Test | What It Checks |
|------|---------------|
| `test_plan_md_exists` | plan.md template file exists |
| `test_plan_md_has_goal_section` | plan.md has `## Goal` |
| `test_plan_md_has_tasks_section` | plan.md has `## Tasks` |
| `test_plan_md_has_acceptance_criteria` | plan.md has `## Acceptance Criteria` |
| `test_planner_mentions_plan_file_writing` | planner.agent.md mentions writing plan files |
| `test_planner_mentions_naming_convention` | planner.agent.md describes naming convention |
| `test_coordinator_mentions_plan_file_execution` | coordinator.agent.md mentions executing plan files |
| `test_coordinator_reads_active_plan` | coordinator.agent.md mentions reading active plan |
| `test_tidyup_has_plan_file_section` | tidyup.agent.md has plan file audit section |
| `test_readme_has_plan_file_row` | AgentDocs/README.md has plan file table row |
| `test_agent_rules_maps_planner_to_plan_files` | AGENT-RULES.md maps Planner to plan files |

---

## Known Limitations

None.
