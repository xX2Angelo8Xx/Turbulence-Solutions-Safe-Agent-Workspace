# Dev Log — INS-011

**Developer:** Developer Agent
**Date started:** 2026-03-14
**Iteration:** 1

## Objective

Launch the downloaded installer and close the current Launcher instance; handle
platform differences (Windows .exe silent install, macOS .dmg, Linux .AppImage swap).
Goal: Launcher restarts running the new version after update completes on all 3 OSes.

## Implementation Summary

Created `src/launcher/core/applier.py` with the following public function:

- `apply_update(installer_path: Path) -> None` — validates the installer path,
  dispatches to the platform-specific handler, and exits the launcher after
  launching the installer.

Platform handlers:
- **Windows** (`_apply_windows`): Runs the Inno Setup .exe with
  `/SILENT /CLOSEAPPLICATIONS` flags via `subprocess.Popen`, then `sys.exit(0)`.
- **macOS** (`_apply_macos`): Uses `hdiutil attach` to mount the .dmg to a
  temp directory, finds the .app bundle, copies it to `/Applications/` using
  `rsync -a --delete`, unmounts with `hdiutil detach`, then `sys.exit(0)`.
- **Linux** (`_apply_linux`): Makes the AppImage executable with
  `chmod +x`, swaps it with `os.replace`, then relaunches via `os.execv`.

Security measures:
- `shell=False` on all subprocess calls; args always passed as a list.
- `_validate_installer_path` verifies the file exists and is a regular file.
- macOS mount point uses a dedicated temp directory (not `/Volumes`).
- Linux relaunch uses `os.execv` (replaces current process) — no orphan process.

UI changes in `src/launcher/gui/app.py`:
- Added `download_update` import from `launcher.core.downloader`.
- Added `apply_update` import from `launcher.core.applier`.
- Added `_latest_version` attribute to track the latest available version.
- Added `download_install_button` (hidden by default) at row 9 below the banner.
- `_apply_update_result` now stores the latest_version and shows/hides the button.
- Added `_on_install_update` method: runs download in a background thread, then
  calls `apply_update` on success; shows error dialog on failure.

## Files Changed

- `src/launcher/core/applier.py` — new file; apply-and-restart logic
- `src/launcher/gui/app.py` — added "Download & Install Update" button and handler

## Tests Written

All tests in `tests/INS-011/test_ins011_applier.py`:

- `TestValidateInstallerPath`:
  - `test_valid_file_passes` — valid tmp file raises nothing
  - `test_missing_file_raises_file_not_found` — non-existent path raises FileNotFoundError
  - `test_directory_raises_value_error` — directory path raises ValueError

- `TestPlatformDispatch`:
  - `test_windows_dispatches_to_apply_windows` — win32 calls _apply_windows
  - `test_macos_dispatches_to_apply_macos` — darwin calls _apply_macos
  - `test_linux_dispatches_to_apply_linux` — linux calls _apply_linux
  - `test_unsupported_platform_raises` — unknown platform raises RuntimeError

- `TestWindowsApply`:
  - `test_windows_popen_called_with_list_args` — subprocess.Popen receives a list
  - `test_windows_popen_no_shell_true` — shell=False (not shell=True)
  - `test_windows_passes_silent_flag` — /SILENT in args
  - `test_windows_passes_close_applications_flag` — /CLOSEAPPLICATIONS in args
  - `test_windows_exits_after_popen` — sys.exit(0) called
  - `test_windows_installer_path_first_arg` — installer is args[0]

- `TestMacosApply`:
  - `test_macos_hdiutil_attach_called` — hdiutil attach invoked
  - `test_macos_hdiutil_attach_no_shell` — shell=False
  - `test_macos_hdiutil_detach_called` — hdiutil detach invoked after copy
  - `test_macos_rsync_copies_app` — rsync invoked with /Applications target
  - `test_macos_exits_after_install` — sys.exit(0) called
  - `test_macos_detach_on_error` — detach still called if rsync fails

- `TestLinuxApply`:
  - `test_linux_makes_appimage_executable` — chmod sets exec bits
  - `test_linux_os_replace_called` — os.replace called with correct args
  - `test_linux_execv_called` — os.execv called to relaunch
  - `test_linux_permission_error_raises_runtime_error` — PermissionError → RuntimeError

- `TestFindAppBundle`:
  - `test_finds_app_bundle_in_directory` — .app dir is found
  - `test_raises_if_no_app_bundle` — RuntimeError if no .app found
  - `test_ignores_non_app_items` — .app file (not dir) is ignored

- `TestNoShellTrue`:
  - `test_windows_subprocess_no_shell_true` — Windows subprocess args contain no shell=True
  - `test_macos_subprocess_no_shell_true` — macOS subprocess calls pass shell=False

## Known Limitations

- macOS: uses `rsync` (available by default on macOS) for the copy step.
  If rsync is absent the copy will fail; a fallback to `shutil.copytree` could
  be added in a future iteration.
- Linux: `os.execv` replaces the current process image. If the launcher is not
  running as a standalone AppImage (e.g. during development with Python), the
  path returned by `sys.executable` is a Python interpreter.  This is intentional:
  during development the swap is a no-op and the relaunch re-runs the interpreter.
- Windows: `subprocess.Popen` is used (fire-and-forget). The installer runs in
  the background and the launcher exits immediately. If the installer requires
  elevation (UAC), Windows will prompt automatically.
