# Turbulence Solutions – Copilot Instructions

## Company

Turbulence Solutions

## Workspace Rules

- The `{{PROJECT_NAME}}/` folder is the designated working directory. Place all project files there.
- The `NoAgentZone/` folder is strictly off-limits. Never read, write, or reference files in it.
- The `.github/` and `.vscode/` folders contain administrator configurations. Do not access or modify them.
- All output must be in English.
- A PreToolUse hook enforces tool approval boundaries automatically. Respect its decisions.

## Security — Denied Actions

- If a tool call is denied by the hook, the denial is **permanent and non-negotiable**.
- **Do NOT retry** denied actions. Do not attempt alternative tools, paths, subagents, or terminal commands to access the same resource.
- Do NOT use terminal commands (`run_in_terminal`) to read, list, modify, or delete files in `.github/`, `.vscode/`, or `NoAgentZone/`. Terminal commands targeting these folders will also be blocked.
- If you are a subagent and your action is denied, **immediately report the denial back** to your parent agent and stop. Do not loop or retry.

## Coding Standards

- Write clean, well-commented code.
- Use meaningful variable and function names.
- Follow the conventions of the language being used.
- Prefer readability over cleverness.

## Communication

- Be concise and direct.
- When uncertain, ask clarifying questions using the ask_questions tool.
- Explain your reasoning when making architectural decisions.
