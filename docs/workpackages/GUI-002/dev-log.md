# Dev Log — GUI-002

**Developer:** Developer Agent
**Date started:** 2026-03-12
**Iteration:** 1

## Objective
Populate the project type dropdown dynamically by listing subdirectories of templates/.
Initial template types: "Coding" and "Creative / Marketing".
Goal: dropdown shows all available template types; adding a template folder
automatically adds a new option without code changes.

## Implementation Summary
- Added `_format_template_name(raw: str) -> str` module-level helper in app.py
  that converts raw directory names to human-readable display strings
  (hyphens and underscores become spaces, result is title-cased).
- Added `App._get_template_options() -> list[str]` instance method that calls
  the existing `list_templates(TEMPLATES_DIR)` from project_creator.py and
  applies the formatter to every entry.
- Updated `App._build_ui()` to replace the hardcoded `values=["Coding"]` with a
  call to `self._get_template_options()`.
- Added `TEMPLATES_DIR` to the import from `launcher.config` in app.py.
- Added `from launcher.core.project_creator import list_templates` to app.py.
- Created `templates/creative-marketing/README.md` as a placeholder for the
  "Creative Marketing" template type, satisfying the stated initial types.
  Display name produced: "Creative Marketing" (the slash variant in the WP
  description — "Creative / Marketing" — is illustrative; the AC uses "e.g.").

## Files Changed
- `src/launcher/gui/app.py` — added `_format_template_name`, `_get_template_options`, updated imports and dropdown instantiation
- `templates/creative-marketing/README.md` — new placeholder template directory

## Tests Written
- `test_format_template_name_single_word` — "coding" → "Coding"
- `test_format_template_name_hyphenated` — "creative-marketing" → "Creative Marketing"
- `test_format_template_name_underscore` — "data_science" → "Data Science"
- `test_format_template_name_mixed` — "my-data_project" → "My Data Project"
- `test_format_template_name_empty` — "" → ""
- `test_get_template_options_with_real_templates_dir` — real templates/ contains at least "Coding" and "Creative Marketing"
- `test_get_template_options_with_temp_dir` — fresh tmpdir with two subdirs returns two formatted names
- `test_get_template_options_empty_dir` — empty tmpdir returns empty list
- `test_get_template_options_missing_dir` — non-existent path returns empty list
- `test_get_template_options_skips_files` — files inside templates/ are not included, only directories
- `test_dropdown_created_with_dynamic_values` — CTkOptionMenu is called with values from _get_template_options
- `test_adding_template_dir_adds_option` — adding a new subdir to a temp templates/ shows up in options
- `test_dropdown_not_hardcoded` — values are not the literal hardcoded list ["Coding"]
- `test_creative_marketing_dir_exists` — templates/creative-marketing/ directory exists in repo

## Known Limitations
- Display names are derived mechanically from directory names (hyphen/underscore → space, title case).
  If a template needs a display name with special characters (e.g. "/"), a metadata file approach
  would be needed — deferred to a future WP.
- The dropdown is populated once at window construction time; it does not refresh dynamically
  while the app is running. Full live-refresh is deferred to a future WP.

## Test Run — 2026-03-12

- **Suite:** tests/GUI-002/ — 25/25 passed (TST-487 through TST-512 logged)
- **Full suite:** Pre-existing failures in SAF-008 (not yet implemented), INS-004
  (settings.json content drift), INS-012 (*.spec gitignore), SAF-010 (legacy shell
  reference) — all unrelated to GUI-002. No new regressions introduced.
- **Status set to:** Review
