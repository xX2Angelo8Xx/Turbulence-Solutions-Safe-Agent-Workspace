# Dev Log — SAF-075: Fix platform-dependent integrity hashes

**Status:** In Progress  
**Branch:** SAF-075/fix-platform-hashes  
**Assigned To:** Developer Agent  
**Date Started:** 2026-04-03

---

## Prior Art Check

Reviewed `docs/decisions/index.csv`. No ADRs (ADR-001 through ADR-006) are
directly related to line-ending normalization or integrity hashing. No
supersession required.

---

## Requirements

From WP row:
- Normalize line endings (CRLF → LF) before computing SHA256 in both
  `security_gate.py` (functions `_compute_file_hash` and
  `_compute_gate_canonical_hash`) and `update_hashes.py` (functions
  `_sha256_file` and `_compute_canonical_gate_hash`).
- Add `.gitattributes` rules for template security files (enforce LF).
- Refresh git index so tracked files are re-normalized.
- Regenerate hashes after normalization.
- Fixes BUG-185.

**Goal:** Integrity check passes on all platforms regardless of line endings.

---

## Implementation Summary

### Files Changed

| File | Change |
|------|--------|
| `templates/agent-workbench/.github/hooks/scripts/security_gate.py` | Added `content.replace(b"\\r\\n", b"\\n")` in `_compute_file_hash()` and `_compute_gate_canonical_hash()` |
| `templates/agent-workbench/.github/hooks/scripts/update_hashes.py` | Added `content.replace(b"\\r\\n", b"\\n")` in `_sha256_file()` and `_compute_canonical_gate_hash()` |
| `.gitattributes` | Added LF enforcement rules for template security files |
| `templates/agent-workbench/.github/hooks/scripts/security_gate.py` | Hashes re-embedded via `update_hashes.py` |

### Design Decisions

1. **Normalize before hashing, not before storing:** The files on disk keep their
   native line endings; only the bytes fed into SHA256 are normalized. This
   avoids rewriting all files and is fully reversible.
2. **`replace(b"\\r\\n", b"\\n")` before `re.sub`:** Normalization must happen
   before the regex substitution in `_compute_canonical_gate_hash/
   _compute_gate_canonical_hash` so the zeroing pattern matches consistently.
3. **`.gitattributes` LF rules:** Ensures future checkouts on all platforms
   produce LF endings for the template security files, making the stored hashes
   correct on every platform.

---

## Tests Written

- `tests/SAF-075/test_saf075_platform_hashes.py`
  - `test_file_hash_crlf_lf_same` — CRLF and LF content produce same hash
  - `test_canonical_gate_hash_crlf_lf_same` — canonical gate hash is line-ending independent
  - `test_verify_integrity_lf_variant` — verify_file_integrity() succeeds with LF-only files
  - `test_verify_integrity_crlf_variant` — verify_file_integrity() succeeds with CRLF files
  - `test_sha256_file_crlf_lf_same` (update_hashes) — _sha256_file normalizes CRLF
  - `test_compute_canonical_gate_hash_crlf_lf_same` (update_hashes) — _compute_canonical_gate_hash normalizes CRLF

---

## Known Limitations

None.

---

## Bugs Fixed

- BUG-185: Integrity hash check is platform-dependent (CRLF vs LF) — fixed by
  CRLF→LF normalization in all four hashing functions.
