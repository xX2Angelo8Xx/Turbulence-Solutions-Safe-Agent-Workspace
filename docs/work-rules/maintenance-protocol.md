# Maintenance Protocol

Structured integrity audit for periodic project health checks. The Maintenance Agent (or a human) runs this protocol to detect inconsistencies, enforce structure, and propose corrective actions.

---

## Trigger

- User prompts an agent with "maintenance" or invokes the Maintenance Agent.
- Recommended frequency: before and after each major milestone, or at least weekly during active development.

## Maintenance Checklist

The following checks are executed in order. Each item produces a **Pass**, **Warning**, or **Fail** result.

### 1. Git Hygiene
- Are there workpackages marked `Done` that have **not** been committed or pushed?
- Do all active branches follow the naming convention `<WP-ID>/<short-description>`?
- Are there stale branches (no commits in 30+ days) that should be cleaned up?

### 2. Workpackage–User Story Consistency
- Does every workpackage reference a valid user story ID or `Enabler`?
- Does every user story's `Linked WPs` column match the actual workpackages referencing it?
- Does each user story's status match the aggregate status of its linked workpackages?

### 3. CSV Integrity
- Are all CSV files parseable with no malformed rows?
- Are required fields filled for every entry?
- Are there duplicate IDs in any CSV?
- Are all status values valid enum values (e.g., `Open`, `In Progress`, `Review`, `Done`)?

### 4. Documentation Freshness
- Does the repository structure in `docs/architecture.md` match the actual directory layout?
- Does `docs/work-rules/index.md` list all existing rule files?
- Are all file paths referenced in documentation still valid?

### 5. Workpackage Folder Integrity
- Does every `In Progress` or `Review` WP have a corresponding folder in `docs/workpackages/<WP-ID>/`?
- Does every WP folder contain a `dev-log.md`?
- Does every `Review` or `Done` WP folder contain a `test-report.md`?

### 6. Orphan Detection
- Are there files in `Project/` not referenced by any workpackage or documentation?
- Are there WP folders under `docs/workpackages/` with no matching WP in the CSV?
- Is there dead code or unused imports in the codebase?

### 7. Test Coverage Gaps
- Are there workpackages in `Done` status with code changes but no corresponding test results in `docs/test-results/test-results.csv`?
- Are there `Done` WPs without a `test-report.md` in their folder?

### 8. Bug Tracking
- Are there open bugs without an assigned workpackage?
- Are there bugs in `Fixed` status without a verification step?
- Are all mandatory fields filled in `docs/bugs/bugs.csv`?

### 9. Structural Integrity
- Is `copilot-instructions.md` still under 40 lines with no detailed process rules?
- Are all agent files in `.github/agents/` syntactically valid with required YAML frontmatter?
- Is the `Default-Project/` template unmodified (no accidental test changes)?

---

## Output — Maintenance Log

The Maintenance Agent creates a timestamped log at:

```
docs/maintenance/YYYY-MM-DD-maintenance.md
```

### Log Format

```markdown
# Maintenance Log — YYYY-MM-DD

**Performed by:** <name or agent>

## Results

| # | Check | Result | Details |
|---|-------|--------|---------|
| 1 | Git Hygiene | Pass/Warning/Fail | <findings> |
| 2 | WP–US Consistency | Pass/Warning/Fail | <findings> |
| 3 | CSV Integrity | Pass/Warning/Fail | <findings> |
| 4 | Documentation Freshness | Pass/Warning/Fail | <findings> |
| 5 | WP Folder Integrity | Pass/Warning/Fail | <findings> |
| 6 | Orphan Detection | Pass/Warning/Fail | <findings> |
| 7 | Test Coverage Gaps | Pass/Warning/Fail | <findings> |
| 8 | Bug Tracking | Pass/Warning/Fail | <findings> |
| 9 | Structural Integrity | Pass/Warning/Fail | <findings> |

## Proposed Actions

| Priority | Action | Affected Files |
|----------|--------|----------------|
| Critical | <description> | <file paths> |
| Warning | <description> | <file paths> |
| Info | <description> | <file paths> |

## Status
**Awaiting human review** — Do NOT implement any changes until approved.
```

---

## Human Verification

**Critical rule:** The Maintenance Agent creates the log and proposes actions, but **NEVER implements fixes directly**. The workflow is:

1. Maintenance Agent runs checklist → creates log file.
2. Human reviews the log and approves, rejects, or modifies proposed actions.
3. Only after human approval does a Developer Agent (or human) execute the approved fixes.
4. Each fix follows the standard workpackage workflow if it involves code changes.
