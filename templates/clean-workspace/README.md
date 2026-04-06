# {{WORKSPACE_NAME}} — Clean Workspace

AI agents work inside `{{PROJECT_NAME}}/` — your project folder, fully accessible to agents by default.

> **Agent orientation:** See `{{PROJECT_NAME}}/AGENT-RULES.md` for the full agent rules.

This workspace uses the Turbulence Solutions safe-agent framework. A **PreToolUse hook** enforces three security tiers that control where AI agents can read and write files.

## Security Tiers

| Tier | Zone | Behaviour |
|------|------|-----------|
| **Tier 1 — Auto-Allow** | Project folder | Read/write tools targeting `{{PROJECT_NAME}}/` proceed without a dialog |
| **Tier 2 — Force Ask** | `.github/`, `.vscode/`, workspace root | Operations outside `{{PROJECT_NAME}}/` trigger an approval dialog |
| **Tier 3 — Hard Block** | `NoAgentZone/` | All agent operations are blocked — no exceptions |

## Workspace Structure

| Folder | Purpose |
|--------|---------|
| `{{PROJECT_NAME}}/` | Your project folder. AI agents work here (Tier 1 above). |
| `NoAgentZone/` | Private files. AI agents cannot access this folder. |
| `.github/` | Workspace configuration and security hook. Do not modify. |
| `.vscode/` | VS Code settings. Do not modify. |

## Getting Started

1. Place your project files in `{{PROJECT_NAME}}/`.
2. Open Copilot Chat and start a conversation — the AI agent will work within that folder.
3. If you want to store sensitive files (credentials, contracts, private data), put them in `NoAgentZone/` — agents are hard-blocked from reading or writing there.
4. To adjust agent rules for your project, edit `{{PROJECT_NAME}}/AGENT-RULES.md`.

## About This Template

This is a **clean workspace** — it includes only the security hook and essential settings, with no custom agents, prompts, or skills pre-configured. It gives you a minimal but secure starting point.

There are no `.github/agents/`, `.github/skills/`, or `.github/prompts/` folders. AI agents in this workspace run with platform defaults, operating within the three-tier security model above.
