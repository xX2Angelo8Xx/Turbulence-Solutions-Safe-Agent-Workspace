# DOC-019 Dev Log — Create programmer.agent.md for Agent Workbench

## WP Summary

- **ID:** DOC-019
- **Branch:** DOC-019/programmer-agent
- **Assigned To:** Developer Agent
- **User Story:** US-042 (Programmer Agent for Agent Workbench)
- **Depends On:** DOC-018 (Done)

## Goal

Create `templates/agent-workbench/.github/agents/programmer.agent.md` with valid YAML frontmatter (name, description, tools: [read, edit, search, execute], model). Persona: practical coder focused on implementation and refactoring. Follows project conventions, writes clean code, refactors when asked. Agent must follow AGENT-RULES.md conventions.

---

## Implementation

### Files Created

- `templates/agent-workbench/.github/agents/programmer.agent.md` — Programmer agent definition with YAML frontmatter and persona description.

### Decisions

- Tools list follows the README.md spec: `[read_file, create_file, replace_string_in_file, multi_replace_string_in_file, grep_search, file_search, semantic_search, run_in_terminal]` — these are the concrete VS Code tool IDs that map to the abstract [read, edit, search, execute] capabilities specified in the WP.
- Model set to `claude-sonnet-4-5` consistent with the example in README.md's How to Customize section.
- Persona body follows AGENT-RULES.md conventions: focuses on implementation within the project folder, references AGENT-RULES.md, does not bypass zone restrictions.
- Agent body is tightly scoped to implementation and refactoring tasks; avoids brainstorming, planning, and other roles that belong to separate agent personas.

---

## Tests

- Test file: `tests/DOC-019/test_doc019_programmer_agent.py`
- Test cases:
  1. File exists at correct path
  2. File has YAML frontmatter (opens with `---`)
  3. YAML frontmatter is parseable
  4. `name` field is present and non-empty
  5. `description` field is present and non-empty
  6. `tools` field is a list
  7. All required tools present: read_file, create_file, replace_string_in_file, grep_search, run_in_terminal
  8. `model` field is present and non-empty
  9. Body contains persona description (text after frontmatter)
  10. Body references AGENT-RULES.md

## Test Results

All 10 tests pass. Logged via `scripts/add_test_result.py`.

---

## Checklist

- [x] `dev-log.md` created and filled in
- [x] `tests/DOC-019/` folder and test file exist
- [x] All tests pass
- [x] Test results logged
- [x] `validate_workspace.py --wp DOC-019` passes
- [x] All changes staged and committed

---

## Iteration 2 — Tester Feedback Fix (2026-03-25)

### Issue

`tests/DOC-018/test_doc018_tester_edge_cases.py::test_agents_dir_contains_only_readme` failed because DOC-019 legitimately added `programmer.agent.md` to `agents/`, making the phase-gate assertion stale. Also BUG-106 was logged by Tester to track this regression.

### Changes Made

- **`tests/DOC-018/test_doc018_tester_edge_cases.py`** — Renamed `test_agents_dir_contains_only_readme` to `test_agents_dir_contains_readme`. Updated assertion from `visible == ["README.md"]` (exact equality) to `"README.md" in visible` (membership check). Updated docstring to reflect that additional `.agent.md` files are added by DOC-019..028.
- **`docs/bugs/bugs.csv`** — Updated BUG-106 status from `Open` to `Closed`, set Fixed In WP to `DOC-019`, added resolution note.

### Test Results

43 tests pass (DOC-018: 20, DOC-019: 23). 0 failures.
