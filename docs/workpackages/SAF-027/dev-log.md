# SAF-027 Dev Log — Tests for python -c Inline Code Scanning

**Status:** Review  
**Assigned To:** Developer Agent  
**Branch:** saf-026/add-python-c-scanning  
**Date Started:** 2026-03-18  
**Date Completed:** 2026-03-18

---

## Objective

Write comprehensive tests for `_scan_python_inline_code` covering all 8 denial categories and safe-code allowance, as specified in SAF-027.

---

## Implementation Summary

SAF-027 is co-delivered with SAF-026. The test deliverable is the file:

```
tests/SAF-026/test_saf026_python_c_scanning.py
```

This file contains 50 tests covering:

1. **Safe code allowed** — `print()`, `math`, `json`, `sys`, `re.compile` allowed
2. **Deny-zone paths denied** — `NoAgentZone`, `.github`, `.vscode` (case-insensitive)
3. **Base64 / encoding obfuscation denied** — `base64`, `b64decode`, `codecs`, `fromhex`, `bytearray`, `chr`
4. **Network modules denied** — `urllib`, `socket`, `requests`, `http.client`, `ftplib`, `smtplib`, `xmlrpc`
5. **Filesystem escape denied** — `expanduser`, `expandvars`, `../`, `..\`, absolute Unix and Windows paths
6. **Infrastructure reference denied** — `security_gate`, `update_hashes`, `zone_classifier`, `require-approval`, `require_approval`
7. **Dynamic code execution denied** — `eval(`, `exec(`, `__import__`, `importlib`, `compile(`, `getattr(`, `setattr(`, `delattr(`
8. **Parent traversal denied** — forward and backslash variants
9. **Integration tests** — full `sanitize_terminal_command` round-trip for python, python3, py

---

## Files

- Test file: `tests/SAF-026/test_saf026_python_c_scanning.py` (50 tests)
- `__init__.py`: `tests/SAF-026/__init__.py`

---

## Test Results

All 50 tests pass. Run: `.venv\Scripts\python -m pytest tests/SAF-026/ -v`
