# Test Report — SAF-006

**Tester:** Tester Agent
**Date:** 2026-03-12
**Iteration:** 3

## Verdict: FAIL

---

## Summary

SAF-006 Iteration 3 introduces `_INHERENTLY_RECURSIVE_COMMANDS`, `_RECURSIVE_FLAG_MAP`, `_is_ancestor_of_deny_zone()`, and `_has_recursive_flag()` and wires them into Step 7 of `_validate_args()`. The BUG-022 and BUG-023 fixes are confirmed correct. However, **BUG-024** was found during testing: `dir /s` with no explicit directory argument returns `ask` instead of `deny`.

**Root cause:** Step 7 path-argument collection filters out POSIX-style flags (tokens starting with `-`) but does **not** filter Windows-style flags (tokens starting with `/` followed by one or two letters, e.g. `/s`, `/b`). When no non-flag paths remain, the fallback to `.` (cwd = workspace root = ancestor of deny zones) should fire — but it never does because `/s` is incorrectly collected as a path argument and passed to `_is_ancestor_of_deny_zone()`, which returns `False` for the literal string `"/s"`.

The same bug affects any `dir` invocation with only Windows flags and no explicit directory path (e.g. `dir /s /b`).

---

## Tests Executed

### Developer tests (46 tests — `test_saf006_recursive_protection.py`)

| Result | Count |
|--------|-------|
| Pass   | 45    |
| Fail   | 1     |
| **Total** | **46** |

**Failing test:** `test_dir_slash_s_blocked` — `dir /s` returns `ask`, expected `deny`.

### Tester edge-case tests (19 tests — `test_saf006_edge_cases.py`)

| Result | Count |
|--------|-------|
| Pass   | 17    |
| Fail   | 2     |
| **Total** | **19** |

**Failing tests:**
- `test_dir_slash_s_no_path_blocked` — same root cause as BUG-024
- `test_dir_slash_s_slash_b_no_path_blocked` — `dir /s /b` (two Windows flags) returns `ask`, expected `deny`

### Full SAF-006 suite (65 tests)

| Result | Count |
|--------|-------|
| Pass   | 62    |
| Fail   | 3     |
| **Total** | **65** |

All 3 failures share **BUG-024** as their root cause.

---

## Bug Analysis

### BUG-024 — `dir /s` with no explicit directory not denied

**Severity:** High  
**Location:** `_validate_args()` Step 7, path-argument collection loop  
**File:** `Default-Project/.github/hooks/scripts/security_gate.py`

**Description:**

Step 7 collects path arguments with:
```python
for tok in args:
    stripped = tok.strip("\"'")
    if stripped.startswith("-"):   # ← filters POSIX flags (-r, --recursive, etc.)
        continue
    if _ENV_ASSIGN_RE.match(stripped):
        continue
    path_args.append(stripped)
```

For `dir /s`, `args = ["/s"]`. `/s` does **not** start with `-`, so it is added to `path_args`. `_is_ancestor_of_deny_zone("/s", "/workspace")` returns `False` (the literal string `/s` is not an ancestor of any deny zone), so the check passes and the command is deemed safe.

Because `/s` is in `path_args`, the fallback `if not path_args: path_args = ["."]` never fires, and the workspace-root ancestor check is skipped.

**Attack vector:** An agent could enumerate the entire workspace tree (including `.github`, `.vscode`, `NoAgentZone`) using `dir /s` without triggering a `deny` decision — only an `ask` decision with no warning about recursive access from the workspace root.

---

## Confirmed Correct (from previous iterations)

