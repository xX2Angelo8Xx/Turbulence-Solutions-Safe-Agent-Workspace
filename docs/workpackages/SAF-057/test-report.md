# SAF-057 Test Report — Add `.git` and VCS Directories to Zone Classifier Deny Set

## Verdict: PASS

**Tester:** Tester Agent  
**Date:** 2026-03-30  
**Branch:** `SAF-057/git-deny-zone`

---

## Summary

SAF-057 correctly adds `.git`, `.hg`, and `.svn` to `_DENY_DIRS` and `_BLOCKED_PATTERN`, and adds a dot-prefix guard to `detect_project_folder()`. All developer tests pass. All 28 Tester edge-case tests pass. No regressions introduced.

---

## Test Results

| Run | Scope | Tests | Pass | Fail | Result ID |
|-----|-------|-------|------|------|-----------|
| Developer suite | SAF-057 unit tests | 28 | 28 | 0 | TST-2239 |
| Tester edge cases | SAF-057 security edge cases | 28 | 28 | 0 | TST-2240 |
| Full regression | Entire `tests/` (excl. DOC-018) | ~7009 | ~6980 | 72 pre-existing | TST-2241 |

**Total SAF-057 tests: 56 passed, 0 failed.**

Note on regression failures: 72 failures confirmed pre-existing on `main` before SAF-057 was applied (INS-015, INS-017, INS-019, MNT-002, SAF-010, SAF-025, DOC-018 and others). SAF-057 introduces zero new failures.

---

## Code Review

### `zone_classifier.py`

1. **`_DENY_DIRS`** — `.git`, `.hg`, `.svn` added to frozenset. Correct.
2. **`_BLOCKED_PATTERN`** — Regex updated with `\.git`, `\.hg`, `\.svn` alternations using anchored `/(pattern)(/|$)` form. Injection-resistant prefix-only matching confirmed.
3. **`detect_project_folder()`** — Dot-prefix guard added (`if entry.startswith("."): continue`) before `_DENY_DIRS` check. Defense-in-depth: any hidden directory is now unconditionally skipped, regardless of `_DENY_DIRS` membership.
4. **`normalize_path()`** — All paths lowercased before comparison, so `.GIT` on case-insensitive Windows filesystems is correctly lowercased to `.git` and then denied.
5. **`is_workspace_root_readable()`** — Uses `_DENY_DIRS` check on direct children; `.git` is in `_DENY_DIRS` so it returns False. Correct.

### `tests/SAF-046/test_saf046_tester_edge_cases.py`

Reference to `sg._DENY_THRESHOLD` updated to reflect new behavior: `.git` is now in `_DENY_DIRS`, so `is_workspace_root_readable()` returns `False` for `.git`. Test updated correctly. All 40 SAF-046 tests pass.

### `docs/bugs/bugs.csv`

BUG-135 status correctly updated from `Open` to `Fixed`, with `Fixed In WP` = `SAF-057`.

---

## Edge Cases Tested by Tester

### Case Sensitivity
- `.GIT` (uppercase) on Windows: `detect_project_folder()` skips it via `.startswith(".")` which is case-sensitive in Python, so `.GIT` is skipped correctly.
- `classify()` receives uppercase path `.GIT/config` → `normalize_path()` lowercases to `.git/config` → caught by `_BLOCKED_PATTERN` and `_DENY_DIRS`.
- `.HG` (uppercase) similarly handled.

### Deeply Nested `.git` Paths
- `.git/objects/pack/pack-abc.idx` → `deny` ✓
- `.git/refs/heads/main` → `deny` ✓
- `.git/HEAD` → `deny` ✓
- `.svn/wc.db` → `deny` ✓

### User-Created Dot-Prefixed Folders
- `.myproject` exists alongside `realproject` → `realproject` detected ✓
- Only `.myproject` exists → `RuntimeError` raised ✓
- `.env` directory → skipped, real project detected ✓

### All-Dot Workspace
- Workspace with `.git` + `.hg` + `.svn` + `.vscode` + `.github` → `RuntimeError` ✓
- `classify()` in that workspace → `"deny"` (fail-closed) ✓

### `.gitignore` / `.gitmodules` Files
- Files (not directories) at workspace root do not affect `detect_project_folder()` (only dirs are scanned) ✓
- `classify()` denies `.gitignore` and `.gitmodules` paths (not inside project folder) ✓

### `is_workspace_root_readable()` with VCS Paths
- `.git` → `False` (in `_DENY_DIRS`) ✓
- `.hg` → `False` ✓
- `.svn` → `False` ✓
- `.gitignore` → `True` (file, not in `_DENY_DIRS`, direct root child) ✓
- `.git/config` (depth > 1) → `False` ✓

### Multiple Co-existing VCS Systems
- `.git` + `.hg` + `.svn` + project → `project` detected ✓
- Alphabetically first VCS dir `.git` does not win over `alpha/` ✓

### Regression
- Normal workspace without VCS dirs → project detected ✓
- Multi-project dir workspace → alphabetically first non-deny, non-dot dir chosen ✓
- Files inside project remain `allow` after `git init` ✓

---

## Security Analysis

**Attack vectors considered:**

1. **Bypass via uppercase `.GIT`**: Mitigated — `normalize_path()` lowercases all paths before pattern matching; `detect_project_folder()` dot-prefix check is case-sensitive in Python but dots are preserved regardless of case.
2. **Path traversal to `.git`**: Mitigated — `posixpath.normpath()` in `normalize_path()` resolves `..` sequences before any pattern check.
3. **Injection via control characters before `.git`**: Mitigated — `normalize_path()` strips all C0 control chars (0x00-0x1f) first, per BUG-010 fix.
4. **VCS subdirectory enumeration**: `.git/objects/`, `.git/refs/heads/`, `.svn/wc.db` all correctly denied by both Method 1 (pathlib) and Method 2 (regex pattern).
5. **`.gitignore` false-allow**: `.gitignore` is correctly denied by `classify()` because it's not inside the project folder. `is_workspace_root_readable()` allows reading it (it's a root-level config file), which is by design (agents read `pyproject.toml`, `README.md`, etc.).
6. **Fail-closed on empty workspace**: Workspace with no non-dot directories → `RuntimeError` caught by `classify()` → `"deny"` returned. No path is ever accidentally allowed.

**No security vulnerabilities found.**

---

## Issues Found

**None.** The implementation is correct, complete, and passes all security checks.

---

## Pre-Checklist Verification

- [x] `docs/workpackages/SAF-057/dev-log.md` exists and is non-empty
- [x] `docs/workpackages/SAF-057/test-report.md` written by Tester
- [x] Test files exist in `tests/SAF-057/` (developer: 28 tests, tester: 28 edge cases)
- [x] All test results logged via `scripts/add_test_result.py` (TST-2239, TST-2240, TST-2241)
- [x] `scripts/validate_workspace.py --wp SAF-057` returns clean (exit code 0)
- [x] BUG-135 marked Fixed in `docs/bugs/bugs.csv`
