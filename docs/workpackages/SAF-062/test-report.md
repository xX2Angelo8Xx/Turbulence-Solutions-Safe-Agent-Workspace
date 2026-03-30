# Test Report — SAF-062

**Tester:** Tester Agent
**Date:** 2026-03-30
**Iteration:** 1

## Summary

SAF-062 adds `"test-path"` to `_PROJECT_FALLBACK_VERBS` in `security_gate.py` so
that `Test-Path .venv` (and other dot-prefixed workspace root paths) receive the
project-folder fallback instead of being incorrectly denied.  The implementation
is minimal, correct, and consistent with the existing pattern for other read-only
verbs.  All 14 tests (5 developer + 9 tester edge-cases) pass.  SHA256 hashes
have been updated and are verified by SAF-025 tests (which passed).  No
regressions introduced — the 164 full-suite failures are pre-existing on `main`
(confirmed independently).

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| `test_test_path_in_fallback_verbs` | Unit | PASS | `"test-path"` present in frozenset |
| `test_test_path_dot_venv_allowed` | Security/Regression | PASS | `Test-Path .venv` now allowed |
| `test_test_path_dot_env_allowed` | Security/Regression | PASS | `Test-Path .env` now allowed |
| `test_test_path_github_denied` | Security | PASS | `.github/` deny zone still enforced |
| `test_test_path_project_file_allowed` | Unit | PASS | Project-folder path allowed |
| `test_test_path_nested_under_dot_venv_allowed` | Unit/Edge | PASS | `Test-Path .venv/Scripts/python.exe` allowed |
| `test_test_path_dot_gitignore_allowed` | Unit/Edge | PASS | `Test-Path .gitignore` (file, not dir) allowed |
| `test_test_path_all_caps_allowed` | Security/Edge | PASS | `TEST-PATH .venv` case-insensitive check |
| `test_test_path_mixed_case_allowed` | Unit/Edge | PASS | `Test-Path .venv` standard casing |
| `test_test_path_lowercase_allowed` | Unit/Edge | PASS | `test-path .venv` lowercase |
| `test_test_path_no_args` | Unit/Edge | PASS | No args — gate does not crash; returns valid verdict |
| `test_test_path_absolute_system_path_denied` | Security/Edge | PASS | `Test-Path C:/Windows/System32` denied |
| `test_test_path_dot_github_denied` | Security/Edge | PASS | `Test-Path .github` still denied (deny zone) |
| `test_test_path_quoted_dot_venv_allowed` | Unit/Edge | PASS | `Test-Path ".venv"` quoted argument allowed |
| SAF-025 embedded hash tests | Security | PASS | `_KNOWN_GOOD_GATE_HASH` matches canonical hash |
| Full regression suite | Regression | PASS | 7462 passed; 164 pre-existing failures unchanged |

**Test result IDs logged:** TST-2319, TST-2320, TST-2321

## Code Review

**Files changed (branch diff vs. main):**
- `templates/agent-workbench/.github/hooks/scripts/security_gate.py` — `"test-path"` added to `_PROJECT_FALLBACK_VERBS`; `_KNOWN_GOOD_GATE_HASH` updated
- `tests/SAF-062/test_saf062_test_path_fallback.py` — developer tests
- `tests/SAF-062/conftest.py` — local conftest no-op override
- `tests/SAF-062/__init__.py` — package marker
- `docs/workpackages/SAF-062/dev-log.md` — developer log
- `docs/workpackages/workpackages.csv` — WP status updated
- `docs/test-results/test-results.csv` — test results logged

No files modified outside the expected scope.

The placement of `"test-path"` (line ~1576, after the `get-childitem` group) is
consistent with the SAF-041 style comment pattern.  The SHA256 `_KNOWN_GOOD_GATE_HASH`
constant (`b33715daefbfd62d5c9068ec308b6e036351e4f4c32a755f65c2462a2e4c62f0`) is
verified correct by `test_embedded_gate_hash_matches_canonical_hash` (SAF-025).

## Security Analysis

- **Bypass attempt:** `Test-Path .github` → correctly denied (deny-zone takes precedence, not fallback).
- **Absolute path:** `Test-Path C:/Windows/System32` → denied (outside project, no fallback route).
- **Case variation:** All three casings (`TEST-PATH`, `Test-Path`, `test-path`) are normalised to lowercase before lookup — consistent with `verb.lower()` used at line ~1820.
- **No destructive side-effect:** `test-path` is a read-only PowerShell built-in; adding it to `_PROJECT_FALLBACK_VERBS` does not grant write access.
- **Boundary check:** No-args invocation gracefully returns a verdict without crashing.

## Bugs Found

None.

## TODOs for Developer

None.

## Verdict

**PASS — mark WP as Done**
