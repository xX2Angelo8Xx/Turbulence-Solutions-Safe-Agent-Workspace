# Test Report — FIX-029

**Tester:** Tester Agent  
**Date:** 2026-03-17  
**Iteration:** 2  

---

## Summary

The Developer correctly fixed the Iteration 1 regression by updating
`tests/INS-015/test_ins015_macos_build_jobs.py::test_macos_arm_has_5_steps` to
assert 6 steps (the new "Verify Code Signing" step was added in FIX-029, making
the total 6). All 28 targeted tests pass. The full regression suite shows 3307
passed, 29 skipped, 1 xfailed, and 7 pre-existing failures (unchanged from the
Developer's pre-review run). Zero new failures attributable to FIX-029.

**Verdict: PASS**

---

## Code Review

### `.github/workflows/release.yml`

| Check | Result |
|-------|--------|
| "Verify Code Signing" step present in `macos-arm-build` | PASS |
| Step positioned immediately after "Build DMG" (index 3 → 4) | PASS |
| Step positioned before "Upload macOS ARM DMG" (index 4 → 5) | PASS |
| Command: `codesign --verify --deep --strict dist/AgentEnvironmentLauncher.app && echo "Code signing verification passed"` | PASS |
| Step has no `continue-on-error: true` | PASS |
| Step has no `if:` condition that could skip it | PASS |
| Step has no shell override | PASS |
| Only one "Verify Code Signing" step in entire workflow | PASS |
| Other jobs (`windows-build`, `linux-build`, `release`) unchanged | PASS |
| Workflow trigger (`push: tags: v*.*.*`) unchanged | PASS |
| YAML file valid | PASS |

### `tests/INS-015/test_ins015_macos_build_jobs.py`

| Check | Result |
|-------|--------|
| `test_macos_arm_has_5_steps` assertion updated from `5` to `6` | PASS |
| Docstring updated to reflect new expected count | PASS |
| Test still correctly identifies the step list when count is wrong | PASS |

Note: The test *function name* (`test_macos_arm_has_5_steps`) is technically
stale since it now checks for 6 steps, but renaming is cosmetic and out of scope
for this fix.

---

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| `tests/INS-015/test_ins015_macos_build_jobs.py::test_macos_arm_has_5_steps` | Regression | PASS | Now asserts 6 steps; was failing in Iter 1 |
| FIX-029 suite — 27 tests (17 dev + 10 Tester edge-cases) | Unit | PASS | All 27 pass unchanged |
| Full regression suite — 3307 tests | Regression | PASS | 7 pre-existing failures; 0 new |

### Pre-existing Failures (unchanged, not caused by FIX-029)

| Test | Root Cause | Tracking |
|------|-----------|---------|
| `tests/FIX-009/*` (6 tests) | UnicodeDecodeError in test-results.csv (byte 0x97) | Pre-existing encoding corruption |
| `tests/INS-005/test_ins005_edge_cases.py::TestShortcutsAndUninstaller::test_uninstall_delete_type_is_filesandirs` | `filesandordirs` vs `filesandirs` typo in Inno Setup | BUG-045 |

---

## Bugs Found

None attributable to FIX-029.

---

## TODOs for Developer

None — WP approved.

---

## Verdict

**PASS** — FIX-029 is marked Done. The "Verify Code Signing" step is correctly
placed, the command is correct, all safeguards (no continue-on-error, no if:
skip, no shell override) are in place, and the INS-015 regression introduced in
the original implementation has been resolved.

---

## Iteration History

| Iteration | Date | Verdict | Key Finding |
|-----------|------|---------|-------------|
| 1 | 2026-03-17 | FAIL | `test_macos_arm_has_5_steps` expected 5 steps, now 6 after FIX-029 added "Verify Code Signing" |
| 2 | 2026-03-17 | PASS | Assertion updated to 6; 0 new failures; all checks pass |


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
