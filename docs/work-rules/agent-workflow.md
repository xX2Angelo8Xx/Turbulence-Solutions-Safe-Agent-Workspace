# Agent Workflow

Onboarding checklist and standard execution protocol for all AI agents working in this project.

---

## Session Startup

1. `copilot-instructions.md` is auto-loaded (landing page with non-negotiable rules).
2. Read `docs/work-rules/index.md` to find which rules apply to your task.
3. Read the specific rule file(s) relevant to your assignment.
4. Read `docs/workpackages/workpackages.jsonl` to see current project state.

---

## Standard Workpackage Execution Workflow

Every agent follows this exact workflow when implementing a workpackage. No steps may be skipped.

### Phase 1 — Developer (Steps 0–7)

| Step | Action | Details |
|------|--------|---------|
| 0 | **Prior Art Check** | Read `docs/decisions/index.jsonl`. Search for ADRs related to this WP's domain. If relevant ADRs exist, acknowledge them in `dev-log.md` or propose supersession. This prevents contradicting prior architectural decisions. |
| 1 | **Read** | Read the WP row from `docs/workpackages/workpackages.jsonl`. Read the linked user story. Read `coding-standards.md`, `security-rules.md`, `testing-protocol.md`. |
| 2 | **Claim** | Set WP status to `In Progress`. Fill in `Assigned To`. |
| 3 | **Prepare** | Create the WP folder: `docs/workpackages/<WP-ID>/`. Create `dev-log.md` inside it (see format below). |
| 4 | **Implement** | Write code following `coding-standards.md` and `security-rules.md`. Stay within WP scope. |
| 5 | **Test** | Create `tests/<WP-ID>/` folder if it doesn't exist. Write and run tests per `testing-protocol.md`. All tests must pass. **Run the final pre-handoff test suite via `scripts/run_tests.py`** (mandatory — this executes pytest and atomically logs results to the JSONL file). `scripts/add_test_result.py` is a manual fallback only for cases where `run_tests.py` cannot be used; direct JSONL editing is always prohibited. |
| 6 | **Document** | Update `dev-log.md` with implementation summary, decisions made, tests written, and known limitations. |
| 7 | **Handoff** | Set WP status to `Review`. Commit per `commit-branch-rules.md`. Hand off to Tester Agent. Include the list of changed files (output of `git diff --cached --name-only`) in the handoff message. |

### Developer Pre-Handoff Checklist

Before setting a WP to `Review`, the Developer MUST verify:
1. All tests pass (run via `scripts/run_tests.py`).
2. `docs/workpackages/<WP-ID>/dev-log.md` is up to date.
3. No `tmp_` files remain in `docs/workpackages/<WP-ID>/` or `tests/<WP-ID>/`.
4. WP branch follows `<WP-ID>/<short-desc>` naming convention.
5. Run `scripts/validate_workspace.py --wp <WP-ID>` — must return exit code 0.
6. All changes are staged and committed.
7. All bugs referenced in `dev-log.md` have `Fixed In WP` populated with this WP-ID.
8. **If this WP is a bug fix (FIX-xxx):** remove the corresponding entry from `tests/regression-baseline.json`, update `_count` and `_updated`, and include the file in the commit. See the "Regression Baseline" section of `testing-protocol.md` for the exact procedure.

### Git Operations for Handoff (Step 7)

Before setting WP to Review and handing off:
1. Run `git add -A` to stage ALL new and modified files.
2. Run `git status` and verify all intended changes are staged.
3. Run `git diff --cached --stat` to confirm the staged changes match your work.
4. Commit with message format: `<WP-ID>: <short description>`
5. Push the feature branch: `git push origin <branch-name>`

After finalization: verify local feature branch is deleted (`git branch -d <branch>`). If `finalize_wp.py` did not delete it, delete manually.

### Post-Edit Verification (required after every code change)

After making any code edit, the Developer MUST verify the edit was actually persisted to disk. In-memory edits (e.g. from IDE buffers or tool chains) can be silently discarded without error.

