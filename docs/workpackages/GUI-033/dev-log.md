# Dev Log — GUI-033: Rename workspace prefix TS-SAE to SAE

**Status:** Review  
**Assigned To:** Developer Agent  
**Branch:** GUI-033/rename-prefix-sae  
**Date:** 2026-04-01  

---

## Objective

Change the workspace folder prefix from `TS-SAE-` to `SAE-` in all source code.  
"SAE" stands for Safe Agent Environment.

---

## Files Changed

| File | Change |
|------|--------|
| `src/launcher/core/project_creator.py` | Line ~61: comment updated; line ~62: `prefixed_name` f-string; line ~114: docstring token; line ~129: `workspace_name` f-string |
| `src/launcher/gui/app.py` | Line ~446: duplicate-check call; line ~448: error message text; line ~502: success message text |
| `docs/workpackages/workpackages.csv` | GUI-033 status → In Progress / Review |

---

## Implementation Summary

Six string literals of the form `TS-SAE-{...}` were replaced with `SAE-{...}`:

1. **`project_creator.py` line ~61** — comment: `# Prepend the SAE- brand prefix`
2. **`project_creator.py` line ~62** — `prefixed_name = f"SAE-{folder_name}"`
3. **`project_creator.py` line ~114** — docstring: `{{WORKSPACE_NAME}}  → SAE-{project_name}`
4. **`project_creator.py` line ~129** — `workspace_name = f"SAE-{project_name}"`
5. **`app.py` line ~446** — `check_duplicate_folder(f"SAE-{folder_name}", ...)`
6. **`app.py` line ~448/502** — error/success messages use `SAE-` prefix

Template `.md` files (which use the `{{WORKSPACE_NAME}}` placeholder) are **not modified** — they will be updated at runtime with the new `SAE-` prefix once the placeholder replacement logic is updated. Template file content is irrelevant here; only the Python logic that expands the placeholder matters.

Existing tests that reference `TS-SAE-` in test assertions are **not modified** here — they are addressed in DOC-048 (a separate WP listed as a dependency).

---

## Tests Written

- `tests/GUI-033/test_gui033_rename_prefix.py`
  - `test_create_project_uses_sae_prefix` — verifies the created folder name starts with `SAE-`
  - `test_create_project_no_ts_sae_prefix` — verifies the created folder does NOT start with `TS-SAE-`
  - `test_replace_template_placeholders_workspace_name` — verifies `{{WORKSPACE_NAME}}` is replaced with `SAE-{name}`
  - `test_replace_template_placeholders_no_ts_sae` — verifies `TS-SAE-` does not appear in output
  - `test_source_project_creator_no_ts_sae` — grep check: no `TS-SAE` in `project_creator.py`
  - `test_source_app_no_ts_sae` — grep check: no `TS-SAE` in `app.py`

---

## Known Limitations / Notes

- Tests relying on `TS-SAE-` assertions in other WP test suites (DOC-001, DOC-009, DOC-040, FIX-044, GUI-017, INS-004) will be updated via DOC-048.

---

## Test Results

See `docs/test-results/test-results.csv` for logged entry.
