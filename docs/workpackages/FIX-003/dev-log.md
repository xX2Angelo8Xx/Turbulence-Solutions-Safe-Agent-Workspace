# Dev Log — FIX-003: INS-004 Template Sync

## Workpackage Summary
- **ID:** FIX-003
- **Type:** Fix
- **Title:** INS-004 Template Sync
- **Branch:** fix/FIX-003
- **Status:** Review
- **Assigned To:** Developer Agent
- **Date:** 2026-03-13

## Problem Statement

Two tests in `tests/INS-004/` were failing:

1. `test_ins004_edge_cases.py::test_vscode_settings_content_matches_default_project`
   — `.vscode/settings.json` text content differed between `templates/coding/` and `Default-Project/`
2. `test_ins004_template_bundling.py::test_template_non_json_files_match_default_project_byte_for_byte`
   — `.github/hooks/scripts/require-approval.sh` content differed between the two directories

Root cause: `Default-Project/` had accumulated JSONC comments in `.vscode/settings.json` and `require-approval.sh` had diverged in `templates/coding/`. The template and source had drifted out of sync.

Additional complication: `Default-Project/.vscode/settings.json` used JSONC comment syntax (not valid strict JSON). The test architecture expects `templates/coding/` to ship **clean JSON** (no comments) and the test `test_vscode_settings_json_is_valid_json` enforces this. Having JSONC in both would have broken that test. The correct fix was to strip the JSONC comments from `Default-Project/.vscode/settings.json` (making it canonical clean JSON) and then sync both files.

## Files Changed

| File | Action |
|------|--------|
| `Default-Project/.vscode/settings.json` | Stripped JSONC comments → clean valid JSON (16 keys preserved) |
| `templates/coding/.vscode/settings.json` | Synced to match `Default-Project/` exactly |
| `templates/coding/.github/hooks/scripts/require-approval.sh` | Synced to match `Default-Project/` byte-for-byte |

## Implementation Details

1. Ran comparison script to identify all mismatches (excluding `__pycache__`/`.pyc`).
2. Found two differing files: `.vscode/settings.json` and `.github/hooks/scripts/require-approval.sh`.
3. Used `shutil.copy2` to sync `require-approval.sh` byte-for-byte.
4. For `settings.json`: stripped all JSONC `//` comments using regex, parsed with `json.loads`, serialized back with `json.dumps(indent=2)` to produce clean canonical JSON. Wrote identical content to both `Default-Project/` and `templates/coding/`.
5. Verified full sync (comparison script output: `Issues: NONE`).
6. All 16 JSON keys preserved; no settings values changed.

## Tests

- **Suite:** `tests/INS-004/`
- **Result:** 66 passed, 0 failed
- Previously failing tests now pass:
  - `test_vscode_settings_content_matches_default_project` ✅
  - `test_template_non_json_files_match_default_project_byte_for_byte` ✅
  - `test_vscode_settings_json_is_valid_json` ✅ (was passing before; confirmed still passing)

## Known Limitations

- `Default-Project/.github/hooks/scripts/__pycache__/` contains `.pyc` files that have no counterpart in `templates/coding/`. These are correctly excluded from the sync (`.pyc` files are build artifacts, not source). The comparison script excludes them by design.
