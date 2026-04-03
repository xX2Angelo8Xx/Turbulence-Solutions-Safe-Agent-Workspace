# Test Report — SAF-075: Fix platform-dependent integrity hashes

**Tester:** Tester Agent  
**Date:** 2026-04-03  
**Branch:** SAF-075/fix-platform-hashes  
**Iteration:** 2  
**Verdict:** PASS

---

## Iteration 1 Report (FAIL)

See git history: commit `1623eb2` contains the original FAIL test report.

---

## Summary (Iteration 2 — PASS)

All 8 regressions identified in the iteration 1 review have been resolved.
All 132 tests in the combined target suite (SAF-022, SAF-025, SAF-052, SAF-075,
SAF-008, SAF-011, snapshots) pass. No new regressions found against the
baseline of 680 known failures. The CRLF normalization is correct, the embedded
hash constants are verified, and all template files have LF line endings on disk.

## Summary (Iteration 1 — archived)

The SAF-075 implementation was logically correct — all 8 dedicated SAF-075
tests passed, the CRLF normalization was applied in the right place. However
template files still had CRLF on disk and `git add --renormalize` was not run,
causing 8 hash-sync regressions in SAF-022, SAF-025, SAF-052.

---

## Test Runs

### SAF-075 — dedicated tests (8 tests)

| Test | Result |
|------|--------|
| test_compute_file_hash_crlf_lf_same | PASS |
| test_compute_file_hash_pure_lf_unchanged | PASS |
| test_compute_gate_canonical_hash_crlf_lf_same | PASS |
| test_compute_gate_canonical_hash_zeroes_constant | PASS |
| test_verify_integrity_lf_variant | PASS |
| test_verify_integrity_crlf_variant | PASS |
| test_sha256_file_crlf_lf_same | PASS |
| test_compute_canonical_gate_hash_uh_crlf_lf_same | PASS |

**8/8 pass.**

### SAF-008 / SAF-011 / snapshots — regression block (59 tests)

All 59 pass. No regressions in these suites.

### SAF-022 / SAF-025 / SAF-052 — hash-sync suites (NEW FAILURES)

| Test | Result | Root Cause |
|------|--------|------------|
| SAF-022::test_default_gate_settings_hash_matches | FAIL | see below |
| SAF-022::test_template_gate_settings_hash_matches | FAIL | see below |
| SAF-025::test_embedded_settings_hash_matches_actual_file | FAIL | see below |
| SAF-025::test_embedded_gate_hash_matches_canonical_hash | FAIL | see below |
| SAF-025::test_verify_file_integrity_passes_templates_copy | FAIL | see below |
| SAF-025::test_canonical_hash_independent_of_settings_hash | FAIL | see below |
| SAF-025::test_no_pycache_in_templates_coding | FAIL | pre-existing (see §Notes) |
| SAF-052::test_gate_hash_matches_embedded_constant | FAIL | see below |

---

## Root Cause Analysis

### Hash comparison

The Developer ran `update_hashes.py` AFTER adding CRLF normalization to it.
`update_hashes.py` now embeds the **normalized (LF-based)** hash values:

| | Current value |
|---|---|
| `_KNOWN_GOOD_SETTINGS_HASH` | `c9cd0834…` = SHA256(LF-normalized settings.json) |
| `_KNOWN_GOOD_GATE_HASH` | `4a2a8128…` = SHA256(canonical(LF-normalized gate)) |

However, on the current Windows working tree, both
`templates/agent-workbench/.vscode/settings.json` and
`templates/agent-workbench/.github/hooks/scripts/security_gate.py`
still have **CRLF** line endings (settings.json: 43 CRLF sequences;
security_gate.py: 3468 CRLF sequences). The `.gitattributes` rules were added
but `git add --renormalize .` was never run to convert the working-tree files to
LF.

The SAF-022, SAF-025, and SAF-052 tests verify hashes using simple
`hashlib.sha256(file.read_bytes()).hexdigest()` **without** CRLF normalization.
Because the files are still CRLF, they compute SHA256(CRLF) which differs from
the embedded SHA256(LF):

```
settings.json:
  SHA256(raw CRLF) = 1786325dfd2a3e00…   ← what old tests compute
  SHA256(LF)       = c9cd0834dd2e3f0e…   ← what is embedded
                                            ^ MISMATCH

security_gate.py canonical:
  SHA256(canonical, CRLF) = 7f48c9f027a0…   ← what old tests compute
  SHA256(canonical, LF)   = 4a2a81289cc1…   ← what is embedded
                                               ^ MISMATCH
```

### `test_no_pycache_in_templates_coding`

This test checks that `__pycache__` does not exist in the templates scripts
directory. The directory already existed before SAF-075 because SAF-008 and
SAF-011 tests also import `security_gate` from the same location. This is a
**pre-existing omission from the regression baseline**, not a SAF-075
regression. It is noted here for completeness but is outside this WP's scope.

---

## Security Analysis

- The CRLF normalization logic is correct and placed BEFORE the `re.sub` zero-
  out step in `_compute_gate_canonical_hash` — ordering is correct.
- Both `security_gate.py` and `update_hashes.py` use identical normalization
  (`content.replace(b"\r\n", b"\n")`), ensuring the stored and computed hashes
  use the same algorithm.
- `verify_file_integrity()` on the current Windows machine returns `True`
  (confirmed by SAF-008 integrity tests passing).
- The `.gitattributes` `eol=lf` rules are correct and comprehensive.
- No security bypass vectors introduced.

---

## Acceptance Criteria Check

