# Dev Log — DOC-028

**Developer:** Developer Agent
**Date started:** 2026-03-25
**Iteration:** 1

## Objective
Create `templates/agent-workbench/.github/agents/prototyper.agent.md` with YAML frontmatter (name, description, tools, model). Persona: speed-focused MVP builder that validates ideas quickly. Builds quick-and-dirty POCs, trades perfection for speed. Agent must follow AGENT-RULES.md conventions. Write tests verifying the file exists and has valid YAML frontmatter.

## Implementation Summary
Created prototyper.agent.md following the established pattern from programmer.agent.md, fixer.agent.md, and scientist.agent.md. The prototyper has the full tool set (read + edit + search + execute) since it needs to rapidly build working prototypes. Persona emphasizes speed over perfection, MVP mindset, and disposable code.

## Files Changed
- `templates/agent-workbench/.github/agents/prototyper.agent.md` — New agent file
- `tests/DOC-028/test_doc028_prototyper_agent.py` — Tests for file existence, YAML frontmatter, tools, persona
- `docs/workpackages/DOC-028/dev-log.md` — This file

## Tests Written
- `test_file_exists` — Verifies prototyper.agent.md exists at correct path
- `test_file_is_not_empty` — Verifies file has content
- `test_file_starts_with_frontmatter_delimiter` — Verifies YAML frontmatter block
- `test_frontmatter_is_parseable` — Verifies valid YAML
- `test_frontmatter_name_present_and_non_empty` — Required field check
- `test_frontmatter_description_present_and_non_empty` — Required field check
- `test_frontmatter_tools_is_list` — Tools field structure check
- `test_frontmatter_required_tools_present` — All 8 tools present (full set)
- `test_frontmatter_no_forbidden_tools` — No notebook/web tools
- `test_frontmatter_model_present_and_non_empty` — Required field check
- `test_body_is_non_trivial` — Body has substantial content
- `test_body_mentions_prototyper_role` — Persona references prototyper identity
- `test_body_contains_zone_restrictions` — Zone restrictions table present
- `test_body_references_agent_rules` — References AGENT-RULES.md
- `test_body_contains_project_name_placeholder` — Uses {{PROJECT_NAME}}

## Known Limitations
- None
