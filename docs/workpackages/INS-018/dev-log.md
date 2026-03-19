# Dev Log — INS-018

**Developer:** Developer Agent
**Date started:** 2026-03-19
**Iteration:** 1

## Objective
Add infrastructure to bundle the Python 3.11 embeddable distribution with the installer across all three platforms (Windows, macOS, Linux). The python-embed directory is optional at build time — when absent the build still succeeds cleanly (no-op paths). When present, it is bundled and installed alongside the application so the launcher has a self-contained Python runtime.

## Implementation Summary
- Created `src/installer/python-embed/README.md` documenting the manual download step, expected directory layout, SHA256 checksum verification, and per-platform notes.
- Updated `launcher.spec` to conditionally include the python-embed directory as a PyInstaller datas entry only when `python.exe` is present, using `_PYTHON_EMBED_DIR` and `_python_embed_bundle` variables merged into the `datas` list.
- Updated `src/installer/windows/setup.iss` with: a `[Files]` entry (Source: `..\python-embed\*`, Flags: `recursesubdirs`, Check: `PythonEmbedExists`); an `[UninstallDelete]` entry for `{app}\python-embed`; and a `[Code]` section defining `PythonEmbedExists()` using `FileExists`.
- Updated `src/installer/macos/build_dmg.sh` to copy python-embed into `Contents/Resources/python-embed` when `PYTHON_EMBED_SRC` is populated, with a graceful skip message when absent.
- Updated `src/installer/linux/build_appimage.sh` to copy python-embed into the AppDir when `PYTHON_EMBED_SRC` is populated, with a graceful skip message when absent.
- Updated `.github/workflows/release.yml` with a commented-out CI download note block prefixed `# INS-018` so the step is documented but not yet active.

## Files Changed
- `src/installer/python-embed/README.md` — new file; download instructions, layout, checksum, per-platform notes
- `launcher.spec` — added `import os`, `_PYTHON_EMBED_DIR`, `_python_embed_bundle` conditional datas, merged into datas
- `src/installer/windows/setup.iss` — [Files] python-embed entry + [UninstallDelete] + [Code] PythonEmbedExists
- `src/installer/macos/build_dmg.sh` — PYTHON_EMBED_SRC variable, conditional copy into Resources/python-embed
- `src/installer/linux/build_appimage.sh` — PYTHON_EMBED_SRC variable, conditional copy into AppDir/python-embed
- `.github/workflows/release.yml` — # INS-018 commented CI download step

## Tests Written
- `tests/INS-018/test_ins018_bundle_python_embed.py` (34 tests):
  - `test_python_embed_readme_exists` — README file exists on disk
  - `test_python_embed_readme_mentions_windows_download` — python.org/ftp/python URL present
  - `test_python_embed_readme_mentions_macos` — macOS section present
  - `test_python_embed_readme_mentions_linux` — Linux section present
  - `test_python_embed_readme_mentions_expected_layout` — python.exe in layout
  - `test_python_embed_readme_mentions_security` — SHA256/checksum mention
  - `test_launcher_spec_imports_os` — `import os` present
  - `test_launcher_spec_has_python_embed_dir_variable` — `_PYTHON_EMBED_DIR` defined
  - `test_launcher_spec_checks_python_exe_before_adding` — guarded on python.exe
  - `test_launcher_spec_python_embed_bundle_variable` — `_python_embed_bundle` defined
  - `test_launcher_spec_python_embed_destination` — `'python-embed'` destination set
  - `test_launcher_spec_merges_datas` — `] + _python_embed_bundle` merge present
  - `test_launcher_spec_conditional_does_not_break_empty_case` — `_python_embed_bundle = []` default
  - `test_setup_iss_has_python_embed_files_entry` — python-embed in [Files]
  - `test_setup_iss_python_embed_source_path` — `..\python-embed\*` source path
  - `test_setup_iss_python_embed_dest_dir` — `{app}\python-embed` dest
  - `test_setup_iss_python_embed_check_function` — PythonEmbedExists referenced
  - `test_setup_iss_has_code_section` — [Code] section exists
  - `test_setup_iss_python_embed_exists_uses_file_exists` — FileExists() used
  - `test_setup_iss_uninstall_delete_python_embed` — [UninstallDelete] entry
  - `test_setup_iss_recursesubdirs_flag_on_python_embed` — recursesubdirs flag
  - `test_build_dmg_references_python_embed` — python-embed in build_dmg.sh
  - `test_build_dmg_checks_for_python_embed_presence` — PYTHON_EMBED_SRC variable
  - `test_build_dmg_copies_to_resources` — Resources/python-embed copy
  - `test_build_dmg_python_embed_conditional` — if-block guards copy
  - `test_build_dmg_skips_gracefully_when_not_populated` — skip message present
  - `test_build_appimage_references_python_embed` — python-embed in build_appimage.sh
  - `test_build_appimage_checks_for_python_embed_presence` — PYTHON_EMBED_SRC variable
  - `test_build_appimage_copies_into_appdir` — AppDir copy
  - `test_build_appimage_python_embed_conditional` — if-block guards copy
  - `test_build_appimage_skips_gracefully_when_not_populated` — skip message present
  - `test_release_yml_has_python_embed_ci_note` — python-embed mentioned in release.yml
  - `test_release_yml_ci_note_is_commented_out` — # INS-018 comment block present
  - `test_release_yml_ci_note_references_python_org` — python.org URL in comment

## Known Limitations
- The python-embed directory is NOT included in the repository (too large, ~15 MB). Builders must download and place it manually before building, following the README instructions.
- The CI pipeline does not yet automatically download the embeddable distribution; the commented step in release.yml is a reference for a future INS WP to activate.
- macOS and Linux python-embed handling uses a shell `cp -r` — no integrity check at build time beyond file presence.
