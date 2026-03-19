# Test Report — FIX-039

**WP:** FIX-039 — Skip launcher re-sign inside .app — verify pre-bundle binary  
**Verdict:** PASS  
**Tester:** Tester Agent  
**Date:** 2026-03-18  
**Branch:** fix/FIX-039-skip-launcher-resign  
**Bug Reference:** BUG-072

---

## Summary

FIX-039 is approved. The implementation correctly fixes BUG-072 by removing
codesign operations that targeted `Contents/MacOS/launcher` (the `CFBundleExecutable`)
inside the `.app` bundle, which triggered macOS bundle validation and caused CI failures
due to non-code data files (TS-Logo.png) being treated as code objects. The pre-bundle
binary at `dist/launcher/launcher` retains its PyInstaller ad-hoc signature and is
verified there instead. All 24 FIX-039 tests pass; 65 total failures all pre-existing.

---

## Review Findings

### Code Review

**`src/installer/macos/build_dmg.sh`**

| Check | Result |
|-------|--------|
| `codesign --force --sign - "${APP_BUNDLE}/Contents/MacOS/launcher"` removed | ✓ REMOVED |
| `codesign --verify "${APP_BUNDLE}/Contents/MacOS/launcher"` removed | ✓ REMOVED |
| `codesign --verify "${DIST_DIR}/launcher/launcher"` added | ✓ PRESENT |
| `.dylib`, `.so`, `Python.framework` signing unchanged | ✓ PRESERVED |
| `${DIST_DIR}` variable form used in verify (not hardcoded `dist/`) | ✓ CORRECT |
| Verify appears before `hdiutil create` | ✓ CORRECT ORDER |
| No `--strict` flag on pre-bundle verify | ✓ SAFE |
| Explanatory comment about CFBundleExecutable trigger present | ✓ DOCUMENTED |
| NOTE comment that PyInstaller already ad-hoc signs binary | ✓ DOCUMENTED |
| `.dylib`/`.so` signing scoped to `_internal/` subdirectory | ✓ CORRECT |
| LF line endings preserved | ✓ NO CRLF |

**`.github/workflows/release.yml`**

| Check | Result |
|-------|--------|
| `codesign --verify dist/...Contents/MacOS/launcher` removed from CI | ✓ REMOVED |
| `codesign --verify dist/launcher/launcher` added | ✓ PRESENT |
| `Python.framework` verification line unchanged | ✓ PRESERVED |
| No reference to CFBundleExecutable path in Verify step | ✓ CONFIRMED |
| `--strict` not accidentally added | ✓ SAFE |

### Implementation Assessment

The implementation is minimal and correctly scoped:
- Only two files changed, exactly those listed in the WP.
- No changes to DMG creation, Info.plist, AppImage, Windows installer, or Python source.
- The fix correctly targets the root cause: CFBundleExecutable triggering bundle validation.
- PyInstaller's ad-hoc signature on the pre-bundle binary is preserved via `cp -R` into the `.app`.
- The verification path (`${DIST_DIR}/launcher/launcher`) correctly precedes DMG assembly.

No security concerns introduced. The codesign approach (ad-hoc, not Developer ID) was
already the design; FIX-039 only moves the verification target, not the signing authority.

---

## Tests Run

### FIX-039 Developer Tests (TST-1826) — pre-existing

13 developer tests had already been logged. All 13 pass. Verified by re-running.

### FIX-039 Tester Edge-Case Tests (TST-1827)

11 Tester-added edge-case tests in `tests/FIX-039/test_fix039_edge_cases.py`:

| # | Test | Covers |
|---|------|--------|
| 1 | `test_no_codesign_sign_any_form_on_bundle_launcher` | No `--sign` of any form on `Contents/MacOS/launcher` |
| 2 | `test_build_dmg_has_cfbundleexecutable_comment` | Explanatory comment about CFBundleExecutable present |
| 3 | `test_build_dmg_verify_uses_dist_dir_variable` | `${DIST_DIR}` variable form in verify command |
| 4 | `test_build_dmg_verify_before_hdiutil` | Verify precedes DMG creation |
| 5 | `test_release_yml_verify_step_no_app_path` | CI step does not verify launcher inside `.app` |
| 6 | `test_release_yml_verify_step_uses_pre_bundle_launcher` | CI step uses `dist/launcher/launcher` |
| 7 | `test_build_dmg_verify_pre_bundle_no_strict` | No `--strict` on pre-bundle verify |
| 8 | `test_build_dmg_has_pyinstaller_presign_note` | NOTE comment about PyInstaller pre-signing |
| 9 | `test_build_dmg_dylib_signing_scoped_to_internal` | `.dylib` signing scoped to `_internal/` |
| 10 | `test_build_dmg_so_signing_scoped_to_internal` | `.so` signing scoped to `_internal/` |
| 11 | `test_build_dmg_launcher_verify_before_framework_verify` | Launcher verify before framework verify |

