# Workpackage Rules

Rules governing workpackage creation, lifecycle, and tracking.

---

## Tracking

- All workpackages are tracked in `docs/workpackages/workpackages.csv` (CSV format, viewable as a table in VS Code with a CSV extension).
- This CSV is the **single source of truth** for all task tracking.

## ID Format

IDs use category prefixes followed by a three-digit number:

| Prefix | Category |
|--------|----------|
| `INS-xxx` | Installer |
| `SAF-xxx` | Safety |
| `GUI-xxx` | GUI |
| `DOC-xxx` | Documentation |

New categories may be introduced as the project evolves. Prefix must be uppercase, number zero-padded to three digits.

## CSV Columns

| Column | Description |
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

If a Developer determines a WP is too large mid-implementation, they must stop, report to the Orchestrator, and request a split before continuing.
