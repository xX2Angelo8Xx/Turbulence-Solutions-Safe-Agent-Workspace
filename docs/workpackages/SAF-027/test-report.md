# Test Report — SAF-027

**Tester:** Tester Agent  
**Date:** 2026-03-18  
**Iteration:** 2 (Re-test after BUG-063, BUG-064, BUG-065 fixes)

---

## Summary

**PASS.** The developer added 6 bug-regression tests covering BUG-063, BUG-064, and BUG-065 bypass vectors, exactly as specified in the Iteration 1 TODOs. Combined with the original 50 developer tests and the 25 Tester edge-case tests, all 81 tests pass. Coverage is now adversarial: the suite tests aliased imports, from-import patterns, and bare module imports for all network and obfuscation categories.

---

## Iteration 1 Summary (Historical)

**FAIL.** The developer's 50-test suite passed entirely with the then-current (buggy) implementation. However, the suite was not comprehensive enough: it did not test bypass vectors involving aliased imports, `from`-style imports, or bare module imports for network modules. This meant the suite did not catch the 3 implementation bugs found in SAF-026 (BUG-063, BUG-064, BUG-065).

---

## Iteration 2 — Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| Developer original suite (50 tests) — `tests/SAF-026/test_saf026_python_c_scanning.py` | Unit + Security | PASS 50/50 | All original tests pass |
| Developer bug-regression tests (6 new) — `tests/SAF-026/test_saf026_python_c_scanning.py` | Regression | PASS 6/6 | Exactly the tests requested in Iteration 1 TODOs |
| Tester edge-case additions (25 tests) — `tests/SAF-026/test_saf026_edge_cases.py` | Security | PASS 25/25 | All 5 previously-failing bypass tests now pass |
| **Total** | | **81/81 PASS** | |

---

## Iteration 2 — Coverage Gap Closure

| Previously Missing Test | Added By | Status |
|------------------------|---------|--------|
| `test_requests_import_alone_denied` | Developer (regression) | PASS ✓ |
| `test_requests_aliased_denied` | Developer (regression) | PASS ✓ |
| `test_from_http_import_server_denied` | Developer (regression) | PASS ✓ |
| `test_from_http_import_client_denied` | Developer (regression) | PASS ✓ |
| `test_codecs_import_alone_denied` | Developer (regression) | PASS ✓ |
| `test_codecs_encode_denied` | Developer (regression) | PASS ✓ |

---

## Iteration 1 — Tests Executed (Historical)

| Test | Type | Result | Notes |
|------|------|--------|-------|
| Developer suite (50 tests) — `tests/SAF-026/test_saf026_python_c_scanning.py` | Unit + Security | PASS 50/50 | All 50 pass |
| Tester edge-case additions (25 tests) — `tests/SAF-026/test_saf026_edge_cases.py` | Security | FAIL 20/25 | 5 failures reveal implementation bugs |

---

## Bugs Found

No new bugs beyond those in SAF-026 test-report (BUG-063, BUG-064, BUG-065).

The SAF-027 Iteration 1 finding was a **test-coverage gap**: the developer's test suite did not test the bypass patterns that expose BUG-063, BUG-064, and BUG-065.

---

## Previously Coverage Gaps (Iteration 1) — Now Closed

| Missing Test | Why It Matters | Related Bug | Status |
|-------------|----------------|-------------|--------|
| `import requests` alone | AC-4 requires requests imports to be denied; bare import bypassed the regex | BUG-063 | ✓ Fixed |
| `import requests as r; r.something()` | Aliased import + usage evaded `requests\.` check | BUG-063 | ✓ Fixed |
| `from http import server` | from-import syntax avoided `"http.server"` substring match | BUG-064 | ✓ Fixed |
| `from http import client` | from-import syntax avoided `"http.client"` substring match | BUG-064 | ✓ Fixed |
| `import codecs` alone | Bare codecs import not blocked; only `codecs.decode` was in deny list | BUG-065 | ✓ Fixed |
| `import codecs; codecs.encode(...)` | `codecs.encode` with Rot-13 was an obfuscation vector not blocked | BUG-065 | ✓ Fixed |

---

## What the Developer's Suite Does Well

- Covers all 6 categories with ≥1 positive test each
- Tests both `_scan_python_inline_code` directly and via `sanitize_terminal_command` round-trips
- Correctly tests python3 and py verb variants
- Tests re.compile negative lookbehind
- Tests case-insensitivity for deny-zone names (NoAgentZone → NOAGENTZONE)
- Tests update_hashes terminal deny via both inline scanner and explicit-deny pattern
- Now adversarially tests aliased imports, from-import patterns, and bare module imports

---

## Iteration 1 TODOs — Completed

- [x] `test_requests_import_alone_denied` — added by developer ✓
- [x] `test_requests_import_aliased_denied` — added by developer ✓
- [x] `test_from_http_import_server_denied` — added by developer ✓
- [x] `test_from_http_import_client_denied` — added by developer ✓
- [x] `test_codecs_import_alone_denied` — added by developer ✓
- [x] `test_codecs_encode_denied` — added by developer ✓
- [x] Re-run full SAF-026 + SAF-027 developer tests (56 total pass) ✓

---

## Verdict

**PASS (Iteration 2)** — All 81 tests pass. The SAF-027 test suite now has comprehensive bypass-vector coverage. SAF-027 set to `Done`.
