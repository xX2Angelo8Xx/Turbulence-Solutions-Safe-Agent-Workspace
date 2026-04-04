# Workpackage Rules

Rules governing workpackage creation, lifecycle, and tracking.

---

## Tracking

- All workpackages are tracked in `docs/workpackages/workpackages.jsonl` (JSONL format, one JSON object per line).
- This JSONL file is the **single source of truth** for all task tracking.

## ID Format

IDs use category prefixes followed by a three-digit number:

| Prefix | Category |
|--------|----------|
| `INS-xxx` | Installer |
| `SAF-xxx` | Safety |
| `GUI-xxx` | GUI |
| `DOC-xxx` | Documentation |
| `FIX-xxx` | Fix / Bug Fix |
| `MNT-xxx` | Maintenance |

New categories may be introduced as the project evolves. Prefix must be uppercase, number zero-padded to three digits.

## JSONL Fields

| Field | Description |
|--------|-------------|
| ID | Workpackage identifier (e.g., `GUI-001`) |
| Category | INS, SAF, GUI, DOC, etc. |
| Name | Short descriptive name |
| Status | Current lifecycle state (see below) |
| Assigned To | Person or agent currently responsible |
| Description | What needs to be done |
| Goal | Measurable completion criteria |
| Comments | Progress notes, blockers, review feedback |
| User Story | Parent user story ID (e.g., `US-001`) or `Enabler` for infrastructure tasks |
| Depends On | Comma-separated WP IDs this WP depends on (e.g., `GUI-001, GUI-002`) |
| Blockers | Description of blockers preventing progress |

## Status Lifecycle

```
Open → In Progress → Review → Done
```

- **Open** — Available for assignment. No work has begun.
- **In Progress** — Actively being worked on. Exactly one person/agent is assigned.
- **Review** — Implementation complete. Awaiting review and testing by a different person/agent.
- **Done** — Reviewed, tested, and approved. A `git push` must follow immediately.

**No skipping states.** A workpackage cannot go from `Open` to `Review` or from `Open` to `Done`.

## Assignment Rules

- **Before starting**: Set status to `In Progress` and fill in `Assigned To`.
- **One agent/person per workpackage.** No shared ownership.
- **One workpackage per branch.** Do not bundle unrelated changes.
- After finishing implementation: set to `Review`. Only a reviewer (Tester Agent or human reviewer) may set `Done`.
- After `Done`: perform a `git push` before starting the next workpackage.

## Workpackage Folders

Each workpackage in active development gets a dedicated folder:

```
docs/workpackages/<WP-ID>/
├── dev-log.md         # Developer's implementation log (created by Developer)
├── test-report.md     # Tester's findings and test results (created by Tester)
└── ...                # Additional iteration artifacts if needed
```

- **Developer** creates the folder and writes `dev-log.md` when starting work (see [agent-workflow.md](agent-workflow.md) for format).
- **Tester** writes `test-report.md` with findings, bugs, and TODOs during review.
- **Developer** reads `test-report.md` to address issues in subsequent iterations.
- Each iteration appends to the existing logs (do not overwrite — maintain history).
- These folders keep all WP-specific artifacts in one traceable location.

## Scope Rules

- **Only implement what the workpackage specifies.** No bonus features, no drive-by refactors.
- Do NOT create, rename, or re-scope workpackages without approval. Propose changes in the Comments column.
- If a workpackage is blocked, note the blocker in Comments and inform the assignee of the blocking WP.

## Workpackage Size — Smallest Possible Units

Workpackages must be broken into the **smallest atomic units** that can be implemented, tested, and reviewed independently. This is a hard rule, not a guideline.

**A workpackage is too large if it would:**
- Touch more than ~3 unrelated files
- Require more than one distinct concern or functional area
- Take a single agent more than one focused implementation session
- Make it unclear which part of the code changed to achieve the goal

**Always split** user stories and large workpackages into smaller sub-WPs. A well-scoped WP should have a single, clear `Goal` that can be verified in one test run.

**Examples of correct splitting:**
- Instead of "Implement the full GUI" → `GUI-001: Main window layout`, `GUI-002: Project type dropdown`, `GUI-003: Folder name input`
- Instead of "Build safety gate" → `SAF-001: Core hook entry point`, `SAF-002: Zone enforcement logic`, `SAF-003: Tool parameter validation`

---

## Regression Found After Done

A Done workpackage is **never reopened**. If a regression or defect is discovered after a WP reaches `Done`, follow this procedure:

1. **Do not modify the Done WP's status.** It stays `Done`.
2. **Create a new FIX-xxx workpackage** referencing the original WP in the `Comments` column (e.g., "Regression in GUI-005").
3. The FIX WP **must** include a regression test that reproduces the issue.
4. Link the FIX WP to the same User Story as the original WP.
5. If the original WP's `Depends On` column is relevant, carry forward any dependencies.
6. Follow the normal WP lifecycle: Open → In Progress → Review → Done.

This preserves the audit trail and ensures every fix is independently tested and reviewed.

If a Developer determines a WP is too large mid-implementation, they must stop, report to the Orchestrator, and request a split before continuing.

## Decomposed Workpackages

When a workpackage is too large and is split into sub-workpackages:

1. The parent WP status remains `Done` with a comment listing all sub-WP IDs.
2. The parent WP **must** have a `docs/workpackages/<WP-ID>/` folder containing a `dev-log.md` that documents the decomposition decision and lists all sub-WPs.
3. The parent WP does **not** require a `test-report.md` — testing is handled by each sub-WP independently.
4. All sub-WPs must reference the same User Story as the parent.
5. The parent WP's `Comments` field must state: "Decomposed into sub-workpackages <list> — see sub-WPs for implementation."

## Human-Performed Work

When a workpackage is implemented by a human (not an AI agent):

1. The human **must** still follow the status lifecycle: `Open → In Progress → Review → Done`.
2. A `dev-log.md` must be created in the WP folder, even if brief.
3. If no separate Tester review is performed, the human must create a retroactive `test-report.md` documenting:
   - How the fix was verified (e.g., "verified via full test suite run")
   - Whether a dedicated `tests/<WP-ID>/` directory is applicable
4. Human-fix WPs that only modify test code or configuration (no production code) may be exempt from creating a dedicated test directory, but this exemption must be documented in the `test-report.md`.
5. The `Assigned To` column must show who performed the work (e.g., "Human" or the person's name).

## Cross-Reference Integrity

When creating a new workpackage, **use `scripts/add_workpackage.py`** which automatically handles cross-reference updates:

```powershell
.venv\Scripts\python scripts/add_workpackage.py `
    --category GUI --name "..." --description "..." --goal "..." --user-story US-007
```

The script:
1. Assigns the next sequential ID within the category (e.g., `GUI-019`).
2. Appends the entry to `workpackages.jsonl` with duplicate-ID prevention.
3. **Automatically updates the User Story's `Linked WPs` field** in `user-stories.jsonl`.
4. Uses file locking for parallel agent safety.

If manual JSONL editing is unavoidable:
1. **Update the User Story's `Linked WPs` field** in `user-stories.jsonl` to include the new WP ID in the same commit.
2. This is mandatory — failing to do so creates cross-reference drift that must be caught and fixed during maintenance.
3. **When a Developer creates or claims a WP that references a User Story**, the Developer MUST verify that the WP ID is listed in the parent User Story's `Linked WPs` field in `docs/user-stories/user-stories.jsonl`. If not present, add it before beginning implementation.
3. When decomposing a WP into sub-WPs, update the parent User Story's `Linked WPs` to include all sub-WP IDs.
