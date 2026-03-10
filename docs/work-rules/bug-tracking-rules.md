# Bug Tracking Rules

Rules for logging, triaging, and resolving bugs.

---

## Tracking

- All bugs are tracked in `docs/bugs/bugs.csv`.

## ID Format

- IDs use the prefix `BUG-NNN` (e.g., `BUG-001`, `BUG-042`).

## CSV Columns

| Column | Required | Description |
|--------|----------|-------------|
| ID | Yes | Bug identifier (e.g., `BUG-001`) |
| Title | Yes | Short descriptive summary |
| Status | Yes | Current lifecycle state (see below) |
| Severity | Yes | `Critical` / `High` / `Medium` / `Low` |
| Reported By | Yes | Who discovered the bug (person or agent name) |
| Description | Yes | Detailed explanation of the defect |
| Steps to Reproduce | Yes | Numbered steps to reliably trigger the bug |
| Expected Behaviour | Yes | What should happen |
| Actual Behaviour | Yes | What actually happens |
| Fixed In WP | No | Workpackage ID that contains the fix |
| Comments | No | Additional context, workarounds, discussion |

## Severity Levels

| Severity | Definition |
|----------|------------|
| **Critical** | System crash, data loss, security breach, or complete feature failure. Blocks release. |
| **High** | Major functionality broken but workaround exists. Should be fixed before release. |
| **Medium** | Minor functionality broken or degraded UX. Fix in next iteration. |
| **Low** | Cosmetic issue or minor inconvenience. Fix when convenient. |

## Status Lifecycle

```
Open → In Progress → Fixed → Verified → Closed
```

- **Open** — Bug reported, awaiting assignment.
- **In Progress** — A developer is actively working on a fix.
- **Fixed** — Fix implemented and committed. Awaiting verification.
- **Verified** — Fix confirmed by tester or reporter. Bug does not recur.
- **Closed** — Verified and done. No further action needed.

## Rules

- Every bug fix **must** reference a workpackage. If no WP exists, request one.
- Bugs found during testing should be logged in `docs/bugs/bugs.csv` **and** noted in the WP's `test-report.md`.
- All mandatory columns must be filled when logging a bug — incomplete entries will be rejected during maintenance checks.
- A regression test must be written for every fixed bug to prevent recurrence.
