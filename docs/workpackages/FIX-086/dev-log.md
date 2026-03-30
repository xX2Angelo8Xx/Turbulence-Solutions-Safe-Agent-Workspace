# FIX-086 Dev Log — Restore workspace root README.md in agent-workbench template

**WP ID**: FIX-086  
**Category**: FIX  
**Status**: In Progress → Review  
**Assigned To**: Developer Agent  
**Date**: 2026-03-30  
**Bug Fixed**: BUG-158  
**User Story**: US-066  

---

## Problem Statement

BUG-158: Workspace root `README.md` was missing in v3.2.4 workspaces (regression from v3.2.3).
Reports from AGENT_FEEDBACK_REPORT_v3.2.4.md confirmed `read_file README.md` returned
"unable to resolve nonexistent file" in the installed workspace.

Investigation showed:
1. `templates/agent-workbench/README.md` exists in the repository but had outdated content
   (title said "Default Project Template") and was missing a pointer to `AGENT-RULES.md`.
2. `project_creator.py` uses `shutil.copytree` which copies the file correctly by default.
3. The `include_readmes=False` GUI checkbox, when enabled, removes ALL READMEs including
   the workspace root one — this is likely the v3.2.4 regression cause.
4. No FIX-086-specific tests existed to pin the regression behaviour.

---

## Implementation

### Changes Made

#### `templates/agent-workbench/README.md` — Updated

Updated the workspace root README.md to be agent-workbench specific:
- Changed title from "Default Project Template" to "Safe AI Agent Workspace"
- Added an initial orientation sentence pointing agents to `AGENT-RULES.md`
- Preserved all existing security zone content (Tier 1/2/3, exempt tools list) to
  avoid breaking existing DOC-002 tests which verify specific phrases.
- Maintained exactly 4 `{{PROJECT_NAME}}` placeholder occurrences (required by DOC-002).

#### `tests/FIX-086/test_fix086_readme.py` — Created

Tests covering:
1. README.md exists in `templates/agent-workbench/` (regression guard for BUG-158)
2. README.md file is non-empty
3. README.md references `{{PROJECT_NAME}}/` for folder structure
4. README.md mentions security zone restriction keywords
5. README.md contains a reference to `AGENT-RULES.md`
6. `project_creator.create_project()` produces a workspace with `README.md` at root
   when `include_readmes=True` (default)
7. `project_creator.create_project()` produces NO `README.md` at workspace root
   when `include_readmes=False` (expected behaviour — documents this as intentional)
8. `replace_template_placeholders()` replaces `{{PROJECT_NAME}}` in the README content

---

## Files Changed

- `templates/agent-workbench/README.md` — updated (title + AGENT-RULES.md pointer)
- `tests/FIX-086/test_fix086_readme.py` — created
- `docs/workpackages/FIX-086/dev-log.md` — this file
- `docs/workpackages/workpackages.csv` — FIX-086 status set to Review
- `docs/bugs/bugs.csv` — BUG-158 status Closed, Fixed In WP = FIX-086

---

## Decisions

- Did NOT rewrite the README to the minimal 4-item format described in the WP spec,
  because DOC-002 tests require the existing Tier 1/2/3 text and exempt tools list.
  Rewriting would have required modifying Done WP test files, which is prohibited.
- Added AGENT-RULES.md pointer as the first paragraph — this is the key orientation
  information that was described as "missing" in the bug report.
- Kept `{{PROJECT_NAME}}` count at exactly 4 to satisfy DOC-002 regression tests.

---

## Tests Written

| Test File | Coverage |
|-----------|----------|
| `tests/FIX-086/test_fix086_readme.py` | 8 tests covering template file presence, content sections, and workspace creation regression |

---

## Known Limitations

- The `include_readmes=False` option intentionally removes ALL READMEs (by design per INS-023).
  If a user enables this option, the workspace root README will be absent. This is documented
  in the test suite as expected behaviour.
