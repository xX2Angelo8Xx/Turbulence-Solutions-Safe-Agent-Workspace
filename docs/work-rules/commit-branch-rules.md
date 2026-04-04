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

After a workpackage reaches `Done` and is merged into `main`, the feature branch **MUST** be deleted immediately. This is handled automatically by `scripts/finalize_wp.py` — do not perform these steps manually unless the script is unavailable:

```bash
# Delete local branch
git branch -d <branch-name>

# Delete remote branch
git push origin --delete <branch-name>
```

Never allow stale merged branches to accumulate in the repository.

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
# Preferred: use the finalization script (handles merge + cleanup + cascades)
.venv/Scripts/python scripts/finalize_wp.py <WP-ID>

# Manual fallback (only if script is unavailable):
git checkout main
git merge <branch-name> --no-edit
git push origin main
git branch -d <branch-name>
git push origin --delete <branch-name>
```

## Rules

- **One workpackage per branch.** Do not bundle unrelated changes.
- **One branch per workpackage.** Do not split a single workpackage across multiple branches.
- After a workpackage reaches `Done`, perform a `git push` before starting the next workpackage.
- Delete the feature branch (local + remote) immediately after merge — see Post-Merge Cleanup above.
- Keep commits focused and atomic — each commit should represent a logical unit of change.
- Do not amend or force-push commits that have already been pushed without explicit approval.

---

## Branch Deletion (Mandatory)

After any feature branch is merged into `main`, it **MUST** be deleted immediately — both locally and remotely. This is non-negotiable.

```bash
# Delete local branch
git branch -d <branch-name>

# Delete remote branch
git push origin --delete <branch-name>
```

**Why this is enforced:**
- Stale merged branches create confusion about what is in-progress vs. complete.
- Accumulation of stale branches has recurred in 5 consecutive maintenance cycles (ACT-038, ACT-039).
- `scripts/finalize_wp.py` handles this automatically — use it whenever available.

**If `finalize_wp.py` is unavailable**, the agent or developer responsible for the merge MUST perform the deletion steps above manually before any other work begins.

Failure to delete merged branches is a workflow violation and will be flagged in the next maintenance audit.

---

## GitHub Branch Protection

The `main` branch must have GitHub branch protection rules configured to enforce PR reviews and CI checks. These rules cannot be set by code — a repository admin must apply them manually.

See [branch-protection.md](branch-protection.md) for the full step-by-step configuration guide.
