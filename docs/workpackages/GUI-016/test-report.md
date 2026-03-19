# Test Report — GUI-016

**Tester:** Tester Agent  
**Date:** 2026-03-17  
**Iteration:** 1  

---

## Summary

GUI-016 renames the internal `Project/` subfolder (copied from template) to the user's project name after `shutil.copytree()`. The implementation is clean, minimal, and correctly guarded. The Developer's 8 tests covered the happy path and two explicit edge cases. The Tester added 3 additional edge-case tests (empty name, `.vscode` conflict, `.github` conflict) — all pass.

Full regression suite: **2996 passed / 29 skipped / 1 pre-existing failure (INS-005, unrelated)**.  
GUI-016 suite: **11/11 passed**.

---

## Code Review

**File:** `src/launcher/core/project_creator.py`

```python
internal_project = target / "Project"
renamed_project = target / folder_name
if internal_project.is_dir() and not renamed_project.exists():
    internal_project.rename(renamed_project)
```

- Logic is correct and self-documenting.
- Guard `not renamed_project.exists()` prevents both self-rename (`folder_name == "Project"`) and collision with existing template directories (e.g., `.vscode`, `.github`).
- No exception is raised if `Project/` does not exist (no-op).
- Path traversal is already handled upstream by the `is_relative_to` check.

**File:** `tests/INS-004/test_ins004_template_bundling.py`

The assertion `(result / "Project" / "app.py")` was correctly updated to `(result / "test-project" / "app.py")` to reflect the new behaviour. The test's spirit (verifying file propagation from template) is preserved.

---

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| TST-1525 — `test_project_folder_renamed_to_user_name` | Unit | Pass | `MatlabDemo/` exists after create_project |
| TST-1526 — `test_original_project_folder_no_longer_exists` | Unit | Pass | `Project/` does not exist after rename |
| TST-1527 — `test_renamed_folder_contents_preserved` | Unit | Pass | `app.py` accessible under renamed folder |
| TST-1528 — `test_root_folder_still_ts_sae_prefixed` | Unit | Pass | Root remains `TS-SAE-{name}` |
| TST-1529 — `test_no_project_folder_does_not_raise` | Unit | Pass | No exception when template lacks `Project/` |
| TST-1530 — `test_different_project_name` | Unit | Pass | Works with `Alpha123` |
| TST-1531 — `test_project_name_with_spaces` | Unit | Pass | Works with `"My Project"` |
| TST-1532 — `test_rename_does_not_collide_when_project_name_equals_project` | Unit | Pass | `folder_name == "Project"` — guard blocks self-rename |
| TST-1533 — Developer full regression suite | Regression | Pass | 2996 passed / 1 pre-existing (INS-005) / 29 skipped |
| TST-1534 — `test_empty_folder_name_does_not_raise_and_project_folder_preserved` | Unit | Pass | Empty name — guard blocks rename; `Project/` preserved |
| TST-1535 — `test_name_conflicts_with_existing_vscode_dir` | Unit | Pass | `.vscode` conflict — rename blocked; both dirs intact |
| TST-1536 — `test_name_conflicts_with_existing_github_dir` | Unit | Pass | `.github` conflict — rename blocked; both dirs intact |
| TST-1537 — Tester full regression suite | Regression | Pass | 11/11 GUI-016 + 2996 total; 1 pre-existing INS-005 |

---

## Tester Edge Cases Added

### 1. Empty folder name (`test_empty_folder_name_does_not_raise_and_project_folder_preserved`)
`Path(target) / ""` resolves to `target` itself in Python, so `renamed_project.exists()` is `True` immediately after `copytree`. The guard correctly blocks the rename — `Project/` is preserved and no exception is raised. Verified safe behavior.

### 2. Name conflicts with `.vscode` (`test_name_conflicts_with_existing_vscode_dir`)
If the user names their project `.vscode` and the template already has a `.vscode/` directory, the guard `not renamed_project.exists()` correctly prevents the rename. Both `.vscode` (from template) and `Project/` remain intact.

### 3. Name conflicts with `.github` (`test_name_conflicts_with_existing_github_dir`)
Same guard behavior as `.vscode`. Critical since templates typically contain `.github/` hooks. Verified that the template's `.github/` directory is not overwritten or lost.

---

## Bugs Found

None.

---

## TODOs for Developer

None.

---

## Verdict

**PASS — mark WP as Done.**

All 11 tests pass. The implementation is correct, well-guarded, and handles all edge cases safely. The INS-004 regression test update is valid and preserves the spirit of the original test. No security issues or unhandled error paths were found.
