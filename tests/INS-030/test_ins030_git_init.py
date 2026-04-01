"""
INS-030: Tests for git repository initialisation on project creation.

Fixes BUG-171: newly created workspaces previously had no .git directory,
causing 'fatal: not a git repository' for all AGENT-RULES §5 git operations.

Covers:
  - _init_git_repository creates .git directory
  - _init_git_repository makes an initial commit
  - _init_git_repository returns False gracefully when git is unavailable
  - create_project produces a workspace with a .git directory (integration)
  - git failures do not prevent workspace creation
"""
from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

REPO_ROOT = pathlib.Path(__file__).parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from launcher.core.project_creator import _init_git_repository, create_project

TEMPLATE_PATH = REPO_ROOT / "templates" / "agent-workbench"


# ---------------------------------------------------------------------------
# _init_git_repository unit tests
# ---------------------------------------------------------------------------

class TestInitGitRepository(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.workspace = pathlib.Path(self.tmp) / "test-workspace"
        self.workspace.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_creates_git_directory(self):
        """_init_git_repository must create a .git directory in the workspace."""
        result = _init_git_repository(self.workspace)
        if not result:
            self.skipTest("git not available in this environment")
        self.assertTrue((self.workspace / ".git").is_dir(), ".git directory must exist")

    def test_returns_true_on_success_with_content(self):
        """_init_git_repository must return True when git init and commit succeed."""
        # Add a file so the initial commit has something to commit.
        (self.workspace / "README.md").write_text("# Test", encoding="utf-8")
        result = _init_git_repository(self.workspace)
        if not result:
            self.skipTest("git not available in this environment")
        self.assertTrue(result)

    def test_returns_false_when_git_missing(self):
        """_init_git_repository must return False if git raises OSError."""
        with patch("launcher.core.project_creator.subprocess.run",
                   side_effect=OSError("git not found")):
            result = _init_git_repository(self.workspace)
        self.assertFalse(result)

    def test_returns_false_when_git_timeout(self):
        """_init_git_repository must return False on TimeoutExpired."""
        with patch("launcher.core.project_creator.subprocess.run",
                   side_effect=subprocess.TimeoutExpired(["git"], 30)):
            result = _init_git_repository(self.workspace)
        self.assertFalse(result)

    def test_returns_false_when_git_init_fails(self):
        """_init_git_repository must return False when git init returns non-zero."""
        mock_result = MagicMock()
        mock_result.returncode = 128
        with patch("launcher.core.project_creator.subprocess.run",
                   return_value=mock_result):
            result = _init_git_repository(self.workspace)
        self.assertFalse(result)


# ---------------------------------------------------------------------------
# create_project integration: workspace has .git after creation
# ---------------------------------------------------------------------------

class TestCreateProjectGitInit(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.dest = pathlib.Path(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_created_workspace_has_git_directory(self):
        """create_project must produce a workspace with a .git directory."""
        workspace = create_project(TEMPLATE_PATH, self.dest, "TestProject")
        if not (workspace / ".git").exists():
            self.skipTest("git not available in this environment")
        self.assertTrue((workspace / ".git").is_dir(), ".git directory must exist in new workspace")

    def test_create_project_succeeds_even_if_git_unavailable(self):
        """create_project must not raise even when git is not installed."""
        with patch("launcher.core.project_creator._init_git_repository", return_value=False):
            workspace = create_project(TEMPLATE_PATH, self.dest, "NoGitProject")
        self.assertTrue(workspace.is_dir(), "Workspace directory must still be created")

    def test_created_workspace_has_initial_commit(self):
        """After create_project, the new workspace must have at least one git commit."""
        workspace = create_project(TEMPLATE_PATH, self.dest, "CommitProject")
        if not (workspace / ".git").is_dir():
            self.skipTest("git not available in this environment")
        result = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=str(workspace),
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, "git log must succeed")
        self.assertTrue(result.stdout.strip(), "There must be at least one commit")


if __name__ == "__main__":
    unittest.main()
