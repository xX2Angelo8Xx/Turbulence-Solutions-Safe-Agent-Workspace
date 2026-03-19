# SAF-018 Test Report — Fix multi_replace_string_in_file Tool Recognition

**Tester:** Tester Agent  
**Date:** 2026-03-16  
**Branch:** `SAF-018/multi-replace-tool`  
**Verdict:** PASS

---

## 1. Review Summary

The Developer correctly identified that `multi_replace_string_in_file` was already present in both `_EXEMPT_TOOLS` and `_WRITE_TOOLS` but was silently denied by `validate_write_tool` because `extract_path()` does not inspect the nested `replacements` array. The implementation adds `validate_multi_replace_tool()` and routes `multi_replace_string_in_file` to it before the general `_WRITE_TOOLS` block in `decide()`.

**Changes reviewed:**
- `Default-Project/.github/hooks/scripts/security_gate.py` — new `validate_multi_replace_tool()`, updated `decide()` routing
- `templates/coding/.github/hooks/scripts/security_gate.py` — mirror updated identically (confirmed `validate_multi_replace_tool` present at line 1463)
- Hash in `_KNOWN_GOOD_GATE_HASH` updated to reflect new canonical form

**User story acceptance criteria (US-019):**
- ✅ `multi_replace_string_in_file` is in `_EXEMPT_TOOLS`
- ✅ `multi_replace_string_in_file` is in `_WRITE_TOOLS`
- ✅ ALL filePaths from the replacements array are extracted and zone-checked
- ✅ If ANY filePath is outside the project folder, the entire operation is denied
- ✅ Fails closed on empty, absent, or malformed replacements

---

## 2. Test Runs

### Run 1 — Developer test suite (TST-1385)
- **Command:** `.venv\Scripts\python -m pytest tests/SAF-018/test_saf018_multi_replace.py --tb=short -q`
- **Result:** 35 passed in 0.20 s
- **Logged:** TST-1385 in test-results.csv

### Run 2 — Full regression suite (TST-1386)
- **Command:** `.venv\Scripts\python -m pytest tests/ --tb=short -q`
- **Result:** 2629 passed / 1 pre-existing failure (INS-005) / 29 skipped
- **Pre-existing failure:** `tests/INS-005/test_ins005_edge_cases.py::TestShortcutsAndUninstaller::test_uninstall_delete_type_is_filesandirs` — unrelated to SAF-018
- **Logged:** TST-1386 in test-results.csv

### Run 3 — Tester edge-case suite (TST-1387)
- Initial run found 1 test incorrectly expecting the zone classifier to deny a path whose `..` segments only escaped to inside the project folder (not above the workspace root). Corrected traversal depth (5×`..` instead of 4×`..` to actually reach workspace-root `.github/`).
- **Command:** `.venv\Scripts\python -m pytest tests/SAF-018/ --tb=short -q`
- **Result:** 51 passed in 0.30 s
- **Logged:** TST-1387 in test-results.csv

---

## 3. Edge Cases Added (TST-1420 – TST-1435)

| Test ID | Description | Result |
|---------|-------------|--------|
| TST-1420 | 100-entry replacements array, all in Project/ | PASS (allow) |
| TST-1421 | 99 valid + 1 outside Project/ at end | PASS (deny) |
| TST-1422 | Unicode filePath inside Project/ | PASS (allow) |
| TST-1423 | Unicode filePath outside Project/ (`.github/`) | PASS (deny) |
| TST-1424 | filePath value is a list (not str) | PASS (deny) |
| TST-1425 | filePath value is None explicitly | PASS (deny) |
| TST-1426 | filePath is whitespace-only string | PASS (deny) |
| TST-1427 | tool_input is a list (not dict) | PASS (deny) |
| TST-1428 | Completely empty data dict | PASS (deny) |
| TST-1429 | replacements is a dict (not list) | PASS (deny) |
| TST-1430 | replacements is an integer | PASS (deny) |
| TST-1431 | replacements list contains mixed types (dict + string + None) | PASS (deny) |
| TST-1432 | filePath key with wrong case (FILE_PATH) | PASS (deny) |
| TST-1433 | 5×`..` traversal escaping project folder to workspace `.github/` | PASS (deny) |
| TST-1434 | Double slashes inside Project/ path (normalized) | PASS (allow) |
| TST-1435 | Top-level `replacements` fallback with outside-Project path | PASS (deny) |

---

## 4. Security Analysis

### Path traversal depth
The `..` traversal test required careful accounting: 4×`..` from `src/a/b/c/` only reaches the project root (`/workspace/project/`), placing `.github` inside the project folder — correctly classified as `allow`. Only 5×`..` escapes above the project folder to the workspace root level where the deny zone actually lives. This is the correct design: deny zones are only at the workspace root level, not recursively inside the project folder.

**Assessment:** This behaviour is correct and by design. There is no vulnerability — a `.github` folder inside the project folder is an allowed project artifact.

### Fail-closed verification
- Empty replacements → deny ✅
- Missing replacements key → delegates to `validate_write_tool` (which also denies) ✅
- Non-list replacements → deny ✅
- Non-dict entry in list → deny ✅
- Non-string filePath → deny ✅
- Empty string filePath → deny ✅
- Whitespace-only filePath → deny ✅ (zone classifier maps it to deny)

### Routing correctness
`decide()` routes `multi_replace_string_in_file` BEFORE the general `_WRITE_TOOLS` block. `validate_write_tool` is confirmed to return `"deny"` for multi-replace payloads (no top-level `filePath`), which validates that the old code path would have always denied this tool.

### Template mirror
Both `Default-Project` and `templates/coding` copies of `security_gate.py` contain `validate_multi_replace_tool` at line 1463. No divergence detected.

---

## 5. Temporary File Cleanup

`docs/workpackages/SAF-018/tmp_check_hashes.py` was deleted by the Tester as required by the temporary file policy.

---

## 6. Bugs Found

No new security bugs found. No bugs logged.

---

## 7. Verdict

**PASS** — All acceptance criteria met. All 35 Developer tests pass. All 16 Tester edge-case tests pass. Full regression suite shows no new failures. Temporary file cleaned up.
