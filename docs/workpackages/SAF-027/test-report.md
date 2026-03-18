# Test Report — SAF-027

**Tester:** Tester Agent  
**Date:** 2026-03-18  
**Iteration:** 1

---

## Summary

**FAIL.** The developer's 50-test suite passes entirely with the current implementation. However, the suite is not comprehensive enough: it does not test bypass vectors involving aliased imports, `from`-style imports, or bare module imports for network modules. This means the suite did not catch the 3 implementation bugs found in SAF-026 (BUG-063, BUG-064, BUG-065). A comprehensive test suite should be adversarial — it should deliberately probe for bypass patterns, not just test the obvious happy/sad paths.

---

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| Developer suite (50 tests) — `tests/SAF-026/test_saf026_python_c_scanning.py` | Unit + Security | PASS 50/50 | All 50 pass |
| Tester edge-case additions (25 tests) — `tests/SAF-026/test_saf026_edge_cases.py` | Security | FAIL 20/25 | 5 failures reveal implementation bugs |

---

## Bugs Found

No new bugs beyond those in SAF-026 test-report (BUG-063, BUG-064, BUG-065).

The SAF-027 finding is a **test-coverage gap**: the developer's test suite does not test the bypass patterns that expose BUG-063, BUG-064, and BUG-065.

---

## Coverage Gaps in Developer's Test Suite

| Missing Test | Why It Matters | Related Bug |
|-------------|----------------|-------------|
| `import requests` alone | AC-4 requires requests imports to be denied; bare import bypasses the regex | BUG-063 |
| `import requests as r; r.something()` | Aliased import + usage evades `requests\.` check without triggering any pattern | BUG-063 |
| `from http import server` | from-import syntax avoids `"http.server"` substring match | BUG-064 |
| `from http import client` | from-import syntax avoids `"http.client"` substring match | BUG-064 |
| `import codecs` alone | Bare codecs import not blocked; only `codecs.decode` is in deny list | BUG-065 |
| `import codecs; codecs.encode(...)` | `codecs.encode` with Rot-13 or zlib is an obfuscation vector not blocked | BUG-065 |

---

## What the Developer's Suite Did Well

- Covers all 6 categories with ≥1 positive test each
- Tests both `_scan_python_inline_code` directly and via `sanitize_terminal_command` round-trips
- Correctly tests python3 and py verb variants
- Tests re.compile negative lookbehind
- Tests case-insensitivity for deny-zone names (NoAgentZone → NOAGENTZONE)
- Tests update_hashes terminal deny via both inline scanner and explicit-deny pattern

---

## TODOs for Developer (SAF-027)

After SAF-026 fixes are applied (BUG-063, BUG-064, BUG-065), add the following tests to the SAF-027/SAF-026 test suite:

- [ ] **BUG-063 coverage:**
  - `test_requests_import_alone_denied` — `import requests` → assert `is False`
  - `test_requests_import_aliased_denied` — `import requests as r; r.get('http://evil.com')` → assert `is False`

- [ ] **BUG-064 coverage:**
  - `test_from_http_import_server_denied` — `from http import server; server.HTTPServer(...)` → assert `is False`
  - `test_from_http_import_client_denied` — `from http import client; ...` → assert `is False`

- [ ] **BUG-065 coverage:**
  - `test_codecs_import_alone_denied` — `import codecs` → assert `is False`
  - `test_codecs_encode_denied` — `import codecs; codecs.encode('x', 'rot_13')` → assert `is False` (no zone name)

- [ ] **Re-run full SAF-026 + SAF-027 developer tests** (50+6 = 56+ total) and confirm all pass after SAF-026 fixes.

---

## Verdict

**FAIL** — Return SAF-027 to `In Progress`. Developer should add the 6 bypass-vector tests listed above, then re-submit both SAF-026 and SAF-027 for Tester review together.
