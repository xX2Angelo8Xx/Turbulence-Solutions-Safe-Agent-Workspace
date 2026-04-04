# {{WORKSPACE_NAME}} — Safe Agent Workspace

AI agents work inside `{{PROJECT_NAME}}/` — your project folder, fully accessible to agents by default.

> **Agent orientation:** See `AgentDocs/AGENT-RULES.md` in your project folder for the full agent rules.

This workspace uses the Turbulence Solutions safe-agent framework. A **PreToolUse hook** enforces three security tiers that control where AI agents can read and write files.

## Security Tiers

| Tier | Zone | Behaviour |
|------|------|-----------|
| **Tier 1 — Auto-Allow** | Project folder | Read/write tools targeting `{{PROJECT_NAME}}/` proceed without a dialog |
| **Tier 2 — Force Ask** | `.github/`, `.vscode/`, workspace root | Operations outside `{{PROJECT_NAME}}/` trigger an approval dialog |
| **Tier 3 — Hard Block** | `NoAgentZone/` | All agent operations are blocked — no exceptions |

### Exempt Tools

Tools such as `read_file` that target paths inside `{{PROJECT_NAME}}/` are auto-allowed.

## Workspace Structure

| Folder | Purpose |
|--------|---------|
| Your Project/ | Your project folder. AI agents work here (see Tier 1 above). |
| AgentDocs/ | Shared knowledge base for agents and humans. Central source of truth. |
| `NoAgentZone/` | Private files. AI agents cannot access this folder. |
| `.github/` | Workspace configuration. Do not modify. |
| `.vscode/` | VS Code settings. Do not modify. |

## Getting Started

Place your project files in your project folder. Open Copilot Chat and start a conversation — agents will work within that folder.

