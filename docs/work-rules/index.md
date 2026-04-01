# Work Rules — Index

Central hub for all project rules, workflows, and protocols. Every rule in this project is reachable from this page.

---

## If You Need To…

| Task | Read This |
|------|-----------|
| Work on a workpackage | [workpackage-rules.md](workpackage-rules.md) |
| Understand or create user stories | [user-story-rules.md](user-story-rules.md) |
| Commit code or create a branch | [commit-branch-rules.md](commit-branch-rules.md) |
| Write or review code | [coding-standards.md](coding-standards.md) |
| Understand security requirements | [security-rules.md](security-rules.md) |
| Log or fix a bug | [bug-tracking-rules.md](bug-tracking-rules.md) |
| Write, run, or log tests | [testing-protocol.md](testing-protocol.md) |
| Perform project maintenance | [maintenance-protocol.md](maintenance-protocol.md) |
| Recover from failures | [recovery.md](recovery.md) |
| Onboard as an AI agent | [agent-workflow.md](agent-workflow.md) |
| Use a helper script | [../scripts/README.md](../../scripts/README.md) |
---

## Key Project Files

| File | Purpose |
|------|---------|
| `docs/architecture.md` | Project overview, repository structure, architecture diagrams |
| `docs/project-scope.md` | Vision, target users, capabilities, technology stack |
| `docs/workpackages/workpackages.csv` | **Single source of truth** for all tasks. Every code change must reference a workpackage ID |
| `docs/workpackages/<WP-ID>/` | Per-workpackage folder containing dev logs, test reports, and iteration artifacts |
| `docs/user-stories/user-stories.csv` | User stories — parent of workpackages |
| `docs/bugs/bugs.csv` | Bug tracking — all identified defects |
| `docs/test-results/test-results.csv` | Test execution records — all test runs |
| `docs/maintenance/` | Maintenance audit logs (timestamped) |
| `templates/agent-workbench/` | Template shipped to end users — **never modify for testing** |

---

## Custom Agents

| Agent | Role | When to Use |
|-------|------|-------------|
| **Orchestrator** | Decomposes multi-WP tasks, spawns Developer subagents, finalizes WPs autonomously | User wants multiple WPs implemented, or wants delegation |
| **Developer** | Implements a single WP, writes tests, hands off to Tester | Assigned a workpackage to implement |
| **Tester** | Reviews code, runs tests, marks Done or returns to Developer | WP is in `Review` status and needs verification |
| **Maintenance** | Runs integrity checks, creates audit log, proposes fixes (human approval required) | Periodic project health checks |
| **Story Writer** | Generates user stories from user input, requires human approval before saving | User wants to create or refine a user story |

Agent definitions are in `.github/agents/`. See [agent-workflow.md](agent-workflow.md) for the full execution protocol, including **Autonomy Rules** (no human input during WP execution).
