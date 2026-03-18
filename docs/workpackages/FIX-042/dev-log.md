# FIX-042 Dev Log — Make NoAgentZone Visible in VS Code File Explorer

**WP ID:** FIX-042  
**Category:** Fix  
**Status:** Review  
**Assigned To:** Developer Agent  
**Date:** 2026-03-18  
**Bug:** BUG-076  
**User Story:** US-021  

---

## Problem Statement

SAF-022 added `"**/NoAgentZone": true` to **both** `files.exclude` and `search.exclude` in both VS Code settings.json files. While `search.exclude` is correct (prevents agent search tools from finding NoAgentZone content), `files.exclude` also hides the folder from the VS Code file explorer — making it invisible to human users who legitimately need to access it.

---

## Implementation

### Files Modified

1. **`Default-Project/.vscode/settings.json`**  
   Removed `"**/NoAgentZone": true` from `files.exclude` block only. Entry retained in `search.exclude`.

2. **`templates/coding/.vscode/settings.json`**  
   Same change as above. Also synced from Default-Project after hash update.

3. **`Default-Project/.github/hooks/scripts/security_gate.py`**  
   Updated SHA256 integrity hashes via `update_hashes.py` after settings.json change.  
   - `_KNOWN_GOOD_SETTINGS_HASH` → `623c80d355b2a69390d8c95e896b1ecbd33a3dc73d8f2a73b30eac5dfec47b6b`  
   - `_KNOWN_GOOD_GATE_HASH` → `8f67333d018dfdefc0ffe9312c0236b007aa414d3a5a4cff733c3a57957ab5ce`

4. **`templates/coding/.github/hooks/scripts/security_gate.py`**  
   Synced from Default-Project (contains the updated hashes).

### Tracking Files Updated

- `docs/bugs/bugs.csv` — Added BUG-076 entry
- `docs/workpackages/workpackages.csv` — Added FIX-042 entry

---

## Security Analysis

- **`search.exclude` remains unchanged** — VS Code's built-in text and file search still ignores NoAgentZone content, protecting against agent `grep_search` / `file_search` bypass via VS Code indexing.
- **Security gate unchanged** — All access-blocking logic in `security_gate.py` still denies reads/writes to NoAgentZone directories. No zone enforcement code was touched.
- **Integrity hashes updated** — SAF-008 hash verification reflects the new settings.json content.

---

## Tests Written

`tests/FIX-042/test_fix042_noagentzone_visible.py`

- `test_noagentzone_not_in_files_exclude_default`
- `test_noagentzone_not_in_files_exclude_template`
- `test_noagentzone_still_in_search_exclude_default`
- `test_noagentzone_still_in_search_exclude_template`
- `test_github_still_in_files_exclude`
- `test_vscode_still_in_files_exclude`
- `test_settings_files_are_in_sync`
- `test_security_gate_hashes_valid`

---

## Test Results

All 8 tests pass. See `docs/test-results/test-results.csv` for logged results.
