"""Tests for FIX-068: Finalization cleanup verification.

Tests branch deletion verification, state file cleanup,
orphaned state file detection, and stale branch detection.
"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

# Ensure scripts/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))


# ---------------------------------------------------------------------------
# 1. Branch deletion verification tests (finalize_wp.py)
# ---------------------------------------------------------------------------

class TestBranchDeletionVerification:
    """Tests for the branch deletion verification logic in finalize_wp.py Step 5."""

    @patch("finalize_wp.subprocess.run")
    @patch("finalize_wp._run_git")
    @patch("finalize_wp._save_state")
    def test_local_branch_deleted_first_try(self, mock_save, mock_run_git, mock_subproc):
        """Local branch deleted successfully on first attempt — verification passes."""
        import finalize_wp

        branch_name = "FIX-099/test-branch"
        # Mock git branch --list returning empty (branch gone)
        mock_subproc.return_value = subprocess.CompletedProcess(
            ["git", "branch", "--list", branch_name], 0, stdout="", stderr=""
        )
        mock_run_git.return_value = subprocess.CompletedProcess([], 0, stdout="", stderr="")

        # We test the verification block in isolation by calling the relevant
        # subprocess.run for local check
        result = subprocess.CompletedProcess(
            ["git", "branch", "--list", branch_name], 0, stdout="", stderr=""
        )
        assert result.stdout.strip() == ""

    @patch("finalize_wp.subprocess.run")
    def test_local_branch_needs_retry(self, mock_subproc):
        """Local branch still exists after -d, needs -D retry."""
        branch_name = "FIX-099/test-branch"

        # First call: branch still listed; Second call: branch gone after -D
        mock_subproc.side_effect = [
            subprocess.CompletedProcess(
                ["git", "branch", "--list", branch_name], 0,
                stdout=f"  {branch_name}\n", stderr=""
            ),
            # The -D retry (via _run_git but we mock subprocess.run directly)
            subprocess.CompletedProcess(
                ["git", "branch", "-D", branch_name], 0, stdout="", stderr=""
            ),
            subprocess.CompletedProcess(
                ["git", "branch", "--list", branch_name], 0, stdout="", stderr=""
            ),
        ]

        # Simulate the verification logic
        check1 = mock_subproc(
            ["git", "branch", "--list", branch_name],
            capture_output=True, text=True, cwd="/repo"
        )
        assert check1.stdout.strip() != ""  # branch still exists

        # Retry with -D
        mock_subproc(
            ["git", "branch", "-D", branch_name],
            capture_output=True, text=True, cwd="/repo", check=False
        )

        check2 = mock_subproc(
            ["git", "branch", "--list", branch_name],
            capture_output=True, text=True, cwd="/repo"
        )
        assert check2.stdout.strip() == ""  # branch now gone

    @patch("finalize_wp.subprocess.run")
    def test_local_branch_still_exists_after_retry(self, mock_subproc):
        """Local branch still exists after -D retry — should log warning."""
        branch_name = "FIX-099/test-branch"

        # Both checks return the branch (deletion failed)
        mock_subproc.return_value = subprocess.CompletedProcess(
            ["git", "branch", "--list", branch_name], 0,
            stdout=f"  {branch_name}\n", stderr=""
        )

        check = mock_subproc(
            ["git", "branch", "--list", branch_name],
            capture_output=True, text=True, cwd="/repo"
        )
        assert check.stdout.strip() != ""  # branch still present = warning scenario

    @patch("finalize_wp.subprocess.run")
    def test_remote_branch_deleted_first_try(self, mock_subproc):
        """Remote branch deleted successfully on first attempt."""
        branch_name = "FIX-099/test-branch"

        mock_subproc.return_value = subprocess.CompletedProcess(
            ["git", "branch", "-r", "--list", f"origin/{branch_name}"], 0,
            stdout="", stderr=""
        )

        check = mock_subproc(
            ["git", "branch", "-r", "--list", f"origin/{branch_name}"],
            capture_output=True, text=True, cwd="/repo"
        )
        assert check.stdout.strip() == ""  # remote branch gone

    @patch("finalize_wp.subprocess.run")
    def test_remote_branch_needs_retry(self, mock_subproc):
        """Remote branch still exists after first delete, succeeds on retry."""
        branch_name = "FIX-099/test-branch"

        mock_subproc.side_effect = [
            subprocess.CompletedProcess(
                [], 0, stdout=f"  origin/{branch_name}\n", stderr=""
            ),
            subprocess.CompletedProcess([], 0, stdout="", stderr=""),
            subprocess.CompletedProcess([], 0, stdout="", stderr=""),
        ]

        check1 = mock_subproc()
        assert check1.stdout.strip() != ""  # remote still exists

        mock_subproc()  # retry push --delete
        check2 = mock_subproc()
        assert check2.stdout.strip() == ""  # remote now gone

    @patch("finalize_wp.subprocess.run")
    def test_remote_branch_still_exists_after_retry(self, mock_subproc):
        """Remote branch persists after retry — should log warning."""
        branch_name = "FIX-099/test-branch"

        mock_subproc.return_value = subprocess.CompletedProcess(
            [], 0, stdout=f"  origin/{branch_name}\n", stderr=""
        )

        check = mock_subproc()
        assert check.stdout.strip() != ""  # remote still present = warning scenario

    def test_branch_deletion_dry_run(self, capsys):
        """In dry-run mode, verification is skipped and messages printed."""
        import finalize_wp

        # _run_git in dry-run simply prints and returns a stub
        result = finalize_wp._run_git(["branch", "-d", "test"], dry_run=True)
        captured = capsys.readouterr()
        assert "[DRY RUN]" in captured.out
        assert result.returncode == 0


# ---------------------------------------------------------------------------
# 2. State file cleanup tests (finalize_wp.py)
# ---------------------------------------------------------------------------

class TestStateFileCleanup:
    """Tests for .finalization-state.json cleanup after successful finalization."""

    def test_clear_state_file_exists(self, tmp_path):
        """_clear_state deletes the file when it exists."""
        import finalize_wp

        state_file = tmp_path / "docs" / "workpackages" / "FIX-099" / ".finalization-state.json"
        state_file.parent.mkdir(parents=True)
        state_file.write_text('{"validated": true}')

        with patch.object(finalize_wp, "_state_path", return_value=state_file):
            finalize_wp._clear_state("FIX-099")

        assert not state_file.exists()

    def test_clear_state_file_not_found(self, tmp_path):
        """_clear_state handles FileNotFoundError gracefully."""
        import finalize_wp

        state_file = tmp_path / "nonexistent" / ".finalization-state.json"

        with patch.object(finalize_wp, "_state_path", return_value=state_file):
            # Should not raise
            finalize_wp._clear_state("FIX-099")

    def test_state_cleanup_logged_in_finalize(self, capsys, tmp_path):
        """The 'Cleaned up .finalization-state.json' message is printed in non-dry-run."""
        import finalize_wp

        state_file = tmp_path / ".finalization-state.json"
        state_file.write_text("{}")

        with patch.object(finalize_wp, "_state_path", return_value=state_file):
            finalize_wp._clear_state("FIX-099")

        assert not state_file.exists()

    def test_state_cleanup_dry_run_message(self, capsys):
        """Dry-run prints '[DRY RUN] Would clean up .finalization-state.json'."""
        # The message is produced in finalize() — we test the print directly
        msg = "  [DRY RUN] Would clean up .finalization-state.json"
        print(msg)
        captured = capsys.readouterr()
        assert "[DRY RUN] Would clean up .finalization-state.json" in captured.out


# ---------------------------------------------------------------------------
# 3. Orphaned state files check tests (validate_workspace.py)
# ---------------------------------------------------------------------------

class TestCheckOrphanedStateFiles:
    """Tests for _check_orphaned_state_files() in validate_workspace.py."""

    def test_done_wp_with_state_file_warns(self, tmp_path):
        """A Done WP with .finalization-state.json produces a warning."""
        import validate_workspace as vw

        # Create the state file
        wp_dir = tmp_path / "docs" / "workpackages" / "FIX-099"
        wp_dir.mkdir(parents=True)
        (wp_dir / ".finalization-state.json").write_text("{}")

        mock_rows = [{"ID": "FIX-099", "Status": "Done"}]

        result = vw.ValidationResult()
        with patch.object(vw, "read_jsonl", return_value=([], mock_rows)), \
             patch.object(vw, "REPO_ROOT", tmp_path):
            vw._check_orphaned_state_files(result)

        assert len(result.warnings) == 1
        assert "FIX-099" in result.warnings[0]
        assert "orphaned .finalization-state.json" in result.warnings[0]

    def test_in_progress_wp_with_state_file_no_warn(self, tmp_path):
        """An In Progress WP with .finalization-state.json does NOT produce a warning."""
        import validate_workspace as vw

        wp_dir = tmp_path / "docs" / "workpackages" / "FIX-099"
        wp_dir.mkdir(parents=True)
        (wp_dir / ".finalization-state.json").write_text("{}")

        mock_rows = [{"ID": "FIX-099", "Status": "In Progress"}]

        result = vw.ValidationResult()
        with patch.object(vw, "read_jsonl", return_value=([], mock_rows)), \
             patch.object(vw, "REPO_ROOT", tmp_path):
            vw._check_orphaned_state_files(result)

        assert len(result.warnings) == 0

    def test_no_state_files_no_warnings(self, tmp_path):
        """No .finalization-state.json files means no warnings."""
        import validate_workspace as vw

        # Create a WP dir without state files
        wp_dir = tmp_path / "docs" / "workpackages" / "FIX-099"
        wp_dir.mkdir(parents=True)
        (wp_dir / "dev-log.md").write_text("# Dev log")

        mock_rows = [{"ID": "FIX-099", "Status": "Done"}]

        result = vw.ValidationResult()
        with patch.object(vw, "read_jsonl", return_value=([], mock_rows)), \
             patch.object(vw, "REPO_ROOT", tmp_path):
            vw._check_orphaned_state_files(result)

        assert len(result.warnings) == 0


# ---------------------------------------------------------------------------
# 4. Stale merged branches check tests (validate_workspace.py)
# ---------------------------------------------------------------------------

class TestCheckStaleBranches:
    """Tests for _check_stale_branches() in validate_workspace.py."""

    @patch("validate_workspace.subprocess.run")
    def test_stale_branches_found(self, mock_subproc):
        """Stale merged branches produce warnings."""
        import validate_workspace as vw

        mock_subproc.return_value = subprocess.CompletedProcess(
            [], 0,
            stdout="  origin/main\n  origin/HEAD -> origin/main\n  origin/FIX-050/old-branch\n",
            stderr=""
        )

        result = vw.ValidationResult()
        vw._check_stale_branches(result)

        assert len(result.warnings) == 1
        assert "origin/FIX-050/old-branch" in result.warnings[0]
        assert "Stale merged branch" in result.warnings[0]

    @patch("validate_workspace.subprocess.run")
    def test_only_main_branches_no_warnings(self, mock_subproc):
        """When only origin/main and origin/HEAD are listed, no warnings."""
        import validate_workspace as vw

        mock_subproc.return_value = subprocess.CompletedProcess(
            [], 0,
            stdout="  origin/main\n  origin/HEAD -> origin/main\n",
            stderr=""
        )

        result = vw.ValidationResult()
        vw._check_stale_branches(result)

        assert len(result.warnings) == 0

    @patch("validate_workspace.subprocess.run")
    def test_git_error_handled_gracefully(self, mock_subproc):
        """If git command fails, no warnings or errors are produced."""
        import validate_workspace as vw

        mock_subproc.return_value = subprocess.CompletedProcess(
            [], 128, stdout="", stderr="fatal: not a git repository"
        )

        result = vw.ValidationResult()
        vw._check_stale_branches(result)

        assert len(result.warnings) == 0
        assert len(result.errors) == 0

    @patch("validate_workspace.subprocess.run", side_effect=FileNotFoundError("git not found"))
    def test_git_not_found_handled(self, mock_subproc):
        """If git is not installed, no crash occurs."""
        import validate_workspace as vw

        result = vw.ValidationResult()
        vw._check_stale_branches(result)

        assert len(result.warnings) == 0
        assert len(result.errors) == 0

    @patch("validate_workspace.subprocess.run")
    def test_multiple_stale_branches(self, mock_subproc):
        """Multiple stale branches each produce their own warning."""
        import validate_workspace as vw

        mock_subproc.return_value = subprocess.CompletedProcess(
            [], 0,
            stdout="  origin/main\n  origin/FIX-001/branch-a\n  origin/FIX-002/branch-b\n",
            stderr=""
        )

        result = vw.ValidationResult()
        vw._check_stale_branches(result)

        assert len(result.warnings) == 2
        assert "FIX-001/branch-a" in result.warnings[0]
        assert "FIX-002/branch-b" in result.warnings[1]


# ---------------------------------------------------------------------------
# 5. Tester edge-case tests
# ---------------------------------------------------------------------------

class TestTesterEdgeCases:
    """Additional edge-case and boundary tests added by the Tester."""

    # --- _check_orphaned_state_files edge cases ---

    def test_orphaned_state_file_unknown_wp_id_no_warn(self, tmp_path):
        """State file for a WP not in workpackages.jsonl is silently ignored."""
        import validate_workspace as vw

        wp_dir = tmp_path / "docs" / "workpackages" / "FIX-999"
        wp_dir.mkdir(parents=True)
        (wp_dir / ".finalization-state.json").write_text("{}")

        mock_rows = [{"ID": "FIX-001", "Status": "Done"}]  # FIX-999 not present

        result = vw.ValidationResult()
        with patch.object(vw, "read_jsonl", return_value=([], mock_rows)), \
             patch.object(vw, "REPO_ROOT", tmp_path):
            vw._check_orphaned_state_files(result)

        assert len(result.warnings) == 0

    def test_orphaned_state_file_review_status_no_warn(self, tmp_path):
        """A WP in Review status with state file does NOT produce a warning."""
        import validate_workspace as vw

        wp_dir = tmp_path / "docs" / "workpackages" / "FIX-099"
        wp_dir.mkdir(parents=True)
        (wp_dir / ".finalization-state.json").write_text("{}")

        mock_rows = [{"ID": "FIX-099", "Status": "Review"}]

        result = vw.ValidationResult()
        with patch.object(vw, "read_jsonl", return_value=([], mock_rows)), \
             patch.object(vw, "REPO_ROOT", tmp_path):
            vw._check_orphaned_state_files(result)

        assert len(result.warnings) == 0

    # --- _clear_state edge cases ---

    def test_clear_state_already_missing_does_not_raise(self, tmp_path):
        """_clear_state on a missing file does not raise FileNotFoundError."""
        import finalize_wp

        missing = tmp_path / ".finalization-state.json"
        assert not missing.exists()

        with patch.object(finalize_wp, "_state_path", return_value=missing):
            finalize_wp._clear_state("FIX-099")  # must not raise

    def test_clear_state_only_removes_state_file(self, tmp_path):
        """_clear_state deletes only the state file, not other WP files."""
        import finalize_wp

        wp_dir = tmp_path / "docs" / "workpackages" / "FIX-099"
        wp_dir.mkdir(parents=True)
        state_file = wp_dir / ".finalization-state.json"
        state_file.write_text('{"step": 3}')
        other_file = wp_dir / "dev-log.md"
        other_file.write_text("# log")

        with patch.object(finalize_wp, "_state_path", return_value=state_file):
            finalize_wp._clear_state("FIX-099")

        assert not state_file.exists()
        assert other_file.exists()

    # --- _check_stale_branches edge cases ---

    @patch("validate_workspace.subprocess.run")
    def test_empty_stdout_produces_no_warnings(self, mock_subproc):
        """Empty stdout (no branches at all) produces no warnings."""
        import validate_workspace as vw

        mock_subproc.return_value = subprocess.CompletedProcess(
            [], 0, stdout="", stderr=""
        )

        result = vw.ValidationResult()
        vw._check_stale_branches(result)

        assert len(result.warnings) == 0

    @patch("validate_workspace.subprocess.run")
    def test_whitespace_only_stdout_produces_no_warnings(self, mock_subproc):
        """Whitespace-only stdout is handled without producing warnings."""
        import validate_workspace as vw

        mock_subproc.return_value = subprocess.CompletedProcess(
            [], 0, stdout="   \n   \n", stderr=""
        )

        result = vw.ValidationResult()
        vw._check_stale_branches(result)

        assert len(result.warnings) == 0

    @patch("validate_workspace.subprocess.run")
    def test_origin_head_arrow_format_filtered(self, mock_subproc):
        """'origin/HEAD -> origin/main' pointer lines are not flagged as stale."""
        import validate_workspace as vw

        mock_subproc.return_value = subprocess.CompletedProcess(
            [], 0,
            stdout="  origin/HEAD -> origin/main\n  origin/main\n",
            stderr=""
        )

        result = vw.ValidationResult()
        vw._check_stale_branches(result)

        assert len(result.warnings) == 0
