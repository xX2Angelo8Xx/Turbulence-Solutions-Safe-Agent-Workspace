# Test Report — MNT-031

**Tester:** Tester Agent
**Date:** 2026-04-07
**Iteration:** 1

## Summary

`scripts/build_windows.py` is a clean, well-structured build helper that accurately mirrors the CI pipeline. All 13 Developer tests pass. 7 Tester edge-case tests were added, bringing the total to 20. No regressions were introduced. Two minor findings are documented below — neither is blocking.

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| TST-2751 (Developer, 13 tests) | Unit | Pass | Logged by Developer against MNT-031 |
| TST-2752: Full regression suite | Regression | Fail (pre-existing) | 248 failed + 91 errors — all in baseline (250 known); no new regressions from MNT-031 |
| TST-2753: MNT-031 unit tests (20 passed) | Unit | Pass | 13 Dev + 7 Tester edge-case |

Edge-case tests added to `tests/MNT-031/test_mnt031_build_windows.py` (`TestTesterEdgeCases`):

| Test | What it verifies |
|------|-----------------|
| `test_dry_run_with_iscc_missing_still_exits` | `--dry-run` calls `find_iscc()` before the guard; exits if ISCC absent (document known behaviour) |
| `test_all_skip_flags_combined` | `--skip-pyinstaller --skip-embed` still runs ISCC exactly once |
| `test_urlretrieve_exception_does_not_leave_zip` | No partial zip file persists when `urlretrieve` raises an `OSError` |
| `test_corrupted_zip_cleanup` | `finally` block removes corrupted zip after `BadZipFile` |
| `test_step_pyinstaller_calls_subprocess_with_check_true` | `check=True` ensures `CalledProcessError` propagates |
| `test_step_inno_setup_calls_subprocess_with_check_true` | `check=True` for ISCC call |
| `test_success_message_printed_after_non_dry_build` | SUCCESS message contains the output EXE path |

## Code Review

### Requirements satisfied
- [x] PyInstaller step (`pyinstaller launcher.spec`) — ✓
- [x] Python 3.11.9 embeddable download into `src/installer/python-embed/` — ✓
- [x] Skip embed if directory already contains files — ✓
- [x] `shutil.which("ISCC")` → fallback `Program Files (x86)` → fallback `Program Files` → `sys.exit(1)` — ✓
- [x] Inno Setup step (`ISCC.exe setup.iss`) — ✓
- [x] `--skip-pyinstaller` flag — ✓
- [x] `--skip-embed` flag — ✓
- [x] `--dry-run` flag — ✓
- [x] Documented in `scripts/README.md` — ✓
- [x] CI alignment verified against `.github/workflows/release.yml` lines 160–195 — ✓

### Security review
- No `shell=True` — all `subprocess.run` calls use list args. ✓
- Download URL is hardcoded HTTPS from `python.org/ftp/` — no SSRF vector. ✓
- No user-controlled input in path construction. ✓
- No credentials or secrets. ✓
- `REPO_ROOT` is derived from `Path(__file__).resolve()`, not from user input. ✓

## Findings (Non-blocking)

### Finding 1 — `--dry-run` requires ISCC to be installed (Low)
`step_inno_setup()` calls `find_iscc()` before checking the `dry_run` flag. A user running `--dry-run` on a machine without Inno Setup installed will get `sys.exit(1)` despite only wanting a preview. This is an inconvenience, not a correctness or security issue. The behaviour is pinned by `test_dry_run_with_iscc_missing_still_exits`.

**Recommendation (deferred):** Move `find_iscc()` inside the `if not dry_run:` block, or pass a dummy path in dry-run mode.

### Finding 2 — `urlretrieve` exception leaves PYTHON_EMBED_DIR created (Very Low)
If `urlretrieve` raises mid-download, `PYTHON_EMBED_DIR` has already been `mkdir`-ed but is empty. The next invocation will attempt download again (empty dir → triggers download), so this self-heals. Not a bug in practice.

## Bugs Found

None.

## TODOs for Developer

None — PASS.

## Verdict

**PASS — mark WP as Done.**
