# Test Report — FIX-115: Drop settings.json from Integrity Hash Check (Iteration 2)

**Tester:** Tester Agent  
**Date:** 2026-04-06  
**Branch:** FIX-115/drop-settings-hash  
**Verdict:** ❌ FAIL — 3 new regressions (4 test cases) not addressed by Developer

---

## Summary

**Iteration 2 context:** The 4 regressions from Iteration 1 (FIX-079, DOC-053, FIX-114,
MNT-029) are now all fixed. However, the full test suite reveals **3 additional test files**
with **4 failing tests** introduced by FIX-115 and not caught in Iteration 1. These are not
in `tests/regression-baseline.json` and represent genuine new regressions.

FIX-115's core implementation is correct: `_KNOWN_GOOD_SETTINGS_HASH` was removed from
`security_gate.py`, `verify_file_integrity()` only checks the gate hash, and `update_hashes.py`
no longer embeds a settings hash. All 10 dedicated FIX-115 tests pass. All 10 `security_gate.py`
golden-file snapshot tests pass. FIX-079, DOC-053, FIX-114, and MNT-029 suites all pass.

However, the Developer missed updating **3 additional test files** that reference the removed
`_KNOWN_GOOD_SETTINGS_HASH` constant or the ADR index state prior to ADR-011.

---

## Code Review Findings

### Correct
- `_KNOWN_GOOD_SETTINGS_HASH` constant removed from `security_gate.py` (only a comment remains).
- `verify_file_integrity()` checks only `_KNOWN_GOOD_GATE_HASH`; no settings.json reference.
- `_INTEGRITY_WARNING` message updated to reference only `security_gate.py`.
- `update_hashes.py`: `_SETTINGS_HASH_RE` removed, `_resolve_paths()` returns single `Path`,
  `update_hashes()` only re-embeds gate hash, docstring updated with ADR-011 reference.
- ADR-011 created in `docs/decisions/ADR-011.md` and indexed in `docs/decisions/index.jsonl`.
- BUG-194 `Fixed In WP` field set to `FIX-115` in `bugs.jsonl`.
- 10 dedicated regression tests in `tests/FIX-115/` covering all key behaviors.

### Missed by Developer
- 4 existing tests in other WP test suites now fail due to FIX-115 changes — see below.

---

## Test Results

### Full Test Suite (`tests/`)

Run: `.venv\Scripts\python.exe -m pytest tests/ -v --tb=short`  
Result: **8952 passed, 75 failed, 344 skipped, 5 xfailed, 66 errors** in 149.58s

All 75 FAIL and 66 ERROR results are accounted for by `tests/regression-baseline.json`
**except for 4 tests in 3 files listed in the next section** — those are new regressions.

### Snapshot Tests (`tests/snapshots/`)

All 10 golden-file snapshot tests for `security_gate.py` PASS. No decision flip.

### Iteration-1 Regression Targets (46 tests in 4 suites)

| Suite | Result |
|-------|--------|
| `tests/FIX-079/` (22 tests) | ✅ ALL PASS |
| `tests/DOC-053/` (16 tests) | ✅ ALL PASS |
| `tests/FIX-114/` (3 tests)  | ✅ ALL PASS |
| `tests/MNT-029/` (4 tests)  | ✅ ALL PASS |

All 4 Iteration-1 regressions are confirmed fixed.

---

## New Regressions Introduced by FIX-115 (Iteration 2 Findings)

These 4 tests were **passing on `main`** before FIX-115 and are **not in the regression baseline**.
They are caused by `_KNOWN_GOOD_SETTINGS_HASH` removal and ADR-011 addition.

---

### REGRESSION 1 — `tests/SAF-009/test_saf009_cross_platform.py::test_af5_integrity_constants_not_zeroed`

**Error:**
```
AttributeError: module 'security_gate' has no attribute '_KNOWN_GOOD_SETTINGS_HASH'
```

**Root cause:** SAF-009 test verifies that `sg._KNOWN_GOOD_SETTINGS_HASH` is a valid non-zeroed
64-char hex string. FIX-115 removed this attribute. The Developer updated `tests/SAF-008`,
`tests/SAF-071`, and `tests/SAF-075` for this change but **missed `tests/SAF-009`**.

**Required fix:** In `tests/SAF-009/test_saf009_cross_platform.py`, update
`test_af5_integrity_constants_not_zeroed` to:
- Remove the `sg._KNOWN_GOOD_SETTINGS_HASH` assertion.
- Instead assert that `_KNOWN_GOOD_SETTINGS_HASH` is **absent** from the module, AND
  that `_KNOWN_GOOD_GATE_HASH` is a valid non-zeroed 64-char hex string.

---

### REGRESSIONS 2 & 3 — `tests/SAF-022/test_saf022_noagentzone_exclude.py`

