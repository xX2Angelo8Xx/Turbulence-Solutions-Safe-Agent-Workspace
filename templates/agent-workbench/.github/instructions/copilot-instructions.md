> [!IMPORTANT]
> **First Action — Read Rule Book:** Before any work, read `{{PROJECT_NAME}}/AGENT-RULES.md` for your complete permissions and rules. That file is the comprehensive reference for zone access, tool permissions, terminal rules, git rules, and known workarounds.

# Turbulence Solutions – Copilot Instructions

## Company

Turbulence Solutions

## Workspace Rules

- The `{{PROJECT_NAME}}/` folder is the designated working directory. Place all project files there.
- The `NoAgentZone/` folder is strictly off-limits. Never read, write, or reference files in it.
- The `.github/` and `.vscode/` folders contain administrator configurations. Do not access or modify them.
- All output must be in English.
- A PreToolUse hook enforces tool approval boundaries automatically. Respect its decisions.
- Specialized agent personas are available in `.github/agents/`. Invoke with `@<agent-name>` in chat. See `.github/agents/README.md` for the full roster.

## Security — Denied Actions

- If a tool call is denied by the hook, the denial is **permanent and non-negotiable**.
- **Do NOT retry** denied actions. Do not attempt alternative tools, paths, subagents, or terminal commands to access the same resource.
- Do NOT use terminal commands (`run_in_terminal`) to read, list, modify, or delete files in `.github/`, `.vscode/`, or `NoAgentZone/`. Terminal commands targeting these folders will also be blocked.
- If you are a subagent and your action is denied, **immediately report the denial back** to your parent agent and stop. Do not loop or retry.

## Known Tool Limitations

Some terminal commands are blocked by the security hook. Use the listed alternatives:

| Blocked | Use Instead |
|---------|-------------|
| `Out-File` | `Set-Content` or `>` redirect |
| `dir` / `ls` / `Get-ChildItem` (no path argument) | `list_dir` tool |
| `Get-ChildItem -Recurse` (no path argument) | `list_dir` tool or `file_search` tool |
| `pip install` via terminal | `install_python_packages` tool |
| Venv activation (`.\venv\Scripts\activate`) | Run `venv\Scripts\python.exe` directly |
| Venv python (`venv\Scripts\python.exe -c "..."`) | Use system `python` command |
| `memory` tool | Not available (blocked by design) |
