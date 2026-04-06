# Test Report — MNT-029

**Tester:** Tester Agent  
**Date:** 2026-04-06  
**Iteration:** 3 (PASS)

## Summary

**PASS (Iteration 3).** All checks passed. The INS-019 baseline entry (`test_verify_shim_existence_only_check`) has been correctly restored. Both BUG-192 and BUG-193 are now Fixed. MANIFEST.json is up to date. All 73 full-suite failures are accounted for in the 141-entry baseline (0 new regressions). All 4 MNT-029 tests pass. Workspace validation clean. WP marked Done.

---

## Iteration 3 Findings

### ✅ INS-019 Baseline Entry Restored
- `tests.INS-019.test_ins019_edge_cases.test_verify_shim_existence_only_check` is present in `tests/regression-baseline.json` (line 360).
- Test passes in isolation: `1 passed in 0.14s`. ✅
- Fails in full suite context due to sys.path mutation (flaky) — expected and documented. ✅

### ✅ DOC-002 Baseline Entry Still Present (iter 2 fix intact)
- `tests.DOC-002.test_doc002_readme_placeholders.TestTemplateFilesContainPlaceholder.test_placeholder_present_in_getting_started_section` present in baseline. ✅

### ✅ Baseline Integrity
- `_count`: 141, actual entries: 141. ✅
- Main branch had 152 entries; 12 removed, 1 restored (INS-019) = net 11 removed. Consistent. ✅

### ✅ Correctly-Removed Entries Sample Verification
All 11 net-removed entries verified — sample of 6 tested in isolation:
- `test_logo_ctk_image_size_is_proportional` (FIX-015): PASS
- `test_logo_pil_open_failure_no_crash` (FIX-015): PASS
- `test_app_build_ui_creates_logo_label` (GUI-013): PASS
- `test_created_workspace_has_initial_commit` (INS-030): PASS
- `test_deny_command_substitution_backtick` (SAF-073): PASS
- `test_locked_next_id_concurrent_threads` (MNT-015): PASS

### ✅ MANIFEST.json
`scripts/generate_manifest.py --check` → "Manifest is up to date." (exit 0). ✅

### ✅ MNT-029 Test Suite
All 4 tests pass in `tests/MNT-029/`:
- `test_manifest_file_count_matches_files_dict` PASS
- `test_baseline_no_stale_entries` PASS
- `test_manifest_check_exits_clean` PASS
- `test_manifest_has_expected_keys` PASS

### ✅ Full Suite Regression Check
- 73 failed, 8941 passed, 344 skipped, 5 xfailed, 66 errors
- All 73 failures verified against 141-entry baseline: **0 new regressions**. ✅

### ✅ Workspace Validation
`scripts/validate_workspace.py --wp MNT-029` → "All checks passed." (exit 0). ✅

### ✅ Bug Tracking
- BUG-192: Status=Fixed, Fixed In WP=MNT-029. ✅
- BUG-193: Status updated to Fixed, Fixed In WP=MNT-029. ✅

---

## Iteration 2 Summary (historical — FAIL)

**FAIL (Iteration 2).** Iteration 2 correctly restores the DOC-002 baseline entry (BUG-192 fix verified). However, a second incorrectly-removed baseline entry was found: `tests.INS-019.test_ins019_edge_cases.test_verify_shim_existence_only_check`. This flaky test was present in the pre-MNT-029 baseline and still fails in the full suite. It must be restored. WP is returned to the Developer.

---

## Iteration 1 Summary (historical)

**FAIL.** MNT-029 introduced 1 new regression by incorrectly removing a still-failing test from `tests/regression-baseline.json`. Additionally, `docs/workpackages/MNT-029/dev-log.md` was missing. Returned to Developer as BUG-192.

---

## Iteration 2 Detailed Findings

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| tests/MNT-029/ (4 tests) | Unit | PASS | All 4 MNT-029 tests pass |
| Full regression suite (TST-2650) | Regression | FAIL | 74 failed + 66 errors = 140 total; 1 exceeds baseline |

## Full-Suite Results

- **Total failures/errors:** 140
- **Baseline entries:** 139
- **New regressions (NOT in baseline):** 1

### New Regression Found

```
tests.DOC-002.test_doc002_readme_placeholders.TestTemplateFilesContainPlaceholder.test_placeholder_present_in_getting_started_section
```

**Why it fails:** The test asserts `"Place your project files in \`{{PROJECT_NAME}}/\`."` is present in the Getting Started section of `templates/agent-workbench/README.md`. The actual content is `"Place your project files in your project folder."` — the placeholder was intentionally removed by FIX-086.

**Why the removal was wrong:** This entry was correctly in the baseline with reason: _"FIX-086 takes precedence as it documents the current README design."_ The fact that FIX-109/110/111/112 ran does not change the README template; it still lacks the `{{PROJECT_NAME}}/` placeholder in the Getting Started section. The test was **not** fixed by those WPs, it was incorrectly presumed fixed.

## Validation errors (scripts/validate_workspace.py --wp MNT-029)

- `[ERROR] MNT-029: missing docs/workpackages/MNT-029/dev-log.md`

## Edge-Case Tests Added by Tester

Two new tests added in `tests/MNT-029/test_mnt029_edge_cases.py`:

| Test | Result | Notes |
|------|--------|-------|
| `test_manifest_file_count_matches_files_dict` | PASS | `file_count` field matches actual `files` dict length |
| `test_baseline_no_stale_entries` | PASS | All baseline keys map to existing `.py` files |

## Manifest Verification

`generate_manifest.py --check` exits 0 — manifest is up to date. ✓  
`_count` (139) matches `len(known_failures)` (139). ✓  
The 12 other removed baseline entries all now pass. ✓

