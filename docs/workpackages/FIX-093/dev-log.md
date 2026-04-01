# Dev Log — FIX-093

## Workpackage
**ID:** FIX-093  
**Name:** Fix index.md formatting and add branch deletion rule  
**Branch:** FIX-093/doc-fixes  
**Assigned To:** Developer Agent  
**Date:** 2026-04-01  

---

## Summary

Two documentation fixes:
1. Fixed concatenated table rows in `docs/work-rules/index.md` line 20.
2. Added explicit post-merge branch deletion section to `docs/work-rules/commit-branch-rules.md`.

---

## Implementation

### Fix 1 — index.md table formatting

**File:** `docs/work-rules/index.md`

Line 20 had two table rows merged on a single line without a newline separator:
```
| Onboard as an AI agent | [agent-workflow.md](agent-workflow.md) || Use a helper script | [../scripts/README.md](../../scripts/README.md) |
```

Split into two separate rows:
```
| Onboard as an AI agent | [agent-workflow.md](agent-workflow.md) |
| Use a helper script | [../scripts/README.md](../../scripts/README.md) |
```

### Fix 2 — commit-branch-rules.md branch deletion rule

**File:** `docs/work-rules/commit-branch-rules.md`

Added an explicit `## Branch Deletion (Mandatory)` section reinforcing the rule already present in `copilot-instructions.md`. This makes the requirement visible in the commit/branch rules document itself, reducing recurrence of stale branches (5 consecutive maintenance cycles).

---

## Files Changed

- `docs/work-rules/index.md`
- `docs/work-rules/commit-branch-rules.md`
- `docs/workpackages/workpackages.csv`
- `docs/workpackages/FIX-093/dev-log.md` (this file)
- `tests/FIX-093/test_fix093_doc_fixes.py`

---

## Tests Written

- `tests/FIX-093/test_fix093_doc_fixes.py`
  - `test_index_md_no_concatenated_rows`: Verifies no line in index.md contains two table rows concatenated (pattern `| |` between two cell separators without a newline).
  - `test_index_md_all_rows_on_own_lines`: Verifies "Onboard as an AI agent" and "Use a helper script" rows each appear on their own separate line.
  - `test_commit_branch_rules_has_deletion_section`: Verifies commit-branch-rules.md contains a branch deletion section.
  - `test_commit_branch_rules_deletion_covers_local_and_remote`: Verifies the deletion rule mentions both local and remote deletion.

---

## Known Limitations

None. Documentation-only change.
