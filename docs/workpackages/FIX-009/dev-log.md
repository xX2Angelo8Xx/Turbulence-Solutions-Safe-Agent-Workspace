# Dev Log — FIX-009: TST-ID Deduplication

## Workpackage Info
- **WP ID:** FIX-009
- **Type:** Fix
- **Status:** Review
- **Assigned To:** Developer Agent
- **Date:** 2026-03-14

---

## Summary

Resolved all ~100 duplicate TST-IDs in `docs/test-results/test-results.csv` (BUG-035, a recurrence of BUG-009). Also added retroactive FIX-006 and FIX-007 test result entries that were missing from the CSV.

---

## Analysis

| Metric | Value |
|--------|-------|
| Original row count | 912 |
| Unique IDs before fix | 770 |
| Duplicate ID groups | 102 |
| Extra rows (duplicates) | 142 |
| Max TST-ID before fix | TST-785 |

### Duplicate Ranges Found
- TST-261 – TST-301 (41 IDs, some appearing 3× due to multiple prior sessions)
- TST-481 – TST-511 (31 IDs)
- TST-522 – TST-544 (23 IDs)
- TST-578 – TST-582 (5 IDs)
- TST-718 (1 ID)
- TST-782 (1 ID)

---

## Implementation

### Step 1 — Deduplication

Script: `docs/workpackages/FIX-009/tmp_deduplicate.py`

Algorithm:
1. Read all 912 rows from CSV.
2. Walk rows in order; track seen IDs in a set.
3. First occurrence of each ID → kept unchanged.
4. All subsequent occurrences → renumbered starting at TST-786 (max+1).
5. 142 duplicate rows renumbered to TST-786 – TST-927.

### Step 2 — Add FIX-006 / FIX-007 Entries

Missing test entries retroactively added:

**FIX-006** (6 tests from `test_fix006_conftest_safety.py`):
- TST-928: test_open_in_vscode_source_binding_is_blocked
- TST-929: test_open_in_vscode_app_binding_is_blocked
- TST-930: test_subprocess_popen_is_real
- TST-931: test_check_for_update_app_binding_is_blocked
- TST-932: test_check_for_update_source_is_real
- TST-933: test_safety_chain_open_in_vscode_cannot_reach_popen

**FIX-007** (7 tests from `test_fix007_mock_pattern.py`):
- TST-934: test_file_does_not_use_del_sys_modules_loop
- TST-935: test_file_uses_shared_ctk_mock
- TST-936: test_app_py_has_no_bom
- TST-937: test_app_py_is_valid_python
- TST-938: test_check_for_update_returns_tuple
- TST-939: test_window_height_assertion_matches_app
- TST-940: test_app_window_height_is_520

### Step 3 — FIX-009 Self-Test Entries

3 FIX-009 test results appended:
- TST-941: test_no_duplicate_tst_ids
- TST-942: test_tst_id_format
- TST-943: test_required_fields_not_empty

### Final State

| Metric | Value |
|--------|-------|
| Final row count | 928 |
| Unique IDs | 928 |
| Duplicate IDs remaining | 0 |
| New max TST-ID | TST-943 |

---

## Files Changed

| File | Change |
|------|--------|
| `docs/test-results/test-results.csv` | 142 IDs renumbered; 13 FIX-006/FIX-007 entries added; 3 FIX-009 entries added |
| `docs/workpackages/workpackages.csv` | FIX-009 status → Review |
| `docs/bugs/bugs.csv` | BUG-035 status → Closed; Fixed In WP → FIX-009 |

## Tests Written

| File | Test | Result |
|------|------|--------|
| `tests/FIX-009/test_fix009_no_duplicate_tst_ids.py` | test_no_duplicate_tst_ids | PASS |
| `tests/FIX-009/test_fix009_tst_id_format.py` | test_tst_id_format | PASS |
| `tests/FIX-009/test_fix009_required_fields.py` | test_required_fields_not_empty | PASS |

All 3 tests passed on 2026-03-14, Windows 11 + Python 3.11.

---

## Verification

Post-fix scan: `len(set(ids)) == len(ids)` → **TRUE** (928 == 928)

---

## Known Limitations

Root cause (no TST-ID assignment protocol in `testing-protocol.md`) is NOT addressed by this WP — that is a separate concern. This WP only deduplicates existing IDs.

---

## Bug Closure

- BUG-035: status → `Closed`, Fixed In WP → `FIX-009`