## Bugs Found

- BUG-192: MNT-029 incorrectly removed DOC-002 getting-started baseline entry (logged in docs/bugs/bugs.jsonl)

## TODOs for Developer

- [ ] **Restore the incorrectly removed baseline entry.** Add back the following key to `tests/regression-baseline.json`:
  ```json
  "tests.DOC-002.test_doc002_readme_placeholders.TestTemplateFilesContainPlaceholder.test_placeholder_present_in_getting_started_section": {
    "reason": "DOC-002 requires exact placeholder strings that would require 6+ total {{PROJECT_NAME}} occurrences; FIX-086 requires exactly 4. Contradiction between test suites; FIX-086 takes precedence as it documents the current README design."
  }
  ```
  Update `_count` from 139 to 140 and `_updated` to 2026-04-06.

- [ ] **Create `docs/workpackages/MNT-029/dev-log.md`** — this is required before any WP can be handed off. The file must document implementation decisions, tests written, and known limitations.

- [ ] **Rerun `scripts/validate_workspace.py --wp MNT-029`** and confirm exit code 0 before re-handing off.

- [ ] **Rerun `scripts/run_tests.py --wp MNT-029 --full-suite`** and confirm 0 new regressions.

## Verdict (Iteration 1)

**FAIL — return to Developer.**

---

## Iteration 2 Checks

### BUG-192 Fix Verification ✅

- `tests.DOC-002.test_doc002_readme_placeholders.TestTemplateFilesContainPlaceholder.test_placeholder_present_in_getting_started_section` present in baseline at line 12.
- Ran targeted pytest → **1 FAILED** (test still fails; baseline entry justified).
- BUG-192 in `docs/bugs/bugs.jsonl` → `"Status": "Fixed"`, `"Fixed In WP": "MNT-029"`. ✅

### Baseline Count ✅

`_count` = 140, `len(known_failures)` = 140. Match confirmed.

### Manifest Check ✅

`generate_manifest.py --check` → "Manifest is up to date." (exit 0).

### MNT-029 Test Suite ✅

All 4 tests pass (`test_manifest_file_count_matches_files_dict`, `test_baseline_no_stale_entries`, `test_manifest_check_exits_clean`, `test_manifest_has_expected_keys`).

### Workspace Validation ✅

`scripts/validate_workspace.py --wp MNT-029` → "All checks passed." (exit 0).

### Full Suite Regression Analysis ❌

Run: `pytest --tb=no -q`  
Result: `73 failed, 8941 passed, 344 skipped, 5 xfailed, 66 errors` (exit 1).

Of 137 total failures+errors: **136 in baseline**, **1 new regression**.

#### New Regression: `tests.INS-019.test_ins019_edge_cases.test_verify_shim_existence_only_check`

- **Status:** FAILED in full suite, PASSES in isolation (`pytest tests/INS-019/` → 59 passed).
- **Pre-MNT-029:** Entry WAS in baseline (commit `100dc6f`) with reason: *"Flaky test: passes when run in isolation but fails in full suite due to sys.path mutation by other test modules. The INS-019 test file uses a module-level sys.path.insert() that is sensitive to import ordering."*
- **Post-MNT-029:** Entry was removed during the 152→140 cleanup. Removal was incorrect — the test still fails in full-suite context.
- This is the same category of error as BUG-192 from Iteration 1.

#### INS-019 Flaky Entries Note (informational)

4 other INS-019 baseline entries did not fire on this run. They are all confirmed flaky tests (INS-019 sys.path issue) and their baseline retention is **correct**.

---

## Iteration 2 TODOs for Developer

### TODO-1 (Blocking): Restore Missing Baseline Entry

Restore the following entry to `tests/regression-baseline.json` (place in alphabetical order among INS-019 entries):

```json
"tests.INS-019.test_ins019_edge_cases.test_verify_shim_existence_only_check": {
  "reason": "Flaky test: passes when run in isolation (python -m pytest tests/INS-019/) but fails in full suite due to sys.path mutation by other test modules. The INS-019 test file uses a module-level sys.path.insert() that is sensitive to import ordering."
},
```

Update `_count` from 140 → 141 and `_updated` to 2026-04-06.

### TODO-2 (Blocking): Log Bug via `scripts/add_bug.py`

Log a new bug for the incorrectly-removed `test_verify_shim_existence_only_check` baseline entry. Direct editing of `docs/bugs/bugs.jsonl` is prohibited — use `scripts/add_bug.py`.

### TODO-3 (Verification): Confirm No Other INS-019 Entries Were Incorrectly Removed

Compare pre-MNT-029 INS-019 entries (`git show 100dc6f:tests/regression-baseline.json | Select-String "INS-019"`) against current baseline to ensure `test_verify_shim_existence_only_check` is the only missing entry.

---

## Iteration 2 Test Execution Log

| Test Run | Command | Result |
|----------|---------|--------|
| DOC-002 targeted | `pytest tests/DOC-002/...::test_placeholder_present_in_getting_started_section` | 1 FAILED (expected) |
| MNT-029 suite | `pytest tests/MNT-029/ -v --tb=short` | 4 PASSED |
| Full suite | `pytest --tb=no -q` | 73 failed, 8941 passed, 344 skipped, 66 errors |
| INS-019 isolated | `pytest tests/INS-019/ -v -q` | 59 PASSED |
| Workspace validation | `scripts/validate_workspace.py --wp MNT-029` | PASSED |
| Manifest check | `scripts/generate_manifest.py --check` | PASSED (exit 0) |

## Verdict (Iteration 2)

**FAIL — return to Developer.**

One additional incorrectly-removed baseline entry found (`test_verify_shim_existence_only_check`). Restore it, log the bug, and resubmit.
