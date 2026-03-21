# Test Report — DOC-007: Create AGENT-RULES.md Template

**Tester:** Tester Agent  
**Date:** 2025-07-14  
**WP:** DOC-007  
**Branch:** DOC-007/agent-rules-template  
**Verdict:** ✅ PASS

---

## 1. Summary

DOC-007 delivers `templates/coding/Project/AGENT-RULES.md`, a reusable agent rule book template for all coding projects. All 35 tests pass (27 developer + 8 tester edge-cases). Zero regressions were introduced against the main branch baseline (76 pre-existing failures unchanged).

---

## 2. Acceptance Criteria Checklist

| # | Acceptance Criterion | Result |
|---|----------------------|--------|
| AC1 | File exists at `templates/coding/Project/AGENT-RULES.md` | ✅ PASS |
| AC2 | File contains read-first directive (mandatory at session start) | ✅ PASS |
| AC3 | File uses `{{PROJECT_NAME}}` and `{{WORKSPACE_NAME}}` placeholders | ✅ PASS |
| AC4 | Section 1: Allowed Zone references both placeholders | ✅ PASS |
| AC5 | Section 2: Denied Zones includes `.github/`, `.vscode/`, `NoAgentZone/` | ✅ PASS |
| AC6 | Section 3: Tool Permission Matrix covers file, search, LSP, and terminal tools | ✅ PASS |
| AC7 | Section 4: Terminal Rules with permitted/blocked examples | ✅ PASS |
| AC8 | Section 5: Git Rules with allowed/blocked operations tables | ✅ PASS |
| AC9 | Section 6: Session-Scoped Denial Counter (Block N of M, resets on new chat) | ✅ PASS |
| AC10 | Section 7: Known Workarounds table (includes `Set-Content`) | ✅ PASS |

---

## 3. Test Results

### 3.1 Targeted Suite (DOC-007 only)

| Test Run ID | Scope | Tests | Passed | Failed | Result |
|-------------|-------|-------|--------|--------|--------|
| TST-1993 | DOC-007 targeted | 35 | 35 | 0 | ✅ Pass |

### 3.2 Developer Test Coverage (27 tests)

All developer tests confirmed passing:
- `test_file_exists`, `test_has_read_first_directive`, `test_placeholder_project_name`, `test_placeholder_workspace_name`
- `test_has_allowed_zone_section`, `test_allowed_zone_references_project_name`
- `test_has_denied_zones_section`, `test_denied_zone_github`, `test_denied_zone_vscode`, `test_denied_zone_noagentzone`
- `test_has_tool_permission_matrix`, `test_matrix_covers_file_tools`, `test_matrix_covers_search_tools`, `test_matrix_covers_lsp_tools`, `test_matrix_has_allowed_or_denied_or_zone_checked`
- `test_has_terminal_rules_section`, `test_terminal_rules_has_permitted_examples`, `test_terminal_rules_has_blocked_examples`
- `test_has_git_rules_section`, `test_git_rules_allowed_operations`, `test_git_rules_blocked_operations`
- `test_has_denial_counter_section`, `test_denial_counter_mentions_block_n_of_m`, `test_denial_counter_mentions_new_chat_resets`
- `test_has_workarounds_section`, `test_workarounds_is_a_table`, `test_workarounds_mentions_set_content`

### 3.3 Tester Edge-Case Tests (8 added)

| Test | What it checks | Result |
|------|---------------|--------|
| `test_no_hardcoded_project_name_uppercase` | No bare "Project" (capital P) outside `{{...}}` placeholders | ✅ Pass |
| `test_valid_markdown_h1_title` | File begins with H1 heading | ✅ Pass |
| `test_all_seven_numbered_sections_present` | All 7 numbered sections (1–7) present with `## N.` heading | ✅ Pass |
| `test_matrix_covers_create_directory_explicitly` | `create_directory` explicitly listed in matrix | ✅ Pass |
| `test_matrix_write_tools_are_zone_checked` | Write tools carry "Zone-checked" label | ✅ Pass |
| `test_matrix_covers_terminal_category` | Terminal appears as category in matrix | ✅ Pass |
| `test_denied_zones_presented_as_table` | Denied zones in markdown table format | ✅ Pass |
| `test_markdown_no_unclosed_code_fence` | Even number of triple-backtick fences (all closed) | ✅ Pass |

### 3.4 Regression Analysis

Baseline failures on `main`: 76 test failures + 14 collection errors (pre-existing — missing `yaml` package in FIX-010/011/029, INS-013–017; unrelated SAF/INS failures).

DOC-007 branch: same 76 failures + 14 collection errors. **Zero new regressions.**

---

## 4. Code Review Findings

### 4.1 Structural Correctness
- Template has exactly 7 numbered sections as required
- All `{{PLACEHOLDER}}` variables consistently used; no hardcoded values found
- First line is a valid H1 heading: `# {{PROJECT_NAME}} — Agent Rules`
- Read-first directive appears immediately after the title

### 4.2 Security Review
- Template directs agents to respect `NoAgentZone/` — correct defense-in-depth
- Blocked git operations listed: `--force`, `--hard`, `amend`, `rebase`, `tag -d` — comprehensive
- Tool permission matrix enforces zone-checked (not unconditionally allowed) for write tools
- No injection vectors in the template itself (it is a static Markdown file)

### 4.3 Content Quality
- Tool Permission Matrix: 15 tools/categories; read/search tools "Allowed"; write/create/edit tools "Zone-checked"; destructive tools "Denied"
- Known Workarounds table: 10 entries covering common Windows PowerShell quirks (e.g., `Set-Content` over `Out-File`)
- Denial counter provides reproducible, auditable session context

### 4.4 Boundary and Edge-Case Analysis
- No hardcoded project-specific names — template is fully reusable ✅
- All 8 code fences are properly paired ✅
- All 7 numbered sections present — no numbering gap ✅
- Placeholders appear in both Section 1 (Allowed Zone path) and the H1 title ✅

---

## 5. Bugs Found

None — no bugs logged.

---

## 6. Pre-Done Checklist

- [x] `docs/workpackages/DOC-007/dev-log.md` exists and is non-empty
- [x] `docs/workpackages/DOC-007/test-report.md` written (this file)
- [x] Test files exist in `tests/DOC-007/` with 35 tests
- [x] All test results logged via `scripts/run_tests.py` (TST-1993)
- [x] `scripts/validate_workspace.py --wp DOC-007` returns clean (exit code 0)
- [x] `git add -A` staged all changes
- [x] `git commit -m "DOC-007: Tester PASS"`
- [x] `git push origin DOC-007/agent-rules-template`

---

**Verdict: PASS — WP DOC-007 marked Done.**
