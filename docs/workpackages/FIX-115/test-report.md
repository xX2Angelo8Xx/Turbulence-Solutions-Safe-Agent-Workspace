# Test Report — FIX-115: Drop settings.json from Integrity Hash Check

**Tester:** Tester Agent  
**Date:** 2026-04-06  
**Branch:** FIX-115/drop-settings-hash  
**Verdict:** ❌ FAIL — 4 new regressions not addressed by Developer

---

## Summary

FIX-115's core implementation is correct and well-tested. The `_KNOWN_GOOD_SETTINGS_HASH`
constant has been removed, `verify_file_integrity()` now only checks the gate hash, and
`update_hashes.py` no longer embeds a settings hash. All 10 dedicated FIX-115 tests pass,
and all directly updated suites (SAF-008, SAF-025, SAF-011, SAF-075, SAF-071, FIX-042)
pass cleanly (100/100).

However, the full suite reveals **4 new regressions** caused by FIX-115 that the Developer
did not address. These tests passed on `main` before FIX-115 was applied and now fail.

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

### Targeted Suite (FIX-115 + all explicitly updated suites)

| Suite | Tests | Result |
|-------|-------|--------|
| tests/FIX-115/ | 10 | ✅ PASS |
| tests/SAF-008/ | 24 | ✅ PASS |
| tests/SAF-025/ | 13 | ✅ PASS |
| tests/SAF-011/ | 29 | ✅ PASS |
| tests/SAF-075/ | 8 | ✅ PASS |
| tests/SAF-071/ | 11 | ✅ PASS |
| tests/FIX-042/ | 8 | ✅ PASS |
| **Total** | **100** | **✅ PASS** |

*Logged as TST-2664.*

### Full Suite (tests/)

**Result:** 8,946 passed / 81 failed / 344 skipped — but critically, **4 failures are new regressions**
not present in the regression baseline (`tests/regression-baseline.json`) and not present on `main`
before FIX-115 was applied. Verified by temporarily checking out `main` — all 4 tests passed.

*Logged as TST-2663.*

---

## New Regressions (must be fixed by Developer)

### REGRESSION 1 — `tests/FIX-079/test_fix079_noagentzone_visible.py::test_security_gate_settings_hash_valid`

**Error:**
```
AssertionError: _KNOWN_GOOD_SETTINGS_HASH not found in
  templates/agent-workbench/.github/hooks/scripts/security_gate.py
```

**Root cause:** FIX-115 removed `_KNOWN_GOOD_SETTINGS_HASH`. The FIX-079 test
`test_security_gate_settings_hash_valid` calls `_extract_hash("_KNOWN_GOOD_SETTINGS_HASH")`
which internally asserts the constant exists. The constant is gone, so the assertion fails.

**Required fix:** In `tests/FIX-079/test_fix079_noagentzone_visible.py`, remove or replace
`test_security_gate_settings_hash_valid`. Since the constant no longer exists by design,
the test should be replaced with one that asserts `_KNOWN_GOOD_SETTINGS_HASH` is **absent**
(consistent with SAF-071's updated `test_settings_hash_absent_from_security_gate`).
Example replacement:

```python
def test_security_gate_settings_hash_absent():
    """FIX-115: _KNOWN_GOOD_SETTINGS_HASH must NOT exist in security_gate.py (ADR-011)."""
    content = GATE.read_text(encoding="utf-8")
    pattern = r'_KNOWN_GOOD_SETTINGS_HASH: str = "[0-9a-fA-F]{64}"'
    assert re.search(pattern, content) is None, (
        "_KNOWN_GOOD_SETTINGS_HASH is still defined in security_gate.py — "
        "FIX-115 should have removed it (ADR-011)."
    )
```

---

### REGRESSION 2 — `tests/DOC-053/test_doc053_adr_related_wps.py::test_adr_index_has_ten_entries`

**Error:**
```
AssertionError: Expected 10 ADR entries, found 11:
  ['ADR-001', ..., 'ADR-010', 'ADR-011']
```

**Root cause:** FIX-115 added ADR-011 to `docs/decisions/index.jsonl`, making the total count 11.
The DOC-053 test hardcodes `== 10`.

**Required fix:** In `tests/DOC-053/test_doc053_adr_related_wps.py`, update:
```python
# Before (line ~60):
assert len(rows) == 10, (
    f"Expected 10 ADR entries, found {len(rows)}: "
    ...
)

# After:
assert len(rows) == 11, (
    f"Expected 11 ADR entries, found {len(rows)}: "
    ...
)
```
Also update the docstring from `ADR-001 through ADR-010` to `ADR-001 through ADR-011`.

---

### REGRESSION 3 & 4 — Manifest out-of-date (FIX-114 and MNT-029)

**Failing tests:**
- `tests/FIX-114/test_fix114_ci_regressions.py::test_manifest_check_passes`
- `tests/MNT-029/test_mnt029_manifest.py::test_manifest_check_exits_clean`

**Error:**
```
AssertionError: Manifest check failed:
  Manifest is OUT OF DATE:
    CHANGED:   .github/hooks/scripts/security_gate.py
    CHANGED:   .github/hooks/scripts/update_hashes.py
  2 discrepancy(ies). Run without --check to regenerate.
```

**Root cause:** FIX-115 modified both `security_gate.py` and `update_hashes.py`, but did not
regenerate `MANIFEST.json`. The manifest is stale.

**Required fix:** Run `scripts/generate_manifest.py` (without `--check`) to regenerate the manifest
and commit the updated `MANIFEST.json`:
```powershell
.venv\Scripts\python scripts/generate_manifest.py
git add templates/agent-workbench/MANIFEST.json
```

---

## Security Assessment

The core change is security-positive: removing a brittle hash check that was causing false
positives (blocking all tool calls) without any security benefit (settings.json only contains
cosmetic VS Code settings, not enforced by the gate). The gate self-hash check is intact.
No security regressions detected.

---

## TODOs for Developer (Iteration 2)

The following must be done before re-submitting for review:

1. **Update `tests/FIX-079/test_fix079_noagentzone_visible.py`**: Replace
   `test_security_gate_settings_hash_valid` with a test that asserts the constant is absent
   (see REGRESSION 1 above).

2. **Update `tests/DOC-053/test_doc053_adr_related_wps.py`**: Change `== 10` to `== 11`
   in `test_adr_index_has_ten_entries` (see REGRESSION 2 above).

3. **Regenerate manifest**: Run `python scripts/generate_manifest.py` and commit the updated
   `templates/agent-workbench/MANIFEST.json` (see REGRESSIONS 3 & 4 above).

4. **Re-run full suite**: Confirm `tests/ --tb=short -q` shows no new failures beyond the
   regression baseline (`_count: 141`).

5. **Re-run `scripts/validate_workspace.py --wp FIX-115`** — must return exit code 0.

---

## Pre-Done Checklist

- [x] `dev-log.md` exists and is non-empty  
- [ ] `test-report.md` written — **this document** (FAIL)  
- [x] Test files exist in `tests/FIX-115/` (10 tests)  
- [x] Test results logged (TST-2663, TST-2664)  
- [ ] No new regressions — **4 NEW regressions found**  
- [ ] Full suite passes (excluding baseline) — **FAIL**  
