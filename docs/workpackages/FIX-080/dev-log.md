# Dev Log — FIX-080

## Workpackage
- **ID:** FIX-080
- **Title:** Handle --version flag before GUI import in main.py
- **Branch:** FIX-080/version-flag
- **Assigned To:** Developer Agent
- **Status:** Review

## Summary
`agent-launcher --version` crashed on macOS CI with `ModuleNotFoundError: No module named '_tkinter'` because `main()` was importing `launcher.gui.app` (which imports tkinter) before handling any CLI flags. Added early `--version` check in `main()` before any GUI imports.

## Implementation

### File Changed
- `src/launcher/main.py` — Added early `--version` check at the start of `main()`, before `ensure_shim_deployed()` and the GUI import.

### Change Description
Added 3 lines to `main()` immediately after the `PYTEST_CURRENT_TEST` guard:

```python
if "--version" in sys.argv:
    print(f"{APP_NAME} {VERSION}")
    sys.exit(0)
```

`sys`, `APP_NAME`, and `VERSION` were already imported at the top of the file, so no new imports were required.

## Tests Written
- `tests/FIX-080/test_fix080_version_flag.py`
  - `test_version_flag_exits_zero` — `--version` causes SystemExit(0)
  - `test_version_flag_prints_version` — output contains VERSION
  - `test_version_flag_prints_app_name` — output contains APP_NAME
  - `test_version_flag_does_not_import_gui` — tkinter / launcher.gui.app not imported
  - `test_no_version_flag_imports_app` — normal path still imports App (mocked)
  - `test_short_flag_not_supported` — `-V` does NOT trigger version exit

## Decisions
- Used `sys.argv` direct check (no argparse) per WP instructions — minimal surgical fix.
- Placed check after `PYTEST_CURRENT_TEST` guard so tests that invoke `main()` directly without `--version` are unaffected.

## Known Limitations
- Only `--version` is supported; `--help` and other flags are not handled (out of scope).
