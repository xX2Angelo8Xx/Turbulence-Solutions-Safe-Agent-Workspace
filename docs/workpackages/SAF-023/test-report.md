# Test Report — SAF-023: Block get_errors for Restricted Zone Paths

**Tester:** Tester Agent  
**Date:** 2026-03-17  
**Branch:** `SAF-023/get-errors-blocking`  
**Verdict:** PASS

---

## 1. Implementation Review

### Files Changed
- `Default-Project/.github/hooks/scripts/security_gate.py` — primary implementation
- `templates/coding/.github/hooks/scripts/security_gate.py` — sync copy
- `docs/workpackages/workpackages.csv` — status update
- `docs/test-results/test-results.csv` — test log

### `_EXEMPT_TOOLS`
`"get_errors"` is present in `_EXEMPT_TOOLS` (line 39). This is correct: it passes the
unknown-tool deny guard while still being intercepted by the early dispatch in `decide()`.

### `validate_get_errors()` (lines 1597–1638)
Logic verified against WP description:

| Condition | Expected | Actual |
|-----------|----------|--------|
| `filePaths` absent | allow | allow ✓ |
| `filePaths = None` | allow | allow ✓ |
| `filePaths = []` | allow | allow ✓ |
| `filePaths` is a non-list type | deny (fail closed) | deny ✓ |
| Element is non-string or empty string | deny (fail closed) | deny ✓ |
| Element is None inside list | deny | deny ✓ |
| Path in "deny" zone (.github, .vscode, NoAgentZone) | deny | deny ✓ |
| Path in project folder (allow zone) | allow | allow ✓ |
| Mixed: project + restricted | deny | deny ✓ |
| Path traversal resolved to deny zone | deny | deny ✓ |
| VS Code hook nested `tool_input.filePaths` format | correct | correct ✓ |
| Flat `filePaths` format (fallback) | correct | correct ✓ |

### `decide()` dispatch (lines 1743–1747)
`get_errors` is dispatched BEFORE the `_EXEMPT_TOOLS` fallback block, matching the
established pattern for `grep_search` and other special-case tools. Correct.

### Hash Update
`_KNOWN_GOOD_GATE_HASH` was updated after implementation. Integrity check passes.

### Dev-log Discrepancy (documentation only)
The dev-log decision notes state "Zone 'ask' paths → deny" but the code only denies
`zone == "deny"`. This is **correct behaviour** per the WP description ("block for
restricted zone paths"). The "ask" zone (e.g. `docs/`) is not a restricted zone.
The dev-log note is a documentation inaccuracy, not a code bug.

---

## 2. Test Results

### Developer Suite — 34 tests
All 34 tests across 5 classes (Unit, Security, Bypass, Cross-platform, Integration) passed.

| Class | Count | Result |
|-------|-------|--------|
| `TestValidateGetErrors` (Unit) | 14 | 14/14 PASS |
| `TestDecideGetErrors` (Security) | 6 | 6/6 PASS |
| `TestBypassAttempts` (Bypass) | 6 | 6/6 PASS |
| `TestCrossPlatform` (Cross-platform) | 4 | 4/4 PASS |
| `TestIntegration` (Integration) | 4 | 4/4 PASS |

### Tester Edge Cases — 10 tests (TST-1475 to TST-1484)
All 10 edge-case tests added by the Tester passed.

| Test | Category | Result |
|------|----------|--------|
| `test_folder_path_to_github_deny` | Unit | PASS |
| `test_folder_path_to_noagentzone_deny` | Unit | PASS |
| `test_unicode_path_in_project_allow` | Unit | PASS |
| `test_unicode_path_to_noagentzone_deny` | Unit | PASS |
| `test_large_array_all_project_allow` | Unit | PASS |
| `test_large_array_last_element_restricted_deny` | Security | PASS |
| `test_dict_as_file_paths_deny` | Security | PASS |
| `test_boolean_element_in_paths_deny` | Security | PASS |
| `test_deep_traversal_to_vscode_deny` | Security | PASS |
| `test_mixed_project_and_vscode_deny` | Security | PASS |

### Full Regression Suite
```
2940 passed, 1 failed (pre-existing), 29 skipped
```
The 1 failed test is `tests/INS-005/test_ins005_edge_cases.py::TestShortcutsAndUninstaller::test_uninstall_delete_type_is_filesandirs`.
This failure is **pre-existing** on the main branch (confirmed by testing on the
base commit `6bf6784`) and is unrelated to SAF-023. It is a test-vs-installer-script
mismatch in an unrelated WP. Already tracked as a known issue.

---

## 3. Security Analysis

### Attack Vectors Tested
1. **Path traversal via `..`** — Developer tested two variants (TST-1459, TST-1460).
   Tester added a four-level ascending traversal (TST-1483). Both are blocked because
   `zone_classifier.normalize_path()` resolves `..` via `posixpath.normpath` before
   any zone check.

2. **Non-list `filePaths` injection** — String, integer, dict (TST-1450, TST-1451,
   TST-1481). All denied via `isinstance(file_paths, list)` check.

3. **Non-string elements inside the list** — None (TST-1462), empty string (TST-1461),
   boolean (TST-1482). All denied via `isinstance(path, str) or not path` check.

4. **Large array with restricted tail** — 999 valid + 1 restricted (TST-1480). Denied
   because the loop does not short-circuit on allow; ALL elements are checked.

5. **Folder-only paths** (no filename) — `.github` and `NoAgentZone` directories
   themselves (TST-1475, TST-1476). Correctly denied by Method 1 (first segment in
   `_DENY_DIRS`).

6. **Unicode path bypass** — Unicode characters do not affect zone classification;
   `normalize_path()` lowercases them (TST-1477, TST-1478).

7. **Malformed `tool_input`** — Non-dict `tool_input` falls back to top-level
   `filePaths` lookup (TST-1464). Correct.

8. **Mixed allowed/restricted arrays** — Multiple variants tested (TST-1449, TST-1463,
   TST-1480, TST-1484). Deny-on-any logic confirmed.

### Boundary Conditions
- Empty array → allow (correct: VS Code handles scope)
- `filePaths: null` (JSON null → Python None) → allow (treated as absent)
- 1000-element homogeneous array → allow (performance: completes without issue)

### No New Vulnerabilities Found

---

## 4. Bugs Logged

No new bugs. All tested behaviours are correct.

---

## 5. Verdict

**PASS** — SAF-023 implementation is complete, correct, and secure.

All WP acceptance criteria are satisfied:
- ✅ `get_errors` is added to `_EXEMPT_TOOLS`
- ✅ `validate_get_errors()` zone-checks the `filePaths` array
- ✅ Restricted zone paths → deny
- ✅ Empty / absent `filePaths` → allow
- ✅ Invalid `filePaths` type → deny (fail closed)
- ✅ Early dispatch in `decide()` before the exempt-tools fallback
- ✅ 44 tests passing (34 Developer + 10 Tester)
- ✅ Full regression suite: no new failures
