# FIX-079 Dev Log — Show NoAgentZone in VS Code File Explorer

**WP ID:** FIX-079  
**Category:** Fix  
**Status:** Review  
**Assigned To:** Developer Agent  
**Date:** 2026-03-30  
**Bug:** BUG-146  
**User Story:** US-064  

---

## Problem Statement

`templates/agent-workbench/.vscode/settings.json` had `"**/NoAgentZone": true` in both
`files.exclude` and `search.exclude`. The `files.exclude` entry hides the NoAgentZone
folder from the VS Code file explorer, making it invisible to human users who legitimately
need to manage its contents. The security gate handles all actual access control — explorer
visibility does not grant agent access.

### Relationship to FIX-042

FIX-042 addressed the same root cause for files named
`Default-Project/.vscode/settings.json` and `templates/coding/.vscode/settings.json`.
Those paths no longer exist in the repository. The current production file is
`templates/agent-workbench/.vscode/settings.json`, which still had the regression.
FIX-079 applies the same fix to the current canonical file.

---

## Implementation

### Files Modified

1. **`templates/agent-workbench/.vscode/settings.json`**  
   Removed `"**/NoAgentZone": true` from `files.exclude` block only.  
   Entry retained in `search.exclude` (prevents agent VS Code search indexing).

2. **`templates/agent-workbench/.github/hooks/scripts/security_gate.py`**  
   Updated SHA256 integrity hashes via `update_hashes.py` after settings.json change:  
   - `_KNOWN_GOOD_SETTINGS_HASH` → `1786325dfd2a3e007112c63e0e82c50fe76e1e4e8c022439a6d3597bc2248447`  
   - `_KNOWN_GOOD_GATE_HASH` → `9d4249569be46f2f6f97ca82afefb2f366c3fe502f321dc991e35146ea60caac`

### Tracking Files Updated

- `docs/workpackages/workpackages.csv` — Status set to `In Progress` / `Review`

---

## Security Analysis

- **`search.exclude` retained** — VS Code search and the built-in `grep_search` / `file_search`
  tools do not index NoAgentZone content. Agent text and file searches remain blocked.
- **Security gate unchanged** — All zone-blocking logic in `security_gate.py` targets
  `noagentzone` at the path-classification level (see `zone_classifier.classify()`). This is
  completely independent of `files.exclude` settings. No zone enforcement code was touched.
- **Integrity hashes updated** — `_KNOWN_GOOD_SETTINGS_HASH` and `_KNOWN_GOOD_GATE_HASH`
  refreshed by `update_hashes.py`. SAF-008 hash verification continues to detect any future
  unauthorised changes to settings.json.

---

## Tests Written

`tests/FIX-079/test_fix079_noagentzone_visible.py`

- `test_settings_json_is_valid_json` — settings.json parses without error
- `test_noagentzone_not_in_files_exclude` — `**/NoAgentZone` absent from `files.exclude`
- `test_noagentzone_in_search_exclude` — `**/NoAgentZone` present in `search.exclude` with value `true`
- `test_github_still_in_files_exclude` — `.github` not accidentally removed from `files.exclude`
- `test_vscode_still_in_files_exclude` — `.vscode` not accidentally removed from `files.exclude`
- `test_security_gate_settings_hash_valid` — `_KNOWN_GOOD_SETTINGS_HASH` matches actual file hash
- `test_security_gate_gate_hash_valid` — `_KNOWN_GOOD_GATE_HASH` canonical hash matches stored value
- `test_noagentzone_zone_deny_direct_path` — zone_classifier denies a direct NoAgentZone path
- `test_noagentzone_zone_deny_nested_path` — zone_classifier denies a nested path inside NoAgentZone

---

## Test Results

All 9 tests pass. See `docs/test-results/test-results.csv` for logged results.
