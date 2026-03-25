# Agent Roster

Custom agent files in this directory give VS Code Copilot Chat specialized personas.
Each `.agent.md` file activates a focused mode you invoke with `@<agent-name>` in chat.

---

## Available Agents

| Agent | File | Role |
|-------|------|------|
| Programmer | `programmer.agent.md` | Writes and implements code; focuses on clean, working solutions |
| Brainstormer | `brainstormer.agent.md` | Explores ideas and trade-offs before committing to an approach |
| Tester | `tester.agent.md` | Writes tests, validates behavior, finds edge cases |
| Researcher | `researcher.agent.md` | Investigates libraries, APIs, and concepts; produces structured summaries |
| Scientist | `scientist.agent.md` | Analyzes data, runs experiments, documents findings with evidence |
| Criticist | `criticist.agent.md` | Reviews code and identifies bugs, security issues, and design flaws |
| Planner | `planner.agent.md` | Breaks down tasks into structured, actionable plans |
| Fixer | `fixer.agent.md` | Diagnoses errors and traces root causes; implements targeted fixes |
| Writer | `writer.agent.md` | Drafts documentation, READMEs, comments, and changelogs |
| Prototyper | `prototyper.agent.md` | Builds quick proof-of-concept code; trades perfection for speed |

---

## How to Use

In the Copilot Chat panel, type `@<agent-name>` to invoke an agent.

```
@programmer implement a CSV parser that handles quoted fields
@tester write unit tests for the parse_csv function
@fixer the CSV parser crashes on empty lines — diagnose and fix
```

---

## How to Customize

Edit the `.agent.md` file for the agent you want to modify.
Each file contains YAML frontmatter followed by the agent's system prompt:

```yaml
---
name: Programmer
description: Writes and implements code
tools: [read, edit, search, execute]
model: ['Claude Opus 4.6 (copilot)']
---
Your system prompt here...
```

- **`name`** — Display name in the agent picker.
- **`description`** — Short label shown when selecting the agent.
- **`tools`** — List of tools the agent may use. Restrict tools to match the agent's role.
- **`model`** — The model to use (e.g. `['Claude Opus 4.6 (copilot)']`, `gpt-4o`).
- **System prompt** — The instructions that shape the agent's behavior and persona.

All agents follow the zone restrictions and tool rules defined in `{{PROJECT_NAME}}/AGENT-RULES.md`.
