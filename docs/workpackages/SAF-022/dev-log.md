# Dev Log — SAF-022: Add NoAgentZone to VS Code Exclude Settings

**WP ID:** SAF-022  
**Category:** SAF  
**Branch:** SAF-022/noagentzone-exclude  
**Developer:** Developer Agent  
**Date:** 2026-03-17  
**Status:** Review  

---

## Summary

Added `"**/NoAgentZone": true` to both the `files.exclude` and `search.exclude`
sections of both VS Code settings files. Updated the SHA256 integrity hashes in
both `security_gate.py` files via `update_hashes.py`.

---

## Requirements Addressed

1. ✅ `"**/NoAgentZone": true` added to `files.exclude` in `Default-Project/.vscode/settings.json`
2. ✅ `"**/NoAgentZone": true` added to `search.exclude` in `Default-Project/.vscode/settings.json`
3. ✅ Same changes made to `templates/coding/.vscode/settings.json`
4. ✅ Both settings.json files are byte-by-byte identical (in sync)
5. ✅ `update_hashes.py` run for both `Default-Project/` and `templates/coding/`
6. ✅ Both `security_gate.py` files updated with new settings hash and gate hash
7. ✅ Both security_gate.py files are byte-by-byte identical (in sync)

---

## Files Changed

| File | Change |
|------|--------|
| `Default-Project/.vscode/settings.json` | Added `"**/NoAgentZone": true` to `files.exclude` and `search.exclude` |
| `templates/coding/.vscode/settings.json` | Same change (kept in sync with Default-Project) |
| `Default-Project/.github/hooks/scripts/security_gate.py` | Updated `_KNOWN_GOOD_SETTINGS_HASH` and `_KNOWN_GOOD_GATE_HASH` via update_hashes.py |
| `templates/coding/.github/hooks/scripts/security_gate.py` | Same hash update (kept in sync with Default-Project) |
| `tests/SAF-022/test_saf022_noagentzone_exclude.py` | New — 18 tests covering protection, sync, hash integrity, bypass attempts |
| `docs/test-results/test-results.csv` | Added TST-1403 through TST-1420 |
| `docs/workpackages/workpackages.csv` | SAF-022 status updated to Review |

---

## New Hashes

After updating both settings.json files, `update_hashes.py` produced:

- `_KNOWN_GOOD_SETTINGS_HASH`: `fcffb52f64514d8d77d3985b8fa9dd1160cb6cff7b72ca4f7b07a04351200e40`
- `_KNOWN_GOOD_GATE_HASH`: `2d3ba750aa744bc98573e1a3270633008791fd601f9dc9bcfd680f0a3be47ac0`

Both hashes are identical across Default-Project and templates/coding because both
settings.json files are identical.

---

## Tests Written

**File:** `tests/SAF-022/test_saf022_noagentzone_exclude.py`  
**Total:** 18 tests, all pass.

| Class | Tests | Type |
|-------|-------|------|
| `TestDefaultSettingsExclusion` | 5 | Security / Regression |
| `TestTemplateSettingsExclusion` | 5 | Security / Regression |
| `TestSettingsSync` | 2 | Integration |
| `TestHashIntegrity` | 2 | Security |
| `TestBypassAttempt` | 4 | Security |

---

## Test Results

- SAF-022 tests: **18/18 passed**
- Full suite: **2880 passed, 1 pre-existing failure (INS-005 — unrelated), 29 skipped**
- The INS-005 failure predates this WP and is not caused by any change here.

---

## Decisions Made

- Used glob pattern `"**/NoAgentZone"` (with `**`) rather than `"NoAgentZone"` to ensure 
  the exclusion matches at any directory depth, not just at the root level.
- Ran `update_hashes.py` for **both** `Default-Project/` and `templates/coding/` independently 
  to ensure both hashes are computed from their respective local files.
- Both security_gate.py files ended up byte-identical because both settings.json files 
  are identical and both security_gate.py files were already in sync before the update.

---

## Known Limitations

- These are VS Code workspace settings — they only take effect when the project is opened 
  in VS Code with this `.vscode/settings.json` active. They do not affect the security 
  gate's Python-level zone blocking (which is handled separately by `zone_classifier.py`).
