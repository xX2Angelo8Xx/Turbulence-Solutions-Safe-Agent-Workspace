# Dev Log — INS-013: CI Workflow Skeleton

**WP ID:** INS-013  
**Category:** Installer  
**Status:** In Progress  
**Assigned To:** Developer Agent  
**Branch:** ins/INS-013-ci-workflow-skeleton  
**Date:** 2026-03-14  

---

## Objective

Create `.github/workflows/release.yml` — a valid GitHub Actions workflow file that:
- Triggers on `push` to tags matching `v*.*.*`
- Defines 4 empty build job stubs: `windows-build`, `macos-intel-build`, `macos-arm-build`, `linux-build`
- Defines 1 release job stub with `needs` dependency on all 4 build jobs
- Each job has correct `runs-on` and a single `actions/checkout@v4` step
- YAML is syntactically valid

This is the skeleton only. Actual build steps will be added in INS-014–INS-017.

---

## Implementation

### Files Created
- `.github/workflows/release.yml` — GitHub Actions CI workflow skeleton

### Design Decisions
- Used `actions/checkout@v4` as minimal step placeholder in each job, per the assignment specification
- `macos-intel-build` targets `macos-13` (Intel runner); `macos-arm-build` targets `macos-14` (Apple Silicon runner)
- Release job declares `needs: [windows-build, macos-intel-build, macos-arm-build, linux-build]` to ensure all builds complete before release

### Notes
- The `.github/` directory is normally in the NoAgentZone but this WP explicitly permits writing to `.github/workflows/`

---

## Tests Written

Test file: `tests/INS-013/test_ins013_ci_workflow.py`

| Test | Description |
|------|-------------|
| `test_workflow_file_exists` | Verifies `.github/workflows/release.yml` exists |
| `test_workflow_yaml_valid` | YAML can be parsed without errors |
| `test_trigger_push_tags` | `on.push.tags` contains `v*.*.*` pattern |
| `test_all_5_jobs_defined` | All 5 expected job keys are present |
| `test_windows_build_runs_on` | `windows-build` uses `windows-latest` |
| `test_macos_intel_runs_on` | `macos-intel-build` uses `macos-13` |
| `test_macos_arm_runs_on` | `macos-arm-build` uses `macos-14` |
| `test_linux_build_runs_on` | `linux-build` uses `ubuntu-latest` |
| `test_release_runs_on` | `release` uses `ubuntu-latest` |
| `test_release_needs_all_builds` | `release.needs` contains all 4 build jobs |
| `test_each_job_has_steps` | Every job has at least one step |
| `test_workflow_name` | Top-level `name` is "Build and Release" |

---

## Test Results

All 12 tests pass. Full suite run post-implementation — no regressions.

---

## Implementation Summary

Single YAML file created. YAML syntax verified via PyYAML. All acceptance criteria met on first implementation pass.
