# Test Report — FIX-096

**Tester:** Tester Agent
**Date:** 2026-04-04
**Iteration:** 1

## Summary

FIX-096 corrects a silent-pass defect in two CI workflow files. Both `test.yml`
and `staging-test.yml` previously called `sys.exit(0)` (with a WARNING / SKIP
message) when `MANIFEST.json` was absent, allowing CI to pass as if nothing was
wrong. The fix changes both exits to `sys.exit(1)` with a clear `ERROR:` message
directing developers to run `scripts/generate_manifest.py`.

The implementation is minimal, targeted, and correct. All 6 developer-written
tests pass. No regressions were detected. No security concerns apply.

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| test_test_yml_does_not_exit_0_on_missing_manifest | Unit | PASS | Confirms `sys.exit(0)` absent in missing-manifest path of test.yml |
| test_test_yml_exits_1_on_missing_manifest | Unit | PASS | Confirms `sys.exit(1)` present in missing-manifest path of test.yml |
| test_test_yml_has_error_message_on_missing_manifest | Unit | PASS | Confirms `ERROR:` + `generate_manifest.py` message present in test.yml |
| test_staging_yml_does_not_exit_0_on_missing_manifest | Unit | PASS | Confirms `sys.exit(0)` absent in missing-manifest path of staging-test.yml |
| test_staging_yml_exits_1_on_missing_manifest | Unit | PASS | Confirms `sys.exit(1)` present in missing-manifest path of staging-test.yml |
| test_staging_yml_has_error_message_on_missing_manifest | Unit | PASS | Confirms `ERROR:` + `generate_manifest.py` message present in staging-test.yml |

Logged as TST-2492 via `scripts/run_tests.py`.

## Additional Checks

- **Workflow content verified manually:** Both `test.yml` (line ~113) and
  `staging-test.yml` (line ~69) were read directly. The `if not manifest_path.exists():`
  branch in each file now prints `ERROR: MANIFEST.json not found — run
  scripts/generate_manifest.py` and calls `sys.exit(1)`. No residual
  `sys.exit(0)` appears in either missing-manifest branch.
- **ADR compliance:** ADR-002 (mandatory CI gate) and ADR-003 (template manifest
  system) both mandate that a missing MANIFEST.json must fail CI. The fix is
  fully compliant.
- **Regression baseline:** No FIX-096 entry existed in
  `tests/regression-baseline.json` — no baseline update required.
- **Workspace validation:** `scripts/validate_workspace.py --wp FIX-096` returned
  exit code 0 with "All checks passed."
- **Edge cases considered:**
  - Only the missing-manifest branch is affected; the normal (file-present) path
    is untouched in both workflows.
  - The error message is actionable — it tells developers exactly which script to run.
  - Both workflow files use identical messaging, ensuring consistent CI output.
  - No race conditions or platform-specific quirks are possible for a static file
    existence check executed inside a CI runner.

## Bugs Found

None.

## TODOs for Developer

None.

## Verdict

PASS — mark WP as Done.
