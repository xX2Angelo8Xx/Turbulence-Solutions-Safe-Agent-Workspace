# User Story Rules

Rules governing user story creation, lifecycle, and relationship to workpackages.

---

## Tracking

- User stories are tracked in `docs/user-stories/user-stories.csv`.

## ID Format

- IDs use the prefix `US-NNN` (e.g., `US-001`, `US-012`).

## CSV Columns

| Column | Description |
|--------|-------------|
| ID | User story identifier (e.g., `US-001`) |
| Title | Short descriptive name |
| As a | The user role (e.g., "developer") |
| I want | The desired functionality |
| So that | The benefit or goal |
| Acceptance Criteria | Numbered list defining the end-to-end definition of done for this feature |
| Status | `Open`, `In Progress`, `Done`, `Closed` |
| Linked WPs | Comma-separated list of workpackage IDs derived from this story |
| Comments | Notes, discussion, change history |

## Lifecycle Rules

1. A user story **MUST** exist and be **approved** before workpackages are created from it.
2. Workpackages reference their parent user story in the `User Story` column of `docs/workpackages/workpackages.csv`.
3. Infrastructure or safety workpackages with no user-facing feature are tagged `Enabler` instead of a user story ID.
4. A user story is `Done` **only when all its linked workpackages are `Done`**.
5. The acceptance criteria in the user story define the end-to-end definition of done for the feature.
6. Do not modify acceptance criteria after workpackages have been created without approval.
7. A user story may be set to `Closed` when it has been superseded or split into other stories and will not be implemented directly. `Closed` stories are retained for audit trail purposes and should have a note in the Comments field explaining the reason (e.g., "Split into US-003, US-004").
