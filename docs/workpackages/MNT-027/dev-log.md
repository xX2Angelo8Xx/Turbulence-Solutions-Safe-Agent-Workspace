# Dev Log — MNT-027: Narrow CI to Windows-only

## Assignment
- **Agent:** Developer Agent
- **Date:** 2026-04-05
- **Status:** In Progress

## ADR Check
- ADR-010 (Windows-only CI) does not exist yet — it will be created by MNT-028. The comment `# Disabled per ADR-010` is added anticipating that ADR.
- ADR-002 (CI test gate) is related; this WP narrows the OS scope but keeps the regression gate intact.

## Scope Summary
Narrowing CI to Windows-only by modifying four workflow files and two docs files. Source code is preserved cross-platform. No code deleted.

## Changes Made

### `.github/workflows/test.yml`
- Changed `matrix.os` from `[windows-latest, ubuntu-latest, macos-latest]` to `[windows-latest]`.
- Changed `manifest-check` job from `runs-on: ubuntu-latest` to `runs-on: windows-latest`.
- Changed `parity-check` job from `runs-on: ubuntu-latest` to `runs-on: windows-latest`.

### `.github/workflows/macos-source-test.yml`
- Added `if: false` to the `macos-source-install` job with comment referencing ADR-010.

### `.github/workflows/staging-test.yml`
- Removed `smoke-test-ubuntu` job.
- Removed `smoke-test-macos` job.
- Updated `staging-summary` job `needs` to only reference `[smoke-test-windows]`.

### `.github/workflows/release.yml`
- Changed `run-tests` matrix from `[windows-latest, ubuntu-latest, macos-latest]` to `[windows-latest]`.
- Removed `macos-arm-build` job.
- Removed `linux-build` job.
- Updated `release` job `needs` to only reference `[windows-build]`.

### `docs/project-scope.md`
- Added "Platform Support Status" section with table (Windows=Active, macOS/Linux=Deferred).

### `docs/architecture.md`
- Added CI/CD note in the Development Setup section referencing Windows-only CI and ADR-010.

## Tests Written
- `tests/MNT-027/test_ci_windows_only.py`
  - `test_test_yml_matrix_windows_only` — verifies test.yml has only windows-latest in OS list
  - `test_macos_workflow_has_if_false` — verifies macos-source-test.yml has if: false on job
  - `test_staging_windows_only` — verifies staging-test.yml has no ubuntu/macos jobs
  - `test_release_no_macos_linux_build_jobs` — verifies release.yml has no macos-arm-build or linux-build
  - `test_project_scope_has_platform_table` — verifies project-scope.md has Platform Support Status table

## Known Limitations
- ADR-010 is referenced in comments but the file doesn't exist until MNT-028 is implemented.
