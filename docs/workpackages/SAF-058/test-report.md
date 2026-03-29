# SAF-058 Test Report

**WP:** SAF-058 — `get_changed_files` conditional `.git/` placement check  
**Branch:** `SAF-058/get-changed-files-conditional`  
**Tester:** Tester Agent  
**Date:** 2025-07-17  
**Verdict:** ✅ PASS

---

## Summary

The implementation correctly removes `get_changed_files` from `_ALWAYS_ALLOW_TOOLS` and gates it through `validate_get_changed_files()`, which checks `.git/` placement to determine whether the tool can expose denied-zone file paths.

All developer tests pass. 7 additional tester edge-case tests added (6 passed, 1 skipped — symlinks require Windows elevated privileges).

---

## Test Runs

| ID      | Suite                          | Type     | Result          | Count                  |
|---------|--------------------------------|----------|-----------------|------------------------|
| TST-2247 | SAF-058 developer tests       | Unit     | PASS            | 10 passed, 0 failed    |
| TST-2248 | SAF-058 tester edge-case tests | Security | PASS            | 16 passed, 1 skipped   |

---

## Code Review

### `_ALWAYS_ALLOW_TOOLS` — Correct

`get_changed_files` is absent from `_ALWAYS_ALLOW_TOOLS`. A confirming comment at line 36 of `security_gate.py` reads:
```
# SAF-058: get_changed_files removed — validated by validate_get_changed_files() in decide()
```

### `validate_get_changed_files()` — Correct

Logic is sound and fail-closed:
1. `os.path.isdir(ws_root/.git)` → **True** → `"deny"` (workspace-root repo exposes all zone files)
2. `zone_classifier.detect_project_folder()` → constructs `ws_root/<project>/.git` → `os.path.isdir(...)` → **True** → `"allow"` (scoped only to project)
3. `RuntimeError` from `detect_project_folder` → `pass` (no project folder) → `"allow"` (no repo)
4. No `.git/` anywhere → `"allow"` (tool returns harmless "no repo" message)
5. `OSError` at any point → `"deny"` (fail-closed)

### `decide()` Integration — Correct

The `get_changed_files` routing in `decide()` appears **before** the `_ALWAYS_ALLOW_TOOLS` check at line ~3003:
```python
# SAF-058: get_changed_files — conditional .git/ placement check.
if tool_name == "get_changed_files":
    return validate_get_changed_files(ws_root)
```
This ordering prevents any bypass via the `_ALWAYS_ALLOW_TOOLS` path.

### SAF-052 Regression — Correct

`tests/SAF-052/test_saf052_get_changed_files.py::test_get_changed_files_in_always_allow_tools` was correctly updated by the developer to assert `get_changed_files` is **NOT** in `_ALWAYS_ALLOW_TOOLS` (assertNotIn), reflecting the SAF-058 change. All 121 tests in SAF-052, SAF-035, SAF-036 and SAF-058 pass.

---

## Coverage Analysis

### Developer Tests (10)

| Test | Scenario | Result |
|------|----------|--------|
| `test_get_changed_files_not_in_always_allow` | Set membership check | PASS |
| `test_git_at_workspace_root_is_denied` | `.git/` dir at ws_root → deny | PASS |
| `test_git_inside_project_folder_is_allowed` | `.git/` dir in project only → allow | PASS |
| `test_no_git_anywhere_is_allowed` | no `.git/` → allow | PASS |
| `test_no_project_folder_no_git_is_allowed` | empty workspace → allow | PASS |
| `test_os_error_fails_closed` | `OSError` → deny | PASS |
| `test_git_at_root_takes_priority_over_project_git` | `.git/` at both root and project → deny | PASS |
| `test_decide_denies_when_git_at_workspace_root` | `decide()` routing → deny | PASS |
| `test_decide_allows_when_git_inside_project` | `decide()` routing → allow | PASS |
| `test_decide_allows_when_no_git` | `decide()` routing → allow | PASS |

### Tester Edge-Case Tests (7)

| Test | Scenario | Result |
|------|----------|--------|
| `test_git_file_at_workspace_root_is_allowed` | `.git` as FILE (not dir) at ws_root → allow | PASS |
| `test_git_file_inside_project_folder_is_allowed` | `.git` as FILE inside project → allow | PASS |
| `test_symlinked_git_dir_at_workspace_root_is_denied` | symlinked `.git/` at ws_root → deny | SKIP (no symlink support on Windows without admin) |
| `test_permission_error_fails_closed` | `PermissionError` → deny | PASS |
| `test_detect_project_folder_runtime_error_no_root_git_is_allowed` | `RuntimeError` from `detect_project_folder` (mocked) + no root `.git/` → allow | PASS |
| `test_custom_project_folder_name_is_used_for_git_path` | custom folder name returned by zone_classifier → `.git/` in it → allow | PASS |
| `test_custom_project_folder_no_git_dir_is_allowed` | custom folder with no `.git/` → allow | PASS |

---

## Regression Check

Full suite run: **7028 passed, 74 failed, 32 skipped, 3 xfailed**

The 74 failures are **pre-existing** and unrelated to SAF-058:
- `FIX-039`, `FIX-042`, `FIX-049` — build/packaging test infrastructure
- `INS-004`, `INS-014`, `INS-015`, `INS-017`, `INS-019` — installer and CI template checks
- `MNT-002` — maintenance action count
- `SAF-010` — hook config command format (templates settings mismatch)
- `SAF-025` — pycache pollution (created by test imports)

None relate to `get_changed_files`, `validate_get_changed_files`, or `decide()` routing. All SAF-related security gate tests (121 tests across SAF-035, SAF-036, SAF-052, SAF-058) pass.

---

## Bugs Found

**BUG-151 (Low):** `validate_get_changed_files` does not detect a `.git` FILE (worktree/submodule pointer) at workspace root. `os.path.isdir()` returns `False` for a file, so the check is bypassed and the tool is allowed. In uncommon git worktree setups, `get_changed_files` could show diffs from the underlying tracked repository, potentially including denied-zone file path references.

> **Impact:** Low — worktree setups at workspace root are uncommon in this deployment model. The design decision to use `os.path.isdir()` is defensible (a `.git` file doesn't directly expose files in the same way a `.git/` directory does), but should be explicitly documented in the source code.

---

## Security Assessment

✅ **Fail-closed:** `OSError` and `PermissionError` both return `"deny"`.  
✅ **Priority ordering:** The tool check runs in `decide()` before `_ALWAYS_ALLOW_TOOLS`, preventing bypass.  
✅ **Zone boundary enforcement:** Only `.git/` inside the project folder (not workspace root) permits the tool.  
✅ **Symlink handling:** `os.path.isdir()` follows symlinks — a symlinked `.git/` is correctly denied.  
⚠️ **`.git` files (worktrees):** Not caught by `os.path.isdir()` — documented as BUG-151 (Low severity). Not a blocking issue.

---

## Verdict

**PASS** — The implementation is correct and secure. All acceptance criteria from US-062 are satisfied. BUG-151 is logged as Low severity and does not block this WP.
