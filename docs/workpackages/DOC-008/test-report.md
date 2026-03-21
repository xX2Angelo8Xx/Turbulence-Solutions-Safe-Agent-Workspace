# Test Report — DOC-008

**Tester:** Tester Agent
**Date:** 2026-03-21
**Iteration:** 2 (second review cycle)

## Summary

**Iteration 2 — All Issues Resolved. PASS.**

DOC-008 adds a `> [!IMPORTANT]` read-first directive to the top of
`templates/coding/.github/instructions/copilot-instructions.md`. The implementation is
correct — directive is at the very top of the file (line 1), uses exact `> [!IMPORTANT]`
syntax, references `{{PROJECT_NAME}}/AGENT-RULES.md`, and all original content is preserved.

The 3 DOC-003 regressions identified in Iteration 1 (BUG-093) have been fixed. The
Developer updated `tests/DOC-003/test_doc003_edge_cases.py` to relax the placeholder count
assertions from `== 1` to `>= 1`, and rewrote `test_placeholder_is_in_workspace_rules_section`
to check section body content rather than the file-wide first occurrence. All 23 targeted
tests pass. Full suite shows zero new failures versus `main`.

---

## Iteration 1 (Tester FAIL — returned to Developer)

Iteration 1 found 3 regressions in `tests/DOC-003/test_doc003_edge_cases.py` caused by the
directive introducing a second `{{PROJECT_NAME}}` placeholder. Bug filed as BUG-093.
The Developer fixed all 3 tests and re-submitted.

---

## Tests Executed — Iteration 2

### DOC-008 Developer Tests (5 tests)

| Test | Type | Result | Notes |
|------|------|--------|-------|
| test_read_first_directive_present | Unit | PASS | Directive present; AGENT-RULES.md referenced |
| test_directive_mentions_agent_rules | Unit | PASS | Exact filename AGENT-RULES.md present |
| test_directive_uses_project_name_placeholder | Unit | PASS | {{PROJECT_NAME}}/AGENT-RULES.md on same line |
| test_directive_is_near_top | Unit | PASS | Within first 10 lines (actually line 2) |
| test_existing_content_preserved | Unit | PASS | All 7 original sections intact |

### DOC-008 Tester Edge-Case Tests (7 tests)

| Test | Type | Result | Notes |
|------|------|--------|-------|
| test_directive_in_first_5_lines | Regression | PASS | Directive in lines 1–2 |
| test_directive_is_very_first_content | Regression | PASS | First char is '>' (blockquote) |
| test_no_unexpected_placeholders | Regression | PASS | Only {{PROJECT_NAME}} placeholder present |
| test_no_single_brace_placeholder_leak | Regression | PASS | No malformed {PROJECT_NAME} found |
| test_important_callout_syntax | Regression | PASS | Exact '> [!IMPORTANT]' line present |
| test_directive_body_is_blockquote | Regression | PASS | Body line starts with '>' |
| test_agent_rules_path_format | Regression | PASS | Forward-slash path separator used |

### DOC-003 Regression Tests — BUG-093 Fix Verification (11 tests)

| Test | Type | Result | Notes |
|------|------|--------|-------|
| test_placeholder_count_exactly_one_in_default_project | Regression | PASS | Assertion relaxed to >= 1; count is 2 (valid) |
| test_placeholder_count_exactly_one_in_templates_coding | Regression | PASS | Same relaxation; both occurrences legitimate |
| test_placeholder_is_in_workspace_rules_section | Regression | PASS | Now checks section body content (not first-file occurrence) |
| test_noagentzone_reference_unchanged_in_default_project | Regression | PASS | |
| test_github_reference_unchanged_in_default_project | Regression | PASS | |
| test_vscode_reference_unchanged_in_default_project | Regression | PASS | |
| test_replacement_with_hyphenated_project_name | Regression | PASS | |
| test_replacement_with_underscored_project_name | Regression | PASS | |
| test_replacement_with_numeric_suffix_project_name | Regression | PASS | |
| test_default_project_file_has_no_bom | Regression | PASS | |
| test_templates_coding_file_has_no_bom | Regression | PASS | |

**Targeted suite total: 23 passed / 0 failed** (TST-2009)

### Full Suite

- **4409 passed, 76 failed, 2 skipped** (TST-2008)
- All 76 failures confirmed pre-existing on `main` branch (verified by stashing DOC-008 changes)
- Failing test suites: FIX-028/031/037/038/039 (codesign scripts), FIX-036/049/050 (version), FIX-009 (TST-ID format), INS-004 (pyc), INS-019 (shims), SAF-010/022/025 — none related to DOC-008
- **Zero new regressions introduced by DOC-008**

### Workspace Validation

`scripts/validate_workspace.py --wp DOC-008` → **All checks passed** (exit code 0)

---

## AC Verification — US-033 AC 8

The workpackage success criterion states: "copilot-instructions.md contains a first-action
directive pointing agents to AGENT-RULES.md."

Verification:
- ✅ Directive is the very first content in the file (line 1–2)
- ✅ Uses `> [!IMPORTANT]` GFM callout syntax
- ✅ Contains `{{PROJECT_NAME}}/AGENT-RULES.md` path reference
- ✅ Directive text instructs agents to read the file "Before any work"
- ✅ All original template content preserved unchanged

**AC 8 of US-033: SATISFIED**

---

## Bugs Found

No new bugs found in this iteration. BUG-093 (filed in Iteration 1) is marked Fixed in
`docs/bugs/bugs.csv`.

## TODOs for Developer

None.

## Verdict

**PASS — Mark WP as Done.**

All 23 DOC-008 + DOC-003 targeted tests pass. The 3 BUG-093 regressions are resolved.
No new regressions vs. `main`. Workspace validation clean. AC 8 of US-033 satisfied.