| Criterion | Status |
|-----------|--------|
| CRLF-normalized hash in `_compute_file_hash()` | PASS |
| CRLF-normalized hash in `_compute_gate_canonical_hash()` | PASS |
| CRLF-normalized hash in `_sha256_file()` (update_hashes) | PASS |
| CRLF-normalized hash in `_compute_canonical_gate_hash()` (update_hashes) | PASS |
| Hashes regenerated and embedded | PASS (hashes are correct for LF) |
| `.gitattributes` LF enforcement added | PASS |
| Files on disk have LF line endings (required for test consistency) | **FAIL** — still CRLF |
| Existing hash-sync tests (SAF-022/025/052) pass | **FAIL** — 7 tests broken |

---

## Required Actions (TODOs for Developer)

### TODO-1 (BLOCKER): Convert on-disk files to LF and re-run `update_hashes.py`

The `.gitattributes` rules were added but the existing working-tree files were
not converted to LF. This is the root cause of all 7 hash-sync regressions.

**Steps:**

```powershell
# 1. Stage the .gitattributes change so git knows about the eol rules
git add .gitattributes

# 2. Re-normalize ALL tracked files according to the new .gitattributes rules
git add --renormalize .

# 3. Check out the renormalized versions into the working tree.
#    Do this selectively for the security-critical files:
git checkout -- templates/agent-workbench/.vscode/settings.json
git checkout -- templates/agent-workbench/.github/hooks/scripts/security_gate.py
git checkout -- templates/agent-workbench/.github/hooks/scripts/update_hashes.py
git checkout -- templates/agent-workbench/.github/hooks/scripts/zone_classifier.py
# (repeat for any other .py/.json file in the template that should be LF)

# 4. Verify files are now LF:
#    security_gate.py should show 0 CRLF sequences.

# 5. Re-run update_hashes.py to embed the correct hashes for the LF files:
.venv\Scripts\python.exe templates\agent-workbench\.github\hooks\scripts\update_hashes.py

# 6. Re-run the full hash-sync test suite to confirm all pass:
.venv\Scripts\python.exe -m pytest tests/SAF-022/ tests/SAF-025/ tests/SAF-052/ tests/SAF-075/ -v
```

The embedded hash values will change when the files switch from CRLF to LF,
because `_compute_canonical_gate_hash` no longer needs to normalize (the file is
already LF). Verify that `verify_file_integrity()` still returns `True` after
the update.

### TODO-2 (BLOCKER): Verify SAF-022 + SAF-025 + SAF-052 + SAF-075 all pass before re-submitting

Run:

```
.venv\Scripts\python.exe -m pytest tests/SAF-022/ tests/SAF-025/ tests/SAF-052/ tests/SAF-075/ tests/SAF-008/ tests/SAF-011/ tests/snapshots/ -v
```

All tests must pass. Update `dev-log.md` with the outcome.

### TODO-3 (CLEANUP): Remove `__pycache__` from templates directory (optional)

`templates/agent-workbench/.github/hooks/scripts/__pycache__` was created by
test imports. While this is pre-existing, consider adding `sys.dont_write_bytecode = True`
(or `importlib.util` approach) when importing from the templates directory in
test modules. Log a follow-up WP if desired. Not a blocker for SAF-075.

---

## Bugs Filed

- **BUG-186** — SAF-022/025/052 hash-sync tests broken after SAF-075: files
  still have CRLF on disk after `.gitattributes` update; working-tree
  renormalization was not performed. **→ Closed (Fixed In WP = SAF-075)**

---

## Iteration 2 Verification (2026-04-03)

### TST-2463 — Tester re-run (132 tests)

```
.venv\Scripts\python.exe -m pytest tests/SAF-022/ tests/SAF-025/ tests/SAF-052/ tests/SAF-075/ tests/SAF-008/ tests/SAF-011/ tests/snapshots/ -v --tb=short
```

**132 passed, 0 failed.**

| Suite | Count | Result |
|-------|-------|--------|
| SAF-022 | 26 | PASS |
| SAF-025 | 14 | PASS |
| SAF-052 | 25 | PASS |
| SAF-075 | 8 | PASS |
| SAF-008 | 22 | PASS |
| SAF-011 | 27 | PASS |
| snapshots | 10 | PASS |

### Full regression sweep

627 failures in full sweep — within baseline of 680 known failures. No new regressions.

### Hash constants verified

| Constant | Embedded | Computed | Match |
|----------|----------|----------|-------|
| `_KNOWN_GOOD_SETTINGS_HASH` | `c9cd0834…` | `c9cd0834…` | ✓ |
| `_KNOWN_GOOD_GATE_HASH` | `4a2a8128…` | `4a2a8128…` | ✓ |

### Template file line endings verified

All 7 security-critical template files show CRLF=0 (pure LF).

### Acceptance Criteria (Iteration 2)

| Criterion | Status |
|-----------|--------|
| `_compute_file_hash()` normalizes CRLF | PASS |
| `_compute_gate_canonical_hash()` normalizes CRLF | PASS |
| `_sha256_file()` (update_hashes) normalizes CRLF | PASS |
| `_compute_canonical_gate_hash()` (update_hashes) normalizes CRLF | PASS |
| `.gitattributes` LF enforcement covers all security template files | PASS |
| Template security files have LF on disk | PASS |
| SAF-022/025/052 hash-sync tests pass | PASS |
| SAF-008/011/snapshots regression tests pass | PASS |
| SAF-075 dedicated tests pass | PASS |
| BUG-185 and BUG-186 closed | PASS |
| `validate_workspace.py --wp SAF-075` clean (exit 0) | PASS |

---

## Verdict (Iteration 1)

**FAIL** — 8 regressions. WP returned to `In Progress`.

## Verdict (Iteration 2)

**PASS** — All 132 tests pass, no new regressions, all acceptance criteria met.