1. **Read back the file from disk** after every edit to confirm the change is present. Do not assume the edit was saved.
2. **Run `git diff` before committing** to verify all intended changes appear in the diff. If a file shows no changes despite edits, the edits were not saved — do not proceed.
3. **Never advance a WP to `Review`** based on assumed or remembered test results. Run the full test suite immediately before advancing and confirm all tests pass.

### Temporary File Policy

Agents may create temporary output files (e.g., pytest output captures, debug logs) **only** inside their workpackage folder: `docs/workpackages/<WP-ID>/` or `tests/<WP-ID>/`. Temporary files must NEVER be created in the repository root or any shared directory.

Rules:
1. **Allowed locations:** `docs/workpackages/<WP-ID>/`, `tests/<WP-ID>/`
2. **Forbidden locations:** Repository root, `src/`, `docs/` (top-level), `templates/`
3. **Cleanup required:** The agent who creates temporary files **must** delete them before handing off the WP. Use `os.remove()` or equivalent after processing.
4. **Never delete:** Test scripts (`test_*.py`), dev-log.md, test-report.md, or any file that is part of the WP's permanent deliverables.
5. **Naming convention:** Prefix temporary files with `tmp_` to make them easily identifiable.

---

### Phase 2 — Tester (Steps 8–10)

| Step | Action | Details |
|------|--------|---------|
| 8 | **Review** | Read the WP row, `dev-log.md`, linked user story, and code changes. Verify requirements are met. |
| 9 | **Test** | Run the full test suite. Add edge-case tests beyond the Developer's. Think beyond the protocol: attack vectors, boundaries, race conditions. Log all runs using `scripts/add_test_result.py` (mandatory — direct JSONL editing is prohibited). |
| 10 | **Verdict** | Write `test-report.md` in the WP folder (see `testing-protocol.md` for format). |

**If PASS:** Set WP to `Done`. Push.  
**If FAIL:** Set WP back to `In Progress`. Write specific TODOs in `test-report.md`. Developer reads `test-report.md` and repeats from Step 4.

### Escalation Rule — Iteration Cap

If the Developer↔Tester cycle **fails 3 times** on the same WP (i.e., the Tester returns the WP to `In Progress` three times), the Tester **must** escalate to the Orchestrator before another iteration. The Orchestrator reviews the WP and may:
- Reassign to a different Developer
- Split the WP into smaller sub-WPs
- Cancel the WP and create a replacement with revised scope

The iteration count is tracked in `dev-log.md` (each iteration adds a numbered section). Three `## Iteration N` sections = escalation required.

### Tester PASS Checklist

Before marking a WP as Done, the Tester MUST verify:
1. `docs/workpackages/<WP-ID>/dev-log.md` exists and is non-empty.
2. `docs/workpackages/<WP-ID>/test-report.md` has been written (by you, the Tester).
3. All test files exist in `tests/<WP-ID>/`.
4. All test runs are logged in `docs/test-results/test-results.jsonl`.
5. All bugs found during testing are logged in `docs/bugs/bugs.jsonl`.
6. WP branch follows `<WP-ID>/<short-desc>` naming convention.
7. No `tmp_` files remain in `docs/workpackages/<WP-ID>/` or `tests/<WP-ID>/`.
8. For each bug in `docs/bugs/bugs.jsonl` with `Fixed In WP` matching this WP-ID and Status=`Fixed`, run:
   `.venv\Scripts\python scripts/update_bug_status.py <BUG-ID> --status Closed`
9. Run `git add -A` to stage all new test files and JSONL updates.
10. Commit: `<WP-ID>: Tester PASS`
11. Push: `git push origin <branch-name>`

If any of items 1–8 are missing, do NOT mark the WP as Done. Create the missing artifact or return to Developer.

### Post-Done Finalization (Orchestrator)

After the Tester marks a WP as Done, the Orchestrator (or the Tester if no Orchestrator is active) runs the finalization script:

```powershell
.venv\Scripts\python scripts/finalize_wp.py <WP-ID>
```

