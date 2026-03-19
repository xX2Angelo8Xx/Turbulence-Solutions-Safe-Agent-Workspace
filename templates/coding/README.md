# Turbulence Solutions – Default Project Template

Standard project template with AI agent safety controls for VS Code + GitHub Copilot.

## Folder Structure

| Folder | Agent Access | Description |
|--------|-------------|-------------|
| `{{PROJECT_NAME}}/` | Auto-allowed (exempt tools) | Working directory for all project files |
| `NoAgentZone/` | Blocked | Sensitive files — no AI access permitted |
| `.github/` | Blocked (hidden) | Hook scripts, Copilot config, agents, prompts, skills |
| `.vscode/` | Blocked (hidden) | VS Code workspace settings and security config |

## Security Zones

The PreToolUse hook (`.github/hooks/scripts/require-approval.sh`) enforces three security tiers:

### Tier 1 — Auto-Allow

Exempt tools targeting `{{PROJECT_NAME}}/` proceed without a dialog.

### Tier 2 — Force Ask

Exempt tools outside `{{PROJECT_NAME}}/`, or any non-exempt tool anywhere, trigger a VS Code approval dialog.

### Tier 3 — Hard Block

Any tool targeting `.github/`, `.vscode/`, or `NoAgentZone/` is denied outright. No dialog, no override.

### Exempt Tools

These tools are auto-allowed inside `{{PROJECT_NAME}}/` and trigger an approval dialog elsewhere:

`read_file`, `edit_file`, `replace_string_in_file`, `create_file`, `multi_replace_string_in_file`, `write_file`, `list_dir`, `search`, `grep_search`, `semantic_search`, `file_search`, `manage_todo_list`, `runSubagent`, `search_subagent`

**Always allowed** (no path check): `ask_questions` / `vscode_ask_questions`

### Non-Exempt Tools

Terminal commands, MCP tools, external tools, browser tools, etc. — these **always** require manual approval regardless of path.


