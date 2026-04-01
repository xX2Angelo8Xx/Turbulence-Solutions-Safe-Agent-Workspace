# Specialist Agents

Seven specialist agents are available in this workspace. Invoke any agent with `@<agent-name>` in VS Code Chat, or delegate to them via `runSubagent`.

| Agent | File | Role |
|-------|------|------|
| **Coordinator** | `coordinator.agent.md` | Orchestrates multi-agent workflows; reads and executes plan files from AgentDocs/ |
| **Planner** | `planner.agent.md` | Designs system architecture and writes task-breakdown plan files into AgentDocs/ |
| **Researcher** | `researcher.agent.md` | Investigates topics, fetches web sources, writes findings to AgentDocs/research-log.md |
| **Brainstormer** | `brainstormer.agent.md` | Generates creative options and captures trade-offs in AgentDocs/open-questions.md |
| **Programmer** | `programmer.agent.md` | Implements features, writes and runs tests, updates AgentDocs/progress.md |
| **Tester** | `tester.agent.md` | Reviews code, runs the test suite, verifies requirements, updates AgentDocs/progress.md |
| **Workspace-Cleaner** | `workspace-cleaner.agent.md` | Audits all AgentDocs documents for drift; fixes stale content or flags issues for human review |

## Typical Workflow

1. **Coordinator** reads a plan file and delegates tasks to specialist agents.
2. **Planner** writes the initial `AgentDocs/plan.md`.
3. **Programmer** and **Tester** work in tandem — Programmer implements, Tester reviews.
4. **Workspace-Cleaner** can be run at any time to reconcile documentation with actual code.

## Adding Custom Agents

To add your own agent, create a `.agent.md` file in this folder following the same frontmatter structure as the existing files.
