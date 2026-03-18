# FIX-031 Test Report — Fix macOS bottom-up code signing

**WP ID:** FIX-031  
**Verdict:** PASS  
**Tester:** Tester Agent  
**Date:** 2026-03-18  
**Branch:** fix-031  
**Commit reviewed:** fe8e1a7  

---

## Summary

FIX-031 replaces the broken `codesign --deep` call in `build_dmg.sh` with a
bottom-up signing strategy that fixes the `bundle format unrecognized` CI
regression (BUG-061) caused by `codesign --deep` attempting to recursively sign
`python3.11/` (a plain directory, not a valid bundle).

All acceptance criteria from US-026 are met. All 14 FIX-031 tests pass (10 Dev +
4 Tester edge-case). All 22 updated FIX-028 tests pass. Full regression suite
shows no new failures attributable to FIX-031.

---

## Review Findings

### `src/installer/macos/build_dmg.sh`

| Check | Result |
|-------|--------|
| `set -euo pipefail` present | PASS |
| Step 3.5 label present | PASS |
| "bottom-up" comment present | PASS |
| `find *.dylib -exec codesign` present | PASS |
| `find *.so -exec codesign` present | PASS |
| `find` commands target `_internal/` | PASS |
| Python.framework signing uses `--deep` | PASS |
| Python.framework signing guarded by `if [ -d ... ]` | PASS |
| Main launcher explicitly signed | PASS |
| Final `.app` bundle signed **without** `--deep` | PASS |
| `codesign --verify --deep --strict` present | PASS |
| All codesign `--sign` lines use `--force` | PASS |
| Signing block appears before `hdiutil create` | PASS |
| No CRLF line endings | PASS |
| No hardcoded credentials | PASS |

### `tests/FIX-031/test_fix031_bottomup_codesign.py`

10 tests covering: dylib/so find commands, Python.framework `--deep`, main launcher
signed, app bundle signed without `--deep`, verify `--deep --strict`, ordering
(bottom-up), Step 3.5 label, `pipefail`, full signing order sequence.

### `tests/FIX-028/test_fix028_codesign.py`

22 tests — Developer correctly updated this file:
- `test_deep_flag_present` now asserts `--deep` on Python.framework only, NOT on
  final `.app` bundle.
- 3 new tests added: `test_find_dylib_signing_present`, `test_find_so_signing_present`,
  `test_python_framework_signing_uses_deep`.

---

## Test Results

| TST-ID | Suite | Result | Count |
|--------|-------|--------|-------|
| TST-1778 | FIX-031 developer tests | Pass | 10/10 |
| TST-1779 | FIX-028 updated tests | Pass | 22/22 |
| TST-1780 | FIX-031 Tester edge-case tests | Pass | 4/4 |
| TST-1781 | Full regression suite | Pass | 3404 passed, 11 pre-existing failures |

---

## Edge-Case Tests Added (Tester)

File: `tests/FIX-031/test_fix031_edge_cases.py`

| Test | Rationale |
|------|-----------|
| `test_python_framework_signing_guarded_by_if_d` | Without the guard, builds without Python.framework would abort on a non-existent path |
| `test_find_dylib_targets_internal_directory` | Ensures find scope is `_internal/` not `Contents/MacOS/` (which would double-sign the launcher) |
| `test_find_so_targets_internal_directory` | Same scope check for `.so` files |
| `test_all_sign_invocations_use_force` | Ensures no codesign `--sign` line omits `--force` (omission causes "already signed" error under `pipefail`) |

All 4 edge-case tests pass.

---

## Regression Analysis

Full suite: **3404 passed / 11 failed / 29 skipped / 1 xfailed**

All 11 failures are pre-existing (confirmed by running the same tests on the state before FIX-031 was applied via `git stash`):

| Test | Pre-existing? | Root Cause |
|------|---------------|-----------|
| `FIX-009::test_tst_ids_sequential_no_gaps_in_renumbered_range` | Yes | TST-ID gap from prior sessions (TST-1662 to TST-1764) |
| `FIX-009::test_no_duplicate_tst_ids` | Yes | Duplicates TST-599, TST-1557 from prior WPs |
| `INS-005::test_uninstall_delete_type_is_filesandirs` | Yes | BUG-045 |
| `SAF-028::*` (8 tests) | Yes | SAF-028 not yet implemented |

**Zero new failures introduced by FIX-031.**

---

## Security Review

- No secrets, credentials, or API keys in the script or tests.
- Ad-hoc signing (`--sign -`) uses the `-` identity (no certificate required).
- `set -euo pipefail` ensures signing failures abort the build immediately.
- No path traversal risk: all paths use the `${APP_BUNDLE}` variable expanded from
  a controlled value set at script start.
- No external network calls.

---

## Verdict: PASS

All acceptance criteria met:
- [x] `.dylib` and `.so` files signed individually before `.app` bundle
- [x] Python.framework signed with `--deep` (valid nested bundle)
- [x] `.app` bundle signed WITHOUT `--deep` (prevents python3.11 dir error)
- [x] `codesign --verify --deep --strict` passes after signing
- [x] `set -euo pipefail` ensures signing failures abort the build
- [x] Step 3.5 labelled with "bottom-up" comment
- [x] No CRLF line endings
- [x] No regressions in existing tests
