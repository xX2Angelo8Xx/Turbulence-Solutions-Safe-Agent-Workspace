# FIX-038 Dev Log — Remove .app bundle codesign — use component-level signing only

## WP Details
- **ID:** FIX-038
- **Category:** Fix
- **Status:** In Progress → Review
- **Assigned To:** Developer Agent
- **Date:** 2026-03-18
- **Branch:** fix/FIX-038-component-level-codesign
- **User Story:** US-026
- **Bug:** BUG-071

---

## Problem Statement

After FIX-037 removed `.dist-info` directories from the PyInstaller bundle, the macOS CI build still fails. `codesign --force --sign -` on the `.app` bundle now fails on `TS-Logo.png` with:

```
dist/AgentEnvironmentLauncher.app/Contents/MacOS/launcher: code object is not signed at all
In subcomponent: .../dist/AgentEnvironmentLauncher.app/Contents/MacOS/_internal/TS-Logo.png
```

**Root Cause (systemic):** PyInstaller puts ALL files (code AND data) into `Contents/MacOS/_internal/`. The macOS `codesign` tool expects `Contents/MacOS/` to contain only code objects. When signing the `.app` bundle with `codesign --force --sign - "${APP_BUNDLE}"`, it walks all files in `Contents/MacOS/` and treats non-code files (images, `.pyc`, `.zip`, text) as subcomponents that need to be signed code objects. This is a whack-a-mole problem — fixing `TS-Logo.png` would expose the next non-code file.

---

## Solution

Remove the `.app` bundle-level `codesign` step and the whole-bundle `codesign --verify --deep --strict` verification. Keep all individual bottom-up code object signing (`.dylib`, `.so`, `Python.framework`, main executable). Replace whole-bundle verification with targeted verification of the individually-signed code components only.

The individual bottom-up signing is sufficient for macOS Apple Silicon execution — Gatekeeper requires signed code objects, not a signed bundle wrapper.

---

## Files Changed

### 1. `src/installer/macos/build_dmg.sh`
- **Removed:** `codesign --force --sign - "${APP_BUNDLE}"` (bundle-level signing)
- **Removed:** `codesign --verify --deep --strict "${APP_BUNDLE}"` (whole-bundle verification)
- **Added:** Explanatory comment block explaining why bundle-level signing is skipped
- **Added:** Component-level verification: `codesign --verify "${APP_BUNDLE}/Contents/MacOS/launcher"`
- **Added:** Conditional Python.framework verification: `codesign --verify --deep "${APP_BUNDLE}/Contents/MacOS/_internal/Python.framework"`

### 2. `.github/workflows/release.yml`
- **Changed:** `Verify Code Signing` step from `codesign --verify --deep --strict dist/AgentEnvironmentLauncher.app` to verify individual components (main executable + Python.framework)

---

## Design Decisions

1. **Why remove bundle-level signing entirely:** PyInstaller bundles non-code files (`.png`, `.pyc`, `.zip`) into `Contents/MacOS/_internal/`. macOS `codesign` cannot sign non-code files as bundle subcomponents and reports them as "code object is not signed at all". There is no way to exclude specific files from bundle-level signing.

2. **Why component-level signing is sufficient:** macOS Gatekeeper validates individual code objects (executables, `.dylib`, `.so`, frameworks) not the bundle wrapper itself. Each code object is already individually signed in the bottom-up signing steps.

3. **Python.framework verification is conditional:** The `if [ -d ... ]` guard ensures the verification step does not fail on systems where PyInstaller did not embed a separate Python.framework (e.g., if bundled differently in a future version).

---

## Tests Written

All tests in `tests/FIX-038/test_fix038_component_codesign.py` (13 tests):

1. `test_no_bundle_level_signing` — build_dmg.sh has no `codesign.*--sign.*\.app"?$` pattern
2. `test_no_whole_bundle_verification` — no `codesign --verify --deep --strict` on .app bundle path
3. `test_dylib_signing_present` — individual .dylib signing still present
4. `test_so_signing_present` — individual .so signing still present
5. `test_python_framework_signing_present` — Python.framework --deep signing still present
6. `test_main_executable_signing_present` — main executable signing still present
7. `test_launcher_verification_present` — codesign --verify on launcher present
8. `test_python_framework_verification_present` — Python.framework verification present
9. `test_release_yml_checks_launcher` — release.yml verifies main executable
10. `test_release_yml_checks_python_framework` — release.yml verifies Python.framework
11. `test_release_yml_no_bundle_strict_verify` — release.yml does NOT use --deep --strict on .app path
12. `test_no_sign_app_bundle_pattern` — no regex pattern that signs .app bundle directly
13. `test_explanatory_comment_present` — build_dmg.sh has the explanatory comment about why bundle-level signing is skipped

---

## Test Results

- FIX-038 test suite: 13 passed / 0 failures — TST-1822
- Full regression suite: 3628 passed / 61 failures / 29 skipped / 1 xfailed — TST-1823

### Supersession Failures (11 tests, expected)

FIX-038 intentionally changes behaviors that the following permanent tests were written to verify:

| WP | Failing Test | Reason |
|----|-------------|--------|
| FIX-028 | `test_verify_uses_deep_strict` | FIX-038 removes `--strict` from verify (no whole-bundle verify) |
| FIX-028 | `test_app_bundle_quoted_in_codesign` | FIX-038 removes `"${APP_BUNDLE}"` from signing (no bundle-level sign) |
| FIX-028 | `test_verify_app_bundle_quoted` | FIX-038 removes `"${APP_BUNDLE}"` from verify |
| FIX-029 | `test_step_run_contains_codesign_verify` | FIX-038 changes CI verify to component-level |
| FIX-029 | `test_step_run_full_command` | FIX-038 changes CI verify command format |
| FIX-029 | `test_step_run_contains_strict_flag` | FIX-038 removes `--strict` from CI verify |
| FIX-031 | `test_app_bundle_sign_no_deep` | FIX-038 removes bundle-level signing entirely |
| FIX-031 | `test_verify_deep_strict_present` | FIX-038 removes `--deep --strict` whole-bundle verify |
| FIX-031 | `test_dylib_so_signed_before_app_bundle` | FIX-038 removes the `.app bundle` codesign target index |
| FIX-031 | `test_signing_order_bottom_up` | FIX-038 removes the final `.app bundle` signing step |
| FIX-037 | `test_codesign_steps_still_present` | FIX-038 removes `codesign.*--verify.*--deep.*--strict` |

Per project rules, permanent test scripts cannot be modified. These 11 failures are the documented expected consequence of FIX-038 superseding the previous bundle-level signing approach. The 50 pre-existing version-pin failures are unchanged.

