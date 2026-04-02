# Dev Log — SAF-070: Regression tests for terminal bypass scenarios

**Agent:** Developer Agent  
**Branch:** SAF-070/regression-tests-bypasses  
**Date Started:** 2026-04-02  
**Status:** In Progress

---

## Requirements Summary

Write comprehensive regression tests covering all bypass scenarios from the security-hook-report. These tests verify that fixes from SAF-068 (unquoted Windows path bypass) and SAF-069 (env-var exfiltration bypass) continue to work and do not regress.

**User Story:** US-074  
**Depends On:** SAF-068 (done), SAF-069 (done)

---

## Acceptance Criteria

- All bypass scenarios from the security-hook-report have passing regression tests
- No regressions in existing SAF test suite
- Tests cover all 12 deny scenarios and 3 allow scenarios listed in WP requirements

---

## Implementation

### Files Created

- `tests/SAF-070/__init__.py` — package marker
- `tests/SAF-070/test_saf070.py` — 15 regression tests covering all bypass scenarios

### Test Coverage

**Windows Path Bypass Tests (SAF-068 fixes):**
- T01: `Get-Content C:\Users\angel\secret.txt` (unquoted) → deny
- T02: `Get-ChildItem C:\Users` (unquoted) → deny
- T03: `Get-Content C:\path\to\NoAgentZone\file.txt` (unquoted, denied zone) → deny
- T04: `Select-String -Path C:\Users\angel\file.txt -Pattern secret` (unquoted flag path) → deny
- T05: `type C:\Windows\System32\drivers\etc\hosts` (unquoted system file) → deny
- T06: `cat C:\Users\angel\.ssh\id_rsa` (unquoted SSH key) → deny

**Environment Variable Exfiltration Tests (SAF-069 fixes):**
- T07: `Write-Output $env:USERNAME` → deny
- T08: `echo $env:GITHUB_TOKEN` → deny
- T09: `Write-Host $env:PATH` → deny
- T10: `write-output $ENV:SECRET` (case-insensitive) → deny
- T11: `echo ${env:USERNAME}` (brace syntax) → deny
- T12: `echo ${ENV:SECRET}` (brace syntax, case-insensitive) → deny

**Allow Scenarios (no regression):**
- T13: `echo "hello world"` → allow
- T14: `echo price is 5 dollars` → allow
- T15: `Get-Content ./project-file.txt` (relative path in workspace) → allow

---

## Test Results

See `docs/test-results/test-results.csv` for logged results.

---

## Notes

- Import path uses the standard SCRIPTS_DIR pattern from SAF-068/SAF-069 tests
- `ws_root` is a temp directory for deny tests (paths outside ws_root trigger deny)
- For T15 (allow), temp dir is used and the referenced file is created inside it
- Return signature: `("allow", None)` or `("deny", str_reason)`
