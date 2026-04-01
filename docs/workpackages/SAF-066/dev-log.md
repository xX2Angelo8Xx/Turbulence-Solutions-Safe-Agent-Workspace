# SAF-066 Dev Log — Fix grep_search unfiltered NoAgentZone bypass

**WP ID:** SAF-066  
**Developer:** Developer Agent  
**Branch:** SAF-066/grep-search-no-include-deny  
**Started:** 2026-04-01  

---

## Problem Statement

`validate_grep_search()` in `security_gate.py` returned "allow" when `grep_search` was called with no `includePattern` and no `filePath` (the `raw_path is None` branch). This trusted VS Code's `search.exclude` to filter restricted zones (.github/, .vscode/, NoAgentZone/). However, `search.exclude` is a UI hint, not a hard security boundary. A `grep_search` call with no `includePattern` can return content from any file in the workspace, including NoAgentZone files. Fixes BUG-172 (Critical).

---

## Implementation Summary

### File Changed: `templates/agent-workbench/.github/hooks/scripts/security_gate.py`

Modified `validate_grep_search()`: in the `raw_path is None` branch, added a check — if no `includePattern` (non-empty string) was provided, return "deny". This is a fail-closed change: without an explicit `includePattern` that has been validated against the zone policy, the search is denied.

**Before (vulnerable):**
```python
raw_path = extract_path(data)
if raw_path is None:
    # FIX-021: grep_search has no filePath — VS Code search.exclude hides restricted content
    return "allow"
```

**After (secure):**
```python
raw_path = extract_path(data)
if raw_path is None:
    # SAF-066: Without an includePattern the search is unscoped and can reach
    # denied zones. Fail closed — require an includePattern.
    if not (isinstance(include_pattern, str) and include_pattern):
        return "deny"
    return "allow"
```

### Files Updated (existing test regressions)

The behavior change invalidated several tests in completed WPs that documented the old FIX-021 "no params → allow" policy:

- `tests/FIX-021/test_fix021_search_tools.py` — updated no-params tests to expect "deny"; updated no-includePattern tests to add a safe includePattern so the test purpose is preserved
- `tests/SAF-003/test_saf003_tool_parameter_validation.py` — updated TST-290 and TST-293 to expect "deny"
- `tests/SAF-045/test_saf045_tester_edge_cases.py` — updated empty-includePattern test; added safe includePattern to includeIgnoredFiles edge-case tests to preserve their purpose

### File Changed: `templates/agent-workbench/Project/AgentDocs/AGENT-RULES.md`

Updated the Known Workarounds / grep_search section to document that `includePattern` is now required.

### New File: `tests/SAF-066/test_saf066_grep_search_no_include_deny.py`

Comprehensive tests covering:
- No includePattern → deny (regression / protection test)
- Empty includePattern → deny (fail-closed)
- Nested tool_input with no includePattern → deny
- Valid project-scoped includePattern → allow (bypass-attempt / compatibility test)
- NoAgentZone includePattern → deny
- .github includePattern → deny
- .vscode includePattern → deny
- includeIgnoredFiles=True → deny (unchanged)
- includeIgnoredFiles with valid includePattern → allow

---

## Tests Written

Location: `tests/SAF-066/test_saf066_grep_search_no_include_deny.py`

| Test | Category | Description |
|------|----------|-------------|
| test_no_include_pattern_denied | Security/Regression | No includePattern → deny (BUG-172 reproduction) |
| test_empty_include_pattern_denied | Security | Empty string includePattern → deny |
| test_nested_no_include_pattern_denied | Security | VS Code nested format, no includePattern → deny |
| test_valid_include_pattern_allowed | Security | Project-scoped includePattern → allow |
| test_nested_valid_include_pattern_allowed | Security | Nested format + project includePattern → allow |
| test_noagentzone_include_pattern_denied | Security | NoAgentZone includePattern → deny |
| test_github_include_pattern_denied | Security | .github includePattern → deny |
| test_vscode_include_pattern_denied | Security | .vscode includePattern → deny |
| test_include_ignored_files_denied | Security | includeIgnoredFiles=True → deny (unchanged) |
| test_include_ignored_files_with_valid_pattern_denied | Security | includeIgnoredFiles + valid pattern → deny |
| test_decide_no_include_pattern_denied | Integration | decide() routes grep_search without includePattern → deny |
| test_decide_valid_include_pattern_allowed | Integration | decide() routes grep_search with valid includePattern → allow |

---

## Known Limitations

None — the fix is a strict tightening of the allow condition.

---

## Bugs Fixed

- BUG-172: grep_search without includePattern leaks NoAgentZone content — Fixed In WP: SAF-066
