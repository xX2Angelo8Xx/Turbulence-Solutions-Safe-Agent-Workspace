# Dev Log — MNT-029: Regenerate Manifest & Update Regression Baseline

**Developer:** Developer Agent  
**Branch:** `MNT-029/regenerate-manifest-update-baseline`  
**Status:** Review (Iteration 2)

---

## Iteration 1 — Manifest Regeneration + Baseline Cleanup

### Summary

Regenerated `templates/agent-workbench/MANIFEST.json` via `scripts/generate_manifest.py` to reflect the current template file set. Also cleaned the regression baseline from 152 entries down to 139 by removing entries for tests that no longer exist or whose bugs were resolved.

### Changes

- `templates/agent-workbench/MANIFEST.json` — regenerated with updated file list and `file_count`
- `tests/regression-baseline.json` — reduced from 152 to 139 entries; `_count` updated to match

### Tests Written

- `tests/MNT-029/test_mnt029_manifest.py` — validates manifest integrity
- `tests/MNT-029/test_mnt029_baseline.py` — validates baseline count consistency

### Outcome

FAIL (Tester Iteration 1): 1 new regression introduced by incorrectly removing a still-failing test entry. Dev-log was also missing.

---

## Iteration 2 — Restore Incorrectly Removed Baseline Entry

### Summary

Restored the baseline entry for `test_placeholder_present_in_getting_started_section` that was incorrectly removed during iteration 1. This test still fails because the `README.md` template lacks `{{PROJECT_NAME}}/` in the Getting Started section (removed by FIX-086). The contradiction between DOC-002 and FIX-086 was an existing known failure; removing it from baseline was incorrect.

### Bug Reference

- **BUG-192** — Baseline entry for `test_placeholder_present_in_getting_started_section` was incorrectly removed in MNT-029 iteration 1. The test still fails; FIX-086 takes precedence over DOC-002 as documented in the baseline reason.

### Changes

- `tests/regression-baseline.json` — restored 1 entry:
  - Key: `tests.DOC-002.test_doc002_readme_placeholders.TestTemplateFilesContainPlaceholder.test_placeholder_present_in_getting_started_section`
  - Placed alphabetically after `test_placeholder_present_in_folder_table_row`
  - `_count` updated from 139 → 140

### Relevant ADRs

No ADRs found specifically for regression baseline management.

### Root Cause

Iteration 1 removed all DOC-002 baseline entries that appeared to be superseded by FIX-086/FIX-109-112; however `test_placeholder_present_in_getting_started_section` was never fixed — the README template still lacks that placeholder. Only entries whose underlying bugs were actually resolved should be removed.

### Outcome

All 4 MNT-029 tests expected to pass. Full regression suite should show no new failures beyond the 140 known baseline entries.