The script performs **all** finalization steps automatically:
1. Validates the WP via `scripts/validate_workspace.py --wp <WP-ID>`
2. Merges the feature branch to main and pushes
3. Deletes the feature branch (local + remote)
4. Cascades User Story status to `Done` if all linked WPs are Done
5. Cascades Bug status to `Closed` for bugs fixed by this WP
6. Syncs `docs/architecture.md` via `scripts/update_architecture.py`
7. Commits cascade changes and pushes
8. Verifies no stale merged branches remain
9. Deletes `docs/workpackages/<WP-ID>/.finalization-state.json`

Use `--dry-run` to preview without executing: `.venv\Scripts\python scripts/finalize_wp.py <WP-ID> --dry-run`

**Do NOT perform these steps manually.** The script exists to prevent the finalization errors that have recurred across every maintenance cycle.

**Post-finalization sanity check:** After running `finalize_wp.py`, verify that `docs/workpackages/<WP-ID>/.finalization-state.json` does NOT exist. If it persists, run `scripts/validate_workspace.py --full --fix` to auto-clean orphaned state files.

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

## Behavior Changes
<!-- Include this section ONLY when one or more snapshot files were updated with
     --update-snapshots.  The snapshot IS the documentation — this section is the
     mandatory paper trail for every intentional security-decision change. -->
- **<snapshot-file>.json** — `<old-decision>` → `<new-decision>`
  Reason: <why the decision changed — policy change, bug fix, new rule, etc.>
  Authorised by: WP <WP-ID> / ADR-<N> (delete as applicable)
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
- **Restricted Zones:** The following paths are restricted. Access is prohibited unless the WP explicitly requires it.

  All paths below are relative to the **repository root**.

  | Path | Scope | Access Rule |
  |------|-------|-------------|
  | `.github/` | Repo root | No access unless WP explicitly requires it |
  | `.vscode/` | Repo root | No access unless WP explicitly requires it |
  | `templates/agent-workbench/NoAgentZone/` | Repo root | No access unless WP explicitly requires it |

- **When uncertain:** Stop and ask — do not guess.
- **Context discipline:** Read only what you need. Do not preemptively load all documentation.
- **No self-review:** The agent who implements a WP must NOT be the one who reviews it.

---

## Mandatory Script Usage

The following operations **MUST** be performed via helper scripts. Direct manual execution of these operations is prohibited — the scripts exist to prevent recurring errors detected across multiple maintenance cycles.

| Operation | Script | Who Uses It |
|-----------|--------|-------------|
| Add test result row | `scripts/add_test_result.py` | Developer, Tester |
| Run tests and log result | `scripts/run_tests.py` | Developer, Tester |
| Create workpackage | `scripts/add_workpackage.py` | Orchestrator, Developer |
| Log a bug | `scripts/add_bug.py` | Tester |
| Pre-commit validation | `scripts/validate_workspace.py` | Developer, Tester |
| Post-Done finalization | `scripts/finalize_wp.py` | Orchestrator |
| Architecture sync | `scripts/update_architecture.py` | Called by finalize_wp.py |
| Deduplicate TST-IDs | `scripts/dedup_test_ids.py` | Maintenance |
| Install Git hooks | `scripts/install_hooks.py` | Setup (once after clone) |
| Archive old test results | `scripts/archive_test_results.py` | Maintenance |
| Update bug status | `scripts/update_bug_status.py` | Tester, Maintenance |
| Regenerate template manifest | `scripts/generate_manifest.py` | Developer |
| Update regression baseline | Direct JSON edit of `tests/regression-baseline.json` (no script — update `_count` and `_updated` manually) | Developer (after bug fix), Orchestrator (at release) |

See `scripts/README.md` for full usage documentation.

**Pre-handoff validation gate:** Before setting a WP to `Review` (Developer) or `Done` (Tester), run:
```powershell
.venv\Scripts\python scripts/validate_workspace.py --wp <WP-ID>
```
Abort and fix any errors before proceeding.

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
