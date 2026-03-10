# Turbulence Solutions — Agent Environment Launcher

## Safety-First Mandate

This project has the highest security classification. Prioritize safety over convenience. When in doubt, choose the more restrictive option.

## Non-Negotiable Rules

- Every code change **MUST** reference a workpackage ID.
- No secrets, credentials, or API keys in source code — ever.
- Never access `.github/`, `.vscode/`, or `NoAgentZone/` in `Default-Project/` unless your workpackage explicitly requires it.
- One agent/person per workpackage. One workpackage per branch.
- When uncertain, stop and ask — do not guess.
- **All agent operations are fully autonomous once kicked off by the Orchestrator.** Never prompt for user input, never run interactive commands, never require human approval during WP execution. Exceptions: Story Writer (human approval before saving stories), Maintenance agent (human approval before implementing fixes).
- **No global Python package installs.** All dependencies go into the workspace-local `.venv`. Ask the user before any global install.
- **Test scripts are permanent.** The final test script for each workpackage lives in `tests/<WP-ID>/` and must never be deleted.

## Key Files

| File | Purpose |
|------|---------|
| `docs/architecture.md` | Project overview and repository structure |
| `docs/project-scope.md` | Vision, capabilities, technology stack |
| `docs/workpackages/workpackages.csv` | Task tracking — single source of truth |
| `docs/user-stories/user-stories.csv` | User stories |
| `docs/bugs/bugs.csv` | Bug tracking |
| `docs/test-results/test-results.csv` | Test execution records |
| `Default-Project/` | Template shipped to users — **never modify for testing** |

## Rules & Workflows

All detailed rules, workflows, and protocols are in **`docs/work-rules/index.md`** — the central hub. Read it to find the specific rule file for your task.

## For AI Agents

1. Read `docs/work-rules/agent-workflow.md` for your onboarding checklist and execution protocol.
2. Read `docs/workpackages/workpackages.csv` to see current project state.
3. Read the rule file(s) relevant to your assigned task (find them via `docs/work-rules/index.md`).
