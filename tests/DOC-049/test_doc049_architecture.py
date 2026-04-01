"""
DOC-049 — Tests for updated architecture.md (v3.3.x)

Verifies that docs/architecture.md contains all required v3.3.x content
and does not contain stale references to old names/prefixes.
"""

import re
from pathlib import Path

ARCH_PATH = Path(__file__).parent.parent.parent / "docs" / "architecture.md"


def _content() -> str:
    return ARCH_PATH.read_text(encoding="utf-8")


def test_architecture_file_exists():
    assert ARCH_PATH.exists(), "docs/architecture.md must exist"


def test_references_v336():
    """architecture.md must reference v3.3.6 as the current version."""
    content = _content()
    assert "v3.3.6" in content or "3.3.6" in content, (
        "architecture.md must reference v3.3.6"
    )


def test_no_stale_ts_sae_prefix_in_prose():
    """No TS-SAE- prefix should appear anywhere in architecture.md."""
    assert "TS-SAE-" not in _content(), (
        "architecture.md must not contain any 'TS-SAE-' references (old prefix)"
    )


def test_contains_agent_workbench_reference():
    """architecture.md must reference the agent-workbench template."""
    assert "agent-workbench" in _content(), (
        "architecture.md must contain 'agent-workbench'"
    )


def test_contains_agentdocs_reference():
    """architecture.md must document the AgentDocs system."""
    assert "AgentDocs" in _content(), (
        "architecture.md must contain 'AgentDocs'"
    )


def test_contains_sae_prefix_reference():
    """architecture.md must document the SAE- workspace prefix."""
    content = _content()
    assert "SAE-" in content, (
        "architecture.md must reference the SAE- workspace prefix"
    )


def test_contains_version_history_section():
    """architecture.md must contain a Version History section."""
    assert "## Version History" in _content(), (
        "architecture.md must contain a '## Version History' section"
    )


def test_version_history_covers_v330():
    """Version History must include an entry for v3.3.0."""
    assert "v3.3.0" in _content(), (
        "architecture.md Version History must include v3.3.0"
    )


def test_version_history_covers_v335():
    """Version History must include an entry for v3.3.5."""
    assert "v3.3.5" in _content(), (
        "architecture.md Version History must include v3.3.5"
    )


def test_contains_agent_system_section():
    """architecture.md must document the redesigned agent system."""
    content = _content()
    assert "## Agent System" in content, (
        "architecture.md must contain an '## Agent System' section"
    )


def test_contains_template_system_section():
    """architecture.md must document the template system."""
    content = _content()
    assert "## Template System" in content, (
        "architecture.md must contain a '## Template System' section"
    )


# --- Edge-case tests (Tester additions) ---

REPO_ROOT = Path(__file__).parent.parent.parent


def test_agentdocs_path_is_accurate():
    """AgentDocs must exist at the correct path and architecture.md must reference it accurately.

    The correct path is templates/agent-workbench/Project/AgentDocs/.
    architecture.md must reference this path (not the old wrong path).
    """
    actual_path = REPO_ROOT / "templates" / "agent-workbench" / "Project" / "AgentDocs"
    assert actual_path.exists(), (
        "AgentDocs must exist at templates/agent-workbench/Project/AgentDocs/"
    )
    content = _content()
    assert "templates/agent-workbench/Project/AgentDocs" in content, (
        "architecture.md must reference AgentDocs at "
        "templates/agent-workbench/Project/AgentDocs/ — update the AgentDocs System section."
    )


def test_agentdocs_agent_rules_file_exists():
    """AGENT-RULES.md must exist inside the AgentDocs directory."""
    agentdocs = REPO_ROOT / "templates" / "agent-workbench" / "Project" / "AgentDocs"
    assert (agentdocs / "AGENT-RULES.md").exists(), (
        "AGENT-RULES.md must exist in templates/agent-workbench/Project/AgentDocs/"
    )


def test_agentdocs_claimed_files_exist():
    """All files mentioned in the AgentDocs table in architecture.md must exist.

    architecture.md lists AGENT-RULES.md, TOOL-MATRIX.md, QUICKREF.md.
    All three must be present. If this test fails, either create the missing
    files or remove their entries from the architecture.md table.
    """
    content = _content()
    # Both files are claimed in architecture.md — verify they actually exist
    agentdocs = REPO_ROOT / "templates" / "agent-workbench" / "Project" / "AgentDocs"
    missing = []
    for filename in ["TOOL-MATRIX.md", "QUICKREF.md"]:
        if filename in content:
            if not (agentdocs / filename).exists():
                missing.append(filename)
    assert not missing, (
        f"architecture.md claims these AgentDocs files exist but they do not: "
        f"{missing}. Either create them or remove from architecture.md."
    )


def test_no_nonexistent_skills_subdir_claimed():
    """architecture.md must not claim .github/agents/skills/ exists if it doesn't.

    If architecture.md states 'skill definitions are stored in .github/agents/skills/',
    that directory must actually exist in the repository.
    """
    content = _content()
    skills_dir = REPO_ROOT / ".github" / "agents" / "skills"
    if ".github/agents/skills/" in content:
        assert skills_dir.exists(), (
            "architecture.md references '.github/agents/skills/' but that "
            "directory does not exist. Update architecture.md to reflect the "
            "actual skills directory location."
        )
