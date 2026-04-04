# Bug Tracking Rules

Rules for logging, triaging, and resolving bugs.

---

## Tracking

- All bugs are tracked in `docs/bugs/bugs.jsonl`.

## ID Format

- IDs use the prefix `BUG-NNN` (e.g., `BUG-001`, `BUG-042`).

## JSONL Fields

| Field | Required | Description |
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
Open → In Progress → Fixed → Closed
```

- **Open** — Bug reported, awaiting assignment.
- **In Progress** — A developer is actively working on a fix.
- **Fixed** — Fix implemented and committed. Awaiting verification.
- **Closed** — Fix verified by Tester during WP review and confirmed at finalization. No further action needed.

> **Note:** The `finalize_wp.py` script auto-closes bugs in `Fixed` status when their `Fixed In WP` references a Done workpackage. Manual closure via `scripts/update_bug_status.py` is available as a backup.

## Rules

- Every bug fix **must** reference a workpackage. If no WP exists, request one.
- Bugs found during testing should be logged in `docs/bugs/bugs.jsonl` **and** noted in the WP's `test-report.md`.
- All mandatory columns must be filled when logging a bug — incomplete entries will be rejected during maintenance checks.
- A regression test must be written for every fixed bug to prevent recurrence.
- **Use `scripts/add_bug.py`** for auto-ID assignment and field validation:
  ```powershell
  .venv\Scripts\python scripts/add_bug.py `
      --title "..." --severity High --reported-by "Tester Agent" `
      --description "..." --steps "..." --expected "..." --actual "..."
  ```

## Bug Closure at Finalization

When a workpackage is finalized (status set to `Done`), all bugs referenced in its `dev-log.md` or `test-report.md` must have:

- **`Fixed In WP`** populated with the WP-ID
- **`Status`** set to `Closed`

The finalization script (`scripts/finalize_wp.py`) automatically scans for bug references (BUG-NNN patterns) in the WP's `dev-log.md` and `test-report.md` and cascades closures — setting `Fixed In WP` and updating `Status` to `Closed` for each referenced bug.

Developers must verify bug linkage before handoff to the Tester:
- Confirm every bug mentioned in `dev-log.md` has its `Fixed In WP` field populated with the current WP-ID.
- If a bug was reported during testing and fixed in the same WP, ensure both `dev-log.md` and `test-report.md` reference the bug ID consistently.
