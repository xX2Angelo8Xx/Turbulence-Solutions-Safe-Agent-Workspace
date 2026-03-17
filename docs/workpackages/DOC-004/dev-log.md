# DOC-004 Developer Log — Update Project Folder README.md with Placeholders

## WP Info

| Field | Value |
|-------|-------|
| ID | DOC-004 |
| Branch | DOC-004/project-readme-placeholders |
| Developer | Developer Agent |
| Date | 2026-03-17 |
| User Story | US-023 |

---

## Summary

Updated both `Default-Project/Project/README.md` and `templates/coding/Project/README.md` to replace the hardcoded `# Project` H1 heading with `# {{PROJECT_NAME}}`. This placeholder is processed at project creation time by `replace_template_placeholders()` (implemented in DOC-001), which substitutes the actual project name chosen by the user.

---

## Files Changed

| File | Change |
|------|--------|
| `Default-Project/Project/README.md` | Replaced `# Project` with `# {{PROJECT_NAME}}` |
| `templates/coding/Project/README.md` | Replaced `# Project` with `# {{PROJECT_NAME}}` (identical to Default-Project) |
| `docs/workpackages/workpackages.csv` | Set DOC-004 status to `Review`; Assigned To = `Developer Agent` |
| `docs/test-results/test-results.csv` | Logged 13 unit/integration tests + 2 regression runs |
| `tests/DOC-004/test_doc004_project_readme_placeholders.py` | New test file — 13 tests |

---

## Implementation Details

The only hardcoded folder-name reference in both README files was the H1 heading `# Project`. All other text ("Turbulence Solutions projects", "Place your project files here") is generic and does not reference the folder name specifically.

The change is minimal and focused: one line per file changed from `# Project` to `# {{PROJECT_NAME}}`.

Both files are kept identical in content, as required by the WP description and tested by `test_both_readmes_are_identical`.

---

## Tests Written

File: `tests/DOC-004/test_doc004_project_readme_placeholders.py`

| Test | Type | Description |
|------|------|-------------|
| `test_default_readme_exists` | Unit | Default-Project README exists on disk |
| `test_default_readme_contains_project_name_placeholder` | Unit | `{{PROJECT_NAME}}` token present |
| `test_default_readme_h1_uses_placeholder` | Unit | H1 heading is `# {{PROJECT_NAME}}` |
| `test_default_readme_no_hardcoded_project_heading` | Unit | No bare `# Project` line present |
| `test_template_readme_exists` | Unit | templates/coding README exists |
| `test_template_readme_contains_project_name_placeholder` | Unit | `{{PROJECT_NAME}}` token present |
| `test_template_readme_h1_uses_placeholder` | Unit | H1 heading is `# {{PROJECT_NAME}}` |
| `test_template_readme_no_hardcoded_project_heading` | Unit | No bare `# Project` line present |
| `test_both_readmes_are_identical` | Unit | Both files have identical content |
| `test_replace_placeholder_substitutes_project_name` | Integration | `replace_template_placeholders()` replaces token |
| `test_replace_placeholder_produces_correct_heading` | Integration | Heading becomes `# Falcon` after replacement |
| `test_replace_placeholder_works_with_hyphenated_name` | Integration | Hyphenated name works correctly |
| `test_replace_placeholder_idempotent_after_no_placeholder` | Integration | No-op when no placeholders present |

**Result:** 13/13 passed.

---

## Test Run Results

- DOC-004 suite: 13/13 passed
- Full regression: 3111 passed / 2 pre-existing failures / 29 skipped / 1 xfailed
  - Pre-existing failures: `test_no_duplicate_tst_ids` (FIX-009, TST-1557 dup from GUI-017) and `test_uninstall_delete_type_is_filesandirs` (INS-005, BUG-045)
  - Zero new failures introduced by DOC-004

---

## Decisions Made

- Only the H1 heading `# Project` was changed to `# {{PROJECT_NAME}}`. Generic references to "project" in body text were intentionally left unchanged as they are not folder-name references.
- Both files kept identical as they serve the same purpose (Default-Project is the canonical template; templates/coding/ is the installed copy).

---

## Known Limitations

None. The change is a targeted one-line-per-file placeholder substitution.
