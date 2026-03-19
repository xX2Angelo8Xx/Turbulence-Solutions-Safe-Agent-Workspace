# Test Report — SAF-026

**Tester:** Tester Agent  
**Date:** 2026-03-18  
**Iteration:** 2 (Re-test after BUG-063, BUG-064, BUG-065 fixes)

---

## Summary

**PASS.** All 3 bugs identified in Iteration 1 have been correctly fixed. All 81 tests pass (50 original developer tests + 6 new bug-regression tests added by developer + 25 Tester edge-case tests). The 5 previously-failing bypass-vector tests now all return `False` (DENIED) as required. All SAF-017 regressions are clean. The full suite shows only pre-existing failures (FIX-009 encoding corruption, INS-005 BUG-045, SAF-028 unimplemented) — none caused by SAF-026 changes.

---

## Iteration 1 Summary (Historical)

**FAIL.** The `_scan_python_inline_code()` implementation passed the developer's 50 tests but contained 3 bypass vulnerabilities in Category B (obfuscation) and Category C (network). Tester edge-case tests revealed that `import requests` without a method call, aliased requests imports, `from http import server/client`, and bare `import codecs` all bypassed the scanner. These violated acceptance criteria AC-3 and AC-4 of US-027.

---

## Iteration 2 — Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| Developer suite (50 tests) — `tests/SAF-026/test_saf026_python_c_scanning.py` | Unit + Security | PASS 50/50 | All original developer tests pass |
| Developer bug-regression tests (6 new) — `tests/SAF-026/test_saf026_python_c_scanning.py` | Regression | PASS 6/6 | BUG-063/064/065 regression tests (requests alone, aliased requests, from http import server, from http import client, codecs alone, codecs.encode) |
| Tester edge-case suite (25 tests) — `tests/SAF-026/test_saf026_edge_cases.py` | Security | PASS 25/25 | All 5 previously-failing bypass tests now pass |
| SAF-017 regression (74 tests) | Regression | PASS 74/74 | No regressions from SAF-026 pattern changes |
| Full suite regression | Regression | PASS (effectively) | 3435 passed / 15 pre-existing only / 29 skipped / 1 xfailed — 0 new SAF-026 failures |

---

## Iteration 2 — Bug Fix Verification

| Bug | Fix Applied | Verification |
|-----|-------------|--------------|
| BUG-063 (requests regex) | `\brequests\.` → `\brequests\b` in `_scan_python_inline_code()` | `test_requests_import_alone_denied` PASS; `test_requests_import_aliased_denied` PASS |
| BUG-064 (http from-import) | Added `"http"` to Category C net list (replacing only `"http.client"` and `"http.server"`) | `test_from_http_import_server_denied` PASS; `test_from_http_import_client_denied` PASS |
| BUG-065 (bare codecs) | Changed `"codecs.decode"` → `"codecs"` in Category B pattern list | `test_codecs_import_alone_denied` PASS; `test_codecs_encode_rot13_denied` PASS |

Both `Default-Project/.github/hooks/scripts/security_gate.py` and `templates/coding/.github/hooks/scripts/security_gate.py` contain identical fixes.

---

## Previously Iteration 1 — Bugs Found

- **BUG-063**: `import requests` bypassed Category C scanner — `\brequests\.` regex required a dot; bare import and aliased imports were allowed  
- **BUG-064**: `from http import server` / `from http import client` bypassed Category C scanner — substring `"http.server"` / `"http.client"` not matched by from-import syntax  
- **BUG-065**: `import codecs` alone bypassed Category B scanner — only `"codecs.decode"` was in the deny list; bare codecs import and `codecs.encode` were not blocked  

All three were logged in `docs/bugs/bugs.csv`. All three are now fixed.

---

## Previously Iteration 1 — Failing Tests (Now Fixed)

| Test Name | Root Cause (Fixed) | Bug |
|-----------|-----------|-----|
| `test_requests_import_alone_denied` | `re.search(r'\brequests\.', low)` missed bare `import requests` | BUG-063 ✓ |
| `test_requests_import_aliased_denied` | Aliased use `import requests as r; r.get(...)` had no `requests.` | BUG-063 ✓ |
| `test_from_http_import_server_denied` | `"http.server"` not a substring of `"from http import server"` | BUG-064 ✓ |
| `test_from_http_import_client_denied` | `"http.client"` not a substring of `"from http import client"` | BUG-064 ✓ |
| `test_codecs_import_alone_denied` | Only `"codecs.decode"` checked; bare `import codecs` was allowed | BUG-065 ✓ |

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

- [x] **Fix BUG-063 (requests):** DONE — `re.search(r'\brequests\b', low)` 

- [x] **Fix BUG-064 (http from-import):** DONE — `"http"` added to Category C net list  

- [x] **Fix BUG-065 (codecs):** DONE — `"codecs"` replaces `"codecs.decode"` in Category B  

- [x] **After fixing:** `update_hashes.py` run; `_KNOWN_GOOD_GATE_HASH` updated.

- [x] **After fixing:** `templates/coding/.github/hooks/scripts/security_gate.py` synced with Default-Project.

- [x] **Re-run full test suite:** (a) all 50 developer tests pass ✓, (b) all 25 Tester edge-case tests pass ✓, (c) no new regressions ✓

---

## Known Limitations (Acceptable, Not Blocking)

- **Unicode homoglyphs**: `bаse64` with Cyrillic 'а' (U+0430) bypasses the `base64` check. The Python `import` itself would fail at runtime (no such module), so this is an acceptable limitation of string-matching approaches. Documented in `test_unicode_homoglyph_base64_is_limitation`.

- **String concatenation**: `"NoAgent" + "Zone"` doesn't produce the literal substring `noagentzone`. Acceptable limitation — this requires dynamic analysis (beyond scope). Documented in `test_ospath_join_concatenation_limitation`.

---

## Verdict

**PASS (Iteration 2)** — All 81 tests pass. BUG-063, BUG-064, and BUG-065 are verified fixed. SAF-026 set to `Done`.
