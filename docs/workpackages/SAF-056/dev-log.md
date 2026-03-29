# SAF-056 Dev Log — Update AGENT-RULES for `.venv` and copilot-instructions reality

## WP Info

| Field | Value |
|-------|-------|
| ID | SAF-056 |
| Category | SAF |
| User Story | US-060 |
| Depends On | SAF-055 |
| Branch | SAF-056/agent-rules-update |
| Assigned To | Developer Agent |
| Status | Review |

## Goal

Update `AGENT-RULES.md` §4 to note that system Python is acceptable when no `.venv` exists.
Verify `copilot-instructions.md` is minimal — just a pointer to `AGENT-RULES.md`.

## Bug Reference

- BUG-145: No `.venv` Python environment despite AGENT-RULES reference

## Implementation Summary

### Changes Made

1. **`templates/agent-workbench/Project/AGENT-RULES.md`**
   - Section 4 (Terminal Rules) — expanded the Python example block to document that `.venv\Scripts\python` is preferred when a virtual environment exists, but system Python is acceptable when no `.venv` is present.

2. **`templates/agent-workbench/.github/instructions/copilot-instructions.md`**
   - Removed generic "Coding Standards" and "Communication" sections that duplicated material covered comprehensively in AGENT-RULES.md.
   - Added an explicit note that AGENT-RULES.md is the comprehensive reference.
   - File remains a concise pointer/quick-reference rather than a duplicate rule book.

### Decisions

- AGENT-RULES.md `§4 Terminal Rules` was the correct section to update (it contains the Python command examples).
- The copilot-instructions.md trimming removed ~10 lines of generic advice; the file is now a clean pointer with security essentials only.
- No file moves were needed (SAF-055 already whitelisted `.github/instructions/`).

## Files Changed

- `docs/workpackages/workpackages.csv` (status → In Progress)
- `templates/agent-workbench/Project/AGENT-RULES.md`
- `templates/agent-workbench/.github/instructions/copilot-instructions.md`
- `tests/SAF-056/test_saf056_agent_rules.py` (new)
- `docs/bugs/bugs.csv` (BUG-145 Fixed In WP → SAF-056)

## Tests Written

| Test | Description |
|------|-------------|
| `test_agent_rules_exists` | AGENT-RULES.md exists and is non-empty |
| `test_agent_rules_system_python_mentioned` | AGENT-RULES.md contains language about system Python being acceptable |
| `test_agent_rules_venv_preferred` | AGENT-RULES.md still documents `.venv\Scripts\python` as the preferred command |
| `test_copilot_instructions_exists` | copilot-instructions.md exists and is non-empty |
| `test_copilot_instructions_references_agent_rules` | copilot-instructions.md references AGENT-RULES.md |
| `test_copilot_instructions_reasonably_short` | copilot-instructions.md line count is within reasonable bounds (<= 80 lines) |
| `test_copilot_instructions_not_duplicate_rules` | copilot-instructions.md does not duplicate large rule sections from AGENT-RULES.md |

## Test Results

See `docs/test-results/test-results.csv` for logged result.
