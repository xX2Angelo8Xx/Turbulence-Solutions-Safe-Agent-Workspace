# Test Report — SAF-025: Update security_gate.py Integrity Hashes

**Tester:** Tester Agent  
**Date:** 2026-03-17  
**Branch:** `SAF-025/update-hashes`  
**Verdict:** PASS

---

## 1. Review Summary

### Code Changes Verified

No application source code was modified by this WP. The Developer ran `update_hashes.py`
and confirmed the hashes were already correct (no file changes required). The only
deliverables are test files and log updates.

- **`tests/SAF-025/test_saf025_hash_sync.py`** — 11 new tests covering sync and hash
  correctness for 7 security-critical files. Tests use `hashlib` + regex directly
  (no importlib writes into `templates/coding/`). ✓
- **`tests/SAF-025/__init__.py`** — Package marker present. ✓
- **`docs/workpackages/SAF-025/dev-log.md`** — Present, non-empty, accurate. ✓
- **`docs/workpackages/workpackages.csv`** — SAF-025 status updated Open → In Progress → Review. ✓
- **`docs/test-results/test-results.csv`** — TST-1632 through TST-1644 logged. ✓

### Independent Tester Hash Verification

Tester independently computed SHA256 hashes:

| Hash Constant | Embedded in security_gate.py | Independently Computed | Match |
|---------------|------------------------------|------------------------|-------|
| `_KNOWN_GOOD_SETTINGS_HASH` | `fcffb52f64514d8d77d3985b8fa9dd1160cb6cff7b72ca4f7b07a04351200e40` | `fcffb52f64514d8d77d3985b8fa9dd1160cb6cff7b72ca4f7b07a04351200e40` | ✓ |
| `_KNOWN_GOOD_GATE_HASH` | `edd089f7bcbc9317f8bb461933a4bc7aed3dd5895eb0cd81dc74c68c0132bca8` | `edd089f7bcbc9317f8bb461933a4bc7aed3dd5895eb0cd81dc74c68c0132bca8` | ✓ |

### Independent File Sync Verification

Tester independently verified byte-for-byte sync between `Default-Project/` and
`templates/coding/` for all 7 security-critical files:

| File | Sync Status |
|------|-------------|
| `.github/hooks/scripts/security_gate.py` | ✓ Identical |
| `.github/hooks/scripts/zone_classifier.py` | ✓ Identical |
| `.github/hooks/scripts/update_hashes.py` | ✓ Identical |
| `.github/hooks/scripts/require-approval.ps1` | ✓ Identical |
| `.github/hooks/scripts/require-approval.sh` | ✓ Identical |
| `.github/hooks/require-approval.json` | ✓ Identical |
| `.vscode/settings.json` | ✓ Identical |

### Requirements Verification

| Requirement | Met |
|-------------|-----|
| SHA256 hashes correct for v2.0.0 security files | ✓ |
| `_KNOWN_GOOD_SETTINGS_HASH` matches `sha256(settings.json)` | ✓ |
| `_KNOWN_GOOD_GATE_HASH` matches canonical `sha256(security_gate.py)` | ✓ |
| `verify_file_integrity()` returns True for Default-Project | ✓ |
| `Default-Project/` and `templates/coding/` in sync (7 files) | ✓ |
| No `__pycache__` created in `templates/coding/` | ✓ |
| No application source code modified | ✓ |

---

## 2. Test Results

### Developer Tests (TST-1632 to TST-1643)

All 11 developer tests pass.

| ID | Test Name | Result |
|----|-----------|--------|
| TST-1632 | `test_security_gate_files_are_identical` | PASS |
| TST-1633 | `test_settings_json_files_are_identical` | PASS |
| TST-1634 | `test_zone_classifier_files_are_identical` | PASS |
| TST-1635 | `test_update_hashes_files_are_identical` | PASS |
| TST-1636 | `test_require_approval_json_files_are_identical` | PASS |
| TST-1637 | `test_require_approval_ps1_files_are_identical` | PASS |
| TST-1638 | `test_require_approval_sh_files_are_identical` | PASS |
| TST-1639 | `test_embedded_settings_hash_matches_actual_file` | PASS |
| TST-1640 | `test_embedded_gate_hash_matches_canonical_hash` | PASS |
| TST-1641 | `test_verify_file_integrity_passes_default_project` | PASS |
| TST-1642 | `test_verify_file_integrity_passes_templates_copy` | PASS |

