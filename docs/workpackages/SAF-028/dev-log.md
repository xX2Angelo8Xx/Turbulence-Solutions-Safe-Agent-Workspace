# SAF-028 Dev Log — Fix Bare Directory Enumeration from Workspace Root

**WP ID:** SAF-028  
**Branch:** saf-028  
**Developer:** Developer Agent  
**Date:** 2026-03-18  
**Status:** Review

---

## Summary

Added **Step 8** to the terminal sanitization pipeline in `security_gate.py` to catch bare directory listing commands (`dir`, `ls`, `Get-ChildItem`, `gci`, `tree`, `find`) executed with no path argument when the CWD is the workspace root or an ancestor of deny zones.

**Security finding addressed:** Security Audit V2.0.0 — Findings 1 & 2. Bare `dir`, `ls`, `Get-ChildItem` commands with no path argument, run from the workspace root, could enumerate `.github/`, `.vscode/`, and `NoAgentZone/` contents despite SAF-006 only checking explicit path arguments.

---

## Implementation

### Files Changed

1. **`Default-Project/.github/hooks/scripts/security_gate.py`**
   - Added `_BARE_LISTING_VERBS: frozenset` constant (near `_INHERENTLY_RECURSIVE_COMMANDS`): `{"dir", "ls", "get-childitem", "gci", "tree", "find"}`
   - Added **Step 8** in `_validate_args()` after the existing Step 7 (SAF-006) block:
     - Identifies bare listing verbs with no real path argument (flags like `-Force`, `-Recurse`, `/b`, `/a` are excluded; empty quoted strings do not count as paths)
     - When no path arg found: calls `os.getcwd()` to get the implicit target
     - Runs `_is_ancestor_of_deny_zone(cwd, ws_root)` — if CWD is workspace root or higher, denies
     - If CWD is inside the project folder (not an ancestor of deny zones), allows
   - Hash constant `_KNOWN_GOOD_GATE_HASH` updated via `update_hashes.py`

2. **`templates/coding/.github/hooks/scripts/security_gate.py`**
   - Synced from `Default-Project/` (identical content)

3. **`docs/workpackages/workpackages.csv`**
   - SAF-028 status updated from `Open` → `In Progress` → `Review`

---

## Design Decisions

- **Step 8 uses `os.getcwd()`** (not the static `"."` → `ws_root` mapping used in Step 7). This allows tests to mock `sg.os.getcwd` independently and properly tests the CWD-is-inside-project-folder ALLOW path.
- **Defence in depth:** Step 8 complements Step 7. Recursive commands are caught by both steps; non-recursive bare listing commands (e.g. plain `dir`, `ls`, `Get-ChildItem`) are only caught by Step 8.
- **Empty quoted strings** (`dir ''`) treated as no real path — cannot bypass the check by passing an empty string argument.

---

## Tests Written

Tests already existed in `tests/SAF-028/` from a previous agent. All 21 tests now pass.

Test file: `tests/SAF-028/test_saf028_bare_enumeration.py`

| Test | Result |
|------|--------|
| `test_gci_recurse_no_path_ws_root_denied` | PASS |
| `test_gci_recurse_force_no_path_denied` | PASS |
| `test_dir_bare_ws_root_denied` | PASS |
| `test_ls_bare_ws_root_denied` | PASS |
| `test_tree_bare_ws_root_denied` | PASS |
| `test_find_bare_ws_root_denied` | PASS |
| `test_dir_explicit_project_path_allowed` | PASS |
| `test_ls_explicit_project_path_allowed` | PASS |
| `test_gci_recurse_explicit_project_path_allowed` | PASS |
| `test_gci_bare_no_recurse_ws_root_denied` | PASS |
| `test_gci_alias_bare_ws_root_denied` | PASS |
| `test_dir_bare_project_cwd_allowed` | PASS |
| `test_ls_bare_project_cwd_allowed` | PASS |
| `test_gci_bare_project_cwd_allowed` | PASS |
| `test_dir_windows_flags_only_no_path_denied` | PASS |
| `test_dir_slash_a_no_path_denied` | PASS |
| `test_dir_explicit_github_denied` | PASS |
| `test_ls_explicit_vscode_denied` | PASS |
| `test_gci_explicit_github_denied` | PASS |
| `test_dir_quoted_empty_string_no_real_path_denied` | PASS |
| `test_bare_listing_verbs_constant_exists` | PASS |

---

## Regression Results

- **SAF-006:** 65/65 pass  
- **SAF-026:** 111/111 pass  
- **Full suite:** 3447 pass, 3 pre-existing failures (FIX-009 TST-IDs, INS-005 Inno Setup — unrelated to this WP), 29 skipped, 1 xfailed

---

## Known Limitations

None. The fix is narrow in scope and does not affect any other security checks.

---

## Iteration 2 — 2026-03-18

**Triggered by:** Tester Agent review (test-report.md) — 4 bypass vectors found.

### Bugs Fixed

| Bug | Command | Fix Applied |
|-----|---------|-------------|
| BUG-066 | `dir "   "` | Changed `if not stripped:` → `if not stripped.strip():` to exclude whitespace-only tokens |
| BUG-067 | `gci -Include *.py`, `gci -Filter *.py` | Added `_prev_was_flag_s8` tracking; non-path tokens following a flag are skipped as flag values |
| BUG-068 | `dir -Recurse -Depth 1`, `Get-ChildItem -Depth 1` | Same `_prev_was_flag_s8` fix covers numeric flag values |
| BUG-069 | `ls .` | After collecting `path_args_s8`, filter out `.` and `./` — bare dot is semantically CWD |

### Implementation Notes

- `_prev_was_flag_s8` uses a path-aware skip: if the token following a `-`-prefixed flag IS `_is_path_like()`, it is still added to `path_args_s8` (handles `-Recurse Project/` correctly — `Project/` must not be consumed as `-Recurse`'s "value").
- Windows-style short flags (`/b`, `/a`) set `_prev_was_flag_s8 = False` since they do not consume a following value token.
- Hash constant `_KNOWN_GOOD_GATE_HASH` re-updated via `update_hashes.py`.
- Template at `templates/coding/.github/hooks/scripts/security_gate.py` re-synced.
- `@pytest.mark.xfail` markers removed from 6 tests in `test_saf028_tester_edge_cases.py`.

### Files Changed

1. `Default-Project/.github/hooks/scripts/security_gate.py` — Step 8 bugfixes + hash updated
2. `templates/coding/.github/hooks/scripts/security_gate.py` — synced
3. `tests/SAF-028/test_saf028_tester_edge_cases.py` — xfail markers removed

### Test Results

| Suite | Pass | Fail |
|-------|------|------|
| tests/SAF-028/ (all) | 31 | 0 |
| tests/SAF-006/ | 65 | 0 |
| tests/SAF-026/ | 111 | 0 |
