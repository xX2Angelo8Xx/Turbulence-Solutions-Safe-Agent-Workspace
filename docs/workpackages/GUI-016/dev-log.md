# Dev Log — GUI-016: Rename Internal Project Folder to User's Name

**Status:** Review  
**Assigned To:** Developer Agent  
**Branch:** `GUI-016/rename-project-folder`  
**Date:** 2026-03-17  

---

## Summary

Modified `create_project()` in `src/launcher/core/project_creator.py` to rename the `Project/` subdirectory (copied from the template) to the user's raw project name after `shutil.copytree()`. For example, if the user enters "MatlabDemo", the workspace layout becomes:

```
TS-SAE-MatlabDemo/
  MatlabDemo/          ← was "Project/"
    app.py
  README.md
  ...
```

---

## Implementation Details

### File Changed: `src/launcher/core/project_creator.py`

Added 4 lines after `shutil.copytree()` in `create_project()`:

```python
internal_project = target / "Project"
renamed_project = target / folder_name
if internal_project.is_dir() and not renamed_project.exists():
    internal_project.rename(renamed_project)
```

**Edge cases handled:**
- Template has no `Project/` subfolder → no-op, no exception raised.
- `folder_name == "Project"` → `renamed_project.exists()` is True (same path), guard prevents self-rename, folder stays as-is.
- Normal case → `Project/` renamed to user's name.

---

## Files Changed

| File | Change |
|------|--------|
| `src/launcher/core/project_creator.py` | Added rename logic after `copytree()` |
| `tests/GUI-016/test_gui016_rename_project_folder.py` | New test file (8 tests) |
| `tests/INS-004/test_ins004_template_bundling.py` | Updated assertion at line 285: `Project/app.py` → `test-project/app.py` to reflect new behaviour |
| `docs/workpackages/workpackages.csv` | Status updated to In Progress → Review |
| `docs/test-results/test-results.csv` | Added TST-1525 through TST-1533 |

---

## INS-004 Test Update Decision

The permanent test `tests/INS-004/test_ins004_template_bundling.py::test_template_discoverable_and_copyable` contained:

```python
assert (result / "Project" / "app.py").is_file()
```

This assertion was checking that files propagate from the template into the copy. With GUI-016 renaming `Project/` → `test-project/`, the correct path is now `result / "test-project" / "app.py"`. The assertion was updated to reflect the intentionally changed behaviour. The spirit of the permanent-test rule (regression protection) is preserved — the test still validates file propagation.

---

## Tests Written

**File:** `tests/GUI-016/test_gui016_rename_project_folder.py`

| Test | Description |
|------|-------------|
| `test_project_folder_renamed_to_user_name` | `MatlabDemo/` exists after create_project |
| `test_original_project_folder_no_longer_exists` | `Project/` does not exist after rename |
| `test_renamed_folder_contents_preserved` | `app.py` accessible under renamed folder |
| `test_root_folder_still_ts_sae_prefixed` | Root remains `TS-SAE-{name}` |
| `test_no_project_folder_does_not_raise` | No exception when template lacks `Project/` |
| `test_different_project_name` | Works with `Alpha123` |
| `test_project_name_with_spaces` | Works with `"My Project"` |
| `test_rename_does_not_collide_when_project_name_equals_project` | folder_name==`"Project"` keeps folder intact |

---

## Test Results

- **GUI-016 suite:** 8/8 passed
- **Full regression suite:** 2996 passed, 29 skipped, 1 pre-existing failure (INS-005 — existed before this branch, unrelated to GUI-016)

---

## Known Limitations

None. The implementation is straightforward and handles all defined edge cases.
