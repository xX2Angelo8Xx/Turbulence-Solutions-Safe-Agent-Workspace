# Dev Log — FIX-099: Extend Validation for Review Status

## Overview
Extends `scripts/validate_workspace.py` so that WPs in **Review** status are subject to artifact checks alongside **Done** WPs. Previously `_check_wp_artifacts` returned immediately when `status != "Done"`, meaning a WP could reach Review without dev-log.md or tests and the validator would not catch it.

## ADR Check
No ADRs in `docs/decisions/index.csv` are relevant to this fix (ADR-001 through ADR-006 cover releases, CI gates, manifest/upgrade system, ADR lifecycle, rollback UI, and code signing).

## Implementation

### Change: `scripts/validate_workspace.py` — `_check_wp_artifacts`

- Changed early-return guard from `if status != "Done"` to `if status not in ("Done", "Review")`
- For **Review** status: dev-log.md and tests/<WP-ID>/ (≥1 test_*.py) are required → ERROR if missing
- For **Review** status: test-report.md is **not** checked (only Tester creates it)
- For **Done** status: all existing checks remain unchanged (dev-log.md, test-report.md unless excepted, tests/ unless excepted)
- Temporary-file check now also runs for Review WPs

The docstring was updated to describe the new dual-status behaviour.

## Files Changed
- `scripts/validate_workspace.py` — extended `_check_wp_artifacts`
- `tests/FIX-099/test_fix099_review_validation.py` — new unit tests

## Tests Written
- `test_review_wp_missing_devlog_raises_error` — Review WP with no dev-log.md → error reported
- `test_review_wp_missing_tests_dir_raises_error` — Review WP with no tests/ dir → error reported
- `test_review_wp_missing_test_py_raises_error` — Review WP with tests/ dir but no test_*.py → error reported
- `test_review_wp_missing_test_report_no_error` — Review WP without test-report.md → no error (optional at Review stage)
- `test_review_wp_all_artifacts_present_no_error` — Review WP with dev-log.md + test_*.py → no error
- `test_done_wp_still_requires_test_report` — Done WP without test-report.md still raises error (regression guard)

## Known Limitations
None.

## Status
Implemented and tested. Handing off to Tester.