- **BUG-021 fix confirmed:** `security_gate.py` is present and committed; all 46 developer tests are collected and run.
- **BUG-022 fix confirmed:** Combined POSIX flags `ls -lR Project/` and `ls -alR Project/` correctly return `ask` (17 edge-case tests covering all BUG-022/023 scenarios pass).
- **BUG-023 fix confirmed:** `ls -R Project/` and `gci -r Project/` correctly return `ask`; `denied_flags` is empty for `ls`, `dir`, `gci`, `get-childitem`.
- `_has_recursive_flag()` handles combined flags (`-lR`, `-alR`, `-Rl`) and mixed case correctly.
- `_is_ancestor_of_deny_zone()` handles `"."`, `""`, relative `.github`, absolute ws root, filesystem root `/`, and path traversal `../../.github` correctly.
- `tree`, `find`, `gci -recurse`, `get-childitem -recurse` without explicit paths correctly deny (workspace root fallback works for these commands since they only produce POSIX-style flags).

---

## Tester Edge Cases Added (`tests/SAF-006/test_saf006_edge_cases.py`)

19 tests covering:
- `find . -name '*.py'` → deny (filter expression not mistaken for a path)
- `find Project/ -name '*.py'` → ask (safe target with filter expression)
- `find .vscode -type f` → deny (deny-zone target)
- `find ../../.github` → deny (path traversal resolved to deny zone)
- `ls -lR Project/` → ask (BUG-022 regression)
- `ls -alR Project/` → ask (BUG-022 regression)
- `ls -R Project/` → ask (BUG-023 regression)
- `gci -r Project/` → ask (BUG-023 regression)
- `ls --recursive Project/` → ask  
- `dir /s Project/` → ask
- `dir Project/` → ask (non-recursive)
- **`dir /s` → deny** ← FAILS (BUG-024)
- **`dir /s /b` → deny** ← FAILS (BUG-024)
- `tree .vscode` → deny
- `tree /` → deny (filesystem root)
- `find /workspace` → deny (absolute workspace root)
- `ls -r .vscode` → deny
- `Get-ChildItem -Recurse -Path .github` → deny
- `gci -recurse NoAgentZone` → deny

---

## TODO for Developer (Iteration 4)

**TODO-1 (Blocking — must fix): Fix Step 7 path-argument collection to skip Windows-style flags.**

In `_validate_args()` Step 7, add a guard to skip tokens that are Windows-style command flags (single `/` followed by 1–2 alphanumeric characters). These are flags, not paths, and must not be treated as path arguments.

**Location:** `security_gate.py`, `_validate_args()`, Step 7, the `for tok in args:` loop.

**Suggested fix:**

```python
# Add before path_args.append(stripped):
import re
# Skip Windows-style flags (e.g., /s, /b, /p for dir)
# Must NOT skip absolute paths like /workspace or /home/user
if re.match(r'^/[a-zA-Z0-9]{1,2}$', stripped):
    continue
```

**Test targets that must pass after fix:**
- `test_dir_slash_s_blocked` (existing developer test)
- `test_dir_slash_s_no_path_blocked` (new tester test)
- `test_dir_slash_s_slash_b_no_path_blocked` (new tester test)

**Note:** The regex `^/[a-zA-Z0-9]{1,2}$` matches Windows short flags (`/s`, `/b`, `/p`, `/ad`) but not absolute POSIX paths (`/workspace`, `/home/user`), which are longer than 3 characters. Verify that `dir /s Project/` still returns `ask` (it should, since `project/` remains in path_args after `/s` is filtered).

---

## Regression Check

Full test suite run (excluding pre-existing failures unrelated to SAF-006):

| WP | Pass | Fail | Notes |
|----|------|------|-------|
| SAF-006 (65 tests) | 62 | 3 | All failures: BUG-024 |
| All other WPs | 519 | 0 | No regressions from SAF-006 code |
| INS-004 (pre-existing) | 0 | 32 | Pre-existing; WP still In Progress |
| INS-012 spec test (pre-existing) | 0 | 1 | Pre-existing; unrelated to SAF-006 |

**Total:** 34 failed / 552 passed / 1 skipped (full suite run).  
SAF-006 code introduced **0 new regressions** in other WPs.
