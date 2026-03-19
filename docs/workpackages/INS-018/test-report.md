# Test Report — INS-018

**Tester:** Tester Agent
**Date:** 2026-03-19
**Iteration:** 1

## Summary

INS-018 implements infrastructure to bundle the Python 3.11 embeddable distribution with the installer across Windows, macOS, and Linux. All deliverables are present and correct. The implementation uses a safe no-op / conditional pattern — if the python-embed directory is absent at build time, every build script skips gracefully without error. All 52 tests pass (34 Developer + 18 Tester edge-case). No regressions detected in the wider test suite.

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| INS-018 developer suite (34 tests) | Unit | PASS | README content (6); launcher.spec conditionals (7); setup.iss [Files]+[UninstallDelete]+[Code]+PythonEmbedExists (8); build_dmg.sh conditional copy (5); build_appimage.sh conditional copy (5); release.yml commented CI note (3) |
| INS-018 Tester edge-case suite (18 tests) | Unit | PASS | See detail below |
| Full regression suite | Regression | PASS | No regressions in existing tests |

### Tester Edge-Case Tests (`tests/INS-018/test_ins018_edge_cases.py`)

18 additional tests covering scenarios the Developer suite did not exercise:

| # | Test | Rationale |
|---|------|-----------|
| 1 | `test_launcher_spec_python_embed_bundle_is_list_when_absent` | Verifies `_python_embed_bundle = []` is the default (empty-list fallback) |
| 2 | `test_launcher_spec_datas_merge_uses_plus_operator` | Confirms the merge uses `+` not `.extend()` (list concat — spec-safe) |
| 3 | `test_launcher_spec_python_exe_guard_in_os_path_join` | Guard uses `os.path.join(_PYTHON_EMBED_DIR, 'python.exe')` not a hard-coded Windows path |
| 4 | `test_setup_iss_python_embed_flags_contain_recursesubdirs` | `recursesubdirs` flag prevents silent omission of nested zip/dll files |
| 5 | `test_setup_iss_uninstall_delete_type_is_filesandordirs` | [UninstallDelete] uses `Type: filesandordirs`, not just `files`, so directory is removed |
| 6 | `test_setup_iss_check_function_name_exact_spelling` | `PythonEmbedExists` spelling consistent between [Files] and [Code] definition |
| 7 | `test_setup_iss_code_section_returns_boolean` | `PythonEmbedExists` returns `True`/`False` (Boolean return, not integer) |
| 8 | `test_build_dmg_python_embed_copy_destination_path` | macOS destination is `Contents/Resources/python-embed`, not root of bundle |
| 9 | `test_build_dmg_uses_cp_minus_r_for_directory` | `cp -r` used (recursive), not plain `cp` which would silently skip subdirs |
| 10 | `test_build_appimage_copy_destination_is_inside_appdir` | Linux destination is inside `$APPDIR`, not a system path |
| 11 | `test_build_appimage_uses_cp_minus_r_for_directory` | `cp -r` used (recursive) for directory copy |
| 12 | `test_readme_mentions_checksum_verification` | SHA256 verification documented so builders don't trust unsigned binaries |
| 13 | `test_readme_mentions_manual_download_step` | README explicitly states this is a manual step (not auto-downloaded) |
| 14 | `test_readme_python_embed_dir_name_consistent` | Directory name `python-embed` consistent throughout README |
| 15 | `test_release_yml_ci_note_block_is_commented` | All lines of the CI download block start with `#` (not accidentally active) |
| 16 | `test_setup_iss_no_unchecked_python_embed_files_entry` | Every `python-embed` [Files] entry has a `Check:` function (no unconditional install) |
| 17 | `test_launcher_spec_python_embed_dir_uses_dirname_of_spec` | `_PYTHON_EMBED_DIR` derived from `SPECPATH` / spec directory, not a hard-coded absolute path |
| 18 | `test_build_dmg_skip_message_references_python_embed` | Skip message references `python-embed` so build logs are informative |

## Security Review

- **Supply chain:** The README mandates SHA256 checksum verification before use. No executable is auto-downloaded. Risk: LOW.
- **Installation scope:** The [Files] entry is guarded by `PythonEmbedExists()`. No files are installed when the embed directory is absent. Risk: LOW.
- **Uninstall completeness:** `[UninstallDelete]` with `Type: filesandordirs` ensures the entire `{app}\python-embed` directory tree is removed on uninstall. No orphaned binaries remain.
- **Path traversal:** `_PYTHON_EMBED_DIR` is derived from `SPECPATH` (the spec file's own directory), not from user input. No traversal risk.
- **No unconditional subprocess calls:** All build script copy steps are inside `if [ -n "$PYTHON_EMBED_SRC" ]` guards.

## Bugs Found

None.

## TODOs for Developer

None.

## Verdict

**PASS — marking INS-018 as Done.**

All 52 tests pass. No regressions. All Pre-Done checklist items verified:
- [x] `dev-log.md` exists and is non-empty
- [x] `test-report.md` written by Tester
- [x] Test files exist in `tests/INS-018/`
- [x] All test runs logged in `test-results.csv`
- [x] Temp file `tmp_pytest.txt` deleted
