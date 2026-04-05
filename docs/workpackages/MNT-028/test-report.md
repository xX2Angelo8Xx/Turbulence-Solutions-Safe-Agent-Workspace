# Test Report — MNT-028: Create ADR-010 Windows-only CI

**Tester:** Tester Agent  
**Date:** 2026-04-05  
**Verdict:** PASS  

---

## Summary

MNT-028 delivers ADR-010 documenting the Windows-only CI decision made in MNT-027, adds the
entry to `docs/decisions/index.jsonl`, and updates the DOC-053 ADR-count assertion from 9 → 10.
All requirements are met. Zero new regressions introduced.

---

## Artifacts Reviewed

| Artifact | Status |
|---|---|
| `docs/decisions/ADR-010-windows-only-ci.md` | ✅ Exists, content correct |
| `docs/decisions/index.jsonl` — ADR-010 entry | ✅ Present, schema valid |
| `tests/MNT-028/test_mnt028_adr010.py` — 3 developer tests | ✅ All pass |
| `tests/DOC-053/test_doc053_adr_related_wps.py` — count updated to 10 | ✅ 18/18 pass |
| `docs/workpackages/MNT-028/dev-log.md` | ✅ Non-empty, complete |

---

## Tests Run

### Developer tests (`tests/MNT-028/test_mnt028_adr010.py`) — 3 tests

| Test | Result |
|---|---|
| `test_adr010_file_exists` | PASS |
| `test_adr010_index_entry_exists` | PASS |
| `test_adr010_references_mnt027` | PASS |

### Tester edge-case tests (`tests/MNT-028/test_mnt028_adr010_tester.py`) — 11 tests

| Test | Result | What it checks |
|---|---|---|
| `test_adr010_has_required_sections` | PASS | All 4 required sections present |
| `test_adr010_status_header_is_active` | PASS | `**Status:** Active` in markdown |
| `test_adr010_references_mnt028` | PASS | ADR-010 mentions the creating WP |
| `test_adr010_date_header_is_present` | PASS | `**Date:**` header present |
| `test_adr010_mentions_windows_only` | PASS | Decision mentions `windows-latest` |
| `test_adr010_index_title_non_empty` | PASS | Title field is non-empty |
| `test_adr010_index_status_is_active` | PASS | Index Status = "Active" |
| `test_adr010_index_date_format` | PASS | Date matches YYYY-MM-DD |
| `test_adr010_index_superseded_by_empty` | PASS | Superseded By = "" |
| `test_adr010_index_related_wps_includes_mnt027_and_mnt028` | PASS | Both MNT-027 and MNT-028 listed |
| `test_adr010_is_last_entry_in_index` | PASS | ADR-010 is the last index entry |

### DOC-053 regression (`tests/DOC-053/`) — 18 tests

All 18 pass including `test_adr_index_has_ten_entries`.

### Full suite regression check

- Total failures: 115  
- Baseline entries: 184  
- **New regressions: 0**  
- All failures pre-exist in `tests/regression-baseline.json`  
- Logged as TST-2633 (full suite) and TST-2634 (targeted MNT-028)

---

## Content Review

**ADR-010 document** (`docs/decisions/ADR-010-windows-only-ci.md`):
- Contains all required sections: Context, Decision, Consequences, Re-Enablement Criteria,
  Alternatives Considered
- Accurately describes the MNT-027 change (disabled macOS/Linux CI jobs)  
- States re-enablement criteria at stable v4.0
- References both MNT-027 (the implementing WP) and MNT-028 (the documenting WP)
- Status is Active, Date is 2026-04-05

**index.jsonl ADR-010 entry**:
- `ADR-ID`: "ADR-010" ✅
- `Title`: "Windows-Only CI Until Stable Release" ✅
- `Status`: "Active" ✅
- `Date`: "2026-04-05" ✅
- `Related WPs`: ["MNT-027", "MNT-028"] ✅
- `Superseded By`: "" ✅

---

## ADR Conflict Check

Reviewed `docs/decisions/index.jsonl` for superseded decisions related to CI. No existing ADR
contradicts ADR-010. ADR-002 (Mandatory CI Test Gate) is complementary — it mandates a Windows
CI gate; ADR-010 restricts CI to Windows only. No conflict.

---

## Issues Found

None.

---

## Verdict

**PASS** — All 32 tests pass (14 MNT-028 + 18 DOC-053). Zero new regressions. All
deliverables complete and correctly implemented.
