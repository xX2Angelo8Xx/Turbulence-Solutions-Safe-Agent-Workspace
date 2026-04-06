# {{PROJECT_NAME}}

Welcome to your project folder. AI agents have full read/write access here (Tier 1 — Auto-Allow).

> **Always read `AGENT-RULES.md` at the start of each session** before taking any other action. It defines your complete permissions, boundaries, tool rules, and known workarounds.

## Zone Summary

| Location | Agent Access |
|----------|-------------|
| `{{PROJECT_NAME}}/` (this folder) | Full read/write — no approval dialog |
| Workspace root, `.github/`, `.vscode/` | Restricted — approval required for writes |
| `NoAgentZone/` | Hard-blocked — no reads or writes |

## Getting Started

Place your source files here. Agents have full read/write access to this folder.

## Quick Tips

- Always read `AGENT-RULES.md` at the start of each session
- Keep your work confined to this folder unless you need workspace-level git operations
- Use `NoAgentZone/` for private files that agents must never access
- Do not attempt to access `.github/hooks/` or `.vscode/` — those paths are permanently denied
