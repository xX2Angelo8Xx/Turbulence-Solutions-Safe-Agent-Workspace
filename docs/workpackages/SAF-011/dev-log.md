# SAF-011 Dev Log — Hash Update Script

**WP ID:** SAF-011  
**Name:** Hash Update Script  
**Category:** SAF (Safety)  
**Assigned To:** Developer Agent  
**Date Started:** 2026-03-14  
**Branch:** SAF-011/hash-update-script  
**Linked Bug:** BUG-027  
**User Story:** US-013

---

## Goal

Create `update_hashes.py` in `Default-Project/.github/hooks/scripts/` that recomputes SHA256 hashes of `security_gate.py` and `settings.json` and re-embeds them into `security_gate.py`. Also copy to `templates/coding/.github/hooks/scripts/` to keep templates in sync.

---

## Implementation Summary

### Files Created

1. `Default-Project/.github/hooks/scripts/update_hashes.py`
2. `templates/coding/.github/hooks/scripts/update_hashes.py` (copy)
3. `tests/SAF-011/__init__.py`
4. `tests/SAF-011/test_saf011_update_hashes.py`

### Algorithm

The script applies the canonical form algorithm used by `security_gate.py`'s own `_compute_gate_canonical_hash()`:

1. Compute `new_settings_hash` = SHA256 of `../.vscode/settings.json` (raw bytes)
2. Read `security_gate.py` bytes
3. Replace `_KNOWN_GOOD_SETTINGS_HASH` value in the content (in memory)
4. Compute canonical form: replace `_KNOWN_GOOD_GATE_HASH` value with 64 zeros in the partially-updated content
5. Compute `new_gate_hash` = SHA256 of canonical content
6. Replace `_KNOWN_GOOD_GATE_HASH` value in the content
7. Write final content to disk
8. Print confirmation of both hashes updated

### Path Layout

`update_hashes.py` lives in `scripts/`. Relative to it:
- `security_gate.py` is in the same directory
- `settings.json` is at `../../../.vscode/settings.json` (scripts → hooks → .github → workspace-root → .vscode)

### Security Considerations

- Uses `pathlib.Path.resolve()` to prevent path traversal
- Validates both target files exist before modifying anything
- Fails with a clear error message on any IO or regex error
- No secrets, no absolute paths in code
- No `eval()`/`exec()` usage

---

## Tests Written

Located in `tests/SAF-011/test_saf011_update_hashes.py`:

| Test | Type | Description |
|------|------|-------------|
| test_script_exists | Unit | update_hashes.py exists in Default-Project and templates |
| test_template_copy_exists | Unit | templates copy exists |
| test_script_is_valid_python | Unit | ast.parse succeeds |
| test_no_absolute_paths | Security | no absolute path strings in script |
| test_computes_settings_hash_correctly | Unit | SHA256(settings.json) matches hashlib |
| test_computes_gate_canonical_hash | Unit | canonical form zeros gate hash |
| test_canonical_independent_of_gate_hash | Unit | different gate hash value → same canonical hash |
| test_reembeds_settings_hash | Unit | settings hash replaced in content |
| test_reembeds_gate_hash | Unit | gate hash replaced after settings update |
| test_full_update_on_real_files | Integration | run script, verify_file_integrity() returns True after |
| test_file_not_found_settings | Unit | clear error when settings.json missing |
| test_file_not_found_gate | Unit | clear error when security_gate.py missing |
| test_hash_format_64_hex_chars | Unit | embedded hashes are 64 lowercase hex chars |
| test_no_dry_run_needed | Unit | script writes updated content back to disk |
| test_idempotent | Integration | running twice produces same result |

---

## Known Limitations

None.

---

## Test Results

| Run | Tests | Pass | Fail | Skip | Notes |
|-----|-------|------|------|------|-------|
| SAF-011 suite | 17 | 17 | 0 | 0 | TST-624–TST-640; fixed importlib module registration issue in test_full_update_on_real_files_integrity_passes |
| Full regression | 1584 | 1584 | 0 | 2 | TST-641; zero regressions vs prior baseline of 1567 |

---

## Iteration History

| Iteration | Date | Summary |
|-----------|------|---------|
| 1 | 2026-03-14 | Initial implementation; 17/17 SAF-011 tests pass; 1584/1584 full regression green; BUG-027 resolved |
