# ADR-007: Migrate from CSV to JSONL for All Data Files

## Status

Active

## Date

2026-04-04

## Context

The project uses CSV files as its single source of truth for workpackages, user stories, bugs, test results, ADR index, and orchestrator runs. Over the project's lifecycle, CSV has caused recurring problems:

- **Corruption incidents**: FIX-059, FIX-060, FIX-065 all addressed CSV structural corruption (overflow columns, misaligned rows, quoting failures).
- **Defensive infrastructure**: `csv_utils.py` grew to 160+ lines of defensive code (file locking, `QUOTE_ALL`, atomic write-verify-rename, overflow detection, bare newline rejection).
- **Agent friction**: Agents are forbidden from editing CSVs directly and must use wrapper scripts. PowerShell string escaping conflicts with inline Python make CSV manipulation harder in terminal contexts.
- **Merge conflicts**: CSV diffs are whole-line rewrites with quoting noise, making git conflicts frequent and hard to resolve.
- **Nested data impossible**: Fields like `Depends On` (comma-separated WP IDs) and `Comments` (free text with commas) require quoting gymnastics that are the root cause of most corruption.
- **Repair tooling**: `_repair_csvs.py` exists solely as an emergency CSV repair tool.

The project is at ~30% completion. A format change now avoids compounding the problem over the remaining 70% of development, including a planned second template (certification-pipeline) which will expand the data volume.

## Decision

Migrate all 7 CSV data files to JSON Lines (`.jsonl`) format:

| Old Path | New Path |
|----------|----------|
| `docs/workpackages/workpackages.csv` | `docs/workpackages/workpackages.jsonl` |
| `docs/user-stories/user-stories.csv` | `docs/user-stories/user-stories.jsonl` |
| `docs/bugs/bugs.csv` | `docs/bugs/bugs.jsonl` |
| `docs/test-results/test-results.csv` | `docs/test-results/test-results.jsonl` |
| `docs/decisions/index.csv` | `docs/decisions/index.jsonl` |
| `docs/maintenance/orchestrator-runs.csv` | `docs/maintenance/orchestrator-runs.jsonl` |
| `docs/test-results/archived-test-results.csv` | `docs/test-results/archived-test-results.jsonl` |

Replace `scripts/csv_utils.py` with `scripts/jsonl_utils.py` providing the same interface (read, write, append, update, lock, next_id).

### JSONL Format

Each line is a self-contained JSON object. Example for workpackages:

```jsonl
{"ID": "GUI-001", "Category": "GUI", "Name": "Main Window Layout", "Status": "Done", ...}
{"ID": "GUI-002", "Category": "GUI", "Name": "Project Type Selection", "Status": "Done", ...}
```

### Why JSONL over JSON, YAML, TOML, or SQLite

| Format | Verdict | Reason |
|--------|---------|--------|
| **JSON** (single file) | Rejected | Entire file must be rewritten on append; merge conflicts on every change; not streamable |
| **YAML** | Rejected | Indentation-sensitive; multiline strings fragile; slower parsing; no append semantics |
| **TOML** | Rejected | Not designed for tabular data; no standard array-of-tables append pattern |
| **SQLite** | Rejected | Binary file — no git diff, no human readability, no merge capability |
| **JSONL** | **Chosen** | Line-per-record (clean diffs); append-only natural; each line self-contained (corruption-isolated); trivial parsing (`json.loads(line)`); native nested data; VS Code extensions available |

## Consequences

### Positive
- Eliminates all CSV quoting/escaping corruption vectors
- Clean git diffs (only changed lines appear)
- Fewer merge conflicts (append-only is natural)
- Nested data support (arrays for `Depends On`, `Linked WPs`)
- Simpler parsing — no csv module edge cases
- Each line is self-contained — a corrupt line cannot damage other records
- `_repair_csvs.py` becomes unnecessary

### Negative
- ~55 files must be updated (scripts, docs, agents, tests)
- Raw readability slightly worse than CSV in a text editor (no column alignment)
- VS Code needs a JSONL extension for table-like viewing
- Historical maintenance logs reference CSV paths (left as-is — historical records)

### Migration Rules
1. All 7 data files converted in one coordinated batch — no mixed CSV/JSONL state
2. `csv_utils.py` replaced by `jsonl_utils.py` with identical public interface
3. All agent definitions, work-rules docs, and copilot-instructions updated
4. All test files updated to use new paths and utilities
5. Old CSV files deleted — not kept alongside JSONL
6. Historical maintenance logs are NOT updated (they document past state)

**Related WPs:** MNT-014, MNT-015, MNT-016, MNT-017, MNT-018, MNT-019, MNT-020, MNT-021, MNT-022, MNT-023