### Tester Edge-Case Tests (TST-1645 to TST-1647)

All 3 tester edge-case tests pass.

| ID | Test Name | Result | Rationale |
|----|-----------|--------|-----------|
| TST-1645 | `test_hash_constants_appear_exactly_once` | PASS | Duplicate constant definitions would confuse `update_hashes.py` and silently embed stale hashes |
| TST-1646 | `test_canonical_hash_independent_of_settings_hash` | PASS | Canonical computation must only zero `_KNOWN_GOOD_GATE_HASH` — confirms the algorithm is correct |
| TST-1647 | `test_no_pycache_in_templates_coding` | PASS | Importing `security_gate` via `sys.path` pointing at Default-Project must not create bytecode in `templates/coding/` |

### SAF-008 Regression (hash integrity functions remain correct)

All 23 SAF-008 tests pass after the SAF-025 changes.

### Full Regression Suite

| Run | Passed | Failed | Skipped | Pre-existing Failures |
|-----|--------|--------|---------|----------------------|
| Developer targeted (TST-1643) | 11 | 0 | 0 | — |
| Developer full suite (TST-1644) | 3132 | 2 | 29 | FIX-009 dup TST-1557 + INS-005 BUG-045 |
| Tester targeted SAF-025 + SAF-008 (TST-1648) | 34 | 0 | 0 | — |
| Tester full suite (TST-1649) | 3135 | 2 | 29 | FIX-009 dup TST-1557 + INS-005 BUG-045 |

The 2 failures are pre-existing and unrelated to SAF-025:
- `test_no_duplicate_tst_ids` (FIX-009): TST-1557 appears twice — known alias bug, tracked in bugs.csv.
- `test_uninstall_delete_type_is_filesandirs` (INS-005): Regex mismatch against Inno Setup `filesandordirs` keyword — tracked as BUG-045.

Zero new failures introduced.

---

## 3. Security Analysis

### Attack Vectors Considered

1. **Stale hash bypass after future file edit**: If `security_gate.py` or `settings.json`
   is modified without re-running `update_hashes.py`, the embedded hashes become stale
   and `verify_file_integrity()` would return `False`, correctly blocking the gate from
   initializing. The dual-hash scheme (gate self-hashes canonically) prevents any
   single-file tampering from succeeding silently. ✓

2. **Duplicate hash constant injection**: An attacker could attempt to add a second
   `_KNOWN_GOOD_GATE_HASH` constant further down the file, causing `update_hashes.py`
   to patch only the first occurrence while the runtime reads the second. TST-1645
   locks in the invariant that exactly one of each constant exists. ✓

3. **Settings hash constant zeroed in canonical computation**: The canonical hash
   algorithm only zeros `_KNOWN_GOOD_GATE_HASH` before hashing itself. If it also
   zeroed `_KNOWN_GOOD_SETTINGS_HASH`, the embedded gate hash would not match
   `sha256(canonical)` at runtime and the gate would deny every operation. TST-1646
   confirms the algorithm is correct. ✓

4. **`__pycache__` pollution in templates**: Importing `security_gate` via Python
   could create `templates/coding/.github/hooks/scripts/__pycache__/`. New agent
   workspaces cloned from the template would inherit this bytecode, which is
   platform-specific and could mask future source changes. TST-1647 ensures this
   cannot regress. ✓

5. **templates/coding drift**: If files become out of sync between `Default-Project/`
   and `templates/coding/`, agent workspaces may receive incorrect hashes and fail
   integrity checks on first use. TST-1632 through TST-1638 provide a full suite of
   byte-level sync assertions across all 7 critical files. ✓

### Boundary & Edge Cases

- Canonical hash computation handles files with no `_KNOWN_GOOD_GATE_HASH` line
  without crashing (regex substitution produces no change → hash is still valid). ✓
- Both `[0-9a-f]` and `[0-9a-fA-F]` patterns accepted in embedded constants — the
  canonical computation uses case-insensitive replacement, and SAF-008 has an
  existing test (`test_canonical_hash_uppercase_hex_recognized`) for this. ✓

---

## 4. Bugs Found

None. No new bugs identified during testing.
