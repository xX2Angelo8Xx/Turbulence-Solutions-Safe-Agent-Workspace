"""
Tests for DOC-008: Add read-first directive to copilot-instructions.md

Verifies that the template file contains a prominent read-first directive
pointing agents to AGENT-RULES.md before any other work.
"""
import pathlib

TEMPLATE_FILE = (
    pathlib.Path(__file__).parent.parent.parent
    / "templates"
    / "coding"
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
    assert "AGENT-RULES.md" in content, (
        "No read-first directive mentioning AGENT-RULES.md found in copilot-instructions.md"
    )
    # Check for common directive keywords indicating it's instructional
    directive_keywords = ["before any work", "first action", "read"]
    content_lower = content.lower()
    assert any(kw in content_lower for kw in directive_keywords), (
        "copilot-instructions.md does not contain a recognisable read-first directive "
        f"(expected one of: {directive_keywords})"
    )


def test_directive_mentions_agent_rules():
    """The directive must reference AGENT-RULES.md by exact filename."""
    content = _read_file()
    assert "AGENT-RULES.md" in content, (
        "AGENT-RULES.md is not referenced in copilot-instructions.md"
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
    """The directive must appear within the first 10 lines or first section of the file."""
    lines = _read_lines()
    # Check first 10 lines for AGENT-RULES.md reference
    first_ten = "\n".join(lines[:10])
    if "AGENT-RULES.md" in first_ten:
        return  # Directive is within first 10 lines — pass

    # Fallback: check first section (up to first blank line after content starts)
    # Find end of first content block
    first_section_end = 0
    content_started = False
    for i, line in enumerate(lines):
        if line.strip():
            content_started = True
        elif content_started and not line.strip() and i > 2:
            first_section_end = i
            break

    first_section = "\n".join(lines[:first_section_end]) if first_section_end else "\n".join(lines[:20])
    assert "AGENT-RULES.md" in first_section, (
        f"Read-first directive (AGENT-RULES.md) not found within first 10 lines or first section. "
        f"First 10 lines:\n{first_ten}"
    )


def test_existing_content_preserved():
    """All major existing content sections must still be present."""
    content = _read_file()
    required_sections = [
        "Turbulence Solutions",
        "NoAgentZone",
        "Workspace Rules",
        "Security",
        "Coding Standards",
        "Communication",
        "Known Tool Limitations",
    ]
    missing = [s for s in required_sections if s not in content]
    assert not missing, (
        f"The following original content sections are missing from copilot-instructions.md: {missing}"
    )
