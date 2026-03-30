# DOC-031 Dev Log — Rewrite AGENT-RULES.md for v3.2.6

## Overview

**WP ID**: DOC-031  
**User Story**: US-067  
**Depends On**: SAF-062 (Done)  
**Branch**: `DOC-031/agent-rules-rewrite`  
**Assigned To**: Developer Agent  
**Status**: In Progress  

## Goal

Rewrite `templates/agent-workbench/Project/AGENT-RULES.md` to accurately reflect actual gate behavior with no discrepancies. Document must be significantly shorter (~40-50% reduction) and resolve all v3.2.5 feedback issues.

## Changes Made

### `templates/agent-workbench/Project/AGENT-RULES.md`
Complete rewrite addressing these issues:
1. **§1 Allowed Zone** — Added `.venv` creation via `python -m venv`, clarified system Python fallback
2. **§2 Denied Zones** — Fixed `.github/` description to reflect partial read access model (individual files in instructions/skills/agents/prompts CAN be read via `read_file`; `list_dir` denied; hooks/ fully denied; all writes denied)
3. **§3 Tool Permission Matrix** — Updated `read_file` and `list_dir` notes; confirmed memory tool is available
4. **§4 Terminal Rules** — Added `cmd /c` / `cmd.exe /c` to blocked commands; updated Python examples
5. **§5 Git Rules** — No changes (verified compliant)
6. **§6 Denial Counter** — Trimmed prose
7. **§7 Known Workarounds** — Trimmed stale entries
8. **§8 Available Agent Personas** — REMOVED (not security-relevant)

Line count reduced from ~200 to ~130 lines.

## Tests Written

- `tests/DOC-031/test_doc031_agent_rules.py` — 10 assertions covering:
  1. File exists
  2. Contains `{{PROJECT_NAME}}` placeholder
  3. Contains `{{WORKSPACE_NAME}}` placeholder
  4. Does NOT contain "blocked by design"
  5. Mentions `.github/` partial read access ("read-only" near ".github/")
  6. Mentions `cmd /c` in blocked commands
  7. Mentions `python -m venv`
  8. Does NOT contain "Available Agent Personas" or "§8"
  9. File has fewer than 150 lines
  10. Contains all key sections

## Test Results

All 10 tests pass. See `docs/test-results/test-results.csv`.
