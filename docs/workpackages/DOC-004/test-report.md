# Test Report — DOC-004

**Tester:** Tester Agent
**Date:** 2026-03-17
**Iteration:** 1

---

## Summary

DOC-004 performed a text-only substitution of `# Project` → `# {{PROJECT_NAME}}` in both
`Default-Project/Project/README.md` and `templates/coding/Project/README.md`. The
substitution was mechanically correct but the implementation is **structurally broken**:

- Both README files are prefixed with a foreign German session README ("Mathematik Demo
  (Streamlit)") that was written into the templates by a prior session without a trailing
  newline.
- As a consequence, `# {{PROJECT_NAME}}` is **not** on its own line — it is appended to
  the end of the final bullet point of the German content on line 27:
  `- \`app.py\`: …Sinuswellen).# {{PROJECT_NAME}}`
- In Markdown, a `#` prefix only creates an H1 heading when it starts a line by itself.
  The placeholder therefore has **no visible effect as a heading** in rendered Markdown.
- The real H1 heading of both files is `# Mathematik Demo (Streamlit)` — every new project
  created from these templates will inherit this wrong heading.
- The Developer's 13 tests passed because they only checked `"# {{PROJECT_NAME}}" in content`
  (substring), not that the placeholder is a **standalone line** or the **first heading**.

**Verdict: FAIL — return to Developer.**

---

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| test_default_readme_exists | Unit | Pass | File present on disk |
| test_default_readme_contains_project_name_placeholder | Unit | Pass | Substring check only — insufficient |
| test_default_readme_h1_uses_placeholder | Unit | Pass | Substring check only — insufficient |
| test_default_readme_no_hardcoded_project_heading | Unit | Pass | No bare `# Project` line |
| test_template_readme_exists | Unit | Pass | File present on disk |
| test_template_readme_contains_project_name_placeholder | Unit | Pass | Substring check only — insufficient |
| test_template_readme_h1_uses_placeholder | Unit | Pass | Substring check only — insufficient |
| test_template_readme_no_hardcoded_project_heading | Unit | Pass | No bare `# Project` line |
| test_both_readmes_are_identical | Unit | Pass | Both files are equal (both broken the same way) |
| test_replace_placeholder_substitutes_project_name | Integration | Pass | Substring match passes on broken file |
| test_replace_placeholder_produces_correct_heading | Integration | Pass | Substring match passes on broken file |
| test_replace_placeholder_works_with_hyphenated_name | Integration | Pass | Substring match passes on broken file |
| test_replace_placeholder_idempotent_after_no_placeholder | Integration | Pass | No-op — correct |
| **test_default_readme_placeholder_is_standalone_line** | Unit | **FAIL** | `# {{PROJECT_NAME}}` is NOT a standalone line — embedded in bullet point |
| **test_template_readme_placeholder_is_standalone_line** | Unit | **FAIL** | Same issue in templates/coding/Project/README.md |
| **test_default_readme_first_nonempty_line_is_placeholder** | Unit | **FAIL** | First H1 is `# Mathematik Demo (Streamlit)` |
| **test_template_readme_first_nonempty_line_is_placeholder** | Unit | **FAIL** | First H1 is `# Mathematik Demo (Streamlit)` |
| **test_default_readme_has_exactly_one_h1** | Unit | **FAIL** | Found 2 H1 headings; expected 1 |
| **test_template_readme_has_exactly_one_h1** | Unit | **FAIL** | Found 2 H1 headings; expected 1 |
| **test_default_readme_no_german_content** | Unit | **FAIL** | German "Mathematik Demo" content present |
| **test_template_readme_no_german_content** | Unit | **FAIL** | German "Mathematik Demo" content present |
| **test_replacement_produces_standalone_heading** | Integration | **FAIL** | `# TestProject` not a standalone line after replacement |
| **test_replacement_removes_all_non_template_content** | Integration | **FAIL** | German content persists after replacement |

**Full regression:** 10 failed / 3113 passed / 29 skipped / 1 xfailed
- 8 new failures from DOC-004 edge-case tests (all documented above)
- 2 pre-existing failures (FIX-009: TST-1557 dup; INS-005: BUG-045) — unchanged

---

## Bugs Found

- **BUG-053**: Project README template files contain stray German session content and broken
  H1 heading (logged in `docs/bugs/bugs.csv`)

---

## Root Cause Analysis

The pre-existing state of `Default-Project/Project/README.md` (and its copy in
`templates/coding/`) was corrupted by a prior session that appended a German "Mathematik
Demo (Streamlit)" README to the top of the file without ensuring the previously-existing
`# Project` heading (from the Turbulence Solutions boilerplate) received a preceding newline.
The result was a single line combining the tail of the German content with the H1 heading:

```
- `app.py`: Streamlit-App mit zwei kleinen Demos (Quadratische Funktion, Sinuswellen).# Project
```

The DOC-004 Developer correctly identified that `# Project` must become `# {{PROJECT_NAME}}`,
but performed a simple `str.replace` without examining the raw file structure (checking that
the heading was correctly positioned on its own line as a proper Markdown H1). A visual or
structural inspection would have revealed the issue immediately.

---

## TODOs for Developer

- [ ] **Fix file structure of both README files** — remove all stray German content
  (lines 1–26, the "Mathematik Demo (Streamlit)" section) from:
  - `Default-Project/Project/README.md`
  - `templates/coding/Project/README.md`
  The correct file content must begin with `# {{PROJECT_NAME}}` on its first line, followed
  by a blank line, then the Turbulence Solutions boilerplate text that is already present
  from line 28 onward.
  
  **Target file content (both files):**
  ```markdown
  # {{PROJECT_NAME}}
  
  This is the designated working directory for Turbulence Solutions projects.
  
  ## Agent Permissions
  
  AI agent tools (read, edit, search, etc.) are **auto-allowed** in this folder — no approval dialog is shown for exempt tools. This enables efficient AI-assisted development.
  
  Non-exempt tools (terminal commands, external tools) still require manual approval.
  
  ## Getting Started
  
  Place your project files here. The folder structure is up to you.
  ```

- [ ] **Verify `# {{PROJECT_NAME}}` is the first non-empty line** of both files after the fix.

- [ ] **Verify both files are identical** after the fix.

- [ ] **Run all 21 tests in `tests/DOC-004/`** (13 Developer + 8 Tester edge-case tests).
  All 21 must pass before setting the WP back to `Review`.

- [ ] **Run the full regression suite** and confirm no regressions beyond the 2 pre-existing
  failures (TST-1557 dup, INS-005 BUG-045).

---

## Verdict

**FAIL — return to Developer.**

DOC-004 status set back to `In Progress`. The Developer must fix the file structure of both
README template files per the TODOs above, then re-run all tests before re-submitting for
review.
