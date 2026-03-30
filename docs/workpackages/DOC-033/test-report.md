# DOC-033 Test Report — README management for agent-workbench template

**Verdict: FAIL**  
**Tester:** Tester Agent  
**Date:** 2026-03-30  
**Branch:** `DOC-033/readme-management`

---

## Summary

DOC-033's implementation is functionally correct: the user-facing README was created and
`templates/agent-workbench/.github/agents/README.md` was deleted as required. All 12
DOC-033-specific tests pass. However, the README replacement **broke 8 pre-existing DOC-002
regression tests** that were passing on `main` before this WP. Per testing protocol, work that
fails any existing test cannot be approved.

---

## Test Results

| Suite | Tests Run | Passed | Failed | Status |
|-------|-----------|--------|--------|--------|
| DOC-033 developer tests | 6 | 6 | 0 | PASS |
| DOC-033 tester edge-case tests | 6 | 6 | 0 | PASS |
| Regression: DOC-001, DOC-002, DOC-003 | 90 | 82 | 8 | **FAIL** |

Logged as: TST-2327 (developer unit), TST-2328 (tester edge-cases), TST-2329 (regression).  
Bug logged: BUG-162.

---

## DOC-033 Tests: PASS

### Developer tests (TST-2327) — 6/6 PASS

- `test_readme_exists` — `templates/agent-workbench/README.md` exists ✓
- `test_readme_contains_project_name_placeholder` — `{{PROJECT_NAME}}` present ✓
- `test_readme_contains_workspace_name_placeholder` — `{{WORKSPACE_NAME}}` present ✓
- `test_readme_mentions_noagentzone` — `NoAgentZone` mentioned ✓
- `test_readme_is_brief` — file is 20 lines (< 50) ✓
- `test_agents_readme_deleted` — `.github/agents/README.md` does not exist ✓

### Tester edge-case tests (TST-2328) — 6/6 PASS

- `test_readme_not_agent_facing` — no agent-instruction patterns (`You are`, `ALWAYS`, `NEVER`, etc.) ✓
- `test_readme_mentions_agent_rules_file` — references `AGENT-RULES.md` ✓
- `test_agent_md_files_still_present` — all 11 `.agent.md` files intact ✓
- `test_agents_dir_contains_only_agent_md_files` — no unexpected files in `.github/agents/` ✓
- `test_readme_is_user_friendly_greeting` — starts with heading containing `{{WORKSPACE_NAME}}` ✓
- `test_readme_no_raw_agent_names` — no internal agent file names leaked into README ✓

---

## Regression Failures: 8 Tests in DOC-002

The DOC-033 developer replaced the old (agent-facing) `templates/agent-workbench/README.md` — which
contained security zone documentation with Tier 1/2/3 and Exempt Tools sections — with a new
user-facing README. **Eight DOC-002 tests assert the old content and now fail.**

### Failing tests (all in `tests/DOC-002/`)

| Test | Failing Assertion | Root Cause |
|------|-------------------|------------|
| `test_placeholder_present_in_tier1_description` | `"targeting \`{{PROJECT_NAME}}/\` proceed without a dialog" in content` | Tier 1 section removed |
| `test_placeholder_present_in_tier2_description` | `"outside \`{{PROJECT_NAME}}/\`" in content` | Tier 2 section removed |
| `test_placeholder_present_in_exempt_tools_section` | `"inside \`{{PROJECT_NAME}}/\`" in content` | Exempt Tools section removed |
| `test_default_readme_has_exactly_four_placeholder_occurrences` | `count("{{PROJECT_NAME}}") == 4` (got 3) | New README has 3, not 4 occurrences |
| `test_coding_template_readme_has_exactly_four_placeholder_occurrences` | `count("{{PROJECT_NAME}}") == 4` (got 3) | Same file, same issue |
| `test_no_workspace_name_placeholder_in_default_readme` | `"{{WORKSPACE_NAME}}" not in content` | New README title IS `{{WORKSPACE_NAME}}` |
| `test_no_workspace_name_placeholder_in_coding_template_readme` | `"{{WORKSPACE_NAME}}" not in content` | Same |
| `test_all_four_actual_readme_occurrences_replaced` | `result.count("Nimbus/") == 4` (got 3) | Only 3 replaceable occurrences in new README |

**Bug:** BUG-162

---

## Implementation Review

### What was delivered (correct)
- `templates/agent-workbench/README.md` — created, user-facing, brief (20 lines), uses both
  `{{PROJECT_NAME}}` and `{{WORKSPACE_NAME}}` placeholders, mentions `NoAgentZone`, references
  `AGENT-RULES.md`, no agent-instruction patterns.
- `templates/agent-workbench/.github/agents/README.md` — deleted as required.
- All 11 `.agent.md` files in `.github/agents/` are intact.

### What is missing
The developer did not update the DOC-002 test suite to reflect the changed README content.
The DOC-002 tests were tightly coupled to the old README's security zone documentation
(Tier 1/2/3, Exempt Tools). Now that the README is user-facing, these tests are stale.

---

## Required Actions (TODOs for Developer)

1. **Update `tests/DOC-002/test_doc002_readme_placeholders.py`** — remove or update the three
   failing static-content assertions that check for old security-zone text:
   - `test_placeholder_present_in_tier1_description` (line ~65): remove or update to match
     a phrase that actually exists in the new README (e.g. `"{{PROJECT_NAME}}/"`)
   - `test_placeholder_present_in_tier2_description` (line ~70): remove or update similarly
   - `test_placeholder_present_in_exempt_tools_section` (line ~75): remove or update similarly

2. **Update `tests/DOC-002/test_doc002_tester_edge_cases.py`** — fix the four failing count/
   existence assertions:
   - `TestPlaceholderCount::test_default_readme_has_exactly_four_placeholder_occurrences`:
     Change `assert count == 4` → `assert count == 3` (new README has exactly 3 `{{PROJECT_NAME}}`
     occurrences).
   - `TestPlaceholderCount::test_coding_template_readme_has_exactly_four_placeholder_occurrences`:
     Same change.
   - `TestPlaceholderCount::test_no_workspace_name_placeholder_in_default_readme`:
     Remove this assertion entirely — `{{WORKSPACE_NAME}}` is now intentionally present as the
     README title. Or flip it to `assert "{{WORKSPACE_NAME}}" in content`.
   - `TestPlaceholderCount::test_no_workspace_name_placeholder_in_coding_template_readme`:
     Same.
   - `TestAllOccurrencesInActualTemplate::test_all_four_actual_readme_occurrences_replaced`:
     Change `assert result.count("Nimbus/") == 4` → `assert result.count("Nimbus/") == 3`.
     Also verify `{{WORKSPACE_NAME}}` is replaced (new README uses it as the title).

3. **Re-run the full regression suite** (`pytest tests/DOC-033/ tests/DOC-002/ -v`) before
   re-setting WP to `Review`. All tests must pass.

4. **Note:** The `{{WORKSPACE_NAME}}` placeholder in the new README is handled by
   `replace_template_placeholders()`. The DOC-002 integration tests for placeholder replacement
   (e.g. `test_folder_table_placeholder_replaced`) use synthetic content and are unaffected — only
   the static-content assertions against the real file need updating.

---

## Verdict: FAIL

**WP DOC-033 is returned to `In Progress`.**  
No code changes required — only DOC-002 test updates are needed.  
All DOC-033 functionality is correct. The failure is a test-maintenance issue.
