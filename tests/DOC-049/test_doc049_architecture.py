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
