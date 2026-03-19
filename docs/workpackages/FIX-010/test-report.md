# Test Report — FIX-010: Fix CI/CD Release Pipeline Failures

**WP ID:** FIX-010  
**Branch:** fix/FIX-010-cicd-release-pipeline  
**Date:** 2026-03-14  
**Tester:** Tester Agent  
**Verdict:** PASS

---

## Summary

All code changes are correct, secure, and complete. The three bugs (BUG-036, BUG-037, BUG-038) are properly fixed and all acceptance criteria are met. The full test suite passes with zero regressions. 17 additional edge-case tests were added covering areas the Developer did not test.

**Full suite result:** 1863 passed, 2 skipped, 0 failed

---

## Phase 1 — Code Review

### `.github/workflows/release.yml`

| Criterion | Result |
|-----------|--------|
| `macos-intel-build` runner updated to `macos-15` | PASS |
| `macos-intel-build` setup-python has `architecture: x64` | PASS |
| Standalone `Build with PyInstaller` removed from macos-intel, macos-arm, linux | PASS |
| `windows-build` retains its `Build with PyInstaller` step | PASS |
| `release` job `needs` all 4 build jobs | PASS |
| No hardcoded secrets or tokens | PASS |
| Workflow triggers only on version tags (no branch triggers) | PASS |
| No duplicate step names within any job | PASS |

### `src/installer/windows/setup.iss`

| Criterion | Result |
|-----------|--------|
| Source path uses `..\..\..` prefix (3 levels up from `src/installer/windows/`) | PASS |
| Resolved path lands at repo root (filesystem walk verified) | PASS |
| Version updated to `1.0.0` | PASS |

### `src/installer/macos/build_dmg.sh`

| Criterion | Result |
|-----------|--------|
| `APP_VERSION` updated to `1.0.0` | PASS |

### `src/installer/linux/build_appimage.sh`

| Criterion | Result |
|-----------|--------|
| `APP_VERSION` updated to `1.0.0` | PASS |

### Version Consistency (all 5 sources)

| Source | Version |
|--------|---------|
| `pyproject.toml` | 1.0.0 |
| `src/launcher/config.py` VERSION | 1.0.0 |
| `src/installer/windows/setup.iss` MyAppVersion | 1.0.0 |
| `src/installer/macos/build_dmg.sh` APP_VERSION | 1.0.0 |
| `src/installer/linux/build_appimage.sh` APP_VERSION | 1.0.0 |

All five sources agree. ✓

### Security Review

- No hardcoded credentials, tokens, or API keys found anywhere in the modified files.
- No `shell: true` or equivalent in the workflow YAML.
- All external actions use pinned major versions (`@v4`, `@v5`, `@v2`).
- Workflow `permissions: contents: write` is scoped only to the `release` job (minimum required for GitHub Release creation).
- No SSRF vectors: no user-controlled URLs in the workflow.

---

## Phase 2 — Test Execution

### Run 1: Developer tests only
**Command:** `.venv\Scripts\python -m pytest tests/FIX-010/test_fix010_cicd_pipeline.py -v`  
**Result:** 21 passed, 0 failed

### Run 2: FIX-010 directory (all tests including Tester edge-cases)
**Command:** `.venv\Scripts\python -m pytest tests/FIX-010/ -v`  
**Result:** 38 passed, 0 failed

### Run 3: Full suite
**Command:** `.venv\Scripts\python -m pytest tests/ -q`  
**Result:** 1863 passed, 2 skipped, 0 failed

No regressions introduced by the FIX-010 changes.

---

## Phase 3 — Edge-Case Analysis

### Areas Developer covered
- BUG-036: Runner updated, architecture specified, PyInstaller step removed from macOS/Linux, retained in Windows
- BUG-037: Source path has correct `..` depth, not bare `dist\`
- BUG-038: All three build scripts and pyproject.toml version matches

### Additional edge cases identified and tested (tests/FIX-010/test_fix010_edge_cases.py)

| # | Test | Rationale |
|---|------|-----------|
| 1 | `test_release_job_needs_all_four_build_jobs` | If a build job is not in `needs`, the release runs without waiting for that artifact — an incomplete release |
| 2 | `test_release_job_needs_exact_four` | Guard against spurious extra dependencies being added inadvertently |
| 3 | `test_release_job_needs_no_typos` | A typo in a job name in `needs` fails silently with a misleading error |
| 4 | `test_workflow_no_hardcoded_api_tokens` | Security: PAT prefixes (ghp_, github_pat_, ghs_) must never appear in committed YAML |
| 5 | `test_workflow_no_hardcoded_passwords` | Security: `password:` key must not have literal values |
| 6 | `test_no_job_has_duplicate_step_names` | Duplicate step names confuse the Actions UI and can mask silent bugs |
| 7 | `test_config_py_version_matches_pyproject` | 5th version source: runtime VERSION constant shown in the GUI would display stale data |
| 8 | `test_all_five_version_sources_match` | All 5 sources must agree simultaneously — mismatch breaks the update flow |
| 9 | `test_pyproject_version_is_valid_semver` | Version must be parseable as MAJOR.MINOR.PATCH for the GitHub Release API |
| 10 | `test_setup_iss_version_is_valid_semver` | Inno Setup requires x.y.z format for display and registry entries |
| 11 | `test_macos_intel_build_has_both_macos15_runner_and_x64_arch` | Either condition alone is insufficient — both must be true simultaneously |
| 12 | `test_macos_arm_does_not_have_x64_architecture` | Prevents a silent architecture mismatch: ARM runner with forced x64 Python |
| 13 | `test_setup_iss_source_path_resolves_to_repo_root_on_filesystem` | Walks the actual filesystem path to confirm `..\..\..` lands at repo root |
| 14 | `test_windows_artifact_upload_path_contains_exe` | Upload path must reference `.exe` — wrong path = missing artifact in GitHub Release |
| 15 | `test_macos_intel_artifact_upload_path_is_dmg` | Upload path must reference `.dmg` |
| 16 | `test_linux_artifact_upload_path_is_appimage` | Upload path must reference `.AppImage` |
| 17 | `test_workflow_triggers_only_on_version_tags` | Release workflow must not fire on branch pushes — only version tags |

All 17 edge-case tests pass.

---

## Bugs Found

None. All three addressed bugs (BUG-036, BUG-037, BUG-038) are correctly resolved.

Minor documentation inconsistency noted (non-blocking, does not affect functionality):  
The dev-log states "24 tests" and "TST-947 to TST-970" but the test file contains 21 tests and the CSV has entries TST-947 to TST-967 (21 entries). The over-count by 3 is a documentation error only — all actual tests pass.

---

## Pre-Done Checklist

- [x] `docs/workpackages/FIX-010/dev-log.md` exists and is non-empty
- [x] `docs/workpackages/FIX-010/test-report.md` written by Tester
- [x] Test files exist in `tests/FIX-010/` (test_fix010_cicd_pipeline.py + test_fix010_edge_cases.py)
- [x] All test runs logged in `docs/test-results/test-results.csv` (TST-968 to TST-984)
- [x] `git add -A` staged
- [x] Commit: `FIX-010: Tester PASS`
- [x] Push: `git push origin fix/FIX-010-cicd-release-pipeline`

---

## Verdict: PASS

All acceptance criteria met. No security issues. No regressions. Full suite passes.  
WP FIX-010 status: **Done**
