# FIX-005 Dev Log — Untrack launcher.spec

**WP ID:** FIX-005  
**Branch:** main (hotfix — direct push)  
**Date:** 2026-03-13  
**Agent:** Developer Agent

---

## Problem

A previous FIX-005 attempt ran `git rm launcher.spec` (without `--cached`), which:
1. Removed `launcher.spec` from the git index (correct), AND
2. **Physically deleted the file from disk** (incorrect — caused test failures).

This caused 21+ test failures across INS-003 and INS-005 test suites because those tests assert
that `launcher.spec` exists on disk as a valid PyInstaller spec file.

Additionally, `tests/INS-012/test_ins012_gitignore.py::test_gitignore_git_recognises_spec`
required that git recognise `launcher.spec` as ignored (via the `*.spec` rule in `.gitignore`).
Because the file was absent from disk entirely, both conditions were broken simultaneously.

## Fix

1. Restored `launcher.spec` from git history (commit `61048e5` — INS-003 original creation):
   ```
   git show 61048e5:launcher.spec  # content extracted and written as UTF-8 no-BOM
   ```
2. File is NOT re-added to git tracking — the `.gitignore` `*.spec` rule prevents it from
   being staged, so `git check-ignore -v launcher.spec` correctly reports `.gitignore:14:*.spec`.
3. `git ls-files -- launcher.spec` produces no output (file is untracked).

## Verification

```
.venv\Scripts\python -c "import ast; ast.parse(open('launcher.spec').read()); print('OK')"
# → OK

git check-ignore -v launcher.spec
# → .gitignore:14:*.spec    launcher.spec

git ls-files -- launcher.spec
# → (no output — not tracked)
```

## Files Changed

| File | Change |
|------|--------|
| `launcher.spec` | Restored to disk from git history; remains untracked (`.gitignore` applies) |
| `docs/workpackages/workpackages.csv` | FIX-005 status → In Progress → Review |

## Tests

```
.venv\Scripts\python -m pytest tests/INS-003/ tests/INS-012/ tests/INS-005/ --tb=short -q
```

**Result:** 90 passed in 0.97s

## Notes

No source code was modified. This is a file-restoration-only change.
`launcher.spec` must remain on disk (INS-003 and INS-005 depend on it) but must never be
re-committed to git (handled by `.gitignore` `*.spec` rule).
