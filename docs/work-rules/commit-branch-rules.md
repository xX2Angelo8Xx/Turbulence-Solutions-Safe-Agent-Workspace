# Commit & Branch Rules

Rules for version control discipline.

---

## Branch Naming

```
<WP-ID>/<short-description>
```

Examples:
- `SAF-003/fix-grep-bypass`
- `GUI-001/main-window-layout`
- `INS-002/python-packaging`

## Commit Messages

Every commit message **MUST** start with the workpackage ID:

```
SAF-003: block includeIgnoredFiles parameter
GUI-001: add main window layout with customtkinter
INS-002: create pyproject.toml with dependencies
```

## Rules

- **One workpackage per branch.** Do not bundle unrelated changes.
- **One branch per workpackage.** Do not split a single workpackage across multiple branches.
- After a workpackage reaches `Done`, perform a `git push` before starting the next workpackage.
- Keep commits focused and atomic — each commit should represent a logical unit of change.
- Do not amend or force-push commits that have already been pushed without explicit approval.
