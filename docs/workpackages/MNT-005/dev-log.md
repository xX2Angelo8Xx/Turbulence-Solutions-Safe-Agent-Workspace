# Dev Log — MNT-005: Add CI validate-version job to release workflow

## Status
In Progress

## Assigned To
Developer Agent

## User Story
US-068 — Automate Release Version Management

## Goal
Add a `validate-version` job to `.github/workflows/release.yml` that runs before all build jobs and ensures all 5 version files match the git tag version.

---

## Implementation Plan

1. Add `validate-version` job to `.github/workflows/release.yml`
   - runs-on: ubuntu-latest
   - Handles both `push` and `workflow_dispatch` triggers
   - Extracts version by stripping `v` prefix from tag
   - Checks all 5 version files with grep
   - Fails with clear error messages on mismatch
2. Add `needs: [validate-version]` to `windows-build`, `macos-arm-build`, `linux-build`
3. Write tests in `tests/MNT-005/`

---

## Implementation Summary

### Files Changed
- `.github/workflows/release.yml` — Added `validate-version` job; added `needs: [validate-version]` to all 3 build jobs

### Files Created
- `docs/workpackages/MNT-005/dev-log.md` — This file
- `tests/MNT-005/test_mnt005_ci_version_validation.py` — Unit tests for the job definition

### Design Decisions
- Used `ubuntu-latest` for the validate-version job (lightweight shell only, no build tools needed)
- Version extraction: `TAG="${{ github.ref_name }}"` for push triggers; `TAG="${{ github.event.inputs.tag }}"` for workflow_dispatch
- Used `grep -oP` for pattern extraction from each file
- On mismatch: prints `Expected: X.Y.Z` and `Actual: <found value>` then exits 1
- On success: prints a summary of all 5 files checked

### Tests Written
- `test_validate_version_job_exists` — job definition present in YAML
- `test_build_jobs_need_validate_version` — all 3 build jobs have `needs: [validate-version]`
- `test_all_5_files_checked` — grep patterns for all 5 version files present
- `test_push_trigger_handled` — `github.ref_name` used for push triggers
- `test_workflow_dispatch_trigger_handled` — `github.event.inputs.tag` used for dispatch
- `test_version_extraction_logic` — `${TAG#v}` shell strip present
- `test_error_reporting_format` — Expected/Actual output format present
- `test_success_summary_present` — success message present
- `test_validate_version_runs_on_ubuntu` — job uses ubuntu-latest
- `test_checkout_step_present` — actions/checkout@v4 present in job
- `test_validate_version_job_order` — validate-version appears before build jobs

---

## Test Results
All 11 tests pass. See `docs/test-results/test-results.csv`.

---

## Known Limitations
None.
