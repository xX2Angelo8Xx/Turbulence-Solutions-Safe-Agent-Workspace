# Dev Log — INS-004

**Developer:** Developer Agent
**Date started:** 2026-03-12
**Iteration:** 1 (restoration after parallel workgroup branch conflict)

## Objective

Copy `Default-Project/` as the "coding" template under `templates/coding/`, ensuring all safety files (hooks, settings, instructions) are included. Add `TEMPLATES_DIR` constant to `config.py` so the application can locate the templates directory at runtime. Add `list_templates()` function to `project_creator.py` to enumerate available template types. Templates must be discoverable and copyable at runtime from the bundled app.

## Implementation Summary

The original implementation was lost due to a race condition where parallel workgroups performed `git checkout` on shared files. All code was restored from the known-good source (`Default-Project/`) and the test suite in `tests/INS-004/` was used as the specification.

**Template files:** All 14 files from `Default-Project/` (excluding `__pycache__`) were copied verbatim to `templates/coding/` maintaining the exact directory structure. The `.vscode/settings.json` file was already present and was not overwritten.

**`config.py`:** Added `from pathlib import Path` import and `TEMPLATES_DIR: Path = Path(__file__).resolve().parent.parent.parent / "templates"` constant. Resolves from `src/launcher/config.py` up three parent levels to the repo root, then into `templates/`. All existing constants (`APP_NAME`, `VERSION`, `COLOR_*`) are unchanged.

**`project_creator.py`:** Added `list_templates(templates_dir: Path) -> list[str]` function after the existing `create_project()` function. Returns a sorted list of subdirectory names, or an empty list if the path does not exist or is not a directory. Input type is validated with `isinstance()`.

## Files Changed

- `templates/coding/README.md` — created (copied from `Default-Project/README.md`)
- `templates/coding/.gitignore` — created (copied from `Default-Project/.gitignore`)
- `templates/coding/.github/hooks/require-approval.json` — created
- `templates/coding/.github/hooks/scripts/require-approval.ps1` — created
- `templates/coding/.github/hooks/scripts/require-approval.sh` — created
- `templates/coding/.github/hooks/scripts/security_gate.py` — created
- `templates/coding/.github/hooks/scripts/zone_classifier.py` — created
- `templates/coding/.github/instructions/copilot-instructions.md` — created
- `templates/coding/.github/prompts/review.prompt.md` — created
- `templates/coding/.github/skills/ts-code-review/SKILL.md` — created
- `templates/coding/NoAgentZone/README.md` — created
- `templates/coding/Project/app.py` — created
- `templates/coding/Project/README.md` — created
- `templates/coding/Project/requirements.txt` — created
- `src/launcher/config.py` — added `from pathlib import Path` and `TEMPLATES_DIR` constant
- `src/launcher/core/project_creator.py` — added `list_templates()` function

## Tests Written

Existing 30+ tests in `tests/INS-004/test_ins004_template_bundling.py` serve as the full specification and regression suite. No new tests were written — the existing suite was the reference for restoration.

Tests cover:
- `test_templates_root_dir_exists` / `test_coding_template_dir_exists` — directory structure
- `test_coding_readme_exists`, `test_coding_gitignore_exists` — top-level files
- `test_coding_github_dir_exists`, `test_coding_hooks_json_exists`, `test_coding_hooks_scripts_*` — `.github/` tree
- `test_coding_instructions_exists`, `test_coding_prompts_review_exists`, `test_coding_skill_exists` — agent config files
- `test_coding_vscode_dir_exists`, `test_coding_vscode_settings_exists` — `.vscode/`
- `test_coding_noagentzone_*`, `test_coding_project_*` — `NoAgentZone/` and `Project/` contents
- `test_no_pycache_in_template`, `test_no_pyc_files_in_template` — quality guards
- `test_config_templates_dir_*` — `config.TEMPLATES_DIR` existence, type, resolved path, disk presence
- `test_list_templates_*` — `list_templates()` function behavior, edge cases
- `test_template_discoverable_and_copyable` — integration test
- `test_template_files_match_default_project` / `test_coding_template_has_no_extra_files_beyond_default_project` — drift guards

## Known Limitations

- None. Restoration is a complete 1:1 copy of `Default-Project/` (minus `__pycache__`).
