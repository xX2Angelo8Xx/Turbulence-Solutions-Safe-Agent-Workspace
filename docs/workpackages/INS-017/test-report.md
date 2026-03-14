# INS-017 Test Report — CI Release Upload Job

**Tester:** Tester Agent  
**Date:** 2026-03-14  
**Branch:** `ins/INS-017-ci-release-upload`  
**Verdict:** ✅ PASS

---

## Summary

All acceptance criteria for INS-017 are met. The `release` job in `.github/workflows/release.yml` has been verified against every review focus item listed in the assignment, plus 11 additional edge-case tests added by the Tester.

| Metric | Value |
|---|---|
| Developer tests | 21 |
| Tester edge-case tests | 11 |
| **Total INS-017 tests** | **32** |
| Full suite (final run) | **1819 passed, 2 skipped, 0 failed** |
| Regressions introduced | **0** |

---

## Code Review Findings

### ✅ permissions: contents: write
Set at job level on the `release` job. Required for `softprops/action-gh-release` to create a GitHub Release. NOT set globally (least-privilege). Verified by `test_release_job_permissions_contents_write`.

### ✅ download-artifact@v4 with no `name` key
`actions/download-artifact@v4` is used with only `path: release-assets`. The absence of the `name` key causes all 4 artifacts to be downloaded into `release-assets/<artifact-name>/` subdirectories. Verified by `test_download_artifact_has_no_name_key`.

### ✅ softprops/action-gh-release@v2 (not v1)
`@v2` is used. `@v1` would be deprecated. Verified by `test_gh_release_uses_v2` and Tester `test_release_job_gh_release_action_not_v1`.

### ✅ files glob captures all platform artifacts
`release-assets/**/*` correctly picks up all files nested under any artifact subdirectory. Verified by `test_gh_release_files_glob`.

### ✅ generate_release_notes: true
Auto-generates release notes from commits since the last tag. Verified by `test_gh_release_generate_release_notes_true`.

### ✅ needs lists exactly all 4 build jobs
`needs: [windows-build, macos-intel-build, macos-arm-build, linux-build]` — exactly 4 entries, both as a set and as a count. Verified by `test_release_needs_all_four_build_jobs` and Tester `test_release_needs_exactly_four_jobs`.

### ✅ No GITHUB_TOKEN leak
- No step in the release job has `env: {GITHUB_TOKEN: ...}`
- No workflow-level `env:` block exposes GITHUB_TOKEN
- No job-level `env:` block on the release job
- No hardcoded PAT pattern (`ghp_*` or `github_pat_*`) in any step
- The action gets the automatic token solely through `permissions: contents: write`

### ✅ No shell: overrides
No step in the release job declares a `shell:` key. Verified by `test_release_job_no_shell_override`.

### ✅ All action versions pinned
Every action in the release job uses a specific major version tag:
- `actions/checkout@v4`
- `actions/download-artifact@v4`
- `softprops/action-gh-release@v2`
No `@main`, `@master`, `@latest`, or `@HEAD` tags anywhere. Verified by Tester `test_release_job_no_floating_action_tags` and individual version tests.

---

## Edge-Case Tests Added (Tester)

File: `tests/INS-017/test_ins017_edge_cases.py`

| Test | Rationale |
|---|---|
| `test_release_steps_no_env_github_token` | Prevents accidental env-based token leak to steps |
| `test_release_needs_exactly_four_jobs` | Guards against partial dependency (3 jobs) or spurious extras |
| `test_download_path_no_conflict_with_artifact_names` | Ensures `release-assets` isn't already an upload-artifact name |
| `test_release_job_no_floating_action_tags` | Blocks `@main`/`@master`/`@latest` supply-chain risk |
| `test_release_job_no_shell_override` | No shell directive means the runner default applies; no unexpected shell injection vector |
| `test_release_job_checkout_action_version` | Pinned to `@v4` exactly |
| `test_release_job_download_action_version` | Pinned to `@v4` exactly |
| `test_release_job_gh_release_action_not_v1` | Deprecated `@v1` blocked |
| `test_workflow_level_env_no_github_token` | Workflow-level env won't silently leak token to all jobs |
| `test_release_job_no_job_level_env` | Job-level env block would be superfluous and a misuse |
| `test_release_job_no_setup_python` | Release job only needs checkout + download + publish; Python runtime is not required |

---

## Security Assessment

- **Supply-chain risk:** All actions pinned to major version tags (v2/v4/v5). No `@main` or floating tags. Risk: Low.
- **Token exposure:** Token never appears in workflow text. Automatic token provided via permissions mechanism only. Risk: None.
- **Artifact integrity:** No checksum verification on downloaded artifacts before upload to release. This is a known limitation — artifact integrity between upload-artifact and download-artifact@v4 within the same workflow run is guaranteed by GitHub Actions' internal mechanism.
- **Path traversal:** `release-assets/**/*` glob is safe within a GitHub Actions runner workspace; no repo path traversal possible.

---

## Test Run Log

| Run | Tests | Result |
|---|---|---|
| INS-017 developer suite | 21 | PASS |
| INS-017 full suite (pre-tester) | 1808 + 2 skip | PASS |
| INS-017 tester edge-case suite | 11 | PASS |
| INS-017 full suite (final regression) | 1819 + 2 skip | PASS |

---

## Verdict: ✅ PASS

All requirements verified. Zero regressions. Setting INS-017 to `Done`.
