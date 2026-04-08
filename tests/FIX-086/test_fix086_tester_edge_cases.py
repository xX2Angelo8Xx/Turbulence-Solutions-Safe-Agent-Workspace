"""Tester edge-case tests for FIX-086: workspace root README.md in agent-workbench template.

Supplements test_fix086_readme.py with boundary conditions and additional coverage.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from launcher.core.project_creator import create_project, replace_template_placeholders

_REPO_ROOT = Path(__file__).resolve().parents[2]
_TEMPLATE_DIR = _REPO_ROOT / "templates" / "agent-workbench"
_README = _TEMPLATE_DIR / "README.md"


# ---------------------------------------------------------------------------
# README content: correctness of security zone descriptions
# ---------------------------------------------------------------------------

class TestReadmeSecurityZoneDescriptions:
    """Verify the README accurately describes all three security tiers."""

    def test_readme_has_tier1_auto_allow(self):
        """README must describe Tier 1 — Auto-Allow."""
        content = _README.read_text(encoding="utf-8")
        assert "Tier 1" in content and "Auto-Allow" in content, (
            "README must describe Tier 1 Auto-Allow security zone"
        )

    def test_readme_has_tier2_controlled_access(self):
        """README must describe Tier 2 — Controlled Access."""
        content = _README.read_text(encoding="utf-8")
        assert "Tier 2" in content and "Controlled Access" in content, (
            "README must describe Tier 2 Controlled Access security zone"
        )

    def test_readme_has_tier3_hard_block(self):
        """README must describe Tier 3 — Hard Block."""
        content = _README.read_text(encoding="utf-8")
        assert "Tier 3" in content and "Hard Block" in content, (
            "README must describe Tier 3 Hard Block security zone"
        )

    def test_readme_exempt_tools_list_is_present(self):
        """README must list at least some exempt tool names (e.g. read_file)."""
        content = _README.read_text(encoding="utf-8")
        assert "read_file" in content, (
            "README must document exempt tools including read_file"
        )

    def test_readme_mentions_pretooluse_hook(self):
        """README must mention the PreToolUse hook that enforces the security tiers."""
        content = _README.read_text(encoding="utf-8")
        assert "PreToolUse" in content, (
            "README must mention the PreToolUse hook as the enforcement mechanism"
        )


# ---------------------------------------------------------------------------
# {{PROJECT_NAME}} placeholder: correctness and count
# ---------------------------------------------------------------------------

class TestPlaceholderUsage:
    """Verify {{PROJECT_NAME}} placeholder is used correctly and consistently."""

    def test_placeholder_count_is_exactly_four(self):
        """README must contain exactly 5 occurrences of {{PROJECT_NAME}} (DOC-002 + FIX-119)."""
        content = _README.read_text(encoding="utf-8")
        count = content.count("{{PROJECT_NAME}}")
        assert count == 5, (
            f"README must have exactly 5 {{{{PROJECT_NAME}}}} occurrences "
            f"(FIX-119 added orientation line with {{{{PROJECT_NAME}}}}/AGENT-RULES.md), found {count}"
        )

    def test_placeholder_appears_in_tier1_section(self):
        """Tier 1 Auto-Allow section references {{PROJECT_NAME}}/ not a hardcoded folder name."""
        content = _README.read_text(encoding="utf-8")
        assert "targeting `{{PROJECT_NAME}}/` proceed without a dialog" in content, (
            "Tier 1 description must reference {{PROJECT_NAME}}/ for exempt tool targeting"
        )

    def test_placeholder_appears_in_tier2_section(self):
        """Tier 2 Controlled Access section references {{PROJECT_NAME}}/ not a hardcoded folder name."""
        content = _README.read_text(encoding="utf-8")
        assert "outside `{{PROJECT_NAME}}/`" in content, (
            "Tier 2 description must reference outside {{PROJECT_NAME}}/"
        )

    def test_placeholder_appears_in_exempt_tools_section(self):
        """Exempt Tools section references {{PROJECT_NAME}}/ not a hardcoded folder name."""
        content = _README.read_text(encoding="utf-8")
        assert "inside `{{PROJECT_NAME}}/`" in content, (
            "Exempt Tools description must reference inside {{PROJECT_NAME}}/"
        )

    def test_placeholder_not_remaining_after_replace(self, tmp_path: Path):
        """replace_template_placeholders must remove all {{PROJECT_NAME}} occurrences."""
        import shutil
        # Copy README into a tmp project dir structure
        proj_dir = tmp_path / "workspace"
        proj_dir.mkdir()
        shutil.copy(_README, proj_dir / "README.md")
        replace_template_placeholders(proj_dir, "SomeProject")
        replaced = (proj_dir / "README.md").read_text(encoding="utf-8")
        assert "{{PROJECT_NAME}}" not in replaced, (
            "No unreplaced {{PROJECT_NAME}} tokens must remain after replacement"
        )


# ---------------------------------------------------------------------------
# README encoding and title
# ---------------------------------------------------------------------------

class TestReadmeEncoding:
    """Verify README is properly encoded and has expected title."""

    def test_readme_is_utf8_decodable(self):
        """README.md must be decodable as UTF-8."""
        raw = _README.read_bytes()
        # Should not raise
        text = raw.decode("utf-8")
        assert len(text) > 0

    def test_readme_title_is_agent_workbench_specific(self):
        """README title must reference the Safe AI Agent Workspace, not a generic project."""
        content = _README.read_text(encoding="utf-8")
        # Title line (first non-empty line) must describe safe agent workspace
        title_line = next(
            (line for line in content.splitlines() if line.strip()),
            ""
        )
        assert "Safe" in title_line or "Agent" in title_line, (
            f"README title must be agent-workbench specific, got: {title_line!r}"
        )

    def test_readme_agent_rules_reference_is_in_early_content(self):
        """AGENT-RULES.md pointer must appear early in the README (within first 5 lines)."""
        content = _README.read_text(encoding="utf-8")
        lines = [l for l in content.splitlines() if l.strip()]
        early_content = "\n".join(lines[:5])
        assert "AGENT-RULES.md" in early_content, (
            "AGENT-RULES.md must be referenced in the first 5 non-empty lines "
            "so agents see the orientation pointer immediately"
        )


# ---------------------------------------------------------------------------
# Boundary: templates/coding/ consistency
# ---------------------------------------------------------------------------

class TestCodingTemplateConsistency:
    """Verify relationship between agent-workbench and coding template READMEs."""

    def test_coding_template_has_no_separate_readme(self):
        """templates/coding/ does not have its own root README.md (uses agent-workbench copy)."""
        coding_readme = _REPO_ROOT / "templates" / "coding" / "README.md"
        # DOC-002 tests confirm coding template uses agent-workbench README;
        # having a divergent separate file would be inconsistent
        if coding_readme.is_file():
            # If it does exist, it must have the same content as agent-workbench
            aw_content = _README.read_text(encoding="utf-8")
            c_content = coding_readme.read_text(encoding="utf-8")
            assert aw_content == c_content, (
                "If templates/coding/README.md exists, it must match templates/agent-workbench/README.md"
            )
        # If it doesn't exist, that is also acceptable (agent-workbench is the canonical source)


# ---------------------------------------------------------------------------
# Workspace creation: edge cases for project_creator.py
# ---------------------------------------------------------------------------

class TestWorkspaceCreationEdgeCases:
    """Edge cases for project_creator.py handling of README during workspace creation."""

    def test_readme_contains_project_name_as_folder_path(self, tmp_path: Path):
        """After creation, README contains project name as a folder path reference."""
        workspace = create_project(
            template_path=_TEMPLATE_DIR,
            destination=tmp_path,
            folder_name="EdgeProject",
            include_readmes=True,
        )
        content = (workspace / "README.md").read_text(encoding="utf-8")
        assert "EdgeProject/" in content, (
            "Created README.md must contain 'EdgeProject/' (placeholder replaced)"
        )

    def test_readme_tier1_section_has_project_name_replaced(self, tmp_path: Path):
        """Tier 1 description must use actual project name after workspace creation."""
        workspace = create_project(
            template_path=_TEMPLATE_DIR,
            destination=tmp_path,
            folder_name="MyWorkspace",
            include_readmes=True,
        )
        content = (workspace / "README.md").read_text(encoding="utf-8")
        assert "targeting `MyWorkspace/` proceed without a dialog" in content, (
            "Tier 1 description must use actual project name in created workspace"
        )

    def test_readme_not_empty_in_created_workspace(self, tmp_path: Path):
        """README.md in created workspace must not be empty."""
        workspace = create_project(
            template_path=_TEMPLATE_DIR,
            destination=tmp_path,
            folder_name="Proj",
            include_readmes=True,
        )
        readme = workspace / "README.md"
        assert readme.stat().st_size > 100, (
            "Created README.md must be substantial (> 100 bytes)"
        )

    def test_readme_project_name_replaced_all_occurrences(self, tmp_path: Path):
        """All 4 placeholder occurrences must be replaced — no stragglers."""
        workspace = create_project(
            template_path=_TEMPLATE_DIR,
            destination=tmp_path,
            folder_name="CleanProject",
            include_readmes=True,
        )
        content = (workspace / "README.md").read_text(encoding="utf-8")
        assert "{{PROJECT_NAME}}" not in content, (
            "No unreplaced {{PROJECT_NAME}} tokens must remain in created workspace README"
        )
        assert content.count("CleanProject/") >= 4, (
            "All 4 {{PROJECT_NAME}}/ occurrences must be replaced with CleanProject/"
        )
