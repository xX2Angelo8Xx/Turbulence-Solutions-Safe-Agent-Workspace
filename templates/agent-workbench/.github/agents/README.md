# Specialist Agents

Seven specialist agents are available in this workspace. Invoke any agent with `@<agent-name>` in VS Code Chat (e.g., `@Coordinator`, `@Programmer`, `@Tester`), or delegate to them via `runSubagent`.

See `{{PROJECT_NAME}}/AGENT-RULES.md` for the full agent permissions, zone restrictions, and documentation rules.

| Agent | File | Role | When to Use |
|-------|------|------|-------------|
| **Coordinator** | `coordinator.agent.md` | Orchestrates multi-agent workflows; delegates tasks, reads and executes plan files from AgentDocs/ | When you want an agent to manage the full workflow autonomously |
| **Planner** | `planner.agent.md` | Designs system architecture and writes task-breakdown plan files into AgentDocs/ | When you need a structured plan with tasks, owners, and dependencies |
| **Researcher** | `researcher.agent.md` | Investigates topics, fetches web sources, writes findings to AgentDocs/research-log.md | When you need evidence-backed facts or technology comparisons |
| **Brainstormer** | `brainstormer.agent.md` | Generates creative options and captures trade-offs in AgentDocs/open-questions.md | When you want multiple approaches explored before committing |
| **Programmer** | `programmer.agent.md` | Implements features, writes and runs tests, updates AgentDocs/progress.md | When you need code written or changed |
| **Tester** | `tester.agent.md` | Reviews code, runs the test suite, verifies requirements, updates AgentDocs/progress.md | When you need edge-case testing or validation |
| **Workspace-Cleaner** | `workspace-cleaner.agent.md` | Audits all AgentDocs documents for drift; fixes stale content or flags issues for human review | When docs may have drifted from the actual code state |

## Typical Workflow

1. **Coordinator** reads a plan file and delegates tasks to specialist agents.
2. **Planner** writes the initial `AgentDocs/plan.md`.
3. **Programmer** and **Tester** work in tandem — Programmer implements, Tester reviews.
4. **Workspace-Cleaner** can be run at any time to reconcile documentation with actual code.

## Adding or Customizing Agents

To customize an existing agent or add your own, create or edit a `.agent.md` file in this folder following the frontmatter structure below:

```
---
name: AgentName
description: "One-line description of the agent's role"
tools: [read, edit, search]
model: ['Claude Sonnet 4.6 (copilot)']
---
```

Then add the agent to `coordinator.agent.md`'s `agents:` list so the Coordinator can delegate to it.
