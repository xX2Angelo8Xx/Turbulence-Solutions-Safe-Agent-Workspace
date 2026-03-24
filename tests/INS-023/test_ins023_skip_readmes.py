"""Tests for INS-023 — skip README files during project creation.

Covers:
- include_readmes=True (default) preserves README.md files
- include_readmes=False removes all README.md files
- Non-README .md files (AGENT-RULES.md, copilot-instructions.md) are never affected
- Missing README files do not raise errors
- Default parameter value is True
- Case-sensitive filename match (only "README.md", not "readme.md" etc.)
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from launcher.core.project_creator import create_project


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_template(tmp_path: Path) -> Path:
    """Create a minimal template directory that mimics templates/coding/."""
    tpl = tmp_path / "template"
    tpl.mkdir()

    # Workspace-root README
    (tpl / "README.md").write_text("# Workspace README", encoding="utf-8")

    # Project subfolder README (mirrors templates/coding/Project/README.md)
    project_dir = tpl / "Project"
    project_dir.mkdir()
    (project_dir / "README.md").write_text("# Project README", encoding="utf-8")
    (project_dir / "AGENT-RULES.md").write_text("# Agent Rules", encoding="utf-8")

    # .github/instructions/copilot-instructions.md
    instructions_dir = tpl / ".github" / "instructions"
    instructions_dir.mkdir(parents=True)
    (instructions_dir / "copilot-instructions.md").write_text(
        "# Copilot instructions", encoding="utf-8"
    )

    # NoAgentZone README (also a README.md — must be deleted when False)
    naz_dir = tpl / "NoAgentZone"
    naz_dir.mkdir()
    (naz_dir / "README.md").write_text("# NoAgentZone README", encoding="utf-8")

    # A hooks script directory with a counter config placeholder
    hooks_dir = tpl / ".github" / "hooks" / "scripts"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    return tpl


def _do_create(
    tpl: Path,
    dest: Path,
    folder_name: str = "TestProject",
    include_readmes: bool = True,
) -> Path:
    """Call create_project with safe defaults and return the created path."""
    return create_project(
        template_path=tpl,
        destination=dest,
        folder_name=folder_name,
        include_readmes=include_readmes,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestIncludeReadmesTrue:
    def test_include_readmes_true_preserves_readmes(
        self, tmp_path: Path
    ) -> None:
        """include_readmes=True (default) must preserve all README.md files."""
        tpl = _build_template(tmp_path)
        dest = tmp_path / "dest"
        dest.mkdir()

        created = _do_create(tpl, dest, include_readmes=True)

        readme_files = list(created.rglob("README.md"))
        assert len(readme_files) >= 2, (
            "Expected at least 2 README.md files when include_readmes=True"
        )

    def test_default_parameter_is_true(self) -> None:
        """The default value for include_readmes must be True."""
        sig = inspect.signature(create_project)
        default = sig.parameters["include_readmes"].default
        assert default is True

    def test_include_readmes_true_explicit(
        self, tmp_path: Path
    ) -> None:
        """Explicitly passing True must behave identically to the default."""
        tpl = _build_template(tmp_path)
        dest = tmp_path / "dest"
        dest.mkdir()

        created = _do_create(tpl, dest, include_readmes=True)

        assert (created / "README.md").exists()
        assert (created / "TestProject" / "README.md").exists()


class TestIncludeReadmesFalse:
    def test_include_readmes_false_removes_readmes(
        self, tmp_path: Path
    ) -> None:
        """include_readmes=False must delete all README.md files in the workspace."""
        tpl = _build_template(tmp_path)
        dest = tmp_path / "dest"
        dest.mkdir()

        created = _do_create(tpl, dest, include_readmes=False)

        remaining_readmes = list(created.rglob("README.md"))
        assert remaining_readmes == [], (
            f"Expected no README.md files, found: {remaining_readmes}"
        )

    def test_include_readmes_false_preserves_agent_rules(
        self, tmp_path: Path
    ) -> None:
        """AGENT-RULES.md must NOT be deleted when include_readmes=False."""
        tpl = _build_template(tmp_path)
        dest = tmp_path / "dest"
        dest.mkdir()

        created = _do_create(tpl, dest, include_readmes=False)

        agent_rules = list(created.rglob("AGENT-RULES.md"))
        assert len(agent_rules) >= 1, "AGENT-RULES.md must survive the README toggle"

    def test_include_readmes_false_preserves_copilot_instructions(
        self, tmp_path: Path
    ) -> None:
        """copilot-instructions.md must NOT be deleted when include_readmes=False."""
        tpl = _build_template(tmp_path)
        dest = tmp_path / "dest"
        dest.mkdir()

        created = _do_create(tpl, dest, include_readmes=False)

        copilot = list(created.rglob("copilot-instructions.md"))
        assert len(copilot) >= 1, (
            "copilot-instructions.md must survive the README toggle"
        )

    def test_only_readme_md_deleted_case_sensitive(
        self, tmp_path: Path
    ) -> None:
        """Only files named exactly 'README.md' are deleted; other names survive."""
        tpl = _build_template(tmp_path)
        # Add a differently-cased file (should NOT be deleted on case-sensitive FS)
        (tpl / "readme.md").write_text("lower-case readme", encoding="utf-8")
        (tpl / "README.txt").write_text("README as txt", encoding="utf-8")

        dest = tmp_path / "dest"
        dest.mkdir()

        created = _do_create(tpl, dest, include_readmes=False)

        # Verify exact-match README.md files are gone
        assert not (created / "README.md").exists()

        # readme.txt must survive (different extension)
        assert (created / "README.txt").exists()


class TestMissingReadmeEdgeCase:
    def test_missing_readme_files_do_not_raise(
        self, tmp_path: Path
    ) -> None:
        """If README.md files are already absent, no FileNotFoundError must be raised."""
        tpl = tmp_path / "template_no_readme"
        tpl.mkdir()

        # Template with NO README.md files at all
        project_dir = tpl / "Project"
        project_dir.mkdir()
        (project_dir / "AGENT-RULES.md").write_text("# Agent Rules", encoding="utf-8")

        instructions_dir = tpl / ".github" / "instructions"
        instructions_dir.mkdir(parents=True)
        (instructions_dir / "copilot-instructions.md").write_text(
            "# Copilot", encoding="utf-8"
        )
        hooks_dir = tpl / ".github" / "hooks" / "scripts"
        hooks_dir.mkdir(parents=True, exist_ok=True)

        dest = tmp_path / "dest"
        dest.mkdir()

        # Must not raise
        created = create_project(
            template_path=tpl,
            destination=dest,
            folder_name="NoReadmeProject",
            include_readmes=False,
        )

        assert created.is_dir()
        assert list(created.rglob("README.md")) == []