**Failing tests:**
- `TestHashIntegrity::test_default_gate_settings_hash_matches`
- `TestHashIntegrity::test_template_gate_settings_hash_matches`

**Error:**
```
AssertionError: _KNOWN_GOOD_SETTINGS_HASH not found in
  .../templates/agent-workbench/.github/hooks/scripts/security_gate.py
assert None
```

**Root cause:** SAF-022's `TestHashIntegrity` class defines a helper `_extract_settings_hash()`
that regex-searches `security_gate.py` for the `_KNOWN_GOOD_SETTINGS_HASH` constant. FIX-115
removed that constant. The Developer updated `tests/FIX-042/test_fix042_noagentzone_visible.py`
(a similar test for FIX-042) but **missed `tests/SAF-022/test_saf022_noagentzone_exclude.py`**.

**Required fix:** In `tests/SAF-022/test_saf022_noagentzone_exclude.py`, update the two
`TestHashIntegrity` tests:
- Remove or rename `_extract_settings_hash()` helper.
- Replace `test_default_gate_settings_hash_matches` with a test asserting that
  `_KNOWN_GOOD_SETTINGS_HASH` is **absent** from the default gate, and `_KNOWN_GOOD_GATE_HASH`
  is present and non-zeroed.
- Apply the same replacement to `test_template_gate_settings_hash_matches`.

---

### REGRESSION 4 — `tests/MNT-028/test_mnt028_adr010_tester.py::test_adr010_is_last_entry_in_index`

**Error:**
```
AssertionError: Expected ADR-010 to be the last entry, but last entry is 'ADR-011'
assert 'ADR-011' == 'ADR-010'
```

**Root cause:** When MNT-028 was implemented, ADR-010 was the last entry in
`docs/decisions/index.jsonl` and the test verified this as a "just added" check. FIX-115 added
ADR-011 to the index, so ADR-010 is no longer the last entry.

**Required fix:** Update `tests/MNT-028/test_mnt028_adr010_tester.py::test_adr010_is_last_entry_in_index`:
- Change the assertion from "ADR-010 is last" to "ADR-010 exists in the index and is
  immediately followed by ADR-011" (preserving the original intent without breaking when
  further ADRs are added later).

Example replacement logic:
```python
# Find ADR-010 position and confirm it exists
ids = [row["ID"] for row in rows]
assert "ADR-010" in ids, "ADR-010 not found in ADR index"
idx = ids.index("ADR-010")
assert idx == len(ids) - 2, (
    f"Expected ADR-010 to be second-to-last (before ADR-011), "
    f"but it is at position {idx} of {len(ids)-1}"
)
assert ids[idx + 1] == "ADR-011", (
    f"Expected ADR-011 to follow ADR-010, but found '{ids[idx+1]}'"
)
```

---

## Security Assessment

The core change is security-positive: removing a brittle hash check that caused false positives
(blocking all tool calls) without any security benefit (settings.json contains only cosmetic VS
Code settings, not enforced by the gate). The gate self-hash check is intact. No decision flips
detected (all 10 snapshot tests pass). No attack surface was widened.

---

## TODOs for Developer (Iteration 3)

The following must be done before re-submitting for review. **Source code (`src/`) is NOT
involved** — only test files need updating:

1. **`tests/SAF-009/test_saf009_cross_platform.py`** — Update `test_af5_integrity_constants_not_zeroed`:
   remove `sg._KNOWN_GOOD_SETTINGS_HASH` assertion; replace with absent-check + gate-hash valid check
   (see REGRESSION 1 above).

2. **`tests/SAF-022/test_saf022_noagentzone_exclude.py`** — Update `TestHashIntegrity` class:
   replace both `test_*_gate_settings_hash_matches` tests with absent-check + gate-hash valid tests
   for both the default and template gate paths (see REGRESSIONS 2 & 3 above).

3. **`tests/MNT-028/test_mnt028_adr010_tester.py`** — Update `test_adr010_is_last_entry_in_index`:
   change assertion to verify ADR-010 is second-to-last (immediately before ADR-011)
   (see REGRESSION 4 above).

4. **Re-run full suite** after fixes: `pytest tests/ --tb=short -q | tail -5` — must show no
   new failures beyond the known baseline (`_count: 141`).

5. **Re-run `scripts/validate_workspace.py --wp FIX-115`** — must return exit code 0.

6. **Commit** as `FIX-115: fix 3 tester regressions (Iteration 2)` and push.

---

## Pre-Done Checklist

- [x] `dev-log.md` exists and is non-empty
- [x] `test-report.md` written — this document (Iteration 2, FAIL)
- [x] Test files exist in `tests/FIX-115/` (10 tests)
- [ ] Test results logged — pending (will log after this report)
- [ ] No new regressions — **3 files / 4 tests FAIL**
- [ ] Full suite passes (excluding baseline) — **FAIL**
- [ ] WP status set to Done — **NOT DONE** (returning to In Progress)
