# SAF-032 Dev Log — Block file tools in .git/ directories

## Status
In Progress

## Assigned To
Developer Agent

## Goal
Deny `create_file`, `replace_string_in_file`, `multi_replace_string_in_file`, `read_file`, and `list_dir` when the target path is inside the `.git/` directory within the project folder.

## Acceptance Criteria
- `create_file` targeting `ProjectFolder/.git/hooks/pre-commit` → deny
- `read_file` targeting `ProjectFolder/.git/HEAD` → deny
- `list_dir` targeting `ProjectFolder/.git/` → deny
- `replace_string_in_file` targeting `ProjectFolder/.git/config` → deny
- Normal project folder operations unaffected
- Path traversal (e.g. `ProjectFolder/src/../../.git/config`) → deny
- Case variation (e.g. `ProjectFolder/.GIT/config`) → deny (Windows)

---

## Implementation Plan

### zone_classifier.py
Add `is_git_internals(path: str) -> bool` helper that:
- Normalizes the path (via `normalize_path`) so traversal and case are handled
- Returns `True` if `/.git/` appears anywhere in the normalized path, or the path ends with `/.git`

### security_gate.py
Three insertion points after zone == "allow":
1. `validate_write_tool` — checked after zone=="allow" for all `_WRITE_TOOLS`
2. `validate_multi_replace_tool` — checked for each `filePath` entry after zone=="allow"
3. `decide()` general exempt-tools block — catches `read_file`, `list_dir` and all other exempt tools

---

## Files Changed

- `templates/coding/.github/hooks/scripts/zone_classifier.py` — added `is_git_internals()`
- `templates/coding/.github/hooks/scripts/security_gate.py` — added git-internals check in three locations
- `tests/SAF-032/test_saf032_git_block.py` — test suite (8 test cases)

---

## Implementation Summary

### `is_git_internals(path)` in zone_classifier.py
The function normalizes the raw path first (lowercasing, backslash→forward-slash,
`..` resolution) so that:
- `.GIT/config` lowercases to `.git/config` → caught
- `src/../../.git/config` resolves then is joined with ws_root prefix → caught
- Bare `.git` directory (no trailing slash) is caught by `endswith("/.git")`

### Security gate changes
- `validate_write_tool`: after zone=="allow", call `is_git_internals(raw_path)` → deny if True
- `validate_multi_replace_tool`: for each entry, after zone=="allow", same check
- `decide()` general path: after zone=="allow" for exempt tools, same check

### Note on Default-Project
Default-Project/ is NOT modified (will be removed in FIX-046).

### Post-change: run update_hashes.py
After all security_gate.py changes, `update_hashes.py` is run to re-embed the correct SHA256 hash.

---

## Tests Written

| Test | Description | Expected |
|------|-------------|----------|
| test_create_file_git_hooks | create_file → .git/hooks/pre-commit | deny |
| test_create_file_git_config | create_file → .git/config | deny |
| test_read_file_git_head | read_file → .git/HEAD | deny |
| test_list_dir_git | list_dir → .git/ | deny |
| test_replace_string_in_file_git | replace_string_in_file → .git/config | deny |
| test_normal_project_file_allowed | create_file/read_file → src/app.py | allow |
| test_path_traversal_git | create_file → src/../../.git/config | deny |
| test_case_variation_git | create_file → .GIT/config (Windows) | deny |

---

## Iteration Log

### Iteration 1 (Initial implementation)
- Added `is_git_internals()` to zone_classifier.py
- Added git-internals check to validate_write_tool, validate_multi_replace_tool, decide()
- Ran update_hashes.py to refresh integrity hashes
- All 8 SAF-032 tests pass; full suite regression clean
