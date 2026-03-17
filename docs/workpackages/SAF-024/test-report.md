# Test Report — SAF-024: Implement Generic Deny Messages

**Tester:** Tester Agent  
**Date:** 2026-03-17  
**Branch:** `SAF-024/generic-deny-messages`  
**Verdict:** PASS

---

## 1. Review Summary

### Code Changes Verified

- **`Default-Project/.github/hooks/scripts/security_gate.py`**
  - `_DENY_REASON` (line 81) = `"Access denied. This action has been blocked by the workspace security policy."` — no zone names, no old `BLOCKED:` prefix. ✓
  - All `("deny", ...)` tuples in `sanitize_terminal_command()` use `_DENY_REASON` (via f-string or directly). ✓
  - `main()` always outputs `build_response("deny", _DENY_REASON)` — never an inline zone-revealing string. ✓
  - `decide()` discards the detailed reason from `sanitize_terminal_command()` before returning to `main()`, ensuring the JSON output is always the generic constant. ✓
  - Internal comments and zone classification variables (`.github`, `.vscode`, `NoAgentZone`) are undisturbed. ✓

- **`templates/coding/.github/hooks/scripts/security_gate.py`**
  - Confirmed byte-for-byte `_DENY_REASON` match with `Default-Project/` version. ✓

- **`tests/SAF-020/test_saf020_wildcard_blocking.py`**
  - Minor assertion update for new deny text — legitimate and correct. ✓

### Requirements Verification

| Requirement | Met |
|-------------|-----|
| `_DENY_REASON` is generic (no zone names) | ✓ |
| `_DENY_REASON` does not start with `BLOCKED:` | ✓ |
| All deny JSON output uses `_DENY_REASON` only | ✓ |
| Internal comments still reference zone names | ✓ |
| `templates/coding/` copy is in sync | ✓ |

---

## 2. Test Results

### Developer Tests (TST-601 to TST-610)

All 10 developer tests pass.

| ID | Test Name | Result |
|----|-----------|--------|
| TST-601 | `test_deny_reason_is_generic_text` | PASS |
| TST-602 | `test_deny_reason_no_github_reference` | PASS |
| TST-603 | `test_deny_reason_no_vscode_reference` | PASS |
| TST-604 | `test_deny_reason_no_noagentzone_reference` | PASS |
| TST-605 | `test_deny_reason_no_blocked_prefix` | PASS |
| TST-606 | `test_main_stdout_generic_on_deny` | PASS |
| TST-607 | `test_main_stdout_no_zone_names_on_deny` | PASS |
| TST-608 | `test_sanitize_terminal_deny_reason_no_zone_names` | PASS |
| TST-609 | `test_deny_reason_constant_is_str` | PASS |
| TST-610 | `test_templates_deny_reason_matches` | PASS |

### Tester Edge-Case Tests (TST-611 to TST-620)

All 10 tester edge-case tests pass.

| ID | Test Name | Result | Rationale |
|----|-----------|--------|-----------|
| TST-611 | `test_main_write_tool_deny_is_generic` | PASS | write tool (create_file → .vscode) end-to-end |
| TST-612 | `test_main_multi_replace_deny_is_generic` | PASS | multi_replace targeting .github end-to-end |
| TST-613 | `test_main_get_errors_deny_is_generic` | PASS | get_errors with .vscode filePath end-to-end |
| TST-614 | `test_main_grep_search_deny_is_generic` | PASS | grep_search with .github includePattern end-to-end |
| TST-615 | `test_main_semantic_search_deny_is_generic` | PASS | semantic_search (always deny) end-to-end |
| TST-616 | `test_sanitize_terminal_all_paths_generic` | PASS | Extra sanitize paths (empty, $var verb, sudo, format) |
| TST-617 | `test_internal_comments_still_reference_zones` | PASS | Confirms internal zone names preserved for maintainability |
| TST-618 | `test_main_unknown_tool_deny_is_generic` | PASS | Completely unknown tool name — generic deny |
| TST-619 | `test_deny_reason_same_both_copies` | PASS | Byte-for-byte comparison of both security_gate.py copies |
| TST-620 | `test_sanitize_terminal_f_string_prefixes_no_zone_names` | PASS | All f-string deny reason prefixes contain no zone names |

### Full Regression Suite

| Run | Passed | Failed | Skipped | Pre-existing Failures |
|-----|--------|--------|---------|----------------------|
| Tester run 1 (developer tests only) | 2960 | 1 | 29 | INS-005 (unrelated) |
| Tester run 2 (all tests including edge-case) | 2960 | 1 | 29 | INS-005 (unrelated) |

The INS-005 failure (`test_uninstall_delete_type_is_filesandirs`) is pre-existing and unrelated to SAF-024.

---

## 3. Security Analysis

### Attack Vectors Considered

1. **Information harvesting via deny messages**: An agent could attempt to probe protected zone paths and extract zone names from error messages. Confirmed that all deny paths — including the terminal sanitizer's internal f-string reasons — use `_DENY_REASON` exclusively in the JSON output. ✓

2. **Direct API call to `sanitize_terminal_command()`**: The function returns detailed f-string reasons to its callers, but these are only exposed internally. The caller (`decide()`) discards the reason, and `main()` substitutes `_DENY_REASON`. The f-string prefixes themselves also contain no zone names. ✓

3. **Zone name in `_INTEGRITY_WARNING`**: This constant deliberately reveals that `.vscode/settings.json` and `security_gate.py` were tampered with — this is intentional (it's an admin-facing alert, not an agent-visible deny reason). `_INTEGRITY_WARNING` is separate from `_DENY_REASON` and not subject to the same constraint. ✓

4. **Template drift**: If templates copy gets out of sync, the zone names could creep back in via a future merge. TST-619 adds a byte-for-byte comparison check to detect any future drift. ✓

### Boundary & Edge Cases

- Empty command after normalization → generic deny ✓
- Command with variable primary verb (`$VAR`) → generic deny ✓
- `sudo` command → generic deny ✓
- Destructive `format` pattern → generic deny ✓
- `semantic_search` (always deny, no path needed) → generic deny ✓
- `get_errors` with empty `filePaths` → allow (correct per SAF-023) ✓

### Maintainability

Zone names are retained in:
- Variable names: `_WILDCARD_DENY_ZONES`, `deny_zones` list in `_is_ancestor_of_deny_zone()`
- Comments throughout the file
- `zone_classifier` calls

This is intentional and correct — only the output to the agent is generic.

---

## 4. Bugs Found

None. No new bugs identified during testing.

---

## 5. Verdict

**PASS** — All acceptance criteria met. No regressions. Implementation is correct, secure, and consistent across both security_gate.py copies. WP set to `Done`.
