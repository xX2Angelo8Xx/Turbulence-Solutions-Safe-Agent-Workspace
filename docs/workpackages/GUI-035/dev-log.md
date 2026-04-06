# GUI-035 Dev Log — Create clean-workspace template structure

**WP:** GUI-035  
**Branch:** GUI-035/clean-workspace-template  
**Status:** In Progress  
**Assigned To:** Developer Agent  
**Started:** 2026-04-06  

## ADR Review

- **ADR-003** (Template Manifest and Workspace Upgrade System) — Active, relevant. This WP adds a
  new template that follows the same manifest pattern as agent-workbench. The clean-workspace
  MANIFEST.json is generated separately via `scripts/generate_manifest.py` (which will be extended
  to also support clean-workspace). ADR-003 is acknowledged; no supersession proposed.
- **ADR-011** (Drop settings.json from Security Gate Integrity Hash) — Active, relevant. The
  clean-workspace template's settings.json is not tracked as security-critical in the manifest,
  consistent with this decision.

## Requirements

Create `templates/clean-workspace/` directory with:
- Security gate files byte-identical to agent-workbench (`security_gate.py`, `update_hashes.py`)
- `.vscode/settings.json` — same hide patterns as agent-workbench
- `NoAgentZone/README.md` — same as agent-workbench
- `Project/AGENT-RULES.md` — simplified (no AgentDocs, no agent-specific content)
- `Project/README.md` — simplified project readme
- `.github/instructions/copilot-instructions.md` — simplified (no agents, no AgentDocs)
- `.gitignore` — same as agent-workbench
- `MANIFEST.json` — generated
- `README.md` — workspace-level readme

NO `.github/agents/`, `.github/prompts/`, `.github/skills/`, `Project/AgentDocs/`

## Implementation Plan

1. Create the directory structure
2. Copy security files byte-identically from agent-workbench
3. Copy/adapt other files (settings.json, .gitignore, NoAgentZone/README.md)
4. Create simplified copilot-instructions.md and AGENT-RULES.md
5. Extend generate_manifest.py to support clean-workspace
6. Generate MANIFEST.json
7. Write tests in tests/GUI-035/
8. Run tests via run_tests.py

## Implementation Summary

### Files Created

**Template files in `templates/clean-workspace/`:**
- `.github/hooks/scripts/security_gate.py` — byte-identical to agent-workbench
- `.github/hooks/scripts/update_hashes.py` — byte-identical to agent-workbench
- `.github/hooks/scripts/zone_classifier.py` — byte-identical to agent-workbench
- `.github/hooks/scripts/require-approval.ps1` — byte-identical to agent-workbench
- `.github/hooks/scripts/require-approval.sh` — byte-identical to agent-workbench
- `.github/hooks/scripts/reset_hook_counter.py` — byte-identical to agent-workbench
- `.github/hooks/scripts/counter_config.json` — byte-identical to agent-workbench
- `.github/hooks/require-approval.json` — byte-identical to agent-workbench
- `.github/instructions/copilot-instructions.md` — simplified (no agents/AgentDocs/skills)
- `.github/version` — version placeholder
- `.vscode/settings.json` — same hide patterns as agent-workbench
- `NoAgentZone/README.md` — identical to agent-workbench
- `Project/AGENT-RULES.md` — simplified rules (no AgentDocs section, no agent roster)
- `Project/README.md` — simplified project readme
- `.gitignore` — identical to agent-workbench
- `README.md` — workspace-level readme for clean workspace
- `MANIFEST.json` — generated via extended generate_manifest.py

**Script changes:**
- `scripts/generate_manifest.py` — extended to support `--template` argument for clean-workspace

**Tests:**
- `tests/GUI-035/test_gui035_clean_workspace_template.py`

## Decisions Made

- The `generate_manifest.py` script is extended with a `--template` argument to generate
  manifests for either `agent-workbench` or `clean-workspace`. This is a minimal, backward-
  compatible change — calling without `--template` still defaults to `agent-workbench`.
- The clean-workspace template does NOT include the `.github/agents/`, `.github/prompts/`,
  `.github/skills/` directories, consistent with US-078 acceptance criteria.
- The `.github/version` file is included (contains `{{VERSION}}` placeholder) so the launcher
  can track which template version was used.
- All hook scripts are copied byte-identically — no modifications to security-critical code.

## Tests Written

- `test_template_directory_exists` — template dir exists
- `test_security_gate_byte_identical` — security_gate.py matches agent-workbench
- `test_update_hashes_byte_identical` — update_hashes.py matches agent-workbench
- `test_required_files_present` — all required files exist
- `test_no_agents_dir` — agents directory absent
- `test_no_prompts_dir` — prompts directory absent  
- `test_no_skills_dir` — skills directory absent
- `test_no_AgentDocs_in_project` — AgentDocs absent from Project/
- `test_vscode_settings_has_hide_patterns` — settings.json has expected keys
- `test_copilot_instructions_no_agent_references` — instructions file has no agent references
- `test_agent_rules_no_agentdocs_section` — AGENT-RULES.md has no AgentDocs section
- `test_manifest_exists_and_valid` — MANIFEST.json is valid JSON
- `test_list_templates_discovers_clean_workspace` — list_templates() returns clean-workspace
- `test_is_template_ready` — is_template_ready() returns True for clean-workspace
- `test_gitignore_present` — .gitignore present
- `test_novagentzone_readme_present` — NoAgentZone/README.md present
