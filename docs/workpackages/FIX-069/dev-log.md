# Dev Log — FIX-069: Fix zone_classifier import for embedded Python

## Summary
Critical security hotfix: `security_gate.py` fails to import `zone_classifier` when invoked via the `ts-python` shim (embedded Python distribution). The Python embeddable package ships with a `._pth` file that restricts `sys.path` — it does NOT automatically add the script's directory. This makes the security gate completely non-functional in v3.1.1.

**Bug Reference:** BUG-092

## Root Cause
The standard CPython interpreter automatically prepends the script's directory to `sys.path`. The embeddable Python distribution (used by `ts-python`) does NOT do this — its `._pth` file explicitly restricts `sys.path` to zip archives and standard library paths only.

## Implementation

### Change 1: `templates/coding/.github/hooks/scripts/security_gate.py`

Added `sys.path.insert(0, str(Path(__file__).resolve().parent))` immediately before `import zone_classifier`. Updated the comment above the import to document the embedded Python requirement.

### Change 2: Run `update_hashes.py`

After modifying `security_gate.py`, ran `update_hashes.py` from within `templates/coding/.github/hooks/scripts/` to recompute and re-embed the SHA256 hash for the modified file. Without this step, the SAF-008 integrity check would fail all tool calls.

## Files Changed
- `templates/coding/.github/hooks/scripts/security_gate.py` — added sys.path fix before import zone_classifier
- (hashes updated by update_hashes.py — security_gate.py modified in-place)
- `docs/workpackages/workpackages.csv` — FIX-069 set to In Progress → Review
- `docs/bugs/bugs.csv` — BUG-092 set to Closed, Fixed In WP = FIX-069
- `tests/FIX-069/test_fix069_zone_classifier_import.py` — new test file

## Tests Written
See `tests/FIX-069/test_fix069_zone_classifier_import.py`:
1. `test_sys_path_insert_present` — verifies the fix line is present in the file
2. `test_sys_path_insert_before_import_zone_classifier` — verifies ordering (fix before import)
3. `test_zone_classifier_importable_with_restricted_sys_path` — simulates embedded Python with restricted sys.path and confirms zone_classifier is importable after the fix
4. `test_script_dir_resolved_correctly_absolute` — verifies path resolves correctly for absolute path
5. `test_script_dir_resolved_correctly_relative` — verifies path resolves correctly when CWD-relative

## Iteration 1
Initial implementation.
