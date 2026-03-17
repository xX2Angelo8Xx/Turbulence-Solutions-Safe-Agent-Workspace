# Test Report — FIX-029

**Tester:** Tester Agent  
**Date:** 2026-03-17  
**Iteration:** 1  

---

## Summary

The implementation is correct and all 27 FIX-029 tests (17 developer + 10 Tester
edge-case additions) pass. However, the new "Verify Code Signing" step increases
the `macos-arm-build` job step count from 5 to 6, breaking one existing test in
`tests/INS-015/` that hard-codes the expected step count as `5`. This is a
regression caused by FIX-029 and must be fixed before the WP can be approved.

**Verdict: FAIL** — return to Developer. See TODO below.

---

## Code Review

### `.github/workflows/release.yml`

| Check | Result |
|-------|--------|
| "Verify Code Signing" step present in `macos-arm-build` | PASS |
| Step positioned immediately after "Build DMG" | PASS |
| Step positioned before "Upload macOS ARM DMG" | PASS |
| Command: `codesign --verify --deep --strict dist/AgentEnvironmentLauncher.app && echo "Code signing verification passed"` | PASS |
| Step has no `continue-on-error: true` | PASS |
| Step has no `if:` condition that could skip it | PASS |
| Step has no shell override | PASS |
| Only one "Verify Code Signing" step in entire workflow | PASS |
| Other jobs (`windows-build`, `linux-build`, `release`) unchanged | PASS |
| Workflow trigger (`push: tags: v*.*.*`) unchanged | PASS |
| YAML file remains valid | PASS |

The implementation fully satisfies the FIX-029 acceptance criteria.

---

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| FIX-029 developer suite (17 tests) | Unit | PASS | All 17 pass |
| Tester edge-case additions (10 tests) | Unit | PASS | All 10 pass; see classes `TestVerifyStepSafeguards` and `TestWorkflowTriggerIntegrity` |
| INS-015 full suite | Regression | **FAIL** | `test_macos_arm_has_5_steps` fails — expects 5 steps, now 6 |
| INS-005 edge cases | Regression | FAIL (pre-existing) | BUG-045 `filesandordirs` vs `filesandirs` — pre-dates FIX-029, not a regression |
| FIX-009 test-results.csv suite | Regression | FAIL (pre-existing) | UnicodeDecodeError on 0x97 bytes in CSV — pre-dates FIX-029, not a regression |
| Full suite (excluding FIX-009) | Regression | **FAIL** | 2 failures: INS-015 (new) + INS-005 (pre-existing BUG-045) |

### Full suite result: 3306 passed, 2 failed, 29 skipped, 1 xfailed
- INS-015 `test_macos_arm_has_5_steps` — **NEW failure caused by FIX-029**
- INS-005 `test_uninstall_delete_type_is_filesandirs` — pre-existing BUG-045

---

## Edge-Case Tests Added (by Tester)

Added to `tests/FIX-029/test_fix029_ci_codesign_verify.py`:

**Class `TestOtherJobsUnchanged` — 1 addition:**
- `test_release_job_has_no_codesign_step` — verifies the "Verify Code Signing" step was not accidentally added to the `release` job

**Class `TestVerifyStepSafeguards` — 6 additions:**
- `test_step_has_no_continue_on_error` — ensures the step cannot silently swallow a failing codesign
- `test_step_has_no_if_condition` — ensures the step cannot be conditionally skipped
- `test_step_has_no_shell_override` — ensures no custom shell override that could bypass codesign
- `test_only_one_codesign_verify_step_in_entire_workflow` — guards against pasting the step into the wrong job
- `test_step_run_contains_strict_flag` — verifies `--strict` flag (required for macOS 14+ Gatekeeper)
- `test_step_run_contains_deep_flag` — verifies `--deep` flag (required to check nested components)

**Class `TestWorkflowTriggerIntegrity` — 3 additions:**
- `test_workflow_triggers_on_push` — confirms the `on: push:` trigger was not removed
- `test_push_trigger_uses_version_tags` — confirms `v*.*.*` tag pattern is intact
- `test_no_pull_request_trigger` — confirms no `pull_request` / `pull_request_target` trigger (security risk)

**Note:** YAML's `on:` key is parsed as Python `True` by `yaml.safe_load`. Tests that access the trigger block use `workflow[True]` accordingly.

---

## Bugs Found

- **BUG-062**: `tests/INS-015/test_macos_arm_has_5_steps` hard-codes expected step count as 5 — stale after FIX-029 adds "Verify Code Signing" step (logged in `docs/bugs/bugs.csv`)

---

## TODOs for Developer

- [ ] Update `tests/INS-015/test_ins015_macos_build_jobs.py` line 98-101:
  - Change docstring from `"macos-arm-build must have exactly 5 steps."` to `"macos-arm-build must have exactly 6 steps."`
  - Change `assert len(arm_steps) == 5` to `assert len(arm_steps) == 6`
  - Change the error message string from `"Expected 5 steps, got ..."` to `"Expected 6 steps, got ..."`
- [ ] Re-run the full test suite and confirm zero new failures before resubmitting for Review.

---

## Verdict

**FAIL** — WP set back to `In Progress`. Resolve BUG-062 (update INS-015 step
count test) and resubmit for Tester review.
