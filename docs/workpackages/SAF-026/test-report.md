# Test Report — SAF-026

**Tester:** Tester Agent  
**Date:** 2026-03-18  
**Iteration:** 1

---

## Summary

**FAIL.** The `_scan_python_inline_code()` implementation passes the developer's 50 tests but contains 3 bypass vulnerabilities in Category B (obfuscation) and Category C (network). Tester edge-case tests revealed that `import requests` without a method call, aliased requests imports, `from http import server/client`, and bare `import codecs` all bypass the scanner. These violate acceptance criteria AC-3 and AC-4 of US-027.

---

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| Developer suite (50 tests) — `tests/SAF-026/test_saf026_python_c_scanning.py` | Unit + Security | PASS 50/50 | All developer tests pass |
| Tester edge-case suite (25 tests) — `tests/SAF-026/test_saf026_edge_cases.py` | Security | FAIL 20/25 | 5 failures: bypass vectors |
| SAF-017 regression (74 tests) | Regression | PASS 74/74 | No regressions from SAF-026 changes |
| Full suite regression (−SAF-028) | Regression | FAIL | 5 new failures from edge-case suite + 3 pre-existing (BUG-063, BUG-064, BUG-065 logged) |

---

## Bugs Found

- **BUG-063**: `import requests` bypasses Category C scanner — `\brequests\.` regex requires a dot; bare import and aliased imports allowed  
- **BUG-064**: `from http import server` / `from http import client` bypass Category C scanner — substring `"http.server"` / `"http.client"` not matched by from-import syntax  
- **BUG-065**: `import codecs` alone bypasses Category B scanner — only `"codecs.decode"` is in the deny list; bare codecs import and `codecs.encode` are not blocked  

All three are logged in `docs/bugs/bugs.csv`.

---

## Failing Tests

| Test Name | Root Cause | Bug |
|-----------|-----------|-----|
| `test_requests_import_alone_denied` | `re.search(r'\brequests\.', low)` misses bare `import requests` | BUG-063 |
| `test_requests_import_aliased_denied` | Aliased use `import requests as r; r.get(...)` has no `requests.` — not caught | BUG-063 |
| `test_from_http_import_server_denied` | `"http.server"` not a substring of `"from http import server"` | BUG-064 |
| `test_from_http_import_client_denied` | `"http.client"` not a substring of `"from http import client"` | BUG-064 |
| `test_codecs_import_alone_denied` | Only `"codecs.decode"` checked; bare `import codecs` allowed | BUG-065 |

---

## Evidence: Bypass Vectors

### BUG-063 — requests alias bypass
```python
# All three bypass the scanner (return True = safe, should return False = dangerous):
_scan_python_inline_code("import requests")                           # → True (bypass!)
_scan_python_inline_code("import requests as r; r.get('http://...')") # → True (bypass!)
```

### BUG-064 — from-import bypass for http modules
```python
_scan_python_inline_code("from http import server; server.HTTPServer(...)") # → True (bypass!)
_scan_python_inline_code("from http import client; c = client.HTTPConnection(...)") # → True (bypass!)
```

### BUG-065 — bare codecs import
```python
_scan_python_inline_code("import codecs")                                  # → True (bypass!)
_scan_python_inline_code("import codecs; codecs.encode('x', 'rot_13')")   # → True (bypass!)
```

---

## TODOs for Developer

- [ ] **Fix BUG-063 (requests):** Replace `re.search(r'\brequests\.', low)` with `re.search(r'\brequests\b', low)` or add `"requests"` to the Category C net list. Note: `"requirements"` does NOT contain `"requests"` as a substring, so plain string matching is safe. Also test: `import requests as r; r.get(...)` is now denied; `REQUIREMENTS_FILE = "..."` is allowed.

- [ ] **Fix BUG-064 (http from-import):** Add detection for from-import patterns. Simplest fix: add `"http"` to the net list OR add `re.search(r'\bhttp\b', low)`. `"http"` as a plain substring would also catch `"http://..."` URL strings in code — acceptable (fail-closed). Alternatively add explicit pattern: `re.search(r'(?:^|\s)(?:from|import)\s+http\b', low)`.

- [ ] **Fix BUG-065 (codecs):** Change `"codecs.decode"` to `"codecs"` in the Category B pattern list. `"codecs"` alone is a narrow enough token that false-positive risk is negligible.

- [ ] **After fixing:** Run `update_hashes.py` to refresh `_KNOWN_GOOD_GATE_HASH` in security_gate.py.

- [ ] **After fixing:** Sync `templates/coding/.github/hooks/scripts/security_gate.py` with Default-Project (byte-identical check must pass).

- [ ] **Re-run full test suite** and confirm: (a) all 50 developer tests still pass, (b) all 25 Tester edge-case tests now pass, (c) no new regressions.

---

## Known Limitations (Acceptable, Not Blocking)

- **Unicode homoglyphs**: `bаse64` with Cyrillic 'а' (U+0430) bypasses the `base64` check. The Python `import` itself would fail at runtime (no such module), so this is an acceptable limitation of string-matching approaches. Documented in `test_unicode_homoglyph_base64_is_limitation`.

- **String concatenation**: `"NoAgent" + "Zone"` doesn't produce the literal substring `noagentzone`. Acceptable limitation — this requires dynamic analysis (beyond scope). Documented in `test_ospath_join_concatenation_limitation`.

---

## Verdict

**FAIL** — Return SAF-026 to `In Progress`. Developer must fix BUG-063, BUG-064, and BUG-065, then re-submit for Tester review.
