"""Tests for FIX-086: workspace root README.md restored in agent-workbench template.

Regression guard for BUG-158: workspace root README.md was missing in v3.2.4.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from launcher.core.project_creator import create_project, replace_template_placeholders

_REPO_ROOT = Path(__file__).resolve().parents[2]
_TEMPLATE_DIR = _REPO_ROOT / "templates" / "agent-workbench"
_README = _TEMPLATE_DIR / "README.md"


# ---------------------------------------------------------------------------
# Template file presence and content (static checks)
# ---------------------------------------------------------------------------

class TestTemplateReadmeExists:
    """Verify the README.md is present in the template directory (BUG-158 guard)."""

    def test_readme_exists_in_template(self):
        """templates/agent-workbench/README.md must exist."""
        assert _README.is_file(), (
            "templates/agent-workbench/README.md is missing — BUG-158 regression"
        )

    def test_readme_is_non_empty(self):
        """templates/agent-workbench/README.md must be non-empty."""
        assert _README.stat().st_size > 0, "README.md must not be empty"

    def test_readme_uses_project_name_placeholder(self):
        """README.md must use {{PROJECT_NAME}}/ to refer to the working folder."""
        content = _README.read_text(encoding="utf-8")
        assert "{{PROJECT_NAME}}/" in content, (
            "README.md must reference the project folder as {{PROJECT_NAME}}/"
        )

    def test_readme_mentions_noagentzone(self):
        """README.md must document the NoAgentZone/ restricted folder."""
        content = _README.read_text(encoding="utf-8")
        assert "NoAgentZone/" in content, (
            "README.md must document the NoAgentZone/ security zone"
        )

    def test_readme_mentions_github_zone(self):
        """README.md must document the .github/ restricted zone."""
        content = _README.read_text(encoding="utf-8")
        assert ".github/" in content, (
            "README.md must document the .github/ security zone"
        )

    def test_readme_mentions_vscode_zone(self):
        """README.md must document the .vscode/ restricted zone."""
        content = _README.read_text(encoding="utf-8")
        assert ".vscode/" in content, (
            "README.md must document the .vscode/ security zone"
        )

    def test_readme_references_agent_rules(self):
        """README.md must point agents to AGENT-RULES.md for detailed rules."""
        content = _README.read_text(encoding="utf-8")
        assert "AGENT-RULES.md" in content, (
            "README.md must contain a reference to AGENT-RULES.md for agent orientation"
        )

    def test_readme_mentions_security_gate(self):
        """README.md must document that a security gate protects restricted zones."""
        content = _README.read_text(encoding="utf-8")
        # Security gate is described via tier blocks; any of these key phrases confirms it
        assert any(
            phrase in content
            for phrase in ("Tier 1", "Tier 2", "security", "PreToolUse", "hook")
        ), "README.md must describe the active security gate protecting restricted zones"


# ---------------------------------------------------------------------------
# Regression test: workspace creation copies README.md to root (BUG-158)
# ---------------------------------------------------------------------------

class TestWorkspaceCreationCopiesReadme:
    """Verify project_creator.create_project() produces a README.md at workspace root."""

    def test_readme_present_at_workspace_root_by_default(self, tmp_path: Path):
        """create_project() with default include_readmes=True must place README.md at root."""
        workspace = create_project(
            template_path=_TEMPLATE_DIR,
            destination=tmp_path,
            folder_name="TestProject",
            include_readmes=True,
        )
        assert (workspace / "README.md").is_file(), (
            "README.md must exist at the workspace root when include_readmes=True "
            "(regression guard for BUG-158)"
        )

    def test_readme_absent_when_include_readmes_false(self, tmp_path: Path):
        """create_project() with include_readmes=False intentionally removes all READMEs."""
        workspace = create_project(
            template_path=_TEMPLATE_DIR,
            destination=tmp_path,
            folder_name="TestProject",
            include_readmes=False,
        )
        assert not (workspace / "README.md").is_file(), (
            "README.md must be removed from workspace root when include_readmes=False"
        )

    def test_readme_placeholders_replaced_in_workspace(self, tmp_path: Path):
        """After create_project(), README.md in the workspace must have PROJECT_NAME replaced."""
        workspace = create_project(
            template_path=_TEMPLATE_DIR,
            destination=tmp_path,
            folder_name="MyAgent",
            include_readmes=True,
        )
        readme_path = workspace / "README.md"
        assert readme_path.is_file(), "README.md must exist at workspace root"
        content = readme_path.read_text(encoding="utf-8")
        assert "{{PROJECT_NAME}}" not in content, (
            "After workspace creation, {{PROJECT_NAME}} must be replaced with 'MyAgent'"
        )
        assert "MyAgent/" in content, (
            "After workspace creation, project folder name 'MyAgent/' must appear in README.md"
        )
