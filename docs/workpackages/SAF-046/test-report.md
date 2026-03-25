# Test Report — SAF-046

**WP:** SAF-046 — Enable workspace root read access in security gate  
**Tester:** Tester Agent  
**Date:** 2026-03-25  
**Verdict:** PASS

---

## Summary

SAF-046 adds `is_workspace_root_readable()` to `zone_classifier.py` and wires it into the exempt-tool path in `security_gate.py::decide()` so that `read_file` and `list_dir` on the workspace root and its direct non-denied children are allowed. All acceptance criteria are met and all security controls are intact.

---

## Acceptance Criteria Review

| # | Criterion | Result |
|---|-----------|--------|
| 1 | `read_file` on workspace root config files succeeds | PASS |
| 2 | `list_dir` on the workspace root itself succeeds | PASS |
| 3 | `.github/`, `.vscode/`, `NoAgentZone/` remain denied | PASS |
| 4 | Paths deeper than 1 level below workspace root (non-project) denied | PASS |
| 5 | Write operations to workspace root remain denied | PASS |

---

## Code Review

### `zone_classifier.py` — `is_workspace_root_readable()`

**Design correctness:** Uses `PurePosixPath.relative_to()` for the depth check — consistent with the existing `classify()` method. The `len(rel.parts) == 1` constraint correctly limits access to direct children only.

**Fail-closed stance:** For paths outside the workspace root, `relative_to()` raises `ValueError` and the function returns `False`. ✓

**Deny-zone check:** Checks `rel.parts[0] not in _DENY_DIRS` which is the same set used by `classify()` (`.github`, `.vscode`, `noagentzone`) — consistent. ✓

**Relative path handling:** Resolves relative paths the same way `classify()` does before the zone check. ✓

**One exposure noted:** `is_workspace_root_readable()` returns `True` for the `.git` directory (it is a direct child and not in `_DENY_DIRS`). The `.git` block is correctly handled by `is_git_internals()` called immediately afterward in `decide()`. This is by design — the defense-in-depth is adequate. A tester edge case test documents this behavior explicitly.

### `security_gate.py` — `decide()` exempt-tool path

The SAF-046 block is inserted **after** the `zone == "allow"` early return and an additional `is_git_internals()` check is applied before returning `"allow"`. This means:
- Write tools (`_WRITE_TOOLS`, `multi_replace_string_in_file`) are handled before the exempt-tool block and still route through `validate_write_tool()` / `validate_multi_replace_tool()` → only project folder is writable. ✓
- `grep_search`, `semantic_search`, `file_search`, `search_subagent`, `memory`, `create_directory`, `get_errors`, `vscode_listCodeUsages`, `vscode_renameSymbol` all have dedicated validators called before the exempt-tool block — SAF-046 does not widen their scope. ✓
- `.git` at workspace root is still denied end-to-end via `is_git_internals()`. ✓

### `tests/SAF-013/test_saf013_edge_cases.py`

Two existing tests were updated to reflect the new behavior:
- `test_decide_root_level_file_returns_deny` → now asserts `"allow"` for `read_file` on a root file  
- `test_decide_workspace_root_itself_returns_deny` → now asserts `"allow"` for `list_dir` on root  

These are correct behavioural updates. ✓

---

## Test Runs

| TST-ID | Name | Type | Status |
|--------|------|------|--------|
| TST-2198 | SAF-046 workspace root access tests (Developer) | Unit | Pass — 22 passed |
| TST-2199 | SAF-046 tester edge-case tests | Security | Pass — 18 passed |
| TST-2200 | SAF-046 full test suite regression check | Regression | Pass — 6591 passed, 72 pre-existing failures unchanged |

---

## Tester Edge Cases Added

File: `tests/SAF-046/test_saf046_tester_edge_cases.py` (18 tests)

