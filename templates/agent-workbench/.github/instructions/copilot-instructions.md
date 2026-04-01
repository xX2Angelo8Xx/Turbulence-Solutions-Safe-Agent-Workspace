# Turbulence Solutions – Copilot Instructions

## Workspace Layout

You work inside `{{PROJECT_NAME}}/` — one layer below the workspace root `{{WORKSPACE_NAME}}/`.

- **Full access:** `{{PROJECT_NAME}}/` — read, create, edit, delete files, run terminal commands, git operations.
- **Restricted:** Everything outside `{{PROJECT_NAME}}/` is denied unless specifically allowed.
- **Off-limits:** `.github/`, `.vscode/`, `NoAgentZone/` — permanent deny. Do not access, do not retry.

## First Action

Read `{{PROJECT_NAME}}/AgentDocs/AGENT-RULES.md` for your complete permissions, tool rules, and boundaries.

## Security

- Denied actions are **permanent and non-negotiable**. Do NOT retry denied actions.
- Do NOT use terminal commands to bypass denied tool calls.
- If you are a subagent and your action is denied, report back to your parent and stop.

## Known Tool Limitations

| Blocked | Use Instead |
|---------|-------------|
| `Out-File` | `Set-Content` or `>` redirect |
| `dir` / `ls` / `Get-ChildItem` (no path argument) | `list_dir` tool |
| `Get-ChildItem -Recurse` (no path argument) | `list_dir` tool or `file_search` tool |
| `pip install` via terminal | `install_python_packages` tool |
| Venv activation (`.\venv\Scripts\activate`) | Run `.venv\Scripts\python.exe` directly |
| Venv python (`venv\Scripts\python.exe -c "..."`) | Use system `python` command |

## Agents

Specialist agents are in `.github/agents/`. Invoke with `@<agent-name>` in chat.
