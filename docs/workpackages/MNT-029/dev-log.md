# Dev Log — MNT-029: Regenerate Manifest & Update Regression Baseline

**Developer:** Developer Agent  
**Branch:** `MNT-029/regenerate-manifest-update-baseline`  
**Status:** Review (Iteration 3)

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

---

## Iteration 3 — Restore INS-019 Incorrectly Removed Baseline Entry

### Summary

Performed a thorough cross-check between the pre-MNT-029 baseline (from `main` branch) and the current baseline to find ALL entries that were removed. The old baseline had 152 entries; the current had 140. Exactly 12 entries were removed. Each was tested both in isolation and in the full suite:

- 11 of the 12 removed entries genuinely pass in both isolation AND the full suite — correctly removed
- 1 entry (`tests.INS-019.test_ins019_edge_cases.test_verify_shim_existence_only_check`) passes in isolation but **fails in the full suite** — incorrectly removed

### Entries Restored

| Key | Reason |
|-----|--------|
| `tests.INS-019.test_ins019_edge_cases.test_verify_shim_existence_only_check` | Flaky test: passes when run in isolation but fails in full suite due to sys.path mutation by other test modules. |

### Bug Reference

- **BUG-193** — `test_verify_shim_existence_only_check` was incorrectly removed from the regression baseline in MNT-029 iteration 2. The test fails in the full suite due to sys.path mutation by other test modules (same class of error as BUG-192/DOC-002 in iteration 2).

### Changes

- `tests/regression-baseline.json` — restored 1 entry:
  - Key: `tests.INS-019.test_ins019_edge_cases.test_verify_shim_existence_only_check`
  - `_count` updated from 140 → 141

### Cross-Check Methodology

1. Exported `main:tests/regression-baseline.json` to compare against current
2. Identified all 12 removed keys
3. Ran each removed test in isolation — all 12 passed
4. Ran full test suite — identified 1 of the 12 still fails in the full suite
5. Confirmed `test_verify_shim_existence_only_check` is the only incorrectly removed entry

### Relevant ADRs

No ADRs found specifically for regression baseline management.

### Outcome

Full regression suite confirms: 70 failures, 69 in baseline + 1 restored INS-019 entry. No new regressions. `_count` is 141 matching actual 141 entries.
