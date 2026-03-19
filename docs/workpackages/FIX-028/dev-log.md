# Dev Log — FIX-028: Add ad-hoc code signing to macOS build script

## Workpackage Info
- **WP ID:** FIX-028
- **Branch:** fix/FIX-028-macos-codesign
- **Assigned To:** Developer Agent
- **Status:** Review
- **Date:** 2026-03-17

---

## Problem

`src/installer/macos/build_dmg.sh` produced an unsigned `.app` bundle. On macOS
14+ (especially Apple Silicon M3), Gatekeeper kills unsigned bundles at launch
with "Launchd job spawn failed" error 153 (BUG-061).

---

## Implementation

### Change: `src/installer/macos/build_dmg.sh`

Added **Step 3.5** (between the existing Step 3 Info.plist write and Step 4 DMG
creation):

```bash
# ---------------------------------------------------------------------------
# Step 3.5: Ad-hoc code signing
# ---------------------------------------------------------------------------
echo "Step 3.5: Code signing..."
codesign --deep --force --sign - "${APP_BUNDLE}"
echo "Verifying code signature..."
codesign --verify --deep --strict "${APP_BUNDLE}"
```

**Flags explained:**
- `--deep` — recursively signs all embedded binaries (Python.framework, python3.11,
  all dylibs).
- `--force` — overrides any previous signature so the step is idempotent.
- `--sign -` — ad-hoc signing (no Apple Developer ID required; removes Gatekeeper
  rejection on developer machines and CI).
- `--verify --deep --strict` — halts the build immediately if signing failed,
  preventing a bad DMG from being created or uploaded.

The signing step fires after the `.app` bundle is fully assembled (Contents/MacOS
populated + Info.plist written) and before hdiutil packages it into the DMG, which
is the correct and required sequence.

---

## Files Changed

| File | Change |
|------|--------|
| `src/installer/macos/build_dmg.sh` | Added Step 3.5 codesign + verify block |
| `docs/workpackages/FIX-028/dev-log.md` | Created (this file) |
| `tests/FIX-028/test_fix028_codesign.py` | Created (12 tests) |
| `docs/test-results/test-results.csv` | Logged TST-1654 and TST-1655 |
| `docs/workpackages/workpackages.csv` | Status set to Review |

---

## Tests Written

File: `tests/FIX-028/test_fix028_codesign.py` — 12 tests

| Test | Description |
|------|-------------|
| `test_script_exists` | build_dmg.sh exists |
| `test_codesign_invocation_present` | `codesign` command present |
| `test_deep_flag_present` | `--deep` flag on signing line |
| `test_adhoc_sign_flag_present` | `--sign -` ad-hoc identity |
| `test_force_flag_present` | `--force` flag present |
| `test_verification_step_present` | `codesign --verify` step present |
| `test_verify_uses_deep_strict` | Verify uses `--deep --strict` |
| `test_codesign_before_hdiutil` | Signing comes before DMG creation |
| `test_verify_before_hdiutil` | Verify comes before DMG creation |
| `test_no_crlf_line_endings` | LF-only line endings |
| `test_app_bundle_variable_used_in_codesign` | `APP_BUNDLE` variable used (no hard-coded path) |
| `test_step_35_label_present` | Step 3.5 label present in script |

---

## Test Results

- FIX-028 tests: **12/12 PASS**
- Full suite: **3168 passed / 2 pre-existing failures / 29 skipped / 1 xfailed**
- Pre-existing failures: FIX-009 (TST-1557 duplicate) + INS-005 (BUG-045)
- **Zero new regressions**

---

## Known Limitations

- Ad-hoc signing allows the app to run on the build machine but does NOT satisfy
  Apple Notarization or App Store requirements. A proper developer certificate
  would be needed for public distribution via Gatekeeper-unmodified paths.
- `codesign` is a macOS-only tool; the verification step in CI is covered by
  FIX-029 which adds a CI-level codesign verify step.
