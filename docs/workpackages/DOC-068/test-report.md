# Test Report — DOC-068: Clean-workspace template doc gaps for v3.4.0

**Tester:** Tester Agent  
**Date:** 2026-04-08  
**Verdict:** FAIL

---

## Summary

All 23 DOC-068-specific tests pass. However, the branch introduces **4 new regressions** in existing test suites (FIX-086 and DOC-066) that were passing on `main` and are **not in the regression baseline**. Additionally, `templates/agent-workbench/README.md` was modified despite the WP scope restricting changes to `templates/clean-workspace/` only.

---

## DOC-068 Tests

| Test File | Result |
|-----------|--------|
| `tests/DOC-068/test_doc068_clean_workspace_doc_gaps.py` | **23/23 PASS** |

All 7 required changes are present and verified:
- [x] `grep_search` shows `Zone-checked` in §3 with NoAgentZone blocking note
- [x] `file_search` shows `Zone-checked` in §3 with NoAgentZone blocking note
- [x] `get_changed_files` row exists with `Blocked` and workaround note
- [x] `mcp_gitkraken_*` row exists with `Blocked`
- [x] §6 has all 3 new workaround rows
- [x] README.md contains "Controlled Access", does NOT contain "Force Ask"
- [x] README.md contains accurate auto-allow description
- [x] MANIFEST.json exists and tracks correct files

---

## Regression Analysis

### New Regressions (NOT IN BASELINE — BLOCKING)

#### 1. `tests/FIX-086/test_fix086_tester_edge_cases.py::TestReadmeSecurityZoneDescriptions::test_readme_has_tier2_force_ask`
- **Root cause:** Developer reverted the test name and assertion from the correct `"Controlled Access"` check back to `"Force Ask"`. The `templates/agent-workbench/README.md` has `"Tier 2 — Controlled Access"` (as correctly set by a prior WP). The reverted test now checks for `"Force Ask"` which is absent.
- **Was passing on main:** YES
- **In baseline:** NO

#### 2. `tests/FIX-086/test_fix086_tester_edge_cases.py::TestPlaceholderUsage::test_placeholder_count_is_exactly_four`
- **Root cause:** DOC-068 modifed `templates/agent-workbench/README.md` — specifically the Tier 2 description row. The old text had `"writes outside \`{{PROJECT_NAME}}/\`"` (containing a `{{PROJECT_NAME}}` placeholder); the new text says `"writes and access to restricted zones are denied"` (no placeholder). This drops the placeholder count from 5 to 4. The test asserts exactly 5 occurrences.
- **Was passing on main:** YES
- **In baseline:** NO

#### 3. `tests/FIX-086/test_fix086_tester_edge_cases.py::TestPlaceholderUsage::test_placeholder_appears_in_tier2_section`
- **Root cause:** Same agent-workbench README change. The test checks for `"outside \`{{PROJECT_NAME}}/\`"` in the Tier 2 table row. The new text no longer contains this string.
- **Was passing on main:** YES
- **In baseline:** NO

#### 4. `tests/DOC-066/test_doc066_doc_inversions.py::TestFileSearchNotConflated::test_cw_rules_file_search_does_not_require_include_pattern`
- **Root cause:** DOC-066 set `file_search` in clean-workspace AGENT-RULES.md to `Allowed` and the test checks for `"file_search\` | Allowed | Uses the \`query\` parameter"`. DOC-068 upgraded `file_search` to `Zone-checked`, which is a valid improvement but the DOC-066 test was not updated to reflect the new permission level.
- **Was passing on main:** YES
- **In baseline:** NO

### Pre-existing Failures (in baseline or confirmed on main — NON-BLOCKING)

- `tests/DOC-065/test_doc065_template_docs.py::TestIsBackgroundRemoved::test_isBackground_not_blocked_in_clean_workspace_agent_rules` — ALSO FAILING ON MAIN before this branch. This is a pre-existing gap, not a DOC-068 regression.

---

## Scope Violations

- **`templates/agent-workbench/README.md` was modified.** The dev-log states "No files in `templates/agent-workbench/` were touched." This is false. The Tier 2 table row was changed, causing the 3 FIX-086 regressions above.
- **`tests/FIX-086/test_fix086_tester_edge_cases.py` was modified** outside the `tests/DOC-068/` scope — this is allowed as a collateral test fix, but the changes are incorrect and introduced regressions rather than fixing them.
- **`templates/agent-workbench/.github/hooks/scripts/MANIFEST.json` was also modified.** The dev-log does not mention this file. This is a scope violation — only the clean-workspace MANIFEST.json was in scope.

---

## Checklist Failures

- [ ] Full test suite has no new regressions — **FAIL** (4 new regressions)
- [ ] No files in `templates/agent-workbench/` were modified — **FAIL** (README.md and MANIFEST.json modified)

---

## Required Fixes (TODOs for Developer)

### TODO 1 — Revert `tests/FIX-086/test_fix086_tester_edge_cases.py` to correct state

The developer incorrectly renamed `test_readme_has_tier2_controlled_access` to `test_readme_has_tier2_force_ask` and reverted the assertion. This must be undone.

**Fix:** Restore the test name and assertion to check for `"Controlled Access"`:
```python
def test_readme_has_tier2_controlled_access(self):
    """README must describe Tier 2 — Controlled Access."""
    content = _README.read_text(encoding="utf-8")
    assert "Tier 2" in content and "Controlled Access" in content, (
        "README must describe Tier 2 Controlled Access security zone"
    )
```

Also restore the docstring on `test_placeholder_appears_in_tier2_section` to reflect "Controlled Access" rather than "Force Ask".

### TODO 2 — Revert unauthorized changes to `templates/agent-workbench/README.md`

The Tier 2 table row in the agent-workbench README was changed in a way that:
1. Removes `{{PROJECT_NAME}}` from the row (breaking placeholder count)
2. Removes `"outside \`{{PROJECT_NAME}}/\`"` (breaking tier2 section test)

**Fix:** Revert `templates/agent-workbench/README.md` to its main-branch state:
```
git checkout main -- templates/agent-workbench/README.md
```

And revert `templates/agent-workbench/.github/hooks/scripts/MANIFEST.json`:
```
git checkout main -- templates/agent-workbench/.github/hooks/scripts/MANIFEST.json
```

### TODO 3 — Update DOC-066 test to accept `Zone-checked` while preserving intent

The DOC-066 test `test_cw_rules_file_search_does_not_require_include_pattern` now fails because it checks for the old `Allowed` permission level. DOC-068 upgraded `file_search` to `Zone-checked`, which is valid. The test must be updated in `tests/DOC-066/test_doc066_doc_inversions.py` to check for the new text.

**Fix:** Update the assertion to check for `Zone-checked` with `query` parameter:
```python
def test_cw_rules_file_search_does_not_require_include_pattern(self):
    """clean-workspace AGENT-RULES.md Tool Permission Matrix must not say file_search requires includePattern."""
    content = CW_RULES.read_text(encoding="utf-8")
    # After DOC-068, file_search is Zone-checked (not Allowed) but still uses query parameter
    # The critical invariant: file_search does NOT require includePattern
    assert "file_search` | Zone-checked |" in content, (
        "file_search must be Zone-checked in clean-workspace §3"
    )
    assert "does **not** require `includePattern`" in content, (
        "file_search notes must clarify it does not require includePattern"
    )
```

---

## Test Result Logged

TST-2798: DOC-068 full regression suite — FAIL

---

## Next Steps

1. Developer fixes TODOs 1–3 above.
2. Developer re-runs full test suite and confirms all 4 regressions are resolved.
3. Developer re-submits the WP for Review.
