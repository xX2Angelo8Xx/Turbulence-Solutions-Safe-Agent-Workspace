# SAF-045 — Verify grep_search Scoping and search.exclude

**Status:** Review  
**Branch:** SAF-045/grep-search-verify  
**Assigned To:** Developer Agent  
**User Story:** US-037  

---

## Summary

This workpackage verifies:
1. `grep_search` is correctly scoped to the project folder (implemented by FIX-021) and cannot return restricted-zone content.
2. VS Code `search.exclude` in `templates/coding/.vscode/settings.json` covers `.github/`, `.vscode/`, and `NoAgentZone/` for both `files.exclude` and `search.exclude`.
3. Targeted tests confirm no search tool leaks paths/content from restricted zones.

---

## Verification Findings

### grep_search scoping (FIX-021)

`validate_grep_search()` in `templates/coding/.github/hooks/scripts/security_gate.py` correctly:
- Denies `includeIgnoredFiles=True` (and truthy equivalents: `"true"`, `1`)
- Denies any `includePattern` that targets `.github/`, `.vscode/`, or `NoAgentZone/`
- Denies `includePattern` containing path traversal sequences (`..`)
- Allows all other queries (no `filePath` field in grep_search → VS Code `search.exclude` handles scoping)
- Supports both flat (test) and nested `tool_input` (VS Code hook) payload formats

This behaviour was implemented by FIX-021 and confirmed by existing FIX-021 tests.

### search.exclude coverage — Gap Found and Fixed

**Gap found:** `templates/coding/.vscode/settings.json` was missing `**/NoAgentZone` from `files.exclude`. It was present in `search.exclude` but not in `files.exclude`.

**Fix applied:** Added `"**/NoAgentZone": true` to `files.exclude`. Updated `_KNOWN_GOOD_SETTINGS_HASH` and `_KNOWN_GOOD_GATE_HASH` in `security_gate.py` to match the new settings.json content.

`templates/coding/.vscode/settings.json` now contains:
```json
"files.exclude": {
  ".github": true,
  ".vscode": true,
  "**/NoAgentZone": true
},
"search.exclude": {
  ".github": true,
  ".vscode": true,
  "**/NoAgentZone": true
}
```

All three restricted zones are now covered in both `files.exclude` and `search.exclude`.

---

## Files Changed

| File | Change Type | Description |
|------|-------------|-------------|
| `templates/coding/.vscode/settings.json` | Modified | Added `**/NoAgentZone` to `files.exclude` (gap fix) |
| `templates/coding/.github/hooks/scripts/security_gate.py` | Modified | Updated `_KNOWN_GOOD_SETTINGS_HASH` and `_KNOWN_GOOD_GATE_HASH` to reflect settings.json change |
| `tests/SAF-045/test_saf045_grep_search_scoping.py` | New | 33 tests verifying grep_search scoping and settings.json coverage |
| `tests/SAF-045/__init__.py` | New | Package marker for test discovery |
| `docs/workpackages/SAF-045/dev-log.md` | New | This log |

---

## Tests Written

**File:** `tests/SAF-045/test_saf045_grep_search_scoping.py`  
**Framework:** pytest  
**Count:** 33 tests

### Deny group (14 tests)
- `includePattern` targeting `.github/**`, `.vscode/**`, `NoAgentZone/**`
- `includePattern` bare `.github`, bare `NoAgentZone`
- `includePattern` with path traversal (`../../../etc/**`, `project/../../.github/**`)
- `includeIgnoredFiles=True`, `"true"`, `1`
- Nested `tool_input` format: `.github/**`, `NoAgentZone/**`, `includeIgnoredFiles=True`
- `decide()` integration: `.github`, `.vscode`, `NoAgentZone`, `includeIgnoredFiles`

### Allow group (11 tests)
- No parameters
- Query only
- `project/**`, `project/**/*.py`
- Nested `tool_input` with project-scoped pattern
- `includeIgnoredFiles=False` with project pattern
- `decide()` integration: no params, project pattern

### settings.json verification group (8 tests)
- `files.exclude` contains `.github`, `.vscode`, `NoAgentZone`
- `search.exclude` contains `.github`, `.vscode`, `NoAgentZone`
- `files.exclude` covers all three restricted zones
- `search.exclude` covers all three restricted zones

---

## Test Results

All 33 tests pass.  
Run: `.venv\Scripts\python.exe -m pytest tests/SAF-045/ -v`

---

## Acceptance Criteria Check

| AC | Description | Status |
|----|-------------|--------|
| AC 4 | grep_search verified project-folder-only | PASS |
| AC 5 | search.exclude covers all restricted zones | PASS |
| AC 7 | No search tool leaks paths from restricted zones | PASS |

---

## Known Limitations

None. One gap was found and fixed (missing `**/NoAgentZone` from `files.exclude`). All other controls were already correct.
