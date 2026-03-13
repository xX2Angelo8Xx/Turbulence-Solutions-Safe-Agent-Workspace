# FIX-005 Dev Log — Untrack launcher.spec

**WP ID:** FIX-005  
**Branch:** fix/FIX-005  
**Date:** 2026-03-13  
**Agent:** Developer Agent

---

## Problem

`tests/INS-012/test_ins012_gitignore.py::test_gitignore_git_recognises_spec` was failing.

The `.gitignore` file contains `*.spec`, but `launcher.spec` was already tracked by git.
Git does not apply `.gitignore` rules to already-tracked files, so `git check-ignore launcher.spec`
returned no output — causing the test to fail.

## Fix

Removed `launcher.spec` from the git index (without deleting it from disk):

```
git rm --cached launcher.spec
```

`launcher.spec` is a PyInstaller build artefact. It should never have been committed. The `*.spec`
pattern in `.gitignore` now applies correctly, preventing it from being re-added accidentally.

## Files Changed

| File | Change |
|------|--------|
| `launcher.spec` | Removed from git index (untracked); file remains on disk |

## Tests

```
.venv\Scripts\python -m pytest tests/INS-012/ -v --tb=short --no-header
```

**Result:** 30 passed in 0.59s

Previously failing test `test_gitignore_git_recognises_spec` now passes.

## Notes

No source code was modified. This is a git index-only change.