**Result: 11/11 PASS**

### Full Regression Suite (TST-1828)

**65 failed, 3661 passed, 29 skipped, 1 xfailed**

Failure breakdown:

| Category | Count | Cause |
|----------|-------|-------|
| Version-pin (FIX-009 CSV) | 5 | Pre-existing: test-results.csv uses `ID` header, tests expect `TST-` column name |
| Version-pin (FIX-010, FIX-014, FIX-017, FIX-019, FIX-020, FIX-030) | 38 | Pre-existing: tests hardcode older expected version (1.0.x or 2.0.0) |
| Version-pin (INS-005, INS-006, INS-007) | 4 | Pre-existing: tests hardcode version 2.0.1 |
| Superseded by FIX-038 (FIX-028×4, FIX-029×3, FIX-031×5, FIX-037×1) | 13 | Pre-existing from TST-1825: tests for bundle-level `--deep --strict` signing removed by FIX-038 |
| Superseded by FIX-039 (FIX-038×2) | 2 | **New:** `test_main_executable_signing_present` and `test_signing_order_framework_before_launcher` in FIX-038 expect launcher inside-bundle signing, which FIX-039 intentionally removes |
| INS-005 filesandirs | 1 | Pre-existing: `test_uninstall_delete_type_is_filesandirs` |
| **Total** | **65** | |

**Zero new failures outside of the 2 superseded FIX-038 tests.**

The 2 FIX-038 superseded failures are expected and acceptable:
- `test_main_executable_signing_present` checked that `codesign --force --sign - .../launcher` was present inside the `.app`. FIX-039 explicitly removes this (that is the bug fix).
- `test_signing_order_framework_before_launcher` checked signing order leading to launcher signing. FIX-039 removes launcher signing entirely, making this test vacuous.
- FIX-039's own tests (`test_regression_no_sign_cfbundleexecutable_in_app`, etc.) explicitly verify the inverse behaviour, serving as the new correctness gate.

This pattern is consistent with FIX-038 Tester PASS (TST-1825) which accepted 11 superseded signing tests.

---

## Edge-Case Analysis

### Attack Vectors / Security

No security regression. Ad-hoc signing (`-` identity) was already the design.
The change reduces risk by avoiding the macOS bundle validation path that previously
caused CI to reject valid builds when non-code files were present.

### Boundary Conditions

- **What if `dist/launcher` doesn't exist?** The script already guards: Step 1 runs PyInstaller if `dist/launcher/` is absent. Verify would fail gracefully with `codesign: error: ... No such file or directory` before the DMG is created. This is correct fail-closed behavior.
- **What if the pre-bundle binary is unsigned?** `codesign --verify` returns non-zero and `set -euo pipefail` aborts the script. Correct.
- **What if Python.framework is unsigned?** Same abort behavior. Correct.
- **What if `_internal/` has no .dylib or .so files?** The `find ... -exec codesign` commands succeed silently (find returns 0 with no matches). Not a problem.

### Platform Quirks

- On Intel Mac (not built in CI): same script, same behavior. On Apple Silicon, PyInstaller produces ARM64 binaries that are re-signed by `codesign --force --sign - {}`. No platform-specific edge cases introduced.
- On Windows/Linux: `build_dmg.sh` is not executed. No impact.

### Resource Leaks

None. The staging directory (`mktemp -d`) is cleaned up with `rm -rf "${STAGING_DIR}"` after `hdiutil create`. No new resources allocated.

---

## Pre-Done Checklist

- [x] `docs/workpackages/FIX-039/dev-log.md` exists and is non-empty
- [x] `docs/workpackages/FIX-039/test-report.md` written by Tester
- [x] Test files exist in `tests/FIX-039/` (13 developer + 11 Tester = 24 tests)
- [x] All test runs logged in `docs/test-results/test-results.csv`
- [x] `git add -A` staged
- [x] Commit: `FIX-039: Tester PASS`
- [x] Push: `git push origin fix/FIX-039-skip-launcher-resign`
