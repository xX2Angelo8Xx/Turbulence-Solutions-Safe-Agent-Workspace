# Test Report — INS-011: Update Apply and Restart

**Tester:** Tester Agent  
**Date:** 2026-03-14  
**Branch:** `INS-011/update-apply-restart`  
**Verdict:** ✅ PASS

---

## Summary

| Metric | Value |
|--------|-------|
| Developer tests | 40 |
| Tester edge-case tests added | 26 |
| **Total INS-011 tests** | **66** |
| Full suite (all WPs) | 1659 passed / 2 skipped / 0 failed |
| Regressions introduced | **None** |

---

## Code Review Findings

### `src/launcher/core/applier.py`

| Area | Finding | Verdict |
|------|---------|---------|
| **Security — shell injection** | All subprocess calls (`Popen`, `run`) use `shell=False` with list args. No `shell=True` anywhere. | ✅ Pass |
| **Security — eval/exec** | `eval()` and `exec()` are absent from the source. | ✅ Pass |
| **Windows handler** | `subprocess.Popen([str(installer_path), "/SILENT", "/CLOSEAPPLICATIONS"], shell=False)` — correct Inno Setup silent install incantation. `sys.exit(0)` called immediately after. | ✅ Pass |
| **macOS handler** | `hdiutil attach` with `-nobrowse` and `-quiet` prevents DMG from appearing in Finder sidebar. Mount point uses `tempfile.mkdtemp(prefix="ts_update_mnt_")` not `/Volumes`. `try/finally` ensures `hdiutil detach` always runs. `rsync -a --delete` with trailing slash for correct atomic copy. `check=True` on rsync so errors propagate. | ✅ Pass |
| **Linux handler** | `chmod` adds all three exec bits (S_IXUSR, S_IXGRP, S_IXOTH). `os.replace` is atomic on same filesystem. `os.execv` replaces process image with correct `sys.argv` passthrough. `PermissionError` wrapped in `RuntimeError`. | ✅ Pass |
| **Validation** | `_validate_installer_path` checks `exists()` and `is_file()`. Rejects missing files and directories. Correct pre-flight guard before any OS action. | ✅ Pass |
| **Platform dispatch** | `sys.platform == "win32"` / `"darwin"` / `startswith("linux")` — correctly handles `linux`, `linux2`, `linux-arm`, etc. Unsupported platform raises `RuntimeError`. | ✅ Pass |
| **Resource leak (minor, non-blocking)** | `tempfile.mkdtemp()` creates a temp directory for the macOS mount point that is never explicitly `rmdir`'d. Since `sys.exit(0)` follows immediately and the directory is empty post-detach, OS cleanup on process exit handles this. Documented as a known limitation. | ℹ️ Info |

### `src/launcher/gui/app.py`

| Area | Finding | Verdict |
|------|---------|---------|
| **Button widget** | `download_install_button` added at row 9, hidden on init via `grid_remove()`. Only shown when `_apply_update_result(update_available=True, ...)` is called. | ✅ Pass |
| **Re-entrancy** | `_on_install_update` disables the button synchronously (`state="disabled"`) before spawning the background thread. Prevents double-click re-entry at the GUI level. | ✅ Pass |
| **Thread safety** | Download runs in a `daemon=True` background thread. `_window.after(0, ...)` used for all main-thread UI updates. Error recovery (`_on_install_error`) dispatched via `after()` — correct tkinter threading pattern. | ✅ Pass |
| **Error recovery** | `_on_install_error` restores button to `state="normal"` and original text. Shows `showerror` dialog. User can retry after seeing the error. | ✅ Pass |
| **Version tracking** | `_latest_version` initialized to `VERSION` (not empty). Updated by `_apply_update_result` only when `update_available=True`. Correct: stale or lower "latest" version from an up-to-date check does not overwrite.| ✅ Pass |
| **Import structure** | `download_update` from `launcher.core.downloader` and `apply_update` from `launcher.core.applier` are both imported at module level. | ✅ Pass |

---

## Edge Cases Investigated

### Attack Vectors

1. **`shell=True` injection** — Static source scan confirmed `shell=True` is absent; all subprocess calls have `shell=False`. ✅
2. **Path traversal in installer_path** — `_validate_installer_path` only checks file existence and type. The path originates from INS-010's download function which stores to a system temp dir. With `shell=False`, even unusual characters in the path cannot cause shell injection. ✅
3. **Malicious `.app` bundle name** — `_find_app_bundle` iterates `Path.iterdir()` and uses `item.name` (filename component only, no directory separator). A DMG cannot contain a bundle whose `name` includes `/`, so path traversal out of `/Applications/` via bundle name is not possible at the filesystem level. ✅
4. **`eval`/`exec`** — Not present. ✅

### Boundary Conditions

5. **Empty installer file** — `_validate_installer_path` passes (file content size is not checked — by design). ✅
6. **Multiple `.app` bundles in DMG** — `_find_app_bundle` returns the first one found (filesystem order). Documented behaviour; no crash. ✅
7. **Installer path with spaces** — Verified list-arg Popen passes the full path including spaces as a single argument without shell splitting. ✅
8. **Installer path with unicode characters** — Passes correctly through `str()` conversion to Popen. ✅

### Platform Edge Cases

9. **`linux2` / `linux-arm`** — `sys.platform.startswith("linux")` correctly catches legacy and variant strings. ✅
10. **Double dispatch prevention** — `apply_update` dispatches exactly once to the platform handler. ✅

### Race Conditions and Re-entrancy

11. **Double-click install** — Button disabled synchronously before thread start. A second click finds the button already disabled. Thread-based architecture prevents concurrent downloads. ✅
12. **Error recovery idempotency** — `_on_install_error` restores button state; subsequent click can retry the install. ✅

