# Recovery Procedures

Runbook for recovering from common failure modes. When something goes wrong, find the matching scenario below and follow the steps.

---

## Corrupt JSONL File

**Symptoms:** Script crashes with `UnicodeDecodeError`, `json.JSONDecodeError`, `KeyError` on a field name, or the file contains malformed JSON lines.

**Recovery:**
1. Do NOT attempt to edit the corrupt file manually.
2. Find the last known-good version in Git history:
   ```bash
   git log --oneline -20 -- <path-to-jsonl>
   ```
3. Restore the file from that commit:
   ```bash
   git checkout <commit-hash> -- <path-to-jsonl>
   ```
4. Run `scripts/validate_workspace.py --full` to verify integrity.
5. Re-apply any legitimate changes that were lost (check recent dev-logs and commit messages).

---

## Orphaned Lock File

**Symptoms:** Script hangs or fails with `TimeoutError: Could not acquire lock on <path>.lock within 30s`.

**Recovery:**
1. Confirm no other agent or process is actively running a JSONL operation:
   ```bash
   # Check for running Python processes
   tasklist | findstr python    # Windows
   ps aux | grep python         # Unix
   ```
2. If no process is actively using the file, delete the lock file:
   ```bash
   del <path>.lock              # Windows
   rm <path>.lock               # Unix
   ```
3. Retry the operation.

**Note:** As of `jsonl_utils.py`, lock files older than 5 minutes are automatically cleaned up. This manual procedure is only needed if the automatic cleanup also fails.

---

## Partial Finalization

**Symptoms:** `finalize_wp.py` failed mid-way (e.g., merge conflict, network error). The WP is in an inconsistent state — partially merged, branches may or may not be deleted, cascades may not have run.

**Recovery:**
1. Check the state file to see which steps completed:
   ```bash
   type docs\workpackages\<WP-ID>\.finalization-state.json    # Windows
   cat docs/workpackages/<WP-ID>/.finalization-state.json      # Unix
   ```
2. **Re-run `finalize_wp.py`** — it is idempotent and will skip completed steps:
   ```bash
   .venv/Scripts/python scripts/finalize_wp.py <WP-ID>
   ```
3. If the failure was a merge conflict, resolve the conflict manually first:
   ```bash
   git checkout main
   git merge <WP-ID>/<branch-name>
   # Resolve conflicts in your editor
   git add -A
   git commit
   ```
   Then re-run `finalize_wp.py` to complete the remaining steps.
4. To restart finalization from scratch (discard state):
   ```bash
   .venv/Scripts/python scripts/finalize_wp.py <WP-ID> --reset
   ```

---

## Merge Conflict During Finalization

**Symptoms:** `finalize_wp.py` exits with a git merge error.

**Recovery:**
1. Switch to main and attempt the merge manually:
   ```bash
   git checkout main
   git merge <branch-name>
   ```
2. Git will show conflicting files. Open each one and resolve conflicts.
3. Stage and commit:
   ```bash
   git add -A
   git commit -m "<WP-ID>: resolve merge conflict"
   ```
4. Re-run `finalize_wp.py` to complete remaining steps (cascade, cleanup, etc.):
   ```bash
   .venv/Scripts/python scripts/finalize_wp.py <WP-ID>
   ```

---

## Accidental Push to Wrong Remote

**Symptoms:** Code was pushed to a different repository URL than the canonical one.

**Recovery:**
1. **Immediately correct the remote URL:**
   ```bash
   git remote set-url origin https://github.com/xX2Angelo8Xx/Turbulence-Solutions-Safe-Agent-Workspace.git
   ```
2. Verify:
   ```bash
   git remote -v
   ```
3. Push to the correct remote:
   ```bash
   git push origin main
   ```
4. If the wrong remote received confidential code, notify the repository owner immediately to delete it.

**Prevention:** `finalize_wp.py` now verifies the remote URL before every push operation. The pre-commit hook also runs validation. Always use `finalize_wp.py` for merging.

---

## Duplicate TST-IDs in test-results.jsonl

**Symptoms:** `validate_workspace.py --full` reports duplicate TST-IDs.

**Recovery:**
1. Run the deduplication script:
   ```bash
   .venv/Scripts/python scripts/dedup_test_ids.py --dry-run   # preview
   .venv/Scripts/python scripts/dedup_test_ids.py              # fix
   ```
2. Verify with validation:
   ```bash
   .venv/Scripts/python scripts/validate_workspace.py --full
   ```

**Prevention:** Always use `scripts/run_tests.py` or `scripts/add_test_result.py` instead of manual JSONL editing. These scripts use `locked_next_id_and_append()` which prevents collisions.

---

## Pre-Commit Hook Not Working After Clone

**Symptoms:** Commits succeed without running validation.

**Recovery:**
1. Run the hook installer:
   ```bash
   .venv/Scripts/python scripts/install_hooks.py
   ```
   This sets `git config core.hooksPath scripts/hooks` which points Git to the tracked hooks directory.

2. Verify:
   ```bash
   git config core.hooksPath
   ```
   Should output: `scripts/hooks`

**Note:** This must be done once per clone/checkout. The hooks themselves are tracked in `scripts/hooks/` and stay up to date via `git pull`.
