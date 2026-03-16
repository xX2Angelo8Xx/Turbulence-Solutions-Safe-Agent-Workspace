# SAF-015 Dev Log — Expand Terminal Allowlist: Write Commands

## WP Details

| Field | Value |
|-------|-------|
| ID | SAF-015 |
| Category | SAF |
| Name | Expand Terminal Allowlist — Write Commands |
| Branch | `SAF-015/terminal-write-commands` |
| Developer | Developer Agent |
| Date | 2026-03-16 |

## Summary

Added 10 write file commands to the `_COMMAND_ALLOWLIST` in `security_gate.py` as a new Category M section. All entries use `path_args_restricted=True` so that every path argument is zone-checked by the existing `_validate_args` infrastructure.

Commands already present in Category J (mkdir, new-item, cp, copy, copy-item, mv, move, move-item) were left unchanged. The WP required adding the following missing entries:

| Command | Role |
|---------|------|
| `set-content` | PowerShell Set-Content |
| `sc` | Alias for Set-Content |
| `add-content` | PowerShell Add-Content |
| `ac` | Alias for Add-Content |
| `out-file` | PowerShell Out-File |
| `rename-item` | PowerShell Rename-Item |
| `ren` | Alias for Rename-Item |
| `tee-object` | PowerShell Tee-Object |
| `tee` | Unix tee |
| `ni` | Alias for New-Item |

## Files Changed

| File | Change |
|------|--------|
| `Default-Project/.github/hooks/scripts/security_gate.py` | Added Category M block (10 entries) before closing `}` of `_COMMAND_ALLOWLIST` |
| `templates/coding/.github/hooks/scripts/security_gate.py` | Identical Category M block added (kept in sync) |
| `docs/workpackages/workpackages.csv` | Status → Review |

## Implementation Notes

- The existing `_validate_args()` function already handles `path_args_restricted=True` by checking ALL path-like tokens against the zone classifier. This covers multi-path commands (rename-item src dest, copy-item src dest) automatically — if any token resolving to a file-system path is in the deny zone, the whole command is denied.
- No logic changes were required in the gate; only allowlist data was added.
- The SAF-008 integrity hash will need to be updated by SAF-025 after all security changes are finalized.
- Templates/coding copy is kept in sync with Default-Project as required.

## Tests Written

**File:** `tests/SAF-015/test_saf015_write_commands.py`  
**Count:** 72 tests

Coverage:
1. `set-content` — allow project, deny .github/.vscode/root
2. `sc` alias — same as set-content  
3. `add-content` — allow project, deny restricted zones
4. `ac` alias — same as add-content
5. `out-file` — allow project, deny restricted zones
6. `rename-item` — allow both paths in project, deny if any path outside
7. `ren` alias — same as rename-item
8. `tee-object` — allow project, deny restricted zones
9. `tee` — allow project, deny restricted zones
10. `ni` alias — allow project, deny restricted zones
11. Alias parity tests (sc==set-content, ac==add-content, ren==rename-item, tee==tee-object)
12. Multi-path edge cases (Category J copy-item, mv, rename-item)
13. Case-insensitive verb matching (Set-Content, Add-Content, Out-File, Rename-Item, Tee-Object, NI)
14. Security protection tests (all new write commands deny .github and .vscode)
15. Security bypass-attempt tests (path traversal ../, dollar-sign variable injection $HOME/$env:)

## Test Results

| Run | Command | Pass | Fail | Skip |
|-----|---------|------|------|------|
| Dev | `pytest tests/SAF-015/ -q --tb=short` | 72 | 0 | 0 |
| Regression | `pytest tests/ -q --tb=line` | 2352 | 8 | 29 |

Pre-existing failures (all existed on `main` before this WP):
- `tests/FIX-009/` (6 tests) — UnicodeDecodeError reading test-results.csv (BUG-045 pre-existing)
- `tests/INS-005/test_ins005_edge_cases.py::TestShortcutsAndUninstaller::test_uninstall_delete_type_is_filesandirs` — pre-existing
- `tests/SAF-008/test_saf008_integrity.py::test_verify_file_integrity_passes_with_good_hashes` — integrity hash not yet updated (pending SAF-025)

No new failures introduced by SAF-015.
