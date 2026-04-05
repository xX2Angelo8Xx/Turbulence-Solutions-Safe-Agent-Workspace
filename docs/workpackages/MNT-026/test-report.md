# Test Report — MNT-026: Create ADR-009 cross-WP test impact

**Tester:** Tester Agent  
**Date:** 2026-04-05  
**Verdict:** FAIL — 2 new regressions caused by this WP

---

## Review Summary

The ADR-009 document and index.jsonl entry are well-structured and accurate. The 4 developer-written tests are correct and pass. However, adding ADR-009 to `docs/decisions/index.jsonl` and `docs/decisions/ADR-009-cross-wp-test-impact.md` broke two pre-existing tests in other WP folders that were not updated in the same commit.

---

## Test Runs

| Run | Scope | Result | Logged As |
|-----|-------|--------|-----------|
| MNT-026 suite (11 tests) | `tests/MNT-026/` | PASS | — |
| Full regression suite | `tests/` (all) | FAIL — 66 failures, 2 new regressions | TST-2622 |

**New regressions (not in `tests/regression-baseline.json`):**
1. `tests/DOC-053/test_doc053_adr_related_wps.py::test_adr_index_has_seven_entries`
2. `tests/DOC-017/test_doc017_tester_edge_cases.py::test_broad_docs_tree_no_stale_coding`

All other 64 failures are pre-existing entries in `tests/regression-baseline.json`.

---

## Regression Details

### Regression 1 — DOC-053: ADR index entry count mismatch

**File:** `tests/DOC-053/test_doc053_adr_related_wps.py`  
**Test:** `test_adr_index_has_seven_entries`  
**Failure:**
```
AssertionError: Expected 8 ADR entries, found 9:
['ADR-001', 'ADR-002', 'ADR-003', 'ADR-004', 'ADR-005', 'ADR-006', 'ADR-007', 'ADR-008', 'ADR-009']
assert 9 == 8
```
**Root cause:** The DOC-053 test hardcodes the expected ADR count as 8. MNT-026 added ADR-009, making the count 9. The test was not updated.

### Regression 2 — DOC-017: Stale `templates/coding/` reference in ADR-009

**File:** `tests/DOC-017/test_doc017_tester_edge_cases.py`  
**Test:** `test_broad_docs_tree_no_stale_coding`  
**Failure:**
```
AssertionError: Found 'templates/coding/' in:
  docs\decisions\ADR-009-cross-wp-test-impact.md
```
**Root cause:** ADR-009 contains `templates/coding/` in its historical table of codebase drift waves (the Context section). The DOC-017 test flags any non-exempted `.md` file in `docs/` that contains this string. ADR-009 was not added to the `STALE_CODING_EXEMPT` set.

---

## Edge-Case Tests Added by Tester

7 additional tests added to `tests/MNT-026/test_adr_009.py`:

| Test | Purpose |
|------|---------|
| `test_adr_009_status_header_is_active` | Verifies `**Status:** Active` appears in the header block, not just the body |
| `test_adr_009_references_adr008` | Verifies ADR-009 references ADR-008 (the rule it enforces) |
| `test_adr_009_index_entry_has_all_required_fields` | All 6 mandatory JSONL fields present |
| `test_adr_009_superseded_by_is_empty` | `Superseded By` is `""` (ADR is active) |
| `test_adr_009_index_entry_is_valid_json` | All lines in index.jsonl parse cleanly |
| `test_adr_009_hook_script_mentioned` | `check_test_impact.py` appears in the ADR |
| `test_adr_009_exit_code_0_documented` | ADR states the hook exits with code 0 |

All 11 MNT-026 tests pass.

---

## Security / ADR Conflict Review

- No security concerns (purely documentation WP).
- No ADR conflicts found in `docs/decisions/index.jsonl`.
- ADR-008 is correctly acknowledged (ADR-009 extends it without superseding it).

---

## TODOs for Developer (required before re-handoff)

### TODO 1 — Update DOC-053 test to expect 9 ADR entries

**File:** `tests/DOC-053/test_doc053_adr_related_wps.py`  
**Change:** In `test_adr_index_has_seven_entries`, update the assertion from `== 8` to `== 9` and update the docstring/message to reflect the current count.

```python
# Before
assert len(rows) == 8, (
    f"Expected 8 ADR entries, found {len(rows)}: "
    + str([r.get("ADR-ID") for r in rows])
)

# After
assert len(rows) == 9, (
    f"Expected 9 ADR entries, found {len(rows)}: "
    + str([r.get("ADR-ID") for r in rows])
)
```

Also rename the function from `test_adr_index_has_seven_entries` to `test_adr_index_has_nine_entries` (or remove the count from the name to avoid future drift, e.g. `test_adr_index_minimum_entries`).

### TODO 2 — Exempt ADR-009 from DOC-017's stale-path check

**File:** `tests/DOC-017/test_doc017_tester_edge_cases.py`  
**Change:** Add `decisions/ADR-009-cross-wp-test-impact.md` to the `STALE_CODING_EXEMPT` set.

The ADR-009 file legitimately contains `templates/coding/` in a historical reference table documenting a past rename event. It is not a stale reference — it is accurate history. Adding it to the exemption list is the correct fix.

Locate the `STALE_CODING_EXEMPT` set in that test file and add the entry:
```python
STALE_CODING_EXEMPT = {
    ...,
    "decisions/ADR-009-cross-wp-test-impact.md",
}
```

### TODO 3 — Verify clean full-suite run after fixes

After making both changes above:
1. Run `python -m pytest tests/DOC-053/ tests/DOC-017/ tests/MNT-026/ -v` — all must pass.
2. Run the full suite: `python -m pytest tests/ -q` — confirm only the 66 known-baseline failures remain (no new failures).
3. Run `scripts/validate_workspace.py --wp MNT-026` — must exit 0.
4. Stage, commit, and push.

---

## Pre-Done Checklist Status

- [x] `docs/workpackages/MNT-026/dev-log.md` exists and non-empty
- [x] `docs/workpackages/MNT-026/test-report.md` written
- [x] Test files exist in `tests/MNT-026/` (11 tests)
- [x] Test results logged via `scripts/run_tests.py` (TST-2622)
- [x] `scripts/validate_workspace.py --wp MNT-026` returns exit code 0
- [ ] **BLOCKED: 2 new regressions in DOC-053 and DOC-017** — WP returned to In Progress
