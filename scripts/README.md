# Agent Helper Scripts

CLI tools that automate error-prone bookkeeping tasks. **Agents MUST use these scripts** instead of editing JSONL files manually for the operations they cover.

All scripts are non-interactive, use file locking for parallel safety, and run via the workspace `.venv`.

---

## Quick Reference

| Script | Purpose | Replaces |
|--------|---------|----------|
| `build_windows.py` | Build the Windows installer locally (mirrors CI) | Running each build step manually |
| `run_tests.py` | **Mandatory.** Run pytest + auto-log results | Manual test execution + `add_test_result.py` |
| `add_test_result.py` | Add test result row with auto TST-ID (fallback) | Manual JSONL editing for test results |
| `add_workpackage.py` | Create WP with auto ID + US cross-ref | Manual JSONL editing + forgetting US Linked WPs update |
| `add_bug.py` | Log bug with auto BUG-ID | Manual JSONL editing for bugs |
| `validate_workspace.py` | Pre-commit integrity checker (also runs as pre-commit hook) | Manual checklist verification |
| `finalize_wp.py` | Post-Done merge, cleanup, cascades (idempotent) | 10-step manual Post-Done Finalization |
| `update_architecture.py` | Regenerate architecture.md tree | Manual architecture.md updates |
| `install_hooks.py` | Set up tracked pre-commit hooks | Manual `git config` commands |
| `dedup_test_ids.py` | One-time TST-ID deduplication | Manual ID renumbering |
| `archive_test_results.py` | Archive old TST entries for Done WPs | Manual CSV pruning |

---

## Usage

All commands assume you're in the repository root.

### run_tests.py (Mandatory)

```powershell
# Run tests for a specific WP and auto-log the result
.venv\Scripts\python scripts/run_tests.py `
    --wp GUI-001 `
    --type Unit `
    --env "Windows 11 + Python 3.13"

# Run full regression suite
.venv\Scripts\python scripts/run_tests.py `
    --wp GUI-001 `
    --type Integration `
    --env "Windows 11 + Python 3.13" `
    --full-suite
```

**Mandatory for:** Developer (Step 5) and Tester (Step 2 & 5). This is the primary tool for running tests and logging results. It executes pytest, parses the output, and atomically logs the result to `test-results.jsonl`.

### add_test_result.py (Fallback)

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

Fallback for cases where `run_tests.py` cannot be used (e.g., manual testing, external tools). Direct JSONL editing for test results is prohibited.

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

Steps performed: verify remote origin → validate → merge to main → delete branch → cascade US status → cascade bug status → sync architecture.md → commit cascades → verify no stale branches.

Finalization is **idempotent** — if interrupted, re-running the command resumes from the last completed step. Use `--reset` to restart from scratch.

### update_architecture.py

```powershell
.venv\Scripts\python scripts/update_architecture.py
.venv\Scripts\python scripts/update_architecture.py --dry-run
```

Usually called automatically by `finalize_wp.py`. Can also be run standalone.

### install_hooks.py

```powershell
.venv\Scripts\python scripts/install_hooks.py
```

Sets `git config core.hooksPath scripts/hooks` so Git uses the tracked pre-commit hook. Run once after cloning the repository.

### dedup_test_ids.py

```powershell
# Preview changes
.venv\Scripts\python scripts/dedup_test_ids.py --dry-run

# Apply deduplication
.venv\Scripts\python scripts/dedup_test_ids.py
```

One-time utility to renumber duplicate TST-IDs in `test-results.jsonl`.

### archive_test_results.py

```powershell
# Preview archival
.venv\Scripts\python scripts/archive_test_results.py --dry-run

# Archive Done WP test results
.venv\Scripts\python scripts/archive_test_results.py
```

Moves test result entries for Done WPs to `docs/test-results/archived-test-results.jsonl` to keep the active JSONL small.

---

### build_windows.py

Builds the Windows installer locally by running the same three steps as the CI pipeline in `.github/workflows/release.yml`.

**Steps performed:**
1. PyInstaller — compiles `dist/launcher/launcher.exe` via `launcher.spec`
2. Python embed — downloads `python-3.11.9-embed-amd64.zip` into `src/installer/python-embed/` (skipped if files already present)
3. Inno Setup — locates `ISCC.exe` and compiles `src/installer/windows/setup.iss`

**Output:** `src/installer/windows/Output/AgentEnvironmentLauncher-Setup.exe`

```powershell
# Full build (PyInstaller + embed download + Inno Setup)
.venv\Scripts\python scripts/build_windows.py

# Skip PyInstaller (only installer/template files changed)
.venv\Scripts\python scripts/build_windows.py --skip-pyinstaller

# Skip Python embed download (already present in src/installer/python-embed/)
.venv\Scripts\python scripts/build_windows.py --skip-embed

# Dry run — print all steps without executing anything
.venv\Scripts\python scripts/build_windows.py --dry-run

# Combined flags
.venv\Scripts\python scripts/build_windows.py --skip-pyinstaller --skip-embed
```

**Prerequisites:** Inno Setup 6 must be installed. Download from https://jrsoftware.org/isdl.php (free). The script will print install instructions if `ISCC.exe` cannot be located.

---

## Setup (After Clone)

```powershell
# 1. Create virtual environment
python -m venv .venv

# 2. Install hooks
.venv\Scripts\python scripts/install_hooks.py
```

This ensures the pre-commit hook (which runs `validate_workspace.py --full`) is active.

---

## Parallel Safety

All scripts use `FileLock` (atomic lock file creation) to prevent race conditions when multiple agents modify the same JSONL file simultaneously. The `locked_next_id_and_append()` function in `jsonl_utils.py` atomically reads the current max ID, computes the next one, and appends the row — all within a single lock.

---

## Shared Module: jsonl_utils.py

Internal module used by all active scripts. Key exports:

- `FileLock(path)` — cross-platform file lock context manager
- `read_jsonl(path, expected_columns=None)` → `(fieldnames, rows)` — read JSONL into dicts
- `write_jsonl(path, fieldnames, rows)` — write JSONL
- `next_id(prefix, rows)` — get next sequential ID
- `update_cell(path, id_col, id_val, target_col, new_val)` — update one cell (locked)
- `locked_next_id_and_append(path, prefix, row_template, id_column, zero_pad)` — atomic ID assign + append (locked)

> **Note:** `csv_utils.py` is a legacy module retained only to support permanent regression test files
> from FIX-065 (which tested CSV overflow handling). It is not used by any active operational script.
