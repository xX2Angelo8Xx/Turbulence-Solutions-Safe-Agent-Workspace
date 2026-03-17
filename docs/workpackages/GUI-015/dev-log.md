# Dev Log — GUI-015: Rename Root Folder to TS-SAE-{ProjectName}

## Workpackage Info

| Field | Value |
|-------|-------|
| WP ID | GUI-015 |
| Category | GUI |
| Branch | `GUI-015/rename-root-folder` |
| Status | Review |
| Developer | Developer Agent |
| Date | 2026-03-17 |

---

## Summary

Modified `create_project()` in `project_creator.py` to prepend the `TS-SAE-` brand prefix to the root folder name. Updated `_on_create_project()` in `app.py` to check for the prefixed folder name when detecting duplicates.

---

## Files Changed

| File | Change |
|------|--------|
| `src/launcher/core/project_creator.py` | Prepend `TS-SAE-` prefix to `folder_name` before constructing the target path |
| `src/launcher/gui/app.py` | Duplicate folder check now looks for `TS-SAE-{folder_name}` and shows prefixed name in error message |
| `tests/GUI-015/test_gui015_rename_root_folder.py` | New test file (15 tests) |
| `tests/GUI-005/test_gui005_project_creation.py` | Updated expected values to reflect new TS-SAE- prefix behavior |
| `tests/GUI-007/test_gui007_validation.py` | Updated duplicate-check tests to create and detect TS-SAE- prefixed folders |
| `tests/GUI-007/test_gui007_tester_additions.py` | Updated stripped-name duplicate test to use TS-SAE- prefixed folder |
| `tests/INS-001/test_ins001_structure.py` | Updated traversal tests: TS-SAE- prefix absorbs one `..` level, so 3 levels needed to escape |
| `tests/INS-004/test_ins004_template_bundling.py` | Updated `assert result.name` to expect `TS-SAE-test-project` |

---

## Implementation Details

### `project_creator.py`

```python
# Prepend the TS-SAE- brand prefix to the folder name.
prefixed_name = f"TS-SAE-{folder_name}"

# Guard against path-traversal in folder_name (e.g. "../../etc").
target = (destination / prefixed_name).resolve()
if not target.is_relative_to(destination.resolve()):
    raise ValueError("Invalid folder name: path traversal attempt detected")
```

The `folder_name` parameter remains unchanged — the caller (app.py) still passes the raw user input. The prefix is applied inside `create_project()`.

### `app.py`

The duplicate check call was updated to use `f"TS-SAE-{folder_name}"` so it detects an existing prefixed folder before attempting to create one:

```python
if check_duplicate_folder(f"TS-SAE-{folder_name}", destination_str):
    self.project_name_error_label.configure(
        text=f'A folder named "TS-SAE-{folder_name}" already exists at the destination.'
    )
    return
```

---

## Path Traversal Security Note

The `TS-SAE-` prefix changes the traversal escape threshold:
- **Before**: `../../x` (2 levels) escaped the destination → guard fired
- **After**: `TS-SAE-../../x` → the prefix component absorbs one `..` level, net effect stays inside destination. 3 levels (`../../../x`) are needed to escape.

This is not a security regression because:
1. `validate_folder_name()` already rejects `/` and `\` characters, so traversal inputs are blocked at the GUI boundary.
2. The `create_project()` guard is defense-in-depth for direct API usage. It still blocks deeper traversal attempts.
3. Affected tests were updated to use 3-level traversal to verify the guard is still effective.

---

## Tests Written (`tests/GUI-015/`)

| Test Class | Tests | Purpose |
|------------|-------|---------|
| `TestCreateProjectPrefix` | 7 | Verify TS-SAE- prefix in folder name and returned path |
| `TestCreateProjectTraversalGuard` | 2 | Confirm traversal guard still works (3-level) and benign names are accepted |
| `TestCreateProjectErrors` | 3 | Pre-existing error conditions unchanged |
| `TestDuplicateFolderCheck` | 3 | Validate that duplicate detection uses the prefixed name |

**Total new tests:** 15  
**All tests passed:** Yes (2975 passing, 1 pre-existing INS-005 failure unrelated to this WP)

---

## Known Limitations / Notes

- GUI-017 (also linked to US-017) also mentions updating the duplicate check — this WP implements that change. GUI-017 should be reviewed for remaining scope.
- INS-005 (`test_uninstall_delete_type_is_filesandirs`) was already failing before this WP on the `main` branch. Not caused by GUI-015.
