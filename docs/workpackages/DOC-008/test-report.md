# Test Report — DOC-008

**Tester:** Tester Agent
**Date:** 2026-03-21
**Iteration:** 1

## Summary

DOC-008 adds a `> [!IMPORTANT]` read-first directive to the top of
`templates/coding/.github/instructions/copilot-instructions.md`. The implementation
itself is correct — the directive is at the right location, uses the right syntax,
references the right file, and uses the `{{PROJECT_NAME}}` placeholder correctly.

**However, the change introduces 3 regressions in the DOC-003 test suite** that must
be resolved before the WP can be approved.

The directive adds a second `{{PROJECT_NAME}}` occurrence at the top of the file.
Existing DOC-003 edge-case tests assert that the placeholder appears exactly once
and that its first occurrence is inside the `## Workspace Rules` section. Both
assumptions are now violated.

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| test_read_first_directive_present | Unit | PASS | Directive present and contains AGENT-RULES.md |
| test_directive_mentions_agent_rules | Unit | PASS | Exact filename AGENT-RULES.md referenced |
| test_directive_uses_project_name_placeholder | Unit | PASS | {{PROJECT_NAME}}/AGENT-RULES.md on same line |
| test_directive_is_near_top | Unit | PASS | Within first 10 lines |
| test_existing_content_preserved | Unit | PASS | All 7 original sections present |
| test_directive_in_first_5_lines (tester) | Regression | PASS | Directive is in lines 1–2 |
| test_directive_is_very_first_content (tester) | Regression | PASS | First character is '>' |
| test_no_unexpected_placeholders (tester) | Regression | PASS | Only {{PROJECT_NAME}} used |
| test_no_single_brace_placeholder_leak (tester) | Regression | PASS | No single-brace variants found |
| test_important_callout_syntax (tester) | Regression | PASS | Exact '> [!IMPORTANT]' present |
| test_directive_body_is_blockquote (tester) | Regression | PASS | Body line starts with '>' |
| test_agent_rules_path_format (tester) | Regression | PASS | Forward-slash path separator used |
| **test_placeholder_count_exactly_one_in_default_project (DOC-003)** | Regression | **FAIL** | Count is 2, expected 1 — DOC-008 introduced second occurrence |
| **test_placeholder_count_exactly_one_in_templates_coding (DOC-003)** | Regression | **FAIL** | Count is 2, expected 1 |
| **test_placeholder_is_in_workspace_rules_section (DOC-003)** | Regression | **FAIL** | First occurrence (idx 75) precedes Workspace Rules (idx 231) |

## Regression Analysis

The DOC-008 directive:

```markdown
> [!IMPORTANT]
> **First Action — Read Rule Book:** Before any work, read `{{PROJECT_NAME}}/AGENT-RULES.md` for your complete permissions and rules.
```

Introduced a second `{{PROJECT_NAME}}` placeholder. DOC-003 asserts:

1. **Exactly 1** occurrence of `{{PROJECT_NAME}}` in the file — now **2** → FAIL
2. **First occurrence** of `{{PROJECT_NAME}}` is inside `## Workspace Rules` — now **at line 2** (before the heading) → FAIL

These tests **pass on `main`** and are broken only by the DOC-008 change.

The DOC-003 assertions were always too strict (the template can legitimately have multiple
placeholder  occurrences), but **existing tests must not be broken** — the Developer must
update or relax those assertions as part of this WP.

## Bugs Found

- BUG-093: DOC-008 breaks DOC-003 placeholder count tests (regression) — logged in `docs/bugs/bugs.csv`

## TODOs for Developer

- [ ] **Fix or update the 3 failing DOC-003 edge-case tests** so the full suite passes.
  The tests are in `tests/DOC-003/test_doc003_edge_cases.py`:
  1. `test_placeholder_count_exactly_one_in_default_project` — change assertion from
     `count == 1` to `count >= 1` (or update to `count == 2` if the new count is intentional and stable).
  2. `test_placeholder_count_exactly_one_in_templates_coding` — same fix as above.
  3. `test_placeholder_is_in_workspace_rules_section` — the test must be updated to
     check that `{{PROJECT_NAME}}` appears somewhere in (or before) the Workspace Rules section,
     or restructured to search for the specific placeholder occurrence in the Workspace Rules section
     rather than using the index of the first occurrence.

  **Preferred approach:** Change the count assertions to `count >= 2` (or `>= 1` to be
  future-proof), and fix the Workspace Rules test to assert the **Workspace Rules section
  contains** `{{PROJECT_NAME}}` (e.g., check the substring between `## Workspace Rules` and
  the next `##` heading).

- [ ] **Ensure all DOC-003 tests pass** after updating them:
  ```
  .venv\Scripts\python -m pytest tests/DOC-003/ -v
  ```
  All 17 tests must pass.

- [ ] **Re-run the full test suite** (excluding pre-existing yaml import failures) and
  confirm no new failures beyond those pre-existing on `main`.

- [ ] **Note:** The developer's own 5 tests (tests/DOC-008/test_doc008_read_first_directive.py)
  all pass and cover the requirements correctly. No changes needed to those.

## Verdict

**FAIL — Return to Developer.**

All 12 DOC-008-specific tests pass (5 developer + 7 Tester edge-case). The implementation
in `copilot-instructions.md` is correct. However, 3 DOC-003 regression tests fail due to
the second `{{PROJECT_NAME}}` introduced by this WP. These were passing on `main` and must
be green before the WP can be marked Done.
