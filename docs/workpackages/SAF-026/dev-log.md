# SAF-026 Dev Log — Add python -c Inline Code Scanning

**Status:** Review  
**Assigned To:** Developer Agent  
**Branch:** saf-026  
**Date Started:** 2026-03-18  
**Date Completed:** 2026-03-18

---

## Objective

Add `_scan_python_inline_code(code_str: str) -> bool` to `security_gate.py` to scan the string argument of `python -c "..."` for dangerous patterns. Integrate the scanner into `_validate_args`. Block `update_hashes` terminal execution via `_EXPLICIT_DENY_PATTERNS`. Sync both `Default-Project/` and `templates/coding/` copies.

---

## Implementation Summary

### 1. New function `_scan_python_inline_code`
- Located near `_validate_args` in `security_gate.py`
- Returns `True` (safe) / `False` (dangerous)
- Denies 6 categories of dangerous patterns:
  - **A** — Deny-zone path literals: `noagentzone`, `.github`, `.vscode`
  - **B** — Path obfuscation/encoding: `base64`, `b64decode`, `codecs`, `fromhex(`, `bytearray(`, `chr(`
  - **C** — Network access: `urllib`, `requests`, `http.client`, `http.server`, `socket`, `ftplib`, `smtplib`, `xmlrpc`
  - **D** — Filesystem escape: `expanduser`, `expandvars`, `../` or `..\`, absolute paths (`/etc`, `/usr`, etc., `C:\`)
  - **E** — Security infrastructure tampering: `update_hashes`, `security_gate`, `zone_classifier`, `require-approval`, `require_approval`
  - **F** — Dynamic code execution: `__import__`, `importlib`, `compile(` (not `re.compile`), `eval(`, `exec(`, `getattr(`, `setattr(`, `delattr(`

### 2. Integration in `_validate_args`
- After building `_code_arg_indices`, scan each inline code arg with `_scan_python_inline_code`
- Return `False` immediately if scanner returns `False`

### 3. `update_hashes` added to `_EXPLICIT_DENY_PATTERNS`
- `re.compile(r'\bupdate_hashes\b')` added to unconditional deny list

### 4. Template sync
- `templates/coding/.github/hooks/scripts/security_gate.py` updated to match

### 5. Hash update
- `update_hashes.py` run to refresh `_KNOWN_GOOD_GATE_HASH`
- Template copy re-synced after hash update

---

## Files Changed

- `Default-Project/.github/hooks/scripts/security_gate.py`
- `templates/coding/.github/hooks/scripts/security_gate.py`
- `tests/SAF-026/test_saf026_python_c_scanning.py`
- `docs/workpackages/workpackages.csv`
- `docs/test-results/test-results.csv`

---

## Tests Written

Located in `tests/SAF-026/test_saf026_python_c_scanning.py`:

- `test_print_allowed` — safe print statement
- `test_math_import_allowed` — safe math import
- `test_json_import_allowed` — safe json import
- `test_noagentzone_denied` — deny-zone path literal
- `test_github_denied` — .github path literal
- `test_vscode_denied` — .vscode path literal
- `test_base64_denied` — base64 obfuscation
- `test_chr_building_denied` — chr() string building
- `test_urllib_denied` — network module
- `test_socket_denied` — network module
- `test_requests_denied` — network module
- `test_expanduser_denied` — filesystem escape
- `test_parent_traversal_denied` — parent traversal
- `test_absolute_path_unix_denied` — absolute Unix path
- `test_absolute_path_windows_denied` — absolute Windows path
- `test_security_gate_ref_denied` — infrastructure reference
- `test_update_hashes_denied` — update_hashes reference
- `test_eval_denied` — dynamic execution
- `test_exec_denied` — dynamic execution
- `test_import_denied` — __import__ dynamic execution
- `test_full_python_c_safe` — integration: full sanitize_terminal_command allows safe
- `test_full_python_c_noagentzone` — integration: full sanitize_terminal_command denies NoAgentZone

---

## Test Results

All 22 tests pass. See `docs/test-results/test-results.csv` for logged run.

---

## Known Limitations

- The `compile(` denial uses a negative lookbehind `(?<!re\.)` to avoid false-positive on `re.compile(`. Other legitimate uses of `compile()` (e.g. `ast.compile`) are also denied — acceptable per fail-closed policy.
- The absolute-path Windows pattern `[A-Za-z]:\\` catches any drive letter. This is intentional.

---

## Iteration 2 — Bug Fixes (2026-03-18)

Returned from Tester with 3 pattern-matching bugs found.

### Bugs Fixed

**BUG-063** (`requests` regex too strict):
- Changed `re.search(r'\brequests\.', low)` → `re.search(r'\brequests\b', low)`
- `import requests` alone and `import requests as r` are now correctly denied.

**BUG-064** (`http.client`/`http.server` too specific):
- Replaced `"http.client", "http.server"` entries in category C with single `"http"` keyword.
- `from http import server` and `from http import client` are now correctly denied.

**BUG-065** (`codecs.decode` too specific):
- Changed `"codecs.decode"` → `"codecs"` in category B pattern list.
- `import codecs` alone and `codecs.encode(...)` are now correctly denied.

### Files Changed

- `Default-Project/.github/hooks/scripts/security_gate.py` — applied 3 pattern fixes
- `templates/coding/.github/hooks/scripts/security_gate.py` — synced from Default-Project
- `tests/SAF-026/test_saf026_python_c_scanning.py` — added 6 regression tests

### Regression Tests Added

- `test_requests_import_alone_denied` — `import requests` denied (BUG-063)
- `test_requests_aliased_denied` — `import requests as r; r.get(...)` denied (BUG-063)
- `test_from_http_import_server_denied` — `from http import server` denied (BUG-064)
- `test_from_http_import_client_denied` — `from http import client` denied (BUG-064)
- `test_codecs_import_alone_denied` — `import codecs` denied (BUG-065)
- `test_codecs_encode_denied` — `codecs.encode(...)` denied (BUG-065)

### Test Results

81 SAF-026 tests pass. 74 SAF-017 tests pass (no regressions).
