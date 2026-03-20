# Agent Helper Scripts

CLI tools that automate error-prone bookkeeping tasks. **Agents MUST use these scripts** instead of editing CSVs manually for the operations they cover.

All scripts are non-interactive, use file locking for parallel safety, and run via the workspace `.venv`.

---

## Quick Reference

| Script | Purpose | Replaces |
|--------|---------|----------|
| `add_test_result.py` | Add test result row with auto TST-ID | Manual CSV editing for test results |
| `add_workpackage.py` | Create WP with auto ID + US cross-ref | Manual CSV editing + forgetting US Linked WPs update |
| `add_bug.py` | Log bug with auto BUG-ID | Manual CSV editing for bugs |
| `validate_workspace.py` | Pre-commit integrity checker | Manual checklist verification |
| `finalize_wp.py` | Post-Done merge, cleanup, cascades | 10-step manual Post-Done Finalization |
| `update_architecture.py` | Regenerate architecture.md tree | Manual architecture.md updates |

---

## Usage

All commands assume you're in the repository root.

### add_test_result.py

```powershell
.venv\Scripts\python scripts/add_test_result.py `
    --name "test_foo_bar" `
    --type Unit `
    --wp GUI-001 `
    --status Pass `
    --env "Windows 11 + Python 3.13" `
    --result "5 passed / 0 failed" `
    --notes "Optional notes"
```

**Mandatory for:** Developer (Step 5) and Tester (Step 9). Direct CSV editing for test results is prohibited.

### add_workpackage.py

```powershell
.venv\Scripts\python scripts/add_workpackage.py `
    --category GUI `
    --name "Button Hover State" `
    --description "Add hover colour change" `
    --goal "Buttons change colour on hover" `
    --user-story US-007
```

Automatically updates the parent User Story's `Linked WPs` column.

### add_bug.py

```powershell
.venv\Scripts\python scripts/add_bug.py `
    --title "Button does not respond" `
    --severity High `
    --reported-by "Tester Agent" `
    --description "Click handler missing" `
    --steps "1. Click Create  2. Nothing happens" `
    --expected "Project created" `
    --actual "No response"
```

### validate_workspace.py

```powershell
# Full workspace validation (maintenance, pre-release)
.venv\Scripts\python scripts/validate_workspace.py --full

# Single WP validation (before handoff/commit)
.venv\Scripts\python scripts/validate_workspace.py --wp GUI-001
```

**Mandatory for:** Developer (before handoff) and Tester (before marking Done). Must return exit code 0.

Checks: duplicate IDs across all CSVs, missing artifacts (dev-log, test-report, test dir), un-cascaded bug/US statuses, branch naming.

### finalize_wp.py

```powershell
# Execute finalization
.venv\Scripts\python scripts/finalize_wp.py GUI-001

# Preview without executing
.venv\Scripts\python scripts/finalize_wp.py GUI-001 --dry-run
```

**Mandatory for:** Orchestrator (after Tester PASS). Replaces the entire Post-Done Finalization section.

Steps performed: validate → merge to main → delete branch → cascade US status → cascade bug status → sync architecture.md → commit cascades → verify no stale branches.

### update_architecture.py

```powershell
.venv\Scripts\python scripts/update_architecture.py
.venv\Scripts\python scripts/update_architecture.py --dry-run
```

Usually called automatically by `finalize_wp.py`. Can also be run standalone.

---

## Parallel Safety

All scripts use `FileLock` (atomic lock file creation) to prevent race conditions when multiple agents modify the same CSV simultaneously. The `locked_next_id_and_append()` function in `csv_utils.py` atomically reads the current max ID, computes the next one, and appends the row — all within a single lock.

---

## Shared Module: csv_utils.py

Internal module used by all scripts. Key exports:

- `FileLock(path)` — cross-platform file lock context manager
- `read_csv(path)` → `(fieldnames, rows)` — read CSV into dicts
- `write_csv(path, fieldnames, rows)` — write CSV preserving quoting style
- `next_id(path, prefix)` — get next sequential ID (no lock)
- `append_row(path, row)` — append with duplicate check (locked)
- `update_cell(path, id_col, id_val, target_col, new_val)` — update one cell (locked)
- `locked_next_id_and_append(path, prefix, row)` — atomic ID assign + append (locked)
