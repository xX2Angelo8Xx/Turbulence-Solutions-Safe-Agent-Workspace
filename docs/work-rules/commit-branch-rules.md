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

## Remote Repository

The canonical remote is:

```
https://github.com/xX2Angelo8Xx/Turbulence-Solutions-Safe-Agent-Workspace.git
```

## Pre-Push Checklist

Before every `git push`, complete the following steps in order:

1. Run `git remote -v` and **visually confirm** the URL matches exactly:
   ```
   https://github.com/xX2Angelo8Xx/Turbulence-Solutions-Safe-Agent-Workspace.git
   ```
2. If the URL is wrong, correct it immediately:
   ```bash
   git remote set-url origin https://github.com/xX2Angelo8Xx/Turbulence-Solutions-Safe-Agent-Workspace.git
   ```
3. **Never push to any other repository URL.** Pushing to the wrong remote (e.g. `agent-environment-launcher`) is a project-breaking error.

## Post-Merge Cleanup

After a workpackage reaches `Done` and is merged into `main`, the feature branch **MUST** be deleted immediately — do not defer cleanup:

```bash
# Delete local branch
git branch -d <branch-name>

# Delete remote branch
git push origin --delete <branch-name>
```

Never allow stale merged branches to accumulate in the repository.

## OneDrive Workspace Note

This workspace is stored on OneDrive. Git directory deletions (e.g. branch log directories) may fail due to OneDrive file-sync locks. If git prompts a retry on directory cleanup, answer **`n`** — the branch reference itself is deleted even if the log directory cleanup fails. **Never use `--force` or destructive flags to work around OneDrive lock failures.**

## Explicit Git Sequence for Agents

AI agents must follow this exact sequence when committing work. Do not skip steps.

### After Implementation (Developer)
```bash
git add -A
git status                    # Verify all files staged
git diff --cached --stat      # Verify staged changes match work
git commit -m "<WP-ID>: <description>"
git push origin <branch-name>
```

### After Review (Tester)
```bash
git add -A
git status                    # Verify all files staged
git commit -m "<WP-ID>: Tester <PASS|FAIL>"
git push origin <branch-name>
```

### After Done (Orchestrator or Tester)
```bash
git checkout main
git merge <branch-name> --no-edit
git push origin main
git branch -d <branch-name>
git push origin --delete <branch-name>
```

**OneDrive Note:** If branch deletion prompts for retry on directory cleanup, answer `n`. The branch is already deleted.

## Rules

- **One workpackage per branch.** Do not bundle unrelated changes.
- **One branch per workpackage.** Do not split a single workpackage across multiple branches.
- After a workpackage reaches `Done`, perform a `git push` before starting the next workpackage.
- Delete the feature branch (local + remote) immediately after merge — see Post-Merge Cleanup above.
- Keep commits focused and atomic — each commit should represent a logical unit of change.
- Do not amend or force-push commits that have already been pushed without explicit approval.
