# DOC-003 Dev Log — Update copilot-instructions.md Template with Placeholders

## Summary

Replace the hardcoded `Project/` folder reference in both copilot-instructions.md
template files with `{{PROJECT_NAME}}/` so that after placeholder substitution
(performed by `replace_template_placeholders()` from DOC-001) the instructions
correctly name the actual project folder.

## Files Changed

| File | Change |
|------|--------|
| `Default-Project/.github/instructions/copilot-instructions.md` | `Project/` → `{{PROJECT_NAME}}/` in Workspace Rules |
| `templates/coding/.github/instructions/copilot-instructions.md` | Same change |

## Implementation Notes

- Only the line that says `The \`Project/\` folder is the designated working directory.` was touched.
- All other folder names (`NoAgentZone/`, `.github/`, `.vscode/`) are literal and must stay unchanged.
- Both template files are kept identical, as required by the WP description.

## Tests Written

- `tests/DOC-003/test_doc003_placeholders.py`
  - `test_default_project_uses_placeholder` — confirms `{{PROJECT_NAME}}` is present in Default-Project file
  - `test_default_project_no_bare_project_folder` — confirms bare `Project/` folder reference is gone from Default-Project file
  - `test_templates_coding_uses_placeholder` — confirms `{{PROJECT_NAME}}` is present in templates/coding file
  - `test_templates_coding_no_bare_project_folder` — confirms bare `Project/` folder reference is gone from templates/coding file
  - `test_files_are_identical` — confirms both template files have identical content
  - `test_placeholder_replaced_in_copy` — simulates `replace_template_placeholders()` on a tmp copy and verifies replacement

## Test Results

All 6 tests pass. See `docs/test-results/test-results.csv` for run log.

## Status

Completed — handed off for Review.
