# DOC-042 Dev Log — Update agent default model and tools settings

**WP:** DOC-042  
**Branch:** DOC-042/agent-settings  
**Assigned To:** Developer Agent  
**Date:** 2026-03-31  

---

## Summary

Update all 7 agent-workbench template agents in `templates/agent-workbench/.github/agents/` with:
- Switch 6 agents from `Claude Opus 4.6 (copilot)` to `Claude Sonnet 4.6 (copilot)` (Planner stays Opus)
- Expand tool lists per agent to include `vscode/memory`, `vscode/vscodeAPI`, `vscode/askQuestions`, and agent-specific additions

Changes were authored by the user directly in the working tree and verified correct via `git diff HEAD`.

---

## Implementation

No code was written by the Developer Agent — the user already made all required edits. The Developer Agent's role was to verify correctness, create tests, and formalize through the WP lifecycle.

### Files Modified by User

| File | Model Change | Tools Change |
|------|-------------|-------------|
| `brainstormer.agent.md` | Opus → Sonnet | `[read, search, edit]` → `[vscode/memory, vscode/vscodeAPI, vscode/askQuestions, read, agent, edit, search, web/fetch, browser]` |
| `coordinator.agent.md` | Opus → Sonnet | No change (already correct) |
| `planner.agent.md` | Stays Opus | `[read, search, ask, edit]` → `[vscode/memory, vscode/vscodeAPI, vscode/askQuestions, read, agent, edit, search]` |
| `programmer.agent.md` | Opus → Sonnet | `[read, edit, search, execute]` → `[vscode/memory, vscode/vscodeAPI, vscode/askQuestions, execute, read, agent, edit, search, todo]` |
| `researcher.agent.md` | Opus → Sonnet | `[read, search, fetch, edit]` → `[vscode/memory, vscode/vscodeAPI, vscode/askQuestions, read, agent, edit, search, web, browser]` |
| `tester.agent.md` | Opus → Sonnet | `[read, edit, search, execute]` → `[vscode/memory, vscode/vscodeAPI, vscode/askQuestions, execute, read, edit, search, todo]` |
| `tidyup.agent.md` | Opus → Sonnet | `[read, search, edit, execute]` → `[vscode/memory, vscode/vscodeAPI, vscode/askQuestions, execute, read, agent, edit, search, todo]` |

---

## Tests Written

- `tests/DOC-042/test_doc042_agent_settings.py` — 18 unit tests validating:
  - All 7 agent files exist
  - 6 agents use Sonnet; Planner uses Opus
  - Each agent's tools list contains all expected tools
  - Coordinator has the `agents:` field listing all 6 specialist agents
  - Tidyup has the `argument-hint` field

---

## Test Results

All 18 tests passed on Windows 11 + Python 3.11.

---

## Acceptance Criteria Check

- [x] All 7 template agent files reflect updated model settings
- [x] 6 agents use `Claude Sonnet 4.6 (copilot)`, Planner retains `Claude Opus 4.6 (copilot)`
- [x] All agents have expanded tool lists including `vscode/memory`, `vscode/vscodeAPI`, `vscode/askQuestions`
- [x] Newly created workspaces will use the updated defaults

---

## Iteration 2 — BUG-166 Fix (2026-03-31)

**Tester returned WP:** Tester found the `argument-hint` field in `coordinator.agent.md` had an unclosed double-quoted string, causing `yaml.safe_load()` to raise a `ScannerError`. 6 of 21 edge-case tests failed as a result.

**Fix applied:** Added missing closing `"` to line 7 of `templates/agent-workbench/.github/agents/coordinator.agent.md`.

**Before:**
```yaml
argument-hint: "Describe the goal or plan you want to autonomously be worked on. 
```

**After:**
```yaml
argument-hint: "Describe the goal or plan you want to autonomously be worked on."
```

**Test result:** All 41 tests pass (TST-2381). BUG-166 fixed in this iteration.
- [x] No unrelated files modified
