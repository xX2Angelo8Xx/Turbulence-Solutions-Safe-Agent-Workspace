# Test Report — SAF-079

**Tester:** Tester Agent
**Date:** 2026-04-08
**Iteration:** 1

---

## Summary

**FAIL.** The implementation correctly adds `push-location` to the allowlist and introduces `_check_nav_path_arg()` for workspace-scoped navigation, and all 26 Developer-written tests pass. However, a security regression was discovered: the project-folder fallback in `_check_nav_path_arg()` does not exclude tilde (`~`) tokens, allowing `cd ~` to be accepted when it must be denied. This breaks the SAF-030 tilde-bypass protection and constitutes a high-severity security regression (BUG-219).

The WP is returned to **In Progress**. Both template files must be fixed identically before re-submission.

---

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| TST-2782 (Developer) | Unit | Pass | 26 SAF-079 tests — all pass |
| TST-2783 | Regression | Fail | Full suite: SAF-030 test_cd_tilde_denied fails; 6 new tester tilde edge cases fail |

---

## Regression Check

The following test in `tests/SAF-030/` was passing before SAF-079 and now fails:

```
FAILED tests/SAF-030/test_saf030_tilde_path.py::TestTildeBypassAttempts::test_cd_tilde_denied
```

This is a **new regression** not present in `tests/regression-baseline.json`. All other full-suite failures were verified to be pre-existing by running the affected suites in isolation.

---

## Security Issue: Tilde Bypass via Project-Folder Fallback (BUG-219)

### Root Cause

`_check_nav_path_arg()` calls `_check_workspace_path_arg()` as the primary check. That function correctly returns `False` for `~` (it has an explicit tilde guard). However, when the primary check returns `False` for a relative token, `_check_nav_path_arg()` then enters the project-folder fallback branch. The fallback does **not** check for tilde.

For input `"~"`:
1. `_check_workspace_path_arg("~", ws_root)` → `False` (tilde correctly denied)
2. Fallback: `norm = posixpath.normpath("~")` → `"~"`
3. `"~"` does not match the absolute-path guard (`re.match(r"^[a-z]:", ...)`)
4. `"~"` is not in the deny zones set
5. `detect_project_folder()` returns e.g. `"project"`
6. `resolved = normpath("c:/workspace/project/~")` → `"c:/workspace/project/~"`
7. `"c:/workspace/project/~".startswith("c:/workspace/")` → `True`
8. Returns `True` — **incorrectly allows `cd ~`**

### Impact

At shell runtime, `~` expands to the user's HOME directory (outside the workspace root). Allowing `cd ~` navigates the agent session outside the workspace, contradicting the workspace-scope mandate and SAF-030.

Affected commands: `cd ~`, `push-location ~`, `sl ~`, `Set-Location ~/anything`.

### New Edge-Case Tests Added

Six tests added to `tests/SAF-079/test_saf079_nav.py` (all currently failing — confirming the bug):

- `test_cd_tilde_denied`
- `test_push_location_tilde_denied`
- `test_sl_tilde_denied`
- `test_set_location_tilde_slash_denied`
- `test_check_nav_path_arg_tilde_denied`
- `test_check_nav_path_arg_tilde_slash_denied`

---

## Bugs Found

- **BUG-219**: `SAF-079: _check_nav_path_arg tilde bypass via project-folder fallback` (logged in `docs/bugs/bugs.jsonl`, Severity: High)

---

## TODOs for Developer

- [ ] **Fix `_check_nav_path_arg()` in both templates**: Add an explicit tilde guard **before** the project-folder fallback. Mirror the guard already present in `_check_workspace_path_arg()`:
  ```python
  # SAF-030: Deny tilde — expands to HOME directory (outside workspace) at shell runtime
  norm_early = posixpath.normpath(token.replace("\\", "/"))
  if norm_early == "~" or norm_early.startswith("~/") or re.match(r"^~[^/]", norm_early):
      return False
  ```
  This check should be inserted after the wildcard check and before `if not _is_path_like(token): return True`. Alternatively, add it immediately before the project-folder fallback block (after `if _check_workspace_path_arg(token, ws_root): return True`).

- [ ] **Apply the same fix to `templates/clean-workspace/.github/hooks/scripts/security_gate.py`** — both files must remain byte-identical.

- [ ] **Run `update_hashes.py`** after the fix to regenerate the integrity hash.

- [ ] **Run `generate_manifest.py`** for both templates after the hash update.

- [ ] **Verify** that all 32 tests in `tests/SAF-079/test_saf079_nav.py` pass (original 26 + 6 tester additions).

- [ ] **Verify** that `tests/SAF-030/test_saf030_tilde_path.py::TestTildeBypassAttempts::test_cd_tilde_denied` now passes.

- [ ] **Run** `scripts/validate_workspace.py --wp SAF-079` → exit code 0.

---

## Verdict

**FAIL — Return to Developer with the TODOs above.**

The implementation is functionally correct for the primary navigation use cases but has a high-severity security hole in the tilde-path edge case that re-opens the SAF-030 bypass channel. The fix is one guard expression; the rest of the implementation is solid.
