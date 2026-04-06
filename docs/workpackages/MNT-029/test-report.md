# Test Report — MNT-029

**Tester:** Tester Agent  
**Date:** 2026-04-06  
**Iteration:** 1

## Summary

**FAIL.** MNT-029 introduced 1 new regression by incorrectly removing a still-failing test from `tests/regression-baseline.json`. Additionally, `docs/workpackages/MNT-029/dev-log.md` is missing. The WP is returned to the Developer.

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

## Verdict

**FAIL — return to Developer.**

See TODOs above. Do not advance to Done until all items are resolved.
