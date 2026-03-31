# AgentDocs

Central knowledge base for this project. All agents and humans read from and contribute to these documents.

## Philosophy — 5 Pillars

1. **AgentDocs is the brain.** This folder is the single source of truth. No scattered notes elsewhere.
2. **Living documents.** Update what exists — do not create new files unless the user asks.
3. **Speed over ceremony.** Move fast. No formal gates, no SOPs.
4. **Read before you act.** Check `progress.md` at the start of every session.
5. **Leave traces.** Log meaningful decisions, findings, and changes before you finish.

## Standard Documents

| Document | Purpose | Primary Contributors |
|----------|---------|---------------------|
| `architecture.md` | System design, tech stack, components | Planner |
| `decisions.md` | Key decisions and rationale (ADR-light) | Planner, Coordinator |
| `research-log.md` | Findings with sources and links | Researcher |
| `progress.md` | What is done, in progress, and next | All agents |
| `open-questions.md` | Unresolved trade-offs needing human input | Brainstormer, any agent |
| `plan.md` / `plan-*.md` | Active plans — task breakdowns with dependencies and ownership | Planner |

## Rules

- **Do not create additional files** in this folder unless explicitly asked by the user — **except for plan files** (`plan.md`, `plan-*.md`), which Planner may create as part of its standard workflow.
- **Tag your entries** with your agent name and date so others can trace contributions.
- **Update, don't append forever.** When a section becomes stale, rewrite it rather than adding a contradicting paragraph below.
