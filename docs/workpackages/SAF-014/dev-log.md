# SAF-014 Dev Log — Expand Terminal Allowlist: Read Commands

**Status:** In Progress  
**Assigned To:** Developer Agent  
**Branch:** `SAF-014/terminal-read-commands`  
**Date Started:** 2026-03-16  

---

## Objective

Add the following read-only file inspection commands to the terminal command allowlist in `security_gate.py` with `path_args_restricted=True`:

- `get-content` (PowerShell) + alias `gc`
- `select-string` (PowerShell grep-like)
- `findstr` (Windows grep)
- `grep` (Unix)
- `wc` (Unix word/line count)
- `file` (Unix file type)
- `stat` (Unix/Windows file info)

Each command must be allowed when ALL path arguments target the project folder, and denied when ANY path argument is outside the project folder.

---

## Implementation Plan

1. Add all 8 entries to `_COMMAND_ALLOWLIST` in Category G (Read-only File Inspection).
2. Sync the change to `templates/coding/.github/hooks/scripts/security_gate.py`.
3. Write tests in `tests/SAF-014/`.

---

## Files Changed

- `Default-Project/.github/hooks/scripts/security_gate.py` — 8 new allowlist entries
- `templates/coding/.github/hooks/scripts/security_gate.py` — synced copy

---

## Implementation Summary

Added 8 new entries to Category G of `_COMMAND_ALLOWLIST`:

| Command | Notes |
|---------|-------|
| `get-content` | PowerShell Get-Content; all path args zone-checked |
| `gc` | Alias for Get-Content |
| `select-string` | PowerShell Select-String; path args zone-checked |
| `findstr` | Windows findstr; path args zone-checked |
| `grep` | Unix grep; path args zone-checked |
| `wc` | Unix wc; path args zone-checked |
| `file` | Unix file type detection; path args zone-checked |
| `stat` | Unix/Windows stat; path args zone-checked |

All entries use `path_args_restricted=True` and `allow_arbitrary_paths=False`, ensuring the existing zone-check logic in `_validate_args()` rejects any argument pointing outside the project folder.

---

## Tests Written

- `tests/SAF-014/test_saf014_read_commands.py`
  - Each command allowed when targeting project folder
  - Each command denied when targeting `.github/`
  - Each command denied when targeting root files
  - Alias `gc` = `get-content` parity
  - Mixed paths (one inside, one outside project) → deny

---

## Known Limitations

None. The existing `_validate_args()` path-checking logic handles all zone enforcement automatically once entries are in the allowlist.

---

## Iteration History

### Iteration 1 (2026-03-16)
Initial implementation. All tests pass.
