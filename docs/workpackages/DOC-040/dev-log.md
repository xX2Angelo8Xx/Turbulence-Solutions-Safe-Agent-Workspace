# DOC-040 Dev Log — Add .github/version file to template

## Status
In Progress

## Assigned To
Developer Agent

## Goal
Add a `.github/version` file to the agent-workbench template. During project creation, `project_creator.py` replaces the `{{VERSION}}` placeholder with the launcher's actual version string, so every created workspace knows which launcher version created it.

## Implementation Plan
1. Create `templates/agent-workbench/.github/version` with `{{VERSION}}` placeholder.
2. Note: `templates/coding/` was **deleted in FIX-046** — this directory no longer exists. Only `agent-workbench` template is in scope.
3. Update `replace_template_placeholders()` in `src/launcher/core/project_creator.py`:
   - Import `VERSION` from `launcher.config`.
   - Extend the file scan to also process files named `version` (no extension).
   - Add `{{VERSION}}` → VERSION replacement.
4. Write tests validating template file presence and placeholder replacement.

## Files Changed
- `templates/agent-workbench/.github/version` — new file (created)
- `src/launcher/core/project_creator.py` — updated `replace_template_placeholders()` and added import
- `tests/DOC-040/test_doc040_version_file.py` — new test file

## Implementation Summary

### Change 1 — Template file
Created `templates/agent-workbench/.github/version` containing the single-line placeholder `{{VERSION}}`.

### Change 2 — `templates/coding/`: skipped
`templates/coding/` was removed in FIX-046 and no longer exists in the repository. The WP CSV row only references the agent-workbench template, so this is out of scope.

### Change 3 — `project_creator.py`
- Added `from launcher.config import VERSION` import.
- Modified `replace_template_placeholders()` to:
  - Accept an optional `version` parameter defaulting to `VERSION`.
  - Also scan for files named `version` (extensionless) via a second `rglob()` call.
  - Replace `{{VERSION}}` placeholder in both `.md` files and `version` files.

## Tests Written
- `test_agentworkbench_version_file_exists` — template file `templates/agent-workbench/.github/version` exists.
- `test_agentworkbench_version_file_contains_placeholder` — file contains `{{VERSION}}`.
- `test_replace_placeholders_version_replaced` — after `replace_template_placeholders()`, `.github/version` contains a semver string, not the placeholder.
- `test_replace_placeholders_version_not_placeholder` — no `{{VERSION}}` remains after replacement.
- `test_replace_placeholders_md_version_replaced` — `.md` files also get `{{VERSION}}` replaced.

## Test Results
TST-2365 logged: 8 passed, 0 failed. All tests pass. Validate workspace: clean (exit code 0).

## Known Limitations
- None
