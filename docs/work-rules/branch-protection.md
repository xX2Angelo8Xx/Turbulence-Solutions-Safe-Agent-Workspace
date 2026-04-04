# Branch Protection Requirements

> **Manual setup required.** The rules on this page must be configured manually in the GitHub repository settings. They cannot be enforced by code or scripts — a repository admin must apply them once.

---

## Overview

The `main` branch is the single source of truth for production-ready code. To prevent accidental or unauthorised changes, the following protection rules must be active at all times. These rules complement the process rules in [commit-branch-rules.md](commit-branch-rules.md) and [agent-workflow.md](agent-workflow.md).

---

## Required Settings — `main`

Navigate to: **GitHub → Repository → Settings → Branches → Add branch ruleset** (or edit the existing `main` ruleset).

### 1. Require a Pull Request Before Merging

| Setting | Value |
|---------|-------|
| **Required approvals** | `1` |
| Dismiss stale pull request approvals when new commits are pushed | Enabled |
| Require review from Code Owners | Optional (enable when `CODEOWNERS` is added) |

**Why:** Prevents any single contributor (human or AI agent) from merging untested code directly into `main`.

### 2. Require Status Checks to Pass Before Merging

| Setting | Value |
|---------|-------|
| **Require branches to be up to date before merging** | Enabled |
| **Required status checks** | `test` (from `test.yml`) |

The job name in `.github/workflows/test.yml` is `test`. All three matrix builds (Windows, Ubuntu, macOS) must pass before merge is allowed.

**Why:** Enforces ADR-002 — the CI test gate is a mandatory quality gate before any change reaches `main`.

### 3. Do Not Allow Bypassing the Above Settings

| Setting | Value |
|---------|-------|
| **Do not allow bypassing the above settings** | Enabled |
| Allow specified actors to bypass required pull requests | See "Admin Exception" below |

### 4. Block Force Pushes

| Setting | Value |
|---------|-------|
| **Block force pushes** | Enabled |

**Why:** Preserves commit history integrity. Force pushes to `main` can erase merged work and break downstream clones.

### 5. Block Branch Deletion

| Setting | Value |
|---------|-------|
| **Block deletions** | Enabled |

**Why:** Prevents accidental deletion of the `main` branch.

---

## Admin Exception — `finalize_wp.py`

The `scripts/finalize_wp.py` script performs a direct merge of feature branches into `main` (without opening a pull request). This is intentional — it is the controlled, automated end-of-WP workflow run by an authorised developer.

To allow this while keeping branch protection active, choose **one** of the following options:

### Option A — Admin Bypass (simplest)

Add the repository owner's GitHub account to the **"Allow specified actors to bypass required pull requests"** list. The owner account can then push directly or merge without a review requirement.

> **Risk:** Any misuse of the owner account bypasses all protection. Keep this account secured with a strong password and MFA.

### Option B — Service Account with Bypass Role (recommended for teams)

1. Create a dedicated GitHub account (e.g. `turbulence-bot`) for automated merge operations.
2. Grant it `Write` access to the repository.
3. Add it to the bypass list for the `main` ruleset.
4. Use a repository secret (`FINALIZE_TOKEN`) with this account's token when running `finalize_wp.py` in CI.

### Option C — Relax to "Squash Merge via PR" Workflow (future)

If the project moves to a fully pull-request-based workflow, `finalize_wp.py` can be updated to open a PR and auto-merge it. This removes the need for any bypass. This is the long-term recommended direction.

---

## Optional Future Settings

The following settings are recommended for future hardening but are not required for current operations:

| Setting | Recommendation |
|---------|---------------|
| Require signed commits | Enable after all contributors have GPG or SSH signing configured |
| Require linear history | Consider enabling to keep `git log` clean (enforce squash/rebase merges) |
| Require conversation resolution before merging | Enable when the team uses PR review comments actively |

---

## Verification

After applying these settings, verify them by:

1. Opening a test PR from any feature branch to `main`.
2. Confirming the PR cannot be merged without at least 1 approval.
3. Confirming the PR cannot be merged if the `test` workflow is failing.
4. Attempting a direct push to `main` with a non-bypass account — it must be rejected.

---

## Related

- [commit-branch-rules.md](commit-branch-rules.md) — branch naming, commit messages, and push procedure
- [agent-workflow.md](agent-workflow.md) — full WP execution protocol including Git operations
- `.github/workflows/test.yml` — CI test workflow whose `test` job is the required status check
- ADR-002 — Mandatory CI Test Gate Before Release Builds
