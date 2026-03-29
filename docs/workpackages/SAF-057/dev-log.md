# SAF-057 Dev Log — Add `.git` and VCS Directories to Zone Classifier Deny Set

## Status
Review

## Assigned To
Developer Agent

## Date
2026-03-30

---

## Summary

Added `.git`, `.hg`, and `.svn` to `_DENY_DIRS` and `_BLOCKED_PATTERN` in `zone_classifier.py`. Updated `detect_project_folder()` to skip all dot-prefixed directories as a defensive measure. Ran `update_hashes.py` to refresh integrity hashes in `security_gate.py`.

---

## Problem

When a user ran `git init` at the workspace root, the `.git` directory was created alongside the project folder. Since `.git` sorts alphabetically before most project folder names and was absent from `_DENY_DIRS`, `detect_project_folder()` selected `.git` as the project folder — making the real project folder inaccessible (all files denied). **BUG-135**.

---

## Changes Made

### `templates/agent-workbench/.github/hooks/scripts/zone_classifier.py`
1. **`_DENY_DIRS`**: Added `.git`, `.hg`, `.svn` to the frozenset.
2. **`_BLOCKED_PATTERN`**: Updated regex to include `\.git`, `\.hg`, `\.svn` alternations.
3. **`detect_project_folder()`**: Added a dot-prefix guard (`if entry.startswith("."): continue`) before the `_DENY_DIRS` check. This ensures no hidden directory (regardless of whether it's in `_DENY_DIRS`) can ever be selected as the project folder.

### `templates/agent-workbench/.github/hooks/scripts/security_gate.py`
- Hashes updated automatically by `update_hashes.py` after zone_classifier.py was modified.

### `tests/SAF-046/test_saf046_tester_edge_cases.py`
- Updated `test_is_workspace_root_readable_returns_true_for_git_dir` to expect `False` (reflects new behavior: `.git` is now in `_DENY_DIRS`, so `is_workspace_root_readable()` returns `False`).

### `docs/bugs/bugs.csv`
- BUG-135 status updated from `Open` to `Fixed`.

### `docs/workpackages/workpackages.csv`
- SAF-057 status set to `In Progress` then `Review`.

---

## Tests Written

File: `tests/SAF-057/test_saf057_vcs_deny_dirs.py`

| Class | Tests |
|---|---|
| `TestDenyDirsMembership` | `.git`, `.hg`, `.svn`, `.github`, `.vscode`, `noagentzone` in `_DENY_DIRS` |
| `TestBlockedPattern` | Regex matches `.git`, `.hg`, `.svn`, `.github`; no false positives |
| `TestDetectProjectFolderDotSkipping` | Skips `.git`, `.hg`, `.svn`, all dot dirs; raises `RuntimeError` when no non-dot dir exists; no regression |
| `TestClassifyGitPaths` | `classify()` returns `"deny"` for `.git/config`, `.git/HEAD`, `.git` itself, `.hg/store`, `.svn/entries`; project file still `"allow"` |
| `TestGitInitScenario` | `git init` at root does not break detection; project file still `"allow"`; `.git` subdir still `"deny"` |

**Total: 28 tests, 28 passed, 0 failed.**

---

## Test Result
TST-2238 — SAF-057 VCS deny dirs tests — Pass — 28 passed, 0 failed

---

## Known Limitations
None.

---

## Bugs Referenced
- **BUG-135**: Fixed by this WP.
