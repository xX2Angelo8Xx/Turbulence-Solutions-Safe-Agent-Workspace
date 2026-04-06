# Turbulence Solutions – Copilot Instructions

## Workspace Layout

You work inside `{{PROJECT_NAME}}/` — one layer below the workspace root `{{WORKSPACE_NAME}}/`.

- **Full access:** `{{PROJECT_NAME}}/` — read, create, edit, delete files, run terminal commands, git operations.
- **Restricted:** Everything outside `{{PROJECT_NAME}}/` is denied unless specifically allowed.
- **Partial read-only:** `.github/` — individual files inside `instructions/`, `skills/`, `agents/`, `prompts/` may be read. `list_dir` on `.github/` and all writes are denied. `hooks/` is fully denied.
- **Off-limits:** `.vscode/`, `NoAgentZone/` — permanent deny. Do not access, do not retry.

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
| `semantic_search` in a fresh workspace (no results before VS Code indexing completes) | Use `grep_search` with `includePattern: "{{PROJECT_NAME}}/**"` until indexing finishes |

## AgentDocs

`{{PROJECT_NAME}}/AgentDocs/` is the shared knowledge base for agents and humans. All agents read and write to these documents as they work.

See `{{PROJECT_NAME}}/AgentDocs/README.md` for the philosophy, document registry, and contribution rules.

## Agents

Specialist agents are in `.github/agents/`. See `.github/agents/README.md` for the full agent roster and when-to-use guidance. Invoke with `@<agent-name>` in chat.