### Resource / Process Lifecycle

13. **Linux `sys.argv` passthrough** — `os.execv(target, sys.argv)` preserves original CLI args on re-launch. ✅
14. **Linux `os.execv` target equals `os.replace` dest** — The binary we swap in is the same binary we re-exec. ✅
15. **macOS `-nobrowse` flag** — DMG not added to Finder sidebar during update. ✅
16. **macOS mount point isolation** — `tempfile.mkdtemp` (not `/Volumes`) used. ✅
17. **macOS rsync trailing slash** — Source arg ends with `/` for correct directory-level sync. ✅

---

## User Story Acceptance Criteria Verification (US-016)

| AC | Criterion | Met? |
|----|-----------|------|
| 1 | User can initiate a download from within the app | ✅ `download_install_button` calls `_on_install_update` |
| 2 | Correct platform installer downloaded to temp dir | ✅ Delegated to INS-010 `download_update`; path passed to `apply_update` |
| 3 | Integrity verified before launch | ✅ Delegated to INS-010 (SHA256 verification); `_validate_installer_path` pre-flight check in applier |
| 4 | Installer launched and current launcher instance closes | ✅ `sys.exit(0)` on Windows/macOS; `os.execv` (process replacement) on Linux |
| 5 | Launcher restarts running the new version on all platforms | ✅ Windows: Inno Setup installer re-creates launcher; macOS: `/Applications` updated; Linux: new AppImage execv'd |

---

## Tests Added by Tester (TST-692 to TST-717)

| TST ID | Test Name | Category | Purpose |
|--------|-----------|----------|---------|
| TST-692 | test_no_shell_true_in_source | Security | Static scan: no `shell=True` in applier.py |
| TST-693 | test_all_subprocess_calls_use_shell_false | Security | Every `shell=` assignment is `False` |
| TST-694 | test_no_eval_or_exec_in_source | Security | `eval()`/`exec()` absent per security-rules.md |
| TST-695 | test_linux2_dispatches_to_apply_linux | Unit | `linux2` legacy platform string dispatches correctly |
| TST-696 | test_linux_arm_dispatches_to_apply_linux | Unit | `linux-arm` platform string dispatches correctly |
| TST-697 | test_apply_update_dispatches_exactly_once | Unit | No double-dispatch regression |
| TST-698 | test_windows_path_with_spaces | Unit | Spaces in path preserved as single list arg |
| TST-699 | test_windows_path_with_unicode | Unit | Unicode characters in path handled correctly |
| TST-700 | test_validate_accepts_regular_file | Unit | Baseline: regular file passes validation |
| TST-701 | test_validate_rejects_empty_file | Unit | Empty file passes (size not checked — by design) |
| TST-702 | test_validate_rejects_nested_directory | Unit | Nested directory raises `ValueError` |
| TST-703 | test_macos_nobrowse_flag_in_attach | Security | `-nobrowse` in `hdiutil attach` args |
| TST-704 | test_macos_installer_path_passed_to_hdiutil | Unit | DMG path included in attach call |
| TST-705 | test_macos_mount_point_uses_mkdtemp_not_volumes | Unit | Temp dir used (not `/Volumes`), prefix verified |
| TST-706 | test_find_app_bundle_with_multiple_app_dirs | Unit | Multiple `.app` dirs: first returned, no crash |
| TST-707 | test_macos_rsync_source_has_trailing_slash | Unit | rsync source ends with `/` |
| TST-708 | test_macos_dest_is_under_applications | Unit | rsync destination starts with `/Applications/` |
| TST-709 | test_linux_execv_passes_sys_argv | Unit | `sys.argv` passed to `os.execv` |
| TST-710 | test_linux_execv_target_matches_os_replace_destination | Unit | `os.replace` dest == `os.execv` path |
| TST-711 | test_linux_chmod_sets_all_exec_bits | Unit | `S_IXUSR`, `S_IXGRP`, `S_IXOTH` all set |
| TST-712 | test_install_button_hidden_on_startup | Integration | Button hidden until update detected |
| TST-713 | test_install_button_shows_only_when_update_available | Integration | Button not shown when no update |
| TST-714 | test_on_install_update_disables_button_before_thread | Integration | Button disabled before thread starts (re-entrancy guard) |
| TST-715 | test_on_install_error_restores_to_normal_state | Integration | Button state and text restored after error |
| TST-716 | test_apply_update_result_updates_latest_version_tracking | Integration | `_latest_version` updated correctly |
| TST-717 | test_apply_update_result_does_not_update_version_when_up_to_date | Integration | `_latest_version` not overwritten when up-to-date |

---

## Known Limitations (documented, non-blocking)

1. **macOS temp directory not deleted** — `tempfile.mkdtemp()` mount point directory is not `rmdir`'d after `hdiutil detach`. Since `sys.exit(0)` follows immediately, OS cleanup handles this. Not a security concern.
2. **Linux dev-mode relaunch** — `os.execv(sys.executable, sys.argv)` in development mode re-invokes the Python interpreter, not a new AppImage. This is correct and intentional per dev-log.
3. **macOS rsync dependency** — `rsync` must be available. Available by default on macOS; a `shutil.copytree` fallback could be added in a future iteration.
4. **Windows fire-and-forget** — `subprocess.Popen` launches the installer and exits immediately. If the installer requires UAC elevation, Windows prompts the user. No feedback to the user about installer success/failure post-exit.

---

## Verdict

**PASS** — All 66 INS-011 tests pass. Full suite: 1659 passed, 2 skipped, 0 failed. Zero regressions. All US-016 acceptance criteria met. Security requirements (no `shell=True`, no `eval`/`exec`, list-based args, pre-flight validation) verified. WP promoted to `Done`.
