# SAF-038 Test Report

**WP ID:** SAF-038  
**Name:** Allow memory and create_directory in project  
**Tester:** Tester Agent  
**Date:** 2026-03-24  
**Branch:** SAF-038/memory-create-directory  
**Verdict:** PASS  

---

## Summary

The implementation correctly enforces project-folder zone restrictions for the `memory` and `create_directory` tools. Both tools are dispatched before the `_EXEMPT_TOOLS` fallback in `decide()`, use dedicated validation functions, and fail closed when no valid path is present. All 71 developer tests pass. All 37 tester edge-case tests pass. No regressions in 1920 SAF-suite tests.

---

## Review Findings

### Code Review — `security_gate.py`

| Item | Verdict |
|------|---------|
| Both tools added to `_EXEMPT_TOOLS` | ✅ Correct — present at line ~45 with SAF-038 comment |
| `validate_memory()` dispatched before `_EXEMPT_TOOLS` fallback | ✅ Correct — line ~2361 in `decide()` |
| `validate_create_directory()` dispatched before `_EXEMPT_TOOLS` fallback | ✅ Correct — line ~2366 in `decide()` |
| `validate_memory()` extracts path from `tool_input.filePath` first | ✅ Correct — nested VS Code hook format preferred |
| Fallback to top-level `filePath`, then `path` | ✅ Correct |
| Fail-closed when no path found | ✅ Returns "deny" |
| Zone-check via `zone_classifier.classify()` | ✅ Correct |
| Blocks `.git` internals even inside project folder | ✅ Correct — `is_git_internals()` check |
| `validate_create_directory()` uses `dirPath` key only | ✅ Correct — `filePath` is not accepted |
| Null byte handling | ✅ Delegated to `zone_classifier.normalize_path()` which strips all C0 chars |
| Path traversal (`../`) handling | ✅ Handled by `posixpath.normpath` inside `normalize_path()` |
| Case handling (Windows paths) | ✅ `normalize_path()` lowercases everything |
| Non-string `tool_input` values | ✅ Guarded with `isinstance(tool_input, dict)` check |

**No security gaps found.**

---

## Test Results

### Developer Tests

| Test File | Type | Result | Tests |
|-----------|------|--------|-------|
| `test_saf038_memory_create_directory.py` | Unit + Security | ✅ Pass | 71 / 71 |

Test result ID: TST-2039

**Coverage by class:**
- `TestValidateMemory` (17 tests) — allow/deny/traversal for `validate_memory()`
- `TestValidateCreateDirectory` (19 tests) — allow/deny/traversal for `validate_create_directory()`
- `TestDecideMemory` (8 tests) — `decide()` dispatch for memory
- `TestDecideCreateDirectory` (8 tests) — `decide()` dispatch for create_directory
- `TestBypassAttempts` (11 tests) — adversarial payloads
- `TestCrossPlatform` (8 tests) — Windows/POSIX/backslash paths

### Tester Edge-Case Tests

| Test File | Type | Result | Tests |
|-----------|------|--------|-------|
| `test_saf038_edge_cases.py` | Security | ✅ Pass | 37 / 37 |

Test result ID: TST-2040

**Coverage by class:**
- `TestNullByteInjection` (6) — `\x00` in path strings, both traversal and benign cases
- `TestControlCharacterInjection` (3) — tab/newline/CR before deny-zone segments (BUG-010 regression)
- `TestMixedCaseToolNames` (5) — `Memory`, `MEMORY`, `CREATE_DIRECTORY`, `Create_Directory` are all denied
- `TestUnicodePaths` (5) — accented chars, CJK inside project (allow); outside (deny)
- `TestWhitespaceOnlyPaths` (4) — space-only and newline-only strings denied
- `TestWrongFieldUsage` (4) — `dirPath` in memory, `filePath` in create_directory
- `TestTraversalInsideProject` (2) — traversal sequences resolving back inside project → allow
- `TestRelativePaths` (6) — relative paths resolved against ws_root (by-design behavior)
- `TestNestedListInput` (2) — `tool_input` as list → denied

### Regression Suite

| Scope | Result | Details |
|-------|--------|---------|
| SAF-001 through SAF-038 | ✅ Pass | 1920 passed, 1 pre-existing failure |

Test result ID: TST-2041

**Pre-existing failure:** `SAF-025::test_no_pycache_in_templates_coding` — fires whenever any test imports `security_gate.py` directly from `templates/coding/.github/hooks/scripts/`. This is a pre-existing issue present before SAF-038 (confirmed by testing HEAD~1). It is NOT caused by SAF-038.

---

## Security Analysis

### Attack Vectors Verified

| Vector | Expected | Actual |
|--------|----------|--------|
| Path traversal: `project/../.github/` | deny | ✅ deny |
| Null byte injection: `\x00../../.github/` | deny | ✅ deny |
| Tab/newline before deny segment | deny | ✅ deny |
| Mixed case tool name: `Memory` | deny | ✅ deny (unknown tool) |
| No path provided | deny | ✅ deny (fail-closed) |
| Empty string path | deny | ✅ deny |
| Whitespace-only path | deny | ✅ deny |
| Wrong field key (`dirPath` for memory) | deny | ✅ deny |
| `tool_input` as non-dict (string, int, list, null) | deny | ✅ deny |
| `.git/` inside project folder | deny | ✅ deny |
| Unicode chars in project path | allow | ✅ allow |
| Traversal resolving back into project | allow | ✅ allow |
| Windows backslash paths | correct zone | ✅ correct |
| WSL `/mnt/c/` paths | correct zone | ✅ correct |

### Fail-Closed Behaviour Confirmed

Both `validate_memory()` and `validate_create_directory()` return `"deny"` in all ambiguous cases (no path, empty string, wrong key, malformed payload). No code path returns `"allow"` without a successful zone check.

### Mixed-Case Tool Names

The tool name matching is case-sensitive (e.g., `"Memory" != "memory"`). Uppercase/mixed-case variants fall through to the unknown-tool denial branch, which denies them. This is the correct secure default — the actual VS Code hook sends lowercase tool names, so this does not affect real usage.

---

## User Story AC Verification (US-035 ACs 1-2, 5-6)

> **Note:** US-035 is not yet present in `docs/user-stories/user-stories.csv`. The ACs were inferred from the WP goal and the described functionality.

| AC | Description | Status |
|----|-------------|--------|
| AC-1 | `memory` tool works inside project folder | ✅ Verified — allow paths confirmed |
| AC-2 | `memory` tool is denied outside project folder | ✅ Verified — deny paths confirmed |
| AC-5 | `create_directory` works inside project folder | ✅ Verified — allow paths confirmed |
| AC-6 | `create_directory` is denied outside project folder | ✅ Verified — deny paths confirmed |

---

## Bugs Found

No new bugs found during testing. The pre-existing `SAF-025::test_no_pycache_in_templates_coding` failure is an existing tracking issue.

---

## Verdict

**PASS**

The implementation is correct, secure, and complete. All ACs are satisfied. 108 tests pass (71 developer + 37 tester). No regressions. WP promoted to `Done`.
