# Test Report — INS-016

**Tester:** Tester Agent
**Date:** 2026-03-14
**Iteration:** 1

## Summary

INS-016 adds the `linux-build` job to `.github/workflows/release.yml`. The implementation installs
libfuse2, builds with PyInstaller, produces an AppImage via `build_appimage.sh x86_64`, and uploads
the artifact as `linux-appimage`. All 35 tests pass and 1794/1794 suite tests pass with zero regressions.

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| INS-016 developer suite (28 tests, TST-779) | Unit | PASS | Logged by Developer Agent |
| INS-016 tester edge-case suite (7 tests, TST-781) | Unit | PASS | Added by Tester Agent |
| Full regression suite 1794 tests (TST-782) | Regression | PASS | 2 skipped, 0 failures |

### Tester Edge-Case Tests Added

| Test | What it verifies |
|------|-----------------|
| `test_linux_build_no_shell_overrides` | No `shell:` key on any linux-build step |
| `test_linux_build_no_secrets_in_run_commands` | No `${{ secrets.*}}` in any run field |
| `test_linux_build_appimage_step_not_using_sudo` | `build_appimage.sh` is NOT prefixed with sudo |
| `test_linux_build_artifact_name_distinct_from_other_platforms` | `linux-appimage` name is unique across all jobs |
| `test_linux_build_checkout_is_first_step` | checkout@v4 is the first step |
| `test_linux_build_libfuse2_uses_apt_get_not_bare_apt` | Non-interactive `apt-get` used, not bare `apt` |
| `test_linux_build_appimage_script_exists_in_repo` | `src/installer/linux/build_appimage.sh` exists on disk |

## Code Review Findings

All five review focus points verified:

1. **libfuse2 installed before AppImage build** ✅ — `Install libfuse2` step precedes both `Build with PyInstaller` and `Build AppImage`; ordering tested.
2. **build_appimage.sh path and architecture arg correct** ✅ — `src/installer/linux/build_appimage.sh x86_64` tested by exact-match assertions.
3. **chmod +x before execution** ✅ — `chmod +x src/installer/linux/build_appimage.sh` appears before the invocation line in the multi-line run block; position tested.
4. **Artifact path matches script output** ✅ — `dist/*.AppImage` glob matches `dist/TurbulenceSolutionsLauncher-x86_64.AppImage`; tested by exact equality.
5. **No shell=True, no secrets, no unnecessary sudo** ✅ — No `shell:` overrides detected; no `${{ secrets.*}}` in run commands; sudo limited to `apt-get` steps only.

## Bugs Found

None.

## TODOs for Developer

None.

## Verdict

**PASS — mark WP as Done.**