| Test | Purpose |
|------|---------|
| `test_is_workspace_root_readable_returns_true_for_git_dir` | Documents that `.git` alone does not block in `is_workspace_root_readable` — defense-in-depth is in `decide()` |
| `test_decide_still_denies_git_dir_at_workspace_root` | End-to-end: `.git` at root → deny |
| `test_decide_denies_git_config_two_levels_deep` | `.git/config` two levels deep → deny |
| `test_git_bash_path_to_workspace_root_file_allowed` | `/c/workspace/pyproject.toml` normalises and allows |
| `test_wsl_path_to_workspace_root_file_allowed` | `/mnt/c/workspace/pyproject.toml` normalises and allows |
| `test_gitignore_at_workspace_root_readable` | `.gitignore` is not a deny zone — must be readable |
| `test_editorconfig_at_workspace_root_readable` | `.editorconfig` is not a deny zone — must be readable |
| `test_edit_file_on_workspace_root_denied` | `edit_file` on root file → deny |
| `test_replace_string_in_file_on_workspace_root_denied` | `replace_string_in_file` on root file → deny |
| `test_multi_replace_on_workspace_root_denied` | `multi_replace_string_in_file` on root file → deny |
| `test_write_file_on_workspace_root_denied` | `write_file` on root file → deny |
| `test_github_with_trailing_slash_denied` | `.github/` trailing slash stripped → still deny |
| `test_vscode_with_trailing_slash_denied` | `.vscode/` trailing slash stripped → still deny |
| `test_list_dir_with_path_field_workspace_root_allow` | `list_dir` using native `path` field on root → allow |
| `test_list_dir_with_path_field_github_deny` | `list_dir` with `path` field → `.github` → deny |
| `test_list_dir_with_directory_field_workspace_root_allow` | `list_dir` using `directory` field → allow |
| `test_c0_control_char_in_path_does_not_bypass_deny` | `.\x01github` → stripped to `.github` → deny |
| `test_control_char_in_noagentzone_still_denied` | `NoAgent\x02Zone` → stripped to `noagentzone` → deny |

---

## Security Analysis

**Attack vectors considered:**

1. **Bypass via path traversal to `.github`:** Tested by Developer — `safe/../.github` resolves to `.github` → deny. ✓  
2. **Bypass via C0 control character injection:** `.\x01github` stripped to `.github` → deny. ✓  
3. **Bypass via case variation:** `.GITHUB`, `.VSCODE`, `NoAgentZone` → all denied (case-insensitive). ✓  
4. **Bypass via Windows backslash:** Normalized and allowed only for valid root files. ✓  
5. **Bypass via Git Bash / WSL path:** Normalized correctly; workspace root files allowed, deny zones still denied. ✓  
6. **Write escalation via read-only function:** `is_workspace_root_readable()` is not called for write tools — they route through `validate_write_tool()` and `validate_multi_replace_tool()` which only allow the project folder. Tested for all 4 write tool variants. ✓  
7. **`.git` internals access:** `is_workspace_root_readable()` returns `True` for `.git` alone, but `is_git_internals()` in `decide()` blocks it. `.git/config` (depth > 1) is blocked by the `len(rel.parts) == 1` guard. ✓  
8. **Scope creep via exempt tool block:** The `is_workspace_root_readable()` call is only reached in the exempt-tool fallback path — all dedicated validators run first. ✓

**Race conditions:** None — the function is stateless and pure.  
**Resource leaks:** None — no file I/O in the new code.

---

## Regressions

No regressions introduced. The 72 pre-existing test failures are all in unrelated workpackages (FIX-028/031/038/039, INS-019, MNT-002, SAF-010, SAF-025) and were present on the `main` branch before this work.

The SAF-013 test updates are correct: two tests that previously asserted `"deny"` for workspace-root reads now correctly assert `"allow"` per the SAF-046 specification.

---

## Verdict

**PASS** — All acceptance criteria met. All security controls verified. 40/40 SAF-046 tests pass. No regressions in related SAF tests.
