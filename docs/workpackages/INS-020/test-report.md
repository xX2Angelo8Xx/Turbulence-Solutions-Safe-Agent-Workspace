# Test Report — INS-020

**Tester:** Tester Agent  
**Date:** 2026-03-19  
**Verdict:** PASS

## Summary

INS-020 updates `templates/coding/.github/hooks/require-approval.json` to use `ts-python` instead of bare `python` for the security gate hook command. This ensures created workspaces use the bundled Python runtime via the shim.

## Test Results

- **INS-020 tests:** 15/15 passed (8 developer + 7 Tester edge-case)
- **Regressions:** None

## Edge-Case Tests Added

- File encoding (no BOM)
- command and windows fields are identical
- PreToolUse has exactly one hook
- ts-python command is lowercase
- No trailing whitespace in command fields
- Hook has all required fields
- Hook has no unexpected fields

## Checklist

- [x] dev-log.md exists
- [x] test-report.md written
- [x] Tests in tests/INS-020/
- [x] Test results logged in test-results.csv
- [x] No temp files remain
