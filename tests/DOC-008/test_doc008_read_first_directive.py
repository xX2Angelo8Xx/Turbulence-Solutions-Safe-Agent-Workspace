"""
Tests for DOC-008: Add read-first directive to copilot-instructions.md

Verifies that the template file contains a prominent read-first directive
pointing agents to AGENT-RULES.md before any other work.
"""
import pathlib

TEMPLATE_FILE = (
    pathlib.Path(__file__).parent.parent.parent
    / "templates"
    / "agent-workbench"
    / ".github"
    / "instructions"
    / "copilot-instructions.md"
)


def _read_file():
    return TEMPLATE_FILE.read_text(encoding="utf-8")


def _read_lines():
    return _read_file().splitlines()


def test_read_first_directive_present():
    """copilot-instructions.md must contain a read-first directive."""
    content = _read_file()
    assert "AgentDocs/AGENT-RULES.md" in content, (
        "No read-first directive mentioning AgentDocs/AGENT-RULES.md found in copilot-instructions.md"
    )
    # Check for common directive keywords indicating it's instructional
    directive_keywords = ["before any work", "first action", "read"]
    content_lower = content.lower()
    assert any(kw in content_lower for kw in directive_keywords), (
        "copilot-instructions.md does not contain a recognisable read-first directive "
        f"(expected one of: {directive_keywords})"
    )


def test_directive_mentions_agent_rules():
    """The directive must reference AgentDocs/AGENT-RULES.md by exact filename."""
    content = _read_file()
    assert "AgentDocs/AGENT-RULES.md" in content, (
        "AgentDocs/AGENT-RULES.md is not referenced in copilot-instructions.md"
    )


def test_directive_uses_project_name_placeholder():
    """The directive must use the {{PROJECT_NAME}} placeholder."""
    content = _read_file()
    assert "{{PROJECT_NAME}}" in content, (
        "{{PROJECT_NAME}} placeholder not found in copilot-instructions.md. "
        "The directive must use this placeholder so project_creator.py can replace it."
    )
    # The placeholder should appear alongside AGENT-RULES.md
    for line in content.splitlines():
        if "AGENT-RULES.md" in line and "{{PROJECT_NAME}}" in line:
            return
    raise AssertionError(
        "{{PROJECT_NAME}} and AGENT-RULES.md do not appear together on the same line. "
        "The path reference should be '{{PROJECT_NAME}}/AGENT-RULES.md'."
    )


def test_directive_is_near_top():
    """The directive must appear within the first 20 lines of the file."""
    lines = _read_lines()
    first_twenty = "\n".join(lines[:20])
    assert "AGENT-RULES.md" in first_twenty, (
        f"Read-first directive (AGENT-RULES.md) not found within first 20 lines. "
        f"First 20 lines:\n{first_twenty}"
    )


def test_existing_content_preserved():
    """All major existing content sections must still be present."""
    content = _read_file()
    required_sections = [
        "Turbulence Solutions",
        "NoAgentZone",
        "Workspace Layout",
        "Security",
        "Known Tool Limitations",
    ]
    missing = [s for s in required_sections if s not in content]
    assert not missing, (
        f"The following original content sections are missing from copilot-instructions.md: {missing}"
    )
