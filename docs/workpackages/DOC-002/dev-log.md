# Dev Log — DOC-002: Update Default-Project README.md with Placeholders

**WP ID:** DOC-002  
**Branch:** DOC-002/readme-placeholders  
**Assigned To:** Developer Agent  
**Date:** 2026-03-17  

---

## Summary

Updated both README.md template files to use the `{{PROJECT_NAME}}` placeholder wherever
the folder structure and security zone descriptions previously hardcoded `Project/` as a
folder name. The `replace_template_placeholders()` function implemented in DOC-001 now
correctly resolves these placeholders at project-creation time.

---

## Files Changed

| File | Change |
|------|--------|
| `Default-Project/README.md` | Replaced 4 occurrences of `` `Project/` `` (folder name) with `` `{{PROJECT_NAME}}/` `` |
| `templates/coding/README.md` | Identical changes — both files kept in sync |
| `docs/workpackages/workpackages.csv` | DOC-002 status: Open → In Progress → Review; Assigned To set |
| `tests/DOC-002/test_doc002_readme_placeholders.py` | New test file (17 tests) |
| `docs/test-results/test-results.csv` | Test run entries TST-1589 and TST-1590 added |

---

## Implementation Notes

### Occurrences changed in each README.md

1. Folder structure table row — `` | `Project/` | Auto-allowed... `` → `` | `{{PROJECT_NAME}}/` | ... ``
2. Tier 1 Auto-Allow description — `Exempt tools targeting \`Project/\`` → `...targeting \`{{PROJECT_NAME}}/\``
3. Tier 2 Force Ask description — `Exempt tools outside \`Project/\`` → `...outside \`{{PROJECT_NAME}}/\``
4. Exempt Tools description — `auto-allowed inside \`Project/\`` → `...inside \`{{PROJECT_NAME}}/\``

### What was intentionally NOT changed

- The word "Project" used as a concept (e.g. "Working directory for all project files",
  "# Turbulence Solutions – Default Project Template") — these are descriptive English
  words, not folder name references.
- `NoAgentZone/`, `.github/`, `.vscode/` references — these are fixed paths, not dynamic.
- No `{{WORKSPACE_NAME}}` placeholder introduced: the current README has no existing
  reference to the `TS-SAE-{name}` workspace root folder name that required updating.

---

## Tests Written

**File:** `tests/DOC-002/test_doc002_readme_placeholders.py` (17 tests)

| Class | Tests | Purpose |
|-------|-------|---------|
| `TestTemplateFilesContainPlaceholder` | 8 | Static content checks on the actual template files |
| `TestPlaceholderReplacementInReadme` | 6 | Unit tests for `replace_template_placeholders()` with README-like content |
| `TestCreateProjectReadmePlaceholders` | 3 | Integration tests via `create_project()` |

---

## Test Results

- DOC-002 tests: **17/17 passed** (0 failures)
- Full suite: **3063 passed, 7 pre-existing failures, 29 skipped, 1 xfailed**
- Pre-existing failures: FIX-009 (test-results.csv integrity, 6 tests) + INS-005 (1 test) — unrelated to this WP
- No regressions introduced
