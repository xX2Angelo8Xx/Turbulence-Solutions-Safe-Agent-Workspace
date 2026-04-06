# FIX-115 Dev Log — Drop settings.json from Integrity Hash Check

## Summary

**Bug Fixed:** BUG-194 — VS Code auto-migrates deprecated settings keys when opening a workspace, modifying `.vscode/settings.json` and invalidating the SHA256 hash embedded in `security_gate.py`. This caused `verify_file_integrity()` to return `False`, blocking ALL tool calls.

**Solution:** Remove `.vscode/settings.json` from the `verify_file_integrity()` hash check. The function now only verifies `security_gate.py` against `_KNOWN_GOOD_GATE_HASH`. The `_KNOWN_GOOD_SETTINGS_HASH` constant is removed entirely.

**ADR:** ADR-011 — Drop settings.json from Security Gate Integrity Hash

## Prior Art Check

Reviewed `docs/decisions/index.jsonl`. ADRs ADR-008 (Tests Must Track Current Codebase State) and ADR-010 (Windows-Only CI) are relevant context. No prior ADR contradicts this decision. ADR-011 is created to document it.

## Files Changed

### Modified
- `templates/agent-workbench/.github/hooks/scripts/security_gate.py`
  - Removed `_KNOWN_GOOD_SETTINGS_HASH` constant
  - Removed settings.json hash check from `verify_file_integrity()`
  - Updated `_INTEGRITY_WARNING` to only reference `security_gate.py`
- `templates/agent-workbench/.github/hooks/scripts/update_hashes.py`
  - Removed `_SETTINGS_HASH_RE` pattern
  - Removed settings.json hash computation and embedding
  - Updated `_resolve_paths()` to only return gate path
  - `update_hashes()` now only re-embeds gate hash
- `docs/decisions/index.jsonl` — Added ADR-011 entry
- `docs/decisions/ADR-011.md` — New ADR document
- `docs/workpackages/workpackages.jsonl` — Status set to In Progress → Review
- `docs/bugs/bugs.jsonl` — BUG-194 `Fixed In WP` set to `FIX-115`

### Test Files Updated
- `tests/SAF-008/test_saf008_integrity.py` — Updated tests that referenced `_KNOWN_GOOD_SETTINGS_HASH` or settings-hash behavior
- `tests/SAF-011/test_saf011_update_hashes.py` — Updated tests for update_hashes.py settings removal
- `tests/SAF-011/test_saf011_edge_cases.py` — Updated edge case tests
- `tests/SAF-025/test_saf025_hash_sync.py` — Updated hash sync tests
- `tests/FIX-042/test_fix042_noagentzone_visible.py` — Updated integrity hash validation test
- `tests/SAF-071/test_saf071.py` — Updated hash constants tests
- `tests/SAF-075/test_saf075_platform_hashes.py` — Updated platform hash tests

### New Test File
- `tests/FIX-115/test_fix115_drop_settings_hash.py` — Dedicated tests for FIX-115

## Implementation Notes

1. `_compute_file_hash()` is retained in `security_gate.py` — it may be used by other consumers or tests.
2. The gate self-hash (`_KNOWN_GOOD_GATE_HASH`) is unchanged in its scheme — still uses canonical zeroing.
3. `update_hashes.py` no longer requires `settings.json` to exist. The `--error-missing-settings` error path is removed.
4. After modifying `security_gate.py`, `update_hashes.py` was run to re-embed the correct gate hash.

## Tests Written

See `tests/FIX-115/` for dedicated regression tests verifying:
- `_KNOWN_GOOD_SETTINGS_HASH` no longer exists in the module
- `verify_file_integrity()` returns `True` even when `settings.json` is missing or modified
- `update_hashes.py` no longer references or embeds a settings hash
- Gate self-hash still works correctly

## Test Results

All tests passed via `scripts/run_tests.py --wp FIX-115`.

---

## Iteration 2 (Tester Findings)

Tester identified 4 failing tests in 3 test files that referenced the removed
`_KNOWN_GOOD_SETTINGS_HASH` constant or the ADR index state prior to ADR-011.

**Files updated in Iteration 2:**
- `tests/FIX-079/test_fix079_noagentzone_visible.py` — Updated integrity hash test
- `tests/DOC-053/` — Updated documentation tests
- `tests/FIX-114/` — Updated related tests
- `tests/MNT-029/` — Updated maintenance tests

---

## Iteration 3 (Tester Findings)

Tester found 3 additional regressions (4 failing tests) not caught in Iteration 2:

1. **`tests/SAF-009/test_saf009_cross_platform.py::test_af5_integrity_constants_not_zeroed`**
   — Referenced `sg._KNOWN_GOOD_SETTINGS_HASH` which was removed. Fixed: removed assertion
   on the removed constant; added `hasattr` check verifying it is absent; retained
   `_KNOWN_GOOD_GATE_HASH` validity assertion.

2. **`tests/SAF-022/test_saf022_noagentzone_exclude.py::TestHashIntegrity`** —
   `_extract_settings_hash()` helper tried to regex-find the removed constant. Fixed:
   replaced both `test_default_gate_settings_hash_matches` and
   `test_template_gate_settings_hash_matches` with tests asserting `_KNOWN_GOOD_SETTINGS_HASH`
   is absent from the gate source and `_KNOWN_GOOD_GATE_HASH` is present and non-zeroed.

3. **`tests/MNT-028/test_mnt028_adr010_tester.py::test_adr010_is_last_entry_in_index`** —
   ADR-011 was added by FIX-115, so ADR-010 is no longer the last entry. Fixed: replaced
   "is last" assertion with a check that ADR-010 exists and is immediately followed by ADR-011
   (second-to-last position).

Full test suite after iteration 3 fixes: 8953 passed, 74 failed (all baseline), 344 skipped,
5 xfailed, 66 errors. Zero new regressions.

**MANIFEST.json regenerated** after test file changes.
**Committed:** `FIX-115: fix 3 remaining test regressions (iter 3)`
**Pushed:** `FIX-115/drop-settings-hash`
**Status:** → Review
