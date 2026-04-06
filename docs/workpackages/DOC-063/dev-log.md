# DOC-063 Dev Log — Tests for clean-workspace template creation

**WP ID:** DOC-063  
**Branch:** DOC-063/clean-workspace-tests  
**Developer:** Developer Agent  
**Date Started:** 2026-04-06  
**Status:** In Progress  

---

## ADR Check

Reviewed `docs/decisions/index.jsonl`. No ADRs are directly scoped to template test coverage. ADR-008 ("Tests Must Track Current Codebase State") is noted — tests are written against the live template files in `templates/clean-workspace/` to ensure they always reflect the current state.

---

## Requirements

DOC-063 requires tests verifying:
1. `list_templates()` includes "clean-workspace"
2. `create_project()` with the clean-workspace template produces the correct workspace structure
3. NO `.github/agents/`, `.github/prompts/`, `.github/skills/` in created workspace
4. NO `AgentDocs/` at the workspace root
5. `AGENT-RULES.md` exists at project root (inside the renamed project folder)
6. `security_gate.py` exists and is byte-identical to the template source
7. Placeholders `{{PROJECT_NAME}}` and `{{WORKSPACE_NAME}}` are replaced in markdown files
8. `.vscode/settings.json` exists with the correct `.github` and `.vscode` exclusion patterns

---

## Implementation

All tests live in `tests/DOC-063/test_doc063_clean_workspace_creation.py`.

The test file contains four classes:
- `TestCleanWorkspaceInDropdown` — list_templates() and is_template_ready() assertions
- `TestCreateProjectStructure` — end-to-end create_project() structural checks
- `TestPlaceholderReplacement` — {{PROJECT_NAME}}/{{WORKSPACE_NAME}} token replacement
- `TestSecurityGateFunctional` — security_gate.py syntax validity and importability

All tests use `tmp_path` (pytest built-in) so no files are left outside the designated temp directory.

---

## Files Changed

- `docs/workpackages/workpackages.jsonl` — status → In Progress, then Review
- `docs/workpackages/DOC-063/dev-log.md` — this file
- `tests/DOC-063/__init__.py` — package marker
- `tests/DOC-063/test_doc063_clean_workspace_creation.py` — 19 tests

---

## Test Results

Run via `scripts/run_tests.py --wp DOC-063 --type Unit --env "Windows 11 + Python 3.11"`. All 19 tests pass.

---

## Known Limitations

- `_init_git_repository()` is called inside `create_project()` — git subprocess calls are non-fatal and silently succeed or fail depending on whether git is installed via the OS. Tests do not assert git initialization outcome, only the workspace structure.
- The security_gate.py "functional" test imports the module from the template source directory via sys.path manipulation. The created workspace copy is verified via SHA256 byte comparison.
