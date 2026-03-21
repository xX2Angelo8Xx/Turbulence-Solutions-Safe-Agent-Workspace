# DOC-009 Dev Log — Add AGENT-RULES.md to Placeholder Replacement

## WP Summary
Update `src/launcher/core/project_creator.py` `replace_template_placeholders()` to include
`AGENT-RULES.md` in the list of files scanned for placeholder tokens (`{{PROJECT_NAME}}`,
`{{WORKSPACE_NAME}}`). Verifies AC 9 of US-033.

## Status
Review

## Analysis

The current `replace_template_placeholders()` implementation (added in GUI-005/related WPs)
already uses `project_dir.rglob("*.md")` to scan **all** Markdown files under the project
directory tree. This covers `AGENT-RULES.md` automatically because it is a `.md` file
located at `<workspace>/<project_name>/AGENT-RULES.md` after the template's `Project/`
subfolder is renamed by `create_project()`.

To make this coverage explicit and satisfy AC 9 of US-033, the implementation change adds
a docstring update that enumerates `AGENT-RULES.md` among the key files processed, making
the intent unambiguous for future maintainers.

## Implementation

**File changed:** `src/launcher/core/project_creator.py`  
**Function:** `replace_template_placeholders()`

Change: Extended the docstring to explicitly document that `AGENT-RULES.md` is among the
files scanned. No logic change is needed — `rglob("*.md")` already covers it.

## Tests Written

Tests in `tests/DOC-009/test_doc009_placeholder_replacement.py`:

1. `test_agent_rules_in_rglob_scope` — verifies AGENT-RULES.md (a .md file) is matched
   by the rglob("*.md") pattern used in replace_template_placeholders().
2. `test_project_name_replaced_in_agent_rules` — after replacement, `{{PROJECT_NAME}}`
   no longer appears in AGENT-RULES.md content.
3. `test_workspace_name_replaced_in_agent_rules` — after replacement, `{{WORKSPACE_NAME}}`
   no longer appears in AGENT-RULES.md content.
4. `test_actual_project_name_in_agent_rules` — the actual project name appears in the
   replaced content.
5. `test_regression_other_md_files_still_processed` — other .md files (e.g. README.md)
   still have their placeholders replaced (no regression).

## Decisions

- No logic change required: `rglob("*.md")` is already the right approach and already
  covers AGENT-RULES.md. The docstring update makes intent explicit.
- Tests use `tmp_project` fixtures with real file I/O to confirm end-to-end replacement.

## Known Limitations

None.

## Files Changed

- `src/launcher/core/project_creator.py` — docstring update in `replace_template_placeholders()`
- `tests/DOC-009/test_doc009_placeholder_replacement.py` — new test file
- `docs/workpackages/DOC-009/dev-log.md` — this file
- `docs/workpackages/workpackages.csv` — status → In Progress / Review
