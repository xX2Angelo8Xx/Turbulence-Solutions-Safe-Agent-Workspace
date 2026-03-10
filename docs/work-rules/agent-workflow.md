# Agent Workflow

Onboarding checklist and standard execution protocol for all AI agents working in this project.

---

## Session Startup

1. `copilot-instructions.md` is auto-loaded (landing page with non-negotiable rules).
2. Read `docs/work-rules/index.md` to find which rules apply to your task.
3. Read the specific rule file(s) relevant to your assignment.
4. Read `docs/workpackages/workpackages.csv` to see current project state.

---

## Standard Workpackage Execution Workflow

Every agent follows this exact workflow when implementing a workpackage. No steps may be skipped.

### Phase 1 — Developer (Steps 1–7)

| Step | Action | Details |
|------|--------|---------|
| 1 | **Read** | Read the WP row from `docs/workpackages/workpackages.csv`. Read the linked user story. Read `coding-standards.md`, `security-rules.md`, `testing-protocol.md`. |
| 2 | **Claim** | Set WP status to `In Progress`. Fill in `Assigned To`. |
| 3 | **Prepare** | Create the WP folder: `docs/workpackages/<WP-ID>/`. Create `dev-log.md` inside it (see format below). |
| 4 | **Implement** | Write code following `coding-standards.md` and `security-rules.md`. Stay within WP scope. |
| 5 | **Test** | Create `tests/<WP-ID>/` folder if it doesn't exist. Write and run tests per `testing-protocol.md`. All tests must pass. Log results in `docs/test-results/test-results.csv`. |
| 6 | **Document** | Update `dev-log.md` with implementation summary, decisions made, tests written, and known limitations. |
| 7 | **Handoff** | Set WP status to `Review`. Commit per `commit-branch-rules.md`. Hand off to Tester Agent. |

### Phase 2 — Tester (Steps 8–10)

| Step | Action | Details |
|------|--------|---------|
| 8 | **Review** | Read the WP row, `dev-log.md`, linked user story, and code changes. Verify requirements are met. |
| 9 | **Test** | Run the full test suite. Add edge-case tests beyond the Developer's. Think beyond the protocol: attack vectors, boundaries, race conditions. Log all runs in `docs/test-results/test-results.csv`. |
| 10 | **Verdict** | Write `test-report.md` in the WP folder (see `testing-protocol.md` for format). |

**If PASS:** Set WP to `Done`. Push.  
**If FAIL:** Set WP back to `In Progress`. Write specific TODOs in `test-report.md`. Developer reads `test-report.md` and repeats from Step 4.

---

## Dev Log Format

The Developer creates `docs/workpackages/<WP-ID>/dev-log.md`:

```markdown
# Dev Log — <WP-ID>

**Developer:** <name or agent>
**Date started:** YYYY-MM-DD
**Iteration:** <number>

## Objective
<What this WP aims to achieve — copied from WP Description/Goal>

## Implementation Summary
<What was done, key decisions, approach taken>

## Files Changed
- <relative/path/to/file> — <what changed>

## Tests Written
- <test name> — <what it validates>

## Known Limitations
- <any caveats, deferred work, edge cases not covered>
```

For subsequent iterations (after Tester feedback), append a new section:

```markdown
## Iteration <N> — YYYY-MM-DD

### Tester Feedback Addressed
- <TODO item from test-report.md> — <how it was resolved>

### Additional Changes
- <file> — <change>

### Tests Added/Updated
- <test> — <purpose>
```

---

## Rules for All Agents

- **One agent per workpackage.** Never work on multiple WPs simultaneously.
- **Restricted zones:** Never access `.github/`, `.vscode/`, or `NoAgentZone/` in `Default-Project/` unless the WP explicitly requires it.
- **When uncertain:** Stop and ask — do not guess.
- **Context discipline:** Read only what you need. Do not preemptively load all documentation.
- **No self-review:** The agent who implements a WP must NOT be the one who reviews it.

---

## Autonomy Rules

These rules apply to all agents in the autonomous pipeline. Once the Orchestrator kicks off a workpackage, the entire Dev → Test → Done cycle runs without human intervention.

- **Never prompt for user input.** No `input()`, no `--prompt`, no `[y/n]` confirmations, no "Should I try again?" queries to the terminal.
- **All terminal commands must be non-interactive.** Use `--yes`, `--no-input`, `--force`, `--quiet`, or equivalent flags where available. If a command requires interaction and no flag exists, find an alternative approach.
- **Never run a command that causes the terminal to await input.** If a command hangs waiting for stdin, it will block the pipeline indefinitely.
- **The Orchestrator finalizes WPs autonomously.** After a Tester PASS, the Orchestrator proceeds to the next WP without asking the user for confirmation.
- **Exceptions:** The Story Writer agent awaits human approval before saving a user story. The Maintenance agent awaits human approval before implementing any proposed fix. All other agents run autonomously.

---

## Agent Handoff Flows

```
Multiple WPs:   User → Orchestrator → Developer(s) → Tester → Done
Single WP:      User → Orchestrator → Developer → Tester → Done
                   OR  User → Developer → Tester → Done
Maintenance:    User → Maintenance → Log → Human reviews → Developer (if fixes needed)
```
