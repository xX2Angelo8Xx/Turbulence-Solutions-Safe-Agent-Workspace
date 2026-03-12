# Test Report — INS-006

**Tester:** Tester Agent
**Date:** 2026-03-12
**Iteration:** 1

## Summary

`src/installer/macos/build_dmg.sh` fully satisfies the WP acceptance criteria. The
script has the correct shebang, error-handling flags, dual-architecture support,
proper `.app` bundle structure, complete `Info.plist` with all required CFBundle keys,
`hdiutil` DMG creation, and no hardcoded absolute paths or credentials.  
All 32 developer tests pass. 31 additional Tester edge-case tests were added and all
pass (63 total). No regressions in the full suite (1001 pass / 16 pre-existing failures).

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| TestFileExists (2 tests) | Unit | PASS | File present and non-empty |
| TestShebangAndSafety (2 tests) | Unit | PASS | `#!/usr/bin/env bash` + `set -euo pipefail` |
| TestHdiutil (4 tests) | Unit | PASS | `hdiutil create`, `UDZO`, `-volname` all present |
| TestAppMetadata (3 tests) | Unit | PASS | App name, version (0.1.0), publisher verified |
| TestArchitectureSupport (3 tests) | Unit | PASS | `x86_64`, `arm64`, `--target-arch` all present |
| TestNoHardcodedPaths (3 tests) | Security | PASS | No `/Users/`, `/home/`, or absolute `dist/` |
| TestAppBundleStructure (3 tests) | Unit | PASS | `Contents/MacOS`, `Contents/Resources`, `Info.plist` |
| TestInfoPlistKeys (10 parametrized) | Unit | PASS | All 10 CFBundle/NS keys present |
| TestPyInstallerIntegration (2 tests) | Unit | PASS | `launcher.spec` and `dist/launcher` referenced |
| **Tester: TestLineEndings (2 tests)** | Unit | PASS | No CRLF or bare CR — safe for macOS bash |
| **Tester: TestEncoding (2 tests)** | Unit | PASS | No UTF-8 BOM; file ends with newline |
| **Tester: TestVersionConsistency (1 test)** | Unit | PASS | `APP_VERSION=0.1.0` matches `pyproject.toml` |
| **Tester: TestPlistXMLStructure (5 tests)** | Unit | PASS | XML declaration, DOCTYPE, `<plist>`, `</plist>`, `<dict>` all present |
| **Tester: TestBundleIdentifier (2 tests)** | Unit | PASS | `APP_ID` is `com.turbulencesolutions.agentlauncher` (reverse-domain); `${APP_ID}` used in plist |
| **Tester: TestTempDirHygiene (3 tests)** | Unit | PASS | `mktemp`, `rm -rf ${STAGING_DIR}` cleanup present |
| **Tester: TestHdiutilFlags (3 tests)** | Unit | PASS | `-ov`, `-srcfolder`, `-o ${DIST_DIR}/...` all correct |
| **Tester: TestNoCredentials (9 tests)** | Security | PASS | No password/token/secret/API key keywords |
| **Tester: TestDmgFilename (3 tests)** | Unit | PASS | `${APP_VERSION}` and `${TARGET_ARCH}` in filename; `.dmg` extension |
| **Tester: TestArchFallback (1 test)** | Unit | PASS | `uname -m` fallback for host-arch detection |
| Full suite regression (1001 + 1 skipped) | Regression | PASS | 16 pre-existing failures unchanged; 0 new failures |

## Bugs Found

None. No bugs were discovered during this review.

## Administrative Note

The developer logged INS-006 test results in `test-results.csv` using TST IDs TST-521
to TST-544. However, those IDs were already assigned to SAF-009 tests. This is the
same class of duplicate-ID issue as BUG-009 (resolved during maintenance 2026-03-11).
This is a documentation-only administrative defect and does not affect the correctness
of the INS-006 implementation. Tester edge-case tests are logged starting from TST-572.

## TODOs for Developer

None — all acceptance criteria are met.

## Verdict

**PASS** — Set INS-006 to `Done`.
